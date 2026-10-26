import { clientIp, handle, json, parseJson } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { audit } from "@/lib/audit";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { consentSchema } from "@/lib/validation/schemas";
import { POLICY_VERSION } from "@/lib/consent";

export const dynamic = "force-dynamic";

/**
 * Record a consent grant or withdrawal.
 *
 * `ConsentRecord` is APPEND-ONLY: never update a row, always insert and mark the previous one
 * withdrawn. The history is the evidence (docs/webapp/10-privacy-and-compliance.md).
 */
export const POST = handle(async (req) => {
  const user = await requireUser();
  await rateLimit(`consent:${user.id}`, 30, WINDOW.hour);

  const input = await parseJson(req, consentSchema);
  const ip = clientIp(req);
  const ua = req.headers.get("user-agent")?.slice(0, 300) ?? null;

  const previous = await prisma.consentRecord.findFirst({
    where: { userId: user.id },
    orderBy: { grantedAt: "desc" },
  });

  const unchanged =
    previous &&
    previous.policyVersion === POLICY_VERSION &&
    JSON.stringify(previous.purposes) === JSON.stringify(input.purposes);

  if (unchanged) {
    return json({ consent: previous, unchanged: true });
  }

  const record = await prisma.$transaction(async (tx) => {
    if (previous && !previous.withdrawnAt) {
      await tx.consentRecord.update({
        where: { id: previous.id },
        data: { withdrawnAt: new Date() },
      });
    }

    const created = await tx.consentRecord.create({
      data: {
        userId: user.id,
        // AU-23: the version the *user* is consenting to is the one live now, not whatever a
        // possibly-stale tab put in the request body.
        policyVersion: POLICY_VERSION,
        purposes: input.purposes as never,
        ip,
        ua,
      },
    });

    return created;
  });

  await audit({
    entity: "consent",
    entityId: record.id,
    action: "update",
    actorId: user.id,
    after: { policyVersion: record.policyVersion, purposes: record.purposes },
  });

  // Withdrawing the `service` purpose stops processing — the deletion path is the honest
  // consequence, and the account page surfaces it.
  const withdrawnService = input.purposes.service === false;

  return json({ consent: record, withdrawnService });
});
