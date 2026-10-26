import { prisma } from "./prisma";
import { deliverReport } from "./email";
import { approveAndDeliver, ApprovalError } from "./review";

/**
 * The 10-hour delivery rule.
 *
 * A reading nobody has looked at used to wait in the queue for as long as the business took to
 * get to it — days, sometimes. That is the wrong failure mode for a product that charges up front:
 * the client has paid, and the promise on the pricing page is a *timed* one.
 *
 * So: ten hours after the order was **paid**, a reading is delivered anyway — whether it is waiting
 * for a reviewer or was claimed and abandoned by one. The reading is the engine's output either way
 * — the review is a judgement call (the 용신 override), not a rewrite —
 * so an unreviewed reading is a lesser reading, not a broken one. What changes is that it is
 * **recorded** as unreviewed (`reviewOutcome = SLA_AUTO`), so the promise can be kept honestly and
 * the owner can see how often the safety net actually fires.
 *
 * The human path is untouched: approving in the console still does everything this does, plus the
 * human judgement.
 */

/** How long a reading may wait for a person before it is released anyway. */
export const REVIEW_SLA_HOURS = 10;

/**
 * How long an auto-delivered reading may wait for its audio summary before the client hears about
 * the reading anyway. A TTS stall must not become a silent one.
 */
export const AUDIO_HOLD_FALLBACK_HOURS = 2;

/** A stuck job is one the dispatcher has not picked up for this long. Visibility, not delivery. */
export const STUCK_JOB_HOURS = 2;

/**
 * How far back a FAILED job counts as "recent".
 *
 * AU-03 (2026-10-26 audit): failed renders were never counted, so an engine that refused every
 * order left this sweep answering 200. "Recent" is deliberately short: while an outage lasts,
 * new orders keep failing and the count stays non-zero; once renders succeed again it clears
 * within four sweeps, so the workflow goes green on its own without anyone resetting state.
 */
export const RECENT_FAILURE_HOURS = 1;

/**
 * How long a paid render may stay FAILED before it is an SLA breach.
 *
 * AU-14 (2026-10-26 audit): failed renders had no deadline at all. `recentFailures` only looks one
 * hour back, so a job that exhausted its attempts yesterday produced no signal today and the paid
 * order behind it waited forever — nothing retries a FAILED job automatically. Past this window the
 * order needs a person, and the sweep says so on every run until it is dealt with.
 */
export const FAILED_RENDER_DEADLINE_HOURS = 2;

/** How many readings one sweep may release. A tick that tries to drain a backlog is a tick that times out. */
export const MAX_PER_SWEEP = 10;

export interface SlaSweepResult {
  /** Readings that had been waiting past the deadline. */
  due: number;
  /** Released by the SLA. */
  autoDelivered: number;
  /** Left alone: a person is already on them. */
  skippedInReview: number;
  /** Left alone: nothing to deliver, or the order is not paid. */
  skipped: number;
  /** Held emails released because the audio summary never arrived. */
  heldReleased: number;
  /** Jobs the dispatcher has not picked up — reported, never touched. */
  stuckJobs: number;
  /**
   * Jobs that failed within `RECENT_FAILURE_HOURS` — reported, never touched. Non-zero means the
   * engine (or the storage path) is refusing renders right now, and the endpoint answers 503.
   */
  recentFailures: number;
  /**
   * Paid renders that have been FAILED for longer than `FAILED_RENDER_DEADLINE_HOURS`. Nothing
   * retries these automatically, so each one is a paid order that will not arrive without a person.
   */
  overdueFailures: number;
  ranAt: string;
}

function hoursAgo(now: Date, hours: number): Date {
  return new Date(now.getTime() - hours * 3_600_000);
}

/**
 * Run one sweep.
 *
 * Idempotent by construction: a reading that was released is no longer `DRAFT_READY`, so the
 * second run finds nothing. Safe to call every 15 minutes, or twice at once.
 */
export async function runSlaSweep(now: Date = new Date()): Promise<SlaSweepResult> {
  const cutoff = hoursAgo(now, REVIEW_SLA_HOURS);
  const result: SlaSweepResult = {
    due: 0,
    autoDelivered: 0,
    skippedInReview: 0,
    skipped: 0,
    heldReleased: 0,
    stuckJobs: 0,
    recentFailures: 0,
    overdueFailures: 0,
    ranAt: now.toISOString(),
  };

  // 1. The readings whose deadline has passed.
  //
  // AU-14 (2026-10-26 audit): this used to ask for DRAFT_READY rows by `createdAt` and only look at
  // the order once the batch was taken. Ten rows that could never be released (unpaid, refunded)
  // filled every batch forever, so a due reading behind them was never reached. The order is part of
  // the query now, and the clock starts at payment — the client's promise begins when they pay, not
  // when the render happened to finish. A slow render must not buy a longer wait.
  //
  // IN_REVIEW rows are due at the same deadline: a reviewer who claims a reading and never comes
  // back must not hold it past the promise either.
  const due = await prisma.report.findMany({
    where: {
      status: { in: ["DRAFT_READY", "IN_REVIEW"] },
      orderId: { not: null },
      // Every transition to PAID writes `paidAt` (the Dodo webhook, the manual mark-paid route and
      // the free-order path), so this cannot silently exclude a paid order.
      order: { is: { status: "PAID", paidAt: { lte: cutoff } } },
    },
    orderBy: { createdAt: "asc" },
    take: MAX_PER_SWEEP,
    select: { id: true, status: true, createdAt: true, order: { select: { status: true } } },
  });
  result.due = due.length;

  for (const report of due) {
    // Between the query and here a DRAFT_READY row may have been picked up by a person — that is a
    // live review, so leave it. An IN_REVIEW row is not re-checked: it is already past the deadline,
    // which is exactly the stale claim this sweep exists to break.
    if (report.status === "DRAFT_READY") {
      const inReview = await prisma.report.count({ where: { id: report.id, status: "IN_REVIEW" } });
      if (inReview > 0) {
        result.skippedInReview += 1;
        continue;
      }
    }
    // A refunded or cancelled order is not a reading we deliver. The query already excludes them;
    // this is the race — a refund can land between the query and the release.
    if (!report.order || report.order.status !== "PAID") {
      result.skipped += 1;
      continue;
    }
    try {
      const approved = await approveAndDeliver(report.id, { actorId: null, outcome: "SLA_AUTO" });
      if (approved.released) result.autoDelivered += 1;
      else result.skipped += 1;
    } catch (err) {
      if (err instanceof ApprovalError) {
        result.skipped += 1;
        continue;
      }
      throw err;
    }
  }

  // 2. Auto-delivered readings whose audio summary never arrived. The client hears about the
  //    reading anyway, with the existing "your audio is being prepared" wording.
  const held = await prisma.report.findMany({
    where: {
      emailHeldForAudio: true,
      audioStatus: { not: "READY" },
      slaApprovedAt: { lte: hoursAgo(now, AUDIO_HOLD_FALLBACK_HOURS) },
    },
    orderBy: { slaApprovedAt: "asc" },
    take: MAX_PER_SWEEP,
    select: { id: true },
  });
  for (const report of held) {
    await prisma.report.update({ where: { id: report.id }, data: { emailHeldForAudio: false } });
    await deliverReport(report.id);
    result.heldReleased += 1;
  }

  // 3. Jobs the dispatcher has not picked up. Reported, never touched — a stuck job is the
  //    dispatcher's problem and a failed render, not a review.
  result.stuckJobs = await prisma.job.count({
    where: { state: "QUEUED", createdAt: { lte: hoursAgo(now, STUCK_JOB_HOURS) } },
  });

  // 4. Jobs that gave up inside the last hour. AU-03 (2026-10-26 audit): an engine refusing
  //    every render produced FAILED rows that no one counted, and this sweep answered 200.
  result.recentFailures = await prisma.job.count({
    where: { state: "FAILED", finishedAt: { gte: hoursAgo(now, RECENT_FAILURE_HOURS) } },
  });

  // 5. Paid renders that failed long enough ago to be a standing breach. AU-14 (2026-10-26 audit):
  //    a FAILED job is never retried automatically, and `recentFailures` stops looking after an
  //    hour, so yesterday's dead render was invisible today. Reported, never touched — the recovery
  //    is a person's: "Retry job" in the admin console. An erased customer's order is excluded
  //    because it is deliberately never re-rendered and would alarm forever.
  result.overdueFailures = await prisma.job.count({
    where: {
      state: "FAILED",
      kind: { in: ["GENERATE", "REGENERATE"] },
      finishedAt: { lte: hoursAgo(now, FAILED_RENDER_DEADLINE_HOURS) },
      order: { is: { status: "PAID", user: { deletedAt: null } } },
    },
  });

  return result;
}
