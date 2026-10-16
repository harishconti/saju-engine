import Link from "next/link";
import { Badge, badgeToneForOrder, Card, CardContent, EmptyState, PageHeader } from "@/components/ui";
import { ResumeCheckoutButton } from "@/components/dashboard/resume-checkout";
import { NewOrderButton } from "@/components/dashboard/shell";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { ORDER_STATUS_LABEL, formatDate, formatUSD } from "@/lib/format";
import { tierFor } from "@/lib/tiers";

export const dynamic = "force-dynamic";
export const metadata = { title: "Purchases" };

export default async function OrdersPage() {
  const user = await requireUser();

  const orders = await prisma.order.findMany({
    where: { userId: user.id },
    orderBy: { createdAt: "desc" },
    include: {
      profileA: { select: { label: true } },
      profileB: { select: { label: true } },
      reports: { select: { id: true, status: true, version: true }, orderBy: { version: "desc" } },
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Purchases"
        title="Orders"
        description="Every order and its payment state. Reports live on the Reports page."
        actions={<NewOrderButton />}
      />

      {orders.length === 0 ? (
        <Card>
          <CardContent className="py-6">
            <EmptyState
              title="No purchases yet"
              description="You can start with the free snapshot, or order a full reading straight away."
              action={
                <div className="flex flex-wrap justify-center gap-2">
                  <Link href="/sample" className="inline-flex h-11 items-center rounded-md border border-border px-4 text-sm">
                    Free snapshot
                  </Link>
                  <Link
                    href="/reports/new"
                    className="inline-flex h-11 items-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground"
                  >
                    Order a reading
                  </Link>
                </div>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-4">
            <div className="divide-y divide-border">
              {orders.map((o) => {
                const tier = tierFor(o.kind, o.tier);
                const who =
                  o.kind === "COMPAT" && o.profileB
                    ? `${o.profileA.label} × ${o.profileB.label}`
                    : o.profileA.label;
                const latest = o.reports[0];

                return (
                  <div
                    key={o.id}
                    className="flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-display text-lg">{tier?.name ?? "Saju reading"}</span>
                        <Badge tone={badgeToneForOrder(o.status)}>
                          {ORDER_STATUS_LABEL[o.status] ?? o.status}
                        </Badge>
                        {latest ? <Badge tone="muted">report v{latest.version}</Badge> : null}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        For <span className="text-foreground">{who}</span> · {formatUSD(o.priceCents)} ·
                        ordered {formatDate(o.createdAt)}
                        {o.paidAt ? ` · paid ${formatDate(o.paidAt)}` : ""}
                      </p>
                    </div>

                    <div className="flex shrink-0 flex-wrap items-center gap-2">
                      {o.status === "AWAITING_PAYMENT" ? (
                        <ResumeCheckoutButton orderId={o.id} />
                      ) : null}
                      {latest ? (
                        <Link
                          href={`/dashboard/reports/${latest.id}`}
                          className="inline-flex h-9 items-center rounded-md border border-border px-3 text-sm hover:bg-muted/60"
                        >
                          View reading
                        </Link>
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </>
  );
}
