/**
 * Server-side pricing: what the customer is charged, and which store product charges it.
 *
 * The behaviour that matters here is the FAIL-CLOSED rule. The offer is advertised only when
 * the store can actually charge it — a missing promotional product must silence the
 * advertising, never leave a promise we cannot keep.
 */
import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { offerPriceCents, productIdForOrderPrice, promoIsLive, promoProductId } from "@/lib/pricing";
import { getTierById, PAID_TIERS } from "@/lib/tiers";

const ENV_KEYS = PAID_TIERS.map((t) => t.promoProductEnv!).filter(Boolean);

const STANDARD: Record<string, string> = {
  DODO_PRODUCT_ESSENTIAL: "pdt_standard_essential",
  DODO_PRODUCT_DEEP: "pdt_standard_deep",
  DODO_PRODUCT_COMPAT_BASIC: "pdt_standard_compat_basic",
  DODO_PRODUCT_COMPAT_DEEP: "pdt_standard_compat_deep",
};

const PROMO: Record<string, string> = {
  DODO_PRODUCT_ESSENTIAL_PROMO: "pdt_promo_essential",
  DODO_PRODUCT_DEEP_PROMO: "pdt_promo_deep",
  DODO_PRODUCT_COMPAT_BASIC_PROMO: "pdt_promo_compat_basic",
  DODO_PRODUCT_COMPAT_DEEP_PROMO: "pdt_promo_compat_deep",
};

let saved: Record<string, string | undefined> = {};

beforeEach(() => {
  saved = {};
  for (const key of [...Object.keys(STANDARD), ...Object.keys(PROMO)]) {
    saved[key] = process.env[key];
    delete process.env[key];
  }
  for (const [k, v] of Object.entries(STANDARD)) process.env[k] = v;
});

afterEach(() => {
  for (const [k, v] of Object.entries(saved)) {
    if (v === undefined) delete process.env[k];
    else process.env[k] = v;
  }
});

describe("promoIsLive", () => {
  it("is false when the promotional products are not configured — the offer fails closed", () => {
    expect(promoIsLive(new Date("2026-10-22T12:00:00Z"))).toBe(false);
  });

  it("is false when only SOME of the promotional products are configured", () => {
    process.env.DODO_PRODUCT_ESSENTIAL_PROMO = PROMO.DODO_PRODUCT_ESSENTIAL_PROMO;
    expect(promoIsLive(new Date("2026-10-22T12:00:00Z"))).toBe(false);
  });

  it("is true when every promotional product is configured and the window is open", () => {
    for (const [k, v] of Object.entries(PROMO)) process.env[k] = v;
    expect(promoIsLive(new Date("2026-10-22T12:00:00Z"))).toBe(true);
  });

  it("is false after the window closes, even with everything configured", () => {
    for (const [k, v] of Object.entries(PROMO)) process.env[k] = v;
    expect(promoIsLive(new Date("2027-01-01T00:00:00Z"))).toBe(false);
  });
});

describe("offerPriceCents", () => {
  it("charges the offer price while the offer runs", () => {
    for (const [k, v] of Object.entries(PROMO)) process.env[k] = v;
    const essential = getTierById("essential")!;
    expect(offerPriceCents(essential, new Date("2026-10-22T12:00:00Z"))).toBe(1520);
  });

  it("charges the list price after the offer ends", () => {
    for (const [k, v] of Object.entries(PROMO)) process.env[k] = v;
    const essential = getTierById("essential")!;
    expect(offerPriceCents(essential, new Date("2027-01-01T00:00:00Z"))).toBe(1900);
  });

  it("charges the list price when the store cannot charge the offer", () => {
    const essential = getTierById("essential")!;
    expect(offerPriceCents(essential, new Date("2026-10-22T12:00:00Z"))).toBe(1900);
  });
});

describe("productIdForOrderPrice", () => {
  it("charges the promotional product when the order was priced at the offer price", () => {
    for (const [k, v] of Object.entries(PROMO)) process.env[k] = v;
    expect(productIdForOrderPrice("SINGLE", "essential", 1520)).toBe("pdt_promo_essential");
  });

  it("charges the standard product when the order was priced at the list price", () => {
    for (const [k, v] of Object.entries(PROMO)) process.env[k] = v;
    expect(productIdForOrderPrice("SINGLE", "essential", 1900)).toBe("pdt_standard_essential");
  });

  it("falls back to the standard product for a tier whose promotional product is missing", () => {
    // Only the essential promotional product exists. An order priced at the offer price for a
    // tier with no promotional product must not be sent to a product that does not exist.
    process.env.DODO_PRODUCT_ESSENTIAL_PROMO = PROMO.DODO_PRODUCT_ESSENTIAL_PROMO;
    expect(productIdForOrderPrice("SINGLE", "essential", 1520)).toBe("pdt_promo_essential");
    expect(productIdForOrderPrice("SINGLE", "deep", 4400)).toBe("pdt_standard_deep");
  });

  it("keeps the compatibility tiers apart by kind", () => {
    for (const [k, v] of Object.entries(PROMO)) process.env[k] = v;
    expect(productIdForOrderPrice("COMPAT", "deep", 3600)).toBe("pdt_promo_compat_deep");
    expect(productIdForOrderPrice("SINGLE", "deep", 4400)).toBe("pdt_promo_deep");
  });
});

describe("promoProductId", () => {
  it("returns null for a tier with no promotional product configured", () => {
    const essential = getTierById("essential")!;
    expect(promoProductId(essential)).toBeNull();
  });
});
