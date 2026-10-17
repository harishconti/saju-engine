import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { ANONYMOUS_SAMPLE_RETENTION_DAYS, ANONYMOUS_SAMPLE_RETENTION_LABEL } from "../retention";

/**
 * Retention numbers that more than one layer quotes, so they cannot drift.
 *
 * The failure this guards is quiet and embarrassing: the emailed link is presigned for as long as the
 * object lives, and if those two ever disagree the message says "the link works for 7 days" while the
 * reading is deleted on day 3 — a 404 sent to someone who asked for their chart. Nothing in the app
 * would error; the link would simply stop working, and only for the people who waited.
 *
 * The same number is stated in the privacy policy, so that is checked too: it is a published document
 * about data retention, which is exactly the kind of page that rots silently.
 */
describe("retention windows", () => {
  const read = (rel: string) => readFileSync(path.resolve(process.cwd(), rel), "utf8");

  it("is the window the privacy policy publishes", () => {
    const privacy = read("src/app/privacy/page.tsx");
    expect(privacy).toContain("ANONYMOUS_SAMPLE_RETENTION_LABEL");
    expect(ANONYMOUS_SAMPLE_RETENTION_LABEL).toBe(`${ANONYMOUS_SAMPLE_RETENTION_DAYS} days`);
  });

  it.each([
    ["src/lib/cleanup.ts", "the sweep's cutoff"],
    ["src/app/api/sample/email/route.ts", "the emailed link's lifetime"],
    ["src/components/sample-flow.tsx", "the confirmation copy"],
  ])("reads the window from the shared constant, not a literal (%s)", (file) => {
    const source = read(file);
    // A bare "7 days" / "3 days" written into any of these is how the two drift apart.
    expect(source).not.toMatch(/\b\d+ days\b/);
    expect(source).toContain("ANONYMOUS_SAMPLE_RETENTION_");
  });

  it("sweeps by the same number it advertises", () => {
    // `cleanup.ts` must not grow its own copy of the window. Asserted on the *expression*, not on the
    // file: other sweeps legitimately roll their own windows (profile inactivity is 23 months), so a
    // blanket "no numeric cutoff anywhere" rule would be wrong — as the first version of this test was.
    const cleanup = read("src/lib/cleanup.ts");
    expect(cleanup).toContain('from "./retention"');
    expect(cleanup).toContain("now.getTime() - ANONYMOUS_SAMPLE_RETENTION_DAYS * DAY_MS");
  });
});
