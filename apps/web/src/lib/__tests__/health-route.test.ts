/**
 * The acceptance check for AU-03, at the layer an operator and an uptime monitor see.
 *
 * `GET /api/health` must go 503 when the engine has no upload allowlist, and the reason must be
 * in `engineDetail` — the field that says *which* configuration gap it is, not merely "engine:
 * false". In October the engine refused every render for five days and this probe stayed green;
 * a red probe with `UPLOAD_HOSTS_UNCONFIGURED uploadAllowlist=0` in it is the difference.
 *
 * The engine client (`engineHealth`) is real here; only `fetch` is stubbed, so the status and the
 * body the engine actually returns are what is being exercised.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const fetchMock = vi.fn();

vi.mock("@/lib/prisma", () => ({ prisma: { $queryRaw: vi.fn(async () => [{ ok: 1 }]) } }));
vi.mock("@/lib/r2", () => ({ isR2Configured: () => true }));
vi.mock("@/lib/dodo", () => ({ isDodoConfigured: () => true, isDodoLiveMode: () => false }));
vi.mock("@/lib/tiers", () => ({ productIdForTier: () => "prod_1" }));
vi.mock("@/lib/turnstile", () => ({
  isTurnstileConfigured: () => true,
  turnstileMode: () => "log",
}));

const { GET } = await import("@/app/api/health/route");

function engineReply(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  process.env.ENGINE_URL = "https://engine.test";
  process.env.ENGINE_SERVICE_TOKEN = "test-token";
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
  delete process.env.ENGINE_URL;
  delete process.env.ENGINE_SERVICE_TOKEN;
});

describe("GET /api/health", () => {
  it("goes 503 and names the empty allowlist in engineDetail", async () => {
    fetchMock.mockResolvedValue(
      engineReply({ ok: false, code: "UPLOAD_HOSTS_UNCONFIGURED", uploadAllowlist: 0 }, 503),
    );

    const res = await GET();
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(503);
    expect(body.status).toBe("degraded");
    expect(body.engine).toBe(false);
    expect(String(body.engineDetail)).toContain("UPLOAD_HOSTS_UNCONFIGURED");
    expect(String(body.engineDetail)).toContain("uploadAllowlist=0");
  });

  it("stays green and reports the allowlist count when the engine is healthy", async () => {
    fetchMock.mockResolvedValue(engineReply({ ok: true, uploadAllowlist: 1 }, 200));

    const res = await GET();
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(200);
    expect(body.status).toBe("ok");
    expect(body.engine).toBe(true);
    expect(body.engineDetail).toBe("uploadAllowlist=1");
  });
});
