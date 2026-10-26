import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-40 / owner decision D6 (2026-10-26 audit): the account page needs to show where the user is
 * signed in and let them end every other session.
 *
 * `list-sessions` is part of the installed SDK (`@neondatabase/auth` 0.6.0-beta); the wrapper here
 * maps the provider's session rows to a small DTO so the browser never receives a session token.
 * `getSession()` and every `list-sessions` entry expose an `id`, which is what makes an honest
 * "this device" marker possible instead of a guess.
 */

const { prismaMock, getSession, listSessions, authRevokeOtherSessions } = vi.hoisted(() => {
  const prismaMock = {
    user: {
      findUnique: vi.fn(async (_args: Record<string, unknown>) => null),
      update: vi.fn(async (_args: Record<string, unknown>) => ({})),
      create: vi.fn(async (_args: Record<string, unknown>) => ({})),
      updateMany: vi.fn(async (_args: Record<string, unknown>) => ({ count: 0 })),
    },
  };
  return {
    prismaMock,
    getSession: vi.fn(),
    listSessions: vi.fn(),
    authRevokeOtherSessions: vi.fn(),
  };
});

// `cache()` needs a React request scope a unit test does not have; identity is what matters.
vi.mock("react", () => ({ cache: (fn: unknown) => fn }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/auth/server", () => ({
  auth: {
    getSession,
    listSessions,
    revokeOtherSessions: authRevokeOtherSessions,
  },
}));

const { getCurrentSessionId, listAccountSessions, revokeOtherSessions } = await import("../auth");

const SESSION_WITH_ID = {
  data: {
    session: { id: "sess-current" },
    user: { id: "u1", email: "a@b.c", name: "A", emailVerified: true },
  },
};

function providerSession(overrides: Record<string, unknown> = {}) {
  return {
    id: "sess-current",
    token: "provider-session-token-should-never-leave-the-server",
    userId: "u1",
    userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130.0 Safari/537.36",
    ipAddress: "203.0.113.9",
    createdAt: new Date("2026-10-01T10:00:00.000Z"),
    updatedAt: new Date("2026-10-20T11:30:00.000Z"),
    expiresAt: new Date("2026-11-01T10:00:00.000Z"),
    ...overrides,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.clearAllMocks();
  getSession.mockResolvedValue(SESSION_WITH_ID);
  listSessions.mockResolvedValue({ data: [providerSession()], error: null });
  authRevokeOtherSessions.mockResolvedValue({ data: { status: true }, error: null });
});

describe("getCurrentSessionId", () => {
  it("reads the id from the live session", async () => {
    await expect(getCurrentSessionId()).resolves.toBe("sess-current");
  });

  it("answers null when there is no session, rather than throwing", async () => {
    getSession.mockResolvedValue({ data: { session: null, user: null }, error: null });
    await expect(getCurrentSessionId()).resolves.toBeNull();
  });

  it("answers null when the provider fails", async () => {
    getSession.mockRejectedValue(new Error("provider down"));
    await expect(getCurrentSessionId()).resolves.toBeNull();
  });
});

describe("listAccountSessions", () => {
  it("marks the session whose id matches the live session", async () => {
    listSessions.mockResolvedValue({
      data: [providerSession(), providerSession({ id: "sess-other", userAgent: "curl/8.0" })],
      error: null,
    });

    const sessions = await listAccountSessions();

    expect(sessions).toHaveLength(2);
    expect(sessions?.find((s) => s.id === "sess-current")?.current).toBe(true);
    expect(sessions?.find((s) => s.id === "sess-other")?.current).toBe(false);
  });

  it("never exposes the provider's session token or IP address", async () => {
    const sessions = await listAccountSessions();
    const serialised = JSON.stringify(sessions);

    expect(sessions?.[0]).not.toHaveProperty("token");
    expect(sessions?.[0]).not.toHaveProperty("ipAddress");
    expect(serialised).not.toContain("provider-session-token-should-never-leave-the-server");
    expect(serialised).not.toContain("203.0.113.9");
  });

  it("answers ISO timestamps for last-used and sign-in time", async () => {
    const [session] = (await listAccountSessions()) ?? [];

    expect(session).toMatchObject({
      id: "sess-current",
      lastUsedAt: "2026-10-20T11:30:00.000Z",
      createdAt: "2026-10-01T10:00:00.000Z",
    });
  });

  it("puts the current session first, then most recently used", async () => {
    listSessions.mockResolvedValue({
      data: [
        providerSession({ id: "old", updatedAt: new Date("2026-10-02T00:00:00.000Z") }),
        providerSession({ id: "sess-current", updatedAt: new Date("2026-10-01T00:00:00.000Z") }),
        providerSession({ id: "new", updatedAt: new Date("2026-10-25T00:00:00.000Z") }),
      ],
      error: null,
    });

    const ids = (await listAccountSessions())?.map((s) => s.id);
    expect(ids).toEqual(["sess-current", "new", "old"]);
  });

  it("omits rows the provider returns without a usable id", async () => {
    listSessions.mockResolvedValue({
      data: [providerSession({ id: null }), providerSession({ id: "sess-other" })],
      error: null,
    });

    const sessions = await listAccountSessions();
    expect(sessions?.map((s) => s.id)).toEqual(["sess-other"]);
  });

  it("answers null when the provider succeeds without an array", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    // A payload we cannot interpret is not "no other devices" — saying so would assert something
    // the provider never told us. Keep the null/[] split: null = unknown, [] = none.
    listSessions.mockResolvedValue({ data: { rows: [] }, error: null });

    await expect(listAccountSessions()).resolves.toBeNull();
    expect(error).toHaveBeenCalled();
  });

  it("answers null and logs only the failure class when the provider refuses", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    listSessions.mockResolvedValue({
      data: null,
      error: { code: "SESSION_NOT_FRESH", message: "provider message can echo request details" },
    });

    await expect(listAccountSessions()).resolves.toBeNull();

    expect(error).toHaveBeenCalled();
    expect(String(error.mock.calls[0]?.[1])).not.toContain("provider message");
    expect(String(error.mock.calls[0]?.[1])).toContain("SESSION_NOT_FRESH");
  });

  it("answers null when the provider throws", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    listSessions.mockRejectedValue(new Error("network down"));

    await expect(listAccountSessions()).resolves.toBeNull();
    expect(error).toHaveBeenCalled();
  });
});

describe("revokeOtherSessions now reports success (AU-40)", () => {
  it("resolves true and calls the provider with no arguments — the current session is kept by design", async () => {
    await expect(revokeOtherSessions()).resolves.toBe(true);

    // No token is passed: Neon's `revoke-other-sessions` ends every session *except* the caller's.
    expect(authRevokeOtherSessions).toHaveBeenCalledTimes(1);
    expect(authRevokeOtherSessions).toHaveBeenCalledWith();
  });

  it("resolves false — without throwing — when the provider returns an error", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    authRevokeOtherSessions.mockResolvedValue({
      error: { code: "UNAUTHORIZED", message: "provider message can echo request details" },
    });

    await expect(revokeOtherSessions()).resolves.toBe(false);

    expect(error).toHaveBeenCalled();
    expect(String(error.mock.calls[0]?.[1])).not.toContain("provider message");
  });

  it("resolves false — without throwing — when the provider call throws", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    authRevokeOtherSessions.mockRejectedValue(new Error("network down"));

    await expect(revokeOtherSessions()).resolves.toBe(false);
    expect(error).toHaveBeenCalled();
  });
});
