import { ApiError, handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";
import { deliverReport } from "@/lib/email";
import { enqueueAudio } from "@/lib/fulfilment";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

type Ctx = { params: Promise<{ id: string }> };

/**
 * Approve and deliver.
 *
 * The state change and the PROFILE delivery are transactional; the EMAIL is attempted after commit.
 * That ordering matters: the report IS delivered once it is in the profile, so a mail failure must
 * update a Delivery row rather than roll back the approval.
 *
 * A delivered report is immutable — any change creates a new version.
 */
export const POST = handle(async (_req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;

  const report = await prisma.report.findUnique({
    where: { id },
    select: { id: true, orderId: true, status: true, userId: true, pdfKey: true, version: true },
  });
  if (!report) throw ApiError.notFound("Report not found");

  if (report.status === "DELIVERED") {
    throw ApiError.conflict("This report has already been delivered", "ALREADY_DELIVERED");
  }
  if (report.status === "SUPERSEDED") {
    throw ApiError.conflict(
      "A newer version of this report exists. Approving a superseded version would deliver stale content.",
      "SUPERSEDED",
    );
  }
  if (!report.pdfKey) {
    throw ApiError.conflict("There is no PDF to deliver — generate it first", "NO_ARTIFACT");
  }

  const now = new Date();

  await prisma.$transaction(async (tx) => {
    await tx.report.update({
      where: { id: report.id },
      data: {
        status: "DELIVERED",
        reviewedBy: admin.id,
        reviewedAt: now,
        deliveredAt: now,
      },
    });

    // The report is now in the client's profile — that IS the delivery.
    await tx.delivery.create({
      data: {
        reportId: report.id,
        userId: report.userId,
        channel: "PROFILE",
        provider: "profile",
        status: "sent",
        sentAt: now,
      },
    });

    await writeAudit(tx, {
      entity: "report",
      entityId: report.id,
      action: "deliver",
      actorId: admin.id,
      before: { status: report.status },
      after: { status: "DELIVERED", version: report.version },
    });
  });

  // Email after commit, recorded as a Delivery row. Never rolls back the approval.
  await deliverReport(report.id);

  // Queue the audio summary, if this tier includes one. Deliberately AFTER delivery: a
  // text-to-speech outage must not hold a reviewed, paid report. The client's page shows
  // it as "being prepared" until it lands.
  const audioQueued = await enqueueAudio(report.id);

  return json({
    ok: true,
    message: audioQueued
      ? "Delivered. The client has been emailed, and their audio summary is being prepared."
      : "Delivered. The client has been emailed.",
    audioQueued,
  });
});
