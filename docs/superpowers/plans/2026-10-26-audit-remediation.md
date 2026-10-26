# Plan — 2026-10-26 Production Audit Remediation

> Source of findings: `docs/analysis/2026-10-26-production-audit.md` (AU-01 … AU-47).
> Tracker: `docs/issues_bugs.md` → "Audit 2026-10-26".
> Decisions D1–D6 were answered by the owner on 2026-10-26 and are binding (see below).

## Global Constraints (binding for every task)

1. **Branch:** work on `audit/2026-10-26-remediation` off `develop`. Commit locally; **never push**
   until the owner says so. Merge to `develop` locally only after the final review.
2. **Production data:** only the controller runs production queries, and only the read-only
   queries approved under D1/D5. No subagent connects to the production database.
3. **Secrets:** never `source apps/web/.env` and never print a secret value. Read env with
   `node --env-file=.env` (see AU-36) or `process.env`. When editing `.env`, do not echo lines.
4. **Scope:** do not touch `candidates_horoscope/`. Do not change report prose, doctrine
   (용신/격국/strength), pricing, or delivered PDFs. UI copy changes are allowed only where the
   audit item explicitly requires them.
5. **TDD:** write the failing test first, then the fix. Every task carries its own tests.
6. **Verify before reporting:**
   - Web, from `apps/web`: `npx tsc --noEmit && npx eslint <changed files> && npx vitest run`
   - Engine, from repo root: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest -q`
7. **No new runtime dependency** unless the task says so. Reuse `ApiError`, `rateLimit`,
   `src/lib/api.ts`, `owner-alert.ts`, and the existing component library.
8. **Error shape:** any new API error is `{ error: string, code: string }`; codes are stable
   identifiers, messages are visitor-safe.
9. **Comments:** follow the existing house style — explain *why*, cite the audit item, and keep
   `file:line` evidence only in the audit doc, not in code comments.
10. **Uncertainty:** if a requirement cannot be met from the code/spec, report `BLOCKED` with the
    evidence instead of inventing behaviour.

## Decisions (binding)

| ID | Decision |
|---|---|
| D1 | ADMIN requires `emailVerified`. Before deploy, the controller confirms the owner's admin session shows `emailVerified=true`; the implementation must not store verification in Prisma. |
| D2 | Erasure keeps Order rows for accounting; scrub birth fields on profiles referenced by orders, anonymise the User, delete unreferenced profiles, and delete R2 objects **after** the transaction commits. Per-request try/catch. |
| D3 | The 20% offer ends at **2027-01-01T08:00:00Z** (end of 31 Dec, US Pacific) everywhere it is evaluated. |
| D4 | Dispatch runs from the existing **15-minute GitHub Actions workflow**, calling `/api/cron/dispatch`. Do not upgrade the Vercel plan. |
| D5 | Read-only production query for outage-affected paid orders runs first; requeue only after the owner confirms the rows. |
| D6 | Improvements in this pass: **AU-40 and AU-41** only. |

---

## Task 1: Auth hardening — shared `safeNext` and verified-email admin

**Audit:** AU-06 (P0), AU-07 (P0).

**Files:** new `src/lib/safe-next.ts`; `src/app/login/page.tsx`; `src/app/auth/complete/page.tsx`;
`src/lib/auth/index.ts`; `src/lib/auth/__tests__/` (new or existing).

**Requirements**

1. Create one `safeNext(raw: string | null | undefined, fallback = "/dashboard"): string` in
   `src/lib/safe-next.ts`, importable from both client pages (pure, no imports beyond stdlib).
2. Return the fallback unless the input is a same-origin path. Reject at minimum: empty,
   not starting with `/`, starting with `//`, containing `\` (any position), containing control
   characters (`\u0000`–`\u001f`, `\u007f`), and anything that does not resolve to the same origin
   when parsed with `new URL(raw, "https://example.invalid")`. `%5C` (encoded backslash) must also
   be rejected — decode once before the backslash test.
3. Allowed: `/dashboard`, `/dashboard?x=1`, `/reports/abc#top`. Rejected: `/\evil.com`,
   `/%5Cevil.com`, `//evil.com`, `/\\evil.com`, `https://evil.com`, `javascript:alert(1)`, ``,
   `dashboard`.
4. Replace the local `safeNext` in `login/page.tsx` and `auth/complete/page.tsx` with the import.
5. Extend the session read path in `src/lib/auth/index.ts`: the Neon session user includes
   `emailVerified: boolean`. Add it to `NeonUser`, carry it through `normalise`/`mirrorUser`, and
   expose it on `AppUser` as a transient field (`emailVerified: boolean`, default `false` when the
   payload omits it). No Prisma migration — verification is read from the session each request.
6. Gate **both** halves of admin on verification:
   - `mirrorUser`: grant `role = ADMIN` only when `isAdminEmail(email) && emailVerified`. If an
     `ADMIN_EMAILS` address signs in unverified, grant `USER` and log one warning
     (`console.warn`) containing the email address and the words "unverified admin address".
   - `requireAdmin`: reject (`ApiError.forbidden()`) unless `role === "ADMIN"`,
     `isAdminEmail(email)`, and `user.emailVerified`.
7. Keep the existing "never demotes except verification" behaviour: an ADMIN whose session is
   unverified is denied by `requireAdmin`; do not downgrade the stored role.

**Tests**

- `safe-next` table test covering every allowed/rejected value in requirement 3, plus `%2F%2Fevil.com`
  and a control-character case.
- `auth/index.ts` unit test: unverified `ADMIN_EMAILS` user is mirrored as `USER`; verified is
  `ADMIN`; `requireAdmin` throws for a user with the email but `emailVerified=false`.
- A page-level test (or pure-function test) proving both pages import the shared helper.

**Acceptance:** `grep -rn "function safeNext" src` returns only `src/lib/safe-next.ts`.

---

## Task 2: Engine health allowlist, outage alerting, and a truthful smoke

**Audit:** AU-03 (P0).

**Files:** `api/index.py`; `src/lib/engine.ts`; `src/lib/fulfilment.ts`; `src/lib/sla.ts`;
`src/lib/owner-alert.ts` (reuse); `.github/workflows/sla-sweep.yml`;
`tools/smoke_compat_reading.py`; Python and web tests.

**Requirements**

1. `/health` in `api/index.py` must call `_allowed_upload_hosts()` (or its equivalent) and include
   `uploadAllowlist: <count>` in the JSON body. When the count is zero it must return **503** with
   `{ ok: false, code: "UPLOAD_HOSTS_UNCONFIGURED", ... }`. It must remain cheap — no network calls.
2. `src/lib/engine.ts::engineHealth` must treat a non-200 `/health` as unhealthy and surface the
   allowlist state in the returned detail.
3. On **every** GENERATE `failJob`, send the owner alert (reuse `src/lib/owner-alert.ts`, extending
   it with a generic `notifyOwnerEngineFailure({ orderId, code, attempts })` if the existing helper
   is review-specific). Alert send must never throw into the job path.
4. `src/lib/sla.ts` must count FAILED jobs in the returned summary, and the sweep endpoint must
   return a non-2xx status when `stuckJobs > 0` or `recentFailures > 0` (keep the JSON body).
5. `.github/workflows/sla-sweep.yml`: `curl -f` already fails on HTTP errors — add a step that also
   fails when the JSON `stuckJobs`/`recentFailures` are non-zero, so the workflow cannot silently pass.
6. `tools/smoke_compat_reading.py` must presign exactly like the webapp: virtual-hosted
   (`https://{bucket}.{endpoint-host}/{key}`), no `forcePathStyle`. Add a scheduled run of the smoke
   tool to the existing GitHub Actions workflow (or a new workflow on a 15-minute/30-minute schedule).
7. Document the required engine env (`SAJU_UPLOAD_HOSTS` and/or `R2_ENDPOINT` + `SAJU_UPLOAD_BUCKET`)
   in the smoke tool's docstring.

**Tests**

- Python: `/health` with an empty allowlist returns 503 and `code=UPLOAD_HOSTS_UNCONFIGURED`; with
  one host returns 200 and `uploadAllowlist=1`; no R2/network calls made.
- Python: a presigned virtual-hosted URL produced by the new smoke helper passes
  `_validate_upload_url`; a path-style URL is rejected.
- Web (vitest): `engineHealth` maps a 503 body to unhealthy; `failJob` triggers exactly one owner
  alert including the engine code; alert failure does not change the job outcome.
- Web: SLA sweep returns 503 when `stuckJobs > 0`; 200 when both counts are zero.

**Acceptance:** a forced empty allowlist is observable from `GET /api/health` (detail field) and
from the sweep's non-2xx.

---

## Task 3: Report deletion completeness and admin job recovery

**Audit:** AU-08 (P0), AU-02 (P0, UI half — the data half is D5/controller).

**Files:** `src/lib/fulfilment.ts`; new `src/app/api/admin/jobs/retry/route.ts` (or extend an
existing admin route); `src/app/api/admin/orders/` (list); the review-queue admin UI;
`src/app/api/admin/reports/[id]/regenerate/route.ts`; tests.

**Requirements**

1. `deleteReportArtifacts` must select and delete `htmlKey` in addition to `pdfKey`, `mdKey`,
   `audioKey`. Add a test asserting the queued keys include the HTML key (this is the exact gap —
   for a sample the HTML is the only artefact).
2. Add an admin action "Retry job" that, for a PAID order, finds its Job, resets `attempts = 0`,
   sets `state = 'QUEUED'` and `lastError = null`, and returns the job id. It must refuse (409) when
   a live job (`QUEUED`/`RUNNING`) already exists, and 404 when the order has no job.
3. Add an admin list endpoint returning PAID orders that have **no Report** and **no live/queued
   job** — the set the outage left unrecoverable. Include order id, kind/tier, paid time, last
   error, and profile label. Read-only.
4. Surface both in the review-queue admin UI: a "Failed orders" table with a Retry button per row,
   and a success/failure message on retry. Keep it behind `requireAdmin`.
5. Add `htmlKey` to the regenerate path's cleanup if it deletes prior artefacts.

**Tests**

- Unit: `deleteReportArtifacts` queues all four keys including `htmlKey`.
- Route: retry refuses a live job (409), requeues a failed job, and 404s an order without a job.
- Route: the failed-orders list excludes orders that have a report or a live job, and requires ADMIN.

**Acceptance:** an order that failed 3× during the outage appears in the admin list and can be
retried from the UI without manual SQL.

---

## Task 4: Erasure correctness and webhook replay

**Audit:** AU-04 (P0), AU-05 (P0).

**Files:** `src/lib/cleanup.ts`; `src/app/api/webhooks/dodo/route.ts` (and the shared handler it
calls); tests.

**Requirements**

1. Rework `processDueDeletions` per D2:
   - Load the user's reports and queue their keys, but **do not delete R2 objects before the
     transaction commits**. Either delete after a successful commit, or enqueue them through the
     existing `deleteObjectOrQueue` mechanism.
   - Inside one `$transaction`: delete Report/Delivery rows; for profiles referenced by any Order
     (`ordersAsA`/`ordersAsB`), **scrub birth data** (`fullName` → "Deleted profile",
     `birthDate`/`birthTime`/`city`/`country`/`latitude`/`longitude`/`timezone`/`utcOffset` →
     null/placeholder, `chartJson`/`chartComputedAt` → null, `deletedAt = now`); delete profiles that
     no order references. Anonymise the User as today.
   - Wrap each deletion request in its own try/catch: log the failure, leave that request `pending`
     (or mark it `failed` only if a status exists), and continue with the others. One bad request
     must not block later requests or the cron's later steps.
2. Webhook replay (AU-05): in `webhooks/dodo/route.ts`, a `P2002` on the event insert means the
   event already exists. Short-circuit with `{ duplicate: true }` **only when `processedAt` is set**;
   otherwise re-process the stored/current payload idempotently.
3. Implement real replay in `retryUnprocessedWebhooks`: extract the provider processing into a
   function that takes the stored payload, and have the cron call it for each unprocessed event
   (bounded, e.g. 20 per run), setting `processedAt` on success. Skip events whose provider has no
   replayer.
4. Keep the erasure semantics documented in the function's docstring (orders retained, consent
   retained, birth data destroyed).

**Tests**

- Erasure with an order: the user, order, and referenced profile survive; the profile's birth fields
  are scrubbed; R2 objects are deleted only after commit; the deletion request is `completed`.
- Erasure with no order: profile is deleted as before.
- One failing request does not prevent a later request from completing.
- Webhook: second delivery of an unprocessed event re-processes and marks `processedAt`; a
  `processedAt`-set duplicate returns 200 `{ duplicate: true }` and does not re-run side effects.

**Acceptance:** running cleanup on a fixture user with an order completes without P2003 and removes
report artefacts.

---

## Task 5: Engine error contract, visitor copy, and timeouts

**Audit:** AU-09 (P1), AU-10 (P1), AU-11 (P1), AU-28 (P2).

**Files:** `api/index.py`; `src/lib/engine.ts`; `src/components/sample-flow.tsx`;
`src/app/api/sample/route.ts`; `src/app/api/admin/reports/[id]/regenerate/route.ts`;
`src/lib/fulfilment.ts`; tests.

**Requirements**

1. Engine status mapping: configuration errors (`UPLOAD_*`, missing token) must return **503**, not
   422; auth mismatch returns 503; only birth-data validation keeps 422. Add a top-level exception
   handler so every error body is `{ error, code }` (no bare strings, no missing `code`).
2. `src/lib/engine.ts`: permanent only for birth-data validation codes (define an explicit set).
   All other failures are retryable. Include the engine status and code on the thrown `ApiError`
   (`details`/`code`) so callers can map them.
3. Visitor copy: map codes client-side (`sample-flow.tsx`) to actionable sentences. The default
   failure must say nothing was charged where true, offer "Try again" inside the alert, and show a
   short request id. Never show "The report engine failed" alone.
4. Timeouts: the sample route passes `timeoutMs ≈ 50_000` to `callEngine` (so it finishes before the
   60 s function limit); log the `ENGINE_TIMEOUT` path. Set regenerate `maxDuration = 300`.
5. `fulfilment.ts`: record `ENGINE_FAILED:<engine code>` in `lastError` when the engine throws with a
   code, so the admin "Recent failures" view shows the real cause.

**Tests**

- Python: config/auth failure → 503 with code; birth-data failure → 422 with code; unexpected
  exception → `{error, code}` (500).
- Web: code→copy mapping for `UPLOAD_HOSTS_UNCONFIGURED`, `ENGINE_TIMEOUT`, `UPLOAD_NOT_VERIFIED`,
  unknown; a permanent set that excludes the config codes.
- Web: sample route passes a timeout below the function limit; failed job `lastError` contains the
  engine code.

**Acceptance:** no visitor-facing path can produce a bare "The report engine failed".

---

## Task 6: Retry accounting, dispatch cadence, and SLA deadlines

**Audit:** AU-12 (P1), AU-13 (P1), AU-14 (P1).

**Files:** `src/lib/fulfilment.ts`; `src/app/api/jobs/kick/route.ts`;
`src/app/api/cron/dispatch/route.ts`; `src/app/api/webhooks/dodo/route.ts`; `src/lib/sla.ts`;
`vercel.json`; `.github/workflows/sla-sweep.yml`; tests.

**Requirements**

1. "Check for updates" must not burn paid attempts. A fast 5xx or `notBefore` backoff must not
   increment `attempts`; when a check fails, tell the client it failed (no silent success).
2. Dispatch per D4: add a step to the existing 15-minute GitHub Actions workflow that calls
   `/api/cron/dispatch` with `CRON_SECRET`; leave `vercel.json`'s daily cron as a harmless fallback
   (or remove it if it duplicates) and correct the code comments/docs that claim per-minute.
3. The Dodo webhook must dispatch the **new** job (`processJobById(createdJobId)`), not the oldest
   pending job.
4. `src/lib/sla.ts`: the sweep query must filter `order.status = PAID` (so un-releasable
   `DRAFT_READY` rows cannot wedge it); add a deadline for stale `IN_REVIEW`; start the clock from
   the paid timestamp, not `createdAt`; and give failed renders a deadline.
5. Update the comments in `cron/dispatch/route.ts` and `fulfilment.ts` that describe the schedule.

**Tests**

- Kick: two 5xx checks leave `attempts` unchanged; a successful check processes the job.
- Webhook: dispatches the job created by that event (assert the id passed).
- SLA: a `DRAFT_READY` report whose order is not PAID does not appear as stuck; an `IN_REVIEW` row
  past the new deadline does; the paid clock is used.
- Workflow YAML parses and contains the dispatch step with the secret.

**Acceptance:** no path can leave a paid order more than ~15 minutes from dispatch on the normal
case, and a customer's repeated "check" clicks cannot fail their job.

---

## Task 7: Login and account UX correctness

**Audit:** AU-15 (P1), AU-16 (P1), AU-17 (P1), AU-18 (P1), AU-19 (P1), AU-21 (P1).

**Files:** `src/app/login/page.tsx`; `src/components/date-of-birth-field.tsx`;
`src/components/time-of-birth-field.tsx`; `src/app/api/account/route.ts`;
`src/lib/auth/index.ts`; `src/components/dashboard/account-actions.tsx`;
`src/app/api/reports/route.ts`; tests.

**Requirements**

1. Login: route all error displays through `authErrorMessage` (the three `result.error.message`
   paths at lines ~103/133/163 bypass the enumeration masking added in `5701ce9`). Read and display
   the `?error=` query parameter set by the magic-link and Google callbacks.
2. Date/time fields: clearing or failing to parse must call `onChange("")` and must not submit the
   previous value. Block submit while a parse error is displayed.
3. Display name: `mirrorUser` must not overwrite `User.name` from the session on every request.
   Update the name through `authClient.updateUser` (or mirror the name only on create), so an
   account-page change is not silently reverted.
4. DB outage: `getCurrentUser`'s bare `catch {}` around `mirrorUser` must re-throw Prisma
   connectivity/known-request errors so the caller returns 503, instead of showing "signed out".
   Keep the safe `null` for an unconfigured auth/network/corrupt-cookie session.
5. Account panels: every save has a `catch` that reverts the optimistic state and shows an error;
   the consent checkbox must not stay toggled after a failed save.
6. `GET /api/reports?status=` must validate with `z.enum` and return 400 for an unknown value
   instead of an unhandled Prisma 500.

**Tests**

- Login page: wrong password shows the actionable message; duplicate sign-up shows the neutral
  sentence; `?error=...` is displayed; no branch prints a raw `result.error.message`.
- Date/time fields: clearing emits `""`; a partial parse emits `""` and blocks submit.
- `mirrorUser`: does not overwrite an existing name; creates with the session name.
- `getCurrentUser`: a Prisma connection error propagates (503 path); a missing session returns null.
- Account actions: failed save reverts the checkbox.
- Reports: unknown `status` → 400.

**Acceptance:** no login path leaks account existence and no name change is reverted.

---

## Task 8: Promo end time

**Audit:** AU-20 (P1) — D3.

**Files:** `src/lib/promo.ts`; any copy that states the end date; tests.

**Requirements**

1. One exported constant for the end instant: `2027-01-01T08:00:00Z`. Every offer check compares
   against it. Do not use a UTC date-string compare.
2. Make the boundary testable by injecting `now` (default `new Date()`), keeping the call sites
   unchanged.
3. Confirm the landing-page and store copy still reads "through 31 December" and is true under the
   new boundary. Do not change the wording unless it is inconsistent.

**Tests**

- Active at `2026-12-31T23:59:59Z`; active at `2027-01-01T07:59:59Z`; inactive at
  `2027-01-01T08:00:00Z`; inactive after.

**Acceptance:** the offer is active for the whole of 31 December US Pacific and nowhere later.

---

## Task 9: Consent and privacy correctness

**Audit:** AU-22 (P2), AU-23 (P2), AU-25 (P2), AU-27 (P2), AU-32 (P2), AU-33 (P2).

**Files:** `src/app/api/sample/route.ts`; `src/app/auth/complete/page.tsx` (and the Google/magic
paths); `src/lib/consent.ts`; `src/app/dashboard/account/page.tsx`; `src/lib/cleanup.ts`;
`src/app/api/profiles/[id]/route.ts`; `src/lib/validation/schemas.ts`; tests.

**Requirements**

1. The free sample must not create a Profile for a signed-in user unless
   `hasActiveServiceConsent(userId)` is true. If consent is missing, return a 409 with a code the UI
   turns into a link to the consent control; do not silently proceed.
2. Record service consent at `/auth/complete` for newly created users on **all** sign-in paths
   (email, Google, magic link), using `POLICY_VERSION`.
3. Re-consent always records the **current** `POLICY_VERSION`; `hasActiveServiceConsent` requires a
   record whose version equals `POLICY_VERSION`.
4. Erasure (AU-25): after the local anonymisation commits, delete the Neon Auth identity and its
   sessions via the server API, so the user cannot sign in to a dead account and can re-register.
   If the API call fails, record/retry it — do not fail the whole erasure.
5. Soft-deleted profiles (AU-27): scrub birth fields when a profile is deleted (same scrub as Task
   4), and replace the no-op `flagInactiveProfiles` (`updateMany({data:{}})`) with a real
   selection+update or remove it and the call site.
6. Consent `purposes` must be a strict Zod object with a bounded key set — no passthrough/unbounded
   JSON.
7. Visitor IP (AU-33): drop it or hash it with a server secret before logging; keep no raw IP.

**Tests**

- Sample route: signed-in without consent → 409 + code, no Profile created; with consent → proceeds.
- `/auth/complete`: a new user on each of the three paths gets one consent record at
  `POLICY_VERSION`.
- Re-consent records the current version; an old-version record does not satisfy
  `hasActiveServiceConsent`.
- Erasure calls the Neon identity deletion once; a failure is logged/retried without failing the
  local erasure.
- Profile delete scrubs birth fields; `flagInactiveProfiles` changes rows (or is gone).
- Schema rejects extra purposes and oversized payloads.
- No raw IP appears in logs.

**Acceptance:** a signed-in user without consent cannot create a profile through the sample path.

---

## Task 10: Pre-delivery exposure and withdrawal promises

**Audit:** AU-24 (P2), AU-26 (P2).

**Files:** `src/app/api/reports/[id]/route.ts`; `src/app/api/reports/[id]/audio/route.ts`;
`src/components/dashboard/account-actions.tsx`; `src/app/api/account/deletion/route.ts`;
`src/lib/consent.ts`; tests.

**Requirements**

1. Report detail (AU-26): gate the response on `report.status = DELIVERED` and return an explicit
   allow-list of fields. Do not return the full row or an unreviewed narration script.
2. Audio (AU-26): the audio route serves only a delivered report's reviewed script; never an
   unreviewed draft.
3. Consent withdrawal (AU-24, **D7: enforce**): on withdrawal mark consent withdrawn, revoke other
   sessions, and block new processing — creating orders and starting report generation — while the
   user has no active service consent. Return a 409 with a stable code that the UI turns into a link
   to the consent control; do not silently no-op.
4. Pending deletion (AU-24, **D7: enforce**): while a `DeletionRequest` is `pending`, sign-in is
   disabled. `getCurrentUser` returns null for such an account (treated as signed out) and the login
   page shows a specific "this account is pending deletion" message when the credentials verify.
   The owner may still see the request in the admin view.
5. Tests assert the enforced behaviour, and the UI copy is left as-is (it now matches).

**Tests**

- Report detail for a non-delivered report returns 409/404 with a code and no script fields.
- Report detail for a delivered report returns only the allow-listed fields.
- Audio for a non-delivered report is refused.
- Withdrawal blocks new report creation (or the corrected copy is asserted).
- Pending deletion blocks sign-in (or the corrected copy is asserted).

**Acceptance:** no unreviewed report content or narration script leaves the server before delivery.

---

## Task 11: API and infrastructure hardening

**Audit:** AU-29 (P2), AU-30 (P2), AU-31 (P2), AU-34 (P2), AU-35 (P2, Neon-side),
AU-36 (P2), AU-37 (P2).

**Files:** `src/app/api/sample/route.ts`; `api/index.py` (upload contract); `src/lib/r2.ts`;
the routes listed under AU-30; `src/app/api/health/route.ts`;
`src/app/api/profiles/[id]/route.ts`; `apps/web/.env` (quoting only); docs for AU-35.

**Requirements**

1. Sample uploads (AU-29): make `uploadUrl` optional in the engine contract (or pass
   `artifacts: ["html"]`). A sample must not fail because a PDF it never keeps could not upload.
   Check `htmlBytes` before calling `headObject`, and surface a real HTML upload failure — not
   `UPLOAD_NOT_VERIFIED`.
2. Rate limits (AU-30): add `rateLimit` to profile PATCH (it calls the engine), account PATCH, and
   report download/html/audio. Reuse the existing helper and limits style; document the chosen limits
   in the task report.
3. `/api/health` (AU-31): the public body must be minimal (ok/version/time). Move `engineDetail`,
   `missingProducts`, and payment mode behind an authorized detail view (token or admin session) and
   cache the engine probe so a hit does not call the engine every time.
4. Profile edit (AU-34): store `countryCode` at creation and pass it when re-resolving the city, so
   "Cambridge" is unambiguous.
5. AU-35 is a Neon-side setting (require verification). Do not change code; record the exact console
   step for the owner in the task report.
6. `.env` quoting (AU-36): quote values containing `&`/spaces (`DATABASE_URL`, `DIRECT_URL`,
   `EMAIL_FROM`) without printing them. Never `source` it afterwards.
7. `presignPutUrl` (AU-37): sign the `content-type` the engine actually sends
   (`text/html; charset=utf-8` for HTML, `application/pdf` for PDF) or remove the decorative
   parameter; add a test that a mismatched type is rejected by the presigned request contract.

**Tests**

- Engine: a sample request without `uploadUrl` succeeds and returns `htmlBytes`; a failing HTML
  upload returns an HTML-specific code.
- Web: rate-limited routes return 429 after the limit; health public body has no engine detail and
  the cached probe is used on repeat hits.
- Profile edit: a `countryCode` is passed to the geocoder.
- Presign: the signed headers include the matching content-type.

**Acceptance:** `/api/health` leaks no operational detail publicly and the sample cannot fail on an
artefact it discards.

---

## Task 12: Account security — sessions and password reset (D6)

**Audit:** AU-40 (IMP), AU-41 (IMP).

**Files:** `src/app/dashboard/account/` (page + components); `src/app/api/account/` routes;
`src/lib/auth/`; new reset route/page under `src/app/auth/` or `src/app/reset/`; tests.

**Requirements**

1. Account page: list the user's active sessions (device/user-agent, last used, current marker) and
   add "Sign out of other devices" calling `revokeOtherSessions`. Confirm the current session
   survives.
2. Password reset: a "Forgot password?" link on the login page → request reset
   (`requestPasswordReset`) → a reset page that accepts the token and sets the new password. Use the
   same neutral wording as the login page (never reveal whether an email exists).
3. Both flows are rate-limited and log failures without leaking account existence.
4. If the installed `@neondatabase/auth` version does not expose a needed method, report `BLOCKED`
   with the exact missing API rather than inventing one.

**Tests**

- Account page renders the session list and the revoke button; the revoke call is made with the
  expected arguments; failure shows an error.
- Forgot-password request always shows the same neutral confirmation; the reset page rejects an
  invalid/expired token and accepts a valid one.
- Rate limiting applies to both.

**Acceptance:** a user can revoke other devices and reset a password without contacting support.

---

## Task 13: Docs and tracker drift

**Audit:** the "Docs and tracker drift" section.

**Files:** `docs/webapp/05-report-pipeline.md`, `07-services-and-integrations.md`,
`08-deployment.md`, `09-operations.md`, `14-security.md`; `docs/issues_bugs.md`;
`docs/MEMORY.md`; `CLAUDE.md`.

**Requirements**

1. `08-deployment.md:191-198`, `07-services-and-integrations.md:583-587`,
   `05-report-pipeline.md:299`, `14-security.md:73`: list `SAJU_UPLOAD_HOSTS` as required on the
   engine project, document the virtual-hosted presign form and the bucket-as-host-label rule.
2. `09-operations.md:104,129,354-361`: replace the per-minute dispatcher claim and the "the engine
   probe catches it" claim with the actual 15-minute workflow and the new allowlist health check.
3. `docs/issues_bugs.md:826` (S4/A1) and `:855` (D3) are done → mark DONE.
4. `docs/MEMORY.md:15,32` (current state / "Open: D3 deploy, A1"), `:176` (expired Vercel token
   claim), `:2213` (test count) → correct or remove.
5. `CLAUDE.md`: add the engine env requirement (`R2_ENDPOINT` and/or `SAJU_UPLOAD_HOSTS`) and note
   the verified-admin rule.
6. Set every AU status in the "Audit 2026-10-26" table to DONE / OPEN with the commit hash, in the
   same pass as the code tasks complete. Never mark an item DONE without a commit.

**Tests:** none (docs), but `git diff --check` must pass and no secret may appear in the diff.

**Acceptance:** no doc states a schedule or guard that the code contradicts.

---

## Controller-only steps (not dispatched to implementers)

1. **AU-01** — owner rotates the Neon password in the Neon console, updates Vercel
   `DATABASE_URL`/`DIRECT_URL` and the local `.env`, and redeploys. Blocked on the owner.
2. **D1 pre-deploy check** — read-only confirmation that the owner's admin session reports
   `emailVerified=true`. If it does not, do not deploy the guard; surface the verification step.
3. **D5** — read-only query for PAID orders 2026-10-17 → 2026-10-24 with a failed job and no report.
   Show the rows; requeue only after the owner confirms.
4. **AU-35** — Neon console setting (require verification) — owner action.

## Final verification

- Web: `npx tsc --noEmit && npx eslint . && npx vitest run`.
- Engine: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest -q`.
- Whole-branch review on the most capable model, with the merge-base diff package.
- Merge to `develop` locally; push only on the owner's word.
