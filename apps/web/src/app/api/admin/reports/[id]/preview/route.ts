import { ApiError, handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { presignGetUrl } from "@/lib/r2";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/** Short-lived signed URL for the inline admin PDF viewer. */
export const GET = handle(async (_req, ctx: Ctx) => {
  await requireAdmin();
  const { id } = await ctx.params;

  const report = await prisma.report.findUnique({ where: { id }, select: { pdfKey: true } });
  if (!report) throw ApiError.notFound("Report not found");
  if (!report.pdfKey) {
    throw new ApiError(409, "NO_ARTIFACT", "This report has no PDF yet — generate it first.");
  }

  // 15 minutes: long enough to read, short enough that a leaked URL is useless.
  const url = await presignGetUrl(report.pdfKey, 900);
  return json({ url, expiresIn: 900 });
});
