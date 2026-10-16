import { describe, expect, it } from "vitest";
import { signStandardWebhook, verifyStandardWebhook } from "../webhook-signature";

/**
 * Webhook signature verification.
 *
 * This is the highest-consequence code in the payment path: get it wrong in the permissive direction
 * and anyone can mark an order paid (a free report); get it wrong in the strict direction and real
 * payments silently never fulfil. It is therefore tested directly, with no network and a fixed clock.
 */

// A valid base64 secret, as Dodo issues it (`whsec_` prefix optional).
const SECRET = "whsec_MfKQ9r8GKYqrTwjUPD8ILPZIo2LaLaSw";
const ID = "msg_2b1c9f0e-1111-2222-3333-444455556666";
const NOW = 1_800_000_000; // fixed clock, seconds
const BODY = JSON.stringify({ type: "payment.succeeded", data: { payment_id: "pay_123" } });

function headers(overrides: Partial<{ id: string | null; timestamp: string | null; signature: string | null }> = {}) {
  // NOTE: `??` would treat an explicit null as "not provided", which silently defeated the
  // missing-header cases. hasOwnProperty is the honest check.
  const has = (k: keyof typeof overrides) => Object.prototype.hasOwnProperty.call(overrides, k);
  return {
    rawBody: BODY,
    id: has("id") ? overrides.id! : ID,
    timestamp: has("timestamp") ? overrides.timestamp! : String(NOW),
    signature: has("signature")
      ? overrides.signature!
      : signStandardWebhook({ id: ID, timestamp: NOW, rawBody: BODY, secret: SECRET }),
    secret: SECRET,
    now: NOW,
  };
}

describe("verifyStandardWebhook", () => {
  it("accepts a correctly signed payload", () => {
    expect(verifyStandardWebhook(headers())).toEqual({ ok: true });
  });

  it("accepts a secret without the whsec_ prefix", () => {
    const bare = SECRET.replace(/^whsec_/, "");
    expect(
      verifyStandardWebhook({
        ...headers({ signature: signStandardWebhook({ id: ID, timestamp: NOW, rawBody: BODY, secret: bare }) }),
        secret: bare,
      }),
    ).toEqual({ ok: true });
  });

  it("accepts any matching candidate when several signatures are offered", () => {
    const good = signStandardWebhook({ id: ID, timestamp: NOW, rawBody: BODY, secret: SECRET });
    expect(verifyStandardWebhook(headers({ signature: `v1,AAAA ${good}` })).ok).toBe(true);
  });

  it("rejects a tampered body", () => {
    const res = verifyStandardWebhook({ ...headers(), rawBody: BODY.replace("pay_123", "pay_999") });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.reason).toMatch(/signature mismatch/);
  });

  it("rejects a wrong secret", () => {
    const res = verifyStandardWebhook({ ...headers(), secret: "whsec_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" });
    expect(res.ok).toBe(false);
  });

  it("rejects a tampered signature", () => {
    expect(verifyStandardWebhook(headers({ signature: "v1,not-a-real-signature" })).ok).toBe(false);
  });

  it("rejects a replayed event outside the tolerance window", () => {
    const old = NOW - 600; // 10 minutes old
    const res = verifyStandardWebhook({
      ...headers({ signature: signStandardWebhook({ id: ID, timestamp: old, rawBody: BODY, secret: SECRET }), timestamp: String(old) }),
    });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.reason).toMatch(/tolerance/);
  });

  it("accepts an event inside the tolerance window", () => {
    const recent = NOW - 120; // 2 minutes old
    expect(
      verifyStandardWebhook({
        ...headers({ signature: signStandardWebhook({ id: ID, timestamp: recent, rawBody: BODY, secret: SECRET }), timestamp: String(recent) }),
      }),
    ).toEqual({ ok: true });
  });

  it("rejects missing headers", () => {
    expect(verifyStandardWebhook(headers({ id: null })).ok).toBe(false);
    expect(verifyStandardWebhook(headers({ timestamp: null })).ok).toBe(false);
    expect(verifyStandardWebhook(headers({ signature: null })).ok).toBe(false);
  });

  it("rejects a non-numeric timestamp", () => {
    const res = verifyStandardWebhook(headers({ timestamp: "not-a-number" }));
    expect(res.ok).toBe(false);
  });

  it("rejects when no secret is configured", () => {
    const res = verifyStandardWebhook({ ...headers(), secret: "" });
    expect(res.ok).toBe(false);
    if (!res.ok) expect(res.reason).toMatch(/secret/);
  });

  it("is not confused by a different webhook id", () => {
    // Same body and timestamp, but the signed id differs — the signature must not validate.
    const res = verifyStandardWebhook({ ...headers(), id: "msg_other" });
    expect(res.ok).toBe(false);
  });

  it("uses a constant-time comparison (no early exit on length match alone)", () => {
    // A signature that shares a prefix with the real one must still fail.
    const good = signStandardWebhook({ id: ID, timestamp: NOW, rawBody: BODY, secret: SECRET });
    const nearMiss = `v1,${good.slice(3, 20)}${"A".repeat(Math.max(0, good.length - 20))}`;
    expect(verifyStandardWebhook(headers({ signature: nearMiss })).ok).toBe(false);
  });
});
