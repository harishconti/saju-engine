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
    // AU-25: the Neon identity is deleted with raw statements on the transaction client. The
    // default probe answers "the relation exists"; tests override the once-queue to simulate a
    // missing relation or a failing delete.
    $queryRaw: vi.fn(
      async (_strings: TemplateStringsArray, relation: string): Promise<Array<{ name: string | null }>> => [
        { name: relation },
      ],
    ),
    $executeRaw: vi.fn(async (strings: TemplateStringsArray, ...values: unknown[]) => {
      const sql = strings.join("?");
      if (sql.includes('neon_auth."session"')) events.push("neon:session");
      else if (sql.includes('neon_auth."account"')) events.push("neon:account");
      else if (sql.includes('neon_auth."user"')) events.push("neon:user");
      events.push(`neon:id:${String(values[0])}`);
      return 1;
    }),
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
    auditLog: {
      create: vi.fn(async () => {
        events.push("tx:auditLog.create");
        return {};
      }),
    },
  };

  const prismaMock = {
    deletionRequest: {
      findMany: vi.fn(),
      update: vi.fn(async (_args: { where: { id: string }; data: Record<string, unknown> }) => {
        events.push("deletion:completed");
        return {};
      }),
    },
    report: { findMany: vi.fn(), deleteMany: vi.fn() },
    profile: { findMany: vi.fn(), updateMany: vi.fn(), deleteMany: vi.fn() },
    order: { findMany: vi.fn() },
    user: { update: vi.fn() },
    consentRecord: { updateMany: vi.fn() },
    auditLog: {
      create: vi.fn(async () => {
        events.push("audit:identity");
        return {};
      }),
    },
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
    expect(prismaMock.deletionRequest.update).toHaveBeenCalledWith({
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

describe("processDueDeletions — Neon identity deletion (AU-25)", () => {
  beforeEach(() => {
    prismaMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.order.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);
  });

  it("deletes sessions, accounts then the user in one transaction, before marking the request completed", async () => {
    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    const session = events.indexOf("neon:session");
    const account = events.indexOf("neon:account");
    const user = events.indexOf("neon:user");
    const completed = events.indexOf("deletion:completed");

    expect(session).toBeGreaterThanOrEqual(0);
    expect(account).toBeGreaterThan(session);
    expect(user).toBeGreaterThan(account);
    expect(completed).toBeGreaterThan(user);
    // Every statement went through the transaction client, and the three probes ran first.
    expect(txMock.$executeRaw).toHaveBeenCalledTimes(3);
    expect(txMock.$queryRaw).toHaveBeenCalledTimes(3);
  });

  it("uses the pre-anonymisation User.id, never the rewritten email", async () => {
    await processDueDeletions(NOW);

    for (const call of txMock.$executeRaw.mock.calls) {
      expect(call).toContain("u1");
      expect(call.join(" ")).not.toContain("deleted+u1@deleted.invalid");
    }
  });

  it("leaves the request pending when the raw delete throws, after the local erasure committed", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    txMock.$executeRaw.mockRejectedValueOnce(new Error("permission denied"));

    await expect(processDueDeletions(NOW)).resolves.toBe(0);

    // The local half committed: the account is anonymised and the request can be retried safely.
    expect(txMock.user.update).toHaveBeenCalled();
    expect(events.indexOf("commit")).toBeGreaterThanOrEqual(0);
    // The identity half did not: no completion, and the failure is recorded for an operator.
    expect(prismaMock.deletionRequest.update).not.toHaveBeenCalled();
    expect(prismaMock.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          entity: "deletion",
          action: "update",
          after: expect.objectContaining({ neonIdentity: "failed" }),
        }),
      }),
    );
    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });

  it("skips the delete entirely when a neon_auth relation is absent, leaving the request retryable", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    txMock.$queryRaw
      .mockResolvedValueOnce([{ name: 'neon_auth."session"' }])
      .mockResolvedValueOnce([{ name: null }])
      .mockResolvedValueOnce([{ name: 'neon_auth."user"' }]);

    await expect(processDueDeletions(NOW)).resolves.toBe(0);

    expect(txMock.$executeRaw).not.toHaveBeenCalled();
    expect(prismaMock.deletionRequest.update).not.toHaveBeenCalled();
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
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
      prismaMock.deletionRequest.update.mock.calls as unknown as Array<[{ where: { id: string } }]>
    ).map((call) => call[0].where.id);
    expect(completedIds).toEqual(["dr2"]);
    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
