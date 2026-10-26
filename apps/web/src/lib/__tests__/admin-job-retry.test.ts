import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";

/**
 * AU-02 (2026-10-26 audit), the UI half: a paid order whose GENERATE job exhausted its attempts
 * during the October outage has no Report, so the regenerate action has nothing to act on. The
 * only recovery was manual SQL.
 *
 * "Retry job" is the narrow, deliberate action: reset the attempts counter and put the existing
 * job back on the queue. It must never fight a job that is already live, and it must say plainly
 * when there is no job to retry.
 */

const { requireAdmin, prismaMock, auditMock } = vi.hoisted(() => ({
  requireAdmin: vi.fn(),
  prismaMock: {
    order: { findUnique: vi.fn() },
    job: { findFirst: vi.fn(), updateMany: vi.fn() },
  },
  auditMock: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({ requireAdmin }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/audit", () => ({ audit: auditMock }));

const { POST } = await import("@/app/api/admin/jobs/retry/route");

function retryRequest(orderId = "o1"): Request {
  return new Request("https://app.test/api/admin/jobs/retry", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ orderId }),
  });
}

const FAILED_JOB = {
  id: "j1",
  state: "FAILED" as const,
  attempts: 3,
  maxAttempts: 3,
  lastError: "ENGINE_FAILED",
};

beforeEach(() => {
  vi.clearAllMocks();
  requireAdmin.mockResolvedValue({ id: "admin-1", role: "ADMIN", email: "owner@test", emailVerified: true });
  prismaMock.order.findUnique.mockResolvedValue({ id: "o1", status: "PAID" });
  // First query: is a job already live? Second: the job to requeue.
  prismaMock.job.findFirst.mockResolvedValueOnce(null).mockResolvedValueOnce(FAILED_JOB);
  prismaMock.job.updateMany.mockResolvedValue({ count: 1 });
});

describe("POST /api/admin/jobs/retry", () => {
  it("requeues a failed job and returns its id", async () => {
    const res = await POST(retryRequest(), undefined as never);

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.jobId).toBe("j1");
    expect(prismaMock.job.updateMany).toHaveBeenCalledWith({
      where: { id: "j1", state: { notIn: ["QUEUED", "RUNNING"] } },
      data: { attempts: 0, state: "QUEUED", lastError: null },
    });
    expect(auditMock).toHaveBeenCalledWith(
      expect.objectContaining({
        entity: "job",
        entityId: "j1",
        action: "update",
        after: expect.objectContaining({ orderId: "o1", state: "QUEUED", attempts: 0 }),
      }),
    );
  });

  it("refuses to touch an order whose job is already live", async () => {
    prismaMock.job.findFirst.mockReset();
    prismaMock.job.findFirst.mockResolvedValueOnce({ id: "j-live" });

    const res = await POST(retryRequest(), undefined as never);

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("JOB_ALREADY_LIVE");
    expect(prismaMock.job.updateMany).not.toHaveBeenCalled();
  });

  it("answers 404 when the order has no job at all", async () => {
    prismaMock.job.findFirst.mockReset();
    prismaMock.job.findFirst.mockResolvedValueOnce(null).mockResolvedValueOnce(null);

    const res = await POST(retryRequest(), undefined as never);

    expect(res.status).toBe(404);
    const body = (await res.json()) as Record<string, unknown>;
    expect(String(body.error)).toMatch(/no job/i);
    expect(prismaMock.job.updateMany).not.toHaveBeenCalled();
  });

  it("does not retry an order that was never paid", async () => {
    prismaMock.order.findUnique.mockResolvedValue({ id: "o1", status: "AWAITING_PAYMENT" });

    const res = await POST(retryRequest(), undefined as never);

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("ORDER_NOT_PAID");
    expect(prismaMock.job.updateMany).not.toHaveBeenCalled();
  });

  it("requires an admin", async () => {
    requireAdmin.mockRejectedValue(ApiError.forbidden());

    const res = await POST(retryRequest(), undefined as never);

    expect(res.status).toBe(403);
    expect(prismaMock.order.findUnique).not.toHaveBeenCalled();
  });
});
