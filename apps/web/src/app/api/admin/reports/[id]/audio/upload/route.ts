import { handle, json, parseJson } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { audit } from "@/lib/audit";
import { buildReportKey, headObject, isR2Configured, presignPutUrl } from "@/lib/r2";
import { deliverAudioReadyEmail } from "@/lib/email";
import { audioUploadCompleteSchema } from "@/lib/validation/schemas";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

type Ctx = { params: Promise<{ id: string }> };

/** Long enough to send a 10 MB file on a slow link, short enough to not be a standing open door. */
const UPLOAD_TTL_SECONDS = 900;

/**
 * Attach an audio summary by hand: `POST` to begin, `PATCH` to finish.
 *
 * **Why two requests.** A Vercel function's request body is capped at ~4.5 MB, and a ten-minute MP3 is
 * around 10 MB, so the file cannot travel through this route. The browser PUTs straight to R2 against a
 * presigned URL — the same pattern the engine already uses for the PDF — and then confirms here. That
 * PUT needs a CORS rule on the bucket; see docs/webapp/07 §CORS (it was documented for months before
 * anyone needed it, and was only actually applied on 2026-10-16).
 *
 * `Prepare audio` on the TTS route is untouched: this covers what it cannot — a hand-recorded
 * narration, a better take, or the MP3 a compatibility customer asks for under the report's cross-sell.
 */
export const POST = handle(async (_req, ctx: Ctx) => {
  await requireAdmin();
  const { id } = await ctx.params;

  if (!isR2Configured()) {
    return json({ error: "Report storage is not configured", code: "STORAGE_UNAVAILABLE" }, 503);
  }

  const report = await prisma.report.findUnique({
    where: { id },
    select: { id: true, userId: true, orderId: true },
  });
  if (!report) return json({ error: "Report not found", code: "NOT_FOUND" }, 404);

  // A saved free sample has no order, so there is nothing for an audio file to belong to.
  if (!report.orderId) {
    return json(
      { error: "This reading has no order, so it cannot carry an audio summary.", code: "NO_ORDER" },
      409,
    );
  }

  const key = buildReportKey(report.userId, report.orderId, report.id, "mp3");
  const uploadUrl = await presignPutUrl(key, "audio/mpeg", UPLOAD_TTL_SECONDS);
  return json({ ok: true, uploadUrl, key, expiresIn: UPLOAD_TTL_SECONDS });
});

export const PATCH = handle(async (req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const input = await parseJson(req, audioUploadCompleteSchema);

  const report = await prisma.report.findUnique({
    where: { id },
    select: {
      id: true,
      userId: true,
      orderId: true,
      status: true,
      audioStatus: true,
      user: { select: { email: true, name: true } },
    },
  });
  if (!report) return json({ error: "Report not found", code: "NOT_FOUND" }, 404);
  if (!report.orderId) {
    return json(
      { error: "This reading has no order, so it cannot carry an audio summary.", code: "NO_ORDER" },
      409,
    );
  }

  // Derive the expected key instead of trusting the one sent: otherwise an admin session could point a
  // report at any object in the bucket.
  const key = buildReportKey(report.userId, report.orderId, report.id, "mp3");
  if (input.key !== key) {
    return json({ error: "That object does not belong to this report.", code: "KEY_MISMATCH" }, 403);
  }

  const object = await headObject(key);
  if (!object) {
    return json({ error: "The upload never reached storage. Please try again.", code: "UPLOAD_NOT_FOUND" }, 409);
  }
  if (object.size === 0) {
    return json({ error: "That file was empty, so nothing was attached.", code: "EMPTY_UPLOAD" }, 422);
  }

  const wasReady = report.audioStatus === "READY";

  await prisma.report.update({
    where: { id },
    data: {
      audioKey: key,
      audioBytes: object.size,
      audioStatus: "READY",
      audioReadyAt: new Date(),
      audioError: null,
    },
  });

  // Email only when it is a genuine change *and* the client can already see the reading — the email
  // links to the report page. An upload made before approval rides along with the delivery email.
  let emailed = false;
  if (report.status === "DELIVERED" && !wasReady) {
    const result = await deliverAudioReadyEmail({
      to: report.user.email,
      clientName: report.user.name,
      reportId: report.id,
      // Unknown length: the sender measured nothing, so the email must not claim a duration.
      seconds: null,
    });
    emailed = result.ok;
  }

  await audit({
    entity: "report",
    entityId: report.id,
    action: "update",
    actorId: admin.id,
    after: { audioStatus: "READY", audioBytes: object.size, via: "admin-upload", emailed },
  });

  return json({
    ok: true,
    bytes: object.size,
    emailed,
    message: emailed
      ? "Audio attached, and the client has been emailed."
      : report.status === "DELIVERED"
        ? "Audio attached — it replaces whatever was there before."
        : "Audio attached. The client will see it the moment the reading is delivered.",
  });
});
