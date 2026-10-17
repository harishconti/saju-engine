import { ImageResponse } from "next/og";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

/**
 * The Open Graph card.
 *
 * Why it exists: the site's own metadata is honest but text-only, so a link shared on Instagram, X,
 * WhatsApp or Reddit rendered as a bare URL with no preview — which undercuts a social-led strategy
 * (external product audit, 2026-10-17). This is the preview.
 *
 * It is a **static brand card**, one for the whole site, deliberately: a per-page or per-snapshot
 * image is the audit's "ideally", and it is now cheap to add because the font pipeline below exists.
 *
 * Two things that are easy to get wrong here:
 *  1. Satori (inside `next/og`) needs **ttf/otf/woff — not woff2**. The brand faces ship as woff2
 *     for the web, so `tools/build-og-fonts.py` re-derives TTFs from those same outlines.
 *  2. No Hanja. The Latin subsets carry no CJK, so a four-pillars motif here would render as tofu.
 *     The element dots carry the brand instead, and they need no typeface at all.
 */
export const alt = "Cosmic Saju — Korean Four Pillars readings";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Brand tokens, from apps/web/src/app/globals.css. Satori cannot read CSS custom properties.
const BACKGROUND = "#08080d";
const FOREGROUND = "#ece8df";
const PRIMARY = "#c8a34a";
const MUTED = "#9a958c";
const ELEMENTS = ["#4fae7c", "#e0674f", "#d9b44a", "#b9bec7", "#4f8fd9"]; // wood fire earth metal water

/** Local fonts are read by a path derived from `import.meta.url` so output tracing keeps them. */
async function loadFonts() {
  const readFont = (name: string) =>
    readFile(fileURLToPath(new URL(`./_og-fonts/${name}`, import.meta.url)));
  const [display, body] = await Promise.all([
    readFont("CormorantGaramond-og.ttf"),
    readFont("Inter-og.ttf"),
  ]);
  return [
    { name: "Cormorant Garamond", data: display, weight: 600 as const, style: "normal" as const },
    { name: "Inter", data: body, weight: 400 as const, style: "normal" as const },
  ];
}

export default async function OpengraphImage() {
  const fonts = await loadFonts();

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: BACKGROUND,
          padding: "72px 80px",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{
              fontFamily: "Inter",
              fontSize: 26,
              letterSpacing: 6,
              textTransform: "uppercase",
              color: PRIMARY,
            }}
          >
            Cosmic Saju
          </div>
          {/* The elemental rule the rest of the design uses. */}
          <div
            style={{
              display: "flex",
              width: 220,
              height: 6,
              marginTop: 20,
              backgroundImage: `linear-gradient(90deg, ${ELEMENTS.join(", ")})`,
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{
              fontFamily: "Cormorant Garamond",
              fontWeight: 600,
              fontSize: 104,
              lineHeight: 1.05,
              color: FOREGROUND,
              letterSpacing: -1,
            }}
          >
            Your chart is arithmetic.
          </div>
          <div
            style={{
              fontFamily: "Inter",
              fontSize: 34,
              lineHeight: 1.4,
              marginTop: 24,
              color: MUTED,
              maxWidth: 900,
            }}
          >
            The interpretation is the hard part — and a person reviews it before it reaches you.
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            {ELEMENTS.map((colour) => (
              <div
                key={colour}
                style={{ display: "flex", width: 22, height: 22, borderRadius: 11, background: colour }}
              />
            ))}
            <div style={{ fontFamily: "Inter", fontSize: 26, color: MUTED, marginLeft: 10 }}>
              Korean Four Pillars, read properly
            </div>
          </div>
          <div style={{ fontFamily: "Inter", fontSize: 28, color: PRIMARY }}>cosmicsaju.com</div>
        </div>
      </div>
    ),
    { ...size, fonts },
  );
}
