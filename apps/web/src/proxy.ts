import type { NextRequest } from "next/server";
import { auth } from "@/lib/auth/server";

/**
 * Next 16 middleware (the `middleware.ts` convention was renamed to `proxy.ts`).
 *
 * ⚠️ IMPORTANT BEHAVIOUR: Neon Auth's middleware PROTECTS EVERY PATH IT MATCHES. Its
 * `shouldProtectRoute()` returns true for anything outside a small skip list (/api/auth, /auth/*),
 * so matching "/" here would make the entire public site require a login.
 *
 * Therefore the matcher lists ONLY protected routes. Public routes (/, /sample, /login, legal
 * pages) are never matched, and the dashboard/admin layouts independently re-check the session
 * server-side as defence in depth.
 *
 * `/auth/complete` IS matched: that is where every OAuth and magic-link sign-in lands, and the
 * middleware is what exchanges the `neon_auth_session_verifier` for a session cookie. The exchange
 * runs before the session check, so an arriving user is not bounced to /login.
 */

let middleware: ((req: NextRequest) => Promise<Response> | Response) | null = null;

export default function proxy(req: NextRequest) {
  if (!middleware) {
    middleware = auth.middleware({ loginUrl: "/login" }) as unknown as (
      req: NextRequest,
    ) => Promise<Response> | Response;
  }
  return middleware(req);
}

export const config = {
  matcher: [
    "/auth/complete",
    "/dashboard/:path*",
    "/admin/:path*",
    "/reports/:path*",
  ],
};
