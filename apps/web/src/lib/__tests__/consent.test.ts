import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Consent is the lawful basis for the sensitive category (birth date/time/place), so this check is
 * what the privacy policy's "recorded before any birth data is collected" actually rests on. It
 * previously rested on a best-effort browser call and nothing else — the first real signup produced
 * a user with no `ConsentRecord`, and the account page displayed the required consent as already
 * granted on top of that.
 */

const mocks = vi.hoisted(() => ({ prisma: { consentRecord: { findFirst: vi.fn() } } }));
vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));

const { hasActiveServiceConsent } = await import("../consent");

beforeEach(() => {
  mocks.prisma.consentRecord.findFirst.mockReset();
});

describe("hasActiveServiceConsent", () => {
  it("is FALSE when there is no record at all — the case that shipped", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue(null);
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("is TRUE for a live grant of the service purpose", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      withdrawnAt: null,
      purposes: { service: true, service_messages: false },
    });
    expect(await hasActiveServiceConsent("u1")).toBe(true);
  });

  it("is FALSE once withdrawn, so withdrawal needs no second code path", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      withdrawnAt: new Date(),
      purposes: { service: true },
    });
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("is FALSE when the service purpose itself is withheld", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      withdrawnAt: null,
      purposes: { service: false, service_messages: true },
    });
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("is FALSE for a malformed purposes object rather than defaulting to allowed", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({ withdrawnAt: null, purposes: null });
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("reads the MOST RECENT record, so a later withdrawal wins", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      withdrawnAt: null,
      purposes: { service: true },
    });
    await hasActiveServiceConsent("u1");
    expect(mocks.prisma.consentRecord.findFirst).toHaveBeenCalledWith(
      expect.objectContaining({
        where: { userId: "u1" },
        orderBy: { grantedAt: "desc" },
      }),
    );
  });
});
