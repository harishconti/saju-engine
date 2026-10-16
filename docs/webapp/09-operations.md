# 09 — Operations

Running the thing: scheduled jobs, health, the owner's daily loop, and what to do when it breaks.

## The owner's daily loop

This is a human-review product, so "operations" starts with a person.

```
Morning (~10 min)
  1. `/admin` — how many reports are waiting, and how old is the oldest?
  2. For each: preview the PDF, check the compliance QA flags,
     optionally set the 용신 override and regenerate, then approve or reject.
  3. /api/health — green?
  4. Delivery failures in /admin (bounces, send errors)

Weekly (~15 min)
  1. Job health: is QUEUED growing? That means the dispatcher is behind.
  2. Webhook health: any un-processed WebhookEvent rows older than 5 minutes?
  3. Neon usage: CU-hours and storage against the Free-plan ceiling.
  4. R2 usage: object count and storage.
  5. Resend: bounce/complaint rate.
  6. Backlog age trend — if review is the bottleneck, that is the business problem to solve,
     not an engineering one.
```

**The oldest-item age on `/admin` is the single most important operational number.** It is the
direct measure of the promise ("reviewed and delivered within N hours") and of whether the business
can take on more volume.

## Scheduled jobs

| Job | Schedule | Auth | Idempotent? |
|---|---|---|---|
| `/api/cron/dispatch` | every minute | `Bearer $CRON_SECRET` | Yes — lease-based claiming; a double-run processes different jobs |
| `/api/cron/cleanup` | daily 03:00 UTC | `Bearer $CRON_SECRET` | Yes — every step is a bounded delete/update |

Both accept `GET` and `POST` (Vercel Cron uses `GET`), and both accept `x-maintenance-secret` as an
alternative header so they can be triggered manually during an incident.

### What cleanup does

1. **Reap anonymous samples.** Two passes, because an anonymous sample has no row to track:
   (a) **list `reports/anonymous/` by prefix and delete by object age** (older than 7 days) — the
   documented promise, and the only version of it that works; (b) a row-backed sweep for reports with
   no order that were never delivered (`DRAFT_READY` / `FAILED`, older than 7 days). Delivered rows are
   deliberately excluded, since a sample a signed-in user kept also has no order but is theirs.
2. **Reclaim dead leases.** `Job` rows `RUNNING` with `leaseUntil < now() - 15 min` → `QUEUED`
   (or `FAILED` if `attempts >= maxAttempts`).
3. **Drain `ObjectDeletion`.** Batch `deleteObjects()` (up to 1000 keys per call) with an attempt cap
   of 10. On repeated failure, stop retrying and alert — a file that refuses to delete 10 times is a
   different problem than a transient one.
4. **Retry un-processed webhooks.** `WebhookEvent` rows with `processedAt IS NULL` and
   `receivedAt < now() - 1 min` → replay the handler.
5. **Reconcile payments.** Query Dodo Payments for orders created in the last 24 h that are paid
   there but `AWAITING_PAYMENT` here (a dropped webhook). Fix them, and alert — a pattern of these
   means the webhook endpoint is misconfigured.
6. **Purge.** `RateLimit` windows older than 1 h; `IdempotencyKey` older than 7 days; `Job` and
   `WebhookEvent` older than 90 days.
7. **Process due deletions.** `DeletionRequest` where `scheduledFor <= now()` → anonymise, delete
   solely-owned profiles and reports, queue their R2 objects. See
   [10 — Privacy and compliance](10-privacy-and-compliance.md).
8. **Retention sweep.** Profiles with no activity for 24 months → queue a warning, not a delete.

Every step writes a summary line to the log with counts only — never ids of user data at info level.

## Health checks

`GET /api/health` — no authentication, no secrets in the response.

```jsonc
{
  "status": "ok",                    // or "degraded"
  "db": true,
  "storage": true,
  "engine": true,
  "version": "«git sha»",
  "checkedAt": "2026-10-15T10:00:00Z"
}
```

| Probe | How | Failure means |
|---|---|---|
| Database | `SELECT 1` via Prisma | Neon down, credentials rotated, or the branch is suspended on the Free plan |
| Storage | A minimal R2 operation (list one key, or `HeadObject` on a sentinel) | Bad credentials, deleted token, wrong bucket |
| Engine | `POST {ENGINE_URL}/health` with the bearer token, short timeout | The deploy failed, or the token drifted between projects |
| Payments | `isDodoConfigured()` **and** every paid tier has a product id | Checkout would throw `PRODUCT_NOT_CONFIGURED` — i.e. you cannot take money |

The response also reports `paymentsMode` (`test_mode` / `live_mode`). That single word is worth watching:
it is how you notice that a real deployment is still pointed at test mode — or, worse, that it went live
before you meant it to.

Returns **503** with `status: "degraded"` if any probe fails, so an uptime monitor can alert on
status code alone. A degraded engine is not fatal for the site (the sample flow is the only
synchronous consumer) but it *is* fatal for fulfilment, so it must page.

⚠️ **Cold-start interaction:** Neon suspends compute after ~5 minutes idle, and the engine cold-starts
in ~1–2 s. Health-checking every minute would pin Neon's compute awake and burn CU-hours. Check every
5–15 minutes, and keep the check cheap.

## Observability

| Signal | Where | Alert threshold |
|---|---|---|
| `/api/health` | uptime monitor | Any 503 for 2 consecutive checks |
| Jobs stuck `QUEUED` | SQL on `Job` | > 5 for 15 minutes → the dispatcher is broken |
| Jobs `FAILED` | SQL on `Job` | Any in a 24 h window → look immediately |
| Oldest review backlog | `/admin` | > 24 h → the promise is at risk |
| UI/UX bar | `tools/audit-ui.py --strict` (CI `ui` job) | any overflow, axe violation, hydration warning or sub-44 px control — a new page or component regressing the shell is the usual cause |
| Delivery failures | `Delivery` where `status IN ('failed','bounced')` | Any → a client is waiting and doesn't know |
| Un-processed webhooks | `WebhookEvent` | > 0 older than 5 min → reconciliation is masking a real problem |
| Engine latency | `durationMs` per job | p95 > 10 s → investigate cold starts or a heavier tier |
| Neon CU-hours | Neon console | > 80 % of the monthly allowance |

The three queries worth having in a snippet:

```sql
-- Is the dispatcher keeping up?
SELECT state, count(*), min("createdAt") AS oldest
  FROM "Job" WHERE "createdAt" > now() - interval '1 day'
 GROUP BY state;

-- Is anything rotting?
SELECT count(*) FROM "Job"
 WHERE state = 'RUNNING' AND "leaseUntil" < now() - interval '15 minutes';

-- Did every paid order become a job?
SELECT o.id, o."paidAt" FROM "Order" o
  LEFT JOIN "Job" j ON j."orderId" = o.id
 WHERE o.status = 'PAID' AND o."paidAt" < now() - interval '10 minutes'
   AND j.id IS NULL;
```

That last one should always return zero rows. If it does not, the webhook handler is failing after it
records the payment.

## Runbooks

### New orders fail with `DATABASE_ERROR` right after a migration

**Symptom.** `POST /api/cron/dispatch` returns `{"error":"Database error","code":"DATABASE_ERROR"}`, and
the job is left untouched — still `QUEUED` with `attempts = 0`, so nothing was even claimed. The runtime
log says:

```
Invalid `prisma.$queryRaw()` invocation:
Raw query failed. Code: `0A000`. Message: `ERROR: cached plan must not change result type`
prisma error P2010
```

**Cause.** Postgres had cached the *result shape* of a prepared statement that used `RETURNING *` /
`SELECT *`, and the migration added a column, so the cached plan no longer matches. The statement is
refused until the plan is invalidated. This hit `claimJob`, which meant **every** dispatcher tick failed
the moment a column was added to `Job` — and it is why one deploy worked and the very next one did not.

**Fix (durable).** Never let a query depend on the table's current column list. `claimJob` now names its
columns explicitly:

```sql
RETURNING id, "orderId", "reportId", kind, state, attempts, "maxAttempts",
          "leaseUntil", worker, payload, "lastError", "startedAt", "finishedAt", "createdAt"
```

Adding a field to that list is now a deliberate act, and a future `ADD COLUMN` cannot break claiming.
**If you add a column to a query with an explicit list, add it to the list.**

**Fix (immediate).** The stale plans belong to live pooled connections and clear as the pool recycles.
Editing the statement text also forces a fresh prepare, so deploying the named-column version fixes it
outright.

**Prevention.** When a migration adds a column, deploy the code change and the migration together, and
prefer explicit column lists in raw SQL over `*`.

### A report is stuck "In review" and the client is asking

1. Check `/admin` — is the report there, or did it vanish?
2. Check its `Job` rows: `state`, `attempts`, `lastError`.
3. If `FAILED`, the fix is usually a profile data problem (bad city, missing gender). Correct it, then
   regenerate — do not edit the report.
4. If it is simply waiting on you: approve it. That is the runbook.

### Dispatch is not running

1. `curl -H "Authorization: Bearer $CRON_SECRET" https://cosmicsaju.com/api/cron/dispatch`
   - **401** → `CRON_SECRET` mismatch between Vercel's cron and the deployment.
   - **200 with `processed: 0`** → the cron is fine and there is nothing to do.
   - **500** → read the function logs.
2. Vercel → project → Cron Jobs → run history. Hobby-plan projects silently will not run a
   per-minute schedule.
3. Still stuck after a manual trigger: run the leak query above, then work the job manually by
   calling the engine route with the order's payload.

### Mail is not arriving, or a client's reply bounces

This looks like a code bug and usually is not — it is DNS.

1. **Check the zone, not the mailbox provider.** Registration (Hostinger) and DNS hosting (Cloudflare)
   are different roles, and only Cloudflare is authoritative:
   ```bash
   dnsq cosmicsaju.com NS        # must be randy/veronica.ns.cloudflare.com
   dnsq cosmicsaju.com MX        # the mailbox's mail hosts. NONE ⇒ nothing can arrive
   dnsq cosmicsaju.com TXT       # exactly one v=spf1
   ```
   ⚠️ This exact failure happened once already: a mail host cannot publish records into a zone it does
   not host, so its panel asks you to add them in Cloudflare — and until that was done the apex had no
   MX/TXT and mail silently went nowhere while the panel showed the mailbox as configured.
2. **Check DKIM, which is the usual residual gap.** The selectors are CNAMEs
   (`hostingermail-a/b/c._domainkey`) and must be **DNS only (grey cloud)** — a proxied CNAME is answered
   by Cloudflare instead of the mail host, so DKIM fails *silently* and mail drifts toward spam. Query
   **TXT**, not CNAME: a CNAME name resolves its TXT to the target's contents, so
   `dnsq hostingermail-a._domainkey.cosmicsaju.com TXT` proves the CNAME **and** prints the key.
   **An empty key (`v=DKIM1;p=`) is the tell-tale of a provider-side gap** — the record exists but can
   never validate, and no DNS change fixes it. That is the current state for Hostinger selectors `b`/`c`.
   Never add a TXT at a selector name: a CNAME cannot share its name with any other record type.
3. **Check `send` separately.** Resend lives on the subdomain (`dnsq send.cosmicsaju.com CNAME` and
   `dnsq rsend.cosmicsaju.com CNAME`). Apex MX missing does **not** break outbound app mail; it breaks
   *receiving*.
4. **Outbound is fine but replies vanish?** `EMAIL_REPLY_TO` must be set (all scopes) **and** the
   deployment must be rebuilt — it is read at runtime, but the value lives with the deployment's env.
   A reply with no `Reply-To` goes to `EMAIL_FROM` (`reports@`), which is an alias and should still land.
5. **Magic-link mail is not ours.** Neon Auth sends it with its own From address, so it does not use
   `EMAIL_REPLY_TO`. Configure it in Neon, not here ([04](04-auth-and-roles.md)).
6. **Never add a second apex SPF record.** Merge the `include:` lists instead; two invalidate both.
7. **Confirm with a real send, not a lookup.** From the app's `EMAIL_FROM` to `hello@cosmicsaju.com`,
   then read `last_event` back via Resend's `GET /emails/{id}` — `delivered` is proof the whole path
   works. ⚠️ Call Resend with **curl**: Cloudflare in front of `api.resend.com` refuses
   `Python-urllib` with `error code: 1010`.

### The free sample is refusing everyone (`403 TURNSTILE_FAILED`)

The gate is Cloudflare Turnstile. It is deliberate, but it is also the one control that can take the
whole funnel down for real visitors, so the failure direction matters more than the happy path.

**Enforcement is opt-in.** `TURNSTILE_MODE` is `off` (default) | `log` | `enforce`. **Deploy new keys at
`log`**: the server verifies whatever token arrives, logs the outcome, and never refuses anyone — so an
unrendered widget costs nothing while real traffic proves whether tokens are actually issued. Move to
`enforce` only after a **real browser** is observed completing the challenge. That switch exists because
the opposite happened on 2026-10-16: the widget failed to render and the enforcing server refused every
visitor at the top of the funnel.

0. **Confirm the project's env vars are the ones actually in use.** `vercel deploy` from the repository
   root uploads `apps/web/.env` unless `.vercelignore` excludes it, and Next loads `.env` at **build and
   runtime** — so a local file silently wins over the project's environment variables. This is not
   hypothetical: it is exactly why deleting `TURNSTILE_SECRET_KEY` from Vercel kept producing live `403`
   responses and why the deleted site key kept being inlined. `/.vercelignore` now excludes `.env*`.
   **If an env change ever appears to do nothing, suspect this first.**
1. **Is it the visitor or the widget?** A real visitor sees a checkbox above *"Get my free snapshot"*.
   If the widget is missing, the client refuses to submit — a keyed widget with no token is treated as
   *"not yet verified"* — so the symptom is *"Please complete the quick verification below"* on a page
   with nothing to complete.
2. **CSP is the usual cause.** The challenge script and its iframe come from `challenges.cloudflare.com`
   **and its regional subdomains** (observed: `hagen.challenges.cloudflare.com`,
   `brunhild.challenges.cloudflare.com`). `next.config.ts` must therefore list
   `https://challenges.cloudflare.com` **and** `https://*.challenges.cloudflare.com` in `script-src`,
   `frame-src` **and** `connect-src` — a bare host never matches its own subdomains. Read the browser
   console for `Refused to load` / `… violates …` before looking anywhere else.
3. **The other usual cause is the widget's own configuration**, which lives in the Cloudflare
   dashboard and cannot be seen from here: the widget must list this domain under **allowed hostnames**
   (`cosmicsaju.com` **and** `www.cosmicsaju.com`), and the **site key and secret must come from the same
   widget**. A valid secret that does not pair with the site key verifies nothing. Symptom in both cases:
   the script loads, `turnstile.render()` runs, and the challenge never appears.
4. **Escape hatch — set `TURNSTILE_MODE=off` and redeploy.** That is the intended switch and it cannot
   half-apply. Removing variables also works but is trap-laden: removing only the site key leaves the
   client unable to produce a token while the server still refuses everything (**worse**); removing only
   the secret makes the server skip while the client still demands a token nobody can obtain. If you do
   remove them, remove **both**. Removing only the site key is **not** enough: the client stops
   rendering the widget so no token is ever produced, while the server still sees a configured secret and
   refuses everything with `403` — an outage that looks like the widget merely failed to load. Removing
   only the secret makes the server skip while the client still demands a token nobody can obtain.
   Redeploy either way: the site key is inlined at build time.
   Check `/api/health` afterwards and confirm `/api/sample` returns **200**.
5. **Never "fix" it by accepting tokens the server could not verify.** That is precisely the state this
   replaced — a `turnstileToken` field that nothing on either end ever read.
6. **Turnstile refuses automation on purpose.** A headless/Playwright check typically reaches "script
   loads, `window.turnstile` is defined, `render()` injects its DOM, challenge never completes". Do **not**
   conclude from that alone that the deployment is fine — on 2026-10-16 exactly this signal was dismissed
   as "automation detection" while the widget was in fact broken for real visitors too. A real browser is
   the only authority.

### The engine service is down

The site keeps working; only the sample flow and new generation break.

1. `/api/health` — `engine: false`?
2. Vercel → `saju-report-engine` → the last deploy. Roll back if it correlates.
3. If the token rotated, update `ENGINE_SERVICE_TOKEN` in **both** projects and redeploy both. A
   one-sided rotation presents as a 401 from the engine while `/health` on the engine itself still
   succeeds.
4. If it is a bundle-size failure after adding a dependency, check `excludeFiles` and the reported
   function size.

### A client got the wrong reading

1. Do not edit or delete the delivered report. It is immutable, deliberately — see
   [05](05-report-pipeline.md) §7.
2. Fix the profile (most wrong readings trace to a wrong birth time, a wrong city, or a wrong
   timezone), then regenerate.
3. Review and approve the new version. The client gets a new report and keeps the old one.
4. If the error was ours, refund. Dodo Payments refunds are at their discretion — a clear, polite
   request with the specifics works better than a bulk appeal.

### Suspected key exposure

1. Rotate the specific credential **first**, then investigate. In order of blast radius:
   `DODO_PAYMENTS_API_KEY` → `R2_SECRET_ACCESS_KEY` → `RESEND_API_KEY` →
   `ENGINE_SERVICE_TOKEN` → `NEON_AUTH_COOKIE_SECRET` (rotating this signs everyone out, which is
   the correct response to a suspected session compromise) → `CRON_SECRET` → database credentials
   (rotate in Neon, update `DATABASE_URL`/`DIRECT_URL`).
2. Check `AuditLog` and Vercel function logs for the exposure window.
3. Check `WebhookEvent` for forged-but-accepted events (there should be none — signatures are
   verified against the secret, so rotating invalidates forged ones).
4. If the database credential leaked, assume the data was read and follow the breach path in
   [10 — Privacy and compliance](10-privacy-and-compliance.md).

### Neon is suspended (Free-plan ceiling)

Free-plan compute suspends when CU-hours or transfer run out, and storage-increasing operations fail
once the storage cap is hit. Neither deletes data.

1. Confirm in the Neon console which limit was hit.
2. Free space (purge old `Job`, `WebhookEvent`, `RateLimit` rows early) or upgrade to Launch
   (usage-based, ~$5 minimum).
3. Prevent the next occurrence: the biggest CU-hours consumer is an always-on compute or a frequent
   health check. Both are configuration mistakes, not load.

### Functions Storage is filling (Hobby: 10 GB)

**Symptom.** The Vercel team dashboard shows Functions Storage approaching 10 GB. It does not take
the site down — it stops **new deployments**, which is the real risk before a fix is urgent.

**What it is.** Vercel charges the account for every *retained* deployment's function bundle. It is
not any single artefact:

| | |
|---|---|
| Repo upload | ~39 MB (`.vercelignore` trims both uploads to what either build needs — and note it governs *both*: listing `apps/` there broke the webapp build) |
| **Engine bundle, per deployment** | **~157 MB** — the Python closure is ~125 MB, of which pandas 65 + numpy 38 come in transitively via `sajupy`; reportlab 8, PIL 6.5 |
| Webapp bundle, per deployment | ~40–80 MB (Next server output + Prisma engines) |
| Growth rate | **Every push deploys both projects** — ~220 MB per push |

**Diagnose.**

```bash
python3 tools/prune_deployments.py            # counts deployments, shows what is removable
npx vercel ls <project> --json                # raw list; paging needs --next
npx vercel list <project> --policy            # view the retention policy in effect
```

**Act.**

```bash
python3 tools/prune_deployments.py --apply    # keep the newest 3 per project; --safe guards aliases
```

Then stop it recurring, because pruning is a cleanup and retention is the cause. Retention has two
places, both in the dashboard: **team** (Settings → Deployment Retention, with *Apply this policy to
all existing projects*) and **per project** (Project → Settings → **Security** → Deployment Retention
Policy), which overrides the team value for that project. Set the shortest offered duration for
Canceled and Errored, and for the **engine** project especially — it is the 157 MB one. Note the lag:
a deployment past its limit is marked for deletion by a background job **within ~48 h**, then
restorable for 30 days, so the storage number falls over a day or two rather than instantly.

**The floor, and why `--keep 3` is the right default.** Vercel retains regardless of policy: on Hobby
the **last 3 deployments created** and the **last 3 Ready production deployments** per project, plus
anything holding an alias and the latest preview of an active branch. That is ~4 per project here
(~900 MB), so a `--keep` below 3 achieves nothing and the dry run will keep listing one deployment
per project that `--safe` refuses to touch. That is the guard working, not a failure.

⚠️ **On Pro, the defaults get *longer*, not shorter** — Production 1 year, Pre-Production 180 days
(versus 30/30 on Hobby). Upgrading raises the allowance but not the ceiling on growth, so set a custom
**team** policy as part of the upgrade or this comes back bigger.

**Reduce the bundle itself (open).** ~103 MB of every engine deployment is pandas + numpy, pulled in
by `sajupy` — nothing in `src/` or `api/` imports them directly. Replacing or lazy-loading that
dependency would cut roughly 80 % of the engine bundle, which is worth investigating after the Pro
upgrade; it is a code change, not a settings one.

## Backups

| Asset | Backup | Restore |
|---|---|---|
| Neon Postgres | Built-in point-in-time restore (6 h on Free; longer on paid) + a manual snapshot before each migration | Neon console → restore, or snapshot promote |
| R2 objects | Effectively the source of truth; enable no lifecycle expiry on `reports/` | Object-level; there is no bulk restore |
| Schema | `prisma/migrations/` in git | `prisma migrate deploy` |
| Report source markdown | Stored in R2 alongside the PDF | Re-render with the engine |
| Secrets | Password manager | Manual re-entry |
| Report templates and knowledge | git | — |

The honest summary: **Postgres is backed up, R2 is not.** R2 objects are cheap to regenerate from
`Report.mdKey` + the profile data (that is what the stored source markdown is for), so a bulk object
loss is a batch re-render, not a data loss. Verify that assumption before relying on it by
re-rendering one report from its stored markdown as a rehearsal.

**Rehearse the restore once before launch.** An untested backup is a belief, not a backup.

## Cost monitoring

| Service | Watch | Act when |
|---|---|---|
| Vercel | Function invocations, bandwidth, cron count | Bandwidth overages are the classic surprise — a viral post costs $0.15/GB past the included allowance |
| Neon | CU-hours, storage, egress | > 80 % of the Free allowance |
| R2 | Storage, Class A ops | Storage > 8 GB (≈ 57,000 reports) |
| Resend | Emails sent | > 2,400/month (free tier ~3,000) |
| Dodo Payments | Fees, refund rate | Refund rate > 5 % is a product signal, not a billing one |

## Incident severity

| Level | Definition | Response |
|---|---|---|
| **S1** | Site down, or a paid order cannot be generated at all | Drop everything. Health, cron, engine, webhook — in that order |
| **S2** | New orders fail, but the site and delivered reports are fine | Same day. Engine or dispatcher |
| **S3** | One report is wrong or stuck | Next business day. Runbook above |
| **S4** | Cosmetic, copy, or a non-blocking failure | Batch it |

At this scale S1 and S2 are almost always one of three things: a rotated secret applied to only one
project, a cron that stopped because the plan changed, or a Neon limit. Check those three first.
