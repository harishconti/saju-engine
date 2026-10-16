/**
 * Birth-data helpers: city resolution, timezone validation, historical/DST-aware offset derivation.
 *
 * Why this module exists (engine change E2): the Python engine's `pillars.py` resolves a city name
 * via Nominatim at request time. That is a network call with a usage policy, real latency, and a
 * silent degrade to "standard time" on failure. Instead we resolve coordinates ONCE here, at profile
 * creation, and hand the engine explicit longitude + timezone/offset.
 *
 * The offset logic mirrors the engine's `derive_utc_offset` intent: stdlib zoneinfo semantics,
 * historical and DST aware for the birth date.
 */

import { CITIES, findCity, type City } from "./cities";
import { ApiError } from "./api";

export interface ResolvedLocation {
  city: string;
  country: string;
  countryCode: string;
  latitude: number;
  longitude: number;
  timezone: string;
}

export function isValidTimeZone(tz: string): boolean {
  try {
    new Intl.DateTimeFormat("en-US", { timeZone: tz });
    return true;
  } catch {
    return false;
  }
}

export function isValidCalendarDate(dateStr: string): boolean {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateStr);
  if (!m) return false;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  if (mo < 1 || mo > 12 || d < 1) return false;
  // Reject 31 Feb etc. by round-tripping through UTC.
  const probe = new Date(Date.UTC(y, mo - 1, d));
  return probe.getUTCFullYear() === y && probe.getUTCMonth() === mo - 1 && probe.getUTCDate() === d;
}

/**
 * Resolve a birthplace string to coordinates + IANA timezone.
 *
 * Fails loudly with 422 CITY_NOT_RESOLVED rather than silently proceeding: an unresolved city means
 * no solar-time correction, and a silently-uncorrected chart is a wrong chart.
 */
export function resolveBirthLocation(input: {
  city: string;
  countryCode?: string | null;
  country?: string | null;
}): ResolvedLocation {
  const byName = findCity(input.city, input.countryCode ?? null);
  const city: City | null =
    byName ??
    (input.countryCode
      ? CITIES.find((c) => c.countryCode.toLowerCase() === input.countryCode!.toLowerCase()) ?? null
      : null);

  if (!city) {
    throw new ApiError(
      422,
      "CITY_NOT_RESOLVED",
      `We couldn't find "${input.city}". Pick a birthplace from the list so the chart can use the correct solar time.`,
    );
  }

  return {
    city: city.name,
    country: city.country,
    countryCode: city.countryCode,
    latitude: city.latitude,
    longitude: city.longitude,
    timezone: city.timezone,
  };
}

/** UTC offset in hours for `timeZone` at the instant `at` (DST + historical rules included). */
export function utcOffsetHours(timeZone: string, at: Date): number {
  const dtf = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hourCycle: "h23",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const parts = dtf.formatToParts(at);
  const get = (type: string) => Number(parts.find((p) => p.type === type)?.value ?? "0");
  const asUTC = Date.UTC(
    get("year"),
    get("month") - 1,
    get("day"),
    get("hour"),
    get("minute"),
    get("second"),
  );
  const atWholeSecond = Math.floor(at.getTime() / 1000) * 1000;
  return (asUTC - atWholeSecond) / 3_600_000;
}

/**
 * Convert a local wall-clock birth time in `timeZone` to the corresponding UTC instant.
 *
 * Iterates because the offset itself depends on the instant (DST transitions). Three passes is
 * ample; it converges on the second. On the two ambiguous/nonexistent DST wall-clock times per
 * year, the result is deterministic and the engine's own boundary notes flag the hour.
 */
export function localWallClockToUtc(dateStr: string, timeStr: string, timeZone: string): Date {
  const [y, mo, d] = dateStr.split("-").map(Number);
  const [h, mi] = timeStr.split(":").map(Number);
  const naive = Date.UTC(y!, mo! - 1, d!, h!, mi!);

  let guess = new Date(naive);
  for (let i = 0; i < 3; i++) {
    const offset = utcOffsetHours(timeZone, guess);
    const next = new Date(naive - offset * 3_600_000);
    if (Math.abs(next.getTime() - guess.getTime()) < 1000) return next;
    guess = next;
  }
  return guess;
}

/** The UTC offset the engine should be given for this birth (rounded to 0.25 h like the CLI). */
export function birthUtcOffset(dateStr: string, timeStr: string, timeZone: string): number {
  const instant = localWallClockToUtc(dateStr, timeStr, timeZone);
  const offset = utcOffsetHours(timeZone, instant);
  return Math.round(offset * 4) / 4;
}

export interface BirthValidation {
  ok: boolean;
  code?: string;
  message?: string;
}

/** Validate before hitting the database so the user gets a precise message. */
export function validateBirth(input: {
  birthDate: string;
  birthTime: string;
  timezone?: string | null;
  timeKnown?: boolean;
}): BirthValidation {
  if (!isValidCalendarDate(input.birthDate)) {
    return { ok: false, code: "INVALID_DATE", message: "That date doesn't exist. Check the day and month." };
  }
  const year = Number(input.birthDate.slice(0, 4));
  const currentYear = new Date().getUTCFullYear();
  if (year < 1900 || year > currentYear) {
    return {
      ok: false,
      code: "DATE_OUT_OF_RANGE",
      message: `Please use a birth year between 1900 and ${currentYear}.`,
    };
  }
  if (input.timeKnown !== false && !/^([01]\d|2[0-3]):[0-5]\d$/.test(input.birthTime)) {
    return { ok: false, code: "INVALID_TIME", message: "Use a 24-hour time like 14:30." };
  }
  if (input.timezone && !isValidTimeZone(input.timezone)) {
    return { ok: false, code: "UNKNOWN_TIMEZONE", message: `Unknown time zone "${input.timezone}".` };
  }
  return { ok: true };
}

/** Human summary, e.g. `12 Sep 1994, 13:28 · Seoul, South Korea`. */
export function describeBirth(input: {
  birthDate: Date | string;
  birthTime: string;
  city: string;
  country?: string | null;
  timeKnown?: boolean;
}): string {
  const d = typeof input.birthDate === "string" ? new Date(`${input.birthDate}T00:00:00Z`) : input.birthDate;
  const date = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(d);
  const time = input.timeKnown === false ? "birth time unknown" : input.birthTime;
  const place = [input.city, input.country].filter(Boolean).join(", ");
  return `${date}, ${time} · ${place}`;
}
