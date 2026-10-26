import { createHash } from "node:crypto";
import type { Order, Profile } from "@prisma/client";
import { ApiError } from "./api";
import { parseChartSummary, type ChartSummary } from "./chart";

/**
 * Client for the report engine service (Vercel project #2).
 *
 * Contract: docs/webapp/05-report-pipeline.md §2. The engine is stateless, holds no database
 * credentials, and receives a presigned R2 PUT url so the PDF never crosses a response body.
 */

export const ENGINE_CONTRACT_VERSION = 1;

/**
 * The free-sample route's engine budget.
 *
 * AU-11 (2026-10-26 audit): `/api/sample` allows the function 60 s (`maxDuration`), but the engine
 * call waited the default 120 s. The platform killed the function first, so the abort never fired,
 * `ENGINE_TIMEOUT` was never logged, and the visitor got a bare 504. 50 s leaves ~10 s for the
 * storage verification and the response inside the same invocation.
 */
export const SAMPLE_ENGINE_TIMEOUT_MS = 50_000;

/**
 * The engine codes that retrying cannot fix: the visitor's birth data is wrong.
 *
 * AU-09 (2026-10-26 audit): permanence used to be inferred from the HTTP status — every 4xx was
 * "permanent". The October outage returned `UPLOAD_HOSTS_UNCONFIGURED` as 422, so it was recorded
 * as bad birth data and five days of refusals were never retried once the allowlist was restored.
 * Permanence is now an explicit set of birth-data codes; every other failure is retryable.
 */
export const PERMANENT_ENGINE_CODES: ReadonlySet<string> = new Set([
  "INVALID_GENDER",
  "INVALID_BIRTH_DATE",
  "INVALID_BIRTH_TIME",
  "MISSING_LONGITUDE",
  "MISSING_TIMEZONE",
  "UNKNOWN_TIMEZONE",
]);

export function isPermanentEngineFailure(code: string): boolean {
  return PERMANENT_ENGINE_CODES.has(code);
}

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
  /** Where the engine should also PUT the web document — the reading the client opens, as one
   *  self-contained HTML file. Every tier gets one, compatibility included. */
  htmlUploadUrl?: string;
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
  /** Integrity metadata for the web document; null when it was not requested. */
  htmlSha256?: string | null;
  htmlBytes?: number | null;
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

    const body = (await res.json().catch(() => ({}))) as { error?: string; code?: string };
    const engineCode = body.code?.trim() || "";

    // Only birth-data validation is permanent (AU-09). A 4xx is not enough: the engine answered
    // UPLOAD_* faults with 422 for five days and this branch filed them as bad input.
    if (isPermanentEngineFailure(engineCode)) {
      throw new ApiError(
        422,
        engineCode,
        body.error ?? "The engine rejected this birth data.",
        { engineStatus: res.status },
      );
    }

    // Everything else is a service or configuration condition, and therefore retryable. The
    // engine's own prose can name environment variables, so it goes to the log, not the visitor.
    // The code and status travel on the error so `fulfilment` can record the real cause and the
    // sample flow can map the code to copy (AU-10, AU-28).
    console.error("engine generate failed", res.status, engineCode || "unknown");
    throw new ApiError(
      503,
      engineCode || "ENGINE_FAILED",
      "We couldn't generate the report just now. Please try again.",
      { engineStatus: res.status },
    );
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof Error && err.name === "AbortError") {
      // AU-11: this is the path that never ran when the function was killed first.
      console.error("engine generate timed out", `ENGINE_TIMEOUT after ${timeoutMs}ms`);
      throw ApiError.unavailable("The report engine timed out", "ENGINE_TIMEOUT");
    }
    throw ApiError.unavailable("The report engine is unreachable", "ENGINE_UNREACHABLE");
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Is the engine able to render?
 *
 * AU-03 (2026-10-26 audit): this used to trust the status code alone. The engine answered 200
 * for five days while refusing every render, because its upload allowlist was empty. The probe
 * now returns 503 in that state; this client also reports *why* and the allowlist count, which
 * `/api/health` exposes as `engineDetail`.
 */
export async function engineHealth(): Promise<{ ok: boolean; detail?: string }> {
  if (!isEngineConfigured()) return { ok: false, detail: "not configured" };
  try {
    const res = await fetch(`${engineUrl()}/health`, {
      method: "POST",
      headers: { authorization: `Bearer ${process.env.ENGINE_SERVICE_TOKEN?.trim()}` },
      cache: "no-store",
      signal: AbortSignal.timeout(8_000),
    });
    // The body is small and never carries secrets — only the code and a count.
    const body = (await res.json().catch(() => ({}))) as { code?: string; uploadAllowlist?: number };
    const allowlist =
      typeof body.uploadAllowlist === "number" ? `uploadAllowlist=${body.uploadAllowlist}` : "";
    if (!res.ok) {
      const code = body.code ? ` ${body.code}` : "";
      return { ok: false, detail: [`HTTP ${res.status}${code}`, allowlist].filter(Boolean).join(" ") };
    }
    return { ok: true, detail: allowlist || "uploadAllowlist=unknown" };
  } catch {
    return { ok: false, detail: "unreachable" };
  }
}

/**
 * Derive a chart summary only — no render, no storage.
 *
 * The cheap half of the engine contract (`POST /chart`). Used by the shareable card, which needs the
 * pillars, Day Master and element balance but no PDF. Unlike `callEngine` this returns the parsed
 * summary directly and throws a typed error, because every caller here is rendering something for a
 * visitor and needs to tell "engine down" apart from "bad birth data".
 */
export async function engineChart(profile: EngineProfile, timeoutMs = 20_000): Promise<ChartSummary> {
  const token = process.env.ENGINE_SERVICE_TOKEN?.trim();
  if (!token) throw ApiError.unavailable("Report engine token is not configured", "ENGINE_UNAVAILABLE");

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${engineUrl()}/chart`, {
      method: "POST",
      headers: { "content-type": "application/json", authorization: `Bearer ${token}` },
      body: JSON.stringify({ contractVersion: ENGINE_CONTRACT_VERSION, ...profile }),
      signal: controller.signal,
      cache: "no-store",
    });

    if (!res.ok) {
      const body = (await res.json().catch(() => ({}))) as { error?: string; code?: string };
      throw new ApiError(
        res.status === 422 ? 422 : 503,
        body.code ?? "CHART_FAILED",
        body.error ?? "The chart could not be derived.",
        { engineStatus: res.status },
      );
    }

    const summary = parseChartSummary(await res.json());
    if (!summary) throw ApiError.unavailable("The engine returned an unusable chart", "CHART_UNUSABLE");
    return summary;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw ApiError.unavailable("The chart engine is unreachable", "ENGINE_UNAVAILABLE");
  } finally {
    clearTimeout(timer);
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
