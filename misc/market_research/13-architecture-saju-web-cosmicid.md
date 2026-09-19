# 13 · Architecture — Saju Backend × Vercel Web × Cosmic ID Android

**Date:** 2026-06-26
**Scope:** How to split the Korean-Saju product across **Saju repo (backend)**, **a new Vercel web app (frontend for paid PDFs)**, and **Cosmic ID / AgeReveal (Android client for free + upsell)**. Includes what to change in the Cosmic ID codebase and the canonical feature split.

---

## 1. The verdict in one paragraph

**Make the Saju repo the backend.** It already contains the canonical engine (`tools/saju_engine/`), the citation-grounded knowledge base (`knowledge/`), the premium tiered report generator (`tools/saju_engine/premium_report.py`), and the PDF toolchain (`tools/md_to_saju_pdf.py`, `tools/md_to_saju_html_pdf.py`). All it needs is a thin HTTP layer wrapping the existing `compute_chart()` + `build_pdf_from_chart()` flow and a Postgres/Redis layer for user accounts, orders, and subscription state. **Add a new Next.js + Vercel web app** that talks to that backend via JSON — this is where paying customers buy Spark/Reading/Full Map and get tiered PDFs. **Keep Cosmic ID (AgeReveal) on-device for free features** (Korean Saju preview, 오행 balance, current 대운, daily fortune) and **deep-link to the web app for paid tiers** (Full Map PDF, Companion subscription, year-ahead). The Android app becomes a discovery + retention surface; the web app becomes the monetization surface.

---

## 2. The three layers

```
┌─────────────────────────────────────────────────────────────────────┐
│  ANDROID CLIENT — Cosmic ID / AgeReveal                             │
│  ─ on-device Korean Saju preview (free)                             │
│  ─ 오행 balance, 천간·지지 in Hangul, current 대운                   │
│  ─ Compatibility (single-screen, free)                              │
│  ─ Daily fortune / birthday reminders (existing v2.0 features)      │
│  ─ "Get Full Map →" deep-link to web app for paid tier               │
│  ─ In-app subscription (Google Play Billing) routes to Companion     │
│    via backend subscription state                                   │
│                                                                     │
│  Location: /mnt/data2/git_repos/AgeReveal/  (existing, KEEP)        │
│  Deploy:    Play Store                                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  HTTPS / JSON
                               │  (capabilities: chart-preview,
                               │   save-profile, link-account)
┌──────────────────────────────▼──────────────────────────────────────┐
│  WEB APP — Next.js 14 + Vercel                                     │
│  ─ Pricing page, FAQ, pillar SEO posts                              │
│  ─ Intake form (DOB + time + location + tier select)                │
│  ─ Razorpay (IN) + Stripe (Intl) checkout                           │
│  ─ User accounts (Clerk or Supabase)                                │
│  ─ Tiered PDF viewer + email delivery                               │
│  ─ Companion dashboard (subscription mgmt)                          │
│  ─ Admin queue: founder review of Reading/Full Map drafts           │
│                                                                     │
│  Location: NEW repo  saju-web/  at /mnt/data2/git_repos/            │
│  Deploy:    Vercel (existing Railway subscription retired)          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  HTTPS / JSON
                               │  (POST /v1/chart,
                               │   POST /v1/report/preview,
                               │   POST /v1/orders,
                               │   GET  /v1/orders/{id}/pdf)
┌──────────────────────────────▼──────────────────────────────────────┐
│  BACKEND — Saju Engine Service                                     │
│  ─ saju_engine.compute_chart()   (60-cycle, 십신, 12운성, 대운)     │
│  ─ saju_engine.premium_report    (tiered Spark/Reading/Full Map)    │
│  ─ md_to_saju_pdf / html_pdf     (PDF rendering, two backends)     │
│  ─ knowledge/  (11-file citation-grounded corpus)                   │
│  ─ POST /v1/chart             → Chart JSON                         │
│  ─ POST /v1/report/preview    → premium markdown (engine draft)     │
│  ─ POST /v1/report/finalize   → apply human-review deltas → PDF     │
│  ─ GET  /v1/orders/{id}/pdf   → signed URL or stream               │
│  ─ POST /v1/subscriptions     → webhook receiver (Razorpay+Stripe) │
│                                                                     │
│  Location: /mnt/data2/git_repos/saju/tools/  (existing)             │
│  Deploy:    Railway (existing subscription KEEP) or Fly.io           │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  DATA LAYER                                                         │
│  ─ Postgres (Neon / Supabase): users, orders, subscriptions         │
│  ─ S3 / R2 / Vercel Blob: generated PDFs                            │
│  ─ Resend: transactional email                                      │
│  ─ Razorpay / Stripe: payments                                      │
│  ─ Plausible / PostHog: analytics                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Why this split

### 3.1 The engine belongs on a server, not in an APK

`saju_engine/` is a Python module wrapping `sajupy` + 11 knowledge files + premium-report scaffold. Three reasons it must stay server-side:

1. **Updates ship instantly.** Pricing change, citation correction, new 섹션 in Reading tier — push to Railway, all clients see it next request. With on-device you'd ship a Play Store update.
2. **Premium tier is a heavy compute.** `premium_report.py` is multi-section markdown with overlay compositing — 5–15s on cold cache. Fine on a server, jank on a phone.
3. **The `knowledge/` corpus is the moat.** Keeping it on-device (in the APK) exposes the citation-grounded rules to anyone who unzips the APK. Server-side it stays private.

### 3.2 The web app is where money changes hands

Web app gets:
- **SEO surface** for "Korean Saju reading English" + 80–100 pillar posts (Google's 2026 YMYL rules disfavor apps for astrology content; web ranks).
- **Full Razorpay + Stripe flow** with checkout, webhook receipt, refund, tax handling.
- **Email + welcome sequence + PDF download** in one place.
- **Subscription dashboard** for Companion.

Android is great for **discovery + retention** but **terrible for SEO** and **fine for IAP** but worse than web for **Razorpay/Stripe** in India where UPI/cards/autopay dominate.

### 3.3 Cosmic ID stays free + on-device

The Android app already has 50k+ installs implied by the v2.0 production rollout, a working SajuKoreanCalculator.kt (673 LOC, lunar-java based, Hangul-first), and a Google Play Billing subscription (`premium_monthly` ₹49, `premium_yearly` ₹299). Throwing all that away to rebuild on Vercel+Capacitor would burn the existing acquisition funnel.

**Keep Cosmic ID as the free + IAP funnel. Push paid tiers to the web app.**

---

## 4. Backend changes in the Saju repo

### 4.1 Add: thin FastAPI wrapper around existing engine

Today: `tools/client_intake_app.py` is a working FastAPI app that:
- serves `client_intake_app.html` at `/`
- accepts form POST → calls `compute_chart()` → calls `build_pdf_from_chart()` → returns PDF

It works for solo-founder local use. Promote it to a production service by:

1. **Wrap with a versioned API** at `/v1/...` (additive, doesn't break the existing `/generate` for legacy clients).
2. **Pull user/orders state out of JSON files in `candidates_horoscope/intake/`** into Postgres.
3. **Add idempotency keys** on order creation (avoid double-charge on retry).
4. **Add webhook receivers** for Razorpay + Stripe.
5. **Add signed PDF URLs** (or stream through backend) — never expose PDFs at predictable paths.

Suggested new file: `tools/api_server.py`. Coexists with `client_intake_app.py`; the latter stays for local solo-founder use.

### 4.2 Add: Postgres schema (minimal)

```sql
-- users
id uuid pk, email text unique, name text, created_at timestamptz

-- profiles (one user → many birth profiles)
id uuid pk, user_id fk, name, gender, dob date, birth_time time,
birth_location text, lat real, lon real, utc_offset_min int

-- orders
id uuid pk, user_id fk, profile_id fk, tier text, price_inr int,
status text, gateway text, gateway_ref text, created_at timestamptz

-- subscriptions
id uuid pk, user_id fk, tier text, gateway text, gateway_ref text,
status text, current_period_end timestamptz

-- review_queue
id uuid pk, order_id fk, engine_draft_md text,
human_review_md text, reviewer text, status text, updated_at timestamptz
```

Neon (free tier) or Supabase Postgres are the obvious picks. Use SQLAlchemy 2.x async + Alembic migrations.

### 4.3 Add: minimal auth (Clerk or Supabase)

You don't want to write auth. **Use Clerk** for the web app (free tier covers hobby scale, magic-link auth out of the box). The Android app uses Google sign-in (already implied by Firebase Analytics) → exchange ID token at `/v1/auth/exchange` for a backend JWT.

### 4.4 Add: payment webhooks

- Razorpay webhook: `payment.captured`, `subscription.activated`, `subscription.cancelled`. Verify HMAC-SHA256 with secret.
- Stripe webhook: `checkout.session.completed`, `invoice.paid`, `customer.subscription.deleted`. Verify with `STRIPE_WEBHOOK_SECRET`.

Both flows should write to `orders` / `subscriptions` tables and trigger `tools/build-pdf.sh --from-chart ...` for the order, then email the customer.

### 4.5 Keep: existing engine + knowledge + PDF toolchain untouched

`tools/saju_engine/`, `tools/md_to_saju_pdf.py`, `tools/md_to_saju_html_pdf.py`, `tools/build-pdf.sh`, and `knowledge/` should **not** be modified for the API split — they're the canonical assets. Only the API layer and storage layer are new.

### 4.6 Keep: Railway subscription

The user already has Railway. **Keep it for the backend.** It's well-suited for FastAPI long-running services with Postgres add-on. Estimated cost at base case (Scenario B from `11-financial-model.md`):
- Railway Hobby plan: $5/mo + usage (~$5–20/mo at low traffic)
- Postgres add-on: $5/mo (free tier exists; paid when DB > 1GB)
- Total backend: **$10–25/mo** until you cross ~10k orders/mo

Vercel is for the **web app only** (Next.js frontend). Railway runs the Python.

### 4.7 What does NOT change

- `tools/saju_engine/` (calculation logic)
- `knowledge/` (citation corpus)
- `tools/build-pdf.sh` (PDF toolchain wrapper)
- `tools/client_intake_app.py` (legacy solo-founder local use)
- `candidates_horoscope/` (hand-written reports + pilot data)
- `tests/` (129 pytest cases — keep green)

---

## 5. New: Web app on Vercel

### 5.1 Stack

- **Framework:** Next.js 14+ App Router (server-rendered for SEO)
- **Styling:** Tailwind + the same brand CSS variables from `market_research_html/combined.html` (warm cream, dark navy headings, brass accent)
- **Auth:** Clerk
- **DB:** Neon Postgres (or Supabase) — same schema as backend
- **Payments:** Razorpay + Stripe Checkout
- **Email:** Resend
- **Analytics:** Plausible (self-hosted or .io)
- **Forms:** React Hook Form + Zod

### 5.2 Pages (URLs)

| Route | Purpose |
|---|---|
| `/` | Landing page (pricing, FAQ, pillar posts index) |
| `/saju-reading` | Spark/Reading/Full Map product page |
| `/compatibility` | 궁합 product page |
| `/pricing` | Tiered pricing table |
| `/blog/[slug]` | SEO pillar posts (4–8/month for Year 1) |
| `/blog` | Index |
| `/faq` | FAQ |
| `/about` | Founder bio + classical-tradition positioning |
| `/contact` | Form |
| `/legal/privacy` | GDPR + DPDP compliant privacy policy |
| `/legal/refunds` | Refund policy |
| `/onboarding` | 2-step intake (name+contact → DOB+time+location+tier) |
| `/checkout/[orderId]` | Razorpay/Stripe redirect |
| `/checkout/success` | Post-payment landing |
| `/dashboard` | User home (orders, subscription, profile) |
| `/dashboard/orders` | Order history + PDF downloads |
| `/dashboard/companion` | Subscription mgmt (cancel, update card) |
| `/dashboard/profile` | Birth profiles CRUD |
| `/admin/queue` | Founder review queue (Reading/Full Map drafts) |
| `/api/auth/[...clerk]` | Clerk webhooks |
| `/api/webhooks/razorpay` | Payment webhook |
| `/api/webhooks/stripe` | Payment webhook |
| `/api/chart/preview` | → proxies backend `/v1/chart` |

### 5.3 What it does NOT do

- **No chart calculation in the browser.** Always proxy to backend.
- **No PDF rendering in the browser.** Always fetch from backend `/v1/orders/{id}/pdf`.
- **No AI prompts on the frontend.** LLM-based review is backend-internal.

### 5.4 SEO

- Server-rendered (App Router default).
- Schema markup: `Article`, `FAQPage`, `Product`, `Organization`, `Person` (founder E-E-A-T).
- Sitemap auto-generated.
- `hreflang` for en/hi/ko future.
- Page speed budget: <2s LCP on Indian 4G.

### 5.5 Vercel cost

- Free tier covers hobby.
- Pro plan ($20/mo per seat) only when you need team features or >100GB bandwidth.
- **At base case Scenario B**, expect **$0–25/mo Vercel**.

---

## 6. Cosmic ID (AgeReveal) — what changes

The Android app has a real, working Saju layer already (`SajuKoreanCalculator.kt`, 673 LOC, lunar-java based, Hangul-first). It's *different* from the Saju repo's `sajupy`-based engine — simpler, less citation-grounded, no `knowledge/` corpus, no premium tiered reports.

### 6.1 The strategic question

**Two options for Korean Saju on Android:**

**Option A — Keep on-device SajuKoreanCalculator.kt, add deep-links to web app.**
- Pros: no APK size increase, no engine sync, on-device works offline (good for Indian rural 4G).
- Cons: two engines means two possible interpretations for the same chart (user complains "my phone says X, my web app says Y").

**Option B — Replace on-device Saju with backend calls.**
- Pros: single source of truth, server citations, no APK size hit from `knowledge/`.
- Cons: requires network for every Saju feature; degrades badly on poor connectivity; APK can't preview offline.

**Recommendation: Option A (keep on-device) for *free preview* features, add backend calls for *paid* features.**

Concretely:
- Day Master, 오행 balance, current 대운, daily fortune → **on-device** (free, offline-friendly)
- Full Map tier PDF, year-ahead, Companion check-ins → **deep-link to web app**

### 6.2 Specific code changes (minimal)

| File | Change | Why |
|---|---|---|
| `SajuKoreanCalculator.kt` | **Keep as-is.** Optionally surface a `[FREE PREVIEW — for Full Map detail, see cosmicsaju.com/saju]` watermark. | On-device stays the discovery surface. |
| `DetailsUnlockScreen.kt` | **Keep Overview/Western/Vedic tabs free.** Add a "Get Full Map →" button on the Korean Saju tab that opens a deep-link to `https://cosmicsaju.com/saju-full-map?profileId={id}` (profile data encoded in URL). | Drives paid conversion to web app without losing the free preview. |
| `CompatibilityScreen.kt` | **Keep the Western + Korean compatibility score** (50/50 blend). Optionally add a "Get 궁합 Full Report →" deep-link. | Compatibility is the #1 requested feature per `04-feature-demand.md`. |
| `PaywallScreen.kt` | **Add a third tier** for "Korean Saju Full Map" pointing to web app. The existing `premium_monthly` (₹49) and `premium_yearly` (₹299) **stay as Companion-style subscriptions** but route through backend for subscription state sync. | Don't break existing billing. |
| `BillingManager.kt` | **Add a webhook listener** to POST purchase events to backend `/v1/subscriptions`. Backend is the source of truth; the Android app reads cached state for UI. | Single subscription state across web + Android. |
| `UserPreferencesRepository` | **Add `webAppLinkToken`** — magic-link token generated by backend for one-tap web login from Android. | No password friction. |
| `MainActivity.kt` | **Handle new deep-links:** `cosmicid://saju-full-map`, `https://cosmicsaju.com/saju-full-map`. | App Links for Android 12+. |
| `OnboardingScreen.kt` | **Step 3 (after birth details): add "Sign in to sync with cosmicsaju.com" as an optional step.** | Bridge to web app account. |
| `CalculatorScreen.kt` | **Add a "Korean Saju" card** (currently lives in DetailsUnlockScreen). Make it more discoverable. | Korean Saju is the East-Asian pillar per CLAUDE.md. |
| `ShareCardGenerator.kt` | **Add `drawSajuKoreanBalanceCard()`** (already in roadmap) — 오행 radar card, free, shareable. | Drives organic discovery. |
| `BuildConfig.kt` | **Add `BACKEND_URL`** build config field (different per build type — debug = staging, release = prod). | Clean config. |

### 6.3 New feature additions (and whether to add them)

| Feature | Add to Cosmic ID? | Add to Web app? | Notes |
|---|---|---|---|
| Day Master preview | ✅ Yes (on-device) | — | Already in `SajuKoreanCalculator.kt` |
| 오행 balance | ✅ Yes (on-device) | — | Already in `SajuKoreanCalculator.kt` |
| Current 대운 | ✅ Yes (on-device) | — | Already in `SajuKoreanCalculator.kt` |
| Daily fortune | ✅ Yes (on-device) | — | Already shipped in v2.0 |
| Compatibility (Western+Korean blend) | ✅ Yes (on-device) | — | Already shipped |
| 궁합 full report PDF | ❌ No — deep-link | ✅ Yes | Avoids two-engine interpretation drift |
| Full Map tier PDF | ❌ No — deep-link | ✅ Yes | Citation-grounded, server-side |
| Year-ahead forecast | ❌ No — deep-link | ✅ Yes | Server-side |
| Companion subscription | ✅ Yes (existing Play Billing) | ✅ Yes (Razorpay/Stripe) | **Both** — sync via backend |
| Companion dashboard | ❌ No — deep-link | ✅ Yes | Web UX is richer |
| Compatibility product (₹999 standalone) | ❌ No — deep-link | ✅ Yes | The #1 market gap |
| Annual report (December reminder) | ✅ Push notif | ✅ Email + landing | Push + email both |
| Spark (₹499 PDF) | ❌ No — deep-link | ✅ Yes | Free preview already covers most of this |
| Reading (₹1,499 PDF) | ❌ No — deep-link | ✅ Yes | Founder-reviewed, server-side |
| Sipsin 십신 table | ✅ Yes (on-device, free preview) | ✅ Yes (full Reading+) | Free preview shows top-3 only |
| 12운성 chart | ✅ Yes (on-device) | ✅ Yes | Same data both sides |
| 신살 (special stars) | ❌ No — server-only | ✅ Yes | Requires `knowledge/stars.md` corpus |
| 궁합 (sipsin cross-matrix) | ⚠️ Free preview only | ✅ Yes (full report) | Free shows score; paid shows full matrix |
| In-app Korean Saju IAP (₹149 one-time) | ⚠️ Deprecate | — | Roadmap Mission 7 lists this, but it conflicts with web-app monetization. **Recommendation: skip in favor of web deep-link.** See §6.4. |
| Lunar phase widget | ✅ Yes (existing) | — | Glance widget already shipped |
| Birthday widget | ✅ Yes (existing) | — | Glance widget already shipped |
| Friend / family profile sharing | ⚠️ Defer | ✅ Yes (later) | Needs user accounts first |

### 6.4 Whether to build the Korean Saju IAP in Cosmic ID

The Cosmic ID roadmap (Mission 7) lists a one-time ₹149 Korean Saju Premium Unlock IAP as a v2.1 item. **Recommendation: do not ship this.** Reasons:

1. **Two-engine interpretation drift** is the single biggest product risk. A user who runs Saju on Android (gets version A) and on web (gets version B) will spot differences and trust collapses.
2. **The web app is the better monetization surface** — SEO drives free → paid; Android drives free → web → paid. Killing the web funnel with an in-app IAP removes the SEO moat.
3. **Play Billing fees (15–30%)** are higher than Razorpay (2%) + Stripe (3%). Keeping IAP on the cheap-tier subscription and pushing paid tiers to the web preserves margin.
4. **The free preview on Android is itself a major moat** — 50k+ installs already, vs. the web app starting from zero. Don't give users a reason to not come back to the app.

Instead, replace this roadmap item with: **"Korean Saju Full Map deep-link to web app + free 오행 radar card"**.

### 6.5 Whether to add full Premium IAP

The existing `premium_monthly` (₹49) and `premium_yearly` (₹299) subscriptions already exist on Cosmic ID. **Keep these** as the **free-tier → IAP** upgrade path inside the app, but reframe them:

- **Today:** premium unlocks all tabs in DetailsUnlockScreen.
- **After this split:** premium stays as **"premium themes + remove banner ads + unlimited saved profiles"** (existing behavior). The deep astrological content (Full Map / Reading / 궁합 full report) lives on the web app.

This protects existing IAP revenue while letting the web app own the high-LTV tiers.

### 6.6 APK size impact

SajuKoreanCalculator.kt + SajuKoreanCompatibilityCalculator.kt already ship in the APK. **No new dependencies.** Adding web deep-link handling + a magic-link token field is <1KB. Estimated APK size delta: **<10KB**.

If you later go Option B (replace on-device Saju with backend calls), APK size **drops** by ~150KB (the lunar-java library + 673 LOC Kotlin), but you lose offline preview. Trade-off.

---

## 7. Cross-cutting concerns

### 7.1 Single source of truth for chart data

The backend's `compute_chart()` is the canonical engine. Cosmic ID's `SajuKoreanCalculator.kt` is an approximation. To prevent drift:

1. Add a "What is Korean Saju" educational screen in the Android app that **explicitly notes** the on-device preview uses a simplified algorithm, and the web app uses the classical-tradition engine.
2. Don't promise identical readings across surfaces.
3. For any user who logs in (via magic link from Android to web app), the web app **recomputes** the chart from raw birth data — never trusts the on-device chart output.

### 7.2 Auth bridge

When a Cosmic ID user wants to upgrade to a paid tier:

1. User taps "Get Full Map →" in Android.
2. Deep-link opens `https://cosmicsaju.com/saju-full-map?profileId={encoded-birth-data}`.
3. Web app shows pricing. If user clicks "Buy," web app asks for sign-in.
4. If user is signed in to Cosmic ID via Google, backend exchanges ID token at `/v1/auth/exchange` for a JWT.
5. Web app uses JWT to create an order tied to the user's `profileId`.

If the user isn't signed in to Cosmic ID on Android, the web app falls back to email + magic-link auth (Clerk).

### 7.3 Payment routing

- **Inside Cosmic ID (existing IAP):** Google Play Billing → Play Console. Backend listens to Real-Time Developer Notifications (RTDN) via Google Pub/Sub → backend `/v1/webhooks/google-play` → updates `subscriptions` table.
- **Web app (new):** Razorpay for India (UPI + cards + netbanking), Stripe for international. Backend listens to webhooks → updates `orders` / `subscriptions`.

A user can have **both** a Play subscription (premium-monthly) and a web subscription (Companion). These are tracked separately. The web subscription is the high-LTV one.

### 7.4 Data flow

```
Android intake (birth data)
    │
    ▼  (deep-link)
Web app intake form
    │
    ▼  POST /v1/chart
Backend computes chart (sajupy + lookup + patterns)
    │
    ▼  POST /v1/report/preview  (tier=reading|fullmap)
Backend generates engine-draft markdown
    │
    ▼  row inserted into review_queue
Founder / part-time reader reviews in /admin/queue
    │
    ▼  POST /v1/report/finalize  (with human_review_md)
Backend applies deltas, renders PDF, stores in S3/R2
    │
    ▼  email customer (Resend)
PDF download link in /dashboard/orders
```

### 7.5 Failure modes

- **Backend down** → web app shows "Temporarily unavailable, retry shortly." Android on-device features still work.
- **Razorpay webhook missed** → backend has a 5-minute poll task that calls Razorpay's `/orders/{id}/payments` to reconcile.
- **Stripe webhook missed** → backend has a 1-hour poll task that calls Stripe's `/events` for reconciliation.
- **PDF generation fails** → user gets a refund voucher + email; order marked `needs_retry`.
- **Founder unavailable** → review queue shows SLA breaches (>72h); auto-pause self-service acquisition.

---

## 8. Migration / rollout sequence

### 8.1 Week 1–2 (no code change yet)

- Stand up the backend skeleton on Railway: FastAPI app, Neon Postgres, S3 (or Vercel Blob), Clerk, Resend.
- Stand up the Vercel web app skeleton: Next.js, Clerk, Razorpay test mode, Stripe test mode.
- Confirm `tools/client_intake_app.py` runs on Railway as-is.
- **Keep Cosmic ID untouched.**

### 8.2 Week 3–4

- Add `/v1/chart`, `/v1/report/preview`, `/v1/report/finalize` to backend.
- Wire up Razorpay + Stripe on web app with test mode.
- Add `/admin/queue` for founder review.
- First end-to-end test: web app → backend → PDF → email.

### 8.3 Week 5–6 (soft launch)

- Switch Razorpay + Stripe to live mode (small initial volume).
- Switch web app to a real domain (e.g. `cosmicsaju.com` or `saju.com` — pick based on brand priority; the user owns `cosmic-id` already).
- Update Cosmic ID's `DetailsUnlockScreen.kt` "Korean Saju" tab to add the "Get Full Map →" deep-link.
- Update `MainActivity.kt` to handle the deep-link.
- Update `BuildConfig.kt` with `BACKEND_URL`.
- Ship Cosmic ID v2.1.0 to Play Store (small change, low risk).

### 8.4 Week 7–8

- Add SEO pillar posts (4 long-form posts).
- Start Instagram Reels kickoff.
- First paid orders via web app.
- Founder review queue active.

### 8.5 Week 9–12

- Add Companion subscription to web app.
- Add Companion tier sync from Cosmic ID via backend RTDN.
- First part-time reader hire.
- Re-evaluate against milestone gate G1 (Month 1 of commercial launch).

---

## 9. Cost summary (Year 1, Scenario B from `11-financial-model.md`)

| Service | Monthly cost | Annual cost |
|---|---|---|
| Railway Hobby + Postgres add-on | $15 | $180 |
| Vercel Pro (only if needed) | $20 | $240 |
| Neon Postgres (free tier covers Year 1) | $0 | $0 |
| S3 / Vercel Blob (free tier covers Year 1) | $0 | $0 |
| Resend (free tier covers Year 1) | $0 | $0 |
| Plausible (free self-host or $9/mo .io) | $9 | $108 |
| Clerk (free tier covers Year 1) | $0 | $0 |
| Razorpay fees (2% of revenue) | variable | ~₹90,000 on ₹45L |
| Stripe fees (3% of international, ~10% of total) | variable | ~₹40,000 on ₹15L international |
| Domain | $1/mo | $12 |
| **Total backend + web infra (fixed)** | **$45/mo** | **~$540/yr** |

Add ~₹1.3 lakh gateway fees per year. These scale linearly with revenue.

Compare to the existing state: ~$0/mo (local FastAPI, no cloud). The new cost is ~$540/yr + ~₹1.3 lakh gateway — a fraction of the ₹14 lakh annual cost in Scenario B.

---

## 10. What to drop from this plan if runway is tight

If personal runway is <₹8 lakh and you want to minimize infra spend, **drop these in order**:

1. **Vercel Pro** — use free tier; revisit at 10k+ visitors/mo.
2. **Clerk** — replace with self-hosted Supabase Auth (free, more setup).
3. **S3 / Vercel Blob** — store PDFs on Railway local disk initially (loses redundancy).
4. **Plausible .io** — use free Umami self-hosted.
5. **Resend paid tier** — use Gmail SMTP via Nodemailer for the first 100 orders.

Realistic minimum backend cost: **$5/mo Railway + domain**. You can ship Scenario A on this.

---

## 11. Summary checklist

### Saju repo (backend) — keep
- [x] `tools/saju_engine/` (engine, 17 modules, 129 tests)
- [x] `knowledge/` (11-file citation corpus)
- [x] `tools/md_to_saju_pdf.py` + `tools/md_to_saju_html_pdf.py`
- [x] `tools/build-pdf.sh`
- [x] `tools/client_intake_app.py` (legacy solo-founder use)
- [x] `tests/` (129 pytest cases — keep green)

### Saju repo (backend) — add
- [ ] `tools/api_server.py` (FastAPI wrapper, `/v1/*` routes)
- [ ] `tools/auth.py` (Clerk JWT verification + Google ID token exchange)
- [ ] `tools/webhooks_razorpay.py` + `tools/webhooks_stripe.py`
- [ ] `tools/webhooks_google_play.py` (RTDN receiver)
- [ ] Postgres schema migrations (Alembic)
- [ ] Deployment config (Railway Procfile or `railway.toml`)
- [ ] `.env.example` with all required env vars

### New: Vercel web app — full build
- [ ] `saju-web/` repo at `/mnt/data2/git_repos/`
- [ ] Next.js 14 + App Router
- [ ] Pricing, FAQ, About, Blog, Onboarding pages
- [ ] Razorpay + Stripe checkout
- [ ] Clerk auth
- [ ] /admin/queue founder review UI
- [ ] /dashboard user + Companion mgmt
- [ ] Resend email templates
- [ ] SEO: schema markup, sitemap, hreflang stubs
- [ ] Analytics: Plausible

### Cosmic ID (AgeReveal) — keep
- [x] `SajuKoreanCalculator.kt` (on-device preview, 673 LOC)
- [x] `SajuKoreanCompatibilityCalculator.kt`
- [x] `BaZiCalculator.kt`
- [x] All v2.0 features (Calculator, Compatibility, Reminders, Timeline, Paywall, Settings, etc.)
- [x] `BillingManager.kt` + Play Billing subscriptions

### Cosmic ID (AgeReveal) — modify
- [ ] `DetailsUnlockScreen.kt` — add "Get Full Map →" deep-link button on Korean Saju tab
- [ ] `CompatibilityScreen.kt` — add "Get 궁합 Full Report →" deep-link button
- [ ] `MainActivity.kt` — handle new deep-links
- [ ] `BuildConfig.kt` — add `BACKEND_URL` per build type
- [ ] `UserPreferencesRepository.kt` — add `webAppLinkToken` field
- [ ] `BillingManager.kt` — POST purchase events to backend `/v1/subscriptions`

### Cosmic ID (AgeReveal) — explicitly do NOT add
- [ ] ❌ Korean Saju Premium IAP (₹149 one-time) — replace with deep-link to web app
- [ ] ❌ Server-side Saju engine calls for free features — keep on-device
- [ ] ❌ PDF rendering in-app — push to web app

### Cosmic ID (AgeReveal) — optionally add later
- [ ] `ShareCardGenerator.drawSajuKoreanBalanceCard()` (오행 radar) — already in roadmap
- [ ] Push notification on year-ahead availability (December campaign)
- [ ] App Actions / App Links for "Korean Saju" intent (deep SEO on Android)

---

## 12. Sources

- Saju repo: [`CLAUDE.md`](../../CLAUDE.md), [`tools/saju_engine/`](../../tools/saju_engine/), [`tools/client_intake_app.py`](../../tools/client_intake_app.py), [`pyproject.toml`](../../pyproject.toml)
- Cosmic ID repo: [`/mnt/data2/git_repos/AgeReveal/CLAUDE.md`](/mnt/data2/git_repos/AgeReveal/CLAUDE.md), `SajuKoreanCalculator.kt`, `SajuKoreanCompatibilityCalculator.kt`, `BaZiCalculator.kt`
- Market context: [`02-market-size-and-demand.md`](02-market-size-and-demand.md), [`07-app-platform-decision.md`](07-app-platform-decision.md), [`11-financial-model.md`](11-financial-model.md)
- Vercel pricing: <https://vercel.com/pricing>
- Railway pricing: <https://railway.app/pricing>
- Neon Postgres pricing: <https://neon.tech/pricing>
- Razorpay fees: <https://razorpay.com/pricing/>
- Stripe fees: <https://stripe.com/pricing>
- Clerk pricing: <https://clerk.com/pricing>
- Resend pricing: <https://resend.com/pricing>
- Google Play Billing fees: <https://support.google.com/googleplay/android-developer/answer/112662>