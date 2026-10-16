# 12 — Testing

Three test surfaces — Python (the engine), TypeScript (the webapp), and browser (the whole thing) —
plus two specialised gates that exist because this product has failure modes ordinary tests miss.

## The gates

```bash
# Engine (existing, and it must stay green)
python -m pytest tests/ -q
python tools/run_validation.py                      # cited-fixture gate
python3 tools/qa_compliance.py <report.md>          # prose compliance (needs TYPESAFE_API_KEY)

# Webapp
npm run lint
npm run typecheck
npm test                     # vitest
npm run build                # proves the no-secrets build works
npm run test:e2e             # playwright

# Engine service (new)
python -m pytest tests/test_engine_service.py -q    # contract test
```

> ✅ **Fixed 2026-10-16.** The workflow now triggers on **`develop`** and `main` and adds a **webapp**
> job (`npm ci` → `prisma generate` → lint → typecheck → `vitest run` → `next build`), verified locally
> with placeholder secrets. It previously triggered on `main` only — so it never ran for real work —
> and covered `pytest` alone. The Playwright tier below remains **unimplemented**. See
> [13](13-launch-audit.md) §B5.

**The engine suite must never be allowed to regress** — with 1,909 cases and a
cited-fixture validation gate, it is the only thing making it safe to touch a working engine while
building a product around it.

## Surface 1 — Python engine (existing, unchanged policy)

| Suite | What it protects |
|---|---|
| `tests/test_textbook_cases.py` | Korean 만세력 cases (박정희, 노무현, 김대중, 김영삼) — end-to-end date → pillar |
| `tests/test_solar_terms_table.py` | Our own 節氣 table (1899–2101), not sajupy's CSV |
| `tests/test_strength.py`, `test_yongsin.py` | Day-Master strength and the single-source-of-truth 용신 |
| `tests/test_compat*.py` | 11 sub-systems and the composite score |
| `tests/golden/` (markdown) and `tests/golden_html/` (rendered HTML) | Byte-exact report snapshots |
| `tests/test_pdf.py` | Hanja-pair rendering + citation stripping |
| `tools/run_validation.py` | 315+ cited checks across 10 subsystems |

**Policy for this work:** the three engine edits (E1 fonts, E2 geocoding, E3 override threading) must
each come with a test, and must not change any golden snapshot unless the change is deliberate and
reviewed. A golden diff during this work is a stop-and-look, not a regenerate.

New tests required:

| Test | Asserts |
|---|---|
| `test_font_dir_override` | `SAJU_FONT_DIR` is honoured; no `font file not found` warning fires; a PDF still renders when the dir is absent (built-in fallback) |
| `test_no_runtime_geocoding` | With explicit `longitude` + `timezone`, the code path never calls Nominatim (patch it to raise if called) |
| `test_favorable_override_single` | `prepare_chart_render(..., favorable_override='Water')` changes the "What This Year Means" callout *and* the body consistently |
| `test_engine_service_contract` | `TestClient` against `api/index.py`: happy path, missing gender → 422, bad tz → 422, wrong contract version → 422, presign not used on failure |
| `test_golden_pdf_sha256` | A known chart produces a byte-identical ReportLab PDF (catches accidental layout drift) |

The `test_no_runtime_geocoding` test is worth writing first — it is the one that prevents a silent,
latency-adding regression that no assertion would otherwise catch.

## Surface 2 — Webapp unit and integration (Vitest)

> **Status (2026-10-16): implemented and green — 69 passed / 4 skipped across 7 files.** No CI job runs
> them yet, so today they only protect a developer who remembers to run `npm test`. See
> §"What actually exists" below.

Node environment, Prisma mocked. The pattern that works:

```ts
const mocks = vi.hoisted(() => ({ prisma: { order: { create: vi.fn(), findUnique: vi.fn() } } }));
vi.mock('@/lib/prisma', () => ({ prisma: mocks.prisma }));
```

**Target coverage** — the taxonomy this layer should satisfy:

| Area | Tests |
|---|---|
| Validation (`src/lib/validation/`) | Every zod schema: valid, missing field, wrong type, out-of-range, injection-shaped input. Enums match the DB `CHECK` constraints |
| `tiers.ts` | Price resolution, unknown tier rejection, legacy-alias normalisation (`spark` → `essential`), `kind`/`tier` compatibility, and `autoDelivers()` / `requiresReview` (an **unknown** tier fails safe toward review) |
| Rate limiting | Window arithmetic, boundary, limit enforcement, window rollover |
| Idempotency | Same key + same body → replay; same key + different body → 409 |
| Roles | `hasMinRole`, admin email allowlist, double-gate behaviour |
| R2 helpers | Key construction (`reports/{userId}/{orderId}/{reportId}.pdf`), presign parameter correctness, deletion enqueue on failure |
| Auth mirroring | New user create; P2002 race recovery; email/name drift update |
| Deletion | `scheduledFor` arithmetic, cancel before/after, anonymisation shape |
| Consent | Append-only semantics; withdrawal sets `withdrawnAt` |
| Chart-hash | Same inputs → same hash; override change → different hash |
| **Bot protection** (`turnstile.test.ts`) | Unconfigured → **skips** and does not call Cloudflare (so local dev works); configured + missing/whitespace token → **refuses** without calling out; valid token → posts `secret`/`response`/`remoteip`; `success:false` → refuses and surfaces Cloudflare's error codes; HTTP error or an unreachable Cloudflare → **refuses, never 500s and never allows** |
| **Mail routing** (`email-reply-to.test.ts`) | `EMAIL_REPLY_TO` lands as `reply_to`; an explicit caller `replyTo` wins; the header is **omitted, not empty**, when unset; an unconfigured Resend reports `skipped` and sends nothing; the published `hello@` / `privacy@` defaults |

Mock-boundary rule: mock the **network and the database**, never our own modules. If a test needs to
mock half the app, the module boundary is wrong.

### What actually exists (2026-10-16)

| File | Covers |
|---|---|
| `core.test.ts` | Validation primitives, tiers, roles, rate-limit windows, idempotency, R2 keys, auth mirroring, deletion, consent, chart hash |
| `keys.test.ts` | `autoDelivers()` / `requiresReview`, including that an **unknown** tier fails safe toward review |
| `tiers.test.ts` | Price resolution and the tier map |
| `birth.test.ts` | City resolution and the birth-time fallback |
| `webhook-signature.test.ts` | Standard Webhooks verification — 12 cases, including tampered body, wrong secret, replay outside the window, and missing headers |
| `email-reply-to.test.ts` | The `Reply-To` invariant — that a client's reply has somewhere real to land |
| `r2.integration.test.ts` | **Skipped** unless `RUN_R2_TESTS=1`: a real presigned PUT → `HeadObject` → GET → delete round-trip, plus an unsigned-access probe |

Accessibility is unit-testable with `vitest-axe` on rendered components (light and dark), which
catches the cheap a11y regressions before Playwright runs.

## Surface 3 — End-to-end (Playwright) — **planned, not implemented**

> 🚫 **None of these specs exist yet**, and no browser is installed in CI. Everything below describes
> the intended shape, so the first author writes the right tests — but today the only automated
> coverage is Surface 1 (pytest) and Surface 2 (Vitest). This is finding **B5** in
> [13](13-launch-audit.md). The one that pays for itself first is `auth-gate.spec.ts`: it is the only
> test that reliably catches "a new route shipped without a guard".

Two tiers, same taxonomy as the reference implementation:

### Public tier (read-only, runs in CI)

| Spec | Asserts |
|---|---|
| `auth-gate.spec.ts` | **Every** protected route returns `401 {error, code:'UNAUTHORIZED'}` when signed out. Includes `/admin`. Must be extended whenever a route is added |
| `login.spec.ts` | The tabbed form renders, validates, and surfaces errors; consent is required to sign up |
| `landing.spec.ts` | All 9 sections render; nav anchors resolve; both themes; no horizontal scroll at 390/768/1440 |
| `sample.spec.ts` | The sample flow produces a downloadable PDF; "I don't know my birth time" is a valid path; the derived pillars are shown for confirmation |
| `a11y.spec.ts` | axe clean (light and dark) on landing, login, sample |
| `legal.spec.ts` | Privacy, terms, and refund policy exist and are non-empty |

The auth-gate spec is the highest-value test in the suite: it is the only thing that reliably catches
"a new route shipped without a guard".

### Authed tier (opt-in writes, dev branch only)

Gated behind `E2E_ALLOW_WRITES=1` and pointed at a throwaway Neon branch. **Never run against
production.**

| Spec | Asserts |
|---|---|
| `order.spec.ts` | Profile → tier → order → `AWAITING_PAYMENT`; a tampered price is ignored |
| `job.spec.ts` | With the dispatcher triggered manually, the job reaches `DRAFT_READY` and an object exists in R2 |
| `review.spec.ts` | Admin can preview, override, regenerate (version increments, old → `SUPERSEDED`), approve |
| `delivery.spec.ts` | Email queued (Resend mocked, or a test-mode key with an assertion on our `Delivery` row) |
| `download.spec.ts` | Owner downloads; **user B gets 404**; a `DRAFT_READY` report is refused with `409` |
| `account.spec.ts` | Schedule deletion, cancel it, then let it process |

### The eight end-to-end acceptance tests

These map 1:1 onto the product-level definition of done in
[11 — Build plan](11-build-plan.md):

| # | Acceptance test |
|---|---|
| 1 | A new visitor gets a sample PDF in one flow, signed out |
| 2 | Creating an account preserves that sample in `/dashboard/reports` |
| 3 | A purchase (test mode) creates exactly one job |
| 4 | The job produces a PDF in R2 with no human action |
| 5 | An admin override + regenerate produces a new version, old superseded |
| 6 | Approving produces a `Delivery` row and a visible report |
| 7 | Download works for the owner; delete removes the row and queues the object |
| 8 | Account deletion anonymises the user and removes birth data |

## Specialised gate 1 — the PDF leak test

A paid deliverable must never contain a citation or an internal marker. The repository already does
this by extracting text from rendered PDFs and grepping for citation patterns; extend it to the
ReportLab path:

```bash
pdftotext -layout report.pdf - | grep -E 'knowledge/|Source anchors|\[UNCERTAIN\]|reviewer|DRAFT'
# expect: no matches
```

Run for every tier (sample, essential, deep, compat basic, compat deep) as part of the build. The
existing worklog records a real incident where a reviewer note leaked into client PDFs (G1) — this
test is the reason it cannot happen again.

## Specialised gate 3 — the UI/UX audit (`tools/audit-ui.py`)

`06-frontend-ux.md` states an acceptance bar of measurable things — no horizontal body scroll at
390 / 768 / 1440, zero hydration warnings, axe clean on every screen, ≥44 px touch targets, one `<h1>`
per page, both themes — so none of it should be a matter of opinion. This runs the measurements in a
real Chrome against a deployed URL:

```bash
python3 tools/audit-ui.py                       # public pages, 3 viewports
AUDIT_EMAIL=… AUDIT_PASSWORD=… python3 tools/audit-ui.py   # + the pages behind the login
```

It reports, per page and viewport: HTTP status, elements forcing horizontal scroll (ignoring anything
inside an `overflow-x: auto` ancestor, which is *meant* to overflow), targets under 44 px (ignoring
inline prose links, which WCAG exempts), `<h1>` count, whether a shell/nav is present, hydration
warnings, and axe-core violations with the offending node.

The a11y engine is **`axe-core` as a devDependency of `apps/web`** (added 2026-10-16) so the audit and any
future end-to-end gate use the same version. Turnstile noise is filtered deliberately: it cannot solve a
challenge under automation, and counting that as a page defect drowns the real findings.

**Not yet in CI**, and it should be — a headless Chrome job on a preview deployment would turn this from
something a human remembers to run into a gate. That is the same gap as the Playwright public tier
([13](13-launch-audit.md) §B5).

**Authenticated runs need an account.** Use a throwaway, never your own, and delete it afterwards
(`neon neon-auth user delete <id>`, plus the `User` row and its dependants — see
[09](09-operations.md)).

## Specialised gate 2 — the compliance QA gate

`tools/qa_compliance.py` flags predictive language, master/guarantee claims, sensitive
medical/legal/financial advice, and missing hedging. It is **advisory, not blocking**, and it runs
during review rather than in CI (it needs `TYPESAFE_API_KEY` and a network call).

| In CI | In review |
|---|---|
| Never (network + cost) | Every report, surfaced in the admin console next to Approve |

If a flagged report is approved anyway, the reason should be recorded — the flags are a prompt for
judgement, not a verdict.

## What NOT to test

| Don't | Why |
|---|---|
| Engine derivation logic | **1,909 tests** already cover it. Re-testing through the HTTP layer is slow and duplicates |
| Report prose wording | Golden snapshots own it. Asserting on prose in the webapp creates two sources of truth |
| Third-party SDKs (Neon Auth, Dodo Payments, Resend internals) | Test our wrapper's contract, not their behaviour |
| The signature *scheme* itself | We do not test HMAC-SHA256's correctness — only that our verifier accepts what we sign and rejects everything else (below) |

### The end-to-end payment smoke test — the only check that uses a real secret

Every other test of the payment path mocks the provider or calls the verifier directly. One script
exercises the whole thing against a **real deployment with the real secret**:

```bash
npm run smoke:dodo                       # against https://www.cosmicsaju.com
npm run smoke:dodo http://localhost:3000 # against a local dev server
```

`scripts/dodo-webhook-smoke.mjs` asserts five things and exits non-zero if any fails:

| # | Assertion | Why |
|---|---|---|
| 1 | A validly signed event is accepted (2xx) | Proves the deployed secret matches Dodo's |
| 2 | The same `webhook-id` again returns 2xx **and** `{duplicate:true}` | Idempotency — Dodo retries until acknowledged |
| 3 | A tampered body is rejected (401) | |
| 4 | A tampered signature is rejected (401) | |
| 5 | A one-hour-old event is rejected (401) | Replay protection |

Safety: it sends `payment.succeeded` with a **non-existent `order_id`**, so it matches no order. It
writes exactly one harmless `WebhookEvent` row (verified: zero orders touched) — and the three rejections
write nothing at all, because they are refused *before* the database insert. The script never prints the
secret.

The signature is implemented **independently** of `src/lib/webhook-signature.ts` on purpose: re-reading
the Standard Webhooks spec in the script means agreement between the two is real evidence rather than a
tautology.

⚠️ Remember to **redeploy after changing an env var** — Vercel reads them at build/runtime start, so a
fresh secret is not live until the next deployment. A `503 WEBHOOK_UNCONFIGURED` almost always means
"variable set, deployment not yet made".

### Webhook signature verification — tested directly, never mocked

The payment webhook is the one place where being wrong is *silently* expensive in both directions:
too permissive and anyone can mark an order paid (a free report); too strict and real payments never
fulfil. It is therefore tested as pure logic, with no network, no database, and a fixed clock:

`src/lib/__tests__/webhook-signature.test.ts` — 13 cases:

| Case | Why it matters |
|---|---|
| Correctly signed payload accepted | The happy path |
| `whsec_`-less secret accepted | The prefix is optional in the spec |
| Multiple space-separated `v1,<sig>` candidates | Real headers carry more than one |
| **Tampered body rejected** | Re-serialising JSON must invalidate the signature |
| **Wrong secret rejected** | |
| **Tampered signature rejected** | |
| **Replay outside the 5-minute window rejected** | Without it, a captured event can be replayed forever |
| Event inside the window accepted | Guards against an over-strict tolerance |
| Missing `webhook-id` / `timestamp` / `signature` rejected | |
| Non-numeric timestamp rejected | |
| No secret configured rejected | A misconfigured deploy must fail closed, not open |
| Different `webhook-id`, same body rejected | The id is part of the signed content |
| Near-miss signature rejected | Confirms a constant-time compare rather than a prefix check |

`signStandardWebhook()` is exported alongside the verifier so a local test-sender can produce a valid
request — necessary because `dodo wh trigger` sends **unsigned** payloads that our handler correctly
rejects with 401.
| Vercel's cron scheduler | Assert our handler's behaviour given a request |
| Snapshot-testing the admin console's markup | Brittle, and it does not catch what matters (permissions, state transitions) |

## Test data rules

- **Never use real client birth data in tests.** The repository's `candidates_horoscope/` library
  contains real people's data (RM demo data is public-figure birth data; others are not). Use
  synthetic dates.
- Fixtures use explicit longitudes and timezones — never rely on an ambient default. A previous
  incident (`tests-geocoder`) was caused by exactly this.
- Pin any date-dependent reference date. Another previous incident (`test_premium_report` drifting
  with the wall clock) came from not doing so.
- The authed e2e tier runs against a **throwaway Neon branch**, created and dropped by the test run.
  Production is never a test target.

## Coverage expectations

| Surface | Target | Rationale |
|---|---|---|
| `src/lib/` (pure logic: tiers, roles, validation, r2 keys, queue math, consent) | **High** — this is where bugs are cheap to catch and expensive to miss | No I/O, fast, deterministic |
| API route handlers | **Behavioural**: status + error code + side effects | Assert the contract from [03](03-api-spec.md), not the implementation |
| React components | Rendering + a11y + the states that matter | Not every prop permutation |
| Engine (Python) | Unchanged policy — additive tests only | Existing suite is the standard |

Percentage targets are a poor goal here. The useful question is: *does every invariant in
[02 — Data model](02-data-model.md) §"Invariants" have a test that fails if it breaks?* Ten
invariants, ten tests, minimum.
