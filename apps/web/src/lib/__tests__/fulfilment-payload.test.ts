import { beforeEach, describe, expect, it, vi } from "vitest";
import type { EnginePayload } from "../engine";

/**
 * What the webapp asks the engine to render — in particular, that it asks for the reading.
 *
 * The bug this file exists for (owner, 2026-10-17): *"I see html reports essential and deep but not in
 * comparability reports."* The engine could always produce a compatibility reading — the compat
 * product renders through the very same `build_pdf`/`markdown_to_html(web=True)` as a single chart —
 * but the webapp only requested `htmlUploadUrl` for `kind === "single"`, on the belief that compat had
 * "its own two-chart renderer with no web mode". So compat orders got a PDF and no reading, silently,
 * and nothing in either suite covered the payload that decides it.
 *
 * Only the edges are mocked (prisma, R2 IO, the engine call); key building and the kind/tier rules are
 * the real ones, because those are what the assertion is about.
 */

const mocks = vi.hoisted(() => ({
  prisma: {
    order: { findUnique: vi.fn() },
    report: { findFirst: vi.fn() },
    $transaction: vi.fn(),
  },
  presignPutUrl: vi.fn(async (key: string) => `https://r2.test/${key}`),
  headObject: vi.fn(),
  callEngine: vi.fn(),
  tx: {
    report: { create: vi.fn(), updateMany: vi.fn() },
    delivery: { create: vi.fn() },
    job: { update: vi.fn() },
  },
}));

vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/r2", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../r2")>()),
  isR2Configured: () => true,
  presignPutUrl: mocks.presignPutUrl,
  headObject: mocks.headObject,
}));
vi.mock("@/lib/engine", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../engine")>()),
  callEngine: mocks.callEngine,
}));
vi.mock("@/lib/email", () => ({ deliverReport: vi.fn(), deliverAudioReadyEmail: vi.fn() }));
vi.mock("@/lib/audit", () => ({ writeAudit: vi.fn() }));
vi.mock("@/lib/queue", () => ({
  LEASE_MS: 60_000,
  claimJob: vi.fn(),
  completeJob: vi.fn(),
  failJob: vi.fn(),
  requeueJob: vi.fn(),
}));

const { processClaimedJob } = await import("../fulfilment");

const PROFILE = {
  id: "prof_1",
  fullName: "Priya",
  gender: "F" as const,
  birthDate: new Date("1992-03-20T00:00:00.000Z"),
  birthTime: "14:00",
  timeKnown: true,
  timezone: "Asia/Seoul",
  utcOffset: 9,
  city: "Seoul",
  latitude: 37.5665,
  longitude: 126.978,
};

function order(kind: "SINGLE" | "COMPAT") {
  return {
    id: "order_1",
    userId: "user_1",
    kind,
    tier: kind === "COMPAT" ? "basic" : "deep",
    profileAId: "prof_1",
    profileBId: kind === "COMPAT" ? "prof_2" : null,
    profileA: PROFILE,
    profileB: kind === "COMPAT" ? { ...PROFILE, id: "prof_2", fullName: "Arun" } : null,
    favorableOverrideA: null,
    favorableOverrideB: null,
  };
}

function setUp(kind: "SINGLE" | "COMPAT") {
  mocks.prisma.order.findUnique.mockResolvedValue(order(kind));
  mocks.prisma.report.findFirst.mockResolvedValue(null);
  mocks.prisma.$transaction.mockImplementation(async (fn: (tx: unknown) => Promise<void>) =>
    fn(mocks.tx),
  );
  // Both the PDF and the reading really land, so the row can record where they are.
  mocks.headObject.mockResolvedValue({ size: 1234 });
  mocks.callEngine.mockResolvedValue({
    sha256: "a".repeat(64),
    bytes: 4096,
    pages: 7,
    engineVersion: "0.2.0",
    htmlSha256: "b".repeat(64),
    htmlBytes: 4096,
  });
}

function payloadSentToEngine(): EnginePayload {
  expect(mocks.callEngine).toHaveBeenCalledTimes(1);
  return mocks.callEngine.mock.calls[0][0] as EnginePayload;
}

const JOB = {
  id: "job_1",
  orderId: "order_1",
  kind: "GENERATE" as const,
  attempts: 0,
  maxAttempts: 3,
};

describe("the engine payload asks for the reading", () => {
  // Calls accumulate across tests otherwise, so `create.mock.calls[0]` would be an earlier test's row.
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.presignPutUrl.mockImplementation(async (key: string) => `https://r2.test/${key}`);
  });

  it("asks for it on a compatibility order", async () => {
    setUp("COMPAT");
    const outcome = await processClaimedJob(JOB as never);
    expect(outcome.ok).toBe(true);

    const payload = payloadSentToEngine();
    expect(payload.kind).toBe("compat");
    expect(payload.profileB).toBeDefined();
    // The regression: this key used to be absent for compat, so no reading was ever rendered.
    expect(payload.htmlUploadUrl).toMatch(/\/reports\/user_1\/order_1\/[0-9a-f-]{36}\.html$/);
    // …and the URL the engine is told to write to is the one the app can later read back.
    expect(payload.htmlUploadUrl).toBe(`https://r2.test/${payload.htmlUploadUrl!.split("/r2.test/")[1]}`);
    expect(payload.mdUploadUrl).toMatch(/\.md$/);
  });

  it("asks for it on a single-chart order too", async () => {
    setUp("SINGLE");
    await processClaimedJob(JOB as never);

    const payload = payloadSentToEngine();
    expect(payload.kind).toBe("single");
    expect(payload.profileB).toBeUndefined();
    expect(payload.htmlUploadUrl).toMatch(/\/reports\/user_1\/order_1\/[0-9a-f-]{36}\.html$/);
  });

  it("records where the reading is only once it really landed", async () => {
    setUp("COMPAT");
    await processClaimedJob(JOB as never);

    const created = mocks.tx.report.create.mock.calls[0][0].data as Record<string, unknown>;
    expect(String(created.htmlKey)).toMatch(/\.html$/);
    expect(created.htmlBytes).toBe(4096);
    expect(String(created.pdfKey)).toMatch(/\.pdf$/);
  });

  it("still files the report when the reading does not land", async () => {
    setUp("COMPAT");
    // The engine says it did not upload it: best-effort, like the markdown. The PDF is the fallback
    // deliverable, and the row must not point at an object that is not there.
    mocks.callEngine.mockResolvedValue({
      sha256: "a".repeat(64),
      bytes: 4096,
      pages: 7,
      engineVersion: "0.2.0",
      htmlSha256: null,
      htmlBytes: null,
    });

    const outcome = await processClaimedJob(JOB as never);
    expect(outcome.ok).toBe(true);
    const created = mocks.tx.report.create.mock.calls[0][0].data as Record<string, unknown>;
    expect(created.htmlKey).toBeNull();
    expect(created.htmlBytes).toBeNull();
  });
});
