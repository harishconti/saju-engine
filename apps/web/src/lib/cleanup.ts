import { SCRUBBED_PROFILE } from "./profile-scrub";
import { prisma } from "./prisma";
import { drainObjectDeletions, deleteObjectOrQueue, deleteObjects, isR2Configured, listObjectsByPrefix } from "./r2";
import { purgeOldIdempotencyKeys } from "./idempotency";
import { purgeOldRateLimits } from "./ratelimit";
import { purgeOldJobs, reclaimStaleJobs } from "./queue";
import { ANONYMOUS_SAMPLE_RETENTION_DAYS, PROFILE_INACTIVITY_RETENTION_MONTHS } from "./retention";
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
  profilesRetired: number;
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
    profilesRetired: 0,
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

  // 7. Retire profiles idle past the published inactivity window.
  report.profilesRetired = await retireInactiveProfiles(now);

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
      // A request is counted only when it reached `completed`. A request whose local erasure
      // committed but whose identity delete failed stays pending and is retried by the next run.
      if (await processDeletionRequest(request, now)) processed++;
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

/**
 * The Neon Auth relations an erasure must clear (AU-25).
 *
 * Probed before deleting rather than assumed: the identity schema belongs to Neon Auth, so a
 * version that renamed or dropped a table must stop the delete cleanly instead of removing half of
 * an identity. `to_regclass` answers null for a relation that does not exist, which is exactly the
 * signal needed and involves no privileged access beyond the app's own connection.
 */
const NEON_AUTH_RELATIONS = ['neon_auth."session"', 'neon_auth."account"', 'neon_auth."user"'] as const;

type IdentityOutcome = "deleted" | "missing-relation" | "failed";

/**
 * Delete the Neon Auth identity behind an erased account (AU-25).
 *
 * The SDK cannot do this for the cron: `auth.deleteUser()` proxies with the caller's session and
 * Better Auth guards it with `sensitiveSessionMiddleware`, while `auth.admin.removeUser()` needs an
 * admin session. The cron has neither. The owner has therefore approved one documented exception to
 * "never touch the `neon_auth` schema" (recorded on the Prisma schema): delete directly over the
 * app's existing `DATABASE_URL`.
 *
 * The id is the Neon user id — the local `User` is mirrored with `id: n.id` — so this never matches
 * on email, which the local transaction has already rewritten by the time this runs.
 *
 * Sessions, then accounts, then the user: the child rows reference the identity, and a partial
 * delete (sessions gone, user alive) would leave an account nobody can reach but that still blocks
 * re-registration. All three statements share one transaction so it is all or nothing.
 *
 * Returns an outcome instead of throwing: the caller keeps the request pending on anything but
 * "deleted", and must never let this step fail an erasure whose local half already committed.
 */
async function deleteNeonIdentity(neonUserId: string): Promise<IdentityOutcome> {
  try {
    return await prisma.$transaction(async (tx) => {
      const missing: string[] = [];
      for (const relation of NEON_AUTH_RELATIONS) {
        const rows = await tx.$queryRaw<Array<{ name: string | null }>>`
          SELECT to_regclass(${relation})::text AS name
        `;
        if (!rows[0]?.name) missing.push(relation);
      }
      if (missing.length > 0) {
        console.warn(
          "neon identity deletion skipped: expected relation(s) absent",
          missing.join(", "),
        );
        return "missing-relation";
      }

      await tx.$executeRaw`DELETE FROM neon_auth."session" WHERE "userId" = ${neonUserId}`;
      await tx.$executeRaw`DELETE FROM neon_auth."account" WHERE "userId" = ${neonUserId}`;
      await tx.$executeRaw`DELETE FROM neon_auth."user" WHERE "id" = ${neonUserId}`;
      return "deleted";
    });
  } catch (err) {
    console.error(
      "neon identity deletion failed; deletion request left pending",
      neonUserId,
      err instanceof Error ? err.name : "unknown",
    );
    return "failed";
  }
}

/**
 * Erase one user's data. Split out only so `processDueDeletions` can isolate failures.
 *
 * Returns true only when the request reached `completed`.
 */
async function processDeletionRequest(
  request: { id: string; userId: string },
  now: Date,
): Promise<boolean> {
  const { id: requestId, userId } = request;
  // AU-25: capture the identity key before the local transaction rewrites the account. `User.id`
  // IS the Neon Auth user id (the mirror is created with `id: n.id`), and the email is anonymised
  // below, so matching on email here would find nothing.
  const neonUserId = userId;

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

    // The request is NOT marked completed here (AU-25). Its identity delete happens after this
    // commits, and a request that is `completed` while the user can still sign in would be a lie
    // the retry path could never correct. Completion is written below, only once that succeeds.
    await tx.auditLog.create({
      data: {
        entity: "deletion",
        entityId: requestId,
        action: "delete",
        actorId: null,
        after: { localErasureCommittedAt: now.toISOString() },
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

  // AU-25: the local half is committed and idempotent; this half severs sign-in. A failure or a
  // missing relation leaves the request pending, so the next run retries both halves, and never
  // undoes what already committed.
  const identity = await deleteNeonIdentity(neonUserId);
  if (identity !== "deleted") {
    try {
      await prisma.auditLog.create({
        data: {
          entity: "deletion",
          entityId: requestId,
          action: "update",
          actorId: null,
          after: { neonIdentity: identity, localErasureCommitted: true },
        },
      });
    } catch (err) {
      // The failure is already logged by `deleteNeonIdentity`; losing the audit row must not be a
      // second reason to fail an erasure whose local half is done.
      console.error("deletion identity audit failed", err instanceof Error ? err.name : "unknown");
    }
    return false;
  }

  await prisma.deletionRequest.update({
    where: { id: requestId },
    data: { status: "completed", completedAt: now },
  });
  await prisma.auditLog.create({
    data: {
      entity: "deletion",
      entityId: requestId,
      action: "update",
      actorId: null,
      after: { completedAt: now.toISOString(), neonIdentity: "deleted" },
    },
  });

  return true;
}

/**
 * Retire profiles nobody has touched for the published inactivity window (AU-27).
 *
 * The privacy policy promises birth details are kept "until you delete them, or after 24 months of
 * inactivity". Before this, the sweep that was supposed to enforce it was an `updateMany` with an
 * empty `data` object — a no-op that changed nothing and could not: no field marked an inactive
 * profile, so nobody downstream could have acted on one either. The promise had no implementation
 * at all. `PROFILE_INACTIVITY_RETENTION_MONTHS` is the number the policy publishes, and this
 * function is what enforces it.
 *
 * The compliance notes also describe a warning at 23 months. Nothing in the app sends mail on a
 * schedule, so there is no delivery mechanism for that warning; inventing an inactivity-mailer is a
 * product decision, not a retention fix. The enforceable half is the sweep at 24, so that is what
 * exists — deliberately, not by omission.
 *
 * Disposition is the one D2 established for erasure, for the same reason:
 *  - `Order_profileAId_fkey` and `Report_profileAId_fkey` are ON DELETE RESTRICT. Deleting a profile
 *    anything still points at would raise P2003 and roll the whole batch back, so a referenced
 *    profile is **scrubbed** (`SCRUBBED_PROFILE`, the one definition), soft-deleted and kept.
 *  - A profile nothing references is deleted outright — the row describes nobody once scrubbed, so
 *    there is nothing left to keep it for.
 *
 * Bounded like every other step so one run cannot hold a long transaction over the whole table;
 * `deletedAt` and the bumped `updatedAt` keep already-retired rows out of the next batch.
 *
 * Exported for the retention tests; `runCleanup` is the only production caller.
 */
export async function retireInactiveProfiles(now: Date): Promise<number> {
  const cutoff = new Date(now);
  cutoff.setUTCMonth(cutoff.getUTCMonth() - PROFILE_INACTIVITY_RETENTION_MONTHS);

  const candidates = await prisma.profile.findMany({
    where: { deletedAt: null, updatedAt: { lt: cutoff } },
    select: { id: true },
    take: 200,
  });
  if (candidates.length === 0) return 0;

  const ids = candidates.map((p) => p.id);

  // A profile is "referenced" by any order or report pointing at it, as A or B: either column being
  // RESTRICT is enough to make a delete fail, and a B-reference is still a delivery that names them.
  const [orders, reports] = await Promise.all([
    prisma.order.findMany({
      where: { OR: [{ profileAId: { in: ids } }, { profileBId: { in: ids } }] },
      select: { profileAId: true, profileBId: true },
    }),
    prisma.report.findMany({
      where: { OR: [{ profileAId: { in: ids } }, { profileBId: { in: ids } }] },
      select: { profileAId: true, profileBId: true },
    }),
  ]);
  const referenced = new Set<string>();
  for (const row of [...orders, ...reports]) {
    referenced.add(row.profileAId);
    if (row.profileBId) referenced.add(row.profileBId);
  }

  const retained = ids.filter((id) => referenced.has(id));
  const unreferenced = ids.filter((id) => !referenced.has(id));

  const [scrubbed, deleted] = await prisma.$transaction(async (tx) => {
    const updated = retained.length
      ? await tx.profile.updateMany({
          where: { id: { in: retained }, deletedAt: null },
          data: { ...SCRUBBED_PROFILE, deletedAt: now },
        })
      : { count: 0 };
    const removed = unreferenced.length
      ? await tx.profile.deleteMany({ where: { id: { in: unreferenced } } })
      : { count: 0 };
    return [updated.count, removed.count] as const;
  });

  return scrubbed + deleted;
}

