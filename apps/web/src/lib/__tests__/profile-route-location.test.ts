/**
 * AU-34 (2026-10-26 audit): a profile edit that changes only the city must still re-resolve it with
 * the country the profile already stores.
 *
 * The request carries a city name and (for a picker choice) a country code — but the stored profile
 * keeps `country` as a *name*. `resolveBirthLocation` declared that field and then ignored it, so an
 * edit to a bare, ambiguous city ("Cambridge") was re-resolved with no country at all and failed.
 * The route now passes the stored country through, and this test pins the call it makes.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  requireUser: vi.fn(async () => ({ id: "u1", email: "owner@example.com" })),
  hasActiveServiceConsent: vi.fn(async () => true),
  rateLimit: vi.fn(async () => undefined),
  resolveBirthLocation: vi.fn((_input: { city: string; countryCode?: string | null; country?: string | null }) => ({
    city: "Cambridge",
    country: "United Kingdom",
    countryCode: "GB",
    latitude: 52.2,
    longitude: 0.12,
    timezone: "Europe/London",
  })),
  validateBirth: vi.fn(() => ({ ok: false, code: "INVALID_BIRTH_DATA", message: "stop here" })),
  birthUtcOffset: vi.fn(() => 0),
  findFirst: vi.fn(),
}));

vi.mock("@/lib/auth", () => ({ requireUser: mocks.requireUser, getCurrentUser: mocks.requireUser }));
vi.mock("@/lib/consent", () => ({
  hasActiveServiceConsent: mocks.hasActiveServiceConsent,
  CONSENT_REQUIRED_MESSAGE: "Please accept the privacy policy in your account settings.",
}));
vi.mock("@/lib/ratelimit", () => ({
  rateLimit: mocks.rateLimit,
  WINDOW: { minute: 60_000, hour: 3_600_000, day: 86_400_000 },
}));
vi.mock("@/lib/prisma", () => ({
  prisma: { profile: { findFirst: mocks.findFirst, findUnique: vi.fn(), update: vi.fn() } },
}));
vi.mock("@/lib/audit", () => ({ writeAudit: vi.fn(), audit: vi.fn() }));
vi.mock("@/lib/birth", () => ({
  resolveBirthLocation: mocks.resolveBirthLocation,
  validateBirth: mocks.validateBirth,
  birthUtcOffset: mocks.birthUtcOffset,
}));
vi.mock("@/lib/chart-compute", () => ({ computeAndStoreChart: vi.fn() }));
vi.mock("@/lib/profile-scrub", () => ({ SCRUBBED_PROFILE: {} }));

const { PATCH } = await import("@/app/api/profiles/[id]/route");

beforeEach(() => {
  vi.clearAllMocks();
  mocks.requireUser.mockResolvedValue({ id: "u1", email: "owner@example.com" });
  mocks.hasActiveServiceConsent.mockResolvedValue(true);
  mocks.findFirst.mockResolvedValue({
    id: "p1",
    userId: "u1",
    city: "Cambridge",
    country: "United Kingdom",
    countryCode: null,
    fullName: "Test Person",
    birthDate: new Date("1990-01-01T00:00:00Z"),
    birthTime: "12:00",
    timeKnown: true,
    timezone: "Europe/London",
    utcOffset: 0,
    latitude: 52.2,
    longitude: 0.12,
  });
  mocks.validateBirth.mockReturnValue({ ok: false, code: "INVALID_BIRTH_DATA", message: "stop here" });
});

describe("PATCH /api/profiles/[id] — city-only edit (AU-34)", () => {
  it("passes the profile's stored country to the resolver", async () => {
    const req = new Request("https://app.test/api/profiles/p1", {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ city: "Cambridge" }),
    });

    const res = await PATCH(req, { params: Promise.resolve({ id: "p1" }) } as never);

    // The route stops at validation in this test; what matters is the resolver's input.
    expect(res.status).toBe(422);
    expect(mocks.resolveBirthLocation).toHaveBeenCalledTimes(1);
    expect(mocks.resolveBirthLocation.mock.calls[0]![0]).toMatchObject({
      city: "Cambridge",
      country: "United Kingdom",
    });
  });

  it("lets an explicit country code win over the stored name", async () => {
    const req = new Request("https://app.test/api/profiles/p1", {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ city: "Cambridge", countryCode: "CA" }),
    });

    await PATCH(req, { params: Promise.resolve({ id: "p1" }) } as never);

    expect(mocks.resolveBirthLocation.mock.calls[0]![0]).toMatchObject({
      city: "Cambridge",
      countryCode: "CA",
    });
  });
});
