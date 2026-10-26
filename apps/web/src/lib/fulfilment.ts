import { randomUUID } from "node:crypto";
import type { Job, Order, Profile } from "@prisma/client";
import { ApiError } from "./api";
import { prisma } from "./prisma";
import { writeAudit } from "./audit";
import { LEASE_MS, claimJob, completeJob, failJob, recordAttempt, requeueJob } from "./queue";
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
import { autoDelivers, tierNameFor } from "./tiers";
import { deliverAudioReadyEmail, deliverReport } from "./email";
import { notifyOwnerEngineFailure, notifyOwnerNewReview } from "./owner-alert";

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
  /**
   * False when this call never ran the job — another dispatcher had already claimed it. The caller
   * must not report that as a failure: nothing here broke, the work is moving somewhere else.
   */
  ran?: boolean;
}

/**
 * How a claim is accounted.
 *
 * `countAttempt` defaults to true, which is the dispatcher's accounting: claiming a job spends one
 * of its `maxAttempts`. A customer's "Check for updates" passes false (AU-12, 2026-10-26 audit):
 * during the October outage every click hit a fast 5xx, and two clicks could push a paid job to
 * `maxAttempts` and fail it for good — the customer's own recovery attempt killed their order.
 * A run that ends in a terminal failure still records the attempt; it really did happen.
 */
export interface ClaimOptions {
  countAttempt?: boolean;
}

type OrderWithProfiles = Order & {
  profileA: Profile;
  profileB: Profile | null;
  user: { deletedAt: Date | null };
};

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
 * the new version immediately instead of waiting up to 15 minutes for the scheduled dispatcher).
 *
 * `opts.countAttempt: false` is the customer-triggered check: it runs the job without spending one
 * of its retries unless the run ends in a terminal failure (AU-12).
 */
export async function processJobById(
  jobId: string,
  worker = "inline",
  opts: ClaimOptions = {},
): Promise<JobOutcome> {
  const claimed = await claimJobById(jobId, worker, opts);
  if (!claimed.matched) return { ok: false, note: "job was not claimable", ran: false };
  if (!claimed.job) return { ok: false, note: "job vanished", ran: false };
  return processClaimedJob(claimed.job, opts);
}

/**
 * Move a specific QUEUED job to RUNNING under a lease.
 *
 * `matched: false` means the row was no longer QUEUED — another dispatcher got it first, or it was
 * cancelled. `job: null` with `matched: true` means the row disappeared between the claim and the
 * read, which should not happen and is worth its own note.
 */
async function claimJobById(
  jobId: string,
  worker: string,
  opts: ClaimOptions,
): Promise<{ matched: boolean; job: Job | null }> {
  const claimed = await prisma.job.updateMany({
    where: { id: jobId, state: "QUEUED" },
    data: {
      state: "RUNNING",
      // AU-12: a customer check claims the job exactly like the dispatcher, but its attempt is only
      // recorded if the run ends in a terminal failure (see `failJob`).
      ...(opts.countAttempt === false ? {} : { attempts: { increment: 1 } }),
      leaseUntil: new Date(Date.now() + LEASE_MS),
      startedAt: new Date(),
      worker,
    },
  });
  if (claimed.count === 0) return { matched: false, job: null };
  return { matched: true, job: await prisma.job.findUnique({ where: { id: jobId } }) };
}

/**
 * Fail a generate job — and tell the owner.
 *
 * AU-03 (2026-10-26 audit): during the October outage every render was refused for five days and
 * no one was told; a `FAILED` row is not an alert. Every *permanent* GENERATE failure — the four
 * early exits in `processClaimedJob` and its retry-exhausted catch — sends one email carrying the
 * engine's code.
 *
 * The alert can never change the job's outcome. It is guarded here as well as inside
 * `notifyOwnerEngineFailure`: a defect in the mailer must not turn a recorded `FAILED` job into a
 * thrown exception the dispatcher would lease-reclaim and retry forever.
 */
async function failGenerateJob(
  job: Job,
  lastError: string,
  alertCode = lastError,
  attemptUncounted = false,
): Promise<void> {
  await failJobAfterCheck(job, lastError, attemptUncounted);
  try {
    // The alert names the bare engine code; `lastError` may carry the `ENGINE_FAILED:` prefix.
    await notifyOwnerEngineFailure({ orderId: job.orderId, code: alertCode, attempts: job.attempts });
  } catch (err) {
    console.error("engine failure alert threw:", err instanceof Error ? err.message : "unknown");
  }
}

/**
 * Fail a job, first recording the attempt if the claim deliberately skipped it.
 *
 * AU-12 (2026-10-26 audit): `processJobById({ countAttempt: false })` — the customer's "Check for
 * updates" — does not increment `attempts` at claim time, because a fast 5xx during an outage must
 * not spend a paid order's retries. A run that ends in a terminal failure really did happen, though,
 * so the attempt is written before the job is marked failed. `attemptUncounted` is false on every
 * dispatcher path, which keeps the ordinary two-argument `failJob` call unchanged.
 */
async function failJobAfterCheck(job: Job, lastError: string, attemptUncounted: boolean): Promise<void> {
  if (attemptUncounted) await recordAttempt(job.id);
  await failJob(job.id, lastError);
}

/**
 * The job's recorded failure for an engine refusal, or null for a local error.
 *
 * AU-28 (2026-10-26 audit): every failed job said `ENGINE_FAILED`, so the admin "Recent failures"
 * view could never have shown `UPLOAD_HOSTS_UNCONFIGURED` — the cause of the October outage. The
 * engine code is kept after the `ENGINE_FAILED:` prefix: the prefix keeps existing dashboards and
 * greps working, and the suffix names what actually happened. Only an error that carries the
 * engine's HTTP status qualifies; a transport failure or a local fault records its own code.
 */
function engineFailureLastError(err: unknown): string | null {
  if (!(err instanceof ApiError)) return null;
  if (typeof err.details.engineStatus !== "number") return null;
  return `ENGINE_FAILED:${err.code}`;
}

/** The actual work. Assumes the job is already leased to us. */
export async function processClaimedJob(job: Job, opts: ClaimOptions = {}): Promise<JobOutcome> {
  // AU-12: a check claimed without spending an attempt still records one if this run ends in a
  // terminal failure. A transient refusal spends nothing, so the job stays where it was.
  const attemptUncounted = opts.countAttempt === false;

  if (job.kind === "VOICE") return processVoiceJob(job, attemptUncounted);
  try {
    const order = (await prisma.order.findUnique({
      where: { id: job.orderId },
      include: { profileA: true, profileB: true, user: { select: { deletedAt: true } } },
    })) as OrderWithProfiles | null;

    if (!order) {
      await failGenerateJob(job, "ORDER_MISSING", undefined, attemptUncounted);
      return { ok: false, note: "order missing" };
    }

    // Order rows are retained for accounting (D2), but generation must never run for an erased
    // person. `failJob` directly, not `failGenerateJob`: this is not an outage, so it must not page
    // the owner.
    if (order.user.deletedAt) {
      await failJobAfterCheck(job, "ACCOUNT_ERASED", attemptUncounted);
      return { ok: false, note: "account erased" };
    }

    if (order.kind === "COMPAT" && !order.profileB) {
      await failGenerateJob(job, "COMPAT_NEEDS_TWO_PROFILES", undefined, attemptUncounted);
      return { ok: false, note: "compat without second profile" };
    }

    if (!isR2Configured()) {
      // Configuration error, not transient: retrying will not help.
      await failGenerateJob(job, "STORAGE_NOT_CONFIGURED", undefined, attemptUncounted);
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
    // The reading: the artefact the client actually opens on a phone, and can save as one file. Every
    // paid kind gets one — a compatibility reading is markdown through the same renderer, so it has a
    // web document too. (It used to be withheld from compat orders.)
    const htmlKey = buildReportKey(order.userId, order.id, reportId, "html");

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
      // …and the web document: the artefact the client actually reads on a phone, which they can
      // also save as one file. Best-effort — a reading that fails to upload leaves the PDF as the
      // deliverable rather than losing the order.
      htmlUploadUrl: await presignPutUrl(htmlKey, "text/html"),
      profileA,
      ...(profileB ? { profileB } : {}),
      favorableOverrideA: order.favorableOverrideA ?? null,
      favorableOverrideB: order.favorableOverrideB ?? null,
    };

    const result = await callEngine(payload);

    // Trust but verify: a 200 without an object would leave a report row pointing at nothing.
    const object = await headObject(pdfKey);
    if (!object) {
      await failGenerateJob(job, "UPLOAD_NOT_VERIFIED", undefined, attemptUncounted);
      return { ok: false, note: "upload not verified" };
    }
    // The reading is best-effort in the same way: a web document that did not land leaves the PDF
    // as the deliverable rather than losing the order. The row records only what is really there.
    const htmlObject = result.htmlBytes ? await headObject(htmlKey) : null;

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
          htmlKey: htmlObject ? htmlKey : null,
          htmlBytes: htmlObject ? (result.htmlBytes ?? htmlObject.size) : null,
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

    // This one is now waiting for a person. Say so — a review queue nobody is told about is a
    // review queue that does not happen. Fire-and-forget: it can never affect the delivery.
    await notifyOwnerNewReview({
      reportId,
      tierName: tierNameFor(order.kind, order.tier),
      profileLabel: order.profileA.label,
      waitedMinutes: 0,
      queueDepth: 1,
    });

    return { ok: true, note: `report v${version}`, reportId, version };
  } catch (err) {
    const code =
      typeof err === "object" && err !== null && "code" in err
        ? String((err as { code?: string }).code ?? "UNKNOWN")
        : err instanceof Error
          ? err.name
          : "UNKNOWN";

    // AU-28: keep the engine's code in `lastError`, not just "ENGINE_FAILED".
    const lastError = engineFailureLastError(err) ?? code;

    // A 422 from the engine is permanent: bad birth data will not improve on retry.
    const permanent =
      typeof err === "object" && err !== null && "status" in err && (err as { status?: number }).status === 422;

    if (permanent || job.attempts >= job.maxAttempts) {
      await failGenerateJob(job, lastError, code, attemptUncounted);
      return { ok: false, note: `failed: ${code}` };
    }
    await requeueJob(job.id, lastError);
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
async function processVoiceJob(job: Job, attemptUncounted = false): Promise<JobOutcome> {
  try {
    const report = await prisma.report.findUnique({
      where: { id: job.reportId ?? "" },
      include: {
        order: { select: { userId: true, kind: true, tier: true } },
        user: { select: { email: true, name: true, deletedAt: true } },
      },
    });
    if (!report) {
      await failJobAfterCheck(job, "REPORT_MISSING", attemptUncounted);
      return { ok: false, note: "report missing" };
    }

    // Order rows are retained for accounting (D2), but no artefact may be produced for an erased
    // person. `failJob` directly: an erased account's voice job is not an outage, so it must not
    // page the owner.
    if (report.user.deletedAt) {
      await failJobAfterCheck(job, "ACCOUNT_ERASED", attemptUncounted);
      return { ok: false, note: "account erased" };
    }

    await prisma.report.update({ where: { id: report.id }, data: { audioStatus: "PROCESSING" } });

    if (!isTtsConfigured()) {
      await prisma.report.update({
        where: { id: report.id },
        data: { audioStatus: "FAILED", audioError: "TTS_NOT_CONFIGURED" },
      });
      await failJobAfterCheck(job, "TTS_NOT_CONFIGURED", attemptUncounted);
      return { ok: false, note: "TTS not configured" };
    }
    if (!report.mdKey) {
      await prisma.report.update({
        where: { id: report.id },
        data: { audioStatus: "FAILED", audioError: "NO_SOURCE_MARKDOWN" },
      });
      await failJobAfterCheck(job, "NO_SOURCE_MARKDOWN", attemptUncounted);
      return { ok: false, note: "source markdown missing" };
    }

    const markdown = await getObjectText(report.mdKey);
    if (!markdown) {
      await requeueOrFail(job, "SOURCE_UNREADABLE", undefined, attemptUncounted);
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

    // An auto-delivered reading waits for its audio: the client gets ONE message with the reading
    // and the MP3 together. If the reading's email was held for this audio, release it now — and
    // do not send the separate "your audio is ready" note as well.
    //
    // The flag was read at the top of this function, before the audio was marked READY: it was
    // set at approval time, when the reading's email was held.
    const wasHeld = report.emailHeldForAudio;
    if (wasHeld) {
      await prisma.report.update({ where: { id: report.id }, data: { emailHeldForAudio: false } });
      await deliverReport(report.id);
      return { ok: true, note: `audio ready (${audio.byteLength} bytes); reading emailed with it` };
    }

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
    await requeueOrFail(job, code, job.reportId ? { reportId: job.reportId } : undefined, attemptUncounted);
    return { ok: false, note: `audio: ${code}` };
  }
}

/** Transient vs permanent, shared by the render and voice paths. */
async function requeueOrFail(
  job: Job,
  code: string,
  extra?: { reportId: string },
  attemptUncounted = false,
): Promise<void> {
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
    await failJobAfterCheck(job, code, attemptUncounted);
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

/**
 * Drain up to `max` jobs. Deliberately bounded — a tick that overruns the function timeout is the
 * situation leases exist to survive, but doing three and returning is better.
 *
 * Owner decision D11 (2026-10-26): in-flight paid work is deliberately NOT consent-gated. A
 * withdrawal stops new orders and new jobs; work already paid for still renders and is delivered.
 * Do not add a consent check here — the gate belongs at the entry points (order creation, checkout,
 * job kick).
 */
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

export interface KickResult {
  /** Jobs the check looked at. */
  processed: number;
  /** Jobs the check actually rendered. */
  generated: number;
  /** Jobs that ran and did not render — the customer is told their check failed. */
  failed: number;
}

/**
 * Process the caller's own queued jobs, inline.
 *
 * The scheduled dispatcher runs every 15 minutes from `.github/workflows/sla-sweep.yml` (decision D4:
 * Vercel Hobby cannot run a per-minute cron, and the daily Vercel cron is only a fallback). This is
 * the recovery path a client can trigger themselves from the dashboard when a report is sitting in
 * review longer than expected.
 *
 * AU-12 (2026-10-26 audit): the check must not spend the job's retries. During an outage every click
 * hit a fast 5xx, and two clicks could push a paid job to `maxAttempts` and fail it for good, so the
 * claim is made with `countAttempt: false`. Failures are counted and returned rather than swallowed:
 * a check that rendered nothing must not be reported as a success.
 *
 * Ownership is checked before anything is processed, and the work is scoped to that user's orders.
 */
export async function kickOwnerJobs(userId: string, max = 2): Promise<KickResult> {
  const jobs = await prisma.job.findMany({
    where: { state: "QUEUED", order: { userId } },
    orderBy: { createdAt: "asc" },
    take: max,
    select: { id: true },
  });

  let generated = 0;
  let failed = 0;
  for (const job of jobs) {
    const outcome = await processJobById(job.id, `kick-${userId.slice(0, 8)}`, { countAttempt: false });
    if (outcome.ok) generated++;
    else if (outcome.ran !== false) failed++;
  }
  return { processed: jobs.length, generated, failed };
}

/** Delete a report row and queue its objects. */
export async function deleteReportArtifacts(reportId: string): Promise<void> {
  const report = await prisma.report.findUnique({
    where: { id: reportId },
    select: { pdfKey: true, mdKey: true, audioKey: true, htmlKey: true },
  });
  if (!report) return;
  if (report.pdfKey) await deleteObjectOrQueue(report.pdfKey);
  if (report.mdKey) await deleteObjectOrQueue(report.mdKey);
  if (report.audioKey) await deleteObjectOrQueue(report.audioKey);
  // AU-08 (2026-10-26 audit): the web document is where the birth data actually sits, and for a
  // sample it is the ONLY artefact — omitting it left the whole chart in R2 after a delete.
  if (report.htmlKey) await deleteObjectOrQueue(report.htmlKey);
  await prisma.report.delete({ where: { id: reportId } });
}

export async function queueOrphansForDeletion(keys: string[]): Promise<void> {
  for (const key of keys) await queueObjectDeletion(key, "orphaned");
}
