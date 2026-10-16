#!/usr/bin/env node
/**
 * Dodo Payments webhook smoke test — end to end, against a real deployment.
 *
 * WHY THIS EXISTS
 * Every other test of the payment path mocks the provider or calls our verifier directly. This is the
 * only check that exercises the whole thing with a REAL secret against a REAL deployment: signature
 * header -> our handler -> verification -> dedupe -> response.
 *
 * SAFETY
 *  - It sends `payment.succeeded` with a deliberately NON-EXISTENT `order_id`, so the handler records
 *    the event and matches no order. Nothing is marked paid and no report is generated.
 *  - It writes one (harmless, purgeable) WebhookEvent row.
 *  - It never prints the webhook secret, and exits non-zero if any assertion fails.
 *
 * The signature is implemented INDEPENDENTLY of src/lib/webhook-signature.ts on purpose: re-reading the
 * Standard Webhooks spec here means agreement between the two is real evidence, not a tautology.
 *
 * Usage:
 *   node scripts/dodo-webhook-smoke.mjs                          # against production
 *   node scripts/dodo-webhook-smoke.mjs http://localhost:3000   # against a local dev server
 */

import { createHmac, randomUUID } from "node:crypto";
import fs from "node:fs";
import path from "node:path";

const DEFAULT_TARGET = "https://www.cosmicsaju.com";
const target = (process.argv[2] ?? DEFAULT_TARGET).replace(/\/+$/, "");
const endpoint = `${target}/api/webhooks/dodo`;

function loadEnv() {
  const file = path.resolve(import.meta.dirname, "../.env");
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, "utf8").split("\n")) {
    const s = line.trim();
    if (!s || s.startsWith("#") || !s.includes("=")) continue;
    const i = s.indexOf("=");
    const k = s.slice(0, i).trim();
    const v = s.slice(i + 1).trim().replace(/^["']|["']$/g, "");
    if (k && !(k in process.env)) process.env[k] = v;
  }
}
loadEnv();

const secret = process.env.DODO_PAYMENTS_WEBHOOK_KEY;

const results = [];
function check(name, pass, detail = "") {
  results.push({ name, pass, detail });
  console.log(`${pass ? "  PASS" : "  FAIL"}  ${name}${detail ? `  — ${detail}` : ""}`);
}

/** Standard Webhooks: HMAC-SHA256 over `id.timestamp.body`, base64, secret base64-decoded. */
function sign(id, timestamp, body) {
  const key = Buffer.from(secret.replace(/^whsec_/, ""), "base64");
  return `v1,${createHmac("sha256", key).update(`${id}.${timestamp}.${body}`, "utf8").digest("base64")}`;
}

async function post(body, headers) {
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "content-type": "application/json", ...headers },
    body,
  });
  const text = await res.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    /* non-JSON body */
  }
  return { status: res.status, json, text };
}

async function main() {
  if (!secret) {
    console.error("DODO_PAYMENTS_WEBHOOK_KEY is not set — nothing to test with.");
    console.error("It lives in apps/web/.env (and in Vercel for the deployed app).");
    process.exit(2);
  }
  if (!secret.startsWith("whsec_")) {
    console.log("  NOTE  secret has no `whsec_` prefix; the verifier tolerates that.");
  }

  console.log(`\nDodo webhook smoke test → ${endpoint}\n`);

  // A payload that CANNOT affect a real order: the order_id does not exist.
  const body = JSON.stringify({
    type: "payment.succeeded",
    timestamp: new Date().toISOString(),
    data: {
      payment_id: `pay_smoketest_${Date.now()}`,
      status: "succeeded",
      metadata: { order_id: `smoketest-nonexistent-${randomUUID()}`, tier: "deep", kind: "SINGLE" },
      customer: { email: "smoketest@invalid.local" },
    },
  });
  const id = `msg_smoketest_${randomUUID()}`;
  const ts = Math.floor(Date.now() / 1000);

  // 1. A correctly signed event must be accepted.
  const ok = await post(body, {
    "webhook-id": id,
    "webhook-timestamp": String(ts),
    "webhook-signature": sign(id, ts, body),
  });
  check(
    "valid signature accepted (2xx)",
    ok.status >= 200 && ok.status < 300,
    `HTTP ${ok.status}${ok.json?.code ? ` code=${ok.json.code}` : ""}`,
  );
  if (ok.status === 503) {
    console.log("        → 503 means the webhook secret is not configured on the target.");
    console.log("          Vercel env vars only apply after a redeploy.");
  }

  // 2. The SAME webhook-id must be treated as a duplicate, not an error.
  const dupe = await post(body, {
    "webhook-id": id,
    "webhook-timestamp": String(ts),
    "webhook-signature": sign(id, ts, body),
  });
  check(
    "duplicate webhook-id returns 2xx (idempotent)",
    dupe.status >= 200 && dupe.status < 300 && dupe.json?.duplicate === true,
    `HTTP ${dupe.status}${dupe.json ? ` ${JSON.stringify(dupe.json)}` : ""}`,
  );

  // 3. A tampered body must be rejected.
  const tampered = await post(body.replace("succeeded", "succeeded!"), {
    "webhook-id": `${id}-tampered`,
    "webhook-timestamp": String(ts),
    "webhook-signature": sign(id, ts, body),
  });
  check("tampered body rejected (401)", tampered.status === 401, `HTTP ${tampered.status}`);

  // 4. A bad secret must be rejected.
  const badSig = await post(body, {
    "webhook-id": `${id}-badsecret`,
    "webhook-timestamp": String(ts),
    "webhook-signature": sign(id, ts, body).replace(/^v1,.{10}/, "v1,AAAAAAAAAA"),
  });
  check("tampered signature rejected (401)", badSig.status === 401, `HTTP ${badSig.status}`);

  // 5. A stale timestamp must be rejected as a replay.
  const oldTs = ts - 3600;
  const replay = await post(body, {
    "webhook-id": `${id}-replay`,
    "webhook-timestamp": String(oldTs),
    "webhook-signature": sign(`${id}-replay`, oldTs, body),
  });
  check("replayed event rejected (401)", replay.status === 401, `HTTP ${replay.status}`);

  const failed = results.filter((r) => !r.pass);
  console.log(`\n${results.length - failed.length}/${results.length} passed`);
  if (failed.length) {
    console.log("failed:", failed.map((f) => f.name).join("; "));
    process.exit(1);
  }
  console.log("The payment webhook path is verified end to end.\n");
}

main().catch((err) => {
  console.error("smoke test error:", err instanceof Error ? err.name : typeof err);
  process.exit(1);
});
