import { createHash } from "node:crypto";
import type { Order, Profile } from "@prisma/client";
import { ApiError } from "./api";

/**
 * Client for the report engine service (Vercel project #2).
 *
 * Contract: docs/webapp/05-report-pipeline.md §2. The engine is stateless, holds no database
 * credentials, and receives a presigned R2 PUT url so the PDF never crosses a response body.
 */

export const ENGINE_CONTRACT_VERSION = 1;

export interface EngineProfile {
  fullName: string;
  gender: "M" | "F";
  birthDate: string; // YYYY-MM-DD
  birthTime: string; // HH:MM
  timeKnown: boolean;
  timezone: string | null;
  utcOffset: number | null;
  city: string;
  latitude: number | null;
  longitude: number | null;
}

export interface EnginePayload {
  contractVersion: number;
  kind: "single" | "compat";
  tier: string;
  uploadUrl: string;
  /** Where the engine should also PUT the source markdown, so the audio script and the
   *  audit trail derive from the artefact that was actually reviewed. */
  mdUploadUrl?: string;
  profileA: EngineProfile;
  profileB?: EngineProfile;
  favorableOverrideA?: string | null;
  favorableOverrideB?: string | null;
}

export interface EngineResult {
  sha256: string;
  bytes: number;
  engineVersion: string;
  durationMs?: number;
  /**
   * Rendered page count. Optional because the HTML/Playwright backend cannot report it — production
   * renders with ReportLab, which counts pages during its two-pass build and now returns the total.
   */
  pages?: number | null;
}

function engineUrl(): string {
  const url = process.env.ENGINE_URL?.trim();
  if (!url) throw ApiError.unavailable("Report engine is not configured", "ENGINE_UNAVAILABLE");
  return url.replace(/\/+$/, "");
}

export function isEngineConfigured(): boolean {
  return Boolean(process.env.ENGINE_URL?.trim() && process.env.ENGINE_SERVICE_TOKEN?.trim());
}

export function profileToEngine(p: Profile): EngineProfile {
  return {
    fullName: p.fullName,
    gender: p.gender,
    birthDate: p.birthDate.toISOString().slice(0, 10),
    birthTime: p.birthTime,
    timeKnown: p.timeKnown,
    timezone: p.timezone ?? null,
    utcOffset: p.utcOffset === null || p.utcOffset === undefined ? null : Number(p.utcOffset),
    city: p.city,
    latitude: p.latitude === null || p.latitude === undefined ? null : Number(p.latitude),
    longitude: p.longitude === null || p.longitude === undefined ? null : Number(p.longitude),
  };
}

export function engineKindFor(order: Pick<Order, "kind">): "single" | "compat" {
  return order.kind === "COMPAT" ? "compat" : "single";
}

/**
 * A stable hash of everything that affects the rendered chart.
 * Used to short-circuit a regenerate that would produce identical output (409 NO_CHANGE).
 */
export function chartHash(a: EngineProfile, b?: EngineProfile | null, overrideA?: string | null, overrideB?: string | null): string {
  return createHash("sha256")
    .update(JSON.stringify({ a, b: b ?? null, overrideA: overrideA ?? null, overrideB: overrideB ?? null }))
    .digest("hex");
}

/**
 * Ask the engine to render and PUT the PDF to `uploadUrl`.
 *
 * Long timeout: the engine imports pandas on a cold start (~1–2 s) and a deep report takes ~1.5 s
 * warm. 120 s leaves room for a cold start plus a slow queue.
 */
export async function callEngine(payload: EnginePayload, timeoutMs = 120_000): Promise<EngineResult> {
  const token = process.env.ENGINE_SERVICE_TOKEN?.trim();
  if (!token) throw ApiError.unavailable("Report engine token is not configured", "ENGINE_UNAVAILABLE");
  if (payload.contractVersion !== ENGINE_CONTRACT_VERSION) {
    throw ApiError.badRequest("Engine contract version mismatch", "CONTRACT_VERSION_MISMATCH");
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${engineUrl()}/generate`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
      cache: "no-store",
    });

    if (res.ok) {
      const data = (await res.json()) as EngineResult;
      return data;
    }

    // 4xx from the engine is permanent (bad birth data will not improve on retry).
    const body = (await res.json().catch(() => ({}))) as { error?: string; code?: string };
    if (res.status >= 400 && res.status < 500) {
      throw new ApiError(res.status === 422 ? 422 : 400, body.code ?? "ENGINE_REJECTED", body.error ?? "The engine rejected this chart");
    }
    throw ApiError.unavailable("The report engine failed", "ENGINE_FAILED");
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof Error && err.name === "AbortError") {
      throw ApiError.unavailable("The report engine timed out", "ENGINE_TIMEOUT");
    }
    throw ApiError.unavailable("The report engine is unreachable", "ENGINE_UNREACHABLE");
  } finally {
    clearTimeout(timer);
  }
}

export async function engineHealth(): Promise<{ ok: boolean; detail?: string }> {
  if (!isEngineConfigured()) return { ok: false, detail: "not configured" };
  try {
    const res = await fetch(`${engineUrl()}/health`, {
      method: "POST",
      headers: { authorization: `Bearer ${process.env.ENGINE_SERVICE_TOKEN?.trim()}` },
      cache: "no-store",
      signal: AbortSignal.timeout(8_000),
    });
    return { ok: res.ok, detail: res.ok ? undefined : `HTTP ${res.status}` };
  } catch {
    return { ok: false, detail: "unreachable" };
  }
}

/**
 * Derive the spoken-word audio script from an approved report's markdown.
 *
 * The markdown is sent in the body rather than recomputed here on purpose: the audio must
 * be a derivation of the text a human approved, not of whatever the engine would produce
 * today. An engine deploy between approval and narration could otherwise change the words a
 * client hears.
 */
export async function engineScript(markdown: string): Promise<{
  script: string;
  chunks: string[];
  stats: { chars: number; words: number; estimatedSeconds: number };
}> {
  const token = process.env.ENGINE_SERVICE_TOKEN?.trim();
  if (!token) throw ApiError.unavailable("Report engine token is not configured", "ENGINE_UNAVAILABLE");
  if (!markdown.trim()) throw ApiError.badRequest("No report text supplied", "EMPTY_MARKDOWN");

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60_000);
  try {
    const res = await fetch(`${engineUrl()}/script`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${token}` },
      body: JSON.stringify({ contractVersion: ENGINE_CONTRACT_VERSION, markdown }),
      signal: controller.signal,
      cache: "no-store",
    });

    const body = (await res.json().catch(() => ({}))) as {
      script?: string;
      chunks?: string[];
      stats?: { chars: number; words: number; estimatedSeconds: number };
      error?: string;
      code?: string;
    };

    if (!res.ok) {
      if (res.status >= 400 && res.status < 500) {
        throw new ApiError(res.status === 422 ? 422 : 400, body.code ?? "SCRIPT_REJECTED",
                           body.error ?? "The engine rejected the report text");
      }
      throw ApiError.unavailable("The audio script could not be derived", "SCRIPT_FAILED");
    }

    return {
      script: body.script ?? "",
      chunks: body.chunks ?? [],
      stats: body.stats ?? { chars: 0, words: 0, estimatedSeconds: 0 },
    };
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof Error && err.name === "AbortError") {
      throw ApiError.unavailable("The engine timed out deriving the script", "SCRIPT_TIMEOUT");
    }
    throw ApiError.unavailable("The engine is unreachable", "ENGINE_UNREACHABLE");
  } finally {
    clearTimeout(timer);
  }
}
