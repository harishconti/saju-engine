/**
 * Which artefacts a report actually has, and what approving one will deliver.
 *
 * The reviewer approves **both** artefacts (owner decision, 2026-10-16): the web document is what
 * the client reads and can save as one file, and the PDF is the keepsake. But not every report has
 * both — a compatibility reading renders through its own two-chart pipeline, which has no web mode
 * yet, and any report generated before the web document existed carries only a PDF. The console must
 * therefore say what it is about to publish rather than implying both are always there.
 *
 * Kept as a plain function with no Prisma or React in scope so the copy and the branches can be
 * tested directly; the console renders what this returns and the preview route uses `previewKeyFor`
 * to pick the object to sign.
 */

export type ArtifactKind = "pdf" | "html";

export interface ArtifactReport {
  pdfKey: string | null;
  htmlKey: string | null;
}

export interface ArtifactSummary {
  /** A web document exists, so the client will read it and can download it as one file. */
  reading: boolean;
  /** A PDF exists, so there is a keepsake to download and print. */
  pdf: boolean;
  /** The artefact to open first in the console, or null when there is nothing to open. */
  previewable: ArtifactKind | null;
  /** One sentence for the reviewer: what pressing Approve actually publishes. */
  approvalNote: string;
}

export function artifactSummary(
  report: ArtifactReport,
  /** `COMPAT` readings have no web mode yet, which is a different reason from "too old to have one". */
  kind: "SINGLE" | "COMPAT" = "SINGLE",
): ArtifactSummary {
  const reading = Boolean(report.htmlKey);
  const pdf = Boolean(report.pdfKey);

  if (reading && pdf) {
    return {
      reading,
      pdf,
      previewable: "html",
      approvalNote:
        "Approving delivers the reading (the web page, which the client can also save as one file) and the PDF.",
    };
  }
  if (pdf && kind === "COMPAT") {
    return {
      reading,
      pdf,
      previewable: "pdf",
      approvalNote:
        "Approving delivers the PDF. Compatibility readings are PDF-only for now — the web document covers single-chart readings.",
    };
  }
  if (pdf) {
    return {
      reading,
      pdf,
      previewable: "pdf",
      approvalNote:
        "Approving delivers the PDF only: this report was generated before the reading existed. Regenerate to add it.",
    };
  }
  if (reading) {
    return {
      reading,
      pdf,
      previewable: "html",
      approvalNote:
        "Approving delivers the reading. There is no PDF for this report yet — regenerate if the client expects one.",
    };
  }
  return {
    reading,
    pdf,
    previewable: null,
    approvalNote: "No artefact yet. Generate the report before approving.",
  };
}

export interface PreviewTarget {
  key: string;
}

export interface PreviewProblem {
  status: number;
  code: string;
  message: string;
}

/** The object to sign for an inline preview, or why there is none. */
export function previewKeyFor(
  report: ArtifactReport,
  kind: ArtifactKind,
): PreviewTarget | PreviewProblem {
  const key = kind === "html" ? report.htmlKey : report.pdfKey;
  if (key) return { key };

  if (kind === "html") {
    return {
      status: 404,
      code: "NO_WEB_DOCUMENT",
      message:
        "This report has no web version — preview the PDF, or regenerate to add the reading.",
    };
  }
  return { status: 409, code: "NO_ARTIFACT", message: "This report has no PDF yet — generate it first." };
}

export function isPreviewProblem(value: PreviewTarget | PreviewProblem): value is PreviewProblem {
  return "status" in value;
}
