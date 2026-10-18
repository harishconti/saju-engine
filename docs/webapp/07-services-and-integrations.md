# 07 — Services and integrations

Every external service this product depends on: what it is for, what to create, what credentials come
out of it, where those credentials go, and what order to do it in.

> This is a checklist, not a secret store. Placeholders: `«ANGLE»` = a value you generate;
> `{...}` = interpolate from a prior step. **No real credential belongs in this file.**

## Stack at a glance

| # | Service | Role | Plan / cost | Status |
|---|---|---|---|---|
| 1 | **Hostinger** | Registrar for `cosmicsaju.com` | ~$12/yr | ✅ owned |
| 1b | **Cloudflare** | **DNS host** for `cosmicsaju.com` (NS delegated from Hostinger) + R2 | free | ✅ active |
| 2 | **Neon** | Postgres (prod + dev branches) + Neon Auth | Free: up to 100 projects, 10 branches/project, 100 CU-hrs/project/mo, ~1 GB storage/project, 5 GB egress, **60,000 Managed Better Auth MAU** | ✅ project `saju` created |
| 3 | **Neon Auth** | Sign-in: Google, email+password, magic link | included in Neon Free | ✅ enabled on `production` |
| 4 | **Google Cloud Console** | OAuth 2.0 client for "Sign in with Google" | free | ⏸️ **deferred to >10 users** (Neon's shared dev key meanwhile) |
| 5 | **Vercel** | Hosting: the webapp (`apps/web`) and the engine (root = repo root, `api/index.py`) | **Pro $20/user/mo** — Hobby crons are once-daily, max 2 | ✅ both live |
| 6 | **Cloudflare R2** | Private PDF storage | Free: 10 GB-mo, 1M Class A, 10M Class B, **$0 egress** | ✅ bucket `saju-engine-dev`, round-trip verified |
| 7 | **Resend** | Transactional email | Free ~3,000 emails/mo | ✅ domain **verified**; `EMAIL_FROM` + `EMAIL_REPLY_TO` set |
| 8 | **Dodo Payments** | Merchant of Record checkout + tax | ⚠️ confirm their current fee schedule — do not assume another provider's | ✅ configured in **test mode**; 4 products wired. ⚠️ live migration outstanding |
| 9 | **Hostinger Email** | The real inbox: `hello@` plus receive-only aliases (`privacy@`, `reports@`, `dmarc@`, `postmaster@`) | bundled with the domain, else ~$1/mo | ✅ **receiving verified** (`delivered`); ⚠️ the 3 DKIM CNAMEs are still to add |
| 10 | **GitHub** | Repo + Actions CI | free | ✅ existing |
| 11 | **Uptime monitoring** | Probe `/api/health` | free tiers exist | ⬜ optional |
| 12 | **Vercel Web Analytics** | Product analytics: page views + funnel events (`snapshot_complete`, `checkout_start`, `purchase`) | included with Vercel; Hobby has an event allowance | 🟡 **code wired 2026-10-17; ⬜ not yet enabled in the Vercel project.** `<Analytics />` is mounted in the root layout and the three events fire from `sample-flow.tsx`, `order-flow.tsx` and the Dodo webhook (server-side, on the paid transition). **Web Analytics must be switched on in the project dashboard**, or the insight script 404s and nothing is recorded — *with no error anywhere*, which is why `src/lib/__tests__/analytics.test.ts` asserts the wiring. Cookieless and same-origin (`/_vercel/insights/script`), so no cookie banner and **no CSP change** needed — `script-src`/`connect-src` already allow `'self'`. It renders `null` on the server and injects its tag client-side, so **it will not appear in the page source** — that is not a fault, and the proof it works is the dashboard |
| 13 | **Cloudflare Turnstile** | Bot protection on the free-sample form | free | 🟡 **built and deployed, running at `TURNSTILE_MODE=log`** — the server verifies and records but never blocks, so the funnel is safe while the widget is validated in a real browser. Was briefly enforcing and took the free sample down (2026-10-16). CSP must allow `challenges.cloudflare.com` **and its subdomains**; the site key needs `--type config` in Vercel. See [09](09-operations.md) |
| 14 | **Password manager** | Source of truth for every secret | 1Password / Bitwarden | ⬜ create |
| 15 | **Ollama Cloud** | Drafts the reader's letter **at review time only** (`tools/suggest_letter.py`). Never in the delivery path: a client request never reaches it, so an outage or a bad generation cannot affect a delivered report. Key `OLLAMA_API_KEY` in `apps/web/.env` (read by the tool from there; not a deployed env var yet). Default model `deepseek-v4.1-flash` — verified against `https://ollama.com/v1/chat/completions` 2026-10-16. `OPENROUTER_API_KEY` is also present in that file, unused. See [05](05-report-pipeline.md) §AI-assisted drafting | ⬜ optional; CLI-only today |

**Steady-state fixed cost: ~$21–25/month** (the drafting step is metered per use — a
1,400-word grounding pack plus a 250-word letter costs well under a cent on
`deepseek-v4.1-flash` at $0.15/$0.60 per million tokens) — inside the "<$50/month" assumption in
[`docs/market-research-2026-09.md`](../market-research-2026-09.md) §7.

---

## Critical path — start these before writing code

Three items have external wait times that block launch regardless of engineering speed:

1. **Dodo Payments onboarding (KYC / business verification).** Any merchant-of-record signup is an
   external review with an unknown timeline, so **start it before the rest of the work**. ⚠️ Confirm
   Dodo's own requirements, approval time, and fee schedule from their dashboard — this document
   deliberately does **not** state them, because the figures that circulated for Lemon Squeezy/Paddle
   (~5% + $0.50, 2–3 day approval, "we don't approve services") belong to *those* providers and must
   not be assumed to apply here.
   **Either way, present the product unambiguously as a digital deliverable** — a PDF the customer
   downloads from the site or receives by email — never as "a personalised consulting service". The
   human review step is an internal quality gate, not a marketed service, and describing it as
   fulfilment-by-hand is exactly what invites an MoR to decline the account.
   **Have a fallback ready:** Paddle, Lemon Squeezy, or manual invoice plus the admin `mark-paid` path.
   The manual path should be built regardless — it covers comps, refund edge cases, and an MoR outage.
2. **Resend domain verification.** Usually ~15 minutes; can take up to 72 hours.
3. **Google OAuth domain verification.** The consent screen can stay in Testing with yourself as a
   test user during development, but public launch wants the app published and the domain verified in
   Google Search Console (DNS TXT record or a hosted verification file).

> The **mailbox** (item 9 in the table above) is a fourth launch blocker, but it is minutes of work
> rather than days. Its only trap is *where* the records go — see §Mailbox records.

---

## Provisioning log

Live state as at **2026-10-15**. Supersedes the recommendations above wherever they conflict.

| Item | State | Value / note |
|---|---|---|
| **Domain** | ✅ live, partially routed | `cosmicsaju.com` registered at Hostinger, **DNS delegated to Cloudflare** (`randy`/`veronica`.ns.cloudflare.com). Nameservers confirmed by lookup. |
| **Neon project** | ✅ created | project **`saju`** |
| **Neon region** | ✅ decided | **`aws-ap-southeast-1` (Singapore)** |
| **Vercel region** | ⚠️ must match | set **`sin1`** on BOTH projects. A cross-region hop to Singapore adds ~100 ms to every query — this is the single most common cause of "the site feels slow" on this stack. |
| **Neon Auth** | ✅ enabled | Base URL (note the `/neondb/auth` path — it is part of the value):<br>`https://ep-raspy-morning-a1xq0p8c.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth`<br>JWKS: `…/neondb/auth/.well-known/jwks.json` |
| **Google OAuth redirect URI** | ⬜ to register | Must be exactly `https://ep-raspy-morning-a1xq0p8c.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth/callback/google` |
| **Database credentials** | ✅ live | Pooled + unpooled fetched via the Neon CLI and written into `apps/web/.env` (gitignored). Hosts match: `ep-raspy-morning-a1xq0p8c{,-pooler}.ap-southeast-1.aws.neon.tech`. `/api/health` reports `db: true`. |
| **Branches** | ✅ **`production` only** | Decision (2026-10-15): **only the `production` branch is used.** `production` = `br-soft-mouse-a1pbgnuq` (default), verified at **14 tables / 13 CHECK constraints**. A `vercel-dev` branch (`br-odd-art-a1xbr1d1`) exists, created by the Neon↔Vercel integration — it has been migrated but is **deliberately unused**; treat it as absent and do not point any env scope at it. Local `apps/web/.env` targets `production`, consistent with that decision. |
| **Initial migration** | ✅ applied | `20261015120000_init` deployed to **both** branches. Verified live: all 13 hand-written `CHECK` constraints present (e.g. inserting a negative `RateLimit.count` is rejected by name), the partial unique index `profile_one_default_per_user` exists with the right predicate, and all 8 enums have the right label sets. |
| **Neon Auth** | ✅ enabled on `production` | `better_auth`, base URL confirmed, JWKS reachable and returning an Ed25519 key. **Trusted domains added:** `https://cosmicsaju.com`, `https://www.cosmicsaju.com`; localhost connections allowed. Previously **none** were configured — which is the exact cause of "OAuth succeeds but the user never arrives". |
| **⚠️ Google provider** | 🕒 **deferred — see below** | Currently Neon's **shared dev-only key**: it works, but the consent screen shows **Neon branding** rather than Cosmic Saju, and Neon explicitly say not to use it in production. Owner decision (2026-10-15): **leave it until the product has more than 10 users.** |
| **⚠️ `vercel-dev` Auth** | ⚠️ unused — ignore | `neon neon-auth status --branch vercel-dev` → "Neon Auth is not configured for this branch". Since the decision is **production-only**, this is fine: point every Vercel scope (Production, Preview, Development) at the `production` branch and this branch stays dormant. |
| **Vercel project** | ✅ configured, ⚠️ not yet serving | One project: **`saju-engine`** (`prj_8hvyP1SO0yvYcMrqks4lYtl6DSUA`, team `harishcontis-projects`). Framework Next.js, Node 24.x, production branch `develop`, linked to the GitHub repo. |
| **Root directory** | ✅ fixed | Was **`apps/landing-page`** — the legacy app whose `src/` is not in this repo, so nothing built and the domain returned `DEPLOYMENT_NOT_FOUND`. Corrected to **`apps/web`** via the API. |
| **Function region** | ✅ fixed | Was defaulting to `iad1`; set to **`sin1`** to match Neon's `aws-ap-southeast-1` (`serverlessFunctionRegion` and `defaultResourceConfig.functionDefaultRegions`, both `sin1`). |
| **Domains** | ✅ attached + verified | `cosmicsaju.com` → **redirects to** `www.cosmicsaju.com`, which is canonical. Plus `saju-engine-three.vercel.app`. Because www is canonical, `NEXT_PUBLIC_APP_URL` is the **www** form. |
| **Env vars** | ✅ **35 set** | Present: DB (pooled + unpooled + `DIRECT_URL`), Neon Auth, R2 (6), engine (2), Resend + `EMAIL_FROM` + **`EMAIL_REPLY_TO`**, app, `ADMIN_EMAILS`, `CRON_SECRET`, Dodo (7), ElevenLabs (4). **Fixed earlier:** `NEXT_PUBLIC_APP_URL` was `http://localhost:3000` (emails would have linked clients to localhost) → `https://www.cosmicsaju.com`; and `ADMIN_EMAILS` was **missing entirely**, which made `/admin` unreachable by anyone. **Added 2026-10-16:** `EMAIL_REPLY_TO`, `NEXT_PUBLIC_CONTACT_EMAIL` (both `hello@cosmicsaju.com`), and the Turnstile trio (`TURNSTILE_MODE`, `TURNSTILE_SECRET_KEY`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`) — the site key needs `--type config` on `vercel env add`, or the CLI refuses the name (see [08](08-deployment.md)). <br>⚠️ Remember **a `NEXT_PUBLIC_*` change needs a redeploy** — the value is inlined at build time. |
| **⚠️ Plan is Hobby** | ⚠️ **blocks per-minute crons** | `vercel deploy` **failed** with *"Hobby accounts are limited to daily cron jobs. This cron expression (`* * * * *`) would run more than once per day."* The dispatcher cron is now daily and generation is webhook-driven — see [08a](08a-vercel-json-notes.md). |
| **🚀 LIVE** | ✅ **serving** | `https://www.cosmicsaju.com` returns **200** with the real landing page (verified 2026-10-15). Apex → 308 → www. `/dashboard` → 307 → `/login` (auth gate working in production). Production `/api/health` → **`{"db":true,"storage":true,"engine":false}`**. Public pages, the demo PDFs, `robots.txt`, and `sitemap.xml` all serve; every protected API route returns **401**. |
| **Deployment protection** | ℹ️ preview-only in practice | The deployment reports `deploymentProtection: ["vercel_authentication"]`, but production is publicly reachable — so protection applies to **preview** deployments, which is the correct default. Worth re-checking the Setting if the site ever starts asking visitors to log in to Vercel. |
| **Env vars still missing** | ⬜ | `DODO_PAYMENTS_API_KEY` (**verified absent from all three scopes**), `DODO_PAYMENTS_WEBHOOK_KEY`, `DODO_PRODUCT_*` (4) — no payment can be taken or fulfilled yet. `DODO_PAYMENTS_ENVIRONMENT=test_mode` is set. `TURNSTILE_*` optional. Also fixed: `DATABASE_URL` was missing from the **preview** scope and `DIRECT_URL` from **development** — both now cover all three (see [08a](08a-vercel-json-notes.md)). |
| **Vercel CLI token** | ⚠️ expired | `~/.local/share/com.vercel.cli/auth.json` holds a token that Vercel now rejects (`"The specified token is not valid"`), so project inspection via CLI/API is blocked. Run `npx vercel login` to refresh. |
| **Cloudflare R2** | ✅ wired + verified | Bucket **`saju-engine-dev`**, account `8b70484a615d5759f6929ef7e4f15f01`. Credentials reused from the `construction-log` project's Cloudflare account (the existing R2 API token can see both buckets — confirmed by `HeadBucket`). Round-trip proven: presigned PUT → `HeadObject` verify → presigned GET → delete, plus an unsigned-access probe confirming the bucket is **private**. Re-runnable with `RUN_R2_TESTS=1 npx vitest run src/lib/__tests__/r2.integration.test.ts`. |
| **R2 buckets** | ✅ **single bucket by decision** | Owner decision (2026-10-15): **one bucket, `saju-engine-dev`** (`https://8b70484a615d5759f6929ef7e4f15f01.r2.cloudflarestorage.com/saju-engine-dev`). No separate prod bucket. `R2_BUCKET=saju-engine-dev` in every Vercel scope, matching what was already set. The "prod bucket" line below is therefore **closed, not outstanding**. |
| **Dedicated R2 token** | ⬜ recommended | The reused token is scoped broadly (it reaches the construction-ledger bucket too). Create a token scoped to the saju buckets only, so a leak in one project cannot touch the other. |
| **Resend** | ✅ **verified** | `cosmicsaju.com` status **verified**, region `ap-northeast-1`. All three records confirmed verified **by Resend's own API**: DKIM `resend._domainkey` and SPF on both `send` and `rsend` (`send.forge.rmta.net`, `rsend-apne1.forge.rmta.net`). ⚠️ No `_dmarc` TXT record exists — recommended for deliverability, not required for verification. |
| **Hostinger Email (mailbox)** | ✅ **published and receiving** (DKIM outstanding) | One mailbox **`hello@cosmicsaju.com`** with receive-only aliases **`privacy@`, `reports@`, `dmarc@`, `postmaster@`** (owner, 2026-10-16). Records published **in Cloudflare** — not at the registrar, because a mail host cannot write to a zone it does not host; until that was done the apex had no MX/TXT and the mailbox received nothing (see §Mailbox records). Now live and verified: `MX → mx1/mx2.hostinger.com` (5/10), one apex SPF `v=spf1 include:_spf.mail.hostinger.com ~all`, `_dmarc v=DMARC1; p=none`. **A real send to `hello@` reports `last_event: delivered`.** ⚠️ **Missing:** the three DKIM CNAMEs (`hostingermail-a/b/c._domainkey`), which is why Hostinger still warns about spam. |
| **Dodo Payments** | 🟡 **keys live, products missing**, replaces Lemon Squeezy | Owner decision (2026-10-15): **Dodo Payments** is the merchant of record, not Lemon Squeezy. Code is migrated (`src/lib/dodo.ts`, `/api/webhooks/dodo`, `DODO_*` env names, Standard Webhooks verification + tests). Verified against Dodo's own API: the API key authenticates (`GET /products` → 200) and a webhook endpoint is configured — `ep_3KjzkirfY0iCcf2AeBt9vK46irc` → `https://www.cosmicsaju.com/api/webhooks/dodo`, subscribing to `payment.succeeded`, `payment.failed`, `payment.cancelled`, `refund.succeeded`. `DODO_PAYMENTS_API_KEY`, `DODO_PAYMENTS_WEBHOOK_KEY` and `DODO_PAYMENTS_ENVIRONMENT` are set in all three Vercel scopes. **Four products created and wired** (test mode), matched to tiers by price rather than by name; every one verified as `price_detail.type = one_time_price`. Payment is therefore fully configured. Verified by replaying the **exact** payload `createCheckout()` sends against Dodo's API: HTTP 200 with a real `checkout_url` — a session was created and left to expire, no payment made. |
| **apps/web** | ✅ **live; the whole pipeline runs** | `npm run build`, `tsc --noEmit` and `eslint` all clean; **69 Vitest cases pass / 4 skipped** (the R2 integration suite, which needs `RUN_R2_TESTS=1`). The engine is deployed, so `/api/sample` returns a real PDF and order → job → review → delivery (PDF **and** MP3) all work end to end. **112 Vitest cases pass** (4 skipped — the R2 integration suite needs `RUN_R2_TESTS=1`). CI now gates it: the `webapp` job (lint, types, tests, build) and the `ui` job (`tools/audit-ui.py --strict` — axe, overflow, targets, both colour schemes). Remaining gap: no Playwright end-to-end tier ([13](13-launch-audit.md) B5). |

**Consequence of the Singapore region for the engine:** the engine project (`saju-report-engine`) must
be deployed with its Vercel function region set to `sin1` as well, or every generation call pays a
trans-Pacific hop.

---

### R2 endpoint form — a common mistake

The Cloudflare dashboard shows a bucket's **S3 API** URL as:

```
https://8b70484a615d5759f6929ef7e4f15f01.r2.cloudflarestorage.com/saju-engine-dev
                                                       └──── bucket name appended ────┘
```

**That whole string is not `R2_ENDPOINT`.** Split it:

| Env var | Value |
|---|---|
| `R2_ENDPOINT` | `https://8b70484a615d5759f6929ef7e4f15f01.r2.cloudflarestorage.com` — **origin only** |
| `R2_BUCKET` | `saju-engine-dev` |

Leaving the bucket on the endpoint makes the S3 client treat it as part of the request path, so keys
end up double-prefixed (`saju-engine-dev/reports/…`). It can appear to work, which is exactly what
makes it expensive to debug later. `r2.ts` builds keys as `reports/{userId}/{orderId}/{reportId}.pdf`
and never names the bucket.

### Reusing credentials across projects on the same Cloudflare account

`construction-log/.env` and this project share one Cloudflare account, so the R2 credentials transfer:

| Variable | Reusable? | Note |
|---|---|---|
| `R2_ACCOUNT_ID` | ✅ | same account — `8b70484a615d5759f6929ef7e4f15f01` |
| `R2_ENDPOINT` | ✅ | same value (origin only, and it is account-scoped, not bucket-scoped) |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | ✅ but prefer a new token | The existing token can reach **both** projects' buckets — verified with `HeadBucket`. Scope a new token to the saju buckets so one leak cannot reach the other project. |
| `R2_REGION` | ✅ | `auto` |
| `DATABASE_URL` / `DIRECT_URL` | ❌ | different Neon project (that one is `us-east-1`; this one is `ap-southeast-1`) |
| `NEON_AUTH_BASE_URL` / `NEON_AUTH_COOKIE_SECRET` | ❌ | different Neon Auth instance |
| `JWT_SECRET` / `MAINTENANCE_SECRET` / `BACKUP_PASSPHRASE` | ❌ | per-application secrets; never share |

**Latency note:** the `construction-log` database sits in `us-east-1` while the saju project is in
`ap-southeast-1`. Sharing the R2 account does not couple them — R2 has no region affinity with the
database — but it does mean the two projects' Vercel function regions differ (`iad1` vs `sin1`), which
is correct and intentional.


### 🕒 Deferred until we have more than 10 users

**Owner decision, 2026-10-15.** Recorded here so it is a deliberate deferral with a trigger, not an
oversight discovered later.

| Item | Now | Do it when | Why the delay is safe |
|---|---|---|---|
| **Own Google OAuth client** | Neon's **shared** dev key. Sign-in works; the consent screen shows **Neon branding** and Neon say not to use it in production | **> 10 users** | Nothing breaks at low volume. The cost of waiting is cosmetic (a "Neon" name on the consent screen); the cost of doing it early is a Google Cloud project + consent-screen review for zero users. Replace with `neon neon-auth oauth-provider update`, redirect URI `https://ep-raspy-morning-a1xq0p8c.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth/callback/google` |

**Trigger checklist when it comes due:** create the Google Cloud OAuth client → register that redirect
URI → update the Neon Auth provider with the new client id/secret → sign in on the production domain →
confirm the consent screen shows Cosmic Saju, not Neon → update this table.



### Neon CLI — the fastest way to do all of this

The `neon` CLI is installed and authenticated with an OAuth session on this machine, and it can do
more than fetch connection strings — including the Auth configuration that otherwise means clicking
around the console.

```bash
# Identity + the two orgs (the saju project lives in the first)
neon me
neon api /users/me/organizations

# Find the project and its branches
neon projects list --org-id org-curly-sky-98590399
#   sparkling-mouse-75978774  saju  aws-ap-southeast-1
neon branches list --project-id sparkling-mouse-75978774
#   [default] production  br-soft-mouse-a1pbgnuq
#   vercel-dev            br-odd-art-a1xbr1d1

# Connection strings — write them straight into .env, never into a chat
neon connection-string production --project-id sparkling-mouse-75978774 --pooled   # → DATABASE_URL
neon connection-string production --project-id sparkling-mouse-75978774            # → DIRECT_URL
neon connection-string vercel-dev --project-id sparkling-mouse-75978774            # → Preview/Local

# Auth state and configuration
neon neon-auth status              --project-id … --branch production
neon neon-auth domain list         --project-id … --branch production
neon neon-auth domain add https://cosmicsaju.com --project-id … --branch production   # full URI required
neon neon-auth domain allow-localhost enable --project-id … --branch production
neon neon-auth oauth-provider list --project-id … --branch production

# Migrate every branch that will serve traffic
DIRECT_URL=«unpooled» DATABASE_URL=«pooled» npx prisma migrate deploy
```

Two notes that otherwise cost time:

- `domain add` **requires a scheme**: `https://cosmicsaju.com`, not `cosmicsaju.com`.
- Migrations are **per branch**. A Neon branch is a copy-on-write snapshot taken when it was created,
  so a branch made *before* a migration does not have it — `vercel-dev` was exactly this case.

## DNS master table

### ⚠️ Your DNS is on Cloudflare, not Hostinger

Your domain is **registered** at Hostinger, but its **DNS is hosted at Cloudflare**. Verified live
(2026-10-16):

```
NS     randy.ns.cloudflare.com.  veronica.ns.cloudflare.com.     ← Cloudflare nameservers (authoritative)
SOA    randy.ns.cloudflare.com. dns.cloudflare.com. …
A      216.198.79.1                                              ← Vercel's anycast IP, proxy OFF
server: Vercel                                                   ← no cf-ray: Cloudflare is not proxying
```

**Every DNS record must be added in the Cloudflare dashboard.** Registration and DNS hosting are
separate roles, so editing Hostinger's DNS zone achieves nothing.

This is not hypothetical — it is what happened to the mailbox. A mail host cannot publish records into
a zone it does not host, so its panel tells you to *"log in to Cloudflare … and add the records below"*.
Until those records existed in the **Cloudflare** zone, the apex had **no MX and no TXT at all**: the
mailbox existed, the panel showed it as configured, and mail went nowhere. The same rule applied to
Resend, which is why *its* records were published in Cloudflare and verified.

### Cloudflare proxy in front of Vercel — decided: **DNS only (grey cloud)**

| Setup | Records in Cloudflare | Trade-off |
|---|---|---|
| **DNS only (grey cloud)** — ✅ **in use** | A/CNAME with the proxy **off** | ✅ **Best-supported with Vercel.** Vercel terminates TLS and issues its own certificate; its edge network is the CDN. No SSL handshake surprises, and `x-vercel-id` reflects the real client. Confirmed by the response carrying `server: Vercel` and **no** `cf-ray` |
| **Proxied (orange cloud)** | A/CNAME proxied | Works, and gives Cloudflare's WAF/bot rules. But Vercel's certificate issuance can fail, redirect loops appear if the SSL mode is wrong, and client IPs become Cloudflare's. Requires **SSL/TLS = Full (strict)** — never Flexible, which proxies HTTPS to Vercel over HTTP and will loop |

The proxy was previously on; it was switched to **DNS-only** (A re-pointed at Vercel's `216.198.79.1`)
during the 2026-10-16 session, and the site is unaffected — `https://www.cosmicsaju.com` still returns
**200**, apex → **308** → www.

**This is also the safer state for mail.** A grey-cloud A record cannot interfere with the apex MX
records the mailbox needs, and Vercel no longer has to route through a proxy for TLS. If you ever
switch back to proxied, set **SSL/TLS = Full (strict)** and turn off "Always Use HTTPS" so it does not
fight the Vercel apex→www redirect.

Our own CSP and security headers are set in `next.config.ts` and pass through fine either way.

### Site records (Vercel) — add these in Cloudflare

Copy the exact values from the domain card in **Vercel → Project → Settings → Domains**; do not retype
them.

| Type | Name | Value | Proxy | Purpose |
|---|---|---|---|---|
| A | `@` (apex) | `76.76.21.21` (Vercel's default; **use the domain card's value**) | 🟠 or ⚪ | apex → Vercel |
| CNAME | `www` | the domain card's target (e.g. `«HASH».vercel-dns-017.com`) | 🟠 or ⚪ | www → Vercel |
| CAA *(optional)* | `@` | `0 issue "letsencrypt.org"` | — | only if you set CAA records |

Pick **one primary** (`cosmicsaju.com` reads better for a report brand) and redirect the other. With
the proxy **off**, Vercel issues the certificate automatically once DNS resolves.

### Email delivery records (Resend)

⚠️ **The gotcha everyone hits:** Resend's MX is on the **`send` subdomain**, not the apex. It therefore
does **not** conflict with the apex MX records a mailbox provider needs. Adding a mailbox later will
not break Resend, and vice versa.

| Type | Name / Host | Value | Priority | Purpose |
|---|---|---|---|---|
| MX | `send` | `feedback-smtp.«REGION».amazonses.com` | 10 | Return-path; bounces/complaints come back to Resend as events |
| TXT | `send` | `v=spf1 include:amazonses.com ~all` | — | SPF — authorises the SES infrastructure Resend sends through |
| TXT | `resend._domainkey` | `p=«LONG_DKIM_PUBLIC_KEY»` | — | DKIM. Resend may instead give **three CNAMEs** — use whichever it shows |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@cosmicsaju.com` | — | DMARC. Start at `p=none`, tighten later |
| CNAME *(optional)* | `link` | Resend-provided target | — | Click/open tracking on your own domain |

**Resend region** changes only the MX value. Options: `us-east-1`, `eu-west-1`, `sa-east-1`,
`ap-northeast-1`. Default to `us-east-1` for a US-skewed global audience; `ap-northeast-1` is closest
to India if your own inbox latency matters.

### Mailbox records (required — the published contact and every reply)

**One mailbox, several aliases**, all landing in the same inbox (owner, 2026-10-16). Chosen over a
provider-per-address setup so that an address already hardcoded in the app starts working without a
code change, and so `privacy@` stays honest about *where* data requests go.

| Address | Type | Purpose | Must receive | Must send |
|---|---|---|---|---|
| **`hello@cosmicsaju.com`** | **the mailbox** | humans: support, refunds, "where's my report?" | ✅ | ✅ — manual replies |
| `privacy@cosmicsaju.com` | alias | data-protection / DSAR requests only (GDPR, DPDP) | ✅ | nice-to-have |
| `reports@cosmicsaju.com` | alias | the transactional `From` identity; where replies to app mail land | ✅ | Resend sends it, not the mailbox |
| `dmarc@cosmicsaju.com` | alias | DMARC aggregate reports (`rua=`) | ✅ | — |
| `postmaster@cosmicsaju.com` | alias | RFC 2142 convention; deliverability sanity | ✅ | — |

**Names are role-based, not person-based**, so they survive delegating to a VA. There is deliberately
**no `no-reply@`**: three app messages invite a reply (*"just reply to this email"*, and two dashboard
states saying *"reply to your order email"*).

#### ✅ Published in Cloudflare — receiving verified working

Records **must live in the Cloudflare zone**, because the nameservers are delegated to Cloudflare while
Hostinger is only the *registrar* — two different roles.

⚠️ **The one real trap is *where* the records go.** A mail host cannot write to a DNS zone it does not
host, so its panel instructs you to add the records in Cloudflare yourself. Until that was done the apex
had **no MX and no TXT at all** — the mailbox existed and received nothing. Everything below is the state
after publishing them in Cloudflare.

| Record | Name | Value | Status |
|---|---|---|---|
| MX | `@` | `mx1.hostinger.com` (priority **5**), `mx2.hostinger.com` (priority **10**) | ✅ live |
| TXT (SPF) | `@` | `v=spf1 include:_spf.mail.hostinger.com ~all` | ✅ live — exactly one SPF at the apex |
| TXT (DMARC) | `_dmarc` | `v=DMARC1; p=none` | ✅ live — **add `rua=mailto:dmarc@cosmicsaju.com`** so aggregate reports arrive at the alias |
| CNAME (DKIM) | `hostingermail-a._domainkey` | `hostingermail-a.dkim.mail.hostinger.com` | ✅ resolves — key **valid** |
| CNAME (DKIM) | `hostingermail-b._domainkey` | `hostingermail-b.dkim.mail.hostinger.com` | ⚠️ resolves — key **empty** at Hostinger |
| CNAME (DKIM) | `hostingermail-c._domainkey` | `hostingermail-c.dkim.mail.hostinger.com` | ⚠️ resolves — key **empty** at Hostinger |

**Receiving is proven, not assumed.** With MX live, a real message sent from the app's own `EMAIL_FROM`
to `hello@cosmicsaju.com` reported **`last_event: delivered`** from Resend's API, carrying
`reply_to: ["hello@cosmicsaju.com"]` — the mailbox receives, and a client's reply is routed correctly.

**DKIM**, which Hostinger's panel flags (*"incorrect, conflicting or pointing to external provider"*), with
two cautions when adding the records:

- **Set them to DNS only (grey cloud).** A proxied (orange) CNAME is answered by Cloudflare instead of the
  mail host, and DKIM then fails to validate — silently.
- **Type the Name as the label only** (`hostingermail-a._domainkey`). Cloudflare appends the zone, so
  pasting the full value produces a junk name like `hostingermail-c.dkim.mail.hostinger.com.cosmicsaju.com`
  — which is exactly what happened once, and has since been corrected.

**Measured state (2026-10-16, DNS-over-HTTPS):**

| Name | Resolves to | Key served at the target | Verdict |
|---|---|---|---|
| `hostingermail-a._domainkey` | `hostingermail-a.dkim.mail.hostinger.com` | `v=DKIM1;k=rsa;p=MIIBIjANBgkq…` | ✅ **valid** |
| `hostingermail-b._domainkey` | `hostingermail-b.dkim.mail.hostinger.com` | `v=DKIM1;p=` — **empty** | ❌ Hostinger must issue the key |
| `hostingermail-c._domainkey` | `hostingermail-c.dkim.mail.hostinger.com` | `v=DKIM1;p=` — **empty** | ❌ Hostinger must issue the key |

**Our side of the DKIM setup is complete and correct** — all three CNAMEs resolve, and the mistyped `c`
record has been fixed. What remains is a **Hostinger-side gap**: selectors `b` and `c` serve **empty** keys
(`v=DKIM1;p=`, no key material), so they can never validate regardless of DNS. Only `a` carries a real key.

**Does it matter? Probably not — and one test settles it.** What counts is which selector the mail host
actually *signs* with, and DNS cannot tell us that. Send a message **from `hello@` in Hostinger webmail** to
a Gmail address, open it → *Show original*, and read `dkim=` and `header.s=`:

- `dkim=pass … header.s=hostingermail-a` → the empty `b`/`c` are simply unused and the panel's warning is
  cosmetic. Nothing to do.
- `dkim=fail … header.s=hostingermail-b` (or `-c`) → those messages carry a *failing* signature, which is
  worse than none; ask Hostinger to issue the keys.

⚠️ **Even in the failing case, delivery is not at risk.** `_dmarc` is `p=none`, and DMARC also passes on
**SPF alignment alone** — the envelope sender is `…@cosmicsaju.com` and the apex SPF authorises Hostinger —
so a DKIM failure cannot cause rejection here. Fix it for reputation hygiene, not deliverability.

⚠️ **Scope — this only affects mail sent by hand from Hostinger webmail.** The app's mail goes out through
**Resend**, which signs with `resend._domainkey` (verified), so reports, audio, and reject emails are
unaffected. *"Pointing to external provider"* is expected and informational: the DNS zone is Cloudflare's,
not Hostinger's.

**Why these cannot collide with anything else.** A CNAME may not share a name with *any* other record
type — which is why the three selectors must never also carry a TXT — but each name is distinct from every
other record in the zone: Resend's CNAMEs sit at `send` and `rsend`, its DKIM is a TXT at
`resend._domainkey`, and `www` is its own CNAME. The coexistence rules that matter:

1. **MX does not conflict with Resend.** Resend's records are on **`send`** and **`rsend`** (plus
   `resend._domainkey`), so the apex is free for the mailbox. Adding a mailbox later cannot break
   transactional sending, and vice versa — this is exactly why the Resend setup put them there.
2. **SPF: exactly one `v=spf1` per name, merged not duplicated.** The apex has exactly one. If Resend is
   ever moved to the apex, *merge* the `include:` lists
   (`v=spf1 include:_spf.mail.hostinger.com include:amazonses.com ~all`) rather than publishing a second
   record — two SPF records invalidate both.
3. **A CNAME name must otherwise be empty.** Never add a TXT at `hostingermail-a._domainkey` afterwards.

⚠️ **Neon Auth's magic-link mail bypasses our `Reply-To`.** Neon Auth sends sign-in mail from its own
SMTP settings, not through `apps/web/src/lib/email.ts`, so it does not inherit `EMAIL_REPLY_TO`. With
the `reports@` alias now real, a reply to a magic-link email lands in the shared inbox rather than
bouncing — but if you want those to be answered as `hello@` specifically, set the From address in
Neon's SMTP configuration rather than relying on our code.

#### Verify

```bash
dnsq cosmicsaju.com MX                                  # mx1/mx2.hostinger.com, priority 5 and 10
dnsq cosmicsaju.com TXT                                 # exactly ONE v=spf1
dnsq _dmarc.cosmicsaju.com TXT                          # v=DMARC1; p=none
dnsq hostingermail-a._domainkey.cosmicsaju.com TXT       # ← TXT chases the CNAME and shows the KEY
dnsq hostingermail-b._domainkey.cosmicsaju.com TXT
dnsq hostingermail-c._domainkey.cosmicsaju.com TXT
```

⚠️ **Query `TXT`, not `CNAME`, for the DKIM selectors.** A name that *is* a CNAME resolves its TXT to the
target's contents, so `TXT` both proves the CNAME exists **and** shows the key — including an empty
`v=DKIM1;p=`, which is how the broken `b`/`c` keys above were found. Cloudflare's DoH answers `CNAME`
with `(none)` in this case (it chases the chain); Google's DoH (`dns.google/resolve?type=CNAME`) does
answer it. A CNAME may not share its name with any other record type, so never add a TXT at these names.

Then send a real message to `hello@` and to `privacy@` from an outside account and confirm both land in
the inbox — that is a stronger check than any DNS lookup, because it exercises the whole path.
Propagation is usually minutes; allow an hour before debugging.

### Optional: a stable engine subdomain

| Type | Name | Value | Purpose |
|---|---|---|---|
| CNAME | `engine` | `«engine-project».vercel.app` | `ENGINE_URL=https://engine.cosmicsaju.com` — stable across project renames |

### Verify

`dig` is **not installed on this machine** — use DNS-over-HTTPS, which also works from anywhere:

```bash
dnsq() { curl -s -H 'accept: application/dns-json' \
  "https://cloudflare-dns.com/dns-query?name=$1&type=$2" \
  | python3 -c "import sys,json;print('; '.join(a['data'] for a in json.load(sys.stdin).get('Answer',[])) or '(none)')"; }

dnsq cosmicsaju.com A
dnsq cosmicsaju.com NS
dnsq www.cosmicsaju.com CNAME
dnsq send.cosmicsaju.com MX
dnsq send.cosmicsaju.com TXT
dnsq resend._domainkey.cosmicsaju.com TXT
dnsq _dmarc.cosmicsaju.com TXT
```

Resend also ships a `dns.email` checker — use it before clicking Verify.

**Current state of the zone (verified 2026-10-16):** NS is Cloudflare and the apex A record points at
Vercel **with the proxy off**. Resend's records (`send` + `rsend` CNAMEs, `resend._domainkey` TXT) are
present and verified, so outbound app mail works. The **mailbox is live**: apex MX → `mx1`/`mx2.hostinger.com`,
one apex SPF, and `_dmarc` in place — a real send to `hello@` is reported **`delivered`**. The only gap is
the **three DKIM CNAMEs** — see §Mailbox records.

---

## Neon

### Project and region

Project **`saju`**. Pick the region to sit as close as possible to the Vercel function region — a
cross-region hop adds ~100 ms to every query, and it is the single most common cause of "the site
feels slow" on this stack.

| Neon region | Pair with Vercel region | When |
|---|---|---|
| **`aws-ap-southeast-1`** | **`sin1`** | ✅ **Chosen for this project** — closest to the owner and to South/SE-Asian traffic |
| `aws-us-east-1` | `iad1` | Would suit a US-skewed audience |
| `aws-eu-central-1` | `fra1` | If the EU becomes primary |

### Branches — production only

**Decision (2026-10-15): one branch, `production`.** All three Vercel scopes point at it.

| Branch | Purpose | Used by |
|---|---|---|
| `production` (`br-soft-mouse-a1pbgnuq`) | The only branch | Vercel Production, Preview, and local `.env` |
| `vercel-dev` (`br-odd-art-a1xbr1d1`) | Created by the Neon↔Vercel integration; **unused, treat as absent** | nothing |

The normal advice is a dev branch for Preview so Preview can never write to production data. That is
the right pattern once there are real users; for a pre-launch single-operator build it doubles the
migration surface for no benefit. **Revisit before launch** — this is the first thing to split when a
second person touches the database.

Migrating a branch is per-branch, so if you do split later, run `prisma migrate deploy` against the
new branch too (a Neon branch is a copy-on-write snapshot of its parent at creation time).

### Connection strings — you need both

| Env var | Which string | Why |
|---|---|---|
| `DATABASE_URL` | **Pooled** (`…-pooler…`) | Runtime traffic. Serverless functions open and drop connections constantly |
| `DIRECT_URL` | **Direct / unpooled** | Prisma Migrate only. Migrations cannot run through a pooler |

### Neon Auth

Enable **Neon Auth** on the project. It provisions Managed Better Auth and gives a **base URL that
includes the path**, e.g. `https://ep-xxx.neonauth.«region».aws.neon.tech/neondb/auth`.

| Env var | Source | Notes |
|---|---|---|
| `NEON_AUTH_BASE_URL` | Neon console | **Include the full path** (`/neondb/auth`). This string also determines the Google redirect URI |
| `NEON_AUTH_COOKIE_SECRET` | you generate | `openssl rand -base64 32` — **≥32 chars or startup throws** |

Console configuration:

- **Providers:** Google, email/password, magic link, email verification.
- **Trusted origins:** `https://cosmicsaju.com`, `https://www.cosmicsaju.com` (**add both — `www`
  is not covered by the apex**), `http://localhost:3000`, and the preview URL pattern. Managed Better
  Auth only redirects to trusted domains; a missing origin shows up as "OAuth succeeds but the user
  never arrives".
- **Email:** dev uses Neon's shared SMTP; **production should use Resend**.
- **Sign-up:** open.

Full wiring detail in [04 — Auth and roles](04-auth-and-roles.md).

### Free-plan realities

- **60,000 Managed Better Auth MAU** — auth is effectively free at this scale.
- **100 CU-hours per project/month.** With scale-to-zero (compute suspends after ~5 min idle) at the
  0.25 CU default, that is roughly 400 active hours. Leave autoscale at the default; **do not set
  always-on**.
- **6-hour point-in-time restore** on Free. Adequate for beta.
- Compute suspends when idle → the **first query after idle is slow**. Keep the health-check interval
  sane or accept occasional cold queries.
- ⚠️ Server Components reading the session/DB need `export const dynamic = 'force-dynamic'`.

---

## Google Cloud Console (for "Sign in with Google")

1. **APIs & Services → OAuth consent screen:** External, app name "Cosmic Saju", support email,
   developer email, links to the privacy policy and terms (these are required fields).
2. **Credentials → Create OAuth client ID → Web application.**
   - **Authorised JavaScript origins:** `https://cosmicsaju.com`, `https://www.cosmicsaju.com`,
     `http://localhost:3000`
   - **Authorised redirect URI:** `{NEON_AUTH_BASE_URL}/callback/google`
     ⚠️ **This exact form** — `…/neondb/auth/callback/google`. Not the site's `/login`, not the
     `callbackURL` passed to `signIn.social()`. This is the #1 cause of `redirect_uri_mismatch`.
     **Register one per environment** — the `dev` and `main` branches have different Auth base URLs.
3. Copy **Client ID** / **Client Secret** into Neon Auth's Google provider config.
4. Keep the consent screen in **Testing** with your own account while developing; publish before
   launch and verify the domain in Search Console.

---

## Vercel

### Two projects, one repository

| | Project #1 | Project #2 |
|---|---|---|
| Name | `saju-engine` | `saju-report-engine` |
| Root directory | `apps/web` | **repository root** (function at `api/index.py`) |
| Framework | Next.js | Other (Python) |
| Build | `prisma generate && next build` | auto — installed from `pyproject.toml`, which `installCommand` cannot override |
| Runtime config | default | `maxDuration: 300`, `excludeFiles` for `tests/ candidates_horoscope/ misc/ tools/ docs/ apps/ tmp/` |
| Domains | `cosmicsaju.com` + `www` | `engine.cosmicsaju.com` (optional) |
| Database access | yes | **none, by design** |

Do not merge them: mixing a Python runtime into a Next.js project makes Next's output tracing bundle
`.next`/`public` into the Python function, which is the classic 250 MB failure. See
[01 — Architecture](01-architecture.md).

### Limits that shape the design

| Limit | Value | Consequence |
|---|---|---|
| Python bundle | **500 MB** uncompressed (5 GB with large functions) | Engine closure ~130 MB — comfortable |
| Function payload | **4.5 MB** | Never stream PDFs through a hop; presign R2 instead |
| Duration | 300 s default; 800 s Pro; 1800 s beta | A 1.5 s render needs none of it; the dispatcher needs headroom |
| **Cron, Hobby** | **once/day, max 2** | ⛔ blocks the per-minute dispatcher → **Pro required** |

### Env scopes

Set values **per scope** (Production / Preview / Development). Preview points at the Neon `dev` branch
and the R2 `-dev` bucket. `NEXT_PUBLIC_*` is public — treat it as public.

The complete variable inventory is in [08 — Deployment](08-deployment.md).

---

## Cloudflare R2

### Buckets

| Bucket | Use |
|---|---|
| **`saju-engine-dev`** | ✅ exists — Local + Preview (**and Production until a prod bucket is created**) |
| *(none)* | **Single bucket by decision (2026-10-15)** — no separate production bucket. See the provisioning log. |

Both **private**. Do not enable the public `r2.dev` URL; do not attach a custom domain. Downloads go
through short-lived presigned URLs issued only after an ownership check.

**Key scheme** and lifetime rules: [05 — Report pipeline](05-report-pipeline.md) §3.

### Credentials

Create an **R2 API token** (Account → R2 → Manage API tokens) scoped to both buckets with **Object
Read & Write**:

| Env var | Value |
|---|---|
| `R2_ACCOUNT_ID` | Cloudflare account id |
| `R2_ACCESS_KEY_ID` | from the token |
| `R2_SECRET_ACCESS_KEY` | from the token (shown once) |
| `R2_BUCKET` | `saju-engine-dev` — the only bucket, in every scope |
| `R2_REGION` | `auto` |
| `R2_ENDPOINT` | `https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com` |

**The engine also reads `R2_ENDPOINT`** — not for credentials (it has none) but as its
**upload-target allowlist**: a presigned URL may only point at that host. `SAJU_UPLOAD_BUCKET`
(optional) additionally pins the path to `/<bucket>/`, and `SAJU_MAX_REQUEST_BYTES` caps the body
(default 2 MB). Set `R2_ENDPOINT` on the `saju-report-engine` project too, or `/generate` fails
closed with `503 UPLOAD_HOSTS_UNCONFIGURED`. See [14 — Security](14-security.md) §3–4.

### CORS

Needed so a browser can PUT an object straight to R2 — which the manual audio upload requires, because a
~10 MB MP3 cannot pass through a Vercel function body. **Applied 2026-10-16.** ⚠️ It had been documented
here for months without ever being set: a preflight against the bucket returned **403**, so any browser
PUT would have failed. Verify with a real preflight, not by reading this table:

```bash
curl -s -i -X OPTIONS "$R2_ENDPOINT/$R2_BUCKET/probe.txt" \
  -H "Origin: https://www.cosmicsaju.com" -H "Access-Control-Request-Method: PUT" \
  -H "Access-Control-Request-Headers: content-type" | head -6
# expect 204 + Access-Control-Allow-Origin / -Methods / -Headers. Allow ~a minute to propagate.
```

- **Allowed origins:** `https://cosmicsaju.com`, `https://www.cosmicsaju.com`, `http://localhost:3000`,
  Vercel preview URLs
- **Allowed methods:** `GET`, `PUT`, `HEAD`
- **Allowed headers:** `Content-Type`
- **Expose headers:** `ETag`

### CSP

```
img-src     'self' data: blob: https://*.r2.cloudflarestorage.com;
connect-src 'self' https://*.r2.cloudflarestorage.com;
```

### Free-tier reality

10 GB-month storage / 1M Class A writes / 10M Class B reads, **$0 egress at any volume**. A deep PDF
is ~140 KB, so 10 GB is ~70,000 reports before storage is billable, and downloads never cost anything.

---

## Resend

1. Create the account → **Domains → Add domain → `cosmicsaju.com`**, choosing the region.
2. Publish the generated MX/TXT/CNAME records **in the Cloudflare dashboard** (copy-paste). Currently the zone has **no MX and no TXT records at all**, so nothing is verified yet.
3. **Verify DNS Records** (~15 min; up to 72 h).
4. Create an **API key** with sending permission → `RESEND_API_KEY`.
5. Choose the From address: **`reports@cosmicsaju.com`** — a *sending* role identity, with replies routed
   to the human inbox by **`EMAIL_REPLY_TO=hello@cosmicsaju.com`** (defaulted inside `sendEmail()`, so no
   sender can forget it). Set both. See §Mailbox records for why a reply must have somewhere to land.
6. Add a **webhook** for `email.bounced` / `email.complained` → `/api/webhooks/resend`, so a bad
   address surfaces in the `Delivery` table instead of silently failing.
7. Enable DMARC reporting and check the first reports after launch.

**Volume:** one email per delivered report. At 25 reports/week that is ~110 emails/month.

---

## Dodo Payments

Chosen over Lemon Squeezy / Paddle as the merchant of record. Dodo is the MoR, so we never see card
data, and the webhook is the only source of truth for "paid".

### Credentials and setup

| Step | Where | Env var |
|---|---|---|
| API key | Dashboard → **Developer → API Keys** | `DODO_PAYMENTS_API_KEY` |
| Webhook signing secret | Dashboard → **Developer → Webhooks** → your endpoint → Overview | `DODO_PAYMENTS_WEBHOOK_KEY` |
| Environment | — | `DODO_PAYMENTS_ENVIRONMENT` = `test_mode` \| `live_mode` |

`test_mode` talks to `https://test.dodopayments.com`, `live_mode` to `https://live.dodopayments.com`.
The base URL is derived from this variable in `src/lib/dodo.ts` — there is no separate `..._RETURN_URL`
to keep in sync, because the checkout `return_url` comes from `NEXT_PUBLIC_APP_URL`.

**Product ids**, one product per tier (Dashboard → Products → copy the `pdt_…` id):

| Product | Tier | Engine call | Price | Env |
|---|---|---|---|---|
| Essential Report | `essential` | `SINGLE` | $19 | `DODO_PRODUCT_ESSENTIAL` |
| Deep Destiny Report | `deep` | `SINGLE` | $55 | `DODO_PRODUCT_DEEP` |
| Compatibility Snapshot | `compat-basic` | `COMPAT` `basic` | $24 | `DODO_PRODUCT_COMPAT_BASIC` |
| Deep Compatibility | `compat-deep` | `COMPAT` `deep` | $45 | `DODO_PRODUCT_COMPAT_DEEP` |
| The Hook | — | `sample` | free | **not** a Dodo product |

> ✅ **Price drift settled (2026-10-16).** The Essential tier is **$19** everywhere: the Dodo product
> ($19), the webapp tier map, the landing page, and — the part that was actually broken — the engine's own
> `TIER_CONFIG` cover, which still printed **"$9 intro → $19"** on every *delivered* Essential report as
> well as in `demo-rm-essential.pdf`. That launch promo is retired. A Dodo product carries exactly **one**
> price, and [02 — Data model](02-data-model.md)'s tier map is the single place to encode it. If an intro
> price is ever wanted again it must be a genuinely separate product with a launch window, not a footnote
> in prose.

> **Cosmic Companion ($9/mo) is deliberately not offered in v1.** The engine supports the tier; the
> billing does not.
>
> Engine legacy aliases (`spark`, `reading`, `fullmap`) exist internally but must never appear in the
> store or the UI.

### Checkout

`POST {base}/checkouts` with `product_cart`, `customer`, `metadata`, `return_url` → `checkout_url`.
Each session is **single-use and expires after 24 hours**, so a new one is created for every attempt
and every customer. The important field is `metadata`:

```jsonc
{ "product_cart": [{ "product_id": "pdt_…", "quantity": 1 }],
  "customer": { "email": "…" },
  "metadata": { "order_id": "cuid…", "user_id": "…", "tier": "deep", "kind": "SINGLE" },
  "return_url": "https://www.cosmicsaju.com/dashboard/orders?paid=1" }
```

**`metadata.order_id` is how the webhook finds our order again.** Without it a payment cannot be
matched to a purchase — it would take money and fulfil nothing.

### Webhooks

Endpoint: **`https://www.cosmicsaju.com/api/webhooks/dodo`**. Subscribe to at least:

| Event | What we do |
|---|---|
| `payment.succeeded` | **The only thing that fulfils.** Marks the order paid, creates the generation job, audits |
| `payment.failed` / `payment.cancelled` | Audit only — the order stays unpaid so the customer can retry |
| `refund.succeeded` | Order → `REFUNDED` |

**Fulfil on the webhook, never on the browser redirect.** The redirect is missed whenever the customer
closes the tab; the webhook is retried until acknowledged. Our handler also dispatches generation via
`after()`, so the provider still gets its 2xx promptly.

Signature scheme: **Standard Webhooks** — HMAC-SHA256 over `{webhook-id}.{webhook-timestamp}.{raw body}`,
base64-encoded, secret base64-decoded after stripping an optional `whsec_`. The `webhook-signature`
header may carry several space-separated `v1,<sig>` candidates. Verified in
`src/lib/webhook-signature.ts` with a 5-minute tolerance, and unit-tested (tampered body, wrong secret,
replay outside tolerance, missing headers, wrong id).

⚠️ **`dodo wh trigger` sends UNSIGNED payloads**, so our verifier correctly rejects them with 401. To
exercise the handler locally, sign the body with the exported `signStandardWebhook()` helper and POST it
with the three `webhook-*` headers — that path is covered by tests.

### Testing and going live

1. **In test mode first.** A test purchase must create **exactly one** `Job` even when the same webhook
   is delivered several times — that is the `WebhookEvent` unique constraint doing its job.
2. Verify a forged signature is rejected (401) and a duplicate `webhook-id` returns 200 immediately.
3. Switch `DODO_PAYMENTS_ENVIRONMENT` to `live_mode` and re-verify with a real low-value purchase.
4. **Payouts:** complete KYC from India. The MoR handles US sales tax and EU VAT — the whole reason for
   choosing one.

### Fallback

If Dodo stalls or rejects: **Paddle** (equivalent economics) or Lemon Squeezy, or ship with the admin
`mark-paid` path and invoice manually. The manual path should be built regardless — comps, refunds, and
support all need it, and it is what makes an MoR outage survivable.

---

## Deliberately not used

Recorded so nobody adds them later "for safety":

| Not needed | Why |
|---|---|
| Upstash Redis / any external rate limiter | Rate limits are a Postgres table (D9). Also drops the old landing page's `@upstash/redis` dependency |
| Sentry / Datadog (initially) | Vercel captures unhandled errors and logs. Add only when debugging pain justifies it |
| Cloudflare proxy/CDN in front of Vercel | Vercel's edge network *is* the CDN; a second proxy complicates TLS and client IPs |
| Google Maps / Mapbox geocoding | Coordinates resolve once at profile creation from a bundled city table — no runtime vendor |
| Cloudflare Pages | Vercel owns hosting |
| A message queue / broker | The `Job` table plus cron is sufficient at this scale |
| A `no-reply@` / `noreply@` address | Several messages explicitly invite a reply ("just reply to this email"). A no-reply address would ask for something it then blocks, and it is exactly the habit an MoR reviewer probes when checking support reachability |

---

## Cost summary

| Service | Monthly | Notes |
|---|---|---|
| Vercel Pro | $20 | Required for the per-minute dispatcher cron |
| Neon Free | $0 | 100 CU-hrs/project is ample with scale-to-zero |
| Neon Auth | $0 | 60k MAU included |
| Cloudflare R2 | $0 | 10 GB free; egress always free |
| Resend | $0 | ~3,000 emails/mo free |
| Google OAuth · Turnstile | $0 | |
| Domain | ~$1 | ~$12/yr amortised |
| Hostinger Email | $0–1 | bundled with the domain, else ~$1/mo. One mailbox + aliases; **no new vendor** |
| **Total fixed** | **~$21/month** | |
| Dodo Payments | ⚠️ **confirm** their current fee schedule | per sale only; deliberately not stated here until verified |

## Open decisions

| # | Decision | Options | Recommendation |
|---|---|---|---|
| 1 | ~~Neon region~~ | — | ✅ **decided: `ap-southeast-1` (Singapore) → Vercel `sin1`** |
| 2 | ~~Mailbox provider~~ | — | ✅ **decided (2026-10-16): Hostinger email** — one mailbox `hello@cosmicsaju.com` + receive-only aliases. ⚠️ Records still to be published in **Cloudflare**, not Hostinger (see §Mailbox records) |
| 3 | Resend region | `us-east-1` / `ap-northeast-1` | `us-east-1` |
| 4 | Bot protection | Turnstile / Vercel WAF / none | Turnstile |
| 5 | Analytics | Vercel Web Analytics / Plausible / Umami | Vercel Web Analytics to start |
| 6 | Engine subdomain | `engine.cosmicsaju.com` / plain `*.vercel.app` | Optional; nicer stable URL |
| 7 | Leave Neon Free? | Free / Launch (~$5 min) | Stay Free until revenue |

## Sources

- Vercel apex `A 76.76.21.21` and "CNAME cannot be used at the zone apex":
  <https://vercel.com/kb/guide/a-record-and-caa-with-vercel>,
  <https://vercel.com/docs/domains/working-with-dns>
- Vercel function size (250 MB; **500 MB for Python**), 4.5 MB payload, limits:
  <https://vercel.com/docs/functions/limitations>
- Vercel extended durations / large functions:
  <https://vercel.com/changelog/vercel-functions-can-now-run-up-to-30-minutes>
- Neon plans (branches, CU-hours, storage, 60k Managed Better Auth MAU):
  <https://neon.com/docs/introduction/plans>, <https://neon.com/pricing>
- Neon Auth env vars, cookie secret ≥32 chars:
  <https://neon.com/docs/auth/reference/nextjs-server>
- Neon Auth `{NEON_AUTH_BASE_URL}/callback/{provider}` and trusted-origin pitfalls:
  <https://neon.com/docs/auth/troubleshooting>
- Resend domain records: <https://resend.com/docs/add-a-domain>,
  <https://resend.com/docs/dashboard/domains/dmarc>
- Cloudflare R2 pricing and free tier: <https://developers.cloudflare.com/r2/pricing>
- Dodo Payments store activation and approval scope:
  <https://docs.dodopayments.com/developer-resources/checkout-session>,
  <https://docs.dodopayments.com/developer-resources/webhooks>
