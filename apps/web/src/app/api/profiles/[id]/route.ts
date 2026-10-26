import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { CONSENT_REQUIRED_MESSAGE, hasActiveServiceConsent } from "@/lib/consent";
import { writeAudit } from "@/lib/audit";
import { birthUtcOffset, resolveBirthLocation, validateBirth } from "@/lib/birth";
import { profileUpdateSchema } from "@/lib/validation/schemas";
import { computeAndStoreChart } from "@/lib/chart-compute";
import { SCRUBBED_PROFILE } from "@/lib/profile-scrub";

export const dynamic = "force-dynamic";

type Ctx = { params: Promise<{ id: string }> };

/** Own-profile only. Another user's profile is a 404, not a 403. */
async function ownedProfile(userId: string, id: string) {
  const profile = await prisma.profile.findFirst({ where: { id, userId, deletedAt: null } });
  if (!profile) throw ApiError.notFound("Profile not found");
  return profile;
}

export const GET = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;
  const profile = await ownedProfile(user.id, id);
  return json({ profile });
});

export const PATCH = handle(async (req, ctx: Ctx) => {
  const user = await requireUser();
  // AU-30 (2026-10-26 audit): an edit re-resolves the birthplace and re-derives the chart through
  // the engine (`computeAndStoreChart`), so it is a metered operation like an order rather than a
  // plain write. The limit is per hour, matching consent/kick; it also bounds a runaway client
  // that would otherwise spend engine renders on repeated edits.
  await rateLimit(`profile-update:${user.id}`, 30, WINDOW.hour);
  const { id } = await ctx.params;
  const existing = await ownedProfile(user.id, id);
  const input = await parseJson(req, profileUpdateSchema);

  // Consent is the lawful basis for the sensitive category (birth date/time/place), so it is enforced
  // where the data is actually written rather than trusted to a best-effort browser call at signup.
  if (!(await hasActiveServiceConsent(user.id))) {
    throw new ApiError(403, "CONSENT_REQUIRED", CONSENT_REQUIRED_MESSAGE);
  }


  // "Make primary" only. Nothing else is a partial update in practice.
  if (input.isDefault === true && Object.keys(input).length === 1) {
    await prisma.$transaction(async (tx) => {
      await tx.profile.updateMany({ where: { userId: user.id, deletedAt: null }, data: { isDefault: false } });
      await tx.profile.update({ where: { id }, data: { isDefault: true } });
      await writeAudit(tx, {
        entity: "profile",
        entityId: id,
        action: "update",
        actorId: user.id,
        after: { isDefault: true },
      });
    });
    const fresh = await prisma.profile.findUnique({ where: { id } });
    return json({ profile: fresh });
  }

  // AU-34 (2026-10-26 audit): an edit that changes only the city sends no country, so a bare
  // ambiguous name ("Cambridge") would be re-resolved with nothing to disambiguate it and the edit
  // would fail. Fall back to the country already stored on the profile — `findCity` accepts the
  // country name or its two-letter code. A country supplied by the request wins, so re-pointing a
  // profile at a same-named place in another country actually resolves there.
  const location = resolveBirthLocation({
    city: input.city ?? existing.city,
    countryCode: input.countryCode ?? null,
    country: input.country ?? existing.country,
  });

  const birthDate = input.birthDate ?? existing.birthDate.toISOString().slice(0, 10);
  const timeKnown = input.timeKnown ?? existing.timeKnown;
  const birthTime = timeKnown === false ? "12:00" : (input.birthTime ?? existing.birthTime);

  const check = validateBirth({
    birthDate,
    birthTime,
    timezone: location.timezone,
    timeKnown,
  });
  if (!check.ok) throw new ApiError(422, check.code ?? "INVALID_BIRTH_DATA", check.message ?? "Invalid birth data");

  const offset = birthUtcOffset(birthDate, birthTime, location.timezone);
  // Country and timezone are chart-affecting too: two same-named cities (Cambridge GB and Cambridge
  // US) share a city string but not an offset. Comparing only the city name left a chart computed
  // for the old zone in place after the location moved.
  const birthChanged =
    birthDate !== existing.birthDate.toISOString().slice(0, 10) ||
    birthTime !== existing.birthTime ||
    location.city !== existing.city ||
    location.country !== existing.country ||
    location.timezone !== existing.timezone ||
    timeKnown !== existing.timeKnown;

  const updated = await prisma.$transaction(async (tx) => {
    const next = await tx.profile.update({
      where: { id },
      data: {
        label: input.label ?? undefined,
        fullName: input.fullName ?? undefined,
        gender: input.gender ?? undefined,
        birthDate: new Date(`${birthDate}T00:00:00Z`),
        birthTime,
        timeKnown,
        timezone: location.timezone,
        utcOffset: offset,
        city: location.city,
        country: location.country,
        latitude: location.latitude,
        longitude: location.longitude,
        // Force a re-derive when anything chart-affecting moved.
        ...(birthChanged ? { chartJson: null as never, chartComputedAt: null } : {}),
      },
    });

    await writeAudit(tx, {
      entity: "profile",
      entityId: id,
      action: "update",
      actorId: user.id,
      before: { label: existing.label, city: existing.city, timeKnown: existing.timeKnown },
      after: { label: next.label, city: next.city, timeKnown: next.timeKnown, birthChanged },
    });

    return next;
  });

  if (birthChanged) await computeAndStoreChart(updated.id);

  const fresh = await prisma.profile.findUnique({ where: { id } });
  return json({ profile: fresh });
});

export const DELETE = handle(async (_req, ctx: Ctx) => {
  const user = await requireUser();
  const { id } = await ctx.params;
  await ownedProfile(user.id, id);

  await prisma.$transaction(async (tx) => {
    await tx.profile.update({
      where: { id },
      // AU-27: a soft delete that only sets `deletedAt` leaves the birth date, time and place — the
      // sensitive category consent exists for — in the row indefinitely. Scrub the person with the
      // same definition account erasure uses, in the same write that marks the row deleted.
      data: { ...SCRUBBED_PROFILE, deletedAt: new Date(), isDefault: false },
    });
    await writeAudit(tx, { entity: "profile", entityId: id, action: "delete", actorId: user.id });

    // Promote another profile if this was the default.
    const remaining = await tx.profile.findFirst({
      where: { userId: user.id, deletedAt: null },
      orderBy: { createdAt: "asc" },
    });
    if (remaining) {
      await tx.profile.update({ where: { id: remaining.id }, data: { isDefault: true } });
    }
  });

  return json({ ok: true });
});
