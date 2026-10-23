import type { Report } from "@prisma/client";
import { prisma } from "./prisma";
import { writeAudit } from "./audit";
import { deliverReport } from "./email";
import { enqueueAudio } from "./fulfilment";
import { tierPromisesAudio } from "./tts";

/**
 * The approval path — the ONE place a paid reading is released to a client.
 *
 * Two callers now share it: the review console's **Approve** button, and the **10-hour SLA
 * sweep** (`lib/sla.ts`) that releases a reading nobody got to. They must do exactly the same
 * thing, because the difference between them is *who* looked at it — not what happens to it.
 *
 * The order of operations is the same as it was when this lived inside the admin route:
 * the state change and the PROFILE delivery are transactional, and the EMAIL is attempted
 * after the commit. A mail failure must update a Delivery row, never roll back a release.
 */

export type ReviewOutcome = "HUMAN" | "SLA_AUTO";

export interface ApproveResult {
  ok: boolean;
  /** False when the report was already released — the caller should treat it as a no-op. */
  released: boolean;
  note: string;
  /** True when the delivery email is being held until the audio summary is ready. */
  emailHeld: boolean;
  audioQueued: boolean;
}

export class ApprovalError extends Error {
  constructor(
    message: string,
    readonly code: string,
  ) {
    super(message);
    this.name = "ApprovalError";
  }
}

/**
 * Release a reading.
 *
 * @param actorId the admin who approved it, or null for the SLA sweep.
 * @param outcome `HUMAN` for a real review, `SLA_AUTO` when the deadline released it.
 */
export async function approveAndDeliver(
  reportId: string,
  opts: { actorId: string | null; outcome: ReviewOutcome },
): Promise<ApproveResult> {
  const report = await prisma.report.findUnique({
    where: { id: reportId },
    select: {
      id: true,
      orderId: true,
      status: true,
      userId: true,
      pdfKey: true,
      htmlKey: true,
      version: true,
      audioStatus: true,
      order: { select: { status: true, kind: true, tier: true } },
    },
  });
  if (!report) throw new ApprovalError("Report not found", "NOT_FOUND");

  if (report.status === "DELIVERED") {
    // Already released. The sweep runs every 15 minutes and must be a no-op the second time.
    return { ok: true, released: false, note: "already delivered", emailHeld: false, audioQueued: false };
  }
  if (report.status === "SUPERSEDED") {
    throw new ApprovalError(
      "A newer version of this report exists. Approving a superseded version would deliver stale content.",
      "SUPERSEDED",
    );
  }
  if (!report.pdfKey && !report.htmlKey) {
    throw new ApprovalError("There is no artefact to deliver — generate it first", "NO_ARTIFACT");
  }
  // A refunded or cancelled order must never receive a reading.
  if (report.order && report.order.status !== "PAID") {
    throw new ApprovalError(
      `This order is ${report.order.status.toLowerCase()}, not paid.`,
      "ORDER_NOT_PAID",
    );
  }

  const now = new Date();
  const auto = opts.outcome === "SLA_AUTO";

  // The auto-delivered deep tier waits for its audio: the client gets the reading and the MP3 in
  // one message, rather than a "your reading is ready" mail followed by a second one an hour
  // later. The reading is already in their profile either way — only the email waits.
  const wantsAudio = report.order ? tierPromisesAudio(report.order) : false;
  const holdForAudio = auto && wantsAudio && report.audioStatus !== "READY";

  await prisma.$transaction(async (tx) => {
    await tx.report.update({
      where: { id: report.id },
      data: {
        status: "DELIVERED",
        // A human approval records who; an SLA release records that nobody did.
        reviewedBy: auto ? null : opts.actorId,
        reviewedAt: now,
        deliveredAt: now,
        reviewOutcome: auto ? "SLA_AUTO" : "HUMAN",
        slaApprovedAt: auto ? now : null,
        emailHeldForAudio: holdForAudio,
      },
    });

    // The report is now in the client's profile — that IS the delivery.
    await tx.delivery.create({
      data: {
        reportId: report.id,
        userId: report.userId,
        kind: "report",
        channel: "PROFILE",
        provider: "profile",
        status: "sent",
        sentAt: now,
      },
    });

    await writeAudit(tx, {
      entity: "report",
      entityId: report.id,
      action: auto ? "sla_deliver" : "deliver",
      actorId: opts.actorId,
      before: { status: report.status },
      after: {
        status: "DELIVERED",
        version: report.version,
        reviewOutcome: auto ? "SLA_AUTO" : "HUMAN",
        emailHeldForAudio: holdForAudio,
      },
    });
  });

  // Queue the audio summary, if this tier includes one. Deliberately AFTER delivery: a
  // text-to-speech outage must not hold a released, paid report hostage.
  const audioQueued = await enqueueAudio(report.id);

  if (holdForAudio) {
    // The email waits for the audio. `lib/sla.ts` releases it if the audio stalls, and the
    // voice path releases it the moment the MP3 is ready.
    return {
      ok: true,
      released: true,
      note: "delivered; email held for the audio summary",
      emailHeld: true,
      audioQueued,
    };
  }

  // Email after commit, recorded as a Delivery row. Never rolls back the release.
  await deliverReport(report.id);

  return {
    ok: true,
    released: true,
    note: auto ? "delivered by the 10-hour SLA" : "delivered",
    emailHeld: false,
    audioQueued,
  };
}

/** Is this report waiting for the audio before the client hears about it? */
export function isEmailHeld(report: Pick<Report, "emailHeldForAudio" | "audioStatus">): boolean {
  return report.emailHeldForAudio && report.audioStatus !== "READY";
}
