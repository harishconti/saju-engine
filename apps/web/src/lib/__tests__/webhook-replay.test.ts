import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-05 (2026-10-26 audit): a payment webhook that failed after its event row was recorded was
 * never replayed. The route treats every P2002 as a duplicate, so the provider's retry was answered
 * `200 {duplicate:true}` and the payment stayed unpaid; the cleanup cron only *counted* pending
 * event rows and never re-ran them.
 *
 * Two rules hold the fix together:
 *  - P2002 is a duplicate only when `processedAt` is set. Otherwise the stored event is re-processed.
 *  - `retryUnprocessedWebhooks` actually replays the stored payload for the providers it knows.
 */

const { prismaMock, processDodoEvent, verifyMock } = vi.hoisted(() => ({
  prismaMock: {
    webhookEvent: {
      create: vi.fn(),
      findUnique: vi.fn(),
      findMany: vi.fn(),
      update: vi.fn(),
    },
  },
  processDodoEvent: vi.fn(),
  verifyMock: vi.fn(),
}));

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/dodo-webhook", () => ({ DODO_PROVIDER: "dodo", processDodoEvent }));
vi.mock("@/lib/webhook-signature", () => ({ verifyStandardWebhook: verifyMock }));

const { POST } = await import("@/app/api/webhooks/dodo/route");
const { retryUnprocessedWebhooks } = await import("../cleanup");

const EVENT = {
  type: "payment.succeeded",
  data: { payment_id: "pay_1", metadata: { order_id: "o1" } },
};

function webhookRequest(body: unknown = EVENT, id = "wh-1"): Request {
  return new Request("https://app.test/api/webhooks/dodo", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "webhook-id": id,
      "webhook-timestamp": "1750000000",
      "webhook-signature": "v1,test",
    },
    body: JSON.stringify(body),
  });
}

function uniqueViolation(): Error {
  return Object.assign(new Error("Unique constraint failed"), { code: "P2002" });
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubEnv("DODO_PAYMENTS_WEBHOOK_KEY", "test-only-webhook-key");
  verifyMock.mockReturnValue({ ok: true });
  prismaMock.webhookEvent.update.mockResolvedValue({});
  processDodoEvent.mockResolvedValue("payment.succeeded");
});

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("POST /api/webhooks/dodo — redelivery of an event recorded but not processed", () => {
  it("re-processes the event and marks processedAt instead of acknowledging it as a duplicate", async () => {
    prismaMock.webhookEvent.create.mockRejectedValue(uniqueViolation());
    prismaMock.webhookEvent.findUnique.mockResolvedValue({ id: "w1", processedAt: null });

    const res = await POST(webhookRequest());

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body).toMatchObject({ ok: true, type: "payment.succeeded" });
    expect(body.duplicate).toBeUndefined();
    expect(prismaMock.webhookEvent.findUnique).toHaveBeenCalledWith({
      where: { provider_eventId: { provider: "dodo", eventId: "wh-1" } },
      select: { id: true, processedAt: true },
    });
    expect(processDodoEvent).toHaveBeenCalledTimes(1);
    expect(processDodoEvent).toHaveBeenCalledWith(EVENT);
    expect(prismaMock.webhookEvent.update).toHaveBeenCalledWith({
      where: { id: "w1" },
      data: { processedAt: expect.any(Date) },
    });
  });

  it("acknowledges a fully processed duplicate without re-running side effects", async () => {
    prismaMock.webhookEvent.create.mockRejectedValue(uniqueViolation());
    prismaMock.webhookEvent.findUnique.mockResolvedValue({ id: "w1", processedAt: new Date() });

    const res = await POST(webhookRequest());

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, duplicate: true });
    expect(processDodoEvent).not.toHaveBeenCalled();
    expect(prismaMock.webhookEvent.update).not.toHaveBeenCalled();
  });

  it("still processes a first delivery and marks it processed", async () => {
    prismaMock.webhookEvent.create.mockResolvedValue({ id: "w1" });

    const res = await POST(webhookRequest());

    expect(res.status).toBe(200);
    expect(processDodoEvent).toHaveBeenCalledWith(EVENT);
    expect(prismaMock.webhookEvent.update).toHaveBeenCalledWith({
      where: { id: "w1" },
      data: { processedAt: expect.any(Date) },
    });
  });

  it("leaves a crashed processing attempt unprocessed so the next retry can replay it", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    prismaMock.webhookEvent.create.mockResolvedValue({ id: "w1" });
    processDodoEvent.mockRejectedValue(new Error("engine unreachable"));

    const res = await POST(webhookRequest());

    expect(res.status).toBe(500);
    expect(prismaMock.webhookEvent.update).not.toHaveBeenCalled();
    consoleError.mockRestore();
  });
});

describe("retryUnprocessedWebhooks — real replay (AU-05)", () => {
  const NOW = new Date("2026-10-26T12:00:00.000Z");

  it("replays a stored Dodo payload and marks it processed", async () => {
    prismaMock.webhookEvent.findMany.mockResolvedValue([
      { id: "w1", provider: "dodo", payload: EVENT },
    ]);

    await expect(retryUnprocessedWebhooks(NOW)).resolves.toBe(1);

    expect(processDodoEvent).toHaveBeenCalledWith(EVENT);
    expect(prismaMock.webhookEvent.update).toHaveBeenCalledWith({
      where: { id: "w1" },
      data: { processedAt: NOW, error: null },
    });
  });

  it("asks only for replayable providers and bounds the batch", async () => {
    prismaMock.webhookEvent.findMany.mockResolvedValue([]);

    await retryUnprocessedWebhooks(NOW);

    expect(prismaMock.webhookEvent.findMany).toHaveBeenCalledWith({
      where: {
        processedAt: null,
        receivedAt: { lt: new Date(NOW.getTime() - 60_000) },
        provider: { in: ["dodo"] },
      },
      orderBy: { receivedAt: "asc" },
      take: 20,
      select: { id: true, provider: true, payload: true },
    });
  });

  it("skips an event whose provider has no replayer", async () => {
    prismaMock.webhookEvent.findMany.mockResolvedValue([
      { id: "w2", provider: "some-future-provider", payload: {} },
    ]);

    await expect(retryUnprocessedWebhooks(NOW)).resolves.toBe(0);

    expect(processDodoEvent).not.toHaveBeenCalled();
    expect(prismaMock.webhookEvent.update).not.toHaveBeenCalled();
  });

  it("keeps a failed replay pending and records why", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    prismaMock.webhookEvent.findMany.mockResolvedValue([
      { id: "w1", provider: "dodo", payload: EVENT },
    ]);
    processDodoEvent.mockRejectedValue(new Error("still down"));

    await expect(retryUnprocessedWebhooks(NOW)).resolves.toBe(0);

    expect(prismaMock.webhookEvent.update).toHaveBeenCalledWith({
      where: { id: "w1" },
      data: { error: "Error" },
    });
    const data = (prismaMock.webhookEvent.update.mock.calls[0][0] as { data: Record<string, unknown> }).data;
    expect(data.processedAt).toBeUndefined();
    consoleError.mockRestore();
  });
});
