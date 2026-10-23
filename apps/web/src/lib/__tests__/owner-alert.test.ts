/**
 * The "a reading is waiting" ping.
 *
 * Two rules keep it from becoming noise, and both are locked here:
 *  - **one message per batch.** Three orders in a minute is one ping, not three — a queue that
 *    already has a reading in it is a queue the owner knows about;
 *  - **it can never affect a delivery.** A mail failure is swallowed and reported as "not sent".
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const { prismaMock, sendEmail } = vi.hoisted(() => ({
  prismaMock: {
    report: { count: vi.fn(), update: vi.fn(), findFirst: vi.fn() },
  },
  sendEmail: vi.fn(),
}));

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/email", () => ({ sendEmail }));

import { notifyOwnerNewReview } from "@/lib/owner-alert";

const INPUT = {
  reportId: "r1",
  tierName: "The Deep Destiny Report",
  profileLabel: "Me",
  waitedMinutes: 0,
  queueDepth: 1,
};

beforeEach(() => {
  vi.clearAllMocks();
  process.env.ADMIN_EMAILS = "owner@cosmicsaju.com";
  prismaMock.report.count.mockResolvedValue(1);
  prismaMock.report.findFirst.mockResolvedValue(null);
  prismaMock.report.update.mockResolvedValue({});
  sendEmail.mockResolvedValue({ ok: true, id: "m1" });
});

describe("notifyOwnerNewReview", () => {
  it("emails the owner when a reading is waiting", async () => {
    const sent = await notifyOwnerNewReview(INPUT);
    expect(sent).toBe(true);
    expect(sendEmail).toHaveBeenCalledTimes(1);
    const call = sendEmail.mock.calls[0]![0] as { to: string; subject: string; text: string };
    expect(call.to).toContain("owner@cosmicsaju.com");
    expect(call.subject).toContain("waiting for review");
    expect(call.text).toContain("/admin/reports/r1");
  });

  it("says nothing when a reading is already waiting — one ping per batch", async () => {
    prismaMock.report.count.mockResolvedValue(3); // more than one reading in the queue
    const sent = await notifyOwnerNewReview(INPUT);
    expect(sent).toBe(false);
    expect(sendEmail).not.toHaveBeenCalled();
  });

  it("never pings twice for the same reading", async () => {
    await notifyOwnerNewReview(INPUT);
    // The second call sees ownerAlertedAt set.
    prismaMock.report.findFirst.mockResolvedValue({ id: "r1" });
    const second = await notifyOwnerNewReview(INPUT);
    expect(sendEmail).toHaveBeenCalledTimes(1);
    expect(second).toBe(false);
  });

  it("marks the reading as alerted so a retry cannot double-ping", async () => {
    await notifyOwnerNewReview(INPUT);
    expect(prismaMock.report.update).toHaveBeenCalledWith({
      where: { id: "r1" },
      data: { ownerAlertedAt: expect.any(Date) },
    });
  });

  it("never throws when the mail fails", async () => {
    sendEmail.mockRejectedValue(new Error("resend is down"));
    const sent = await notifyOwnerNewReview(INPUT);
    expect(sent).toBe(false);
  });

  it("does nothing when no owner address is configured", async () => {
    delete process.env.ADMIN_EMAILS;
    delete process.env.EMAIL_FROM;
    const sent = await notifyOwnerNewReview(INPUT);
    expect(sent).toBe(false);
    expect(sendEmail).not.toHaveBeenCalled();
  });
});
