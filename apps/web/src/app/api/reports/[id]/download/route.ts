import { ApiError, handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { presignGetUrl } from "@/lib/r2";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * Download a delivered report.
 *
 * **The web document is the default** (`kind=html`): it is the reading, one self-contained file, so
 * "download the reading" means a single `.html` the client can keep and open anywhere. The PDF is
 * the additional option (`kind=pdf`) — the artefact that matches what the reviewer approved.
 *
 * Ownership is checked first, and a report that is not yet DELIVERED is refused (409): until a human
 * has reviewed it there is nothing to download, and pretending otherwise would break the product
 * promise.
 */
export const GET = handle(async (req, ctx: Ctx) => {
  const user = await requireUser();
  // AU-30 (2026-10-26 audit): a download streams the object through this function for an HTML
  // download or a forced attachment, so it is bandwidth we pay for. 30/minute is far above a
  // person reading their own report (a download or two) and bounds a script.
  await rateLimit(`report-download:${user.id}`, 30, WINDOW.minute);
  const { id } = await ctx.params;

  const kind = new URL(req.url).searchParams.get("kind") === "pdf" ? "pdf" : "html";

  const report = await prisma.report.findFirst({
    where: { id, userId: user.id },
    select: { id: true, status: true, pdfKey: true, htmlKey: true, sha256: true },
  });
  if (!report) throw ApiError.notFound("Report not found");

  if (report.status !== "DELIVERED") {
    throw new ApiError(409, "REPORT_NOT_READY", "This reading is still being reviewed and isn't ready to download yet.");
  }
  // A report rendered before the web document existed has only a PDF. Rather than failing the
  // download, fall back to it: the client asked for their reading, not for a format.
  const useHtml = kind === "html" && Boolean(report.htmlKey);
  const key = useHtml ? report.htmlKey : report.pdfKey;
  if (!key) {
    throw ApiError.notFound("No file for this report");
  }

  const url = await presignGetUrl(key, useHtml ? 600 : 3600);
  const disposition = new URL(req.url).searchParams.get("disposition");

  // Forced download, or any web-document download: stream it so we can control the headers (an R2
  // redirect cannot set them, and the HTML needs a filename, a policy and `noindex`).
  if (disposition === "attachment" || useHtml) {
    const upstream = await fetch(url, { cache: "no-store" });
    if (!upstream.ok || !upstream.body) {
      throw ApiError.unavailable("Could not fetch the report file", "STORAGE_READ_FAILED");
    }
    return new Response(upstream.body, {
      status: 200,
      headers: useHtml
        ? {
            "content-type": "text/html; charset=utf-8",
            "content-disposition": `attachment; filename="cosmic-saju-reading-${report.id.slice(0, 8)}.html"`,
            // The document is self-contained and scriptless; the policy makes that a guarantee
            // rather than a property of today's template.
            "content-security-policy":
              "default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'",
            "x-robots-tag": "noindex, nofollow",
            "x-content-type-options": "nosniff",
            "referrer-policy": "no-referrer",
            "cache-control": "private, no-store",
          }
        : {
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
