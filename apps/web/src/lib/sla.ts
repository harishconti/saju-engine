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
 * So: ten hours after a reading becomes reviewable, it is delivered anyway. The reading is the
 * engine's output either way — the review is a judgement call (the 용신 override), not a rewrite —
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
    ranAt: now.toISOString(),
  };

  // 1. The readings whose deadline has passed.
  const due = await prisma.report.findMany({
    where: {
      status: "DRAFT_READY",
      createdAt: { lte: cutoff },
      orderId: { not: null },
    },
    orderBy: { createdAt: "asc" },
    take: MAX_PER_SWEEP,
    select: { id: true, createdAt: true, order: { select: { status: true } } },
  });
  result.due = due.length;

  for (const report of due) {
    // A person already has this one.
    const inReview = await prisma.report.count({ where: { id: report.id, status: "IN_REVIEW" } });
    if (inReview > 0) {
      result.skippedInReview += 1;
      continue;
    }
    // A refunded or cancelled order is not a reading we deliver.
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

  return result;
}
