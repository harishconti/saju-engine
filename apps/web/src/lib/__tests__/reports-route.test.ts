import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-21 (2026-10-26 audit): an unknown `?status=` was cast straight into the Prisma `where`, so
 * Prisma threw and the visitor got a 500 for what is a bad request. The value is validated with
 * the same enum the schema uses, and an unknown one is a 400 in the standard `{ error, code }`
 * envelope.
 */

const { requireUser, prismaMock } = vi.hoisted(() => ({
  requireUser: vi.fn(),
  prismaMock: { report: { findMany: vi.fn() } },
}));

vi.mock("@/lib/auth", () => ({ requireUser }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));

const { GET } = await import("@/app/api/reports/route");

function request(query = ""): Request {
  return new Request(`https://app.test/api/reports${query}`);
}

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", name: "Visitor", email: "v@example.com", role: "USER", emailVerified: true });
  prismaMock.report.findMany.mockResolvedValue([]);
});

describe("GET /api/reports", () => {
  it("returns 400 for an unknown status instead of reaching Prisma", async () => {
    const res = await GET(request("?status=NOT_A_STATUS"), undefined as never);

    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ code: "INVALID_STATUS" });
    expect(prismaMock.report.findMany).not.toHaveBeenCalled();
  });

  it("returns 400 for an explicitly empty status", async () => {
    const res = await GET(request("?status="), undefined as never);

    expect(res.status).toBe(400);
    expect(prismaMock.report.findMany).not.toHaveBeenCalled();
  });

  it("filters by a known status", async () => {
    const res = await GET(request("?status=DELIVERED"), undefined as never);

    expect(res.status).toBe(200);
    expect(prismaMock.report.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ where: { userId: "u1", status: "DELIVERED" } }),
    );
  });

  it("returns everything when no status is given", async () => {
    await GET(request(), undefined as never);

    expect(prismaMock.report.findMany).toHaveBeenCalledWith(
      expect.objectContaining({ where: { userId: "u1" } }),
    );
  });
});
