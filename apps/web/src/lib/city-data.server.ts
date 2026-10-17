import { readFileSync } from "node:fs";
import path from "node:path";
import { decodeCityIndex, hydrateCityIndex } from "./cities";

/**
 * The world place index, on the server.
 *
 * `/api/profiles` resolves a typed birthplace to coordinates **on the server** and stores them, which is
 * the whole point of engine change E2: the engine must receive explicit values, never geocode. So the
 * server needs the same places the browser's picker offers — otherwise the client would happily resolve
 * `Vellore` from the index it just fetched and the server would answer `CITY_NOT_RESOLVED`, and the two
 * halves would disagree about which places exist.
 *
 * **One file, two readers.** It lives in `public/city-index.json` so the browser fetches it as a plain
 * static asset (a CDN hit, not a function invocation) — and this module reads the very same bytes from
 * disk. `next.config.ts` lists it in `outputFileTracingIncludes`, because a file read through `cwd` is
 * invisible to Next's tracing and would otherwise be missing from the serverless bundle.
 *
 * Why not `new URL("./city-index.json", import.meta.url)`: the bundler rewrites a **static** URL like
 * that into an asset reference, and it arrives at `fileURLToPath` as something else entirely — the build
 * failed with "The 'path' argument must be of type string ... Received an instance of URL". A path
 * through `cwd` plus an explicit tracing entry is duller and works.
 *
 * Parsed once per instance at import: ~2.6 MB of JSON is tens of milliseconds once, not per request, and
 * it buys a synchronous `resolveBirthLocation` at every call site.
 */
const FILE = path.join(process.cwd(), "public", "city-index.json");

const RAW = readFileSync(FILE, "utf8");
const { cities, aliases } = decodeCityIndex(JSON.parse(RAW));
hydrateCityIndex(cities, aliases);
