import { randomUUID } from "node:crypto";
import type { Job, Order, Profile } from "@prisma/client";
import { prisma } from "./prisma";
import { writeAudit } from "./audit";
import { LEASE_MS, claimJob, completeJob, failJob, requeueJob } from "./queue";
import {
  buildReportKey,
  deleteObjectOrQueue,
  getObjectText,
  headObject,
  isR2Configured,
  presignPutUrl,
  putObject,
  queueObjectDeletion,
} from "./r2";
import {
  ENGINE_CONTRACT_VERSION,
  callEngine,
  chartHash,
  engineKindFor,
  engineScript,
  profileToEngine,
  type EnginePayload,
} from "./engine";
import { isTtsConfigured, synthesise, tierPromisesAudio } from "./tts";
import { autoDelivers } from "./tiers";
import { deliverAudioReadyEmail, deliverReport } from "./email";

/**
 * Fulfilment: render a PDF for an order, verify it, file it as a Report awaiting review.
 *
 * Contract: docs/webapp/05-report-pipeline.md §4
 *
 * Crash-safety comes from the lease, not from this function being careful: if we die mid-render the
 * lease expires and the next dispatcher tick reclaims the job.
 */

export interface DispatchResult {
  processed: number;
  failed: number;
  remaining: number;
}

export interface JobOutcome {
  ok: boolean;
  note: string;
  reportId?: string;
  version?: number;
}

type OrderWithProfiles = Order & { profileA: Profile; profileB: Profile | null };

/** Create a queued job for an order. Returns the job id. */
export async function createJobForOrder(orderId: string, kind: "GENERATE" | "REGENERATE"): Promise<string> {
  const job = await prisma.job.create({ data: { orderId, kind, state: "QUEUED" } });
  return job.id;
}

/**
 * Claim one queued job and process it.
 * Returns processed=false when there was nothing to do.
 */
export async function runOneJob(worker: string): Promise<{ processed: boolean } & JobOutcome> {
  const job = await claimJob(worker);
  if (!job) return { processed: false, ok: true, note: "no job" };
  const outcome = await processClaimedJob(job);
  return { processed: true, ...outcome };
}

/**
 * Claim a SPECIFIC job and process it inline (used by the admin regenerate path so the reviewer sees
 * the new version immediately instead of waiting up to a minute for the dispatcher).
 */
export async function processJobById(jobId: string, worker = "inline"): Promise<JobOutcome> {
  const claimed = await prisma.job.updateMany({
    where: { id: jobId, state: "QUEUED" },
    data: {
      state: "RUNNING",
      attempts: { increment: 1 },
      leaseUntil: new Date(Date.now() + LEASE_MS),
      startedAt: new Date(),
      worker,
    },
  });
  if (claimed.count === 0) return { ok: false, note: "job was not claimable" };

  const job = await prisma.job.findUnique({ where: { id: jobId } });
  if (!job) return { ok: false, note: "job vanished" };
  return processClaimedJob(job);
}

/** The actual work. Assumes the job is already leased to us. */
export async function processClaimedJob(job: Job): Promise<JobOutcome> {
  if (job.kind === "VOICE") return processVoiceJob(job);
  try {
    const order = (await prisma.order.findUnique({
      where: { id: job.orderId },
      include: { profileA: true, profileB: true },
    })) as OrderWithProfiles | null;

    if (!order) {
      await failJob(job.id, "ORDER_MISSING");
      return { ok: false, note: "order missing" };
    }

    if (order.kind === "COMPAT" && !order.profileB) {
      await failJob(job.id, "COMPAT_NEEDS_TWO_PROFILES");
      return { ok: false, note: "compat without second profile" };
    }

    if (!isR2Configured()) {
      // Configuration error, not transient: retrying will not help.
      await failJob(job.id, "STORAGE_NOT_CONFIGURED");
      return { ok: false, note: "R2 not configured" };
    }

    const last = await prisma.report.findFirst({
      where: { orderId: order.id },
      orderBy: { version: "desc" },
      select: { version: true },
    });
    const version = (last?.version ?? 0) + 1;

    // A tier that does not require review is delivered the moment it renders — no queue, no
    // reviewer. See `autoDelivers()`; the free tier is the only one that sets this.
    const autoDeliver = autoDelivers(order.kind, order.tier);

    const reportId = randomUUID();
    const pdfKey = buildReportKey(order.userId, order.id, reportId, "pdf");
    const mdKey = buildReportKey(order.userId, order.id, reportId, "md");

    const profileA = profileToEngine(order.profileA);
    const profileB = order.profileB ? profileToEngine(order.profileB) : null;
    const hash = chartHash(profileA, profileB, order.favorableOverrideA, order.favorableOverrideB);

    const payload: EnginePayload = {
      contractVersion: ENGINE_CONTRACT_VERSION,
      kind: engineKindFor(order),
      tier: order.tier, // stored as the ENGINE tier; `kind` disambiguates
      uploadUrl: await presignPutUrl(pdfKey, "application/pdf"),
      // The source markdown, stored so the audio script is derived from what was approved
      // rather than recomputed from today's engine.
      mdUploadUrl: await presignPutUrl(mdKey, "text/markdown"),
      profileA,
      ...(profileB ? { profileB } : {}),
      favorableOverrideA: order.favorableOverrideA ?? null,
      favorableOverrideB: order.favorableOverrideB ?? null,
    };

    const result = await callEngine(payload);

    // Trust but verify: a 200 without an object would leave a report row pointing at nothing.
    const object = await headObject(pdfKey);
    if (!object) {
      await failJob(job.id, "UPLOAD_NOT_VERIFIED");
      return { ok: false, note: "upload not verified" };
    }

    await prisma.$transaction(async (tx) => {
      await tx.report.create({
        data: {
          id: reportId,
          orderId: order.id,
          userId: order.userId,
          kind: order.kind,
          tier: order.tier,
          version,
          // Decision D5: a paid report is never delivered without review. A tier that
          // declares `requiresReview: false` is the documented exception — and it is read
          // from the tier map rather than hard-coded here, so the field is not a comment.
          status: autoDeliver ? "DELIVERED" : "DRAFT_READY",
          deliveredAt: autoDeliver ? new Date() : null,
          profileAId: order.profileAId,
          profileBId: order.profileBId,
          pdfKey,
          mdKey,
          enginePayload: JSON.parse(JSON.stringify(payload)) as never,
          sha256: result.sha256 ?? null,
          bytes: result.bytes ?? object.size,
          // Shown in the review console. Null rather than guessed when the backend cannot report it.
          pageCount: result.pages ?? null,
          chartHash: hash,
          engineVersion: result.engineVersion ?? null,
        },
      });

      // Supersede undelivered earlier versions; a DELIVERED report is retained, never edited.
      await tx.report.updateMany({
        where: { orderId: order.id, id: { not: reportId }, status: { in: ["DRAFT_READY", "IN_REVIEW"] } },
        data: { status: "SUPERSEDED" },
      });

      if (autoDeliver) {
        // The report is in the client's profile the instant it exists — that IS the delivery.
        await tx.delivery.create({
          data: {
            reportId,
            userId: order.userId,
            kind: "report",
            channel: "PROFILE",
            provider: "profile",
            status: "sent",
            sentAt: new Date(),
          },
        });
      }

      await writeAudit(tx, {
        entity: "report",
        entityId: reportId,
        action: autoDeliver ? "deliver" : "create",
        actorId: null,
        after: { orderId: order.id, version, bytes: result.bytes, autoDelivered: autoDeliver },
      });

      await tx.job.update({
        where: { id: job.id },
        data: {
          payload: JSON.parse(JSON.stringify(payload)),
          state: "SUCCEEDED",
          finishedAt: new Date(),
          leaseUntil: null,
        },
      });
    });

    if (autoDeliver) {
      // After commit, exactly like the approval path: a mail failure must not un-deliver a report.
      await deliverReport(reportId);
      return { ok: true, note: `report v${version} auto-delivered`, reportId, version };
    }

    return { ok: true, note: `report v${version}`, reportId, version };
  } catch (err) {
    const code =
      typeof err === "object" && err !== null && "code" in err
        ? String((err as { code?: string }).code ?? "UNKNOWN")
        : err instanceof Error
          ? err.name
          : "UNKNOWN";

    // A 422 from the engine is permanent: bad birth data will not improve on retry.
    const permanent =
      typeof err === "object" && err !== null && "status" in err && (err as { status?: number }).status === 422;

    if (permanent || job.attempts >= job.maxAttempts) {
      await failJob(job.id, code);
      return { ok: false, note: `failed: ${code}` };
    }
    await requeueJob(job.id, code);
    return { ok: false, note: `retry: ${code}` };
  }
}

/**
 * Produce the audio summary for an approved report.
 *
 * Runs *after* approval, and never blocks delivery — a TTS outage must not hold a reviewed,
 * paid report hostage. The script is derived from the **stored** markdown (the artefact the
 * reviewer approved), not recomputed, so the narration cannot drift from the PDF.
 */
async function processVoiceJob(job: Job): Promise<JobOutcome> {
  try {
    const report = await prisma.report.findUnique({
      where: { id: job.reportId ?? "" },
      include: { order: { select: { userId: true, kind: true, tier: true } }, user: { select: { email: true, name: true } } },
    });
    if (!report) {
      await failJob(job.id, "REPORT_MISSING");
      return { ok: false, note: "report missing" };
    }

    await prisma.report.update({ where: { id: report.id }, data: { audioStatus: "PROCESSING" } });

    if (!isTtsConfigured()) {
      await prisma.report.update({
        where: { id: report.id },
        data: { audioStatus: "FAILED", audioError: "TTS_NOT_CONFIGURED" },
      });
      await failJob(job.id, "TTS_NOT_CONFIGURED");
      return { ok: false, note: "TTS not configured" };
    }
    if (!report.mdKey) {
      await prisma.report.update({
        where: { id: report.id },
        data: { audioStatus: "FAILED", audioError: "NO_SOURCE_MARKDOWN" },
      });
      await failJob(job.id, "NO_SOURCE_MARKDOWN");
      return { ok: false, note: "source markdown missing" };
    }

    const markdown = await getObjectText(report.mdKey);
    if (!markdown) {
      await requeueOrFail(job, "SOURCE_UNREADABLE");
      return { ok: false, note: "source unreadable" };
    }

    const { script, stats } = await engineScript(markdown);
    if (!script.trim()) {
      // The approved text promises no audio summary — not a failure, just nothing to say.
      await prisma.report.update({ where: { id: report.id }, data: { audioStatus: "NONE", script: null } });
      await completeJob(job.id);
      return { ok: true, note: "no audio promised" };
    }

    const { audio, chunks, model } = await synthesise(script);
    const audioKey = buildReportKey(report.userId, report.orderId ?? report.id, report.id, "mp3");
    await putObject(audioKey, audio, "audio/mpeg");

    await prisma.$transaction(async (tx) => {
      await tx.report.update({
        where: { id: report.id },
        data: {
          script,
          audioKey,
          audioBytes: audio.byteLength,
          audioStatus: "READY",
          audioReadyAt: new Date(),
          audioError: null,
        },
      });
      await writeAudit(tx, {
        entity: "report",
        entityId: report.id,
        action: "update",
        actorId: null,
        after: { audioStatus: "READY", audioBytes: audio.byteLength, ttsModel: model, chunks, ...stats },
      });
      await tx.job.update({
        where: { id: job.id },
        data: { state: "SUCCEEDED", finishedAt: new Date(), leaseUntil: null },
      });
    });

    // Tell the client their audio has landed. Best-effort: the PDF is already delivered.
    await deliverAudioReadyEmail({
      to: report.user.email,
      clientName: report.user.name,
      reportId: report.id,
      seconds: stats.estimatedSeconds,
    });

    return { ok: true, note: `audio ready (${audio.byteLength} bytes)` };
  } catch (err) {
    const code =
      typeof err === "object" && err !== null && "code" in err
        ? String((err as { code?: string }).code ?? "TTS_FAILED")
        : err instanceof Error
          ? err.name
          : "TTS_FAILED";
    await requeueOrFail(job, code, job.reportId ? { reportId: job.reportId } : undefined);
    return { ok: false, note: `audio: ${code}` };
  }
}

/** Transient vs permanent, shared by the render and voice paths. */
async function requeueOrFail(job: Job, code: string, extra?: { reportId: string }): Promise<void> {
  const permanent = ["TTS_VOICE_MISSING", "EMPTY_SCRIPT", "NO_SOURCE_MARKDOWN"].includes(code);
  if (extra?.reportId) {
    await prisma.report.update({
      where: { id: extra.reportId },
      data: {
        audioStatus: permanent || job.attempts >= job.maxAttempts ? "FAILED" : "PENDING",
        audioError: code,
      },
    });
  }
  if (permanent || job.attempts >= job.maxAttempts) {
    await failJob(job.id, code);
  } else {
    await requeueJob(job.id, code);
  }
}

/**
 * Queue the audio summary for an approved report.
 *
 * Called at approval, never before: the script derives from the *approved* text. Delivery
 * does not wait for it — the PDF is already in the client's profile by then.
 */
export async function enqueueAudio(reportId: string): Promise<boolean> {
  const report = await prisma.report.findUnique({
    where: { id: reportId },
    include: { order: { select: { kind: true, tier: true } } },
  });
  if (!report?.order || !tierPromisesAudio(report.order)) return false;
  if (report.audioStatus === "READY" || report.audioStatus === "PROCESSING") return false;

  // Narrowing does not survive into the transaction closure, so capture the id first.
  const orderId = report.orderId;
  if (!orderId) return false; // a saved sample has no order to hang a job off

  await prisma.$transaction(async (tx) => {
    // `orderId` is a required FK to Order, so it is the ORDER's id; the report is carried
    // alongside. Storing the report id in orderId violated the foreign key.
    await tx.job.create({
      data: { orderId, reportId, kind: "VOICE", state: "QUEUED" },
    });
    await tx.report.update({ where: { id: reportId }, data: { audioStatus: "PENDING", audioError: null } });
    await writeAudit(tx, {
      entity: "report",
      entityId: reportId,
      action: "update",
      actorId: null,
      after: { audioStatus: "PENDING" },
    });
  });
  return true;
}

/** Drain up to `max` jobs. Deliberately bounded — a tick that overruns the function timeout is the
 *  situation leases exist to survive, but doing three and returning is better. */
export async function runDispatchTick(max = 3): Promise<DispatchResult> {
  const worker = `cron-${randomUUID().slice(0, 8)}`;
  let processed = 0;
  let failed = 0;

  for (let i = 0; i < max; i++) {
    const res = await runOneJob(worker);
    if (!res.processed) break;
    processed++;
    if (!res.ok) failed++;
  }

  const remaining = await prisma.job.count({ where: { state: "QUEUED" } });
  return { processed, failed, remaining };
}

/**
 * Process the caller's own queued jobs, inline.
 *
 * This exists because Vercel Hobby forbids a per-minute cron, so the per-minute dispatcher cannot be
 * the primary trigger (docs/webapp/05-report-pipeline.md §4). The webhook dispatches via `after()`;
 * this is the recovery path a user can trigger themselves from the dashboard when a report is sitting
 * in review longer than expected.
 *
 * Ownership is checked before anything is processed, and the work is scoped to that user's orders.
 */
export async function kickOwnerJobs(userId: string, max = 2): Promise<{ processed: number; generated: number }> {
  const jobs = await prisma.job.findMany({
    where: { state: "QUEUED", order: { userId } },
    orderBy: { createdAt: "asc" },
    take: max,
    select: { id: true },
  });

  let generated = 0;
  for (const job of jobs) {
    const outcome = await processJobById(job.id, `kick-${userId.slice(0, 8)}`);
    if (outcome.ok) generated++;
  }
  return { processed: jobs.length, generated };
}

/** Delete a report row and queue its objects. */
export async function deleteReportArtifacts(reportId: string): Promise<void> {
  const report = await prisma.report.findUnique({
    where: { id: reportId },
    select: { pdfKey: true, mdKey: true, audioKey: true },
  });
  if (!report) return;
  if (report.pdfKey) await deleteObjectOrQueue(report.pdfKey);
  if (report.mdKey) await deleteObjectOrQueue(report.mdKey);
  if (report.audioKey) await deleteObjectOrQueue(report.audioKey);
  await prisma.report.delete({ where: { id: reportId } });
}

export async function queueOrphansForDeletion(keys: string[]): Promise<void> {
  for (const key of keys) await queueObjectDeletion(key, "orphaned");
}
