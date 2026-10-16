import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * The "your audio summary is ready" email, and the one thing it must not invent.
 *
 * A text-to-speech run measures its own length, so the email can say "about 10 minutes". An audio file
 * attached **by hand** — the upload route, added because a ~10 MB MP3 cannot pass through a Vercel
 * function body — has no length we measured. Stating one anyway would be the same offence the report
 * prose is not allowed: a confident detail nobody verified.
 */

const mocks = vi.hoisted(() => ({
  prisma: {
    report: { findUniqueOrThrow: vi.fn() },
    delivery: { create: vi.fn(), update: vi.fn() },
  },
}));
vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));

const { deliverAudioReadyEmail } = await import("../email");

function captureResend() {
  const sent: Array<Record<string, unknown>> = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (_url: string, init: { body: string }) => {
      sent.push(JSON.parse(init.body) as Record<string, unknown>);
      return new Response(JSON.stringify({ id: "msg_audio" }), {
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
  mocks.prisma.report.findUniqueOrThrow.mockResolvedValue({ userId: "u1" });
  mocks.prisma.delivery.create.mockResolvedValue({ id: "d1" });
  mocks.prisma.delivery.update.mockResolvedValue({ id: "d1" });
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("the audio-ready email", () => {
  it("states a duration when one was measured", async () => {
    const sent = captureResend();
    await deliverAudioReadyEmail({ to: "a@b.com", clientName: "Ada", reportId: "r1", seconds: 600 });

    expect(sent[0].text).toContain("about 10 minutes");
  });

  it("claims NO duration when none is known — an uploaded file has no measured length", async () => {
    const sent = captureResend();
    await deliverAudioReadyEmail({ to: "a@b.com", clientName: "Ada", reportId: "r1", seconds: null });

    const text = String(sent[0].text);
    expect(text).toContain("Your audio summary is ready");
    expect(text).not.toMatch(/\bminutes?\b/);
    expect(text).not.toMatch(/\babout \d/);
  });

  it("is just as careful in the HTML body", async () => {
    const sent = captureResend();
    await deliverAudioReadyEmail({ to: "a@b.com", clientName: "Ada", reportId: "r1" });

    expect(String(sent[0].html)).not.toMatch(/\bminutes?\b/);
  });

  it("records the send as a Delivery row, so /admin can answer 'did they get the audio link?'", async () => {
    captureResend();
    await deliverAudioReadyEmail({ to: "a@b.com", clientName: "Ada", reportId: "r1", seconds: 60 });

    expect(mocks.prisma.delivery.create).toHaveBeenCalledWith(
      expect.objectContaining({ data: expect.objectContaining({ kind: "audio", channel: "EMAIL" }) }),
    );
    expect(mocks.prisma.delivery.update).toHaveBeenCalledWith(
      expect.objectContaining({ data: expect.objectContaining({ status: "sent" }) }),
    );
  });
});
