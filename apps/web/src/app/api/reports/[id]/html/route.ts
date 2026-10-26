import { ApiError, handle } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { presignGetUrl } from "@/lib/r2";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * The reading itself: the stored web document, served as a page.
 *
 * This is what a client opens — the audit's own recommendation is that the web report is what people
 * *read* and the PDF is the keepsake they keep. The document is one self-contained file (inline CSS
 * and SVG, no scripts, no webfonts, no external requests), which is why it can be streamed straight
 * through with a strict response policy rather than hosted anywhere else:
 *
 *   - `default-src 'none'` — nothing loads. Inline `style-src` is all the document needs; `img-src
 *     data:` covers the inline SVG if a browser treats it as an image. A script injected into a
 *     report could not run even if a future template tried.
 *   - `noindex` in both the document and the header: the link is private, but a reader's report must
 *     never be indexable.
 *   - `private, no-store`: it is personal data and it is not cached by anything in between.
 *   - Ownership and delivery state are checked exactly as for a download: a report still in review
 *     has nothing to show, and saying otherwise would break the product promise.
 */
export const GET = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  // AU-30 (2026-10-26 audit): opening the reading streams the document through this function.
  // 60/minute covers a page and a few reloads; it is higher than the download limit because
  // reading is the primary action and a refresh must not be refused.
  await rateLimit(`report-html:${user.id}`, 60, WINDOW.minute);
  const { id } = await ctx.params;

  const report = await prisma.report.findFirst({
    where: { id, userId: user.id },
    select: { id: true, status: true, htmlKey: true },
  });
  if (!report) throw ApiError.notFound("Report not found");

  if (report.status !== "DELIVERED") {
    throw new ApiError(
      409,
      "REPORT_NOT_READY",
      "This reading is still being reviewed and isn't ready to open yet.",
    );
  }
  if (!report.htmlKey) {
    // Only one reason remains: the report was rendered before the web document existed. A clear 404
    // lets the UI fall back to the PDF rather than showing an empty page.
    throw new ApiError(
      404,
      "NO_WEB_DOCUMENT",
      "This reading has no web version; download the PDF instead.",
    );
  }

  const url = await presignGetUrl(report.htmlKey, 600);
  const upstream = await fetch(url, { cache: "no-store" });
  if (!upstream.ok || !upstream.body) {
    throw ApiError.unavailable("Could not open this reading", "STORAGE_READ_FAILED");
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "content-security-policy":
        "default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'",
      "x-robots-tag": "noindex, nofollow",
      "x-content-type-options": "nosniff",
      "referrer-policy": "no-referrer",
      "cache-control": "private, no-store",
    },
  });
});
