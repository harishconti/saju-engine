import type { Order } from "@prisma/client";
import { ApiError } from "./api";

/**
 * ElevenLabs text-to-speech — the voice for the audio summary.
 *
 * The **script is not written here.** It is derived deterministically from the approved
 * report text (`engineScript()` in `engine.ts`, implemented in
 * `src/saju_html/audio_script.py`), so this module only turns already-approved words into
 * sound. That is what keeps "reviewed by a human" true of the MP3 and not just the PDF.
 *
 * Model: `eleven_flash_v2_5` — the cheapest tier, multilingual, which matters because the
 * reports carry Korean and Chinese terms in romanised form.
 */

function apiKey(): string {
  const key = process.env.ELEVENLABS_API_KEY?.trim();
  if (!key) throw ApiError.unavailable("Voice generation is not configured", "TTS_UNAVAILABLE");
  return key;
}

function voiceId(): string {
  const id = process.env.ELEVENLABS_VOICE_ID?.trim();
  if (!id) throw ApiError.unavailable("No voice is configured", "TTS_VOICE_MISSING");
  return id;
}

export function isTtsConfigured(): boolean {
  return Boolean(process.env.ELEVENLABS_API_KEY?.trim() && process.env.ELEVENLABS_VOICE_ID?.trim());
}

export function ttsModel(): string {
  return process.env.ELEVENLABS_MODEL?.trim() || "eleven_flash_v2_5";
}

/**
 * Characters per request. ElevenLabs allows 40,000 on a paid plan, 5,000 on `eleven_v3`
 * and only 2,500 on a free one — so the default is deliberately conservative and works on
 * any plan. Raising it merely reduces the number of joins.
 */
export function ttsChunkChars(): number {
  const raw = Number(process.env.ELEVENLABS_MAX_CHUNK_CHARS ?? "2000");
  return Number.isFinite(raw) && raw > 0 ? Math.floor(raw) : 2000;
}

/**
 * True when this order's tier promises an audio summary.
 *
 * Deep only (plus its legacy alias `fullmap`). The compatibility report merely *cross-sells*
 * the MP3; it does not include one, so a compat order must never queue a voice job.
 */
export function tierPromisesAudio(order: Pick<Order, "kind" | "tier">): boolean {
  return order.kind === "SINGLE" && (order.tier === "deep" || order.tier === "fullmap");
}

/**
 * Synthesise one chunk. Returns MP3 bytes.
 *
 * `previous_text` / `next_text` are the vendor's documented way to keep prosody natural
 * across a split — without them the narration audibly restarts at each join.
 */
async function synthesiseChunk(
  text: string,
  opts: { previousText?: string; nextText?: string },
): Promise<Buffer> {
  const body: Record<string, unknown> = {
    text,
    model_id: ttsModel(),
    voice_settings: { stability: 0.5, similarity_boost: 0.75, use_speaker_boost: true },
  };
  if (opts.previousText) body.previous_text = opts.previousText.slice(-500);
  if (opts.nextText) body.next_text = opts.nextText.slice(0, 500);

  const res = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voiceId())}?output_format=mp3_44100_128`,
    {
      method: "POST",
      headers: { "xi-api-key": apiKey(), "content-type": "application/json", accept: "audio/mpeg" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(120_000),
    },
  );

  if (!res.ok) {
    // Log the status only; the provider's message can echo the submitted text.
    console.error("elevenlabs tts failed", res.status);
    const detail = await res.text().catch(() => "");
    const hint = detail.toLowerCase().includes("model") ? ", check ELEVENLABS_MODEL" : "";
    throw ApiError.unavailable(`Voice generation failed (HTTP ${res.status}${hint})`, "TTS_FAILED");
  }
  return Buffer.from(await res.arrayBuffer());
}

/** An ID3v2 tag is metadata; leaving one mid-file makes some players stop early. */
function stripId3(buf: Buffer): Buffer {
  if (buf.length >= 10 && buf.subarray(0, 3).toString("latin1") === "ID3") {
    // Syncsafe 28-bit size, bytes 6..9.
    const size =
      ((buf[6] & 0x7f) << 21) | ((buf[7] & 0x7f) << 14) | ((buf[8] & 0x7f) << 7) | (buf[9] & 0x7f);
    return buf.subarray(10 + size);
  }
  return buf;
}

export interface SynthesiseResult {
  audio: Buffer;
  chunks: number;
  model: string;
}

/**
 * Synthesise a whole script and return one playable MP3.
 *
 * Chunks are split on sentence boundaries, so `chunkChars` only has to be *at least* as
 * large as the longest sentence; the joins are the only place an intonation seam can show.
 */
export async function synthesise(script: string, chunkChars = ttsChunkChars()): Promise<SynthesiseResult> {
  const text = script.trim();
  if (!text) throw ApiError.badRequest("Nothing to narrate", "EMPTY_SCRIPT");

  const chunks: string[] = [];
  let current: string[] = [];
  let size = 0;
  for (const sentence of text.split(/(?<=[.!?])\s+/)) {
    const piece = sentence.trim();
    if (!piece) continue;
    if (size + piece.length + 1 > chunkChars && current.length) {
      chunks.push(current.join(" "));
      current = [];
      size = 0;
    }
    current.push(piece);
    size += piece.length + 1;
  }
  if (current.length) chunks.push(current.join(" "));

  const parts: Buffer[] = [];
  for (let i = 0; i < chunks.length; i++) {
    const raw = await synthesiseChunk(chunks[i], {
      previousText: i > 0 ? chunks[i - 1] : undefined,
      nextText: i < chunks.length - 1 ? chunks[i + 1] : undefined,
    });
    parts.push(i === 0 ? raw : stripId3(raw));
  }

  return { audio: Buffer.concat(parts), chunks: chunks.length, model: ttsModel() };
}
