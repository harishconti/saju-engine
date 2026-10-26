import { ApiError, handle, json } from "@/lib/api";
import { requireUser, revokeOtherSessions } from "@/lib/auth";
import { rateLimit, WINDOW } from "@/lib/ratelimit";

/**
 * "Sign out of other devices" (AU-40, owner decision D6).
 *
 * Deliberately a POST route rather than a server action: the account page is a server component, and
 * the action needs one place to apply the rate limit and one place to report a provider failure to
 * the panel. The identity is `requireUser()` — the same gate every other account route uses.
 *
 * Revocation itself is the existing `revokeOtherSessions()` helper, which calls the provider's
 * `revoke-all-sessions` endpoint with no arguments. Neon documents that endpoint as ending every
 * session *except the current one*, so the caller stays signed in; this route neither re-implements
 * that filter nor accepts a session id from the browser (which would let a visitor pick whose
 * session to end).
 */

export const dynamic = "force-dynamic";

/**
 * Five an hour is generous for a real person (the action is taken once, then the list is empty) and
 * bounds a scripted loop against the identity provider. Bucket key: the local user id, because this
 * action requires a session and two accounts behind one IP must not exhaust each other's allowance.
 */
const REVOKE_LIMIT = 5;

export const POST = handle(async () => {
  const user = await requireUser();
  await rateLimit(`sessions:revoke:${user.id}`, REVOKE_LIMIT, WINDOW.hour);

  if (!(await revokeOtherSessions())) {
    throw ApiError.unavailable(
      "We couldn't sign out your other devices. Please try again.",
      "SESSION_REVOKE_FAILED",
    );
  }

  return json({ ok: true });
});
