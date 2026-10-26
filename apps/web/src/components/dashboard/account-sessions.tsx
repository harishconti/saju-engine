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
 *
 * `sessions` is deliberately nullable and the action does not depend on it. The provider's
 * `list-sessions` endpoint is gated by `freshSessionMiddleware`, which compares the session's
 * *creation* time against `freshAge` (24 h by default) and refuses with `SESSION_NOT_FRESH`; the
 * refresh that keeps an active session alive moves `expiresAt`/`updatedAt`, not `createdAt`. The
 * revoke endpoint uses `sensitiveSessionMiddleware`, which applies no such comparison. So a
 * returning user — exactly the person with other devices to end — can get `null` here and still
 * revoke successfully. Losing the control in that case would fail the whole feature.
 */

const GENERIC_ERROR = "We couldn't sign out your other devices. Please try again.";

export function SessionsPanel({ sessions }: { sessions: AccountSession[] | null }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  // Null means "we couldn't ask", so the count is unknown rather than zero — the button stays
  // enabled instead of asserting there is nothing to sign out.
  const otherSessions = sessions === null ? null : sessions.filter((session) => !session.current).length;

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

      {sessions === null ? (
        // Distinct from the empty list below. The suggestion is accurate: reloading asks the
        // provider again, while signing out and back in revokes nothing anywhere else.
        <Alert tone="warning" title="We couldn't load your active sessions">
          Refresh the page to try again. You can still sign out of your other devices below — that
          action does not need the list.
        </Alert>
      ) : (
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
      )}

      {error ? <Alert tone="danger">{error}</Alert> : null}
      {done ? (
        <Alert tone="success">Signed out of your other devices. You&apos;re still signed in on this device.</Alert>
      ) : null}

      {otherSessions === 0 ? (
        <p className="text-xs text-muted-foreground">You&apos;re only signed in on this device.</p>
      ) : null}

      <Button
        variant="outline"
        size="sm"
        loading={busy}
        disabled={otherSessions === 0}
        onClick={revokeOthers}
      >
        Sign out of other devices
      </Button>
    </div>
  );
}
