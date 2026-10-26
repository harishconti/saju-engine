import { clientIp, handle, json, parseJson } from "@/lib/api";
import { auth } from "@/lib/auth/server";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { passwordResetRequestSchema } from "@/lib/validation/schemas";

/**
 * Password reset, request step (AU-41, owner decision D6).
 *
 * The browser posts here instead of calling the auth proxy directly for one reason: the rate limit
 * has to live somewhere the visitor cannot skip, and the proxy path is shared by every auth method.
 *
 * Neutrality is the contract: this route answers **202 `{ ok: true }` for every syntactically valid
 * address**, whether the account exists, whether the provider sent a mail, and whether the provider
 * failed. The provider itself already simulates the lookup for unknown addresses; this route adds no
 * branch of its own, so the bytes cannot become an account-existence oracle. A malformed address is
 * a 422 — that is a statement about the input, not about any account.
 *
 * Nothing here logs the address: the failure line carries the provider's code class only.
 */

export const dynamic = "force-dynamic";

/**
 * Five an hour per IP. One reset request is the normal case; a couple more cover a mistyped address
 * or a mail that never arrived. Beyond that the cost is an outbound email, so the limit has to be
 * tighter than the confirm step's.
 *
 * Keyed on the visitor IP (via `clientIp`, the same trusted-header helper the sample route uses),
 * because this route is deliberately unauthenticated. The limit is not per address — a bucket key
 * containing an email would put personal data in the rate-limit table, and the neutral response
 * gives a distributed prober almost nothing to learn anyway.
 */
const REQUEST_LIMIT = 5;

function appOrigin(): string {
  return (process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000").replace(/\/+$/, "");
}

export const POST = handle(async (req) => {
  const ip = clientIp(req);
  await rateLimit(`password-reset:request:${ip}`, REQUEST_LIMIT, WINDOW.hour);

  const { email } = await parseJson(req, passwordResetRequestSchema);

  try {
    const res = (await auth.requestPasswordReset({
      email,
      // The provider mails a link that comes back to this page with `?token=…`. This exact origin
      // must be allowlisted in the Neon console, or the provider refuses the redirect (see
      // docs/webapp/08-deployment.md § Password reset email).
      redirectTo: `${appOrigin()}/reset-password`,
    })) as { error?: { code?: string } | null } | undefined;

    if (res?.error) {
      // The code, never the message: it can echo the address the provider refused.
      console.error(
        "[auth] requestPasswordReset failed:",
        typeof res.error.code === "string" ? res.error.code : "provider error",
      );
    }
  } catch (err) {
    console.error("[auth] requestPasswordReset failed:", err instanceof Error ? err.name : "unknown");
  }

  // One answer for every valid request. See the neutrality note above.
  return json({ ok: true }, 202);
});
