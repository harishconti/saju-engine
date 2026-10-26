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
    select: { id: true, name: true, email: true, role: true, deletedAt: true, lastSeenAt: true },
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
      select: { id: true, name: true, email: true, role: true, deletedAt: true, lastSeenAt: true },
    });
    if (!row || row.deletedAt) return null;
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
