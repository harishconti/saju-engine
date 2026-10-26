/**
 * A worker that died mid-render is a lost order, and the owner hears about it.
 *
 * AU-03 (2026-10-26 audit) covers every `failJob` on a generate path, not only the ones the
 * dispatcher takes itself. `reclaimStaleJobs` runs from the cleanup cron and fails a job whose
 * lease expired at the last attempt; without this alert it would be the one silent exit left.
 * VOICE jobs are excluded — a TTS stall does not lose a reading (the PDF is already delivered).
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  prisma: { job: { findMany: vi.fn(), update: vi.fn() } },
  notifyOwnerEngineFailure: vi.fn(),
}));

vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/owner-alert", () => ({
  notifyOwnerEngineFailure: mocks.notifyOwnerEngineFailure,
}));

const { reclaimStaleJobs } = await import("@/lib/queue");

beforeEach(() => {
  vi.clearAllMocks();
  mocks.prisma.job.update.mockResolvedValue({});
  mocks.notifyOwnerEngineFailure.mockResolvedValue(true);
});

describe("reclaimStaleJobs", () => {
  it("fails an exhausted generate job and alerts the owner", async () => {
    mocks.prisma.job.findMany.mockResolvedValue([
      { id: "job_1", orderId: "order_1", kind: "GENERATE", attempts: 3, maxAttempts: 3 },
    ]);

    const result = await reclaimStaleJobs();

    expect(result).toEqual({ requeued: 0, failed: 1 });
    expect(mocks.prisma.job.update).toHaveBeenCalledWith({
      where: { id: "job_1" },
      data: expect.objectContaining({ state: "FAILED" }),
    });
    expect(mocks.notifyOwnerEngineFailure).toHaveBeenCalledTimes(1);
    expect(mocks.notifyOwnerEngineFailure).toHaveBeenCalledWith({
      orderId: "order_1",
      code: "LEASE_EXPIRED",
      attempts: 3,
    });
  });

  it("does not alert for a voice job", async () => {
    mocks.prisma.job.findMany.mockResolvedValue([
      { id: "job_2", orderId: "order_1", kind: "VOICE", attempts: 3, maxAttempts: 3 },
    ]);

    await reclaimStaleJobs();

    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
  });

  it("requeues a job that still has attempts left, without alerting", async () => {
    mocks.prisma.job.findMany.mockResolvedValue([
      { id: "job_3", orderId: "order_1", kind: "GENERATE", attempts: 1, maxAttempts: 3 },
    ]);

    const result = await reclaimStaleJobs();

    expect(result).toEqual({ requeued: 1, failed: 0 });
    expect(mocks.prisma.job.update).toHaveBeenCalledWith({
      where: { id: "job_3" },
      data: expect.objectContaining({ state: "QUEUED" }),
    });
    expect(mocks.notifyOwnerEngineFailure).not.toHaveBeenCalled();
  });
});
