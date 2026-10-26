import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

/**
 * AU-27 (2026-10-26 audit): `flagInactiveProfiles` ran `updateMany({ data: {} })` — a query that
 * writes nothing, on a schema with no field to flag. It read as a retention control in the cron
 * while enforcing nothing. There is no column to warn into, so the honest fix is to remove it
 * rather than keep a no-op that promises a sweep the schema cannot perform.
 */

const source = fs.readFileSync(path.resolve(import.meta.dirname, "../cleanup.ts"), "utf8");

describe("cleanup retention flag (AU-27)", () => {
  it("no longer runs a no-op profile update", () => {
    expect(source).not.toMatch(/data:\s*\{\s*\}/);
  });

  it("no longer carries the flagInactiveProfiles function or its call site", () => {
    expect(source).not.toContain("flagInactiveProfiles");
  });
});
