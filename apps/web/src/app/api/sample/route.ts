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
import {
  ENGINE_CONTRACT_VERSION,
  SAMPLE_ENGINE_TIMEOUT_MS,
  callEngine,
  isEngineConfigured,
} from "@/lib/engine";
import { sampleRequestSchema } from "@/lib/validation/schemas";
import { CONSENT_REQUIRED_MESSAGE, hasActiveServiceConsent } from "@/lib/consent";
import { computeAndStoreChart } from "@/lib/chart-compute";
import { turnstileMode, verifyTurnstile } from "@/lib/turnstile";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

// AU-11 (2026-10-26 audit): the engine call uses `SAMPLE_ENGINE_TIMEOUT_MS` (50 s), below this
// 60 s limit. It used to use the 120 s default, so the platform killed the function before the
// abort fired and the timeout was never logged. Keep the two numbers in that order.

/**
 * The free sample — the funnel, and the only place a visitor does real work before signing up.
 *
 * Deliberately account-free: it is the only proof the product works, so gating it behind sign-up would
 * gut it. If the caller IS signed in we also save a profile, which is what makes "keep this" work.
 *
 * Nothing is persisted for anonymous callers. The reading lands under reports/anonymous/… and is swept
 * by the **daily cleanup cron** after `ANONYMOUS_SAMPLE_RETENTION_DAYS` — there is no row to track it by.
 * (This used to claim "an R2 lifecycle rule". The bucket has no such rule — its only rule is
 * Cloudflare's default multipart abort — so believing that comment would have meant shipping a retention
 * promise nothing enforced.)
 */
export const POST = handle(async (req) => {
  const ip = clientIp(req);
  await rateLimit(`sample:${ip}`, 5, WINDOW.minute);

  const input = await parseJson(req, sampleRequestSchema);

  // AU-22 (2026-10-26 audit): saving a sample on a signed-in visitor creates a `Profile` holding
  // birth date, time and place — precisely the data consent is the lawful basis for. The check used
  // to be absent entirely, so the sample route could write sensitive birth data for a user whose
  // consent had never been recorded, or had been withdrawn. Refuse with a code the UI turns into a
  // link to the consent control; never silently proceed.
  const user = await getCurrentUser();
  if (user && !(await hasActiveServiceConsent(user.id))) {
    throw new ApiError(409, "CONSENT_REQUIRED", CONSENT_REQUIRED_MESSAGE);
  }

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
      // AU-33: no IP in the log line. An address is personal data, the log has no erasure path, and
      // the rollout signal needs only the failure reason.
      console.warn(`turnstile[log]: not satisfied (${turnstile.error})`);
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
          // The reading is what a sample offers — since 2026-10-17 it has no PDF at all, so `pdfKey`
          // is null and a `pdfKey: { not: null }` filter would never match a freshly saved sample.
          htmlKey: { not: null },
        },
        orderBy: { createdAt: "desc" },
        select: { id: true, htmlKey: true, htmlBytes: true, engineVersion: true },
      });
      if (kept?.htmlKey) {
        return json({
          ok: true,
          readUrl: await presignGetUrl(kept.htmlKey, 900),
          expiresIn: 900,
          bytes: kept.htmlBytes ?? undefined,
          engineVersion: kept.engineVersion ?? undefined,
          savedToProfile: true,
          reportId: kept.id,
          reused: true,
        });
      }
    }
  }

  // Decide where the artefact lives *before* presigning.
  const sampleId = randomUUID();
  // **The reading is the free artefact.** A sample is one page of chart: it exists to prove the product
  // works, and a PDF download is the worst way to show that — it leaves the site, cannot be read on the
  // phone it was requested from, and looks nothing like what a paid client gets. So the sample is
  // delivered as the same self-contained web document every paid tier is, and the free tier offers **no
  // PDF at all**.
  //
  // AU-29 (2026-10-26 audit): the engine used to require a PDF upload target, so this route presigned
  // one under the swept prefix and the sample failed whenever that throwaway upload failed. The
  // contract's `uploadUrl` is now optional, so a sample asks for the reading and nothing else.
  const readKey = user ? buildSampleKey(user.id, sampleId, "html") : buildAnonymousKey(sampleId, "html");

  const result = await callEngine(
    {
      contractVersion: ENGINE_CONTRACT_VERSION,
      kind: "single",
      tier: "sample",
      // No `uploadUrl`: there is no PDF to keep or verify. The reading is the deliverable.
      // AU-37: this exact content type is what `presignPutUrl` signs (and what the engine sends),
      // so the presigned PUT cannot fail with a signature mismatch.
      htmlUploadUrl: await presignPutUrl(readKey, "text/html; charset=utf-8"),
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
    },
    // Below the function's 60 s limit so a timeout is an `ENGINE_TIMEOUT` we log and explain,
    // not a platform kill the visitor sees as a bare 504 (AU-11).
    SAMPLE_ENGINE_TIMEOUT_MS,
  );

  // AU-29: `engine` answers `htmlBytes` only when the reading really uploaded. Check that **before**
  // `headObject`, so a failed reading upload surfaces as an HTML-specific code rather than as
  // `UPLOAD_NOT_VERIFIED` on a verify step for an object that was never written.
  if (!result.htmlBytes) {
    throw ApiError.unavailable("The snapshot did not upload correctly", "HTML_UPLOAD_FAILED");
  }
  const object = await headObject(readKey);
  if (!object) throw ApiError.unavailable("The snapshot did not upload correctly", "UPLOAD_NOT_VERIFIED");
  const bytes = result.htmlBytes ?? object.size;

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
          // No PDF is kept for a sample: the reading is the artefact, and the PDF the engine produced
          // on the way is under the swept prefix. `pdfKey: null` is therefore correct, not missing.
          pdfKey: null,
          htmlKey: readKey,
          sha256: null,
          bytes,
          htmlBytes: bytes,
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

  const readUrl = await presignGetUrl(readKey, 900);

  return json({
    ok: true,
    // The handle the "email me my snapshot" step uses to ask for a fresh link later. Safe to expose:
    // it is a random UUID that only *names* an object, and every read re-derives the key server-side.
    sampleId,
    // The reading. There is deliberately no PDF URL: the free tier offers the web document only.
    readUrl,
    expiresIn: 900,
    bytes,
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
