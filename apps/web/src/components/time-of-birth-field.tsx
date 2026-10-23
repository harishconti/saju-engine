"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Button, Field, Input } from "@/components/ui";
import { formatBirthTimeForEcho, formatBirthTimeForInput, parseTypedBirthTime } from "@/lib/birth-time";

/**
 * The time-of-birth control.
 *
 * A native `type="time"` input is a wheel picker on phones, so on mobile it cannot be typed
 * into at all — the visitor has to hunt for their birth time in a scrolling wheel. This is a
 * text field that accepts `14:30`, `2:30 pm`, `2pm` and `1430`, **echoes the time it
 * understood** ("2:30 PM") so a misread is visible before anything is saved, and keeps the
 * native picker behind a clock button for the people who prefer one.
 */
export function TimeOfBirthField({
  value,
  onChange,
  error,
  disabled = false,
  required = true,
  id,
}: {
  /** `HH:MM`, or "" when nothing is entered yet. */
  value: string;
  onChange: (hhmm: string) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
}) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  const [text, setText] = useState(value ? formatBirthTimeForInput(value) : "");
  const [parseError, setParseError] = useState<string | null>(null);
  const nativeRef = useRef<HTMLInputElement>(null);

  const lastValue = useRef(value);
  useEffect(() => {
    if (value !== lastValue.current) {
      lastValue.current = value;
      setText(value ? formatBirthTimeForInput(value) : "");
      setParseError(null);
    }
  }, [value]);

  const message = error ?? parseError ?? undefined;

  function commit(next: string) {
    const parsed = parseTypedBirthTime(next);
    if (!parsed.ok) {
      setParseError(next.trim() === "" ? null : parsed.error);
      return;
    }
    setParseError(null);
    lastValue.current = parsed.hhmm;
    onChange(parsed.hhmm);
  }

  function openPicker() {
    const el = nativeRef.current;
    if (!el) return;
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
      <Field label="Time of birth" htmlFor={fieldId} error={message} optional={!required}>
        <div className="flex gap-2">
          <Input
            id={fieldId}
            type="text"
            inputMode="numeric"
            autoComplete="off"
            placeholder="14:30 or 2:30 pm"
            required={required}
            value={text}
            aria-describedby={`${fieldId}-echo`}
            disabled={disabled}
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
            disabled={disabled}
            aria-label="Open the clock"
            title="Open the clock"
          >
            🕒
          </Button>
        </div>
      </Field>

      {/* The native control, kept in the tree (not `display:none`, which would break
          `showPicker()`) but out of the way. */}
      <input
        ref={nativeRef}
        type="time"
        className="sr-only"
        tabIndex={-1}
        aria-hidden="true"
        value={value}
        disabled={disabled}
        onChange={(e) => {
          if (!e.target.value) return;
          lastValue.current = e.target.value;
          onChange(e.target.value);
        }}
      />

      <p id={`${fieldId}-echo`} className="text-xs text-muted-foreground">
        {value ? (
          <>That is {formatBirthTimeForEcho(value)}.</>
        ) : (
          <>Type it as 14:30 or 2:30 pm, or use the clock.</>
        )}
      </p>
    </div>
  );
}
