"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Alert, Button, Field, Input } from "@/components/ui";

/**
 * Password reset, confirm step (AU-41, D6).
 *
 * The token arrives in the query string. It is a one-time credential, so:
 *  - it is read once into a ref and handed to the submit; it is never state, never rendered, never
 *    logged, and the ref is cleared as soon as the server accepts it;
 *  - the address bar is scrubbed on mount, so the token is not sitting in a screenshot, a pasted URL
 *    or the next history entry;
 *  - the server decides validity. Invalid and expired get one message here, because the server gives
 *    one answer.
 *
 * Residual exposure this page cannot remove: the token was in the request URL as the provider's
 * redirect arrived, so the hosting platform's access log may have seen it. The page scrubs as early
 * as React runs; keeping it out of platform logs needs a redaction rule at that layer.
 */

const INVALID = "This reset link is invalid or has expired. Request a new one.";
const UNAVAILABLE = "We couldn't reset your password just now. Please try again.";

export function ResetPasswordForm() {
  const params = useSearchParams();
  // The token itself lives in a ref (not state) so it is never part of a rendered snapshot and is
  // not serialised anywhere React keeps; `hasToken` is the only thing render reads.
  const tokenRef = useRef<string | null>(params.get("token"));
  // Frozen at mount: scrubbing the address bar must never be able to make the form disappear mid-edit.
  const [hasToken] = useState(() => Boolean(params.get("token")));
  const [error, setError] = useState<string | null>(hasToken ? null : INVALID);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");

  useEffect(() => {
    // Replace, not push: the token must not be the history entry a Back press restores.
    window.history.replaceState(null, "", "/reset-password");
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const token = tokenRef.current;
    if (!token) {
      setError(INVALID);
      return;
    }
    if (newPassword.length < 8) {
      setError("Use at least 8 characters.");
      return;
    }
    if (newPassword !== confirmation) {
      setError("Those passwords don't match. Please retype them.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/account/password-reset/confirm", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ token, newPassword }),
      });
      if (res.status === 429) {
        setError("Too many attempts. Please wait a few minutes and try again.");
        return;
      }
      if (res.status === 400) {
        setError(INVALID);
        return;
      }
      if (!res.ok) {
        setError(UNAVAILABLE);
        return;
      }
      // The token is spent; drop it.
      tokenRef.current = null;
      setNewPassword("");
      setConfirmation("");
      setDone(true);
    } catch {
      setError(UNAVAILABLE);
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="space-y-4">
        <Alert tone="success">Your password has been changed. You can sign in with it now.</Alert>
        <p className="text-center text-xs text-muted-foreground">
          <Link href="/login" className="underline hover:text-foreground">
            Back to sign in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error ? <Alert tone="danger">{error}</Alert> : null}

      {hasToken ? (
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="New password" htmlFor="new-password" hint="At least 8 characters.">
            <Input
              id="new-password"
              name="new-password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={8}
            />
          </Field>
          <Field label="Confirm new password" htmlFor="confirm-password">
            <Input
              id="confirm-password"
              name="confirm-password"
              type="password"
              autoComplete="new-password"
              value={confirmation}
              onChange={(e) => setConfirmation(e.target.value)}
              required
              minLength={8}
            />
          </Field>
          <Button type="submit" size="md" className="w-full" loading={busy}>
            Set new password
          </Button>
        </form>
      ) : (
        <p className="text-sm text-muted-foreground">
          <Link href="/forgot-password" className="underline hover:text-foreground">
            Request a new reset link
          </Link>
        </p>
      )}

      <p className="text-center text-xs text-muted-foreground">
        <Link href="/login" className="underline hover:text-foreground">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
