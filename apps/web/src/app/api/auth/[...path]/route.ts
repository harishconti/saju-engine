import { errorResponse } from "@/lib/api";
import { auth } from "@/lib/auth/server";

/**
 * Pass-through proxy for Neon Auth.
 *
 * Every verb is forwarded to the Neon Auth handler, so the browser only ever talks to our own
 * origin. Mounted at /api/auth/[...path] — the browser client is configured for this by default.
 */

type Ctx = { params: Promise<{ path: string[] }> };
type Method = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

async function dispatch(method: Method, req: Request, ctx: Ctx): Promise<Response> {
  try {
    const handler = auth.handler()[method] as unknown as (r: Request, c: Ctx) => Promise<Response>;
    return await handler(req, ctx);
  } catch (err) {
    return errorResponse(err);
  }
}

export const GET = (req: Request, ctx: Ctx) => dispatch("GET", req, ctx);
export const POST = (req: Request, ctx: Ctx) => dispatch("POST", req, ctx);
export const PUT = (req: Request, ctx: Ctx) => dispatch("PUT", req, ctx);
export const DELETE = (req: Request, ctx: Ctx) => dispatch("DELETE", req, ctx);
export const PATCH = (req: Request, ctx: Ctx) => dispatch("PATCH", req, ctx);
