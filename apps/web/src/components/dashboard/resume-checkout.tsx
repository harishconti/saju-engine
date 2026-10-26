"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert, Button } from "@/components/ui";
import { failureNotice, type FailureAction } from "@/lib/visitor-copy";

/** Creates a fresh hosted-checkout session for an existing unpaid order. */
export function ResumeCheckoutButton({ orderId }: { orderId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // AU-24 (D7): checkout refuses when service consent has been withdrawn. That refusal has one fix,
  // so the alert links to it — resolved by the shared `failureNotice` helper, like the order flow
  // and "Check for updates", rather than keeping a local copy of the mapping.
  const [consentAction, setConsentAction] = useState<FailureAction | null>(null);

  async function onClick() {
    setBusy(true);
    setError(null);
    setConsentAction(null);
    try {
      const res = await fetch(`/api/orders/${orderId}/checkout`, { method: "POST" });
      const body = (await res.json().catch(() => ({}))) as {
        checkoutUrl?: string;
        error?: string;
        code?: string;
      };
      if (!res.ok || !body.checkoutUrl) {
        // This surface only resumes payment on a paid order, so the context is `paid`.
        setConsentAction(failureNotice({ code: body.code, context: "paid" }).action);
        setError(body.error ?? "Couldn't start checkout. Try again.");
        return;
      }
      window.location.href = body.checkoutUrl;
    } catch {
      setError("Couldn't start checkout. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-1">
      <Button variant="outline" size="sm" loading={busy} onClick={onClick}>
        Complete payment
      </Button>
      {error ? (
        <Alert tone="danger">
          <p>{error}</p>
          {consentAction ? (
            <p className="pt-2">
              <Link href={consentAction.href} className="font-medium underline">
                {consentAction.label}
              </Link>
            </p>
          ) : null}
        </Alert>
      ) : null}
    </div>
  );
}
