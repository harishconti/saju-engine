import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { buildShareCard, shareCardFields } from "../share-card";
import type { ChartSummary } from "../chart";

/**
 * The shareable card is the one artefact in this product a **reader publishes themselves**, so the
 * rule that matters is narrow and absolute: it may carry the *derivation* and nothing that identifies
 * the person. No birth date, no time, no place, no name.
 *
 * `shareCardFields()` is the only input the card is built from, so this file attacks it two ways —
 * behaviourally (feed it a summary polluted with profile fields; assert none survive) and at the
 * source level (assert the renderer never names a birth field, so it cannot start).
 */
const SUMMARY: ChartSummary = {
  pillars: [
    { stem: "甲", branch: "戌", label: "Year" },
    { stem: "癸", branch: "酉", label: "Month" },
    { stem: "辛", branch: "丑", label: "Day" },
    { stem: "乙", branch: "未", label: "Hour" },
  ],
  dayMaster: { char: "辛", element: "Metal", polarity: "Yin" },
  elementBalance: { Wood: 34, Fire: 4, Earth: 17, Metal: 29, Water: 16 },
  strength: "Balanced",
  favorableElement: "Water",
};

describe("share card fields", () => {
  it("carries the derived chart", () => {
    const fields = shareCardFields(SUMMARY);
    expect(fields.dayMaster).toBe("Yin Metal");
    expect(fields.dayMasterChar).toBe("辛");
    expect(fields.pillars.map((p) => `${p.stem}${p.branch}`)).toEqual(["甲戌", "癸酉", "辛丑", "乙未"]);
    expect(fields.favorable).toBe("Water");
  });

  it("returns exactly the known fields — nothing can be passed through", () => {
    const fields = shareCardFields(SUMMARY);
    expect(Object.keys(fields).sort()).toEqual([
      "dayMaster",
      "dayMasterChar",
      "elements",
      "favorable",
      "pillars",
    ]);
  });

  it("drops identifying data even when it is smuggled into the summary", () => {
    const polluted = {
      ...SUMMARY,
      // Everything a caller might accidentally spread in.
      fullName: "Harish Gurumoorthy",
      birthDate: "1992-06-04",
      birthTime: "03:10",
      city: "Pallipattu",
      latitude: 13.33,
      longitude: 79.45,
      timezone: "Asia/Kolkata",
      label: "Me",
    } as unknown as ChartSummary;

    const serialised = JSON.stringify(shareCardFields(polluted));
    for (const leak of ["Harish", "1992-06-04", "03:10", "Pallipattu", "79.45", "Kolkata", "13.33"]) {
      expect(serialised).not.toContain(leak);
    }
  });

  it("keeps the five elements in canonical order so the colour legend is stable", () => {
    expect(shareCardFields(SUMMARY).elements.map((e) => e.name)).toEqual([
      "Wood",
      "Fire",
      "Earth",
      "Metal",
      "Water",
    ]);
  });

  it("survives a missing element balance without producing NaN", () => {
    const fields = shareCardFields({ ...SUMMARY, elementBalance: {} });
    expect(fields.elements.every((e) => Number.isFinite(e.percent))).toBe(true);
    expect(fields.elements.every((e) => e.percent === 0)).toBe(true);
  });

  it("the renderer never names a birth field", () => {
    const source = readFileSync(path.resolve(process.cwd(), "src/lib/share-card.tsx"), "utf8");
    for (const forbidden of ["birthDate", "birthTime", "fullName", "latitude", "longitude", "timezone"]) {
      expect(source, `share-card.tsx must not reference ${forbidden}`).not.toContain(forbidden);
    }
  });
});

describe("share card render", () => {
  /**
   * Renders through Satori for real. This is the only test that would catch the font traps — a woff2
   * or a variable font makes `next/og` throw, and a face missing the Hanja makes the pillars render as
   * nothing at all, which no assertion about *content* would notice. Set `SHARE_CARD_OUT=/tmp/x.png`
   * to write the image out and look at it.
   */
  it("renders a 1080×1920 PNG", async () => {
    const image = await buildShareCard(shareCardFields(SUMMARY));
    expect(image.headers.get("content-type")).toContain("image/png");

    const bytes = Buffer.from(await image.arrayBuffer());
    expect(bytes.subarray(0, 8).toString("latin1")).toBe("\x89PNG\r\n\x1a\n");
    // PNG IHDR: width and height are big-endian uint32 at offsets 16 and 20.
    expect(bytes.readUInt32BE(16)).toBe(1080);
    expect(bytes.readUInt32BE(20)).toBe(1920);

    if (process.env.SHARE_CARD_OUT) writeFileSync(process.env.SHARE_CARD_OUT, bytes);
  });
});
