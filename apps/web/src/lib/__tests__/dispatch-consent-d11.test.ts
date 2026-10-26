import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api";

/**
 * Owner decision D11 (2026-10-26): withdrawing service consent stops NEW orders and NEW jobs, but
 * work already paid for is still produced and delivered. The dispatcher is therefore deliberately
 * NOT consent-gated — a gate there would strand a paid order whose owner withdrew after paying.
 *
 * This test exists to stop a future reader "fixing" that absence. It drives the real
 * `runDispatchTick` over a queued job, past the order fetch and into the engine call, and fails if
 * the dispatch path ever consults consent.
 */

const mocks = vi.hoisted(() => ({
  claimJob: vi.fn(),
  failJob: vi.fn(),
  callEngine: vi.fn(),
  hasActiveServiceConsent: vi.fn(),
  requireActiveServiceConsent: vi.fn(),
  prisma: {
    job: { count: vi.fn() },
    order: { findUnique: vi.fn() },
    report: { findFirst: vi.fn() },
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
vi.mock("@/lib/engine", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../engine")>()),
  // The pipeline must reach this call; its refusal is attributed to the engine, not to consent.
  callEngine: mocks.callEngine,
}));
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

const ORDER = {
  id: "order_1",
  userId: "user_1",
  kind: "SINGLE" as const,
  tier: "essential",
  status: "PAID" as const,
  priceCents: 1900,
  currency: "USD",
  provider: "manual",
  providerOrderId: null,
  providerCheckoutId: null,
  paidAt: new Date("2026-10-01T00:00:00.000Z"),
  profileAId: "profile_1",
  profileBId: null,
  favorableOverrideA: null,
  favorableOverrideB: null,
  idempotencyKey: null,
  createdAt: new Date("2026-10-01T00:00:00.000Z"),
  updatedAt: new Date("2026-10-01T00:00:00.000Z"),
  // The pipeline reads these; the exact values are irrelevant to the consent assertion.
  profileA: {
    id: "profile_1",
    userId: "user_1",
    label: "Me",
    fullName: "Test Person",
    gender: "F" as const,
    birthDate: new Date("1990-01-01T00:00:00.000Z"),
    birthTime: "12:00",
    timezone: "Asia/Seoul",
    utcOffset: 9,
    city: "Seoul",
    country: "KR",
    latitude: 37.5665,
    longitude: 126.978,
    timeKnown: true,
    isDefault: true,
    chartJson: null,
    chartComputedAt: null,
    createdAt: new Date("2026-10-01T00:00:00.000Z"),
    updatedAt: new Date("2026-10-01T00:00:00.000Z"),
    deletedAt: null,
  },
  profileB: null,
  user: { deletedAt: null },
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.claimJob.mockReset();
  // One queued job, then nothing: the tick processes exactly one and stops.
  mocks.claimJob.mockResolvedValueOnce(JOB).mockResolvedValue(null);
  // A real order, so the pipeline runs past the fetch and reaches the engine call. The engine
  // refusal (a permanent 422) ends the run as an engine failure, attributed to the engine.
  mocks.prisma.order.findUnique.mockResolvedValue(ORDER);
  mocks.prisma.report.findFirst.mockResolvedValue(null);
  mocks.prisma.job.count.mockResolvedValue(0);
  mocks.failJob.mockResolvedValue(undefined);
  mocks.callEngine.mockRejectedValue(new ApiError(422, "INVALID_BIRTH_DATE", "Stub engine refusal"));
  mocks.hasActiveServiceConsent.mockResolvedValue(false);
  mocks.requireActiveServiceConsent.mockRejectedValue(new Error("dispatch must not consult consent"));
});

describe("runDispatchTick — in-flight paid work is not consent-gated (D11)", () => {
  it("still claims and processes a queued job after the owner withdrew service consent", async () => {
    const result = await runDispatchTick(3);

    // The tick claimed the job and processed it all the way to the engine call.
    expect(result).toMatchObject({ processed: 1, failed: 1 });
    expect(mocks.claimJob).toHaveBeenCalled();
    expect(mocks.prisma.order.findUnique).toHaveBeenCalledWith(
      expect.objectContaining({ where: { id: "order_1" } }),
    );
    expect(mocks.callEngine).toHaveBeenCalled();
    // The failure is the engine's, not a consent refusal.
    expect(mocks.failJob).toHaveBeenCalledWith(JOB.id, "INVALID_BIRTH_DATE");

    // D11: the consent module is never consulted anywhere on this path — not before the order
    // fetch and not after it, where a future "fix" would most naturally add a gate. Either call
    // here would fail this test.
    expect(mocks.hasActiveServiceConsent).not.toHaveBeenCalled();
    expect(mocks.requireActiveServiceConsent).not.toHaveBeenCalled();
  });
});
