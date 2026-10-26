/**
 * The engine error contract, as the webapp consumes it.
 *
 * AU-09 / AU-28 (2026-10-26 audit). Two properties, both load-bearing:
 *
 *  1. **Permanent only for birth data.** Before this, every 4xx from the engine was treated as a
 *     permanent rejection. The October misconfiguration came back as 422, so five days of
 *     `UPLOAD_HOSTS_UNCONFIGURED` were filed as "bad birth data" and never retried.
 *  2. **Keep the engine's status and code.** `callEngine` used to throw a single opaque
 *     `ENGINE_FAILED`, so the admin "Recent failures" view could never show the real cause. The
 *     thrown `ApiError` now carries the engine's status in `details` and its code in `code`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api";
import {
  PERMANENT_ENGINE_CODES,
  callEngine,
  isPermanentEngineFailure,
  type EnginePayload,
} from "@/lib/engine";

const fetchMock = vi.fn();

function reply(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

const PAYLOAD: EnginePayload = {
  contractVersion: 1,
  kind: "single",
  tier: "sample",
  uploadUrl: "https://r2.test/report.pdf",
  profileA: {
    fullName: "Test Visitor",
    gender: "F",
    birthDate: "1992-03-20",
    birthTime: "14:00",
    timeKnown: true,
    timezone: "Asia/Seoul",
    utcOffset: 9,
    city: "Seoul",
    latitude: 37.5665,
    longitude: 126.978,
  },
};

async function caught(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (err) {
    expect(err).toBeInstanceOf(ApiError);
    return err as ApiError;
  }
  throw new Error("expected the call to reject");
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(console, "error").mockImplementation(() => {});
  process.env.ENGINE_URL = "https://engine.test";
  process.env.ENGINE_SERVICE_TOKEN = "test-token";
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.clearAllMocks();
  delete process.env.ENGINE_URL;
  delete process.env.ENGINE_SERVICE_TOKEN;
});

describe("the permanent set", () => {
  it("contains only birth-data validation codes", () => {
    expect([...PERMANENT_ENGINE_CODES].sort()).toEqual([
      "INVALID_BIRTH_DATE",
      "INVALID_BIRTH_TIME",
      "INVALID_GENDER",
      "MISSING_LONGITUDE",
      "MISSING_TIMEZONE",
      "UNKNOWN_TIMEZONE",
    ]);
  });

  it("excludes the configuration and availability codes", () => {
    for (const code of [
      "UPLOAD_HOSTS_UNCONFIGURED",
      "UPLOAD_URL_NOT_ALLOWED",
      "UPLOAD_NOT_VERIFIED",
      "ENGINE_UNAUTHORIZED",
      "ENGINE_TIMEOUT",
      "ENGINE_UNREACHABLE",
      "ENGINE_FAILED",
      "RENDER_FAILED",
    ]) {
      expect(isPermanentEngineFailure(code)).toBe(false);
    }
  });

  it("includes the birth-data codes", () => {
    for (const code of [...PERMANENT_ENGINE_CODES]) {
      expect(isPermanentEngineFailure(code)).toBe(true);
    }
  });
});

describe("callEngine", () => {
  it("keeps a configuration failure retryable and names its code and status", async () => {
    fetchMock.mockResolvedValue(
      reply({ error: "no allowlist", code: "UPLOAD_HOSTS_UNCONFIGURED" }, 503),
    );

    const err = await caught(callEngine(PAYLOAD));

    expect(err.code).toBe("UPLOAD_HOSTS_UNCONFIGURED");
    expect(err.status).toBe(503);
    expect(err.details.engineStatus).toBe(503);
    expect(isPermanentEngineFailure(err.code)).toBe(false);
  });

  it("keeps a 422 that is not birth data retryable", async () => {
    // A storage-target refusal the engine used to answer with 422. The status alone must not
    // decide permanence any more — the code does.
    fetchMock.mockResolvedValue(
      reply({ error: "target not allowed", code: "UPLOAD_URL_NOT_ALLOWED" }, 422),
    );

    const err = await caught(callEngine(PAYLOAD));

    expect(err.code).toBe("UPLOAD_URL_NOT_ALLOWED");
    expect(err.details.engineStatus).toBe(422);
    expect(isPermanentEngineFailure(err.code)).toBe(false);
  });

  it("marks birth-data rejection permanent and keeps the engine's message", async () => {
    fetchMock.mockResolvedValue(
      reply(
        { error: "Date of birth must be YYYY-MM-DD.", code: "INVALID_BIRTH_DATE" },
        422,
      ),
    );

    const err = await caught(callEngine(PAYLOAD));

    expect(err.status).toBe(422);
    expect(err.code).toBe("INVALID_BIRTH_DATE");
    expect(err.message).toBe("Date of birth must be YYYY-MM-DD.");
    expect(isPermanentEngineFailure(err.code)).toBe(true);
  });

  it("does not put the engine's operator-facing message in the visitor path", async () => {
    // The engine's prose names environment variables. It is for the log, not the visitor.
    fetchMock.mockResolvedValue(
      reply(
        {
          error: "set R2_ENDPOINT or SAJU_UPLOAD_HOSTS",
          code: "UPLOAD_HOSTS_UNCONFIGURED",
        },
        503,
      ),
    );

    const err = await caught(callEngine(PAYLOAD));

    expect(err.message).not.toContain("R2_ENDPOINT");
    expect(err.message).toMatch(/try again/i);
  });

  it("records an engine 500 without a code as ENGINE_FAILED, still retryable", async () => {
    fetchMock.mockResolvedValue(reply({ error: "boom" }, 500));

    const err = await caught(callEngine(PAYLOAD));

    expect(err.status).toBe(503);
    expect(err.code).toBe("ENGINE_FAILED");
    expect(err.details.engineStatus).toBe(500);
    expect(isPermanentEngineFailure(err.code)).toBe(false);
  });

  it("reports an aborted call as ENGINE_TIMEOUT", async () => {
    fetchMock.mockRejectedValue(Object.assign(new Error("aborted"), { name: "AbortError" }));

    const err = await caught(callEngine(PAYLOAD, 50_000));

    expect(err.code).toBe("ENGINE_TIMEOUT");
    expect(err.status).toBe(503);
  });

  it("reports a transport failure as ENGINE_UNREACHABLE", async () => {
    fetchMock.mockRejectedValue(new TypeError("fetch failed"));

    const err = await caught(callEngine(PAYLOAD));

    expect(err.code).toBe("ENGINE_UNREACHABLE");
  });
});
