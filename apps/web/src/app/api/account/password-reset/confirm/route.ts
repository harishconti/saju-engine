import { ApiError, clientIp, handle, json, parseJson } from "@/lib/api";
import { auth } from "@/lib/auth/server";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { passwordResetConfirmSchema } from "@/lib/validation/schemas";

/**
 * Password reset, confirm step (AU-41, owner decision D6).
 *
 * `resetPassword` server-side needs no session — the emailed token *is* the authorisation — and this
 * context must not try to revoke sessions: there is nobody signed in here, and the provider's own
 * `revokeSessionsOnPasswordReset` setting is the place that decision lives.
 *
 * The token is treated as a credential throughout: it is read from the JSON body, passed straight to
 * the provider, and never logged, echoed, or put into an error. Invalid and expired tokens get the
 * same status and the same body, so the response reveals only "usable / not usable".
 */

export const dynamic = "force-dynamic";

/**
 * Ten an hour per IP. One or two attempts cover a typo; the token is single-use and high-entropy, so
 * this limit is about bounding a scripted loop, not about making guessing infeasible.
 *
 * Keyed on the visitor IP for the same reason as the request step: an unauthenticated route, and a
 * bucket keyed on the token would copy a credential into the rate-limit table.
 */
const CONFIRM_LIMIT = 10;

const INVALID_TOKEN_MESSAGE = "This reset link is invalid or has expired. Request a new one.";
const UNAVAILABLE_MESSAGE = "We couldn't reset your password just now. Please try again.";
const RATE_LIMITED_MESSAGE = "Too many attempts. Please try again in a little while.";

/**
 * The only provider status that is a statement about *this token*.
 *
 * The installed provider emits 400 for every rejection: `resetPassword` in
 * `node_modules/better-auth/dist/api/routes/password.mjs` throws `APIError.from("BAD_REQUEST", …)`
 * for a missing token, a consumed/expired verification (`INVALID_TOKEN`), `USER_NOT_FOUND`, and a
 * new password that is too short or too long (`INVALID_PASSWORD`). It never emits 401/404/410.
 *
 * So any other 4xx comes from something in between — a proxy, a wrong `baseURL` — and means "try
 * again", not "your link is dead". A blanket "any 4xx means a bad link" told a rate-limited or
 * misrouted caller to discard a link that still works; the token is single-use, so the wrong
 * verdict here costs the person their reset.
 */
const TOKEN_REJECTION_STATUSES = new Set([400]);

export const POST = handle(async (req) => {
  const ip = clientIp(req);
  await rateLimit(`password-reset:confirm:${ip}`, CONFIRM_LIMIT, WINDOW.hour);

  const { token, newPassword } = await parseJson(req, passwordResetConfirmSchema);

  let failure: { status?: unknown; code?: unknown } | null = null;
  try {
    const res = (await auth.resetPassword({ newPassword, token })) as
      | { error?: { status?: unknown; code?: unknown } | null }
      | undefined;
    failure = res?.error ?? null;
  } catch (err) {
    // The class only. A thrown message here is exactly where the token could leak into a log.
    console.error("[auth] resetPassword failed:", err instanceof Error ? err.name : "unknown");
    throw ApiError.unavailable(UNAVAILABLE_MESSAGE, "RESET_UNAVAILABLE");
  }

  if (failure) {
    console.error(
      "[auth] resetPassword failed:",
      typeof failure.code === "string" ? failure.code : "provider error",
    );
    // A provider outage must not be reported as a bad token — the visitor would discard a link
    // that still works. Conversely only a token-rejection status is a statement about the link;
    // the token is single-use, so a wrong verdict here costs the person their reset.
    const status = typeof failure.status === "number" ? failure.status : 0;
    if (TOKEN_REJECTION_STATUSES.has(status)) {
      throw new ApiError(400, "INVALID_RESET_TOKEN", INVALID_TOKEN_MESSAGE);
    }
    if (status === 429) {
      throw ApiError.rateLimited(RATE_LIMITED_MESSAGE);
    }
    throw ApiError.unavailable(UNAVAILABLE_MESSAGE, "RESET_UNAVAILABLE");
  }

  return json({ ok: true });
});
