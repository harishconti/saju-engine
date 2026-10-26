/**
 * AU-29 (2026-10-26 audit): the free sample must not depend on an artefact it discards.
 *
 * The engine used to require a PDF upload target, so `/api/sample` presigned one under the swept
 * prefix — a PDF nobody keeps — and a failure of that throwaway upload failed the sample. A
 * failed *reading* upload, meanwhile, was only noticed by `headObject` and surfaced as
 * `UPLOAD_NOT_VERIFIED`, which says nothing about which artefact was missing.
 *
 * The contract now accepts a reading-only request. These tests pin both halves: the sample asks
 * for the reading and no PDF, and a reading that did not upload is an HTML-specific failure.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  hasActiveServiceConsent: vi.fn(),
  rateLimit: vi.fn(),
  writeAudit: vi.fn(async () => ({})),
  computeAndStoreChart: vi.fn(async () => ({})),
  isR2Configured: vi.fn(() => true),
  isEngineConfigured: vi.fn(() => true),
  buildSampleKey: vi.fn((userId: string, id: string) => `reports/${userId}/samples/${id}.html`),
  buildAnonymousKey: vi.fn((id: string) => `reports/anonymous/${id}/sample.html`),
  headObject: vi.fn(),
  presignGetUrl: vi.fn(async () => "https://r2.test/read"),
  presignPutUrl: vi.fn(async (_key: string, _contentType?: string) => "https://r2.test/put"),
  callEngine: vi.fn(),
  turnstileMode: vi.fn(() => "off"),
  verifyTurnstile: vi.fn(async () => ({ ok: true })),
}));

vi.mock("@/lib/auth", () => ({ getCurrentUser: mocks.getCurrentUser }));
vi.mock("@/lib/consent", () => ({
  hasActiveServiceConsent: mocks.hasActiveServiceConsent,
  CONSENT_REQUIRED_MESSAGE: "Please accept the privacy policy in your account settings.",
}));
vi.mock("@/lib/ratelimit", () => ({
  rateLimit: mocks.rateLimit,
  WINDOW: { minute: 60_000, hour: 3_600_000, day: 86_400_000 },
}));
vi.mock("@/lib/prisma", () => ({ prisma: {} }));
vi.mock("@/lib/r2", () => ({
  isR2Configured: mocks.isR2Configured,
  buildSampleKey: mocks.buildSampleKey,
  buildAnonymousKey: mocks.buildAnonymousKey,
  headObject: mocks.headObject,
  presignGetUrl: mocks.presignGetUrl,
  presignPutUrl: mocks.presignPutUrl,
}));
vi.mock("@/lib/engine", () => ({
  ENGINE_CONTRACT_VERSION: 1,
  SAMPLE_ENGINE_TIMEOUT_MS: 50_000,
  callEngine: mocks.callEngine,
  isEngineConfigured: mocks.isEngineConfigured,
}));
vi.mock("@/lib/chart-compute", () => ({ computeAndStoreChart: mocks.computeAndStoreChart }));
vi.mock("@/lib/audit", () => ({ writeAudit: mocks.writeAudit }));
vi.mock("@/lib/turnstile", () => ({
  turnstileMode: mocks.turnstileMode,
  verifyTurnstile: mocks.verifyTurnstile,
}));

const { POST } = await import("@/app/api/sample/route");

const BODY = {
  fullName: "Test Visitor",
  gender: "F",
  birthDate: "1993-03-19",
  birthTime: "14:30",
  timeKnown: true,
  city: "Seoul",
  countryCode: "KR",
  country: "South Korea",
};

function request(overrides: Partial<typeof BODY> = {}): Request {
  return new Request("https://app.test/api/sample", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ...BODY, ...overrides }),
  });
}

function enginePayload(): Record<string, unknown> {
  return mocks.callEngine.mock.calls[0]![0] as Record<string, unknown>;
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.getCurrentUser.mockResolvedValue(null);
  mocks.rateLimit.mockResolvedValue(undefined);
  mocks.isR2Configured.mockReturnValue(true);
  mocks.isEngineConfigured.mockReturnValue(true);
  mocks.turnstileMode.mockReturnValue("off");
  mocks.verifyTurnstile.mockResolvedValue({ ok: true });
  mocks.presignPutUrl.mockResolvedValue("https://r2.test/put");
  mocks.presignGetUrl.mockResolvedValue("https://r2.test/read");
  mocks.headObject.mockResolvedValue({ size: 1024 });
  mocks.callEngine.mockResolvedValue({ htmlBytes: 1024, sha256: null, bytes: null, engineVersion: "engine-1" });
});

describe("POST /api/sample — reading-only upload (AU-29)", () => {
  it("asks the engine for the reading and no PDF at all", async () => {
    const res = await POST(request(), undefined as never);

    expect(res.status).toBe(200);
    const payload = enginePayload();
    expect(payload.uploadUrl).toBeUndefined();
    expect(payload.htmlUploadUrl).toBe("https://r2.test/put");
    // Exactly one presign, and it is the reading — with the content type the engine sends (AU-37).
    expect(mocks.presignPutUrl).toHaveBeenCalledTimes(1);
    expect(mocks.presignPutUrl.mock.calls[0]![1]).toBe("text/html; charset=utf-8");
  });

  it("fails with an HTML-specific code when the reading did not upload", async () => {
    mocks.callEngine.mockResolvedValue({ htmlBytes: null, sha256: null, bytes: null, engineVersion: "engine-1" });

    const res = await POST(request(), undefined as never);
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(503);
    expect(body.code).toBe("HTML_UPLOAD_FAILED");
    // Nothing was written, so there was nothing to verify — and no verify call was made.
    expect(mocks.headObject).not.toHaveBeenCalled();
  });

  it("still verifies a claimed upload, and says UPLOAD_NOT_VERIFIED when the object is missing", async () => {
    mocks.headObject.mockResolvedValue(null);

    const res = await POST(request(), undefined as never);
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(503);
    expect(body.code).toBe("UPLOAD_NOT_VERIFIED");
    expect(mocks.headObject).toHaveBeenCalledTimes(1);
  });

  it("returns the reading's own byte count", async () => {
    const res = await POST(request(), undefined as never);
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(200);
    expect(body.bytes).toBe(1024);
    expect(body.readUrl).toBe("https://r2.test/read");
  });
});

describe("POST /api/sample — country disambiguation", () => {
  it("forwards a request-supplied country so a country-only choice resolves", async () => {
    // "Cambridge" is ambiguous without a country; the schema accepts `country`, so a caller may
    // disambiguate that way even when it sends no two-letter code.
    const res = await POST(
      request({ city: "Cambridge", country: "United States", countryCode: undefined }),
      undefined as never,
    );

    expect(res.status).toBe(200);
    const profile = enginePayload().profileA as Record<string, unknown>;
    expect(profile.timezone).toBe("America/New_York");
  });
});
