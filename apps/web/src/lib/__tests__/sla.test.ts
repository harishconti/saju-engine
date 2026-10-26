/**
 * The 10-hour delivery rule.
 *
 * The behaviour locked here:
 *  - a reading that has waited past the deadline is released, and **recorded** as released
 *    without a human reading it (`reviewOutcome = SLA_AUTO`) — not passed off as reviewed;
 *  - a reading a person is already on is left alone;
 *  - an unpaid or refunded order is not delivered;
 *  - running the sweep twice delivers once;
 *  - an auto-delivered deep reading (the one that promises an MP3) approves at the deadline but
 *    **waits for its audio** before the client hears about it — and if the audio never arrives,
 *    the fallback releases the email anyway.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

// `vi.mock` factories are hoisted above the module body, so the mocks they need have to be
// created with `vi.hoisted` — a plain top-level const would not exist yet.
const { prismaMock, approveAndDeliver, deliverReport, enqueueAudio, tierPromisesAudio } = vi.hoisted(
  () => ({
    prismaMock: {
      report: {
        findMany: vi.fn(),
        count: vi.fn(),
        update: vi.fn(),
        findUnique: vi.fn(),
      },
      job: { count: vi.fn(), create: vi.fn() },
      delivery: { create: vi.fn(), findFirst: vi.fn() },
      $transaction: vi.fn(),
      order: { findUnique: vi.fn() },
    },
    approveAndDeliver: vi.fn(),
    deliverReport: vi.fn(),
    enqueueAudio: vi.fn(),
    tierPromisesAudio: vi.fn(),
  }),
);

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/email", () => ({ deliverReport }));
vi.mock("@/lib/fulfilment", () => ({ enqueueAudio }));
vi.mock("@/lib/tts", () => ({ tierPromisesAudio }));
vi.mock("@/lib/review", () => ({
  approveAndDeliver,
  ApprovalError: class ApprovalError extends Error {
    constructor(message: string, readonly code: string) {
      super(message);
    }
  },
}));

import { AUDIO_HOLD_FALLBACK_HOURS, FAILED_RENDER_DEADLINE_HOURS, REVIEW_SLA_HOURS, runSlaSweep } from "@/lib/sla";

const NOW = new Date("2026-10-23T12:00:00Z");

/** The deadline the sweep computes: the paid clock, `REVIEW_SLA_HOURS` back from now. */
const CUTOFF = new Date(NOW.getTime() - REVIEW_SLA_HOURS * 3_600_000);

beforeEach(() => {
  vi.clearAllMocks();
  prismaMock.report.findMany.mockResolvedValue([]);
  prismaMock.report.count.mockResolvedValue(0);
  prismaMock.report.update.mockResolvedValue({});
  prismaMock.job.count.mockResolvedValue(0);
  prismaMock.delivery.create.mockResolvedValue({});
  prismaMock.$transaction.mockImplementation(async (fn: (tx: unknown) => unknown) => fn(prismaMock));
  approveAndDeliver.mockResolvedValue({
    ok: true,
    released: true,
    note: "delivered",
    emailHeld: false,
    audioQueued: false,
  });
  deliverReport.mockResolvedValue(undefined);
  enqueueAudio.mockResolvedValue(false);
  tierPromisesAudio.mockReturnValue(false);
});

/** A reading that has been waiting longer than the deadline. */
function overdue(id = "r1", status: "DRAFT_READY" | "IN_REVIEW" = "DRAFT_READY") {
  return {
    id,
    status,
    createdAt: new Date(NOW.getTime() - (REVIEW_SLA_HOURS + 1) * 3_600_000),
    order: { status: "PAID" },
  };
}

describe("the 10-hour rule", () => {
  it("releases a reading that has waited past the deadline", async () => {
    prismaMock.report.findMany.mockResolvedValueOnce([overdue()]);
    const result = await runSlaSweep(NOW);

    expect(approveAndDeliver).toHaveBeenCalledWith("r1", { actorId: null, outcome: "SLA_AUTO" });
    expect(result.autoDelivered).toBe(1);
    expect(result.due).toBe(1);
  });

  it("leaves a reading a person is already on alone", async () => {
    prismaMock.report.findMany.mockResolvedValueOnce([overdue()]);
    prismaMock.report.count.mockResolvedValueOnce(1); // IN_REVIEW

    const result = await runSlaSweep(NOW);

    expect(approveAndDeliver).not.toHaveBeenCalled();
    expect(result.skippedInReview).toBe(1);
  });

  it("does not deliver a reading whose order is not paid", async () => {
    prismaMock.report.findMany.mockResolvedValueOnce([
      { ...overdue(), order: { status: "REFUNDED" } },
    ]);

    const result = await runSlaSweep(NOW);

    expect(approveAndDeliver).not.toHaveBeenCalled();
    expect(result.skipped).toBe(1);
  });

  it("does nothing when the queue is empty", async () => {
    const result = await runSlaSweep(NOW);
    expect(approveAndDeliver).not.toHaveBeenCalled();
    expect(result.due).toBe(0);
    expect(result.autoDelivered).toBe(0);
  });

  it("is idempotent — the second run finds nothing left to release", async () => {
    // The sweep only looks at DRAFT_READY; once released, the report is DELIVERED.
    prismaMock.report.findMany.mockResolvedValueOnce([overdue()]);
    await runSlaSweep(NOW);
    prismaMock.report.findMany.mockResolvedValueOnce([]);
    const second = await runSlaSweep(NOW);
    expect(second.autoDelivered).toBe(0);
    expect(approveAndDeliver).toHaveBeenCalledTimes(1);
  });

  it("releases a held email when the audio never arrived", async () => {
    // First call: the overdue readings. Second call: the held emails.
    prismaMock.report.findMany
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { id: "r-held" },
      ]);
    const result = await runSlaSweep(NOW);

    expect(prismaMock.report.update).toHaveBeenCalledWith({
      where: { id: "r-held" },
      data: { emailHeldForAudio: false },
    });
    expect(deliverReport).toHaveBeenCalledWith("r-held");
    expect(result.heldReleased).toBe(1);
  });

  it("reports the audio fallback window it uses", () => {
    expect(AUDIO_HOLD_FALLBACK_HOURS).toBe(2);
    expect(REVIEW_SLA_HOURS).toBe(10);
  });

  // AU-14 (2026-10-26 audit): the query asked for DRAFT_READY rows by `createdAt` and looked at the
  // order only after taking the batch. Ten rows that could never be released (unpaid, refunded)
  // filled every batch forever, and the due readings behind them were never reached.
  it("asks only for paid orders, so an un-releasable row cannot fill the batch", async () => {
    await runSlaSweep(NOW);

    const where = prismaMock.report.findMany.mock.calls[0][0].where;
    expect(where.order).toEqual({ is: { status: "PAID", paidAt: { lte: CUTOFF } } });
  });

  it("clocks the deadline from the payment, not from the render", async () => {
    await runSlaSweep(NOW);

    const where = prismaMock.report.findMany.mock.calls[0][0].where;
    // The promise starts when the client paid; a slow render must not buy a longer wait.
    expect(where.createdAt).toBeUndefined();
    expect(where.order.is.paidAt.lte.getTime()).toBe(CUTOFF.getTime());
  });

  it("releases a stale IN_REVIEW row: claiming a reading does not extend the deadline", async () => {
    prismaMock.report.findMany.mockResolvedValueOnce([overdue("r-stale", "IN_REVIEW")]);

    const result = await runSlaSweep(NOW);

    expect(approveAndDeliver).toHaveBeenCalledWith("r-stale", { actorId: null, outcome: "SLA_AUTO" });
    expect(result.autoDelivered).toBe(1);
    expect(result.skippedInReview).toBe(0);
  });

  it("reports stuck jobs without touching them", async () => {
    prismaMock.job.count.mockResolvedValue(2);
    const result = await runSlaSweep(NOW);
    expect(result.stuckJobs).toBe(2);
    expect(prismaMock.job.create).not.toHaveBeenCalled();
  });

  it("counts jobs that failed recently, so the sweep can go non-2xx", async () => {
    // AU-03 (2026-10-26 audit): FAILED jobs were never counted, so a render that refused every
    // order left the sweep's answer 200 and the workflow green.
    prismaMock.job.count.mockResolvedValueOnce(0).mockResolvedValueOnce(3).mockResolvedValueOnce(0);

    const result = await runSlaSweep(NOW);

    expect(result.stuckJobs).toBe(0);
    expect(result.recentFailures).toBe(3);
    expect(prismaMock.job.count).toHaveBeenNthCalledWith(2, {
      where: { state: "FAILED", finishedAt: { gte: expect.any(Date) } },
    });
  });

  // AU-14: a failed render has no automatic retry. `recentFailures` only looks an hour back, so a
  // paid order whose job died yesterday produced no signal at all and waited forever.
  it("reports paid renders that have been failed past the deadline", async () => {
    prismaMock.job.count.mockResolvedValueOnce(0).mockResolvedValueOnce(0).mockResolvedValueOnce(2);

    const result = await runSlaSweep(NOW);

    expect(result.overdueFailures).toBe(2);
    expect(prismaMock.job.count).toHaveBeenNthCalledWith(3, {
      where: {
        state: "FAILED",
        kind: { in: ["GENERATE", "REGENERATE"] },
        finishedAt: { lte: new Date(NOW.getTime() - FAILED_RENDER_DEADLINE_HOURS * 3_600_000) },
        // A paid order that will never arrive. An erased customer's row is excluded: it is
        // deliberately not re-rendered, so it must not alarm forever.
        order: { is: { status: "PAID", user: { deletedAt: null } } },
      },
    });
  });
});
