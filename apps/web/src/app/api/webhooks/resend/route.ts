import { createHmac, timingSafeEqual as cryptoEqual } from "node:crypto";
import { errorResponse, json } from "@/lib/api";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

/**
 * Resend webhook (Svix-signed).
 *
 * Purpose: surface a bad address in the Delivery table instead of losing it. If we never learn that an
 * email bounced, we never learn that a client is still waiting.
 *
 * Signature scheme (Svix): HMAC-SHA256 over `${svix-id}.${svix-timestamp}.${body}` using the base64
 * secret with its `whsec_` prefix stripped.
 */
function verifySvix(headers: Headers, body: string): boolean {
  const secret = process.env.RESEND_WEBHOOK_SECRET?.trim();
  if (!secret) return false;

  const id = headers.get("svix-id");
  const timestamp = headers.get("svix-timestamp");
  const signatureHeader = headers.get("svix-signature");
  if (!id || !timestamp || !signatureHeader) return false;

  const key = Buffer.from(secret.replace(/^whsec_/, ""), "base64");
  const expected = createHmac("sha256", key).update(`${id}.${timestamp}.${body}`, "utf8").digest("base64");

  // Header looks like: "v1,<sig> v1,<sig2>"
  return signatureHeader
    .split(" ")
    .map((part) => part.split(",")[1])
    .filter(Boolean)
    .some((sig) => {
      const a = Buffer.from(sig, "utf8");
      const b = Buffer.from(expected, "utf8");
      return a.length === b.length && cryptoEqual(a, b);
    });
}

export async function POST(req: Request): Promise<Response> {
  try {
    const body = await req.text();

    if (!verifySvix(req.headers, body)) {
      return json({ error: "Invalid signature", code: "INVALID_SIGNATURE" }, 401);
    }

    const payload = JSON.parse(body) as {
      type?: string;
      data?: { email_id?: string; to?: string[]; bounce?: { message?: string }; [k: string]: unknown };
    };

    const type = payload.type ?? "unknown";
    const messageId = payload.data?.email_id ?? "";

    // Record for idempotency, same pattern as the payment webhook.
    try {
      await prisma.webhookEvent.create({
        data: {
          provider: "resend",
          eventId: `${type}:${messageId}`,
          type,
          payload: JSON.parse(body) as never,
          processedAt: new Date(),
        },
      });
    } catch (err) {
      const dup = typeof err === "object" && err !== null && "code" in err && (err as { code?: string }).code === "P2002";
      if (dup) return json({ ok: true, duplicate: true });
      throw err;
    }

    const statusMap: Record<string, string> = {
      "email.bounced": "bounced",
      "email.complained": "complained",
      "email.delivered": "sent",
    };
    const status = statusMap[type];

    if (status && messageId) {
      await prisma.delivery.updateMany({
        where: { providerMessageId: messageId },
        data: { status, error: status === "bounced" ? "bounced" : null },
      });
    }

    return json({ ok: true });
  } catch (err) {
    return errorResponse(err);
  }
}
