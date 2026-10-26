import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-40 (owner decision D6): "Sign out of other devices" on the account page.
 *
 * The route is the only writer: it takes the signed-in user from `requireUser()`, limits the action,
 * and delegates to the existing `revokeOtherSessions()` helper — the same wrapper the consent
 * withdrawal already uses, now reporting success so the panel can show an honest error.
 *
 * The current session surviving is a property of the provider's `revoke-all-sessions` endpoint
 * (Neon documents it as "revokes all sessions except the current one"), not something this route
 * re-implements; the test below proves the route passes no token and reports the list it gets back.
 */

const store = new Map<string, number>();
const upsert = vi.fn(
  async ({ where }: { where: { bucket_windowStart: { bucket: string; windowStart: Date } } }) => {
    const { bucket, windowStart } = where.bucket_windowStart;
    const key = `${bucket}|${new Date(windowStart).toISOString()}`;
    const count = (store.get(key) ?? 0) + 1;
    store.set(key, count);
    return { count };
  },
);

const { requireUser, revokeOtherSessions } = vi.hoisted(() => ({
  requireUser: vi.fn(),
  revokeOtherSessions: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({ requireUser, revokeOtherSessions }));
vi.mock("@/lib/prisma", () => ({ prisma: { rateLimit: { upsert } } }));

const { POST } = await import("@/app/api/account/sessions/route");

function post(): Request {
  return new Request("https://app.test/api/account/sessions", { method: "POST" });
}

beforeEach(() => {
  vi.clearAllMocks();
  store.clear();
  requireUser.mockResolvedValue({ id: "u1", name: "A", email: "a@b.c", role: "CLIENT" });
  revokeOtherSessions.mockResolvedValue(true);
});

describe("POST /api/account/sessions — revoke other devices", () => {
  it("calls the shared revoke helper with no arguments and answers only ok", async () => {
    const res = await POST(post(), undefined as never);

    expect(res.status).toBe(200);
    expect(revokeOtherSessions).toHaveBeenCalledTimes(1);
    expect(revokeOtherSessions).toHaveBeenCalledWith();

    // No session list: nothing reads it, and re-listing would cost a second provider round trip
    // (and return null for a caller whose session is not fresh).
    const body = (await res.json()) as Record<string, unknown>;
    expect(body).toEqual({ ok: true });
  });

  it("answers 503 with an actionable message when the provider refuses", async () => {
    revokeOtherSessions.mockResolvedValue(false);

    const res = await POST(post(), undefined as never);

    expect(res.status).toBe(503);
    const body = (await res.json()) as { error: string; code: string };
    expect(body.code).toBe("SESSION_REVOKE_FAILED");
    expect(body.error).toMatch(/try again/i);
  });

  it("answers 401 and touches nothing when there is no session", async () => {
    const { ApiError } = await import("@/lib/api");
    requireUser.mockRejectedValue(ApiError.unauthorized());

    const res = await POST(post(), undefined as never);

    expect(res.status).toBe(401);
    expect(revokeOtherSessions).not.toHaveBeenCalled();
  });

  it("returns 429 once the limit is exceeded, before the provider is called", async () => {
    const responses: Response[] = [];
    for (let i = 0; i < 6; i += 1) responses.push(await POST(post(), undefined as never));

    expect(responses.slice(0, 5).every((r) => r.status === 200)).toBe(true);
    const refused = responses[5]!;
    expect(refused.status).toBe(429);
    expect(((await refused.json()) as { code: string }).code).toBe("RATE_LIMITED");
    // Five real revocations, not six.
    expect(revokeOtherSessions).toHaveBeenCalledTimes(5);
  });
});
