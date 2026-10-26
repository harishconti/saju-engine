import { z } from "zod";
import { ApiError, handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

/**
 * The statuses `Report.status` can hold (schema.prisma). AU-21: an unknown `?status=` used to be
 * cast straight into the Prisma `where`, which threw and answered 500 for what is a bad request.
 */
const reportStatus = z.enum(["DRAFT_READY", "IN_REVIEW", "APPROVED", "DELIVERED", "SUPERSEDED", "FAILED"]);

/** The caller's reports, newest first. */
export const GET = handle(async (req) => {
  const user = await requireUser();
  const url = new URL(req.url);
  const rawStatus = url.searchParams.get("status");

  let status: z.infer<typeof reportStatus> | null = null;
  if (rawStatus !== null) {
    const parsed = reportStatus.safeParse(rawStatus);
    if (!parsed.success) {
      throw ApiError.badRequest("Unknown report status", "INVALID_STATUS");
    }
    status = parsed.data;
  }

  const reports = await prisma.report.findMany({
    where: {
      userId: user.id,
      ...(status ? { status } : {}),
    },
    orderBy: { createdAt: "desc" },
    select: {
      id: true,
      kind: true,
      tier: true,
      status: true,
      version: true,
      bytes: true,
      pageCount: true,
      createdAt: true,
      deliveredAt: true,
    },
  });

  return json({ reports });
});
