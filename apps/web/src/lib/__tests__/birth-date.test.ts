/**
 * The date-of-birth rules and the typed-date parser.
 *
 * Two findings are locked here:
 *  - **the minimum age** (2026-10-22): the form accepted today's date, and the engine would
 *    happily print a day master, a career arc and a relationship outlook for a baby. The year
 *    pillar, the twelve-stage cycle and the first major-luck chapter are annual structures, so a
 *    reading starts at one year old.
 *  - **typing a date** (2026-10-22): a native `type="date"` input cannot be typed into on many
 *    devices, and it silently rejects "19/03/1993". The field now parses what people type.
 */
import { describe, expect, it } from "vitest";

import {
  birthTooRecentMessage,
  formatBirthDateForEcho,
  formatBirthDateForInput,
  isOldEnoughForReading,
  maxBirthDateISO,
  parseTypedBirthDate,
} from "@/lib/birth-date";
import { validateBirth } from "@/lib/birth";

const NOW = new Date("2026-10-22T09:00:00Z");

describe("the minimum age", () => {
  it("allows a birth date exactly one year ago", () => {
    expect(maxBirthDateISO(NOW)).toBe("2025-10-22");
    expect(isOldEnoughForReading("2025-10-22", NOW)).toBe(true);
  });

  it("refuses a birth date inside the last year — including today", () => {
    expect(isOldEnoughForReading("2026-10-22", NOW)).toBe(false);
    expect(isOldEnoughForReading("2026-10-21", NOW)).toBe(false);
    expect(isOldEnoughForReading("2026-01-01", NOW)).toBe(false);
  });

  it("refuses a malformed date rather than letting it through on a technicality", () => {
    expect(isOldEnoughForReading("not-a-date", NOW)).toBe(false);
    expect(isOldEnoughForReading("", NOW)).toBe(false);
  });

  it("clamps the one-year cutoff to the last day of a short month", () => {
    // 29 February 2024 → the cutoff is 28 February 2023, not 1 March.
    expect(maxBirthDateISO(new Date("2024-02-29T00:00:00Z"))).toBe("2023-02-28");
  });

  it("is enforced by validateBirth, which is the rule of record", () => {
    const tooRecent = validateBirth({
      birthDate: "2026-10-22",
      birthTime: "10:00",
      now: NOW,
    });
    expect(tooRecent.ok).toBe(false);
    expect(tooRecent.code).toBe("BIRTH_TOO_RECENT");
    expect(tooRecent.message).toBe(birthTooRecentMessage());
  });
});

describe("parsing a typed date", () => {
  it("reads YYYY-MM-DD as written", () => {
    const parsed = parseTypedBirthDate("1993-03-19");
    expect(parsed).toMatchObject({ ok: true, iso: "1993-03-19" });
  });

  it("reads DD/MM/YYYY, the order a bio-data uses", () => {
    expect(parseTypedBirthDate("19/03/1993")).toMatchObject({ ok: true, iso: "1993-03-19" });
  });

  it("reads MM/DD/YYYY when the day is unambiguous", () => {
    expect(parseTypedBirthDate("03/19/1993")).toMatchObject({ ok: true, iso: "1993-03-19" });
  });

  it("reads a two-digit day and month, and '.' or '-' separators", () => {
    expect(parseTypedBirthDate("9/3/1993")).toMatchObject({ ok: true, iso: "1993-03-09" });
    expect(parseTypedBirthDate("19.03.1993")).toMatchObject({ ok: true, iso: "1993-03-19" });
    expect(parseTypedBirthDate("19-03-1993")).toMatchObject({ ok: true, iso: "1993-03-19" });
  });

  it("refuses a date that does not exist", () => {
    const parsed = parseTypedBirthDate("31/02/1993");
    expect(parsed.ok).toBe(false);
    if (!parsed.ok) expect(parsed.error).toContain("doesn't exist");
  });

  it("refuses nonsense with a message that says what to type", () => {
    const parsed = parseTypedBirthDate("last tuesday");
    expect(parsed.ok).toBe(false);
    if (!parsed.ok) expect(parsed.error).toContain("YYYY-MM-DD");
  });

  it("echoes and displays the date in an unambiguous form", () => {
    expect(formatBirthDateForEcho("1993-03-19")).toBe("19 March 1993");
    expect(formatBirthDateForInput("1993-03-19")).toBe("19/03/1993");
  });
});
