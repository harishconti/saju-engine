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
 */
const { prismaMock, txMock, processDodoEvent } = vi.hoisted(() => {
  const txMock = {
    profile: {
      updateMany: vi.fn(async () => ({ count: 1 })),
      deleteMany: vi.fn(async () => ({ count: 0 })),
    },
  };
  const prismaMock = {
    profile: {
      findMany: vi.fn(
        async (_args: {
          where: { deletedAt: null; updatedAt: { lt: Date } };
          select: { id: true };
          take: number;
        }) => [] as Array<{ id: string }>,
      ),
    },
    order: { findMany: vi.fn(async () => [] as Array<{ profileAId: string; profileBId: string | null }>) },
    report: { findMany: vi.fn(async () => [] as Array<{ profileAId: string; profileBId: string | null }>) },
    $transaction: vi.fn(async (fn: (t: typeof txMock) => Promise<unknown>) => fn(txMock)),
  };
  return { prismaMock, txMock, processDodoEvent: vi.fn() };
});

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/r2", () => ({
  isR2Configured: () => false,
  drainObjectDeletions: vi.fn(),
  listObjectsByPrefix: vi.fn(),
  deleteObjects: vi.fn(),
  deleteObjectOrQueue: vi.fn(),
}));
vi.mock("@/lib/dodo-webhook", () => ({ processDodoEvent }));

const { retireInactiveProfiles } = await import("../cleanup");

const NOW = new Date("2026-10-26T12:00:00.000Z");
/** Exactly 24 calendar months before NOW. */
const CUTOFF = new Date("2024-10-26T12:00:00.000Z");

function cutoffUsed(): Date {
  const args = prismaMock.profile.findMany.mock.calls[0]?.[0];
  if (!args) throw new Error("profile.findMany was never called");
  return args.where.updatedAt.lt;
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
    prismaMock.profile.findMany.mockResolvedValue([]);
    prismaMock.order.findMany.mockResolvedValue([]);
    prismaMock.report.findMany.mockResolvedValue([]);
    txMock.profile.updateMany.mockResolvedValue({ count: 1 });
    txMock.profile.deleteMany.mockResolvedValue({ count: 0 });
  });

  it("selects only live profiles older than exactly 24 calendar months", async () => {
    await retireInactiveProfiles(NOW);

    expect(PROFILE_INACTIVITY_RETENTION_MONTHS).toBe(24);
    expect(cutoffUsed()).toEqual(CUTOFF);
    expect(prismaMock.profile.findMany.mock.calls[0]![0].where).toEqual({
      deletedAt: null,
      updatedAt: { lt: CUTOFF },
    });
  });

  it("does nothing when no profile has been idle that long", async () => {
    prismaMock.profile.findMany.mockResolvedValue([]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(0);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
    expect(txMock.profile.deleteMany).not.toHaveBeenCalled();
  });

  it("scrubs an old profile a report still references, and keeps the row", async () => {
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.report.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);

    await expect(retireInactiveProfiles(NOW)).resolves.toBe(1);

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

  it("scrubs rather than deletes a profile an order references — Profile A is RESTRICT", async () => {
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.order.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);

    await retireInactiveProfiles(NOW);

    expect(txMock.profile.updateMany).toHaveBeenCalledTimes(1);
    expect(txMock.profile.deleteMany).not.toHaveBeenCalled();
  });

  it("deletes an old profile nothing references", async () => {
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
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
