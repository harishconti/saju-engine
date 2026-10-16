import { handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { audit } from "@/lib/audit";
import { enqueueAudio } from "@/lib/fulfilment";
import { isTtsConfigured, ttsModel } from "@/lib/tts";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

type Ctx = { params: Promise<{ id: string }> };

/**
 * Prepare or retry the audio summary.
 *
 * Normally queued automatically at approval. This exists for the two cases that need a
 * human: a failed text-to-speech run, and a report approved before the voice was
 * configured.
 */
export const POST = handle(async (_req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;

  const report = await prisma.report.findUnique({
    where: { id },
    select: { id: true, audioStatus: true, mdKey: true, order: { select: { kind: true, tier: true } } },
  });
  if (!report) return json({ error: "Report not found", code: "NOT_FOUND" }, 404);

  if (!isTtsConfigured()) {
    return json(
      { error: "Voice generation is not configured on this deployment", code: "TTS_UNAVAILABLE" },
      503,
    );
  }
  if (!report.mdKey) {
    return json(
      {
        error:
          "This report has no stored source markdown, so no script can be derived. Regenerate it first.",
        code: "NO_SOURCE_MARKDOWN",
      },
      409,
    );
  }

  const queued = await enqueueAudio(report.id);
  if (!queued) {
    return json(
      {
        ok: true,
        queued: false,
        message:
          report.audioStatus === "READY"
            ? "The audio is already ready."
            : report.audioStatus === "PROCESSING" || report.audioStatus === "PENDING"
              ? "The audio is already being prepared."
              : "This reading's tier does not include an audio summary.",
      },
      200,
    );
  }

  await audit({
    entity: "report",
    entityId: report.id,
    action: "update",
    actorId: admin.id,
    after: { audioStatus: "PENDING", ttsModel: ttsModel(), via: "admin-retry" },
  });

  return json({ ok: true, queued: true, message: "Audio queued. It will appear on the client's page when ready." });
});
