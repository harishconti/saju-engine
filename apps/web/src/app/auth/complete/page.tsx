import { redirect } from "next/navigation";

/**
 * Where every OAuth and magic-link sign-in lands.
 *
 * By the time this renders, the middleware (src/proxy.ts) has already exchanged the
 * `neon_auth_session_verifier` for a session cookie — and because this route is in the matcher, an
 * arrival WITHOUT a session is bounced to /login by the middleware instead of reaching this page.
 * So all that is left is to send the user onward.
 */
export const dynamic = "force-dynamic";

function safeNext(raw: string | string[] | undefined): string {
  const value = Array.isArray(raw) ? raw[0] : raw;
  if (!value) return "/dashboard";
  if (!value.startsWith("/") || value.startsWith("//")) return "/dashboard";
  return value;
}

export default async function AuthCompletePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  redirect(safeNext(params.next));
}
