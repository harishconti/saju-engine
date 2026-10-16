import { ApiError, handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";
import { deleteReportArtifacts } from "@/lib/fulfilment";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

export const GET = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;
  const report = await prisma.report.findFirst({ where: { id, userId: user.id } });
  if (!report) throw ApiError.notFound("Report not found");
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
      before: { tier: report.tier, status: report.status, version: report.version },
    });
  });

  await deleteReportArtifacts(id);

  return json({ ok: true });
});
