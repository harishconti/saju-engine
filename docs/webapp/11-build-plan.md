# 11 — Build plan

Phases, tasks, and acceptance criteria. Sequenced to fail early rather than late.

## Sequencing principle: risk first

Two things are unproven. Everything else is a variation on code that already exists:

1. **Vercel Python with this engine** (bundle size, fonts, pandas cold start, geocoding removal).
2. **Neon Auth beta** wired into Next 16.

Both are proven or disproven in **phase 1 and phase 2**. If either fails, we find out on day two, not
day twenty — and the fallbacks are known ([07](07-services-and-integrations.md) and
[04](04-auth-and-roles.md)).

## Milestone 0 — a walking skeleton

Before breadth, build the thinnest possible end-to-end thread:

```
/sample form  →  /api/sample  →  engine service  →  PDF in R2  →  download link works
```

No auth, no database, no payments, no review. This single thread proves the riskiest integration
(two Vercel projects + R2 + the engine) in about a day. **Then** widen. Every phase after this one is
additive.

---

## Phase 0 — Provisioning

**Goal:** every external dependency exists and is reachable.

| # | Task | Done means |
|---|---|---|
| 0.1 | **Submit the Dodo Payments store application** | Submitted — this is the long pole, do it first, before any code |
| 0.2 | Resend account + add `cosmicsaju.com` | ✅ Records published **in Cloudflare** (on the `send` subdomain) and verified |
| 0.3 | Verify the Resend domain | ✅ Dashboard and Resend's own API both show **Verified**; a real send is accepted |
| 0.4 | Cloudflare account + R2 bucket | ✅ `saju-engine-dev` — private, round-trip verified, single bucket by decision |
| 0.5 | R2 API token → S3 credentials | Presigned PUT + GET round-trip with a throwaway script |
| 0.6 | Google Cloud OAuth client | ⏸️ **Deferred to >10 users** — Neon's shared dev key is in use meanwhile |
| 0.7 | Neon: verify project `saju`, region, `production` branch | ✅ Both connection string pairs captured (pooled + direct); **production branch only** by decision |
| 0.8 | Enable Neon Auth; configure Google/email/magic-link, trusted origins | `NEON_AUTH_BASE_URL` captured; cookie secret generated |
| 0.9 | Create both Vercel projects with root directories | ✅ `saju-engine` (root `apps/web`) and `saju-report-engine` (root = repo root) |
| 0.10 | Domain: A/CNAME in **Cloudflare**, domain attached in Vercel | ✅ Domain card **Valid Configuration**; apex 308 → www; `https://www.cosmicsaju.com` serves the app |
| 0.11 | **Mailbox + aliases, records published in Cloudflare** | ✅ `hello@` + aliases live; MX/SPF/DMARC published **in Cloudflare** (a mail host cannot write to a zone it does not host) and **receiving verified** (`delivered`); published contact split and `EMAIL_REPLY_TO` wired. ⚠️ The DKIM CNAMEs are still to add ([07](07-services-and-integrations.md) §Mailbox records) |
| 0.12 | Password manager entry with every credential | Inventory complete; nothing only in a chat window |

**Exit:** all `dig` checks in [07](07-services-and-integrations.md) pass; both Vercel projects deploy.

---

## Phase 1 — Report engine service

**Goal:** a URL that turns birth data into a PDF in R2.

| # | Task | Notes |
|---|---|---|
| 1.1 | **E1** — `SAJU_FONT_DIR` override + bundle DejaVu + `outputFileTracingIncludes` | Verify no `Warning: font file not found` in logs |
| 1.2 | **E2** — remove runtime geocoding from the request path | Confirm with a report for a city that is *not* in Nominatim's index |
| 1.3 | **E3** — thread `favorable_override` through `prepare_chart_render` → `chart_markdown` | Single-chart override now works end to end |
| 1.4 | **E4** — `api/index.py`: `POST /generate`, `POST /health` | Bearer auth; contract-version check; PII-safe errors |
| 1.5 | Presigned PUT upload, return `{sha256, bytes, engineVersion, durationMs}` | PDF never crosses the response body |
| 1.6 | `vercel.json` with `maxDuration` + `excludeFiles` | Reported function size well under 500 MB |
| 1.7 | **E6** — contract test + golden-PDF sha256 test | Fails loudly if the contract drifts |
| 1.8 | **E5** — regenerate the five demo PDFs with ReportLab | Marketing preview matches delivered output |
| 1.9 | `pytest` green; validation gate unchanged | 1,909 passing; `run_validation.py` PASS count unchanged |

**Exit:** `/generate` returns a verified object in R2 for `deep` and `compat deep`; cold start < 3 s;
warm < 2 s; Hangul/Hanja render correctly in the compat PDF.

**Fallback if the Python function cannot be made to fit:** Vercel container-image function
(Python + Chromium), which also restores the HTML PDF templates. Costs a heavier build.

---

## Phase 2 — Web app skeleton

**Goal:** sign in, land on an empty dashboard.

| # | Task | Notes |
|---|---|---|
| 2.1 | `apps/web` scaffold: Next 16, TS strict, Tailwind v4, shadcn primitives | Mirrors the existing landing page's design tokens |
| 2.2 | Prisma schema (all 14 models) + first migration | Through `DIRECT_URL`; `CHECK` constraints hand-added |
| 2.3 | `src/lib/prisma.ts` with widened transaction timeouts | `maxWait: 10s`, `timeout: 15s` |
| 2.4 | `src/lib/auth/{server,client,index}.ts` — lazy Proxy pattern | **Build must pass with zero runtime secrets** |
| 2.5 | `src/app/api/auth/[...path]/route.ts` proxy | All five verbs |
| 2.6 | `src/proxy.ts` gate with `/auth/complete` in the matcher | Next 16 naming |
| 2.7 | `/login` — tabbed sign-in/sign-up, Google + email + magic link, consent checkbox | `window.location.origin` callbacks; allowlisted `next` |
| 2.8 | `/auth/complete` — exchange verifier, redirect | |
| 2.9 | `requireUser` / `requireRole` / `handle()` / `ApiError` / error envelope | |
| 2.10 | `/api/health` — db + storage + engine | 503 on any failure |
| 2.11 | Dashboard shell + sign-out | `router.refresh()` after sign-out |
| 2.12 | Audit + rate-limit + idempotency helpers | Postgres-backed |

**Exit:** Google sign-in works locally **and** on the production domain; a `User` row is mirrored;
`/dashboard` 401s when signed out; `npm run build` succeeds with no secrets present.

**Fallback if `@neondatabase/auth` beta blocks:** self-hosted Better Auth on the same Neon database,
or Auth.js. Contained to `src/lib/auth/` by design.

---

## Phase 3 — Profiles and ordering

**Goal:** a user can store birth data and create an order.

| # | Task | Notes |
|---|---|---|
| 3.1 | Bundled city table + server-side coordinate/timezone resolution | No runtime geocoding |
| 3.2 | `derive_utc_offset` parity: zoneinfo-based, historical + DST aware | Port the engine's logic or shell out to the engine's `/health`-adjacent endpoint |
| 3.3 | Profile CRUD routes + validation | `gender` required; `timeKnown` supported |
| 3.4 | `/dashboard/profiles` — list, create, edit, delete | First profile auto-default |
| 3.5 | **Tier map module** (one file: tier → price → variant env) | The single source of truth for pricing |
| 3.6 | `POST /api/orders` with server-side price resolution + `Idempotency-Key` | Client price ignored |
| 3.7 | `/reports/new` — tier picker → profile picker → confirm | Chart shown for confirmation before payment |
| 3.8 | Order list + detail views | |

**Exit:** a profile and an order exist; a tampered price is ignored; a duplicate submit returns the
original order rather than creating a second.

---

## Phase 4 — Generation pipeline

**Goal:** a queued order becomes a `DRAFT_READY` report, unattended.

| # | Task | Notes |
|---|---|---|
| 4.1 | R2 helper: presign put/get, `HeadObject`, delete, batch delete | |
| 4.2 | Job claim query with `FOR UPDATE SKIP LOCKED` + lease | Verify with two concurrent dispatchers |
| 4.3 | `/api/cron/dispatch` — claim, call engine, verify, create `Report` | Bounded at 3 jobs per tick |
| 4.4 | Retry/backoff; `FAILED` on `4xx` (permanent) vs `5xx` (retryable) | |
| 4.5 | Stale-lease reclaim in cleanup | Kill a dispatcher mid-run and confirm recovery |
| 4.6 | `ObjectDeletion` queue + drain | |
| 4.7 | `WebhookEvent` idempotency + un-processed retry | |

**Exit:** an order placed by hand becomes `DRAFT_READY` without intervention; killing the dispatcher
mid-run leaves the job reclaimable; a forced engine `500` retries then fails cleanly.

---

## Phase 5 — Review console and delivery

**Goal:** the product promise, delivered. This is the phase that makes it a real business.

| # | Task | Notes |
|---|---|---|
| 5.1 | `/admin` gate: `role = ADMIN` **and** email in `ADMIN_EMAILS` | Two independent conditions |
| 5.2 | `/admin/queue` — oldest-first, age, tier, client | The oldest-item age is the key operational metric |
| 5.3 | Inline PDF preview (presigned, 15 min) | Keyboard-navigable |
| 5.4 | **용신 override** control + `POST /override` | The headline feature |
| 5.5 | Regenerate → `Job(REGENERATE)` → new `Report.version`, old → `SUPERSEDED` | `chartHash` short-circuits no-op regens |
| 5.6 | Compliance QA integration (`qa_compliance.py`) surfaced in the console | Advisory, not blocking |
| 5.7 | Approve → `DELIVERED` + `Delivery` rows | Transactional |
| 5.8 | Reject with a mandatory reason + client notification | |
| 5.9 | Resend email on approval | Link-first; attachment optional |
| 5.10 | `/dashboard/reports` — library with status timeline | Explain `DRAFT_READY` as "in review", never as a broken state |
| 5.11 | Report detail; download; **refuse download before `DELIVERED`** | `409 REPORT_NOT_READY` |
| 5.12 | Delete report → `ObjectDeletion` | |
| 5.13 | Audit every admin action | before/after values |

**Exit:** end to end — order → draft → override → regenerate → approve → email arrives →
downloadable from the profile; and user B cannot fetch user A's report.

---

## Phase 6 — Payments

**Goal:** money in, once and only once.

| # | Task | Notes |
|---|---|---|
| 6.1 | Dodo Payments products/variants; ids into env | Test mode |
| 6.2 | Checkout creation on order | Hosted checkout, off-site |
| 6.3 | `POST /api/webhooks/dodo` — raw-body HMAC verify | Verify before parsing |
| 6.4 | `WebhookEvent` dedupe → **200 on duplicate** | Never non-2xx on a duplicate, or the provider retries forever |
| 6.5 | Transaction: `PAID` + `Job(QUEUED)` + audit | |
| 6.6 | Refund handling | |
| 6.7 | Admin `mark-paid` manual path | Comps, invoices, MoR fallback |
| 6.8 | Payment reconciliation in cleanup | Catches dropped webhooks |
| 6.9 | ⚠️ **Vercel plan decision** | Hobby blocks any cron more than once per day and **fails the deploy**. Either stay on Hobby (webhook `after()` dispatch + dashboard kick + daily safety net — already implemented) or upgrade to Pro and restore `* * * * *`. See [08a](08a-vercel-json-notes.md) |

**Exit:** a test-mode purchase creates exactly one job across repeated webhook delivery; a forged
signature is rejected; the reconciliation query returns zero rows.

---

## Phase 7 — Landing page and the free sample

**Goal:** the public face, and the funnel. Independent of phases 3–6 — can run in parallel.

| # | Task | Notes |
|---|---|---|
| 7.1 | Port the 9 sections from the worklog inventory + the archived prototype | Hero, Why Saju, Demo Reports, Pricing, Compare Tiers, How It's Built, About Reader, FAQ, Final CTA |
| 7.2 | Design tokens: 오방색 `--el-*`, Cormorant + IBM Plex Mono, elemental rule motif | Inherited, not reinvented |
| 7.3 | `src/components/viz/*` SVG set | FourPillarsChart, ElementBalance, LuckTimeline, DayMasterBadge, SealMark, KoreanWatermark |
| 7.4 | `/sample` flow: birth data → confirm pillars → result → "keep this" | **Do not gate behind sign-up** |
| 7.5 | Turnstile on the sample endpoint | |
| 7.6 | Save-sample-to-profile path | Creates `Profile` + `Report` so it appears in the dashboard |
| 7.7 | **Replace or remove the fabricated testimonials** | Documented FTC risk (LP3) |
| 7.8 | Delivery-window copy matching the review workflow | |
| 7.9 | Header, mobile sticky CTA, footer with disclaimer | |
| 7.10 | Static pages: privacy, terms, refund policy | Dodo Payments requires all three |

**Exit:** Lighthouse ≥ the previous baseline; no horizontal scroll at 390/768/1440; light + dark; axe
clean; a sample PDF downloads and lands in the profile.

---

## Phase 8 — Hardening and launch

| # | Task | Notes |
|---|---|---|
| 8.1 | Consent recording + `/dashboard/account` preferences | |
| 8.2 | Deletion request flow (schedule, cancel, process) | 30-day grace |
| 8.3 | Retention + anonymous-sample sweep | |
| 8.4 | Rate limits on every write path | Postgres fixed-window |
| 8.5 | CSP + security headers | Allow R2 endpoints |
| 8.6 | PII-free logging audit | Grep for any log of name/email/birth data |
| 8.7 | **PDF leak test** — `pdftotext` for citations and reviewer notes | Build-time, not hopeful |
| 8.8 | Playwright public tier: every protected route 401s | Regenerate when routes are added |
| 8.9 | Playwright authed tier: order → report → download; cross-user denial | |
| 8.10 | GitHub Actions CI for both projects | Placeholder env only |
| 8.11 | Uptime monitor on `/api/health` | 5–15 minute interval (see [09](09-operations.md)) |
| 8.12 | Rehearse a restore | An untested backup is a belief |
| 8.13 | Legal review of policy, terms, refund policy, consent wording | External, see [10](10-privacy-and-compliance.md) §9 |
| 8.14 | Launch checklist in [08](08-deployment.md) | Every box ticked |

**Exit:** CI green; `/api/health` green for all three probes; a real purchase completes end to end in
production.

---

## Task graph

```
Phase 0 ──▶ Phase 1 ──▶ Milestone 0 ──▶ Phase 2 ──▶ Phase 3 ──▶ Phase 4 ──▶ Phase 5 ──▶ Phase 6
   │           │             (skeleton)                                │
   │           └─────────────────────────────────────────────────────┐│
   │                                                                 ▼▼
   └──▶ Phase 7 (landing page + sample)  ◀── can run in parallel ──────┘
                                                        │
                                                        ▼
                                                    Phase 8
```

Critical path: **0 → 1 → 2 → 3 → 4 → 5 → 6 → 8**. Phase 7 is off the critical path except for 7.4,
which depends on phase 1.

---

## Effort estimate

| Phase | Days (one developer) | Notes |
|---|---|---|
| 0 | 0.5–1 | Mostly waiting on external verification |
| 1 | 1–2 | Includes the three engine edits |
| 2 | 2–3 | Auth is the risk |
| 3 | 2–3 | City table + offset logic is the fiddly part |
| 4 | 3–4 | The claim/lease logic needs real testing |
| 5 | 3–4 | Largest phase; the PDF viewer and override flow |
| 6 | 2–3 | Mostly configuration + webhook hardening |
| 7 | 2–4 | Depends entirely on how much of the design is reused |
| 8 | 3–4 | Compliance and tests |
| **Total** | **18–28** | |

## Definition of done (product level)

The webapp is done when, without the owner touching the machine:

1. A stranger lands on `cosmicsaju.com` and gets a free sample in under ten seconds.
2. They can create an account and find that sample waiting for them.
3. They can buy the Deep Compatibility report with a card.
4. The order produces a PDF with no human in the loop.
5. The owner reviews it, and can change one judgement call (용신), regenerate, and approve.
6. The client receives an email and finds the report in their profile.
7. They can download it, delete it, or delete their whole account.
8. Nothing in the database leaked into a log, an email, or a shared URL along the way.

Every one of those eight is an acceptance test in [12 — Testing](12-testing.md).

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Dodo Payments rejects or stalls the store | **Blocks revenue** | Submit in phase 0; Paddle fallback; manual `mark-paid` path built regardless |
| `@neondatabase/auth` beta instability | Blocks auth | Quarantined in `src/lib/auth/`; self-hosted Better Auth as the fallback |
| Python function exceeds the bundle limit | Blocks the engine | `excludeFiles`; local closure measured at ~130 MB against a 500 MB limit; container function as the escape hatch |
| ReportLab output looks materially worse than the HTML demos | Product quality | Regenerate the demos with ReportLab and compare side by side **before** launch; container function as the escape hatch |
| Review becomes the bottleneck | Caps revenue at ~15–25/week | The 용신 override turns a 30–90 min review into 5–10 min; measure oldest-item age from day one |
| Birth data is mis-entered | Wrong reports, refunds | Show the derived pillars for confirmation before payment; flag knife-edge cases; `timeKnown` |
| The site implies instant delivery | Refund disputes | Copy must state the review window ([06](06-frontend-ux.md)) |
| Two deploys drift out of contract | Broken reports | `contractVersion` + a contract test in CI on both sides |
| Free-plan ceilings (Neon CU-hours, R2 storage) | Outage | Documented monitoring thresholds in [09](09-operations.md); both are cheap to upgrade |
| Scope creep into "platform" | Never ships | [00 — Overview](00-overview.md) lists what is explicitly out of scope |
