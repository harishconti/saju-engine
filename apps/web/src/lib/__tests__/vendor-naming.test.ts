import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Customer-facing text must name the processor that actually exists.
 *
 * The merchant of record moved from Lemon Squeezy to **Dodo Payments**, and the migration updated the
 * code and the documentation but missed the *customer-facing prose*: the privacy policy (four times),
 * the terms, the refund policy, and the checkout confirmation all kept naming a company that no longer
 * processes anything. That is the worst place to be wrong — the privacy policy names our
 * sub-processors, and the checkout tells someone who is taking their money.
 *
 * This is a lint-like guard rather than a behavioural test, and deliberately so: the failure mode is a
 * rename that misses files, which no amount of runtime testing would catch.
 */
describe("customer-facing vendor naming", () => {
  const files = [
    "src/app/privacy/page.tsx",
    "src/app/terms/page.tsx",
    "src/app/refund-policy/page.tsx",
    "src/components/dashboard/order-flow.tsx",
  ];

  const read = (rel: string) => readFileSync(path.resolve(process.cwd(), rel), "utf8");

  it.each(files)("%s names Dodo Payments as the merchant of record", (rel) => {
    expect(read(rel)).toContain("Dodo Payments");
  });

  it.each(files)("%s does not name a processor we no longer use", (rel) => {
    const src = read(rel);
    for (const stale of ["Lemon Squeezy", "Lemonsqueezy", "lemonsqueezy", "Paddle"]) {
      expect(src).not.toContain(stale);
    }
  });

  it("the privacy policy names every processor it relies on", () => {
    const privacy = read("src/app/privacy/page.tsx");
    for (const processor of [
      "Neon", // database + auth
      "Cloudflare", // R2 storage
      "Vercel", // hosting
      "Resend", // transactional email
      "Dodo Payments", // merchant of record
      "Hostinger", // the mailbox holding correspondence
      "Google", // optional sign-in
    ]) {
      expect(privacy).toContain(processor);
    }
  });
});
