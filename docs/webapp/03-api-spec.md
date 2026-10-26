# 03 — API spec

Two APIs live in this system:

1. **The webapp API** — Next.js route handlers under `apps/web/src/app/api/`. This is the one browsers
   call. It is the only API with authentication.
2. **The engine API** — FastAPI at `api/index.py` (the Vercel project's Root Directory is the repository
   root; see [05](05-report-pipeline.md) §1.1). It is internal, called only by the webapp, and
   authenticated by a single shared bearer token. See
   [05 — Report pipeline](05-report-pipeline.md) for its full contract.

## Conventions (webapp API)

| Convention | Rule |
|---|---|
| **Error envelope** | `{ "error": "<human readable>", "code": "<SCREAMING_SNAKE>" }` — always both keys |
| **Status mapping** | zod failure → **422**; unique violation (P2002) → **409**; not found (P2025) → **404**; unauthorised → **401**; forbidden → **403**; cross-user resource → **404** (never 403) |
| **Ownership** | Every query is scoped by `userId`. Cross-user access returns 404 so existence is not disclosed |
| **Auth resolution** | `requireUser()` / `requireRole()` read the DB fresh. Never trust a token claim |
| **Mutations** | Always inside `prisma.$transaction`, and always writes an `AuditLog` row **with the same `tx`** |
| **Idempotency** | Any route that creates a row the client may retry accepts an `Idempotency-Key` header and uses `withIdempotency()` |
| **Rate limits** | Postgres-backed, fixed window. Bucket = `"<action>:<userId\|ip>"` |
| **Validation** | zod schema per route in `src/lib/validation/schemas.ts`. Enums are shared with Prisma and the DB `CHECK` constraints |
| **Logging** | Never log birth data, names, emails, tokens, or signed URLs. Log ids and error classes only |
| **Caching** | All authenticated routes are dynamic. No `Cache-Control` on anything containing PII |

The `handle()` wrapper is the front door for every route: it catches `ApiError` and Prisma/zod
errors, maps them to the envelope above, and guarantees no unexpected error text reaches the client.

```ts
export const POST = handle(async (req: Request) => {
  const user = await requireUser();
  const body = await parseJson(req, orderSchema);
  await rateLimit(`order:${user.id}`, 10, WINDOW.hour);
  // …
  return json({ order }, 201);
});
```

## Route index

### Public

| Method | Path | Purpose | Rate limit |
|---|---|---|---|
| `GET` | `/api/health` | Minimal liveness for monitors: `{ok, status, version, checkedAt}`. No configuration detail. 200 `{status:'ok',…}` / 503 `{status:'degraded',…}` | none |
| `POST` | `/api/sample` | Generate a free sample **reading** (the web document). No account required, and no PDF — see the response below | 5 / min / IP |
| `POST` | `/api/share-card` | The reader's own Day Master card, a 1080×1920 PNG. No account required — it is the free snapshot's growth loop. Carries no birth data (built from `shareCardFields()`), stores nothing | 5 / min / IP |
| `POST` | `/api/sample/email` | Email the free snapshot, and record the lead (`SampleLead`). No account required. Stores no birth data — only the address and the marketing choice | 5 / min / IP **and** 20 / h / IP **and** 2 / h / recipient |

> **There is no `/api/contact` route, deliberately.** An earlier draft specified one; it was never built.
> Contact is a `mailto:` to a monitored address (`hello@`, or `privacy@` for data-protection requests —
> see [07](07-services-and-integrations.md) §Mailbox records). A form would add a spam surface, a
> deliverability problem, and a second place for a message to be lost, in exchange for nothing a mail
> client does not already provide.

### Auth (proxied)

| Method | Path | Purpose |
|---|---|---|
| `*` | `/api/auth/[...path]` | Passes every verb through to Neon Auth's handler. Not authored by us — see [04](04-auth-and-roles.md) |

### Account

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/account` | user | Profile of the signed-in user + consent state |
| `PATCH` | `/api/account` | user | Display name, locale |
| `POST` | `/api/account/consent` | user | Record a consent grant/withdrawal |
| `GET` | `/api/account/deletion` | user | Deletion request state |
| `POST` | `/api/account/deletion` | user | Schedule account deletion (30-day grace) |
| `DELETE` | `/api/account/deletion` | user | Cancel a scheduled deletion |

### Profiles

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/profiles` | user | List own profiles |
| `POST` | `/api/profiles` | user | Create a profile (resolves lat/long/tz server-side). **Requires an active `service` consent** -> `403 CONSENT_REQUIRED` |
| `GET` | `/api/profiles/{id}` | user | Read one |
| `PATCH` | `/api/profiles/{id}` | user | Update. **Requires an active `service` consent** -> `403 CONSENT_REQUIRED` (it can rewrite birth data) |
| `DELETE` | `/api/profiles/{id}` | user | Soft delete |

### Orders

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/orders` | user | Create an order. Returns a checkout URL for paid tiers. **Rejects the free tier** with `422 TIER_NOT_ORDERABLE` — the snapshot has its own path. Requires `Idempotency-Key`, and requires `adultConfirmed: true` (an absent field is a refusal — see [10](10-privacy-and-compliance.md) §Minors) |
| `GET` | `/api/orders` | user | List own orders |
| `GET` | `/api/orders/{id}` | user | Read one |
| `POST` | `/api/orders/{id}/checkout` | user | Re-issue a hosted checkout for an unpaid order (abandoned first attempt) |

> **Tier storage convention.** `Order.tier` and `Report.tier` hold the **engine** tier (`sample`,
> `essential`, `deep`, `basic`), with `Order.kind` (`SINGLE` | `COMPAT`) disambiguating. `deep` alone
> is therefore ambiguous — resolve display names and store variants with
> `tierFor(kind, tier)` / `variantIdForOrder(kind, tier)`, never with a bare id lookup. The client
> sends the **UI** id (`compat-deep`), which the route maps via `getTierById`.

### Reports

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/reports` | user | List own reports (dashboard library) |
| `GET` | `/api/reports/{id}` | user | Metadata: tier, status, dates, page count |
| `GET` | `/api/reports/{id}/html` | user | **The reading**: the stored web document, streamed as `text/html` with a strict CSP and `noindex`. `409 REPORT_NOT_READY` before delivery, `404 NO_WEB_DOCUMENT` when the report has no web version |
| `GET` | `/api/reports/{id}/download` | user | **Download the reading** (`kind=html`, the default) as one self-contained `.html`. `?kind=pdf` gives the PDF; with no `kind` a report that has no web document falls back to the PDF |
| `GET` | `/api/reports/{id}/download?disposition=attachment` | user | Streamed forced download (`octet-stream` for the PDF) |
| `DELETE` | `/api/reports/{id}` | user | Delete report + queue the R2 object for deletion |
| `GET` | `/api/reports/{id}/audio` | user | 302 to a presigned GET for the MP3; `?disposition=attachment` streams it. `409 AUDIO_NOT_READY` while being prepared, `404` when the tier has no audio |
| `POST` | `/api/reports/{id}/audio` | user | The narration text, for reading instead of listening (and for audit) |

### Admin

All admin routes require `role = ADMIN` and additionally check that the actor's email is in
`ADMIN_EMAILS`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/admin/queue` | Orders/reports awaiting review, oldest first |
| `GET` | `/api/admin/reports/{id}/preview` | Short-lived presigned URL for the inline viewer. `?kind=pdf` (default) signs the PDF; `?kind=html` signs the **web document** — the reading. `404 NO_WEB_DOCUMENT` when the report has no reading, `409 NO_ARTIFACT` when there is no PDF |
| `POST` | `/api/admin/reports/{id}/override` | Set/clear the 용신 override on the order |
| `POST` | `/api/admin/reports/{id}/regenerate` | Enqueue a `REGENERATE` job with the current overrides |
| `POST` | `/api/admin/reports/{id}/approve` | Approve → deliver (email + profile) |
| `POST` | `/api/admin/reports/{id}/reject` | Mark failed with a reason; notify the client |
| `POST` | `/api/admin/orders/{id}/mark-paid` | Manual payment (comps, invoice, MoR fallback) |
| `POST` | `/api/admin/reports/{id}/audio` | Prepare or retry the audio summary (TTS). Normally queued automatically at approval |
| `POST` | `/api/admin/reports/{id}/audio/upload` | **Begin a manual audio upload** → `{ uploadUrl, key, expiresIn }`. Presigned because a ~10 MB MP3 is far past a function body limit; the browser PUTs straight to R2. `409 NO_ORDER` for a report with no order |
| `PATCH` | `/api/admin/reports/{id}/audio/upload` | **Confirm it** — re-derives the key (never trusts the one sent), verifies with `HeadObject`, marks the audio `READY`, and emails the client if the report is already delivered. `403 KEY_MISMATCH`, `409 UPLOAD_NOT_FOUND`, `422 EMPTY_UPLOAD` |
| `POST` | `/api/admin/orders/{id}/refund` | Record a refund; cancel or leave the report |

### Webhooks

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/webhooks/dodo` | HMAC signature | `order_created` → paid + enqueue; `order_refunded` → refunded |
| `POST` | `/api/webhooks/resend` | signature | Bounce/complaint → update `Delivery` |

### Operations

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/api/health/detail` | `Authorization: Bearer $HEALTH_DETAIL_TOKEN`, **or** an admin session (`ADMIN_EMAILS` + `role: ADMIN` + verified email) | The full health snapshot: db/storage/engine booleans, `engineDetail`, `payments` + `paymentsMode`, `botProtection` + `botProtectionConfigured`, `missingProducts`, `status`, `version`, `checkedAt`. Same 200/503 rule as the public route; `401 UNAUTHORIZED` without disclosing anything (AU-31) |

The engine probe behind both routes is cached for 60 seconds; see
[09 — Operations](09-operations.md#health-checks).

### Cron

| Method | Path | Auth | Schedule |
|---|---|---|---|
| `GET`/`POST` | `/api/cron/dispatch` | `Authorization: Bearer $CRON_SECRET` | every 15 minutes (GitHub Actions); daily Vercel cron fallback |
| `GET`/`POST` | `/api/cron/cleanup` | same | daily |

Cron routes must accept both `GET` and `POST` (Vercel Cron uses `GET`) and must be safe to run
concurrently — the dispatcher and cleanup are both idempotent by construction.

---

## Endpoint detail

### `POST /api/sample`

The funnel. Deliberately account-free.

```jsonc
// request
{
  "fullName": "Jisoo K.",
  "gender": "F",
  "birthDate": "1994-09-12",
  "birthTime": "13:28",
  "timeKnown": true,
  "timezone": "Asia/Seoul",
  "city": "Seoul",
  "country": "KR",
  "turnstileToken": "…",
  "idempotencyKey": "…"
}
```

```jsonc
// 200
{
  "ok": true,
  "sampleId": "5d3f…",          // random; the email step's handle. Only NAMES an object — every read
                                //   re-derives the key server-side, so it cannot point at anyone else's
  "readUrl": "https://…r2.cloudflarestorage.com/…&X-Amz-Expires=900",
  "expiresIn": 900,
  "bytes": 273689,             // the READING's size — there is no PDF to report on
  "engineVersion": "0.2.0",
  "savedToProfile": false
}
```

**The free tier is the reading, with no PDF** (since 2026-10-17). A sample is one page of chart, so the
PDF was the worst way to present it: it leaves the site, cannot be read on the phone that requested it,
and looks nothing like what a paid client receives. The engine still *requires* an upload target for a
PDF (that is the contract), so one is presigned — always under the **swept** `reports/anonymous/` prefix
and never recorded on a row, so it cannot become dead storage nobody can reach. For a signed-in visitor
the *reading* is what is kept. Consequently `Report.pdfKey` is **null** for a sample, and the reused-sample
lookup filters on `htmlKey`; a sample saved before this change has no reading and is superseded by a
fresh render rather than reused.

⚠️ **The response carries no chart.** An earlier version of this page documented `dayMaster` and
`chartPreview.pillars` here; the route has never returned them. That matters, because the same page
described the free flow as confirming the derived pillars before the snapshot — it does not (see
[06](06-frontend-ux.md) §Free sample, and the open item in `MEMORY.md`). Pillars are confirmed in the
**order flow**, from `Profile.chartJson`, which is populated by the engine's `/chart`.

**Signed in?** The snapshot is *kept*: a `Report` is filed as `DELIVERED` under
`reports/{userId}/samples/…` and a link to it appears in the dashboard library. A repeat request for the
same birth details returns the **stored** report (`reused: true`, same `reportId`) rather than rendering
the identical chart again — so the free endpoint is idempotent per person and the library does not fill
with duplicates. Signed out, nothing is persisted and the object lives under `reports/anonymous/…`,
which is swept after 3 days.

Errors: `422 VALIDATION_FAILED` (bad or missing birth fields), `409 BIRTH_DATA_AMBIGUOUS`
(the engine flagged a solar-term or hour-boundary knife-edge and wants confirmation), `429
RATE_LIMITED`, `403 TURNSTILE_FAILED` (bot check not satisfied — see below), `503 STORAGE_UNAVAILABLE`,
`503 ENGINE_UNAVAILABLE`.

**Turnstile.** The form is protected by Cloudflare Turnstile. `turnstileToken` is verified server-side
**before** any storage or engine work, so a failed check costs nothing.

`TURNSTILE_MODE` controls enforcement: `off` (default) skips verification entirely, `log` verifies and
records but **never refuses**, and `enforce` returns `403 TURNSTILE_FAILED` on an absent or invalid token.
**Deploy new keys at `log`**, confirm real visitors actually receive tokens, then move to `enforce`. The
switch exists because this control can take the whole funnel down: a widget that fails to render produces
no token, and an enforcing server then refuses *everybody* — which happened on 2026-10-16. The
authorised `/api/health/detail` reports the live mode as `botProtection`, so a `log` rollout is visible
rather than mistaken for
`enforce`; see [14](14-security.md) §4 for the flip.

`TURNSTILE_SECRET_KEY` and the public site key must be deployed as a pair — the secret alone verifies, the
site key alone renders, and only both together protect anything. Note the site key is public by design
(it is rendered into the HTML) and must be added to Vercel with an explicit `--type config`; Vercel's CLI
otherwise refuses any `NEXT_PUBLIC_*` name that looks like a credential.

The ground rule it serves is real — **no silent auto-calculation of the four pillars** — but it is
enforced in the **order flow**, not here: `Profile.chartJson` is populated from the engine's `/chart`
when a profile is created, and `/reports/new` shows those pillars before payment. See
[06](06-frontend-ux.md) §Free sample for the corrected account of the free path.

### `POST /api/share-card`

The reader's own **Day Master card** — a 1080×1920 PNG they can post. Public on purpose: it is the
growth loop for the account-free free snapshot, so gating it behind sign-up would defeat it.

```jsonc
// request — the same shape as /api/sample (birth fields are required, turnstile/idempotency are not)
{
  "fullName": "Jisoo K.",
  "gender": "F",
  "birthDate": "1994-09-12",
  "birthTime": "13:28",
  "timeKnown": true,
  "city": "Seoul",
  "countryCode": "KR"
}
```

Returns `200` with `content-type: image/png` and `cache-control: private, no-store` plus
`x-robots-tag: noindex`. It is a **POST** deliberately: birth details must not travel in a query
string, where they would land in access logs and referrers.

Nothing is stored — no R2 object, no row — so there is nothing to sweep. The card is built from
`shareCardFields()`, which returns only derived values, so it cannot carry a birth date, time, place or
name; that is asserted in `src/lib/__tests__/share-card.test.ts`, and the reader is about to publish the
result.

**No Turnstile here, deliberately.** A token is single-use, so the one spent on `/api/sample` cannot be
reused, and mounting a second challenge for a cosmetic image is real friction. The exposure (an
unauthenticated engine call) is bounded by the rate limit instead. Errors: `422 VALIDATION_FAILED`,
`429 RATE_LIMITED`, `503 ENGINE_UNAVAILABLE`.

### `POST /api/sample/email`

The one thing the free snapshot was missing: a way to be contacted again. Optional, and taken **after**
the result is on screen — never a wall in front of it (see [06](06-frontend-ux.md) §Free sample).

```jsonc
{
  "sampleId": "5d3f…",
  "email": "Someone@Example.com",   // lower-cased and validated
  "marketingOptIn": false           // defaults to false; omitted ≠ consent
}
```

```jsonc
// 201
{ "ok": true, "emailed": true, "expiresInDays": 7 }
```

- **The key is re-derived server-side from `sampleId`** (anonymous prefix, or the owner's prefix if
  signed in) and confirmed with a `HEAD` before anything is sent. The caller never supplies a key or a
  URL, so there is nothing here to point at someone else's file; `sampleEmailSchema` has no such field,
  and a test asserts unknown keys are stripped.
- **The lead is written before the send.** The address is the point of the exercise and the mail is the
  side effect, so a Resend outage must not lose it. If email is unconfigured, the response still
  `201 {emailed:false}` rather than pretending it sent.
- **The link lasts 3 days**, not 900 s, and that number comes from `ANONYMOUS_SAMPLE_RETENTION_DAYS`
  (`lib/retention.ts`) rather than being written twice — the anonymous object is swept at 3 days, and a
  link that outlives its object is a 404 sent to someone who asked for their chart. `retention.test.ts`
  fails if the two ever drift. This is the longest a link can **usefully** be:
  longest a link can usefully be. A longer URL would outlive its object.
- Errors: `422 VALIDATION_FAILED`, `404 SAMPLE_EXPIRED` (past the sweep — the UI offers a fresh
  snapshot), `429 RATE_LIMITED`, `502` when the send failed though the lead was kept.

### `POST /api/profiles`

```jsonc
{
  "label": "Me",
  "fullName": "Jisoo K.",
  "gender": "F",
  "birthDate": "1994-09-12",
  "birthTime": "13:28",
  "timeKnown": true,
  "timezone": "Asia/Seoul",
  "city": "Seoul",
  "country": "KR"
}
```

Server-side: look up `latitude`/`longitude` in the bundled city table (fail with
`422 CITY_NOT_RESOLVED` rather than silently falling back to solar-time-off), verify the timezone or
derive the UTC offset via `zoneinfo` (historical and DST aware — the engine's
`derive_utc_offset()` is the reference implementation), then insert.

Returns `201 { profile }`. The first profile created for a user is automatically `isDefault: true`.

### `POST /api/orders`

```jsonc
{
  "tier": "deep",              // "essential" | "deep" | "compat-basic" | "compat-deep"
  "profileAId": "cuid",
  "profileBId": null,          // required for compat tiers
  "idempotencyKey": "…",
  "adultConfirmed": true       // required; must be true. Absent is refused, not defaulted
}
```

```jsonc
// 201 — paid tier
{
  "order": { "id": "cuid", "status": "AWAITING_PAYMENT", "priceCents": 5500, "currency": "USD" },
  "checkoutUrl": "https://checkout.dodopayments.com/…"
}
```

The client-supplied price, if any, is **ignored**. `priceCents` comes from the server tier map.

Errors: `422 TIER_PROFILE_MISMATCH` (e.g. a compat tier with no `profileBId`), `422 TIER_NOT_ORDERABLE`
(the free tier), `404` if a profile does not belong to the caller, `409` on an idempotency-key reuse with
a different body.

### `GET /api/reports/{id}/html` — the reading

Ownership and delivery state are checked exactly as for a download, and then the stored web document
is streamed **through the app** rather than redirected to R2, because the response needs a policy that
a redirect cannot set:

| Header | Value | Why |
|---|---|---|
| `Content-Type` | `text/html; charset=utf-8` | It is a document |
| `Content-Security-Policy` | `default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'` | The document is self-contained and scriptless; the policy makes that a guarantee rather than a property of today's template |
| `X-Robots-Tag` | `noindex, nofollow` | A private link, in a reader's hands |
| `Cache-Control` | `private, no-store` | Personal data; nothing in between caches it |
| `Referrer-Policy` / `X-Content-Type-Options` | `no-referrer` / `nosniff` | — |

`DRAFT_READY`/`IN_REVIEW` return `409 REPORT_NOT_READY`. A report with no web document — a
compatibility reading, or one rendered before the web document existed — returns
`404 NO_WEB_DOCUMENT`, which the UI treats as "offer the PDF instead".

### `GET /api/reports/{id}/download`

**Default `kind=html`**: the reading, streamed with `Content-Disposition: attachment;
filename="cosmic-saju-reading-<id>.html"` and the same policy as above — one file the client can keep
and open anywhere. **`kind=pdf`**: the PDF keepsake, streamed as `application/octet-stream` with
`X-Report-SHA256` for integrity.

With no `kind` and no web document on the row, the route falls back to the PDF rather than failing: the
client asked for their reading, not for a format. Otherwise the original behaviour stands — presign a
1-hour R2 GET and `302`, streaming only when `disposition=attachment`.

A `DRAFT_READY` or `IN_REVIEW` report is **not** downloadable by its owner. Until it is `DELIVERED`
there is nothing to download, and the API says so with `409 REPORT_NOT_READY`.

### `POST /api/webhooks/dodo`

Dodo Payments follows the **Standard Webhooks** specification. Endpoint:
`https://www.cosmicsaju.com/api/webhooks/dodo`.

1. Read the **raw body before parsing** — the signature covers the exact bytes, and re-serialising JSON
   changes them.
2. Verify the signature (`src/lib/webhook-signature.ts`): HMAC-SHA256 over
   `{webhook-id}.{webhook-timestamp}.{raw body}`, base64-encoded, secret base64-decoded after stripping
   an optional `whsec_`. The `webhook-signature` header may hold several space-separated `v1,<sig>`
   candidates; **any** match passes, compared in constant time. Reject when the timestamp is more than
   5 minutes from now (replay), and reject with **401** on any failure — an unverified webhook is a free
   report.
3. `WebhookEvent` insert keyed on `(provider='dodo', eventId=<webhook-id>)`; on P2002 return
   **200 immediately** — a duplicate delivery is not an error, and returning non-2xx makes Dodo retry
   forever.
4. Branch on `payload.type`:

   | Event | Action |
   |---|---|
   | `payment.succeeded` | Find the order via `payload.data.metadata.order_id` → in one transaction: `Order → PAID`, `paidAt`, `provider='dodo'`, `providerOrderId=<payment_id>`, create `Job(QUEUED)`, `AuditLog{actorId: null}`. Then dispatch generation via `after()` |
   | `payment.failed` / `payment.cancelled` | Audit only. **The order is left unpaid** so the customer can retry — Dodo reuses `metadata.order_id` on a fresh checkout |
   | `refund.succeeded` | `Order → REFUNDED` + audit |

5. Mark the event processed. Return 200.

**Fulfil on the webhook, never on the browser redirect.** The redirect is missed whenever a customer
closes the tab; the webhook is retried until acknowledged. If `metadata.order_id` is absent the payment
cannot be matched and nothing is fulfilled — which is why the checkout session always sets it.

Anything that throws after step 3 leaves the event un-processed; the daily cleanup cron retries
un-processed events older than a minute.

### `POST /api/webhooks/resend`

Bounce/complaint handling for delivery email — see [`07`](07-services-and-integrations.md).

---

## The engine API (internal)

Full route reference lives in [05 — Report pipeline](05-report-pipeline.md). Summary:

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/generate` | `Authorization: Bearer $ENGINE_SERVICE_TOKEN` | Compute a chart, render a PDF, PUT it to a presigned URL |
| `POST` | `/chart` | same | Derive the chart summary only (no render) — stored on `Profile.chartJson` when a profile is created |
| `POST` | `/generate` | same | Renders and uploads. Returns integrity metadata — **including `pages`**, the two-pass page count the ReportLab renderer already computes for its footer, so the review console can show a real figure. `null` when the backend cannot report one |
| `POST` | `/script` | same | Derive the spoken-word audio script from an approved report's markdown. Deterministic; returns `{script, chunks, stats}` |
| `POST` | `/health` | same | Report engine version, dependency readiness, warm-up |

```
POST /generate
{
  "contractVersion": 1,
  "kind": "single" | "compat",
  "tier": "sample|essential|deep|basic",
  "uploadUrl": "https://…r2.cloudflarestorage.com/reports/…?X-Amz-Signature=…",
  "mdUploadUrl": "optional — where to also PUT the source markdown",
  "profileA": { "fullName","gender","birthDate","birthTime","timezone","utcOffset","city","longitude","latitude" },
  "profileB": { … },                       // compat only
  "favorableOverrideA": "Water",           // optional, set by a reviewer
  "favorableOverrideB": "Fire"
}
```

```jsonc
// 200
{ "sha256": "…", "bytes": 142276, "pages": 7, "engineVersion": "saju-engine/0.2.0", "durationMs": 1642 }
// 422 { "error": "…", "code": "INVALID_BIRTH_DATA" }        // birth data only; permanent
// 503 { "error": "…", "code": "UPLOAD_HOSTS_UNCONFIGURED" }  // config/auth fault; retryable
// 500 { "error": "…", "code": "RENDER_FAILED" }              // exception class only, never a message with PII
```

Every error body is `{ error, code }`, including auth failures and bodies pydantic rejects before an
endpoint runs. Only birth-data validation is 422 (the webapp treats that as permanent); all
configuration and availability faults are 503 and are retried.

`uploadUrl` is presigned by the webapp so the PDF never transits a request/response body — which
also keeps every payload comfortably under Vercel's 4.5 MB function limit.
