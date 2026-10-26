"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Button, Field, Input } from "@/components/ui";
import {
  birthTooRecentMessage,
  formatBirthDateForEcho,
  formatBirthDateForInput,
  isOldEnoughForReading,
  maxBirthDateISO,
  parseTypedBirthDate,
} from "@/lib/birth-date";

/**
 * The date-of-birth control.
 *
 * A native `type="date"` input has two problems this replaces:
 *  - **it cannot be typed into on many devices** (iOS shows a wheel picker; on some platforms the
 *    whole field is a button that opens the calendar), so a visitor who knows their date has to
 *    hunt for it in a calendar; and
 *  - **it silently rejects a date typed in the visitor's own order** — "19/03/1993" is not
 *    "03/19/1993", so the field just refuses to take it.
 *
 * So the field is a text input that accepts `YYYY-MM-DD` and `DD/MM/YYYY` (and `M/D/YYYY`, and
 * `.`/`-` separators), **echoes the date it understood** ("19 March 1993") so a misread is
 * visible before anything is saved, and keeps a native date picker behind a calendar button for
 * the people who prefer one.
 *
 * The one-year minimum age is enforced by the server (`lib/birth.ts`); here it is a courtesy
 * check plus the `max` the native picker uses.
 */
export function DateOfBirthField({
  value,
  onChange,
  error,
  required = true,
  id,
}: {
  /** ISO `YYYY-MM-DD`, or "" when nothing is entered yet. */
  value: string;
  onChange: (iso: string) => void;
  error?: string;
  required?: boolean;
  id?: string;
}) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const [text, setText] = useState(value ? formatBirthDateForInput(value) : "");
  const [parseError, setParseError] = useState<string | null>(null);
  const nativeRef = useRef<HTMLInputElement>(null);
  const textRef = useRef<HTMLInputElement>(null);

  // Keep the text in step when the value is set from outside (the native picker, an edit form
  // loading a saved profile) without stomping on what the visitor is currently typing.
  const lastValue = useRef(value);
  useEffect(() => {
    if (value !== lastValue.current) {
      lastValue.current = value;
      setText(value ? formatBirthDateForInput(value) : "");
      setParseError(null);
    }
  }, [value]);

  // AU-16: a parse error must block the form's submit, not merely be printed under the field. The
  // native constraint API is what a `<form>` consults, so mirroring the message into
  // `setCustomValidity` makes the browser refuse to submit while the text is not a date.
  useEffect(() => {
    textRef.current?.setCustomValidity(parseError ?? "");
  }, [parseError]);

  const tooRecent = value !== "" && !isOldEnoughForReading(value);
  const message = error ?? parseError ?? (tooRecent ? birthTooRecentMessage() : undefined);

  function commit(next: string) {
    const parsed = parseTypedBirthDate(next);
    if (!parsed.ok) {
      // AU-16: clearing or mistyping used to leave `value` untouched, so the form submitted the
      // date the visitor had just deleted. Emit "" and keep the typed text visible so it can be
      // corrected; `lastValue` is updated first so the sync effect does not wipe that text.
      setParseError(next.trim() === "" ? null : parsed.error);
      lastValue.current = "";
      onChange("");
      return;
    }
    setParseError(null);
    lastValue.current = parsed.iso;
    onChange(parsed.iso);
  }

  function openPicker() {
    const el = nativeRef.current;
    if (!el) return;
    // `showPicker()` is the modern way to open the native calendar from a button; browsers
    // without it get focus, which still lets them use the control itself.
    if (typeof el.showPicker === "function") {
      try {
        el.showPicker();
        return;
      } catch {
        /* fall through to focus */
      }
    }
    el.focus();
  }

  return (
    <div className="space-y-1">
      <Field label="Date of birth" htmlFor={fieldId} error={message} optional={!required}>
        <div className="flex gap-2">
          <Input
            id={fieldId}
            ref={textRef}
            type="text"
            inputMode="numeric"
            autoComplete="bday"
            placeholder="19/03/1993"
            required={required}
            value={text}
            aria-describedby={`${fieldId}-echo`}
            onChange={(e) => {
              const next = e.target.value;
              setText(next);
              setParseError(null);
              // AU-16: clearing must reach the parent at once, not only on blur — otherwise a
              // click that does not move focus could submit the date the visitor just deleted.
              if (next.trim() === "" && value !== "") {
                lastValue.current = "";
                onChange("");
              }
            }}
            onBlur={(e) => commit(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                commit((e.target as HTMLInputElement).value);
              }
            }}
          />
          <Button
            type="button"
            variant="outline"
            onClick={openPicker}
            aria-label="Open the calendar"
            title="Open the calendar"
          >
            📅
          </Button>
        </div>
      </Field>

      {/* The native control, kept in the tree (not `display:none`, which would break
          `showPicker()`) but visually out of the way. Choosing a date here fills the text
          field in the same format the visitor types. */}
      <input
        ref={nativeRef}
        type="date"
        className="sr-only"
        tabIndex={-1}
        aria-hidden="true"
        min="1900-01-01"
        max={maxBirthDateISO()}
        value={value}
        onChange={(e) => {
          if (!e.target.value) {
            lastValue.current = "";
            onChange("");
            return;
          }
          lastValue.current = e.target.value;
          onChange(e.target.value);
        }}
      />

      <p id={`${fieldId}-echo`} className="text-xs text-muted-foreground">
        {value ? (
          <>That is {formatBirthDateForEcho(value)}.</>
        ) : (
          <>Type it as DD/MM/YYYY or YYYY-MM-DD, or pick it from the calendar.</>
        )}
      </p>
    </div>
  );
}
