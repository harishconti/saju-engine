/**
 * Engine timeouts must fit inside the Vercel function limit.
 *
 * AU-11 (2026-10-26 audit): `/api/sample` declared `maxDuration = 60` but called the engine with
 * the default 120 s budget. On a slow render the platform killed the function at 60 s, before the
 * abort fired — so the `ENGINE_TIMEOUT` path never ran, nothing was logged as a timeout, and the
 * visitor got a platform 504 instead of copy they could act on. The route now passes a budget
 * below the limit, and the admin regenerate route gets enough headroom for a deep re-render.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  callEngine: vi.fn(),
  isEngineConfigured: vi.fn(() => true),
  isR2Configured: vi.fn(() => true),
  presignPutUrl: vi.fn(async (key: string) => `https://r2.test/${key}`),
  presignGetUrl: vi.fn(async (key: string) => `https://r2.test/get/${key}`),
  headObject: vi.fn(async () => ({ size: 1234 })),
  rateLimit: vi.fn(async () => undefined),
  getCurrentUser: vi.fn(async () => null),
  requireAdmin: vi.fn(),
  verifyTurnstile: vi.fn(),
  turnstileMode: vi.fn(() => "off"),
  computeAndStoreChart: vi.fn(),
}));

vi.mock("@/lib/engine", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../engine")>()),
  callEngine: mocks.callEngine,
  isEngineConfigured: mocks.isEngineConfigured,
}));
vi.mock("@/lib/r2", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../r2")>()),
  isR2Configured: mocks.isR2Configured,
  presignPutUrl: mocks.presignPutUrl,
  presignGetUrl: mocks.presignGetUrl,
  headObject: mocks.headObject,
}));
vi.mock("@/lib/auth", () => ({
  getCurrentUser: mocks.getCurrentUser,
  requireAdmin: mocks.requireAdmin,
}));
vi.mock("@/lib/prisma", () => ({ prisma: {} }));
vi.mock("@/lib/ratelimit", () => ({ rateLimit: mocks.rateLimit, WINDOW: { minute: 60_000 } }));
vi.mock("@/lib/turnstile", () => ({
  turnstileMode: mocks.turnstileMode,
  verifyTurnstile: mocks.verifyTurnstile,
}));
vi.mock("@/lib/chart-compute", () => ({ computeAndStoreChart: mocks.computeAndStoreChart }));
vi.mock("@/lib/audit", () => ({ writeAudit: vi.fn() }));
vi.mock("@/lib/fulfilment", () => ({
  createJobForOrder: vi.fn(),
  processJobById: vi.fn(),
}));

const sampleRoute = await import("@/app/api/sample/route");
const regenerateRoute = await import("@/app/api/admin/reports/[id]/regenerate/route");
const { SAMPLE_ENGINE_TIMEOUT_MS } = await import("@/lib/engine");

const REQUEST = {
  fullName: "Test Visitor",
  gender: "F",
  birthDate: "1992-03-20",
  birthTime: "14:00",
  timeKnown: true,
  city: "Seoul",
  countryCode: "KR",
};

function post(body: unknown): Request {
  return new Request("https://saju.test/api/sample", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.isEngineConfigured.mockReturnValue(true);
  mocks.isR2Configured.mockReturnValue(true);
  mocks.turnstileMode.mockReturnValue("off");
  mocks.rateLimit.mockResolvedValue(undefined);
  mocks.getCurrentUser.mockResolvedValue(null);
  mocks.presignPutUrl.mockImplementation(async (key: string) => `https://r2.test/${key}`);
  mocks.presignGetUrl.mockImplementation(async (key: string) => `https://r2.test/get/${key}`);
  mocks.headObject.mockResolvedValue({ size: 1234 });
  mocks.callEngine.mockResolvedValue({
    sha256: "a".repeat(64),
    bytes: 4096,
    engineVersion: "0.2.0",
    htmlSha256: "b".repeat(64),
    htmlBytes: 4096,
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("the free sample route", () => {
  it("gives the engine less time than the function is allowed to live", () => {
    expect(SAMPLE_ENGINE_TIMEOUT_MS).toBeLessThan(sampleRoute.maxDuration * 1000);
    expect(SAMPLE_ENGINE_TIMEOUT_MS).toBeGreaterThanOrEqual(40_000);
  });

  it("passes that budget to callEngine, so the abort fires before the platform kills us", async () => {
    const res = await sampleRoute.POST(post(REQUEST), undefined as never);

    expect(res.status).toBe(200);
    expect(mocks.callEngine).toHaveBeenCalledTimes(1);
    expect(mocks.callEngine.mock.calls[0][1]).toBe(SAMPLE_ENGINE_TIMEOUT_MS);
  });
});

describe("the admin regenerate route", () => {
  it("allows a deep re-render rather than dying at the engine's default timeout", () => {
    // The engine call may take up to 120 s; 120 s of function budget left no room to finish.
    expect(regenerateRoute.maxDuration).toBe(300);
  });
});
