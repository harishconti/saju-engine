import { handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

/** The caller's reports, newest first. */
export const GET = handle(async (req) => {
  const user = await requireUser();
  const url = new URL(req.url);
  const status = url.searchParams.get("status");

  const reports = await prisma.report.findMany({
    where: {
      userId: user.id,
      ...(status ? { status: status as never } : {}),
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
