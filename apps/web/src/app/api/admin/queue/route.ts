import { handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { jobStats } from "@/lib/queue";

export const dynamic = "force-dynamic";

/** Everything the admin console needs in one call. */
export const GET = handle(async () => {
  await requireAdmin();

  const [queue, failedJobs, jobs] = await Promise.all([
    prisma.report.findMany({
      where: { status: { in: ["DRAFT_READY", "IN_REVIEW"] } },
      orderBy: { createdAt: "asc" },
      select: {
        id: true,
        kind: true,
        tier: true,
        status: true,
        version: true,
        createdAt: true,
        user: { select: { email: true } },
        profileA: { select: { label: true } },
        profileB: { select: { label: true } },
      },
    }),
    prisma.job.findMany({
      where: { state: "FAILED" },
      orderBy: { finishedAt: "desc" },
      take: 10,
      select: { id: true, orderId: true, kind: true, attempts: true, maxAttempts: true, lastError: true, finishedAt: true },
    }),
    jobStats(),
  ]);

  const oldest = queue[0]?.createdAt ?? null;

  return json({
    queue,
    oldestAgeMinutes: oldest ? Math.round((Date.now() - oldest.getTime()) / 60_000) : null,
    failedJobs,
    jobs,
  });
});
