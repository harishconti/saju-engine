import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-23 (2026-10-26 audit): re-consent recorded whatever `policyVersion` the browser sent. A tab
 * left open across a policy update would therefore write consent to the *old* text and the app
 * would treat it as current. The server now owns the version: it always records `POLICY_VERSION`,
 * and a record that only matches an older version is not "unchanged" — it is superseded.
 */

const { requireUser, prismaMock, audit, rateLimit, revokeOtherSessions } = vi.hoisted(() => {
  const tx = {
    consentRecord: {
      update: vi.fn(async () => ({})),
      create: vi.fn(async () => ({
        id: "c2",
        policyVersion: "CURRENT",
        purposes: { service: true, service_messages: false },
      })),
    },
  };
  return {
    requireUser: vi.fn(),
    audit: vi.fn(async () => ({})),
    rateLimit: vi.fn(async () => undefined),
    revokeOtherSessions: vi.fn(async () => undefined),
    prismaMock: {
      consentRecord: { findFirst: vi.fn() },
      $transaction: vi.fn(async (fn: (t: typeof tx) => Promise<unknown>) => fn(tx)),
      tx,
    },
  };
});

vi.mock("@/lib/auth", () => ({ requireUser, revokeOtherSessions }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/audit", () => ({ audit }));
vi.mock("@/lib/ratelimit", () => ({
  rateLimit,
  WINDOW: { minute: 60_000, hour: 3_600_000, day: 86_400_000 },
}));

const { POST } = await import("@/app/api/account/consent/route");
const { POLICY_VERSION } = await import("@/lib/consent");

function request(body: unknown): Request {
  return new Request("https://app.test/api/account/consent", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", name: "Test", email: "t@test", role: "CLIENT" });
  prismaMock.consentRecord.findFirst.mockResolvedValue(null);
});

describe("POST /api/account/consent — the recorded version (AU-23)", () => {
  it("records the CURRENT policy version even when the client sends an old one", async () => {
    await POST(
      request({
        policyVersion: "2025-01-01",
        purposes: { service: true, service_messages: false },
      }),
      undefined as never,
    );

    expect(prismaMock.tx.consentRecord.create).toHaveBeenCalledWith({
      data: expect.objectContaining({
        userId: "u1",
        policyVersion: POLICY_VERSION,
        purposes: { service: true, service_messages: false },
      }),
    });
  });

  it("treats an old-version record as superseded, not as an unchanged consent", async () => {
    prismaMock.consentRecord.findFirst.mockResolvedValue({
      id: "c1",
      policyVersion: "2025-01-01",
      purposes: { service: true, service_messages: false },
      withdrawnAt: null,
    });

    const res = await POST(
      request({
        policyVersion: POLICY_VERSION,
        purposes: { service: true, service_messages: false },
      }),
      undefined as never,
    );
    const body = (await res.json()) as Record<string, unknown>;

    expect(body.unchanged).toBeUndefined();
    expect(prismaMock.$transaction).toHaveBeenCalledTimes(1);
    expect(prismaMock.tx.consentRecord.update).toHaveBeenCalledWith({
      where: { id: "c1" },
      data: { withdrawnAt: expect.any(Date) },
    });
    expect(prismaMock.tx.consentRecord.create).toHaveBeenCalledTimes(1);
  });

  it("treats a withdrawn row with identical purposes as a fresh grant, never 'unchanged'", async () => {
    // AU-23 follow-up: withdrawal is a later record with `withdrawnAt` set, so its purposes can
    // still match the re-grant the visitor is sending. Returning `unchanged` there would write
    // nothing and leave `hasActiveServiceConsent` false — the account page would look granted and
    // every birth-data write would be refused.
    prismaMock.consentRecord.findFirst.mockResolvedValue({
      id: "c1",
      policyVersion: POLICY_VERSION,
      purposes: { service: true, service_messages: false },
      withdrawnAt: new Date("2026-10-20T09:00:00.000Z"),
    });

    const res = await POST(
      request({
        policyVersion: POLICY_VERSION,
        purposes: { service: true, service_messages: false },
      }),
      undefined as never,
    );
    const body = (await res.json()) as Record<string, unknown>;

    expect(body.unchanged).toBeUndefined();
    expect(prismaMock.$transaction).toHaveBeenCalledTimes(1);
    // A withdrawn row has nothing left to withdraw, so no second withdrawal is written.
    expect(prismaMock.tx.consentRecord.update).not.toHaveBeenCalled();
    expect(prismaMock.tx.consentRecord.create).toHaveBeenCalledTimes(1);
  });

  it("still answers unchanged for a matching current-version record", async () => {
    prismaMock.consentRecord.findFirst.mockResolvedValue({
      id: "c1",
      policyVersion: POLICY_VERSION,
      purposes: { service: true, service_messages: false },
      withdrawnAt: null,
    });

    const res = await POST(
      request({
        policyVersion: POLICY_VERSION,
        purposes: { service: true, service_messages: false },
      }),
      undefined as never,
    );
    const body = (await res.json()) as Record<string, unknown>;

    expect(body.unchanged).toBe(true);
    expect(prismaMock.$transaction).not.toHaveBeenCalled();
  });
});

describe("POST /api/account/consent — withdrawal also ends other sessions (AU-24)", () => {
  it("revokes the other sessions when the service purpose is withdrawn", async () => {
    // D7: withdrawal is meant to stop processing. The record alone does not end a session that is
    // already open on another device, so the withdrawal signs those out too — the current one is
    // kept, because the visitor stays on the page that just recorded it.
    prismaMock.consentRecord.findFirst.mockResolvedValue({
      id: "c1",
      policyVersion: POLICY_VERSION,
      purposes: { service: true, service_messages: false },
      withdrawnAt: null,
    });
    prismaMock.tx.consentRecord.create.mockResolvedValue({
      id: "c2",
      policyVersion: POLICY_VERSION,
      purposes: { service: false, service_messages: false },
    });

    const res = await POST(
      request({ policyVersion: POLICY_VERSION, purposes: { service: false, service_messages: false } }),
      undefined as never,
    );
    const body = (await res.json()) as Record<string, unknown>;

    expect(body.withdrawnService).toBe(true);
    expect(revokeOtherSessions).toHaveBeenCalledTimes(1);
  });

  it("leaves other sessions alone when consent is granted", async () => {
    await POST(
      request({ policyVersion: POLICY_VERSION, purposes: { service: true, service_messages: false } }),
      undefined as never,
    );

    expect(revokeOtherSessions).not.toHaveBeenCalled();
  });

  it("does not revoke for the no-op 'unchanged' answer", async () => {
    prismaMock.consentRecord.findFirst.mockResolvedValue({
      id: "c1",
      policyVersion: POLICY_VERSION,
      purposes: { service: true, service_messages: false },
      withdrawnAt: null,
    });

    const res = await POST(
      request({ policyVersion: POLICY_VERSION, purposes: { service: true, service_messages: false } }),
      undefined as never,
    );

    expect(((await res.json()) as Record<string, unknown>).unchanged).toBe(true);
    expect(revokeOtherSessions).not.toHaveBeenCalled();
  });
});
