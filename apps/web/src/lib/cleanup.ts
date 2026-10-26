import { SCRUBBED_PROFILE } from "./profile-scrub";
import { prisma } from "./prisma";
import { drainObjectDeletions, deleteObjectOrQueue, deleteObjects, isR2Configured, listObjectsByPrefix } from "./r2";
import { purgeOldIdempotencyKeys } from "./idempotency";
import { purgeOldRateLimits } from "./ratelimit";
import { purgeOldJobs, reclaimStaleJobs } from "./queue";
import { ANONYMOUS_SAMPLE_RETENTION_DAYS } from "./retention";
import { processDodoEvent, type DodoEvent } from "./dodo-webhook";

/**
 * The daily maintenance sweep.
 *
 * Every step is a bounded delete/update, so the whole job is safe to run twice concurrently.
 * Contract: docs/webapp/09-operations.md §"What cleanup does"
 *
 * ⚠️ **Nothing else expires the free snapshots.** No R2 lifecycle rule covers `reports/anonymous/`
 * (verified 2026-10-17: the bucket's only rule is Cloudflare's default multipart abort), so this cron
 * is the whole retention mechanism for them. See `retention.ts`.
 */

const DAY_MS = 24 * 60 * 60 * 1000;

export interface CleanupReport {
  leasesRequeued: number;
  leasesFailed: number;
  objectsDeleted: number;
  objectsFailed: number;
  objectsAbandoned: number;
  jobsPurged: number;
  keysPurged: number;
  limitsPurged: number;
  webhooksReplayed: number;
  deletionsProcessed: number;
  anonymousSwept: number;
}

export async function runCleanup(now = new Date()): Promise<CleanupReport> {
  const report: CleanupReport = {
    leasesRequeued: 0,
    leasesFailed: 0,
    objectsDeleted: 0,
    objectsFailed: 0,
    objectsAbandoned: 0,
    jobsPurged: 0,
    keysPurged: 0,
    limitsPurged: 0,
    webhooksReplayed: 0,
    deletionsProcessed: 0,
    anonymousSwept: 0,
  };

  // 1. Reclaim dead leases.
  const leases = await reclaimStaleJobs();
  report.leasesRequeued = leases.requeued;
  report.leasesFailed = leases.failed;

  // 2. Drain the R2 deletion queue.
  if (isR2Configured()) {
    const drained = await drainObjectDeletions(200);
    report.objectsDeleted = drained.deleted;
    report.objectsFailed = drained.failed;
    report.objectsAbandoned = drained.abandoned;

    // 3. Sweep unclaimed anonymous samples older than ANONYMOUS_SAMPLE_RETENTION_DAYS.
    report.anonymousSwept = await sweepAnonymousSamples(now);
  }

  // 4. Retry webhooks that were recorded but never processed.
  report.webhooksReplayed = await retryUnprocessedWebhooks(now);

  // 5. Purges.
  report.jobsPurged = await purgeOldJobs();
  report.keysPurged = await purgeOldIdempotencyKeys();
  report.limitsPurged = await purgeOldRateLimits();

  // 6. Process due deletions.
  report.deletionsProcessed = await processDueDeletions(now);

  return report;
}

/**
 * Anonymous samples are stored under reports/anonymous/… until claimed. We cannot list by prefix
 * without a ListObjects call, so the sweep works from the tracking rows instead and additionally
 * deletes by prefix when R2 listing is available.
 */
async function sweepAnonymousSamples(now: Date): Promise<number> {
  const cutoff = new Date(now.getTime() - ANONYMOUS_SAMPLE_RETENTION_DAYS * DAY_MS);
  let deleted = 0;

  // (a) Objects, by age, under the anonymous prefix.
  //
  // This is the sweep the docs promise, and it has to work WITHOUT rows: an anonymous sample
  // creates no Report at all, so the previous row-driven version matched nothing and the objects
  // accumulated in R2 forever (~70 KB per visitor).
  try {
    const objects = await listObjectsByPrefix("reports/anonymous/", 1000);
    const expired = objects
      .filter((o) => o.lastModified !== null && o.lastModified < cutoff)
      .map((o) => o.key);
    if (expired.length > 0) {
      const res = await deleteObjects(expired);
      deleted += res.deleted.length;
    }
  } catch (err) {
    console.error("anonymous object sweep failed", err instanceof Error ? err.name : "unknown");
  }

  // (b) Row-backed leftovers: a report with no order that was never delivered (an abandoned
  // draft). Delivered rows are deliberately excluded — a sample a signed-in user kept is theirs
  // until they delete it, and `orderId` is null for those too.
  const stale = await prisma.report.findMany({
    where: {
      orderId: null,
      status: { in: ["DRAFT_READY", "FAILED"] },
      createdAt: { lt: cutoff },
    },
    select: { id: true, pdfKey: true, mdKey: true, audioKey: true, htmlKey: true },
    take: 200,
  });

  if (stale.length > 0) {
    const keys = stale
      .flatMap((r) => [r.pdfKey, r.mdKey, r.audioKey, r.htmlKey])
      .filter((k): k is string => Boolean(k));
    if (keys.length > 0) {
      const res = await deleteObjects(keys);
      deleted += res.deleted.length;
    }
    await prisma.report.deleteMany({ where: { id: { in: stale.map((r) => r.id) } } });
  }

  return deleted;
}

/**
 * Providers whose recorded events can be replayed from the stored payload.
 *
 * A provider without a replayer is skipped rather than guessed at: replaying an event shape we do
 * not understand could duplicate whatever side effect it represents. The query below also filters
 * on this list so un-replayable rows cannot crowd replayable ones out of the bounded batch.
 */
const WEBHOOK_REPLAYERS: Record<string, (payload: unknown) => Promise<unknown>> = {
  dodo: (payload) => processDodoEvent(payload as DodoEvent),
};

/**
 * Replay webhook events that were stored but never processed (a crash between the two steps).
 *
 * Exported so the retention tests can exercise it directly; `runCleanup` is the only production
 * caller. Bounded to 20 per run, oldest first, so a poison event cannot hold up the whole day.
 * A failed replay keeps `processedAt` null (and records its error class) so the next run retries.
 */
export async function retryUnprocessedWebhooks(now = new Date()): Promise<number> {
  const cutoff = new Date(now.getTime() - 60_000);
  const pending = await prisma.webhookEvent.findMany({
    where: {
      processedAt: null,
      receivedAt: { lt: cutoff },
      provider: { in: Object.keys(WEBHOOK_REPLAYERS) },
    },
    orderBy: { receivedAt: "asc" },
    take: 20,
    select: { id: true, provider: true, payload: true },
  });

  let replayed = 0;
  for (const row of pending) {
    const replayer = WEBHOOK_REPLAYERS[row.provider];
    if (!replayer) continue;

    try {
      await replayer(row.payload);
      await prisma.webhookEvent.update({
        where: { id: row.id },
        data: { processedAt: now, error: null },
      });
      replayed++;
    } catch (err) {
      const name = err instanceof Error ? err.name : "unknown";
      console.error("webhook replay failed", row.provider, row.id, name);
      try {
        await prisma.webhookEvent.update({ where: { id: row.id }, data: { error: name } });
      } catch {
        // Leave the row unprocessed; the next run tries again.
      }
    }
  }

  return replayed;
}

/**
 * Complete deletions whose grace period has expired.
 *
 * What survives is deliberate and documented (owner decision D2, 2026-10-26):
 *  - **Order rows are retained** for accounting. `Order_profileAId_fkey` is ON DELETE RESTRICT, so
 *    the profiles any order references are scrubbed in place and kept: names, labels, birth data
 *    and the derived chart are destroyed, `deletedAt` is set, and the row no longer describes a
 *    person.
 *  - **Profiles no order references are deleted outright.**
 *  - **Consent records are retained** as proof the consent existed; they are withdrawn, not removed.
 *  - **Reports and their R2 artefacts are destroyed.** The PDF, markdown, audio and HTML objects are
 *    deleted only after the transaction commits (through `deleteObjectOrQueue`, so a storage error is
 *    retried by the next sweep instead of rolling back an already-completed erasure).
 *  - **The User is anonymised but kept**, because the retained order rows resolve to it.
 *
 * Each request is isolated in its own try/catch: one failure is logged and leaves that request
 * `pending` for the next run, without blocking the requests after it or the rest of the cron.
 *
 * Exported for the retention tests; `runCleanup` is the only production caller.
 */
export async function processDueDeletions(now: Date): Promise<number> {
  const due = await prisma.deletionRequest.findMany({
    where: { status: "pending", scheduledFor: { lte: now } },
    take: 10,
    select: { id: true, userId: true },
  });

  let processed = 0;
  for (const request of due) {
    try {
      await processDeletionRequest(request, now);
      processed++;
    } catch (err) {
      // Leave it pending. Throwing here would block every later request and the cron's later steps.
      console.error(
        "deletion request failed; left pending for the next run",
        request.id,
        err instanceof Error ? err.name : "unknown",
      );
    }
  }

  return processed;
}

/** Erase one user's data. Split out only so `processDueDeletions` can isolate failures. */
async function processDeletionRequest(
  request: { id: string; userId: string },
  now: Date,
): Promise<void> {
  const { id: requestId, userId } = request;

  const reports = await prisma.report.findMany({
    where: { userId },
    // Include the MP3 and the web document: an erasure request must not leave either behind.
    select: { id: true, pdfKey: true, mdKey: true, audioKey: true, htmlKey: true },
  });
  const keys = reports
    .flatMap((r) => [r.pdfKey, r.mdKey, r.audioKey, r.htmlKey])
    .filter((k): k is string => Boolean(k));

  // Order rows are retained for accounting, so find which profiles they still point at. Profile B
  // is SET NULL on delete, but Profile A is RESTRICT — deleting either referenced row fails the
  // whole transaction with P2003.
  const profiles = await prisma.profile.findMany({
    where: { userId },
    select: { id: true },
  });
  const profileIds = profiles.map((p) => p.id);

  const referencedProfileIds = new Set<string>();
  if (profileIds.length > 0) {
    const orders = await prisma.order.findMany({
      where: { OR: [{ profileAId: { in: profileIds } }, { profileBId: { in: profileIds } }] },
      select: { profileAId: true, profileBId: true },
    });
    for (const order of orders) {
      referencedProfileIds.add(order.profileAId);
      if (order.profileBId) referencedProfileIds.add(order.profileBId);
    }
  }
  const retainedProfileIds = [...referencedProfileIds];

  await prisma.$transaction(async (tx) => {
    // Reports first: Report_profileAId_fkey is RESTRICT too.
    await tx.report.deleteMany({ where: { userId } });
    await tx.delivery.deleteMany({ where: { userId } });

    if (retainedProfileIds.length > 0) {
      await tx.profile.updateMany({
        where: { userId, id: { in: retainedProfileIds } },
        data: { ...SCRUBBED_PROFILE, deletedAt: now },
      });
    }
    // `notIn: []` matches everything, which is what an order-free user needs.
    await tx.profile.deleteMany({ where: { userId, id: { notIn: retainedProfileIds } } });

    // Anonymise the account; keep it so the order rows still resolve.
    await tx.user.update({
      where: { id: userId },
      data: {
        name: "Deleted user",
        email: `deleted+${userId}@deleted.invalid`,
        deletedAt: now,
      },
    });

    await tx.consentRecord.updateMany({
      where: { userId, withdrawnAt: null },
      data: { withdrawnAt: now },
    });

    await tx.deletionRequest.update({
      where: { id: requestId },
      data: { status: "completed", completedAt: now },
    });

    await tx.auditLog.create({
      data: {
        entity: "deletion",
        entityId: requestId,
        action: "delete",
        actorId: null,
        after: { completedAt: now.toISOString() },
      },
    });
  });

  // Only now that the database has committed. If storage is down, `deleteObjectOrQueue` enqueues
  // the key for the next sweep instead of throwing away an erasure that already succeeded.
  for (const key of keys) {
    try {
      await deleteObjectOrQueue(key);
    } catch (err) {
      console.error("erasure object cleanup failed", err instanceof Error ? err.name : "unknown");
    }
  }
}

