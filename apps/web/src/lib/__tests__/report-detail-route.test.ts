import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-26 (2026-10-26 audit): `GET /api/reports/{id}` returned the whole `Report` row to its owner
 * regardless of review state — including the narration `script` and the stored engine payload for a
 * reading a human had not yet released. A client could read their unreviewed reading through the
 * API before the review promise said they could.
 *
 * The route is now gated on `DELIVERED` and answers an explicit allow-list, so a future field (or
 * the narration script) cannot reach a client merely by existing on the model.
 */

const { requireUser, prismaMock } = vi.hoisted(() => ({
  requireUser: vi.fn(),
  prismaMock: { report: { findFirst: vi.fn() } },
}));

vi.mock("@/lib/auth", () => ({ requireUser }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));

const { GET } = await import("@/app/api/reports/[id]/route");

const ALLOWED_KEYS = [
  "bytes",
  "createdAt",
  "deliveredAt",
  "id",
  "kind",
  "pageCount",
  "reviewedAt",
  "status",
  "tier",
  "version",
].sort();

function request(): Request {
  return new Request("https://app.test/api/reports/r1");
}

function ctx(id = "r1") {
  return { params: Promise.resolve({ id }) };
}

const DELIVERED_ROW = {
  id: "r1",
  kind: "SINGLE",
  tier: "deep",
  version: 2,
  status: "DELIVERED",
  pageCount: 24,
  bytes: 4096,
  createdAt: new Date("2026-10-01T10:00:00.000Z"),
  deliveredAt: new Date("2026-10-02T10:00:00.000Z"),
  reviewedAt: new Date("2026-10-02T09:00:00.000Z"),
};

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", name: "Visitor", email: "v@example.com", role: "USER" });
});

describe("GET /api/reports/{id} — pre-delivery exposure (AU-26)", () => {
  it("refuses a report that has not been delivered, with a code", async () => {
    prismaMock.report.findFirst.mockResolvedValue({ status: "DRAFT_READY" });

    const res = await GET(request(), ctx());

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("REPORT_NOT_READY");
    expect(body.report).toBeUndefined();
  });

  it("asks the database only for the allow-listed columns, never the script", async () => {
    prismaMock.report.findFirst.mockResolvedValue(DELIVERED_ROW);

    await GET(request(), ctx());

    const args = prismaMock.report.findFirst.mock.calls[0]![0] as {
      where: Record<string, unknown>;
      select: Record<string, unknown>;
    };
    expect(args.where).toEqual({ id: "r1", userId: "u1" });
    expect(Object.keys(args.select).sort()).toEqual(ALLOWED_KEYS);
    expect(args.select).not.toHaveProperty("script");
    expect(args.select).not.toHaveProperty("enginePayload");
    expect(args.select).not.toHaveProperty("mdKey");
  });

  it("returns only the allow-listed fields for a delivered report", async () => {
    prismaMock.report.findFirst.mockResolvedValue(DELIVERED_ROW);

    const res = await GET(request(), ctx());

    expect(res.status).toBe(200);
    const body = (await res.json()) as { report: Record<string, unknown> };
    expect(Object.keys(body.report).sort()).toEqual(ALLOWED_KEYS);
    expect(body.report).toMatchObject({ id: "r1", status: "DELIVERED", tier: "deep" });
  });

  it("does not disclose another user's report", async () => {
    prismaMock.report.findFirst.mockResolvedValue(null);

    const res = await GET(request(), ctx());

    expect(res.status).toBe(404);
    expect((await res.json()) as Record<string, unknown>).toMatchObject({ code: "NOT_FOUND" });
  });
});
