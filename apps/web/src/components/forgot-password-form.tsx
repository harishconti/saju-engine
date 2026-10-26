"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert, Button, Field, Input } from "@/components/ui";

/**
 * Password reset, request step (AU-41, D6).
 *
 * The confirmation is deliberately conditional ("if an account exists…") and is the only outcome
 * for any successful server answer, so this form never reveals whether an address is registered.
 * The server route enforces the same thing on the wire; this is the human-readable half.
 */

const CONFIRMATION =
  "If an account exists for that address, we've sent a reset link. Check your inbox — the link expires in an hour.";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/account/password-reset", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      // The limit is about this visitor's request rate, not about any account, so saying so is not
      // an enumeration leak — and claiming the mail was sent would be a lie.
      if (res.status === 429) {
        setError("Too many reset requests. Please wait a few minutes and try again.");
        return;
      }
      if (!res.ok) {
        setError("We couldn't send that just now. Please try again.");
        return;
      }
      setSent(true);
    } catch {
      setError("We couldn't send that just now. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      {sent ? (
        <Alert tone="success">{CONFIRMATION}</Alert>
      ) : (
        <>
          <p className="text-sm text-muted-foreground">
            Enter the email address you signed up with and we&apos;ll send you a link to choose a new
            password.
          </p>
          {error ? <Alert tone="danger">{error}</Alert> : null}
          <form onSubmit={onSubmit} className="space-y-4">
            <Field label="Email" htmlFor="reset-request-email">
              <Input
                id="reset-request-email"
                name="email"
                type="email"
                autoComplete="email"
                inputMode="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </Field>
            <Button type="submit" size="md" className="w-full" loading={busy}>
              Send reset link
            </Button>
          </form>
        </>
      )}

      <p className="text-center text-xs text-muted-foreground">
        <Link href="/login" className="underline hover:text-foreground">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
