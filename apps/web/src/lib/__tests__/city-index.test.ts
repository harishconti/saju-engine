import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { decodeCityIndex } from "../cities";

/**
 * The shipped place index, checked as *data*.
 *
 * The picker is only as good as this file, and its failure mode is silent in both directions: too
 * little and someone cannot enter their own birthplace (`/sample` will not submit an unresolved
 * place), and a broken alias map tells them their town does not exist. The original hand-written table
 * had 156 cities, **12 of them in India**, and was missing every birthplace this repository's own
 * reports use — so these assertions are about coverage, not about code paths.
 *
 * `tools/build-cities.py` also verifies all of this at build time and refuses to write a broken index.
 * This test is the second lock on the same door, because the file is committed and could be replaced by
 * hand.
 */
const INDEX = JSON.parse(
  readFileSync(path.resolve(process.cwd(), "public/city-index.json"), "utf8"),
) as unknown;

describe("shipped place index", () => {
  const { cities, aliases } = decodeCityIndex(INDEX);

  it("covers the world at a usable depth", () => {
    expect(cities.length).toBeGreaterThan(50_000);
    const india = cities.filter((c) => c.countryCode === "IN").length;
    // Was 12 — the entire complaint. Assert a floor rather than a number, so a rebuild that shrinks the
    // set is caught without pinning an exact count.
    expect(india, "Indian coverage collapsed").toBeGreaterThan(2_000);
  });

  it("gives every place a real timezone and plausible coordinates", () => {
    for (const c of cities.slice(0, 5_000)) {
      // An IANA `Area/Location` name. A bare "UTC" would mean the zone index failed to line up — the
      // zones are stored once and referenced by index, so an off-by-one would be silent otherwise.
      expect(c.timezone, `${c.name} has no zone`).toMatch(/^[A-Za-z]+\/[A-Za-z_0-9+/-]+$/);
      expect(Math.abs(c.latitude)).toBeLessThanOrEqual(90);
      expect(Math.abs(c.longitude)).toBeLessThanOrEqual(180);
      expect(c.country.length).toBeGreaterThan(1);
      // A country resolved to its own code means `Intl.DisplayNames` failed; "IN" is not a country name.
      expect(c.country).not.toBe(c.countryCode);
    }
  });

  it("points every alias at a place that exists — a dead alias says 'that is not a real place'", () => {
    const shipped = new Set(cities.map((c) => `${c.name.toLowerCase()}|${c.countryCode}`));
    const dead = Object.entries(aliases)
      .filter(([, [name, cc]]) => !shipped.has(`${name.toLowerCase()}|${cc}`))
      .map(([alias, [name, cc]]) => `${alias} → ${name} (${cc})`);
    expect(dead).toEqual([]);
    expect(Object.keys(aliases).length).toBeGreaterThan(20);
  });

  it("keeps the renames people still write", () => {
    // The specific, checkable cases behind the alias map, in India and beyond.
    for (const alias of ["mysore", "bangalore", "bombay", "calcutta", "madras", "trivandrum", "poona"]) {
      expect(aliases[alias], alias).toBeDefined();
    }
  });
});
