/**
 * Every failed render tells the owner.
 *
 * AU-03 (2026-10-26 audit): during the October outage the engine refused every render for five
 * days and nobody was told. The SLA sweep reported counts nobody read, and the health probe lied.
 * This is the direct channel: each time a GENERATE job is failed for good, one email leaves with
 * the engine's error code — never the birth data, never the presigned URL.
 *
 * Two properties are locked here:
 *  - exactly one alert per failed job, carrying the code and the attempt count;
 *  - an alert that itself fails cannot change the job's outcome. A notification problem is never
 *    a delivery problem.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";

const mocks = vi.hoisted(() => ({
  prisma: {
    order: { findUnique: vi.fn() },
    report: { findFirst: vi.fn() },
    $transaction: vi.fn(),
  },
  presignPutUrl: vi.fn(async (key: string) => `https://r2.test/${key}`),
  callEngine: vi.fn(),
  failJob: vi.fn(),
  requeueJob: vi.fn(),
  notifyOwnerEngineFailure: vi.fn(),
  notifyOwnerNewReview: vi.fn(),
}));

vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/r2", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../r2")>()),
  isR2Configured: () => true,
  presignPutUrl: mocks.presignPutUrl,
  headObject: vi.fn(),
}));
vi.mock("@/lib/engine", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../engine")>()),
  callEngine: mocks.callEngine,
}));
vi.mock("@/lib/queue", () => ({
  LEASE_MS: 60_000,
  claimJob: vi.fn(),
  completeJob: vi.fn(),
  failJob: mocks.failJob,
  requeueJob: mocks.requeueJob,
}));
vi.mock("@/lib/owner-alert", () => ({
  notifyOwnerNewReview: mocks.notifyOwnerNewReview,
  notifyOwnerEngineFailure: mocks.notifyOwnerEngineFailure,
}));
vi.mock("@/lib/email", () => ({ deliverReport: vi.fn(), deliverAudioReadyEmail: vi.fn() }));
vi.mock("@/lib/audit", () => ({ writeAudit: vi.fn() }));

const { processClaimedJob } = await import("../fulfilment");

const PROFILE = {
  id: "prof_1",
  fullName: "Priya",
  gender: "F" as const,
  birthDate: new Date("1992-03-20T00:00:00.000Z"),
  birthTime: "14:00",
  timeKnown: true,
  timezone: "Asia/Seoul",
  utcOffset: 9,
  city: "Seoul",
  latitude: 37.5665,
  longitude: 126.978,
};

function order() {
  return {
    id: "order_1",
    userId: "user_1",
    kind: "SINGLE" as const,
    tier: "deep",
    profileAId: "prof_1",
    profileBId: null,
    profileA: PROFILE,
    profileB: null,
    user: { deletedAt: null },
    favorableOverrideA: null,
    favorableOverrideB: null,
  };
}

const JOB = {
  id: "job_1",
  orderId: "order_1",
  kind: "GENERATE" as const,
  attempts: 3,
  maxAttempts: 3,
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.prisma.order.findUnique.mockResolvedValue(order());
  mocks.prisma.report.findFirst.mockResolvedValue(null);
  mocks.prisma.$transaction.mockImplementation(async (fn: (tx: unknown) => Promise<void>) =>
    fn({
      report: { create: vi.fn(), updateMany: vi.fn() },
      delivery: { create: vi.fn() },
      job: { update: vi.fn() },
    }),
  );
  mocks.presignPutUrl.mockImplementation(async (key: string) => `https://r2.test/${key}`);
  mocks.notifyOwnerEngineFailure.mockResolvedValue(true);
  mocks.notifyOwnerNewReview.mockResolvedValue(true);
});

describe("a failed GENERATE job alerts the owner", () => {
  it("sends exactly one alert carrying the engine's code", async () => {
    mocks.callEngine.mockRejectedValue(
      new ApiError(503, "UPLOAD_HOSTS_UNCONFIGURED", "no allowlist", {
        engineStatus: 503,
      }),
    );

    const outcome = await processClaimedJob(JOB as never);

    expect(outcome).toEqual({ ok: false, note: "failed: UPLOAD_HOSTS_UNCONFIGURED" });
    expect(mocks.failJob).toHaveBeenCalledTimes(1);
    // AU-28: the job keeps both the "engine failed" fact and the engine's own code, so the admin
    // "Recent failures" view can show the cause that actually happened.
    expect(mocks.failJob).toHaveBeenCalledWith("job_1", "ENGINE_FAILED:UPLOAD_HOSTS_UNCONFIGURED");
    expect(mocks.notifyOwnerEngineFailure).toHaveBeenCalledTimes(1);
    expect(mocks.notifyOwnerEngineFailure).toHaveBeenCalledWith({
      orderId: "order_1",
      code: "UPLOAD_HOSTS_UNCONFIGURED",
      attempts: 3,
    });
  });

  it("alerts on the early permanent failures too", async () => {
    mocks.prisma.order.findUnique.mockResolvedValue(null);

    const outcome = await processClaimedJob(JOB as never);

    expect(outcome).toEqual({ ok: false, note: "order missing" });
    expect(mocks.notifyOwnerEngineFailure).toHaveBeenCalledWith({
      orderId: "order_1",
      code: "ORDER_MISSING",
      attempts: 3,
    });
  });

  it("does not alert while a job can still be retried", async () => {
    // A transport failure never reached the engine, so there is no engine code to prefix.
    mocks.callEngine.mockRejectedValue(new ApiError(503, "ENGINE_UNREACHABLE", "unreachable"));

    const retryable = { ...JOB, attempts: 1 };
    const outcome = await processClaimedJob(retryable as never);

    expect(outcome).toEqual({ ok: false, note: "retry: ENGINE_UNREACHABLE" });
    expect(mocks.requeueJob).toHaveBeenCalledWith("job_1", "ENGINE_UNREACHABLE");
    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
  });

  it("records the engine's own code on a retry too", async () => {
    mocks.callEngine.mockRejectedValue(
      new ApiError(503, "UPLOAD_HOSTS_UNCONFIGURED", "no allowlist", { engineStatus: 503 }),
    );

    const outcome = await processClaimedJob({ ...JOB, attempts: 1 } as never);

    expect(outcome).toEqual({ ok: false, note: "retry: UPLOAD_HOSTS_UNCONFIGURED" });
    expect(mocks.requeueJob).toHaveBeenCalledWith("job_1", "ENGINE_FAILED:UPLOAD_HOSTS_UNCONFIGURED");
  });

  it("an alert that fails never changes the job outcome", async () => {
    mocks.callEngine.mockRejectedValue(
      new ApiError(503, "UPLOAD_HOSTS_UNCONFIGURED", "no allowlist", {
        engineStatus: 503,
      }),
    );
    mocks.notifyOwnerEngineFailure.mockRejectedValue(new Error("resend is down"));

    const outcome = await processClaimedJob(JOB as never);

    expect(outcome).toEqual({ ok: false, note: "failed: UPLOAD_HOSTS_UNCONFIGURED" });
    expect(mocks.failJob).toHaveBeenCalledWith("job_1", "ENGINE_FAILED:UPLOAD_HOSTS_UNCONFIGURED");
  });
});
