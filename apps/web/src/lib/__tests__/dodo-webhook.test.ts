import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The Dodo processing used to live inside the webhook route. AU-05 moved it into a shared function
 * so the cleanup cron can replay a stored event through exactly the same code. These tests hold the
 * money path still: the replay must not be able to charge a second time, queue a second generation
 * job, or double-count revenue.
 */

const { prismaMock, txMock, writeAudit, audit, track, processJobById, afterCallbacks } = vi.hoisted(() => {
  const afterCallbacks: Array<() => Promise<void> | void> = [];
  const txMock = {
    order: { updateMany: vi.fn(), update: vi.fn() },
    job: { create: vi.fn() },
  };
  const prismaMock = {
    order: { findUnique: vi.fn() },
    $transaction: vi.fn(),
  };
  return {
    prismaMock,
    txMock,
    writeAudit: vi.fn(),
    audit: vi.fn(),
    track: vi.fn(),
    processJobById: vi.fn(),
    afterCallbacks,
  };
});

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/audit", () => ({ writeAudit, audit }));
vi.mock("@/lib/fulfilment", () => ({ processJobById }));
vi.mock("next/server", () => ({
  after: (fn: () => Promise<void> | void) => {
    afterCallbacks.push(fn);
  },
}));
vi.mock("@vercel/analytics/server", () => ({ track }));

const { processDodoEvent } = await import("../dodo-webhook");

const SUCCEEDED = {
  type: "payment.succeeded",
  data: { payment_id: "pay_1", metadata: { order_id: "o1" } },
};

beforeEach(() => {
  vi.clearAllMocks();
  afterCallbacks.length = 0;
  prismaMock.$transaction.mockImplementation(async (fn: (tx: typeof txMock) => Promise<unknown>) =>
    fn(txMock),
  );
  txMock.order.updateMany.mockResolvedValue({ count: 1 });
  txMock.order.update.mockResolvedValue({});
  txMock.job.create.mockResolvedValue({ id: "job_new" });
  track.mockResolvedValue({});
  processJobById.mockResolvedValue({ ok: true, note: "report v1" });
});

describe("processDodoEvent — payment.succeeded", () => {
  it("marks the order paid, queues generation and records the audit", async () => {
    prismaMock.order.findUnique.mockResolvedValue({
      id: "o1",
      status: "AWAITING_PAYMENT",
      tier: "deep",
      user: { deletedAt: null },
    });

    await expect(processDodoEvent(SUCCEEDED)).resolves.toBe("payment.succeeded");

    expect(txMock.order.updateMany).toHaveBeenCalledWith({
      where: { id: "o1", status: { notIn: ["PAID", "REFUNDED"] } },
      data: {
        status: "PAID",
        paidAt: expect.any(Date),
        provider: "dodo",
        providerOrderId: "pay_1",
      },
    });
    expect(txMock.job.create).toHaveBeenCalledWith({
      data: { orderId: "o1", kind: "GENERATE", state: "QUEUED" },
      select: { id: true },
    });
    expect(writeAudit).toHaveBeenCalledWith(
      txMock,
      expect.objectContaining({ entity: "order", entityId: "o1", action: "paid" }),
    );
    expect(track).toHaveBeenCalledWith("purchase", { tier: "deep", provider: "dodo" });

    // AU-13 (2026-10-26 audit): the old dispatch tick picked the OLDEST queued job, which during a
    // backlog is somebody else's order — the payment that just succeeded waited another round trip.
    // The webhook now dispatches the exact job this event created.
    expect(afterCallbacks).toHaveLength(1);
    await afterCallbacks[0]();
    expect(processJobById).toHaveBeenCalledTimes(1);
    expect(processJobById.mock.calls[0][0]).toBe("job_new");
  });

  it("does nothing when the order is already paid", async () => {
    prismaMock.order.findUnique.mockResolvedValue({
      id: "o1",
      status: "PAID",
      tier: "deep",
      user: { deletedAt: null },
    });

    await processDodoEvent(SUCCEEDED);

    expect(prismaMock.$transaction).not.toHaveBeenCalled();
    expect(txMock.job.create).not.toHaveBeenCalled();
    expect(track).not.toHaveBeenCalled();
  });

  it("does not queue a second job when a concurrent delivery already made the transition", async () => {
    prismaMock.order.findUnique.mockResolvedValue({
      id: "o1",
      status: "AWAITING_PAYMENT",
      tier: "deep",
      user: { deletedAt: null },
    });
    txMock.order.updateMany.mockResolvedValue({ count: 0 });

    await processDodoEvent(SUCCEEDED);

    expect(txMock.job.create).not.toHaveBeenCalled();
    expect(writeAudit).not.toHaveBeenCalled();
    expect(track).not.toHaveBeenCalled();
    expect(afterCallbacks).toHaveLength(0);
  });

  it("records the payment on an erased account but queues no generation and no dispatch", async () => {
    prismaMock.order.findUnique.mockResolvedValue({
      id: "o1",
      status: "AWAITING_PAYMENT",
      tier: "deep",
      user: { deletedAt: new Date("2026-10-20T00:00:00.000Z") },
    });

    await processDodoEvent(SUCCEEDED);

    // Accounting stays correct…
    expect(txMock.order.updateMany).toHaveBeenCalledWith(
      expect.objectContaining({ data: expect.objectContaining({ status: "PAID" }) }),
    );
    expect(writeAudit).toHaveBeenCalledWith(
      txMock,
      expect.objectContaining({ entity: "order", entityId: "o1", action: "paid" }),
    );
    // …but nothing is generated for a person who asked to be erased.
    expect(txMock.job.create).not.toHaveBeenCalled();
    expect(afterCallbacks).toHaveLength(0);
  });
});

describe("processDodoEvent — refunds and failures", () => {
  it("marks a refunded order once", async () => {
    prismaMock.order.findUnique.mockResolvedValue({ id: "o1", status: "PAID" });

    await processDodoEvent({ type: "refund.succeeded", data: { metadata: { order_id: "o1" } } });

    expect(txMock.order.update).toHaveBeenCalledWith({
      where: { id: "o1" },
      data: { status: "REFUNDED" },
    });
    expect(writeAudit).toHaveBeenCalledWith(
      txMock,
      expect.objectContaining({ entity: "order", entityId: "o1", action: "refund" }),
    );
  });

  it("records a failed payment without cancelling the order", async () => {
    await processDodoEvent({ type: "payment.failed", data: { metadata: { order_id: "o1" } } });

    expect(audit).toHaveBeenCalledWith(
      expect.objectContaining({
        entity: "order",
        entityId: "o1",
        after: expect.objectContaining({ paymentState: "payment.failed" }),
      }),
    );
    expect(prismaMock.order.findUnique).not.toHaveBeenCalled();
  });

  it("ignores an unrecognised event type", async () => {
    await expect(processDodoEvent({ type: "payment.processing" })).resolves.toBe("payment.processing");
    expect(prismaMock.order.findUnique).not.toHaveBeenCalled();
    expect(audit).not.toHaveBeenCalled();
  });
});
