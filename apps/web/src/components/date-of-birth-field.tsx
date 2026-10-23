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

  const tooRecent = value !== "" && !isOldEnoughForReading(value);
  const message = error ?? parseError ?? (tooRecent ? birthTooRecentMessage() : undefined);

  function commit(next: string) {
    const parsed = parseTypedBirthDate(next);
    if (!parsed.ok) {
      setParseError(next.trim() === "" ? null : parsed.error);
      // Clear the committed value too. Keeping it would let the form submit the *previous* entry
      // while the box shows something else (an edited-then-mistyped or emptied field).
      if (lastValue.current !== "") {
        lastValue.current = "";
        onChange("");
      }
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
            type="text"
            inputMode="numeric"
            autoComplete="bday"
            placeholder="19/03/1993"
            required={required}
            value={text}
            aria-describedby={`${fieldId}-echo`}
            onChange={(e) => {
              setText(e.target.value);
              setParseError(null);
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
          if (!e.target.value) return;
          // Fill the text box here: the sync effect can't, because `lastValue` already matches.
          setText(formatBirthDateForInput(e.target.value));
          setParseError(null);
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
