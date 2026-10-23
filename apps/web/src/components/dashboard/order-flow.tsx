"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { track } from "@vercel/analytics";
import { Alert, Badge, Button, Card, CardContent, Field, Select, Steps, buttonClasses } from "@/components/ui";
import { COMPAT_TIERS, SINGLE_TIERS, TIERS, type Tier } from "@/lib/tiers";
import { promoPriceCents } from "@/lib/promo";
import { formatUSD } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface OrderProfile {
  id: string;
  label: string;
  fullName: string;
  gender: "M" | "F";
  hasChart: boolean;
}

const STEPS = ["Choose a reading", "Who it's for", "Confirm"];

/**
 * `promoOn` is decided by the SERVER (it knows whether the promotional products are configured,
 * so the offer can fail closed) and passed in. The client only does the arithmetic — it never
 * decides for itself that a discount exists, and the price the server records on the order is
 * the price that is charged.
 */
export function OrderFlow({
  profiles,
  initialTier,
  promoOn = false,
}: {
  profiles: OrderProfile[];
  initialTier?: string | null;
  promoOn?: boolean;
}) {
  const router = useRouter();

  const initial = TIERS.find((t) => t.id === initialTier) ?? null;
  const [tier, setTier] = useState<Tier | null>(initial);
  const [profileAId, setProfileAId] = useState<string>(profiles[0]?.id ?? "");
  const [profileBId, setProfileBId] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Not persisted anywhere client-side: it is an affirmation made at submission, and the server
  // re-requires it (lib/validation/schemas.ts) so this state is only a convenience.
  const [adultConfirmed, setAdultConfirmed] = useState(false);
  // Set only if the server prices the order differently from what was displayed here (the offer
  // ended between page render and submission). The server is authoritative; the customer is told
  // the new number before paying it.
  const [priceNote, setPriceNote] = useState<string | null>(null);

  // One key per submission attempt; reused across retries of the same submission.
  const [idempotencyKey] = useState(() =>
    typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `key-${Date.now()}`,
  );

  const step = tier === null ? 0 : tier.kind === "COMPAT" && !profileBId ? 1 : tier ? 2 : 1;

  /** The price shown for a tier: the offer price while the promotion runs, the list price after. */
  const priceOf = (t: Tier): number =>
    promoOn && t.priceCents > 0 ? promoPriceCents(t.priceCents) : t.priceCents;

  const profileA = useMemo(() => profiles.find((p) => p.id === profileAId) ?? null, [profiles, profileAId]);
  const profileB = useMemo(() => profiles.find((p) => p.id === profileBId) ?? null, [profiles, profileBId]);

  const secondOptions = profiles.filter((p) => p.id !== profileAId);

  async function submit() {
    if (!tier) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "content-type": "application/json", "idempotency-key": idempotencyKey },
        body: JSON.stringify({
          tier: tier.id,
          profileAId,
          profileBId: tier.kind === "COMPAT" ? profileBId || null : null,
          idempotencyKey,
          adultConfirmed,
        }),
      });

      const body = (await res.json().catch(() => ({}))) as {
        checkoutUrl?: string;
        error?: string;
        order?: { id: string; priceCents?: number };
      };

      if (!res.ok) {
        setError(body.error ?? "Couldn't create that order. Try again.");
        return;
      }

      // The server priced the order. If that differs from what was on screen, say so plainly
      // rather than letting the customer discover it at the payment page.
      const serverPrice = body.order?.priceCents;
      if (serverPrice != null && tier && serverPrice !== priceOf(tier)) {
        setPriceNote(
          `The launch offer ended while you were choosing, so this order is now ${formatUSD(serverPrice)} — the standard price. Nothing has been charged yet.`,
        );
        setBusy(false);
        return;
      }

      if (body.checkoutUrl) {
        // Fired as the buyer leaves for the hosted checkout — the closest client-side proxy for
        // "intent to pay". The authoritative purchase event is server-side, from the provider's
        // webhook. Values are strings only: the analytics client rejects nested or object props.
        track("checkout_start", { tier: tier.id });
        window.location.href = body.checkoutUrl;
        return;
      }

      // Free tier: queued directly.
      router.push(body.order ? `/dashboard/reports` : "/dashboard");
      router.refresh();
    } catch {
      setError("Couldn't create that order. Check your connection and try again.");
    } finally {
      setBusy(false);
    }
  }

  if (profiles.length === 0) {
    return (
      <Card>
        <CardContent className="py-6">
          <Alert tone="primary" title="Add someone first">
            A reading needs birth details. Add yourself (or whoever the reading is for) and you&apos;ll come
            straight back here.
          </Alert>
          <div className="pt-4">
            <Link href="/dashboard/profiles" className={buttonClasses("primary", "md")}>
              Add birth details
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Steps steps={STEPS} current={step} />

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {priceNote ? <Alert tone="warning">{priceNote}</Alert> : null}

      {/* Step 1 — tier */}
      <section aria-label="Choose a reading" className="space-y-3">
        <h2 className="font-display text-xl">Choose a reading</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {[...SINGLE_TIERS.filter((t) => t.priceCents > 0), ...COMPAT_TIERS].map((t) => {
            const selected = tier?.id === t.id;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => {
                  setTier(t);
                  if (t.kind !== "COMPAT") setProfileBId("");
                }}
                aria-pressed={selected}
                className={cn(
                  "card-surface flex flex-col gap-2 p-4 text-left transition-colors",
                  selected ? "border-primary" : "hover:border-muted-foreground/40",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="font-display text-lg">{t.name}</span>
                  <span className="text-right">
                    <span className="block font-display text-lg">{formatUSD(priceOf(t))}</span>
                    {promoOn && t.priceCents > 0 ? (
                      <span className="block text-xs text-muted-foreground line-through">
                        {formatUSD(t.priceCents)}
                      </span>
                    ) : null}
                  </span>
                </div>
                <span className="text-xs text-muted-foreground">{t.pages}</span>
                <span className="text-sm text-muted-foreground">{t.tagline}</span>
                {t.kind === "COMPAT" ? <Badge tone="muted">two charts</Badge> : null}
              </button>
            );
          })}
        </div>
      </section>

      {/* Step 2 — people */}
      {tier ? (
        <section aria-label="Who it's for" className="space-y-3">
          <h2 className="font-display text-xl">{tier.kind === "COMPAT" ? "Both people" : "Who it's for"}</h2>

          {tier.kind === "COMPAT" ? (
            <Alert tone="neutral" title="A compatibility reading compares two charts">
              Pick two different people. If you haven&apos;t added the second person yet, add them on the{" "}
              <Link href="/dashboard/profiles" className="underline">
                People
              </Link>{" "}
              page and come back.
            </Alert>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label={tier.kind === "COMPAT" ? "First person" : "Person"} htmlFor="profileA">
              <Select id="profileA" value={profileAId} onChange={(e) => setProfileAId(e.target.value)}>
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label} — {p.fullName}
                  </option>
                ))}
              </Select>
            </Field>

            {tier.kind === "COMPAT" ? (
              <Field label="Second person" htmlFor="profileB">
                <Select id="profileB" value={profileBId} onChange={(e) => setProfileBId(e.target.value)}>
                  <option value="">Choose someone…</option>
                  {secondOptions.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.label} — {p.fullName}
                    </option>
                  ))}
                </Select>
              </Field>
            ) : null}
          </div>

          {!profileA?.hasChart ? (
            <Alert tone="warning">
              We don&apos;t have a derived chart for {profileA?.label ?? "this person"} yet. You can still
              order — the chart is computed as part of producing the reading — but check their birth details
              are right first.
            </Alert>
          ) : null}
        </section>
      ) : null}

      {/* Step 3 — confirm */}
      {tier && (tier.kind !== "COMPAT" || profileBId) ? (
        <section aria-label="Confirm" className="space-y-3">
          <h2 className="font-display text-xl">Confirm</h2>
          <Card>
            <CardContent className="space-y-3 py-5">
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">Reading</dt>
                  <dd className="font-medium">{tier.name}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">For</dt>
                  <dd className="font-medium">
                    {tier.kind === "COMPAT" && profileB
                      ? `${profileA?.label} × ${profileB.label}`
                      : (profileA?.label ?? "—")}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted-foreground">Delivery</dt>
                  <dd className="font-medium">Email + your profile, after review</dd>
                </div>
                <div className="flex justify-between gap-4 border-t border-border pt-2">
                  <dt className="text-muted-foreground">Total</dt>
                  <dd className="font-display text-xl">
                    {formatUSD(priceOf(tier))}
                    {promoOn && tier.priceCents > 0 ? (
                      <span className="ml-2 text-sm font-normal text-muted-foreground line-through">
                        {formatUSD(tier.priceCents)}
                      </span>
                    ) : null}
                  </dd>
                </div>
              </dl>

              <Alert tone="neutral">
                Every paid reading is reviewed by a person before it&apos;s sent — usually within a day. You
                can change your mind about the birth details right up until delivery.
              </Alert>

              {/* An affirmation, not a marketing prompt: the tier covers relationship and health
                  content, and the Hallyu-adjacent audience skews young (docs/webapp/10 §Minors).
                  The server requires this too, so it is enforcement rather than decoration. */}
              {tier.priceCents > 0 ? (
                <label className="flex items-start gap-3 rounded-md border border-border bg-muted/30 p-3 text-sm">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--primary)]"
                    checked={adultConfirmed}
                    onChange={(e) => setAdultConfirmed(e.target.checked)}
                  />
                  <span>
                    <span className="font-medium text-foreground">I&apos;m 18 or over</span>
                    <span className="ml-1 text-muted-foreground">
                      These readings include relationship and health guidance, so we sell them to adults
                      only.
                    </span>
                  </span>
                </label>
              ) : null}

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  loading={busy}
                  disabled={tier.priceCents > 0 && !adultConfirmed}
                  onClick={submit}
                >
                  {tier.priceCents === 0 ? "Confirm" : `Pay ${formatUSD(priceOf(tier))}`}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    setTier(null);
                    setProfileBId("");
                  }}
                  disabled={busy}
                >
                  Change reading
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Payment is handled by Dodo Payments, our merchant of record, who manages sales tax and VAT.
              </p>
            </CardContent>
          </Card>
        </section>
      ) : null}
    </div>
  );
}
