/**
 * AU-37 (2026-10-26 audit): a presigned PUT must sign the `content-type` the engine sends.
 *
 * SigV4 signs `host` by default, so the upload URL alone says nothing about the body's media type.
 * The engine sends an exact `Content-Type` on every PUT, and R2 rejects the upload with
 * `SignatureDoesNotMatch` if that header is not one of the signed headers. The sample and fulfilment
 * paths therefore sign the media type explicitly, and this test pins both facts:
 *
 *   - `X-Amz-SignedHeaders` names `content-type`; and
 *   - the signature changes with the media type, which is only true if the *value* is signed.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/prisma", () => ({ prisma: {} }));

const { presignPutUrl } = await import("@/lib/r2");

const KEY = "reports/u1/o1/r1.html";
const FROZEN = new Date("2026-10-26T00:00:00Z");

function signedHeaders(url: string): string {
  return new URL(url).searchParams.get("X-Amz-SignedHeaders") ?? "";
}

function signature(url: string): string {
  return new URL(url).searchParams.get("X-Amz-Signature") ?? "";
}

beforeEach(() => {
  process.env.R2_ACCOUNT_ID = "test-account";
  process.env.R2_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE";
  process.env.R2_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";
  process.env.R2_BUCKET = "test-bucket";
  delete process.env.R2_ENDPOINT;
  vi.useFakeTimers();
  vi.setSystemTime(FROZEN);
});

afterEach(() => {
  vi.useRealTimers();
  delete process.env.R2_ACCOUNT_ID;
  delete process.env.R2_ACCESS_KEY_ID;
  delete process.env.R2_SECRET_ACCESS_KEY;
  delete process.env.R2_BUCKET;
});

describe("presignPutUrl — signed content type (AU-37)", () => {
  it("signs the exact media type the engine sends for a reading", async () => {
    const url = await presignPutUrl(KEY, "text/html; charset=utf-8");
    expect(signedHeaders(url)).toContain("content-type");
  });

  it("binds the media type *value* into the signature", async () => {
    const html = await presignPutUrl(KEY, "text/html; charset=utf-8");
    const pdf = await presignPutUrl(KEY, "application/pdf");
    // Same key, same instant, same credentials: only the media type differs.
    expect(signature(html)).not.toBe(signature(pdf));
  });

  it("defaults to the PDF media type", async () => {
    const dflt = await presignPutUrl(KEY);
    const explicit = await presignPutUrl(KEY, "application/pdf");
    expect(signature(dflt)).toBe(signature(explicit));
    expect(signedHeaders(dflt)).toContain("content-type");
  });
});
