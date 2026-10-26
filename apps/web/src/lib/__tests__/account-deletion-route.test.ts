import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-24 (owner decision D7, 2026-10-26): a pending deletion is supposed to disable sign-in.
 * `getCurrentUser` is the one place every server gate reads identity, so an account with a
 * `pending` `DeletionRequest` is treated as signed out there.
 *
 * That creates a second problem this route has to solve: the docs promise deletion is
 * "cancellable any time before it completes", and a visitor who cannot sign in cannot reach the
 * account page to cancel. So the route accepts a live session for the two operations that only
 * concern the pending request itself — reading it (so the login page can say why) and cancelling
 * it — and for nothing else. Creating a new deletion still requires a real signed-in user.
 */

const { getCurrentUser, getSessionUserId, prismaMock, txMock, audit, rateLimit } = vi.hoisted(() => {
  const txMock = {
    deletionRequest: {
      create: vi.fn(),
      update: vi.fn(),
    },
  };
  return {
    getCurrentUser: vi.fn(),
    getSessionUserId: vi.fn(),
    audit: vi.fn(async () => ({})),
    rateLimit: vi.fn(async () => undefined),
    txMock,
    prismaMock: {
      deletionRequest: { findFirst: vi.fn() },
      $transaction: vi.fn(async (fn: (tx: typeof txMock) => Promise<unknown>) => fn(txMock)),
    },
  };
});

vi.mock("@/lib/auth", () => ({ getCurrentUser, getSessionUserId, requireUser: vi.fn() }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/audit", () => ({ audit, writeAudit: vi.fn(async () => ({})) }));
vi.mock("@/lib/ratelimit", () => ({
  rateLimit,
  WINDOW: { minute: 60_000, hour: 3_600_000, day: 86_400_000 },
}));

const { GET, DELETE } = await import("@/app/api/account/deletion/route");

function req(): Request {
  return new Request("https://app.test/api/account/deletion");
}

const PENDING = { id: "d1", status: "pending", scheduledFor: new Date("2026-11-25T00:00:00.000Z") };

beforeEach(() => {
  vi.clearAllMocks();
  getCurrentUser.mockResolvedValue({ id: "u1", name: "A", email: "a@b.c", role: "USER" });
  getSessionUserId.mockResolvedValue(null);
});

describe("GET /api/account/deletion — the pending-deletion session (AU-24)", () => {
  it("lets a blocked session see the request that is blocking it", async () => {
    // The login page needs this: credentials verify, the server treats the account as signed out,
    // and the visitor is shown *why* plus a way to cancel.
    getCurrentUser.mockResolvedValue(null);
    getSessionUserId.mockResolvedValue("u1");
    prismaMock.deletionRequest.findFirst.mockResolvedValue(PENDING);

    const res = await GET(req(), undefined as never);

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.pendingDeletion).toBe(true);
    expect(body.deletion).toMatchObject({ id: "d1", status: "pending" });
    expect(prismaMock.deletionRequest.findFirst).toHaveBeenCalledWith({
      where: { userId: "u1", status: "pending" },
    });
  });

  it("answers 401 for a session with no pending request — being blocked is not a way in", async () => {
    getCurrentUser.mockResolvedValue(null);
    getSessionUserId.mockResolvedValue("u1");
    prismaMock.deletionRequest.findFirst.mockResolvedValue(null);

    const res = await GET(req(), undefined as never);

    expect(res.status).toBe(401);
    expect(((await res.json()) as Record<string, unknown>).code).toBe("UNAUTHORIZED");
  });

  it("still answers 401 with no session at all", async () => {
    getCurrentUser.mockResolvedValue(null);
    getSessionUserId.mockResolvedValue(null);

    const res = await GET(req(), undefined as never);

    expect(res.status).toBe(401);
    expect(prismaMock.deletionRequest.findFirst).not.toHaveBeenCalled();
  });

  it("keeps the ordinary signed-in shape for a live account", async () => {
    prismaMock.deletionRequest.findFirst.mockResolvedValue(PENDING);

    const res = await GET(req(), undefined as never);

    const body = (await res.json()) as Record<string, unknown>;
    expect(body.deletion).toMatchObject({ id: "d1" });
    expect(body.pendingDeletion).toBeUndefined();
    expect(prismaMock.deletionRequest.findFirst).toHaveBeenCalledWith({
      where: { userId: "u1" },
      orderBy: { requestedAt: "desc" },
    });
  });
});

describe("DELETE /api/account/deletion — cancelling while blocked (AU-24)", () => {
  it("lets the blocked session cancel its own pending deletion", async () => {
    // "Cancellable any time before it completes" (docs/webapp/10) must survive the sign-in block,
    // or the block would be irreversible from the customer's side.
    getCurrentUser.mockResolvedValue(null);
    getSessionUserId.mockResolvedValue("u1");
    prismaMock.deletionRequest.findFirst.mockResolvedValue(PENDING);
    txMock.deletionRequest.update.mockResolvedValue({ id: "d1", status: "cancelled" });

    const res = await DELETE(req(), undefined as never);

    expect(res.status).toBe(200);
    expect(((await res.json()) as Record<string, unknown>).deletion).toMatchObject({ status: "cancelled" });
    expect(txMock.deletionRequest.update).toHaveBeenCalledWith({
      where: { id: "d1" },
      data: { status: "cancelled" },
    });
  });

  it("refuses a session that has nothing pending", async () => {
    getCurrentUser.mockResolvedValue(null);
    getSessionUserId.mockResolvedValue("u1");
    prismaMock.deletionRequest.findFirst.mockResolvedValue(null);

    const res = await DELETE(req(), undefined as never);

    expect(res.status).toBe(401);
    expect(txMock.deletionRequest.update).not.toHaveBeenCalled();
  });
});
