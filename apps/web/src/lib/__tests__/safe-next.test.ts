/**
 * `safeNext` is the only place a post-sign-in `next` target is validated (AU-06).
 *
 * The table is the test: the original bug was a value nobody pictured — `/\evil.com` starts with a
 * single `/`, so the old prefix check let it through and the browser normalised the backslash into
 * `//evil.com`. Every value the brief calls out is pinned here, allowed and rejected alike.
 */
import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { safeNext } from "../safe-next";

const ALLOWED = ["/dashboard", "/dashboard?x=1", "/reports/abc#top"] as const;

const REJECTED = [
  "/\\evil.com", // one slash, one backslash — the original open redirect
  "/%5Cevil.com", // encoded backslash, decoded once before the test
  "//evil.com",
  "/\\\\evil.com", // two backslashes
  "https://evil.com",
  "javascript:alert(1)",
  "",
  "dashboard",
  "%2F%2Fevil.com", // encoded protocol-relative URL: not a path at all
  "/dash\u0000board", // NUL
  "/dash\u001fboard", // unit separator
  "/dash\u007fboard", // DEL
  "/\tevil.com", // tab: stripped by URL parsers, leaving //evil.com
  "/dash%00board", // encoded control character
] as const;

describe("safeNext", () => {
  it.each(ALLOWED)("keeps the same-origin path %j", (raw) => {
    expect(safeNext(raw)).toBe(raw);
  });

  it.each(REJECTED)("falls back for %j", (raw) => {
    expect(safeNext(raw)).toBe("/dashboard");
  });

  it("falls back for null and undefined", () => {
    expect(safeNext(null)).toBe("/dashboard");
    expect(safeNext(undefined)).toBe("/dashboard");
  });

  it("uses the caller's fallback", () => {
    expect(safeNext("//evil.com", "/login")).toBe("/login");
    expect(safeNext("/dashboard", "/login")).toBe("/dashboard");
  });
});

describe("both auth pages use the shared helper", () => {
  const webRoot = path.resolve(import.meta.dirname, "../../..");
  const pages = ["src/app/login/page.tsx", "src/app/auth/complete/page.tsx"];

  it.each(pages)("%s imports safeNext and defines no local copy", (relative) => {
    const source = fs.readFileSync(path.join(webRoot, relative), "utf8");
    expect(source).toMatch(/import\s*\{\s*safeNext\s*\}\s*from\s*"@\/lib\/safe-next"/);
    expect(source).not.toMatch(/function\s+safeNext\b/);
  });

  it("has exactly one declaration in src/", () => {
    const files = sourceFiles(path.join(webRoot, "src")).filter((file) =>
      /function\s+safeNext\b/.test(fs.readFileSync(file, "utf8")),
    );
    expect(files.map((file) => path.relative(webRoot, file))).toEqual(["src/lib/safe-next.ts"]);
  });
});

function sourceFiles(dir: string): string[] {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return sourceFiles(full);
    return /\.(ts|tsx)$/.test(entry.name) ? [full] : [];
  });
}
