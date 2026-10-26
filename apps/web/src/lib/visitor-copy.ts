/**
 * What a visitor is told when a report could not be generated.
 *
 * AU-10 (2026-10-26 audit): during the October outage every visitor saw the one sentence
 * "The report engine failed". No cause, no retry, no reference for support — and for a free
 * sample, no reassurance that it had cost them nothing.
 *
 * Copy is mapped here, from the engine's code, in one place, so no route or component can
 * regress to that bare sentence. Two contexts, deliberately different:
 *
 *   `sample` — free. It is true and useful to say nothing was charged.
 *   `paid`   — the customer has already paid. Saying "nothing was charged" is false and
 *              alarming; they need to hear that the order is safe and will not be charged twice.
 *
 * The reference is quoted in the message itself, so it survives whichever surface renders the
 * sentence; it is derived from the `x-request-id` header the route sets on every error response
 * (`handle` in `./api`), which also appears in the server log.
 */

export type FailureContext = "sample" | "paid";

/** A link out of the failure, for refusals that a retry cannot fix (AU-22's consent gate). */
export interface FailureAction {
  href: string;
  label: string;
}

export interface FailureNotice {
  /** The sentence(s) the visitor sees. Always complete, always actionable. */
  message: string;
  /** Whether a "Try again" control belongs inside the alert. */
  retryable: boolean;
  /** Short id support can grep the server log for; null when the request never reached us. */
  reference: string | null;
  /**
   * A control that actually resolves the refusal, when one exists. `CONSENT_REQUIRED` (AU-22) is the
   * case: no number of retries will store birth data the account has not consented to, so the alert
   * must point at the account page instead of offering "Try again".
   */
  action: FailureAction | null;
}

/**
 * The last eight alphanumerics of a request id, lowercased. Vercel request ids look like
 * `iad1::7f3a2c19-…`; the tail is the unique part and is short enough to read aloud.
 */
export function shortReference(requestId?: string | null): string | null {
  if (!requestId) return null;
  const compact = requestId.replace(/[^a-z0-9]/gi, "").toLowerCase();
  return compact ? compact.slice(-8) : null;
}

const SUBJECT: Record<FailureContext, string> = {
  sample: "your snapshot",
  paid: "your reading",
};

/** Never "nothing was charged" for a paid order — that would be false. */
const REASSURANCE: Record<FailureContext, string> = {
  sample: "Nothing was charged.",
  paid: "Your order is safe — you have not been charged twice.",
};

/**
 * The next step differs by context: a free visitor can retry immediately, while a paying
 * customer's generation happens server-side and their retry is ours to run.
 */
const NEXT_STEP: Record<FailureContext, string> = {
  sample: "Please try again.",
  paid: "We're on it — you don't need to do anything, and we'll email you when it's ready.",
};

function sentence(context: FailureContext, lead: string): string {
  return `${lead} ${REASSURANCE[context]} ${NEXT_STEP[context]}`;
}

const ACTIONABLE: Record<string, (context: FailureContext) => string> = {
  UPLOAD_HOSTS_UNCONFIGURED: (context) =>
    sentence(
      context,
      `Our report service is misconfigured at the moment, so ${SUBJECT[context]} could not be generated.`,
    ) + " We've been alerted to fix it.",
  ENGINE_TIMEOUT: (context) =>
    sentence(context, `The report engine took too long to answer, so ${SUBJECT[context]} was not generated.`),
  UPLOAD_NOT_VERIFIED: (context) =>
    sentence(context, `${capitalise(SUBJECT[context])} was generated but didn't save correctly.`),
  // A lost *reading* upload (the engine's `HTML_UPLOAD_FAILED`). `UPLOAD_NOT_VERIFIED` covers a
  // claimed-but-missing object; this one is the engine telling us the reading never reached storage.
  HTML_UPLOAD_FAILED: (context) =>
    sentence(context, `We generated ${SUBJECT[context]}, but the reading didn't save correctly.`),
  ENGINE_UNAVAILABLE: (context) =>
    sentence(context, `The report service isn't reachable at the moment, so ${SUBJECT[context]} could not be generated.`),
  ENGINE_UNREACHABLE: (context) =>
    sentence(context, `The report service isn't reachable at the moment, so ${SUBJECT[context]} could not be generated.`),
  ENGINE_FAILED: (context) =>
    sentence(context, `Something went wrong while generating ${SUBJECT[context]}.`),
  RENDER_FAILED: (context) =>
    sentence(context, `Something went wrong while generating ${SUBJECT[context]}.`),
  STORAGE_UNAVAILABLE: (context) =>
    sentence(context, `Our storage service isn't available at the moment, so ${SUBJECT[context]} could not be saved.`),
};

/**
 * Birth-data rejections need an edit, not a resubmit of the same payload — so they are not
 * retryable. The sample form validates most of these client-side; these catch the rest.
 */
const BIRTH_DATA_FIX: Record<string, string> = {
  INVALID_GENDER: "Choose a gender — the major-luck direction needs it.",
  INVALID_BIRTH_DATE: "That date of birth doesn't look right. Use YYYY-MM-DD.",
  INVALID_BIRTH_TIME: "That time of birth doesn't look right. Use a 24-hour time like 13:28.",
  MISSING_LONGITUDE: "We need the birthplace so solar-time correction is exact. Pick it from the list.",
  MISSING_TIMEZONE: "We need a timezone or UTC offset for that birthplace.",
  UNKNOWN_TIMEZONE: "That birthplace's timezone couldn't be resolved. Pick a different birthplace.",
  CITY_NOT_RESOLVED: "We couldn't find that birthplace. Pick one from the list.",
  INVALID_BIRTH_DATA: "Please check the birth details and try again.",
};

/** Where a signed-in visitor can grant or withdraw the `service` consent. */
export const CONSENT_CONTROL: FailureAction = {
  href: "/dashboard/account",
  label: "Open your consent settings",
};

const ACTIONS: Record<string, FailureAction> = {
  CONSENT_REQUIRED: CONSENT_CONTROL,
};

const REFUSALS: Record<string, (context: FailureContext) => string> = {
  // AU-22: the server refused to store birth data because no current consent is on file. The fix
  // is on the account page, so the copy names it and never invites another attempt as-is.
  CONSENT_REQUIRED: (context) =>
    `Please accept the privacy policy in your account settings first — we can't store birth details ` +
    `without your consent, so ${SUBJECT[context]} wasn't generated. ${REASSURANCE[context]}`,
};

function capitalise(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function failureNotice(input: {
  code?: string | null;
  context: FailureContext;
  requestId?: string | null;
}): FailureNotice {
  const code = input.code?.trim() || "";
  const reference = shortReference(input.requestId);

  const fix = BIRTH_DATA_FIX[code];
  const refusal = REFUSALS[code];
  const base = refusal
    ? refusal(input.context)
    : fix
      ? `${fix} ${REASSURANCE[input.context]}`
      : (ACTIONABLE[code]?.(input.context) ??
        sentence(input.context, `We couldn't generate ${SUBJECT[input.context]} just now.`));

  const message = reference ? `${base} If you contact support, quote reference ${reference}.` : base;

  const action = ACTIONS[code] ?? null;

  // Only a free visitor can retry from the page; a paid order's regeneration is ours to run — and a
  // refusal with a named fix (bad birth data, missing consent) never becomes a retry.
  return {
    message,
    retryable: input.context === "sample" && !fix && !refusal,
    reference,
    action,
  };
}
