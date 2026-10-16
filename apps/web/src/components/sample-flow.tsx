"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Alert, Button, Card, CardContent, Field, Input, Select, Steps, buttonClasses } from "@/components/ui";
import { findCity, searchCities } from "@/lib/cities";
import { ElementalRule, SealMark } from "@/components/viz";

const STEPS = ["Your birth details", "Check your chart", "Your snapshot"];

interface SampleResult {
  downloadUrl: string;
  bytes?: number;
  savedToProfile?: boolean;
}

export function SampleFlow({ signedIn, engineReady }: { signedIn: boolean; engineReady: boolean }) {
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SampleResult | null>(null);

  const [fullName, setFullName] = useState("");
  const [gender, setGender] = useState<"M" | "F">("F");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("12:00");
  const [timeKnown, setTimeKnown] = useState(true);
  const [city, setCity] = useState("");

  const cityOptions = useMemo(() => searchCities(city, 8), [city]);
  const resolved = useMemo(() => findCity(city), [city]);

  async function generate() {
    setError(null);

    if (!fullName.trim()) return setError("Please give your name.");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(birthDate)) return setError("Add your date of birth.");
    if (!resolved) return setError("Pick your birthplace from the suggestions.");

    setBusy(true);
    try {
      const res = await fetch("/api/sample", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          fullName: fullName.trim(),
          gender,
          birthDate,
          birthTime: timeKnown ? birthTime : "12:00",
          timeKnown,
          city: resolved.name,
          countryCode: resolved.countryCode,
          country: resolved.country,
        }),
      });

      const body = (await res.json().catch(() => ({}))) as SampleResult & { error?: string; code?: string };
      if (!res.ok || !body.downloadUrl) {
        setError(body.error ?? "We couldn't generate your snapshot. Please try again.");
        return;
      }
      setResult(body);
      setStep(2);
    } catch {
      setError("Network problem. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <Steps steps={STEPS} current={step} />

      {!engineReady ? (
        <Alert tone="warning" title="The calculation engine isn't connected yet">
          You can fill the form, but the snapshot can&apos;t be generated until the report engine is
          deployed and reachable. Nothing here is charged either way.
        </Alert>
      ) : null}

      {error ? <Alert tone="danger">{error}</Alert> : null}

      {step < 2 ? (
        <Card>
          <CardContent className="space-y-5 py-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Your name" htmlFor="fullName">
                <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} maxLength={80} />
              </Field>

              <Field label="Gender" htmlFor="gender" hint="Required: major-luck direction depends on it.">
                <Select id="gender" value={gender} onChange={(e) => setGender(e.target.value as "M" | "F")}>
                  <option value="F">Female</option>
                  <option value="M">Male</option>
                </Select>
              </Field>

              <Field label="Date of birth" htmlFor="birthDate">
                <Input
                  id="birthDate"
                  type="date"
                  min="1900-01-01"
                  value={birthDate}
                  onChange={(e) => setBirthDate(e.target.value)}
                />
              </Field>

              <Field
                label="Time of birth"
                htmlFor="birthTime"
                hint="The local clock time where you were born."
              >
                <Input
                  id="birthTime"
                  type="time"
                  value={birthTime}
                  onChange={(e) => setBirthTime(e.target.value)}
                  disabled={!timeKnown}
                />
              </Field>

              <Field
                label="Place of birth"
                htmlFor="city"
                hint={resolved ? `${resolved.latitude}°, ${resolved.longitude}° · ${resolved.timezone}` : "Start typing and pick from the list."}
              >
                <Input
                  id="city"
                  list="sample-city-options"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Seoul"
                  autoComplete="off"
                />
                <datalist id="sample-city-options">
                  {cityOptions.map((c) => (
                    <option key={`${c.name}-${c.countryCode}`} value={c.name}>
                      {c.name}, {c.country}
                    </option>
                  ))}
                </datalist>
              </Field>
            </div>

            <label className="flex items-start gap-3 rounded-md border border-border bg-muted/30 p-3 text-sm">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--primary)]"
                checked={!timeKnown}
                onChange={(e) => setTimeKnown(!e.target.checked)}
              />
              <span>
                <span className="font-medium text-foreground">I don&apos;t know my birth time</span>
                <span className="ml-1 text-muted-foreground">
                  The hour pillar becomes uncertain and we&apos;ll say so rather than guessing a time for you.
                </span>
              </span>
            </label>

            <div className="flex flex-wrap items-center gap-3">
              <Button onClick={generate} loading={busy}>
                Get my free snapshot
              </Button>
              {signedIn ? (
                <span className="text-xs text-muted-foreground">
                  You&apos;re signed in — this will also be saved to your profile.
                </span>
              ) : (
                <span className="text-xs text-muted-foreground">No account needed.</span>
              )}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {step === 2 && result ? (
        <Card>
          <CardContent className="space-y-5 py-6">
            <div className="flex flex-col items-center gap-3 text-center">
              <SealMark char="四" />
              <h2 className="font-display text-2xl">Your snapshot is ready</h2>
              <p className="max-w-md text-sm text-muted-foreground">
                One page: your four pillars, element balance, Day Master, and your lucky cues.
              </p>
              <ElementalRule className="max-w-32" />
            </div>

            <div className="flex flex-wrap justify-center gap-3">
              <a href={result.downloadUrl} target="_blank" rel="noreferrer" className={buttonClasses("primary", "lg")}>
                Open my snapshot
              </a>
              <a
                href={result.downloadUrl}
                download="cosmic-saju-snapshot.pdf"
                className={buttonClasses("outline", "lg")}
              >
                Download the PDF
              </a>
            </div>

            <Alert tone="neutral" title="The link is temporary">
              It expires in 15 minutes. Create an account and we&apos;ll keep the chart in your profile —
              along with everything a full reading adds.
            </Alert>

            <div className="flex flex-wrap justify-center gap-3 border-t border-border pt-5">
              {signedIn ? (
                <Link href="/dashboard/profiles" className={buttonClasses("primary", "md")}>
                  See it in your profile
                </Link>
              ) : (
                <Link href="/login?next=/dashboard" className={buttonClasses("primary", "md")}>
                  Create an account to keep this
                </Link>
              )}
              <Link href="/reports/new" className={buttonClasses("outline", "md")}>
                Go deeper with a full reading
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <p className="text-xs text-muted-foreground">
        We ask for a birthplace because solar-time correction depends on longitude. Nothing you enter here is
        shared or sold — see the{" "}
        <Link href="/privacy" className="underline hover:text-foreground">
          privacy policy
        </Link>
        .
      </p>
    </div>
  );
}
