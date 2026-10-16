import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";
import { overrideSchema } from "@/lib/validation/schemas";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * Set or clear the reader's favourable-element (용신) override on the order.
 *
 * This is the console's headline feature: the engine derives 용신 heuristically and records its
 * provenance; a reader who has argued a different element imposes it here, and the report re-derives
 * consistently — including the "What This Year Means for You" callout, which reads the same resolved
 * value (the two-channel bug class is already closed in the engine).
 *
 * Saving an override does NOT change an existing report. It takes effect on the next regenerate, so a
 * delivered report is never rewritten.
 */
export const POST = handle(async (req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;

  const report = await prisma.report.findUnique({ where: { id }, select: { id: true, orderId: true, kind: true } });
  if (!report) throw ApiError.notFound("Report not found");
  if (!report.orderId) {
    throw ApiError.badRequest("This report has no order, so it has no overrides to set", "NO_ORDER");
  }

  const input = await parseJson(req, overrideSchema);

  const order = await prisma.order.findUnique({
    where: { id: report.orderId },
    select: { favorableOverrideA: true, favorableOverrideB: true },
  });

  const nextB = report.kind === "COMPAT" ? (input.favorableOverrideB ?? null) : null;

  await prisma.$transaction(async (tx) => {
    await tx.order.update({
      where: { id: report.orderId! },
      data: { favorableOverrideA: input.favorableOverrideA ?? null, favorableOverrideB: nextB },
    });

    await writeAudit(tx, {
      entity: "order",
      entityId: report.orderId!,
      action: "override",
      actorId: admin.id,
      before: { a: order?.favorableOverrideA ?? null, b: order?.favorableOverrideB ?? null },
      after: { a: input.favorableOverrideA ?? null, b: nextB },
    });
  });

  return json({
    ok: true,
    message: "Override saved. Regenerate to apply it to the report.",
    favorableOverrideA: input.favorableOverrideA ?? null,
    favorableOverrideB: nextB,
  });
});
