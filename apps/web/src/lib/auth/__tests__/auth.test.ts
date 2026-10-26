/**
 * Admin is a three-way gate (AU-07): `role = ADMIN` in the database, the address in ADMIN_EMAILS,
 * and a verified email in the *session*. Verification is deliberately not stored in Prisma — it is
 * read fresh on every request, so revoking it takes effect on the next page load.
 *
 * These tests drive the real `mirrorUser` path through `getCurrentUser`, with only the session and
 * the database faked, so the emailVerified plumbing from the Neon payload to `AppUser` is covered.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { getSession, prismaMock, warn } = vi.hoisted(() => ({
  getSession: vi.fn(),
  prismaMock: {
    user: { findUnique: vi.fn(), update: vi.fn(), create: vi.fn() },
  },
  warn: vi.fn(),
}));

vi.mock("../server", () => ({ auth: { getSession } }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));

import { ApiError } from "@/lib/api";
import { getCurrentUser, requireAdmin } from "../index";

const ADMIN_EMAIL = "owner@cosmicsaju.com";
const USER_EMAIL = "visitor@example.com";

function signedIn(overrides: Record<string, unknown> = {}) {
  getSession.mockResolvedValue({
    data: { user: { id: "u1", email: ADMIN_EMAIL, name: "Owner", emailVerified: true, ...overrides } },
  });
}

/** Mirror the columns `mirrorUser` selects, so a stubbed row looks like a real one. */
function storedRow(overrides: Record<string, unknown> = {}) {
  return { id: "u1", name: "Owner", email: ADMIN_EMAIL, role: "USER", deletedAt: null, ...overrides };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubEnv("ADMIN_EMAILS", ADMIN_EMAIL);
  vi.spyOn(console, "warn").mockImplementation(warn);
  prismaMock.user.findUnique.mockResolvedValue(null);
  prismaMock.user.create.mockImplementation(({ data }: any) => ({
    id: data.id,
    name: data.name,
    email: data.email,
    role: data.role ?? "USER",
  }));
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

describe("mirrorUser admin grant", () => {
  it("grants ADMIN to a verified allowlisted address", async () => {
    signedIn();

    const user = await getCurrentUser();

    expect(user).toMatchObject({ email: ADMIN_EMAIL, role: "ADMIN", emailVerified: true });
    expect(prismaMock.user.create).toHaveBeenCalledWith(
      expect.objectContaining({ data: expect.objectContaining({ role: "ADMIN" }) }),
    );
    expect(warn).not.toHaveBeenCalled();
  });

  it("mirrors an unverified allowlisted address as USER and warns once", async () => {
    signedIn({ emailVerified: false });

    const user = await getCurrentUser();

    expect(user).toMatchObject({ email: ADMIN_EMAIL, role: "USER", emailVerified: false });
    expect(prismaMock.user.create).toHaveBeenCalledTimes(1);
    expect((prismaMock.user.create.mock.calls[0][0] as any).data.role).toBeUndefined();
    expect(warn).toHaveBeenCalledTimes(1);
    const line = warn.mock.calls[0].map(String).join(" ");
    expect(line).toContain(ADMIN_EMAIL);
    expect(line).toContain("unverified admin address");
  });

  it("defaults emailVerified to false when the session omits it", async () => {
    signedIn({ emailVerified: undefined });

    const user = await getCurrentUser();

    expect(user?.emailVerified).toBe(false);
    expect(user?.role).toBe("USER");
  });

  it("does not downgrade a stored ADMIN role when the session is unverified", async () => {
    prismaMock.user.findUnique.mockResolvedValue(storedRow({ role: "ADMIN" }));
    signedIn({ emailVerified: false });

    const user = await getCurrentUser();

    expect(user).toMatchObject({ role: "ADMIN", emailVerified: false });
    expect(prismaMock.user.update).not.toHaveBeenCalled();
  });
});

describe("requireAdmin", () => {
  it("rejects an allowlisted admin whose session is unverified", async () => {
    prismaMock.user.findUnique.mockResolvedValue(storedRow({ role: "ADMIN" }));
    signedIn({ emailVerified: false });

    const error = await requireAdmin().catch((err) => err);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 403, code: "FORBIDDEN" });
  });

  it("accepts a verified admin", async () => {
    prismaMock.user.findUnique.mockResolvedValue(storedRow({ role: "ADMIN" }));
    signedIn();

    await expect(requireAdmin()).resolves.toMatchObject({ role: "ADMIN", emailVerified: true });
  });

  it("rejects an ADMIN role whose address is no longer allowlisted", async () => {
    prismaMock.user.findUnique.mockResolvedValue(storedRow({ name: "Visitor", email: USER_EMAIL, role: "ADMIN" }));
    signedIn({ email: USER_EMAIL, name: "Visitor", emailVerified: true });

    await expect(requireAdmin()).rejects.toMatchObject({ status: 403, code: "FORBIDDEN" });
  });

  it("still answers 401 when signed out, so the admin surface stays undiscoverable", async () => {
    getSession.mockResolvedValue({ data: null });

    await expect(requireAdmin()).rejects.toMatchObject({ status: 401, code: "UNAUTHORIZED" });
  });
});
