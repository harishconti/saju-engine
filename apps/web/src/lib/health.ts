import { prisma } from "@/lib/prisma";
import { isR2Configured } from "@/lib/r2";
import { engineHealth } from "@/lib/engine";
import { isDodoConfigured, isDodoLiveMode } from "@/lib/dodo";
import { productIdForTier } from "@/lib/tiers";
import { isTurnstileConfigured, turnstileMode } from "@/lib/turnstile";

/**
 * The health probe, shared by the public and authorised views.
 *
 * AU-31 (2026-10-26 audit): `GET /api/health` published `engineDetail`, `missingProducts` and the
 * payment mode to anyone, and called the engine on every hit. The public body is now minimal
 * (`ok`/`status`/version/checkedAt) and the operational detail lives behind `/api/health/detail`;
 * this module is the one implementation, so the two cannot disagree about what "degraded" means.
 */

/** Every paid tier must have a product id or checkout throws PRODUCT_NOT_CONFIGURED. */
const PAID_TIER_IDS = ["essential", "deep", "compat-basic", "compat-deep"] as const;

/**
 * How long an engine probe answer is reused.
 *
 * The engine is the only network probe here and it cold-starts in ~1–2 s. The documented check
 * interval is 5–15 minutes, but a few monitors (or a person refreshing during an incident) can
 * still add up. A minute bounds the staleness while making a burst cost one probe. Deliberately
 * process-local: a serverless instance is the unit that would otherwise hammer the engine, and a
 * shared cache would need another piece of infrastructure for a read-only probe.
 */
export const ENGINE_PROBE_TTL_MS = 60_000;

export interface EngineProbe {
  ok: boolean;
  detail?: string;
}

interface CacheEntry {
  at: number;
  value: EngineProbe;
}

let engineCache: CacheEntry | null = null;

/**
 * The engine's readiness, cached for `ENGINE_PROBE_TTL_MS`.
 *
 * Both answers are cached: during an outage the last thing the engine needs is every health check
 * retrying a dead connection. `now` is a parameter so the expiry is testable without sleeping.
 */
export async function probeEngine(now: number = Date.now()): Promise<EngineProbe> {
  if (engineCache && now - engineCache.at < ENGINE_PROBE_TTL_MS) return engineCache.value;
  const value = await engineHealth();
  engineCache = { at: now, value };
  return value;
}

/** Forget the cached probe. Tests only — a real instance should keep the cache. */
export function resetHealthProbeCacheForTests(): void {
  engineCache = null;
}

export interface HealthSnapshot {
  /** Everything the monitor needs: false when any hard requirement or the engine is down. */
  ok: boolean;
  status: "ok" | "degraded";
  db: boolean;
  storage: boolean;
  engine: boolean;
  engineDetail?: string;
  payments: boolean;
  paymentsMode: "live_mode" | "test_mode";
  botProtection: string;
  botProtectionConfigured: boolean;
  missingProducts: string[];
  version: string;
  checkedAt: string;
}

/** Run every probe. The DB is checked on each call; the engine is cached (see above). */
export async function runHealthProbe(): Promise<HealthSnapshot> {
  let db = false;
  try {
    await prisma.$queryRaw`SELECT 1`;
    db = true;
  } catch {
    db = false;
  }

  const storage = isR2Configured();
  const engine = await probeEngine();

  const missingProducts: string[] = PAID_TIER_IDS.filter((id) => !productIdForTier(id));
  const payments = isDodoConfigured() && missingProducts.length === 0;
  const liveMode = isDodoLiveMode();

  // The engine is the only probe that does not affect the marketing site, so it degrades rather than
  // fails. DB and storage are hard requirements; payments is too, once you intend to sell.
  const ok = db && storage && engine.ok;

  return {
    ok,
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
     * `log` (verify + record, **never block**) and `enforce` (refuse). Surfacing it is deliberate —
     * in an ops review, "log" must not look like "protected". It does not affect `ok`: a rollout
     * state is a known posture, not an outage.
     */
    botProtection: turnstileMode(),
    botProtectionConfigured: isTurnstileConfigured(),
    missingProducts,
    version: process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 7) ?? "dev",
    checkedAt: new Date().toISOString(),
  };
}

/** The public body: no operational detail, no configuration, no payment state. */
export interface PublicHealth {
  ok: boolean;
  status: "ok" | "degraded";
  version: string;
  checkedAt: string;
}

export function publicHealth(snapshot: HealthSnapshot): PublicHealth {
  return {
    ok: snapshot.ok,
    status: snapshot.status,
    version: snapshot.version,
    checkedAt: snapshot.checkedAt,
  };
}
