import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Owner decision D11 (2026-10-26): withdrawing service consent stops NEW orders and NEW jobs, but
 * work already paid for is still produced and delivered. The dispatcher is therefore deliberately
 * NOT consent-gated — a gate there would strand a paid order whose owner withdrew after paying.
 *
 * This test exists to stop a future reader "fixing" that absence. It drives the real
 * `runDispatchTick` over a queued job and fails if the dispatch path ever consults consent.
 */

const mocks = vi.hoisted(() => ({
  claimJob: vi.fn(),
  failJob: vi.fn(),
  hasActiveServiceConsent: vi.fn(),
  requireActiveServiceConsent: vi.fn(),
  prisma: {
    job: { count: vi.fn() },
    order: { findUnique: vi.fn() },
  },
}));

vi.mock("@/lib/queue", () => ({
  LEASE_MS: 60_000,
  claimJob: mocks.claimJob,
  completeJob: vi.fn(),
  failJob: mocks.failJob,
  recordAttempt: vi.fn(),
  requeueJob: vi.fn(),
}));
vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/consent", () => ({
  hasActiveServiceConsent: mocks.hasActiveServiceConsent,
  requireActiveServiceConsent: mocks.requireActiveServiceConsent,
}));
vi.mock("@/lib/owner-alert", () => ({
  notifyOwnerNewReview: vi.fn(),
  notifyOwnerEngineFailure: vi.fn().mockResolvedValue(true),
}));
vi.mock("@/lib/audit", () => ({ writeAudit: vi.fn() }));
vi.mock("@/lib/email", () => ({ deliverReport: vi.fn(), deliverAudioReadyEmail: vi.fn() }));
vi.mock("@/lib/r2", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../r2")>()),
  isR2Configured: () => true,
  presignPutUrl: vi.fn(),
  headObject: vi.fn(),
}));

const { runDispatchTick } = await import("../fulfilment");

const JOB = {
  id: "job_1",
  orderId: "order_1",
  reportId: null,
  kind: "GENERATE" as const,
  state: "RUNNING" as const,
  attempts: 1,
  maxAttempts: 3,
  leaseUntil: new Date("2026-10-26T07:00:00.000Z"),
  worker: "cron-test",
  lastError: null,
  startedAt: new Date("2026-10-26T06:59:00.000Z"),
  finishedAt: null,
  createdAt: new Date("2026-10-26T06:30:00.000Z"),
  payload: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.claimJob.mockReset();
  // One queued job, then nothing: the tick processes exactly one and stops.
  mocks.claimJob.mockResolvedValueOnce(JOB).mockResolvedValue(null);
  // An early terminal outcome (the order row is gone) keeps the test on the real dispatch path
  // without standing up the whole render pipeline.
  mocks.prisma.order.findUnique.mockResolvedValue(null);
  mocks.prisma.job.count.mockResolvedValue(0);
  mocks.failJob.mockResolvedValue(undefined);
  mocks.hasActiveServiceConsent.mockResolvedValue(false);
  mocks.requireActiveServiceConsent.mockRejectedValue(new Error("dispatch must not consult consent"));
});

describe("runDispatchTick — in-flight paid work is not consent-gated (D11)", () => {
  it("still claims and processes a queued job after the owner withdrew service consent", async () => {
    const result = await runDispatchTick(3);

    // The tick claimed the job and began processing it.
    expect(result).toMatchObject({ processed: 1, failed: 1 });
    expect(mocks.claimJob).toHaveBeenCalled();
    expect(mocks.prisma.order.findUnique).toHaveBeenCalledWith(
      expect.objectContaining({ where: { id: "order_1" } }),
    );
    expect(mocks.failJob).toHaveBeenCalled();

    // D11: neither consent helper is consulted anywhere on this path. A future "fix" that adds a
    // gate here would make one of these a call and fail this test.
    expect(mocks.hasActiveServiceConsent).not.toHaveBeenCalled();
    expect(mocks.requireActiveServiceConsent).not.toHaveBeenCalled();
  });
});
