/**
 * The sweep's HTTP answer.
 *
 * AU-03 (2026-10-26 audit): the sweep computed `stuckJobs` and returned it in JSON, but always
 * answered 200. `.github/workflows/sla-sweep.yml` used `curl -f`, which only fails on an HTTP
 * error — so a dispatcher that had stopped picking up jobs was invisible. The status code is now
 * the alert: 503 while anything is stuck or has recently failed, with the same JSON body.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const { runSlaSweep } = vi.hoisted(() => ({ runSlaSweep: vi.fn() }));

vi.mock("@/lib/sla", () => ({ runSlaSweep }));

const { GET } = await import("@/app/api/cron/sla/route");

function sweepResult(overrides: Record<string, number> = {}) {
  return {
    due: 0,
    autoDelivered: 0,
    skippedInReview: 0,
    skipped: 0,
    heldReleased: 0,
    stuckJobs: 0,
    recentFailures: 0,
    overdueFailures: 0,
    ranAt: "2026-10-26T12:00:00.000Z",
    ...overrides,
  };
}

function request(): Request {
  return new Request("https://app.test/api/cron/sla", {
    headers: { authorization: "Bearer cron-secret" },
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  process.env.CRON_SECRET = "cron-secret";
  runSlaSweep.mockResolvedValue(sweepResult());
});

afterEach(() => {
  delete process.env.CRON_SECRET;
});

describe("GET /api/cron/sla", () => {
  it("answers 200 when nothing is stuck and nothing failed", async () => {
    const res = await GET(request(), undefined as never);

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.ok).toBe(true);
    expect(body.stuckJobs).toBe(0);
    expect(body.recentFailures).toBe(0);
  });

  it("answers 503 when a job is stuck, and keeps the JSON body", async () => {
    runSlaSweep.mockResolvedValue(sweepResult({ stuckJobs: 2 }));

    const res = await GET(request(), undefined as never);

    expect(res.status).toBe(503);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.ok).toBe(false);
    expect(body.stuckJobs).toBe(2);
    expect(body.recentFailures).toBe(0);
  });

  it("answers 503 when a job failed recently", async () => {
    runSlaSweep.mockResolvedValue(sweepResult({ recentFailures: 1 }));

    const res = await GET(request(), undefined as never);

    expect(res.status).toBe(503);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.ok).toBe(false);
    expect(body.recentFailures).toBe(1);
  });

  it("answers 503 for a paid render that failed past its deadline", async () => {
    // AU-14: nothing retries a FAILED job, so "recent only" would let a dead paid order sit in a
    // green pipeline forever.
    runSlaSweep.mockResolvedValue(sweepResult({ overdueFailures: 2 }));

    const res = await GET(request(), undefined as never);

    expect(res.status).toBe(503);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.ok).toBe(false);
    expect(body.overdueFailures).toBe(2);
  });

  it("still refuses an unauthenticated caller", async () => {
    const res = await GET(new Request("https://app.test/api/cron/sla"), undefined as never);

    expect(res.status).toBe(401);
    expect(runSlaSweep).not.toHaveBeenCalled();
  });
});
