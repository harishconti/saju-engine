/**
 * The minimum age for a Saju reading, and the date arithmetic that goes with it.
 *
 * Why one year: the year pillar, the twelve-stage (12운성) cycle and the first major-luck
 * chapter are **annual** structures. A chart for a baby is not a chart with fewer conclusions —
 * the whole vocabulary is empty, and the engine would print a confident day master, a career
 * arc and a relationship outlook for a person who has lived a few weeks. So the reading starts
 * at one year old.
 *
 * This module is deliberately free of server-only imports (the city index is a server module),
 * so the client can compute the same "latest acceptable date" the server enforces.
 */

/** The minimum age for a reading, in years. */
export const MIN_READING_AGE_YEARS = 1;

/** The earliest birth date the product accepts at all. */
export const EARLIEST_BIRTH_DATE = "1900-01-01";

/** Days in a given month, leap years included. */
function daysInMonth(year: number, monthIndex: number): number {
  return new Date(Date.UTC(year, monthIndex + 1, 0)).getUTCDate();
}

/**
 * The latest acceptable birth date: exactly `MIN_READING_AGE_YEARS` ago.
 *
 * UTC throughout, so the rule does not shift with the visitor's time zone, and the day is
 * clamped to the last day of the target month (29 February in a common year becomes the 28th).
 */
export function maxBirthDateISO(now: Date = new Date()): string {
  const year = now.getUTCFullYear() - MIN_READING_AGE_YEARS;
  const month = now.getUTCMonth();
  const day = Math.min(now.getUTCDate(), daysInMonth(year, month));
  return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

/**
 * Is this birth date old enough for a reading?
 *
 * A malformed date is not "old enough" — the caller validates the shape separately, and this
 * function must not let a nonsense date through on a technicality.
 */
export function isOldEnoughForReading(birthDate: string, now: Date = new Date()): boolean {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(birthDate)) return false;
  return birthDate <= maxBirthDateISO(now);
}

/** The message shown when someone is too young for a reading. */
export function birthTooRecentMessage(): string {
  return `Readings start at ${MIN_READING_AGE_YEARS} year old — please use a birth date at least a year ago.`;
}

// ── Typing a date ────────────────────────────────────────────────────────────
//
// A native `type="date"` input cannot be typed into on many devices, and on the ones where it
// can, it silently rejects a date typed in the visitor's own order ("19/03/1993" is not
// "03/19/1993"). So the text path is ours: parse what they typed, and echo the result back so a
// misread is visible before anything is saved.

export type ParsedBirthDate =
  | { ok: true; iso: string; dayFirst: boolean }
  | { ok: false; error: string };

/** Does this y/m/d exist on the calendar? */
function isRealDate(y: number, m: number, d: number): boolean {
  if (m < 1 || m > 12 || d < 1) return false;
  return d <= daysInMonth(y, m - 1);
}

function toIso(y: number, m: number, d: number): string {
  return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

/**
 * Parse a typed date.
 *
 * Accepted: `YYYY-MM-DD`, and `D/M/YYYY`, `M/D/YYYY`, `D-M-YYYY`, `D.M.YYYY` (and two-digit
 * day/month). ISO is unambiguous by definition. For the separated forms the day/month order is
 * read from the numbers themselves — a first part above 12 can only be a day, a second part above
 * 12 can only be a month — and **when both could be either, the day comes first**, which is the
 * order a South-Asian bio-data uses. The field echoes the parsed date, so a wrong guess is
 * visible and can be corrected rather than silently stored.
 */
export function parseTypedBirthDate(input: string): ParsedBirthDate {
  const raw = input.trim();
  if (!raw) return { ok: false, error: "Please enter your date of birth." };

  const iso = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(raw);
  if (iso) {
    const y = Number(iso[1]);
    const m = Number(iso[2]);
    const d = Number(iso[3]);
    if (!isRealDate(y, m, d)) return { ok: false, error: "That date doesn't exist. Check the day and month." };
    return { ok: true, iso: toIso(y, m, d), dayFirst: false };
  }

  const sep = /^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$/.exec(raw);
  if (sep) {
    const a = Number(sep[1]);
    const b = Number(sep[2]);
    const y = Number(sep[3]);
    let day: number;
    let month: number;
    let dayFirst: boolean;
    if (a > 12) {
      day = a;
      month = b;
      dayFirst = true;
    } else if (b > 12) {
      day = b;
      month = a;
      dayFirst = false;
    } else {
      day = a;
      month = b;
      dayFirst = true;
    }
    if (!isRealDate(y, month, day)) {
      return { ok: false, error: "That date doesn't exist. Check the day and month." };
    }
    return { ok: true, iso: toIso(y, month, day), dayFirst };
  }

  return {
    ok: false,
    error: "Use YYYY-MM-DD, or DD/MM/YYYY (for example 19/03/1993).",
  };
}

/** "19 March 1993" — the unambiguous echo of a parsed date. */
export function formatBirthDateForEcho(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return iso;
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(d);
}

/** "19/03/1993" — how a date is shown in the text field, in the order we read it. */
export function formatBirthDateForInput(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return iso;
  return `${m[3]}/${m[2]}/${m[1]}`;
}
