"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Badge, Button } from "@/components/ui";
import { formatDateTime } from "@/lib/format";
import { describeUserAgent } from "@/lib/device";
import type { AccountSession } from "@/lib/auth";

/**
 * The account page's active-session list and its "Sign out of other devices" action (AU-40, D6).
 *
 * The list is rendered on the server and passed in; this component exists for the action, so a
 * provider failure produces a visible error instead of a button that appears to have worked.
 */

const GENERIC_ERROR = "We couldn't sign out your other devices. Please try again.";

export function SessionsPanel({ sessions }: { sessions: AccountSession[] }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const otherSessions = sessions.filter((session) => !session.current).length;

  async function revokeOthers() {
    setBusy(true);
    setError(null);
    setDone(false);
    try {
      const res = await fetch("/api/account/sessions", { method: "POST" });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? GENERIC_ERROR);
        return;
      }
      setDone(true);
      router.refresh();
    } catch {
      // A dropped connection has no response to inspect; it must not look like success.
      setError(GENERIC_ERROR);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Everywhere your account is signed in. Signing out ends every other session; this device stays
        signed in.
      </p>

      <ul className="divide-y divide-border rounded-lg border border-border">
        {sessions.map((session) => (
          <li key={session.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
            <div>
              <p className="flex flex-wrap items-center gap-2 text-sm font-medium text-foreground">
                {describeUserAgent(session.userAgent)}
                {session.current ? <Badge tone="primary">This device</Badge> : null}
              </p>
              <p className="text-xs text-muted-foreground">Last used {formatDateTime(session.lastUsedAt)}</p>
            </div>
          </li>
        ))}
      </ul>

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {done ? (
        <Alert tone="success">Signed out of your other devices. You&apos;re still signed in on this device.</Alert>
      ) : null}

      {otherSessions === 0 ? (
        <p className="text-xs text-muted-foreground">You&apos;re only signed in on this device.</p>
      ) : null}

      <Button variant="outline" size="sm" loading={busy} disabled={otherSessions === 0} onClick={revokeOthers}>
        Sign out of other devices
      </Button>
    </div>
  );
}
