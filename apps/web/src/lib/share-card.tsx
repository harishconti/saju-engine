import { ImageResponse } from "next/og";
import { loadOgFonts, OG_COLOURS } from "@/lib/og-fonts";
import { ELEMENTS, type ElementName } from "@/components/viz";
import type { ChartSummary } from "@/lib/chart";

/**
 * The shareable Day Master card: a 1080×1920 image for Instagram Stories, TikTok and WhatsApp.
 *
 * Why: the external product audit's biggest-gap finding was that nothing in the English market turns a
 * Saju result into something two people send each other. A shareable card is the growth loop the free
 * snapshot was missing — the reader's own chart, in a format built for a phone screen.
 *
 * ## The privacy rule on this file
 *
 * **`shareCardFields()` is deliberately the only thing the card is built from, and it cannot carry
 * birth data.** No date, no time, no place, no name. A chart is derived from those things, but the
 * card is going to be *published* by the reader, so it must contain nothing that identifies them — only
 * the derivation. That is enforced by construction here and asserted in
 * `src/lib/__tests__/share-card.test.ts`.
 */

export interface ShareCardFields {
  /** e.g. "Yin Metal" */
  dayMaster: string;
  /** The Hanja character of the day-master stem, e.g. 辛. */
  dayMasterChar: string;
  pillars: { label: string; stem: string; branch: string }[];
  elements: { name: ElementName; percent: number; colour: string }[];
  favorable?: string;
}

const ELEMENT_COLOUR: Record<string, string> = {
  Wood: OG_COLOURS.elements[0],
  Fire: OG_COLOURS.elements[1],
  Earth: OG_COLOURS.elements[2],
  Metal: OG_COLOURS.elements[3],
  Water: OG_COLOURS.elements[4],
};

/**
 * Reduce a chart summary to exactly what the card may show.
 *
 * Takes a `ChartSummary` and returns a *new* object containing only derived values, so a future change
 * cannot accidentally widen the card's surface by passing the profile through. Note the element list is
 * ordered by the canonical five-element order rather than by size, so the colour legend is stable.
 */
export function shareCardFields(summary: ChartSummary): ShareCardFields {
  const balance = summary.elementBalance ?? {};
  const total = Object.values(balance).reduce((sum, n) => sum + n, 0);

  return {
    dayMaster: [summary.dayMaster.polarity, summary.dayMaster.element].filter(Boolean).join(" "),
    dayMasterChar: summary.dayMaster.char,
    pillars: summary.pillars.map((p) => ({ label: p.label, stem: p.stem, branch: p.branch })),
    elements: ELEMENTS.map((name) => ({
      name,
      percent: total > 0 ? Math.round(((balance[name] ?? 0) / total) * 100) : 0,
      colour: ELEMENT_COLOUR[name] ?? OG_COLOURS.muted,
    })),
    favorable: summary.favorableElement ?? undefined,
  };
}

export async function buildShareCard(fields: ShareCardFields) {
  const fonts = await loadOgFonts();
  const { background, foreground, primary, muted } = OG_COLOURS;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          gap: 40,
          background,
          padding: "96px 80px",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontFamily: "Inter", fontSize: 30, letterSpacing: 8, color: primary }}>
            COSMIC SAJU
          </div>
          <div
            style={{
              display: "flex",
              width: 260,
              height: 8,
              marginTop: 24,
              backgroundImage: `linear-gradient(90deg, ${OG_COLOURS.elements.join(", ")})`,
            }}
          />
        </div>

        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexGrow: 1, justifyContent: "center" }}>
          <div style={{ fontFamily: "Inter", fontSize: 32, color: muted, letterSpacing: 4 }}>
            MY DAY MASTER
          </div>
          <div style={{ display: "flex", fontFamily: "SajuCJK", fontSize: 260, lineHeight: 1.1, color: foreground }}>
            {fields.dayMasterChar}
          </div>
          <div
            style={{
              display: "flex",
              fontFamily: "Cormorant Garamond",
              fontWeight: 600,
              fontSize: 96,
              lineHeight: 1.1,
              color: primary,
            }}
          >
            {fields.dayMaster || "Day Master"}
          </div>
          {/* The four pillars. Hanja, so they need the CJK face. */}
          <div style={{ display: "flex", gap: 28, marginTop: 56 }}>
            {fields.pillars.map((p) => (
              <div
                key={`${p.stem}${p.branch}`}
                style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}
              >
                <div style={{ fontFamily: "Inter", fontSize: 22, color: muted, letterSpacing: 2 }}>
                  {p.label.toUpperCase()}
                </div>
                <div style={{ fontFamily: "SajuCJK", fontSize: 64, color: foreground, lineHeight: 1 }}>
                  {p.stem}
                </div>
                <div style={{ fontFamily: "SajuCJK", fontSize: 64, color: foreground, lineHeight: 1 }}>
                  {p.branch}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 40 }}>
          {fields.elements.map((e) => (
            <div key={e.name} style={{ display: "flex", alignItems: "center", gap: 18 }}>
              <div style={{ fontFamily: "Inter", fontSize: 24, color: muted, width: 130 }}>{e.name}</div>
              <div style={{ display: "flex", flexGrow: 1, height: 14, background: "#1b1b23", borderRadius: 7 }}>
                <div
                  style={{
                    display: "flex",
                    width: `${Math.max(2, e.percent) * 8.8}px`,
                    height: 14,
                    background: e.colour,
                    borderRadius: 7,
                  }}
                />
              </div>
              <div style={{ fontFamily: "Inter", fontSize: 24, color: foreground, width: 80, textAlign: "right" }}>
                {`${e.percent}%`}
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontFamily: "Inter", fontSize: 26, color: muted }}>
            {fields.favorable ? `Favourable element: ${fields.favorable}` : "Korean Four Pillars"}
          </div>
          <div style={{ fontFamily: "Inter", fontSize: 30, color: primary }}>cosmicsaju.com</div>
        </div>
      </div>
    ),
    { width: 1080, height: 1920, fonts },
  );
}
