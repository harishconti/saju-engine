import Link from "next/link";
import { notFound } from "next/navigation";
import { Alert, Card, CardContent, KeyValue, PageHeader, Stat } from "@/components/ui";
import { ReportStatusBadge } from "@/components/dashboard/report-row";
import { ReviewConsole } from "@/components/dashboard/review-console";
import { artifactSummary } from "@/lib/report-artifacts";
import {
  DayMasterBadge,
  ElementBalanceBars,
  ElementBalanceWheel,
  FourPillarsChart,
} from "@/components/viz";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { elementCountsFrom, parseChartSummary } from "@/lib/chart";
import { describeBirth } from "@/lib/birth";
import { formatBytes, formatDateTime, timeAgo } from "@/lib/format";
import { tierFor } from "@/lib/tiers";

export const dynamic = "force-dynamic";
export const metadata = { title: "Review a reading" };

export default async function AdminReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  await requireAdmin();

  const report = await prisma.report.findUnique({
    where: { id },
    include: {
      user: { select: { id: true, email: true, name: true } },
      profileA: true,
      profileB: true,
      order: {
        select: {
          id: true,
          priceCents: true,
          paidAt: true,
          favorableOverrideA: true,
          favorableOverrideB: true,
          jobs: { orderBy: { createdAt: "desc" }, take: 5 },
        },
      },
      deliveries: { orderBy: { createdAt: "desc" } },
    },
  });

  if (!report) notFound();

  // What approving this will publish, from the tested helper: the reading and the PDF, unless this
  // report predates the reading (every tier renders one now, compatibility included).
  const artifacts = artifactSummary({ pdfKey: report.pdfKey, htmlKey: report.htmlKey });

  const tier = tierFor(report.kind, report.tier);
  const chartA = parseChartSummary(report.profileA.chartJson);
  const chartB = report.profileB ? parseChartSummary(report.profileB.chartJson) : null;

  const overrideA = report.order?.favorableOverrideA ?? null;
  const overrideB = report.order?.favorableOverrideB ?? null;

  const otherVersions = report.orderId
    ? await prisma.report.count({ where: { orderId: report.orderId } })
    : 1;

  return (
    <>
      <div className="text-sm">
        <Link href="/admin" className="text-muted-foreground hover:text-foreground">
          ← Review queue
        </Link>
      </div>

      <PageHeader
        eyebrow={`${report.kind} · v${report.version} · ordered ${timeAgo(report.createdAt)}`}
        title={tier?.name ?? "Saju reading"}
        description={
          report.kind === "COMPAT" && report.profileB
            ? `${report.profileA.fullName} × ${report.profileB.fullName}`
            : report.profileA.fullName
        }
        actions={<ReportStatusBadge status={report.status} />}
      />

      {report.status === "DELIVERED" ? (
        <Alert tone="success" title="Already delivered">
          This reading has been sent. Delivered reports are immutable — a change produces a new version.
        </Alert>
      ) : null}
      {report.status === "SUPERSEDED" ? (
        <Alert tone="neutral" title="Superseded">
          A newer version exists for this order. Reviewing this one further is probably pointless.
        </Alert>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Pages" value={report.pageCount ?? "—"} />
        <Stat label="Size" value={formatBytes(report.bytes)} />
        <Stat label="Versions" value={otherVersions} hint={otherVersions > 1 ? "older ones are kept" : "first version"} />
        <Stat label="Price" value={report.order ? `$${(report.order.priceCents / 100).toFixed(2)}` : "Free"} />
      </section>

      <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        {/* Left: the chart and provenance */}
        <div className="space-y-5">
          <Card>
            <CardContent className="space-y-5 py-5">
              <h2 className="font-display text-xl">Chart — {report.profileA.label}</h2>
              {chartA ? (
                <>
                  <FourPillarsChart pillars={chartA.pillars} animate={false} />
                  {chartA.caveats?.length ? (
                    <Alert tone="warning" title="Confidence notes">
                      <ul className="space-y-1">
                        {chartA.caveats.map((c) => (
                          <li key={c}>{c}</li>
                        ))}
                      </ul>
                    </Alert>
                  ) : null}
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
                    <ElementBalanceWheel counts={elementCountsFrom(chartA)} size={130} />
                    <div className="flex-1 space-y-3">
                      <DayMasterBadge
                        char={chartA.dayMaster.char}
                        element={chartA.dayMaster.element ?? null}
                        polarity={chartA.dayMaster.polarity ?? null}
                      />
                      <ElementBalanceBars counts={elementCountsFrom(chartA)} />
                      <dl className="pt-1">
                        <KeyValue label="Engine strength" value={chartA.strength ?? "—"} />
                        <KeyValue
                          label="Engine favourable"
                          value={
                            <>
                              {chartA.favorableElement ?? "—"}
                              {chartA.favorableProvenance ? (
                                <span className="ml-1 text-xs text-muted-foreground">
                                  ({chartA.favorableProvenance})
                                </span>
                              ) : null}
                            </>
                          }
                        />
                        <KeyValue
                          label="Reader override"
                          value={overrideA ? <span className="text-primary">{overrideA}</span> : "none"}
                        />
                      </dl>
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No chart summary stored for this profile.</p>
              )}
            </CardContent>
          </Card>

          {report.profileB ? (
            <Card>
              <CardContent className="space-y-5 py-5">
                <h2 className="font-display text-xl">Chart — {report.profileB.label}</h2>
                {chartB ? (
                  <>
                    <FourPillarsChart pillars={chartB.pillars} animate={false} />
                    <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
                      <ElementBalanceWheel counts={elementCountsFrom(chartB)} size={130} />
                      <div className="flex-1 space-y-3">
                        <DayMasterBadge
                          char={chartB.dayMaster.char}
                          element={chartB.dayMaster.element ?? null}
                          polarity={chartB.dayMaster.polarity ?? null}
                        />
                        <ElementBalanceBars counts={elementCountsFrom(chartB)} />
                        <dl className="pt-1">
                          <KeyValue
                            label="Reader override"
                            value={overrideB ? <span className="text-primary">{overrideB}</span> : "none"}
                          />
                        </dl>
                      </div>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">No chart summary stored.</p>
                )}
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardContent className="py-5">
              <h2 className="pb-2 font-display text-xl">Birth data as entered</h2>
              <dl className="grid gap-x-8 sm:grid-cols-2">
                <KeyValue label="Person" value={`${report.profileA.label} (${report.profileA.fullName})`} />
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
                <KeyValue label="Time known" value={report.profileA.timeKnown ? "yes" : "no — hour uncertain"} />
                {report.profileB ? (
                  <>
                    <KeyValue label="Partner" value={`${report.profileB.label} (${report.profileB.fullName})`} />
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
                If these are wrong, fix them on the profile and tell the client — a regenerate cannot fix
                bad input.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="py-5">
              <h2 className="pb-2 font-display text-xl">Provenance</h2>
              <dl>
                <KeyValue label="Client" value={report.user.email} />
                <KeyValue label="Order" value={report.orderId?.slice(0, 12) ?? "none (sample)"} />
                <KeyValue label="Paid" value={report.order?.paidAt ? formatDateTime(report.order.paidAt) : "—"} />
                <KeyValue label="Engine version" value={report.engineVersion ?? "—"} />
                <KeyValue label="Chart hash" value={<span className="font-mono text-xs">{report.chartHash?.slice(0, 16) ?? "—"}…</span>} />
                <KeyValue label="PDF sha256" value={<span className="font-mono text-xs">{report.sha256?.slice(0, 16) ?? "—"}…</span>} />
              </dl>

              {report.order?.jobs.length ? (
                <>
                  <h3 className="pt-4 pb-1 font-display text-base">Jobs</h3>
                  <ul className="space-y-1 text-xs text-muted-foreground">
                    {report.order.jobs.map((j) => (
                      <li key={j.id} className="flex justify-between gap-3">
                        <span className="font-mono">
                          {j.kind} · {j.state} · {j.attempts}/{j.maxAttempts}
                        </span>
                        <span>{timeAgo(j.finishedAt ?? j.createdAt)}</span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
            </CardContent>
          </Card>
        </div>

        {/* Right: the decision */}
        <div className="lg:sticky lg:top-6 lg:self-start">
          <Card>
            <CardContent className="py-5">
              <ReviewConsole
                reportId={report.id}
                kind={report.kind}
                initialOverrideA={overrideA}
                initialOverrideB={overrideB}
                chartHash={report.chartHash}
                audioStatus={report.audioStatus}
                audioError={report.audioError}
                audioPromised={report.kind === "SINGLE" && (report.tier === "deep" || report.tier === "fullmap")}
                canUpload={Boolean(report.orderId)}
                reportDelivered={report.status === "DELIVERED"}
                approvalNote={artifacts.approvalNote}
                hasHtml={artifacts.reading}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
}
