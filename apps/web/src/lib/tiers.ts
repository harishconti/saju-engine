/**
 * THE tier map. Single source of truth for names, prices, page counts, and Dodo products.
 *
 * A price change is a one-file change — update here, the Dodo product, and
 * docs/openwiki/products/reports.md. Never restate a price in prose or in a component.
 *
 * Normative reference: docs/webapp/02-data-model.md §"Tier map"
 */

export type TierKind = "SINGLE" | "COMPAT";

export interface Tier {
  /** Stable id used in the UI, API, and DB `Order.tier`. */
  id: string;
  /** Client-facing name. */
  name: string;
  kind: TierKind;
  /** The tier string the engine expects. */
  engineTier: string;
  /**
   * The LIST price — what the customer pays when no promotion is running.
   *
   * A promotion is not a different number in this map: the offer price is DERIVED from this one
   * (see `promo.ts`) and charged through a separate Dodo product, so the two can never drift.
   */
  priceCents: number;
  currency: "USD";
  pages: string;
  tagline: string;
  /** What the client receives, one bullet per line. */
  includes: string[];
  /** Env var holding the Dodo Payments product id. Absent for the free sample. */
  productEnv?: string;
  /**
   * Env var holding the Dodo Payments product id for the PROMOTIONAL price of this tier.
   *
   * A Dodo product carries exactly one price, so a discount needs its own product. While the
   * promotion runs, checkout uses this product and charges the discounted price; after it, the
   * standard product and the list price are used again — no code change on the day it ends.
   */
  promoProductEnv?: string;
  /** Paid tiers are reviewed before delivery (decision D5). */
  requiresReview: boolean;
  /** Marketing emphasis. */
  highlight?: boolean;
}

export const TIERS: Tier[] = [
  {
    id: "sample",
    name: "The Hook",
    kind: "SINGLE",
    engineTier: "sample",
    priceCents: 0,
    currency: "USD",
    pages: "~1 page",
    tagline: "A free first look at your chart",
    includes: [
      "Your four pillars",
      "Element balance",
      "Day Master",
      "Lucky colors, directions, and numbers",
    ],
    requiresReview: false,
  },
  {
    id: "essential",
    name: "The Essential Report",
    kind: "SINGLE",
    engineTier: "essential",
    priceCents: 1900,
    currency: "USD",
    pages: "6–7 pages",
    tagline: "Your chart, read properly",
    includes: [
      "Everything in the free sample",
      "A short Day Master portrait",
      "Career and wealth overview",
      "Major-luck (대운) table",
      "Lucky attributes reference card",
    ],
    productEnv: "DODO_PRODUCT_ESSENTIAL",
    promoProductEnv: "DODO_PRODUCT_ESSENTIAL_PROMO",
    requiresReview: true,
  },
  {
    id: "deep",
    name: "The Deep Destiny Report",
    kind: "SINGLE",
    engineTier: "deep",
    priceCents: 5500,
    currency: "USD",
    pages: "25–30 pages",
    tagline: "The full reading, argued from the classical sources",
    includes: [
      "Everything in Essential",
      "Full Day Master portrait",
      "Relationships",
      "Health and vitality",
      "Business and launch timing",
      "Year-by-year windows",
      "Full practical guidance",
    ],
    productEnv: "DODO_PRODUCT_DEEP",
    promoProductEnv: "DODO_PRODUCT_DEEP_PROMO",
    requiresReview: true,
    highlight: true,
  },
  {
    id: "compat-basic",
    name: "Compatibility Snapshot",
    kind: "COMPAT",
    engineTier: "basic",
    priceCents: 2400,
    currency: "USD",
    pages: "~4 pages",
    tagline: "Two charts, one score",
    includes: [
      "Composite 0–100 score with a four-band verdict",
      "Four-pillar glance for both people",
      "The four most decisive sub-systems",
      "Condensed practical guidance",
    ],
    productEnv: "DODO_PRODUCT_COMPAT_BASIC",
    promoProductEnv: "DODO_PRODUCT_COMPAT_BASIC_PROMO",
    requiresReview: true,
  },
  {
    id: "compat-deep",
    name: "Deep Compatibility",
    kind: "COMPAT",
    engineTier: "deep",
    priceCents: 4500,
    currency: "USD",
    pages: "9–10 pages",
    tagline: "The full 궁합 reading across all eleven sub-systems",
    includes: [
      "Everything in the Snapshot",
      "All 11 sub-system cards",
      "Per-partner element balance and Day Master snapshots",
      "Major-luck timelines for both",
      "Year-by-year couple timing overlay",
    ],
    productEnv: "DODO_PRODUCT_COMPAT_DEEP",
    promoProductEnv: "DODO_PRODUCT_COMPAT_DEEP_PROMO",
    requiresReview: true,
    highlight: true,
  },
];

/** Engine legacy aliases. Accepted by the engine; never surfaced in the UI or the store. */
export const LEGACY_TIER_ALIASES: Record<string, string> = {
  spark: "essential",
  reading: "deep",
  fullmap: "deep",
  companion: "companion", // exists in the engine, deliberately not offered (docs/webapp/00-overview.md)
};

/**
 * Resolve a tier by our own id, accepting engine legacy aliases.
 *
 * Note: match on `id`, never on `engineTier` — `compat-deep` and the single-chart `deep` tier both
 * send the engine tier "deep"; the request's `kind` disambiguates them downstream.
 */
export function getTier(id: string | null | undefined): Tier | null {
  if (!id) return null;
  if (id === "companion") return null; // engine-supported, deliberately not offered
  const alias = LEGACY_TIER_ALIASES[id];
  const resolved = alias && alias !== "companion" ? alias : id;
  return TIERS.find((t) => t.id === resolved) ?? null;
}

export function getTierById(id: string): Tier | null {
  return TIERS.find((t) => t.id === id) ?? null;
}

/**
 * Resolve by the pair actually stored in the database (`Order.tier` / `Report.tier` hold the ENGINE
 * tier, with `kind` disambiguating): SINGLE+deep is the Deep Destiny Report, COMPAT+deep is Deep
 * Compatibility. Storing the engine value means the engine payload needs no translation.
 */
export function tierFor(kind: "SINGLE" | "COMPAT", engineTier: string): Tier | null {
  return TIERS.find((t) => t.kind === kind && t.engineTier === engineTier) ?? null;
}

export function tierNameFor(kind: "SINGLE" | "COMPAT", engineTier: string): string {
  return tierFor(kind, engineTier)?.name ?? "Saju reading";
}

export const PAID_TIERS = TIERS.filter((t) => t.priceCents > 0);
export const SINGLE_TIERS = TIERS.filter((t) => t.kind === "SINGLE");
export const COMPAT_TIERS = TIERS.filter((t) => t.kind === "COMPAT");

export function isCompatTier(id: string): boolean {
  return getTierById(id)?.kind === "COMPAT";
}

/** Server-side price resolution. The client's number is always discarded. */
/**
 * Does this tier skip the human review step?
 *
 * `requiresReview: false` means the report is delivered the moment it renders — no queue, no
 * reviewer. True of the free tier only, and deliberately so: the snapshot is the proof the product
 * works, and it carries almost no interpretive surface (the judgement lives in the paid prose).
 *
 * Until this was read by anything, `requiresReview` was a comment: `processClaimedJob` always set
 * `DRAFT_READY`, so any free tier added later would have silently joined the review queue.
 */
export function autoDelivers(kind: "SINGLE" | "COMPAT", engineTier: string): boolean {
  return tierFor(kind, engineTier)?.requiresReview === false;
}

export function priceForTier(id: string): { cents: number; currency: "USD" } | null {
  const tier = getTierById(id);
  if (!tier) return null;
  return { cents: tier.priceCents, currency: tier.currency };
}

export function productId(tier: Tier | null): string | null {
  if (!tier?.productEnv) return null;
  return process.env[tier.productEnv] ?? null;
}

/** Convenience for the UI-tier id form. */
export function productIdForTier(id: string): string | null {
  return productId(getTierById(id));
}

/**
 * ⚠️ Use this for anything read out of the database. `Order.tier` / `Report.tier` store the ENGINE
 * tier, and 'deep' is ambiguous on its own — the SINGLE deep tier and Deep Compatibility share it.
 * Resolving by (kind, tier) is the only correct lookup.
 */
export function productIdForOrder(kind: "SINGLE" | "COMPAT", engineTier: string): string | null {
  return productId(tierFor(kind, engineTier));
}
