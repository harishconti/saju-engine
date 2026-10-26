import type { JobState, OrderKind, Prisma } from "@prisma/client";
import { prisma } from "./prisma";

/**
 * The admin recovery list for AU-02 (2026-10-26 audit).
 *
 * A paid order whose GENERATE job exhausted its attempts during the October outage has no Report,
 * so the regenerate action — which starts from a report — has nothing to act on. This is the
 * read-only query that finds those orders so an operator can retry the job from the console.
 *
 * Two exclusions, both deliberate:
 *  - an order that has a report is not a failure (it may simply be waiting for review);
 *  - an order with a live (QUEUED/RUNNING) job is already being worked on.
 *
 * A third exclusion is subtler. A paid order can legitimately have no report because the customer
 * deleted it themselves. That is not an outage loss and "retrying" it would regenerate a reading
 * the customer asked to be removed. Deletions are audited (`entity = "report"`, `action =
 * "delete"`); the link back to the order is either the order id recorded on the deletion row
 * (written from this task onward) or the report id shared with the order's own `create`/`deliver`
 * audit row. Rows written before the delete route recorded the order id have no other surviving
 * link — the report row is gone and the job never stored its id.
 *
 * A fourth exclusion is broader than any of those: an erased account (`User.deletedAt` set) keeps
 * its order rows for accounting, and after erasure those orders have no report. They must never
 * appear here, because this list's only action is "regenerate this customer's reading" — the exact
 * thing the customer asked us to destroy.
 */

export interface RecoverableOrder {
  orderId: string;
  kind: OrderKind;
  tier: string;
  paidAt: string | null;
  profileLabel: string;
  jobId: string | null;
  jobState: JobState | null;
  attempts: number | null;
  maxAttempts: number | null;
  lastError: string | null;
}

/**
 * The order-level predicate for "this paid order's missing reading needs a person".
 *
 * Exported so the SLA sweep counts the same set this list offers, rather than its own idea of
 * failure. AU-14 (2026-10-26 audit): the sweep counted every FAILED generate-family row, but the
 * only remedy — "Retry job" in the admin console — acts on an order from this list. An orphaned
 * attempt (a REGENERATE that exhausted its attempts before a re-regenerate created a fresh row, or
 * a later row that succeeded and was delivered) is not in this list, so counting it produced a 503
 * no operator action could ever clear. One predicate, so the alert and the remedy cannot drift.
 */
export const recoverableOrderWhere: Prisma.OrderWhereInput = {
  status: "PAID",
  reports: { none: {} },
  jobs: { none: { state: { in: ["QUEUED", "RUNNING"] } } },
  // Erasure retains the order but destroys the report; never offer to rebuild it.
  user: { deletedAt: null },
};

/** The order id an audit row names, when it names one. */
function orderIdFromJson(value: Prisma.JsonValue | null): string | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const orderId = (value as { orderId?: unknown }).orderId;
  return typeof orderId === "string" ? orderId : null;
}

/**
 * Which of `orderIds` are report-less because the customer deleted their own report(s), rather than
 * because a render failed.
 *
 * Extracted so the SLA sweep's `overdueFailures` can subtract exactly the set this list hides.
 * AU-14 (2026-10-26 audit, re-review finding #7): the delete route removes only the Report row and
 * its objects — never the Job rows — so a deleted report puts an order back into the
 * `reports: { none: {} }` shape while an abandoned FAILED generate-family row remains. Counting that
 * row kept `/api/cron/sla` on 503 forever with no "Retry job" row in the console to clear it, which
 * is precisely the unclearable red this scoping exists to end. The count and the list must share
 * this computation, not each have their own idea of "missing".
 *
 * A deletion is linked to an order two ways (both audited):
 *  - the delete row names the order in `before.orderId` (written from AU-02 onward); or
 *  - the delete row names a report id that the order's own `create`/`deliver` row also names — the
 *    only surviving link for rows written before the delete route recorded the order id.
 * The report row is gone and the job never stored its id, so the audit log is all there is.
 */
export async function findIntentionallyDeletedOrderIds(orderIds: string[]): Promise<Set<string>> {
  if (orderIds.length === 0) return new Set();

  const auditRows = await prisma.auditLog.findMany({
    where: {
      entity: "report",
      OR: [
        { action: "delete" },
        ...orderIds.flatMap((orderId) => [
          { action: "create", after: { path: ["orderId"], equals: orderId } },
          { action: "deliver", after: { path: ["orderId"], equals: orderId } },
        ]),
      ],
    },
    select: { entityId: true, action: true, before: true, after: true },
  });

  const deletedReportIds = new Set<string>();
  const directlyDeletedOrderIds = new Set<string>();
  const reportIdsByOrder = new Map<string, Set<string>>();
  const wantedOrderIds = new Set(orderIds);

  for (const row of auditRows) {
    if (row.action === "delete") {
      deletedReportIds.add(row.entityId);
      const orderId = orderIdFromJson(row.before) ?? orderIdFromJson(row.after);
      if (orderId && wantedOrderIds.has(orderId)) directlyDeletedOrderIds.add(orderId);
      continue;
    }
    // `create` / `deliver`: the only surviving record of which report belonged to the order.
    const orderId = orderIdFromJson(row.after);
    if (!orderId || !wantedOrderIds.has(orderId)) continue;
    const ids = reportIdsByOrder.get(orderId) ?? new Set<string>();
    ids.add(row.entityId);
    reportIdsByOrder.set(orderId, ids);
  }

  const intentionallyDeleted = new Set(directlyDeletedOrderIds);
  for (const [orderId, reportIds] of reportIdsByOrder) {
    for (const reportId of reportIds) {
      if (deletedReportIds.has(reportId)) {
        intentionallyDeleted.add(orderId);
        break;
      }
    }
  }

  return intentionallyDeleted;
}

export async function listRecoverableOrders(limit = 100): Promise<RecoverableOrder[]> {
  const orders = await prisma.order.findMany({
    where: recoverableOrderWhere,
    orderBy: { paidAt: "desc" },
    take: limit,
    select: {
      id: true,
      kind: true,
      tier: true,
      paidAt: true,
      profileA: { select: { label: true } },
      profileB: { select: { label: true } },
    },
  });
  if (orders.length === 0) return [];

  const orderIds = orders.map((order) => order.id);

  const [jobs, intentionallyDeleted] = await Promise.all([
    // The generate-family jobs only: a VOICE job is a different failure and cannot produce the
    // missing report. Newest first so the table shows the attempt that actually failed.
    prisma.job.findMany({
      where: { orderId: { in: orderIds }, kind: { in: ["GENERATE", "REGENERATE"] } },
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        orderId: true,
        state: true,
        attempts: true,
        maxAttempts: true,
        lastError: true,
      },
    }),
    findIntentionallyDeletedOrderIds(orderIds),
  ]);

  const latestJob = new Map<string, (typeof jobs)[number]>();
  for (const job of jobs) {
    if (!latestJob.has(job.orderId)) latestJob.set(job.orderId, job);
  }

  return orders
    .filter((order) => !intentionallyDeleted.has(order.id))
    .map((order) => {
      const job = latestJob.get(order.id) ?? null;
      return {
        orderId: order.id,
        kind: order.kind,
        tier: order.tier,
        paidAt: order.paidAt ? order.paidAt.toISOString() : null,
        profileLabel:
          order.kind === "COMPAT" && order.profileB
            ? `${order.profileA.label} × ${order.profileB.label}`
            : order.profileA.label,
        jobId: job?.id ?? null,
        jobState: job?.state ?? null,
        attempts: job?.attempts ?? null,
        maxAttempts: job?.maxAttempts ?? null,
        lastError: job?.lastError ?? null,
      };
    });
}
