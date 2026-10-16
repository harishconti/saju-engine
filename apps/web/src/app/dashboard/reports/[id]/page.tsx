import Link from "next/link";
import { notFound } from "next/navigation";
import { Alert, Badge, buttonClasses, Card, CardContent, KeyValue, PageHeader, Stat } from "@/components/ui";
import { ReportStatusBadge } from "@/components/dashboard/report-row";
import { DeleteReportButton } from "@/components/dashboard/report-actions";
import {
  DayMasterBadge,
  ElementBalanceBars,
  ElementBalanceWheel,
  FourPillarsChart,
} from "@/components/viz";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { elementCountsFrom, parseChartSummary } from "@/lib/chart";
import { describeBirth } from "@/lib/birth";
import {
  AUDIO_STATUS_HELP,
  AUDIO_STATUS_LABEL,
  REPORT_STATUS_HELP,
  formatBytes,
  formatDate,
  formatDateTime,
} from "@/lib/format";
import { tierFor } from "@/lib/tiers";

export const dynamic = "force-dynamic";

export default async function ReportDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = await requireUser();

  // Scoped by userId: another user's report is a 404, not a 403 (existence is not disclosed).
  const report = await prisma.report.findFirst({
    where: { id, userId: user.id },
    include: {
      profileA: true,
      profileB: true,
      deliveries: { orderBy: { createdAt: "asc" } },
      order: { select: { id: true, priceCents: true, currency: true, paidAt: true } },
    },
  });

  if (!report) notFound();

  const tier = tierFor(report.kind, report.tier);
  const chart = parseChartSummary(report.profileA.chartJson);
  const counts = elementCountsFrom(chart);
  const canDownload = report.status === "DELIVERED";

  const siblings = report.orderId
    ? await prisma.report.findMany({
        where: { orderId: report.orderId, id: { not: report.id } },
        orderBy: { version: "desc" },
        select: { id: true, version: true, status: true, createdAt: true },
      })
    : [];

  const who =
    report.kind === "COMPAT" && report.profileB
      ? `${report.profileA.label} × ${report.profileB.label}`
      : report.profileA.label;

  return (
    <>
      <div className="text-sm">
        <Link href="/dashboard/reports" className="text-muted-foreground hover:text-foreground">
          ← All readings
        </Link>
      </div>

      <PageHeader
        eyebrow={`v${report.version} · ordered ${formatDate(report.createdAt)}`}
        title={tier?.name ?? "Saju reading"}
        description={
          <>
            For <span className="text-foreground">{who}</span> · {REPORT_STATUS_HELP[report.status]}
          </>
        }
        actions={
          <>
            <ReportStatusBadge status={report.status} />
            {canDownload ? (
              <a href={`/api/reports/${report.id}/download`} className={buttonClasses("primary", "md")} download>
                Download PDF
              </a>
            ) : null}
          </>
        }
      />

      {report.status === "FAILED" ? (
        <Alert tone="danger" title="This reading didn't complete">
          Something went wrong producing it. We&apos;re on it, and you haven&apos;t been charged twice. If you
          don&apos;t hear from us, reply to your order email.
        </Alert>
      ) : null}

      {report.status === "SUPERSEDED" ? (
        <Alert tone="neutral" title="A newer version exists">
          This reading was replaced by a newer version, usually after a correction or a reviewer override.
          You keep access to what you received.
        </Alert>
      ) : null}

      {!canDownload ? (
        <Alert tone="warning" title="Not downloadable yet">
          Every paid reading is reviewed by a person before it&apos;s sent. You can download it here, and
          from the email link, once it&apos;s delivered.
        </Alert>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Pages" value={report.pageCount ?? "—"} />
        <Stat label="Size" value={formatBytes(report.bytes)} />
        <Stat label="Delivered" value={report.deliveredAt ? formatDate(report.deliveredAt) : "—"} />
        <Stat
          label="Price"
          value={report.order ? `$${(report.order.priceCents / 100).toFixed(2)}` : "Free"}
        />
      </section>

      {chart ? (
        <Card>
          <CardContent className="space-y-5 py-6">
            <h2 className="font-display text-xl">The chart this reading is built from</h2>
            <FourPillarsChart pillars={chart.pillars} animate={false} />
            <div className="flex flex-col items-center gap-6 sm:flex-row">
              <ElementBalanceWheel counts={counts} size={140} />
              <div className="w-full flex-1 space-y-4">
                <DayMasterBadge
                  char={chart.dayMaster.char}
                  element={chart.dayMaster.element ?? null}
                  polarity={chart.dayMaster.polarity ?? null}
                />
                <ElementBalanceBars counts={counts} />
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {report.audioStatus !== "NONE" ? (
        <Card>
          <CardContent className="space-y-3 py-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="font-display text-xl">Audio summary</h2>
              <Badge
                tone={
                  report.audioStatus === "READY"
                    ? "success"
                    : report.audioStatus === "FAILED"
                      ? "danger"
                      : "warning"
                }
              >
                {AUDIO_STATUS_LABEL[report.audioStatus] ?? report.audioStatus}
              </Badge>
            </div>

            {report.audioStatus === "READY" ? (
              <>
                <audio controls preload="none" className="w-full" src={`/api/reports/${report.id}/audio`}>
                  Your browser cannot play this audio. You can download the MP3 instead.
                </audio>
                <div className="flex flex-wrap items-center gap-3">
                  <a
                    href={`/api/reports/${report.id}/audio?disposition=attachment`}
                    className={buttonClasses("outline", "sm")}
                    download
                  >
                    Download the MP3
                  </a>
                  <span className="text-xs text-muted-foreground">
                    {formatBytes(report.audioBytes)}
                    {report.audioReadyAt ? ` · ready ${formatDate(report.audioReadyAt)}` : ""}
                  </span>
                </div>
              </>
            ) : null}

            <p className="text-sm text-muted-foreground">{AUDIO_STATUS_HELP[report.audioStatus]}</p>

            {report.status !== "DELIVERED" ? (
              <p className="text-xs text-muted-foreground">
                The audio is recorded from the finished reading, so it is prepared after the written
                report is sent.
              </p>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardContent className="py-5">
          <h2 className="pb-2 font-display text-xl">Birth details used</h2>
          <dl className="grid gap-x-8 sm:grid-cols-2">
            <KeyValue label="Person" value={report.profileA.label} />
            <KeyValue label="Name" value={report.profileA.fullName} />
            <KeyValue
              label="Birth"
              value={describeBirth({
                birthDate: report.profileA.birthDate,
                birthTime: report.profileA.birthTime,
                city: report.profileA.city,
                country: report.profileA.country,
                timeKnown: report.profileA.timeKnown,
              })}
            />
            <KeyValue label="Timezone" value={report.profileA.timezone ?? "offset only"} />
            {report.profileB ? (
              <>
                <KeyValue label="Partner" value={report.profileB.label} />
                <KeyValue
                  label="Partner birth"
                  value={describeBirth({
                    birthDate: report.profileB.birthDate,
                    birthTime: report.profileB.birthTime,
                    city: report.profileB.city,
                    country: report.profileB.country,
                    timeKnown: report.profileB.timeKnown,
                  })}
                />
              </>
            ) : null}
          </dl>
          <p className="pt-3 text-xs text-muted-foreground">
            Wrong details?{" "}
            <Link href="/dashboard/profiles" className="underline hover:text-foreground">
              Correct them
            </Link>{" "}
            and order a fresh reading — we keep the old one so you can compare.
          </p>
        </CardContent>
      </Card>

      {report.deliveries.length > 0 ? (
        <Card>
          <CardContent className="py-5">
            <h2 className="pb-2 font-display text-xl">Delivery</h2>
            <dl>
              {report.deliveries.map((d) => (
                <KeyValue
                  key={d.id}
                  label={
                    d.channel === "EMAIL"
                      ? d.kind === "audio"
                        ? "Email (audio)"
                        : "Email (report)"
                      : "Saved to your profile"
                  }
                  value={
                    <span className="text-muted-foreground">
                      {d.channel === "EMAIL" ? (d.to ?? "—") : formatDateTime(d.createdAt)} · {d.status}
                    </span>
                  }
                />
              ))}
            </dl>
          </CardContent>
        </Card>
      ) : null}

      {siblings.length > 0 ? (
        <Card>
          <CardContent className="py-5">
            <h2 className="pb-2 font-display text-xl">Other versions</h2>
            <ul className="space-y-2 text-sm">
              {siblings.map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-4 border-b border-border py-2 last:border-0">
                  <Link href={`/dashboard/reports/${s.id}`} className="hover:text-primary">
                    Version {s.version} · {formatDate(s.createdAt)}
                  </Link>
                  <ReportStatusBadge status={s.status} />
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 border-t border-border pt-5">
        <DeleteReportButton reportId={report.id} />
        <span className="text-xs text-muted-foreground">
          Deleting removes the PDF from storage. Your purchase record stays on file.
        </span>
      </div>
    </>
  );
}
