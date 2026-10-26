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

/** Upsert the local mirror. The first-sign-in race (P2002) is handled, not fatal. */
async function mirrorUser(u: NeonUser): Promise<AppUser | null> {
  const n = normalise(u);
  if (!n) return null;

  const existing = await prisma.user.findUnique({
    where: { id: n.id },
    select: { id: true, name: true, email: true, role: true, deletedAt: true },
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
    if (!needsRole && existing.name === n.name && existing.email === n.email) {
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
      data: { name: n.name, email: n.email, ...(needsRole ? { role: "ADMIN" as const } : {}) },
      select: { id: true, name: true, email: true, role: true },
    });
    return { ...updated, role: updated.role as Role, emailVerified: n.emailVerified };
  }

  try {
    const created = await prisma.user.create({
      data: { id: n.id, name: n.name, email: n.email, ...(grantAdmin ? { role: "ADMIN" as const } : {}) },
      select: { id: true, name: true, email: true, role: true },
    });
    return { ...created, role: created.role as Role, emailVerified: n.emailVerified };
  } catch (err) {
    if (!isUniqueViolation(err)) throw err;
    // Lost the race: another request created it. Re-read.
    const row = await prisma.user.findUnique({
      where: { id: n.id },
      select: { id: true, name: true, email: true, role: true, deletedAt: true },
    });
    if (!row || row.deletedAt) return null;
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
  } catch {
    // Unconfigured auth, network failure, or a corrupt cookie: treat as signed out rather than 500.
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
