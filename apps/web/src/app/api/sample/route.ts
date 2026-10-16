import { randomUUID } from "node:crypto";
import { ApiError, clientIp, handle, json, parseJson } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { writeAudit } from "@/lib/audit";
import { birthUtcOffset, resolveBirthLocation, validateBirth } from "@/lib/birth";
import {
  buildAnonymousKey,
  buildSampleKey,
  headObject,
  isR2Configured,
  presignGetUrl,
  presignPutUrl,
} from "@/lib/r2";
import { ENGINE_CONTRACT_VERSION, callEngine, isEngineConfigured } from "@/lib/engine";
import { sampleRequestSchema } from "@/lib/validation/schemas";
import { computeAndStoreChart } from "@/lib/chart-compute";
import { turnstileMode, verifyTurnstile } from "@/lib/turnstile";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

/**
 * The free sample — the funnel, and the only place a visitor does real work before signing up.
 *
 * Deliberately account-free: it is the only proof the product works, so gating it behind sign-up would
 * gut it. If the caller IS signed in we also save a profile, which is what makes "keep this" work.
 *
 * Nothing is persisted for anonymous callers. The object lands under reports/anonymous/… and is swept
 * by an R2 lifecycle rule (7 days) — there is no row to track it by.
 */
export const POST = handle(async (req) => {
  const ip = clientIp(req);
  await rateLimit(`sample:${ip}`, 5, WINDOW.minute);

  const input = await parseJson(req, sampleRequestSchema);

  // Bot protection. Deliberately after the rate limit (cheap, and it bounds the cost of this call)
  // and before any storage or engine work.
  //
  // The mode gate matters: this control has already taken the funnel down once, because a widget that
  // fails to render produces no token and an enforcing server then refuses everybody. `log` mode
  // verifies and records but never blocks, so protection can be validated against real traffic
  // before it is allowed to refuse anyone.
  const tMode = turnstileMode();
  if (tMode !== "off") {
    const turnstile = await verifyTurnstile(input.turnstileToken, ip);
    if (!turnstile.ok) {
      if (tMode === "enforce") {
        throw new ApiError(
          403,
          "TURNSTILE_FAILED",
          "We couldn't confirm you're a person. Please refresh the page and try again.",
        );
      }
      // Log-only: surface it for the rollout without refusing a real visitor.
      console.warn(`turnstile[log]: not satisfied (${turnstile.error}) ip=${ip}`);
    }
  }

  if (!isR2Configured()) {
    throw ApiError.unavailable("Report storage is not configured", "STORAGE_UNAVAILABLE");
  }
  if (!isEngineConfigured()) {
    throw ApiError.unavailable(
      "The report engine isn't reachable yet, so we can't generate your snapshot. Nothing was charged.",
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

  const offset = birthUtcOffset(input.birthDate, input.birthTime, location.timezone);

  const user = await getCurrentUser();
  const birthDate = new Date(`${input.birthDate}T00:00:00Z`);
  const birthTime = input.timeKnown === false ? "12:00" : input.birthTime;

  // A signed-in visitor who has already taken their snapshot for these exact birth details gets
  // the stored report back rather than a second render of the identical chart. That keeps the
  // library free of duplicates and makes the free endpoint idempotent for a signed-in caller.
  let profileId: string | null = null;
  if (user) {
    const samePerson = await prisma.profile.findFirst({
      where: { userId: user.id, deletedAt: null, fullName: input.fullName, birthDate, birthTime },
      select: { id: true },
    });
    profileId = samePerson?.id ?? null;

    if (profileId) {
      const kept = await prisma.report.findFirst({
        where: {
          userId: user.id,
          profileAId: profileId,
          tier: "sample",
          status: "DELIVERED",
          pdfKey: { not: null },
        },
        orderBy: { createdAt: "desc" },
        select: { id: true, pdfKey: true, bytes: true, engineVersion: true },
      });
      if (kept?.pdfKey) {
        return json({
          ok: true,
          downloadUrl: await presignGetUrl(kept.pdfKey, 900),
          expiresIn: 900,
          bytes: kept.bytes ?? undefined,
          engineVersion: kept.engineVersion ?? undefined,
          savedToProfile: true,
          reportId: kept.id,
          reused: true,
        });
      }
    }
  }

  // Decide where the artefact lives *before* presigning. A signed-in snapshot is kept under the
  // user's own prefix, because `reports/anonymous/` is swept by age and a kept sample must not be.
  const sampleId = randomUUID();
  const key = user ? buildSampleKey(user.id, sampleId) : buildAnonymousKey(sampleId, "pdf");

  const result = await callEngine({
    contractVersion: ENGINE_CONTRACT_VERSION,
    kind: "single",
    tier: "sample",
    uploadUrl: await presignPutUrl(key, "application/pdf"),
    profileA: {
      fullName: input.fullName,
      gender: input.gender,
      birthDate: input.birthDate,
      birthTime: input.timeKnown === false ? "12:00" : input.birthTime,
      timeKnown: input.timeKnown !== false,
      timezone: location.timezone,
      utcOffset: offset,
      city: location.city,
      latitude: location.latitude,
      longitude: location.longitude,
    },
  });

  const object = await headObject(key);
  if (!object) throw ApiError.unavailable("The snapshot did not upload correctly", "UPLOAD_NOT_VERIFIED");

  // If the visitor is signed in, keep it — and make the copy true. Previously only the Profile was
  // saved: the PDF was not, so the reading never appeared in the dashboard library and the download
  // link expired after 15 minutes.
  let reportId: string | null = null;
  if (user) {
    const profileCount = profileId
      ? 0
      : await prisma.profile.count({ where: { userId: user.id, deletedAt: null } });

    const resolvedProfileId =
      profileId ??
      (await prisma.$transaction(async (tx) => {
        const created = await tx.profile.create({
          data: {
            userId: user.id,
            label: profileCount === 0 ? "Me" : input.fullName,
            fullName: input.fullName,
            gender: input.gender,
            birthDate,
            birthTime,
            timeKnown: input.timeKnown !== false,
            timezone: location.timezone,
            utcOffset: offset,
            city: location.city,
            country: location.country,
            latitude: location.latitude,
            longitude: location.longitude,
            isDefault: profileCount === 0,
          },
        });
        await writeAudit(tx, {
          entity: "profile",
          entityId: created.id,
          action: "create",
          actorId: user.id,
          after: { source: "free-sample", city: created.city },
        });
        return created.id;
      }));
    profileId = resolvedProfileId;

    // The free tier is delivered on creation: `requiresReview: false`.
    const report = await prisma.$transaction(async (tx) => {
      const created = await tx.report.create({
        data: {
          userId: user.id,
          orderId: null, // a saved sample has no order
          kind: "SINGLE",
          tier: "sample",
          version: 1,
          status: "DELIVERED",
          profileAId: resolvedProfileId,
          pdfKey: key,
          sha256: result.sha256 ?? null,
          bytes: result.bytes ?? object.size,
          engineVersion: result.engineVersion ?? null,
          deliveredAt: new Date(),
        },
        select: { id: true },
      });
      await tx.delivery.create({
        data: {
          reportId: created.id,
          userId: user.id,
          kind: "report",
          channel: "PROFILE",
          provider: "profile",
          status: "sent",
          sentAt: new Date(),
        },
      });
      await writeAudit(tx, {
        entity: "report",
        entityId: created.id,
        action: "deliver",
        actorId: user.id,
        after: { tier: "sample", source: "free-sample", autoDelivered: true },
      });
      return created;
    });
    reportId = report.id;

    await computeAndStoreChart(resolvedProfileId);
  }

  const downloadUrl = await presignGetUrl(key, 900);

  return json({
    ok: true,
    downloadUrl,
    expiresIn: 900,
    bytes: result.bytes,
    engineVersion: result.engineVersion,
    savedToProfile: Boolean(user),
    // Present when signed in, so the UI can link straight to the library entry.
    reportId,
  });
});

/** Used by the header CTA to decide whether to offer "keep this". */
export const GET = handle(async () => {
  const user = await getCurrentUser();
  return json({ signedIn: Boolean(user), engineReady: isEngineConfigured(), storageReady: isR2Configured() });
});
