import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * Every client-facing message must give replies somewhere real to land.
 *
 * Three places invite a reply — the reject email ("just reply to this email") and two report-page
 * states ("reply to your order email"). `EMAIL_FROM` is the *sending* identity (`reports@`), a role
 * address nobody sits in, so without an explicit `Reply-To` those invitations point at a mailbox
 * that is never read.
 *
 * `email.ts` imports the Prisma singleton, which requires a datasource URL at construction. The
 * client is lazy — nothing connects — so a syntactically valid dummy is enough to import it.
 */
process.env.DATABASE_URL ??= "postgresql://user:pass@localhost:5432/test";

const { sendEmail, deliverReportEmail } = await import("../email");

/** Capture the JSON bodies Resend would receive, without leaving the process. */
function stubResend(): Array<Record<string, unknown>> {
  const sent: Array<Record<string, unknown>> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_url: string, init: { body: string }) => {
      sent.push(JSON.parse(init.body) as Record<string, unknown>);
      return new Response(JSON.stringify({ id: "msg_test" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    }),
  );
  return sent;
}

beforeEach(() => {
  vi.stubEnv("RESEND_API_KEY", "re_test_key");
  vi.stubEnv("EMAIL_FROM", "Cosmic Saju <reports@cosmicsaju.com>");
  vi.stubEnv("NEXT_PUBLIC_APP_URL", "https://www.cosmicsaju.com");
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("reply-to routing", () => {
  it("puts EMAIL_REPLY_TO on a report email, so 'reply to your order email' works", async () => {
    vi.stubEnv("EMAIL_REPLY_TO", "hello@cosmicsaju.com");
    const sent = stubResend();

    await deliverReportEmail({
      to: "client@example.com",
      clientName: "Ada",
      tierName: "Deep Reading",
      reportId: "rep_1",
      profileLabel: "Ada, 1990-01-01",
      audioPending: true,
    });

    expect(sent).toHaveLength(1);
    expect(sent[0].from).toBe("Cosmic Saju <reports@cosmicsaju.com>");
    expect(sent[0].reply_to).toBe("hello@cosmicsaju.com");
  });

  it("lets a caller override the default deliberately", async () => {
    vi.stubEnv("EMAIL_REPLY_TO", "hello@cosmicsaju.com");
    const sent = stubResend();

    await sendEmail({ to: "a@b.com", subject: "s", text: "t", replyTo: "refunds@cosmicsaju.com" });

    expect(sent[0].reply_to).toBe("refunds@cosmicsaju.com");
  });

  it("omits the header entirely when nothing is configured", async () => {
    vi.stubEnv("EMAIL_REPLY_TO", "");
    const sent = stubResend();

    await sendEmail({ to: "a@b.com", subject: "s", text: "t" });

    // Absent, not empty: an empty reply_to would be rejected by Resend.
    expect("reply_to" in sent[0]).toBe(false);
  });

  it("never sends when Resend is unconfigured, and reports it as skipped", async () => {
    vi.stubEnv("RESEND_API_KEY", "");
    const sent = stubResend();

    const result = await sendEmail({ to: "a@b.com", subject: "s", text: "t" });

    expect(result).toEqual({ ok: false, skipped: true, error: "email not configured" });
    expect(sent).toHaveLength(0);
  });
});

describe("published addresses", () => {
  it("defaults to hello@ for contact and privacy@ for data requests", async () => {
    const { CONTACT_EMAIL, CONTACT_HREF, PRIVACY_EMAIL, PRIVACY_HREF } = await import("../contact");

    expect(CONTACT_EMAIL).toBe("hello@cosmicsaju.com");
    expect(PRIVACY_EMAIL).toBe("privacy@cosmicsaju.com");
    expect(CONTACT_HREF).toBe("mailto:hello@cosmicsaju.com");
    expect(PRIVACY_HREF).toBe("mailto:privacy@cosmicsaju.com");
  });
});
