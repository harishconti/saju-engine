import { errorResponse, json } from "@/lib/api";
import { prisma } from "@/lib/prisma";
import { DODO_PROVIDER, processDodoEvent, type DodoEvent } from "@/lib/dodo-webhook";
import { verifyStandardWebhook } from "@/lib/webhook-signature";

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
 *   2. Record the event, deduped on the `webhook-id` header.
 *   3. Process it through the shared `processDodoEvent` (the same function the cleanup cron replays
 *      with), then mark `processedAt`.
 *
 * A duplicate is acknowledged with 200 IMMEDIATELY — anything non-2xx makes Dodo retry forever —
 * but only once the stored event was actually processed. If the first attempt crashed mid-way,
 * `processedAt` is still null and the redelivery is re-processed instead (AU-05). The event id is
 * still deduped in the database, so this cannot create a second row.
 *
 * Contract: docs/webapp/03-api-spec.md, docs/webapp/05-report-pipeline.md §6
 */

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
          provider: DODO_PROVIDER,
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
      if (!isUnique) throw err;

      // The provider is retrying an event we already recorded. Only a fully processed event is a
      // duplicate; otherwise the first attempt died between the insert and `processedAt`, and this
      // delivery is the retry that must finish the work.
      const stored = await prisma.webhookEvent.findUnique({
        where: { provider_eventId: { provider: DODO_PROVIDER, eventId: webhookId as string } },
        select: { id: true, processedAt: true },
      });
      if (!stored || stored.processedAt) return json({ ok: true, duplicate: true });
      eventRowId = stored.id;
    }

    // Step 3: apply the event (shared with the cron's replay), then mark it processed.
    await processDodoEvent(event);
    await prisma.webhookEvent.update({ where: { id: eventRowId }, data: { processedAt: new Date() } });

    return json({ ok: true, type });
  } catch (err) {
    return errorResponse(err);
  }
}
