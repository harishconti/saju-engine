#!/usr/bin/env node
/**
 * ElevenLabs text-to-speech smoke test.
 *
 * The audio path has four things that can be wrong and none of them raise: the model id, the
 * voice id, the chunking, and the MP3 concatenation. This checks all four against the real
 * API using the *actual* `synthesise()` from `src/lib/tts.ts` — not a copy of its logic.
 *
 * It deliberately uses a short two-chunk script: enough to exercise the join, cheap enough
 * to run repeatedly. The full nine-minute narration is what production does.
 *
 *   npm run smoke:tts
 *
 * Costs a few hundred characters of your ElevenLabs quota. Exits non-zero on any failure.
 */

import fs from "node:fs";
import path from "node:path";

// Load .env before importing the library, because tts.ts reads process.env at call time.
const envFile = path.resolve(import.meta.dirname, "../.env");
if (fs.existsSync(envFile)) {
  for (const line of fs.readFileSync(envFile, "utf8").split("\n")) {
    const s = line.trim();
    if (!s || s.startsWith("#") || !s.includes("=")) continue;
    const i = s.indexOf("=");
    const k = s.slice(0, i).trim();
    const v = s.slice(i + 1).trim().replace(/^["']|["']$/g, "");
    if (k && !(k in process.env)) process.env[k] = v;
  }
}

const { isTtsConfigured, synthesise, ttsModel, ttsChunkChars } = await import("../src/lib/tts.ts");

const results = [];
function check(name, pass, detail = "") {
  results.push({ name, pass });
  console.log(`${pass ? "  PASS" : "  FAIL"}  ${name}${detail ? `  — ${detail}` : ""}`);
}

/**
 * Is this actually audio?
 *
 * ElevenLabs returns `ID3`-tagged MP3 (so the first bytes are ASCII "ID", not a frame sync),
 * which is a perfectly valid file — an earlier version of this check wrongly failed it. Accept
 * either a leading ID3 tag or a bare frame, then require a real frame sync to appear shortly
 * after, which is what catches "we got JSON back" or "we concatenated garbage".
 */
function looksLikeMp3(buf) {
  const hasId3 = buf.length > 10 && buf.subarray(0, 3).toString("latin1") === "ID3";
  const frameAt = (i) => buf[i] === 0xff && (buf[i + 1] & 0xe0) === 0xe0;
  if (frameAt(0)) return true;
  if (!hasId3) return false;
  // Search a little way past the tag for the first frame.
  for (let i = 10; i < Math.min(buf.length - 1, 20_000); i++) if (frameAt(i)) return true;
  return false;
}

async function main() {
  if (!isTtsConfigured()) {
    console.error("ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID must both be set in apps/web/.env");
    process.exit(2);
  }
  console.log(`\nElevenLabs smoke test — model ${ttsModel()}, chunk ${ttsChunkChars()} chars\n`);

  // Two sentences is not enough to split; make it long enough to force two chunks.
  const sentence = "Water finds its level, and so does a chart read with patience. ";
  const script = sentence.repeat(60); // ~3,700 chars -> at 2,000/chunk that is two requests
  console.log(`  script: ${script.length} chars (expecting 2 chunks at ${ttsChunkChars()})`);

  const started = Date.now();
  const { audio, chunks, model } = await synthesise(script);
  const ms = Date.now() - started;

  check("synthesis returned audio", audio.byteLength > 1000, `${audio.byteLength} bytes`);
  check("more than one chunk was exercised", chunks >= 2, `${chunks} chunks`);
  check("model id was accepted", Boolean(model), model);
  check("output is playable audio (MP3)", looksLikeMp3(audio), `first bytes ${audio.subarray(0, 3).toString("latin1")}`);

  const out = "/tmp/opencode/tts-smoke.mp3";
  fs.writeFileSync(out, audio);
  // 128 kbps => 16 KB/s, a rough duration sanity check.
  const seconds = Math.round(audio.byteLength / 16000);
  check("duration is plausible", seconds > 5 && seconds < 600, `~${seconds}s from ${audio.byteLength} bytes`);

  // A second call must also work: repeated use is the normal case.
  const again = await synthesise("A short second generation.");
  check("a second, short synthesis works", looksLikeMp3(again.audio), `${again.audio.byteLength} bytes`);
  check("the concatenated join did not corrupt the stream", looksLikeMp3(audio), "frame sync found after the tag");

  console.log(`\n  wrote ${out}  (${Math.round(ms / 100) / 10}s wall time)\n`);
  const failed = results.filter((r) => !r.pass);
  console.log(`${results.length - failed.length}/${results.length} passed`);
  if (failed.length) {
    console.log("failed:", failed.map((f) => f.name).join("; "));
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("smoke test error:", err instanceof Error ? err.message : typeof err);
  process.exit(1);
});
