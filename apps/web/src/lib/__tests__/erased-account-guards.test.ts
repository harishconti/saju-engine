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
  headObject: vi.fn(),
  deleteObjectOrQueue: vi.fn(async (_key: string) => undefined),
  callEngine: vi.fn(),
  engineScript: vi.fn(),
  synthesise: vi.fn(),
  failJob: vi.fn(),
  requeueJob: vi.fn(),
  completeJob: vi.fn(),
  notifyOwnerEngineFailure: vi.fn(),
  notifyOwnerNewReview: vi.fn(),
  // The transaction client for the report write. `user.findUnique` is the re-read that closes the
  // window between the pre-engine check and the commit.
  tx: {
    user: { findUnique: vi.fn() },
    report: { create: vi.fn(), updateMany: vi.fn() },
    delivery: { create: vi.fn() },
    job: { update: vi.fn() },
  },
}));

vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/r2", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../r2")>()),
  isR2Configured: () => true,
  presignPutUrl: mocks.presignPutUrl,
  headObject: mocks.headObject,
  // The queue-delete the erasure branch uses for artefacts the engine already uploaded.
  deleteObjectOrQueue: mocks.deleteObjectOrQueue,
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

describe("an erasure that commits while a render is in flight", () => {
  const RENDER_JOB = {
    id: "job_1",
    orderId: "order_1",
    kind: "GENERATE" as const,
    attempts: 1,
    maxAttempts: 3,
  };

  function renderableOrder() {
    return {
      id: "order_1",
      userId: "user_1",
      kind: "SINGLE" as const,
      tier: "deep",
      profileAId: "prof_1",
      profileBId: null,
      profileA: {
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
      },
      profileB: null,
      // The check at the top of the render passed: the account was not erased then.
      user: { deletedAt: null },
      favorableOverrideA: null,
      favorableOverrideB: null,
    };
  }

  beforeEach(() => {
    mocks.prisma.order.findUnique.mockResolvedValue(renderableOrder());
    mocks.prisma.report.findFirst.mockResolvedValue(null);
    mocks.prisma.$transaction.mockImplementation(async (fn: (tx: unknown) => Promise<unknown>) =>
      fn(mocks.tx),
    );
    mocks.headObject.mockResolvedValue({ size: 1234 });
    mocks.deleteObjectOrQueue.mockResolvedValue(undefined);
    mocks.callEngine.mockResolvedValue({
      sha256: "a".repeat(64),
      bytes: 4096,
      pages: 7,
      engineVersion: "0.2.0",
      htmlBytes: null,
    });
  });

  it("aborts the report write, writes no Report and fails the job with ACCOUNT_ERASED", async () => {
    // Erasure committed after `processClaimedJob` read the order, before this transaction. The
    // report row would carry `enginePayload` (full birth data) and the R2 keys, and its uploads
    // would already be in storage — so the write has to be refused here, under the transaction.
    mocks.tx.user.findUnique.mockResolvedValue({ deletedAt: ERASED_AT });

    const outcome = await processClaimedJob(RENDER_JOB as never);

    expect(outcome).toEqual({ ok: false, note: "account erased" });
    expect(mocks.tx.user.findUnique).toHaveBeenCalledWith({
      where: { id: "user_1" },
      select: { deletedAt: true },
    });
    expect(mocks.tx.report.create).not.toHaveBeenCalled();
    expect(mocks.tx.job.update).not.toHaveBeenCalled();
    // Terminal: one FAILED row, no retries, and no owner page — an erased account is not an outage.
    expect(mocks.failJob).toHaveBeenCalledWith("job_1", "ACCOUNT_ERASED");
    expect(mocks.requeueJob).not.toHaveBeenCalled();
    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
    // The PDF and markdown were uploaded before the write; the HTML was not (`htmlBytes: null`), so
    // its key is not queued. Only objects this render actually created may be touched.
    const keys = (mocks.deleteObjectOrQueue.mock.calls as unknown as Array<[string]>).map(
      (call) => call[0],
    );
    expect(keys.filter((key) => key.endsWith(".pdf"))).toHaveLength(1);
    expect(keys.filter((key) => key.endsWith(".md"))).toHaveLength(1);
    expect(keys.filter((key) => key.endsWith(".html"))).toHaveLength(0);
  });

  it("deletes every artefact the engine already uploaded, once per key", async () => {
    // Erasure committed during the render. The engine has PUT the PDF, the markdown and the HTML;
    // with the write refused there is no Report row, and erasure finds objects only through report
    // rows — so nothing would ever reach these three again.
    mocks.tx.user.findUnique.mockResolvedValue({ deletedAt: ERASED_AT });
    mocks.callEngine.mockResolvedValue({
      sha256: "a".repeat(64),
      bytes: 4096,
      pages: 7,
      engineVersion: "0.2.0",
      htmlBytes: 4096,
    });

    const outcome = await processClaimedJob(RENDER_JOB as never);

    expect(outcome).toEqual({ ok: false, note: "account erased" });
    expect(mocks.deleteObjectOrQueue).toHaveBeenCalledTimes(3);
    const keys = (mocks.deleteObjectOrQueue.mock.calls as unknown as Array<[string]>).map(
      (call) => call[0],
    );
    for (const suffix of [".pdf", ".md", ".html"]) {
      expect(keys.filter((key) => key.endsWith(suffix))).toHaveLength(1);
    }
    for (const key of keys) {
      expect(key).toMatch(/^reports\/user_1\/order_1\/[0-9a-f-]{36}\./);
    }
    // Still terminal: a cleanup failure must not convert the refusal into a retry or a page.
    expect(mocks.failJob).toHaveBeenCalledWith("job_1", "ACCOUNT_ERASED");
    expect(mocks.requeueJob).not.toHaveBeenCalled();
    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
  });

  it("keeps the terminal ACCOUNT_ERASED outcome when the artefact cleanup throws", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    mocks.tx.user.findUnique.mockResolvedValue({ deletedAt: ERASED_AT });
    mocks.deleteObjectOrQueue.mockRejectedValue(new Error("r2 is down"));

    const outcome = await processClaimedJob(RENDER_JOB as never);

    // `deleteObjectOrQueue` already queues on a live failure; here it throws outright, and even
    // that must not change the job's outcome.
    expect(outcome).toEqual({ ok: false, note: "account erased" });
    expect(mocks.failJob).toHaveBeenCalledWith("job_1", "ACCOUNT_ERASED");
    expect(mocks.requeueJob).not.toHaveBeenCalled();
    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
    expect(consoleError).toHaveBeenCalled();
    // The log carries the error class only — never a key, never PII.
    const logged = consoleError.mock.calls
      .flat()
      .map((arg) => (typeof arg === "string" ? arg : String(arg)))
      .join(" ");
    expect(logged).toContain("Error");
    expect(logged).not.toContain("reports/user_1");
    consoleError.mockRestore();
  });

  it("writes the report when the account is still live at commit time", async () => {
    mocks.tx.user.findUnique.mockResolvedValue({ deletedAt: null });

    const outcome = await processClaimedJob(RENDER_JOB as never);

    expect(outcome.ok).toBe(true);
    expect(mocks.tx.report.create).toHaveBeenCalledTimes(1);
    // The live path keeps its artefacts; the erasure cleanup is not reached.
    expect(mocks.deleteObjectOrQueue).not.toHaveBeenCalled();
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
