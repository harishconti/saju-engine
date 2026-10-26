import { ApiError, handle, json, parseJson } from "@/lib/api";
import { getCurrentUser, getSessionUserId, requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { writeAudit } from "@/lib/audit";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { deletionRequestSchema } from "@/lib/validation/schemas";

export const dynamic = "force-dynamic";

const GRACE_DAYS = 30;

/** Current deletion request state, or null. */
export const GET = handle(async () => {
  const user = await getCurrentUser();

  if (user) {
    const request = await prisma.deletionRequest.findFirst({
      where: { userId: user.id },
      orderBy: { requestedAt: "desc" },
    });
    return json({ deletion: request });
  }

  // AU-24 (owner decision D7): a pending deletion disables sign-in, which means `getCurrentUser`
  // answers null. The login page still has to explain *why* credentials did not lead anywhere, so
  // a live session may read the request that is blocking it — and nothing else about the account.
  const sessionUserId = await getSessionUserId();
  if (!sessionUserId) throw ApiError.unauthorized();

  const pending = await prisma.deletionRequest.findFirst({
    where: { userId: sessionUserId, status: "pending" },
  });
  if (!pending) throw ApiError.unauthorized();
  return json({ deletion: pending, pendingDeletion: true });
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
  // AU-24 (D7): the privacy page promises deletion is "cancellable any time before it completes",
  // and the account page is unreachable while sign-in is disabled — so the blocked session may
  // cancel its own pending request. With nothing pending it is simply not a valid session.
  const user = await getCurrentUser();
  const userId = user?.id ?? (await getSessionUserId());
  if (!userId) throw ApiError.unauthorized();

  const existing = await prisma.deletionRequest.findFirst({
    where: { userId, status: "pending" },
  });
  if (!existing) {
    throw user ? ApiError.notFound("No pending deletion request") : ApiError.unauthorized();
  }

  const updated = await prisma.$transaction(async (tx) => {
    const next = await tx.deletionRequest.update({
      where: { id: existing.id },
      data: { status: "cancelled" },
    });
    await writeAudit(tx, {
      entity: "deletion",
      entityId: next.id,
      action: "update",
      // `userId`, not `user.id`: the blocked-session path has no `AppUser` (AU-24).
      actorId: userId,
      before: { status: "pending" },
      after: { status: "cancelled" },
    });
    return next;
  });

  return json({ deletion: updated });
});
