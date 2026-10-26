import { handle, json, providedSecret, timingSafeEqual } from "@/lib/api";
import { runDispatchTick } from "@/lib/fulfilment";

export const dynamic = "force-dynamic";
/** Vercel functions default to 300s on Pro; a tick only needs a fraction of that. */
export const maxDuration = 300;

/**
 * Job dispatcher.
 *
 * Schedule: every 15 minutes from `.github/workflows/sla-sweep.yml` (decision D4, AU-13 — the audit
 * found a queued `VOICE` job that had waited since 2026-10-26 06:36 while this comment claimed a
 * per-minute cron). `vercel.json` keeps a DAILY cron as a harmless fallback; the account is on the
 * Hobby plan, which refuses any cron that runs more than once a day, so a per-minute schedule cannot
 * be deployed here.
 *
 * Auth: Vercel Cron sends `Authorization: Bearer $CRON_SECRET`; we also accept
 * `x-maintenance-secret` so an operator can trigger a tick by hand during an incident.
 *
 * Bounded at 3 jobs per tick by design: a tick that tries to drain a whole backlog gets killed
 * mid-flight, which is exactly what leases exist to survive.
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
  const result = await runDispatchTick(3);
  return json({ ok: true, ...result, ranAt: new Date().toISOString() });
}

export const GET = handle(run);
export const POST = handle(run);
