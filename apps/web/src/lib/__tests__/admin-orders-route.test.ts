import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";

/**
 * AU-02 (2026-10-26 audit): the read-only admin list of paid orders the October outage left
 * unrecoverable — PAID, no Report, no live job.
 *
 * The exclusion that matters most is the customer's own deletion (D5 verification, 2026-10-26):
 * a PAID order whose DRAFT_READY report its owner deleted minutes after it appeared is not a
 * failure, and flagging it for "retry" would be wrong. The deletion audit row does not carry the
 * order id (it was written before this task), so the link is made through the report id the
 * order's own `create`/`deliver` audit rows name.
 */

const { requireAdmin, prismaMock } = vi.hoisted(() => ({
  requireAdmin: vi.fn(),
  prismaMock: {
    order: { findMany: vi.fn() },
    job: { findMany: vi.fn() },
    auditLog: { findMany: vi.fn() },
  },
}));

vi.mock("@/lib/auth", () => ({ requireAdmin }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));

const { GET } = await import("@/app/api/admin/orders/route");

const ORDER = {
  id: "cmvngcbv60007n1wpm8d74f5n",
  kind: "COMPAT" as const,
  tier: "basic",
  paidAt: new Date("2026-10-25T10:00:00.000Z"),
  userId: "user-1",
  profileA: { label: "Me" },
  profileB: { label: "Partner" },
};

const FAILED_JOB = {
  id: "job-1",
  orderId: ORDER.id,
  state: "FAILED" as const,
  attempts: 3,
  maxAttempts: 3,
  lastError: "ENGINE_FAILED",
};

beforeEach(() => {
  vi.clearAllMocks();
  requireAdmin.mockResolvedValue({ id: "admin-1", role: "ADMIN", email: "owner@test", emailVerified: true });
  prismaMock.order.findMany.mockResolvedValue([ORDER]);
  prismaMock.job.findMany.mockResolvedValue([FAILED_JOB]);
  prismaMock.auditLog.findMany.mockResolvedValue([]);
});

describe("GET /api/admin/orders", () => {
  it("requires an admin", async () => {
    requireAdmin.mockRejectedValue(ApiError.forbidden());

    const res = await GET(undefined as never, undefined as never);

    expect(res.status).toBe(403);
    expect(prismaMock.order.findMany).not.toHaveBeenCalled();
  });

  it("asks only for PAID orders with no report and no live job", async () => {
    const res = await GET(undefined as never, undefined as never);

    expect(res.status).toBe(200);
    expect(prismaMock.order.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        where: {
          status: "PAID",
          reports: { none: {} },
          jobs: { none: { state: { in: ["QUEUED", "RUNNING"] } } },
        },
      }),
    );
  });

  it("returns the fields the recovery table needs", async () => {
    const res = await GET(undefined as never, undefined as never);
    const body = (await res.json()) as { orders: Record<string, unknown>[] };

    expect(body.orders).toHaveLength(1);
    expect(body.orders[0]).toMatchObject({
      orderId: ORDER.id,
      kind: "COMPAT",
      tier: "basic",
      paidAt: "2026-10-25T10:00:00.000Z",
      profileLabel: "Me × Partner",
      jobId: "job-1",
      lastError: "ENGINE_FAILED",
    });
  });

  it("excludes an order whose report the customer deleted themselves", async () => {
    // The historical shape: the delete audit has no orderId; the create audit names the order and
    // shares the deleted report's id, which is the link.
    prismaMock.auditLog.findMany.mockResolvedValue([
      { entityId: "report-1", action: "create", actorId: null, before: null, after: { orderId: ORDER.id, version: 1 } },
      { entityId: "report-1", action: "delete", actorId: "user-1", before: { tier: "basic", status: "DRAFT_READY", version: 1 }, after: null },
    ]);

    const res = await GET(undefined as never, undefined as never);
    const body = (await res.json()) as { orders: unknown[] };

    expect(body.orders).toEqual([]);
  });

  it("also honours a delete row that names the order directly", async () => {
    prismaMock.auditLog.findMany.mockResolvedValue([
      { entityId: "report-1", action: "delete", actorId: "user-1", before: { orderId: ORDER.id, tier: "basic" }, after: null },
    ]);

    const res = await GET(undefined as never, undefined as never);
    const body = (await res.json()) as { orders: unknown[] };

    expect(body.orders).toEqual([]);
  });

  it("keeps an order when the deletion belonged to a different report", async () => {
    prismaMock.auditLog.findMany.mockResolvedValue([
      { entityId: "other-report", action: "delete", actorId: "user-1", before: { tier: "essential" }, after: null },
    ]);

    const res = await GET(undefined as never, undefined as never);
    const body = (await res.json()) as { orders: unknown[] };

    expect(body.orders).toHaveLength(1);
  });
});
