import { createHmac, timingSafeEqual } from "node:crypto";

/**
 * Standard Webhooks signature verification.
 *
 * Dodo Payments follows the Standard Webhooks specification, so this covers it: the signature is an
 * HMAC-SHA256 over `{webhook-id}.{webhook-timestamp}.{raw body}`, base64-encoded, with the secret
 * base64-decoded after stripping an optional `whsec_` prefix.
 *
 * Contract: docs/webapp/03-api-spec.md, docs/webapp/07-services-and-integrations.md
 *
 * Kept dependency-free and network-free so it can be unit tested directly — a webhook signature check
 * is exactly the code you cannot afford to be subtly wrong, and an unverified webhook is a free report.
 */

export interface WebhookSignatureInput {
  /** The raw request body, EXACTLY as received — before any JSON parsing or re-serialisation. */
  rawBody: string;
  id: string | null;
  timestamp: string | null;
  signature: string | null;
  secret: string;
  /** Reject events older than this, to prevent replay. Standard Webhooks libraries use 5 minutes. */
  toleranceSeconds?: number;
  /** Injectable clock (seconds) for deterministic tests. */
  now?: number;
}

export type WebhookSignatureResult = { ok: true } | { ok: false; reason: string };

export function verifyStandardWebhook(input: WebhookSignatureInput): WebhookSignatureResult {
  const { rawBody, id, timestamp, signature, secret } = input;

  if (!secret) return { ok: false, reason: "no webhook secret configured" };
  if (!id) return { ok: false, reason: "missing webhook-id" };
  if (!timestamp) return { ok: false, reason: "missing webhook-timestamp" };
  if (!signature) return { ok: false, reason: "missing webhook-signature" };

  const ts = Number(timestamp);
  if (!Number.isFinite(ts)) return { ok: false, reason: "webhook-timestamp is not a number" };

  const tolerance = input.toleranceSeconds ?? 300;
  const now = input.now ?? Math.floor(Date.now() / 1000);
  if (Math.abs(now - ts) > tolerance) {
    return { ok: false, reason: `timestamp outside ${tolerance}s tolerance` };
  }

  // `whsec_` prefix is optional; the remainder is base64-encoded key material.
  const key = Buffer.from(secret.replace(/^whsec_/, ""), "base64");
  const expected = createHmac("sha256", key).update(`${id}.${timestamp}.${rawBody}`, "utf8").digest("base64");

  // Header format: "v1,<sig>" or several space-separated candidates, any of which may match.
  const candidates = signature
    .split(" ")
    .map((part) => part.split(",")[1])
    .filter((v): v is string => Boolean(v));

  const expectedBuf = Buffer.from(expected, "utf8");
  const matched = candidates.some((candidate) => {
    const candidateBuf = Buffer.from(candidate, "utf8");
    return candidateBuf.length === expectedBuf.length && timingSafeEqual(candidateBuf, expectedBuf);
  });

  return matched ? { ok: true } : { ok: false, reason: "signature mismatch" };
}

/** Produce a valid signature. Used by tests and by a local test-sender. */
export function signStandardWebhook(opts: {
  id: string;
  timestamp: number;
  rawBody: string;
  secret: string;
}): string {
  const key = Buffer.from(opts.secret.replace(/^whsec_/, ""), "base64");
  const digest = createHmac("sha256", key)
    .update(`${opts.id}.${opts.timestamp}.${opts.rawBody}`, "utf8")
    .digest("base64");
  return `v1,${digest}`;
}
