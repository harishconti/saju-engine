import { Prisma } from "@prisma/client";
import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-04 (2026-10-26 audit): erasure failed for anyone who had ever ordered.
 *
 * `processDueDeletions` deleted the R2 artefacts first and then tried to delete every profile. But
 * `Order_profileAId_fkey` is ON DELETE RESTRICT, so the transaction raised P2003 and rolled back —
 * after the artefacts were already gone. The request stayed `pending`, and every later cron run
 * threw on the same rows, blocking deletions queued behind them.
 *
 * Owner decision D2: keep order rows for accounting and scrub the profiles they reference. The
 * birth data still goes, and the R2 objects are removed only once the database has committed.
 */

const { prismaMock, txMock, r2Mock, processDodoEvent, events } = vi.hoisted(() => {
  const events: string[] = [];
  const txMock = {
    report: {
      deleteMany: vi.fn(async () => {
        events.push("tx:report.deleteMany");
        return { count: 1 };
      }),
    },
    profile: {
      updateMany: vi.fn(async () => {
        events.push("tx:profile.updateMany");
        return { count: 1 };
      }),
      deleteMany: vi.fn(async () => {
        events.push("tx:profile.deleteMany");
        return { count: 1 };
      }),
    },
    delivery: {
      deleteMany: vi.fn(async () => {
        events.push("tx:delivery.deleteMany");
        return { count: 0 };
      }),
    },
    user: {
      update: vi.fn(async () => {
        events.push("tx:user.update");
        return {};
      }),
    },
    consentRecord: {
      updateMany: vi.fn(async () => {
        events.push("tx:consentRecord.updateMany");
        return { count: 0 };
      }),
    },
    deletionRequest: {
      update: vi.fn(async () => {
        events.push("tx:deletionRequest.update");
        return {};
      }),
    },
    auditLog: {
      create: vi.fn(async () => {
        events.push("tx:auditLog.create");
        return {};
      }),
    },
  };

  const prismaMock = {
    deletionRequest: { findMany: vi.fn(), update: vi.fn() },
    report: { findMany: vi.fn(), deleteMany: vi.fn() },
    profile: { findMany: vi.fn(), updateMany: vi.fn(), deleteMany: vi.fn() },
    order: { findMany: vi.fn() },
    user: { update: vi.fn() },
    consentRecord: { updateMany: vi.fn() },
    auditLog: { create: vi.fn() },
    webhookEvent: { findMany: vi.fn(), update: vi.fn() },
    $transaction: vi.fn(),
  };

  const r2Mock = {
    isR2Configured: vi.fn(() => true),
    drainObjectDeletions: vi.fn(),
    listObjectsByPrefix: vi.fn(),
    deleteObjects: vi.fn(),
    deleteObjectOrQueue: vi.fn(async (key: string) => {
      events.push(`r2:${key}`);
    }),
  };

  const processDodoEvent = vi.fn();

  return { prismaMock, txMock, r2Mock, processDodoEvent, events };
});

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/r2", () => r2Mock);
vi.mock("@/lib/dodo-webhook", () => ({ processDodoEvent }));

const { processDueDeletions } = await import("../cleanup");

const NOW = new Date("2026-10-26T12:00:00.000Z");

const KEYS = {
  pdfKey: "reports/u1/o1/r1.pdf",
  mdKey: "reports/u1/o1/r1.md",
  audioKey: "reports/u1/o1/r1.mp3",
  htmlKey: "reports/u1/o1/r1.html",
};

function deletionRequest(id: string, userId: string) {
  return { id, userId };
}

beforeEach(() => {
  vi.clearAllMocks();
  events.length = 0;

  // A commit is what makes the post-commit R2 deletion safe, so record when it happens.
  prismaMock.$transaction.mockImplementation(async (fn: (tx: typeof txMock) => Promise<unknown>) => {
    const result = await fn(txMock);
    events.push("commit");
    return result;
  });

  prismaMock.deletionRequest.findMany.mockResolvedValue([deletionRequest("dr1", "u1")]);
  prismaMock.report.findMany.mockResolvedValue([]);
  prismaMock.profile.findMany.mockResolvedValue([]);
  prismaMock.order.findMany.mockResolvedValue([]);
});

describe("processDueDeletions — erasure with an order (AU-04, D2)", () => {
  beforeEach(() => {
    prismaMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.order.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);
  });

  it("completes instead of hitting the Order RESTRICT constraint", async () => {
    await expect(processDueDeletions(NOW)).resolves.toBe(1);
    expect(txMock.deletionRequest.update).toHaveBeenCalledWith({
      where: { id: "dr1" },
      data: { status: "completed", completedAt: NOW },
    });
  });

  it("keeps the order and scrubs the profile it references", async () => {
    await processDueDeletions(NOW);

    expect(txMock.profile.deleteMany).toHaveBeenCalledWith({
      where: { userId: "u1", id: { notIn: ["p1"] } },
    });
    expect(txMock.profile.updateMany).toHaveBeenCalledWith({
      where: { userId: "u1", id: { in: ["p1"] } },
      data: expect.objectContaining({
        label: "Deleted profile",
        fullName: "Deleted profile",
        birthDate: new Date(0),
        birthTime: "00:00",
        timezone: null,
        utcOffset: null,
        city: "Deleted",
        country: "Deleted",
        latitude: null,
        longitude: null,
        timeKnown: false,
        chartJson: Prisma.DbNull,
        chartComputedAt: null,
        deletedAt: NOW,
      }),
    });
    // The order itself is never touched.
    expect(prismaMock.order.findMany).toHaveBeenCalledWith({
      where: { OR: [{ profileAId: { in: ["p1"] } }, { profileBId: { in: ["p1"] } }] },
      select: { profileAId: true, profileBId: true },
    });
  });

  it("deletes report artefacts only after the transaction commits", async () => {
    await processDueDeletions(NOW);

    const commitAt = events.indexOf("commit");
    expect(commitAt).toBeGreaterThan(-1);
    for (const key of Object.values(KEYS)) {
      const deletedAt = events.indexOf(`r2:${key}`);
      expect(deletedAt, `${key} was never deleted`).toBeGreaterThan(-1);
      expect(deletedAt, `${key} was deleted before the commit`).toBeGreaterThan(commitAt);
    }
    expect(r2Mock.deleteObjectOrQueue).toHaveBeenCalledTimes(4);
  });

  it("deletes deliveries and anonymises the account", async () => {
    await processDueDeletions(NOW);

    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { userId: "u1" } });
    expect(txMock.delivery.deleteMany).toHaveBeenCalledWith({ where: { userId: "u1" } });
    expect(txMock.user.update).toHaveBeenCalledWith({
      where: { id: "u1" },
      data: {
        name: "Deleted user",
        email: "deleted+u1@deleted.invalid",
        deletedAt: NOW,
      },
    });
    expect(txMock.consentRecord.updateMany).toHaveBeenCalledWith({
      where: { userId: "u1", withdrawnAt: null },
      data: { withdrawnAt: NOW },
    });
  });
});

describe("processDueDeletions — erasure with no order", () => {
  it("deletes the profile as before", async () => {
    prismaMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
    expect(txMock.profile.deleteMany).toHaveBeenCalledWith({
      where: { userId: "u1", id: { notIn: [] } },
    });
    const commitAt = events.indexOf("commit");
    expect(events.indexOf(`r2:${KEYS.pdfKey}`)).toBeGreaterThan(commitAt);
  });
});

describe("processDueDeletions — one failure cannot block the rest", () => {
  it("leaves the failed request pending and completes a later one", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    prismaMock.deletionRequest.findMany.mockResolvedValue([
      deletionRequest("dr1", "u1"),
      deletionRequest("dr2", "u2"),
    ]);
    prismaMock.report.findMany
      .mockRejectedValueOnce(new Error("database hiccup"))
      .mockResolvedValueOnce([]);
    prismaMock.profile.findMany.mockResolvedValue([]);

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    const completedIds = (
      txMock.deletionRequest.update.mock.calls as unknown as Array<[{ where: { id: string } }]>
    ).map((call) => call[0].where.id);
    expect(completedIds).toEqual(["dr2"]);
    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
