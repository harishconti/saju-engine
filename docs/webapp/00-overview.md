# 00 — Overview

## What we are building

Today this repository is an **engine plus a manual fulfilment service**: a Python chart engine, a
knowledge base, a PDF toolchain, a stored library of candidate readings, and a FastAPI intake app
whose paid orders queue for the owner to review and release one at a time.

The webapp turns that into a **self-service product**:

> A visitor lands on `cosmicsaju.com`, gets a free chart sample, creates an account, buys a report
> tier, and receives a reviewed PDF in their inbox and in their profile.

Nothing about the interpretive engine changes. The product is the **delivery and account layer**
around it.

## Positioning (inherited, not re-decided)

From [`docs/market-research-2026-09.md`](../market-research-2026-09.md):

- **Audience:** English-speaking global — K-culture fans and the diaspora. Not India-first.
- **Canonical line:** *"an accurate engine and an honest interpreter — not a Korean master."*
- **Prices:** USD. Essential $19, Deep Destiny $55, Compatibility Snapshot $24, Deep Compatibility
  $45, free sample. Cosmic Companion ($9/mo) is **out of scope for v1** — the docs already treat it
  as manual-billing, off the primary pricing grid.
- **Marketing hero:** the compatibility (궁합) product.
- **Honest ceiling:** a $1–3K/month side business with a realistic chance of never clearing $500.
  The architecture should be cheap, boring, and easy to delete — not a platform bet.

That last point is a design constraint, not a disclaimer. It is why the stack is "Vercel + Neon + R2
+ nothing else", why there is no queue broker, no microservice mesh, and no vendor that bills
monthly until it earns its keep.

## The target flow

```
                         ┌──────────────────────────────────────────────┐
   visitor               │  /  — landing page (public)                  │
      │                  │  hero · why saju · demo reports · pricing    │
      │                  │  tier comparison · how it's built · FAQ      │
      ▼                  └──────────────────────────────────────────────┘
   free sample  ──────────────────────────┐
   (no account, ~1.6s, instant PDF)       │
      │                                   │ "see what you get"
      ▼                                   │
   "save this to my profile" ──▶ sign in ─┘
      │                              (Google / email+password / magic link)
      ▼
  /dashboard  ──▶ /profiles   (birth data, stored once, reused forever)
      │
      ▼
  /reports/new  ──▶ pick tier ──▶ pick profile(s) ──▶ confirm
      │                                                  │
      │                                        paid tier ─┴─▶ Dodo Payments checkout
      │                                                  │        (Merchant of Record)
      │                                                  ▼
      │                                          webhook: order paid
      │                                                  │
      │                                          Job created (queued)
      │                                                  │
      │                                    cron: dispatcher → report engine
      │                                                  │
      │                                    PDF → Cloudflare R2 (private)
      │                                                  │
      │                                          Report: DRAFT_READY
      │                                                  │
      │                                    /admin: owner reviews, may set
      │                                    the 용신 override and regenerate
      │                                                  │
      │                                          approved
      │                                                  │
      └◀──── Resend email ◀──────────────────────────────┤
      └────  appears in /dashboard/reports ◀─────────────┘
```

**The free sample is the funnel.** It must stay instant and account-free, because it is the only
thing that answers "is this real?" before we ask for money. It is also the natural place to create a
profile: run the sample, then offer "keep this — create your account and I'll save these details".

## Report types offered

| Client-facing name | Engine tier | Price | Pages | Review required |
|---|---|---|---|---|
| **The Hook** (sample) | `sample` | Free | ~1 | **No** — instant, generated on demand |
| **The Essential Report** | `essential` | $19 | 6–7 | Yes |
| **The Deep Destiny Report** | `deep` | $55 | 25–30 | Yes |
| **Compatibility Snapshot** | compat `basic` | $24 | ~4 | Yes |
| **Deep Compatibility** | compat `deep` | $45 | 9–10 | Yes |

Legacy engine aliases (`spark` → essential, `reading`/`fullmap` → deep) remain valid at the engine
API but must **never** appear in the UI, the store, or a client-facing artefact.

## Locked decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | **Two Vercel projects** — `saju-engine` (root `apps/web`, Next.js) and `saju-report-engine` (root = **repository root**, Python at `api/index.py`) | The engine is Python and cannot be rewritten. Keeping it out of the Next project avoids Next's output tracing bundling `.next`/`public` into the Python function (the classic 250 MB failure). The engine's root is the repo root so it can import `src/` — Vercel bundles only files under the Root Directory, so a subdirectory root would hide the engine packages |
| D2 | **ReportLab PDF backend** in production | Chromium/Playwright does not fit a Vercel function. ReportLab is pure Python, already tested, and measured at ~0.6 s per deep report |
| D3 | **Rebuild the landing page inside `apps/web`** | `apps/landing-page/src/` is not in this repository (open item A1) and its recovery is not verifiable. A rebuild also gives one design system and one deployable |
| D4 | **Dodo Payments** as Merchant of Record | Acts as MoR, so it handles US sales tax and EU VAT and we never see card data. **Confirm its current fee schedule and onboarding requirements directly** — the ~5% + $0.50 figure belongs to Lemon Squeezy/Paddle and was not verified for Dodo. Chosen over Lemon Squeezy and Paddle. |
| D5 | **Always review before delivery** for every paid tier | Preserves the "honest interpreter" promise and the compliance gate. The free sample is the only instant product — and that is **enforced**, not assumed: `requiresReview` on the tier map is consulted by the dispatcher (`autoDelivers()`), so a tier that declares `requiresReview: false` is delivered on creation while everything else waits for a human. An unknown tier fails safe (review) |
| D6 | **Resend** for transactional email | Free tier covers ~3,000/month; the research already assumes it |
| D7 | **Cloudflare R2**, private bucket, presigned URLs | Zero egress fees; no public URL ever |
| D8 | **No PII column encryption** | Neon encrypts at rest; column encryption would break filtering and complicate every query for marginal gain over strict access control and "never log PII" |
| D9 | **Postgres-only state** — no Redis, no broker | Rate limits, idempotency, job leases, and the R2 deletion queue are all tables. One fewer vendor |
| D10 | **Vercel Pro** | Hobby crons are once-daily with a 2-cron maximum; the dispatcher needs per-minute. **Superseded 2026-10-26 (AU-13):** dispatch runs from the 15-minute GitHub Actions workflow, so Pro is no longer required — it would only restore a per-minute Vercel cron |
| D11 | **Dark by default, light from the OS** — `:root` is the brand surface and `@media (prefers-color-scheme: light)` swaps the token set | The light palette already existed and was never wired; honouring the OS makes `06`'s "both themes render" true without a toggle to maintain. No user-facing switch, deliberately — a half-considered light mode is worse than a deliberate dark identity |
| D12 | **The UI/UX bar is machine-checked** — `tools/audit-ui.py --strict` runs in CI as the `ui` job | The bar in [06](06-frontend-ux.md) is measurable (no overflow at three viewports, axe clean in both schemes, ≥44 px controls), so it should not depend on someone remembering to look. Its coverage is stated explicitly, including what it does *not* check |

## What already exists and is reused

Substantial parts of this system are already built and tested. The webapp is largely **wiring**:

| Existing asset | Reused as |
|---|---|
| `src/saju_engine/` — chart, compat, luck overlays, premium report | Called unchanged by the report engine service |
| `src/saju_html/` — markdown → PDF renderers | `md_to_saju_pdf.build_pdf` (ReportLab) behind a FastAPI endpoint |
| `src/saju_web/jobs.py` — `render_single` / `render_compat` | The core of the engine service; the geocode-free variants |
| `src/saju_web/jobs.py` — `is_stale`, lease semantics | The model for the Postgres job queue's stale-lease reclaim |
| `src/saju_web/notify.py` — SMTP link delivery | Replaced by Resend, but its opt-in/env-gated shape and "never raise" contract carry over |
| `src/saju_web/store.py` — encrypted store, token hashes, retention purge | **Retired.** Its guarantees are reimplemented on Postgres (see [02](02-data-model.md)) |
| `--favorable-override` (CLI + `compat_report`) | The admin review console's headline feature |
| `tools/qa_compliance.py` — prose compliance gate | Run during review, before approval |
| 1,909 pytest cases | The regression net that makes touching the engine safe |

## What is genuinely new

| Component | Why it cannot be reused |
|---|---|
| Next.js app (`apps/web`) | The current landing page's source is not available; the app needs accounts, orders, and a dashboard that never existed |
| Report engine service | The existing FastAPI app is stateful (SQLite), synchronous, and HTML/Playwright-based. The new one is stateless, queued, and ReportLab-based |
| Job queue + dispatcher | The current background-draft model is in-process threads on one machine; serverless needs lease-based claiming |
| Review console | `tools/intake_admin.py` is a CLI. Reviewing a PDF needs a browser |
| Payments | Nothing is charged today (open item D1) |

## Explicitly out of scope for v1

- **Cosmic Companion subscription.** The engine supports the tier; the billing does not.
- **Re-engineering the engine in TypeScript.** Non-starter against 1,909 tests.
- **Chromium-quality HTML PDF output.** See [05](05-report-pipeline.md) for the tradeoff and the
  escape hatch (a container-image function) if it ever matters.
- **Multi-tenant / team accounts.** One user, their profiles.
- **Tarot, Zi Wei Dou Shu, QMDM, Western astrology, standalone numerology.** Out of scope for the
  whole project per [`AGENTS.md`](../../AGENTS.md).
- **Public API / MCP server.** Parked in the research (§5) as an unsuccessful monetisation bet.
