import { handle, json, providedSecret, timingSafeEqual } from "@/lib/api";
import { runSlaSweep } from "@/lib/sla";

export const dynamic = "force-dynamic";
export const maxDuration = 120;

/**
 * The review-queue SLA sweep.
 *
 * Releases any reading that has been waiting for a person for more than
 * `REVIEW_SLA_HOURS` (10) — and records that it was released *without* a human reading it, so
 * the promise stays honest and the owner can see how often the safety net fires.
 *
 * Auth: Vercel Cron sends `Authorization: Bearer $CRON_SECRET`; `x-maintenance-secret` is
 * accepted too, so it can be triggered by hand during an incident.
 *
 * Scheduled by `.github/workflows/sla-sweep.yml` (every 15 minutes) rather than by a Vercel cron:
 * the account is on the Hobby plan, which allows only two cron jobs and runs them once a day —
 * not soon enough for a ten-hour rule.
 *
 * Idempotent: a reading that was released is no longer `DRAFT_READY`, so a second run does
 * nothing. Safe to call twice.
 *
 * Answers **503** (keeping the JSON body) when `stuckJobs > 0` or `recentFailures > 0`, so the
 * scheduled workflow fails rather than reporting a green sweep over a broken dispatcher or an
 * engine that is refusing renders.
 */
function authorized(req: Request): boolean {
  const provided = providedSecret(req);
  const secrets = [process.env.CRON_SECRET, process.env.MAINTENANCE_SECRET].filter(
    (s): s is string => typeof s === "string" && s.length > 0,
  );
  if (secrets.length === 0) return false;
  return secrets.some((s) => timingSafeEqual(provided, s));
}

async function run(req: Request) {
  if (!authorized(req)) {
    return json({ error: "Not authorised", code: "UNAUTHORIZED" }, 401);
  }
  const result = await runSlaSweep();
  // AU-03 (2026-10-26 audit): the counts used to be reported with a 200, and the workflow's
  // `curl -f` only sees the status code — so a dispatcher that had stopped, or an engine that
  // refused every render, left the check green. The status is now the alert; the body stays.
  const degraded = result.stuckJobs > 0 || result.recentFailures > 0;
  return json({ ok: !degraded, ...result }, degraded ? 503 : 200);
}

export const GET = handle(run);
export const POST = handle(run);
