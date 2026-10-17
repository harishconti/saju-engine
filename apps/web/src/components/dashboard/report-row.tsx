import Link from "next/link";
import { Badge, buttonClasses, type BadgeTone } from "@/components/ui";
import { REPORT_STATUS_HELP, REPORT_STATUS_LABEL, formatBytes, formatDate, timeAgo } from "@/lib/format";
import { tierNameFor } from "@/lib/tiers";

/** Status vocabulary → display. Kept in one place so every screen agrees. */

const STATUS_TONE: Record<string, BadgeTone> = {
  DRAFT_READY: "warning",
  IN_REVIEW: "warning",
  APPROVED: "primary",
  DELIVERED: "success",
  SUPERSEDED: "muted",
  FAILED: "danger",
};

export function ReportStatusBadge({ status }: { status: string }) {
  return <Badge tone={STATUS_TONE[status] ?? "neutral"}>{REPORT_STATUS_LABEL[status] ?? status}</Badge>;
}

export interface ReportRowData {
  id: string;
  kind: "SINGLE" | "COMPAT";
  tier: string;
  status: string;
  version: number;
  createdAt: Date;
  deliveredAt: Date | null;
  bytes: number | null;
  profileA: { label: string };
  profileB?: { label: string } | null;
}

export function ReportRow({ report, showHelp = false }: { report: ReportRowData; showHelp?: boolean }) {
  const name = tierNameFor(report.kind, report.tier);
  const who =
    report.kind === "COMPAT" && report.profileB
      ? `${report.profileA.label} × ${report.profileB.label}`
      : report.profileA.label;
  const canDownload = report.status === "DELIVERED";

  return (
    <div className="flex flex-col gap-3 border-b border-border py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <Link href={`/dashboard/reports/${report.id}`} className="font-display text-lg hover:text-primary">
            {name}
          </Link>
          <ReportStatusBadge status={report.status} />
          {report.version > 1 ? <Badge tone="muted">v{report.version}</Badge> : null}
        </div>
        <p className="text-sm text-muted-foreground">
          For <span className="text-foreground">{who}</span> · ordered {formatDate(report.createdAt)}
          {report.bytes ? ` · ${formatBytes(report.bytes)}` : ""}
        </p>
        {showHelp ? (
          <p className="max-w-xl text-xs text-muted-foreground">{REPORT_STATUS_HELP[report.status]}</p>
        ) : null}
      </div>

      {/* One action per row: the list is a library, not a download manager. "Details" opens the
          report, and that page is where the reading lives (Read your reading → Save → PDF). The old
          per-format button here was also wrong — it asked the download route with no `kind`, which
          defaults to the web document, so it handed back the reading labelled as the PDF. */}
      <div className="flex shrink-0 items-center gap-2">
        <Link href={`/dashboard/reports/${report.id}`} className={buttonClasses("ghost", "sm")}>
          Details
        </Link>
        {canDownload ? null : (
          <span className="text-xs text-muted-foreground" title={REPORT_STATUS_HELP[report.status]}>
            {timeAgo(report.deliveredAt ?? report.createdAt)}
          </span>
        )}
      </div>
    </div>
  );
}
