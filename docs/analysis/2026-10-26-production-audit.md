# Production Audit — 2026-10-26

> **Status:** audit complete, **no fixes started**. Execution is planned for the next session —
> see [§ Execution handoff](#execution-handoff). Tracker summary: `docs/issues_bugs.md` →
> "Audit 2026-10-26".

## Why this audit

From 2026-10-18 (commit `0508edb`, upload-host allowlist, fail-closed) to 2026-10-23, the engine
project `saju-report-engine` had no `SAJU_UPLOAD_HOSTS` set, so **every** `/generate` returned
`503 UPLOAD_HOSTS_UNCONFIGURED`. The webapp showed "The report engine failed" and no check, alert, or
dashboard noticed for five days. A visitor (free snapshot, 14 May 1975 05:30, Visakhapatnam) hit it on
2026-10-23. Testing sign-in/sign-up afterwards found two more live bugs. The owner then asked for a
full audit.

Method: three read-only audits (auth & API security; report pipeline & engine; UX, ops, tests,
tracker), then the Critical/P0 claims were re-read in code before being recorded here. Every item has
`file:line` evidence; paths are relative to the repo root unless they start with `src/`, which means
`apps/web/src/`.

**Severity:** **P0** money, data loss, security, or a silent outage · **P1** broken behaviour a user or
the owner hits · **P2** privacy/consent/correctness gaps · **IMP** improvement.

## Already fixed (deployed and verified live, 2026-10-26)

| Commit | Fix | Verified |
|---|---|---|
| env only | `SAJU_UPLOAD_HOSTS=saju-engine-dev.<account>.r2.cloudflarestorage.com` on the engine project | live `/generate` 200, PDF + HTML stored |
| `6027746` | Engine allows `{bucket}.{R2_ENDPOINT host}` (the webapp presigns virtual-hosted); `SAJU_UPLOAD_BUCKET` accepts bucket as path segment or host label; `engine.ts` logs engine status + code | 44 engine-service tests; CI |
| `310fd3d` | Login shows the real auth error (Neon Auth **throws** `AuthError` on non-2xx instead of returning `{error}`); `dashboard/layout.tsx` passed bare `isAdmin` (= `true`) so every user saw "Review queue" | live: "Invalid email or password"; non-admin nav has no admin link |
| `5701ce9` | Account-existence answers on the login page get one neutral sentence | live duplicate sign-up shows neutral copy |

Also confirmed live: one account may hold several concurrent sessions (two independent sign-ins both
stay valid). A test account `ngharish.conti+cs-signuptest-1026@gmail.com` exists in production — delete
when no longer needed.

---

## P0 — fix first

### AU-01 · Rotate the Neon database password — **owner action**
- **Evidence:** the `DATABASE_URL` / `DIRECT_URL` values in `apps/web/.env:14-15` were echoed into
  session transcripts on 2026-10-23 and 2026-10-26 (shell-sourcing `.env`). Rotation was already open
  (`docs/MEMORY.md` — Neon password / old Resend key).
- **Fix:** rotate in the Neon console; update Vercel `DATABASE_URL` + `DIRECT_URL` on `saju-engine`
  and the local `.env`; redeploy. Do not `source apps/web/.env` again (see AU-36).

### AU-02 · Paid orders that failed during the outage cannot be recovered from the UI
- **Evidence:** `src/lib/fulfilment.ts:258-276` — after `maxAttempts` (default 3,
  `prisma/schema.prisma:153`) the job is `failJob`'d; no Report row exists, so admin regenerate
  (`src/app/api/admin/reports/[id]/regenerate/route.ts:24-29`) has nothing to act on, and `mark-paid`
  returns early for PAID orders. Recovery today = manual SQL.
- **Fix:** (a) one-off: list PAID orders created 2026-10-17 → 2026-10-24 whose Job has
  `lastError` like `ENGINE_FAILED%` (or state FAILED/QUEUED) and no Report; requeue (reset `attempts`,
  `state='QUEUED'`). (b) admin "Retry job" action + an admin list of PAID orders with no live job and
  no report.
- **Note:** the read-only query for (a) was proposed on 2026-10-26 and **declined pending the next
  session** — ask before running it against production.

### AU-03 · Nothing alerts when the engine refuses every render
- **Evidence:** engine `/health` (`api/index.py:723-741`) checks only token + imports, never
  `_allowed_upload_hosts()`; `engineHealth` (`src/lib/engine.ts:153-166`) trusts it; no uptime
  monitor (`docs/webapp/14-security.md:124`, `13-launch-audit.md:155`); SLA sweep returns
  `stuckJobs` in JSON only (`src/lib/sla.ts:133-135`) and the workflow's `curl -f`
  (`.github/workflows/sla-sweep.yml:35-38`) only fails on HTTP errors; FAILED jobs are never counted.
  The smoke tool presigns **path-style** (`tools/smoke_compat_reading.py:45-48`) while the webapp
  presigns **virtual-hosted** (`src/lib/r2.ts:45-52`, no `forcePathStyle`) — it would have passed.
- **Fix:** `/health` reports `uploadAllowlist` count and returns 503 when empty; `engineHealth` reads
  it; owner email on every GENERATE `failJob` (reuse `src/lib/owner-alert.ts`); sweep returns non-2xx
  when stuck/recently-failed jobs > 0; smoke tool signs exactly like the webapp and runs on a schedule
  (GitHub Actions); add an external uptime monitor on `/api/health`.

### AU-04 · Account erasure fails for anyone who has ordered — after their files are deleted
- **Evidence:** `src/lib/cleanup.ts:177-183` deletes R2 objects first, then in a transaction
  `tx.profile.deleteMany` — but `Order_profileAId_fkey` is `ON DELETE RESTRICT`
  (`prisma/migrations/20261015120000_init/migration.sql:313`). P2003 rolls back; files are already
  gone; the request stays `pending`; `runCleanup` throws daily on the same 10 requests, blocking all
  later deletions and the steps after it.
- **Fix:** scrub birth fields on profiles referenced by orders (keep the row) and delete the rest;
  delete R2 objects **after** commit (or queue them); per-request try/catch. **Decision needed (D2).**

### AU-05 · A payment webhook that fails mid-processing is never retried
- **Evidence:** `src/app/api/webhooks/dodo/route.ts:88-91` inserts the event row first; if processing
  throws, Dodo's retry hits P2002 and gets `200 {duplicate:true}`. `retryUnprocessedWebhooks`
  (`src/lib/cleanup.ts:138-150`) only counts, never replays.
- **Failure:** a transient DB error → order never marked paid → the customer paid and gets nothing.
- **Fix:** on P2002 short-circuit only when `processedAt` is set, otherwise re-process; make the cron
  replay stored unprocessed payloads idempotently.

### AU-06 · Open redirect via backslash in `safeNext`
- **Evidence:** `src/app/auth/complete/page.tsx:13-18` and `src/app/login/page.tsx:15-20` accept
  `/\evil.com` (starts with `/`, not `//`); browsers normalise `\` to `/`.
- **Fix:** one shared `safeNext` in `src/lib/` — reject `\` and control characters, resolve with
  `new URL(raw, origin)` and require same origin; tests for `/\x`, `/%5Cx`, `//x`, `https://x`.

### AU-07 · Admin is granted by email alone; email verification is not required
- **Evidence:** `src/lib/auth/index.ts:58-77` grants ADMIN from `roleForEmail(session.email)`; nothing
  in `src` reads `emailVerified`. Live test 2026-10-26: password sign-up went straight to the dashboard
  with no verification.
- **Failure:** any `ADMIN_EMAILS` address not yet registered can be claimed by a stranger.
- **Fix:** require `emailVerified` for the ADMIN grant and in `requireAdmin`. **Decision needed (D1)**
  — confirm the owner's admin account is verified first, or the review console locks.

### AU-08 · Deleting a report leaves the HTML reading (birth data) in R2
- **Evidence:** `src/lib/fulfilment.ts:493-501` selects/deletes `pdfKey`, `mdKey`, `audioKey` — not
  `htmlKey`. For samples the HTML is the only artefact. (`cleanup.ts:119,171` does include it.)
- **Fix:** add `htmlKey`.

---

## P1 — broken behaviour

| ID | Issue | Evidence | Fix |
|---|---|---|---|
| AU-09 | Config errors come back **422** (permanent "bad birth data"); 401 token mismatch shown as "The engine rejected this chart"; errors without `code` | `api/index.py:207-212,326,703`; `src/lib/engine.ts:133-135` | Engine: `UPLOAD_*` and auth → 503; exception handler so every error is `{error, code}`. Web: permanent only for birth-data codes |
| AU-10 | Visitor copy not actionable: "The report engine failed" — no "nothing was charged", no retry, no reference | `src/lib/engine.ts:141,145,147`; `src/components/sample-flow.tsx:88` | Map codes to visitor copy client-side; "Try again" inside the alert; short request id |
| AU-11 | Sample function killed at 60 s while `callEngine` waits 120 s (504, `ENGINE_TIMEOUT` never logged); regenerate `maxDuration` 120 = engine timeout | `src/app/api/sample/route.ts:22`; `src/lib/engine.ts:105`; `regenerate/route.ts:9` | Sample passes `timeoutMs≈50_000`; regenerate `maxDuration=300` |
| AU-12 | "Check for updates" burns retry attempts — two clicks during an outage fail a paid job | `src/lib/fulfilment.ts:476-490`; `src/app/api/jobs/kick/route.ts:18-28` | Fast 5xx don't count against `maxAttempts`, or `notBefore` backoff; tell the client the check failed |
| AU-13 | Dispatcher runs **daily** (Hobby) but code/docs say per-minute; a retry can be 24 h away vs the 10 h promise; webhook dispatches the *oldest* job, not the new one | `vercel.json`; `src/app/api/cron/dispatch/route.ts:9`; `src/lib/fulfilment.ts:73`; `webhooks/dodo/route.ts:136` | Run dispatch from the 15-min GitHub Actions workflow; webhook → `processJobById(createdJobId)`; fix comments |
| AU-14 | SLA sweep can wedge on 10 un-releasable `DRAFT_READY` rows; `IN_REVIEW` has no deadline; clock starts at `createdAt`, not payment; failed renders have no deadline | `src/lib/sla.ts:76-108` | Filter `order.status=PAID` in the query; deadline for stale `IN_REVIEW`; clock from paid time |
| AU-15 | Login: three `result.error.message` paths bypass the enumeration masking from `5701ce9`; `?error=` from magic-link / Google callbacks is ignored | `src/app/login/page.tsx:103,133,163,47` | Route all through `authErrorMessage`; read and show `error` |
| AU-16 | Clearing or mistyping date/time keeps and submits the previous value | `src/components/date-of-birth-field.tsx:66-70`; `src/components/time-of-birth-field.tsx:49-53` | `onChange("")` on empty/failed parse; block submit while a parse error shows |
| AU-17 | Display-name change silently reverted — `mirrorUser` overwrites `User.name` from the Neon session each request | `src/app/api/account/route.ts:34`; `src/lib/auth/index.ts:64-69` | Update via `authClient.updateUser`, or mirror name only on create |
| AU-18 | DB outage looks like "signed out" — bare `catch {}` around `mirrorUser` | `src/lib/auth/index.ts:106` | Re-throw Prisma errors → 503 |
| AU-19 | Account panels have no `catch`; the consent checkbox stays toggled after a failed save | `src/components/dashboard/account-actions.tsx:66-90,143-174` | catch → revert + error |
| AU-20 | "Through 31 December" offer ends 16:00 PST / 05:30 IST (UTC date compare) | `src/lib/promo.ts:47` | **Decision needed (D3)** |
| AU-21 | Bad `?status=` on the reports list → unhandled Prisma error → 500 | `src/app/api/reports/route.ts:16` | `z.enum` |

---

## P2 — privacy, consent, correctness

| ID | Issue | Evidence | Fix |
|---|---|---|---|
| AU-22 | Free sample creates a Profile for signed-in users without a consent check; Google and magic-link sign-ups never record consent | `src/app/api/sample/route.ts:178-196`; `src/app/login/page.tsx` (Google / magic paths) | Check `hasActiveServiceConsent`; record consent at `/auth/complete` for new users |
| AU-23 | Re-consent records the old policy version; versions never compared | `src/app/dashboard/account/page.tsx:84`; `src/lib/consent.ts:26-36` | Always `POLICY_VERSION`; require it in `hasActiveServiceConsent` |
| AU-24 | Consent withdrawal and pending deletion promise behaviour nothing enforces ("stops processing", "sign-in is disabled") | `account-actions.tsx:104,180-181`; `src/app/api/account/deletion/route.ts:43-55` | Enforce (revoke sessions, block writes) or correct the copy |
| AU-25 | Erasure leaves the Neon Auth identity — user can sign in to a dead account and cannot re-register | `src/lib/cleanup.ts:186-193` | Delete the Neon user + sessions via the server API |
| AU-26 | Unreviewed narration script and the whole report row returned before delivery | `src/app/api/reports/[id]/audio/route.ts:67-76`; `src/app/api/reports/[id]/route.ts:14-16` | Gate on `DELIVERED`; explicit field allow-list |
| AU-27 | Soft-deleted profiles keep birth data forever; `flagInactiveProfiles` is a no-op (`updateMany({data:{}})`) | `src/app/api/profiles/[id]/route.ts:127-130`; `src/lib/cleanup.ts:225-230` | Scrub birth fields on delete or purge after N days |
| AU-28 | Failed jobs record `ENGINE_FAILED`, not the engine's code — admin "Recent failures" would never have shown `UPLOAD_HOSTS_UNCONFIGURED` | `src/lib/fulfilment.ts:259-275`; `src/lib/engine.ts:140-141` | `ENGINE_FAILED:<engine code>` on the `ApiError` |
| AU-29 | Sample renders and must upload a PDF nobody keeps; PDF upload failure fails the sample; HTML failure surfaces as `UPLOAD_NOT_VERIFIED` | `src/app/api/sample/route.ts:142-165`; `api/index.py:840-852` | Make `uploadUrl` optional in the contract (or `artifacts:["html"]`); check `htmlBytes` before `headObject` |
| AU-30 | Rate-limit gaps: profile PATCH (engine call), account PATCH, report download/html/audio | routes under `src/app/api/` | Add `rateLimit` |
| AU-31 | Public `/api/health` over-shares (`engineDetail`, `missingProducts`, payment mode) and calls the engine per hit | `src/app/api/health/route.ts:236-256` | Minimal public body; detail behind auth/token; cache |
| AU-32 | Consent `purposes` JSON unbounded | `src/lib/validation/schemas.ts:92` | Strict object |
| AU-33 | Visitor IP logged in the sample route | `src/app/api/sample/route.ts:61` | Drop or hash |
| AU-34 | Profile edit re-resolves the bare stored city with `countryCode:null` — ambiguous names ("Cambridge") fail | `src/app/api/profiles/[id]/route.ts:58-61` | Store and pass `countryCode` |
| AU-35 | The auth API itself reveals account existence (`422 USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL`) | Neon Auth server | Neon-side setting (e.g. require verification); UI already masked |
| AU-36 | `apps/web/.env` is not shell-sourceable: unquoted `EMAIL_FROM` (line 35); `&` in the DB URLs backgrounds the assignment | `apps/web/.env:14-15,35` | Quote values; prefer `node --env-file` |
| AU-37 | `presignPutUrl(contentType)` is decorative: the presigner never signs `content-type`, so any type is accepted (R2 stores the engine's `text/html; charset=utf-8`) | `src/lib/r2.ts:114-121`; `@aws-sdk/s3-request-presigner` | Match the engine's value so nobody is misled |

---

## Improvements

| ID | Improvement | Evidence / note |
|---|---|---|
| AU-40 | "Sign out of other devices" + session list on the Account page | No caller of `revokeOtherSessions`; multiple sessions confirmed live |
| AU-41 | Password reset flow | Nothing calls `requestPasswordReset` |
| AU-42 | Self-serve data export | Account page offers email only |
| AU-43 | Sign-out failure is hidden (redirects with a valid cookie) | `src/components/dashboard/shell.tsx:71-73` |
| AU-44 | Sample funnel: engine 5xx not counted against the 5/min limit; friendlier Zod messages (`src/lib/api.ts:62-66`); nearest-city escape hatch on `CITY_NOT_RESOLVED`; warn when the 2.6 MB city index fails to load (`src/lib/cities.ts:351`); highlight the echo for ambiguous day/month (`src/lib/birth-date.ts:114-117`); accept "2:30 p.m." (`src/lib/birth-time.ts:32`) | |
| AU-45 | Vercel Web Analytics: enable on `saju-engine` or remove `<Analytics/>` (`src/app/layout.tsx:60`) — console 404 on every page | |
| AU-46 | Purge `SampleLead` emails and stored webhook payloads on a schedule | |
| AU-47 | Still-open launch items (tracker): Turnstile in log mode; Dodo in test mode (no live guard, `src/lib/dodo.ts:24`); DKIM/DMARC; unsubscribe route; free sample skips the "Check your chart" step (`sample-flow.tsx:15,94`); no Playwright E2E | `docs/MEMORY.md` |

## Test gaps (close alongside the fixes)

- Dashboard layout rendered for a non-admin → no admin nav (would have caught `310fd3d`).
- Login page: error display, enumeration masking, `?error=` param.
- A fixture of URLs produced by the webapp's real `presignPutUrl` (virtual-hosted), checked by the
  Python `_validate_upload_url` tests — today only hand-written URLs (`tests/test_report_engine_service.py`).
- `engine.ts` status/code → visitor error mapping; `sample-flow` error paths; `safeNext` backslash
  cases; cleanup erasure for a user with an order; webhook replay after a mid-processing failure.

## Docs and tracker drift

- `docs/webapp/08-deployment.md:191-198`, `07-services-and-integrations.md:583-587`,
  `05-report-pipeline.md:299`, `14-security.md:73`: list `SAJU_UPLOAD_HOSTS` as required for the
  engine project, document the virtual-hosted form and the new host-label rule.
- `docs/webapp/09-operations.md:104,129,354-361`: per-minute dispatcher and "the engine probe catches
  it" are wrong.
- `docs/issues_bugs.md:826` (S4/A1) and `:855` (D3) are done → close.
- `docs/MEMORY.md:15,32` (current state, "Open: D3 deploy, A1"), `:176` (Vercel token expired — later
  contradicted), `:2213` (test count) are stale.
- `CLAUDE.md`: add the engine env requirement (`R2_ENDPOINT` and/or `SAJU_UPLOAD_HOSTS`).

---

## Decisions needed before execution

| ID | Question | Recommendation |
|---|---|---|
| D1 (AU-07) | Require a verified email for ADMIN? | Yes — after confirming the owner's admin account shows `emailVerified=true` in Neon |
| D2 (AU-04) | Erasure for users with orders | Keep order rows (accounting), scrub profile birth fields and anonymise the user; delete R2 after commit |
| D3 (AU-20) | Promo end | Honour the copy everywhere: end at `2027-01-01T08:00Z` (end of 31 Dec in US Pacific) |
| D4 (AU-13) | Dispatch frequency on Hobby | Call `/api/cron/dispatch` from the existing 15-min GitHub Actions workflow |
| D5 (AU-02) | Run the read-only production query for outage-affected orders, then requeue | Yes, owner approves at the start of the session |
| D6 (IMP) | Which improvements to build (AU-40 – AU-47) | AU-40 and AU-41 first |

## Execution handoff

Run per the owner's standing preference (`memory/feedback_audit_workflow.md`): subagent-driven,
TDD, implementer + reviewer per task, merge to `develop` locally; push only when the owner says.

1. **Start:** ask D1–D6 in one batched question. Owner does AU-01 (Neon rotation).
2. **Wave 1 — P0** (AU-02 … AU-08). Independent file groups, so tasks can run in parallel:
   - *Auth:* AU-06, AU-07 (`src/lib/auth/*`, `login/page.tsx`, `auth/complete/page.tsx`).
   - *Pipeline & alerting:* AU-02, AU-03, AU-08 (`api/index.py` health, `src/lib/engine.ts`,
     `src/lib/fulfilment.ts`, `src/lib/sla.ts`, admin retry route, workflows, smoke tool).
   - *Money & data:* AU-04, AU-05 (`src/lib/cleanup.ts`, `webhooks/dodo/route.ts`).
3. **Wave 2 — P1** (AU-09 … AU-21) with the matching tests.
4. **Wave 3 — P2**, chosen improvements, docs/tracker drift.
5. After each wave: update the status column in `docs/issues_bugs.md` → "Audit 2026-10-26".

### Verification
- Engine: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest -q`.
- Web (`apps/web`): `npx tsc --noEmit -p .`, `npx eslint <changed files>`, `npx vitest run`.
- After deploy: GitHub check-runs and the two Vercel statuses on the pushed commit; live checks with
  `agent-browser` (login copy, non-admin nav, `/login?next=/%5Cevil.com` stays on-site); live
  `/generate` smoke with a virtual-hosted presign (`node --env-file=.env`, never `source`); engine
  `/health` shows the allowlist; a forced engine failure on a preview deployment sends the owner alert.
- Erasure: run cleanup on a Neon **branch** against a test user with an order — rows scrubbed, R2
  objects gone, cron completes.
