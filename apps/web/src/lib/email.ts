import { prisma } from "./prisma";

/**
 * Transactional email via Resend (REST, no SDK dependency).
 *
 * Delivery is a *recorded* side effect: one `Delivery` row per (report, channel). Sending happens
 * after the approval transaction commits — an email failure never rolls back a delivery, because
 * the report is already in the profile.
 *
 * Contract: docs/webapp/05-report-pipeline.md §6
 */

export function isEmailConfigured(): boolean {
  return Boolean(process.env.RESEND_API_KEY?.trim() && process.env.EMAIL_FROM?.trim());
}

function appUrl(): string {
  return (process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000").replace(/\/+$/, "");
}

export interface SendResult {
  ok: boolean;
  id?: string;
  error?: string;
  /** true when the message was not attempted because Resend is not configured. */
  skipped?: boolean;
}

/**
 * Where a client's reply lands.
 *
 * `EMAIL_FROM` is the *sending* identity (`reports@`) — a role address nobody sits in. Several of
 * our messages explicitly invite a reply ("just reply to this email"), so without an explicit
 * `Reply-To` those replies would go to the sending address instead of the human inbox.
 *
 * Defaulting here rather than at each call site means a new sender cannot forget it. Falls back to
 * `EMAIL_FROM`'s own address when unset, which is a receiving alias too — so a reply never vanishes.
 */
function replyToAddress(): string | undefined {
  const configured = process.env.EMAIL_REPLY_TO?.trim();
  return configured ? configured : undefined;
}

/** Low-level send. Never throws — a delivery problem is reported, not propagated. */
export async function sendEmail(opts: {
  to: string;
  subject: string;
  text: string;
  html?: string;
  replyTo?: string;
}): Promise<SendResult> {
  if (!isEmailConfigured()) return { ok: false, skipped: true, error: "email not configured" };

  const replyTo = opts.replyTo?.trim() || replyToAddress();

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        authorization: `Bearer ${process.env.RESEND_API_KEY}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        from: process.env.EMAIL_FROM,
        to: [opts.to],
        subject: opts.subject,
        text: opts.text,
        ...(opts.html ? { html: opts.html } : {}),
        ...(replyTo ? { reply_to: replyTo } : {}),
      }),
      signal: AbortSignal.timeout(15_000),
    });

    const body = (await res.json().catch(() => ({}))) as { id?: string; message?: string };
    if (!res.ok) return { ok: false, error: body.message ?? `HTTP ${res.status}` };
    return { ok: true, id: body.id };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.name : "unknown" };
  }
}

/**
 * "Your reading is ready" — link-first, no attachment by default.
 *
 * A link (a) drives the user back to the account, (b) lets a revoked report actually be revoked,
 * and (c) avoids the client forwarding a file as "the product".
 *
 * The copy must not predict, promise, or guarantee — same ground rules as the report prose.
 */
export async function deliverReportEmail(opts: {
  to: string;
  clientName: string;
  tierName: string;
  reportId: string;
  profileLabel: string;
  /** True when an audio summary is being prepared. Delivery never waits for it. */
  audioPending?: boolean;
}): Promise<SendResult> {
  const link = `${appUrl()}/dashboard/reports/${opts.reportId}`;
  const greeting = opts.clientName?.trim() ? `Hi ${opts.clientName.trim()},` : "Hello,";

  const text = [
    greeting,
    "",
    `Your ${opts.tierName} for ${opts.profileLabel} has been prepared and reviewed, and it is ready.`,
    "",
    `Read or download it here: ${link}`,
    "",
    "It is also in your profile whenever you want it.",
    ...(opts.audioPending
      ? [
          "",
          "Your included audio summary is being prepared — it will appear on the same page shortly,",
          "and we will email you when it is ready. You do not need to wait for it.",
        ]
      : []),
    "",
    "This link is personal — please don't forward it.",
    "",
    "— Cosmic Saju",
    "An accurate engine and an honest interpreter, not a Korean master.",
    "",
    "Readings describe tendencies and timing, not fixed outcomes, and are for reflection rather",
    "than professional medical, legal, or financial advice.",
  ].join("\n");

  const html = `<div style="font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6;color:#111">
  <p>${escapeHtml(greeting)}</p>
  <p>Your <strong>${escapeHtml(opts.tierName)}</strong> for ${escapeHtml(opts.profileLabel)} has been prepared and reviewed, and it is ready.</p>
  <p><a href="${link}" style="display:inline-block;padding:10px 18px;background:#b8912f;color:#0b0b0f;text-decoration:none;border-radius:6px;font-weight:600">Read your report</a></p>
  <p>It is also in your profile whenever you want it.</p>
  ${
    opts.audioPending
      ? `<p style="color:#666">Your included <strong>audio summary</strong> is being prepared — it will appear on the same page shortly, and we will email you when it is ready. You do not need to wait for it.</p>`
      : ""
  }
  <p style="color:#666;font-size:13px">This link is personal — please don't forward it.</p>
  <hr style="border:none;border-top:1px solid #e5e5e5;margin:20px 0" />
  <p style="color:#666;font-size:12px">
    Cosmic Saju — an accurate engine and an honest interpreter, not a Korean master.<br />
    Readings describe tendencies and timing, not fixed outcomes, and are for reflection rather than
    professional medical, legal, or financial advice.
  </p>
</div>`;

  return sendEmail({
    to: opts.to,
    subject: `Your ${opts.tierName} is ready`,
    text,
    html,
  });
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Deliver a report: records the PROFILE channel, attempts EMAIL, and records the outcome.
 * Call AFTER the approval transaction has committed.
 */
export async function deliverReport(reportId: string): Promise<void> {
  const report = await prisma.report.findUnique({
    where: { id: reportId },
    include: { user: true, profileA: true, order: { select: { kind: true, tier: true } } },
  });
  if (!report) return;

  // Idempotent: never send a second email for the same report.
  const existing = await prisma.delivery.findFirst({
    where: { reportId, channel: "EMAIL", status: { in: ["sent", "queued"] } },
    select: { id: true },
  });
  if (existing) return;

  const { tierNameFor } = await import("./tiers");
  const { tierPromisesAudio } = await import("./tts");
  const tierName = tierNameFor(report.kind as "SINGLE" | "COMPAT", report.tier);
  // ...and false when the audio is *already* there: a reviewer can attach an MP3 before approving
  // (see the audio upload route), and a delivery email claiming it is "being prepared" would then be
  // wrong on the client's very first read of it.
  const audioPending =
    (report.order ? tierPromisesAudio(report.order) : false) && report.audioStatus !== "READY";

  const delivery = await prisma.delivery.create({
    data: {
      reportId,
      userId: report.userId,
      kind: "report",
      channel: "EMAIL",
      to: report.user.email,
      provider: "resend",
      status: "queued",
    },
    select: { id: true },
  });

  const result = await deliverReportEmail({
    to: report.user.email,
    clientName: report.user.name,
    tierName,
    reportId,
    profileLabel: report.profileA.label,
    audioPending,
  });

  await prisma.delivery.update({
    where: { id: delivery.id },
    data: {
      status: result.ok ? "sent" : result.skipped ? "failed" : "failed",
      providerMessageId: result.id ?? null,
      error: result.ok ? null : result.error ?? null,
      sentAt: result.ok ? new Date() : null,
    },
  });
}

/**
 * "Your audio summary is ready."
 *
 * Sent only after the MP3 has landed in R2. The report itself was delivered at approval, so
 * this is a *second*, additive message — a text-to-speech outage must never hold back a
 * reviewed, paid report.
 *
 * Same ground rules as every other client-facing message: no promises, no predictions.
 */
export async function deliverAudioReadyEmail(opts: {
  to: string;
  clientName: string;
  reportId: string;
  /**
   * Length in seconds, when it is known — a TTS run measures it. **Optional on purpose**: an audio file
   * attached by hand (see `/api/admin/reports/[id]/audio/upload`) has no length we can vouch for, and
   * stating one we did not measure is exactly the kind of invented detail the report prose is not
   * allowed to contain either.
   */
  seconds?: number | null;
}): Promise<SendResult> {
  const link = `${appUrl()}/dashboard/reports/${opts.reportId}`;
  const greeting = opts.clientName?.trim() ? `Hi ${opts.clientName.trim()},` : "Hello,";
  const lead =
    typeof opts.seconds === "number" && opts.seconds > 0
      ? `Your audio summary is ready — about ${Math.max(1, Math.round(opts.seconds / 60))} minutes, read from the same reading you already have.`
      : "Your audio summary is ready, read from the same reading you already have.";

  const text = [
    greeting,
    "",
    lead,
    "",
    `Listen here: ${link}`,
    "",
    "It is a reading of the report, so it says nothing the written version does not.",
    "",
    "— Cosmic Saju",
    "Readings describe tendencies and timing, not fixed outcomes, and are for reflection rather",
    "than professional medical, legal, or financial advice.",
  ].join("\n");

  const html = `<div style="font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.6;color:#111">
  <p>${escapeHtml(greeting)}</p>
  <p>${escapeHtml(lead)}</p>
  <p><a href="${link}" style="display:inline-block;padding:10px 18px;background:#b8912f;color:#0b0b0f;text-decoration:none;border-radius:6px;font-weight:600">Listen to your summary</a></p>
  <p>It is a reading of the report, so it says nothing the written version does not.</p>
  <hr style="border:none;border-top:1px solid #e5e5e5;margin:20px 0" />
  <p style="color:#666;font-size:12px">
    Cosmic Saju — an accurate engine and an honest interpreter, not a Korean master.<br />
    Readings describe tendencies and timing, not fixed outcomes, and are for reflection rather than
    professional medical, legal, or financial advice.
  </p>
</div>`;

  // Recorded like the report email, so `/admin` can answer "did they get the audio link?".
  const delivery = await prisma.delivery.create({
    data: {
      reportId: opts.reportId,
      userId: (await prisma.report.findUniqueOrThrow({ where: { id: opts.reportId }, select: { userId: true } })).userId,
      kind: "audio",
      channel: "EMAIL",
      to: opts.to,
      provider: "resend",
      status: "queued",
    },
    select: { id: true },
  });

  const result = await sendEmail({ to: opts.to, subject: "Your audio summary is ready", text, html });

  await prisma.delivery.update({
    where: { id: delivery.id },
    data: {
      status: result.ok ? "sent" : "failed",
      providerMessageId: result.id ?? null,
      error: result.ok ? null : (result.error ?? null),
      sentAt: result.ok ? new Date() : null,
    },
  });

  return result;
}
