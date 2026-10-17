import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Analytics is wired *silently*: a blocked script, an unmounted client, or an event fired from the
 * wrong place produces no error anywhere — you just get an empty dashboard and no way to tell
 * "nobody converted" from "the measurement never ran". So the wiring is asserted, not assumed.
 *
 * The CSP assertions exist for a specific precedent: `docs/webapp/13-launch-audit.md` records that
 * the CSP's `style-src`/`font-src` never allowed Google Fonts, so three typefaces silently never
 * loaded for any visitor. The analytics client is served same-origin (`/_vercel/insights/script`,
 * verified against the installed package), so `script-src 'self'` and `connect-src 'self'` are what
 * keep it working — a future allowlist that drops `'self'` would break it silently in the same way.
 */
describe("analytics wiring", () => {
  const read = (rel: string) => readFileSync(path.resolve(process.cwd(), rel), "utf8");

  it("mounts the analytics client in the root layout", () => {
    const layout = read("src/app/layout.tsx");
    expect(layout).toContain("@vercel/analytics/next");
    expect(layout).toContain("<Analytics />");
  });

  it("fires the funnel events from the funnel's own components", () => {
    expect(read("src/components/sample-flow.tsx")).toContain('track("snapshot_complete"');
    expect(read("src/components/dashboard/order-flow.tsx")).toContain('track("checkout_start"');
  });

  it("fires purchase server-side from the paid transition, not the browser redirect", () => {
    const webhook = read("src/app/api/webhooks/dodo/route.ts");
    expect(webhook).toContain("@vercel/analytics/server");
    expect(webhook).toContain('track("purchase"');
  });

  it("keeps 'self' in script-src and connect-src, so the same-origin client is not blocked", () => {
    const lines = read("next.config.ts").split("\n");
    // Match the directive itself (a template literal), not the comment block above it, which also
    // mentions the directive names.
    const directive = (name: string) => lines.find((line) => line.trim().startsWith("`" + name));
    const scriptSrc = directive("script-src");
    const connectSrc = directive("connect-src");
    expect(scriptSrc, "script-src directive not found in next.config.ts").toBeDefined();
    expect(connectSrc, "connect-src directive not found in next.config.ts").toBeDefined();
    expect(scriptSrc).toContain("'self'");
    expect(connectSrc).toContain("'self'");
  });
});
