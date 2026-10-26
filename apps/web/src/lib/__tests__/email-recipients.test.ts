import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * `sendEmail` hands the transport a real array of addresses.
 *
 * Admin alerts fan out to every address in `ADMIN_EMAILS`, which is comma-separated. Joining those
 * back into one string (`"a@x.com, b@y.com"`) produced a single malformed Resend address: the send
 * failed quietly and nobody was told. These tests are at the transport boundary — they assert on the
 * JSON body Resend would actually receive, not on how the caller formatted the value.
 *
 * `email.ts` imports the Prisma singleton, which requires a datasource URL at construction. The
 * client is lazy — nothing connects — so a syntactically valid dummy is enough to import it.
 */
process.env.DATABASE_URL ??= "postgresql://user:pass@localhost:5432/test";

const { sendEmail } = await import("../email");

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
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("sendEmail recipients", () => {
  it("sends a single string address as a one-element array", async () => {
    const sent = stubResend();

    const result = await sendEmail({ to: "client@example.com", subject: "s", text: "t" });

    expect(result.ok).toBe(true);
    expect(sent[0].to).toEqual(["client@example.com"]);
  });

  it("sends two owners as two separate addresses, trimming and dropping blanks", async () => {
    const sent = stubResend();

    const result = await sendEmail({
      to: [" owner@cosmicsaju.com ", "", " second@cosmicsaju.com "],
      subject: "s",
      text: "t",
    });

    expect(result.ok).toBe(true);
    // Two addresses, not one joined string: ["owner@cosmicsaju.com, second@cosmicsaju.com"] would
    // be rejected by Resend and the alert would silently go nowhere.
    expect(sent[0].to).toEqual(["owner@cosmicsaju.com", "second@cosmicsaju.com"]);
  });

  it("sends nothing when every entry is blank", async () => {
    const sent = stubResend();

    const result = await sendEmail({ to: [" ", ""], subject: "s", text: "t" });

    expect(result).toEqual({ ok: false, error: "no recipients" });
    expect(sent).toHaveLength(0);
  });
});
