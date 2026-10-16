import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";
import { sendEmail } from "@/lib/email";
import { rejectSchema } from "@/lib/validation/schemas";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/**
 * Reject a report. A reason is mandatory — it is the only path where a paid client receives bad news,
 * so it has to be deliberate, and the client sees the reason.
 */
export const POST = handle(async (req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;
  const { reason } = await parseJson(req, rejectSchema);

  const report = await prisma.report.findUnique({
    where: { id },
    select: {
      id: true,
      userId: true,
      status: true,
      orderId: true,
      user: { select: { email: true, name: true } },
    },
  });
  if (!report) throw ApiError.notFound("Report not found");

  if (report.status === "DELIVERED") {
    throw ApiError.conflict("A delivered report cannot be rejected — issue a refund or a new version", "ALREADY_DELIVERED");
  }

  const now = new Date();

  await prisma.$transaction(async (tx) => {
    await tx.report.update({
      where: { id: report.id },
      data: { status: "FAILED", reviewedBy: admin.id, reviewedAt: now },
    });

    await writeAudit(tx, {
      entity: "report",
      entityId: report.id,
      action: "reject",
      actorId: admin.id,
      before: { status: report.status },
      after: { status: "FAILED", reason },
    });
  });

  // Tell the client, and invite them to reply. Best-effort: the Delivery row records the outcome.
  await sendEmail({
    to: report.user.email,
    subject: "Something went wrong with your reading",
    text: [
      "Hello,",
      "",
      "We couldn't complete your reading to the standard we'd want to send it at, so we haven't sent it.",
      "",
      reason,
      "",
      "You have not been charged twice, and we'll either fix this or refund you — just reply to this email.",
      "",
      "— Cosmic Saju",
    ].join("\n"),
  });

  return json({ ok: true, message: "Rejected and the client has been notified." });
});
