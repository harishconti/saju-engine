import { Prisma } from "@prisma/client";
import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-27 (2026-10-26 audit): deleting a profile only set `deletedAt`. The birth date, time and
 * place — the sensitive category the whole consent machinery exists for — stayed in the row
 * forever. A soft-deleted profile must end up as free of birth data as an erased one, so it uses
 * the SAME scrub definition as account erasure (Task 4), not a second, drifting copy.
 */

const { requireUser, prismaMock, writeAudit, txMock } = vi.hoisted(() => {
  const txMock = {
    profile: {
      update: vi.fn(async (_args: { where: { id: string }; data: Record<string, unknown> }) => ({})),
      findFirst: vi.fn(async () => null),
    },
  };
  return {
    requireUser: vi.fn(),
    writeAudit: vi.fn(async () => ({})),
    txMock,
    prismaMock: {
      profile: { findFirst: vi.fn() },
      $transaction: vi.fn(async (fn: (t: typeof txMock) => Promise<unknown>) => fn(txMock)),
    },
  };
});

vi.mock("@/lib/auth", () => ({ requireUser }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/audit", () => ({ writeAudit }));
vi.mock("@/lib/consent", () => ({
  hasActiveServiceConsent: vi.fn(async () => true),
  CONSENT_REQUIRED_MESSAGE: "consent required",
}));
vi.mock("@/lib/chart-compute", () => ({ computeAndStoreChart: vi.fn() }));

const { DELETE } = await import("@/app/api/profiles/[id]/route");

const NOW_BEFORE = Date.now();

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", name: "Test", email: "t@test", role: "CLIENT" });
  prismaMock.profile.findFirst.mockResolvedValue({ id: "p1", userId: "u1" });
});

describe("DELETE /api/profiles/[id] — soft delete scrubs the person (AU-27)", () => {
  it("blanks the birth fields, name, label and derived chart in the same write as deletedAt", async () => {
    const res = await DELETE(
      new Request("https://app.test/api/profiles/p1", { method: "DELETE" }),
      { params: Promise.resolve({ id: "p1" }) },
    );

    expect(res.status).toBe(200);
    expect(txMock.profile.update).toHaveBeenCalledTimes(1);
    const data = (txMock.profile.update.mock.calls[0]![0] as { data: Record<string, unknown> }).data;

    expect(data).toMatchObject({
      label: "Deleted profile",
      fullName: "Deleted profile",
      birthDate: new Date(0),
      birthTime: "00:00",
      timezone: null,
      utcOffset: null,
      city: "Deleted",
      country: "Deleted",
      latitude: null,
      longitude: null,
      timeKnown: false,
      chartJson: Prisma.DbNull,
      chartComputedAt: null,
      isDefault: false,
    });
    expect(data.deletedAt).toBeInstanceOf(Date);
    expect((data.deletedAt as Date).getTime()).toBeGreaterThanOrEqual(NOW_BEFORE);
    // The old, leaking shape only marked the row — it must not be possible again.
    expect(data).not.toEqual({ deletedAt: expect.any(Date), isDefault: false });
  });
});
