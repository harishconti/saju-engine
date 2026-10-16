# Saju Project Memory

> **Context file:** `CLAUDE.md` (primary agent persona + ground rules)  
> **Project overview:** `README.md`  
> This file tracks persistent facts, decisions, and conventions that should be remembered across sessions when working on the saju repo.

## Project Identity

- **Name:** Saju Engine (PyPI-style package name `saju-engine`, version `0.2.0`)
- **What it is:** Korean Saju (Four Pillars of Destiny / 사주, 四柱) calculation engine, PDF toolchain, and Claude Code skill.
- **Author:** Harish Gurumoorthy
- **License:** MIT
- **Stack:** Python 3.10+, `sajupy==0.2.0` (pinned 2026-09-26 — see N-17 below; was `>=0.2.0`), `reportlab>=4.1`, optional `playwright`, optional `fastapi`/`uvicorn`.

## Current State (last updated 2026-10-16)

- **2026-10-01 audit fully worked through (2026-10-02 → 10-04), all merged to `develop`, not pushed.**
  Suite **1,794 passed / 5 skipped / 14 xfailed**; validation gate **315 checks (PASS 306,
  INTERPRETATION 9, FAIL 0)**; `ruff --select F` clean. Branches (all merged + deleted):
  `fix/audit-2026-10-01-wave-ab`, `refactor/p2-report-primitives`, `test/p3-validation-coverage`,
  `feat/p4-web-hardening`, `feat/p5-html-first`. Plans in `docs/superpowers/plans/`.
  - **Engine decisions (user, 2026-10-03):** extreme_weak verdict removed (unreachable; formula floor
    −3.78) — 종격 decided by knowledge/07 conditions, month BRANCH kept for 득령; a "likely" 종격 takes
    the dominant element as 용신 (`method="jonggyeok-follow"`, knowledge/07:73). Compat: guidance uses
    day branches only, cover warnings ranked by actual score, primary 육해/육파 on the caution list,
    different 대운 directions not "favorable", no % in compat flag labels.
  - **Operations:** self-service app needs `SAJU_INTAKE_KEY`; paid orders queue for owner review
    (`tools/intake_admin.py list/show/attach/approve/revoke/reissue/regenerate/rotate/purge`);
    `SAJU_PUBLIC_URL` for links. PDFs default to HTML/Playwright (system Chrome used with a warning if
    bundled Chromium is missing; `SAJU_ALLOW_SYSTEM_CHROME=0` = strict); `--reportlab` for legacy.
    Delivered client PDFs were NOT regenerated (`tools/regen/pdfs.sh` overwrites them — owner's call).
  - **Open:** D1 MoR checkout, D3 deploy, A1 landing-page source (not on this machine),
    reportlab removal (deferred). (`D2` email, `P4-ratelimit`, and `C1-templates` are now DONE —
    code complete and tested; D2 only needs SMTP credentials / a proxy at deploy.) P3-isolated/
    geonrok are deliberate `documented_interpretation` school divergences, not bugs.
  - **2026-10-07:** `P3-bangham` FIXED (방합국 detector in `patterns.detect_structural_notes`,
    fixture `bangham-guk-巳午未-1991`), `P3-yangin` FIXED (`stars._yangin` scans all four pillars,
    matching `knowledge/11 §I` "in chart"; no published compat score moved), `P3-golden` FIXED
    (new `tests/golden_scaffold/` snapshots of prose-scaffold + plain-words drafts), and
    `tests-geocoder` FIXED (explicit longitudes in 4 test files + pinned the date-table reference
    date in `test_premium_report`, which had drifted with the wall clock). Also `P3-reader-claim`
    FIXED (tension-branch text says "engine has weighed both" unless reader-confirmed) and `P2-F`
    FIXED (compat F over/missing wording now from the canonical element tables; score frozen) —
    both owner-approved, both client-visible. `P5-hangul-tokens` FIXED (particle consumption +
    ten-god Hanja dedup; widened random coverage). Web/infra: `P4-ratelimit` FIXED (in-app per-IP
    limiter + body cap), `D2` FIXED (optional SMTP private-link delivery), `C1-templates` FIXED
    (Jinja2 document/cover templates — byte-identical, goldens unchanged). Suite **1,839 passed
    / 13 xfailed**; validation **316 (PASS 308, INTERPRETATION 8, FAIL 0)**; ruff clean. Also
    regenerated the 5 stale compat pairs (S2/S3/P2 back-port) and added the Harish×Priyanka
    **namesake** pairs — 1996 in `harish_priyanka/` (58) and 1998 in `harish_priyanka_1998/` (52)
    — wired into `tools/regen/{compat.py,pdfs.sh}`.
  - **2026-10-11:** Added the optional **compliance-QA gate** for report prose —
    `src/saju_qa/` (stdlib-only TypeSafe/Jev `/v1/systemone` client + `compliance.scan_report()`),
    CLI `tools/qa_compliance.py` (exit 0 clean / 1 flagged / 2 unavailable; `--json`,
    `--warn-only`), tests `tests/test_saju_qa.py` (7, no network). Flags predictive,
    master-claim, sensitive-advice, and unhedged prose against the ground rules; gated behind
    `TYPESAFE_API_KEY` (model via `SAJU_CLASSIFY_MODEL`, default `jev-latest`). **Standalone by
    design — not wired into the report/web pipeline** (a manual pre-delivery gate, run alongside
    reader review). Suite **1,846 passed / 5 skipped / 13 xfailed**; documented in
    `docs/openwiki/operations/toolchain-and-testing.md` + `AGENTS.md`.
  - **2026-10-15: webapp architecture + service/integration planning documented.** Added a new
    numbered documentation set at `docs/webapp/` (14 files: overview, architecture, data model, API
    spec, auth/roles, report pipeline, frontend/UX, services & integrations, deployment, operations,
    privacy & compliance, build plan, testing, index) describing how to launch the product as a paid,
    account-based web app on Vercel. Cross-linked from `README.md`, `AGENTS.md`,
    `docs/openwiki/README.md`, and `docs/openwiki/quickstart.md`.
    **Locked decisions (owner, 2026-10-15):** two Vercel projects (`apps/web` Next.js +
    `services/report-engine` FastAPI/Python); **ReportLab** PDF backend in production (Chromium does
    not fit a Vercel function — measured here at 0.70 s markdown + 0.62 s PDF for the deep tier,
    ~130 MB dependency closure vs a 500 MB Python limit); **rebuild** the landing page inside
    `apps/web` (A1 source still not in this repo); **Lemon Squeezy** as Merchant of Record;
    **always review before delivery** for every paid tier (so the review console and the
    `--favorable-override` 용신 workflow are core, not optional); **Resend** for email;
    **Cloudflare R2** private storage, presigned URLs, **no PII column encryption** (retires the
    SQLite/Fernet `saju_web/store.py` posture); **no Redis** — rate limits, idempotency, job leases,
    and the R2 deletion queue are all Postgres tables. Vercel **Pro** is required (Hobby crons are
    once-daily, max 2). Free sample stays instant and account-free.
    **Three engine edits identified as prerequisites** (all small, all test-covered, none done yet):
    E1 `SAJU_FONT_DIR` override + bundled DejaVu (the ReportLab renderer hardcodes
    `/usr/share/fonts/truetype/dejavu`, absent in a Vercel function); E2 remove runtime Nominatim
    geocoding from the request path (coordinates resolve once at profile creation — `pillars.py`
    currently geocodes city names via geopy at request time); E3 thread `favorable_override` through
    `prepare_chart_render`/`chart_markdown` (the CLI and the compat path already support overrides;
    the single-chart web render path does not). Also: regenerate the five demo PDFs in
    `apps/landing-page/public/` with the ReportLab backend so marketing previews match delivered
    output. **Docs only — no code changed; suite unaffected (1,846 passed).**
  - **2026-10-15 (later): `apps/web` scaffolded and building.** The Next.js webapp now exists at
    `apps/web/` — 40 routes, `npm run build` clean, `tsc --noEmit` clean, `eslint` clean, **44 vitest
    cases passing**. Built: the 9-section landing page + a mobile sticky CTA; `/sample` (free funnel,
    account-free); `/login` (Google / email+password / magic link, tabbed, consent checkbox);
    `/auth/complete`; legal pages (privacy, terms, refund policy — all three required for Lemon
    Squeezy activation); the full authenticated surface (`/dashboard` overview with the derived chart,
    `/dashboard/reports` + detail, `/dashboard/profiles`, `/dashboard/orders`, `/dashboard/account`
    with consent + deletion); `/reports/new` order flow; and the `/admin` review console
    (queue + per-report 용신 override → regenerate → approve/reject, plus manual mark-paid).
    25 API routes including profiles/orders/reports/account, the engine dispatcher + cleanup crons,
    both webhooks, and the sample endpoint. Libs: `prisma`, `api` (error envelope + `handle()`),
    `auth/{server,client,index}`, `roles`, `tiers`, `ratelimit`, `audit`, `idempotency`, `r2`
    (presign + object-deletion queue), `engine`, `queue` (`FOR UPDATE SKIP LOCKED` + leases),
    `fulfilment`, `cleanup`, `checkout` (Lemon Squeezy), `email` (Resend), `birth` (city resolution +
    historical/DST-aware offsets), `cities` (~160-city bundled table), `chart`, `chart-compute`,
    `validation/schemas`.
    **Notable correctness findings while building:**
    - **`auth.middleware()` protects EVERY path it matches** (`shouldProtectRoute()` returns true for
      anything outside its small skip list). So `src/proxy.ts` matches **only** protected routes —
      matching `/` would have locked the entire public site behind a login.
    - **`Order.tier`/`Report.tier` store the ENGINE tier**, so `deep` is ambiguous between the single
      Deep Destiny tier and Deep Compatibility. Resolution must go through
      `tierFor(kind, tier)` / `variantIdForOrder(kind, tier)`; a bare id lookup silently charges the
      wrong Lemon Squeezy variant. Locked in with a regression test.
    - **Timezone handling is genuinely precise** (verified, now asserted in tests): Asia/Seoul = +8:30
      in 1910, +10 during 1950 summer DST, +8:30 in the 1954–61 era (+9:30 with DST), +10 for the
      1987–88 Seoul Olympics DST; Asia/Kolkata = +6:30 during WWII. A hardcoded +9 (or +5:30) gets
      the hour branch wrong for every pre-1961 Korean and wartime Indian birth.
    - **The `Essential` tier's engine text promises an "included MP3 audio summary"**
      (`candidates_horoscope/reports/rm/rm-sample.md`) while `README.md` says the MP3 "is produced
      separately". Not fixed — changing engine prose would move golden snapshots and needs an owner
      decision. Flagged because it is a refund/dispute risk the moment someone buys on that promise.
    - `apps/web/.env` written (gitignored) with the pooled + unpooled Neon URLs, the Neon Auth base
      URL, and freshly generated `NEON_AUTH_COOKIE_SECRET` / `ENGINE_SERVICE_TOKEN` / `CRON_SECRET`.
      **The DB password placeholders still need filling in.**
    - Initial migration generated offline at `apps/web/prisma/migrations/20261015120000_init/`
      (428 lines incl. CHECK constraints + the one-default-profile partial unique index) — **not yet
      applied to Neon.**
    **Still blocking end-to-end use:** `services/report-engine` is not written, so `/api/sample` and
    generation return a clear 503 and profiles save with `chartJson = null`. Region decision recorded:
    Neon `ap-southeast-1` (Singapore) → Vercel `sin1` on both projects.
  - **2026-10-15 (later still): Neon and R2 are live and verified.** Using the authenticated `neon`
    CLI on this machine (`neon me` → ngharish.conti), the `saju` project was found as
    **`sparkling-mouse-75978774`** (org `org-curly-sky-98590399`, `aws-ap-southeast-1`), with two
    branches: `production` (`br-soft-mouse-a1pbgnuq`, default) and **`vercel-dev`**
    (`br-odd-art-a1xbr1d1`, created by the Neon↔Vercel integration). Connection strings (pooled →
    `DATABASE_URL`, unpooled → `DIRECT_URL`) were fetched with `neon connection-string` and written
    straight into `apps/web/.env` — **no secret was printed into the transcript or committed**.
    **`20261015120000_init` applied to BOTH branches** and verified live: 14 tables, all **13**
    hand-written CHECK constraints rejecting bad rows by name (probe: negative `RateLimit.count`,
    COMPAT order with no second profile, SINGLE order with a COMPAT tier value), the partial unique
    index `profile_one_default_per_user` with the exact predicate, and all 8 enums with correct
    labels. `vercel-dev` was created *before* the migration and was empty — migrating it prevents a
    Preview deployment failing with "table does not exist".
    **Neon Auth** confirmed enabled on `production` (`better_auth`; JWKS reachable, Ed25519 key).
    **Two gaps found and one fixed:** (a) **zero trusted domains were configured** — the exact cause of
    "OAuth succeeds but the user never arrives" — now `https://cosmicsaju.com`,
    `https://www.cosmicsaju.com`, and localhost allowed; (b) the configured Google provider uses
    **Neon's shared dev-only key** (works, but shows Neon branding and is explicitly not for
    production) — needs the owner's own Google OAuth client; (c) `vercel-dev` has **no Auth
    configured**, so Vercel Preview sign-in will fail until it is enabled.
    **Cloudflare R2 wired and proven:** bucket **`saju-engine-dev`**, account
    `8b70484a615d5759f6929ef7e4f15f01`; credentials reused from `construction-log/.env` after
    verifying the existing token reaches both projects' buckets. A new **opt-in integration test**
    (`apps/web/src/lib/__tests__/r2.integration.test.ts`, `RUN_R2_TESTS=1`) proves the full round-trip
    — presigned PUT → `HeadObject` verify → presigned GET → delete — plus an unsigned-access probe
    confirming the bucket is **private**. It self-guards: refuses to run unless the bucket name looks
    like dev/test, so it can never touch production storage. Default `npm test` → **44 passed,
    4 skipped**.
    `/api/health` now reports `{"db":true,"storage":true,"engine":false}` — **the report engine
    service is the only remaining blocker.** Also fixed while verifying: a database outage used to
    surface as a generic 500 on every rate-limited route (rate limiting is the first DB touch); Prisma
    `P1xxx`/`P2024`/`PrismaClientInitializationError` now map to **503 `DATABASE_UNAVAILABLE`**.
    Docs updated: `docs/webapp/07-services-and-integrations.md` gained a provisioning log, an
    R2-endpoint-form warning, a cross-project credential-reuse table, and a Neon CLI reference.
  - **2026-10-15 (final): branch + DNS decisions from the owner.** **(a) Single branch:** the owner
    decided **only Neon `production` counts**; `vercel-dev` is migrated but deliberately unused, and
    every Vercel scope points at `production`. Docs updated in `07` §"Branches — production only" and
    `08` §"Scope discipline" (with an explicit note that the usual Preview-never-gets-prod-credentials
    rule is relaxed deliberately until a second person has DB access). **(b) The domain's DNS is on
    CLOUDFLARE, not Hostinger** — verified by lookup: NS = `randy`/`veronica`.ns.cloudflare.com, A =
    `104.21.77.175`/`172.67.210.158` (Cloudflare proxy IPs, not Vercel's `76.76.21.21`). All DNS
    instructions in `docs/webapp/07` and `11` were **wrong** and have been corrected: records must be
    added in the **Cloudflare dashboard**, because editing Hostinger's zone does nothing. The request
    path is Cloudflare → Vercel, and the proxy caveat (SSL/TLS must be **Full (strict)**; grey-cloud
    DNS-only is the better-supported option) is now documented. **(c)** The domain is attached in
    Vercel but `https://cosmicsaju.com` returns `x-vercel-error: DEPLOYMENT_NOT_FOUND` — the project
    has no successful production build yet, so it will resolve on first deploy. **(d)** The zone has
    **no MX and no TXT records**, so no mailbox and no Resend verification exist yet. **(e)** The
    stored Vercel CLI token (`~/.local/share/com.vercel.cli/auth.json`) is **expired** — `vercel whoami`
    → "The specified token is not valid" — so `npx vercel login` is needed before CLI/API inspection.
    `dig` is not installed on this machine; `07` now ships a DNS-over-HTTPS helper instead.
  - **2026-10-15 (Vercel connected and inspected).** `vercel login` was completed by the owner and the
    project was inspected via CLI + REST API. One project: **`saju-engine`**
    (`prj_8hvyP1SO0yvYcMrqks4lYtl6DSUA`, team `harishcontis-projects`), Next.js preset, Node 24.x,
    linked to GitHub with production branch `develop`.
    **Two blocking misconfigurations found and fixed via the API:**
    **(1) Root Directory was `apps/landing-page`** — the legacy app whose `src/` is not in this repo,
    so nothing built and `https://cosmicsaju.com` returned `404 DEPLOYMENT_NOT_FOUND`. Corrected to
    **`apps/web`**. **(2) Function region was defaulting to `iad1`** while Neon is in
    `ap-southeast-1`; set to **`sin1`** (both `serverlessFunctionRegion` and
    `defaultResourceConfig.functionDefaultRegions`). Note the API rejects a bare `regions` property
    on PATCH — the field is `serverlessFunctionRegion`.
    **Env vars: 21 set by the owner; two corrected.** `NEXT_PUBLIC_APP_URL` was
    `http://localhost:3000` (delivery emails would have linked clients to localhost) → set to
    `https://www.cosmicsaju.com`. `ADMIN_EMAILS` was **missing entirely**, which made `/admin`
    unreachable by anyone (requireAdmin needs the DB role *and* an email in that list) → added for all
    three scopes. Domains: `cosmicsaju.com` **redirects to** `www.cosmicsaju.com`, so **www is
    canonical**. Still missing: `LEMONSQUEEZY_*` (7) and `TURNSTILE_*` (2).
    **⚠️ Vercel plan is Hobby, which BLOCKS the per-minute dispatcher — the deploy failed with
    "Hobby accounts are limited to daily cron jobs. This cron expression (`* * * * *`) would run more
    than once per day."** This is exactly the constraint the plan predicted, now proven at deploy
    time. Made Hobby-compatible: dispatch cron → daily (`0 4 * * *`); the Lemon Squeezy webhook now
    triggers generation via **`after()` from `next/server`** (returns the 2xx first, then dispatches);
    new **`POST /api/jobs/kick`** lets a client nudge their own queued jobs (ownership-scoped +
    rate-limited) with a "Check for updates" button on `/dashboard/reports`; `kickOwnerJobs()` added
    to `fulfilment.ts`. Restoring per-minute dispatch on Pro is a **one-line** schedule change with no
    code change. Also learned: **`vercel.json` is validated against a strict schema** — even a
    `_note` key fails the deploy — so the reasoning now lives in a new
    `docs/webapp/08a-vercel-json-notes.md`.
    **Google OAuth client: deferred by owner decision until the product has >10 users** (recorded with
    a trigger checklist in `07` §"Deferred until we have more than 10 users"); sign-in keeps working on
    Neon's shared dev key, which shows Neon branding on the consent screen.
    **⚠️ R2 production bucket not found.** `ListBuckets` (which the shared token *can* call) returns
    only `construction-ledger-dev` and `saju-engine-dev`, and 14 plausible prod names all 404 — so the
    token is bucket-scoped and the new bucket is not visible to it. `R2_BUCKET` in Vercel is still
    `saju-engine-dev`. **The exact bucket name (or a token covering it) is needed.**
    Also flagged: `ENGINE_URL` is still `http://localhost:8000` in the production scope (must change
    once the engine service is deployed), and `RESEND_API_KEY` is set while the DNS zone has **no MX or
    TXT records at all**, so sending would fail verification.
    **⚠️ A credential was leaked into the session transcript by a masking bug of mine** — the
    `DIRECT_URL` password printed in full because the mask only covered `DATABASE_URL`. **Rotation
    recommended** (cheap now: no users, nothing deployed). Separately, `vercel env pull` wrote
    `.env.vercel-check`, which the `.gitignore` did **not** cover — the file has been deleted and the
    pattern added. Nothing sensitive is tracked (`git check-ignore` confirms).
  - **2026-10-15 (🚀 DEPLOYED — the site is live).** After the root-directory and region fixes, `vercel
    deploy` **succeeded** and the first deployment was auto-promoted to production. Verified from
    outside with plain HTTP, no auth:
    - `https://www.cosmicsaju.com` → **200**, 106 KB, `<title>Cosmic Saju — Korean Four Pillars
      readings</title>`, contains the hero copy. **Not** behind a Vercel SSO wall.
    - apex `https://cosmicsaju.com` → **308 → www** (www canonical, as configured).
    - `/sample`, `/login`, `/privacy`, `/terms`, `/refund-policy` → 200. `/demo/demo-rm-deep.pdf` →
      200, 139,980 bytes.
    - Production `/api/health` → **`{"status":"degraded","db":true,"storage":true,"engine":false}`** —
      the database and R2 are connected **in production**, and only the engine is dark. `version` is
      the real git SHA (`9a016a1`).
    - `/dashboard` → **307 → /login**, proving the `src/proxy.ts` auth gate works in production.
    - All protected API routes → **401 `UNAUTHORIZED`** in production (`/api/profiles`, `/api/orders`,
      `/api/reports`, `/api/account`, `/api/admin/queue`). `/api/jobs/kick` → 405 on GET (POST-only).
    Added `src/app/robots.ts` and `src/app/sitemap.ts` (public surface only; the dashboard, admin, and
    API are disallowed and excluded) — `/sitemap.xml` had been 404 and `robots.txt` was Vercel's
    platform-injected content-signals file rather than ours. Both now build as static routes.
    **Remaining gaps to launch a paid product:** (1) `services/report-engine` still unwritten — the
    only thing between this and end-to-end readings; (2) `LEMONSQUEEZY_*` (7 env vars) absent, so no
    payment can be taken; (3) Resend's DNS records still absent from the Cloudflare zone, so delivery
    email cannot send; (4) the R2 production bucket is unidentified (Vercel still points `R2_BUCKET`
    at `saju-engine-dev`); (5) `ENGINE_URL` still `http://localhost:8000` in the production scope;
    (6) the leaked Neon password should be rotated.
  - **2026-10-15 (payments swapped to Dodo; Resend verified; R2 single-bucket confirmed).** Owner
    decisions: **Dodo Payments replaces Lemon Squeezy** as the merchant of record; **Resend's DNS
    records are live**; and **`saju-engine-dev` is the one and only R2 bucket** — no separate
    production bucket.
    **Resend verified, confirmed via Resend's own API** (not by eyeballing DNS): `cosmicsaju.com`
    status **verified**, region `ap-northeast-1`, with DKIM `resend._domainkey` and SPF on both `send`
    and `rsend` (`send.forge.rmta.net`, `rsend-apne1.forge.rmta.net`) all **verified**. (The
    `forge.rmta.net` hostnames looked suspicious in a DNS lookup and are in fact Resend's.) ⚠️ No
    `_dmarc` TXT record exists — recommended for deliverability.
    **Dodo integration implemented and tested.** Researched the real API rather than guessing:
    `POST /checkouts` with `Bearer` auth, `product_cart` + `customer` + **`metadata`** + `return_url`
    → `{session_id, checkout_url}`; `test_mode`/`live_mode` select `test.dodopayments.com` /
    `live.dodopayments.com`; webhooks follow the **Standard Webhooks** spec (HMAC-SHA256 over
    `{webhook-id}.{webhook-timestamp}.{raw body}`, base64, `whsec_` stripped then base64-decoded, 5-min
    replay tolerance). New: `src/lib/dodo.ts`, `src/app/api/webhooks/dodo/route.ts`, and
    `src/lib/webhook-signature.ts` with **13 dedicated unit tests** (tampered body, wrong secret,
    tampered signature, replay outside tolerance, missing headers, wrong webhook-id, near-miss
    signature, multi-candidate headers, `whsec_`-less secret). `metadata.order_id` is what lets the
    webhook find the order again — without it a payment would take money and fulfil nothing. Fulfils on
    `payment.succeeded` (never the browser redirect, per Dodo's own guidance), audits
    `payment.failed`/`payment.cancelled` **without** cancelling the order so the customer can retry, and
    handles `refund.succeeded`. Removed `src/lib/checkout.ts` and the `lemonsqueezy` route; tier map now
    carries `productEnv: DODO_PRODUCT_*`. **Suite 57 passed / 4 skipped.**
    **Two of my own bugs caught by tests/build:** a `??` in a test helper silently swallowed an explicit
    `null`, so the missing-header cases were not actually testing null (fixed with `hasOwnProperty`);
    and `.checkoutId` needed renaming to `.sessionId` at two call sites.
    ⚠️ **A SECOND credential leaked into the transcript** — a `sed -n '34,44p' .env` printed the live
    `RESEND_API_KEY` in full, because only the `grep` in that command was masked. **Rotate both the
    Resend API key and the Neon password.** The lesson: never `sed`/`cat` an env file to inspect it —
    list keys and mask values in the same command.
    Docs updated across all 14 webapp pages: mechanical rename plus **substantive corrections**, because
    a blind rename had attributed Lemon Squeezy's *policies and fees* to Dodo. The critical-path item now
    says to confirm Dodo's own onboarding/fees and explicitly refuses to state the ~5% + $0.50 figure;
    `00` D4 and the cost tables no longer assert an unverified rate; `03` documents the real Standard
    Webhooks flow; `01`'s sequence diagram says "verify signature (Standard Webhooks)"; and
    `docs/market-research-2026-09.md` gained a "Superseded 2026-10-15" note preserving its Lemon
    Squeezy/Paddle findings as historical evidence.
  - **2026-10-15 (env-var audit).** Audited every Vercel env var and its scope. Two findings.
    **(1) `DODO_PAYMENTS_API_KEY` is not set anywhere** — not production, preview, or development —
    despite the owner believing it was added. The only Dodo var present was
    `DODO_PAYMENTS_ENVIRONMENT` (which I had created). Worth noting the owner's message spelled it
    `dodo_payements_api_key`; a typo in the **name** field would silently not match, since the code
    reads `DODO_PAYMENTS_API_KEY` exactly, and no typo'd variable exists either — so it most likely
    never saved or landed in another project. **(2) Real scope gaps, now fixed:** `DATABASE_URL` was
    missing from **preview** (it had `DIRECT_URL` but not `DATABASE_URL`, so any Preview deployment
    would have failed every Prisma query at runtime with no obvious cause) and `DIRECT_URL` was missing
    from **development** (breaking `vercel env pull --environment=development` + `prisma migrate`).
    Both now cover all three scopes with the same production-branch connection strings, consistent with
    the single-branch decision. Documented in `08a` §"Scope gaps found and fixed".
    **Clarified for the owner:** `DODO_PAYMENTS_WEBHOOK_KEY` takes the endpoint's **signing secret**
    (`whsec_…`, on the endpoint's Overview tab), **not** the endpoint id — the id authenticates nothing,
    while the secret is the HMAC key over `{webhook-id}.{webhook-timestamp}.{body}`.
  - **2026-10-15 (Dodo live and verified end to end).** The owner had put `DODO_PAYMENTS_API_KEY` in
    `apps/web/.env` **only** — which production never reads. Both secrets were pushed into Vercel for
    **all three scopes**, and the app redeployed (env changes are not live until the next deployment).
    Confirmed against **Dodo's own API**: the API key authenticates (`GET /products` → 200, test mode)
    and a webhook endpoint exists — **`ep_3KjzkirfY0iCcf2AeBt9vK46irc` →
    `https://www.cosmicsaju.com/api/webhooks/dodo`**, not disabled, subscribing to
    `payment.succeeded`, `payment.failed`, `payment.cancelled`, `refund.succeeded`. The owner's webhook
    value **is** a signing secret (`whsec_…`, 38 chars), so that question is settled correctly.
    **New: `scripts/dodo-webhook-smoke.mjs`** (`npm run smoke:dodo [target]`) — the first test that
    exercises the payment path with a **real secret against the real deployment**. It asserts: valid
    signature accepted (200); the same `webhook-id` again returns `{duplicate:true}` (idempotent);
    tampered body → 401; tampered signature → 401; one-hour-old event → 401 (replay). **Result: 5/5
    passed against production.** Verified afterwards in the database that exactly **one**
    `WebhookEvent` row was written and **zero `Order` rows** were touched — the three rejections write
    nothing, because they are refused before the DB insert. Smoke rows then deleted. The signature is
    implemented **independently** of `src/lib/webhook-signature.ts` in that script, deliberately, so
    agreement between the two is real evidence rather than a tautology.
    ⚠️ **Only remaining payments gap: the four products.** `GET /products` returns an **empty list** in
    Dodo test mode, so `DODO_PRODUCT_ESSENTIAL` / `_DEEP` / `_COMPAT_BASIC` / `_COMPAT_DEEP` cannot be
    set yet. Once created, the ids can be fetched straight from the API rather than copied by hand.
    Also learned and documented: **a Vercel env change needs a redeploy** — `503 WEBHOOK_UNCONFIGURED`
    almost always means "variable set, deployment not yet made".
  - **2026-10-16 (🚀 the engine exists — the funnel works end to end).** Built and deployed
    `services/report-engine` — which, for a reason that took two failed deploys to find, is **not where
    the docs said**: the Vercel project's Root Directory is the **repository root**, and the ASGI app
    lives at **`api/index.py`**, declared via `[tool.vercel] entrypoint = "api.index:app"`. See
    `docs/webapp/05-report-pipeline.md` §1.1/§1.2.
    **Engine edits landed (all three prerequisites):**
    - **E1** — `md_to_saju_pdf.py` now resolves fonts as `$SAJU_FONT_DIR` → `<package>/saju_html/fonts/`
      → `/usr/share/fonts/truetype/dejavu`, and the **five DejaVu faces + their licence are bundled**
      (3.0 MB) so output is identical on every host. A missing dir warns with every path searched.
      **Proved in production:** `/health` reports `fontsDir: /var/task/src/saju_html/fonts` — the
      *bundled* faces, inside the Lambda, where the system path does not exist.
    - **E2** — turned out **narrower than documented**: `sajupy` geocodes only when `longitude is None`
      (`sajupy/core.py:406`), and the webapp always supplies one, so our path never geocoded. The
      residual risk (a profile with `longitude = NULL`) is now a hard `422 MISSING_LONGITUDE` — a
      refusal is honest, a silent fallback is a wrong chart.
    - **E3** — `favorable_override` threaded through `chart_markdown` → `prepare_chart_render` →
      `build_pdf_from_chart` → `generate_premium_report`, so the review console's 용신 override now
      works for single charts too, not just compatibility readings.
    **Two deployment traps, both now documented:** (a) a Root Directory of `services/report-engine/`
    would have hidden `src/` from the function bundle — Vercel only bundles files under the Root
    Directory; (b) **Vercel's Python builder installs from `pyproject.toml` and ignores
    `installCommand`**, so `fastapi` had to be promoted out of the `web` extra into main dependencies
    or the function died with a bare `500`; and (c) a file at `api/index.py` without an entrypoint gets
    Vercel's **legacy `/api` file-function mode**, mounted at the exact path only — every sub-path
    404ed until the entrypoint was declared.
    **Verified in production:** `/chart` returns the reference chart exactly (甲戌 癸酉 辛丑 乙未 ·
    辛 Metal · Water via `strong-dm-drain` · the real hour-boundary caveat); `/generate` (deep) returned
    **139,898 bytes in 1,877 ms**, the object landed in R2, and the **downloaded sha256 matched**. Local
    `pytest` **1866 passed** (1846 + 20 new contract tests in `tests/test_report_engine_service.py`,
    which call the endpoint functions directly because httpx 0.28 removed the `app=` argument that
    starlette 0.36's `TestClient` still passes).
    **The live funnel works.** `POST https://www.cosmicsaju.com/api/sample` → **200**, a 70,899-byte PDF
    in R2 with a 15-minute presigned URL; the downloaded artefact is a valid PDF with the right cover
    (`Day Master Im (Water Yang)`) and **zero** citation/draft/reviewer leaks. And `/api/health` is
    **`{"status":"ok","db":true,"storage":true,"engine":true,"payments":true,"paymentsMode":"test_mode"}`**
    — green on every probe for the first time. Remaining: the demo-PDF/MP3 decision (D1), a real mailbox
    (B4), e2e tests and web CI (B5), and the Dodo test→live migration.
  - **2026-10-16 (the audio summary — the MP3 promise is now kept).** Owner decision: **deliver the
    MP3**, deriving the script deterministically from the **approved report text** (no LLM), send it to
    email + profile, and let delivery proceed **without waiting** for the audio while the client's page
    shows "being prepared".
    **Engine:** new `src/saju_html/audio_script.py` (in the HTML layer, because it is a *rendering* of
    the report and must run the same text pipeline the PDF does: `strip_source_citations` →
    `strip_engine_drafts` → `translate_inline`). Two defects were found and fixed during development:
    (a) **deleting** Hanja instead of translating it left grammatical husks — "energy is shaped by.",
    "its theme is." — because the report writes glyphs *with* a Latin gloss; reusing the renderer's
    translator yields "shaped by Bing O (Indirect Wealth)"; (b) a **single global character budget** let
    the opening sections consume everything and silently dropped the timing windows and the
    recommendations — i.e. it would have shipped audio that does not cover what the report promises —
    fixed with **per-section budgets**. New `POST /script` endpoint; `POST /generate` now accepts
    `mdUploadUrl` and uploads the source markdown too (closing the long-standing gap where `mdKey` was
    declared but never written, and making the script a derivation of the *stored approved* artefact
    rather than a recomputation that an engine deploy could change). **43 new pytest cases**
    (`tests/test_audio_script.py` 36, service `/script` 7); suite **1909 passed**.
    **Webapp:** `JobKind` gains `VOICE`; `Report` gains `enginePayload`, `script`, `audioKey`,
    `audioBytes`, `audioStatus`, `audioError`, `audioReadyAt`; new `AudioStatus` enum; new
    `src/lib/tts.ts` (ElevenLabs `eleven_flash_v2_5`, sentence-boundary chunking, `previous_text`/
    `next_text` for prosody across joins, ID3 stripping so the concatenation does not stop early) and
    `engineScript()` in `engine.ts`; `enqueueAudio()` at approval; `job.kind === 'VOICE'` handling in the
    dispatcher; `GET/POST /api/reports/{id}/audio`; `POST /api/admin/reports/{id}/audio` (prepare/retry);
    an audio card on the report page and an audio panel in the review console; a second "audio is ready"
    email; and the MP3 added to both erasure sweeps.
    **A real bug was caught by testing end to end:** `enqueueAudio` stored the **report** id in
    `Job.orderId`, which is a **required FK to `Order`** — every approval would have thrown a 500 at
    delivery time. Fixed by adding `Job.reportId` (nullable FK to `Report`) with its own migration
    (`20261016100000_job_report_link`), so a VOICE job now carries both ids.
    **Verified:** the TTS leg against the live API via `npm run smoke:tts` — **7/7** (model id, voice id,
    chunking, MP3 validity, ~239 s duration from 3.8 MB, a repeat call, and that the chunk join did not
    corrupt the stream). An earlier version of that check wrongly *failed* a valid file because
    ElevenLabs returns `ID3`-tagged MP3 (first bytes ASCII "ID", not a frame sync) — the test was wrong,
    not the code. Deployed `/script` on the real golden report returns 8,893 chars ≈ **9m31s**, 5 chunks.
    Voice set to ElevenLabs' *George — Warm, Captivating Storyteller* as a placeholder the owner should
    replace after listening. Migrations `20261016090000_report_audio_summary` and
    `20261016100000_job_report_link` applied to Neon. Cost ≈ **$0.32–0.40 per Deep report**.
    **Still open from the audit:** the copy's window mismatch (the audio note says `current_year … +2`,
    the upsell says `+5`; the narration now covers the report's full window, so the note under-promises)
    — harmless, but it moves the golden snapshots so it is its own change.
  - **2026-10-16 (the free tier — four findings, all fixed).** The owner asked whether the free report
    needs the review layer; it does not, and that intent was only *accidentally* implemented. Four fixes:
    **(1) `requiresReview` was dead data** — declared on the tier map and asserted in tests but read by
    **no application code**; `processClaimedJob` always set `DRAFT_READY`, so any free tier added later
    would have silently joined the review queue. The rule is now consulted via `autoDelivers()` (in
    `tiers.ts`): a non-review tier is created `DELIVERED` with a `Delivery(PROFILE)` row and emailed
    after commit, and an **unknown tier fails safe** (review). Unit-tested in
    `src/lib/__tests__/keys.test.ts`.
    **(2) `POST /api/orders` accepted `tier: "sample"`** (price 0 → `PAID` + a job) → a free report in
    the review queue. Unreachable from the UI, reachable from the API. Now `422 TIER_NOT_ORDERABLE`
    (422 for consistency with `UNKNOWN_TIER` / `TIER_PROFILE_MISMATCH`).
    **(3) "Saved to your profile" was half true** — the sample saved a `Profile` but **never a
    `Report`**, so the PDF never appeared in the library and the link expired after 15 minutes. A
    signed-in sample is now filed as a delivered `Report` under `reports/{userId}/samples/…` (new
    `buildSampleKey`, **outside** the swept `reports/anonymous/` prefix) with a `Delivery(PROFILE)` row,
    reuses a profile for identical birth details, and is **idempotent**: a repeat request returns the
    stored report (`reused: true`) instead of re-rendering the identical chart.
    **(4) 🐛 Anonymous samples were never deleted.** The sweep found stale objects by querying `Report`
    rows with `orderId: null` — but anonymous samples create **no row**, so it matched nothing and ~70 KB
    per visitor accumulated in R2 forever while `05` claimed a 7-day sweep. The sweep now lists
    `reports/anonymous/` **by prefix and deletes by object age** (`listObjectsByPrefix`), plus a
    row-backed pass scoped to never-delivered drafts so it can never touch a sample a user kept.
    **Verified end to end against production** by signing up through our own auth proxy (the CLI's
    `neon neon-auth user delete` made this safely reversible): the signed-in sample returned
    `savedToProfile: true` + `reportId`, the row is `DELIVERED` / `orderId null` / `pdfKey` under
    `reports/{userId}/samples/`, a repeat run returned `reused: true` with the same report and **no new
    render**, profile dedupe held at 1 after two runs, and `/api/orders` with `tier: "sample"` returned
    `422 TIER_NOT_ORDERABLE`. **All probe artefacts removed** — DB rows, audit rows, R2 objects (bucket
    now empty) and both Neon Auth users deleted.
    ⚠️ A false alarm worth recording: `curl -c` showed *no* cookies after sign-in, which looked like
    broken sessions. It writes HttpOnly cookies as `#HttpOnly_…` lines, which a naive `awk` filter skips.
    Sessions were fine — `__Secure-neon-auth.session_token` with `Path=/; HttpOnly; Secure; SameSite=Lax`.
    Webapp suite **64 passed**; engine unchanged at 1,909; `/api/health` green on all four probes.
  - **2026-10-15 (payments fully configured + verified).** The owner created all four Dodo products.
    They were fetched from the API and matched to tiers **by price, not by name** (names are `saju-19`
    etc.): 1900→`pdt_0NpoArP13BV3e0QbI18TR` (essential), 5500→`pdt_0NpoB67xwOcTjCoc4Dfbb` (deep),
    2400→`pdt_0NpoBDXleHNyHVs2KyySb` (compat basic), 4500→`pdt_0NpoBMQhUhs2VRMsBXtI1` (compat deep).
    **Every one is `price_detail.type = one_time_price`**, so the subscription trap warned about earlier
    did not occur — no product takes money in a way the `payment.succeeded`-only handler cannot fulfil.
    All four `DODO_PRODUCT_*` set in Vercel across all three scopes and mirrored into local `.env`; all
    **7** Dodo variables are now configured. The script refuses to write anything unless every tier
    resolves to exactly one one-time product, so a half-configured state cannot be introduced.
    **The checkout path is verified end to end:** replaying the **exact** payload `createCheckout()`
    sends against `POST /checkouts` returned **HTTP 200 with a real `checkout_url`**
    (`cks_0NpoBX6HmFxDJSz9EgcCU`), proving both the product id and our request shape are accepted by
    Dodo. No payment was made; the session expires on its own.
    **`/api/health` now reports payments**: `payments` (true only when the provider is configured *and*
    every paid tier has a product id) and `paymentsMode` (`test_mode` | `live_mode`). That turns "are
    payments configured?" into a verifiable boolean, and `paymentsMode` is how you notice a deployment
    still pointed at test mode — or one that went live early. Documented in `09` §health checks.
    **Payments are therefore complete.** The only remaining blocker for a real sale is
    `services/report-engine`: money can be taken, but nothing can be fulfilled until it exists.

  - **2026-10-16 (contact mail: a real mailbox, and the reply that never landed).** The owner created
    `hello@cosmicsaju.com` as **one mailbox plus receive-only aliases** in Hostinger webmail. Chasing the
    dead `privacy@` address surfaced something larger than the legal contact: **three client-facing
    messages explicitly invite a reply, and all three bounced.** `deliverReportEmail` sent
    `From: reports@cosmicsaju.com` with **no `Reply-To`**, and with no MX at the apex a reply went
    nowhere. The invitations: the reject email (*"we'll either fix this or refund you — just reply to
    this email"*), the report page's `FAILED` state (*"reply to your order email"*), and the audio-failed
    copy (*"reply to your order email if you'd like us to try again"*).
    **Address scheme — one mailbox, role-based names, deliberate split:** `hello@` (the mailbox a human
    reads; general contact + the footer), `privacy@` (alias; **reserved for data-protection requests**, so
    a DSAR is recognisable on arrival — and still the address the legal pages publish), `reports@` (the
    transactional From; receives replies too), `dmarc@` (for `rua=`), `postmaster@`. New
    `apps/web/src/lib/contact.ts` exports `CONTACT_EMAIL` / `PRIVACY_EMAIL` (+ `_HREF`); five files now
    import from it instead of repeating `process.env.… ?? "privacy@…"` — `site.tsx` (footer) and
    `refund-policy/page.tsx` move to `hello@`; `privacy/page.tsx` and `dashboard/account/page.tsx` keep
    `privacy@`; `legal.tsx`'s `LEGAL_CONTACT` re-exports `CONTACT_EMAIL`.
    **The actual fix for the bounce is `EMAIL_REPLY_TO`.** `sendEmail()` already accepted a `replyTo`
    that **nothing ever set**; it now defaults to `process.env.EMAIL_REPLY_TO`, so a new sender cannot
    forget it (there is exactly one `api.resend.com` call site, inside `sendEmail`). `EMAIL_FROM` stays
    `reports@` — a *sending* role identity, not an inbox.
    **Verified rather than assumed:** on the live site `/privacy` publishes `privacy@` and the footer
    publishes `hello@`; and a real send through Resend's API stores
    `reply_to: ["hello@cosmicsaju.com"]` beside the right `from` (read back via `GET /emails/{id}`).
    New `src/lib/__tests__/email-reply-to.test.ts` (5 cases) locks the invariant — an explicit caller
    `replyTo` wins, the header is **omitted rather than sent empty** when unset, and an unconfigured
    Resend reports `skipped` and sends nothing. That file stubs `global.fetch` and must import
    `email.ts`, which reaches for the Prisma singleton, so it sets a dummy `DATABASE_URL` first (the
    client is lazy — nothing connects). Webapp suite **64 → 69 passed**.
    **⚠️ Then the trap this document predicted fired — and was fixed the same day.** A mail host cannot
    publish records into a DNS zone it does not host, so Hostinger's panel says *"log in to Cloudflare …
    and add the records below"*. Until that was done, `MX cosmicsaju.com` read **NONE** and apex TXT was
    empty while the mailbox was configured — mail went nowhere. The owner then published the records
    **in Cloudflare**, and the live state is now: `MX → mx1/mx2.hostinger.com`
    (priority 5/10), **exactly one** apex SPF (`v=spf1 include:_spf.mail.hostinger.com ~all`), and
    `_dmarc` = `v=DMARC1; p=none`.
    **Receiving is proven, not assumed:** a real message from the app's own `EMAIL_FROM` to
    `hello@cosmicsaju.com` came back from Resend's API as **`last_event: delivered`** — where the earlier
    test against the MX-less zone had only reached `sent`.
    **The DKIM CNAMEs were then added, the mistyped `c` record corrected, and the final state is: our side
    is complete.** All three names resolve as CNAME (`hostingermail-a/b/c._domainkey` →
    `hostingermail-*.dkim.mail.hostinger.com`) and the junk
    `hostingermail-c.dkim.mail.hostinger.com.cosmicsaju.com` record is gone. But the **keys** are the
    remaining fault, and it is Hostinger-side: `hostingermail-a.dkim.mail.hostinger.com` serves a **real**
    key (`v=DKIM1;k=rsa;p=MIIBIjANBgkq…`), while **`hostingermail-b` and `hostingermail-c` serve EMPTY
    keys** (`v=DKIM1;p=`, no key material) — so those two can never validate however DNS is configured.
    No further DNS change is possible; it needs Hostinger to (re)issue keys for `b` and `c`.
    **What actually matters, and one test settles it:** which selector the mail host *signs* with is
    invisible to DNS. Send from `hello@` in Hostinger webmail to a Gmail address → *Show original* → read
    `dkim=` and `header.s=`. `dkim=pass … header.s=hostingermail-a` ⇒ the empty selectors are unused and
    the panel warning is cosmetic; `dkim=fail … header.s=hostingermail-b|-c` ⇒ a *failing* signature, which
    is worse than none, and Hostinger must issue the keys.
    ⚠️ **Neither outcome risks delivery:** `_dmarc` is `p=none` and DMARC also passes on **SPF alignment
    alone** (envelope sender `…@cosmicsaju.com`; the apex SPF authorises Hostinger), so a DKIM failure
    cannot cause rejection. And the scope is narrow — this affects only mail sent **by hand from Hostinger
    webmail**; the app's mail goes through **Resend** (`resend._domainkey`, verified), so reports, audio
    and reject emails are unaffected. `_dmarc` still needs `rua=mailto:dmarc@cosmicsaju.com` (bare `p=none`
    at present).
    ⚠️ **Diagnostic gotchas worth keeping.** (1) `dnsq … CNAME` returned `(none)` for names that *are*
    CNAMEs — Cloudflare's DoH chases the chain; query `TXT` (which chases and returns the target's key,
    including an empty `v=DKIM1;p=`) or use Google's `dns.google/resolve?type=CNAME`. (2) The Google
    endpoint is `https://dns.google/resolve`, **not** `https://dns.google/dns-query` (the latter 404s and
    yields a JSON parse error).
    **On the earlier false alarm:** the owner's first report of *"cname is already there"* was a false
    alarm — at that point all three DKIM names were genuinely **empty** (CNAME/TXT/A all `(none)`, no
    wildcard, no swap), and the existing CNAMEs sit at different names (`send`, `rsend`, `www`).
    Hostinger's MX does not conflict with Resend because Resend is on `send`/`rsend`.
    Documented as `07` §Mailbox records plus a `09` runbook — *"Mail is not arriving, or a client's reply
    bounces"* — which names DNS, not code, as the first suspect. Also recorded: **Neon Auth's magic-link
    mail bypasses our `Reply-To`** (Neon sends it from its own SMTP configuration), so that From address
    is Neon's to set, not ours.
    **Env:** `EMAIL_REPLY_TO` and `NEXT_PUBLIC_CONTACT_EMAIL` (both `hello@cosmicsaju.com`) added to all
    three Vercel scopes — **32** distinct variables now. `NEXT_PUBLIC_*` is inlined **at build time**, so
    this needed a redeploy, which is also what confirmed the addresses on the live pages.
    **Two side discoveries.** (1) The **Cloudflare proxy is now off**: the apex A record points at
    Vercel's `216.198.79.1` (`server: Vercel`, no `cf-ray`). That is the better-supported setup and it
    leaves the apex free for the mailbox's MX. Recorded in `07`/`13`. (2) **Cloudflare in front of
    `api.resend.com` refuses `Python-urllib` with `error code: 1010`** while `curl` passes — so a Resend
    smoke check must use curl, or it looks like a bot and is blocked.
    **Deploy note:** the webapp deploys by **CLI from the repository root**, because the project's Root
    Directory is `apps/web` and the CLI applies it relative to the upload — running `vercel` *inside*
    `apps/web` fails with *"The specified Root Directory apps/web does not exist"*. That needs a
    temporary root `.vercel/project.json` (same project id), removed afterwards. `apps/web` is **not
    tracked by git at all** (0 files), which is why a git-based deploy cannot build it.
    **Still open:** the three **DKIM CNAMEs** (above), and the two credentials leaked into the transcript
    (the Neon password and the Resend key `re_Nb6…`) are **not yet rotated** — now the highest-priority
    item, since a real mailbox exists.
    Docs updated: `07` (stack table, provisioning log, a rewritten §Mailbox records, DNS-only decision,
    Resend From guidance, a `no-reply@` entry under "deliberately not used", cost + open decisions),
    `08` (two new env vars, a Mail subsection, engine root/entrypoint/Node/`excludeFiles`/cron
    corrections), `10` (correspondence as a processor-held data class, retention, deletion survivors,
    DSAR intake, checklist), `05` (the `Reply-To` contract), `13` (B4 rewritten with the three bounced
    invitations, §D2, remediation and open decisions), `12` (what actually exists vs. planned, the new
    suite), `06` (which address appears where), `11` (Phase-0 rows), `04` (the magic-link From caveat),
    `00`/`01`/`03`/`09` and `openwiki/quickstart.md`.

### Earlier state (2026-09-26)

- **Two 2026-09-26 audit passes closed 22 + 16 findings, 26 of 38 fixed.** See "Recent Changes"
  below. The 2026-09 audit reports that tracked this work were removed in the 2026-10-01 cleanup. **Suite: 1136 passed / 9 xfailed / 0 failed.** Validation gate:
  `python3 tools/run_validation.py` → `206 (PASS 202, INTERPRETATION 4, FAIL 0)`. `ruff check
  --select F src tools tests` is now clean and enforced in CI (was not run in CI before this pass).
  **All three doctrinal items are now implemented:** **N-5** (yin-DM strength now scores
  the month branch by element relation / 득령, knowledge/09 Step 2 — not the 12운성 stage; extreme
  bands widened 4.0→5.0 to keep `extreme` rare and hold published verdicts stable) and **N-9**
  (양인격/건록격 now fire at the month/월령 position as the classical grid, with the year/day/hour
  case relabelled a related-but-distinct pattern). **N-3 is now FIXED** — the engine reads an
  accurate ephemeris-generated solar-term table (`src/saju_engine/data/solar_terms.csv`, via
  `tools/generate_solar_terms.py`; PyEphem VSOP87, 1899–2101) instead of sajupy's CSV, which was
  off by a median 22 min / up to 114 min — fixing month-pillar flips for births near a 節氣.
  **N-6 is now FIXED (industry-standard whole-chart gate)** — following 정해 만세력 (8-codes) and 사주플러스, `climate.climate_temperature()` computes a
  weighted whole-chart 한난 score (month/hour weighted higher) and two threshold-free gates decide
  priority: `is_climate_extreme()` withholds the override when a hot/cold month's whole chart clearly
  leans the other way, and `is_remedy_dominant()` withholds it when the prescribed remedy is already
  the most-abundant element. The **element** stays month/stem-derived (궁통보감 — deriving it from the
  temperature score would flip Harish's validated Water). Corrects both audit examples, changes
  **zero** published deliverables (verified: regen produced no markdown diff). See
  `docs/research/2026-09-26-climate-extremeness-threshold.md`. Client reports were regenerated for
  N-5/N-9 on 2026-09-26 (second pass).

- Engine is feature-complete for the current product scope, now including a 조후 (climate-balance)
  cross-check on top of the existing 억부 (strength-balance) 용신 heuristic — see the 2026-09-13
  entry below and `knowledge/17-climate-method.md`.
- **885 pytest tests pass / 10 xfailed / 0 failed** (`python3 -m pytest` from the repo root; verified
  2026-09-14 late evening, after the item-1 fix below). The 10 xfails are `xfail(strict=False)`
  markers asserting the *correct* behaviour that a still-unfixed defect blocks — "still xfailed"
  means *still defective*; the marker turning XPASS is the delete-the-marker signal. Cross-validation
  cases are in `tests/test_cross_validate.py` (the standalone harness was folded in and deleted).
- **Validation gate grew to 10 subsystems (P3, 2026-10-03):** W7 stars (신살, 57 fixtures,
  c8ef120) and W8 patterns (격국, 51 fixtures, 2e78fc8 + 1648979 + 04cf1d5) added; gate is now
  `python3 tools/run_validation.py` → `314 (PASS 305, INTERPRETATION 9, FAIL 0)`. Per-gate narrative
  lives in `docs/validation/gate-history.md`. **Adding a fixture:** append an entry to
  `tests/validation/fixtures/stars.json` or `patterns.json` (`id`, `subsystem`, `input`, `source`
  with a `knowledge/<file>.md:<lines>` citation + an external URL, `expected`, `status`
  `expect_match`|`documented_interpretation`, `notes`). Schema: docstrings of `check_stars` /
  `check_patterns` in `src/saju_engine/validation.py` (stars `expected.stars` + optional
  `input.star_anchor` day|year; patterns `expected.patterns` keys). Unknown keys raise. Also P2-W
  closed (d292746): 종격 confidence is condition-based, `extreme_weak` removed.
- **Validation campaign closed 2026-09-14:** all six workstreams certified — 194 checks / 189 PASS /
  5 INTERPRETATION / 0 FAIL across 8 subsystems (W1 pillars 17, W2 대운·세운 19, W3 lookups 56,
  W4 용신 13, W5 조후 30, W6 compat+career 59). Gate commands and expected output:
  `python3 tools/run_validation.py` → `194 (PASS 189, INTERPRETATION 5, FAIL 0)`, exit 0, stdout md5
  `9626959ad9b18f658fa49adb1b3ebeee`. The rendered report
  `tmp/engine-validation-report.md` is **produced by that tool — never hand-edit it**;
  current render md5 `c697db8f529cb992f07de623598869b4`.
- **Post-campaign fix wave landed (2026-09-14) — tree is CLEAN, not dirty.** The user directed work on
  the 13 loose ends the campaign pinned but didn't fix (see `memory/saju-open-defects-triage.md` in
  Claude's own memory for the full record). **Nine are now fixed:** #5 (nayin order-dependence), #6
  (career tier-pool Day-Master→용신/희신 rekey, which also fixed client-visible item 2), #8
  (`md_to_saju_compat_pdf.py --output` path bug), #9 (Harish longitude 76.33→79.42), #11 (辰/戌 climate
  divergence, resolved as documentation+scope not a model change), #12 (unsourced dry/damp claim
  removed), #13 (dead `_CHECKERS` registry pruned), and **#4 + client-visible item 3 together**,
  landed as **"(A) + C-none"**: the 육합 (six-combination) dead-code arity fix in
  `compat.py::_branch_pair_lookup` (moved exactly one fixture, `compat-mahesh-vp` 64/Mixed→68/Strong),
  plus documenting the 삼형 (branch-punishment) chain position as an unsourced scope limit — C9 stays
  pinned by design, not a bug. `src/saju_engine/compat.py` current md5 `9de82a5548caaf22828a2298a591966e`
  — this is the **sanctioned final state**, not the mid-experiment variant. (An earlier same-day
  session note about a "dirty tree at variant A-high" describes a since-resolved intermediate state;
  do not act on it.)
- **Client-visible item 1 — FIXED 2026-09-14 late evening.** `premium_report.py`'s
  `_right_now_callout()` and `ctx_favorable_phrase()` now read the resolved `favorable_element()`
  value (with `ctx.favorable_override` threaded through) instead of the raw candidate field. This
  closes the entire two-channel bug class found by the campaign. Harish's `harish-report.md` was
  regenerated from scratch the same session and now shows Water natively (previously a hand-patch).
  **#7** (regenerating client reports affected by the 야자시 hour-stem fix, plus Harish's stale
  follow-ups) is still in progress, not complete — see "Active Wishes / Open Items" below. Two
  **product decisions** (not defects) remain surfaced but undecided: #10 (조후-vs-억부 gate width)
  and whether `climate.py` should expand to the full 寒暖燥濕 four-way 궁통보감 reading.
- **Products implemented** (USD, after the 2026-09-07 pivot — see `docs/market-research-2026-09.md`):
  - **The Hook** (`sample`) — free 1-page report.
  - **The Essential Report** (`essential`) — $9 intro → $19, 6–7 pages.
  - **The Deep Destiny Report** (`deep`) — $55, 10–12 pages.
  - **Cosmic Companion** (`companion`) — $9/month or $79/year, 3–4 pages; manual-billing subscription (off the primary pricing grid).
  - **두 분 궁합 / Compatibility** (`compat`) — Snapshot ($24) and Deep ($45) tiers, 11 sub-systems, composite 0–100 score. Deep is the hero product.
- **Intake paths:** self-service FastAPI app (`tools/client_intake_app.py`; `/` single-chart, `/compat` two-chart, saves JSON intake and returns tiered PDFs), and landing-page Next.js app (`apps/landing-page`) wired to the calculator for the free sample tier.
- **PDF backends:** reportlab (default) and HTML/Playwright (`--html`).
- **Major recent additions (2026-06-21 through 2026-07-12):** daily-luck (일운) overlay, engine-driven prose scaffold, premium report generator, landing-page tiered products, major-luck activation overlay, marriage-compatibility engine + report + PDF renderer, 30×30 Nayin pair table, Korean textbook 만세력 validation cases, repo-root documentation consolidation into `docs/`, Cosmic Companion subscription tier, deeper special-formations validation tests, richer engine-drafted prose fillers, landing-page/free-sample integration, complete `docs/openwiki/` reference site (README + quickstart + architecture + domain + products + operations), and landing-page demo reports generated from RM (Kim Nam-joon, BTS) birth data for all three single-chart tiers.

## Strategy (2026-09-07 pivot)

Triggered by the deep-dive research report `research-engine/output/2026-09-07/report-saju.html`.
The product moved from an **India / ₹ / Vedic-adjacent NRI** framing to an **English-speaking-global
/ USD** one. India is now a Phase-2 PPP experiment only. Positioning: *"an accurate engine and an
honest interpreter — not a Korean master."* Lowest-CAC channel is organic short-form video; the
compatibility (궁합) product is the marketing hero. Realistic revenue ceiling with manual
fulfilment: ~$1–3K/month; most likely 12-month outcome is a kill/skip.

- **Sourced research:** `docs/market-research-2026-09.md` — every market number with a confidence flag.
- **P0 blockers fixed 2026-09-07:** G1 (reviewer-note leak into client PDFs), G2 (per-pillar template
  grammar), G3 (용신 single source of truth via `src/saju_engine/yongsin.py` + provenance), G6 (₹→USD
  in engine text). Suite 568 → 590.

## Decisions to Remember

1. **Package layout:** The Python packages live under `src/`: `src/saju_engine/` and `src/saju_html/`. `pyproject.toml` declares `where = ["src"]` and `pytest` adds `src` to `pythonpath`. Direct-run scripts under `src/saju_html/` and `src/saju_engine/` insert `src/` into `sys.path` so they still work when invoked directly.
2. **Calculation backend:** Use `sajupy` for solar-term and 60-cycle math; all Korean / Myeongri (명리) lookups and overlays are our own.
3. **Zi-hour convention:** Default is `korean` (야자시, 23:00–00:59 belongs to the *current* day's 子 hour). Use `chinese` for the early-Zi / 조子시 rule if requested.
4. **Solar-time correction:** Enabled by default for non-standard longitudes. Indian births are corrected from the IST meridian (82.5°E) before deriving hour branch and day pillar.
5. **Engine output is a draft:** Premium reports are explicitly marked `[ENGINE DRAFT — REVIEW REQUIRED]`. Human review is required before delivering paid tiers to clients.
6. **No custom ephemeris:** `sajupy` is sufficient for the target accuracy; a from-scratch ephemeris is explicitly out of scope.
7. **No public web app in repo:** The FastAPI self-service app exists for local use; deployment to a public endpoint is a separate, deliberate decision.
8. **Language:** Primary output language is English; technical terms include Korean (한글) and Hanja (한자) on first use.
9. **용신 resolution order (as of 2026-09-13):** `yongsin.favorable_element(chart, override=None)` checks, in order: (1) an explicit `override=` argument, (2) `chart.strength_assessment["reader_override_favorable"]` (set by `compat.py::compat_score`'s `favorable_element_a`/`_b` params — this is what lets a compat report's reader override survive the climate merge), (3) for a **balanced** verdict born in a **hot** (巳午未) or **cold** (亥子丑) month, the 조후 climate element wins the headline (`method="climate-balanced"`) over the old "least-represented element" fallback, (4) otherwise the existing 억부 strong/weak-drain/support logic (unchanged) — see `src/saju_engine/climate.py` + `knowledge/17-climate-method.md`. `compat.py`'s 4 scoring functions (`compat_yongshin`, `_spouse_palace_virtue`, `compat_combined_elements`, `compat_tengod_cross`) all route through `favorable_element()` now too (via `_resolved_favorable`/`_resolved_supporting` helpers), not the raw `strength_assessment` fields directly — this keeps compat *scoring* and *display* from disagreeing.

## File Map

| Need | File |
|---|---|
| Agent persona / ground rules | `CLAUDE.md` |
| Project overview & quickstart | `README.md` |
| This memory file | `docs/MEMORY.md` |
| Engine issue tracker + fix history | `docs/issues_bugs.md` |
| Sourced market research | `docs/market-research-2026-09.md` |
| Reference doc site | `docs/openwiki/` |
| Knowledge base (interpretive reference) | `knowledge/00-glossary.md` through `knowledge/17-climate-method.md` |
| Calculation engine | `src/saju_engine/` |
| HTML/PDF shared helpers | `src/saju_html/` |
| PDF builders | `src/saju_html/md_to_saju_pdf.py`, `src/saju_html/md_to_saju_html_pdf.py`, `src/saju_html/md_to_saju_compat_pdf.py`, `tools/build-pdf.sh` |
| Report combiner | `src/saju_html/combine_candidate_report.py` |
| Tests (includes cross-validation cases) | `tests/` |
| Per-candidate readings | `candidates_horoscope/reports/{slug}/` |
| Client intake records (gitignored — may hold PII) | `candidates_horoscope/intake/` |
| Slash commands | `.claude/commands/saju.md`, `.claude/commands/saju-client.md` |

## Conventions

### Report tables and golden snapshots
- **Report primitives:** All shared report helper tables, enums, and formatting functions live in a single `src/saju_engine/report_primitives.py` module. Never re-declare a copy in another module (e.g., `prose_fillers`, `compat_report`, etc.). If you need a table or function, import it from `report_primitives`.
- **Golden snapshots:** Regression test baselines live in `tests/golden/` (currently 7 charts covering strong/extreme/weak/climate-override cases). Regenerate them with `tools/regen_golden.py` **only** when a reviewed output change is approved. Running the tool without review risks masking bugs.

### Candidate folders
- One subfolder per candidate: `candidates_horoscope/reports/{name-slug}/`
- Slug style: lowercase, hyphenated.
- Base natal reading: `{slug}-report.md`
- Topic follow-ups: `career.md`, `relationships.md`, `health.md`, `2027-outlook.md`, etc.
- Overlapping follow-ups append to the existing file under a dated heading: `## YYYY-MM-DD — summary`.
- Consolidated client PDF: `{slug}-combined.{md,pdf}` generated via `src/saju_html/combine_candidate_report.py {slug}`.

### Compatibility reports
- All compat reports live under `candidates_horoscope/marriage_compatibility/{name_a_slug}_{name_b_slug}/` (one subfolder per pair).
- Basic tier: `{name_a_slug}_{name_b_slug}_compatibility.{md,pdf}`.
- Deep tier: `{name_a_slug}_{name_b_slug}_compatibility_deep.{md,pdf}`.
- Partner A is listed first; for heterosexual pairs Partner A is the male.
- Update the **Compatibility (궁합) readings** table at the bottom of `candidates_horoscope/README.md`.

### Client products (USD — 2026-09-07 pivot)
| Client-facing name | Engine tier | Price | Page target | Notes |
|---|---|---|---|---|
| The Hook | `sample` | Free | ~1 page | Fully automatable. |
| The Essential Report | `essential` | $9 intro → $19 | 6–7 pages | Engine draft → review required. |
| The Deep Destiny Report | `deep` | $55 | 10–12 pages | Includes year-by-year windows; MP3 audio summary wording included by default. |
| Compatibility Snapshot (두 분 궁합) | `compat_report(..., tier="basic")` | $24 | ~4 pages | Two-chart snapshot: composite 0–100 score + 4-band verdict, four-pillar glance, four decisive sub-systems, condensed Practical Guidance, Closing Note. |
| Deep Compatibility (두 분 궁합) — hero | `compat_report(..., tier="deep")` | $45 | 9–10 pages | Basic + all 11 sub-system cards, per-partner element balance / Day Master snapshots, major-luck timelines, year-by-year couple timing overlay, full Practical Guidance, Closing Note. |
| Cosmic Companion | `companion` | $9/mo or $79/yr | 3–4 pages | Manual-billing subscription; off the primary pricing grid. |

`generate_compat_report` accepts `favorable_element_a` / `favorable_element_b` — pass the reader-argued 용신 so the natal and compat products agree (see `src/saju_engine/yongsin.py`).

Legacy tiers `spark`, `reading`, and `fullmap` are still accepted by the engine but map to `essential`/`deep`/`deep` and should not be sold to new clients.

### Engine-first rule
When a user supplies a Gregorian birth date, time, and place, run the engine first to get a structured skeleton. When the user supplies the four pillars directly (년주/월주/일주/시주), accept them and proceed without the engine.

## Quick Commands

```bash
# Run the full pytest suite (includes cross-validation cases)
python3 -m pytest tests/ -v

# Generate an engine skeleton for interpretive work
PYTHONPATH=src python3 -m saju_engine \
  --date YYYY-MM-DD --time HH:MM --gender M --city "City" \
  --format skeleton --output-file /tmp/skeleton.md

# Generate a premium client-facing draft
PYTHONPATH=src python3 -m saju_engine \
  --date YYYY-MM-DD --time HH:MM --gender M --city "City" \
  --name "Client" --format premium --tier essential \
  --output-file /tmp/premium.md

# Build PDF from an existing markdown report
./tools/build-pdf.sh sruthi

# Build a consolidated client PDF (base report + topic follow-ups)
./tools/build-pdf.sh --combined --html sruthi "Title" "Client" "DOB" "Day Master"

# Build a compatibility PDF
python3 src/saju_html/md_to_saju_compat_pdf.py <compat.md> --name-a ... --name-b ...
```

## Active Wishes / Open Items

As of 2026-09-07 the engine P0 blockers (G1–G3, G6) are fixed. Open P1 items:
- **Merchant-of-Record checkout** — ✅ **Dodo Payments** chosen (replacing Lemon Squeezy/Paddle) and
  configured; test-mode checkout verified end to end. Remaining: the **test→live migration** — 4 live
  products, a live webhook endpoint + signing secret, then `DODO_PAYMENTS_ENVIRONMENT=live_mode`.
- **Real testimonials** on the landing page — the section was **removed** rather than faked, so the
  documented FTC risk is closed by omission.
- Self-service app hardening: DONE 2026-10-04 (encrypted store, background drafts, review queue, private
  links). Deployment: **DONE** — `https://www.cosmicsaju.com` is live, and the engine, review console,
  and delivery (PDF **and** MP3) all run.
- **Contact mail** — mailbox `hello@` + aliases, a default `Reply-To`, and the records published in
  Cloudflare; **receiving verified** (`delivered`, 2026-10-16). All three DKIM CNAMEs now resolve. ⚠️
  Remaining: Hostinger serves **empty** DKIM keys for selectors `b`/`c` (`v=DKIM1;p=`) — a Hostinger-side
  fix — and `_dmarc` still wants `rua=mailto:dmarc@cosmicsaju.com`. Neither risks delivery
  (`p=none`; DMARC passes on SPF alignment). See `docs/webapp/07` §Mailbox records.
- **Rotate the two credentials leaked into the session transcript** — the Neon password and the Resend
  API key `re_Nb6…`. Highest priority now that a real mailbox exists.
- **Webapp CI + end-to-end tests** — still missing (launch-audit B5). `12-testing.md` now marks the
  Playwright surface as planned rather than present.
- **A1:** ~~recover `apps/landing-page/src/` from the machine that built it~~ — **closed**: the landing
  page was rebuilt inside `apps/web`, which is what serves the site.
- Engine prerequisites E1/E2/E3: **DONE**; the engine is deployed at `api/index.py` (Vercel root = repo
  root, region `sin1`).
- Populate the 30×30 Nayin pair table from a published source (currently on the 5-element fallback).
- Optional additional Korean textbook 만세력 cases if more independent sources are found.
- **`premium_report.py` "What This Year Means for You" bug — FIXED 2026-09-14.**
  `_right_now_callout()` (line 181) and `ctx_favorable_phrase()` (line 1399, called from
  `_year_one_liner`) now take an `override: Optional[str] = None` param, read
  `favorable_element(chart, override).element` instead of the raw
  `strength_assessment["candidate_favorable"]`, and both call sites (`_section_chart_glance`'s
  "What This Year Means" block, `_year_one_liner`'s Hook-tier one-liner) thread
  `ctx.favorable_override` through. This was the last surface in the two-channel bug class (the
  matching `report_data.py` career-section bug was fixed earlier the same day). The 2
  `xfail(strict=False)` markers in `tests/validation/test_val_climate.py:234`/`:255` XPASSed and
  were retired — the tests now stand as plain regression locks. Suite 883/12 → **885 passed / 10
  xfailed / 0 failed**; validation CLI gate unchanged at `194 (PASS 189, INTERPRETATION 5, FAIL 0)`
  (these 2 tests were never part of the CLI's own check count). **Note for future regens:** this
  fix changes the "What This Year Means for You" / Hook-tier one-liner text for any *already
  generated* report whose raw candidate element differs from its resolved element (climate-merged
  or reader-overridden charts) — worth checking before treating an old PDF as current.
- **Harish's candidate folder — base report regenerated from scratch 2026-09-14, follow-ups still
  pending.** All 8 original files were deleted 2026-09-14 (md5-verified backup at
  `/tmp/harish-backup-2026-09-14`, not in the repo). `harish-report.md` + `harish-report.pdf` are
  now regenerated cleanly (`--tier deep`, `--longitude 79.4408 --city "Pallipattu, Tamil Nadu"`, no
  override; pillars 壬申/乙巳/辛亥/己丑 confirmed; PDF audited clean — 0 draft markers, 0 citation
  leaks) — and now that the bug above is fixed, the "What This Year Means for You" line shows
  Water natively with no hand-patching. **Not yet recreated:** `career.md`,
  `land-workshop-business.md`, `luck-timeline.md` (+ their PDFs). Mechanical mapping for the
  re-authoring: 용신=Water, 희신=Metal, 기신=Earth (controls Water), secondary avoid=Fire (controls
  Metal); branch-activation bonuses (합/충/해/파/삼형) are unaffected. This is real classical
  interpretive writing (the deleted originals were ~30KB each), not a mechanical regen — treat as a
  separate task.
- **#7 — regen for the 야자시 hour-stem fix, in progress:** Pawan's `pawan-report.md` + `career.md` +
  PDF are regenerated and promoted (hour 戊子→庚子). **Still pending:** Mahesh's client report +
  the `pawan_sruthi` compat pair PDF rebuild (the `.md` was hand-edited — hour cells 戊子→庚子,
  score re-measured 55/Mixed — but the PDF rebuild was user-rejected, so `.md`/`.pdf` are currently
  out of sync), plus the `yongsin.json`/`climate.json` fixture cascade noted in the plan.
- **`md_to_saju_compat_pdf.py` default `--output` path bug — FIXED 2026-09-14** (carried defect #8):
  `output_pdf.parent.mkdir(parents=True, exist_ok=True)` added before write. `--output` no longer
  needs to be passed explicitly, though doing so is still fine.

## Recent Changes to Remember

- **2026-10-04 (P5 HTML-first reports, branch `feat/p5-html-first`)** — User decision "flip default, keep
  reportlab". 6401cd4 + 560e1fb: no silent backend fallback (renderer raises unless `allow_fallback=True`
  or env `SAJU_PDF_FALLBACK=reportlab`); unmapped CJK kept in HTML and reported (reportlab warns);
  phrase-level Korean rules `_PHRASE_RULES`; `tests/test_translation_coverage.py` +
  `test_translation_quality.py`. f2a7e15: HTML/Playwright is the default — `build-pdf.sh` default HTML,
  `--reportlab` legacy writes `*-reportlab.pdf`, `--html` no-op alias; `src/saju_html/chart_input.py`
  shared chart-to-markdown; `md_to_saju_html_pdf.py --from-chart/--tier`; compat tool `--backend
  html|reportlab` (default html); `jobs.py` env `SAJU_PDF_BACKEND=reportlab` override. 3645ea8: pdftotext
  leak test, compat default path for both backends. a839244: 46 rendered-HTML snapshots in
  `tests/golden_html/` (`tools/regen_golden.py --html`; they embed the full CSS, so a CSS change rewrites
  them all — regenerate deliberately). Browser install: `pip install playwright && python -m playwright
  install chromium`. Still open: C1-templates (Jinja2 rewrite), reportlab removal after one release,
  P5-hangul-tokens, D1/D2/D3, P2-F, P3-reader-claim, P4-ratelimit, tests-geocoder, A1.

- **2026-10-04 (P4 web hardening, branch `feat/p4-web-hardening`)** — S8a (bf131bf + 691118e): 세운/월운
  use `data/solar_terms.csv` at 12:00 KST, reused day clamped to month length (drift vs sajupy 1,355/73,414
  days, all on 절기 days except sajupy errors 1903-07 and 2019-06). C3/M15 (d0b68c1 + 1ce4aa5): encrypted
  SQLite intake store `src/saju_web/store.py` (`SAJU_INTAKE_KEY`, retention default 180 days; approval only
  via token, free sample via `mark_approved_without_token`). S8c/S8d/S8e/S8f/C4 (72cb696 + 1976180):
  `/generate` validates before saving; paid tiers -> 202 + background draft + owner approval; private
  `GET /report/{token}`; CORS no credentials; `SAJU_HOST` default 127.0.0.1; `SAJU_INTAKE_DIR`; sanitized
  logs. Owner workflow: `python3 tools/intake_admin.py genkey|list|show|approve <id> --base-url|regenerate|purge`
  (run the app with `SAJU_INTAKE_KEY` set and umask 077). Suite 1552 passed; validation 315 checks.
  **Open: email delivery (D2), MoR checkout (D1), deploy (D3)**, plus P2-F, P3-reader-claim, landing page A1.

- **2026-10-02 (audit 2026-10-01 Wave A/B fixes, branch `fix/audit-2026-10-01-wave-ab`)** — S1: 세수/current
  대운 compare 입춘 in the birth's local time. S2: compat element-balance table uses canonical
  `strength.element_balance_pct`; compat 용신/기신 flags and combined-elements narrative no longer print
  percentages (user decision; the table is the only client-visible %); scoring helper is now
  `compat._weighted_presence_pct`, WEIGHT unchanged. S3: compat Major Luck favorability uses the shared
  `prose_fillers.period_favorable_status`. S5: stdlib intake servers and `client_intake_form.html` removed;
  FastAPI serves both flows. S7: USD prices in intake forms. S8b/S8c: `/compat/generate` requires
  `utc_offset_a/b` and validates before saving intake JSON. A5/A6/A7: test PYTHONPATH cleanup, CLAUDE.md
  path fixes, dead code removed. Tracker: `docs/issues_bugs.md` "Audit 2026-10-01".

- **2026-09-30 (new compat pair: Harish × Srinidhi)** — Created `candidates_horoscope/
  marriage_compatibility/harish_srinidhi/` (basic + deep, both `.md` and `.pdf`; added to the
  Compatibility table in `candidates_horoscope/README.md`). **Srinidhi** — 9 April 1994, 20:47 IST,
  Tiruchirappalli (78.70°E): pillars **甲戌/戊辰/乙丑/丙戌**, Day Master **乙** (Yin Wood), balanced,
  용신 **Fire** (climate-balanced); hour 戌 stable, no boundary caveats. **Harish** — 壬申/乙巳/辛亥/
  己丑, 辛, balanced, 용신 Water. **Composite 61/100 — Mixed.** Positive: the spouse palaces (亥·丑)
  form a partial Metal 삼합 (반합 巳酉丑). Watch: favorable-element cross-supply — Harish's Metal runs
  over for Srinidhi (her challenging element); her chart carries 정재격. No 辛乙 day-stem combination,
  so the match leans on the day-branch tie + element balance. No 용신 overrides used (both resolved
  natively). Engine drafts — review before client delivery. PDFs audit clean (0 citation/draft leaks).

- **2026-09-26 (N-3 ephemeris term table + N-15/N-18/N-19 P3 cleanups, Suite 1104 → 1126)** —
  - **N-3 (P1).** The engine no longer reads sajupy's inaccurate `calendar_data.csv` for the
    month-opener 節氣 instants. `daeun._parse_calendar()` now reads our own
    `src/saju_engine/data/solar_terms.csv`, generated by `tools/generate_solar_terms.py` (PyEphem/
    libastro VSOP87, nutation + aberration; calibrated to published KASI/HKO 2024 values; covers
    1899–2101). sajupy is still used for day pillar / lunar / sewoon per-day pillars. New
    regression tests in `tests/test_solar_terms_table.py`. **Client impact:** only Gurumoorthy's
    대운수 note moved, by one month (77→78 months; Dec 1970→Jan 1971) — a correct precision gain.
  - **N-15 (P2) remainder.** Adding `pillars._term_boundary_info` → `Chart.term_boundary` →
    premium-report "⚠ Solar-term boundary note", so births within 30 min of a 節氣 are flagged as
    lower-confidence (month/year pillar knife-edge), parallel to the existing hour-boundary note.
  - **N-18 (P3) partial.** `saju_age` now compares the 입춘 **instant** (accepts `birth_time_str`;
    `saju_year` accepts `datetime`), so a birth on 입춘 day before the term instant counts in the
    prior saju year. Late-2100 forward start-age no longer silently returns 0 (the N-3 table
    extends to 2101). The 1900-01-01 solar-rollback crash remains open — it originates inside
    sajupy's own table and needs a sajupy-side or pre-1900 guard.
  - **N-19 (P3).** The balanced-fallback least-element tie is now surfaced as
    `strength_assessment["balanced_tie_elements"]` instead of silently resolving to Wood.
  - **N-12 (P2).** `strength._element_counts` now normalises each branch's hidden stems to a fixed
    total qi (`_HIDDEN_BRANCH_QI = 0.6`), so every branch contributes equally — the old fixed role
    weights (0.6/0.3/0.1) made 왕지 (子卯酉) total 0.6 vs 1.0 for three-stem branches. The absolute
    scale is unchanged, so resolved **verdicts, favorable elements, and compat scores are all
    unchanged**; only the displayed Element Balance percentages shift. `element_balance_pct` now
    uses largest-remainder rounding so the percentages sum to exactly 100. Fixture raw-strength
    blocks re-baselined (resolved `fe` unchanged); regression tests in `test_strength.py`.
  - **N-13 (P2).** Added `saju_engine.timezone.derive_utc_offset` (stdlib `zoneinfo`, historical +
    DST aware), a CLI `--timezone` flag, and the intake app now reuses it; removed the intake
    server's implicit `Form(5.5)` default (offset optional; timezone-or-offset required) and set the
    numeric field's step to 0.25. knowledge/09 documents the DST/historical-offset rule.
  - **N-18 (P3).** `compute_pillars` now retries without solar correction when a very
    early-1900 birth's rollback leaves sajupy's table (`solar_correction["range_edge_fallback"]`
    discloses it), so the 1900-01-01 crash is gone.
  - Gates: suite **1136 passed / 9 xfailed / 0 failed**; validation `206 (PASS 202, INTERPRETATION
    4, FAIL 0)`; `ruff check --select F` clean. **All fixable 2026-09-26 audit findings are now
    closed** (only N-21 — `apps/landing-page` source — is not actionable in this repo).

- **2026-09-26 (client-report regen + N-6 research)** — Two follow-ups after the N-5/N-9 work:
  - **Full client-report regeneration** (`tools/regen_client_reports.sh`): all base reports, tier
    files, combined reports, compat pairs, and PDFs regenerated. Verdicts, favorable elements, and
    compat scores confirmed **unchanged** (Harish×Manvitha 64/Mixed, Pawan×Sruthi 50/Mixed);
    four-pillar tables byte-identical. The visible delta is the N-5 strength/arrival lines plus
    accumulated catch-up the prior regen predated (F-4 Hanja first-use, F-13 tier price, N-2 대운수
    precision, F-6 basic-tier compat table, N-10 red-flag order). All PDFs audited clean (0 citation
    /draft leaks). Also fixed the **N-22 regression test**, which asserted a clean `git status` and
    so failed on any legitimate regen of a tracked deliverable — it now compares the tracked PDF's
    bytes before/after instead.
  - **N-6 FIXED (industry-standard whole-chart extremeness gate)** — `docs/research/
    2026-09-26-climate-extremeness-threshold.md`. Per the user's "industry standard" direction, the
    조후 override is now gated on the **whole chart**: `climate.climate_temperature()` computes a
    weighted 한난 score (month/hour weighted higher — 정해 만세력/8-codes; per-character table from
    사주플러스), and two threshold-free tests decide priority — `is_climate_extreme()` (a hot/cold
    month whose whole chart clearly leans the other way withdraws the override) and
    `is_remedy_dominant()` (remedy already the most-abundant element). `FavorableElement` carries
    `climate_temperature`/`climate_extreme`/`remedy_dominant`; knowledge/17 + 09 updated.
    **The element stays month/stem-derived** (궁통보감 — a temperature-derived element would flip
    Harish's validated Water, whose chart scores ≈0/neutral). Corrects both audit examples
    (1963 → Wood, 2010 → Earth) and changes **zero** published deliverables (regen: no markdown
    diff). New fixtures `hot-month-cool-chart` + `dry-remedy-dominant`; re-pointed
    `dry-balanced-synth-v2`; regression tests in `test_climate.py`/`test_yongsin_consistency.py`;
    validation CLI 204→206. Suite 1096 → **1113**. `_NEUTRAL_TEMPERATURE_MARGIN` is an operational
    (not transcribed) constant, flagged `[UNCERTAIN]`.

- **2026-09-26 (N-5 + N-9 doctrinal decisions implemented, Suite 1094 → 1096)** — Two of the three
  [doctrinal] items from the second deep audit were implemented against their recorded user
  decisions:
  - **N-5 — yin Day Master strength.** `strength.py::assess_strength` now scores the month term from
    the **element-relation 득령** signal (`month_season_score`, `_MONTH_BRANCH_SEASON`) instead of the
    12운성 `month_stage_score`, per knowledge/09 Step 2. The 12운성 stage is retained as descriptive
    metadata (`month_stage`/`month_stage_score` still exported). Because the season term's ceiling
    (2.0×1.5=3.0) exceeds the stage term's effective ceiling, the **extreme bands were widened
    4.0→5.0** so `extreme` stays ~3% of charts and every published verdict is unchanged (verified:
    rm/gurumoorthy strong, harish/vishnu/sruthi/pawan/mahesh balanced — all hold). The yin inversion
    is gone: 乙 in 亥 is now resource-supported, 乙 in 午 is not, and 乙/甲 agree by season. Six
    synthetic *climate-merge* fixtures were re-baselined (raw strength/candidate moved; their
    climate-resolved `fe` is unchanged); `damp-strong-synth` was re-pointed to a genuinely strong
    辰-month chart. `prose_fillers._season_signal` now consumes the element-relation score, and the
    Quick-Reference `**Strength:**` reasoning line names the element-relation baseline (with the
    12운성 stage still named descriptively). knowledge/06 + knowledge/09 record the scope.
  - **N-9 — 양인격/건록격 position.** `patterns.py::detect_patterns` now flags the **월령 (month
    branch)** case as the classical 양인격/건록격 grid (`yangin_grid`/`jianlu_grid.present`) and
    surfaces the year/day/hour case as new `yangin_related` / `jianlu_related` blocks (the raw
    `jianlu` block keeps an any-position presence flag).
    knowledge/07 §3–4 rewritten with both patterns + citations (자평진전 월령 격국; 淵海子平/
    명리정종/三命通會). `skeleton.py` renders both distinctly. Regression tests in `test_patterns.py`.
  - Also fixed a **pre-existing ruff F841** in `pillars.py` (orphaned by the N-2 fix: dead
    `eff_date` / `_effective_calendar_date`) that had left the CI `ruff check --select F` gate red.
  - Gates: suite **1096 passed / 9 xfailed / 0 failed**; validation `204 (PASS 200, INTERPRETATION
    4, FAIL 0)`; `ruff check --select F src tools tests` clean. Tracker updated:
    the second-pass audit verification. N-6 (조후 gate threshold) remains
    open pending research. **Client reports were not regenerated** — run `tools/regen_client_reports.sh`
    and diff Quick Reference blocks before re-sending (verdicts/elements are unchanged; the
    reasoning line and pattern lines move).

- **2026-09-26 (second deep engine audit, 11 of 22 fixed + 3 doctrinal decisions recorded, Suite →
  1094)** — A separate session ran a fresh from-scratch audit
  (N-1..N-22) against the same baseline the
  F-1..F-16 pass below started from (so it did not know about those fixes), merged via PR #4.
  Cross-referenced against F-1..F-16 first (N-1/N-9-partial/N-16-partial were already fixed),
  then fixed the rest of the audit's recommended order: **N-2** (절기 override compared solar time
  against civil term instants), **N-4** (current 대운 selected 1.3-2.4y early — 세수 vs.
  floored-elapsed-year mismatch; first fix attempt used the wrong unit conversion, caught by the
  Kim-Dae-jung validation fixture, not the unit test), **N-7** (web compat mislabeled a raw 억부
  pick as reader-confirmed), **N-8** (HTML injection into the Playwright PDF backend via
  `<script>`/`<iframe>` in a client name — `html: False` + JS-disabled Playwright context),
  **N-10** (compat's top red flags were alphabetical, not by severity), **N-11** ("this year" prose
  stated the Gregorian year instead of 사주 year — new `daeun.saju_year()` helper), **N-14** (web
  app overwrote curated client PDFs + blocked the event loop + leaked exceptions), **N-15**
  (partial: 子-hour boundary now disclosed), **N-16** (remaining lint debt + `ruff` added to CI),
  **N-17** (pinned `sajupy==0.2.0` + CSV hash test), **N-20** (duplicate pairwise 삼형), **N-22**
  (tests were overwriting `sruthi-report.pdf` on every run — `build-pdf.sh` gained `SAJU_OUT_DIR`).
  **Three items are marked doctrinal** (need a sourced decision, not a unilateral fix, per Ground
  Rule 1) — investigated each against the actual knowledge files (not the audit's word alone) and
  found genuine internal conflicts, then asked the user: **N-5** (yin DM strength — knowledge/06's
  12운성-stage cheat sheet vs. knowledge/09 Step 2's season/element criterion, which disagree for
  yin stems specifically) → decided: switch to season/element, not yet implemented. **N-6** (조후
  gate — knowledge/17's own cited source says the CHART must be extreme, not just the birth month,
  but no source gives a numeric threshold) → user asked for more research before deciding, open.
  **N-9's 양인격/건록격** month-branch question (자평진전's 월령-based grids vs. the current
  year/day/hour-only rule, uncitable independently) → decided: support both, labeled differently,
  not yet implemented. Full tracker with fix-log commit hashes:
  the verification. **Still open, not started:** N-3
  (ephemeris-accurate 절기 table — the largest remaining item), N-12 (hidden-stem qi weights), N-13
  (IANA timezone/DST redesign), N-15's remainder (절기-proximity disclosure), N-18/N-19 (range-edge
  crashes; N-19's dead `month_season_score` half is now fixed by N-5, its Wood tie-break half
  remains). N-21 (landing-page source) is not fixable from this repo —
  the source simply is not here. Gates: suite **1094 passed / 9 xfailed / 0 failed**; validation
  `204 (PASS 200, INTERPRETATION 4, FAIL 0)`; `ruff check --select F src tools tests` clean and now
  in CI.
- **2026-09-26 (first deep engine audit, 16 of 16 fixed, F-1..F-16)** — Fixed all 16 findings from
  a from-scratch audit pasted directly into the session (not a repo file): F-1 (P0, EoT-only
  midnight day-pillar crossing never recomputed the day pillar), F-2 (천덕귀인 branch-target months
  could never fire), F-3 (`client_intake_app.py` crashed on import, undefined `TOOLS_DIR` — this is
  N-1 above), F-4 (already-parenthesized terms got double-annotated), F-5 (day-branch 육합+육파
  double-dipped), F-6 (compat basic tier leaked deep-tier verdict detail), F-7 (conflicting
  stem/branch daeun-favorability signal defaulted to "favorable" instead of "neutral" — also fixed
  the same bug duplicated in `prose_fillers.period_favorable_status`), F-8 (annual/monthly pillar
  out-of-range fallback ignored 입춀), F-9 (도화스쳐 flag never bucketed into red/yellow), F-10
  (intake forms defaulted UTC offset to India's 5.5), F-11 (`star_anchor` unvalidated by the direct
  API), F-12 (added a `hidden_stems` validation-lookup kind + a cross-timezone daeun fixture), F-13
  (essential tier's stale `$19` price), F-14 (`Chart.to_dict()` duplicate `reference_date` key),
  F-15 (3 duplicate `HANJA_GLOSSARY` keys), F-16 (F821 `Dict`/`List` in `daeun.py`/`sewoon.py`,
  scoped to only the two files the finding named — the wider repo-scale ruff UP006/UP045 sweep was
  judged disproportionate for a P3 item). Suite 1034 → 1068 passed / 9 xfailed. Committed and
  pushed as `3fc4d1f`.
- **2026-09-14 (full-engine architecture audit, documentation-only)** — Wrote
  a design/robustness review of every
  calculation subsystem (distinct from the validation campaign's classical-source-correctness
  check). Full reads of `engine.py`, `daeun.py`, `pillars.py`, `sewoon.py`, `lookup.py`,
  `strength.py`, `chart.py`; targeted reads of `patterns.py`/`stars.py`; compared against two
  external open-source BaZi engines (bazi-analyzer, viet-bazi-engine) found via web search, plus
  Chinese-language sourcing on 대운 starting-age remainder handling. **Key findings:** the engine's
  `starting_age()` floors the day-count remainder to whole years instead of the classical
  months-conversion (undocumented simplification, not a bug); `strength.py`'s `month_season_score`
  is computed but never consumed anywhere (dead field); 13 bare `except Exception:` blocks in the
  presentation layer (`prose_fillers.py` ×6, `compat.py` ×3, `premium_report.py` ×3) swallow errors
  with no logging — the top robustness risk found, since a real bug there would silently degrade
  to a plausible-looking sentence in a paid PDF rather than crash a test; the raw-vs-resolved
  favorable-element two-channel bug (fixed 3× independently this project) is a design smell, not
  three coincidences — recommends renaming the raw field to self-flag direct reads. No code
  changes made; see the audit's §5 priority list for the follow-up work.
- **2026-09-14 (client-visible item 1 fixed + Harish base report regenerated, Suite 883 → 885)** —
  Fixed the last surface of the raw-vs-resolved favorable-element bug class:
  `premium_report.py::_right_now_callout()` and `ctx_favorable_phrase()` (called from
  `_year_one_liner`) now accept an `override` param and read `favorable_element(chart, override)`
  instead of `strength_assessment["candidate_favorable"]`; both call sites thread
  `ctx.favorable_override`. Retired the 2 `xfail(strict=False)` markers in
  `tests/validation/test_val_climate.py` that pinned the bug (they XPASSed). Regenerated
  `candidates_horoscope/reports/harish/harish-report.md` + `.pdf` from scratch (his folder had been
  cleared 2026-09-14 for a from-scratch rebuild) — the "What This Year Means for You" line now
  shows Water natively with no hand patch. PDF audited clean (0 draft markers, 0 citation leaks).
  Harish's `career.md`/`land-workshop-business.md`/`luck-timeline.md` (+ PDFs) are still not
  recreated — flagged as a separate re-authoring task. Gates: suite **885 passed / 10 xfailed / 0
  failed**; validation CLI unchanged `194 (PASS 189, INTERPRETATION 5, FAIL 0)`.
- **2026-09-13 → 2026-09-14 (Engine Validation Campaign — COMPLETE, Suite 649 → 883)** — Independent
  validation of the whole engine against classical sources, run as spec + Plans 1–6
  (design spec + plan,
  3-lookups,4-yongsin,5-climate,6-compat-career}.md` — all six now **deleted**, superseded by this
  entry + `docs/research/2026-09-validation-*.md` + the rendered report). Built a permanent
  validation harness: `src/saju_engine/validation.py` + `tools/run_validation.py` (`python3
  tools/run_validation.py` → renders `tmp/engine-validation-report.md`, **never
  hand-edit it**) + `tests/validation/` fixtures. **Certified 194 checks / 189 PASS / 5
  INTERPRETATION / 0 FAIL across 8 subsystems**: W1 pillars 17, W2 대운·세운 19, W3
  십신/12운성/납음/공망 56, W4 용신 13, W5 조후 30, W6 compat+career 59. Each workstream is backed by
  a research doc citing ≥2 independent Korean sources per rule family
  (`docs/research/2026-09-validation-{yongsin,climate,compat-career}.md`). Validation-only by
  design — defects found were **pinned as tests asserting the current wrong behaviour**, not fixed
  in-campaign (sole exception: the user-ordered 야자시 hour-stem fix in `pillars.py`, part of W1).
  Found **13 loose ends**: 3 client-visible (`premium_report.py` + `report_data.py` reading the raw
  un-resolved 용신 field instead of the display value; 육합 dead code in `compat.py`) and 10 others
  (C9 삼형 chain position, C8 nayin order-dependence, KB12 career tier-pool contradiction, Harish's
  longitude inconsistency, a compat PDF output-path bug, a 辰/戌 climate-model divergence, an
  unsourced climate wording claim, a dead test registry, and two Pawan/Mahesh client reports needing
  regen for the 야자시 fix).
- **2026-09-14 (post-campaign fix wave — user-directed on items 4–13, Suite → 883/12 xfailed)** —
  Nine of the thirteen loose ends are now fixed, each independently re-measured, not transcribed:
  **#5** nayin order-dependence (`compat.py::_canonical_nayin_pair`, male-first canonicalization);
  **#6** career tier pool re-keyed from the Day Master's element family onto the resolved
  용신+희신 families per `knowledge/12-career-and-vocation.md:130-152` (new `_resolved_favorable()`
  helper in `report_data.py`) — **this also fixed client-visible item 2** (career sections were
  reading the raw, un-resolved favorable element); **#8** `md_to_saju_compat_pdf.py --output` path
  bug (missing `mkdir(parents=True)`); **#9** Harish's longitude reconciled to `79.42` at 3 data
  sites (pillar-neutral); **#11** the 辰/戌 climate-model divergence resolved as a **documentation +
  scope** fix (not a model change — see the reusable precedent in Claude's own memory,
  `saju-open-defects-triage.md`); **#12** an unsourced dry/damp climate claim removed from
  `knowledge/17-climate-method.md`; **#13** the dead `_CHECKERS` test registry pruned; and **#4 +
  client-visible item 3 together**, landed as **"(A) + C-none"** on the user's approval — the 육합
  (six-combination) dead-code arity fix in `compat.py::_branch_pair_lookup` (the table is 3-tuples,
  the lookup was testing 2-tuple membership, so 육합 never fired at 4 call sites including the
  spouse-palace bonus), plus documenting the 삼형 branch-punishment chain position as an unsourced
  scope limit rather than reordering it (C9 stays intentionally pinned — branch 삼형 has zero
  citations anywhere in `knowledge/`). Net measured effect: one fixture moved,
  `compat-mahesh-vp` 64/Mixed → 68/Strong; the two published compat anchors (70/Strong, 74/Strong)
  did not move. **Still open:** client-visible **item 1** (`premium_report.py`'s "What This Year
  Means for You" callout, still reading the raw favorable element — see "Active Wishes" below);
  **#7** (regenerating the Pawan/Mahesh/Harish client deliverables affected by the 야자시 fix and
  the 조후 fix — Pawan done, Mahesh and the fixture cascade pending, Harish's base report
  regenerated but its three follow-up files not yet re-authored); and two **product decisions**
  surfaced but not decided — #10 (whether 조후 should outrank 억부 more broadly) and whether
  `climate.py` should expand from its conservative 3-band model to the full 寒暖燥濕 four-way
  궁통보감 reading. Final verified gates: suite **883 passed / 12 xfailed / 0 failed**; CLI
  `194 (PASS 189, INTERPRETATION 5, FAIL 0)` exit 0.
- **2026-09-13 (조후 climate-balance engine fix — plan complete, Suite 627 → 649)** — Triggered by
  the user noticing Harish's 용신 (Fire, from the old "least-represented element" balanced-verdict
  fallback) disagreed with an independent reading (Water). Investigation confirmed the four-pillar
  engine was already correct (verified against `tests/test_textbook_cases.py`'s 9 independently
  published charts); the real gap was that 용신 determination only implemented 抑扶
  (strength-balance) — missing 조후 (climate-balance, 궁통보감/적천수), both cited in CLAUDE.md's
  persona but never wired into `knowledge/09-interpretation-method.md` Step 3 or the code. Full
  design + plan, executed via
  subagent-driven-development (adapted for no-git: no commits/worktrees, reviewers read files
  directly). **What shipped:**
  - New `src/saju_engine/climate.py` (`assess_climate(month_branch)`): a conservative, general
    season-based model — 巳午未 (hot) → Water, 亥子丑 (cold) → Fire, everything else → no override.
    Deliberately NOT a fabricated per-stem-per-month 궁통보감 table (no source text was available).
  - `src/saju_engine/yongsin.py` rewritten to merge climate into `favorable_element()` — see the new
    "Decisions to Remember" #9 above for the exact resolution order.
  - **Mid-implementation discovery (real bug, not in the original plan):** `compat.py` had 4 scoring
    functions reading `strength_assessment["candidate_favorable"]` directly, and its reader-override
    mechanism mutated that same field — both silently broken by the climate merge for any
    balanced+hot/cold chart (Mahesh, this project's own canonical demo compat partner, is one).
    User decided to fix in scope: `compat.py` now routes through `favorable_element()`, and its
    override sets a new `reader_override_favorable` field that `yongsin.py` checks with the same
    outright-wins precedence as an explicit override.
  - `premium_report.py`/`compat_report.py`'s "Supporting Element" display fixed to read the resolved
    `.supporting` value (was reading the stale raw field, would have silently gone out of sync).
  - New `knowledge/17-climate-method.md` + `knowledge/09-interpretation-method.md` Step 3 updated.
  - **Content regenerated:** `harish-report.md`+PDF (Fire/Wood → Water/Metal, fully internally
    consistent), Vishnu Priya's reports (note text only, element already agreed), the Pawan×Sruthi
    compat report (picked up an unrelated latent display-bug fix in the same pass). **Confirmed
    correctly left untouched:** Sruthi/Pawan/Gurumoorthy (reader-argued `--favorable-override`,
    documented `(reader-argued)` in `candidates_horoscope/README.md`, bypasses climate by design),
    Mahesh (fully hand-crafted Weak-DM analysis overriding the engine's own balanced auto-verdict),
    RM (strong verdict + temperate month → climate never even consulted, byte-identical). This
    4-of-6-unaffected finding corrected an earlier over-broad assumption in the plan — always check
    the actual delivered file for a documented override before assuming the raw engine table
    applies.
  - **harish_vinothini compat pair:** its Harish-side favorable element was a stale "Earth" (matched
    neither the old nor new engine value, no documented override anywhere) — corrected to Water.
    Vinothini's real birth data isn't recoverable from the repo, so her side was reconstructed
    pillars-only from her own already-published numbers (verified against a published cross-supply
    percentage before use) to recompute just the 2 favorable-element-dependent sub-systems; composite
    score unchanged. User confirmed (2026-09-13) this reconstruction stands as final — no further
    action pending on this pair.
  - **Follow-up fix applied same day (user-approved):** the pawan_sruthi regen exposed a real
    contradiction — its corrected Supporting Element display (Pawan→Metal, Sruthi→Fire, the
    classically-correct generator) disagreed with Pawan's and Sruthi's own *individual* reports
    (which duplicated favorable==supporting: Water/Water, Earth/Earth). Fixed the individual reports
    to match (5 lines each: Quick Reference, Wealth Pattern, Investment Style Cue, Relocation table
    + orientation line), rebuilt both PDFs.
  - **3 items explicitly flagged, not fixed** (see "Active Wishes / Open Items" above for full
    detail): `premium_report.py`'s "What This Year Means" line reads the wrong raw field;
    Harish's `career.md`/`land-workshop-business.md`/`luck-timeline.md` still argue stale Fire/Wood;
    `md_to_saju_compat_pdf.py`'s default `--output` path bug (workaround: pass `--output` explicitly).
  - **Same-day follow-on:** created a new compat pair, `harish_manvitha` (both tiers, both PDFs;
    added to `candidates_horoscope/README.md`'s index) — Harish × Manvitha (1996-12-03, 21:15,
    Kadapa, Andhra Pradesh), composite 70/100 "Strong". Manvitha's chart (甲, strong, 亥월) is a
    clean fresh validation of the new engine with no overrides on either side.
- **2026-09-08 (candidate regen, starting Harish — DONE)** — Re-validating each candidate's
  pillars against external sources and regenerating reports. **Harish complete:** pillars
  壬申/乙巳/辛亥/己丑 validated (year/month/day confirmed via web + the engine's verified 노무현
  anchor; hour 己丑 correct for 03:10 but solar time 02:57 is ~3–5 min from the 丑→寅 boundary —
  lower-confidence). Longitude corrected 79.32→**79.45°E** (Wikipedia 13.33°N,79.45°E); pillars
  unchanged. Regenerated: `harish-report.md`+PDF (engine deep + plain-language layer); `career.md`
  and `land-workshop-business.md` **re-grounded in `knowledge/12-16`** — the old "not in the
  knowledge base / [UNCERTAIN — extrapolation]" disclaimers on industries and directions replaced
  with real citations + each file's modern-convention caveat. All 4 PDFs clean (no leaks / drafts
  / residual CJK). The regen surfaced & fixed clusters of bugs in `plain_glossary.gloss_first_use`
  (TOC corruption, noun-phrase splits, "Monthly Luck" ⊂ "Monthly Lucky"), `strip_source_citations`
  (line-wrapped `*(see …)*`, short `knowledge/13` form, orphan `§Section`), and the PDF translation
  maps (+20 compound terms). `collect_used_terms` now filters like the glossers. Suite **626**.
  RM demos rebuilt. **Sruthi / Pawan / Gurumoorthy also done** (2026-09-08): pillars
  re-validated (Sruthi 癸酉/甲子/丙寅/己丑, Pawan 辛未/丁酉/丙午/戊子, Gurumoorthy 甲辰/辛未/己巳/戊辰
  — all confirmed via the 노무현 anchor + engine solar-term checks; no hour knife-edge). Base
  reports regenerated as engine `--tier deep` via a new **`--favorable-override`** CLI flag set
  to each reader-argued 용신 (Earth / Water / Metal); hand-written bases kept as
  `{name}-report-legacy.md`. Each `career.md` re-grounded in `knowledge/12-16`. Fixed
  `combine_candidate_report.PROJECT_ROOT` (broke after the src/ migration). Two PDF-render fixes
  landed too: `premium_report` practical-guidance lists now emit `-` bullets (were rendering
  `1. 1. 1.`), and the reportlab inline renderer now handles `_underscore italic_`. Suite **627**.
- **2026-09-08 (Better Reports — plan complete)** — Executed
  Tasks 1–16 of the better-reports plan inline. **Track B:**
  `knowledge/12`–`16` (career / wealth / directions / health / date-selection) now exist,
  are Hanja-compliant, wired into the method / glossary / `CLAUDE.md` / `.claude/commands/saju.md`
  / openwiki, and back the engine's interpretive tables (`report_data.py` `# source:` comments +
  `tests/test_knowledge_grounding.py`). **Track A:** new `src/saju_engine/plain_glossary.py`
  adds a plain-language layer — inline first-use glosses (`Direct Wealth (正財) — steady, earned
  income …`), `> **In plain words:**` section callouts (`prose_fillers.plain_words_*` +
  `prose_scaffold.generate_plain_words`), and a tier-scaled `## What the Terms Mean` appendix
  after the Closing Note — wired into `premium_report.py`, `skeleton.py`, `compat_report.py`.
  `strip_source_citations` eats the leading space; `combine_candidate_report.py` keeps the
  glossary last. RM demo set regenerated leak-free. Suite 594 → **625**; PDF backends + compat
  renderer + landing `npm run build` green.
- **2026-09-07 (landing redesign — shipped)** — Full `apps/landing-page` restructure:
  ~15 sections → ~9, proof-first arc, new Saju visual system (`src/components/viz/`), premium-editorial
  aesthetic, elemental palette tokens, `四柱` watermark. Deletes `WhatIsSaju` / `WhatYouReceive` /
  `TrustClarity` / `ImportantDetails` / `ComparisonTable`.
- **2026-09-07 (repo housekeeping)** — Deleted cruft (`!`, `.coverage`, `.pytest_cache/`,
  `.playwright-mcp/`, stray root PNGs, `rm-deep.md` dup, 12 intake test files). Archived the 3
  audit reports. Deleted 4 completed plan docs (`docs/PLAN.md`,
  `docs/plans/*`, `.claude/plan.md`). `misc/market_research/` kept with a SUPERSEDED banner.
  `.gitignore` extended (node_modules, .next, intake/, .remember/, settings.local.json).
  `.claude/settings.local.json` trimmed from ~250 stale allowlist entries to a compact set.
  `docs/issues_bugs.md` paths `tools/ → src/`. New file map in README + `docs/MEMORY.md`.
- **2026-09-07** — Go-to-market pivot to English-speaking-global / USD (see
  `docs/market-research-2026-09.md`). Fixed 3 client-facing engine defects: G1 reviewer-note leak
  (`premium_report._reviewer_note`, `strip_source_citations`), G2 per-pillar template grammar, G3
  용신 single source of truth (`src/saju_engine/yongsin.py` — `favorable_element()` +
  `FavorableElement` provenance; `generate_premium_report`/`generate_compat_report` consume it, with
  `favorable_override` / `favorable_element_a`/`_b` for reader-argued values). Engine + docs + all
  candidate/landing prices ₹→USD. Landing page (`apps/landing-page`) repositioned; testimonials
  flagged illustrative. Suite 568 → 590; landing build + 107 vitest green. RM + pawan_sruthi demo
  reports/PDFs regenerated leak-free.
- **2026-06-28** — Added Codex support (`saju-reading` and `saju-client-order` skills in `~/.codex/skills/`); the in-repo Codex instructions were removed in the 2026-10-01 cleanup.
- **2026-06-28** — Marriage-compatibility engine (`compat.py`), 16-section report generator (`compat_report.py`), Nayin lookup (`nayin.py`), two-chart intake form + server, standalone compat PDF renderer, and `knowledge/11-gunghap.md` reference completed.
- **2026-06-28** — Repo cleanup: deleted old `docs/`, `ENGINE_SPEC.md`, `ENGINE_RESEARCH.md`. Documentation surface then lived in `README.md`, `CLAUDE.md`, `candidates_horoscope/README.md`, and this `MEMORY.md`.
- **2026-07-06** — Repo-root reorganization: created `docs/` and consolidated project memory, issue tracker, engine audit, plan artifacts, OpenWiki stubs, and Codex instructions there. Deleted stray files/dirs (`:`, `=0.2.0`, `=4.1`, `EOF`, `.coverage`, `.pytest_cache/`) and added coverage/cache artifacts to `.gitignore`.
- **2026-06-27** — Added landing-page tiers (`sample`/`essential`/`deep`) and `/saju-client` slash command.
- **2026-06-22** — Self-service FastAPI calculator, tiered intake form, combined-report combiner, colored Element Balance rendering, citation stripping in PDFs.
- **2026-06-21** — Daily-luck overlay, prose scaffold, premium report generator, major-luck activation overlay, grid/pattern candidates, HTML/Playwright PDF backend.

## Codex-Specific Notes

- Project-level Codex instructions were removed in the 2026-10-01 cleanup.
- Two user-level skills are installed in `~/.codex/skills/` for auto-discovery:
  - `saju-reading` — single-chart reading workflow.
  - `saju-client-order` — client order fulfillment workflow.
- The skills reference the same `docs/MEMORY.md`, `CLAUDE.md`, and `knowledge/` files that the Claude slash commands use.

## How to Use This Memory

At the start of a new session working on this repo, read:
1. `MEMORY.md` (this file) for state, conventions, and quick commands.
2. `CLAUDE.md` for persona, ground rules, and interpretive workflow.
3. `docs/issues_bugs.md` for the engine issue tracker and change log.
