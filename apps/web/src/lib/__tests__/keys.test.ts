import { describe, expect, it } from "vitest";
import { buildAnonymousKey, buildReportKey, buildSampleKey } from "../r2";
import { autoDelivers } from "../tiers";

/**
 * Object keys and the auto-deliver rule — both pure, both easy to get subtly wrong.
 *
 * The key scheme leads with the user id so a deletion request is one list + one batch delete, and
 * separates anonymous samples so the age sweep cannot touch a sample someone kept.
 */
describe("R2 key scheme", () => {
  it("leads report keys with the user id", () => {
    expect(buildReportKey("user_1", "order_1", "report_1", "pdf")).toBe(
      "reports/user_1/order_1/report_1.pdf",
    );
    expect(buildReportKey("user_1", "order_1", "report_1", "mp3")).toBe(
      "reports/user_1/order_1/report_1.mp3",
    );
  });

  it("keeps anonymous samples in their own prefix", () => {
    // That prefix is swept by age, which is only safe because nothing a user keeps lives there.
    expect(buildAnonymousKey("abc", "pdf")).toBe("reports/anonymous/abc/sample.pdf");
    // The free tier's artefact is the reading, and the PDF the engine is contractually required to
    // produce is deliberately left in this swept prefix rather than recorded anywhere.
    expect(buildAnonymousKey("abc", "html")).toBe("reports/anonymous/abc/sample.html");
  });

  it("keeps a user's saved sample OUT of the swept prefix", () => {
    const key = buildSampleKey("user_1", "sample_1");
    expect(key).toBe("reports/user_1/samples/sample_1.pdf");
    expect(key.startsWith("reports/anonymous/")).toBe(false);
    expect(buildSampleKey("user_1", "sample_1", "html")).toBe("reports/user_1/samples/sample_1.html");
  });

  it("does not let a user id escape its own prefix", () => {
    // A key must never be constructible such that one user's objects land under another's path.
    for (const userId of ["user_1", "user-2", "u3"]) {
      expect(buildReportKey(userId, "o", "r", "pdf").startsWith(`reports/${userId}/`)).toBe(true);
    }
  });
});

describe("autoDelivers (the requiresReview rule)", () => {
  it("auto-delivers the free tier", () => {
    expect(autoDelivers("SINGLE", "sample")).toBe(true);
  });

  it("never auto-delivers a paid tier", () => {
    expect(autoDelivers("SINGLE", "essential")).toBe(false);
    expect(autoDelivers("SINGLE", "deep")).toBe(false);
    expect(autoDelivers("COMPAT", "basic")).toBe(false);
    expect(autoDelivers("COMPAT", "deep")).toBe(false);
  });

  it("fails safe for an unknown tier: review, do not deliver", () => {
    // The dangerous default would be to deliver something nobody has looked at.
    expect(autoDelivers("SINGLE", "not-a-tier")).toBe(false);
    expect(autoDelivers("COMPAT", "not-a-tier")).toBe(false);
  });
});
