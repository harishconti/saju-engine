/**
 * What a visitor is told when a report could not be generated.
 *
 * AU-10 (2026-10-26 audit): during the October outage every visitor saw the one sentence
 * "The report engine failed" — no cause, no retry, no reference for support, and no reassurance
 * that the free sample had cost them nothing. Copy is now mapped from the engine's code in one
 * place, in two contexts that must never be confused:
 *
 *   sample — free. It is true and useful to say nothing was charged.
 *   paid   — the customer has already paid. Saying "nothing was charged" is false and alarming;
 *            they need to hear that the order is safe and will not be charged twice.
 */
import { describe, expect, it } from "vitest";

import { failureNotice, shortReference } from "@/lib/visitor-copy";

const REQUEST_ID = "iad1::7f3a2c19-4b8e-4c1a-9f2d-1a2b3c4d5e6f";

describe("failureNotice", () => {
  it("maps UPLOAD_HOSTS_UNCONFIGURED to an actionable sentence, and says nothing was charged", () => {
    const notice = failureNotice({
      code: "UPLOAD_HOSTS_UNCONFIGURED",
      context: "sample",
      requestId: REQUEST_ID,
    });

    expect(notice.retryable).toBe(true);
    expect(notice.message).toMatch(/misconfigured/i);
    expect(notice.message).toContain("Nothing was charged.");
    expect(notice.reference).toBe("3c4d5e6f");
  });

  it("maps ENGINE_TIMEOUT to a timeout sentence, not a generic failure", () => {
    const notice = failureNotice({ code: "ENGINE_TIMEOUT", context: "sample" });

    expect(notice.retryable).toBe(true);
    expect(notice.message).toMatch(/took too long/i);
    expect(notice.message).toContain("Nothing was charged.");
  });

  it("maps UPLOAD_NOT_VERIFIED to a save-problem sentence", () => {
    const notice = failureNotice({ code: "UPLOAD_NOT_VERIFIED", context: "sample" });

    expect(notice.retryable).toBe(true);
    expect(notice.message).toMatch(/didn't save correctly/i);
    expect(notice.message).toContain("Nothing was charged.");
  });

  it("falls back to a complete sentence for an unknown code", () => {
    const notice = failureNotice({ code: "SOMETHING_NEW", context: "sample", requestId: "abcdef123456" });

    expect(notice.retryable).toBe(true);
    expect(notice.message).not.toBe("The report engine failed");
    expect(notice.message).toContain("Please try again.");
    expect(notice.message).toContain("Nothing was charged.");
    expect(notice.message).toContain("abcdef123456".slice(-8));
  });

  it("never says nothing was charged for a paid order", () => {
    for (const code of ["UPLOAD_HOSTS_UNCONFIGURED", "ENGINE_TIMEOUT", "UPLOAD_NOT_VERIFIED", undefined]) {
      const notice = failureNotice({ code, context: "paid" });

      expect(notice.message).not.toMatch(/nothing was charged/i);
      // The reassurance a paying customer needs instead.
      expect(notice.message).toMatch(/order is safe|not been charged twice/i);
      // Regeneration is the server's job, so no "Try again" button and no "you should retry".
      expect(notice.retryable).toBe(false);
      expect(notice.message).not.toMatch(/please try again/i);
    }
  });

  it("offers a retry only when retrying can help", () => {
    expect(failureNotice({ code: "ENGINE_TIMEOUT", context: "sample" }).retryable).toBe(true);
    // Bad birth data needs an edit, not a resubmit of the same payload.
    expect(failureNotice({ code: "INVALID_BIRTH_DATE", context: "sample" }).retryable).toBe(false);
    expect(failureNotice({ code: "INVALID_BIRTH_DATE", context: "sample" }).message).toMatch(
      /YYYY-MM-DD/,
    );
  });

  it("turns a missing consent into a LINK to the consent control, never a retry (AU-22)", () => {
    const notice = failureNotice({ code: "CONSENT_REQUIRED", context: "sample" });

    expect(notice.retryable).toBe(false);
    expect(notice.message).toMatch(/consent/i);
    expect(notice.message).toContain("Nothing was charged.");
    expect(notice.action).not.toBeNull();
    expect(notice.action?.href).toBe("/dashboard/account");
    expect(notice.action?.label).toMatch(/consent/i);
  });

  it("has no action for an ordinary failure", () => {
    expect(failureNotice({ code: "ENGINE_TIMEOUT", context: "sample" }).action).toBeNull();
  });

  it("carries a short reference derived from the request id", () => {
    const notice = failureNotice({ code: "ENGINE_TIMEOUT", context: "sample", requestId: REQUEST_ID });

    expect(notice.reference).toBe("3c4d5e6f");
    expect(notice.message).toContain("3c4d5e6f");
  });

  it("has no reference when the failure never reached the server", () => {
    const notice = failureNotice({ context: "sample", code: null, requestId: null });

    expect(notice.reference).toBeNull();
    expect(notice.message).not.toMatch(/reference/i);
  });

  it("never surfaces the bare sentence the audit found", () => {
    const codes = [undefined, null, "ENGINE_FAILED", "UPLOAD_HOSTS_UNCONFIGURED", "ENGINE_TIMEOUT"];
    for (const code of codes) {
      for (const context of ["sample", "paid"] as const) {
        expect(failureNotice({ code, context }).message).not.toBe("The report engine failed");
        expect(failureNotice({ code, context }).message.length).toBeGreaterThan(40);
      }
    }
  });
});

describe("shortReference", () => {
  it("keeps the last eight alphanumerics, lowercased", () => {
    expect(shortReference("iad1::7f3a2c19-4b8e")).toBe("2c194b8e");
  });

  it("returns null for an absent or empty id", () => {
    expect(shortReference(null)).toBeNull();
    expect(shortReference("   ")).toBeNull();
  });
});
