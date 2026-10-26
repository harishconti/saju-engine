"use client";

import { useEffect, useMemo, useState } from "react";
import { track } from "@vercel/analytics";
import Link from "next/link";
import { Alert, Button, Card, CardContent, Field, Input, Select, Steps, buttonClasses } from "@/components/ui";
import { TurnstileWidget } from "@/components/turnstile-widget";
import { findCity, searchCities } from "@/lib/cities";
import { DateOfBirthField } from "@/components/date-of-birth-field";
import { TimeOfBirthField } from "@/components/time-of-birth-field";
import { useCityIndex } from "@/lib/use-city-index";
import { ANONYMOUS_SAMPLE_RETENTION_LABEL } from "@/lib/retention";
import { failureNotice, type FailureNotice } from "@/lib/visitor-copy";
import { ElementalRule, SealMark } from "@/components/viz";

const STEPS = ["Your birth details", "Check your chart", "Your snapshot"];

interface SampleResult {
  /** The reading — a self-contained web document. The free tier has no PDF. */
  readUrl: string;
  bytes?: number;
  savedToProfile?: boolean;
  /** The handle the email step uses. Random, and only *names* an object — the key is re-derived. */
  sampleId?: string;
}

export function SampleFlow({ signedIn, engineReady }: { signedIn: boolean; engineReady: boolean }) {
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  // AU-10 (2026-10-26 audit): a failure is a `FailureNotice`, not a bare string — the copy says
  // what happened, offers a retry when retrying can help, and carries a reference support can use.
  const [error, setError] = useState<FailureNotice | null>(null);
  const [result, setResult] = useState<SampleResult | null>(null);
  // The Day Master card. Held as an object URL so the preview, the save and the share all use one
  // render of the image; revoked on unmount so a long session cannot accumulate blobs.
  const [cardUrl, setCardUrl] = useState<string | null>(null);
  const [cardBusy, setCardBusy] = useState(false);
  const [cardError, setCardError] = useState<string | null>(null);
  // Email capture. `optIn` starts false and the server defaults it false too — an absent field must
  // never read as consent.
  const [leadEmail, setLeadEmail] = useState("");
  const [leadOptIn, setLeadOptIn] = useState(false);
  const [leadState, setLeadState] = useState<"idle" | "sending" | "sent">("idle");
  const [leadError, setLeadError] = useState<string | null>(null);

  const [fullName, setFullName] = useState("");
  const [gender, setGender] = useState<"M" | "F">("F");
  const [birthDate, setBirthDate] = useState("");
  // Empty, not a pre-filled 12:00. The site's own FAQ promises that an unknown birth time is
  // "marked as lower-confidence rather than quietly assuming a time" — a pre-filled noon would
  // break that promise silently. The visitor types the time, or ticks "I don't know".
  const [birthTime, setBirthTime] = useState("");
  const [timeKnown, setTimeKnown] = useState(true);
  const [city, setCity] = useState("");
  const [turnstileToken, setTurnstileToken] = useState("");
  const [turnstileReset, setTurnstileReset] = useState(0);

  const cityIndexReady = useCityIndex();
  const cityOptions = useMemo(() => searchCities(city, 8), [city, cityIndexReady]);
  const resolved = useMemo(() => findCity(city), [city, cityIndexReady]);

  /** A local form problem. No retry control: the visitor has to change a field first. */
  function formError(message: string) {
    setError({ message, retryable: false, reference: null, action: null });
  }

  async function generate() {
    setError(null);

    if (!fullName.trim()) return formError("Please give your name.");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(birthDate)) return formError("Add your date of birth.");
    if (timeKnown && !/^([01]\d|2[0-3]):[0-5]\d$/.test(birthTime)) {
      return formError("Add your time of birth, or tick \u201cI don\u2019t know my birth time\u201d.");
    }
    if (!resolved) return formError("Pick your birthplace from the suggestions.");
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
          ...(turnstileToken ? { turnstileToken } : {}),
        }),
      });

      const body = (await res.json().catch(() => ({}))) as SampleResult & { error?: string; code?: string };
      if (!res.ok || !body.readUrl) {
        // Map the code client-side rather than echoing the API's prose: an operator-facing
        // message ("set R2_ENDPOINT…") must never reach a visitor, and "nothing was charged" is
        // true for a free sample. The `x-request-id` header (`handle`) gives support a reference.
        setError(
          failureNotice({
            code: body.code,
            context: "sample",
            requestId: res.headers.get("x-request-id"),
          }),
        );
        // A Turnstile token is single-use, so any retry needs a fresh challenge.
        setTurnstileReset((n) => n + 1);
        return;
      }
      setResult(body);
      setStep(2);
      // The funnel's north-star event. Fired only on a real rendered result, never on submit, so
      // "starts" and "completions" differ by exactly the failures. Carries no personal data and no
      // birth details — only the fact that a snapshot was produced.
      track("snapshot_complete");
    } catch {
      // The request never reached the server, so there is no request id to quote.
      setError(failureNotice({ context: "sample", code: null }));
      setTurnstileReset((n) => n + 1);
    } finally {
      setBusy(false);
    }
  }

  /** Email the snapshot, and record the lead. Never blocks the snapshot itself. */
  async function emailSnapshot() {
    if (!result?.sampleId) return;
    setLeadError(null);
    if (!leadEmail.trim()) {
      setLeadError("Add an email address.");
      return;
    }
    setLeadState("sending");
    try {
      const res = await fetch("/api/sample/email", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          sampleId: result.sampleId,
          email: leadEmail.trim(),
          marketingOptIn: leadOptIn,
        }),
      });
      const body = (await res.json().catch(() => ({}))) as { emailed?: boolean; error?: string };
      if (!res.ok) {
        setLeadError(body.error ?? "We couldn't send that. Try again.");
        setLeadState("idle");
        return;
      }
      setLeadState("sent");
      track("sample_email_captured");
    } catch {
      setLeadError("Network problem. Please try again.");
      setLeadState("idle");
    }
  }

  /** Release the card's object URL if the visitor navigates away mid-session. */
  useEffect(() => {
    return () => {
      setCardUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return null;
      });
    };
  }, []);

  async function makeCard() {
    if (!resolved) return;
    setCardError(null);
    setCardBusy(true);
    try {
      const res = await fetch("/api/share-card", {
        method: "POST",
        headers: { "content-type": "application/json" },
        // Deliberately no Turnstile token: it would have to be a *fresh* one (they are single-use),
        // and the route is rate-limited instead — see the rationale in the route.
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

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setCardError(body.error ?? "We couldn't build your card. Please try again.");
        return;
      }

      const blob = await res.blob();
      setCardUrl((previous) => {
        if (previous) URL.revokeObjectURL(previous);
        return URL.createObjectURL(blob);
      });
      track("share_card");
    } catch {
      setCardError("Network problem. Please try again.");
    } finally {
      setCardBusy(false);
    }
  }

  /** The Web Share API when the browser can share files, a plain download otherwise. */
  async function shareCard() {
    if (!cardUrl) return;
    try {
      const blob = await fetch(cardUrl).then((r) => r.blob());
      const file = new File([blob], "cosmic-saju-day-master.png", { type: "image/png" });
      if (typeof navigator !== "undefined" && navigator.canShare?.({ files: [file] })) {
        await navigator.share({ files: [file], title: "My Saju Day Master" });
      }
    } catch {
      // A cancelled share sheet throws too; falling back to the download link is the right outcome.
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

      {error ? (
        <Alert tone="danger" title="We couldn't generate your snapshot">
          <p>{error.message}</p>
          {error.action ? (
            <div className="mt-3">
              {/* AU-22: a refusal a retry cannot fix points at the control that resolves it —
                  the consent gate on the account page. */}
              <Link href={error.action.href} className={buttonClasses("outline", "sm")}>
                {error.action.label}
              </Link>
            </div>
          ) : error.retryable ? (
            <div className="mt-3">
              {/* Inside the alert, next to the explanation: the visitor should not have to hunt
                  for the button, and a Turnstile challenge has already been reset above. */}
              <Button size="sm" variant="outline" loading={busy} onClick={generate}>
                Try again
              </Button>
            </div>
          ) : null}
        </Alert>
      ) : null}

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

              <DateOfBirthField value={birthDate} onChange={setBirthDate} />

              <TimeOfBirthField
                value={birthTime}
                onChange={setBirthTime}
                disabled={!timeKnown}
              />

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
                    // The label the visitor sees is the value that gets stored, so a duplicated name is
                    // selectable at all — see `findCity`. A bare name would be ambiguous.
                    <option key={`${c.name}-${c.countryCode}`} value={`${c.name}, ${c.country}`} />
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

            <TurnstileWidget onToken={setTurnstileToken} resetKey={turnstileReset} />

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
              {/* Read first, Save second — the same order and the same two actions a paid client gets.
                  The free tier is the *reading*; there is no PDF to download (see the route). */}
              <a href={result.readUrl} target="_blank" rel="noreferrer" className={buttonClasses("primary", "lg")}>
                Read it
              </a>
              <a
                href={result.readUrl}
                download="cosmic-saju-snapshot.html"
                className={buttonClasses("outline", "lg")}
              >
                Save it
              </a>
            </div>

            {/* The shareable card. Sized for a phone screen (1080×1920), so Instagram Stories and
                WhatsApp both take it — the growth loop the free snapshot was missing. Nothing
                identifying is on it: no birth date, time, place or name, only the derived chart. */}
            <div className="border-t border-border pt-5">
              {cardError ? (
                <Alert tone="danger">{cardError}</Alert>
              ) : cardUrl ? (
                <div className="flex flex-col items-center gap-4">
                  {/* A blob URL cannot go through next/image. */}
                  <img
                    src={cardUrl}
                    alt="Your Day Master card: your Day Master, four pillars and element balance"
                    className="w-full max-w-[240px] rounded-lg border border-border"
                  />
                  <div className="flex flex-wrap justify-center gap-3">
                    <a href={cardUrl} download="cosmic-saju-day-master.png" className={buttonClasses("primary", "md")}>
                      Save the card
                    </a>
                    <Button variant="outline" onClick={shareCard}>
                      Share
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3 text-center">
                  <p className="max-w-md text-sm text-muted-foreground">
                    Turn your chart into a card you can share — Day Master, four pillars and element
                    balance, sized for a phone screen.
                  </p>
                  <Button variant="outline" loading={cardBusy} onClick={makeCard}>
                    Make my Day Master card
                  </Button>
                </div>
              )}
            </div>

            <Alert tone="neutral" title="The link is temporary">
              It expires in 15 minutes. Create an account and we&apos;ll keep the chart in your profile —
              along with everything a full reading adds.
            </Alert>

            {/* Lead capture — the funnel's missing piece (external audit, 2026-10-17: "every free user
                leaves without a way to be contacted again"). Deliberately a *second*, optional action
                after the result is on screen: 06-frontend-ux.md forbids gating the sample behind
                sign-up, and a wall here would trade proof for a list. */}
            <div className="border-t border-border pt-5">
              {leadState === "sent" ? (
                <Alert tone="success" title="On its way">
                  Sent to {leadEmail}. The link works for {ANONYMOUS_SAMPLE_RETENTION_LABEL} — longer than
                  the one above.
                </Alert>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm font-medium">Email me this snapshot</p>
                  <Field
                    label="Your email"
                    htmlFor="leadEmail"
                    hint="So you can open it on your phone, or keep it past today."
                  >
                    <Input
                      id="leadEmail"
                      type="email"
                      autoComplete="email"
                      value={leadEmail}
                      onChange={(e) => setLeadEmail(e.target.value)}
                    />
                  </Field>
                  <label className="flex items-start gap-3 text-sm">
                    <input
                      type="checkbox"
                      className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--primary)]"
                      checked={leadOptIn}
                      onChange={(e) => setLeadOptIn(e.target.checked)}
                    />
                    <span className="text-muted-foreground">
                      Also send me the free five-part &ldquo;read your own chart&rdquo; course. No other
                      marketing, and replying to any email unsubscribes you.
                    </span>
                  </label>
                  {leadError ? <p className="text-sm text-danger">{leadError}</p> : null}
                  <Button variant="outline" loading={leadState === "sending"} onClick={emailSnapshot}>
                    Email it to me
                  </Button>
                </div>
              )}
            </div>

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
