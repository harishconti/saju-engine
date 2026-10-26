/**
 * The engine readiness probe, as the webapp sees it.
 *
 * AU-03 (2026-10-26 audit): in October the engine had no upload-host allowlist for five days,
 * so every `/generate` was refused with `UPLOAD_HOSTS_UNCONFIGURED` — and `/api/health` stayed
 * green because the probe only asked "did the engine answer 200?". The probe now returns 503
 * from the engine and this client surfaces *why* in `detail`, which `/api/health` exposes as
 * `engineDetail` — the one field an operator sees without reading the engine's logs.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { engineHealth } from "@/lib/engine";

const fetchMock = vi.fn();

function reply(body: unknown, status: number): Response {
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

describe("engineHealth", () => {
  it("treats a 503 as unhealthy and names the missing allowlist", async () => {
    fetchMock.mockResolvedValue(
      reply(
        { ok: false, code: "UPLOAD_HOSTS_UNCONFIGURED", uploadAllowlist: 0 },
        503,
      ),
    );

    const health = await engineHealth();

    expect(health.ok).toBe(false);
    expect(health.detail).toContain("503");
    expect(health.detail).toContain("UPLOAD_HOSTS_UNCONFIGURED");
    expect(health.detail).toContain("uploadAllowlist=0");
  });

  it("surfaces the allowlist count when the engine is healthy", async () => {
    fetchMock.mockResolvedValue(reply({ ok: true, uploadAllowlist: 1 }, 200));

    const health = await engineHealth();

    expect(health).toEqual({ ok: true, detail: "uploadAllowlist=1" });
  });

  it("still reports an unreachable engine as unhealthy", async () => {
    fetchMock.mockRejectedValue(new TypeError("fetch failed"));

    expect(await engineHealth()).toEqual({ ok: false, detail: "unreachable" });
  });

  it("reports a non-JSON error body without throwing", async () => {
    fetchMock.mockResolvedValue(new Response("upstream exploded", { status: 500 }));

    const health = await engineHealth();

    expect(health.ok).toBe(false);
    expect(health.detail).toContain("HTTP 500");
  });

  it("does not call out when the engine is not configured", async () => {
    delete process.env.ENGINE_URL;

    expect(await engineHealth()).toEqual({ ok: false, detail: "not configured" });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
