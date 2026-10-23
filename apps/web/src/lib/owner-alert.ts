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
      to: recipients.join(", "),
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
