import Link from "next/link";
import { Alert, buttonClasses, Card, CardContent, EmptyState, PageHeader } from "@/components/ui";
import { ReportRow } from "@/components/dashboard/report-row";
import { CheckForUpdatesButton } from "@/components/dashboard/check-for-updates";
import { NewOrderButton } from "@/components/dashboard/shell";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";
export const metadata = { title: "Your readings" };

export default async function ReportsPage() {
  const user = await requireUser();

  const reports = await prisma.report.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
    include: { profileA: { select: { label: true } }, profileB: { select: { label: true } } },
  });

  const awaiting = reports.filter((r) => r.status === "DRAFT_READY" || r.status === "IN_REVIEW");
  const ready = reports.filter((r) => r.status === "DELIVERED");
  const other = reports.filter(
    (r) => !["DRAFT_READY", "IN_REVIEW", "DELIVERED"].includes(r.status),
  );

  const toRow = (r: (typeof reports)[number]) => ({
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
  });

  return (
    <>
      <PageHeader
        eyebrow="Your readings"
        title="Reports"
        description="Everything you've ordered, from the free snapshot to the deepest reading. Paid readings are reviewed by a person before delivery."
        actions={<NewOrderButton />}
      />

      {awaiting.length > 0 ? (
        <Alert tone="warning" title={`${awaiting.length} reading${awaiting.length === 1 ? "" : "s"} being reviewed`}>
          Every paid reading is checked by a human before it&apos;s sent. You&apos;ll get an email the moment
          it&apos;s ready — usually within a day. You can safely close this tab.
          <div className="pt-3">
            <CheckForUpdatesButton />
          </div>
        </Alert>
      ) : null}

      {reports.length === 0 ? (
        <Card>
          <CardContent className="py-6">
            <EmptyState
              title="No readings yet"
              description="Start with the free chart snapshot — it shows your four pillars, element balance, and Day Master. No account, no payment."
              action={
                <div className="flex flex-wrap justify-center gap-2">
                  <Link href="/sample" className={buttonClasses("primary", "md")}>
                    Get your free snapshot
                  </Link>
                  <Link href="/reports/new" className={buttonClasses("outline", "md")}>
                    Order a full reading
                  </Link>
                </div>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {ready.length > 0 ? (
            <Card>
              <CardContent className="py-4">
                <h2 className="pb-1 font-display text-xl">Delivered</h2>
                {ready.map((r) => (
                  <ReportRow key={r.id} report={toRow(r)} />
                ))}
              </CardContent>
            </Card>
          ) : null}

          {awaiting.length > 0 ? (
            <Card>
              <CardContent className="py-4">
                <h2 className="pb-1 font-display text-xl">In review</h2>
                {awaiting.map((r) => (
                  <ReportRow key={r.id} report={toRow(r)} showHelp />
                ))}
              </CardContent>
            </Card>
          ) : null}

          {other.length > 0 ? (
            <Card>
              <CardContent className="py-4">
                <h2 className="pb-1 font-display text-xl">Archive</h2>
                {other.map((r) => (
                  <ReportRow key={r.id} report={toRow(r)} showHelp />
                ))}
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </>
  );
}
