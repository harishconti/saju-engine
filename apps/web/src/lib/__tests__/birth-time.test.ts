/**
 * Typing a birth time (2026-10-22).
 *
 * The reported bug: on a phone the native `type="time"` control is a wheel picker, so the birth
 * time could not be typed at all. The field now parses what people type — and echoes it back, so
 * "2:30" is never silently read as 14:30.
 */
import { describe, expect, it } from "vitest";

import { formatBirthTimeForEcho, parseTypedBirthTime } from "@/lib/birth-time";

describe("parsing a typed time", () => {
  it("reads a 24-hour time", () => {
    expect(parseTypedBirthTime("14:30")).toMatchObject({ ok: true, hhmm: "14:30" });
    expect(parseTypedBirthTime("00:05")).toMatchObject({ ok: true, hhmm: "00:05" });
    expect(parseTypedBirthTime("23:59")).toMatchObject({ ok: true, hhmm: "23:59" });
  });

  it("reads a 12-hour time with am/pm", () => {
    expect(parseTypedBirthTime("2:30 pm")).toMatchObject({ ok: true, hhmm: "14:30" });
    expect(parseTypedBirthTime("2:30 PM")).toMatchObject({ ok: true, hhmm: "14:30" });
    expect(parseTypedBirthTime("12:00 am")).toMatchObject({ ok: true, hhmm: "00:00" });
    expect(parseTypedBirthTime("12:00 pm")).toMatchObject({ ok: true, hhmm: "12:00" });
  });

  it("reads an hour on its own", () => {
    expect(parseTypedBirthTime("2 pm")).toMatchObject({ ok: true, hhmm: "14:00" });
    expect(parseTypedBirthTime("2am")).toMatchObject({ ok: true, hhmm: "02:00" });
  });

  it("reads four digits and a dot separator", () => {
    expect(parseTypedBirthTime("1430")).toMatchObject({ ok: true, hhmm: "14:30" });
    expect(parseTypedBirthTime("14.30")).toMatchObject({ ok: true, hhmm: "14:30" });
    expect(parseTypedBirthTime("14:30:00")).toMatchObject({ ok: true, hhmm: "14:30" });
  });

  it("refuses a time that does not exist", () => {
    expect(parseTypedBirthTime("25:00").ok).toBe(false);
    expect(parseTypedBirthTime("10:75").ok).toBe(false);
    expect(parseTypedBirthTime("13 pm").ok).toBe(false);
  });

  it("refuses nonsense with a message that says what to type", () => {
    const parsed = parseTypedBirthTime("around noon");
    expect(parsed.ok).toBe(false);
    if (!parsed.ok) expect(parsed.error).toContain("14:30");
  });

  it("echoes the time in the form people recognise", () => {
    expect(formatBirthTimeForEcho("14:30")).toBe("2:30 PM");
    expect(formatBirthTimeForEcho("00:05")).toBe("12:05 AM");
    expect(formatBirthTimeForEcho("12:00")).toBe("12:00 PM");
  });
});
