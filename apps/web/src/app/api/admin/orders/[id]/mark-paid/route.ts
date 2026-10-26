import { z } from "zod";
import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

const schema = z.object({ note: z.string().trim().max(200).optional() });

/**
 * Manual payment. Covers three real cases: comps, invoices paid outside the MoR, and the fallback
 * when Dodo Payments rejects or stalls the store.
 *
 * Marks the order paid and queues generation — exactly what the webhook does, minus the signature.
 *
 * Owner decision D11 (2026-10-26): deliberately NOT consent-gated. A withdrawal stops new orders;
 * this payment already exists, so its reading still renders and is delivered.
 */
export const POST = handle(async (req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const { note } = await parseJson(req, schema);

  const order = await prisma.order.findUnique({
    where: { id },
    select: { id: true, status: true, priceCents: true, provider: true },
  });
  if (!order) throw ApiError.notFound("Order not found");

  if (order.status === "PAID") {
    return json({ ok: true, message: "This order is already marked paid.", alreadyPaid: true });
  }
  if (order.status === "REFUNDED" || order.status === "CANCELLED") {
    throw ApiError.conflict("This order is closed", "ORDER_CLOSED");
  }

  const now = new Date();

  const job = await prisma.$transaction(async (tx) => {
    await tx.order.update({
      where: { id: order.id },
      data: { status: "PAID", paidAt: now, provider: order.provider ?? "manual" },
    });

    const created = await tx.job.create({ data: { orderId: order.id, kind: "GENERATE", state: "QUEUED" } });

    await writeAudit(tx, {
      entity: "order",
      entityId: order.id,
      action: "paid",
      actorId: admin.id,
      before: { status: order.status },
      after: { status: "PAID", provider: "manual", note: note ?? null, jobId: created.id },
    });

    return created;
  });

  return json({ ok: true, message: "Marked paid and queued for generation.", jobId: job.id });
});
