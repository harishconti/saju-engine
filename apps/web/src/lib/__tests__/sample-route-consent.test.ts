import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-22 (2026-10-26 audit): the free sample created a Profile for any signed-in visitor. The
 * privacy policy says consent is the lawful basis for holding birth data, and the sample is the
 * single biggest path by which birth data arrives — so it cannot be the one path that skips the
 * check. A signed-in caller without an active, current-version consent is refused with a code the
 * UI turns into a link to the consent control.
 */

const mocks = vi.hoisted(() => {
  const tx = {
    profile: { create: vi.fn(async (_args: { data: Record<string, unknown> }) => ({ id: "prof_1" })) },
    report: { create: vi.fn(async () => ({ id: "report_1" })) },
    delivery: { create: vi.fn(async () => ({})) },
  };
  return {
    tx,
    getCurrentUser: vi.fn(),
    hasActiveServiceConsent: vi.fn(),
    rateLimit: vi.fn(),
    writeAudit: vi.fn(async () => ({})),
    computeAndStoreChart: vi.fn(async () => ({})),
    prisma: {
      profile: { findFirst: vi.fn(), count: vi.fn() },
      report: { findFirst: vi.fn() },
      $transaction: vi.fn(async (fn: (t: typeof tx) => Promise<unknown>) => fn(tx)),
    },
    isR2Configured: vi.fn(() => true),
    isEngineConfigured: vi.fn(() => true),
    buildSampleKey: vi.fn(() => "reports/u1/sample.html"),
    buildAnonymousKey: vi.fn((id: string) => `reports/anonymous/${id}`),
    headObject: vi.fn(async () => ({ size: 1024 })),
    presignGetUrl: vi.fn(async () => "https://r2.test/read"),
    presignPutUrl: vi.fn(async () => "https://r2.test/put"),
    callEngine: vi.fn(async () => ({ htmlBytes: 1024, engineVersion: "engine-1" })),
    turnstileMode: vi.fn(() => "off"),
    verifyTurnstile: vi.fn(async (): Promise<{ ok: boolean; error?: string }> => ({ ok: true })),
  };
});

vi.mock("@/lib/auth", () => ({ getCurrentUser: mocks.getCurrentUser }));
vi.mock("@/lib/consent", () => ({
  hasActiveServiceConsent: mocks.hasActiveServiceConsent,
  CONSENT_REQUIRED_MESSAGE: "Please accept the privacy policy in your account settings.",
}));
vi.mock("@/lib/ratelimit", () => ({
  rateLimit: mocks.rateLimit,
  WINDOW: { minute: 60_000, hour: 3_600_000, day: 86_400_000 },
}));
vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/r2", () => ({
  isR2Configured: mocks.isR2Configured,
  buildSampleKey: mocks.buildSampleKey,
  buildAnonymousKey: mocks.buildAnonymousKey,
  headObject: mocks.headObject,
  presignGetUrl: mocks.presignGetUrl,
  presignPutUrl: mocks.presignPutUrl,
}));
vi.mock("@/lib/engine", () => ({
  ENGINE_CONTRACT_VERSION: "1",
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
  fullName: "Test Person",
  gender: "F",
  birthDate: "1993-03-19",
  birthTime: "14:30",
  timeKnown: true,
  city: "Seoul",
  countryCode: "KR",
  country: "South Korea",
};

function request(headers: Record<string, string> = {}): Request {
  return new Request("https://app.test/api/sample", {
    method: "POST",
    headers: { "content-type": "application/json", ...headers },
    body: JSON.stringify(BODY),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.getCurrentUser.mockResolvedValue(null);
  mocks.hasActiveServiceConsent.mockResolvedValue(false);
  mocks.rateLimit.mockResolvedValue(undefined);
  mocks.prisma.profile.findFirst.mockResolvedValue(null);
  mocks.prisma.profile.count.mockResolvedValue(0);
  mocks.prisma.report.findFirst.mockResolvedValue(null);
  mocks.turnstileMode.mockReturnValue("off");
  mocks.verifyTurnstile.mockResolvedValue({ ok: true });
});

describe("POST /api/sample — consent gate (AU-22)", () => {
  it("refuses a signed-in visitor with no active consent: 409, a code, and no Profile", async () => {
    mocks.getCurrentUser.mockResolvedValue({ id: "u1", name: "Test", email: "t@test", role: "CLIENT" });
    mocks.hasActiveServiceConsent.mockResolvedValue(false);

    const res = await POST(request(), undefined as never);
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(409);
    expect(body.code).toBe("CONSENT_REQUIRED");
    expect(mocks.hasActiveServiceConsent).toHaveBeenCalledWith("u1");
    // Nothing was written and no engine work was spent before the refusal.
    expect(mocks.prisma.$transaction).not.toHaveBeenCalled();
    expect(mocks.tx.profile.create).not.toHaveBeenCalled();
    expect(mocks.callEngine).not.toHaveBeenCalled();
  });

  it("proceeds for a signed-in visitor with active consent and creates exactly one Profile", async () => {
    mocks.getCurrentUser.mockResolvedValue({ id: "u1", name: "Test", email: "t@test", role: "CLIENT" });
    mocks.hasActiveServiceConsent.mockResolvedValue(true);

    const res = await POST(request(), undefined as never);
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(200);
    expect(body.savedToProfile).toBe(true);
    expect(body.reportId).toBe("report_1");
    expect(mocks.hasActiveServiceConsent).toHaveBeenCalledWith("u1");
    expect(mocks.tx.profile.create).toHaveBeenCalledTimes(1);
    expect(mocks.tx.profile.create.mock.calls[0]![0]).toMatchObject({
      data: expect.objectContaining({ userId: "u1", fullName: "Test Person" }),
    });
  });

  it("never gates an anonymous visitor — the sample is still the account-free funnel", async () => {
    mocks.getCurrentUser.mockResolvedValue(null);

    const res = await POST(request(), undefined as never);
    const body = (await res.json()) as Record<string, unknown>;

    expect(res.status).toBe(200);
    expect(body.savedToProfile).toBe(false);
    expect(mocks.hasActiveServiceConsent).not.toHaveBeenCalled();
    expect(mocks.prisma.$transaction).not.toHaveBeenCalled();
  });
});

describe("POST /api/sample — visitor IP never reaches a log (AU-33)", () => {
  it("logs the Turnstile failure without the visitor's raw address", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    mocks.turnstileMode.mockReturnValue("log");
    mocks.verifyTurnstile.mockResolvedValue({ ok: false, error: "missing-token" });

    const res = await POST(request({ "x-real-ip": "203.0.113.7" }), undefined as never);

    expect(res.status).toBe(200);
    expect(warn).toHaveBeenCalled();
    const logged = warn.mock.calls.flat().map(String).join(" ");
    expect(logged).toContain("turnstile[log]");
    expect(logged).not.toContain("203.0.113.7");
    warn.mockRestore();
  });
});
