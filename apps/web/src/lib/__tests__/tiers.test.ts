import { describe, expect, it } from "vitest";
import {
  COMPAT_TIERS,
  LEGACY_TIER_ALIASES,
  PAID_TIERS,
  SINGLE_TIERS,
  TIERS,
  getTier,
  getTierById,
  isCompatTier,
  priceForTier,
  tierFor,
  tierNameFor,
} from "../tiers";

describe("tier map", () => {
  it("offers exactly the documented tiers", () => {
    expect(TIERS.map((t) => t.id)).toEqual([
      "sample",
      "essential",
      "deep",
      "compat-basic",
      "compat-deep",
    ]);
  });

  it("keeps prices on the tier map, not in prose", () => {
    expect(getTierById("sample")?.priceCents).toBe(0);
    expect(getTierById("essential")?.priceCents).toBe(1900);
    expect(getTierById("deep")?.priceCents).toBe(5500);
    expect(getTierById("compat-basic")?.priceCents).toBe(2400);
    expect(getTierById("compat-deep")?.priceCents).toBe(4500);
  });

  it("does not offer the companion subscription", () => {
    expect(getTierById("companion")).toBeNull();
    expect(getTier("companion")).toBeNull();
  });

  it("resolves a tier for the (kind, engine tier) pair stored in the database", () => {
    // 'deep' alone is ambiguous — this is exactly the bug the pair lookup prevents.
    expect(tierFor("SINGLE", "deep")?.id).toBe("deep");
    expect(tierFor("COMPAT", "deep")?.id).toBe("compat-deep");
    expect(tierFor("SINGLE", "basic")).toBeNull();
    expect(tierFor("COMPAT", "essential")).toBeNull();
  });

  it("maps legacy engine aliases", () => {
    expect(getTier("spark")?.id).toBe("essential");
    expect(getTier("reading")?.id).toBe("deep");
    expect(getTier("fullmap")?.id).toBe("deep");
    expect(LEGACY_TIER_ALIASES.spark).toBe("essential");
  });

  it("reports names for stored engine tiers", () => {
    expect(tierNameFor("COMPAT", "deep")).toBe("Deep Compatibility");
    expect(tierNameFor("SINGLE", "deep")).toBe("The Deep Destiny Report");
    expect(tierNameFor("SINGLE", "nonsense")).toBe("Saju reading");
  });

  it("classifies compat tiers", () => {
    expect(isCompatTier("compat-deep")).toBe(true);
    expect(isCompatTier("deep")).toBe(false);
    expect(COMPAT_TIERS).toHaveLength(2);
    expect(SINGLE_TIERS).toHaveLength(3);
  });

  it("requires review for every paid tier, and never for the sample", () => {
    expect(PAID_TIERS.every((t) => t.requiresReview)).toBe(true);
    expect(getTierById("sample")?.requiresReview).toBe(false);
  });

  it("resolves prices server-side from an id only", () => {
    expect(priceForTier("deep")).toEqual({ cents: 5500, currency: "USD" });
    expect(priceForTier("nope")).toBeNull();
  });

  it("gives every paid tier a Dodo product env var", () => {
    expect(PAID_TIERS.every((t) => Boolean(t.productEnv))).toBe(true);
    expect(getTierById("sample")?.productEnv).toBeUndefined();
    expect(PAID_TIERS.every((t) => t.productEnv!.startsWith("DODO_PRODUCT_"))).toBe(true);
  });
});
