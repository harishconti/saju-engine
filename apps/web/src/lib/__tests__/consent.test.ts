import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Consent is the lawful basis for the sensitive category (birth date/time/place), so this check is
 * what the privacy policy's "recorded before any birth data is collected" actually rests on. It
 * previously rested on a best-effort browser call and nothing else — the first real signup produced
 * a user with no `ConsentRecord`, and the account page displayed the required consent as already
 * granted on top of that.
 *
 * AU-23 (2026-10-26 audit): a record for an older policy version was treated as consent to the
 * current text. Versions are now compared; an old record satisfies nothing until the user
 * re-consents, and re-consent writes the current version.
 */

const mocks = vi.hoisted(() => ({
  prisma: {
    consentRecord: { findFirst: vi.fn(), create: vi.fn() },
  },
}));
vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));

const { POLICY_VERSION, hasActiveServiceConsent, recordInitialServiceConsent, requireActiveServiceConsent } =
  await import("../consent");
const { ApiError } = await import("@/lib/api");

beforeEach(() => {
  vi.clearAllMocks();
});

describe("hasActiveServiceConsent", () => {
  it("is FALSE when there is no record at all — the case that shipped", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue(null);
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("is TRUE for a live grant of the service purpose at the current policy version", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: POLICY_VERSION,
      withdrawnAt: null,
      purposes: { service: true, service_messages: false },
    });
    expect(await hasActiveServiceConsent("u1")).toBe(true);
  });

  it("is FALSE once withdrawn, so withdrawal needs no second code path", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: POLICY_VERSION,
      withdrawnAt: new Date(),
      purposes: { service: true },
    });
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("is FALSE when the service purpose itself is withheld", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: POLICY_VERSION,
      withdrawnAt: null,
      purposes: { service: false, service_messages: true },
    });
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("is FALSE for a malformed purposes object rather than defaulting to allowed", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: POLICY_VERSION,
      withdrawnAt: null,
      purposes: null,
    });
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("is FALSE for a record written to an older policy version (AU-23)", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: "2025-01-01",
      withdrawnAt: null,
      purposes: { service: true, service_messages: false },
    });
    expect(await hasActiveServiceConsent("u1")).toBe(false);
  });

  it("reads the MOST RECENT record, so a later withdrawal wins", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: POLICY_VERSION,
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

describe("recordInitialServiceConsent (AU-22)", () => {
  it("writes ONE grant of the service purpose at the current policy version", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue(null);
    mocks.prisma.consentRecord.create.mockResolvedValue({ id: "c1" });

    await recordInitialServiceConsent("u1");

    expect(mocks.prisma.consentRecord.create).toHaveBeenCalledTimes(1);
    expect(mocks.prisma.consentRecord.create).toHaveBeenCalledWith({
      data: {
        userId: "u1",
        policyVersion: POLICY_VERSION,
        purposes: { service: true, service_messages: false },
      },
    });
  });

  it("does nothing when a record already exists", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({ id: "c1" });

    await recordInitialServiceConsent("u1");

    expect(mocks.prisma.consentRecord.create).not.toHaveBeenCalled();
  });

  it("never re-grants consent a user has withdrawn", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({ id: "c1" });

    await recordInitialServiceConsent("u1");

    expect(mocks.prisma.consentRecord.create).not.toHaveBeenCalled();
  });
});

describe("requireActiveServiceConsent (AU-24, D7)", () => {
  it("passes when the latest record grants the service purpose", async () => {
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: POLICY_VERSION,
      withdrawnAt: null,
      purposes: { service: true },
    });

    await expect(requireActiveServiceConsent("u1")).resolves.toBeUndefined();
  });

  it("refuses with a stable, actionable code when consent has been withdrawn", async () => {
    // D7 turns withdrawal into enforcement. The route layer answers this 409 as-is; the UI keys on
    // the code to point at the account page, so the code and status must not drift.
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: POLICY_VERSION,
      withdrawnAt: new Date(),
      purposes: { service: true },
    });

    await expect(requireActiveServiceConsent("u1")).rejects.toMatchObject({
      status: 409,
      code: "CONSENT_REQUIRED",
    });
  });

  it("uses the same version-aware check as every other consent gate", async () => {
    // The point of reusing `hasActiveServiceConsent`: a grant to an older policy text is not
    // consent to what the app does now, and this gate must not be more lenient than the rest.
    mocks.prisma.consentRecord.findFirst.mockResolvedValue({
      policyVersion: "2025-01-01",
      withdrawnAt: null,
      purposes: { service: true },
    });

    await expect(requireActiveServiceConsent("u1")).rejects.toBeInstanceOf(ApiError);
  });
});
