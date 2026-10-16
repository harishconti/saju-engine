import { prisma } from "./prisma";
import { ApiError } from "./api";

/**
 * Postgres-backed fixed-window rate limiting.
 *
 * Deliberately not Redis/Upstash: the whole system keeps operational state in Postgres
 * (docs/webapp/01-architecture.md, decision D9). One row per bucket per window.
 */

export const WINDOW = {
  minute: 60_000,
  hour: 3_600_000,
  day: 86_400_000,
};

/**
 * Increment the bucket for the current window; throw 429 when the limit is exceeded.
 *
 * @param bucket  e.g. `sample:203.0.113.5` or `order:user_123`
 * @param limit   max requests allowed inside the window
 * @param windowMs window length
 */
export async function rateLimit(bucket: string, limit: number, windowMs: number): Promise<void> {
  if (limit <= 0) return;

  const windowStart = new Date(Math.floor(Date.now() / windowMs) * windowMs);

  const row = await prisma.rateLimit.upsert({
    where: { bucket_windowStart: { bucket, windowStart } },
    update: { count: { increment: 1 } },
    create: { bucket, windowStart, count: 1 },
    select: { count: true },
  });

  if (row.count > limit) {
    throw new ApiError(429, "RATE_LIMITED", "Too many requests, please slow down");
  }
}

/** Purge windows older than one hour (called by the daily cleanup cron). */
export async function purgeOldRateLimits(): Promise<number> {
  const cutoff = new Date(Date.now() - WINDOW.hour);
  const res = await prisma.rateLimit.deleteMany({ where: { windowStart: { lt: cutoff } } });
  return res.count;
}
