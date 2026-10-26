import { ApiError, handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { presignGetUrl } from "@/lib/r2";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * Download the audio summary.
 *
 * The MP3 is produced *after* approval, so unlike the PDF this can legitimately be missing
 * while the report is already delivered. Each state gets its own status code so the UI can
 * say something true instead of showing a broken player:
 *
 *   200/302 ready      · 409 still being prepared · 404 this tier has no audio · 503 failed
 */
export const GET = handle(async (req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;

  const report = await prisma.report.findFirst({
    where: { id, userId: user.id },
    // AU-26: no `script` — this path never renders it, and the allow-list rule is "select what you
    // return", so an unused column is one more place an unreviewed draft could start leaking from.
    select: { status: true, audioStatus: true, audioKey: true, audioBytes: true },
  });
  if (!report) throw ApiError.notFound("Report not found");

  // The audio belongs to a delivered reading. Handing it over earlier would leak an
  // unreviewed narration.
  if (report.status !== "DELIVERED") {
    throw new ApiError(409, "REPORT_NOT_READY", "This reading is still being reviewed.");
  }

  switch (report.audioStatus) {
    case "READY": {
      if (!report.audioKey) throw new ApiError(503, "AUDIO_UNAVAILABLE", "The audio is unavailable.");
      const url = await presignGetUrl(report.audioKey, 3600);
      if (new URL(req.url).searchParams.get("disposition") === "attachment") {
        const upstream = await fetch(url, { cache: "no-store" });
        if (!upstream.ok || !upstream.body) {
          throw ApiError.unavailable("Could not fetch the audio file", "STORAGE_READ_FAILED");
        }
        return new Response(upstream.body, {
          status: 200,
          headers: {
            "content-type": "audio/mpeg",
            "content-disposition": `attachment; filename="cosmic-saju-audio-${id.slice(0, 8)}.mp3"`,
            "x-content-type-options": "nosniff",
            "cache-control": "private, no-store",
          },
        });
      }
      return new Response(null, { status: 302, headers: { location: url, "cache-control": "private, no-store" } });
    }
    case "PENDING":
    case "PROCESSING":
      throw new ApiError(409, "AUDIO_NOT_READY", "Your audio summary is still being prepared.");
    case "FAILED":
      throw ApiError.unavailable("The audio summary could not be produced", "AUDIO_FAILED");
    default:
      throw ApiError.notFound("This reading has no audio summary");
  }
});

/**
 * The narration text, for anyone who would rather read it (and for audit).
 *
 * Same delivery gate as the MP3 itself (AU-26): the script is the reviewed reading spoken aloud,
 * so returning it for a draft would expose unreviewed content through a second door.
 */
export const POST = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;
  const report = await prisma.report.findFirst({
    where: { id, userId: user.id },
    select: { status: true, script: true, audioStatus: true },
  });
  if (!report) throw ApiError.notFound("Report not found");
  if (report.status !== "DELIVERED") {
    throw new ApiError(409, "REPORT_NOT_READY", "This reading is still being reviewed.");
  }
  return json({ script: report.script, audioStatus: report.audioStatus });
});
