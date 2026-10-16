import { describe, expect, it } from "vitest";

import { artifactSummary, previewKeyFor } from "@/lib/report-artifacts";

/**
 * The console tells the reviewer what approving will publish, and the preview signs one object.
 *
 * Both matter because the answer is not always "both": compatibility readings have no web mode yet,
 * and reports generated before the web document existed carry only a PDF. Getting this wrong means
 * either telling the reviewer the client will get a reading that does not exist, or hiding a preview
 * that does.
 */

const both = { pdfKey: "reports/u/o/r.pdf", htmlKey: "reports/u/o/r.html" };
const pdfOnly = { pdfKey: "reports/u/o/r.pdf", htmlKey: null };
const htmlOnly = { pdfKey: null, htmlKey: "reports/u/o/r.html" };
const neither = { pdfKey: null, htmlKey: null };

describe("artifactSummary", () => {
  it("reports both artefacts and leads with the reading", () => {
    const summary = artifactSummary(both);
    expect(summary.reading).toBe(true);
    expect(summary.pdf).toBe(true);
    expect(summary.previewable).toBe("html");
    expect(summary.approvalNote).toMatch(/reading/);
    expect(summary.approvalNote).toMatch(/PDF/);
  });

  it("says a compatibility reading is PDF-only, and why", () => {
    const summary = artifactSummary(pdfOnly, "COMPAT");
    expect(summary.pdf).toBe(true);
    expect(summary.reading).toBe(false);
    expect(summary.previewable).toBe("pdf");
    expect(summary.approvalNote).toMatch(/PDF-only/);
  });

  it("tells the reviewer a single-chart report predates the reading, and what to do", () => {
    const summary = artifactSummary(pdfOnly, "SINGLE");
    expect(summary.approvalNote).toMatch(/before the reading existed/);
    expect(summary.approvalNote).toMatch(/Regenerate/);
    expect(summary.previewable).toBe("pdf");
  });

  it("does not claim a PDF that is missing", () => {
    const summary = artifactSummary(htmlOnly);
    expect(summary.reading).toBe(true);
    expect(summary.pdf).toBe(false);
    expect(summary.previewable).toBe("html");
    expect(summary.approvalNote).not.toMatch(/and the PDF/);
  });

  it("refuses to imply anything is deliverable when nothing is", () => {
    const summary = artifactSummary(neither);
    expect(summary.previewable).toBeNull();
    expect(summary.approvalNote).toMatch(/Generate/);
  });
});

describe("previewKeyFor", () => {
  it("signs the reading by default kind and the PDF on request", () => {
    expect(previewKeyFor(both, "html")).toEqual({ key: both.htmlKey });
    expect(previewKeyFor(both, "pdf")).toEqual({ key: both.pdfKey });
  });

  it("gives a 404 with an actionable message when the reading is missing", () => {
    const problem = previewKeyFor(pdfOnly, "html");
    expect(problem).toMatchObject({ status: 404, code: "NO_WEB_DOCUMENT" });
    if ("message" in problem) expect(problem.message).toMatch(/preview the PDF/);
  });

  it("gives a 409 when the PDF is missing", () => {
    expect(previewKeyFor(htmlOnly, "pdf")).toMatchObject({ status: 409, code: "NO_ARTIFACT" });
  });
});
