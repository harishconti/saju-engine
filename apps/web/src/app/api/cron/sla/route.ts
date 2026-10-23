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
  return json({ ok: true, ...result });
}

export const GET = handle(run);
export const POST = handle(run);
