/**
 * The launch promotion — one place to turn it on, and one place to turn it off.
 *
 * A Dodo product carries exactly ONE price (docs/webapp/07 §"Dodo Payments"), so a discount
 * cannot be a footnote in prose: the discounted price is a genuinely SEPARATE product, and this
 * module decides which of the two a customer is offered. The list price stays in the tier map
 * and the offer price is DERIVED from it, so the two can never drift apart.
 *
 * Rules this module keeps:
 *  - the offer ends at one fixed instant, and after it the claim simply disappears (no stale
 *    "20% off" banner left on the site, and no discount anyone was promised);
 *  - the discount is only ever advertised when the store can actually charge it — see
 *    `pricing.ts`, which fails CLOSED if the promotional products are not configured;
 *  - the free snapshot is never discounted. There is nothing to discount.
 *
 * This module is pure (no env, no I/O) so the client can use it to render the same numbers the
 * server will charge. The server remains the authority on what is actually charged.
 */

/** The offer. Change `percentOff` or `endsAt` here and the whole site follows. */
export const PROMO = {
  id: "launch-20",
  percentOff: 20,
  /**
   * The instant the offer closes, exclusive: the end of 31 December 2026 in US Pacific, which
   * is the day the copy ("through 31 December") promises. After it the offer is simply gone —
   * no code change, no stale claim.
   *
   * Expressed as an instant, not a UTC date. A date compare closed the offer at 16:00 PST on
   * the 31st, taking the last eight hours of the advertised day away from every customer in
   * the Americas (AU-20). Comparing instants also means the switch flips at the same moment
   * for every viewer, so the client and the server never disagree.
   */
  endsAt: "2027-01-01T08:00:00Z",
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
 * Is the offer running? Compared as instants against the one end constant, so the answer is
 * the same in every time zone and the client and the server always agree (AU-20).
 *
 * `now` is injectable so the boundary can be tested without freezing the clock.
 */
export function promoActive(now: Date = new Date()): boolean {
  return now.getTime() < Date.parse(PROMO.endsAt);
}

/** The offer price for a list price, in cents. Rounded, never below zero. */
export function promoPriceCents(listCents: number): number {
  if (listCents <= 0) return listCents;
  return Math.round((listCents * (100 - PROMO.percentOff)) / 100);
}

/**
 * "31 December 2026" — the last day the offer covers, for copy that states it.
 *
 * Derived from the same end instant so the label can never drift from the window it describes:
 * one millisecond before the boundary is still 31 December in US Pacific.
 */
export function promoEndsLabel(): string {
  return new Date(Date.parse(PROMO.endsAt) - 1).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "America/Los_Angeles",
  });
}
