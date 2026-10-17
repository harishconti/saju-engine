import { ApiError, clientIp, handle, json, parseJson } from "@/lib/api";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { buildAnonymousKey, buildSampleKey, headObject, isR2Configured, presignGetUrl } from "@/lib/r2";
import { isEmailConfigured, sendEmail } from "@/lib/email";
import { POLICY_VERSION } from "@/lib/consent";
import { sampleEmailSchema } from "@/lib/validation/schemas";

export const dynamic = "force-dynamic";

/**
 * The emailed link's lifetime. The anonymous object is R2-swept at 7 days, so this is the longest a
 * link can *usefully* be — a longer URL would outlive the object it points at and 404. Seven days is
 * also the standard ceiling for a presigned S3/R2 GET.
 */
const LINK_SECONDS = 7 * 24 * 60 * 60;

/**
 * `POST /api/sample/email` — send the free snapshot to an address, and record the lead.
 *
 * The funnel's missing piece: the free snapshot was the only proof the product works, and a visitor
 * left without any way to be contacted again (external product audit, 2026-10-17).
 *
 * ## The product rule this must not break
 *
 * `docs/webapp/06-frontend-ux.md` is explicit: **do not gate the free sample behind sign-up.** So this
 * is a *second*, optional action taken *after* the result is already on screen — never a wall in front
 * of it. The snapshot works whether or not this is ever called.
 *
 * ## What is stored, and on what basis
 *
 * One `SampleLead` row: the address, the marketing choice, the policy version, and the IP. No birth
 * data — the visitor is anonymous and we keep nothing that identifies them. `marketingOptIn` defaults
 * to false, so an omitted field cannot be read as consent (see `10-privacy-and-compliance.md` §Email).
 *
 * The lead is written **before** the send, deliberately: the address is the point of the exercise and
 * the email is the side effect, so a Resend outage must not lose it.
 */
export const POST = handle(async (req) => {
  const ip = clientIp(req);
  await rateLimit(`sample-email:${ip}`, 5, WINDOW.minute);

  const input = await parseJson(req, sampleEmailSchema);

  if (!isR2Configured()) {
    throw ApiError.unavailable("Report storage is not configured", "STORAGE_UNAVAILABLE");
  }

  // Re-derive the object key server-side from the id — the client never supplies a key or a URL, so
  // there is nothing here to point at someone else's file. Two shapes are possible for the same id:
  // anonymous (the funnel case) and a kept sample under the owner's prefix.
  const user = await getCurrentUser();
  const candidates = [buildAnonymousKey(input.sampleId)];
  if (user) candidates.push(buildSampleKey(user.id, input.sampleId));

  let key: string | null = null;
  for (const candidate of candidates) {
    if (await headObject(candidate)) {
      key = candidate;
      break;
    }
  }
  if (!key) {
    // Its own code, not the generic NOT_FOUND: the UI offers "take another snapshot" for this one,
    // which is a different action from "that report does not exist".
    throw new ApiError(
      404,
      "SAMPLE_EXPIRED",
      "That snapshot has expired. Take it again and we'll email you a fresh one.",
    );
  }

  await prisma.sampleLead.upsert({
    where: { email: input.email },
    create: {
      email: input.email,
      marketingOptIn: input.marketingOptIn,
      policyVersion: POLICY_VERSION,
      ip,
    },
    // An existing address updates only its preference: the first-captured time and the IP stay.
    update: { marketingOptIn: input.marketingOptIn },
  });

  const url = await presignGetUrl(key, LINK_SECONDS);

  if (!isEmailConfigured()) {
    // The lead is safe; say plainly that the mail could not be sent rather than pretending.
    return json({ ok: true, emailed: false, expiresInDays: 7 }, 201);
  }

  const sent = await sendEmail({
    to: input.email,
    subject: "Your Korean birth chart snapshot",
    text: [
      "Here is the chart snapshot you asked for.",
      "",
      url,
      "",
      "The link works for 7 days. Nothing is stored about your birth details — create an account and",
      "we'll keep the chart for you: https://www.cosmicsaju.com/sample",
      "",
      "Reply to this email if anything looks wrong.",
    ].join("\n"),
  });

  return json(
    { ok: true, emailed: sent.ok, expiresInDays: sent.ok ? 7 : undefined },
    sent.ok ? 201 : 502,
  );
});
