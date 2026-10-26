import { randomUUID } from "node:crypto";
import { Prisma } from "@prisma/client";
import { ZodError } from "zod";

/**
 * The error envelope for every route in this app: `{ error, code }`, always both keys.
 * Contract: docs/webapp/03-api-spec.md
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  /**
   * Structured context for callers that must branch on it, never rendered to a visitor.
   * `callEngine` puts the engine's own HTTP status here so `fulfilment` can tell an engine
   * refusal apart from a local error without parsing the message.
   */
  readonly details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  static badRequest(message = "Invalid request", code = "BAD_REQUEST") {
    return new ApiError(400, code, message);
  }
  static unauthorized(message = "Not signed in") {
    return new ApiError(401, "UNAUTHORIZED", message);
  }
  static forbidden(message = "Not allowed") {
    return new ApiError(403, "FORBIDDEN", message);
  }
  /** Use for cross-user access too: 404 discloses less than 403. */
  static notFound(message = "Not found") {
    return new ApiError(404, "NOT_FOUND", message);
  }
  static conflict(message = "Conflict", code = "CONFLICT") {
    return new ApiError(409, code, message);
  }
  static unprocessable(message = "Validation failed", code = "VALIDATION_FAILED") {
    return new ApiError(422, code, message);
  }
  static rateLimited(message = "Too many requests, please slow down") {
    return new ApiError(429, "RATE_LIMITED", message);
  }
  static unavailable(message = "Service unavailable", code = "SERVICE_UNAVAILABLE") {
    return new ApiError(503, code, message);
  }
}

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "content-type": "application/json", "cache-control": "no-store" },
  });
}

/**
 * Maps a thrown value to the error envelope. Never leaks internals: unknown errors become a
 * generic 500, and Prisma/zod specifics are translated rather than forwarded.
 *
 * Every failure is logged here, once, as its code and (when known) its request id. AU-10
 * (2026-10-26 audit): the visitor is told to quote that id to support, so it has to exist in
 * this server's log for *every* class of error — engine failures arrive as `ApiError`, and
 * before this only the last-resort branch emitted the id. The message text is deliberately not
 * logged: an `ApiError`'s message can name environment variables and an exception's can embed
 * birth data.
 *
 * `requestId`, when given, is echoed as `x-request-id`. It is a header rather than a body key
 * because every error body is exactly `{ error, code }`.
 */
export function errorResponse(err: unknown, requestId?: string): Response {
  const { response, code } = errorEnvelope(err);
  console.error(`route error code=${code}${requestId ? ` requestId=${requestId}` : ""}`);
  if (requestId) response.headers.set("x-request-id", requestId);
  return response;
}

function errorEnvelope(err: unknown): { response: Response; code: string } {
  if (err instanceof ApiError) {
    return { response: json({ error: err.message, code: err.code }, err.status), code: err.code };
  }

  if (err instanceof ZodError) {
    const first = err.issues[0];
    const path = first?.path?.join(".") ?? "";
    const detail = first ? `${path ? `${path}: ` : ""}${first.message}` : "Validation failed";
    return { response: json({ error: detail, code: "VALIDATION_FAILED" }, 422), code: "VALIDATION_FAILED" };
  }

  if (err instanceof Prisma.PrismaClientKnownRequestError) {
    if (err.code === "P2002") {
      return { response: json({ error: "Already exists", code: "DUPLICATE" }, 409), code: "DUPLICATE" };
    }
    if (err.code === "P2025") {
      return { response: json({ error: "Not found", code: "NOT_FOUND" }, 404), code: "NOT_FOUND" };
    }
    if (err.code === "P2003") {
      return { response: json({ error: "Related record is missing", code: "FOREIGN_KEY" }, 409), code: "FOREIGN_KEY" };
    }
    // P1xxx = the database could not be reached (auth, DNS, server down); P2024 = pool timeout.
    // These are availability problems, not bugs: report 503 so the client can say "try again"
    // instead of implying the request was malformed.
    if (err.code.startsWith("P1") || err.code === "P2024") {
      console.error("database unavailable", err.code);
      return {
        response: json({ error: "The database is temporarily unavailable", code: "DATABASE_UNAVAILABLE" }, 503),
        code: "DATABASE_UNAVAILABLE",
      };
    }
    console.error("prisma error", err.code);
    return { response: json({ error: "Database error", code: "DATABASE_ERROR" }, 500), code: "DATABASE_ERROR" };
  }

  // Thrown when the client cannot connect at all (bad credentials, suspended compute, no network).
  if (err instanceof Prisma.PrismaClientInitializationError) {
    console.error("database initialization failed", err.errorCode ?? "unknown");
    return {
      response: json({ error: "The database is temporarily unavailable", code: "DATABASE_UNAVAILABLE" }, 503),
      code: "DATABASE_UNAVAILABLE",
    };
  }

  // The class name only, never the message: an exception message can embed birth data.
  console.error("unhandled route error", err instanceof Error ? err.name : typeof err);
  return { response: json({ error: "Something went wrong", code: "INTERNAL_ERROR" }, 500), code: "INTERNAL_ERROR" };
}

type Handler<C = unknown> = (req: Request, ctx: C) => Promise<Response>;

/**
 * Front door for every route handler: catches everything and guarantees the error envelope.
 * Usage: `export const GET = handle(async (req) => { ... })`
 */
export function handle<C = unknown>(fn: Handler<C>): (req: Request, ctx: C) => Promise<Response> {
  return async (req: Request, ctx: C) => {
    // A short id that appears both in the response header and in this server's log, so a
    // visitor's "reference" is enough for support to find the request (AU-10). Generated only
    // on the error path's response; a successful call has nothing to trace.
    try {
      return await fn(req, ctx);
    } catch (err) {
      const requestId = randomUUID().replace(/[^a-z0-9]/gi, "").slice(0, 12).toLowerCase();
      return errorResponse(err, requestId);
    }
  };
}

/** Parse and validate a JSON body. Throws ApiError (400) on malformed JSON, ZodError on bad shape. */
export async function parseJson<S extends { parse: (v: unknown) => unknown }>(
  req: Request,
  schema: S,
): Promise<ReturnType<S["parse"]>> {
  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    throw ApiError.badRequest("Request body must be valid JSON", "MALFORMED_JSON");
  }
  return schema.parse(raw) as ReturnType<S["parse"]>;
}

/** Constant-time string comparison for shared secrets. */
export function timingSafeEqual(a: string | null, b: string | null): boolean {
  if (!a || !b || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/** Extracts a maintenance secret from either header convention. */
export function providedSecret(req: Request): string | null {
  const direct = req.headers.get("x-maintenance-secret");
  if (direct) return direct;
  const auth = req.headers.get("authorization");
  if (auth?.toLowerCase().startsWith("bearer ")) return auth.slice(7).trim();
  return null;
}

// Re-exported so every route keeps importing it from `@/lib/api`; the trusted-header
// logic lives in its own module so it can be unit-tested without Prisma/zod.
export { clientIp } from "./client-ip";
