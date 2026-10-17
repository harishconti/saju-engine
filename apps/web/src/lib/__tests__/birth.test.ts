import { describe, expect, it } from "vitest";
import {
  birthUtcOffset,
  isValidCalendarDate,
  isValidTimeZone,
  localWallClockToUtc,
  utcOffsetHours,
  validateBirth,
} from "../birth";
import { resolveBirthLocation } from "../birth";

/**
 * These are the assertions that matter most: a wrong offset silently shifts the hour branch, which
 * changes the chart without changing anything the user can see.
 */
describe("utc offset derivation", () => {
  it("returns standard offsets", () => {
    expect(utcOffsetHours("Asia/Seoul", new Date("1994-09-12T00:00:00Z"))).toBe(9);
    expect(utcOffsetHours("Asia/Kolkata", new Date("1994-09-12T00:00:00Z"))).toBe(5.5);
    expect(utcOffsetHours("UTC", new Date("1994-09-12T00:00:00Z"))).toBe(0);
  });

  it("is DST aware for the given instant, not the current one", () => {
    expect(utcOffsetHours("America/New_York", new Date("2026-07-01T12:00:00Z"))).toBe(-4);
    expect(utcOffsetHours("America/New_York", new Date("2026-01-01T12:00:00Z"))).toBe(-5);
    expect(utcOffsetHours("Europe/London", new Date("2026-07-01T12:00:00Z"))).toBe(1);
    expect(utcOffsetHours("Europe/London", new Date("2026-01-01T12:00:00Z"))).toBe(0);
  });

  it("uses historical rules, not today's offset", () => {
    // Asia/Seoul genuinely varies: LMT before 1908, +8:30 from 1912, the +8:30 era of 1954–1961,
    // historical summer time (KDT), and the 1987–88 Seoul Olympics DST. A competitor that hardcodes
    // +9 gets the hour branch wrong for every Korean birth before 1961.
    expect(utcOffsetHours("Asia/Seoul", new Date("1910-01-15T00:00:00Z"))).toBe(8.5);
    expect(utcOffsetHours("Asia/Seoul", new Date("1950-01-15T00:00:00Z"))).toBe(9);
    expect(utcOffsetHours("Asia/Seoul", new Date("1950-06-01T00:00:00Z"))).toBe(10); // historical DST
    expect(utcOffsetHours("Asia/Seoul", new Date("1957-01-15T00:00:00Z"))).toBe(8.5); // the +8:30 era
    expect(utcOffsetHours("Asia/Seoul", new Date("1957-07-15T00:00:00Z"))).toBe(9.5); // +8:30 with DST
    expect(utcOffsetHours("Asia/Seoul", new Date("1961-09-15T00:00:00Z"))).toBe(9);
    expect(utcOffsetHours("Asia/Seoul", new Date("1987-06-15T00:00:00Z"))).toBe(10); // Olympics DST
    expect(utcOffsetHours("Asia/Seoul", new Date("2026-07-01T00:00:00Z"))).toBe(9);
  });

  it("handles India's wartime offset", () => {
    // +6:30 during the Second World War, +5:30 otherwise.
    expect(utcOffsetHours("Asia/Kolkata", new Date("1942-09-01T00:00:00Z"))).toBe(6.5);
    expect(utcOffsetHours("Asia/Kolkata", new Date("2026-06-01T00:00:00Z"))).toBe(5.5);
  });

  it("converts a wall clock to the right instant", () => {
    const instant = localWallClockToUtc("1994-09-12", "13:28", "Asia/Seoul");
    expect(instant.toISOString()).toBe("1994-09-12T04:28:00.000Z");
  });

  it("rounds the engine-facing offset to a quarter hour", () => {
    expect(birthUtcOffset("1994-09-12", "13:28", "Asia/Seoul")).toBe(9);
    expect(birthUtcOffset("1994-09-12", "13:28", "Asia/Kolkata")).toBe(5.5);
    expect(Number.isInteger(birthUtcOffset("1994-09-12", "13:28", "Asia/Seoul") * 4)).toBe(true);
  });
});

describe("city resolution", () => {
  it("resolves a known city with coordinates and a zone", () => {
    const loc = resolveBirthLocation({ city: "Seoul" });
    expect(loc.timezone).toBe("Asia/Seoul");
    expect(loc.latitude).toBeCloseTo(37.5665, 3);
    expect(loc.longitude).toBeCloseTo(126.978, 3);
  });

  it("is case and whitespace insensitive", () => {
    expect(resolveBirthLocation({ city: "  sEOul " }).city).toBe("Seoul");
  });

  it("resolves the places this repository's own reports were built from", () => {
    // Every one of these was missing from the original 156-city table, which is what made the picker a
    // wall for the very people the product was built for: `/sample` refuses to submit an unresolved
    // place. A dataset swap that broke one of them would be a regression, not a fix.
    for (const city of ["Pallipattu", "Tiruvallur", "Vellore", "Ambur", "Tirupati", "Kolar"]) {
      expect(resolveBirthLocation({ city }).city, city).toBe(city);
    }
    // "Mysore" is the pre-rename spelling; GeoNames ships "Mysuru", so this only works through the
    // generated alias map.
    expect(resolveBirthLocation({ city: "Mysore" }).city).toBe("Mysuru");
  });

  it("fails loudly rather than silently dropping solar-time correction", () => {
    // NOT "Atlantis": that is a real town in South Africa, so it resolves now — the old fixture was
    // fictional only because the old table was tiny. Use a place that cannot exist.
    const nowhere = "Zzznowhereville";
    expect(() => resolveBirthLocation({ city: nowhere })).toThrowError(/couldn't find/i);
    try {
      resolveBirthLocation({ city: nowhere });
    } catch (err) {
      expect((err as { code?: string }).code).toBe("CITY_NOT_RESOLVED");
      expect((err as { status?: number }).status).toBe(422);
    }
  });

  it("never substitutes another city in the same country", () => {
    // The regression that matters. This used to fall back to the *first* city of the given country, so a
    // misspelled Indian birthplace silently resolved to **Mumbai** — 6.5° of longitude, about half an
    // hour of solar time, enough to move the hour pillar. A silent substitute is a wrong chart; E2's
    // whole point is that a refusal is the honest answer.
    expect(() => resolveBirthLocation({ city: "Zzznowhereville", countryCode: "IN" })).toThrowError(
      /couldn't find/i,
    );
  });

  it("refuses an ambiguous bare name, and resolves it once the country is known", () => {
    // "Cambridge" exists in Canada, the United Kingdom, New Zealand and the United States — four
    // different timezones. Picking one of them for someone who typed the bare name would move their
    // chart, so the bare name is refused and the picker's own label ("Name, Country") is what resolves.
    expect(() => resolveBirthLocation({ city: "Cambridge" })).toThrowError(/couldn't find/i);

    const picked = resolveBirthLocation({ city: "Cambridge, United Kingdom" });
    expect(picked.countryCode).toBe("GB");
    expect(picked.timezone).toBe("Europe/London");

    const canada = resolveBirthLocation({ city: "Cambridge", countryCode: "CA" });
    expect(canada.timezone).toBe("America/Toronto");
  });
});

describe("birth validation", () => {
  it("accepts a normal birth", () => {
    expect(validateBirth({ birthDate: "1994-09-12", birthTime: "13:28", timezone: "Asia/Seoul" }).ok).toBe(true);
  });

  it("rejects dates that do not exist", () => {
    expect(isValidCalendarDate("1991-02-30")).toBe(false);
    expect(validateBirth({ birthDate: "1991-02-30", birthTime: "10:00" }).ok).toBe(false);
  });

  it("accepts a leap day and rejects a non-leap 29 Feb", () => {
    expect(isValidCalendarDate("2024-02-29")).toBe(true);
    expect(isValidCalendarDate("2023-02-29")).toBe(false);
  });

  it("rejects out-of-range years", () => {
    const early = validateBirth({ birthDate: "1899-12-31", birthTime: "10:00" });
    expect(early.ok).toBe(false);
    expect(early.code).toBe("DATE_OUT_OF_RANGE");
  });

  it("rejects malformed times", () => {
    expect(validateBirth({ birthDate: "1994-09-12", birthTime: "25:00" }).ok).toBe(false);
    expect(validateBirth({ birthDate: "1994-09-12", birthTime: "13:60" }).ok).toBe(false);
    expect(validateBirth({ birthDate: "1994-09-12", birthTime: "1:28" }).ok).toBe(false);
  });

  it("skips the time check when the user does not know it", () => {
    expect(validateBirth({ birthDate: "1994-09-12", birthTime: "", timeKnown: false }).ok).toBe(true);
  });

  it("rejects unknown time zones", () => {
    expect(isValidTimeZone("Mars/Olympus")).toBe(false);
    expect(validateBirth({ birthDate: "1994-09-12", birthTime: "10:00", timezone: "Mars/Olympus" }).ok).toBe(false);
  });
});
