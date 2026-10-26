/**
 * The acceptance checks for AU-31 at the layer an operator and an uptime monitor see.
 *
 * Two properties are load-bearing:
 *
 *  1. **The public body is minimal.** `GET /api/health` used to publish `engineDetail`,
 *     `missingProducts`, the payment mode and the Turnstile rollout state to anyone — a map of
 *     which configuration is wrong, and whether the deployment can take real money. A monitor
 *     needs a status code; the diagnosis belongs behind authorisation.
 *  2. **The engine probe is cached.** The probe was a network call on every hit, so a monitor
 *     (or a person refreshing during an incident) multiplied load on the service it was checking.
 *
 * The engine client (`engineHealth`) is real here; only `fetch` is stubbed, so the status and the
 * body the engine actually returns are what is being exercised.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  fetchMock: vi.fn(),
  getCurrentUser: vi.fn(async (): Promise<unknown> => null),
}));

vi.mock("@/lib/prisma", () => ({ prisma: { $queryRaw: vi.fn(async () => [{ ok: 1 }]) } }));
vi.mock("@/lib/r2", () => ({ isR2Configured: () => true }));
vi.mock("@/lib/dodo", () => ({ isDodoConfigured: () => true, isDodoLiveMode: () => false }));
vi.mock("@/lib/tiers", () => ({ productIdForTier: () => "prod_1" }));
vi.mock("@/lib/turnstile", () => ({
  isTurnstileConfigured: () => true,
  turnstileMode: () => "log",
}));
vi.mock("@/lib/auth", () => ({ getCurrentUser: mocks.getCurrentUser }));

const { GET } = await import("@/app/api/health/route");
const { GET: detailGET } = await import("@/app/api/health/detail/route");
const { resetHealthProbeCacheForTests } = await import("@/lib/health");

/** The exact public contract. A new field must be a deliberate change to this list, not a leak. */
const PUBLIC_KEYS = ["checkedAt", "ok", "status", "version"] as const;

function engineReply(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function detailRequest(token?: string): Request {
  return new Request("https://app.test/api/health/detail", {
    headers: token ? { authorization: `Bearer ${token}` } : {},
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  resetHealthProbeCacheForTests();
  vi.stubGlobal("fetch", mocks.fetchMock);
  process.env.ENGINE_URL = "https://engine.test";
  process.env.ENGINE_SERVICE_TOKEN = "test-token";
  mocks.getCurrentUser.mockResolvedValue(null);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
  resetHealthProbeCacheForTests();
  delete process.env.ENGINE_URL;
  delete process.env.ENGINE_SERVICE_TOKEN;
  delete process.env.HEALTH_DETAIL_TOKEN;
  delete process.env.ADMIN_EMAILS;
});

describe("GET /api/health — the public body", () => {
  it("is minimal and leaks none of the operational detail", async () => {
    mocks.fetchMock.mockResolvedValue(
      engineReply({ ok: false, code: "UPLOAD_HOSTS_UNCONFIGURED", uploadAllowlist: 0 }, 503),
    );

    const res = await GET();
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(503);
    expect(body.status).toBe("degraded");
    expect(body.ok).toBe(false);
    expect(typeof body.version).toBe("string");
    expect(typeof body.checkedAt).toBe("string");
    // Exactly these keys: a denylist would let a newly added field leak silently.
    expect(Object.keys(body).sort()).toEqual([...PUBLIC_KEYS]);
  });

  it("stays green when everything is healthy", async () => {
    mocks.fetchMock.mockResolvedValue(engineReply({ ok: true, uploadAllowlist: 1 }, 200));

    const res = await GET();
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(200);
    expect(body.status).toBe("ok");
    expect(body.ok).toBe(true);
  });

  it("reuses the cached engine probe on a repeat hit", async () => {
    mocks.fetchMock.mockResolvedValue(engineReply({ ok: true, uploadAllowlist: 1 }, 200));

    await GET();
    await GET();

    expect(mocks.fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("GET /api/health/detail — the authorised view", () => {
  it("keeps the diagnosis: engineDetail names the empty allowlist", async () => {
    process.env.HEALTH_DETAIL_TOKEN = "health-secret";
    mocks.fetchMock.mockResolvedValue(
      engineReply({ ok: false, code: "UPLOAD_HOSTS_UNCONFIGURED", uploadAllowlist: 0 }, 503),
    );

    const res = await detailGET(detailRequest("health-secret"));
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(503);
    expect(body.status).toBe("degraded");
    expect(String(body.engineDetail)).toContain("UPLOAD_HOSTS_UNCONFIGURED");
    expect(String(body.engineDetail)).toContain("uploadAllowlist=0");
    expect(body.paymentsMode).toBe("test_mode");
    expect(body.botProtection).toBe("log");
    expect(body.missingProducts).toEqual([]);
  });

  it("reports the allowlist count when the engine is healthy", async () => {
    process.env.HEALTH_DETAIL_TOKEN = "health-secret";
    mocks.fetchMock.mockResolvedValue(engineReply({ ok: true, uploadAllowlist: 1 }, 200));

    const res = await detailGET(detailRequest("health-secret"));
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(200);
    expect(body.status).toBe("ok");
    expect(body.engine).toBe(true);
    expect(body.engineDetail).toBe("uploadAllowlist=1");
  });

  it("refuses an unauthorised caller without disclosing anything", async () => {
    // No token configured, no session: the endpoint is closed, not merely uninformative.
    const res = await detailGET(detailRequest());

    expect(res.status).toBe(401);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("UNAUTHORIZED");
    expect(body).not.toHaveProperty("engineDetail");
    expect(mocks.fetchMock).not.toHaveBeenCalled();
  });

  it("accepts an admin session, with the same three-part gate as requireAdmin", async () => {
    process.env.ADMIN_EMAILS = "owner@example.com";
    mocks.getCurrentUser.mockResolvedValue({
      id: "u1",
      name: "Owner",
      email: "owner@example.com",
      role: "ADMIN",
      emailVerified: true,
    });
    mocks.fetchMock.mockResolvedValue(engineReply({ ok: true, uploadAllowlist: 1 }, 200));

    const res = await detailGET(detailRequest());

    expect(res.status).toBe(200);
  });

  it("does not accept an unverified admin address", async () => {
    process.env.ADMIN_EMAILS = "owner@example.com";
    mocks.getCurrentUser.mockResolvedValue({
      id: "u1",
      name: "Owner",
      email: "owner@example.com",
      role: "ADMIN",
      emailVerified: false,
    });

    const res = await detailGET(detailRequest());

    expect(res.status).toBe(401);
  });
});
