import { prisma } from "./prisma";
import { audit, writeAudit } from "./audit";
import { processJobById } from "./fulfilment";
import { after } from "next/server";
import { track } from "@vercel/analytics/server";

/**
 * Dodo Payments webhook processing, shared by the live route and the cleanup cron's replay.
 *
 * The route records the event first and then calls `processDodoEvent`. If the process dies between
 * those two steps, the row stays with `processedAt = null`; the next provider retry (or the daily
 * cleanup cron) replays the stored payload through this same function (AU-05).
 *
 * Every branch is written to be safe to run more than once:
 *  - `payment.succeeded` mutates only on the first transition to PAID, so a replay cannot double-
 *    count revenue or create a second GENERATE job;
 *  - `refund.succeeded` mutates only when the order is not already REFUNDED;
 *  - `payment.failed` / `payment.cancelled` only record an audit row.
 *
 * An erased account's payment is still recorded on its retained order (D2: accounting stays
 * correct), but it never queues generation — the customer asked for their reading to be destroyed.
 *
 * Contract: docs/webapp/03-api-spec.md, docs/webapp/05-report-pipeline.md §6
 */

export const DODO_PROVIDER = "dodo";

export interface DodoEvent {
  /** e.g. "payment.succeeded" */
  type?: string;
  timestamp?: string;
  data?: {
    payment_id?: string;
    status?: string;
    metadata?: Record<string, unknown>;
    customer?: { email?: string };
    checkout_session_id?: string;
  };
}

/**
 * Apply a Dodo event's side effects. Returns the event type so the route can echo it.
 * Idempotent: safe to call with the same payload twice.
 */
export async function processDodoEvent(event: DodoEvent): Promise<string> {
  const type = event.type ?? "unknown";
  const orderId = typeof event.data?.metadata?.order_id === "string" ? event.data.metadata.order_id : null;
  const paymentId = event.data?.payment_id ?? null;

  if (type === "payment.succeeded" && orderId) {
    const order = await prisma.order.findUnique({
      where: { id: orderId },
      select: { id: true, status: true, tier: true, user: { select: { deletedAt: true } } },
    });

    if (order && order.status !== "PAID" && order.status !== "REFUNDED") {
      const erased = Boolean(order.user.deletedAt);

      // The status guard is read-then-write, so two concurrent deliveries (the provider retrying
      // while the first attempt is still running) could both pass it. Re-check it as part of the
      // write: only the delivery that actually moves the order to PAID creates the job and counts
      // the revenue, which makes replay safe under concurrency as well as sequentially.
      let createdJobId: string | null = null;
      const transitioned = await prisma.$transaction(async (tx) => {
        const updated = await tx.order.updateMany({
          where: { id: order.id, status: { notIn: ["PAID", "REFUNDED"] } },
          data: { status: "PAID", paidAt: new Date(), provider: "dodo", providerOrderId: paymentId },
        });
        if (updated.count === 0) return false;

        // Order rows are retained for accounting (D2), and the payment must still be recorded — but
        // no reading may be generated for an erased person, so no GENERATE job is queued.
        if (!erased) {
          const job = await tx.job.create({
            data: { orderId: order.id, kind: "GENERATE", state: "QUEUED" },
            select: { id: true },
          });
          createdJobId = job.id;
        }
        await writeAudit(tx, {
          entity: "order",
          entityId: order.id,
          action: "paid",
          actorId: null,
          after: { provider: "dodo", paymentId, tier: order.tier },
        });
        return true;
      });
      if (!transitioned) return type;

      // Revenue event, server-side on purpose: it fires on the provider's confirmation rather than
      // on a browser redirect the buyer may never complete, and it cannot be lost to an ad blocker.
      // Only reachable on the first transition to PAID (the guarded write above skips replays), so a
      // duplicate webhook cannot double-count revenue. Wrapped because analytics must never be able
      // to break fulfilment — and the client rejects non-primitive property values by throwing.
      try {
        await track("purchase", { tier: order.tier, provider: "dodo" });
      } catch {
        // Fulfilment already committed; a lost analytics event is acceptable.
      }

      // Dispatch without blocking the provider's 2xx. The scheduled dispatcher runs every 15
      // minutes from `.github/workflows/sla-sweep.yml` (decision D4 — Hobby cannot run a per-minute
      // Vercel cron), so this is the immediate trigger and that workflow is the ceiling on the wait.
      //
      // AU-13 (2026-10-26 audit): this used to run `runDispatchTick(1)`, which claims the OLDEST
      // queued job — during a backlog that is somebody else's order, and the payment that just
      // succeeded waited another round. It now dispatches exactly the job this event created.
      if (createdJobId) {
        const jobId = createdJobId;
        try {
          after(async () => {
            try {
              await processJobById(jobId, "webhook");
            } catch {
              // Job stays QUEUED: the 15-minute dispatcher, the dashboard kick, or an admin
              // regenerate recovers it.
            }
          });
        } catch {
          // `after` unavailable (e.g. replayed outside a request) — recovery paths above pick it up.
        }
      }
    }
  }

  if ((type === "payment.failed" || type === "payment.cancelled") && orderId) {
    // Deliberately NOT cancelling the order: the customer can retry, and Dodo reuses the order id
    // from metadata on a fresh checkout. We only record what happened.
    await audit({
      entity: "order",
      entityId: orderId,
      action: "update",
      actorId: null,
      after: { provider: "dodo", paymentState: type, paymentId },
    });
  }

  if (type === "refund.succeeded" && orderId) {
    const order = await prisma.order.findUnique({ where: { id: orderId }, select: { id: true, status: true } });
    if (order && order.status !== "REFUNDED") {
      await prisma.$transaction(async (tx) => {
        await tx.order.update({ where: { id: order.id }, data: { status: "REFUNDED" } });
        await writeAudit(tx, {
          entity: "order",
          entityId: order.id,
          action: "refund",
          actorId: null,
          before: { status: order.status },
          after: { status: "REFUNDED", paymentId },
        });
      });
    }
  }

  return type;
}
