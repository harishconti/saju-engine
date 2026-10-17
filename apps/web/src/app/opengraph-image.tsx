import { ImageResponse } from "next/og";
import { loadOgFonts, OG_COLOURS } from "@/lib/og-fonts";

/**
 * The Open Graph card.
 *
 * Why it exists: the site's own metadata is honest but text-only, so a link shared on Instagram, X,
 * WhatsApp or Reddit rendered as a bare URL with no preview — which undercuts a social-led strategy
 * (external product audit, 2026-10-17). This is the preview.
 *
 * It is a **static brand card**, one for the whole site, deliberately: a per-page or per-snapshot image
 * is the audit's "ideally", and it is now cheap to add because `loadOgFonts()` exists.
 *
 * No Hanja here — the Latin subsets carry no CJK, so a four-pillars motif would render as tofu. The
 * element dots carry the brand instead and need no typeface at all.
 */
export const alt = "Cosmic Saju — Korean Four Pillars readings";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function OpengraphImage() {
  const fonts = await loadOgFonts();
  const { background, foreground, primary, muted, elements } = OG_COLOURS;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background,
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
              color: primary,
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
              backgroundImage: `linear-gradient(90deg, ${elements.join(", ")})`,
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
              color: foreground,
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
              color: muted,
              maxWidth: 900,
            }}
          >
            The interpretation is the hard part — and a person reviews it before it reaches you.
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            {elements.map((colour) => (
              <div
                key={colour}
                style={{ display: "flex", width: 22, height: 22, borderRadius: 11, background: colour }}
              />
            ))}
            <div style={{ fontFamily: "Inter", fontSize: 26, color: muted, marginLeft: 10 }}>
              Korean Four Pillars, read properly
            </div>
          </div>
          <div style={{ fontFamily: "Inter", fontSize: 28, color: primary }}>cosmicsaju.com</div>
        </div>
      </div>
    ),
    { ...size, fonts },
  );
}
