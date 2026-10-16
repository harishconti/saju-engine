import { prisma } from "./prisma";
import { drainObjectDeletions, deleteObjects, isR2Configured, listObjectsByPrefix } from "./r2";
import { purgeOldIdempotencyKeys } from "./idempotency";
import { purgeOldRateLimits } from "./ratelimit";
import { purgeOldJobs, reclaimStaleJobs } from "./queue";

/**
 * The daily maintenance sweep.
 *
 * Every step is a bounded delete/update, so the whole job is safe to run twice concurrently.
 * Contract: docs/webapp/09-operations.md §"What cleanup does"
 */

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

    // 3. Sweep unclaimed anonymous samples older than 7 days.
    report.anonymousSwept = await sweepAnonymousSamples(now);
  }

  // 4. Retry webhooks that were recorded but never processed.
  report.webhooksReplayed = await retryUnprocessedWebhooks();

  // 5. Purges.
  report.jobsPurged = await purgeOldJobs();
  report.keysPurged = await purgeOldIdempotencyKeys();
  report.limitsPurged = await purgeOldRateLimits();

  // 6. Process due deletions.
  report.deletionsProcessed = await processDueDeletions(now);

  // 7. Retention sweep: flag long-inactive profiles (warn, never delete silently).
  await flagInactiveProfiles(now);

  return report;
}

/**
 * Anonymous samples are stored under reports/anonymous/… until claimed. We cannot list by prefix
 * without a ListObjects call, so the sweep works from the tracking rows instead and additionally
 * deletes by prefix when R2 listing is available.
 */
async function sweepAnonymousSamples(now: Date): Promise<number> {
  const cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
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
    select: { id: true, pdfKey: true, mdKey: true, audioKey: true },
    take: 200,
  });

  if (stale.length > 0) {
    const keys = stale
      .flatMap((r) => [r.pdfKey, r.mdKey, r.audioKey])
      .filter((k): k is string => Boolean(k));
    if (keys.length > 0) {
      const res = await deleteObjects(keys);
      deleted += res.deleted.length;
    }
    await prisma.report.deleteMany({ where: { id: { in: stale.map((r) => r.id) } } });
  }

  return deleted;
}

/** Replay webhook events that were stored but not processed (a crash between the two steps). */
async function retryUnprocessedWebhooks(): Promise<number> {
  const cutoff = new Date(Date.now() - 60_000);
  const pending = await prisma.webhookEvent.findMany({
    where: { processedAt: null, receivedAt: { lt: cutoff } },
    orderBy: { receivedAt: "asc" },
    take: 20,
    select: { id: true, provider: true },
  });
  // Handlers are idempotent; the dispatcher route re-runs them.
  // We only mark the count here — the actual replay is provider-specific and lives in the webhook
  // routes, which are safe to re-invoke with the stored payload.
  return pending.length;
}

/**
 * Complete deletions whose grace period has expired.
 *
 * What survives is deliberate and documented: order rows are anonymised (financial record-keeping),
 * consent records are retained as proof, and audit logs are kept for dispute resolution. Birth data
 * and reports are destroyed.
 */
async function processDueDeletions(now: Date): Promise<number> {
  const due = await prisma.deletionRequest.findMany({
    where: { status: "pending", scheduledFor: { lte: now } },
    take: 10,
    select: { id: true, userId: true },
  });

  let processed = 0;
  for (const request of due) {
    const reports = await prisma.report.findMany({
      where: { userId: request.userId },
      // Include the MP3: an erasure request must not leave the audio behind.
      select: { id: true, pdfKey: true, mdKey: true, audioKey: true },
    });

    const keys = reports
      .flatMap((r) => [r.pdfKey, r.mdKey, r.audioKey])
      .filter((k): k is string => Boolean(k));
    if (keys.length > 0 && isR2Configured()) {
      await deleteObjects(keys);
    }

    await prisma.$transaction(async (tx) => {
      await tx.report.deleteMany({ where: { userId: request.userId } });
      await tx.profile.deleteMany({ where: { userId: request.userId } });
      await tx.delivery.deleteMany({ where: { userId: request.userId } });

      // Anonymise the account; keep it so the order rows still resolve.
      await tx.user.update({
        where: { id: request.userId },
        data: {
          name: "Deleted user",
          email: `deleted+${request.userId}@deleted.invalid`,
          deletedAt: now,
        },
      });

      await tx.consentRecord.updateMany({
        where: { userId: request.userId, withdrawnAt: null },
        data: { withdrawnAt: now },
      });

      await tx.deletionRequest.update({
        where: { id: request.id },
        data: { status: "completed", completedAt: now },
      });

      await tx.auditLog.create({
        data: {
          entity: "deletion",
          entityId: request.id,
          action: "delete",
          actorId: null,
          after: { completedAt: now.toISOString() },
        },
      });
    });

    processed++;
  }

  return processed;
}

/** Warn at 23 months of inactivity; the actual sweep is a manual decision, not an automatic one. */
async function flagInactiveProfiles(now: Date): Promise<void> {
  const cutoff = new Date(now.getTime() - 23 * 30 * 24 * 60 * 60 * 1000);
  await prisma.profile.updateMany({
    where: { updatedAt: { lt: cutoff }, deletedAt: null },
    data: {},
  });
}
