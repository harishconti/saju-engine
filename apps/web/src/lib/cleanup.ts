import { Prisma } from "@prisma/client";
import { SCRUBBED_PROFILE } from "./profile-scrub";
import { prisma } from "./prisma";
import { drainObjectDeletions, deleteObjectOrQueue, deleteObjects, isR2Configured, listObjectsByPrefix } from "./r2";
import { purgeOldIdempotencyKeys } from "./idempotency";
import { purgeOldRateLimits } from "./ratelimit";
import { purgeOldJobs, reclaimStaleJobs } from "./queue";
import { ANONYMOUS_SAMPLE_RETENTION_DAYS, PROFILE_INACTIVITY_RETENTION_MONTHS } from "./retention";
import { processDodoEvent, type DodoEvent } from "./dodo-webhook";
import { notifyOwnerIdentityDeletionFailed } from "./owner-alert";

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
  //
  // Isolated like every other step: the sweep selects candidates and then deletes them, so an order
  // can be created against a candidate in between. That race raises P2003 on Profile A (RESTRICT),
  // and it must cost one night's sweep — retried by tomorrow's run — not the whole cron, whose later
  // steps share this function's error path with the HTTP handler that triggered it.
  try {
    report.profilesRetired = await retireInactiveProfiles(now);
  } catch (err) {
    console.error(
      "inactive-profile sweep failed; next run retries",
      err instanceof Error ? err.name : "unknown",
    );
  }

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
 *  - **Reports and their R2 artefacts are destroyed.** The keys are read inside the erasure
 *    transaction, so the rows deleted and the keys queued come from the same view, and a bounded
 *    post-commit re-sweep catches a report that committed just afterwards. The PDF, markdown, audio
 *    and HTML objects are deleted only after the transaction commits (through `deleteObjectOrQueue`,
 *    so a storage error is retried by the next sweep instead of rolling back an already-completed
 *    erasure).
 *  - **Retained job rows lose their payload.** `Job.payload` holds the full engine request (both
 *    profiles' birth data) and the row outlives the account until `purgeOldJobs()` removes it, so it
 *    is nulled in the same transaction.
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
    // Oldest first (AU-25): with a fixed take of 10 and no ordering, the same stuck rows came back
    // every run on whatever order the planner chose, and requests behind them never got a slot.
    orderBy: { scheduledFor: "asc" },
    take: 10,
    select: { id: true, userId: true },
  });

  let processed = 0;
  for (const request of due) {
    try {
      // Counted once the request reaches a terminal state — `completed` or the identity-error end
      // state — because either way the next run must not see it again.
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

/**
 * How many times the identity delete is attempted before the request is marked terminal (AU-25).
 *
 * Three nightly runs is plenty for a blip (a dropped connection, a momentary permission error) and
 * short enough that a permanent fault becomes a person's problem within days rather than never.
 * Without a cap the request returns to the front of the queue for ever, and the ten-slot batch
 * slowly fills with requests that can never finish.
 */
const NEON_IDENTITY_MAX_ATTEMPTS = 3;

/**
 * How many post-commit re-sweeps may run for reports that committed just after the erasure
 * transaction (must-fix 2a).
 *
 * A report can commit between the transaction and the sweep; the sweep reads, queues the keys and
 * deletes the row, and a second pass confirms nothing is left. Three is plenty and fixed — an
 * unbounded loop over a table a concurrent render could keep writing to would never terminate.
 */
const ERASURE_RESWEEP_PASSES = 3;

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
 * Returns an outcome instead of throwing: the caller decides how long to retry, and must never let
 * this step fail an erasure whose local half already committed.
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
 * Returns true once the request reaches a terminal state — `completed`, or
 * `completed_with_identity_error` after the identity delete exhausted its retries (AU-25).
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

  // The report keys are read *inside* the transaction, not before it, and that ordering is the
  // point. The transaction deletes reports by `userId`; a report that committed between an outside
  // snapshot and the transaction would be deleted with its storage keys never queued — permanent,
  // unfindable PII in R2 that no later sweep could locate. Reading and deleting under one
  // transaction makes the rows deleted and the keys queued the same view.
  const keys = await prisma.$transaction(async (tx) => {
    const reports = await tx.report.findMany({
      where: { userId },
      // Include the MP3 and the web document: an erasure request must not leave either behind.
      select: { id: true, pdfKey: true, mdKey: true, audioKey: true, htmlKey: true },
    });
    const reportKeys = reports
      .flatMap((r) => [r.pdfKey, r.mdKey, r.audioKey, r.htmlKey])
      .filter((k): k is string => Boolean(k));

    // Reports first: Report_profileAId_fkey is RESTRICT too.
    await tx.report.deleteMany({ where: { userId } });
    await tx.delivery.deleteMany({ where: { userId } });

    // `fulfilment.ts` stores the entire engine request in `Job.payload` — both profiles' names and
    // full birth details included — and a finished job is retained by `purgeOldJobs()` long after
    // the order's profiles are scrubbed. The job row outlives the person's profile data, so erasure
    // must clear the payload in place. Jobs are reached through their required `order` relation, and
    // `payload` is nullable Json, so the value is `Prisma.DbNull` (a SQL NULL) — not `null` (JSON
    // null) and not `{}` (an object).
    await tx.job.updateMany({
      where: { order: { userId } },
      data: { payload: Prisma.DbNull },
    });

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

    return reportKeys;
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

  // A render that was already past its account check when the transaction above ran can still
  // commit a Report just after it. The transaction's view could not contain it, so a single delete
  // by `userId` would strand its objects in R2 with no row left to find them by. Re-read and purge
  // what is still there, taking each row's keys before deleting it.
  //
  // Bounded by `ERASURE_RESWEEP_PASSES`: two concurrent commits cannot repeat indefinitely now that
  // the report write re-checks `deletedAt` inside its own transaction (`fulfilment.ts`), and an
  // unbounded loop over a table an attacker could keep writing to is not an option. A database
  // error here deliberately propagates: the request stays `pending`, so the next run repeats the
  // idempotent erasure rather than settling it with a report row left behind.
  for (let pass = 0; pass < ERASURE_RESWEEP_PASSES; pass++) {
    const leftovers = await prisma.report.findMany({
      where: { userId },
      select: { id: true, pdfKey: true, mdKey: true, audioKey: true, htmlKey: true },
    });
    if (leftovers.length === 0) break;

    for (const report of leftovers) {
      for (const key of [report.pdfKey, report.mdKey, report.audioKey, report.htmlKey]) {
        if (!key) continue;
        try {
          await deleteObjectOrQueue(key);
        } catch (err) {
          console.error(
            "erasure re-sweep object cleanup failed",
            err instanceof Error ? err.name : "unknown",
          );
        }
      }
    }
    await prisma.report.deleteMany({ where: { userId } });

    if (pass === ERASURE_RESWEEP_PASSES - 1) {
      console.error("erasure re-sweep hit its bound; a report row may remain", userId);
    }
  }

  // AU-25: the local half is committed and idempotent; this half severs sign-in. A failure or a
  // missing relation never undoes what already committed.
  const identity = await deleteNeonIdentity(neonUserId);

  if (identity === "deleted") {
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

  // Prior failures are counted from the audit trail rather than held in memory, so the cap survives
  // a deploy or a crash. Counting only this request's rows keeps one account's history from
  // exhausting another's retries.
  const priorFailures =
    identity === "failed"
      ? await prisma.auditLog.count({
          where: {
            entity: "deletion",
            entityId: requestId,
            action: "update",
            after: { path: ["neonIdentity"], equals: "failed" },
          },
        })
      : 0;
  const attempts = priorFailures + 1;

  // `missing-relation` is terminal: the identity schema no longer matches this code, and retrying
  // cannot make a dropped table reappear. A transient failure is worth retrying, but only
  // `NEON_IDENTITY_MAX_ATTEMPTS` times — a permanent fault (bad `DATABASE_URL`, a removed DELETE
  // grant) would otherwise hold one of the ten queue slots on every run for ever.
  const terminal = identity === "missing-relation" || attempts >= NEON_IDENTITY_MAX_ATTEMPTS;

  try {
    await prisma.auditLog.create({
      data: {
        entity: "deletion",
        entityId: requestId,
        action: "update",
        actorId: null,
        after: { neonIdentity: identity, localErasureCommitted: true, attempt: attempts },
      },
    });
  } catch (err) {
    // The failure is already logged by `deleteNeonIdentity`; losing the audit row must not be a
    // second reason to fail an erasure whose local half is done.
    console.error("deletion identity audit failed", err instanceof Error ? err.name : "unknown");
  }

  if (!terminal) return false;

  // Terminal: stop occupying the queue, record why, and tell a human — the data is gone but the
  // account may still be able to sign in, which is the one state a retry cannot resolve.
  //
  // Guarded on the row still being `pending`: two cleanup runs can overlap (a retried invocation, a
  // manual run during the cron), and without the condition both would settle the request and both
  // would send the owner the same alert. Only the run whose update changed a row alerts.
  const settled = await prisma.deletionRequest.updateMany({
    where: { id: requestId, status: "pending" },
    data: { status: "completed_with_identity_error", completedAt: now },
  });
  if (settled.count === 0) return true;

  await notifyOwnerIdentityDeletionFailed({
    requestId,
    userId: neonUserId,
    outcome: identity,
    attempts,
  });
  return true;
}

/**
 * Exact calendar months, with the day clamped to the target month's last day.
 *
 * `setUTCMonth(getUTCMonth() - 24)` rolls an impossible date forward — 29 February 2028 minus two
 * years becomes 1 March 2026 — which would put a profile idle since 28 February one day *inside*
 * the window. The cutoff is a privacy promise, so it is computed exactly instead.
 */
function calendarMonthsBefore(date: Date, months: number): Date {
  const targetMonthIndex = date.getUTCMonth() - months;
  const targetYear = date.getUTCFullYear() + Math.floor(targetMonthIndex / 12);
  const targetMonth = ((targetMonthIndex % 12) + 12) % 12;
  const lastDay = new Date(Date.UTC(targetYear, targetMonth + 1, 0)).getUTCDate();
  const result = new Date(date);
  result.setUTCFullYear(targetYear, targetMonth, Math.min(date.getUTCDate(), lastDay));
  return result;
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
 * "Inactive" is not `Profile.updatedAt`. That was the Critical defect in the first version of this
 * sweep: nothing advances the timestamp for an active customer. `mirrorUser` returns early when an
 * account is unchanged, and no order or report route writes the profile, so a chart delivered
 * yesterday can still sit on a two-year-old row. Real activity is anything that *references* the
 * profile — an order or a report — so a profile is a candidate only when the row and every
 * reference to it predate the cutoff. One recent reference spares it.
 *
 * Owner decision D9 supplies the signal references cannot see: `User.lastSeenAt`, written on
 * authenticated requests. A customer who signs in to re-read an old report creates no order and no
 * report, and is now recognised as active — measured as COALESCE(lastSeenAt, createdAt).
 *
 * Disposition is the one D2 established for erasure, for the same reason:
 *  - `Order_profileAId_fkey` is ON DELETE RESTRICT. Deleting a profile an order points at would
 *    raise P2003 and roll the whole batch back, so an order-referenced profile is **scrubbed**
 *    (`SCRUBBED_PROFILE`, the one definition), soft-deleted and kept for accounting.
 *  - A profile no order references is deleted outright — the row describes nobody once scrubbed, so
 *    there is nothing left to keep it for.
 *  - The profile's **reports** are deleted with it. The promise covers them, `Report` retains the
 *    `enginePayload`, the R2 keys and the `script`, and no other sweep purges them. Their objects go
 *    through the deletion queue only after the transaction commits.
 *
 * Bounded like every other step so one run cannot hold a long transaction over the whole table;
 * `deletedAt` and the bumped `updatedAt` keep already-retired rows out of the next batch.
 *
 * Exported for the retention tests; `runCleanup` is the only production caller.
 */
export async function retireInactiveProfiles(now: Date): Promise<number> {
  const cutoff = calendarMonthsBefore(now, PROFILE_INACTIVITY_RETENTION_MONTHS);

  // The activity conditions belong in the query, not after it. Filtering the batch in memory after
  // `take: 200` (the first version of this fix) meant two hundred spared rows could fill the batch
  // and every idle profile behind them was never reached. The `none` relation filters ask the
  // database instead, and the ordering makes the batch deterministic, so the same rows cannot sit
  // in the prefix run after run.
  const recentReport = () => ({
    OR: [
      { createdAt: { gte: cutoff } },
      // A report created long ago but delivered (or re-sent) recently is still use of the profile.
      { deliveries: { some: { createdAt: { gte: cutoff } } } },
    ],
  });

  const candidates = await prisma.profile.findMany({
    where: {
      deletedAt: null,
      updatedAt: { lt: cutoff },
      ordersAsA: { none: { createdAt: { gte: cutoff } } },
      ordersAsB: { none: { createdAt: { gte: cutoff } } },
      reportsAsA: { none: recentReport() },
      reportsAsB: { none: recentReport() },
      // The owner's own sign-in signal (D9, `User.lastSeenAt`): COALESCE(lastSeenAt, createdAt)
      // must be older than the cutoff too. A null means the account has not been seen since the
      // column existed, so its created date stands in — exactly what COALESCE does.
      user: {
        OR: [{ lastSeenAt: null, createdAt: { lt: cutoff } }, { lastSeenAt: { lt: cutoff } }],
      },
    },
    select: { id: true, user: { select: { lastSeenAt: true, createdAt: true } } },
    orderBy: [{ updatedAt: "asc" }, { id: "asc" }],
    take: 200,
  });
  if (candidates.length === 0) return 0;

  const ids = candidates.map((p) => p.id);
  const candidateIds = new Set(ids);

  // Every order and report that references a candidate, with the dates that make them activity.
  const [orders, reports] = await Promise.all([
    prisma.order.findMany({
      where: { OR: [{ profileAId: { in: ids } }, { profileBId: { in: ids } }] },
      select: { profileAId: true, profileBId: true, createdAt: true },
    }),
    prisma.report.findMany({
      where: { OR: [{ profileAId: { in: ids } }, { profileBId: { in: ids } }] },
      select: {
        id: true,
        profileAId: true,
        profileBId: true,
        createdAt: true,
        deliveries: { select: { createdAt: true } },
        pdfKey: true,
        mdKey: true,
        audioKey: true,
        htmlKey: true,
      },
    }),
  ]);

  // A second check at execution time: a row can change between the select and the delete, and
  // sparing one profile costs a night's delay while retiring a live customer costs their chart.
  const active = new Set<string>();
  for (const profile of candidates) {
    const seenAt = profile.user.lastSeenAt ?? profile.user.createdAt;
    if (seenAt.getTime() >= cutoff.getTime()) active.add(profile.id);
  }
  const noteReference = (profileId: string | null, recent: boolean) => {
    if (!profileId || !candidateIds.has(profileId)) return;
    if (recent) active.add(profileId);
  };
  for (const order of orders) {
    const recent = order.createdAt.getTime() >= cutoff.getTime();
    noteReference(order.profileAId, recent);
    noteReference(order.profileBId, recent);
  }
  for (const report of reports) {
    const recent =
      report.createdAt.getTime() >= cutoff.getTime() ||
      report.deliveries.some((delivery) => delivery.createdAt.getTime() >= cutoff.getTime());
    noteReference(report.profileAId, recent);
    noteReference(report.profileBId, recent);
  }

  // Only the profiles with no recent reference at all are retired. A report is deleted along with
  // its profile whether the profile itself is scrubbed or removed.
  const retiring = ids.filter((id) => !active.has(id));
  if (retiring.length === 0) return 0;
  const retiringIds = new Set(retiring);

  const retiringReports = reports.filter(
    (report) =>
      retiringIds.has(report.profileAId) ||
      (report.profileBId !== null && retiringIds.has(report.profileBId)),
  );
  const reportIds = [...new Set(retiringReports.map((report) => report.id))];
  const keys = [
    ...new Set(
      retiringReports
        .flatMap((report) => [report.pdfKey, report.mdKey, report.audioKey, report.htmlKey])
        .filter((key): key is string => Boolean(key)),
    ),
  ];

  // Order A is RESTRICT, so an order-referenced profile is kept (scrubbed); one no order points at
  // is deleted. Report references are no reason to keep the row: those rows are deleted here too.
  const orderReferenced = new Set<string>();
  for (const order of orders) {
    if (retiringIds.has(order.profileAId)) orderReferenced.add(order.profileAId);
    if (order.profileBId && retiringIds.has(order.profileBId)) orderReferenced.add(order.profileBId);
  }
  const retained = retiring.filter((id) => orderReferenced.has(id));
  const unreferenced = retiring.filter((id) => !orderReferenced.has(id));

  const [scrubbed, deleted] = await prisma.$transaction(async (tx) => {
    if (reportIds.length > 0) {
      // Delivery and Job cascade from Report; deleting them explicitly keeps the intent visible and
      // does not rely on the constraint staying that way.
      await tx.delivery.deleteMany({ where: { reportId: { in: reportIds } } });
      await tx.report.deleteMany({ where: { id: { in: reportIds } } });
    }
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

  // Only after the rows are gone, and through the queue: the profile is already retired, so a
  // storage failure must not roll that back — the next sweep retries the object instead.
  for (const key of keys) {
    try {
      await deleteObjectOrQueue(key);
    } catch (err) {
      console.error(
        "retired report object cleanup failed",
        err instanceof Error ? err.name : "unknown",
      );
    }
  }

  return scrubbed + deleted;
}

