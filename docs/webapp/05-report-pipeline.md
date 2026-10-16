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
POST /health  → 200 {"status":"ok","engineVersion":"0.2.0","contractVersion":1,
                     "fontsDir":"/var/task/src/saju_html/fonts"}
POST /chart   → 200  甲戌 癸酉 辛丑 乙未 · 辛 Metal · Water via strong-dm-drain
POST /generate (deep) → 200  139898 bytes · 1877 ms · sha256 matched after download · valid PDF
```

`fontsDir` pointing at `/var/task/src/saju_html/fonts` is the proof that **E1 works inside the deployed
function** — it found the *bundled* faces rather than the system directory, which does not exist there.

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

**Consequence accepted:** delivered PDFs will differ slightly from the demo PDFs already in
`apps/landing-page/public/`. **Regenerate those demos with `SAJU_PDF_BACKEND=reportlab`** so the
marketing preview matches the delivered artefact. Shipping a sample that looks different from the
product is a refund request waiting to happen.

**Escape hatch if fidelity ever matters more than simplicity:** Vercel supports OCI container-image
functions. A container with Python + Chromium restores the HTML templates byte-for-byte. That is a
later, isolated change to this one project — it does not touch the webapp.

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

// 422  { "error": "…", "code": "INVALID_BIRTH_DATA" }
// 422  { "error": "…", "code": "UNKNOWN_TIMEZONE" }
// 500  { "error": "render failed", "code": "RENDER_FAILED" }   // exception CLASS only
```

`contractVersion` is checked and rejected on mismatch. It exists so the two Vercel projects can be
deployed independently: a webapp that ships a new field before the engine understands it must fail
loudly, not silently produce a wrong report. The CI contract test runs on both sides.

### Required engine changes — status

| # | Change | Status |
|---|---|---|
| **E1** | `SAJU_FONT_DIR` env override + bundled DejaVu | ✅ **done.** `md_to_saju_pdf.py` now resolves in order: `$SAJU_FONT_DIR` → `<package>/saju_html/fonts/` → `/usr/share/fonts/truetype/dejavu`. Five faces + their licence are bundled (3.0 MB), and the resolver *prefers* the bundle, so output is identical on every host — which is what the renderer docs wanted. A missing directory now warns with every path it searched, instead of a bare `font file not found`. `/health` reports the resolved `fontsDir`, so a silent fallback is visible. |
| **E2** | No silent geocoding | ✅ **done, and narrower than first thought.** `sajupy` geocodes **only when `longitude is None`** (`sajupy/core.py:406`); the webapp always supplies one, so our path never geocoded. The residual risk was a profile with `longitude = NULL`, which would trigger a live Nominatim call and *change the chart*. The service now **refuses** with `422 MISSING_LONGITUDE` rather than falling back — a refusal is honest, a silent fallback is a wrong chart. |
| **E3** | Thread `favorable_override` through the single-chart path | ✅ **done.** Added to `chart_markdown()`, `prepare_chart_render()` and `build_pdf_from_chart()`, forwarded to `generate_premium_report(..., favorable_override=…)`. This is what makes the review console's 용신 override work for single charts, not just compatibility readings. |
| **E4** | FastAPI entry with presigned upload, PII-safe errors | ✅ **done** — `api/index.py`, three endpoints, bearer auth, `HEAD`-style contract version check, class-name-only logging |
| **E5** | Regenerate `apps/web/public/demo-*.pdf` with ReportLab | ⬜ **still open** — and now it also carries the MP3 decision (see [13 — Launch audit](13-launch-audit.md) D1) |
| **E6** | Contract tests | ✅ **done** — `tests/test_report_engine_service.py`, **20 cases**, no network and no storage. They call the endpoint functions directly rather than through `TestClient`, because the local httpx 0.28 dropped the `app=` argument that starlette 0.36's `TestClient` still passes; testing the functions is faster and version-proof. |

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
| `reports/anonymous/{uuid}/sample.pdf` | Free samples not yet claimed | Swept after 7 days, **by object age** (see [09](09-operations.md)) — an anonymous sample creates no row to track, so a row-driven sweep found nothing |
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
| **Dodo Payments webhook → `after()`** | `runDispatchTick(1)` | Primary path. `after()` from `next/server` lets the webhook return its 2xx promptly and generate afterwards |
| **`POST /api/jobs/kick`** | `kickOwnerJobs(userId)` | A client taps "Check for updates". Scoped to that caller's orders only, rate limited |
| **Daily cron** (04:00 UTC) | `runDispatchTick(3)` | Safety net for anything the above missed |

Restoring true per-minute dispatching is a **one-line change** on Pro — `"schedule": "* * * * *"` — with
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

On Hobby there is no per-minute cron, so the webhook *is* the trigger — but it still does not block:
`after()` from `next/server` runs the dispatch once the response has already been sent, so the provider
gets its 2xx first. If the dispatch fails, the job stays `QUEUED` and the recovery paths (the daily
cron, the dashboard kick, an admin regenerate) pick it up. The webhook is never the single point of
failure for a paid order, either way. Delivery is gated on human review regardless, so the work must
survive an arbitrary wait — which is why it lives in a leased job row rather than in the request.

### Idempotency at every layer

| Layer | Guard |
|---|---|
| Webhook | `@@unique([provider, eventId])` on `WebhookEvent` |
| Job dispatch | Lease + state machine; a reclaimed job re-renders, which is safe |
| Report creation | `@@unique([orderId, version])` — a duplicate dispatch cannot create two `Report` rows |
| Email | A `Delivery` row per `(report, channel)`; send only if none exists in `sent` |
| API creates | `Idempotency-Key` header → `IdempotencyKey` table |

---

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

This is not an admin panel bolted on. Given decision **D5 (always review)**, it is the component
that delivers the promise *"an accurate engine and an honest interpreter."*

```
/admin/queue                 oldest-first list: tier, client, age, status
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
| **Email** | Resend, from `reports@cosmicsaju.com` with **`Reply-To: hello@cosmicsaju.com`**, linking to the report page |

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
| `/api/health` | DB (`SELECT 1`), R2 (head a known-zero-byte sentinel or list one key), engine (`POST /health`) |
| Job health | `Job` grouped by `state`; a growing `QUEUED` count means the dispatcher is not keeping up |
| Review backlog | `/admin/queue` age of the oldest item — the number that tells you if review is the bottleneck |
| Delivery health | `Delivery` grouped by `status` |
| Engine latency | `durationMs` logged per job (ids only, no PII) |
| Webhook health | Count of un-processed `WebhookEvent` rows older than 5 minutes |
| Cron | Vercel's cron run history |
