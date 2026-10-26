/**
 * Retention windows that more than one layer has to agree on.
 *
 * Isomorphic on purpose (no imports, no `server-only`): the *server* sweep and the *client* copy both
 * state how long a free snapshot lives, and a number written twice is a number that drifts. This is the
 * same reasoning as `POLICY_VERSION` in `consent.ts`.
 */

/**
 * How long an unclaimed free snapshot lives in R2, and therefore how long the link to it works.
 *
 * **The daily cleanup cron is the only thing that deletes these.** There is no R2 lifecycle rule for
 * `reports/anonymous/` — the bucket's sole rule is Cloudflare's default multipart-upload abort — so if
 * the cron stops, nothing expires. Verified with `GetBucketLifecycleConfiguration` on 2026-10-17.
 *
 * Three days, down from seven (2026-10-17): the storage saving is negligible, but this is the personal
 * data of someone who never became a customer, so the shorter window is the easier one to defend. The
 * cost is the returning visitor's window — the link in the browser is 15 minutes regardless, so only
 * the *emailed* link is affected, and three days is still enough to come back tomorrow.
 *
 * A shorter window is a deliberate choice, not a default: it must be changed here, and the pages that
 * quote it (`privacy`, `02`, `09`, `10`) follow. `src/lib/__tests__/retention.test.ts` fails if the
 * emailed link outlives the object.
 */
export const ANONYMOUS_SAMPLE_RETENTION_DAYS = 3;

/** `"3 days"` — for prose that has to state the window. */
export const ANONYMOUS_SAMPLE_RETENTION_LABEL = `${ANONYMOUS_SAMPLE_RETENTION_DAYS} days`;

/**
 * How long a profile may sit untouched before its birth details are retired.
 *
 * The privacy policy publishes this number ("until you delete them, or after 24 months of
 * inactivity"), and `docs/webapp/10-privacy-and-compliance.md` describes a warning at 23 months
 * followed by a sweep at 24. **Only the sweep exists.** Nothing in the app sends an inactivity
 * warning — there is no scheduled mailer, and inventing one is a product decision, not a retention
 * fix. So the enforceable half of the promise is this number and the cleanup sweep that applies it;
 * the copy stays as published (owner decision D7: enforce the promise, do not water down the text).
 */
export const PROFILE_INACTIVITY_RETENTION_MONTHS = 24;

/** `"24 months"` — for prose that has to state the window. */
export const PROFILE_INACTIVITY_RETENTION_LABEL = `${PROFILE_INACTIVITY_RETENTION_MONTHS} months`;
