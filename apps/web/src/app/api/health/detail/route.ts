import { json, providedSecret, timingSafeEqual } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
import { isAdminEmail } from "@/lib/roles";
import { runHealthProbe } from "@/lib/health";

export const dynamic = "force-dynamic";

/**
 * The authorised health detail view.
 *
 * AU-31 (2026-10-26 audit): the public `/api/health` body was the operator's whole diagnosis — *which*
 * configuration gap is degrading the service (`engineDetail`), which products are missing, whether
 * the deployment is in live or test payment mode, and the Turnstile rollout state. That is exactly
 * what an attacker wants and exactly what a monitor does not need, so it lives here instead.
 *
 * Two ways in:
 *  - `Authorization: Bearer $HEALTH_DETAIL_TOKEN` (or `x-maintenance-secret`), for an uptime monitor
 *    or an operator during an incident. If the variable is unset, the token path is closed.
 *  - An admin session, via the same three-part gate `requireAdmin` uses (role, allowlisted address,
 *    verified email), so the console can show it without a shared secret.
 *
 * Everything else is a 401 with no body detail. The status code still says 503 when degraded, for
 * the same reason the public probe does.
 */
async function authorized(req: Request): Promise<boolean> {
  const expected = process.env.HEALTH_DETAIL_TOKEN?.trim();
  if (expected && timingSafeEqual(providedSecret(req), expected)) return true;

  try {
    const user = await getCurrentUser();
    return Boolean(
      user && user.role === "ADMIN" && isAdminEmail(user.email) && user.emailVerified,
    );
  } catch {
    // A database failure while resolving the session is not authorisation. Fall through to 401;
    // the public probe (which reports the DB failure) is the monitor's signal.
    return false;
  }
}

export async function GET(req: Request) {
  if (!(await authorized(req))) {
    // No detail in the refusal: which configuration is wrong is the secret being protected.
    return json({ error: "Not authorised", code: "UNAUTHORIZED" }, 401);
  }

  const snapshot = await runHealthProbe();
  return json(snapshot, snapshot.ok ? 200 : 503);
}
