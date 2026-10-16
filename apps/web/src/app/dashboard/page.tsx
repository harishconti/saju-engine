import Link from "next/link";
import { Alert, buttonClasses, Card, CardContent, EmptyState, PageHeader, Stat } from "@/components/ui";
import { NewOrderButton } from "@/components/dashboard/shell";
import { ReportRow } from "@/components/dashboard/report-row";
import {
  DayMasterBadge,
  ElementBalanceBars,
  ElementBalanceWheel,
  ElementLegend,
  FourPillarsChart,
} from "@/components/viz";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { elementCountsFrom, parseChartSummary } from "@/lib/chart";
import { describeBirth } from "@/lib/birth";

export const dynamic = "force-dynamic";
export const metadata = { title: "Overview" };

export default async function DashboardOverview() {
  const user = await requireUser();

  const [profiles, reports, deliveredCount, reviewCount] = await Promise.all([
    prisma.profile.findMany({
      where: { userId: user.id, deletedAt: null },
      orderBy: [{ isDefault: "desc" }, { createdAt: "asc" }],
    }),
    prisma.report.findMany({
      where: { userId: user.id },
      orderBy: { createdAt: "desc" },
      take: 4,
      include: { profileA: { select: { label: true } }, profileB: { select: { label: true } } },
    }),
    prisma.report.count({ where: { userId: user.id, status: "DELIVERED" } }),
    prisma.report.count({ where: { userId: user.id, status: { in: ["DRAFT_READY", "IN_REVIEW"] } } }),
  ]);

  const primary = profiles.find((p) => p.isDefault) ?? profiles[0] ?? null;
  const chart = primary ? parseChartSummary(primary.chartJson) : null;
  const counts = chart ? elementCountsFrom(chart) : null;

  const firstName = user.name.split(" ")[0];

  return (
    <>
      <PageHeader
        eyebrow="Dashboard"
        title={`Hello, ${firstName}`}
        description="Your charts, readings, and purchases in one place."
        actions={<NewOrderButton />}
      />

      <section aria-label="Summary" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="People" value={profiles.length} hint={profiles.length === 1 ? "1 profile" : "profiles saved"} />
        <Stat label="Delivered" value={deliveredCount} hint="readings you can download" tone={deliveredCount > 0 ? "success" : "default"} />
        <Stat
          label="In review"
          value={reviewCount}
          hint={reviewCount > 0 ? "being checked before sending" : "nothing waiting"}
          tone={reviewCount > 0 ? "warning" : "default"}
        />
        <Stat label="Reports total" value={deliveredCount + reviewCount} />
      </section>

      {/* Primary chart */}
      {!primary ? (
        <Card>
          <CardContent className="py-6">
            <EmptyState
              title="Add your birth details to see your chart"
              description="We need your date, time, and place of birth to derive the four pillars. It takes about a minute, and you'll see the chart before anything is ordered."
              action={
                <Link href="/dashboard/profiles" className={buttonClasses("primary", "md")}>
                  Add your birth details
                </Link>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="space-y-5 py-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="eyebrow">
                  {primary.label} · {primary.isDefault ? "primary profile" : "profile"}
                </p>
                <h2 className="mt-1 font-display text-2xl">{primary.fullName}</h2>
                <p className="text-sm text-muted-foreground">
                  {describeBirth({
                    birthDate: primary.birthDate,
                    birthTime: primary.birthTime,
                    city: primary.city,
                    country: primary.country,
                    timeKnown: primary.timeKnown,
                  })}
                </p>
              </div>
              <Link href="/dashboard/profiles" className={buttonClasses("ghost", "sm")}>
                Edit details
              </Link>
            </div>

            {chart ? (
              <>
                {chart.caveats?.length ? (
                  <Alert tone="warning" title="Confidence note">
                    <ul className="space-y-1">
                      {chart.caveats.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </Alert>
                ) : null}

                <FourPillarsChart pillars={chart.pillars} />

                <div className="flex flex-col items-center gap-6 sm:flex-row">
                  <ElementBalanceWheel counts={counts ?? {}} size={150} />
                  <div className="w-full flex-1 space-y-4">
                    <DayMasterBadge
                      char={chart.dayMaster.char}
                      element={chart.dayMaster.element ?? null}
                      polarity={chart.dayMaster.polarity ?? null}
                    />
                    <ElementBalanceBars counts={counts ?? {}} />
                    <ElementLegend counts={counts ?? {}} />
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-md border border-border px-3 py-2.5">
                    <p className="eyebrow">Strength</p>
                    <p className="text-sm">{chart.strength ?? "—"}</p>
                  </div>
                  <div className="rounded-md border border-border px-3 py-2.5">
                    <p className="eyebrow">Favourable element</p>
                    <p className="text-sm">
                      {chart.favorableElement ?? "—"}
                      {chart.favorableProvenance ? (
                        <span className="ml-1 text-xs text-muted-foreground">({chart.favorableProvenance})</span>
                      ) : null}
                    </p>
                  </div>
                  <div className="rounded-md border border-border px-3 py-2.5">
                    <p className="eyebrow">Lucky cues</p>
                    <p className="text-sm">
                      {chart.luckyCues
                        ? [
                            chart.luckyCues.colors?.join(", "),
                            chart.luckyCues.direction,
                            chart.luckyCues.numbers?.join(", "),
                          ]
                            .filter(Boolean)
                            .join(" · ") || "—"
                        : "—"}
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <Alert tone="neutral" title="Chart not computed yet">
                Your details are saved, but the chart hasn&apos;t been derived. This happens automatically as
                soon as the report engine is reachable — you don&apos;t need to do anything.
              </Alert>
            )}

            <div className="flex flex-wrap gap-2 border-t border-border pt-4">
              <Link href="/reports/new" className={buttonClasses("primary", "md")}>
                Order a reading
              </Link>
              <Link href="/dashboard/profiles" className={buttonClasses("outline", "md")}>
                Add someone for a compatibility reading
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent reports */}
      <Card>
        <CardContent className="py-5">
          <div className="flex items-center justify-between gap-4 pb-2">
            <h2 className="font-display text-xl">Recent readings</h2>
            {reports.length > 0 ? (
              <Link href="/dashboard/reports" className={buttonClasses("ghost", "sm")}>
                See all
              </Link>
            ) : null}
          </div>

          {reports.length === 0 ? (
            <EmptyState
              title="No readings yet"
              description="Your free chart snapshot is the fastest way to see what a reading looks like. It takes a minute and costs nothing."
              action={
                <Link href="/sample" className={buttonClasses("primary", "md")}>
                  Get your free snapshot
                </Link>
              }
            />
          ) : (
            <div>
              {reports.map((r) => (
                <ReportRow
                  key={r.id}
                  report={{
                    id: r.id,
                    kind: r.kind,
                    tier: r.tier,
                    status: r.status,
                    version: r.version,
                    createdAt: r.createdAt,
                    deliveredAt: r.deliveredAt,
                    bytes: r.bytes,
                    profileA: r.profileA,
                    profileB: r.profileB,
                  }}
                  showHelp
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        Signed in as {user.email}. Manage your data on the{" "}
        <Link href="/dashboard/account" className="underline hover:text-foreground">
          account page
        </Link>
        .
      </p>
    </>
  );
}
