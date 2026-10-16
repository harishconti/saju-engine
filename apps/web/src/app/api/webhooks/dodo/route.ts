import { errorResponse, json } from "@/lib/api";
import { prisma } from "@/lib/prisma";
import { audit, writeAudit } from "@/lib/audit";
import { runDispatchTick } from "@/lib/fulfilment";
import { verifyStandardWebhook } from "@/lib/webhook-signature";
import { after } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

/**
 * Dodo Payments webhook — the ONLY source of truth for "paid".
 *
 * Dodo's own guidance: fulfil on `payment.succeeded` from the webhook, never on the browser redirect,
 * because the redirect can be missed if the customer closes the tab while the webhook is retried until
 * acknowledged.
 *
 * Order of operations matters:
 *   1. Verify the Standard Webhooks signature against the RAW body (before any JSON parsing).
 *   2. Record the event, deduped on the `webhook-id` header. A duplicate returns 200 IMMEDIATELY —
 *      anything non-2xx makes Dodo retry forever.
 *   3. Mutate inside one transaction: Order -> PAID, Job -> QUEUED, audit.
 *
 * Contract: docs/webapp/03-api-spec.md, docs/webapp/05-report-pipeline.md §6
 */

interface DodoEvent {
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

export async function POST(req: Request): Promise<Response> {
  try {
    const secret = process.env.DODO_PAYMENTS_WEBHOOK_KEY?.trim();
    if (!secret) {
      return json({ error: "Webhook is not configured", code: "WEBHOOK_UNCONFIGURED" }, 503);
    }

    // The signature covers the exact bytes, so read the raw body first.
    const rawBody = await req.text();
    const webhookId = req.headers.get("webhook-id");

    const verdict = verifyStandardWebhook({
      rawBody,
      id: webhookId,
      timestamp: req.headers.get("webhook-timestamp"),
      signature: req.headers.get("webhook-signature"),
      secret,
    });

    if (!verdict.ok) {
      // An unverified webhook is a free report.
      console.error("dodo webhook rejected:", verdict.reason);
      return json({ error: "Invalid signature", code: "INVALID_SIGNATURE" }, 401);
    }

    let event: DodoEvent;
    try {
      event = JSON.parse(rawBody) as DodoEvent;
    } catch {
      return json({ error: "Malformed JSON", code: "MALFORMED_JSON" }, 400);
    }

    const type = event.type ?? "unknown";

    // Step 2: record first, deduped on webhook-id.
    let eventRowId: string;
    try {
      const row = await prisma.webhookEvent.create({
        data: {
          provider: "dodo",
          eventId: webhookId as string,
          type,
          payload: JSON.parse(rawBody) as never,
        },
        select: { id: true },
      });
      eventRowId = row.id;
    } catch (err) {
      const isUnique =
        typeof err === "object" && err !== null && "code" in err && (err as { code?: string }).code === "P2002";
      if (isUnique) return json({ ok: true, duplicate: true });
      throw err;
    }

    const orderId = typeof event.data?.metadata?.order_id === "string" ? event.data.metadata.order_id : null;
    const paymentId = event.data?.payment_id ?? null;

    if (type === "payment.succeeded" && orderId) {
      const order = await prisma.order.findUnique({
        where: { id: orderId },
        select: { id: true, status: true, tier: true },
      });

      if (order && order.status !== "PAID" && order.status !== "REFUNDED") {
        await prisma.$transaction(async (tx) => {
          await tx.order.update({
            where: { id: order.id },
            data: { status: "PAID", paidAt: new Date(), provider: "dodo", providerOrderId: paymentId },
          });
          await tx.job.create({ data: { orderId: order.id, kind: "GENERATE", state: "QUEUED" } });
          await writeAudit(tx, {
            entity: "order",
            entityId: order.id,
            action: "paid",
            actorId: null,
            after: { provider: "dodo", paymentId, tier: order.tier },
          });
        });

        // Dispatch without blocking the provider's 2xx. On Vercel Hobby there is no per-minute cron,
        // so this is the primary generation trigger.
        try {
          after(async () => {
            try {
              await runDispatchTick(1);
            } catch {
              // Job stays QUEUED: the daily cron, the dashboard kick, or an admin regenerate recovers it.
            }
          });
        } catch {
          // `after` unavailable — recovery paths above pick it up.
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

    await prisma.webhookEvent.update({ where: { id: eventRowId }, data: { processedAt: new Date() } });

    return json({ ok: true, type });
  } catch (err) {
    return errorResponse(err);
  }
}
