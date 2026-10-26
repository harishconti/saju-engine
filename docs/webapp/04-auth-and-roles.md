# 04 — Auth and roles

Identity is **Neon Auth** (managed Better Auth) on the same Neon project as the data. We store no
passwords, no sessions, and no OAuth tokens.

## Division of responsibility

| Neon Auth owns | We own |
|---|---|
| User records, credentials, sessions, OAuth flows, magic links, email verification | A `User` row **mirrored** from the Neon Auth identity, plus roles, consent, and everything else |
| The `neon_auth` database schema | Our own tables. **Never touch `neon_auth`**, with one documented exception: account erasure deletes the identity over the app's `DATABASE_URL` after the local erasure commits, because the SDK offers the cron no other route (AU-25 — see [02](02-data-model.md) §Retention and the note on `schema.prisma`). |

## The three files

Auth lives in exactly one folder so it can be replaced:

```
src/lib/auth/server.ts   ← lazy server client + middleware factory
src/lib/auth/client.ts   ← browser client
src/lib/auth/index.ts    ← getCurrentUser / requireUser / user mirroring
src/app/api/auth/[...path]/route.ts   ← pass-through proxy to Neon Auth
src/proxy.ts             ← Next 16 middleware: the actual gate
```

### `server.ts` — lazy behind a Proxy

Neon Auth's client must not be constructed at module load, because `next build` runs **without**
runtime secrets (locally and in CI). A module-scope `createNeonAuth(...)` would break the build.

```ts
import { createNeonAuth } from '@neondatabase/auth/next/server';

type Auth = ReturnType<typeof createNeonAuth>;
let instance: Auth | null = null;

function authInstance(): Auth {
  if (!instance) {
    const baseUrl = process.env.NEON_AUTH_BASE_URL;
    const secret = process.env.NEON_AUTH_COOKIE_SECRET;
    if (!baseUrl || !secret) {
      throw new Error('Neon Auth is not configured: set NEON_AUTH_BASE_URL and NEON_AUTH_COOKIE_SECRET (>= 32 chars).');
    }
    instance = createNeonAuth({ baseUrl, cookies: { secret } });
  }
  return instance;
}

/** Constructed on first property access (request time), never at module load. */
export const auth: Auth = new Proxy({} as Auth, {
  get(_t, prop) {
    const a = authInstance() as unknown as Record<string, unknown>;
    const v = a[prop as string];
    return typeof v === 'function' ? (v as (...args: unknown[]) => unknown).bind(a) : v;
  },
});
```

### `client.ts` — talks to our own origin

```ts
'use client';
import { createAuthClient } from '@neondatabase/auth/next';

// No arguments: it talks to the same-origin proxy at /api/auth/[...path].
export const authClient = createAuthClient();
```

### The proxy route

```ts
async function dispatch(method: Method, req: Request, ctx: Ctx): Promise<Response> {
  try {
    return await auth.handler()[method](req, ctx);
  } catch (err) {
    return errorResponse(err);
  }
}
export const GET = (req, ctx) => dispatch('GET', req, ctx);
export const POST = (req, ctx) => dispatch('POST', req, ctx);
// … PUT, DELETE, PATCH
```

### `src/proxy.ts` — the gate

Next 16 renamed the middleware convention from `middleware.ts` to `proxy.ts`. Built lazily for the
same build-time reason.

```ts
export default function proxy(req: NextRequest) {
  if (!middleware) middleware = auth.middleware({ loginUrl: '/login' });
  return middleware(req);
}

export const config = {
  matcher: ['/', '/auth/complete', '/dashboard/:path*', '/admin/:path*'],
};
```

⚠️ `/auth/complete` must be in the matcher: that is where **every** OAuth and magic-link sign-in
lands, and the middleware is what exchanges the `neon_auth_session_verifier` for a session cookie.
Omitting it produces the classic "OAuth succeeded but the user never arrives" bug.

## User mirroring

The Neon Auth identity is the source of truth for identity; our `User` row is where roles, consent,
and relations hang. `getCurrentUser()` mirrors on read.

```ts
export const getCurrentUser = cache(async (): Promise<AppUser | null> => {
  const { data: session } = await auth.getSession();
  const u = session?.user as NeonUser | undefined;
  if (!u?.id) return null;
  return mirrorUser(u);
});
```

`mirrorUser()`:

1. Normalises (`email` falls back to `<id>@neon-auth.local`, `name` falls back to the email local
   part).
2. `findUnique` by Neon Auth id.
3. If found and unchanged → return; if only email/name drifted → update.
4. If absent → `create`. **A P2002 unique violation here is not an error** — it is the first-sign-in
   race, so catch it and re-read.
5. **Claims pending invitations** if the product ever adds them (it does not in v1, but the hook
   point is documented so nobody re-invents it later).

`getCurrentUser` is wrapped in React's `cache()` so a page and its layout resolve the session once.

## Guards

```ts
export async function requireUser(): Promise<AppUser> {
  const user = await getCurrentUser();
  if (!user) throw ApiError.unauthorized();
  return user;
}
```

```ts
/** Roles are always read fresh from the database — never trusted from a token. */
export async function requireRole(minRole: Role): Promise<AppUser> {
  const user = await requireUser();
  if (!hasMinRole(user.role, minRole)) throw ApiError.forbidden();
  return user;
}
```

| Role | Rank | Grants |
|---|---|---|
| `USER` | 1 | Own profiles, orders, reports |
| `ADMIN` | 2 | The review console, manual payment, override/approve/reject |

**Admin is doubly gated:** `role = ADMIN` in the database **and** the account's email present in the
`ADMIN_EMAILS` environment variable. Two independent conditions means a database compromise alone
does not hand over the review console, and revoking access does not require a data change.

**How the role is granted.** `mirrorUser()` derives it from the allowlist: an account whose email is in
`ADMIN_EMAILS` is written `ADMIN`, and everyone else is left exactly as they were. It deliberately never
*demotes* — removing an address from `ADMIN_EMAILS` already revokes access through the other half of the
gate, and a surprise demotion would lock an operator out mid-session.

- This replaced a gap, not a design. The prose above described the gate correctly, but **nothing in the
  codebase could set `role = ADMIN`** — no route, no script, no seed — so an `ADMIN_EMAILS` entry on its
  own was inert and the review console was unreachable. The first real signup proved it: the row was
  created `USER`, which would have made **every paid report unapprovable**.
- If an existing row is ever stuck on `USER`, one sign-in heals it, or
  `UPDATE "User" SET role = 'ADMIN' WHERE email = '…'` does it directly.

## Sign-in surfaces

| Method | Provider | Notes |
|---|---|---|
| Google OAuth | Neon Auth → Google | Requires the Google Cloud OAuth client — see [07](07-services-and-integrations.md) §5 |
| Email + password | Neon Auth | Password rules are Neon's; we do not store hashes |
| Magic link | Neon Auth | Needs SMTP. Dev uses Neon's shared SMTP; production uses **Resend**. ⚠️ Neon sends this mail itself, so it **does not** inherit our `EMAIL_REPLY_TO` — a reply goes to whatever From address is configured in Neon. With the `reports@` alias now real that lands in the shared inbox rather than bouncing, but the From/Reply-To pair is Neon's to set, not ours |

The `/login` page is a single tabbed client component (`sign-in` / `sign-up`), not two routes:

```ts
await authClient.signIn.social({ provider: 'google', callbackURL, newUserCallbackURL, errorCallbackURL });
await authClient.signIn.email({ email, password });
await authClient.signUp.email({ email, password, name });
await authClient.signIn.magicLink({ email, callbackURL, newUserCallbackURL, errorCallbackURL });
```

Callback URLs are built from `window.location.origin` + `/auth/complete?next=…`, and `next` is
validated against an allowlist (a naive `next` parameter is an open-redirect).

Sign-up carries the **consent checkbox** for the privacy policy; accepting it writes a
`ConsentRecord` (see [10](10-privacy-and-compliance.md)).

Sign-out: `authClient.signOut()` → `router.push('/login')` → `router.refresh()`. The `refresh()` is
required or the server-rendered layout keeps showing the signed-in shell from cache.

## Neon Auth configuration (in the Neon console, not in code)

| Setting | Value for this project |
|---|---|
| Google provider | Enabled; client id/secret from Google Cloud |
| Authorised redirect URI (Google) | `{NEON_AUTH_BASE_URL}/callback/google` — **this exact string** |
| Trusted origins | `https://cosmicsaju.com`, `https://www.cosmicsaju.com` (**both**), `http://localhost:3000`, preview URL pattern |
| Email/password | Enabled |
| Magic link / email verification | Enabled; production SMTP = Resend. The From address here is Neon's setting, **not** `EMAIL_FROM` — check it if replies to sign-in mail matter ([07](07-services-and-integrations.md) §Mailbox records) |
| Sign-up | Open (Google + email) |

## Environment variables

| Variable | Notes |
|---|---|
| `NEON_AUTH_BASE_URL` | From the Neon console. **Includes the path** (`…/neondb/auth`) |
| `NEON_AUTH_COOKIE_SECRET` | `openssl rand -base64 32` — **≥ 32 chars or startup throws** |
| `ADMIN_EMAILS` | Comma-separated allowlist, second factor for admin |
| `NEXT_PUBLIC_APP_URL` | Absolute links in emails |

One value per environment: the Neon `dev` branch and the `main` branch each have their **own** Auth
base URL and therefore their own Google redirect URI. Register both.

## Failure modes and what they look like

| Symptom | Cause |
|---|---|
| `redirect_uri_mismatch` from Google | The redirect URI is not exactly `{NEON_AUTH_BASE_URL}/callback/google` for *this* branch's Auth URL |
| OAuth succeeds, user never lands | The origin is missing from **trusted origins** (remember `www` separately), or `/auth/complete` is not in the proxy matcher |
| "missing or invalid cookie secret" at startup | `NEON_AUTH_COOKIE_SECRET` unset or shorter than 32 chars |
| Build fails with an auth error in CI | Something constructs the auth client at module scope instead of behind the lazy Proxy |
| Signed-in user still sees the marketing header after sign-out | Missing `router.refresh()` |
| Page renders stale/empty user data | Missing `export const dynamic = 'force-dynamic'` on a Server Component that reads the session |

## Testing implications

The Playwright **public** tier asserts that every protected route returns
`401 {error, code:'UNAUTHORIZED'}` when signed out — including `/admin`, which additionally must
return 401 (not 403) so the admin surface is not discoverable. New protected routes must be added to
that spec in the same change. See [12 — Testing](12-testing.md).
