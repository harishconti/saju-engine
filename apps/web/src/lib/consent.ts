import { ApiError } from "./api";
import { prisma } from "./prisma";

/**
 * The privacy-policy version recorded with every consent.
 *
 * Single source deliberately: this string is the evidence of *which* text someone agreed to, so two
 * copies drifting apart would quietly weaken the audit trail — and it had already been declared twice,
 * identically, under two different names.
 */
export const POLICY_VERSION = "2026-10-15";

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
    select: { withdrawnAt: true, purposes: true, policyVersion: true },
  });
  if (!latest || latest.withdrawnAt) return false;

  // AU-23: a grant is evidence of agreement to *a text*. If the policy has moved on since the
  // record was written, the user has not consented to what we do now, so the record satisfies
  // nothing until they re-consent on the account page.
  if (latest.policyVersion !== POLICY_VERSION) return false;

  const purposes = latest.purposes as { service?: boolean } | null;
  return purposes?.service === true;
}

/**
 * Record the initial `service` grant for a brand-new account (AU-22).
 *
 * Every sign-in path converges on `/auth/complete` — email, Google and magic link — so that page is
 * the one place the server can record this for all three. The old approach was a best-effort browser
 * POST during email sign-up only: closing the tab lost it, and the OAuth and magic-link paths never
 * made it at all.
 *
 * Idempotent by design: any existing row, including a withdrawn one, means this is not a first
 * arrival. Re-granting a withdrawn consent on the next sign-in would quietly undo a withdrawal.
 */
export async function recordInitialServiceConsent(userId: string): Promise<void> {
  const existing = await prisma.consentRecord.findFirst({
    where: { userId },
    select: { id: true },
  });
  if (existing) return;

  await prisma.consentRecord.create({
    data: {
      userId,
      policyVersion: POLICY_VERSION,
      purposes: { service: true, service_messages: false },
    },
  });
}

/** The refusal used wherever birth data would be written. Single copy, so the wording cannot drift. */
export const CONSENT_REQUIRED_MESSAGE =
  "Please accept the privacy policy in your account settings before we store birth details. " +
  "It takes a moment and you can withdraw it there at any time.";

/**
 * The refusal used wherever processing would begin — creating an order, paying for one, or nudging a
 * queued job. The reason there is processing, not storage, so it is a second message rather than a
 * reworded first one; the storage wording above is what the sample and profile routes promise.
 */
export const CONSENT_REQUIRED_PROCESSING_MESSAGE =
  "Please accept the privacy policy in your account settings before we start a reading. " +
  "It takes a moment and you can withdraw it there at any time.";

/**
 * The enforcement half of AU-24 (owner decision D7).
 *
 * Withdrawal used to record a fact and nothing else: the account page said processing had stopped,
 * while an order could still be created and a render started. Any route that begins processing now
 * calls this first. It deliberately delegates to `hasActiveServiceConsent` rather than repeating the
 * rule — the version-awareness from AU-23 must apply to this gate too, and a second copy of the
 * semantics would drift.
 *
 * 409 `CONSENT_REQUIRED` is a stable code the dashboard turns into a link to the consent control
 * (`lib/visitor-copy.ts`), so the refusal is never a dead end.
 */
export async function requireActiveServiceConsent(userId: string): Promise<void> {
  if (await hasActiveServiceConsent(userId)) return;
  throw new ApiError(409, "CONSENT_REQUIRED", CONSENT_REQUIRED_PROCESSING_MESSAGE);
}
