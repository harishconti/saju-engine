import { ApiError, handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { chartHash, profileToEngine } from "@/lib/engine";
import { createJobForOrder, processJobById } from "@/lib/fulfilment";
import { audit } from "@/lib/audit";

export const dynamic = "force-dynamic";
// AU-11 (2026-10-26 audit): the engine call may take up to its 120 s default, and this route
// renders inline plus writes the audit row. A 120 s function budget could be exhausted by the
// engine alone, so the reviewer saw a platform timeout instead of the new version.
export const maxDuration = 300;

type Ctx = { params: Promise<{ id: string }> };

/**
 * Regenerate the report for this order with the CURRENT overrides.
 *
 * Runs inline so the reviewer sees the result immediately rather than waiting for the next dispatcher
 * tick. A no-op regenerate (identical chart hash and no override change) is refused with 409 rather
 * than burning a render.
 */
export const POST = handle(async (_req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;

  const report = await prisma.report.findUnique({
    where: { id },
    select: { id: true, orderId: true, chartHash: true, status: true },
  });
  if (!report) throw ApiError.notFound("Report not found");
  if (!report.orderId) throw ApiError.badRequest("This report has no order to regenerate", "NO_ORDER");
  if (report.status === "DELIVERED") {
    throw ApiError.conflict(
      "This report is delivered and immutable. Regenerating would create a new version the client did not pay for — correct the profile and order a fresh reading instead.",
      "REPORT_IMMUTABLE",
    );
  }

  const order = await prisma.order.findUnique({
    where: { id: report.orderId },
    include: { profileA: true, profileB: true },
  });
  if (!order) throw ApiError.notFound("Order not found");

  // Short-circuit a regenerate that would produce identical output.
  const nextHash = chartHash(
    profileToEngine(order.profileA),
    order.profileB ? profileToEngine(order.profileB) : null,
    order.favorableOverrideA,
    order.favorableOverrideB,
  );
  if (nextHash === report.chartHash) {
    throw new ApiError(
      409,
      "NO_CHANGE",
      "Nothing has changed since the last render — no override, no profile edit. Nothing to regenerate.",
    );
  }

  const jobId = await createJobForOrder(order.id, "REGENERATE");

  await audit({
    entity: "order",
    entityId: order.id,
    action: "regenerate",
    actorId: admin.id,
    after: { fromReportId: report.id, jobId },
  });

  const outcome = await processJobById(jobId, `admin-${admin.id.slice(0, 8)}`);

  if (!outcome.ok) {
    return json({ ok: false, message: outcome.note, jobId }, 502);
  }

  return json({
    ok: true,
    message: `Regenerated as version ${outcome.version}.`,
    reportId: outcome.reportId,
    version: outcome.version,
  });
});
