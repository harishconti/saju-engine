import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The "Check for updates" route must never answer a silent success.
 *
 * AU-12 (2026-10-26 audit): the route always answered `200 { ok: true, message: "Checked N reports." }`
 * — even when the render it triggered had failed and the job was back in the queue. The customer saw
 * "Checked" and waited, with no way to know their order was not moving. The failure now travels as a
 * non-2xx with an `error` the dashboard already renders as an alert.
 */

const { requireUser, requireActiveServiceConsent, rateLimit, kickOwnerJobs } = vi.hoisted(() => ({
  requireUser: vi.fn(),
  requireActiveServiceConsent: vi.fn(),
  rateLimit: vi.fn(),
  kickOwnerJobs: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({ requireUser }));
vi.mock("@/lib/consent", () => ({ requireActiveServiceConsent }));
vi.mock("@/lib/ratelimit", () => ({ rateLimit, WINDOW: { hour: 3_600_000 } }));
vi.mock("@/lib/fulfilment", () => ({ kickOwnerJobs }));

const { POST } = await import("@/app/api/jobs/kick/route");

function request(): Request {
  return new Request("https://app.test/api/jobs/kick", { method: "POST" });
}

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "user_1", email: "client@test" });
  rateLimit.mockResolvedValue(undefined);
  requireActiveServiceConsent.mockResolvedValue(true);
  kickOwnerJobs.mockResolvedValue({ processed: 0, generated: 0, failed: 0 });
});

describe("POST /api/jobs/kick", () => {
  it("says the check failed when a queued job could not be rendered", async () => {
    kickOwnerJobs.mockResolvedValue({ processed: 1, generated: 0, failed: 1 });

    const res = await POST(request(), undefined as never);

    expect(res.status).toBe(503);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.ok).toBe(false);
    expect(body.code).toBe("CHECK_FAILED");
    expect(body.failed).toBe(1);
    expect(String(body.error)).toMatch(/try again/i);
    // The order is untouched by a failed check — the job went back on the queue.
    expect(String(body.error)).toMatch(/safe/i);
  });

  it("reports a successful check as success", async () => {
    kickOwnerJobs.mockResolvedValue({ processed: 1, generated: 1, failed: 0 });

    const res = await POST(request(), undefined as never);

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.ok).toBe(true);
    expect(body.generated).toBe(1);
    expect(String(body.message)).toBe("Checked 1 report.");
  });

  it("says nothing was waiting, without calling it a failure", async () => {
    const res = await POST(request(), undefined as never);

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.ok).toBe(true);
    expect(String(body.message)).toBe("Nothing was waiting.");
  });

  it("does not start render work for an account with no active service consent (AU-24)", async () => {
    const { ApiError } = await import("@/lib/api");
    requireActiveServiceConsent.mockRejectedValue(
      new ApiError(409, "CONSENT_REQUIRED", "Please accept the privacy policy in your account settings first."),
    );

    const res = await POST(request(), undefined as never);

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("CONSENT_REQUIRED");
    expect(body.ok).toBeUndefined();
    // The whole point of D7: withdrawal stops processing, it does not merely record a flag.
    expect(kickOwnerJobs).not.toHaveBeenCalled();
    expect(requireActiveServiceConsent).toHaveBeenCalledWith("user_1");
  });
});
