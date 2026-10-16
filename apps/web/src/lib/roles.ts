/**
 * Role model. Mirrors the Prisma `Role` enum and the DB CHECK constraint — three places,
 * deliberately (docs/webapp/02-data-model.md).
 */
export const ROLES = ["USER", "ADMIN"] as const;
export type Role = (typeof ROLES)[number];

export const ROLE_RANK: Record<Role, number> = { USER: 1, ADMIN: 2 };

export function isRole(value: unknown): value is Role {
  return typeof value === "string" && (ROLES as readonly string[]).includes(value);
}

export function hasMinRole(role: Role, minRole: Role): boolean {
  return ROLE_RANK[role] >= ROLE_RANK[minRole];
}

/**
 * Admin is doubly gated: `role = ADMIN` in the database AND the account's email in ADMIN_EMAILS.
 * Two independent conditions, so a database compromise alone does not hand over the review console,
 * and revoking access does not require a data change.
 */
export function adminEmails(): string[] {
  return (process.env.ADMIN_EMAILS ?? "")
    .split(",")
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean);
}

export function isAdminEmail(email: string | null | undefined): boolean {
  if (!email) return false;
  return adminEmails().includes(email.toLowerCase());
}

/**
 * The role an account should hold, given its email. Grants ADMIN from the allowlist; never revokes
 * (see the reasoning in auth/index.ts). Pure, so the decision can be tested without a database.
 */
export function roleForEmail(email: string | null | undefined, current: Role): Role {
  return isAdminEmail(email) ? "ADMIN" : current;
}
