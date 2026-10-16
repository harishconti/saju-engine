import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import {
  buildAnonymousKey,
  buildReportKey,
  deleteObject,
  headObject,
  isR2Configured,
  presignGetUrl,
  presignPutUrl,
} from "../r2";

/**
 * Opt-in integration test for the storage layer.
 *
 * This is the highest-risk part of the report pipeline — presign correctness, the key scheme, and the
 * verify-after-upload step all fail silently if they are wrong. Unit tests cannot cover it, so it runs
 * against real R2 only when explicitly asked:
 *
 *   RUN_R2_TESTS=1 npx vitest run src/lib/__tests__/r2.integration.test.ts
 *
 * Safety: refuses to run against a bucket whose name does not look like a dev/test bucket, so this can
 * never write into production storage.
 */

function loadDotEnv() {
  const candidates = [
    path.resolve(import.meta.dirname, "../../../.env"),
    path.resolve(import.meta.dirname, "../../../.env.local"),
  ];
  for (const file of candidates) {
    if (!fs.existsSync(file)) continue;
    for (const line of fs.readFileSync(file, "utf8").split("\n")) {
      const s = line.trim();
      if (!s || s.startsWith("#") || !s.includes("=")) continue;
      const i = s.indexOf("=");
      const k = s.slice(0, i).trim();
      const v = s.slice(i + 1).trim().replace(/^["']|["']$/g, "");
      if (k && !(k in process.env)) process.env[k] = v;
    }
  }
}

if (process.env.RUN_R2_TESTS === "1") loadDotEnv();

const bucket = process.env.R2_BUCKET ?? "";
const looksLikeDevBucket = /dev|test/i.test(bucket);
const enabled = process.env.RUN_R2_TESTS === "1" && isR2Configured() && looksLikeDevBucket;

describe.skipIf(!enabled)("R2 storage round-trip (opt-in: RUN_R2_TESTS=1)", () => {
  it("presigns a PUT, verifies with HeadObject, presigns a GET, then deletes", async () => {
    const key = `tests/${Date.now()}-probe.pdf`;
    const body = new TextEncoder().encode("%PDF-1.4\n% round-trip probe\n");

    // 1. Presigned PUT — what the engine service is handed.
    const putUrl = await presignPutUrl(key, "application/pdf", 120);
    expect(putUrl).toContain("X-Amz-Signature");
    expect(putUrl.startsWith("https://")).toBe(true);

    const put = await fetch(putUrl, {
      method: "PUT",
      body,
      headers: { "content-type": "application/pdf" },
    });
    expect(put.ok, `PUT failed: ${put.status}`).toBe(true);

    // 2. The verify step the dispatcher relies on. Without it a "successful" render can leave a
    //    Report row pointing at nothing.
    const head = await headObject(key);
    expect(head?.size).toBe(body.byteLength);

    // 3. Presigned GET — what a client download resolves to.
    const getUrl = await presignGetUrl(key, 120);
    const got = await fetch(getUrl);
    expect(got.ok).toBe(true);
    expect((await got.arrayBuffer()).byteLength).toBe(body.byteLength);

    // 4. Delete, then confirm it is really gone.
    await deleteObject(key);
    expect(await headObject(key)).toBeNull();
  }, 30_000);

  it("builds keys that lead with the user id", () => {
    // Leading with userId is what makes a GDPR/DPDP erasure one list + one batch delete.
    expect(buildReportKey("user_1", "order_1", "report_1", "pdf")).toBe(
      "reports/user_1/order_1/report_1.pdf",
    );
    expect(buildReportKey("user_1", "order_1", "report_1", "md")).toBe(
      "reports/user_1/order_1/report_1.md",
    );
    expect(buildAnonymousKey("abc", "pdf")).toBe("reports/anonymous/abc/sample.pdf");
  });

  it("returns null for a key that does not exist rather than throwing", async () => {
    expect(await headObject(`tests/definitely-not-here-${Date.now()}.pdf`)).toBeNull();
  }, 15_000);

  it("is private: a bucket-scoped URL without a signature cannot list", async () => {
    const endpoint = process.env.R2_ENDPOINT!.replace(/\/+$/, "");
    const res = await fetch(`${endpoint}/${bucket}?list-type=2`);
    expect(res.ok).toBe(false); // unsigned access must be refused
  }, 15_000);
});
