import { ApiError, clientIp, handle, parseJson } from "@/lib/api";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { birthUtcOffset, resolveBirthLocation, validateBirth } from "@/lib/birth";
import { engineChart, isEngineConfigured } from "@/lib/engine";
import { sampleRequestSchema } from "@/lib/validation/schemas";
import { buildShareCard, shareCardFields } from "@/lib/share-card";

export const dynamic = "force-dynamic";
export const maxDuration = 30;

/**
 * `POST /api/share-card` — the reader's own Day Master card, as a 1080×1920 PNG.
 *
 * Account-free on purpose: it exists to be the *growth loop* for the free snapshot, so putting it
 * behind sign-up would defeat it. That makes this an unauthenticated endpoint that costs an engine
 * call, so it is rate-limited exactly like `/api/sample` — and it is deliberately a **POST**: the birth
 * details must not travel in a query string, where they would land in access logs and referrers.
 *
 * The response is the image, not a URL to one. Nothing is stored: there is no R2 object and no row, so
 * there is nothing to sweep and nothing to leak. The card is built from `shareCardFields()`, which
 * cannot carry birth data (see `src/lib/share-card.tsx`) — the reader is about to publish it.
 *
 * ## Why no Turnstile here, deliberately
 *
 * `/api/sample` verifies Turnstile because it is the first thing a stranger touches. This route is
 * reached *after* that — the reader has just been challenged to get their snapshot. A Turnstile token
 * is **single-use**, so reusing that one is impossible, and mounting a second challenge to obtain a
 * cosmetic share image is real friction for a real visitor. The exposure (an unauthenticated engine
 * call) is bounded by the rate limit below instead. **If this is ever abused, the fix is to issue a
 * fresh token from the share step — not to relax the limiter.**
 */
export const POST = handle(async (req) => {
  const ip = clientIp(req);
  await rateLimit(`share-card:${ip}`, 5, WINDOW.minute);

  const input = await parseJson(req, sampleRequestSchema);

  if (!isEngineConfigured()) {
    throw ApiError.unavailable(
      "The chart engine isn't reachable, so we can't build your card. Try again shortly.",
      "ENGINE_UNAVAILABLE",
    );
  }

  const location = resolveBirthLocation({ city: input.city, countryCode: input.countryCode ?? null });
  const check = validateBirth({
    birthDate: input.birthDate,
    birthTime: input.birthTime,
    timezone: location.timezone,
    timeKnown: input.timeKnown,
  });
  if (!check.ok) throw new ApiError(422, check.code ?? "INVALID_BIRTH_DATA", check.message ?? "Invalid birth data");

  const summary = await engineChart({
    fullName: input.fullName,
    gender: input.gender,
    birthDate: input.birthDate,
    birthTime: input.timeKnown === false ? "12:00" : input.birthTime,
    timeKnown: input.timeKnown,
    timezone: location.timezone,
    utcOffset: birthUtcOffset(input.birthDate, input.birthTime, location.timezone),
    city: `${location.city}, ${location.country}`,
    latitude: location.latitude,
    longitude: location.longitude,
  });

  const image = await buildShareCard(shareCardFields(summary));

  // Never cached, never indexed: it is personal even though `shareCardFields` strips every identifier.
  image.headers.set("cache-control", "private, no-store");
  image.headers.set("x-robots-tag", "noindex, nofollow");
  image.headers.set("x-content-type-options", "nosniff");
  return image;
});
