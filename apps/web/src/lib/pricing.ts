/**
 * Server-side pricing: what the customer is actually charged, and which store product it is
 * charged through.
 *
 * The rule this file exists to enforce: **the site never advertises a discount the store cannot
 * charge.** A Dodo product carries exactly one price, so the promotional price is a separate
 * product (`tier.promoProductEnv`). If those products are not configured, the offer is not
 * advertised at all — the site falls back to the list price. That is the fail-closed direction:
 * a missing env var loses a promotion, it never produces a promise we cannot keep.
 *
 * This module reads `process.env`, so it is server-only. The pure parts (the offer's dates and
 * the arithmetic) live in `promo.ts`, which the client also uses to render the same numbers.
 */
import "server-only";
import { PAID_TIERS, type Tier, tierFor } from "./tiers";
import { promoActive, promoPriceCents } from "./promo";

/** The Dodo product id for the promotional price of a tier, or null if it isn't configured. */
export function promoProductId(tier: Tier): string | null {
  const env = tier.promoProductEnv;
  if (!env) return null;
  return process.env[env]?.trim() || null;
}

/**
 * Is the offer running AND chargeable?
 *
 * Two conditions, both required: the date window is open, and every paid tier has its
 * promotional product configured. The second condition is what makes this fail closed.
 */
export function promoIsLive(now: Date = new Date()): boolean {
  if (!promoActive(now)) return false;
  return PAID_TIERS.every((tier) => promoProductId(tier) !== null);
}

/** The price charged for a tier right now: the offer price while it runs, the list price after. */
export function offerPriceCents(tier: Tier, now: Date = new Date()): number {
  if (tier.priceCents === 0) return 0;
  return promoIsLive(now) ? promoPriceCents(tier.priceCents) : tier.priceCents;
}

/**
 * The store product to charge for an order.
 *
 * Driven by the price ALREADY RECORDED on the order, not by the clock: a customer who started
 * checkout before the window closed keeps the price they were shown. A recorded price that
 * matches the promotional price is charged through the promotional product; anything else goes
 * through the standard product.
 */
export function productIdForOrderPrice(
  kind: "SINGLE" | "COMPAT",
  engineTier: string,
  priceCents: number,
): string | null {
  const tier = tierFor(kind, engineTier);
  if (!tier) return null;
  if (tier.priceCents > 0 && priceCents === promoPriceCents(tier.priceCents)) {
    const promo = promoProductId(tier);
    if (promo) return promo;
  }
  if (!tier.productEnv) return null;
  return process.env[tier.productEnv]?.trim() || null;
}
