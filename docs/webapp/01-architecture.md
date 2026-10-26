# 01 — Architecture

## The two deployables

```
┌─ Vercel project #1 ────────────────────────┐   ┌─ Vercel project #2 ─────────────────┐
│  apps/web                                  │   │  api/index.py  (root = repo root)   │
│  Next.js 16 · React 19 · TypeScript        │   │  Python 3.12 · FastAPI              │
│                                            │   │                                     │
│  · Public landing page (/)                 │   │  · POST /generate                   │
│  · Auth (/login, /api/auth/[...path])      │   │  · POST /health                     │
│  · Dashboard (/dashboard/…)                │   │                                     │
│  · Admin review console (/admin)           │   │  sajupy + reportlab + jinja2        │
│  · API routes (/api/…)                     │   │  imports src/saju_engine + _html    │
│  · Vercel Cron: dispatch + cleanup         │   │                                     │
│                                            │   │  NO database                        │
│  Prisma ──▶ Neon Postgres                  │   │  NO secrets beyond one bearer token │
│  Neon Auth (managed Better Auth)           │   │  NO persistent state                │
│  @aws-sdk/client-s3 ──▶ Cloudflare R2      │   │                                     │
│  Resend · Dodo Payments                    │   │  maxDuration 300s                   │
└──────────────────┬─────────────────────────┘   └──────────────▲──────────────────────┘
                   │                                            │
                   │  POST /generate                            │
                   │  Authorization: Bearer $ENGINE_SERVICE_TOKEN
                   │  { kind, tier, profileA, profileB?,        │
                   │    favorableOverrideA?, uploadUrl |        │
                   │    htmlUploadUrl }                         │
                   └────────────────────────────────────────────┘
                        engine PUTs the artefact(s) to the presigned R2 URLs
                        and returns { sha256?, bytes?, htmlSha256?, htmlBytes?,
                                      engineVersion }
```

## Why the split is here

The engine is Python. That is the only reason there are two deployables, and it drives every other
architectural choice.

**Options considered:**

| Option | Verdict |
|---|---|
| Rewrite the engine in TypeScript | Rejected. 1,909 tests, a validation gate with 315 cited checks, and years of Korean 명리 lookups. Not a rewrite candidate. |
| Python function inside the Next.js project (`api/*.py`) | Rejected as the default. Works, but Next's output tracing bundles `.next`/`public` into the Python function, which is the documented cause of "A Serverless Function has exceeded the unzipped maximum size of 250 MB". Needs `excludeFiles` + `outputFileTracingExcludes` tuning to stay alive. |
| **Separate Vercel project** | ✅ Chosen. Own root directory, own build, own runtime config, own duration, own rollback. Zero coupling to Next's tracing. |
| Container-image function on Vercel | Deferred. It is the only way to keep the Chromium/HTML PDF templates, and Vercel does support OCI container functions. Heavier builds and slower cold starts for a fidelity gain the review step does not require. See the escape hatch in [05](05-report-pipeline.md). |
| External container worker (Fly.io/Render) | Rejected. Adds a second host, a second deploy path, and a second thing to pay for and monitor — against the D9/D10 posture. |

**Consequence accepted:** two projects must be deployed in a compatible pair. Version the payload
(see the engine contract in [05](05-report-pipeline.md)) and run the contract test on both sides in CI.

## Component responsibilities

| Concern | Owner | Never |
|---|---|---|
| Identity (sign-up, sessions, OAuth) | **Neon Auth** | We do not store passwords, tokens, or sessions |
| User/profile/order/report records | **Neon Postgres** via Prisma | The engine never touches the database |
| Chart computation and report prose | **Report engine service** | The engine never knows about users, prices, or orders |
| PDF bytes | **Cloudflare R2** (private) | Never in Postgres, never a public URL, never a long-lived signed URL |
| Email delivery | **Resend**, orchestrated by the webapp | The engine never sends email |
| Payment and tax | **Dodo Payments** (MoR) | We never see card data; the webhook is the only source of truth for "paid" |
| Rate limiting, idempotency, audit, job leases, R2 deletion queue | **Postgres tables** | No Redis, no broker, no scheduler service |
| Scheduling | **Vercel Cron** | No external cron service |

That table is the whole architecture. Everything below is detail.

## Request paths

### A. Free sample (no account, no order)

```
Browser
  │ POST /api/sample          { profile data, turnstile token }
  ▼
apps/web
  │ rateLimit('sample:{ip}', 5, minute)
  │ validate profile (zod) + resolve lat/long/tz
  │ presign R2 PUT → reports/anonymous/{uuid}/sample.html
  │ POST {ENGINE_URL}/generate  { kind:'single', tier:'sample', htmlUploadUrl, … }
  ▼                              (no uploadUrl — the sample keeps no PDF)
saju-report-engine  (Vercel project #2, root = repository root)
  │ compute_chart() → prepare_chart_render() → render the HTML reading  (~1.6 s total)
  │ PUT the HTML to htmlUploadUrl
  ▼
→ { htmlSha256, htmlBytes }
  │
apps/web
  │ check htmlBytes, verify with HeadObject, then return a short-lived presigned GET
  ▼
Browser opens the reading (Read it / Save it)
```

Notes:
- Anonymous objects live under `reports/anonymous/…` and are swept by the daily cleanup cron.
- If the visitor then creates an account, the webapp copies the profile into `Profile` and the
  sample into a `Report` row so it shows up in their dashboard.
- `maxDuration` on this route should be 60 s — enough for a cold engine start plus render.

### B. Paid report — order to delivery

```
1  POST /api/orders                     → Order(status: awaiting_payment)
                                        → Dodo Payments checkout URL
2  Dodo Payments hosted checkout        (off our infrastructure entirely)
3  POST /api/webhooks/dodo      → verify signature (Standard Webhooks)
                                        → WebhookEvent upsert (idempotent on event id)
                                        → txn: Order → paid, Job → QUEUED, AuditLog
4  GET /api/cron/dispatch  (every 15 min, GitHub Actions; daily Vercel fallback)
                                        → claim job (FOR UPDATE SKIP LOCKED, leaseUntil)
                                        → presign R2 PUT
                                        → POST {ENGINE_URL}/generate
                                        → verify object with HeadObject
                                        → Report(status: DRAFT_READY), Job → SUCCEEDED
5  Owner opens /admin                   → previews the PDF
                                        → optionally sets the 용신 override
                                        → POST /api/admin/reports/{id}/regenerate (new version)
                                        → POST /api/admin/reports/{id}/approve
6  On approve                           → Report → APPROVED → DELIVERED
                                        → Resend: "your report is ready"
                                        → one Delivery row per channel (EMAIL, PROFILE)
7  GET /api/reports/{id}/download       → requireUser + ownership
                                        → 302 to a presigned R2 GET (or stream)
```

Steps 1–2 are the only ones outside our infrastructure. Step 4 is the only place where a serverless
function calls another service and must be crash-safe.

### C. Read paths (dashboard, admin)

Server Components read through Prisma directly with `force-dynamic`, after the auth gate. They do
**not** fetch their own API routes — that would add a hop and lose the request-cached session.

## Why a job queue instead of doing the work inline

The tempting simplification is: "the webhook fires, call the engine right there". Rejected because:

1. **The engine is a network call.** It can be cold (pandas import), slow, or down. Inline means a
   paid order is lost if the call fails at the wrong moment.
2. **Delivery is gated on human review.** The order must survive between "paid" and "owner wakes
   up". That is inherently a persisted state machine, not a function invocation.
3. **Retries need a home.** With a lease-based queue, a crashed dispatcher is recoverable by
   definition: the lease expires and the next tick reclaims the job.
4. **Regeneration is the same job.** A reviewer who overrides the 용신 and regenerates is enqueuing
   the same work with different inputs — one code path, not two.

The queue is a table plus a cron. No broker. This mirrors the crash-safe semantics the existing
in-process `is_stale()` / `requeue_pending()` logic already had, moved into Postgres.

## State machine

```
                    ┌───────────────┐
                    │ awaiting_     │
                    │ payment       │──refund/abandon──▶ cancelled
                    └───────┬───────┘
            webhook: paid   │
                            ▼
   ┌────────────────────paid ──────────────────────┐
   │                    │                          │
   │        Job        ▼                          │
   │      ┌──────────────────────────┐            │
   │      │ QUEUED → RUNNING         │            │
   │      │   ├─ success ──▶ Report  │            │
   │      │   └─ failure ──▶ retry ──┼─▶ FAILED   │
   │      └──────────────────────────┘            │
   │                                              │
   └──────────────────────────────────────────────┘

   Report:  DRAFT_READY ──▶ IN_REVIEW ──▶ APPROVED ──▶ DELIVERED
                  │              │                        │
                  │              └─ reject ─▶ FAILED      └─ regenerate ─▶ SUPERSEDED
                  └─ regenerate (new version) ─▶ SUPERSEDED
```

Invariants:
- A `Report` in `DELIVERED` is immutable. Changes create a new `version`.
- A `Job` is claimed by exactly one dispatcher at a time (lease).
- An `Order` that is `paid` always eventually has at least one `Job`.
- Nothing is emailed before `Report.status = DELIVERED`.

## Technology choices and versions

| Layer | Choice | Version seen locally |
|---|---|---|
| App framework | Next.js, App Router, Turbopack | 16.x |
| UI runtime | React | 19.x |
| Language | TypeScript, `strict: true` | 5.9 |
| Styling | Tailwind CSS (v4, `@tailwindcss/postcss`) | 4.3 |
| Components | shadcn/ui "new-york" over Radix primitives, `lucide-react` | — |
| ORM | Prisma + `@prisma/client` | 5.x |
| Auth | `@neondatabase/auth` (managed Better Auth) | 0.6.0-beta |
| Object storage | `@aws-sdk/client-s3` + `s3-request-presigner` against R2 | 3.x |
| Email | Resend | — |
| Validation | zod | 3.x |
| Unit tests | Vitest + `@testing-library/react` + `happy-dom` + `vitest-axe` | 4.x |
| E2E | Playwright | 1.6x |
| Engine | Python, sajupy + reportlab + jinja2 + markdown-it-py | 3.12 |

⚠️ **`@neondatabase/auth` is beta.** It is deliberately quarantined behind one folder
(`src/lib/auth/`) exposing `getCurrentUser()`, `requireUser()`, and `requireRole()`, so swapping to
self-hosted Better Auth on the same Neon database, or to Auth.js, is a contained change.

## Next.js 16 specifics that bite

| Thing | Detail |
|---|---|
| **`src/proxy.ts`, not `src/middleware.ts`** | Next 16 renamed the middleware convention. The file must also export `default` and a `config.matcher`. |
| **Dynamic `params`** | Route handler and page `params` are a `Promise`. Type them `{ params: Promise<{ id: string }> }` and `await` them. |
| **`force-dynamic`** | Any Server Component reading the session or the DB needs it. Neon's own docs list the missing-`force-dynamic` case as a known failure mode. |
| **Lazy secret access** | Anything constructed at module scope from env vars will break `next build`, which runs without runtime secrets in CI. Use the Proxy pattern in [04](04-auth-and-roles.md). |
| **`output: 'standalone'`** | Only if deploying self-hosted. On Vercel it is unnecessary. |

## Security posture

- Every API route: `handle()` wrapper → `requireUser()` → ownership/role check → validate → mutate in
  a transaction with an audit row.
- Roles and ownership are **read fresh from the database**, never trusted from a token claim.
- Every query is scoped by `userId` (or by an admin check). Cross-user access returns **404, not 403**,
  so the existence of another user's report is not disclosed.
- Uploads: presign → browser/server PUT → verify with `HeadObject` → only then link the row.
- Downloads: presigned GET, 1 hour, issued only after an ownership check; a forced-download variant
  sends `application/octet-stream` + `Content-Disposition: attachment` + `nosniff`.
- Webhooks: HMAC verification + event-id dedupe. An unverified webhook is a free report.
- CSP allows only `self` plus the R2 endpoints; security headers set in `next.config.ts` and
  repeated at the proxy.
- Secrets never reach the client. `NEXT_PUBLIC_*` is treated as public — it is.
