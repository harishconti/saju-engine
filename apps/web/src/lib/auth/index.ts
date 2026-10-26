import { cache } from "react";
import { Prisma } from "@prisma/client";
import { prisma } from "@/lib/prisma";
import { ApiError } from "@/lib/api";
import { hasMinRole, isAdminEmail, type Role } from "@/lib/roles";
import { auth } from "./server";

/**
 * User mirroring + guards.
 *
 * Neon Auth owns identity (credentials, sessions, OAuth). Our `User` row is where roles, consent,
 * and relations hang, and is keyed by the Neon Auth user id.
 *
 * Contract: docs/webapp/04-auth-and-roles.md
 */

export interface AppUser {
  id: string;
  name: string;
  email: string;
  role: Role;
  /**
   * Read from the Neon session on every request and never persisted (AU-07). Prisma stores the
   * role, but the admin gate additionally needs a verified address, so revoking verification
   * takes effect on the next request instead of leaving a stale flag in the database.
   */
  emailVerified: boolean;
}

interface NeonUser {
  id?: string | null;
  email?: string | null;
  name?: string | null;
  emailVerified?: boolean | null;
}

function normalise(u: NeonUser): { id: string; email: string; name: string; emailVerified: boolean } | null {
  if (!u?.id) return null;
  const email = (u.email ?? `${u.id}@neon-auth.local`).toLowerCase();
  const name = u.name?.trim() || email.split("@")[0] || "Friend";
  return { id: u.id, email, name, emailVerified: u.emailVerified === true };
}

function isUniqueViolation(err: unknown): boolean {
  return err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002";
}

/**
 * A database failure, as opposed to an identity one.
 *
 * AU-18: a Prisma outage inside `mirrorUser` used to be swallowed by the same `catch` that handles
 * "no session", so a signed-in visitor was shown the signed-out page during the October outage.
 * These errors must reach the route layer, which maps them to a retryable 503.
 */
function isDatabaseError(err: unknown): boolean {
  return (
    err instanceof Prisma.PrismaClientKnownRequestError || err instanceof Prisma.PrismaClientInitializationError
  );
}

/** The sign-in signal is written at most once per this window (owner decision D9). */
const LAST_SEEN_THROTTLE_MS = 24 * 60 * 60 * 1000;

/**
 * Record that an account was used (owner decision D9).
 *
 * Retention measures "inactivity" as 24 months without use, and nothing else writes a timestamp
 * when an account is merely read: `Profile.updatedAt` moves only when the profile itself changes, and
 * mirrored users return unchanged. This is that timestamp, written from the `getCurrentUser` path at
 * most once every 24 hours.
 *
 * Three rules:
 *  - the in-memory check keeps the common case at zero writes;
 *  - the `updateMany` re-checks the stored value as well as the id, so two concurrent requests
 *    cannot both write it;
 *  - a failure is logged and swallowed — bookkeeping must never turn a valid session into a 500 or a
 *    signed-out page.
 */
async function touchLastSeen(userId: string, lastSeenAt: Date | null): Promise<void> {
  const now = new Date();
  if (lastSeenAt && now.getTime() - lastSeenAt.getTime() < LAST_SEEN_THROTTLE_MS) return;
  const staleBefore = new Date(now.getTime() - LAST_SEEN_THROTTLE_MS);
  try {
    await prisma.user.updateMany({
      where: { id: userId, OR: [{ lastSeenAt: null }, { lastSeenAt: { lt: staleBefore } }] },
      data: { lastSeenAt: now },
    });
  } catch (err) {
    console.error("[auth] lastSeenAt write failed:", err instanceof Error ? err.name : "unknown");
  }
}

/** Upsert the local mirror. The first-sign-in race (P2002) is handled, not fatal. */
async function mirrorUser(u: NeonUser): Promise<AppUser | null> {
  const n = normalise(u);
  if (!n) return null;

  const existing = await prisma.user.findUnique({
    where: { id: n.id },
    select: {
      id: true,
      name: true,
      email: true,
      role: true,
      deletedAt: true,
      lastSeenAt: true,
      // AU-24 (D7): a pending deletion disables sign-in. Only `pending` blocks — a cancelled or
      // completed request must not (Task 4 / D2).
      deletions: { where: { status: "pending" }, take: 1, select: { id: true } },
    },
  });

  // Admin is derived here because nothing else can grant it: there is no route, script or CLI that
  // sets `role = ADMIN`. Both halves of the gate are required — the address on ADMIN_EMAILS *and*
  // a verified email in the live session (AU-07) — because anyone can sign up with an allowlisted
  // address before the operator does. An unverified allowlisted sign-in grants nothing and is
  // logged, since it is either the operator's own first sign-in or an attempt to claim the console.
  //
  // Deliberately never *demotes*: dropping an address from `ADMIN_EMAILS` (or losing verification)
  // already revokes access through the other halves of the gate, and a surprise demotion would lock
  // an operator out mid-session.
  const allowlisted = isAdminEmail(n.email);
  const grantAdmin = allowlisted && n.emailVerified;
  if (allowlisted && !n.emailVerified) {
    console.warn(
      `[auth] unverified admin address ${n.email} — admin access withheld until the address is verified`,
    );
  }

  if (existing) {
    if (existing.deletedAt) return null; // anonymised account: treat as signed out
    // AU-24 (D7): the account is scheduled for deletion, so it cannot sign in. Checked before
    // `touchLastSeen` on purpose: a blocked account must not be recorded as "in use", or the
    // retention sweep would count a session it just refused as activity.
    if (existing.deletions.length > 0) return null;
    const needsRole = grantAdmin && existing.role !== "ADMIN";
    // AU-17: the local row is authoritative for the display name once it exists. Copying the
    // Neon session's name here reverted every change made on the account page, because that page
    // saves to this row and the next request overwrote it. The session name seeds a new row only.
    if (!needsRole && existing.email === n.email) {
      await touchLastSeen(existing.id, existing.lastSeenAt);
      return {
        id: existing.id,
        name: existing.name,
        email: existing.email,
        role: existing.role as Role,
        emailVerified: n.emailVerified,
      };
    }
    const updated = await prisma.user.update({
      where: { id: n.id },
      data: { email: n.email, ...(needsRole ? { role: "ADMIN" as const } : {}) },
      select: { id: true, name: true, email: true, role: true },
    });
    await touchLastSeen(existing.id, existing.lastSeenAt);
    return { ...updated, role: updated.role as Role, emailVerified: n.emailVerified };
  }

  try {
    const created = await prisma.user.create({
      data: {
        id: n.id,
        name: n.name,
        email: n.email,
        // A first sign-in is activity: seeding it here keeps the new account out of the sweep's
        // candidate set from day one, without waiting for the first throttled write.
        lastSeenAt: new Date(),
        ...(grantAdmin ? { role: "ADMIN" as const } : {}),
      },
      select: { id: true, name: true, email: true, role: true },
    });
    return { ...created, role: created.role as Role, emailVerified: n.emailVerified };
  } catch (err) {
    if (!isUniqueViolation(err)) throw err;
    // Lost the race: another request created it. Re-read.
    const row = await prisma.user.findUnique({
      where: { id: n.id },
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        deletedAt: true,
        lastSeenAt: true,
        deletions: { where: { status: "pending" }, take: 1, select: { id: true } },
      },
    });
    if (!row || row.deletedAt || row.deletions.length > 0) return null;
    await touchLastSeen(row.id, row.lastSeenAt);
    return { id: row.id, name: row.name, email: row.email, role: row.role as Role, emailVerified: n.emailVerified };
  }
}

/**
 * The signed-in user, mirrored locally, or null. Cached per request with React `cache()`.
 *
 * Never throws on a missing session — callers decide. `requireUser()` is the throwing variant.
 */
export const getCurrentUser = cache(async (): Promise<AppUser | null> => {
  try {
    const res = (await auth.getSession()) as unknown as {
      data?: { user?: NeonUser } | null;
      error?: unknown;
    };
    if (res?.error) return null;
    return mirrorUser(res?.data?.user ?? {});
  } catch (err) {
    // Unconfigured auth, network failure, or a corrupt cookie: treat as signed out rather than 500.
    // AU-18: a database error is not "signed out" — re-throw it so the caller answers 503.
    if (isDatabaseError(err)) throw err;
    return null;
  }
});

/** Like getCurrentUser but throws 401 when unauthenticated. */
export async function requireUser(): Promise<AppUser> {
  const user = await getCurrentUser();
  if (!user) throw ApiError.unauthorized();
  return user;
}

/**
 * The raw Neon session user id, without mirroring and without the pending-deletion gate.
 *
 * AU-24 (D7) needs this for the one honest exception to the sign-in block: an account that is
 * *pending* deletion must still be able to read and cancel that request, which is how the privacy
 * page's "cancellable any time before it completes" survives sign-in being disabled. Callers must
 * never treat this as authentication — `getCurrentUser`/`requireUser` remain the only identity gates.
 */
export const getSessionUserId = cache(async (): Promise<string | null> => {
  try {
    const res = (await auth.getSession()) as unknown as {
      data?: { user?: { id?: string | null } } | null;
      error?: unknown;
    };
    if (res?.error) return null;
    return res?.data?.user?.id ?? null;
  } catch {
    // Unconfigured auth, network failure, corrupt cookie: no usable session.
    return null;
  }
});

/** Whether the account has a `pending` deletion request (AU-24, D7). */
export async function hasPendingDeletion(userId: string): Promise<boolean> {
  const pending = await prisma.deletionRequest.findFirst({
    where: { userId, status: "pending" },
    select: { id: true },
  });
  return pending !== null;
}

/**
 * End the caller's other sessions (AU-24 D7; reused by the account page in AU-40 D6).
 *
 * Withdrawing consent stops new processing, but the consent record does not end sessions already
 * open on other devices. The account page offers the same action explicitly. The current session is
 * kept — Neon's `revoke-all-sessions` endpoint is documented as "revokes all sessions except the
 * current one" — so the visitor stays on the page they are standing on. No token is passed, and none
 * could be: only the provider knows which session made the call.
 *
 * Never throws: this crosses into the identity provider, and a failure there must not turn a
 * recorded withdrawal into a 500. It reports whether the call succeeded so a caller that *is* just a
 * button can show an error (AU-40); callers that only need best effort ignore the value. The failure
 * is logged by class/code only (never a message, a token or a cookie).
 */
export async function revokeOtherSessions(): Promise<boolean> {
  try {
    const res = (await auth.revokeOtherSessions()) as { error?: { code?: string } } | undefined;
    if (res?.error) {
      // The code, never the message: a provider message can echo the request it refused.
      console.error("[auth] revokeOtherSessions failed:", res.error.code ?? "provider error");
      return false;
    }
    return true;
  } catch (err) {
    console.error("[auth] revokeOtherSessions failed:", err instanceof Error ? err.name : "unknown");
    return false;
  }
}

/** A signed-in device, as the account page needs it — and no more (AU-40, D6). */
export interface AccountSession {
  id: string;
  /** Raw user-agent; the page turns it into a short device name. */
  userAgent: string | null;
  /** When this device first signed in. */
  createdAt: string | null;
  /** The provider's `updatedAt`, which moves as the session is used. */
  lastUsedAt: string | null;
  /** True for the session making the request. */
  current: boolean;
}

interface NeonSessionRow {
  id?: string | null;
  userAgent?: string | null;
  createdAt?: string | Date | null;
  updatedAt?: string | Date | null;
}

function isoOrNull(value: string | Date | null | undefined): string | null {
  if (!value) return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

/**
 * The id of the session making this request, or null.
 *
 * AU-40: marking "this device" is only honest if both sides expose an id. They do — `getSession()`
 * returns `data.session.id` and every `list-sessions` row carries the same `id` — so no approximation
 * is needed. A missing id simply means no marker, never a guess.
 */
export const getCurrentSessionId = cache(async (): Promise<string | null> => {
  try {
    const res = (await auth.getSession()) as unknown as {
      data?: { session?: { id?: string | null } | null } | null;
      error?: unknown;
    };
    if (res?.error) return null;
    const id = res?.data?.session?.id;
    return typeof id === "string" && id.length > 0 ? id : null;
  } catch {
    // Unconfigured auth, network failure, corrupt cookie: no usable session id.
    return null;
  }
});

/**
 * Every active session for the signed-in user, current first (AU-40, D6).
 *
 * Answers null when the provider could not be reached, refused, or answered with something that is
 * not a session array, so the page can say "couldn't load" rather than pretend the account has no
 * other devices. `[]` is reserved for a provider-confirmed empty list. Only the fields the page
 * shows are copied out: the provider's rows also carry a session **token**, which must never reach
 * the browser.
 *
 * The provider gates this endpoint on the session's *creation* age, not its last use
 * (`freshSessionMiddleware` in better-auth: `node_modules/better-auth/dist/api/routes/session.mjs`
 * `:337-341,:347-350`, default `freshAge` 24 h from `context/create-context.mjs:149`). A returning
 * user who is still active therefore gets a 403 `SESSION_NOT_FRESH` here, which is one reason the
 * account page must not tie the revoke control to this list: `revoke-other-sessions` uses
 * `sensitiveSessionMiddleware` (`:304-311,:450-453`) and does not apply the freshness comparison at
 * all.
 *
 * Logs by code/class only — a provider message can echo the request it refused. An uninterpretable
 * payload is logged the same way, without its contents.
 */
export async function listAccountSessions(): Promise<AccountSession[] | null> {
  let rows: NeonSessionRow[];
  try {
    const res = (await auth.listSessions()) as unknown as {
      data?: NeonSessionRow[] | null;
      error?: { code?: unknown } | null;
    };
    if (res?.error) {
      console.error(
        "[auth] listSessions failed:",
        typeof res.error.code === "string" ? res.error.code : "provider error",
      );
      return null;
    }
    // A success payload we cannot interpret is not evidence of an empty account.
    if (!Array.isArray(res?.data)) {
      console.error("[auth] listSessions failed:", "unexpected payload");
      return null;
    }
    rows = res.data;
  } catch (err) {
    console.error("[auth] listSessions failed:", err instanceof Error ? err.name : "unknown");
    return null;
  }

  const currentId = await getCurrentSessionId();

  return rows
    .filter((row): row is NeonSessionRow & { id: string } => typeof row?.id === "string" && row.id.length > 0)
    .map((row) => ({
      id: row.id,
      userAgent: typeof row.userAgent === "string" && row.userAgent.trim() ? row.userAgent : null,
      createdAt: isoOrNull(row.createdAt),
      lastUsedAt: isoOrNull(row.updatedAt),
      current: row.id === currentId,
    }))
    .sort((a, b) => {
      if (a.current !== b.current) return a.current ? -1 : 1;
      return (b.lastUsedAt ?? "").localeCompare(a.lastUsedAt ?? "");
    });
}

/** Roles are always read fresh from the database — never trusted from a token. */
export async function requireRole(minRole: Role): Promise<AppUser> {
  const user = await requireUser();
  if (!hasMinRole(user.role, minRole)) throw ApiError.forbidden();
  return user;
}

/**
 * Admin = `role === 'ADMIN'` in the database **AND** the email present in ADMIN_EMAILS **AND** a
 * verified email in the live session. Three independent conditions (AU-07;
 * docs/webapp/04-auth-and-roles.md).
 *
 * Throws 401 (not 403) when unauthenticated so the admin surface is not discoverable; a signed-in
 * caller who fails any condition gets 403.
 */
export async function requireAdmin(): Promise<AppUser> {
  const user = await requireUser();
  if (user.role !== "ADMIN" || !isAdminEmail(user.email) || !user.emailVerified) {
    throw ApiError.forbidden();
  }
  return user;
}
