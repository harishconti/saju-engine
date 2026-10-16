import { prisma } from "./prisma";
import { isEngineConfigured } from "./engine";
import { parseChartSummary } from "./chart";

/**
 * Derive a chart summary for a profile and store it on `Profile.chartJson`.
 *
 * Why store rather than compute on read: the dashboard renders on every page load and the order flow
 * must show the pillars for confirmation BEFORE payment. Calling the engine on each read would be slow
 * and would make the dashboard fail whenever the engine is down.
 *
 * Best-effort by design: a profile is useful without a chart, and this is called from the create/update
 * paths, so a failure must not fail the save. Returns null when the engine is unavailable.
 */

interface ChartResponse {
  pillars?: { stem: string; branch: string; label?: string }[];
  dayMaster?: { char: string; element?: string; polarity?: string };
  elementBalance?: Record<string, number>;
  strength?: string;
  favorableElement?: string;
  favorableProvenance?: string;
  luckyCues?: Record<string, unknown>;
  caveats?: string[];
}

function engineBaseUrl(): string | null {
  const url = process.env.ENGINE_URL?.trim();
  return url ? url.replace(/\/+$/, "") : null;
}

export async function computeAndStoreChart(profileId: string): Promise<boolean> {
  if (!isEngineConfigured()) return false;

  const base = engineBaseUrl();
  const token = process.env.ENGINE_SERVICE_TOKEN?.trim();
  if (!base || !token) return false;

  const profile = await prisma.profile.findUnique({ where: { id: profileId } });
  if (!profile) return false;

  try {
    const res = await fetch(`${base}/chart`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${token}` },
      body: JSON.stringify({
        contractVersion: 1,
        fullName: profile.fullName,
        gender: profile.gender,
        birthDate: profile.birthDate.toISOString().slice(0, 10),
        birthTime: profile.birthTime,
        timeKnown: profile.timeKnown,
        timezone: profile.timezone,
        utcOffset: profile.utcOffset === null ? null : Number(profile.utcOffset),
        city: profile.city,
        latitude: profile.latitude === null ? null : Number(profile.latitude),
        longitude: profile.longitude === null ? null : Number(profile.longitude),
      }),
      signal: AbortSignal.timeout(20_000),
      cache: "no-store",
    });

    if (!res.ok) return false;

    const data = (await res.json()) as ChartResponse;
    const summary = parseChartSummary({
      pillars: data.pillars,
      dayMaster: data.dayMaster,
      elementBalance: data.elementBalance,
      strength: data.strength,
      favorableElement: data.favorableElement,
      favorableProvenance: data.favorableProvenance,
      luckyCues: data.luckyCues,
      caveats: data.caveats,
    });

    if (!summary) return false;

    await prisma.profile.update({
      where: { id: profileId },
      data: {
        chartJson: JSON.parse(JSON.stringify(summary)) as never,
        chartComputedAt: new Date(),
      },
    });
    return true;
  } catch {
    // Engine unreachable, timed out, or returned something unusable: leave the chart unset.
    return false;
  }
}
