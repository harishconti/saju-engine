import { ApiError, handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { approveAndDeliver, ApprovalError } from "@/lib/review";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

type Ctx = { params: Promise<{ id: string }> };

/**
 * Approve and deliver.
 *
 * The work lives in `lib/review.ts` now, because the 10-hour SLA sweep releases readings the
 * same way — a state change and the PROFILE delivery in one transaction, the EMAIL after the
 * commit — and the only difference between the two paths is who looked at it. One implementation,
 * two callers, no drift.
 *
 * A delivered report is immutable — any change creates a new version.
 */
export const POST = handle(async (_req, ctx: Ctx) => {
  const admin = await requireAdmin();
  const { id } = await ctx.params;

  const existing = await prisma.report.findUnique({
    where: { id },
    select: { id: true, status: true },
  });
  if (!existing) throw ApiError.notFound("Report not found");

  let result;
  try {
    result = await approveAndDeliver(id, { actorId: admin.id, outcome: "HUMAN" });
  } catch (err) {
    if (err instanceof ApprovalError) {
      // The two conflicts the reviewer can actually act on.
      if (err.code === "SUPERSEDED") {
        throw ApiError.conflict(
          "A newer version of this report exists. Approving a superseded version would deliver stale content.",
          "SUPERSEDED",
        );
      }
      if (err.code === "NO_ARTIFACT") {
        throw ApiError.conflict("There is no PDF to deliver — generate it first", "NO_ARTIFACT");
      }
      if (err.code === "ALREADY_DELIVERED") {
        throw ApiError.conflict("This report has already been delivered", "ALREADY_DELIVERED");
      }
      throw ApiError.conflict(err.message, err.code);
    }
    throw err;
  }

  if (!result.released) {
    throw ApiError.conflict("This report has already been delivered", "ALREADY_DELIVERED");
  }

  return json({
    ok: true,
    message: result.audioQueued
      ? "Delivered. The client has been emailed, and their audio summary is being prepared."
      : "Delivered. The client has been emailed.",
    audioQueued: result.audioQueued,
  });
});
