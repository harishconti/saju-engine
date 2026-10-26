import { redirect } from "next/navigation";
import { getCurrentUser, getSessionUserId, hasPendingDeletion } from "@/lib/auth";
import { recordInitialServiceConsent } from "@/lib/consent";
import { safeNext } from "@/lib/safe-next";

/**
 * Where every OAuth and magic-link sign-in lands.
 *
 * By the time this renders, the middleware (src/proxy.ts) has already exchanged the
 * `neon_auth_session_verifier` for a session cookie — and because this route is in the matcher, an
 * arrival WITHOUT a session is bounced to /login by the middleware instead of reaching this page.
 * So all that is left is to send the user onward.
 *
 * AU-22 (2026-10-26 audit): this is also the one point every sign-in path converges on — email
 * sign-up is routed here too — which makes it the only place the server can record the initial
 * `service` consent for all three methods. The old browser-side POST ran on email sign-up only and
 * was lost if the tab closed. A failure here must never block a sign-in that has already
 * authenticated: the sample route refuses to store birth data without consent, so the gap is
 * recoverable on the account page.
 */
export const dynamic = "force-dynamic";

export default async function AuthCompletePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  const next = Array.isArray(params.next) ? params.next[0] : params.next;
  let pendingDeletion = false;

  try {
    const user = await getCurrentUser();
    if (user) {
      await recordInitialServiceConsent(user.id);
    } else {
      // AU-24 (owner decision D7): an account pending deletion authenticates at the provider but
      // is treated as signed out. Redirecting it onward would drop it into a 401 page; the login
      // page is where the reason and the cancel control live.
      const sessionUserId = await getSessionUserId();
      pendingDeletion = sessionUserId ? await hasPendingDeletion(sessionUserId) : false;
    }
  } catch (err) {
    // Recording consent is best-effort by design (see the comment above); the sign-in itself is not.
    console.error("auth/complete: could not record initial consent", err);
  }

  if (pendingDeletion) redirect("/login?error=ACCOUNT_PENDING_DELETION");
  redirect(safeNext(next));
}
