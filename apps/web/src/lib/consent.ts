import { prisma } from "./prisma";

/**
 * Consent enforcement.
 *
 * The privacy policy states that consent is recorded **before** any birth data is collected
 * (docs/webapp/10-privacy-and-compliance.md), and the account page lets a user withdraw it. But
 * recording it was *best-effort in the browser* and nothing on the server ever checked — so the claim
 * was aspirational. The first real signup proved it: a `User` row was created with **no**
 * `ConsentRecord` at all, an evidence gap in precisely the place a data-protection review looks, since
 * birth date/time/place is the sensitive category and consent is the lawful basis.
 *
 * `ConsentRecord` is append-only, so "active" means: the most recent row has not been withdrawn *and*
 * it grants the `service` purpose. Withdrawal is therefore enforced by the same check that grants it —
 * there is no second code path to keep in step.
 */
export async function hasActiveServiceConsent(userId: string): Promise<boolean> {
  const latest = await prisma.consentRecord.findFirst({
    where: { userId },
    orderBy: { grantedAt: "desc" },
    select: { withdrawnAt: true, purposes: true },
  });
  if (!latest || latest.withdrawnAt) return false;

  const purposes = latest.purposes as { service?: boolean } | null;
  return purposes?.service === true;
}

/** The refusal used wherever birth data would be written. Single copy, so the wording cannot drift. */
export const CONSENT_REQUIRED_MESSAGE =
  "Please accept the privacy policy in your account settings before we store birth details. " +
  "It takes a moment and you can withdraw it there at any time.";
