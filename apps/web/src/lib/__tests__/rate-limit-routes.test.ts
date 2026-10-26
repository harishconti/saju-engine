/**
 * AU-30 (2026-10-26 audit): the account, profile and report routes had no request limit at all.
 *
 * A limit is only real if the route returns 429 once it is reached, so these tests drive each route
 * past its own limit against an in-memory implementation of the same fixed-window store. The real
 * `rateLimit` and the real `handle` wrapper run; only Postgres is replaced.
 *
 * The limits themselves live with the routes, and each is chosen from what the route costs:
 *   - account PATCH        30/hour  — a deliberate display-name edit
 *   - profile PATCH        30/hour  — re-resolves the birthplace and re-renders the chart
 *   - report download      30/minute — streams the object (bandwidth)
 *   - report HTML          60/minute — the primary read path; a refresh must not be refused
 *   - report audio (GET+POST) 30/minute — the MP3 and its script are one narration
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const store = new Map<string, number>();

const upsert = vi.fn(async ({ where }: { where: { bucket_windowStart: { bucket: string; windowStart: Date } } }) => {
  const { bucket, windowStart } = where.bucket_windowStart;
  const key = `${bucket}|${new Date(windowStart).toISOString()}`;
  const count = (store.get(key) ?? 0) + 1;
  store.set(key, count);
  return { count };
});

vi.mock("@/lib/auth", () => ({
  requireUser: vi.fn(async () => ({ id: "u1", email: "owner@example.com" })),
  getCurrentUser: vi.fn(async () => ({ id: "u1", email: "owner@example.com" })),
}));
vi.mock("@/lib/prisma", () => ({
  prisma: {
    rateLimit: { upsert },
    user: { findUnique: vi.fn(async () => null), update: vi.fn() },
    profile: { findFirst: vi.fn(async () => null), findUnique: vi.fn(), update: vi.fn(), updateMany: vi.fn() },
    report: { findFirst: vi.fn(async () => null) },
    $transaction: vi.fn(),
  },
}));
vi.mock("@/lib/r2", () => ({
  presignGetUrl: vi.fn(async () => "https://r2.test/read"),
  isR2Configured: vi.fn(() => true),
}));
vi.mock("@/lib/consent", () => ({
  hasActiveServiceConsent: vi.fn(async () => true),
  CONSENT_REQUIRED_MESSAGE: "consent required",
}));
vi.mock("@/lib/audit", () => ({ audit: vi.fn(), writeAudit: vi.fn() }));
vi.mock("@/lib/validation/schemas", () => ({
  // The routes are exercised only up to the limiter; the schema accepts everything here so a
  // rejection never stands in for the 429 under test.
  profileUpdateSchema: { parse: (v: unknown) => v },
  sampleRequestSchema: { parse: (v: unknown) => v },
}));
vi.mock("@/lib/profile-scrub", () => ({ SCRUBBED_PROFILE: {} }));
vi.mock("@/lib/chart-compute", () => ({ computeAndStoreChart: vi.fn() }));

const { PATCH: accountPATCH } = await import("@/app/api/account/route");
const { PATCH: profilePATCH } = await import("@/app/api/profiles/[id]/route");
const { GET: downloadGET } = await import("@/app/api/reports/[id]/download/route");
const { GET: htmlGET } = await import("@/app/api/reports/[id]/html/route");
const { GET: audioGET, POST: audioPOST } = await import("@/app/api/reports/[id]/audio/route");

const ctx = { params: Promise.resolve({ id: "r1" }) } as never;

function jsonRequest(method: string, body: unknown = {}): Request {
  return new Request("https://app.test/api/test", {
    method,
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

function plainRequest(url: string, method = "GET"): Request {
  return new Request(url, { method });
}

/** Drive `call` `limit` times, then assert the next one is refused. */
async function expectRefusalAfter(limit: number, call: () => Promise<Response>): Promise<void> {
  for (let i = 0; i < limit; i += 1) {
    const res = await call();
    expect(res.status, `request ${i + 1} of ${limit} must not be limited`).not.toBe(429);
  }
  const refused = await call();
  expect(refused.status).toBe(429);
  const body = (await refused.json()) as Record<string, unknown>;
  expect(body.code).toBe("RATE_LIMITED");
}

beforeEach(() => {
  store.clear();
  upsert.mockClear();
  vi.clearAllMocks();
});

describe("AU-30 — routes refuse past their limit", () => {
  it("account PATCH: 30/hour", async () => {
    await expectRefusalAfter(30, () => accountPATCH(jsonRequest("PATCH", { name: "New Name" }), ctx));
  });

  it("profile PATCH: 30/hour", async () => {
    await expectRefusalAfter(30, () => profilePATCH(jsonRequest("PATCH", { city: "Cambridge" }), ctx));
  });

  it("report download: 30/minute", async () => {
    await expectRefusalAfter(30, () => downloadGET(plainRequest("https://app.test/api/reports/r1/download"), ctx));
  });

  it("report HTML: 60/minute", async () => {
    await expectRefusalAfter(60, () => htmlGET(plainRequest("https://app.test/api/reports/r1/html"), ctx));
  });

  it("report audio GET: 30/minute", async () => {
    await expectRefusalAfter(30, () => audioGET(plainRequest("https://app.test/api/reports/r1/audio"), ctx));
  });

  it("report script POST shares the audio bucket", async () => {
    await expectRefusalAfter(30, () => audioPOST(plainRequest("https://app.test/api/reports/r1/audio", "POST"), ctx));
  });
});
