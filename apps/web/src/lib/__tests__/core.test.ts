import { afterEach, describe, expect, it } from "vitest";
import { orderSchema, profileSchema, sampleRequestSchema } from "../validation/schemas";
import { formatUSD, timeAgo, REPORT_STATUS_HELP } from "../format";
import { isAdminEmail, hasMinRole, roleForEmail, ROLE_RANK } from "../roles";
import { parseChartSummary, elementCountsFrom } from "../chart";

describe("profile validation", () => {
  const valid = {
    label: "Me",
    fullName: "Jisoo K.",
    gender: "F",
    birthDate: "1994-09-12",
    birthTime: "13:28",
    city: "Seoul",
  };

  it("accepts a complete profile", () => {
    expect(profileSchema.parse(valid).city).toBe("Seoul");
  });

  it("rejects a missing label, name, or city", () => {
    expect(profileSchema.safeParse({ ...valid, label: "" }).success).toBe(false);
    expect(profileSchema.safeParse({ ...valid, fullName: "" }).success).toBe(false);
    expect(profileSchema.safeParse({ ...valid, city: "" }).success).toBe(false);
  });

  it("rejects a bad date or time format", () => {
    expect(profileSchema.safeParse({ ...valid, birthDate: "12/09/1994" }).success).toBe(false);
    expect(profileSchema.safeParse({ ...valid, birthTime: "1:28 PM" }).success).toBe(false);
  });

  it("rejects an unknown gender", () => {
    expect(profileSchema.safeParse({ ...valid, gender: "X" }).success).toBe(false);
  });

  it("defaults timeKnown to true", () => {
    expect(profileSchema.parse(valid).timeKnown).toBe(true);
  });
});

describe("order validation", () => {
  const base = { tier: "deep", profileAId: "a", adultConfirmed: true };

  it("accepts a single-chart order without a second profile", () => {
    expect(orderSchema.safeParse(base).success).toBe(true);
  });

  it("accepts a compat order with two different people", () => {
    expect(orderSchema.safeParse({ ...base, tier: "compat-deep", profileBId: "b" }).success).toBe(true);
  });

  it("refuses a compat order that names the same person twice", () => {
    const res = orderSchema.safeParse({ ...base, profileBId: "a" });
    expect(res.success).toBe(false);
  });

  it("refuses an order with no 18+ affirmation — absent is a refusal, not a default", () => {
    expect(orderSchema.safeParse({ tier: "deep", profileAId: "a" }).success).toBe(false);
  });

  it("refuses an order where the affirmation is falsy, not merely untrue-typed", () => {
    for (const falsy of [false, undefined, null, 0, ""]) {
      expect(orderSchema.safeParse({ ...base, adultConfirmed: falsy }).success).toBe(false);
    }
  });
});

describe("sample validation", () => {
  it("requires the birth essentials", () => {
    const res = sampleRequestSchema.safeParse({
      fullName: "A",
      gender: "M",
      birthDate: "1990-01-01",
      birthTime: "09:15",
      city: "Busan",
    });
    expect(res.success).toBe(true);
  });
});

describe("formatting", () => {
  it("formats whole-dollar prices without cents", () => {
    expect(formatUSD(5500)).toBe("$55");
    expect(formatUSD(2400)).toBe("$24");
  });

  it("keeps cents when they exist", () => {
    expect(formatUSD(1999)).toBe("$19.99");
  });

  it("describes recency coarsely", () => {
    expect(timeAgo(new Date())).toBe("just now");
    expect(timeAgo(new Date(Date.now() - 3 * 3600_000))).toBe("3h ago");
  });

  it("explains every report status a client can see", () => {
    for (const status of ["DRAFT_READY", "IN_REVIEW", "APPROVED", "DELIVERED", "SUPERSEDED", "FAILED"]) {
      expect(REPORT_STATUS_HELP[status]).toBeTruthy();
    }
  });
});

describe("roles", () => {
  it("ranks roles", () => {
    expect(hasMinRole("ADMIN", "USER")).toBe(true);
    expect(hasMinRole("USER", "ADMIN")).toBe(false);
    expect(ROLE_RANK.ADMIN).toBeGreaterThan(ROLE_RANK.USER);
  });

  it("gates admin on the email allowlist as well as the role", () => {
    const previous = process.env.ADMIN_EMAILS;
    process.env.ADMIN_EMAILS = "owner@cosmicsaju.com, second@cosmicsaju.com";
    try {
      expect(isAdminEmail("owner@cosmicsaju.com")).toBe(true);
      expect(isAdminEmail("OWNER@cosmicsaju.com")).toBe(true);
      expect(isAdminEmail("someone@else.com")).toBe(false);
      expect(isAdminEmail(null)).toBe(false);
    } finally {
      process.env.ADMIN_EMAILS = previous;
    }
  });
});

describe("chart summary", () => {
  it("returns null for missing or malformed data", () => {
    expect(parseChartSummary(null)).toBeNull();
    expect(parseChartSummary({})).toBeNull();
    expect(parseChartSummary({ pillars: [], dayMaster: { char: "辛" } })).toBeNull();
    expect(parseChartSummary({ pillars: [{ stem: "辛", branch: "丑" }] })).toBeNull();
  });

  it("parses a valid summary and labels unnamed pillars positionally", () => {
    const parsed = parseChartSummary({
      pillars: [
        { stem: "甲", branch: "戌" },
        { stem: "癸", branch: "酉" },
        { stem: "辛", branch: "丑" },
        { stem: "乙", branch: "未" },
      ],
      dayMaster: { char: "辛", element: "Metal", polarity: "Yin" },
      elementBalance: { Wood: 34.1, Fire: 3.7, Earth: 16.9, Metal: 28.7, Water: 16.6 },
      caveats: ["hour boundary"],
    });
    expect(parsed?.pillars.map((p) => p.label)).toEqual(["Year", "Month", "Day", "Hour"]);
    expect(parsed?.dayMaster.char).toBe("辛");
    expect(parsed?.caveats).toEqual(["hour boundary"]);
  });

  it("normalises element keys for the viz components", () => {
    const counts = elementCountsFrom({
      pillars: [{ stem: "辛", branch: "丑", label: "Day" }],
      dayMaster: { char: "辛" },
      elementBalance: { wood: 30, fire: 10 },
    });
    expect(counts.Wood).toBe(30);
    expect(counts.Fire).toBe(10);
    expect(counts.Water).toBe(0);
  });
});

/**
 * The role an account holds. This is the seam that had no implementation at all: nothing in the
 * codebase could set `role = ADMIN`, so an `ADMIN_EMAILS` entry on its own was inert and the review
 * console was unreachable — proven by the first real signup, which produced a `USER` row.
 */
describe("roleForEmail", () => {
  const previous = process.env.ADMIN_EMAILS;

  afterEach(() => {
    if (previous === undefined) delete process.env.ADMIN_EMAILS;
    else process.env.ADMIN_EMAILS = previous;
  });

  it("grants ADMIN to an allowlisted address, case-insensitively", () => {
    process.env.ADMIN_EMAILS = "owner@cosmicsaju.com";
    expect(roleForEmail("owner@cosmicsaju.com", "USER")).toBe("ADMIN");
    expect(roleForEmail("OWNER@cosmicsaju.com", "USER")).toBe("ADMIN");
  });

  it("leaves everyone else exactly as they were", () => {
    process.env.ADMIN_EMAILS = "owner@cosmicsaju.com";
    expect(roleForEmail("someone@else.com", "USER")).toBe("USER");
  });

  it("never demotes — revocation is the other half of the gate, not a role change", () => {
    process.env.ADMIN_EMAILS = "";
    expect(roleForEmail("owner@cosmicsaju.com", "ADMIN")).toBe("ADMIN");
  });

  it("is safe with no email at all", () => {
    process.env.ADMIN_EMAILS = "owner@cosmicsaju.com";
    expect(roleForEmail(null, "USER")).toBe("USER");
    expect(roleForEmail(undefined, "USER")).toBe("USER");
  });
});
