import { json } from "@/lib/api";
import { publicHealth, runHealthProbe } from "@/lib/health";

export const dynamic = "force-dynamic";

/**
 * Public health probe for uptime monitoring.
 *
 * AU-31 (2026-10-26 audit): this used to answer with `db`, `storage`, `engine`, `engineDetail`,
 * `payments`, `paymentsMode`, `botProtection` and `missingProducts` to anyone — a map of which
 * environment variables are wrong, and whether the deployment can take real money. The public body
 * is now just enough for a monitor (`ok`, `status`, `version`, `checkedAt`); the diagnostic detail
 * moved to the authorised `/api/health/detail`, and the engine probe is cached so repeated hits do
 * not call the engine every time.
 *
 * Still answers **503** when anything is degraded, so a monitor can alert on the status code alone
 * (AU-03: a green probe over an engine that refused every render is what hid the October outage).
 */
export async function GET() {
  const snapshot = await runHealthProbe();
  return json(publicHealth(snapshot), snapshot.ok ? 200 : 503);
}
