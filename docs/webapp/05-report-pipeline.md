# 05 — Report pipeline

The path from "a paid order exists" to "a reviewed PDF is in the client's inbox and profile".

This is the most failure-prone part of the system, so it gets the most explicit design.

---

## 1. The engine service

A stateless FastAPI app on Vercel. It is a **thin, honest wrapper** around code that already exists.

> **Layout note — this differs from the original plan, deliberately.** The Vercel project's
> **Root Directory is the repository root**, so the function lives at `api/index.py` and can import
> `src/`. A Root Directory of `services/report-engine/` would have hidden `src/` from the function
> bundle: Vercel only bundles files under the Root Directory, so the engine packages would simply not
> be there at runtime. Putting the service at the repo root removes the problem instead of working
> around it — and the repo root has no `package.json`, so Vercel does not misdetect Next.js.

```
saju-engine/                     ← Vercel project #2, Root Directory = repository root
├── api/
│   └── index.py                 # FastAPI: POST /health, /chart, /generate
├── requirements.txt             # sajupy, reportlab, jinja2, markdown-it-py, fastapi
├── vercel.json                  # framework: null, maxDuration, excludeFiles
├── src/saju_html/fonts/         # bundled DejaVu TTFs (E1) + their licence
├── src/saju_engine/             # imported unchanged
└── src/saju_html/               # imported unchanged
```

It imports the repository's existing engine packages — it does **not** fork them:

```python
# api/index.py (sketch)
from saju_engine.compat_report import generate_compat_report
from saju_engine.engine import compute_chart
from saju_engine.timezone import derive_utc_offset
from saju_html.chart_input import prepare_chart_render
from saju_html.md_to_saju_pdf import build_pdf          # ReportLab backend
```

**Hard constraints on this service:**

| Constraint | Reason |
|---|---|
| **No database access** | Nothing to compromise. State lives in the webapp |
| **No user, price, or order concepts** | It receives birth data and overrides; it does not know who is paying or how much |
| **No persistent state** | Vercel functions are ephemeral; a temp dir is fine, durable state is not |
| **No LLM or third-party AI dependency** | Report prose is generated **deterministically** by the engine. Nothing in `/health`, `/chart` or `/generate` calls a model, and there is no API key to rotate or bill. See §1.1 — this is a deliberate property, not an accident |
| **One bearer token in, one presigned URL out** | Minimal surface |
| **Never log PII** | Exception *messages* can embed birth data (`jobs.py` already documents this). Log the class name and a stack; never `str(exc)` |
| **Always write the PDF to R2, never return it in the body** | Keeps every hop far below Vercel's 4.5 MB payload limit and makes the upload retry-safe |

### 1.1 The engine has no LLM dependency — and that is deliberate

An LLM was considered in two places during the project's design, and **neither is in the automated
path**:

| Where an LLM could sit | Current reality |
|---|---|
| **Writing the report prose** | The engine's own generators (`premium_report.py`, `prose_scaffold.py`, `prose_fillers.py`, `report_data.py`) produce every word deterministically from the chart. The market research's "AI draft + human polish ≤45 min" workflow is about *the owner* polishing by hand — there is no model call anywhere in the pipeline |
| **Compliance screening of prose** | `src/saju_qa/` can call TypeSafe/Jev (`POST https://api.typesafe.ai/v1/systemone`) behind `TYPESAFE_API_KEY`. It is **optional, standalone, and never imported by `src/saju_engine/`, `src/saju_html/` or `api/`**. Without a key it *skips* and exits 2. It is a manual pre-delivery gate, run alongside the human review, not part of the service |

There is **no Ollama reference anywhere in the repository**. If local-model assistance is ever wanted,
the right shape is a separate, optional tool the owner runs — *not* something inside the Vercel
function: serverless has no GPU, a cold model load would blow the duration budget, and it would make
the core product depend on a third party for no benefit.

Consequences worth stating plainly: the engine works offline, produces byte-identical output for
identical input, has no per-report marginal cost, and cannot leak birth data to a model provider.

### 1.2 Where it is hosted

| | |
|---|---|
| **Platform** | Vercel — a **second project** in the same team, from the same repository |
| Project | `saju-report-engine` (`prj_xbsxhey2adyc67mWd8INKJtibaqD`) |
| **Root Directory** | the **repository root** (see the layout note in §1) |
| Framework preset | none — Vercel's Python serverless runtime |
| **Region** | **`sin1`** (Singapore), beside Neon `ap-southeast-1` |
| Runtime | Python 3.12 |
| URL | `https://saju-report-engine.vercel.app` |
| Auth | one shared bearer token, `ENGINE_SERVICE_TOKEN`, the same value in both projects |
| Duration | `maxDuration: 300`; a deep report measures ~1.6 s |

⚠️ **The install-command gotcha, for anyone re-creating this project.** With both `pyproject.toml` and
`requirements.txt` at the repo root, Vercel installs from **`pyproject.toml`** — so `fastapi`, which
lives in the optional `web` extra, was never installed and the function crashed on import with a bare
`500`. `vercel.json` therefore sets:

```json
"installCommand": "pip install -r requirements.txt"
```

`requirements.txt` is a superset of pyproject's main dependencies, so that one line is sufficient.

⚠️ **The second gotcha: `api/index.py` is the wrong place for an ASGI app.** Vercel has two Python
modes, and the difference cost two deploys to find:

| Mode | How it is selected | Routing |
|---|---|---|
| **Framework preset** (what we want) | Vercel detects FastAPI from a dependency, then looks for `app.py` / `index.py` / `server.py` / `main.py` / `wsgi.py` / `asgi.py` — or the same names inside `src/` or `app/` — **or** an explicit `[tool.vercel] entrypoint` | **every** request is routed to the app, so `/health`, `/chart`, `/generate` work at the root |
| **Legacy `/api` file functions** | a file under `api/` with no entrypoint configured | the file is mounted at its **exact path only** — `/api/index` works, `/api/index/health` 404s |

A file at `api/index.py` therefore gets the *second* mode: the app received a path it had no route for
and answered FastAPI's `{"detail":"Not Found"}`. Declaring the entrypoint is what switches it over:

```toml
[tool.vercel]
entrypoint = "api.index:app"
```

With that, the endpoints are the clean `https://saju-report-engine.vercel.app/{health,chart,generate}`
and `ENGINE_URL` needs no suffix. **Verified in production:**

```
POST /health  → 200 {"status":"ok","ok":true,"engineVersion":"0.2.0","contractVersion":1,
                     "fontsDir":"/var/task/src/saju_html/fonts","uploadAllowlist":1}
POST /chart   → 200  甲戌 癸酉 辛丑 乙未 · 辛 Metal · Water via strong-dm-drain
POST /generate (deep) → 200  139898 bytes · 1877 ms · sha256 matched after download · valid PDF
```

`fontsDir` pointing at `/var/task/src/saju_html/fonts` is the proof that **E1 works inside the deployed
function** — it found the *bundled* faces rather than the system directory, which does not exist there.

`uploadAllowlist` is the number of upload hosts the engine will accept (`_allowed_upload_hosts()`).
**Zero is a 503** with `{ ok: false, code: "UPLOAD_HOSTS_UNCONFIGURED", error }`: with no allowlist
the engine refuses every render, which is exactly what happened for five days in October 2026
(AU-03 audit). `/api/health/detail` surfaces the count and the code as `engineDetail`.

### Why ReportLab, not the HTML/Chromium backend

The default renderer in `tools/build-pdf.sh` today is the HTML/Playwright one. It cannot run here:
Chromium alone exceeds the function size budget, and installing a browser at cold-start is not a
thing.

Measured locally on this repository:

| Path | Time |
|---|---|
| Deep tier → markdown | **0.70 s** |
| Deep markdown → ReportLab PDF | **0.62 s** |
| Sample tier end to end (`compute_chart` → `prepare_chart_render` → `build_pdf`) | **1.57 s** |
| Runtime dependency closure (pandas 68 MB + numpy 40 MB + reportlab 8 MB + PIL 7 MB + sajupy 3.5 MB) | **~130 MB** |

Against Vercel's **500 MB** Python bundle limit that is comfortable, and against the 300 s function
duration it is two orders of magnitude of headroom. Cold start adds ~1–2 s for the pandas import;
`/health` can be hit on a warm-up schedule if that ever matters.

**Consequence accepted:** delivered PDFs will differ slightly from the demo PDFs already served from
`apps/web/public/demo/`. **Regenerate those demos with `SAJU_PDF_BACKEND=reportlab`** so the
marketing preview matches the delivered artefact. Shipping a sample that looks different from the
product is a refund request waiting to happen.

**Escape hatch if fidelity ever matters more than simplicity:** Vercel supports OCI container-image
functions. A container with Python + Chromium restores the HTML templates byte-for-byte. That is a
later, isolated change to this one project — it does not touch the webapp.

**What the ReportLab artefact contains.** Because this is the backend the client actually gets, its
output is a contract, not an implementation detail: a **linked contents page** with page numbers (from
the same measuring pass that fills `pageCount`), a **PDF outline**, **Title/Author/Subject/Creator**
metadata, markdown blockquote notes rendered as notes, and Hangul/Hanja drawn with a bundled glyph
subset of Noto Sans KR (embedded, so it renders in browsers and phone viewers). Report prose stays
English-primary — Korean/Hanja is translated, and only what survives translation is drawn. Details and
the regeneration command: [products/reports.md](../openwiki/products/reports.md) § The PDF artefact.

### AI-assisted drafting (review time only)

The one page the engine cannot template is the reader's letter: the audit's §1 asks for
150–250 words naming the two or three chart features that drive everything, plus the caveat
about birth-time accuracy. `tools/suggest_letter.py` (package `src/saju_ai/`) drafts it for
the reviewer. The design constraints are the whole story:

- **Never in the delivery path.** No client request ever reaches a model. The tool runs when
  the owner asks; a provider outage or a bad generation cannot affect a delivered report.
- **Grounded, never free-written.** The engine builds a *grounding pack*: computed chart
  facts from a fixed whitelist, plus six to eight short excerpts from `knowledge/` chosen by
  heading keyword. The model must answer with JSON that cites those excerpts by id.
- **No PII leaves the building.** The pack carries no name, birth date, time or place; the
  letter is written as "you" and the engine adds the name downstream. `--dry-run` prints the
  exact request so it can be read before it is sent, and the tool refuses to send a pack that
  contains any supplied identifier.
- **A deterministic validator disposes.** Unknown citations, numbers absent from the facts,
  a stated time measurement the chart does not give, wrong length, a missing birth-time
  caveat, ground-rule absolutes, machinery words, or anything `qa_client_ready.py` flags all
  fail the draft. The live example that motivated the duration check: the model wrote the
  knife-edge margin as "a minute and a half" where the chart says 41 seconds — and the pack
  was ambiguous about it, so the pack was fixed as well as the check.
- **Suggest-only.** It writes to `--out` or stdout. Nothing edits a report automatically, and
  the accepted text is frozen into the markdown before approval, so an approved artefact can
  never change under a client.

Provider: Ollama Cloud (`OLLAMA_API_KEY`, default `deepseek-v4.1-flash`) via an OpenAI-shaped
call; Anthropic and OpenAI are one flag away. Env and cost: [07](07-services-and-integrations.md).

### The delivered reading: web document + PDF

The engine can now produce **both** artefacts from one markdown source:

| Artefact | Command | Role |
|---|---|---|
| Web document | `md_to_saju_html_pdf.py --web --output report.html` | The reading. Self-contained HTML (inline CSS/SVG, no scripts or webfonts), heading anchors, a linked contents list, scrollable tables, an audio slot. Served at `/report/{token}` and **downloadable as one file**. |
| PDF | `… --output report.pdf` (ReportLab) | The keepsake, and the record of what the reviewer approved. |

**How it is wired.** `POST /generate` takes an optional `htmlUploadUrl`; when present the engine
renders the web document from the same markdown and PUTs it beside the PDF — best-effort, like the
markdown, because losing the reading must not lose the order — and returns
`htmlSha256`/`htmlBytes` so a caller can tell "not uploaded" from "not asked for". **Every kind now
sends it**, compatibility included: a two-chart reading is markdown through the same renderer, so the
engine renders one for `kind: "compat"` too. (Until 2026-10-17 both sides withheld it — see MEMORY.)
`fulfilment.ts` presigns that URL, verifies the object with `HeadObject`, and stores
`Report.htmlKey`/`htmlBytes`. The client reads it at `GET /api/reports/{id}/html` and downloads it —
or the PDF — from `GET /api/reports/{id}/download`. `12-testing.md` §Gate 4 covers the document's own
properties.

**Still open.** The audio player sits in the app *around* the reading (it already does, beside the
MP3 route) rather than inside the stored document: the MP3 is produced after approval and the
document is immutable by design. The review console still previews only the PDF. Every tier now has a
web reading, compatibility included — it renders through the same renderer, so `htmlKey` is null only
for a report rendered before this existed, and the UI falls back to the PDF for those.

### `/chart` — derive without rendering

Called when a profile is created or when anything chart-affecting changes. The webapp stores the
result on `Profile.chartJson` so the dashboard and the order flow can show the four pillars without a
render and without an engine round-trip per page load.

```jsonc
POST /chart
{ "contractVersion": 1, "fullName": "…", "gender": "F", "birthDate": "1994-09-12",
  "birthTime": "13:28", "timeKnown": true, "timezone": "Asia/Seoul", "utcOffset": 9,
  "city": "Seoul", "latitude": 37.5665, "longitude": 126.978 }

// 200
{ "pillars": [{ "stem": "甲", "branch": "戌", "label": "Year" }, …],
  "dayMaster": { "char": "辛", "element": "Metal", "polarity": "Yin" },
  "elementBalance": { "Wood": 34.1, "Fire": 3.7, "Earth": 16.9, "Metal": 28.7, "Water": 16.6 },
  "strength": "Strong",
  "favorableElement": "Water",
  "favorableProvenance": "climate-merged",
  "luckyCues": { "colors": ["black", "navy"], "direction": "north", "numbers": [1, 6] },
  "caveats": ["The corrected time sits seconds from a two-hour branch boundary…"] }
```

`caveats` is not decoration: it is how the hour-boundary and solar-term-boundary knife-edges reach the
UI, where they are shown to the client as a confidence note. A failed `/chart` is non-fatal — the
profile saves with `chartJson = null` and the UI says the chart has not been derived yet.

---

## 2. The engine contract

```jsonc
POST /generate
Authorization: Bearer $ENGINE_SERVICE_TOKEN

{
  "contractVersion": 1,
  "kind": "single" | "compat",
  "tier": "sample" | "essential" | "deep" | "basic",
  "uploadUrl": "https://<acct>.r2.cloudflarestorage.com/reports/…&X-Amz-Expires=900",
  "profileA": {
    "fullName": "Jisoo K.",

    "gender": "F",                  // REQUIRED — 대운 direction is undefined without it
    "birthDate": "1994-09-12",
    "birthTime": "13:28",           // local wall clock at the birthplace
    "timeKnown": true,
    "timezone": "Asia/Seoul",       // preferred
    "utcOffset": 9.0,               // fallback when the zone is unknown
    "city": "Seoul",
    "longitude": 126.978,
    "latitude": 37.5665
  },
  "profileB": { "...": "compat only" },
  "favorableOverrideA": "Water",    // optional; set by a reviewer, never by the client
  "favorableOverrideB": "Fire"
}
```

```jsonc
// 200
{ "sha256": "…", "bytes": 142276, "engineVersion": "saju-engine/0.2.0", "durationMs": 1642 }

// 422  { "error": "…", "code": "INVALID_BIRTH_DATA" }        // birth data ONLY
// 422  { "error": "…", "code": "UNKNOWN_TIMEZONE" }
// 503  { "error": "…", "code": "UPLOAD_HOSTS_UNCONFIGURED" }  // deployment fault, retryable
// 500  { "error": "…", "code": "RENDER_FAILED" }             // exception CLASS only
```

**Every** error body is `{ error, code }` — a top-level handler covers auth failures, pydantic
rejections and unexpected exceptions, so no path returns a bare string or a missing `code`.
Status carries meaning the webapp acts on: **only birth-data validation is 422**, which the webapp
treats as permanent and never retries; configuration faults (`UPLOAD_*`, a missing token), an auth
mismatch, and availability failures are **503** and stay retryable. (AU-09, 2026-10-26 audit: the
October outage answered `UPLOAD_HOSTS_UNCONFIGURED` with 422 for five days, so restoring the
allowlist could not have recovered a single order.)

`contractVersion` is checked and rejected on mismatch. It exists so the two Vercel projects can be
deployed independently: a webapp that ships a new field before the engine understands it must fail
loudly, not silently produce a wrong report. The CI contract test runs on both sides.

### Upload targets (the engine's only write capability)

The engine holds no storage credentials — `uploadUrl` (and the optional `mdUploadUrl` /
`htmlUploadUrl`) are the only places it can write. They are **allowlisted**, because a leaked service
token would otherwise turn the service into an arbitrary-URL PUT primitive:

- allowlist from `SAJU_UPLOAD_HOSTS` (comma-separated) and/or the host of `R2_ENDPOINT`;
  **empty means fail closed** (`503 UPLOAD_HOSTS_UNCONFIGURED`);
- https required (http is allowed only to loopback, for local development), no embedded
  credentials, no fragment;
- optional `SAJU_UPLOAD_BUCKET` pins the path to `/<bucket>/…`;
- a body cap (`SAJU_MAX_REQUEST_BYTES`, default 2 MB) and pydantic bounds on every field.

Errors: `503 UPLOAD_URL_NOT_ALLOWED` / `UPLOAD_URL_INSECURE` / `UPLOAD_URL_INVALID` /
`UPLOAD_PATH_NOT_ALLOWED` / `UPLOAD_HOSTS_UNCONFIGURED` — all deployment/caller faults, so all 503
and all retryable. The error never echoes the URL, which carries a signature.
See [14 — Security](14-security.md) §3.

### Required engine changes — status

| # | Change | Status |
|---|---|---|
| **E1** | `SAJU_FONT_DIR` env override + bundled DejaVu | ✅ **done.** `md_to_saju_pdf.py` now resolves in order: `$SAJU_FONT_DIR` → `<package>/saju_html/fonts/` → `/usr/share/fonts/truetype/dejavu`. Five faces + their licence are bundled (3.0 MB), and the resolver *prefers* the bundle, so output is identical on every host — which is what the renderer docs wanted. A missing directory now warns with every path it searched, instead of a bare `font file not found`. `/health` reports the resolved `fontsDir`, so a silent fallback is visible. |
| **E2** | No silent geocoding | ✅ **done, and narrower than first thought.** `sajupy` geocodes **only when `longitude is None`** (`sajupy/core.py:406`); the webapp always supplies one, so our path never geocoded. The residual risk was a profile with `longitude = NULL`, which would trigger a live Nominatim call and *change the chart*. The service now **refuses** with `422 MISSING_LONGITUDE` rather than falling back — a refusal is honest, a silent fallback is a wrong chart. |
| **E3** | Thread `favorable_override` through the single-chart path | ✅ **done.** Added to `chart_markdown()`, `prepare_chart_render()` and `build_pdf_from_chart()`, forwarded to `generate_premium_report(..., favorable_override=…)`. This is what makes the review console's 용신 override work for single charts, not just compatibility readings. |
| **E4** | FastAPI entry with presigned upload, PII-safe errors | ✅ **done** — `api/index.py`, three endpoints, bearer auth, `HEAD`-style contract version check, class-name-only logging |
| **E5** | Regenerate `apps/web/public/demo-*.pdf` with ReportLab | ⬜ **still open** — and now it also carries the MP3 decision (see [13 — Launch audit](13-launch-audit.md) D1) |
| **E6** | Contract tests | ✅ **done** — `tests/test_report_engine_service.py` (no network, no storage), now including the upload-allowlist, request-size and field-bound cases. They call the endpoint functions directly rather than through `TestClient`, because the local httpx 0.28 dropped the `app=` argument that starlette 0.36's `TestClient` still passes; testing the functions is faster and version-proof. |

**Verified end to end** (real presigned PUT into R2, then download and compare):

```
POST /generate  {kind: single, tier: deep}
→ 200  {"sha256":"982a912e…","bytes":139898,"durationMs":1592}

object in R2            : 139898 bytes, content-type application/pdf
downloaded & sha256     : MATCHES the engine's report  ✓
starts with %PDF        : YES ✓
leak check (pdftotext)  : knowledge/ = 0, [ENGINE DRAFT = 0, review er notes = 0,
                          candidates_horoscope = 0, [UNCERTAIN] = 0  ✓
```

And `/chart` returns the **known-correct** chart for the repo's reference subject: pillars
`甲戌/癸酉/辛丑/乙未`, Day Master `辛 Yin Metal`, element balance `34.1/3.7/16.9/28.7/16.6`,
favourable element `Water` (provenance `strong-dm-drain`), lucky cues `north · black, navy, deep blue ·
1, 6` — matching `candidates_horoscope/reports/rm/` exactly, and it lifts the real hour-boundary caveat
("only ~17 seconds from a 2-hour branch boundary").

> **`pytest` must stay green across all of this.** With 1,909 passing cases plus the cited-fixture
> validation gate, the suite is the safety net that makes touching the engine acceptable. Any engine
> change that also changes a fixture is a decision, not a fix — stop and look.

---

## 3. Storage model (Cloudflare R2)

Private buckets, no public URL, no custom domain. Every byte moves through a presigned URL issued
after a check.

| Key pattern | Contents | Lifetime |
|---|---|---|
| `reports/anonymous/{uuid}/sample.pdf` | Free samples not yet claimed | Swept after 3 days, **by object age** (see [09](09-operations.md)) — an anonymous sample creates no row to track, so a row-driven sweep found nothing |
| `reports/{userId}/samples/{uuid}.pdf` | A sample a signed-in user kept | Until the user deletes it. Deliberately **outside** the swept prefix |
| `reports/{userId}/{orderId}/{reportId}.pdf` | Delivered report | Until deletion is requested |
| `reports/{userId}/{orderId}/{reportId}.md` | Source markdown — the audit trail **and** the input the audio script is derived from | Same |
| `reports/{userId}/{orderId}/{reportId}.mp3` | The audio summary (Deep tier) | Same |

> The markdown was declared from the start but **was not actually written** until the audio work
> needed it: the engine uploaded only the PDF. It now uploads both, which closed the "what did we
> actually send?" gap at the same time.

Leading with `userId` is deliberate: a GDPR/DPDP erasure request becomes one `list` + one
`deleteObjects`, not a scan.

| Operation | Presign | Notes |
|---|---|---|
| Engine upload | `PutObject`, 10 min | Handed to the engine in the request body |
| Admin preview | `GetObject`, 15 min | Inline viewer |
| Client download | `GetObject`, 1 hour | After an ownership check |
| Forced download | streamed | `octet-stream` + `Content-Disposition: attachment` + `nosniff` + `no-store` |
| Delete | direct delete | On failure, enqueue to `ObjectDeletion` (never lose the intent) |

After the engine reports success, the webapp verifies with `HeadObject` before creating the `Report`
row. Trusting the engine's `200` alone would mean a report row pointing at nothing.

**`ObjectDeletion` is a retry queue, not a log.** Failed deletes, oversized uploads, and content-type
mismatches all enqueue here and the daily cleanup cron drains it in batches with an attempt cap. This
is the same pattern the reference implementation uses for attachments, and it exists because "the
delete failed" must never mean "the file stays forever".

---

## 4. The queue and dispatcher

### Claim semantics

Postgres-native, no broker. The claim is one statement:

```sql
UPDATE "Job"
   SET state = 'RUNNING',
       attempts = attempts + 1,
       leaseUntil = now() + interval '5 minutes',
       startedAt = coalesce("startedAt", now()),
       worker = $1
 WHERE id = (
   SELECT id FROM "Job"
    WHERE state = 'QUEUED'
       OR (state = 'RUNNING' AND "leaseUntil" < now())     -- crashed worker: reclaim
    ORDER BY "createdAt"
    FOR UPDATE SKIP LOCKED
    LIMIT 1
 )
RETURNING *;
```

`FOR UPDATE SKIP LOCKED` is what makes concurrent dispatcher invocations safe: two overlapping cron
ticks each get a different job, neither blocks.

`leaseUntil` is what makes a crashed dispatcher recoverable. The existing Python job code already
reasons this way (`STALE_AFTER = 15 minutes`, `requeue_pending()` on startup) — same semantics,
durable storage.

### `/api/cron/dispatch` — the schedule depends on the Vercel plan

⚠️ **Vercel Hobby rejects any cron that runs more than once per day, at deploy time:**

```
Hobby accounts are limited to daily cron jobs. This cron expression (* * * * *)
would run more than once per day. Upgrade to the Pro plan to unlock all Cron Jobs features.
```

This project is on Hobby, so the per-minute dispatcher this design originally assumed **cannot exist**.
Generation is triggered three ways instead, and the same machinery serves all of them:

| Trigger | Runs | Note |
|---|---|---|
| **Dodo Payments webhook → `after()`** | `processJobById(createdJobId)` | Immediate path. `after()` from `next/server` lets the webhook return its 2xx promptly and generate that exact job afterwards (AU-13: it used to dispatch the *oldest* queued job) |
| **GitHub Actions workflow, every 15 min** | `POST /api/cron/dispatch` → `runDispatchTick(3)` | Primary scheduled trigger (decision D4, AU-13). `.github/workflows/sla-sweep.yml` |
| **`POST /api/jobs/kick`** | `kickOwnerJobs(userId)` | A client taps "Check for updates". Scoped to that caller's orders only, rate limited, and it does not spend the job's retries (AU-12) |
| **Daily cron** (04:00 UTC) | `runDispatchTick(3)` | Fallback for anything the above missed — `vercel.json` keeps it because the Vercel plan is Hobby |

A true per-minute cron would still be a **one-line change** on Pro — `"schedule": "* * * * *"` — with
no code change, because the claim/lease/retry machinery below is already correct and simply runs more
often. See [08a — Deployment notes](08a-vercel-json-notes.md).

```
1. verify Authorization: Bearer $CRON_SECRET   (constant-time compare)
2. loop up to N times (N = 3, to stay inside the function duration):
     claim a job
     if none → break
     presign R2 PUT for reports/{userId}/{orderId}/{reportId}.pdf
     build the engine payload from Order + Profile (+ overrides)
     POST {ENGINE_URL}/generate   (timeout 120 s)
     on 200: HeadObject verify → create Report(DRAFT_READY) → Job SUCCEEDED → audit
     on 4xx: Job FAILED (permanent — bad data will not get better), alert
     on 5xx/timeout/network: attempts < maxAttempts ?
                              → Job back to QUEUED (lease cleared)
                              : Job FAILED + alert
3. return { processed, failed, remaining }
```

Deliberately bounded: a dispatcher tick that tries to drain the whole backlog will be killed
mid-flight by the function timeout, which is exactly the situation leases exist to survive. Better to
do three and return.

### Why the webhook dispatches but does not block

On a per-minute cron (Pro) the webhook only records the payment and enqueues a job — it never talks to
the engine, so a cold Python service can never delay or fail a payment acknowledgment.

On Hobby there is no per-minute Vercel cron, so the webhook *is* the immediate trigger and the
15-minute GitHub Actions workflow is the scheduled one — but the webhook still does not block:
`after()` from `next/server` runs the dispatch once the response has already been sent, so the provider
gets its 2xx first. If the dispatch fails, the job stays `QUEUED` and the recovery paths (the
15-minute dispatch, the daily cron, the dashboard kick, an admin regenerate) pick it up. The webhook is
never the single point of failure for a paid order, either way. Delivery is gated on human review
regardless, so the work must survive an arbitrary wait — which is why it lives in a leased job row
rather than in the request.

### Idempotency at every layer

| Layer | Guard |
|---|---|
| Webhook | `@@unique([provider, eventId])` on `WebhookEvent` |
| Job dispatch | Lease + state machine; a reclaimed job re-renders, which is safe |
| Report creation | `@@unique([orderId, version])` — a duplicate dispatch cannot create two `Report` rows |
| Email | A `Delivery` row per `(report, channel)`; send only if none exists in `sent` |
| API creates | `Idempotency-Key` header → `IdempotencyKey` table |

---

### The 10-hour delivery rule

A reading nobody has looked at used to wait in the queue for as long as the business took to get to
it — days, sometimes. That is the wrong failure mode for a product that charges up front, so a
reading has a **deadline**: ten hours after the order was **paid** it is released anyway.

```
Order.paidAt ──── 10h ────► /api/cron/sla → approveAndDeliver(outcome: SLA_AUTO)
                                        │
                                        ├─► status DELIVERED, reviewOutcome = SLA_AUTO
                                        ├─► PROFILE delivery (in the same transaction)
                                        └─► email — HELD if the tier owes an MP3 (§ below)
```

**What it is and is not.** The review is a *judgement call* — the 용신 override — not a rewrite: the
prose is the engine's output either way, and the engine's copy rules already forbid predictive or
master-claim language. So an unreviewed reading is a **lesser** reading, not a broken one. What
changes is that it is **recorded** as unreviewed:

| Field | Human path | SLA path |
|---|---|---|
| `reviewOutcome` | `HUMAN` | `SLA_AUTO` |
| `reviewedBy` | the admin's id | `null` — nobody looked |
| `reviewedAt` | when they approved it | when the deadline released it |
| `slaApprovedAt` | `null` | the release time |
| audit action | `deliver` | `sla_deliver` |

`/admin` shows a 30-day count of SLA releases. A number that stays near zero means the human path
is still doing the work; a number that climbs is the business telling you it needs another pair of
hands.

**Both paths are one function.** `lib/review.ts::approveAndDeliver` is the only place a reading is
released — the console's Approve button and the sweep both call it, and the only difference between
them is the `outcome`. The state change and the PROFILE delivery are transactional; the email is
attempted after the commit, and a mail failure never rolls back a release.

**What the sweep will not touch.** A reading whose order is not `PAID`, and anything that is not
`DRAFT_READY` or `IN_REVIEW`. The order is part of the query itself, so un-releasable rows cannot
fill a batch and hide the due readings behind them; an `IN_REVIEW` reading is due at the same
deadline, because claiming it must not extend the client's wait. It is bounded (10 per tick) and
idempotent — a released reading is no longer in the queue, so a second run does nothing. It also
reports paid renders that have been `FAILED` for more than two hours: nothing retries those
automatically, so each one is an order that needs a person.

**The MP3 case.** The deep single-chart tier promises an audio summary. An auto-delivered reading of
that tier is approved at the deadline but its **email waits** for the MP3, so the client gets one
message with the reading and the audio together rather than two messages an hour apart. The reading
is already in their profile either way — only the mail waits. If the audio has not arrived **two
hours** after the release, the reading's email goes out anyway with the existing "your audio is being
prepared" wording: a TTS stall must not become a silent one.

**The trigger.** A scheduled GitHub Actions workflow (`.github/workflows/sla-sweep.yml`) calls
`GET /api/cron/sla` every 15 minutes with `CRON_SECRET` — a Vercel cron cannot run that often on
the Hobby plan (see above). The sweep is **also** run when the owner opens `/admin`, so the queue
cannot grow without bound even if the workflow is not running.

### The queue-alert

When a reading enters the queue, the owner is told once — by email to `ADMIN_EMAILS`, through the
Resend integration that already exists. One message per *batch* (the alert fires when the queue goes
from empty to non-empty, not per reading), no birth details, and a link to the review console. It is
fire-and-forget: a notification failure is logged and nothing else happens, because a ping is never
allowed to affect a delivery.

## 5. The review console — where the product actually happens

**Everything except the free tier passes through here.** The rule is read from the tier map
(`Tier.requiresReview` → `autoDelivers()`), not hard-coded: `processClaimedJob` creates a report as
`DRAFT_READY` when the tier requires review and as `DELIVERED` when it does not. Only the free sample
sets `requiresReview: false`, so it is delivered the moment it renders — no queue, no reviewer — while
every paid tier waits for a human. An **unknown** tier fails safe and is treated as requiring review,
because the dangerous default would be delivering something nobody has looked at.

The free snapshot has its own synchronous path (`POST /api/sample`) and is not orderable through
`/api/orders`, which rejects it with `TIER_NOT_ORDERABLE`: it needs no account, no order and no job, and
routing it through the paid flow would only duplicate that machinery.

**Its artefact is the reading, not a PDF** (since 2026-10-17), so `Report.pdfKey` is null for a sample and
its `htmlKey` is what the library and the detail page serve. The engine's `uploadUrl` is optional, so the
route asks for the reading only (`htmlUploadUrl`) and renders no PDF at all — no throwaway presign and no
swept PDF object (AU-29). A request that targets neither URL is still refused with
`400 MISSING_UPLOAD_URL`.

This is not an admin panel bolted on. Given decision **D5 (always review)**, it is the component
that delivers the promise *"an accurate engine and an honest interpreter."*

```
/admin                       oldest-first list: tier, client, age, status
   │
   ▼
/admin/reports/{id}          inline PDF preview (presigned, 15 min)
   │
   ├─ [용신 override]  Wood · Fire · Earth · Metal · Water  (clearable)
   │     the engine's own single source of truth:
   │     yongsin.favorable_element(chart, override)
   │
   ├─ [Regenerate]     POST /api/admin/reports/{id}/regenerate
   │     → Job(REGENERATE) with the current overrides → new Report.version
   │
   ├─ [Run compliance QA]   tools/qa_compliance.py on the markdown
   │     flags predictive language, master/guarantee claims,
   │     sensitive medical/legal/financial advice, missing hedging
   │
   ├─ [Approve]        → APPROVED → DELIVERED → email + profile
   └─ [Reject]         → FAILED with a reason, client notified
```

**Why the override is the centrepiece.** The engine derives 용신 heuristically and reports its
provenance. A reader who has argued a different favorable element can impose it, and the entire
report — including the "What This Year Means for You" callout — re-derives consistently. That
mechanism already exists end to end (`--favorable-override`, `yongsin.favorable_element()`,
`ctx.favorable_override`), including the fix that closed the two-channel bug class where the callout
and the body could disagree. The review console simply puts a human in front of it.

Practical effect: the reviewer's leverage is not copy-editing, it is **one high-value judgement call**
per chart. That is a 5–10 minute review instead of a 30–90 minute one, which is the difference
between the research's "~15–25 reports/week ceiling" and a business that can actually scale.

Supporting requirements:

- Every override, regenerate, approve, and reject writes an `AuditLog` row with the actor, before and
  after values.
- An override never mutates a delivered report — it creates a new version. The client's received
  PDF is immutable.
- `chartHash` (hash of chart inputs + overrides) short-circuits a regenerate that would produce
  identical output: `409 NO_CHANGE` rather than a wasted render.
- Rejecting requires a reason. It is emailed, and it is the only path where a paid client receives
  bad news, so it must be deliberate.

---

## 6. Delivery

On `approve`, in one transaction: `Report.status = DELIVERED`, `deliveredAt`, `Delivery{channel:PROFILE}`
created, `Delivery{channel:EMAIL}` created as `queued`. The email send happens after commit; a failure
updates that `Delivery` row to `failed` and surfaces in `/admin` — it never rolls back an approval,
because the report *is* delivered once it is in the profile.

| Channel | Mechanism |
|---|---|
| **Profile** | A `Report` row in `DELIVERED`; appears in `/dashboard/reports` |
| **Email** | Resend, from `reports@cosmicsaju.com` with **`Reply-To: hello@cosmicsaju.com`**, linking to the report page. It mentions the audio as "being prepared" only when the tier promises one *and* none is attached yet |

`Report.pageCount` is filled from the engine's `pages` — the two-pass count the ReportLab renderer already
computes for its footer — so the review console shows a real figure instead of an em dash.

Email shape: short, plain-text-first, one link, no attachment by default. Attaching the PDF (~140 KB)
is well within Resend's limits and is a reasonable option for the deep tier — but a link is better
because it (a) drives the user to the account, (b) lets a revoked report actually be revoked, and
(c) avoids the client forwarding a file as "the product".

The email must not overstate. It says the reading has been prepared and reviewed. It does not
predict, promise, or guarantee — the same ground rules as the report prose.

**Replies must have somewhere to land.** Several messages in and around this pipeline explicitly invite
one — the reject email says *"just reply to this email"*, and two report-page states say *"reply to
your order email"*. `EMAIL_FROM` is a *sending* role identity (`reports@`) that nobody sits in, so
`sendEmail()` applies a default **`Reply-To: hello@cosmicsaju.com`** (from `EMAIL_REPLY_TO`) to every
message it sends. Replies therefore reach the human inbox, with the `reports@` receiving alias as a
fallback. See [07](07-services-and-integrations.md) §Mailbox records.

---

### 6.1 The audio summary (Deep tier only)

The Deep Destiny report includes an MP3. It is **derived from the approved text**, never
written by a model, which is what lets it be produced *after* approval without a second review
pass: it says nothing the PDF does not.

```
approve ──► Report DELIVERED ──► email + profile (PDF)          ← delivery does NOT wait
                    │
                    └─► Job(VOICE) ──► engine /script ──► ElevenLabs ──► .mp3 ──► R2
                                                    └─► audioStatus READY ──► "audio ready" email
```

| Step | Where | Note |
|---|---|---|
| Manual attach | `/api/admin/reports/{id}/audio/upload` | A reviewer can put an MP3 there by hand — a recorded narration, a better take, or the audio a compatibility customer asks for under the report's cross-sell. Presigned PUT (a ~10 MB file cannot pass through a function body), then a `HeadObject` verify. The email it sends deliberately **omits the duration**, because nobody measured one |
| Script extraction | `src/saju_html/audio_script.py`, called via `POST /script` | Deterministic; runs the same text pipeline as the PDF renderer (`strip_source_citations` → `strip_engine_drafts` → `translate_inline`) |
| Its input | the **stored** markdown (`Report.mdKey`) | Not a recomputation. An engine deploy between approval and narration would otherwise change the words a client hears |
| Voice | `src/lib/tts.ts` → ElevenLabs `eleven_flash_v2_5` | Chunked on sentence boundaries; `previous_text`/`next_text` keep prosody across joins; ID3 tags stripped so the concatenation does not stop early |
| Storage | R2 `reports/{userId}/{orderId}/{reportId}.mp3` | `Report.audioKey`, `audioBytes`, `audioReadyAt` |
| Status | `Report.audioStatus` — `NONE → PENDING → PROCESSING → READY \| FAILED` | `NONE` for tiers that promise no audio (any compatibility reading) |

**Delivery never waits for the audio.** A text-to-speech outage must not hold a reviewed, paid
report hostage — the PDF is already in the client's profile by the time narration starts. The
client's page shows *"being prepared"* and a second email follows when the MP3 lands. That is why
`audioStatus` exists as a first-class field rather than the audio being part of the report
transaction.

**Only the Deep tier gets audio.** `tierPromisesAudio()` gates it to `SINGLE` + `deep` (or its
legacy alias `fullmap`). The compatibility report merely *cross-sells* the MP3; it does not
include one, so a compat order never queues a voice job.

**Why the script is not reviewed separately.** It is a mechanical rendering of text a human
already approved — same claims, fewer tables. If an LLM ever writes the script instead, that
changes: it would have to be generated *before* approval and approved alongside the PDF.

The narration covers exactly the sections the report promises the audio covers — Chart at a
Glance, Day Master Portrait, Timing, Practical Guidance, Closing Note — on **per-section character
budgets**. A single global budget was tried first and was wrong: the opening sections consumed it
and the timing windows and recommendations were silently dropped, i.e. it would have shipped an
audio summary that did not cover what it claims to.

Verified against the live API with `npm run smoke:tts` (7 assertions: model id, voice id, chunking,
MP3 validity, duration, a repeat call, and that the concatenated join did not corrupt the stream).

## 7. Regeneration and versioning

| Trigger | Result |
|---|---|
| Reviewer changes an override | New `Report.version`; previous → `SUPERSEDED` |
| Engine bug fix | Same — new version, old retained |
| Profile corrected (wrong birth time) | New version, and the old one is retained because it was delivered |
| Client requests a correction | Admin decision; usually a new version after the reviewer looks at the corrected chart |

Rules:

- `version` increments per order; `@@unique([orderId, version])` makes collisions impossible.
- Superseding a **delivered** report does not retract it. The client keeps access to what they
  received, and the new version is delivered as an additional report. Anything else is rewriting
  history a customer may have screenshotted.
- The `.md` source is retained per version, which is what makes a "what did we actually send?"
  question answerable months later.

---

## 8. Failure modes

| Failure | Detection | Response |
|---|---|---|
| Engine cold / slow | `durationMs` in the response, function duration | Retry (lease) → if persistent, raise the `maxDuration` and consider a warm-up ping |
| Engine down | `5xx` / network error | Job returns to `QUEUED` with backoff; after `maxAttempts` → `FAILED` + alert |
| Engine returns bad birth data | `422` | Job → `FAILED` immediately (retrying cannot fix bad input); surface to the reviewer with the field |
| R2 upload "succeeded" but no object | `HeadObject` after the engine call | Job → `FAILED` + alert. Never create a `Report` row pointing at nothing |
| Dispatcher killed mid-run | Lease expires | Next tick reclaims. `attempts` prevents an infinite loop |
| Webhook delivered twice | `WebhookEvent` unique constraint | Return `200` immediately on duplicate |
| Webhook delivered zero times | Order stuck `AWAITING_PAYMENT` while Dodo Payments shows paid | Cleanup cron reconciles recent Dodo Payments orders against our `Order` rows; `mark-paid` as the manual override |
| Email bounces | Resend webhook | `Delivery.status = bounced`, surfaced in `/admin`, so we know a client never got their link |
| Font rendering silently degraded | `Warning: font file not found` in logs | Caught in E1's verification, not in production |
| A delivered PDF has a citation or reviewer note leak | `pdftotext` audit (the repo already does this) | Block approval; this is a build-time test, not a hope |

## 9. Observability

| Signal | Where |
|---|---|
| `/api/health/detail` (authorised) | DB (`SELECT 1`), R2 (head a known-zero-byte sentinel or list one key), engine (`POST /health`) |
| Job health | `Job` grouped by `state`; a growing `QUEUED` count means the dispatcher is not keeping up |
| Review backlog | `/admin` — age of the oldest item — the number that tells you if review is the bottleneck |
| Delivery health | `Delivery` grouped by `status` |
| Engine latency | `durationMs` logged per job (ids only, no PII) |
| Webhook health | Count of un-processed `WebhookEvent` rows older than 5 minutes |
| Cron | Vercel's cron run history |
