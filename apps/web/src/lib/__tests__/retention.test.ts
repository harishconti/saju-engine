import { Prisma } from "@prisma/client";
import { readFileSync } from "node:fs";
import path from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  ANONYMOUS_SAMPLE_RETENTION_DAYS,
  ANONYMOUS_SAMPLE_RETENTION_LABEL,
  PROFILE_INACTIVITY_RETENTION_LABEL,
  PROFILE_INACTIVITY_RETENTION_MONTHS,
} from "../retention";

/**
 * AU-27 (2026-10-26 audit) follow-up: the privacy policy promises birth details are kept "until
 * you delete them, or after 24 months of inactivity", and the compliance notes describe a warning
 * at 23 months and a sweep at 24. Removing the old no-op `flagInactiveProfiles` left the promise
 * with no implementation at all. The tests below pin the real sweep and the number it publishes.
 *
 * The first version of the sweep keyed "inactive" on `Profile.updatedAt`, which is a row timestamp,
 * not activity: `mirrorUser` returns early for an unchanged account and no order or report route
 * writes the profile, so a customer whose report was delivered yesterday could still carry a
 * two-year-old profile row. Owner decision D9 adds the missing signal — `User.lastSeenAt`, written
 * on authenticated requests — and the activity conditions now live in the query itself, so a spared
 * row cannot occupy the `take: 200` prefix.
 */

type Candidate = {
  id: string;
  user: { lastSeenAt: Date | null; createdAt: Date };
};
type OrderRef = { profileAId: string; profileBId: string | null; createdAt: Date };
type ReportRef = {
  id: string;
  profileAId: string;
  profileBId: string | null;
  createdAt: Date;
  deliveries: Array<{ createdAt: Date }>;
  pdfKey?: string | null;
  mdKey?: string | null;
  audioKey?: string | null;
  htmlKey?: string | null;
};
type FindArgs = {
  where: { updatedAt: { lt: Date } } & Record<string, unknown>;
  select: Record<string, unknown>;
  orderBy: unknown;
  take: number;
};

const OLD = new Date("2024-01-01T00:00:00.000Z");
const RECENT = new Date("2026-10-01T00:00:00.000Z");

const { prismaMock, txMock, r2Mock, processDodoEvent, events } = vi.hoisted(() => {
  const events: string[] = [];
  const txMock = {
    report: {
      deleteMany: vi.fn(async () => {
        events.push("tx:report.deleteMany");
        return { count: 1 };
      }),
    },
    delivery: {
      deleteMany: vi.fn(async () => {
        events.push("tx:delivery.deleteMany");
        return { count: 0 };
      }),
    },
    profile: {
      updateMany: vi.fn(async () => {
        events.push("tx:profile.updateMany");
        return { count: 1 };
      }),
      deleteMany: vi.fn(async () => {
        events.push("tx:profile.deleteMany");
        return { count: 0 };
      }),
    },
  };
  const prismaMock = {
    profile: {
      findMany: vi.fn(async (_args: FindArgs) => [] as Candidate[]),
    },
    order: {
      findMany: vi.fn(async (_args: Record<string, unknown>) => [] as OrderRef[]),
    },
    report: {
      findMany: vi.fn(async (_args: Record<string, unknown>) => [] as ReportRef[]),
    },
    $transaction: vi.fn(async (fn: (t: typeof txMock) => Promise<unknown>) => {
      const result = await fn(txMock);
      events.push("commit");
      return result;
    }),
  };
  const r2Mock = {
    isR2Configured: () => false,
    drainObjectDeletions: vi.fn(),
    listObjectsByPrefix: vi.fn(),
    deleteObjects: vi.fn(),
    deleteObjectOrQueue: vi.fn(async (key: string) => {
      events.push(`r2:${key}`);
    }),
  };
  return { prismaMock, txMock, r2Mock, processDodoEvent: vi.fn(), events };
});

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/r2", () => r2Mock);
vi.mock("@/lib/dodo-webhook", () => ({ processDodoEvent }));

const { retireInactiveProfiles } = await import("../cleanup");

const NOW = new Date("2026-10-26T12:00:00.000Z");
/** Exactly 24 calendar months before NOW. */
const CUTOFF = new Date("2024-10-26T12:00:00.000Z");

function profileRow(
  id: string,
  overrides: { lastSeenAt?: Date | null; createdAt?: Date } = {},
): Candidate {
  return {
    id,
    user: {
      lastSeenAt: overrides.lastSeenAt === undefined ? OLD : overrides.lastSeenAt,
      createdAt: overrides.createdAt ?? OLD,
    },
  };
}

function cutoffUsed(): Date {
  const args = prismaMock.profile.findMany.mock.calls[0]?.[0];
  if (!args) throw new Error("profile.findMany was never called");
  return args.where.updatedAt.lt;
}

function order(profileAId: string, createdAt: Date, profileBId: string | null = null): OrderRef {
  return { profileAId, profileBId, createdAt };
}

function report(
  profileAId: string,
  createdAt: Date,
  extra: Partial<Omit<ReportRef, "profileAId" | "createdAt">> = {},
): ReportRef {
  return { id: "r1", profileAId, profileBId: null, createdAt, deliveries: [], ...extra };
}

/** The report condition both profile columns use: recent row, or a recent delivery of it. */
function recentReportFilter() {
  return {
    OR: [
      { createdAt: { gte: CUTOFF } },
      { deliveries: { some: { createdAt: { gte: CUTOFF } } } },
    ],
  };
}

/**
 * Retention numbers that more than one layer quotes, so they cannot drift.
 *
 * The failure this guards is quiet and embarrassing: the emailed link is presigned for as long as the
 * object lives, and if those two ever disagree the message says "the link works for 7 days" while the
 * reading is deleted on day 3 — a 404 sent to someone who asked for their chart. Nothing in the app
 * would error; the link would simply stop working, and only for the people who waited.
 *
 * The same number is stated in the privacy policy, so that is checked too: it is a published document
 * about data retention, which is exactly the kind of page that rots silently.
 */
describe("retention windows", () => {
  const read = (rel: string) => readFileSync(path.resolve(process.cwd(), rel), "utf8");

  it("is the window the privacy policy publishes", () => {
    const privacy = read("src/app/privacy/page.tsx");
    expect(privacy).toContain("ANONYMOUS_SAMPLE_RETENTION_LABEL");
    expect(ANONYMOUS_SAMPLE_RETENTION_LABEL).toBe(`${ANONYMOUS_SAMPLE_RETENTION_DAYS} days`);
  });

  it.each([
    ["src/lib/cleanup.ts", "the sweep's cutoff"],
    ["src/app/api/sample/email/route.ts", "the emailed link's lifetime"],
    ["src/components/sample-flow.tsx", "the confirmation copy"],
  ])("reads the window from the shared constant, not a literal (%s)", (file) => {
    const source = read(file);
    // A bare "7 days" / "3 days" written into any of these is how the two drift apart.
    expect(source).not.toMatch(/\b\d+ days\b/);
    expect(source).toContain("ANONYMOUS_SAMPLE_RETENTION_");
  });

  it("sweeps by the same number it advertises", () => {
    // `cleanup.ts` must not grow its own copy of the window. Asserted on the *expression*, not on the
    // file: other sweeps legitimately roll their own windows (profile inactivity is 24 months, from
    // its own published constant), so a blanket "no numeric cutoff anywhere" rule would be wrong —
    // as the first version of this test was.
    const cleanup = read("src/lib/cleanup.ts");
    expect(cleanup).toContain('from "./retention"');
    expect(cleanup).toContain("now.getTime() - ANONYMOUS_SAMPLE_RETENTION_DAYS * DAY_MS");
  });
});

describe("inactive-profile sweep — the 24-month promise (AU-27)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    events.length = 0;
    prismaMock.profile.findMany.mockResolvedValue([]);
    prismaMock.order.findMany.mockResolvedValue([]);
    prismaMock.report.findMany.mockResolvedValue([]);
    txMock.profile.updateMany.mockResolvedValue({ count: 1 });
    txMock.profile.deleteMany.mockResolvedValue({ count: 0 });
    txMock.report.deleteMany.mockResolvedValue({ count: 0 });
    txMock.delivery.deleteMany.mockResolvedValue({ count: 0 });
  });

  it("selects only live profiles older than exactly 24 calendar months", async () => {
    await retireInactiveProfiles(NOW);

    expect(PROFILE_INACTIVITY_RETENTION_MONTHS).toBe(24);
    expect(cutoffUsed()).toEqual(CUTOFF);
    const args = prismaMock.profile.findMany.mock.calls[0]![0];
    expect(args.where.deletedAt).toBeNull();
    expect(args.take).toBe(200);
  });

  it("pushes every activity condition into the query, not a post-`take` filter", async () => {
    // Important 1: the in-memory filter ran *after* `take: 200`, so two hundred spared rows could
    // occupy the whole batch and the idle profiles behind them would never be reached. The `none`
    // relation filters make the database answer the activity question before the limit applies.
    await retireInactiveProfiles(NOW);

    const args = prismaMock.profile.findMany.mock.calls[0]![0];
    expect(args.where).toEqual({
      deletedAt: null,
      updatedAt: { lt: CUTOFF },
      ordersAsA: { none: { createdAt: { gte: CUTOFF } } },
      ordersAsB: { none: { createdAt: { gte: CUTOFF } } },
      reportsAsA: { none: recentReportFilter() },
      reportsAsB: { none: recentReportFilter() },
      user: {
        OR: [
          { lastSeenAt: null, createdAt: { lt: CUTOFF } },
          { lastSeenAt: { lt: CUTOFF } },
        ],
      },
    });
    // Deterministic order, so the same rows cannot sit in the prefix run after run.
    expect(args.orderBy).toEqual([{ updatedAt: "asc" }, { id: "asc" }]);
  });

  it("does nothing when no profile has been idle that long", async () => {
    prismaMock.profile.findMany.mockResolvedValue([]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
    expect(txMock.profile.deleteMany).not.toHaveBeenCalled();
  });

  it("deletes an old profile whose only reference is a report, retiring the report with it", async () => {
    // A report reference no longer pins the row: the report is deleted in the same transaction, so
    // the only RESTRICT that matters is the order one. An unreferenced row describes nobody.
    prismaMock.profile.findMany.mockResolvedValue([profileRow("p1")]);
    prismaMock.report.findMany.mockResolvedValue([report("p1", OLD, { id: "r1" })]);
    txMock.profile.deleteMany.mockResolvedValue({ count: 1 });

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(1);

    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["r1"] } } });
    expect(txMock.profile.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["p1"] } } });
    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
  });

  it("scrubs rather than deletes a profile an order references — Profile A is RESTRICT", async () => {
    prismaMock.profile.findMany.mockResolvedValue([profileRow("p1")]);
    prismaMock.order.findMany.mockResolvedValue([order("p1", OLD)]);

    await retireInactiveProfiles(NOW);

    expect(txMock.profile.updateMany).toHaveBeenCalledWith({
      where: { id: { in: ["p1"] }, deletedAt: null },
      data: expect.objectContaining({
        label: "Deleted profile",
        fullName: "Deleted profile",
        birthDate: new Date(0),
        birthTime: "00:00",
        city: "Deleted",
        country: "Deleted",
        timeKnown: false,
        chartJson: Prisma.DbNull,
        chartComputedAt: null,
        deletedAt: NOW,
      }),
    });
    expect(txMock.profile.deleteMany).not.toHaveBeenCalled();
  });

  it("deletes an old profile nothing references", async () => {
    prismaMock.profile.findMany.mockResolvedValue([profileRow("p1")]);
    txMock.profile.deleteMany.mockResolvedValue({ count: 1 });

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(1);

    expect(txMock.profile.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["p1"] } } });
    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
  });

  it("sweeps by the number the privacy policy publishes", () => {
    const privacy = readFileSync(
      path.resolve(process.cwd(), "src/app/privacy/page.tsx"),
      "utf8",
    );
    expect(privacy).toContain("PROFILE_INACTIVITY_RETENTION_LABEL");
    expect(PROFILE_INACTIVITY_RETENTION_LABEL).toBe(`${PROFILE_INACTIVITY_RETENTION_MONTHS} months`);
  });
});

describe("inactive-profile sweep — activity spares a live customer (AU-27, D9)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    events.length = 0;
    prismaMock.profile.findMany.mockResolvedValue([profileRow("p1")]);
    prismaMock.order.findMany.mockResolvedValue([]);
    prismaMock.report.findMany.mockResolvedValue([]);
    txMock.profile.updateMany.mockResolvedValue({ count: 1 });
    txMock.profile.deleteMany.mockResolvedValue({ count: 0 });
    txMock.report.deleteMany.mockResolvedValue({ count: 0 });
    txMock.delivery.deleteMany.mockResolvedValue({ count: 0 });
  });

  it("spares a profile whose order is inside the window, though the row is old", async () => {
    prismaMock.order.findMany.mockResolvedValue([order("p1", RECENT)]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
    expect(txMock.profile.deleteMany).not.toHaveBeenCalled();
  });

  it("spares a profile whose report was delivered inside the window — the row never moves", async () => {
    prismaMock.report.findMany.mockResolvedValue([
      report("p1", OLD, { id: "r-old" }),
      report("p1", RECENT, { id: "r-new", pdfKey: "reports/u1/o1/r-new.pdf" }),
    ]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
    expect(r2Mock.deleteObjectOrQueue).not.toHaveBeenCalled();
  });

  it("spares a profile whose old report was delivered recently", async () => {
    prismaMock.report.findMany.mockResolvedValue([
      report("p1", OLD, { id: "r1", deliveries: [{ createdAt: RECENT }] }),
    ]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
  });

  it("spares a profile referenced as partner B by a recent order", async () => {
    prismaMock.order.findMany.mockResolvedValue([order("someone-else", RECENT, "p1")]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
  });

  it("spares a profile whose owner signed in recently (D9), though the row and references are old", async () => {
    // Nothing writes `Profile.updatedAt` when a customer signs in to re-read a report, so a fresh
    // `User.lastSeenAt` is the only evidence that the profile is still in use.
    prismaMock.profile.findMany.mockResolvedValue([profileRow("p1", { lastSeenAt: RECENT })]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
    expect(txMock.profile.deleteMany).not.toHaveBeenCalled();
  });

  it("treats a never-seen account by its created date: a recent account is spared", async () => {
    prismaMock.profile.findMany.mockResolvedValue([
      profileRow("p1", { lastSeenAt: null, createdAt: RECENT }),
    ]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
  });

  it("still retires a profile whose every reference is older than the cutoff", async () => {
    prismaMock.report.findMany.mockResolvedValue([report("p1", OLD)]);
    txMock.profile.deleteMany.mockResolvedValue({ count: 1 });

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(1);

    expect(prismaMock.$transaction).toHaveBeenCalledTimes(1);
  });
});

describe("inactive-profile sweep — reports go with the profile (AU-27, D10)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    events.length = 0;
    prismaMock.profile.findMany.mockResolvedValue([profileRow("p1")]);
    prismaMock.order.findMany.mockResolvedValue([]);
    prismaMock.report.findMany.mockResolvedValue([]);
    txMock.profile.updateMany.mockResolvedValue({ count: 1 });
    txMock.profile.deleteMany.mockResolvedValue({ count: 1 });
    txMock.report.deleteMany.mockResolvedValue({ count: 1 });
    txMock.delivery.deleteMany.mockResolvedValue({ count: 1 });
  });

  it("deletes the reports and deliveries, then queues their objects after the commit", async () => {
    prismaMock.report.findMany.mockResolvedValue([
      report("p1", OLD, {
        id: "r1",
        pdfKey: "reports/u1/o1/r1.pdf",
        mdKey: "reports/u1/o1/r1.md",
        audioKey: "reports/u1/o1/r1.mp3",
        htmlKey: null,
      }),
    ]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(1);

    // The rows go in the same transaction that retires the profile, not in a later sweep.
    expect(txMock.delivery.deleteMany).toHaveBeenCalledWith({ where: { reportId: { in: ["r1"] } } });
    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["r1"] } } });

    // Objects are queued only after the database has committed: the profile row is what the queue
    // row depends on for its retry, and a storage error must not roll back the retirement.
    const commitAt = events.indexOf("commit");
    expect(commitAt).toBeGreaterThan(-1);
    for (const key of ["reports/u1/o1/r1.pdf", "reports/u1/o1/r1.md", "reports/u1/o1/r1.mp3"]) {
      const at = events.indexOf(`r2:${key}`);
      expect(at, `${key} was never queued`).toBeGreaterThan(-1);
      expect(at, `${key} was queued before the commit`).toBeGreaterThan(commitAt);
    }
    // A null key is skipped; the shared key list has no blanks in it.
    expect(r2Mock.deleteObjectOrQueue).toHaveBeenCalledTimes(3);
  });

  it("retires the reports of a profile kept for an order, and scrubs the profile", async () => {
    prismaMock.order.findMany.mockResolvedValue([order("p1", OLD)]);
    prismaMock.report.findMany.mockResolvedValue([
      report("p1", OLD, { id: "r1", pdfKey: "reports/u1/o1/r1.pdf" }),
    ]);

    await retireInactiveProfiles(NOW);

    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["r1"] } } });
    expect(txMock.profile.updateMany).toHaveBeenCalledTimes(1);
    expect(txMock.profile.deleteMany).not.toHaveBeenCalled();
    expect(r2Mock.deleteObjectOrQueue).toHaveBeenCalledWith("reports/u1/o1/r1.pdf");
  });

  it("retires a compatibility report shared with another profile (D10)", async () => {
    // The report embeds the retiring person's birth data, so it cannot be kept for the survivor.
    // The survivor gets no email: the deletion is part of the published retention behaviour.
    prismaMock.profile.findMany.mockResolvedValue([profileRow("p1"), profileRow("p2")]);
    prismaMock.order.findMany.mockResolvedValue([order("p1", OLD, "p2")]);
    prismaMock.report.findMany.mockResolvedValue([
      report("p1", OLD, { id: "shared", profileBId: "p2", pdfKey: "reports/u1/o1/shared.pdf" }),
    ]);

    await retireInactiveProfiles(NOW);

    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["shared"] } } });
    expect(r2Mock.deleteObjectOrQueue).toHaveBeenCalledWith("reports/u1/o1/shared.pdf");
  });

  it("does not touch the reports of a profile the sweep spares", async () => {
    prismaMock.order.findMany.mockResolvedValue([order("p1", RECENT)]);
    prismaMock.report.findMany.mockResolvedValue([
      report("p1", OLD, { id: "r1", pdfKey: "reports/u1/o1/r1.pdf" }),
    ]);

    await retireInactiveProfiles(NOW);

    expect(txMock.report.deleteMany).not.toHaveBeenCalled();
    expect(txMock.delivery.deleteMany).not.toHaveBeenCalled();
    expect(r2Mock.deleteObjectOrQueue).not.toHaveBeenCalled();
  });
});

describe("inactive-profile sweep — calendar-month cutoff", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    events.length = 0;
    prismaMock.profile.findMany.mockResolvedValue([]);
    prismaMock.order.findMany.mockResolvedValue([]);
    prismaMock.report.findMany.mockResolvedValue([]);
  });

  it("clamps a leap day to the last day of the target month instead of rolling into March", async () => {
    // `setUTCMonth` turns 29 February 2028 minus 24 months into 1 March 2026, so a profile idle
    // since 28 February would sit one day inside the window. Exact calendar maths clamps it.
    await retireInactiveProfiles(new Date("2028-02-29T12:00:00.000Z"));

    expect(cutoffUsed()).toEqual(new Date("2026-02-28T12:00:00.000Z"));
  });

  it("keeps the same month-end day when the target month has it", async () => {
    await retireInactiveProfiles(new Date("2026-08-31T12:00:00.000Z"));

    expect(cutoffUsed()).toEqual(new Date("2024-08-31T12:00:00.000Z"));
  });
});
