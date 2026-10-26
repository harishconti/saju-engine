import { prisma } from "./prisma";
import { sendEmail } from "./email";

/**
 * "A reading is waiting for you."
 *
 * The review queue is a human process, and a human process that nobody is told about is a human
 * process that does not happen. This is the ping.
 *
 * Deliberately **email**, not WhatsApp: the Resend integration already exists, the owner already
 * has a mailbox, and a new external service (with its own account, template approval and monthly
 * bill) is not worth it for one message a day. The channel can grow later without changing
 * anything here — the function is the seam.
 *
 * Two rules keep it from becoming noise:
 *  - **one message per batch.** The alert fires when the queue goes from empty to non-empty, not
 *    per reading, so three orders in a minute is one ping, not three;
 *  - **it can never affect a delivery.** The call is fire-and-forget: a mail failure is logged
 *    and nothing else.
 */

/** Where the ping goes. Falls back to the sender identity if no admin list is configured. */
function ownerRecipients(): string[] {
  const configured = (process.env.ADMIN_EMAILS ?? "")
    .split(",")
    .map((e) => e.trim())
    .filter(Boolean);
  if (configured.length > 0) return configured;
  const from = process.env.EMAIL_FROM?.trim();
  return from ? [from] : [];
}

export interface OwnerAlertInput {
  reportId: string;
  tierName: string;
  profileLabel: string;
  /** How long the reading has been waiting, in minutes. */
  waitedMinutes: number;
  /** How many readings are waiting in total, including this one. */
  queueDepth: number;
}

function appUrl(): string {
  return (process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000").replace(/\/+$/, "");
}

/**
 * Tell the owner a reading is waiting.
 *
 * Returns true if a message was sent, false if it was skipped (the queue was already busy, or
 * email is not configured). Never throws.
 */
export async function notifyOwnerNewReview(input: OwnerAlertInput): Promise<boolean> {
  try {
    return await sendOwnerAlert(input);
  } catch (err) {
    // A notification problem is never a delivery problem. Swallowed, logged, and forgotten:
    // the reading is released either way.
    console.error("owner alert failed:", err instanceof Error ? err.message : "unknown");
    return false;
  }
}

async function sendOwnerAlert(input: OwnerAlertInput): Promise<boolean> {
  const recipients = ownerRecipients();
  if (recipients.length === 0) return false;

  // One ping per batch: if a reading is already waiting, the owner knows.
  const waiting = await prisma.report.count({ where: { status: { in: ["DRAFT_READY", "IN_REVIEW"] } } });
  if (waiting > 1) return false;

  // …and never the same reading twice.
  const already = await prisma.report.findFirst({
    where: { id: input.reportId, ownerAlertedAt: { not: null } },
    select: { id: true },
  });
  if (already) return false;

  const link = `${appUrl()}/admin/reports/${input.reportId}`;
  const waited =
    input.waitedMinutes >= 60
      ? `${Math.floor(input.waitedMinutes / 60)}h`
      : `${Math.max(1, input.waitedMinutes)} min`;

  const text = [
    `A reading is waiting for review — ${input.tierName} (${input.profileLabel}).`,
    "",
    `It has been ready for ${waited}. ${input.queueDepth} reading(s) in the queue.`,
    `Review it: ${link}`,
    "",
    "Readings are released automatically after 10 hours, so this is a nudge, not a warning.",
  ].join("\n");

  try {
    const result = await sendEmail({
      to: recipients,
      subject: `A reading is waiting for review — ${input.tierName}`,
      text,
    });
    if (!result.ok && !result.skipped) return false;

    // Marked so a retry cannot double-ping. Written after the send: a failed send must stay
    // retryable, and a successful one must never repeat.
    await prisma.report.update({
      where: { id: input.reportId },
      data: { ownerAlertedAt: new Date() },
    });
    return true;
  } catch (err) {
    // A notification problem is never a delivery problem.
    console.error("owner alert failed:", err instanceof Error ? err.message : "unknown");
    return false;
  }
}

// ─────────────────── engine failure ("a render was lost") ───────────────────

export interface EngineFailureAlertInput {
  orderId: string;
  /**
   * The engine's error code — `UPLOAD_HOSTS_UNCONFIGURED`, `ENGINE_TIMEOUT`, and so on. A code,
   * never a message: a message could carry a presigned URL, and this channel is email.
   */
  code: string;
  /** How many times the dispatcher tried. 3/3 is a lost order, 1/3 is a retry. */
  attempts: number;
}

/**
 * Tell the owner a paid order's render was failed for good.
 *
 * AU-03 (2026-10-26 audit): during the October outage the engine refused every render for five
 * days and nobody was told. This is the direct channel, and unlike the review nudge it is
 * **not** batched or deduplicated — every lost render is an order that will not arrive, so each
 * one is worth a message. The sweep's non-2xx (see `runSlaSweep`) is the aggregate view.
 *
 * Returns true if a message was sent, false if email is not configured or the send failed. Never
 * throws: the caller has already recorded the failure and must return the same outcome either way.
 */
export async function notifyOwnerEngineFailure(input: EngineFailureAlertInput): Promise<boolean> {
  try {
    const recipients = ownerRecipients();
    if (recipients.length === 0) return false;

    const hint =
      input.code === "UPLOAD_HOSTS_UNCONFIGURED"
        ? [
            "",
            "The engine has no upload-host allowlist. Set R2_ENDPOINT (or SAJU_UPLOAD_HOSTS) on "
              + "the engine project, check POST /health reports uploadAllowlist > 0, then retry the job.",
          ]
        : [];

    const text = [
      `Report generation failed — ${input.code}.`,
      "",
      `Order: ${input.orderId}`,
      `Attempts: ${input.attempts}`,
      ...hint,
      `Admin: ${appUrl()}/admin`,
      "",
      "The order stays paid. Retry the job once the engine is healthy.",
    ].join("\n");

    const result = await sendEmail({
      to: recipients,
      subject: `Report generation failed — ${input.code}`,
      text,
    });
    return result.ok;
  } catch (err) {
    // A notification problem is never a delivery problem.
    console.error("engine failure alert failed:", err instanceof Error ? err.message : "unknown");
    return false;
  }
}

/**
 * "An erasure finished locally but the account can still sign in." (AU-25)
 *
 * The local half of an erasure commits before the Neon Auth identity is deleted, deliberately: the
 * data must go even if the identity half is unavailable, and the local half is idempotent so the
 * retry is safe. That leaves one state a log line cannot resolve — a scrubbed account whose login
 * still works — and it needs a person, not another cron run.
 *
 * Only fired on a **terminal** identity outcome: a transient failure the next sweep will retry is
 * not news, and alerting on it every night would train the owner to ignore the alert that matters.
 */
export async function notifyOwnerIdentityDeletionFailed(input: {
  requestId: string;
  userId: string;
  outcome: "failed" | "missing-relation";
  attempts: number;
}): Promise<boolean> {
  try {
    const recipients = ownerRecipients();
    if (recipients.length === 0) return false;

    const cause =
      input.outcome === "missing-relation"
        ? "an expected neon_auth relation is absent (the identity schema changed)"
        : `the raw delete failed ${input.attempts} time(s)`;

    const text = [
      "Account erasure completed locally but the Neon Auth identity could not be deleted.",
      "",
      `Deletion request: ${input.requestId}`,
      `Neon user id: ${input.userId}`,
      `Cause: ${cause}`,
      "",
      "The account's data is already scrubbed, but the person may still be able to sign in with",
      "the identity. Delete the Neon Auth user for this id in the Neon console, then re-run the",
      "cleanup cron: the request is terminal and will not be retried on its own.",
      "",
      `Admin: ${appUrl()}/admin`,
    ].join("\n");

    const result = await sendEmail({
      to: recipients,
      subject: "Account erasure: Neon Auth identity not deleted (AU-25)",
      text,
    });
    return result.ok;
  } catch (err) {
    // A notification problem is never an erasure problem: the audit row is the durable record.
    console.error("identity deletion alert failed:", err instanceof Error ? err.message : "unknown");
    return false;
  }
}
