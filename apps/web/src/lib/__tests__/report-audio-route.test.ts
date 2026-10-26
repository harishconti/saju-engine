import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-26 (2026-10-26 audit): the audio GET was already gated on `DELIVERED`, but its POST sibling —
 * "the narration text, for anyone who would rather read it (and for audit)" — returned the
 * unreviewed script for any draft. Both verbs now serve only a delivered report's reviewed text.
 */

const { requireUser, prismaMock, presignGetUrl } = vi.hoisted(() => ({
  requireUser: vi.fn(),
  prismaMock: { report: { findFirst: vi.fn() } },
  presignGetUrl: vi.fn(async () => "https://r2.test/signed"),
}));

vi.mock("@/lib/auth", () => ({ requireUser }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/r2", () => ({ presignGetUrl }));

const { GET, POST } = await import("@/app/api/reports/[id]/audio/route");

type Ctx = { params: Promise<{ id: string }> };

function request(query = ""): Request {
  return new Request(`https://app.test/api/reports/r1/audio${query}`);
}

function ctx(): Ctx {
  return { params: Promise.resolve({ id: "r1" }) };
}

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", name: "Visitor", email: "v@example.com", role: "USER" });
});

describe("GET /api/reports/{id}/audio — pre-delivery exposure (AU-26)", () => {
  it("refuses a narration file for an unreviewed report and signs no URL", async () => {
    prismaMock.report.findFirst.mockResolvedValue({
      status: "DRAFT_READY",
      audioStatus: "READY",
      audioKey: "reports/u/o/r1.mp3",
    });

    const res = await GET(request(), ctx());

    expect(res.status).toBe(409);
    expect((await res.json()) as Record<string, unknown>).toMatchObject({ code: "REPORT_NOT_READY" });
    expect(presignGetUrl).not.toHaveBeenCalled();
  });

  it("serves a delivered, ready audio file", async () => {
    prismaMock.report.findFirst.mockResolvedValue({
      status: "DELIVERED",
      audioStatus: "READY",
      audioKey: "reports/u/o/r1.mp3",
    });

    const res = await GET(request(), ctx());

    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toBe("https://r2.test/signed");
  });
});

describe("POST /api/reports/{id}/audio — the narration script (AU-26)", () => {
  it("refuses to return an unreviewed script", async () => {
    prismaMock.report.findFirst.mockResolvedValue({
      status: "DRAFT_READY",
      audioStatus: "PENDING",
      script: "UNREVIEWED NARRATION",
    });

    const res = await POST(request(), ctx());

    expect(res.status).toBe(409);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.code).toBe("REPORT_NOT_READY");
    expect(body.script).toBeUndefined();
  });

  it("returns the reviewed script once the report is delivered", async () => {
    prismaMock.report.findFirst.mockResolvedValue({
      status: "DELIVERED",
      audioStatus: "READY",
      script: "Reviewed narration.",
    });

    const res = await POST(request(), ctx());

    expect(res.status).toBe(200);
    const body = (await res.json()) as Record<string, unknown>;
    expect(body.script).toBe("Reviewed narration.");
    expect(body.audioStatus).toBe("READY");
  });
});
