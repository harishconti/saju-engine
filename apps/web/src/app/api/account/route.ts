import { z } from "zod";
import { handle, json, parseJson } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { audit } from "@/lib/audit";

export const dynamic = "force-dynamic";

const patchSchema = z.object({ name: z.string().trim().min(1).max(80) });

export const GET = handle(async () => {
  const user = await requireUser();
  const [record, consent, deletion, counts] = await Promise.all([
    prisma.user.findUnique({
      where: { id: user.id },
      select: { id: true, email: true, name: true, role: true, createdAt: true },
    }),
    prisma.consentRecord.findFirst({ where: { userId: user.id }, orderBy: { grantedAt: "desc" } }),
    prisma.deletionRequest.findFirst({ where: { userId: user.id }, orderBy: { requestedAt: "desc" } }),
    prisma.user.findUnique({
      where: { id: user.id },
      select: { _count: { select: { profiles: true, reports: true, orders: true } } },
    }),
  ]);

  return json({ account: record, consent, deletion, counts: counts?._count ?? null });
});

export const PATCH = handle(async (req) => {
  const user = await requireUser();
  const { name } = await parseJson(req, patchSchema);

  const before = await prisma.user.findUnique({ where: { id: user.id }, select: { name: true } });
  const updated = await prisma.user.update({
    where: { id: user.id },
    data: { name },
    select: { id: true, name: true, email: true },
  });

  await audit({
    entity: "user",
    entityId: user.id,
    action: "update",
    actorId: user.id,
    before: { name: before?.name },
    after: { name: updated.name },
  });

  return json({ account: updated });
});
