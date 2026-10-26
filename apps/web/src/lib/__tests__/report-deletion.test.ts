import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-08 (2026-10-26 audit): deleting a report queued the PDF, the markdown and the audio for
 * deletion but not the web document — the reading, which is where the birth data actually is.
 * For a sample the reading is the ONLY artefact, so the delete left the whole chart in R2.
 *
 * The rule is simple and this file holds it: whatever a report stored, its deletion queues.
 */

const { prismaMock, deleteObjectOrQueue } = vi.hoisted(() => ({
  prismaMock: {
    report: { findUnique: vi.fn(), delete: vi.fn() },
  },
  deleteObjectOrQueue: vi.fn(),
}));

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/r2", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../r2")>()),
  deleteObjectOrQueue,
}));

const { deleteReportArtifacts } = await import("../fulfilment");

const KEYS = {
  pdfKey: "reports/u/o/r.pdf",
  mdKey: "reports/u/o/r.md",
  audioKey: "reports/u/o/r.mp3",
  htmlKey: "reports/u/o/r.html",
};

beforeEach(() => {
  vi.clearAllMocks();
  prismaMock.report.findUnique.mockResolvedValue(KEYS);
  prismaMock.report.delete.mockResolvedValue({});
});

describe("deleteReportArtifacts", () => {
  it("queues the HTML reading along with the PDF, markdown and audio", async () => {
    await deleteReportArtifacts("r1");

    expect(prismaMock.report.findUnique).toHaveBeenCalledWith({
      where: { id: "r1" },
      select: expect.objectContaining({ htmlKey: true }),
    });
    expect(deleteObjectOrQueue.mock.calls.map((call) => call[0])).toEqual([
      KEYS.pdfKey,
      KEYS.mdKey,
      KEYS.audioKey,
      KEYS.htmlKey,
    ]);
    expect(prismaMock.report.delete).toHaveBeenCalledWith({ where: { id: "r1" } });
  });

  it("deletes the reading for a sample, where the HTML is the only artefact", async () => {
    const sample = {
      pdfKey: null,
      mdKey: null,
      audioKey: null,
      htmlKey: "reports/anonymous/abc/sample.html",
    };
    prismaMock.report.findUnique.mockResolvedValue(sample);

    await deleteReportArtifacts("sample-1");

    expect(deleteObjectOrQueue.mock.calls.map((call) => call[0])).toEqual([sample.htmlKey]);
  });

  it("queues nothing for a missing report", async () => {
    prismaMock.report.findUnique.mockResolvedValue(null);

    await deleteReportArtifacts("gone");

    expect(deleteObjectOrQueue).not.toHaveBeenCalled();
    expect(prismaMock.report.delete).not.toHaveBeenCalled();
  });
});
