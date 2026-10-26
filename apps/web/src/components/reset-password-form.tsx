"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Alert, Button, Field, Input } from "@/components/ui";

/**
 * Password reset, confirm step (AU-41, D6).
 *
 * The token arrives in the query string. It is read from `window.location.search` **on the client**
 * and never from the page's `searchParams`: Next serialises a page's search params into the
 * server-rendered flight payload, so reading them there would deliver the credential inside the
 * HTML that a reverse proxy, an edge cache or an error reporter may keep. It is a one-time
 * credential, so:
 *  - it is read once into a ref and handed to the submit; it is never state, never rendered, never
 *    logged, and the ref is cleared as soon as the server accepts it;
 *  - the address bar is scrubbed on mount, so the token is not sitting in a screenshot, a pasted URL
 *    or the next history entry;
 *  - the server decides validity. Invalid and expired get one message here, because the server gives
 *    one answer.
 *
 * Residual exposure this page cannot remove: the token was in the request URL as the provider's
 * redirect arrived, so the host's and any reverse proxy's access log may have seen it. Scrubbing
 * happens only after React runs; keeping it out of those logs needs a redaction rule at that layer
 * (see docs/webapp/08-deployment.md § Password reset email).
 */

const INVALID = "This reset link is invalid or has expired. Request a new one.";
const UNAVAILABLE = "We couldn't reset your password just now. Please try again.";
const MIN_PASSWORD = 8;
const MAX_PASSWORD = 128;

export function ResetPasswordForm() {
  // The token itself lives in a ref (not state) so it is never part of a rendered snapshot and is
  // not serialised anywhere React keeps; `hasToken` is the only thing render reads.
  const tokenRef = useRef<string | null>(null);
  // Guard against a re-run (React Strict Mode mounts effects twice in development): the second run
  // would see the already-scrubbed URL and wrongly conclude the link had no token.
  const loadedRef = useRef(false);
  const [ready, setReady] = useState(false);
  const [hasToken, setHasToken] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [newPassword, setNewPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");

  useEffect(() => {
    if (loadedRef.current) return;
    loadedRef.current = true;
    const token = new URLSearchParams(window.location.search).get("token");
    tokenRef.current = token;
    setHasToken(Boolean(token));
    setError(token ? null : INVALID);
    setReady(true);
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
    if (newPassword.length < MIN_PASSWORD) {
      setError(`Use at least ${MIN_PASSWORD} characters.`);
      return;
    }
    if (newPassword.length > MAX_PASSWORD) {
      setError(`Use at most ${MAX_PASSWORD} characters.`);
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

  // The server renders this shell without a token and without the form; the address bar is read
  // after mount so the credential never appears in the delivered HTML.
  if (!ready) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
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
          <Field
            label="New password"
            htmlFor="new-password"
            hint={`At least ${MIN_PASSWORD} characters, at most ${MAX_PASSWORD}.`}
          >
            <Input
              id="new-password"
              name="new-password"
              type="password"
              autoComplete="new-password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={MIN_PASSWORD}
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
              minLength={MIN_PASSWORD}
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
