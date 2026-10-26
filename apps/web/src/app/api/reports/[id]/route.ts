import { ApiError, handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";
import { deleteReportArtifacts } from "@/lib/fulfilment";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * The client-facing shape of a reading. Deliberately an allow-list, not a spread of the row:
 * AU-26 (2026-10-26 audit) found this route returning the narration `script` and the stored
 * engine payload for an unreviewed draft. A future column must be added here by hand before it
 * can reach a client.
 */
const CLIENT_REPORT_FIELDS = {
  id: true,
  kind: true,
  tier: true,
  version: true,
  status: true,
  pageCount: true,
  bytes: true,
  createdAt: true,
  deliveredAt: true,
  reviewedAt: true,
} as const;

/**
 * Report metadata for its owner.
 *
 * Gated on `DELIVERED` (AU-26): before a human has released the reading, the draft is internal.
 * The dashboard reads the row directly server-side, so this only constrains API clients — the
 * review console never calls it.
 */
export const GET = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;
  const report = await prisma.report.findFirst({
    where: { id, userId: user.id },
    select: CLIENT_REPORT_FIELDS,
  });
  if (!report) throw ApiError.notFound("Report not found");
  if (report.status !== "DELIVERED") {
    throw new ApiError(409, "REPORT_NOT_READY", "This reading is still being reviewed.");
  }
  return json({ report });
});

/**
 * Delete a report and its stored objects.
 * The row is removed; the objects are queued so a storage failure cannot leave a file forever.
 */
export const DELETE = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;

  const report = await prisma.report.findFirst({ where: { id, userId: user.id } });
  if (!report) throw ApiError.notFound("Report not found");

  await prisma.$transaction(async (tx) => {
    await writeAudit(tx, {
      entity: "report",
      entityId: id,
      action: "delete",
      actorId: user.id,
      // AU-02 (2026-10-26 audit): record the order, so the admin recovery list can tell a
      // customer-deleted report from an outage failure without guessing from the actor.
      before: { orderId: report.orderId, tier: report.tier, status: report.status, version: report.version },
    });
  });

  await deleteReportArtifacts(id);

  return json({ ok: true });
});
