# 08 — Deployment

Two Vercel projects, one repository, one domain.

## What each project uploads

Upload weight is billed — Functions Storage, per retained deployment — so the root `.vercelignore`
excludes what **neither** build needs at runtime or at build time: `tests/` (the engine's suite and its
manseryeok PNG evidence), `candidates_horoscope/`, `docs/`, `tools/`, `.github/`. `src/`, `api/`,
`apps/`, `knowledge/` and the packaging files stay.

⚠️ **That file governs both uploads, even though the webapp's project root is `apps/web`.** A first
attempt added `apps/` — reasoning that it belonged to the root-rooted engine project — and broke the
webapp deployment: its upload lost `apps/web/package.json` and `npm install` exited
`254 [BUILD_UTILS_SPAWN_254]`. The rule that follows from that: **only list what neither build
needs.** If in doubt, add nothing — a failed production deploy costs far more than the megabytes.

The dominant cost is not the repository at all — it is the Python dependency closure (~125 MB per
engine deployment, mostly pandas and numpy via `sajupy`). See
[09-operations.md](09-operations.md) § Functions Storage is filling, and `tools/prune_deployments.py`.

## Repo layout

```
saju-engine/
├── apps/
│   ├── landing-page/               # ⚠️ LEGACY — config only, src/ is not in this repo (A1)
│   └── web/                        # ← Vercel project #1 (Root Directory = apps/web)
│       ├── src/app/
│       │   ├── (public)/           # /, /sample, /pricing, /privacy, /terms, /refund-policy
│       │   ├── dashboard/          # authenticated shell
│       │   ├── admin/              # review console
│       │   ├── login/  auth/complete/
│       │   └── api/                # route handlers (see 03-api-spec.md)
│       ├── src/lib/                # prisma, auth/, r2, engine, queue, email, tiers, roles, audit, ratelimit, validation/
│       ├── src/components/         # ui/ primitives + viz/ charts + feature views
│       ├── src/proxy.ts            # Next 16 middleware (auth gate)
│       ├── prisma/{schema.prisma,migrations/,seed.ts}
│       ├── next.config.ts
│       └── vercel.json
├── api/
│   └── index.py                    # ← Vercel project #2: the FastAPI app
├── vercel.json                     # project #2 config (framework: null, entrypoint, excludeFiles)
├── requirements.txt                # project #2 deps — `fastapi` must stay a MAIN dependency (05 §1.2)
├── src/saju_engine/                # imported by the engine service, unchanged
├── src/saju_html/                  # imported by the engine service, unchanged
└── docs/webapp/                    # this documentation set
```

## Project settings

### Project #1 — `saju-engine` (the webapp)

| Setting | Value |
|---|---|
| Framework preset | Next.js |
| Root directory | `apps/web` |
| Install command | `npm install` |
| Build command | `prisma generate && next build` |
| Output directory | `.next` |
| Node | **24.x** — must agree in three places: the Vercel dashboard, `engines.node` in `apps/web/package.json`, and CI. Vercel honours `engines.node` for the **function runtime**, so a stale value silently pins the runtime while the build uses the dashboard's version. That happened here: `builds.config.nodeVersion = 24.x` but `builds.output.lambda.runtime = nodejs22.x`. Verify with `vercel inspect --json <url>` |
| Region | **`sin1`** — matches the Neon project region `aws-ap-southeast-1`. A mismatch adds ~100 ms to every query. |
| Domains | `cosmicsaju.com` (redirects) + `www.cosmicsaju.com` (**canonical**) |
| DNS | **Cloudflare** (nameservers delegated from Hostinger), A record **DNS-only** — grey cloud, so `server: Vercel`. The apex is therefore free for the mailbox's MX records; Resend's MX lives on the `send` subdomain and does not conflict |

`npm install` runs at the repository root but the build runs in `apps/web`; keep the app's
`package.json` self-contained (no workspace hoisting assumptions) so this stays true.

### Project #2 — `saju-report-engine`

| Setting | Value |
|---|---|
| Framework preset | Other |
| **Root directory** | **repository root** — *not* `services/report-engine/`. Vercel bundles only files under the Root Directory, so a subdirectory root would hide `src/` from the function. The repo root also has no `package.json`, so Vercel does not misdetect Next.js |
| Entrypoint | `[tool.vercel] entrypoint = "api.index:app"` in `pyproject.toml`. **Without it** the file gets legacy `/api` file-function mode and only the exact path routes |
| Build command | (auto — Python, installed from `pyproject.toml`; `installCommand` is ignored) |
| Region | same as project #1 |
| Domain | `engine.cosmicsaju.com` (optional but recommended for a stable `ENGINE_URL`) |

```json
// vercel.json (repository root — the deployed values)
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "fastapi",
  "functions": {
    "api/index.py": {
      "maxDuration": 300,
      "excludeFiles": "{tests/**,candidates_horoscope/**,misc/**,tools/**,docs/**,apps/**,tmp/**,**/__pycache__/**,**/*.pyc,**/*.pdf,.git/**,.next/**}"
    }
  }
}
```

`excludeFiles` is not cosmetic: without it the Python function can absorb test fixtures, the
candidate report library, and PDFs — hundreds of megabytes of payload for a service that needs
`saju_engine` + `saju_html` and nothing else. Verify the reported bundle size after the first deploy.

## Environment variables

### `apps/web`

```bash
# ── Neon Postgres ──
DATABASE_URL=postgresql://…-pooler…/neondb?sslmode=require     # pooled, runtime
DIRECT_URL=postgresql://…/neondb?sslmode=require                # direct, migrations

# ── Neon Auth ──
NEON_AUTH_BASE_URL=https://ep-xxx.neonauth.«region».aws.neon.tech/neondb/auth
NEON_AUTH_COOKIE_SECRET=«openssl rand -base64 32»               # ≥32 chars

# ── Cloudflare R2 ──
R2_ACCOUNT_ID=«account_id»
R2_ACCESS_KEY_ID=«from R2 API token»
R2_SECRET_ACCESS_KEY=«from R2 API token»
R2_BUCKET=saju-engine-dev
R2_REGION=auto
R2_ENDPOINT=https://«account_id».r2.cloudflarestorage.com

# ── Report engine ──
ENGINE_URL=https://engine.cosmicsaju.com
ENGINE_SERVICE_TOKEN=«openssl rand -base64 32»

# ── Email ──
RESEND_API_KEY=re_«…»
EMAIL_FROM=Cosmic Saju <reports@cosmicsaju.com>          # the sending identity
EMAIL_REPLY_TO=hello@cosmicsaju.com                      # where client replies land (the real inbox)

# ── Payments ──
DODO_PAYMENTS_API_KEY=«…»
DODO_PAYMENTS_ENVIRONMENT=«…»
DODO_PAYMENTS_WEBHOOK_KEY=«…»
DODO_PRODUCT_ESSENTIAL=«variant_id»
DODO_PRODUCT_DEEP=«variant_id»
DODO_PRODUCT_COMPAT_BASIC=«variant_id»
DODO_PRODUCT_COMPAT_DEEP=«variant_id»

# ── App ──
NEXT_PUBLIC_APP_URL=https://www.cosmicsaju.com          # www is canonical; the apex 308s to it
NEXT_PUBLIC_LEGAL_CONTACT_EMAIL=privacy@cosmicsaju.com  # data-protection requests only
NEXT_PUBLIC_CONTACT_EMAIL=hello@cosmicsaju.com          # general contact: footer + support prompts
ADMIN_EMAILS=«your login email»
CRON_SECRET=«openssl rand -base64 32»    # Vercel Cron sends this as a bearer token

# ── Optional ──
TURNSTILE_MODE=off                                        # off (default) | log (verify, never block) | enforce
TURNSTILE_SECRET_KEY=«from the Turnstile widget»            # server verification; only bites in `enforce`

# ⚠️ Adding the site key needs an explicit type, or Vercel's CLI refuses it:
#   vercel env add NEXT_PUBLIC_TURNSTILE_SITE_KEY production --type config
# Without `--type` you get `public_prefix_requires_type`, because `NEXT_PUBLIC_` exposes the value and
# the name looks credential-ish. The site key IS public — it is rendered into the HTML — but the guard
# means a silent failure: the variable never lands, the widget never renders, and (in `enforce`) the
# funnel refuses every visitor. This happened on 2026-10-16 and was masked by the uploaded `.env`.
NEXT_PUBLIC_TURNSTILE_SITE_KEY=«from the Turnstile widget»  # rendered by the sample form; inlined at BUILD time,
                                                            # so changing it needs a redeploy
```

#### Mail

`EMAIL_FROM` is the *sending* identity (`reports@cosmicsaju.com`); **`EMAIL_REPLY_TO` is the real inbox**
(`hello@cosmicsaju.com`). Set both: several messages invite a reply (*"just reply to this email"*), and
`reports@` is a role address nobody sits in. `sendEmail()` defaults the `Reply-To` so a new sender
cannot forget it.

The mailbox's **records must be published in Cloudflare** — a mail host cannot write to a zone it does
not host, and that trap caught us once: the mailbox existed and received nothing while its panel showed
it as configured. Live now: apex MX, exactly one apex SPF, and `_dmarc`; **receiving is verified**
(`delivered`). Resend sits on `send`/`rsend`, so the apex is free for the mailbox. ⚠️ The three **DKIM
CNAMEs** (`hostingermail-a/b/c._domainkey`, **DNS only**) are still missing. Full detail:
[07](07-services-and-integrations.md) §Mailbox records.

### The engine project (`saju-report-engine`, root = repository root)

```bash
ENGINE_SERVICE_TOKEN=«same value as the webapp»
SAJU_PDF_BACKEND=reportlab
SAJU_FONT_DIR=«usually omit»   # E1 auto-resolves <package>/saju_html/fonts, which inside the
                               # function is /var/task/src/saju_html/fonts (verified: /health
                               # reports `fontsDir`). The system path does not exist there
```

**Deliberately absent:** no database URL, no R2 keys, no Resend key, no payment keys. See
[05](05-report-pipeline.md) §1.

### Scope discipline

**Production branch everywhere** (decision 2026-10-15: single branch).

| Scope | Database | R2 bucket | Engine |
|---|---|---|---|
| Production | Neon `production` | `saju-engine-dev` (the only bucket) | `saju-report-engine` (root = repo root) |
| Preview | Neon `production` | `saju-engine-dev` | `saju-report-engine` |
| Development | Neon `production` | `saju-engine-dev` | local (`http://localhost:8000`) |

⚠️ The usual rule is that Preview must never receive production credentials — that is the single most
common way a small team corrupts production data. It is relaxed here **deliberately and temporarily**
because there is one operator and no users yet. When a second person gets DB access, split off a dev
branch and move Preview to it.

## Crons

```json
// apps/web/vercel.json
{
  "crons": [
    { "path": "/api/cron/dispatch", "schedule": "0 4 * * *" },
    { "path": "/api/cron/cleanup",  "schedule": "0 3 * * *" }
  ]
}
```

| Cron | Schedule | Note |
|---|---|---|
| `dispatch` | **daily, 04:00 UTC** | **Hobby allows only once-daily crons** (max 2) — this is why generation is **webhook-driven** and the cron is only a safety net. The original per-minute expression made `vercel deploy` fail outright; see [08a](08a-vercel-json-notes.md) |
| `cleanup` | daily, 03:00 UTC | any plan |

Vercel authenticates cron invocations with `Authorization: Bearer $CRON_SECRET`. Our handlers accept
either that or `x-maintenance-secret`, and both are compared in constant time. With neither secret
configured the endpoint 401s — the correct failure direction.

⚠️ **Vercel cron schedules run in UTC.** A "3 AM" schedule is 3 AM UTC, not local. Pick the hour
deliberately (03:00 UTC is 08:30 IST — a fine time for a sweep).

## Build behaviour

Two constraints that will bite during the first deploy:

1. **The build must succeed without runtime secrets.** CI and Vercel's build step run with no
   `NEON_AUTH_*`, no `DATABASE_URL` in some configurations, and no payment keys. Everything that
   reads a secret must do so lazily — at request time, not module scope. The auth client's Proxy
   pattern ([04](04-auth-and-roles.md)) exists for exactly this reason.
2. **`prisma generate` must run before `next build`.** Prisma's client is generated code; without it
   the build fails on a missing `@prisma/client`. Hence the build command
   `prisma generate && next build`.

## Deploying

```bash
# from the REPOSITORY ROOT (the project's Root Directory is apps/web, so the CLI resolves it there —
# deploying from inside apps/web would look for apps/web/web)
npx vercel deploy --project saju-engine            # preview
npx vercel deploy --prod --project saju-engine     # production
```

Two gotchas:

- **The first deployment is auto-promoted to production** and the CLI says so explicitly. Every
  deployment after that is a **preview** unless you pass `--prod`.
- **`vercel.json` is schema-validated strictly.** An unknown key — including a `_note` or a comment —
  fails the whole deploy with `should NOT have additional property`. Reasoning about that file
  therefore lives in [08a](08a-vercel-json-notes.md).

Production deployments trigger on pushes to the `develop` branch (the project's Production Branch from
the GitHub link).

## CI/CD

`.github/workflows/ci.yml` — **two jobs**, triggered on push and PR to **`develop`** and `main`, with
`concurrency` cancelling superseded runs.

> ⚠️ `develop` is the production branch. The workflow originally triggered on **`main` only**, so it
> never ran for real work and every "CI covers X" claim was wrong in practice. Fixed 2026-10-16.

| Job | Steps |
|---|---|
| **ui** — the `tools/audit-ui.py` gate | builds, serves on `localhost:3000`, installs a Playwright browser, then runs the audit with `--strict` — axe (§ [12](12-testing.md)), horizontal overflow, hydration warnings and sub-44 px controls, at 390/768/1440 in **both colour schemes**. Build, serve and audit are one step, because a background server started in one step is not guaranteed to survive into the next |
| **engine** — Python 3.10 and 3.12 | `pip install -e ".[dev,html,web]"` plus `-r requirements.txt` → Playwright **chromium** → `ruff check --select F src tools tests api` → `pytest -q` → `tools/run_validation.py` (the cited-fixture gate) |
| **webapp** — Node 24.x | `npm ci` → **`prisma generate`** → `lint` → `typecheck` → `vitest run` → `next build` |

**`prisma generate` must run before the tests.** `src/lib/__tests__/email-reply-to.test.ts` imports the
real `email.ts`, which imports the real Prisma singleton — without a generated client that import throws
before a single assertion runs.

Chromium is required for the engine job because the **HTML/Playwright backend is the default PDF
renderer**, so its tests need a browser. The 3.11 matrix entry was dropped: ~4 extra minutes for no
signal between the declared floor (3.10) and production (3.12).

**CI needs no real secrets.** Every client is lazy, so placeholders suffice even for `prisma generate`
and `next build`:

```yaml
env:
  DATABASE_URL: postgresql://ci:ci@localhost:5432/ci
  DIRECT_URL: postgresql://ci:ci@localhost:5432/ci
  DATABASE_URL_UNPOOLED: postgresql://ci:ci@localhost:5432/ci
  NEXT_PUBLIC_APP_URL: https://www.cosmicsaju.com
```

Verified locally by running all five webapp steps with exactly those placeholders and nothing else —
`lint`, `typecheck`, 112 tests and `next build` all pass.

### ⚠️ `vercel deploy` uploads the working tree — keep `.env` out of it

A CLI deploy sends the repository as it sits on disk, and Next loads `.env` at **build and runtime**.
Without a `/.vercelignore`, `apps/web/.env` therefore travelled with every deployment and *silently
overrode the project's environment variables*: a deleted `TURNSTILE_SECRET_KEY` kept producing live
`403`s, a deleted `NEXT_PUBLIC_*` kept being inlined, and every secret in that file shipped inside the
bundle. The repository root now has a `.vercelignore` that excludes `.env*`.

**Rule: Vercel's env vars are the only source of truth for a deployed build.** `.env` is for running
locally. If an env change appears to do nothing, check for an uploaded `.env` before anything else.

CI does **not** run migrations (no database service), and the **Playwright public tier does not exist
yet** — that is the outstanding piece, see [13](13-launch-audit.md) §B5 and [12](12-testing.md).

## Release process

```
1.  npm run lint && npm run typecheck && npm test && npm run build     # both projects
2.  python -m pytest tests/ -q                                        # if the engine changed
3.  npm run db:backup                                                 # before any migration
4.  npx prisma migrate status && npx prisma migrate deploy
5.  deploy: merge to the production branch → Vercel builds and promotes
6.  smoke: /api/health → db, storage, engine all green
7.  verify one real order end to end if payment code changed
```

**Order matters:** migrate *before* deploy when a migration is additive (new nullable column), and
deploy *before* migrate when the code must tolerate both shapes. A migration that drops or renames a
column in use is a breaking change and needs the two-step treatment (add → backfill → switch → drop
in a later release).

## Rollback

| Layer | Mechanism | Reversible? |
|---|---|---|
| Webapp | Vercel → promote a previous deployment | Yes, instantly |
| Engine service | Same, independently | Yes, instantly |
| Database | Neon point-in-time restore (6 h on Free) or a forward-fix migration | **Forward-only in practice** — plan migrations to be additive |

A database rollback is not instant and loses data written since. Design migrations so the previous
code still works against the new schema; then a webapp rollback does not need a database rollback.

## Pre-launch verification

- [ ] DNS checks in [07](07-services-and-integrations.md) pass (`dig` is not installed here — use the
      DoH helper in that page); the Vercel domain card shows **Valid Configuration** and SSL is issued
- [ ] `https://cosmicsaju.com` and `https://www.cosmicsaju.com` both load the app — **not** Vercel's
      `404 DEPLOYMENT_NOT_FOUND` (the current state: the domain is attached to a project with no
      production build yet)
- [ ] Cloudflare **SSL/TLS mode = Full (strict)** if the records stay proxied (🟠), or the records are
      switched to DNS-only (⚪) so Vercel owns TLS. Flexible mode causes redirect loops
- [ ] Resend shows **Verified**; a test email to Gmail/Yahoo/Outlook lands in the inbox
- [ ] Google sign-in works **on the production domain**, not just localhost
- [ ] Neon `production` is migrated, and every Vercel scope points at it (single-branch decision)
- [ ] R2 presigned PUT then GET round-trips; no public URL is reachable; CORS preflight passes
- [ ] `/api/health` is green for db + storage + engine
- [ ] Dodo Payments store activated; a test-mode purchase creates **exactly one** job under repeated
      webhook delivery; a forged signature is rejected
- [ ] Privacy, Terms, and **Refund Policy** are live with a real contact address
- [ ] Consent checkbox writes a `ConsentRecord`; the deletion path works end to end
- [ ] The public e2e suite proves every protected route 401s when signed out, and user B cannot fetch
      user A's report
- [ ] Demo PDFs regenerated with the ReportLab backend (marketing/delivery parity)
- [ ] Both crons running in production with `CRON_SECRET` set
- [ ] Secrets inventoried in the password manager; **no secret has ever been committed**
