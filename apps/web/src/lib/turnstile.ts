/**
 * Cloudflare Turnstile — bot protection for the free-sample form.
 *
 * Contract: docs/webapp/03-api-spec.md
 *
 * **Fail closed when configured, skip when not.** No `TURNSTILE_SECRET_KEY` means local development
 * (the widget cannot render either), so verification is deliberately not attempted. Once a secret
 * exists, an absent or invalid token is a refusal — accepting it anyway would make the control
 * decorative, which is precisely the state this replaces: the `turnstileToken` field sat in the zod
 * schema for months with nothing on either end reading it.
 *
 * The widget itself is rendered by `components/turnstile-widget.tsx`, keyed on the PUBLIC site key.
 * Keep the pair in step: the secret alone verifies, and the site key alone renders, but the control
 * only works when both are deployed.
 */

const SITEVERIFY = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

/**
 * Rollout mode, from `TURNSTILE_MODE`:
 *
 *   `off`     (default) — do not verify at all. The safe state.
 *   `log`     — verify when a token is present, log the outcome, **never block**.
 *   `enforce` — refuse on failure.
 *
 * This exists because the control can take the whole funnel down: if the widget fails to render,
 * no token is ever produced, and an enforcing server then refuses *every* visitor. That is not
 * hypothetical — it happened on 2026-10-16. `log` lets real traffic prove the widget works before
 * anything is enforced, and it cannot cause an outage because it never returns a refusal.
 */
export type TurnstileMode = "off" | "log" | "enforce";

export function turnstileMode(): TurnstileMode {
  const raw = process.env.TURNSTILE_MODE?.trim().toLowerCase();
  if (raw === "enforce") return "enforce";
  if (raw === "log") return "log";
  return "off";
}

/** True when the server can verify tokens. Drives whether `verifyTurnstile` does anything. */
export function isTurnstileConfigured(): boolean {
  return Boolean(process.env.TURNSTILE_SECRET_KEY?.trim());
}

export interface TurnstileResult {
  ok: boolean;
  /** True when no secret is configured, so verification was intentionally skipped. */
  skipped?: boolean;
  /** Short, PII-free reason suitable for logs. Never surfaced to the client verbatim. */
  error?: string;
}

/**
 * Verify a Turnstile token. Never throws — a Cloudflare outage must degrade to a clean refusal,
 * not a 500, and must never be mistaken for success.
 */
export async function verifyTurnstile(
  token: string | undefined,
  remoteIp?: string,
): Promise<TurnstileResult> {
  const secret = process.env.TURNSTILE_SECRET_KEY?.trim();
  if (!secret) return { ok: true, skipped: true };

  const response = token?.trim();
  if (!response) return { ok: false, error: "missing-token" };

  const form = new URLSearchParams({ secret, response });
  // Optional: Cloudflare cross-checks this against the challenge's origin.
  if (remoteIp) form.set("remoteip", remoteIp);

  try {
    const res = await fetch(SITEVERIFY, {
      method: "POST",
      body: form,
      signal: AbortSignal.timeout(10_000),
    });

    const body = (await res.json().catch(() => ({}))) as {
      success?: boolean;
      "error-codes"?: string[];
    };

    if (!res.ok) return { ok: false, error: `HTTP ${res.status}` };
    if (!body.success) {
      return { ok: false, error: (body["error-codes"] ?? []).join(",") || "rejected" };
    }
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.name : "unknown" };
  }
}
