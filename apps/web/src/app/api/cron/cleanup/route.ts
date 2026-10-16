import { handle, json, providedSecret, timingSafeEqual } from "@/lib/api";
import { runCleanup } from "@/lib/cleanup";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

/** Daily maintenance sweep: lease reclaim, R2 deletion queue, purges, due deletions. */
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
  const report = await runCleanup();
  return json({ ok: true, ...report, ranAt: new Date().toISOString() });
}

export const GET = handle(run);
export const POST = handle(run);
