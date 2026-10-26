import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-24 (owner decision D7, 2026-10-26): withdrawing the `service` purpose is supposed to stop
 * processing. Before this, it only flipped a flag: an account with no active consent could still
 * create an order and start a paid render. The account page told them processing had stopped.
 *
 * Both entry points into generation — creating an order and the "check for updates" nudge — now
 * refuse with a stable `CONSENT_REQUIRED` code, which the dashboard turns into a link to the
 * consent control instead of a dead end.
 */

const { requireUser, requireActiveServiceConsent, rateLimit, withIdempotency, prismaMock } = vi.hoisted(() => ({
  requireUser: vi.fn(),
  requireActiveServiceConsent: vi.fn(),
  rateLimit: vi.fn(),
  withIdempotency: vi.fn(),
  prismaMock: {
    order: { create: vi.fn(), update: vi.fn() },
    profile: { findMany: vi.fn() },
  },
}));

vi.mock("@/lib/auth", () => ({ requireUser }));
vi.mock("@/lib/consent", () => ({ requireActiveServiceConsent }));
vi.mock("@/lib/ratelimit", () => ({ rateLimit, WINDOW: { hour: 3_600_000 } }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/idempotency", () => ({ withIdempotency }));

const { POST } = await import("@/app/api/orders/route");
const { ApiError } = await import("@/lib/api");

function request(body: unknown): Request {
  return new Request("https://app.test/api/orders", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", email: "a@b.c", role: "USER" });
  rateLimit.mockResolvedValue(undefined);
  requireActiveServiceConsent.mockResolvedValue(true);
});

describe("POST /api/orders — withdrawn service consent (AU-24)", () => {
  it("refuses to create an order when the account has no active service consent", async () => {
    requireActiveServiceConsent.mockRejectedValue(
      new ApiError(409, "CONSENT_REQUIRED", "Please accept the privacy policy in your account settings first."),
    );

    const res = await POST(
      request({ tier: "essential", profileAId: "p1", adultConfirmed: true }),
      undefined as never,
    );

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("CONSENT_REQUIRED");
    expect(String(body.error)).toMatch(/privacy policy/i);
    // Nothing was written and no idempotency record was claimed: the refusal happens before both.
    expect(withIdempotency).not.toHaveBeenCalled();
    expect(prismaMock.order.create).not.toHaveBeenCalled();
  });

  it("checks consent for the authenticated user, not whatever the body claims", async () => {
    requireActiveServiceConsent.mockRejectedValue(new ApiError(409, "CONSENT_REQUIRED", "refused"));

    await POST(request({ tier: "essential", profileAId: "p1", adultConfirmed: true }), undefined as never);

    expect(requireActiveServiceConsent).toHaveBeenCalledWith("u1");
  });

  it("lets a consented account past the gate (the refusal is not a blanket block)", async () => {
    // An empty body fails validation *after* the gate, which is how we can tell the request got
    // past it without standing up the whole order pipeline.
    const res = await POST(request({}), undefined as never);

    expect(res.status).toBe(422);
    expect(((await res.json()) as Record<string, unknown>).code).toBe("VALIDATION_FAILED");
    expect(requireActiveServiceConsent).toHaveBeenCalledTimes(1);
  });
});
