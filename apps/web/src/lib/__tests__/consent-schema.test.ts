import { describe, expect, it } from "vitest";

import { consentSchema } from "@/lib/validation/schemas";

/**
 * AU-32 (2026-10-26 audit): `purposes` was `z.record(z.string(), z.boolean())` — an unbounded map
 * written straight into a JSON column. Anything (a typo, a stale client, a hand-crafted request)
 * could add keys forever. The policy defines exactly two purposes, so the schema now carries
 * exactly those, and rejects everything else.
 */

const VALID = {
  policyVersion: "2026-10-15",
  purposes: { service: true, service_messages: false },
};

describe("consentSchema purposes (AU-32)", () => {
  it("accepts the two purposes the policy defines", () => {
    expect(consentSchema.parse(VALID)).toEqual(VALID);
  });

  it("rejects a purpose the policy does not define", () => {
    expect(() =>
      consentSchema.parse({
        ...VALID,
        purposes: { ...VALID.purposes, marketing: true },
      }),
    ).toThrow();
  });

  it("rejects an oversized map of invented purposes", () => {
    const many = {
      ...VALID.purposes,
      ...Object.fromEntries(Array.from({ length: 500 }, (_, i) => [`purpose_${i}`, true])),
    };

    expect(() => consentSchema.parse({ ...VALID, purposes: many })).toThrow();
  });

  it("rejects an oversized policy version", () => {
    expect(() => consentSchema.parse({ ...VALID, policyVersion: "v".repeat(41) })).toThrow();
  });

  it("rejects an oversized value hidden in a purpose", () => {
    expect(() =>
      consentSchema.parse({
        ...VALID,
        purposes: { service: "x".repeat(10_000), service_messages: false },
      }),
    ).toThrow();
  });
});
