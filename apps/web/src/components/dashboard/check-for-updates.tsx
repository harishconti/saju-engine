"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alert, Button } from "@/components/ui";
import { failureNotice, type FailureAction } from "@/lib/visitor-copy";

/**
 * User-triggered dispatch.
 *
 * Reports sit in "in review" until a human checks them, but a *generation* can also be queued behind a
 * failed webhook dispatch. On Vercel Hobby there is no per-minute cron to pick that up promptly, so the
 * client gets a button rather than a mysterious wait.
 */
export function CheckForUpdatesButton() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // AU-24 (D7): a withdrawn consent means this action cannot run, and the fix is on the account
  // page — so the alert links there instead of leaving the customer to retry a refusal. The link
  // comes from the shared `failureNotice` helper rather than a local copy of the mapping.
  const [consentAction, setConsentAction] = useState<FailureAction | null>(null);

  async function onClick() {
    setBusy(true);
    setError(null);
    setMessage(null);
    setConsentAction(null);
    try {
      const res = await fetch("/api/jobs/kick", { method: "POST" });
      const body = (await res.json().catch(() => ({}))) as { message?: string; error?: string; code?: string };
      if (!res.ok) {
        // This button only acts on paid orders, so the failure context is `paid`.
        setConsentAction(failureNotice({ code: body.code, context: "paid" }).action);
        setError(body.error ?? "Couldn't check right now.");
        return;
      }
      setMessage(body.message ?? "Checked.");
      router.refresh();
    } catch {
      setError("Couldn't check right now.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button variant="outline" size="sm" loading={busy} onClick={onClick}>
        Check for updates
      </Button>
      {message ? <span className="text-xs text-muted-foreground">{message}</span> : null}
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
