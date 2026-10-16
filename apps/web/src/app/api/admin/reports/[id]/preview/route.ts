import { ApiError, handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { presignGetUrl } from "@/lib/r2";
import { isPreviewProblem, previewKeyFor } from "@/lib/report-artifacts";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * Short-lived signed URL for an inline preview, of **either** artefact.
 *
 * `kind=pdf` (the default, so existing callers keep working) signs the PDF; `kind=html` signs the
 * web document — the reading, which is what the reviewer should read first now that it exists. The
 * decision of which key to sign, and the reason when one is missing, lives in
 * `lib/report-artifacts.ts` so it is unit-tested rather than buried in here.
 */
export const GET = handle(async (req, ctx: Ctx) => {
  await requireAdmin();
  const { id } = await ctx.params;

  const kind = new URL(req.url).searchParams.get("kind") === "html" ? "html" : "pdf";

  const report = await prisma.report.findUnique({
    where: { id },
    select: { pdfKey: true, htmlKey: true },
  });
  if (!report) throw ApiError.notFound("Report not found");

  const target = previewKeyFor(report, kind);
  if (isPreviewProblem(target)) {
    throw new ApiError(target.status, target.code, target.message);
  }

  // 15 minutes: long enough to read, short enough that a leaked URL is useless.
  const url = await presignGetUrl(target.key, 900);
  return json({ url, expiresIn: 900, kind });
});
