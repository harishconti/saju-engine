"use client";

import { useState } from "react";
import { Alert, Button } from "@/components/ui";

/** Creates a fresh hosted-checkout session for an existing unpaid order. */
export function ResumeCheckoutButton({ orderId }: { orderId: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/orders/${orderId}/checkout`, { method: "POST" });
      const body = (await res.json().catch(() => ({}))) as { checkoutUrl?: string; error?: string };
      if (!res.ok || !body.checkoutUrl) {
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
      {error ? <Alert tone="danger">{error}</Alert> : null}
    </div>
  );
}
