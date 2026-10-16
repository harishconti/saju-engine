/**
 * Parsed shape of `Profile.chartJson` — the derived chart summary computed once by the engine
 * service when a profile is created.
 *
 * Why it exists: the order flow must show the derived four pillars for confirmation BEFORE payment
 * (CLAUDE.md ground rule: no silent auto-calculated pillars), and the dashboard needs something to
 * show without calling the engine on every page load.
 *
 * Contract: docs/webapp/05-report-pipeline.md §2 (engine `/chart`).
 */

export interface ChartPillar {
  stem: string;
  branch: string;
  label: string;
}

export interface ChartSummary {
  pillars: ChartPillar[];
  dayMaster: { char: string; element?: string; polarity?: string };
  elementBalance: Record<string, number>;
  strength?: string;
  favorableElement?: string;
  favorableProvenance?: string;
  luckyCues?: { colors?: string[]; direction?: string; numbers?: (string | number)[] };
  /** Honest caveats the engine raised, e.g. an hour-boundary or solar-term-boundary knife-edge. */
  caveats?: string[];
}

export function parseChartSummary(json: unknown): ChartSummary | null {
  if (!json || typeof json !== "object") return null;
  const c = json as Partial<ChartSummary>;
  if (!Array.isArray(c.pillars) || c.pillars.length === 0) return null;
  if (!c.dayMaster || typeof c.dayMaster.char !== "string") return null;
  return {
    pillars: c.pillars.map((p, i) => ({
      stem: String(p?.stem ?? ""),
      branch: String(p?.branch ?? ""),
      label: String(p?.label ?? ["Year", "Month", "Day", "Hour"][i] ?? `P${i + 1}`),
    })),
    dayMaster: {
      char: c.dayMaster.char,
      element: c.dayMaster.element,
      polarity: c.dayMaster.polarity,
    },
    elementBalance: (c.elementBalance ?? {}) as Record<string, number>,
    strength: c.strength,
    favorableElement: c.favorableElement,
    favorableProvenance: c.favorableProvenance,
    luckyCues: c.luckyCues,
    caveats: Array.isArray(c.caveats) ? c.caveats : undefined,
  };
}

import type { ElementCounts } from "@/components/viz";

/** Element counts normalised to the five names, for the viz components. */
export function elementCountsFrom(summary: ChartSummary | null): ElementCounts {
  const out: ElementCounts = { Wood: 0, Fire: 0, Earth: 0, Metal: 0, Water: 0 };
  if (!summary) return out;
  for (const [k, v] of Object.entries(summary.elementBalance)) {
    const key = (k.charAt(0).toUpperCase() + k.slice(1).toLowerCase()) as keyof ElementCounts;
    if (key in out && typeof v === "number") out[key] = v;
  }
  return out;
}
