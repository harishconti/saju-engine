import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

/**
 * The two faces Satori can use, for `next/og` (the Open Graph card and the shareable Day Master card).
 *
 * Satori accepts **ttf / otf / woff** — not woff2, and not a variable font (it dies mid-render with an
 * opaque "Cannot read properties of undefined"). The brand faces the *web* uses are both, so
 * `tools/build-og-fonts.py` derives these statics from the same outlines. Regenerate with it if the
 * web fonts ever change.
 *
 * Paths come from `import.meta.url` rather than `process.cwd()` so Next's output tracing follows them
 * into the serverless bundle. (A `fetch(new URL(...))` on a `file:` URL throws "not implemented... yet"
 * in this Node, hence `fs`.)
 */
export async function loadOgFonts() {
  const read = (name: string) =>
    readFile(fileURLToPath(new URL(`./og-fonts/${name}`, import.meta.url)));

  const [display, body, hanja] = await Promise.all([
    read("CormorantGaramond-og.ttf"),
    read("Inter-og.ttf"),
    read("SajuCJK-og.ttf"),
  ]);

  return [
    { name: "Cormorant Garamond", data: display, weight: 600 as const, style: "normal" as const },
    { name: "Inter", data: body, weight: 400 as const, style: "normal" as const },
    // The ten stems and twelve branches (plus 四, the site's seal character), so a four-pillars card
    // renders Hanja rather than nothing. Set `fontFamily: "SajuCJK"` on those elements explicitly —
    // do not rely on cross-family fallback.
    { name: "SajuCJK", data: hanja, weight: 400 as const, style: "normal" as const },
  ];
}

/** The brand tokens Satori needs as literals — it cannot read CSS custom properties. */
export const OG_COLOURS = {
  background: "#08080d",
  foreground: "#ece8df",
  primary: "#c8a34a",
  muted: "#9a958c",
  /** Wood · Fire · Earth · Metal · Water, matching `--el-*` in globals.css. */
  elements: ["#4fae7c", "#e0674f", "#d9b44a", "#b9bec7", "#4f8fd9"],
} as const;
