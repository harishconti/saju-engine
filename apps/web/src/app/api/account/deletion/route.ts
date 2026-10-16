import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { deletionRequestSchema } from "@/lib/validation/schemas";

export const dynamic = "force-dynamic";

const GRACE_DAYS = 30;

/** Current deletion request state, or null. */
export const GET = handle(async () => {
  const user = await requireUser();
  const request = await prisma.deletionRequest.findFirst({
    where: { userId: user.id },
    orderBy: { requestedAt: "desc" },
  });
  return json({ deletion: request });
});

/** Schedule deletion. Idempotent: an existing pending request is returned rather than duplicated. */
export const POST = handle(async (req) => {
  const user = await requireUser();
  await rateLimit(`deletion:${user.id}`, 10, WINDOW.hour);

  // Body is optional here, so read it defensively rather than via parseJson.
  let input: { reason?: string } = {};
  try {
    const raw = await req.text();
    if (raw) input = deletionRequestSchema.parse(JSON.parse(raw));
  } catch {
    input = {};
  }

  const existing = await prisma.deletionRequest.findFirst({
    where: { userId: user.id, status: "pending" },
  });
  if (existing) return json({ deletion: existing, alreadyScheduled: true });

  const scheduledFor = new Date(Date.now() + GRACE_DAYS * 24 * 60 * 60 * 1000);

  const request = await prisma.$transaction(async (tx) => {
    const created = await tx.deletionRequest.create({
      data: { userId: user.id, status: "pending", reason: input.reason ?? null, scheduledFor },
    });
    await writeAudit(tx, {
      entity: "deletion",
      entityId: created.id,
      action: "create",
      actorId: user.id,
      after: { scheduledFor: scheduledFor.toISOString() },
    });
    return created;
  });

  return json({ deletion: request, graceDays: GRACE_DAYS }, 201);
});

/** Cancel a pending deletion. Allowed any time before it completes. */
export const DELETE = handle(async () => {
  const user = await requireUser();

  const existing = await prisma.deletionRequest.findFirst({
    where: { userId: user.id, status: "pending" },
  });
  if (!existing) throw ApiError.notFound("No pending deletion request");

  const updated = await prisma.$transaction(async (tx) => {
    const next = await tx.deletionRequest.update({
      where: { id: existing.id },
      data: { status: "cancelled" },
    });
    await writeAudit(tx, {
      entity: "deletion",
      entityId: next.id,
      action: "update",
      actorId: user.id,
      before: { status: "pending" },
      after: { status: "cancelled" },
    });
    return next;
  });

  return json({ deletion: updated });
});
