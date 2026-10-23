/**
 * Typing a birth time.
 *
 * The same problem as the date: a native `type="time"` input is a wheel picker on iOS and
 * Android, so on a phone it cannot be typed into at all, and a visitor who knows their birth
 * time has to hunt for it. This module parses what they type.
 *
 * Accepted: `14:30`, `2:30 pm`, `2pm`, `1430`, `14.30`, `14:30:00`, and the 12-hour forms with
 * `am`/`pm` in either case. The output is always the `HH:MM` the engine and the schema expect.
 */

export type ParsedBirthTime =
  | { ok: true; hhmm: string }
  | { ok: false; error: string };

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

/** Parse a typed clock time. */
export function parseTypedBirthTime(input: string): ParsedBirthTime {
  const raw = input.trim().toLowerCase().replace(/\s+/g, " ");
  if (!raw) return { ok: false, error: "Please enter your time of birth." };

  let hours: number;
  let minutes: number;
  let suffix: string | undefined;

  // "2 pm" / "2pm"
  const hourOnly = /^(\d{1,2})\s*(am|pm)$/.exec(raw);
  // "14:30", "2:30 pm", "14.30", "14:30:00"
  const withMinutes = /^(\d{1,2})[:.](\d{2})(?::\d{2})?\s*(am|pm)?$/.exec(raw);
  // "1430"
  const digitsOnly = /^(\d{3,4})$/.exec(raw);

  if (hourOnly) {
    hours = Number(hourOnly[1]);
    minutes = 0;
    suffix = hourOnly[2];
  } else if (withMinutes) {
    hours = Number(withMinutes[1]);
    minutes = Number(withMinutes[2]);
    suffix = withMinutes[3];
  } else if (digitsOnly) {
    const d = digitsOnly[1]!;
    hours = Number(d.slice(0, d.length - 2));
    minutes = Number(d.slice(-2));
  } else {
    return { ok: false, error: "Use a 24-hour time like 14:30, or 2:30 pm." };
  }

  if (!Number.isFinite(hours) || !Number.isFinite(minutes)) {
    return { ok: false, error: "Use a 24-hour time like 14:30, or 2:30 pm." };
  }
  if (suffix && (hours < 1 || hours > 12)) {
    // "13 pm" is not a time. With am/pm the hour is 1–12.
    return { ok: false, error: "With am/pm the hour is 1 to 12 — try 2:30 pm." };
  }
  if (minutes > 59) {
    return { ok: false, error: "That time doesn't exist. Check the minutes." };
  }
  if (suffix === "pm" && hours < 12) hours += 12;
  if (suffix === "am" && hours === 12) hours = 0;
  if (hours > 23) {
    return { ok: false, error: "That time doesn't exist. Use 00:00 to 23:59." };
  }

  return { ok: true, hhmm: `${pad(hours)}:${pad(minutes)}` };
}

/** "2:30 PM" — the unambiguous echo of a parsed time. */
export function formatBirthTimeForEcho(hhmm: string): string {
  const m = /^(\d{2}):(\d{2})$/.exec(hhmm);
  if (!m) return hhmm;
  const hours = Number(m[1]);
  const minutes = Number(m[2]);
  const suffix = hours >= 12 ? "PM" : "AM";
  const h12 = hours % 12 === 0 ? 12 : hours % 12;
  return `${h12}:${String(minutes).padStart(2, "0")} ${suffix}`;
}

/** "14:30" — how a time is shown in the text field. */
export function formatBirthTimeForInput(hhmm: string): string {
  return hhmm;
}
