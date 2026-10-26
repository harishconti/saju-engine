import { clientIp, handle, json, parseJson } from "@/lib/api";
import { requireUser, revokeOtherSessions } from "@/lib/auth";
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
    // AU-23 follow-up: a withdrawn row still carries the purposes it granted before withdrawal. If
    // it counted as "unchanged", a visitor re-granting exactly those purposes would write nothing
    // and `hasActiveServiceConsent` would stay false — consent visibly ticked, every birth-data
    // write refused.
    !previous.withdrawnAt &&
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

  // Withdrawing the `service` purpose stops new orders and new readings (owner decision D11);
  // readings already paid for still render and are delivered. The account page says both halves.
  const withdrawnService = input.purposes.service === false;

  // AU-24 (owner decision D7): a withdrawal has to reach sessions that are already open, or the
  // promise only holds on this device. Other sessions end; this one stays, because the visitor is
  // still on the page that just recorded the withdrawal. Best-effort — `revokeOtherSessions` never
  // throws, so a provider failure cannot lose the record we just wrote.
  if (withdrawnService) {
    await revokeOtherSessions();
  }

  return json({ consent: record, withdrawnService });
});
