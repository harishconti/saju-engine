/**
 * The launch promotion — one place to turn it on, and one place to turn it off.
 *
 * A Dodo product carries exactly ONE price (docs/webapp/07 §"Dodo Payments"), so a discount
 * cannot be a footnote in prose: the discounted price is a genuinely SEPARATE product, and this
 * module decides which of the two a customer is offered. The list price stays in the tier map
 * and the offer price is DERIVED from it, so the two can never drift apart.
 *
 * Rules this module keeps:
 *  - the offer has an end date, and after it the claim simply disappears (no stale "20% off"
 *    banner left on the site, and no discount anyone was promised);
 *  - the discount is only ever advertised when the store can actually charge it — see
 *    `pricing.ts`, which fails CLOSED if the promotional products are not configured;
 *  - the free snapshot is never discounted. There is nothing to discount.
 *
 * This module is pure (no env, no I/O) so the client can use it to render the same numbers the
 * server will charge. The server remains the authority on what is actually charged.
 */

/** The offer. Change `percentOff` or `endsOn` here and the whole site follows. */
export const PROMO = {
  id: "launch-20",
  percentOff: 20,
  /** Inclusive, UTC date. After this the offer is simply gone — no code change, no stale claim. */
  endsOn: "2026-11-30",
} as const;

/** "20% off" — the badge wording. Derived so it can never disagree with the discount. */
export function promoBadgeLabel(): string {
  return `${PROMO.percentOff}% off`;
}

/** "every report" — what the offer covers. */
export function promoScopeLabel(): string {
  return "every paid report";
}

/**
 * Is the offer running? Date only (UTC), so the switch does not flip at a local midnight and
 * the client and the server always agree about which day it is.
 */
export function promoActive(now: Date = new Date()): boolean {
  return now.toISOString().slice(0, 10) <= PROMO.endsOn;
}

/** The offer price for a list price, in cents. Rounded, never below zero. */
export function promoPriceCents(listCents: number): number {
  if (listCents <= 0) return listCents;
  return Math.round((listCents * (100 - PROMO.percentOff)) / 100);
}

/** "30 November 2026" — the end date, for copy that states it. */
export function promoEndsLabel(): string {
  return new Date(`${PROMO.endsOn}T00:00:00Z`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  });
}
