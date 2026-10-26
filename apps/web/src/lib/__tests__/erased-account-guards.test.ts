import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Erasure (D2) keeps order rows for accounting, so a paid order and its jobs can outlive the
 * customer's request. Generation must nevertheless never run for an erased person, on any path.
 *
 * The admin retry route refuses them (Task 4 requirement 5), but queued jobs reach the dispatcher,
 * the inline regenerate worker and the voice pipeline directly. These tests pin the guard in
 * `processClaimedJob` and `processVoiceJob`: fail with `ACCOUNT_ERASED`, run no engine/TTS work,
 * and stay silent — an erased account's job is not an outage and must not page the owner.
 */

const mocks = vi.hoisted(() => ({
  prisma: {
    order: { findUnique: vi.fn() },
    report: { findUnique: vi.fn(), findFirst: vi.fn(), update: vi.fn() },
    $transaction: vi.fn(),
  },
  presignPutUrl: vi.fn(async (key: string) => `https://r2.test/${key}`),
  callEngine: vi.fn(),
  engineScript: vi.fn(),
  synthesise: vi.fn(),
  failJob: vi.fn(),
  requeueJob: vi.fn(),
  completeJob: vi.fn(),
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
  engineScript: mocks.engineScript,
}));
vi.mock("@/lib/tts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../tts")>()),
  synthesise: mocks.synthesise,
}));
vi.mock("@/lib/queue", () => ({
  LEASE_MS: 60_000,
  claimJob: vi.fn(),
  completeJob: mocks.completeJob,
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

const ERASED_AT = new Date("2026-10-20T00:00:00.000Z");

const JOB = {
  id: "job_1",
  orderId: "order_1",
  kind: "GENERATE" as const,
  attempts: 1,
  maxAttempts: 3,
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("generation for an erased account", () => {
  it("fails the generate job with ACCOUNT_ERASED and never calls the engine or the owner", async () => {
    mocks.prisma.order.findUnique.mockResolvedValue({
      id: "order_1",
      userId: "user_1",
      kind: "SINGLE",
      tier: "deep",
      profileAId: "prof_1",
      profileBId: null,
      profileA: { id: "prof_1" },
      profileB: null,
      user: { deletedAt: ERASED_AT },
    });

    const outcome = await processClaimedJob(JOB as never);

    expect(outcome).toEqual({ ok: false, note: "account erased" });
    expect(mocks.failJob).toHaveBeenCalledWith("job_1", "ACCOUNT_ERASED");
    expect(mocks.callEngine).not.toHaveBeenCalled();
    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
    expect(mocks.requeueJob).not.toHaveBeenCalled();
  });

  it("asks the database for the order's account state", async () => {
    mocks.prisma.order.findUnique.mockResolvedValue({
      id: "order_1",
      userId: "user_1",
      kind: "SINGLE",
      tier: "deep",
      profileAId: "prof_1",
      profileBId: null,
      profileA: { id: "prof_1" },
      profileB: null,
      user: { deletedAt: ERASED_AT },
    });

    await processClaimedJob(JOB as never);

    expect(mocks.prisma.order.findUnique).toHaveBeenCalledWith({
      where: { id: "order_1" },
      include: {
        profileA: true,
        profileB: true,
        user: { select: { deletedAt: true } },
      },
    });
  });
});

describe("voice for an erased account", () => {
  it("fails the voice job with ACCOUNT_ERASED and does no TTS work or owner alert", async () => {
    const voiceJob = { ...JOB, kind: "VOICE" as const, reportId: "report_1" };
    mocks.prisma.report.findUnique.mockResolvedValue({
      id: "report_1",
      userId: "user_1",
      orderId: "order_1",
      mdKey: "reports/u/o/report_1.md",
      user: { email: "deleted+u1@deleted.invalid", name: "Deleted user", deletedAt: ERASED_AT },
    });

    const outcome = await processClaimedJob(voiceJob as never);

    expect(outcome).toEqual({ ok: false, note: "account erased" });
    expect(mocks.failJob).toHaveBeenCalledWith("job_1", "ACCOUNT_ERASED");
    expect(mocks.engineScript).not.toHaveBeenCalled();
    expect(mocks.synthesise).not.toHaveBeenCalled();
    expect(mocks.prisma.report.update).not.toHaveBeenCalled();
    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
  });
});
