import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Owner decision D11 (2026-10-26): withdrawing service consent stops NEW work, but paid work already
 * in flight finishes. The boundary the decision left to the controller is this route — an order
 * created before the withdrawal but not yet paid is refused at checkout, because taking payment
 * would start processing after the withdrawal. An order that is already PAID never reaches the
 * guard: it is answered "already paid" first, and its render is deliberately un-gated
 * (`lib/fulfilment.ts::runDispatchTick`).
 *
 * The refusal reuses the 409 `CONSENT_REQUIRED` code the UI already turns into a link to the
 * consent control, and carries the PROCESSING message rather than the storage one (the reason here
 * is that we would begin processing, not that we would store birth details).
 */

const mocks = vi.hoisted(() => ({
  requireUser: vi.fn(),
  rateLimit: vi.fn(),
  createCheckout: vi.fn(),
  isDodoConfigured: vi.fn(),
  prisma: {
    order: { findFirst: vi.fn(), update: vi.fn() },
    consentRecord: { findFirst: vi.fn() },
  },
}));

vi.mock("@/lib/auth", () => ({ requireUser: mocks.requireUser }));
vi.mock("@/lib/ratelimit", () => ({ rateLimit: mocks.rateLimit, WINDOW: { hour: 3_600_000 } }));
vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/dodo", () => ({
  createCheckout: mocks.createCheckout,
  isDodoConfigured: mocks.isDodoConfigured,
}));

const { POST } = await import("@/app/api/orders/[id]/checkout/route");
const { CONSENT_REQUIRED_MESSAGE, CONSENT_REQUIRED_PROCESSING_MESSAGE } = await import("@/lib/consent");

const ORDER = {
  id: "order_1",
  userId: "user_1",
  status: "AWAITING_PAYMENT" as const,
  priceCents: 5500,
  tier: "deep",
  kind: "SINGLE" as const,
  currency: "USD",
};

const CTX = { params: Promise.resolve({ id: "order_1" }) };

function request(): Request {
  return new Request("https://app.test/api/orders/order_1/checkout", { method: "POST" });
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.requireUser.mockResolvedValue({ id: "user_1", email: "visitor@example.com" });
  mocks.rateLimit.mockResolvedValue(undefined);
  mocks.isDodoConfigured.mockReturnValue(true);
  mocks.createCheckout.mockResolvedValue({ url: "https://checkout.test/session", sessionId: "cs_1" });
  mocks.prisma.order.findFirst.mockResolvedValue({ ...ORDER });
  mocks.prisma.order.update.mockResolvedValue({});
  mocks.prisma.consentRecord.findFirst.mockResolvedValue(null);
});

describe("POST /api/orders/[id]/checkout — withdrawn service consent (D11)", () => {
  it("refuses an unpaid order when the account has no active service consent", async () => {
    const res = await POST(request(), CTX as never);

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("CONSENT_REQUIRED");
    // The reason is processing, not storage — so this is the second message, not the storage one.
    expect(body.error).toBe(CONSENT_REQUIRED_PROCESSING_MESSAGE);
    expect(body.error).not.toBe(CONSENT_REQUIRED_MESSAGE);
    // No payment session was created and no order row was touched.
    expect(mocks.createCheckout).not.toHaveBeenCalled();
    expect(mocks.prisma.order.update).not.toHaveBeenCalled();
  });

  it("proceeds to create a checkout session for a consented account", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: (await import("@/lib/consent")).POLICY_VERSION,
      withdrawnAt: null,
      purposes: { service: true },
    });

    const res = await POST(request(), CTX as never);

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.checkoutUrl).toBe("https://checkout.test/session");
    expect(mocks.createCheckout).toHaveBeenCalledTimes(1);
  });

  it("leaves an already-PAID order on its existing answer, never the consent guard", async () => {
    mocks.prisma.order.findFirst.mockResolvedValue({ ...ORDER, status: "PAID" });

    const res = await POST(request(), CTX as never);

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("ALREADY_PAID");
    expect(mocks.prisma.consentRecord.findFirst).not.toHaveBeenCalled();
    expect(mocks.createCheckout).not.toHaveBeenCalled();
  });
});
