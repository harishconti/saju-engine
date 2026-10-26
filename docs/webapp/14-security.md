# 14 — Security and hardening

This page is the **bar**, not a point-in-time audit: every control names where it lives and what
fails when it is removed. Update it in the same change that adds or removes a control — a security
claim that only exists in prose is exactly how this project shipped `requiresReview`,
`turnstileToken` and the admin role as documentation of controls the code did not have.

> **Status (2026-10-18):** the five gaps from the 2026-10-18 review are closed in code; the
> remaining items are configuration (Turnstile `enforce`) and operations (credential rotation,
> WAF/uptime). See §5 for the residual-risk list.

## 1. Trust boundaries and assets

```
Browser ──► apps/web (Vercel, Next 16) ──► Neon Postgres
   │              │  └──► Neon Auth (identity)
   │              ├──► Cloudflare R2 (private; presigned only)
   │              ├──► Dodo Payments (webhook = source of truth)
   │              ├──► Resend (mail + webhook)
   │              └──► api/index.py (engine; bearer token)
   │                         └──► R2 presigned PUT (the only write capability)
   └──► Neon Auth proxy (/api/auth/*)
```

**Assets:** birth data (date/time/place), delivered readings, payment state, the admin console,
and the shared secrets (`ENGINE_SERVICE_TOKEN`, `CRON_SECRET`, `DODO_PAYMENTS_WEBHOOK_KEY`,
`NEON_AUTH_COOKIE_SECRET`, `R2_SECRET_ACCESS_KEY`).

**Boundaries that matter:**

| Boundary | Rule |
|---|---|
| Browser → webapp | Untrusted input. Zod at every route; price resolved server-side; ownership checked before any read/write. |
| Webapp → engine | One shared bearer token. The engine has **no database and no storage credentials**; a presigned URL is its only write capability. Never expose the engine to the browser. |
| Engine → R2 | Only a URL on the configured allowlist (`R2_ENDPOINT` / `SAJU_UPLOAD_HOSTS`), https (http loopback for dev), optionally scoped to `SAJU_UPLOAD_BUCKET`. |
| Provider → webapp | Webhooks are verified against the **raw body** before parsing; unverified is refused. |

## 2. Controls

| Control | Where | Enforced by | Regression guard |
|---|---|---|---|
| Authentication | Neon Auth; sessions never stored locally | `src/lib/auth/server.ts` | — (managed) |
| Authorization (user) | Every data route | `requireUser()` + `userId` in the query; cross-user is **404, not 403** | route review |
| Authorization (admin) | Every `/api/admin/*` | `requireAdmin()` — DB role **and** `ADMIN_EMAILS`, read fresh | 401 (not 403) to hide the surface |
| Route protection | `src/proxy.ts` matcher | Neon Auth middleware **plus** per-layout re-check | defence in depth |
| Input validation | `src/lib/validation/schemas.ts` | Zod, length bounds, enums, date/time regex | unit tests |
| Price integrity | `src/app/api/orders/route.ts` | Server-side tier map; client price discarded; free tier not orderable | unit tests |
| Tenant isolation | Prisma queries | Every user route filters by `userId`; keys re-derived, never trusted (`KEY_MISMATCH`) | review (see §5.2) |
| Payment webhook | `src/lib/webhook-signature.ts` | Standard Webhooks HMAC-SHA256 over raw body, 300 s replay window, timing-safe compare, `webhook-id` dedupe | `webhook-signature.test.ts` |
| Mail webhook | `src/app/api/webhooks/resend/route.ts` | Svix HMAC, timing-safe compare | — |
| Engine auth | `api/index.py:_authorize` | Bearer + `hmac.compare_digest`; **fails closed** (503) without a token | `test_health_fails_closed_when_unconfigured` |
| Engine upload target | `api/index.py:_validate_upload_url` | Host allowlist + https + no credentials/fragment + optional bucket prefix; fail closed without a list | `test_generate_refuses_an_upload_url_on_an_unlisted_host` et al. |
| Engine request size | `api/index.py:MaxBodySizeMiddleware` | `Content-Length` and streamed-byte cap (default 2 MB, `SAJU_MAX_REQUEST_BYTES`) | `test_body_size_middleware_*` |
| Engine field bounds | `api/index.py` pydantic models | `max_length` / `ge`/`le` on every field | `test_script_request_caps_markdown_length` |
| Rate limiting | `src/lib/ratelimit.ts` | Postgres fixed window; public + mutating routes | see §3 |
| Client IP trust | `src/lib/client-ip.ts` | Prefer `x-vercel-forwarded-for` / `x-real-ip`; raw `x-forwarded-for` uses the **rightmost** hop | `client-ip.test.ts` |
| Email abuse | `src/app/api/sample/email/route.ts` | Per-IP (5/min, 20/h) **and per-recipient** (2/h) | — |
| Bot protection | `src/lib/turnstile.ts` | Cloudflare Turnstile; `off` / `log` / `enforce`; state exposed by the authorised `/api/health/detail` | `turnstile.test.ts` |
| Storage | `src/lib/r2.ts` | Private bucket; presigned PUT/GET with short TTLs; object keys derived server-side | `r2.integration.test.ts` |
| Security headers | `apps/web/next.config.ts` | CSP (`default-src 'self'`, `object-src 'none'`, `frame-ancestors 'none'`), HSTS, `nosniff`, `X-Frame-Options: DENY`, Referrer/Permissions policy, no `X-Powered-By` | manual / `audit-ui` |
| CSRF | Neon Auth cookies + JSON-only mutations + `form-action 'self'` + no CORS | implicit; see §5.4 | — |
| Cron auth | `src/lib/api.ts:providedSecret` | Bearer / `x-maintenance-secret`, timing-safe; fails closed without a secret | — |
| Audit trail | `src/lib/audit.ts` | Same transaction as the mutation; **PII forbidden** in `before`/`after` | review |
| Secrets | `.gitignore`, `.vercelignore` | `.env*` never tracked or uploaded; Vercel env is the single source of truth | `git ls-files` / CI |
| Dependencies | `package-lock.json` | `npm audit --omit=dev` → 0 known vulnerabilities (2026-10-18) | manual; see §5.5 |

## 3. What the five 2026-10-18 fixes changed

1. **Engine SSRF via `uploadUrl`.** `_upload` used to PUT to whatever URL the caller sent. The
   engine is token-gated, so this was not internet-reachable abuse — but a leaked token or a webapp
   bug made it an arbitrary-URL write primitive (including cloud metadata). Now every target must
   pass `_validate_upload_url`: https (or http to loopback), no embedded credentials, no fragment,
   host on `R2_ENDPOINT`/`SAJU_UPLOAD_HOSTS` (one of them must be set on the engine project), and —
   when `SAJU_UPLOAD_BUCKET` is set — that bucket as the first path segment (path-style) or the
   first host label (virtual-hosted, which is what the webapp presigns). **No allowlist means 503**:
   fail closed.
2. **Unbounded request bodies.** FastAPI/Starlette impose no limit. Added
   `MaxBodySizeMiddleware` (default 2 MB) and pydantic bounds on every engine field, including
   `ScriptRequest.markdown` (1 M chars).
3. **Spoofable rate-limit key.** `clientIp()` used the **leftmost** `X-Forwarded-For` entry, which a
   client can prepend. It now prefers Vercel's own headers and otherwise takes the **rightmost** hop.
4. **Open mail relay.** `POST /api/sample/email` sends mail from our domain to a caller-chosen
   address. Added a per-recipient bucket (2/h) on top of the per-IP buckets.
5. **Invisible bot-protection state.** `/api/health/detail` reports `botProtection: off|log|enforce`
   and `botProtectionConfigured`, so a `log` rollout cannot be mistaken for `enforce`.

## 4. Deploying these changes

The engine change **fails closed**, so it needs one of these set on the `saju-report-engine`
project **before or with** the deploy, or every `/generate` returns `503 UPLOAD_HOSTS_UNCONFIGURED`:

```bash
# Required: the virtual-hosted host the webapp presigns into ({bucket}.{account_id}.r2...).
# The bucket is the first DNS label, not a path segment (apps/web/src/lib/r2.ts, no forcePathStyle).
SAJU_UPLOAD_HOSTS=saju-engine-dev.«account_id».r2.cloudflarestorage.com

# Alternative: the account origin. The engine accepts exactly one bucket label in front of it,
# so this also allows the virtual-hosted URL the webapp actually signs. Set one or both.
R2_ENDPOINT=https://«account_id».r2.cloudflarestorage.com

# Optional, stricter: pin the bucket — first path segment (path-style) or first host label
# (virtual-hosted).
SAJU_UPLOAD_BUCKET=saju-engine-dev
```

Then flip bot protection only after a real browser has completed the challenge:

```bash
vercel env add TURNSTILE_MODE production   # value: enforce
# With HEALTH_DETAIL_TOKEN, /api/health/detail must show botProtection: "enforce" after the redeploy.
```

## 5. Deliberate residual risks (not "done")

1. **Turnstile is still `log` until the env flip above.** It verifies and records but never blocks;
   anonymous endpoints therefore rely on rate limits. This is a known, visible state — not a silent
   gap.
2. **Tenant isolation is application-level.** There is no Postgres RLS; every query must carry
   `userId`. The routes are consistent today, but a single missed filter is a cross-tenant read. A
   Prisma extension that auto-scopes user tables would make it structural.
3. **CSP allows `'unsafe-inline'` scripts** (required by Next's inline bootstrap today). It weakens
   XSS defence; a nonce/hash CSP is the eventual answer.
4. **CSRF is implicit**, not asserted: Neon Auth cookies + JSON-only mutation routes + `form-action
   'self'` + no CORS. Pin the cookie's `SameSite`/`Secure` attributes in a test before calling it
   covered.
5. **No security scanning in CI** — no `npm audit`, `pip-audit`, secret scan, Dependabot or CodeQL.
   Dependencies are clean *today*; nothing keeps them that way. Python dependencies are also `>=`
   (no upper pins).
6. **No WAF/DDoS control beyond Vercel's defaults**, and no uptime monitor on `/api/health`.
7. **No end-to-end auth-gate test.** [12](12-testing.md) describes Playwright specs; none exist, so
   a route added without a guard is not caught automatically.
8. **Operational items from the launch audit remain** ([13](13-launch-audit.md) §B6): rotate the
   Neon password and Resend key seen in a transcript, confirm `ADMIN_EMAILS`, add `_dmarc rua`.
9. **The legacy FastAPI intake app** (`tools/client_intake_app.py`, `src/saju_web/`) is a separate
   surface with its own queue/tokens/CORS posture. It is not deployed at cosmicsaju.com; if it is
   ever exposed, it needs its own review at this bar.
10. **`/api/health` was public and disclosed coarse configuration** (db/storage/engine booleans,
    `paymentsMode`, `botProtection`, version). **Fixed 2026-10-26 (AU-31):** the public body is now
    `{ok, status, version, checkedAt}` only. The diagnosis moved to `/api/health/detail`, which needs
    `HEALTH_DETAIL_TOKEN` or an admin session and answers `401` to everyone else without probing.
11. **The auth API still reveals account existence.** Neon Auth answers sign-up for an existing
    address with `422 USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL`. The login page already maps that to a
    neutral message, but a caller reading the API directly still learns the fact. **Owner action
    (AU-35):** enable **Require email verification** for the Neon Auth email/password provider (with
    Resend SMTP configured) so sign-up cannot be used as an account-enumeration oracle. This is a
    console setting, not code; the exact steps are in
    [08 — Deployment](08-deployment.md#pre-launch-verification).

## 6. How to verify

```bash
# Engine: allowlist, body caps, field bounds
python3 -m pytest tests/test_report_engine_service.py -q

# Webapp: trusted client IP, Turnstile modes, webhook signatures
cd apps/web && npm test -- client-ip turnstile webhook-signature
cd apps/web && npm run lint && npm run typecheck

# Dependencies
cd apps/web && npm audit --omit=dev

# Live posture (after deploy) — the detail view needs the operator token
curl -s -H "Authorization: Bearer $HEALTH_DETAIL_TOKEN" \
  https://www.cosmicsaju.com/api/health/detail | jq '{status, botProtection, paymentsMode}'
```

## 7. Maintenance rule

A new route must state, in the same change: its auth guard (`requireUser`/`requireAdmin`), whether
it needs a rate limit, and whether it accepts a body (and therefore a bound). Add it to
[03](03-api-spec.md) and to the table above. If it changes a control, change this page — the page is
the claim.
