import type { Job } from "@prisma/client";
import { prisma } from "./prisma";
import { notifyOwnerEngineFailure } from "./owner-alert";

/**
 * Lease-based job queue, Postgres-native.
 *
 * `FOR UPDATE SKIP LOCKED` makes concurrent dispatcher invocations safe (each tick gets a different
 * job). `leaseUntil` makes a crashed dispatcher recoverable — the next tick reclaims the job.
 *
 * Why a queue at all: docs/webapp/01-architecture.md §"Why a job queue instead of doing the work inline".
 */

export const LEASE_MS = 5 * 60 * 1000;
export const STALE_LEASE_MS = 15 * 60 * 1000;

/**
 * Claim the oldest queued job, or reclaim one whose lease has expired. Returns null if none.
 *
 * ⚠️ The RETURNING list is written out explicitly and must stay that way. It used to be
 * `RETURNING *`, which broke in production with `0A000: cached plan must not change result
 * type` — Postgres had cached the statement's result shape when the table had fewer columns,
 * and the next `ALTER TABLE ... ADD COLUMN` invalidated it. Naming the columns means a future
 * migration cannot break job claiming. If you add a field here, add it to the list.
 */
export async function claimJob(worker: string): Promise<Job | null> {
  const rows = await prisma.$queryRaw<Job[]>`
    UPDATE "Job"
       SET state = 'RUNNING',
           attempts = attempts + 1,
           "leaseUntil" = now() + interval '5 minutes',
           "startedAt" = coalesce("startedAt", now()),
           worker = ${worker}
     WHERE id = (
       SELECT id FROM "Job"
        WHERE state = 'QUEUED'
           OR (state = 'RUNNING' AND "leaseUntil" < now())
        ORDER BY "createdAt"
        FOR UPDATE SKIP LOCKED
        LIMIT 1
     )
    RETURNING id, "orderId", "reportId", kind, state, attempts, "maxAttempts",
              "leaseUntil", worker, payload, "lastError", "startedAt", "finishedAt", "createdAt"`;
  return rows[0] ?? null;
}

export async function completeJob(jobId: string): Promise<void> {
  await prisma.job.update({
    where: { id: jobId },
    data: { state: "SUCCEEDED", finishedAt: new Date(), leaseUntil: null, lastError: null },
  });
}

/** Permanent failure: retrying cannot fix bad input. */
export async function failJob(jobId: string, error: string): Promise<void> {
  await prisma.job.update({
    where: { id: jobId },
    data: { state: "FAILED", finishedAt: new Date(), leaseUntil: null, lastError: error },
  });
}

/** Transient failure: release the lease so the next tick retries. */
export async function requeueJob(jobId: string, error: string): Promise<void> {
  await prisma.job.update({
    where: { id: jobId },
    data: { state: "QUEUED", leaseUntil: null, lastError: error },
  });
}

/** Reclaim jobs whose worker died. Called by the cleanup cron. */
export async function reclaimStaleJobs(): Promise<{ requeued: number; failed: number }> {
  const cutoff = new Date(Date.now() - STALE_LEASE_MS);

  const stale = await prisma.job.findMany({
    where: { state: "RUNNING", leaseUntil: { lt: cutoff } },
    select: { id: true, orderId: true, kind: true, attempts: true, maxAttempts: true },
  });

  let requeued = 0;
  let failed = 0;
  for (const job of stale) {
    if (job.attempts >= job.maxAttempts) {
      await failJob(job.id, "lease expired after max attempts");
      // AU-03 (2026-10-26 audit): a generate job that dies mid-render is a paid order that will
      // not arrive. This is a `failJob` on the same path as the dispatcher's, so it alerts too.
      if (job.kind !== "VOICE") {
        try {
          await notifyOwnerEngineFailure({
            orderId: job.orderId,
            code: "LEASE_EXPIRED",
            attempts: job.attempts,
          });
        } catch (err) {
          // A notification problem is never a delivery problem.
          console.error("engine failure alert threw:", err instanceof Error ? err.message : "unknown");
        }
      }
      failed++;
    } else {
      await requeueJob(job.id, "lease expired; reclaimed");
      requeued++;
    }
  }
  return { requeued, failed };
}

export async function jobStats() {
  const rows = await prisma.job.groupBy({
    by: ["state"],
    _count: { _all: true },
    _min: { createdAt: true },
  });
  return rows.map((r) => ({ state: r.state, count: r._count._all, oldest: r._min.createdAt }));
}

/** Purge finished jobs older than 90 days (cleanup cron). */
export async function purgeOldJobs(): Promise<number> {
  const cutoff = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
  const res = await prisma.job.deleteMany({
    where: { state: { in: ["SUCCEEDED", "FAILED"] }, createdAt: { lt: cutoff } },
  });
  return res.count;
}
