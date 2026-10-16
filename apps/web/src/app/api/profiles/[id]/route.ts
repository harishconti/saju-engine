import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { CONSENT_REQUIRED_MESSAGE, hasActiveServiceConsent } from "@/lib/consent";
import { writeAudit } from "@/lib/audit";
import { birthUtcOffset, resolveBirthLocation, validateBirth } from "@/lib/birth";
import { profileUpdateSchema } from "@/lib/validation/schemas";
import { computeAndStoreChart } from "@/lib/chart-compute";

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

  const location = resolveBirthLocation({
    city: input.city ?? existing.city,
    countryCode: input.countryCode ?? null,
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
  const birthChanged =
    birthDate !== existing.birthDate.toISOString().slice(0, 10) ||
    birthTime !== existing.birthTime ||
    location.city !== existing.city ||
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
      data: { deletedAt: new Date(), isDefault: false },
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
