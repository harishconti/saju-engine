import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-41 (owner decision D6): password reset without contacting support.
 *
 * Two thin server routes exist so both steps have somewhere for the rate limit to live and so the
 * browser never talks to the auth proxy directly for them:
 *
 *   POST /api/account/password-reset          — ask Neon Auth to mail a reset link
 *   POST /api/account/password-reset/confirm  — consume the token and set the new password
 *
 * Neutrality (AU-15's rule, applied to reset): the request route answers the **same** status and
 * the **same** body whether the address is registered or not. That is the whole anti-enumeration
 * property, so the test drives both cases and compares the bytes.
 *
 * The token is a credential. It is never logged, never echoed, and the invalid/expired answers are
 * identical so the response cannot be used to probe token state beyond "usable / not usable".
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

const { requestPasswordReset, resetPassword } = vi.hoisted(() => ({
  requestPasswordReset: vi.fn(),
  resetPassword: vi.fn(),
}));

vi.mock("@/lib/auth/server", () => ({ auth: { requestPasswordReset, resetPassword } }));
vi.mock("@/lib/prisma", () => ({ prisma: { rateLimit: { upsert } } }));

const { POST: requestReset } = await import("@/app/api/account/password-reset/route");
const { POST: confirmReset } = await import("@/app/api/account/password-reset/confirm/route");

const TOKEN = "tok_4f9a2c7b1e8d6f3a5c0b9e7d2a1f8c6b";

function jsonRequest(url: string, body: unknown, ip = "198.51.100.7"): Request {
  return new Request(url, {
    method: "POST",
    headers: { "content-type": "application/json", "x-real-ip": ip },
    body: JSON.stringify(body),
  });
}

function requestBody(email: string): Request {
  return jsonRequest("https://app.test/api/account/password-reset", { email });
}

function confirmBody(token = TOKEN, newPassword = "correct-horse-battery"): Request {
  return jsonRequest("https://app.test/api/account/password-reset/confirm", { token, newPassword });
}

/** Every console call's arguments, flattened to one searchable string. */
function logged(spy: { mock: { calls: unknown[][] } }): string {
  return spy.mock.calls.flat().map((arg) => (typeof arg === "string" ? arg : JSON.stringify(arg))).join(" ");
}

beforeEach(() => {
  vi.clearAllMocks();
  store.clear();
  vi.stubEnv("NEXT_PUBLIC_APP_URL", "https://cosmicsaju.com");
  requestPasswordReset.mockResolvedValue({
    data: { status: true, message: "If this email exists in our system, check your email for the reset link" },
    error: null,
  });
  resetPassword.mockResolvedValue({ data: { status: true }, error: null });
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.restoreAllMocks();
});

describe("POST /api/account/password-reset — the request step", () => {
  it("answers byte-for-byte the same for a known and an unknown address", async () => {
    const known = await requestReset(requestBody("member@example.com"), undefined as never);
    const knownText = await known.text();

    const unknown = await requestReset(requestBody("nobody@example.com"), undefined as never);
    const unknownText = await unknown.text();

    expect(unknown.status).toBe(known.status);
    expect(unknownText).toBe(knownText);
    expect(known.status).toBe(202);
    expect(JSON.parse(knownText)).toEqual({ ok: true });

    // The provider was asked in both cases; the route never inspects existence itself.
    expect(requestPasswordReset).toHaveBeenCalledTimes(2);
  });

  it("asks the provider for a link back to our reset page", async () => {
    await requestReset(requestBody("Member@Example.com "), undefined as never);

    expect(requestPasswordReset).toHaveBeenCalledWith({
      email: "member@example.com",
      redirectTo: "https://cosmicsaju.com/reset-password",
    });
  });

  it("stays neutral when the provider itself fails, and logs only the code", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    requestPasswordReset.mockResolvedValue({
      data: null,
      error: { status: 500, code: "INTERNAL_ERROR", message: "mail relay rejected member@example.com" },
    });

    const res = await requestReset(requestBody("member@example.com"), undefined as never);

    expect(res.status).toBe(202);
    expect(await res.json()).toEqual({ ok: true });
    expect(error).toHaveBeenCalled();
    expect(logged(error)).not.toContain("member@example.com");
    expect(logged(error)).not.toContain("mail relay rejected");
  });

  it("rejects a malformed address before spending a provider call", async () => {
    const res = await requestReset(requestBody("not-an-address"), undefined as never);

    expect(res.status).toBe(422);
    expect(requestPasswordReset).not.toHaveBeenCalled();
  });

  it("returns 429 once the per-IP limit is exceeded, before the provider is called", async () => {
    const responses: Response[] = [];
    for (let i = 0; i < 6; i += 1) {
      responses.push(await requestReset(requestBody(`visitor${i}@example.com`), undefined as never));
    }

    expect(responses.slice(0, 5).every((r) => r.status === 202)).toBe(true);
    expect(responses[5]!.status).toBe(429);
    expect(((await responses[5]!.json()) as { code: string }).code).toBe("RATE_LIMITED");
    expect(requestPasswordReset).toHaveBeenCalledTimes(5);
  });

  it("counts each client IP separately", async () => {
    for (let i = 0; i < 5; i += 1) {
      await requestReset(jsonRequest("https://app.test/api/account/password-reset", {
        email: `a${i}@example.com`,
      }, "203.0.113.4"), undefined as never);
    }

    const other = await requestReset(jsonRequest("https://app.test/api/account/password-reset", {
      email: "b@example.com",
    }, "203.0.113.5"), undefined as never);

    expect(other.status).toBe(202);
  });
});

describe("POST /api/account/password-reset/confirm — the reset step", () => {
  it("accepts a valid token and sets the new password", async () => {
    const res = await confirmReset(confirmBody(), undefined as never);

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true });
    expect(resetPassword).toHaveBeenCalledWith({ newPassword: "correct-horse-battery", token: TOKEN });
  });

  it("rejects an invalid or expired token with one indistinguishable answer", async () => {
    resetPassword.mockResolvedValue({
      data: null,
      error: { status: 400, code: "INVALID_TOKEN", message: "Invalid token" },
    });
    const invalid = await confirmReset(confirmBody("tok_invalid"), undefined as never);
    const invalidText = await invalid.text();

    resetPassword.mockResolvedValue({
      data: null,
      error: { status: 400, code: "INVALID_TOKEN", message: "Verification expired" },
    });
    const expired = await confirmReset(confirmBody("tok_expired"), undefined as never);
    const expiredText = await expired.text();

    expect(invalid.status).toBe(400);
    expect(expired.status).toBe(invalid.status);
    expect(expiredText).toBe(invalidText);
    expect(JSON.parse(invalidText).code).toBe("INVALID_RESET_TOKEN");
    expect(JSON.parse(invalidText).error).toMatch(/invalid or has expired/i);
  });

  it("maps a provider outage to 503, not to a claim that the token is bad", async () => {
    resetPassword.mockResolvedValue({
      data: null,
      error: { status: 503, code: "SERVICE_UNAVAILABLE", message: "upstream unavailable" },
    });

    const res = await confirmReset(confirmBody(), undefined as never);

    expect(res.status).toBe(503);
    expect(((await res.json()) as { code: string }).code).toBe("RESET_UNAVAILABLE");
  });

  it("does not tell the visitor to discard a working link when the provider is rate limiting", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    resetPassword.mockResolvedValue({
      data: null,
      error: { status: 429, code: "TOO_MANY_REQUESTS", message: "slow down" },
    });

    const res = await confirmReset(confirmBody(), undefined as never);

    expect(res.status).toBe(429);
    const body = (await res.json()) as { error: string; code: string };
    expect(body.code).toBe("RATE_LIMITED");
    expect(body.error).toMatch(/too many attempts/i);
    expect(body.error).not.toMatch(/invalid or has expired/i);
  });

  it("does not report a provider 403 as a bad token", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    resetPassword.mockResolvedValue({
      data: null,
      error: { status: 403, code: "FORBIDDEN", message: "request refused" },
    });

    const res = await confirmReset(confirmBody(), undefined as never);

    expect(res.status).toBe(503);
    const body = (await res.json()) as { error: string; code: string };
    expect(body.code).toBe("RESET_UNAVAILABLE");
    expect(body.error).not.toMatch(/invalid or has expired/i);
  });

  it("treats an unclassified provider failure as retryable, not as a bad token", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    resetPassword.mockResolvedValue({ data: null, error: { code: "NETWORK_ERROR" } });

    const res = await confirmReset(confirmBody(), undefined as never);

    expect(res.status).toBe(503);
    expect(error).toHaveBeenCalled();
  });

  it("answers 503 when the provider throws, and logs no token", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    resetPassword.mockRejectedValue(new Error(`upstream exploded for ${TOKEN}`));

    const res = await confirmReset(confirmBody(), undefined as never);

    expect(res.status).toBe(503);
    expect(logged(error)).not.toContain(TOKEN);
    expect(await res.text()).not.toContain(TOKEN);
  });

  it("never writes the token to a log line on any path", async () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const warns = vi.spyOn(console, "warn").mockImplementation(() => {});
    const logs = vi.spyOn(console, "log").mockImplementation(() => {});

    await confirmReset(confirmBody(), undefined as never);
    resetPassword.mockResolvedValue({
      data: null,
      error: { status: 400, code: "INVALID_TOKEN", message: "Invalid token" },
    });
    const rejected = await confirmReset(confirmBody(), undefined as never);

    expect(logged(errors)).not.toContain(TOKEN);
    expect(logged(warns)).not.toContain(TOKEN);
    expect(logged(logs)).not.toContain(TOKEN);
    expect(await rejected.text()).not.toContain(TOKEN);
  });

  it("rejects a too-short password before spending the one-time token", async () => {
    const res = await confirmReset(confirmBody(TOKEN, "short"), undefined as never);

    expect(res.status).toBe(422);
    expect(resetPassword).not.toHaveBeenCalled();
  });

  it("returns 429 once the per-IP limit is exceeded, before the token is spent", async () => {
    const responses: Response[] = [];
    for (let i = 0; i < 11; i += 1) responses.push(await confirmReset(confirmBody(), undefined as never));

    expect(responses.slice(0, 10).every((r) => r.status === 200)).toBe(true);
    expect(responses[10]!.status).toBe(429);
    expect(resetPassword).toHaveBeenCalledTimes(10);
  });
});
