/**
 * The shared approval path.
 *
 * The human review and the 10-hour SLA release the same reading, so they must do the same
 * thing. These cases lock the parts that differ between them — and the parts that must NOT
 * differ:
 *  - a human approval records WHO reviewed it; the SLA records that nobody did;
 *  - both deliver to the profile in the same transaction, and email after the commit;
 *  - an auto-delivered deep reading holds its email back until the audio is ready.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const { prismaMock, deliverReport, enqueueAudio, tierPromisesAudio } = vi.hoisted(() => ({
  prismaMock: {
    report: {
      findUnique: vi.fn(),
      update: vi.fn(),
    },
    delivery: { create: vi.fn() },
    auditLog: { create: vi.fn() },
    $transaction: vi.fn(),
  },
  deliverReport: vi.fn(),
  enqueueAudio: vi.fn(),
  tierPromisesAudio: vi.fn(),
}));

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/email", () => ({ deliverReport }));
vi.mock("@/lib/fulfilment", () => ({ enqueueAudio }));
vi.mock("@/lib/tts", () => ({ tierPromisesAudio }));

import { approveAndDeliver, ApprovalError } from "@/lib/review";

const REPORT = {
  id: "r1",
  orderId: "o1",
  status: "DRAFT_READY" as const,
  userId: "u1",
  pdfKey: "k.pdf",
  htmlKey: "k.html",
  version: 1,
  audioStatus: "NONE" as const,
  order: { status: "PAID" as const, kind: "SINGLE" as const, tier: "essential" },
};

beforeEach(() => {
  vi.clearAllMocks();
  prismaMock.report.findUnique.mockResolvedValue(REPORT);
  prismaMock.report.update.mockResolvedValue({});
  prismaMock.delivery.create.mockResolvedValue({});
  prismaMock.$transaction.mockImplementation(async (fn: (tx: unknown) => unknown) => fn(prismaMock));
  deliverReport.mockResolvedValue(undefined);
  enqueueAudio.mockResolvedValue(false);
  tierPromisesAudio.mockReturnValue(false);
});

describe("approveAndDeliver", () => {
  it("records who reviewed it on a human approval", async () => {
    const result = await approveAndDeliver("r1", { actorId: "admin-1", outcome: "HUMAN" });

    expect(result.released).toBe(true);
    const update = prismaMock.report.update.mock.calls[0]![0] as { data: Record<string, unknown> };
    expect(update.data.reviewedBy).toBe("admin-1");
    expect(update.data.reviewOutcome).toBe("HUMAN");
    expect(update.data.slaApprovedAt).toBeNull();
    expect(update.data.status).toBe("DELIVERED");
  });

  it("records that nobody reviewed it on an SLA release", async () => {
    await approveAndDeliver("r1", { actorId: null, outcome: "SLA_AUTO" });

    const update = prismaMock.report.update.mock.calls[0]![0] as { data: Record<string, unknown> };
    expect(update.data.reviewedBy).toBeNull();
    expect(update.data.reviewOutcome).toBe("SLA_AUTO");
    expect(update.data.slaApprovedAt).toEqual(expect.any(Date));
  });

  it("delivers to the profile in the same transaction, on both paths", async () => {
    await approveAndDeliver("r1", { actorId: null, outcome: "SLA_AUTO" });
    expect(prismaMock.delivery.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({ reportId: "r1", channel: "PROFILE", status: "sent" }),
      }),
    );
  });

  it("emails the client after the commit", async () => {
    await approveAndDeliver("r1", { actorId: "admin-1", outcome: "HUMAN" });
    expect(deliverReport).toHaveBeenCalledWith("r1");
  });

  it("holds the email when an auto-delivered reading still owes its audio", async () => {
    tierPromisesAudio.mockReturnValue(true);
    prismaMock.report.findUnique.mockResolvedValue({ ...REPORT, order: { ...REPORT.order, tier: "deep" } });

    const result = await approveAndDeliver("r1", { actorId: null, outcome: "SLA_AUTO" });

    expect(result.emailHeld).toBe(true);
    expect(deliverReport).not.toHaveBeenCalled();
    const update = prismaMock.report.update.mock.calls[0]![0] as { data: Record<string, unknown> };
    expect(update.data.emailHeldForAudio).toBe(true);
  });

  it("does not hold the email for a human approval of the same tier", async () => {
    tierPromisesAudio.mockReturnValue(true);
    prismaMock.report.findUnique.mockResolvedValue({ ...REPORT, order: { ...REPORT.order, tier: "deep" } });

    const result = await approveAndDeliver("r1", { actorId: "admin-1", outcome: "HUMAN" });

    expect(result.emailHeld).toBe(false);
    expect(deliverReport).toHaveBeenCalledWith("r1");
  });

  it("does not hold the email when the audio is already there", async () => {
    tierPromisesAudio.mockReturnValue(true);
    prismaMock.report.findUnique.mockResolvedValue({
      ...REPORT,
      audioStatus: "READY" as const,
      order: { ...REPORT.order, tier: "deep" },
    });

    const result = await approveAndDeliver("r1", { actorId: null, outcome: "SLA_AUTO" });

    expect(result.emailHeld).toBe(false);
    expect(deliverReport).toHaveBeenCalledWith("r1");
  });

  it("is a no-op for a reading that was already delivered", async () => {
    prismaMock.report.findUnique.mockResolvedValue({ ...REPORT, status: "DELIVERED" as const });
    const result = await approveAndDeliver("r1", { actorId: "admin-1", outcome: "HUMAN" });
    expect(result.released).toBe(false);
    expect(prismaMock.report.update).not.toHaveBeenCalled();
  });

  it("refuses a superseded version — delivering it would send stale content", async () => {
    prismaMock.report.findUnique.mockResolvedValue({ ...REPORT, status: "SUPERSEDED" as const });
    await expect(approveAndDeliver("r1", { actorId: "admin-1", outcome: "HUMAN" })).rejects.toBeInstanceOf(
      ApprovalError,
    );
  });

  it("refuses a reading whose order is not paid", async () => {
    prismaMock.report.findUnique.mockResolvedValue({
      ...REPORT,
      order: { ...REPORT.order, status: "REFUNDED" as const },
    });
    await expect(approveAndDeliver("r1", { actorId: null, outcome: "SLA_AUTO" })).rejects.toBeInstanceOf(
      ApprovalError,
    );
  });

  it("refuses a reading with no artefact to deliver", async () => {
    prismaMock.report.findUnique.mockResolvedValue({ ...REPORT, pdfKey: null, htmlKey: null });
    await expect(approveAndDeliver("r1", { actorId: "admin-1", outcome: "HUMAN" })).rejects.toBeInstanceOf(
      ApprovalError,
    );
  });
});
