import Link from "next/link";
import { Alert, Badge, Card, CardContent, EmptyState, PageHeader, Stat } from "@/components/ui";
import { ReportStatusBadge } from "@/components/dashboard/report-row";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { timeAgo } from "@/lib/format";
import { tierFor } from "@/lib/tiers";
import { jobStats } from "@/lib/queue";

export const dynamic = "force-dynamic";
export const metadata = { title: "Review queue" };

export default async function AdminQueuePage() {
  const admin = await requireAdmin();

  const [queue, failedJobs, stats] = await Promise.all([
    prisma.report.findMany({
      where: { status: { in: ["DRAFT_READY", "IN_REVIEW"] } },
      orderBy: { createdAt: "asc" },
      include: {
        user: { select: { email: true, name: true } },
        profileA: { select: { label: true, fullName: true } },
        profileB: { select: { label: true } },
        order: { select: { id: true, priceCents: true, paidAt: true } },
      },
    }),
    prisma.job.findMany({
      where: { state: "FAILED" },
      orderBy: { finishedAt: "desc" },
      take: 5,
      include: { order: { select: { id: true, tier: true, kind: true } } },
    }),
    jobStats(),
  ]);

  const oldest = queue[0]?.createdAt ?? null;
  const oldestAgeHours = oldest ? Math.floor((Date.now() - oldest.getTime()) / 3_600_000) : 0;
  const queuedJobs = stats.find((s) => s.state === "QUEUED")?.count ?? 0;

  return (
    <>
      <PageHeader
        eyebrow="Admin"
        title="Review queue"
        description="Every paid report waits here until a human checks it. Approved readings are emailed and filed in the client's profile."
      />

      <Alert tone="danger" title="SLA risk if the oldest item exceeds 24 hours">
        The promise on the pricing page is a human review before delivery. The age of the oldest item below
        is the number that tells you whether that promise is still true — it is the constraint on how many
        readings you can sell.
      </Alert>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Awaiting review"
          value={queue.length}
          hint={queue.length === 0 ? "queue is clear" : "oldest is the number that matters"}
          tone={queue.length > 0 ? "warning" : "success"}
        />
        <Stat
          label="Oldest item"
          value={oldest ? timeAgo(oldest) : "—"}
          hint={oldest ? (oldestAgeHours > 24 ? "over 24h — at risk" : "within target") : "nothing waiting"}
          tone={oldestAgeHours > 24 ? "danger" : oldestAgeHours > 12 ? "warning" : "success"}
        />
        <Stat label="Jobs queued" value={queuedJobs} hint={queuedJobs > 5 ? "dispatcher may be behind" : "healthy"} tone={queuedJobs > 5 ? "warning" : "default"} />
        <Stat
          label="Failed jobs"
          value={stats.find((s) => s.state === "FAILED")?.count ?? 0}
          hint="any is worth a look"
          tone={(stats.find((s) => s.state === "FAILED")?.count ?? 0) > 0 ? "danger" : "default"}
        />
      </section>

      <Card>
        <CardContent className="py-4">
          <h2 className="pb-2 font-display text-xl">Waiting on you</h2>
          {queue.length === 0 ? (
            <EmptyState title="Nothing to review" description="Queue is clear. New paid orders appear here automatically." />
          ) : (
            <div className="divide-y divide-border">
              {queue.map((r) => {
                const tier = tierFor(r.kind, r.tier);
                const who =
                  r.kind === "COMPAT" && r.profileB
                    ? `${r.profileA.label} × ${r.profileB.label}`
                    : r.profileA.label;
                return (
                  <div key={r.id} className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link href={`/admin/reports/${r.id}`} className="font-display text-lg hover:text-primary">
                          {tier?.name ?? "Saju reading"}
                        </Link>
                        <ReportStatusBadge status={r.status} />
                        <Badge tone="muted">{r.kind}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {who} · {r.user.email} · ordered {timeAgo(r.createdAt)}
                        {r.order?.priceCents != null ? ` · $${(r.order.priceCents / 100).toFixed(2)}` : ""}
                      </p>
                    </div>
                    <Link
                      href={`/admin/reports/${r.id}`}
                      className="inline-flex h-9 shrink-0 items-center rounded-md bg-primary px-3 text-sm font-semibold text-primary-foreground"
                    >
                      Review
                    </Link>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {failedJobs.length > 0 ? (
        <Card>
          <CardContent className="py-4">
            <h2 className="pb-2 font-display text-xl">Recent failures</h2>
            <ul className="space-y-2 text-sm">
              {failedJobs.map((j) => (
                <li key={j.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-border py-2 last:border-0">
                  <span className="font-mono text-xs">
                    {j.kind} · order {j.orderId.slice(0, 8)} · attempts {j.attempts}/{j.maxAttempts}
                  </span>
                  <span className="text-muted-foreground">{j.lastError ?? "unknown"}</span>
                  <span className="text-xs text-muted-foreground">{timeAgo(j.finishedAt ?? j.createdAt)}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <p className="text-xs text-muted-foreground">Signed in as {admin.email}.</p>
    </>
  );
}
