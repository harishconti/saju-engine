# Deployment notes that cannot live in `vercel.json`

Vercel validates `vercel.json` against a **strict** schema: any unknown key — including a `_note` or a
comment — fails the deploy with `should NOT have additional property`. So the reasoning lives here.

## ⚠️ Why the crons are DAILY, not per-minute

`vercel.json` currently has:

```json
"crons": [
  { "path": "/api/cron/dispatch", "schedule": "0 4 * * *" },
  { "path": "/api/cron/cleanup",  "schedule": "0 3 * * *" }
]
```

The design in [05 — Report pipeline](05-report-pipeline.md) §4 calls for **per-minute** dispatching.
This project is on Vercel **Hobby**, which rejects any cron expression that runs more than once per
day, with the deploy failing outright:

```
Hobby accounts are limited to daily cron jobs. This cron expression (* * * * *)
would run more than once per day. Upgrade to the Pro plan to unlock all Cron Jobs features.
```

So generation cannot depend on a per-minute cron. It depends on four triggers instead:

| Trigger | When | Scope |
|---|---|---|
| **Dodo Payments webhook → `after()`** | Immediately after payment, without blocking the provider's 2xx | `processJobById(createdJobId)` — the job this webhook created, not a queue drain (AU-13) |
| **GitHub Actions workflow, every 15 min** (`.github/workflows/sla-sweep.yml`) | `*/15 * * * *` → `POST /api/cron/dispatch` | `runDispatchTick(3)` — the primary scheduled trigger (decision D4) |
| **`POST /api/jobs/kick`** | A client taps "Check for updates" in their dashboard | that caller's own queued jobs only |
| **Daily cron** (`vercel.json`) | 04:00 UTC | `runDispatchTick(3)` — fallback for anything the three above missed |

`after()` from `next/server` is what lets the webhook respond promptly and still generate. The
15-minute dispatch is a GitHub Actions schedule rather than a Vercel cron because Hobby allows only
daily crons — see [05](05-report-pipeline.md) §4.

### Restoring the per-minute dispatcher

On Vercel **Pro**, change the dispatch schedule back and nothing else:

```json
{ "path": "/api/cron/dispatch", "schedule": "* * * * *" }
```

The daily cron then becomes a redundant safety net, which is harmless. No code changes are required —
the dispatcher, the lease/`FOR UPDATE SKIP LOCKED` claim, and the retry ladder are all already correct
and simply run more often.

## Vercel project settings that are NOT in this file

They live in the dashboard / API, and `vercel.json` cannot express them:

| Setting | Value | Why |
|---|---|---|
| Root Directory | **`apps/web`** | It was `apps/landing-page` — the legacy app whose `src/` is not in this repo, so nothing built and the domain served `DEPLOYMENT_NOT_FOUND` |
| Framework Preset | Next.js | |
| Node.js Version | 24.x | |
| Function region | **`sin1`** | Must match the Neon project region `aws-ap-southeast-1` or every query pays a cross-region hop |
| Production Branch | `develop` | from the GitHub link |
| Domains | `cosmicsaju.com` **→ redirects to** `www.cosmicsaju.com` | www is canonical, so `NEXT_PUBLIC_APP_URL` uses the www form |

## Environment variables that are still missing

Set in Vercel, absent in this file by design:

| Variable | Blocks | Status |
|---|---|---|
| `DODO_PAYMENTS_API_KEY` | Payments — orders cannot be paid for | ✅ set in all three scopes (validated against Dodo's API: HTTP 200). **A local `.env` only affects local dev — production reads Vercel's env, and Vercel needs a redeploy to pick up a change** |
| `DODO_PAYMENTS_WEBHOOK_KEY` | Payments — nothing can be fulfilled | ✅ set in all three scopes. It **is** the endpoint's signing secret (`whsec_…`), correctly identified |
| `DODO_PRODUCT_ESSENTIAL` / `_DEEP` / `_COMPAT_BASIC` / `_COMPAT_DEEP` | Payments — `createCheckout()` throws `PRODUCT_NOT_CONFIGURED` | ✅ all four set in every scope. Ids match by **price**, not by name: 1900→`pdt_0NpoArP13BV3e0QbI18TR`, 5500→`pdt_0NpoB67xwOcTjCoc4Dfbb`, 2400→`pdt_0NpoBDXleHNyHVs2KyySb`, 4500→`pdt_0NpoBMQhUhs2VRMsBXtI1`. All four are **`one_time_price`**, so nothing takes money as a subscription that we cannot fulfil |
| `DODO_PAYMENTS_ENVIRONMENT` | — | ✅ `test_mode` (so nothing can be charged for real yet) |
| `TURNSTILE_SECRET_KEY`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY` | Bot protection on the free-sample form (optional; rate limiting still applies) | ⬜ not set |
| `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL`, `ELEVENLABS_MAX_CHUNK_CHARS` | The Deep tier's audio summary | ✅ all four set in every scope (key verified against the live API) |

### Scope gaps found and fixed (2026-10-15)

`DATABASE_URL` and `DIRECT_URL` were each missing from one scope:

| Variable | Was | Now |
|---|---|---|
| `DATABASE_URL` | `development`, `production` — **missing `preview`** | ✅ all three |
| `DIRECT_URL` | `preview`, `production` — **missing `development`** | ✅ all three |

The `preview` gap was the dangerous one: a Preview deployment would have had `DIRECT_URL` but no
`DATABASE_URL`, so every Prisma query would fail at runtime with no obvious cause. The `development`
gap only broke `vercel env pull --environment=development` followed by `prisma migrate`.

**Both are the same production-branch connection strings**, consistent with the single-branch decision
(see [07](07-services-and-integrations.md) §"Branches — production only").

Deliberately **not** set: nothing else. `ADMIN_EMAILS` was missing and has been added — without it
`/admin` is unreachable by anyone, because `requireAdmin()` needs both the DB role *and* an email in
that allowlist.
