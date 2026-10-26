/**
 * A visitor's support reference must exist in the server log.
 *
 * AU-10 (2026-10-26 audit): `handle` gives every error a short request id, puts it in
 * `x-request-id`, and the sample's failure message tells the visitor to quote it. But only the
 * last-resort unhandled branch ever logged that id — every `ApiError` (which is how all engine
 * failures arrive: `UPLOAD_HOSTS_UNCONFIGURED`, `ENGINE_TIMEOUT`, `UPLOAD_NOT_VERIFIED`),
 * every `ZodError` and every known Prisma fault returned without a trace, so the reference
 * pointed at a request support could not find.
 *
 * These tests pin one log line per error, carrying the code and the id, and keep the message
 * text out of it: an `ApiError`'s message can name env vars and an exception's can carry birth
 * data, neither of which belongs in the log.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { ZodError } from "zod";

import { ApiError, errorResponse } from "@/lib/api";

const REQUEST_ID = "3c4d5e6f7a8b";

function loggedText(): string[] {
  return (vi.mocked(console.error).mock.calls as unknown[][]).map((args) =>
    args.map((arg) => (typeof arg === "string" ? arg : String(arg))).join(" "),
  );
}

/** Every log line that mentions the visitor's reference. Must be exactly one. */
function linesQuoting(requestId: string): string[] {
  return loggedText().filter((line) => line.includes(requestId));
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("errorResponse logging", () => {
  it("logs the code and request id for an ApiError, exactly once, and keeps the envelope", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    const response = errorResponse(
      new ApiError(503, "UPLOAD_HOSTS_UNCONFIGURED", "set R2_ENDPOINT or SAJU_UPLOAD_HOSTS"),
      REQUEST_ID,
    );

    // The response contract is untouched: header for the reference, body exactly { error, code }.
    expect(response.status).toBe(503);
    expect(response.headers.get("x-request-id")).toBe(REQUEST_ID);
    await expect(response.json()).resolves.toEqual({
      error: "set R2_ENDPOINT or SAJU_UPLOAD_HOSTS",
      code: "UPLOAD_HOSTS_UNCONFIGURED",
    });

    const quoting = linesQuoting(REQUEST_ID);
    expect(quoting).toHaveLength(1);
    expect(quoting[0]).toContain("UPLOAD_HOSTS_UNCONFIGURED");
    // Operator-facing prose (and anything else in `message`) stays out of the log.
    expect(loggedText().join("\n")).not.toContain("R2_ENDPOINT");
  });

  it("logs a ZodError's code and request id, exactly once", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    const zod = new ZodError([{ code: "custom", path: ["birthDate"], message: "Required" }]);
    const response = errorResponse(zod, REQUEST_ID);

    expect(response.status).toBe(422);
    expect(response.headers.get("x-request-id")).toBe(REQUEST_ID);

    const quoting = linesQuoting(REQUEST_ID);
    expect(quoting).toHaveLength(1);
    expect(quoting[0]).toContain("VALIDATION_FAILED");
  });

  it("keeps the class name for an unexpected error and does not log its message", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    // An exception message can embed birth data, so the existing discipline is to log the class
    // only. The new code+id line must not undo that.
    const err = new Error("1992-03-20 14:00 Seoul");
    err.name = "RangeError";
    const response = errorResponse(err, REQUEST_ID);

    expect(response.status).toBe(500);
    expect(response.headers.get("x-request-id")).toBe(REQUEST_ID);

    const text = loggedText().join("\n");
    expect(text).toContain("RangeError");
    expect(text).not.toContain("1992-03-20");
    expect(text).toContain("INTERNAL_ERROR");

    // Still one line quoting the reference: the existing unhandled log must not repeat it.
    expect(linesQuoting(REQUEST_ID)).toHaveLength(1);
  });

  it("logs once per error even when a request id is absent", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});

    errorResponse(ApiError.unavailable("try later"));

    // Webhook routes call errorResponse without an id; the code is still useful.
    expect(loggedText().filter((line) => line.includes("SERVICE_UNAVAILABLE"))).toHaveLength(1);
  });
});
