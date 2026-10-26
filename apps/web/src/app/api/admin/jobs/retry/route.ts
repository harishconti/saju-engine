import { z } from "zod";
import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { audit } from "@/lib/audit";

export const dynamic = "force-dynamic";

const schema = z.object({ orderId: z.string().trim().min(1) });

/**
 * Retry a paid order's generation job — AU-02 (2026-10-26 audit).
 *
 * The outage left paid orders whose GENERATE job exhausted its attempts and therefore has no
 * Report. Regenerate starts from a report, so it cannot help; this action starts from the job:
 * reset the attempt counter and put the existing row back on the queue.
 *
 * It refuses to fight a job that is already queued or running, and says plainly when there is no
 * job at all (nothing to retry — the order needs `mark-paid` or a fresh job).
 */
export const POST = handle(async (req) => {
  const admin = await requireAdmin();
  const { orderId } = await parseJson(req, schema);

  const order = await prisma.order.findUnique({
    where: { id: orderId },
    select: { id: true, status: true },
  });
  if (!order) throw ApiError.notFound("Order not found");
  if (order.status !== "PAID") {
    throw ApiError.conflict("Only a paid order can be retried", "ORDER_NOT_PAID");
  }

  const live = await prisma.job.findFirst({
    where: { orderId: order.id, state: { in: ["QUEUED", "RUNNING"] } },
    select: { id: true },
  });
  if (live) {
    throw ApiError.conflict("This order already has a live job", "JOB_ALREADY_LIVE");
  }

  const job = await prisma.job.findFirst({
    where: { orderId: order.id, kind: { in: ["GENERATE", "REGENERATE"] } },
    orderBy: { createdAt: "desc" },
    select: { id: true, state: true, attempts: true, lastError: true },
  });
  if (!job) throw ApiError.notFound("This order has no job to retry");

  // Guarded update: another operator may have retried between the reads above.
  const updated = await prisma.job.updateMany({
    where: { id: job.id, state: { notIn: ["QUEUED", "RUNNING"] } },
    data: { attempts: 0, state: "QUEUED", lastError: null },
  });
  if (updated.count === 0) {
    throw ApiError.conflict("This job is already queued or running", "JOB_ALREADY_LIVE");
  }

  await audit({
    entity: "job",
    entityId: job.id,
    action: "update",
    actorId: admin.id,
    before: { orderId: order.id, state: job.state, attempts: job.attempts, lastError: job.lastError },
    after: { orderId: order.id, state: "QUEUED", attempts: 0 },
  });

  return json({
    ok: true,
    jobId: job.id,
    message: "Job requeued. The dispatcher will pick it up on its next tick.",
  });
});
