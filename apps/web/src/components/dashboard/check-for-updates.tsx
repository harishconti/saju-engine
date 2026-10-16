"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button } from "@/components/ui";

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

  async function onClick() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const res = await fetch("/api/jobs/kick", { method: "POST" });
      const body = (await res.json().catch(() => ({}))) as { message?: string; error?: string };
      if (!res.ok) {
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
      {error ? <Alert tone="danger">{error}</Alert> : null}
    </div>
  );
}
