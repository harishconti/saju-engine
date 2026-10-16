import { ApiError, handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { presignGetUrl } from "@/lib/r2";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * Download a delivered report.
 *
 * Ownership is checked first, and a report that is not yet DELIVERED is refused (409): until a human
 * has reviewed it there is nothing to download, and pretending otherwise would break the product
 * promise.
 */
export const GET = handle(async (req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;

  const report = await prisma.report.findFirst({
    where: { id, userId: user.id },
    select: { id: true, status: true, pdfKey: true, sha256: true },
  });
  if (!report) throw ApiError.notFound("Report not found");

  if (report.status !== "DELIVERED") {
    throw new ApiError(409, "REPORT_NOT_READY", "This reading is still being reviewed and isn't ready to download yet.");
  }
  if (!report.pdfKey) {
    throw ApiError.notFound("No file for this report");
  }

  const url = await presignGetUrl(report.pdfKey, 3600);
  const disposition = new URL(req.url).searchParams.get("disposition");

  // Forced download: stream it so we can control the headers (an R2 redirect cannot set them).
  if (disposition === "attachment") {
    const upstream = await fetch(url, { cache: "no-store" });
    if (!upstream.ok || !upstream.body) {
      throw ApiError.unavailable("Could not fetch the report file", "STORAGE_READ_FAILED");
    }
    return new Response(upstream.body, {
      status: 200,
      headers: {
        "content-type": "application/octet-stream",
        "content-disposition": `attachment; filename="cosmic-saju-report-${report.id.slice(0, 8)}.pdf"`,
        "x-content-type-options": "nosniff",
        "cache-control": "private, no-store",
        ...(report.sha256 ? { "x-report-sha256": report.sha256 } : {}),
      },
    });
  }

  // Default: hand the browser a short-lived signed URL. Buckets are private, so this is the only
  // way bytes leave storage.
  return new Response(null, {
    status: 302,
    headers: { location: url, "cache-control": "private, no-store" },
  });
});
