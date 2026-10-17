"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alert, Button, Card, CardContent, Field, Input, Select } from "@/components/ui";
import { findCity, searchCities } from "@/lib/cities";
import { useCityIndex } from "@/lib/use-city-index";
import { POLICY_VERSION } from "@/lib/consent";

export interface ProfileFormValues {
  id?: string;
  label: string;
  fullName: string;
  gender: "M" | "F";
  birthDate: string;
  birthTime: string;
  timeKnown: boolean;
  city: string;
  countryCode?: string | null;
}

const EMPTY: ProfileFormValues = {
  label: "",
  fullName: "",
  gender: "F",
  birthDate: "",
  birthTime: "12:00",
  timeKnown: true,
  city: "",
  countryCode: null,
};

/**
 * Create or edit a profile.
 *
 * The birthplace is a typeahead over the bundled city table — no runtime geocoding, and the user can
 * see exactly which place (and therefore which coordinates and timezone) the chart will use.
 */
export function ProfileForm({
  initial,
  onDone,
  submitLabel,
  hasConsent = true,
}: {
  initial?: Partial<ProfileFormValues>;
  onDone?: () => void;
  submitLabel?: string;
  /**
   * False when the account holds no active `service` consent. The server refuses to store birth data
   * without one (`403 CONSENT_REQUIRED`), so consent is taken **here**, beside the data it covers.
   * Previously the refusal only printed a sentence pointing at another page, and read as "the save
   * silently did nothing" — which is exactly how the owner reported it.
   */
  hasConsent?: boolean;
}) {
  const router = useRouter();
  const editing = Boolean(initial?.id);

  const [values, setValues] = useState<ProfileFormValues>({ ...EMPTY, ...initial });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [consentNeeded, setConsentNeeded] = useState(!hasConsent);
  const [agreed, setAgreed] = useState(hasConsent);

  // Mounting this fetch is what makes the picker offer more than the curated 156 places.
  const cityIndexReady = useCityIndex();

  const cityOptions = useMemo(() => {
    const q = values.city?.trim() ?? "";
    const list = q.length >= 2 ? searchCities(q, 8) : [];
    return list.map((c) => ({ label: `${c.name}, ${c.country}`, value: `${c.name}, ${c.country}`, cc: c.countryCode }));
  }, [values.city, cityIndexReady]);

  const resolvedCity = useMemo(
    () => findCity(values.city ?? "", values.countryCode ?? null),
    [values.city, values.countryCode, cityIndexReady],
  );

  function set<K extends keyof ProfileFormValues>(key: K, value: ProfileFormValues[K]) {
    setValues((v) => ({ ...v, [key]: value }));
    setFieldErrors((e) => ({ ...e, [key as string]: "" }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const local: Record<string, string> = {};
    if (!values.label.trim()) local.label = "Give this profile a label, like “Me” or “Partner”.";
    if (!values.fullName.trim()) local.fullName = "Whose chart is this?";
    if (!/^\d{4}-\d{2}-\d{2}$/.test(values.birthDate)) local.birthDate = "Use the date picker or YYYY-MM-DD.";
    if (!values.city.trim()) local.city = "Pick a birthplace from the list.";
    if (values.city.trim() && !resolvedCity) {
      local.city = "Pick a place from the suggestions so we use the right coordinates.";
    }
    if (Object.keys(local).length > 0) {
      setFieldErrors(local);
      return;
    }

    // Consent first: it is the lawful basis for what follows, and the server enforces it.
    if (consentNeeded) {
      if (!agreed) {
        setError("Please accept the privacy policy below — it is what allows us to store birth details.");
        return;
      }
      setBusy(true);
      try {
        const consentRes = await fetch("/api/account/consent", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            policyVersion: POLICY_VERSION,
            purposes: { service: true, service_messages: false },
          }),
        });
        if (!consentRes.ok) {
          setError("We couldn't record your consent, so nothing was saved. Please try again.");
          setBusy(false);
          return;
        }
        setConsentNeeded(false);
      } catch {
        setError("We couldn't record your consent, so nothing was saved. Please try again.");
        setBusy(false);
        return;
      }
    }

    setBusy(true);
    try {
      const payload = {
        label: values.label.trim(),
        fullName: values.fullName.trim(),
        gender: values.gender,
        birthDate: values.birthDate,
        birthTime: values.timeKnown ? values.birthTime : "12:00",
        timeKnown: values.timeKnown,
        timezone: resolvedCity?.timezone ?? null,
        city: resolvedCity?.name ?? values.city.trim(),
        countryCode: resolvedCity?.countryCode,
        country: resolvedCity?.country,
      };

      const res = await fetch(editing ? `/api/profiles/${initial!.id}` : "/api/profiles", {
        method: editing ? "PATCH" : "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string; code?: string };
        // Consent can be withdrawn elsewhere between page load and save, so re-offer it rather than
        // leaving the visitor at a dead end.
        if (body.code === "CONSENT_REQUIRED") setConsentNeeded(true);
        setError(body.error ?? "Couldn't save that. Try again.");
        return;
      }

      router.refresh();
      onDone?.();
      if (!editing) setValues({ ...EMPTY });
    } catch {
      setError("Couldn't save that. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardContent className="py-5">
        <form onSubmit={onSubmit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Label" htmlFor="label" error={fieldErrors.label} hint="How you'll recognise them.">
              <Input
                id="label"
                value={values.label}
                onChange={(e) => set("label", e.target.value)}
                placeholder="Me"
                maxLength={40}
                required
              />
            </Field>

            <Field label="Full name" htmlFor="fullName" error={fieldErrors.fullName}>
              <Input
                id="fullName"
                value={values.fullName}
                onChange={(e) => set("fullName", e.target.value)}
                autoComplete="name"
                maxLength={80}
                required
              />
            </Field>

            <Field
              label="Gender"
              htmlFor="gender"
              hint="Required: major-luck direction depends on it."
            >
              <Select
                id="gender"
                value={values.gender}
                onChange={(e) => set("gender", e.target.value as "M" | "F")}
              >
                <option value="F">Female</option>
                <option value="M">Male</option>
              </Select>
            </Field>

            <Field label="Date of birth" htmlFor="birthDate" error={fieldErrors.birthDate}>
              <Input
                id="birthDate"
                type="date"
                min="1900-01-01"
                value={values.birthDate}
                onChange={(e) => set("birthDate", e.target.value)}
                required
              />
            </Field>

            <Field
              label="Time of birth"
              htmlFor="birthTime"
              hint="Local clock time at the birthplace."
              error={fieldErrors.birthTime}
            >
              <Input
                id="birthTime"
                type="time"
                value={values.birthTime}
                onChange={(e) => set("birthTime", e.target.value)}
                disabled={!values.timeKnown}
                required={values.timeKnown}
              />
            </Field>

            <Field
              label="Place of birth"
              htmlFor="city"
              error={fieldErrors.city}
              hint={
                resolvedCity
                  ? `${resolvedCity.latitude}°, ${resolvedCity.longitude}° · ${resolvedCity.timezone}`
                  : "Start typing and pick from the list."
              }
            >
              <Input
                id="city"
                list="city-options"
                value={values.city}
                onChange={(e) => {
                  set("city", e.target.value);
                  const hit = findCity(e.target.value);
                  set("countryCode", hit?.countryCode ?? null);
                }}
                placeholder="Seoul"
                autoComplete="off"
                required
              />
              <datalist id="city-options">
                {cityOptions.map((o) => (
                  <option key={`${o.value}-${o.cc}`} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </datalist>
            </Field>
          </div>

          <label className="flex items-start gap-3 rounded-md border border-border bg-muted/30 p-3 text-sm">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--primary)]"
              checked={!values.timeKnown}
              onChange={(e) => set("timeKnown", !e.target.checked)}
            />
            <span>
              <span className="font-medium text-foreground">I don&apos;t know the birth time.</span>
              <span className="ml-1 text-muted-foreground">
                The hour pillar becomes genuinely uncertain, and the reading will say so rather than quietly
                assuming a time.
              </span>
            </span>
          </label>

          {consentNeeded ? (
            <label className="flex items-start gap-3 rounded-md border border-primary/40 bg-muted/30 p-3 text-sm">
              <input
                type="checkbox"
                className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--primary)]"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
              />
              <span>
                <span className="font-medium text-foreground">I accept the privacy policy</span>
                <span className="ml-1 text-muted-foreground">
                  Required before we can store birth details — it is the lawful basis for keeping them, and
                  you can withdraw it any time in your{" "}
                  <Link href="/dashboard/account" className="underline hover:text-foreground">
                    account settings
                  </Link>
                  .
                </span>
              </span>
            </label>
          ) : null}

          {error ? <Alert tone="danger">{error}</Alert> : null}

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" loading={busy}>
              {submitLabel ?? (editing ? "Save changes" : "Save this person")}
            </Button>
            {onDone ? (
              <Button type="button" variant="ghost" onClick={onDone} disabled={busy}>
                Cancel
              </Button>
            ) : null}
            <span className="text-xs text-muted-foreground">
              The chart is derived as soon as you save.
            </span>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
