"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Alert, Button, Card, CardContent, Field, Input, buttonClasses } from "@/components/ui";
import { ElementalRule, SealMark } from "@/components/viz";
import { isAuthError } from "@neondatabase/auth/next";
import { authClient } from "@/lib/auth/client";
import { safeNext } from "@/lib/safe-next";

type Mode = "signin" | "signup";
type Busy = null | "google" | "email" | "magic";

/**
 * The reason an auth call failed, in words a visitor can act on.
 *
 * Neon Auth's fetch wrapper **throws** a normalized `AuthError` on any non-2xx response rather than
 * returning `{ error }`, so a wrong password lands in `catch`, not in `result.error`. A bare `catch`
 * therefore turned "Invalid email or password" and "User already exists" into the same vague
 * sentence. Only an `AuthError` message is shown; anything else (a network failure) gets the fallback.
 *
 * Except whether an account exists: "User already exists" on sign-up tells anyone which emails are
 * registered here, so those answers get one neutral sentence (AU-15). Matched on the message as well
 * as the code, because the server's `USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL` is not in Neon's code map.
 * The same helper serves a *returned* `{ error }` as well as a thrown one: AU-15 found three paths
 * that printed `result.error.message` raw, which reintroduced the enumeration leak.
 */
const ACCOUNT_EXISTENCE_CODES = new Set([
  "user_already_exists",
  "email_exists",
  "user_not_found",
  "identity_not_found",
  "USER_ALREADY_EXISTS",
  "USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL",
  "USER_NOT_FOUND",
]);

const NEUTRAL_AUTH_ERROR =
  "We couldn't do that with this email. If you already have an account, sign in or use a magic link.";

/**
 * AU-24 (owner decision D7): a pending deletion disables sign-in. Credentials still verify at the
 * identity provider, so the visitor needs a specific reason and the one control that resolves it —
 * the deletion stays cancellable until it runs, but the account page that normally offers the
 * cancel is unreachable from a blocked session.
 */
const PENDING_DELETION_ERROR =
  "This account is pending deletion, so sign-in is turned off. You can cancel the scheduled deletion below and sign in again.";

/** `GET /api/account/deletion` answers this for a session blocked by its own pending deletion. */
const ACCOUNT_PENDING_DELETION = "ACCOUNT_PENDING_DELETION";

type AuthErrorLike = { code?: unknown; message?: unknown };

/**
 * Both shapes the auth client produces: a thrown `AuthError` (marked with `__isAuthError`) and a
 * plain returned `{ code, message }`. A foreign `Error` (a network failure) is deliberately not
 * accepted — its message ("Failed to fetch") is not something a visitor can act on.
 */
function asAuthErrorLike(err: unknown): AuthErrorLike | null {
  if (!err || typeof err !== "object") return null;
  if (isAuthError(err)) return err as AuthErrorLike;
  // A thrown foreign `Error` is a transport failure ("Failed to fetch"), which the fallback covers.
  if (err instanceof Error) return null;
  if (typeof (err as AuthErrorLike).code === "string" || typeof (err as AuthErrorLike).message === "string") {
    return err as AuthErrorLike;
  }
  return null;
}

function authErrorMessage(err: unknown, fallback: string): string {
  const e = asAuthErrorLike(err);
  if (!e) return fallback;
  const code = typeof e.code === "string" ? e.code : "";
  const message = typeof e.message === "string" ? e.message.trim() : "";
  if (ACCOUNT_EXISTENCE_CODES.has(code) || /already exists|not found|already registered/i.test(message)) {
    return NEUTRAL_AUTH_ERROR;
  }
  return message || fallback;
}

/**
 * The `?error=` code a magic-link or Google failure redirect appends to `/login` (AU-15).
 * The code is shown in parentheses so support can match it to the provider's log; it is capped so a
 * hand-crafted URL cannot fill the page.
 */
function callbackErrorMessage(code: string): string {
  const reason = code.trim().slice(0, 60);
  if (reason === ACCOUNT_PENDING_DELETION) return PENDING_DELETION_ERROR;
  return reason ? `Sign-in didn't complete (${reason}). Please try again.` : "Sign-in didn't complete. Please try again.";
}

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const next = safeNext(params.get("next"));

  const [mode, setMode] = useState<Mode>("signin");
  const [busy, setBusy] = useState<Busy>(null);
  // A failed magic-link / Google callback lands back here with `?error=`; show it instead of
  // dropping the visitor on a clean form with no explanation (AU-15).
  const callbackError = params.get("error");
  const [error, setError] = useState<string | null>(callbackError ? callbackErrorMessage(callbackError) : null);
  const [notice, setNotice] = useState<string | null>(null);
  // Set when the credentials verified but the account is blocked, or when the OAuth callback came
  // back with the code. Shows the cancel control without claiming the visitor is signed in.
  const [pendingDeletion, setPendingDeletion] = useState(
    callbackError?.trim() === ACCOUNT_PENDING_DELETION,
  );
  const [cancelling, setCancelling] = useState(false);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreed, setAgreed] = useState(false);

  const completeUrl = (target: string) => {
    const origin = typeof window === "undefined" ? "" : window.location.origin;
    return `${origin}/auth/complete?next=${encodeURIComponent(target)}`;
  };

  /**
   * Where the provider sends a failed sign-in. It must be `/login` itself, not `/auth/complete`:
   * the provider appends `?error=<code>`, and `/auth/complete` (protected by the middleware) would
   * bounce a session-less arrival to `/login` without the query string.
   */
  const errorCallbackUrl = () => {
    const origin = typeof window === "undefined" ? "" : window.location.origin;
    return `${origin}/login`;
  };

  async function onGoogle() {
    setError(null);
    setBusy("google");
    try {
      const result = await authClient.signIn.social({
        provider: "google",
        callbackURL: completeUrl(next),
        newUserCallbackURL: completeUrl(next),
        errorCallbackURL: errorCallbackUrl(),
      });
      if (result?.error) setError(authErrorMessage(result?.error, "Google sign-in failed."));
    } catch (err) {
      setError(authErrorMessage(err, "Google sign-in failed. Try email instead."));
    } finally {
      setBusy(null);
    }
  }

  /**
   * Whether the just-authenticated account is blocked by its own pending deletion.
   *
   * The identity provider has no concept of our `DeletionRequest`, so the sign-in itself succeeds;
   * the server is what treats the account as signed out (`getCurrentUser`). Asking this route is
   * how the browser finds out before navigating into a wall. It answers 401 for every other
   * signed-out state, which is a plain "no".
   */
  async function isPendingDeletion(): Promise<boolean> {
    try {
      const res = await fetch("/api/account/deletion", { cache: "no-store" });
      if (!res.ok) return false;
      const body = (await res.json().catch(() => ({}))) as { pendingDeletion?: boolean };
      return body.pendingDeletion === true;
    } catch {
      // A network failure is not evidence of deletion; fall through to the normal path.
      return false;
    }
  }

  async function onCancelDeletion() {
    setError(null);
    setNotice(null);
    setCancelling(true);
    try {
      const res = await fetch("/api/account/deletion", { method: "DELETE" });
      if (!res.ok) {
        // 401 is the stale-link case: the code arrived in a URL but there is no session to cancel
        // with. Saying "sign in again" is more useful than the bare "Not signed in".
        if (res.status === 401) {
          setError("Please sign in again to cancel the scheduled deletion.");
          return;
        }
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Couldn't cancel the deletion. Please try again.");
        return;
      }
      // The session still exists — only the block is gone — so the sign-in can simply resume.
      setPendingDeletion(false);
      setNotice("Deletion cancelled. Signing you in…");
      router.push(next);
      router.refresh();
    } catch {
      setError("Couldn't cancel the deletion. Check your connection and try again.");
    } finally {
      setCancelling(false);
    }
  }

  async function onEmailSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);

    if (mode === "signup" && !agreed) {
      setError("Please accept the privacy policy and terms to create an account.");
      return;
    }
    if (mode === "signup" && !name.trim()) {
      setError("Please tell us what to call you.");
      return;
    }

    setBusy("email");
    try {
      const result =
        mode === "signup"
          ? await authClient.signUp.email({ email, password, name })
          : await authClient.signIn.email({ email, password });

      if (result?.error) {
        setError(authErrorMessage(result?.error, "That didn't work. Check your details and try again."));
        return;
      }

      if (mode === "signup") {
        // AU-22: send a new account through `/auth/complete` — the same landing every OAuth and
        // magic-link sign-in uses — so the server records the initial consent once, for all three
        // paths. A browser POST here could be lost with the tab and was only ever wired for email.
        router.push(`/auth/complete?next=${encodeURIComponent(next)}`);
      } else {
        // AU-24 (D7): credentials verified, but a pending deletion means the server will treat this
        // session as signed out. Say so here instead of letting the next page 401.
        if (await isPendingDeletion()) {
          setPendingDeletion(true);
          setError(PENDING_DELETION_ERROR);
          return;
        }
        router.push(next);
      }
      router.refresh();
    } catch (err) {
      setError(authErrorMessage(err, "That didn't work. Check your details and try again."));
    } finally {
      setBusy(null);
    }
  }

  async function onMagicLink() {
    setError(null);
    setNotice(null);
    if (!email.trim()) {
      setError("Enter your email first, then request the link.");
      return;
    }
    setBusy("magic");
    try {
      const result = await authClient.signIn.magicLink({
        email,
        callbackURL: completeUrl(next),
        newUserCallbackURL: completeUrl(next),
        errorCallbackURL: errorCallbackUrl(),
      });
      if (result?.error) {
        setError(authErrorMessage(result?.error, "Couldn't send the link."));
        return;
      }
      setNotice("Check your inbox — the link expires in a few minutes.");
    } catch (err) {
      setError(authErrorMessage(err, "Couldn't send the link. Try a different method."));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="grid-noise min-h-screen">
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 px-4 py-12">
        <div className="flex flex-col items-center gap-3 text-center">
          {/* This link holds only the seal glyph, so it needs a label — unlike the marketing header,
              where the visible "Cosmic Saju 사주" text is the accessible name (an aria-label there
              would *omit* that text and fail `label-content-name-mismatch`). */}
          <Link href="/" aria-label="Cosmic Saju — home">
            <SealMark char="四" />
          </Link>
          <h1 className="h2">{mode === "signin" ? "Welcome back" : "Create your account"}</h1>
          <p className="text-sm text-muted-foreground">
            Your chart, your reports, and your birth details in one place.
          </p>
          <ElementalRule className="max-w-32" />
        </div>

        <Card>
          <CardContent className="space-y-5 py-6">
            {/* Tabs */}
            <div className="grid grid-cols-2 gap-1 rounded-lg border border-border p-1" role="tablist">
              {(["signin", "signup"] as Mode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => {
                    setMode(m);
                    setError(null);
                    setNotice(null);
                    setPendingDeletion(false);
                  }}
                  // min-h-11 (44px): these are real controls on a touch-first page, and `py-2` alone
                  // measured 36px — under the >=44 px bar in docs/webapp/06.
                  className={
                    (mode === m
                      ? "rounded-md bg-muted px-3 text-sm font-medium text-foreground"
                      : "rounded-md px-3 text-sm text-muted-foreground hover:text-foreground") +
                    " inline-flex min-h-11 items-center justify-center py-2"
                  }
                >
                  {m === "signin" ? "Sign in" : "Sign up"}
                </button>
              ))}
            </div>

            {error ? <Alert tone="danger">{error}</Alert> : null}
            {notice ? <Alert tone="success">{notice}</Alert> : null}

            {/* The one control that resolves a pending-deletion block. Deliberately outside the
                sign-in form: it acts on the account, not on the credentials. */}
            {pendingDeletion ? (
              <Button
                type="button"
                variant="outline"
                size="md"
                className="w-full"
                loading={cancelling}
                onClick={onCancelDeletion}
              >
                Cancel scheduled deletion
              </Button>
            ) : null}

            <Button
              type="button"
              variant="outline"
              size="md"
              className="w-full"
              loading={busy === "google"}
              onClick={onGoogle}
            >
              <GoogleMark />
              Continue with Google
            </Button>

            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span className="h-px flex-1 bg-border" />
              or
              <span className="h-px flex-1 bg-border" />
            </div>

            <form onSubmit={onEmailSubmit} className="space-y-4">
              {mode === "signup" ? (
                <Field label="What should we call you?" htmlFor="name">
                  <Input
                    id="name"
                    name="name"
                    autoComplete="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                  />
                </Field>
              ) : null}

              <Field label="Email" htmlFor="email">
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  inputMode="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </Field>

              <Field
                label="Password"
                htmlFor="password"
                hint={mode === "signup" ? "At least 8 characters." : undefined}
              >
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete={mode === "signup" ? "new-password" : "current-password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </Field>

              {mode === "signup" ? (
                <label className="flex items-start gap-3 text-sm text-muted-foreground">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--primary)]"
                    checked={agreed}
                    onChange={(e) => setAgreed(e.target.checked)}
                  />
                  <span>
                    I agree to the{" "}
                    <Link href="/privacy" className="underline hover:text-foreground">
                      privacy policy
                    </Link>{" "}
                    and{" "}
                    <Link href="/terms" className="underline hover:text-foreground">
                      terms
                    </Link>
                    , including storing my birth date, time, and place to produce my reading.
                  </span>
                </label>
              ) : null}

              <Button type="submit" size="md" className="w-full" loading={busy === "email"}>
                {mode === "signin" ? "Sign in" : "Create account"}
              </Button>
            </form>

            <button
              type="button"
              onClick={onMagicLink}
              disabled={busy === "magic"}
              className={buttonClasses("ghost", "sm", "w-full")}
            >
              {busy === "magic" ? "Sending…" : "Email me a magic link instead"}
            </button>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          Readings describe tendencies and timing, not fixed outcomes. Not medical, legal, or financial advice.
        </p>
      </div>
    </main>
  );
}

function GoogleMark() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden>
      <path
        fill="#4285F4"
        d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.4a5.5 5.5 0 0 1-2.4 3.6v3h3.9c2.3-2.1 3.6-5.2 3.6-8.8Z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.2 0 5.9-1.1 7.9-2.9l-3.9-3c-1.1.7-2.5 1.2-4 1.2-3.1 0-5.7-2.1-6.7-4.9H1.3v3.1A12 12 0 0 0 12 24Z"
      />
      <path fill="#FBBC05" d="M5.3 14.4a7.2 7.2 0 0 1 0-4.6V6.7H1.3a12 12 0 0 0 0 10.8l4-3.1Z" />
      <path
        fill="#EA4335"
        d="M12 4.8c1.8 0 3.3.6 4.6 1.8l3.4-3.4A12 12 0 0 0 1.3 6.7l4 3.1C6.3 6.9 8.9 4.8 12 4.8Z"
      />
    </svg>
  );
}
