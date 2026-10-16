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
}

interface NeonUser {
  id?: string | null;
  email?: string | null;
  name?: string | null;
}

function normalise(u: NeonUser): { id: string; email: string; name: string } | null {
  if (!u?.id) return null;
  const email = (u.email ?? `${u.id}@neon-auth.local`).toLowerCase();
  const name = u.name?.trim() || email.split("@")[0] || "Friend";
  return { id: u.id, email, name };
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

  if (existing) {
    if (existing.deletedAt) return null; // anonymised account: treat as signed out
    if (existing.name === n.name && existing.email === n.email) {
      return { id: existing.id, name: existing.name, email: existing.email, role: existing.role as Role };
    }
    const updated = await prisma.user.update({
      where: { id: n.id },
      data: { name: n.name, email: n.email },
      select: { id: true, name: true, email: true, role: true },
    });
    return { ...updated, role: updated.role as Role };
  }

  try {
    const created = await prisma.user.create({
      data: { id: n.id, name: n.name, email: n.email },
      select: { id: true, name: true, email: true, role: true },
    });
    return { ...created, role: created.role as Role };
  } catch (err) {
    if (!isUniqueViolation(err)) throw err;
    // Lost the race: another request created it. Re-read.
    const row = await prisma.user.findUnique({
      where: { id: n.id },
      select: { id: true, name: true, email: true, role: true, deletedAt: true },
    });
    if (!row || row.deletedAt) return null;
    return { id: row.id, name: row.name, email: row.email, role: row.role as Role };
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
 * Admin = `role === 'ADMIN'` in the database **AND** the email present in ADMIN_EMAILS.
 * Two independent conditions (docs/webapp/04-auth-and-roles.md).
 *
 * Throws 401 (not 403) when unauthenticated so the admin surface is not discoverable.
 */
export async function requireAdmin(): Promise<AppUser> {
  const user = await requireUser();
  if (user.role !== "ADMIN" || !isAdminEmail(user.email)) {
    throw ApiError.unauthorized("Not available");
  }
  return user;
}
