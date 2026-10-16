import { ApiError, handle, json, parseJson } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { writeAudit } from "@/lib/audit";
import { birthUtcOffset, resolveBirthLocation, validateBirth } from "@/lib/birth";
import { profileSchema } from "@/lib/validation/schemas";
import { computeAndStoreChart } from "@/lib/chart-compute";

export const dynamic = "force-dynamic";

/** List the caller's profiles. */
export const GET = handle(async () => {
  const user = await requireUser();
  const profiles = await prisma.profile.findMany({
    where: { userId: user.id, deletedAt: null },
    orderBy: [{ isDefault: "desc" }, { createdAt: "asc" }],
  });
  return json({ profiles });
});

/**
 * Create a profile.
 *
 * Coordinates and timezone resolve ONCE here from the bundled city table (engine change E2) — never
 * at report time, where a geocoding failure would silently drop solar-time correction.
 */
export const POST = handle(async (req) => {
  const user = await requireUser();
  await rateLimit(`profile:${user.id}`, 30, WINDOW.hour);

  const input = await parseJson(req, profileSchema);

  const location = resolveBirthLocation({
    city: input.city,
    countryCode: input.countryCode ?? null,
    country: input.country ?? null,
  });

  const check = validateBirth({
    birthDate: input.birthDate,
    birthTime: input.birthTime,
    timezone: location.timezone,
    timeKnown: input.timeKnown,
  });
  if (!check.ok) throw new ApiError(422, check.code ?? "INVALID_BIRTH_DATA", check.message ?? "Invalid birth data");

  const offset = birthUtcOffset(input.birthDate, input.birthTime, location.timezone);
  const existingCount = await prisma.profile.count({ where: { userId: user.id, deletedAt: null } });

  const profile = await prisma.$transaction(async (tx) => {
    const created = await tx.profile.create({
      data: {
        userId: user.id,
        label: input.label,
        fullName: input.fullName,
        gender: input.gender,
        birthDate: new Date(`${input.birthDate}T00:00:00Z`),
        birthTime: input.timeKnown === false ? "12:00" : input.birthTime,
        timezone: location.timezone,
        utcOffset: offset,
        city: location.city,
        country: location.country,
        latitude: location.latitude,
        longitude: location.longitude,
        timeKnown: input.timeKnown !== false,
        isDefault: input.isDefault ?? existingCount === 0,
      },
    });

    await writeAudit(tx, {
      entity: "profile",
      entityId: created.id,
      action: "create",
      actorId: user.id,
      // No birth data in the audit trail.
      after: { label: created.label, city: created.city, timeKnown: created.timeKnown },
    });

    return created;
  });

  // Derive the chart now so the user sees their pillars immediately. Best-effort: if the engine is
  // unreachable the profile is still saved, and the chart can be derived later.
  await computeAndStoreChart(profile.id);

  const fresh = await prisma.profile.findUnique({ where: { id: profile.id } });
  return json({ profile: fresh }, 201);
});
