import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { isTurnstileConfigured, turnstileMode, verifyTurnstile } from "../turnstile";

/**
 * Turnstile is the only thing standing between a script and our report engine, so the failure
 * directions matter more than the happy path:
 *
 *   * configured + bad token  → **refuse** (never accept)
 *   * configured + no secret  → should be impossible; treated as unconfigured
 *   * not configured          → **skip** (or local development cannot run at all)
 *   * Cloudflare unreachable  → **refuse**, never 500 and never allow
 *
 * The module reads env at call time and does not touch Prisma, hence no DATABASE_URL dance here.
 */

function stubSiteverify(response: { ok?: boolean; status?: number; body?: unknown }) {
  const calls: Array<{ url: string; body: URLSearchParams }> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: { body: URLSearchParams }) => {
      calls.push({ url, body: init.body });
      return new Response(JSON.stringify(response.body ?? { success: true }), {
        status: response.status ?? 200,
        headers: { "content-type": "application/json" },
      });
    }),
  );
  return calls;
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("rollout mode", () => {
  it("defaults to off — the safe state, so a fresh deploy cannot block anyone", () => {
    vi.stubEnv("TURNSTILE_MODE", "");
    expect(turnstileMode()).toBe("off");
  });

  it("reads log and enforce, case-insensitively", () => {
    vi.stubEnv("TURNSTILE_MODE", "log");
    expect(turnstileMode()).toBe("log");
    vi.stubEnv("TURNSTILE_MODE", "ENFORCE");
    expect(turnstileMode()).toBe("enforce");
  });

  it("treats an unrecognised value as off rather than guessing at enforcement", () => {
    vi.stubEnv("TURNSTILE_MODE", "yes-please");
    expect(turnstileMode()).toBe("off");
  });

  it("leaves `log` non-blocking by contract: it must never be the reason a visitor is refused", () => {
    // The route only throws when the mode is `enforce`. This pins the invariant that makes
    // validating a new widget safe: an unrendered widget produces no token, and log mode must
    // still let the visitor through.
    vi.stubEnv("TURNSTILE_MODE", "log");
    expect(turnstileMode()).not.toBe("enforce");
  });
});

describe("when Turnstile is not configured", () => {
  beforeEach(() => vi.stubEnv("TURNSTILE_SECRET_KEY", ""));

  it("reports itself as unconfigured", () => {
    expect(isTurnstileConfigured()).toBe(false);
  });

  it("skips verification and does not call Cloudflare — this is what keeps local dev working", async () => {
    const calls = stubSiteverify({ body: { success: true } });

    const result = await verifyTurnstile(undefined, "203.0.113.9");

    expect(result).toEqual({ ok: true, skipped: true });
    expect(calls).toHaveLength(0);
  });
});

describe("when Turnstile is configured", () => {
  beforeEach(() => vi.stubEnv("TURNSTILE_SECRET_KEY", "0x4AAAAAATEST-secret"));

  it("reports itself as configured", () => {
    expect(isTurnstileConfigured()).toBe(true);
  });

  it("REFUSES a missing token rather than falling through", async () => {
    const calls = stubSiteverify({ body: { success: true } });

    const result = await verifyTurnstile(undefined, "203.0.113.9");

    expect(result.ok).toBe(false);
    expect(result.error).toBe("missing-token");
    expect(calls).toHaveLength(0);
  });

  it("REFUSES a whitespace-only token", async () => {
    stubSiteverify({ body: { success: true } });
    expect((await verifyTurnstile("   ")).ok).toBe(false);
  });

  it("accepts a valid token and sends secret, response and remoteip", async () => {
    const calls = stubSiteverify({ body: { success: true } });

    const result = await verifyTurnstile("tok_abc", "203.0.113.9");

    expect(result.ok).toBe(true);
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toContain("challenges.cloudflare.com/turnstile/v0/siteverify");
    expect(calls[0].body.get("secret")).toBe("0x4AAAAAATEST-secret");
    expect(calls[0].body.get("response")).toBe("tok_abc");
    expect(calls[0].body.get("remoteip")).toBe("203.0.113.9");
  });

  it("omits remoteip when the caller has no IP (and still verifies)", async () => {
    const calls = stubSiteverify({ body: { success: true } });
    expect((await verifyTurnstile("tok_abc")).ok).toBe(true);
    expect(calls[0].body.has("remoteip")).toBe(false);
  });

  it("REFUSES a token Cloudflare rejects, surfacing its error codes", async () => {
    stubSiteverify({ body: { success: false, "error-codes": ["invalid-input-response"] } });

    const result = await verifyTurnstile("tok_bad");

    expect(result.ok).toBe(false);
    expect(result.error).toBe("invalid-input-response");
  });

  it("REFUSES (does not 500) when siteverify returns an HTTP error", async () => {
    stubSiteverify({ status: 502, body: {} });
    const result = await verifyTurnstile("tok_abc");
    expect(result.ok).toBe(false);
    expect(result.error).toBe("HTTP 502");
  });

  it("REFUSES when siteverify is unreachable — an outage must never become an open door", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new DOMException("timed out", "TimeoutError");
      }),
    );

    const result = await verifyTurnstile("tok_abc");

    expect(result.ok).toBe(false);
    expect(result.error).toBe("TimeoutError");
  });

  it("REFUSES when the response body is not JSON", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("<html>oops</html>", { status: 200 })));
    const result = await verifyTurnstile("tok_abc");
    expect(result.ok).toBe(false);
  });
});
