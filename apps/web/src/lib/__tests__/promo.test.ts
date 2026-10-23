/**
 * The launch promotion (20% off every paid report, ends 2026-12-31).
 *
 * The rule these tests protect is the one the whole feature rests on: **the number the site
 * advertises is the number the store charges.** A Dodo product carries exactly one price, so
 * the offer price must be the list price minus exactly 20% — the same arithmetic Dodo applies
 * with its own 20% discount on the promotional products.
 */
import { describe, expect, it } from "vitest";

import { PROMO, promoActive, promoBadgeLabel, promoEndsLabel, promoPriceCents } from "@/lib/promo";
import { PAID_TIERS, TIERS } from "@/lib/tiers";

describe("promo arithmetic", () => {
  it("takes exactly 20% off every paid tier, with no rounding drift", () => {
    for (const tier of PAID_TIERS) {
      const offer = promoPriceCents(tier.priceCents);
      // The offer price must be exactly what Dodo charges for a 20% discount on the list
      // price — 1900 → 1520, 5500 → 4400, 2400 → 1920, 4500 → 3600.
      expect(offer).toBe(Math.round((tier.priceCents * (100 - PROMO.percentOff)) / 100));
      expect(tier.priceCents % 10).toBe(0); // 20% of every list price is exact
      expect(offer).toBeLessThan(tier.priceCents);
    }
  });

  it("matches the prices the promotional Dodo products were created with", () => {
    // The four products created in the Dodo dashboard carry `discount: 20` on the list price.
    // If the tier map changes, this test is the reminder that the store has to change too.
    expect(promoPriceCents(1900)).toBe(1520);
    expect(promoPriceCents(5500)).toBe(4400);
    expect(promoPriceCents(2400)).toBe(1920);
    expect(promoPriceCents(4500)).toBe(3600);
  });

  it("never discounts the free snapshot", () => {
    const sample = TIERS.find((t) => t.id === "sample")!;
    expect(sample.priceCents).toBe(0);
    expect(promoPriceCents(sample.priceCents)).toBe(0);
  });
});

describe("the offer window", () => {
  it("is open before the end date and closed after it", () => {
    expect(promoActive(new Date("2026-10-22T12:00:00Z"))).toBe(true);
    expect(promoActive(new Date("2026-12-31T23:59:59Z"))).toBe(true);
    expect(promoActive(new Date("2027-01-01T00:00:00Z"))).toBe(false);
  });

  it("states the end date in copy", () => {
    expect(promoEndsLabel()).toBe("31 December 2026");
    expect(promoBadgeLabel()).toBe("20% off");
  });
});

describe("the tier map", () => {
  it("gives every paid tier a promotional product, so a discount is never half-applied", () => {
    for (const tier of PAID_TIERS) {
      expect(tier.promoProductEnv, `${tier.id} has no promotional product`).toBeTruthy();
      expect(tier.promoProductEnv).not.toBe(tier.productEnv);
    }
  });
});
