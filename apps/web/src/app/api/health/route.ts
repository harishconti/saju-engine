import { json } from "@/lib/api";
import { prisma } from "@/lib/prisma";
import { isR2Configured } from "@/lib/r2";
import { engineHealth } from "@/lib/engine";
import { isDodoConfigured, isDodoLiveMode } from "@/lib/dodo";
import { productIdForTier } from "@/lib/tiers";
import { isTurnstileConfigured, turnstileMode } from "@/lib/turnstile";

export const dynamic = "force-dynamic";

/** Every paid tier must have a product id or checkout throws PRODUCT_NOT_CONFIGURED. */
const PAID_TIER_IDS = ["essential", "deep", "compat-basic", "compat-deep"] as const;

/**
 * Health probe for uptime monitoring. No auth, no secrets in the response.
 * Returns 503 when anything is degraded so a monitor can alert on status code alone.
 */
export async function GET() {
  let db = false;
  try {
    await prisma.$queryRaw`SELECT 1`;
    db = true;
  } catch {
    db = false;
  }

  const storage = isR2Configured();
  const engine = await engineHealth();

  const missingProducts = PAID_TIER_IDS.filter((id) => !productIdForTier(id));
  const payments = isDodoConfigured() && missingProducts.length === 0;
  const liveMode = isDodoLiveMode();

  // The engine is the only probe that does not affect the marketing site, so it degrades rather than
  // fails. DB and storage are hard requirements; payments is too, once you intend to sell.
  const ok = db && storage && engine.ok;

  return json(
    {
      status: ok ? "ok" : "degraded",
      db,
      storage,
      engine: engine.ok,
      ...(engine.detail ? { engineDetail: engine.detail } : {}),
      payments,
      /** `test_mode` means nothing can be charged for real — a useful thing to see in one glance. */
      paymentsMode: liveMode ? "live_mode" : "test_mode",
      /**
       * Bot protection is a rollout switch, not a boolean: `off` (no verification),
       * `log` (verify + record, **never block**) and `enforce` (refuse). Surfacing it
       * here is deliberate — in an ops review, "log" must not look like "protected".
       * It does not affect `ok`: a rollout state is a known posture, not an outage.
       */
      botProtection: turnstileMode(),
      botProtectionConfigured: isTurnstileConfigured(),
      ...(missingProducts.length ? { missingProducts } : {}),
      version: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? "dev",
      checkedAt: new Date().toISOString(),
    },
    ok ? 200 : 503,
  );
}
