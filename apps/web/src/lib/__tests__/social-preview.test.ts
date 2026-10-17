import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The social/search preview, guarded where it fails quietly.
 *
 * Three separate traps live here, and only one of them is loud:
 *  - Satori (`next/og`) cannot read a **variable** font — it dies mid-prerender with an opaque
 *    "Cannot read properties of undefined". Loud, but only at build time on the OG route.
 *  - Satori cannot read **woff2** at all. The brand faces ship as woff2, so dropping one straight
 *    into `_og-fonts/` is the obvious mistake. This asserts the format instead of trusting it.
 *  - The fallback meta description drifting back to opening on "not a Korean master" is **silent**
 *    — it just makes every search result and shared link worse. That was an external-audit finding.
 */
describe("social preview", () => {
  const read = (rel: string) => readFileSync(path.resolve(process.cwd(), rel), "utf8");
  const readBytes = (rel: string) => readFileSync(path.resolve(process.cwd(), rel));

  it("ships an Open Graph image route at the right size", () => {
    const route = read("src/app/opengraph-image.tsx");
    expect(route).toContain("ImageResponse");
    expect(route).toMatch(/width:\s*1200/);
    expect(route).toMatch(/height:\s*630/);
    expect(route).toContain('contentType = "image/png"');
  });

  it("gives Satori a static TTF, never the woff2 the web uses", () => {
    for (const face of ["CormorantGaramond-og.ttf", "Inter-og.ttf", "SajuCJK-og.ttf"]) {
      const head = readBytes(`src/lib/og-fonts/${face}`).subarray(0, 4);
      // 'wOF2' would be a woff2, which Satori refuses; 0x00010000 / 'OTTO' are real sfnt headers.
      expect(head.toString("latin1"), face).not.toBe("wOF2");
      const sfnt = head.equals(Buffer.from([0x00, 0x01, 0x00, 0x00])) || head.toString("latin1") === "OTTO";
      expect(sfnt, `${face} is not a TTF/OTF`).toBe(true);
    }
  });

  it("keeps the fallback description benefit-led, not open on the disavowal", () => {
    const layout = read("src/app/layout.tsx");
    const description = layout.slice(layout.indexOf("description:"), layout.indexOf("applicationName"));
    expect(description).not.toContain("not a Korean master");
    expect(description).toContain("free chart snapshot");
  });

  it("asks X/Twitter for the large card, so the preview image is used", () => {
    expect(read("src/app/layout.tsx")).toContain('card: "summary_large_image"');
  });
});
