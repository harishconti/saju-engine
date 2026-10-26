/**
 * Admin is a three-way gate (AU-07): `role = ADMIN` in the database, the address in ADMIN_EMAILS,
 * and a verified email in the *session*. Verification is deliberately not stored in Prisma — it is
 * read fresh on every request, so revoking it takes effect on the next page load.
 *
 * These tests drive the real `mirrorUser` path through `getCurrentUser`, with only the session and
 * the database faked, so the emailVerified plumbing from the Neon payload to `AppUser` is covered.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Prisma } from "@prisma/client";

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
  return {
    id: "u1",
    name: "Owner",
    email: ADMIN_EMAIL,
    role: "USER",
    deletedAt: null,
    lastSeenAt: null,
    // AU-24: `mirrorUser` selects pending deletions; empty means the account can sign in.
    deletions: [],
    ...overrides,
  };
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

/**
 * AU-17 (2026-10-26 audit): the account page's new display name was silently reverted.
 *
 * `mirrorUser` copied the Neon session's name onto the local row on *every* request, so a name
 * saved through `PATCH /api/account` survived only until the next page load. The local row is now
 * authoritative once it exists: the session's name is used to create the row, never to overwrite
 * it afterwards.
 */
describe("mirrorUser display name", () => {
  it("does not overwrite a name that was changed on the account page", async () => {
    prismaMock.user.findUnique.mockResolvedValue(storedRow({ name: "Chosen Name", email: USER_EMAIL }));
    signedIn({ email: USER_EMAIL, name: "Provider Name" });

    const user = await getCurrentUser();

    expect(user?.name).toBe("Chosen Name");
    expect(prismaMock.user.update).not.toHaveBeenCalled();
  });

  it("still syncs the email when the provider has a different one", async () => {
    prismaMock.user.findUnique.mockResolvedValue(storedRow({ name: "Chosen Name", email: "old@example.com" }));
    prismaMock.user.update.mockResolvedValue({
      id: "u1",
      name: "Chosen Name",
      email: USER_EMAIL,
      role: "USER",
    });
    signedIn({ email: USER_EMAIL });

    const user = await getCurrentUser();

    expect(user).toMatchObject({ name: "Chosen Name", email: USER_EMAIL });
    expect(prismaMock.user.update).toHaveBeenCalledWith(
      expect.objectContaining({ data: expect.not.objectContaining({ name: expect.anything() }) }),
    );
  });

  it("creates the row with the session's name on first sign-in", async () => {
    signedIn({ email: USER_EMAIL, name: "First Visit" });

    const user = await getCurrentUser();

    expect(user?.name).toBe("First Visit");
    expect(prismaMock.user.create).toHaveBeenCalledWith(
      expect.objectContaining({ data: expect.objectContaining({ name: "First Visit" }) }),
    );
  });
});

/**
 * AU-18 (2026-10-26 audit): a database outage made every signed-in visitor look signed out.
 *
 * The bare `catch {}` around the session read swallowed a Prisma connectivity failure and returned
 * `null`, which the UI rendered as "signed out" instead of "try again". A database error is now
 * re-thrown so the route layer answers 503; an unconfigured auth provider, a network failure or a
 * corrupt cookie is still a safe `null`.
 */
describe("getCurrentUser database failures", () => {
  it("propagates a Prisma connectivity error so the caller can answer 503", async () => {
    signedIn();
    prismaMock.user.findUnique.mockRejectedValue(
      new Prisma.PrismaClientKnownRequestError("Can't reach database server", {
        code: "P1001",
        clientVersion: "5.22.0",
      }),
    );

    await expect(getCurrentUser()).rejects.toMatchObject({ code: "P1001" });
  });

  it("propagates a Prisma initialization error", async () => {
    signedIn();
    prismaMock.user.findUnique.mockRejectedValue(
      new Prisma.PrismaClientInitializationError("Engine is not yet connected", "5.22.0", "P1001"),
    );

    await expect(getCurrentUser()).rejects.toBeInstanceOf(Prisma.PrismaClientInitializationError);
  });

  it("returns null when no session exists", async () => {
    getSession.mockResolvedValue({ data: null });

    await expect(getCurrentUser()).resolves.toBeNull();
  });

  it("still returns null when the auth provider is not configured", async () => {
    getSession.mockRejectedValue(new Error("Neon Auth is not configured: set NEON_AUTH_BASE_URL"));

    await expect(getCurrentUser()).resolves.toBeNull();
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
