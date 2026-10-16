/**
 * Published addresses.
 *
 * One mailbox (`hello@`) with receive-only aliases, all landing in the same inbox — see
 * docs/webapp/07-services-and-integrations.md §"Mailbox".
 *
 * The split is deliberate rather than cosmetic: `privacy@` appears *only* where someone is
 * exercising a data right, so those requests are recognisable on arrival and the address is the
 * one a regulator would expect. Everything else — support, refunds, "where's my report?" — goes to
 * `hello@`.
 */

/** General contact: support, refunds, anything a customer needs to ask. */
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL ?? "hello@cosmicsaju.com";

/** Data-protection requests only (GDPR / DPDP access, correction, erasure). */
export const PRIVACY_EMAIL =
  process.env.NEXT_PUBLIC_LEGAL_CONTACT_EMAIL ?? "privacy@cosmicsaju.com";

export const CONTACT_HREF = `mailto:${CONTACT_EMAIL}`;
export const PRIVACY_HREF = `mailto:${PRIVACY_EMAIL}`;
