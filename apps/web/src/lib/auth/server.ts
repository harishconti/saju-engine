import { createNeonAuth } from "@neondatabase/auth/next/server";

type Auth = ReturnType<typeof createNeonAuth>;

let instance: Auth | null = null;

function authInstance(): Auth {
  if (!instance) {
    const baseUrl = process.env.NEON_AUTH_BASE_URL;
    const secret = process.env.NEON_AUTH_COOKIE_SECRET;
    if (!baseUrl || !secret) {
      throw new Error(
        "Neon Auth is not configured: set NEON_AUTH_BASE_URL and NEON_AUTH_COOKIE_SECRET (>= 32 chars).",
      );
    }
    if (secret.length < 32) {
      throw new Error("NEON_AUTH_COOKIE_SECRET must be at least 32 characters (HMAC-SHA256).");
    }
    instance = createNeonAuth({ baseUrl, cookies: { secret } });
  }
  return instance;
}

/**
 * Lazily constructed Neon Auth server client.
 *
 * Constructed on FIRST PROPERTY ACCESS (request time), never at module load — because `next build`
 * runs without runtime secrets (locally and in CI). A module-scope `createNeonAuth(...)` would break
 * the build.
 *
 * Provides all Better Auth server methods plus `.handler()` and `.middleware()`.
 * Contract: docs/webapp/04-auth-and-roles.md
 */
export const auth: Auth = new Proxy({} as Auth, {
  get(_target, prop) {
    const a = authInstance() as unknown as Record<string, unknown>;
    const value = a[prop as string];
    return typeof value === "function" ? (value as (...args: unknown[]) => unknown).bind(a) : value;
  },
});
