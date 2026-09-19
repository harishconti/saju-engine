# 09 · Product Roadmap — Build, Optimize, Enhance, Skip

**Date:** 2026-06-26
**Scope:** What to build, what to optimize, what to enhance, what to skip, organized by 12-month phases. Built on the feature-demand analysis from `04-feature-demand.md`, the platform decision from `07-app-platform-decision.md`, and the existing codebase inventory.

---

## 1. The product backlog, organized by 4-quadrant prioritization

Each item is scored against:

- **Demand intensity** (from `04-feature-demand.md`): H / M / L
- **Build effort** (solo founder, India-based): XS / S / M / L / XL
- **Revenue impact** (Year 1): ₹ / ₹₹ / ₹₹₹ / ₹₹₹₹

The roadmap combines these into a clear build sequence.

## 2. The four quadrants

```
                HIGH DEMAND
                    │
                    │   QUICK WINS            BIG BETS
                    │   (build first)         (build second)
                    │
                    │   Compatibility         Companion
                    │   Daily content         subscription
                    │   engine                User accounts
                    │   Web app + Razorpay    B2B API
                    │   SEO foundation        Course / cohort
                    │
LOW EFFORT ────────┼─────────────────────── HIGH EFFORT
                    │
                    │   FILL-INS             MONEY PITS (skip)
                    │   (build if time)      (don't build)
                    │
                    │   Lucky attributes      Native iOS app
                    │   PDF reference card    Live chat marketplace
                    │   Year-ahead email      Numerology / tarot
                    │   WhatsApp broadcast   Vedic Jyotish
                    │
                LOW DEMAND
```

## 3. Phase-by-phase roadmap

### Phase 0 — Now (pre-launch, weeks 0–4)

**Status:** Most of this is built. Verify, polish, and deploy.

| Task | Effort | Status | Notes |
|---|---|---|---|
| Web app shell (Next.js 14) | S | ❌ Missing | Need to deploy FastAPI behind a Next.js frontend |
| Domain + hosting (Railway / Fly.io) | XS | ❌ Missing | ₹500–2,000/month |
| Razorpay integration | S | ❌ Missing | 1 week of dev + Razorpay account setup |
| Stripe integration (international) | S | ❌ Missing | 1 week of dev + Stripe account |
| Intake form polish (existing at `tools/client_intake_app.html`) | XS | ✅ Built | Convert to React component |
| Self-service Spark flow end-to-end | S | 🟡 Partial | Engine + PDF works; needs payment + email + download |
| Spark `[ENGINE DRAFT — REVIEW REQUIRED]` removed (it's automated) | XS | ✅ Built | Already marked appropriately |
| Reading / Full Map human-review queue | S | ❌ Missing | Simple admin UI or Notion-based queue |

**Phase 0 deliverables:** Self-service Spark live and selling. Reading/Full Map available on request with 48–72 hour SLA.

### Phase 1 — Months 1–4 (build the foundation)

#### Quick wins (build first)

1. **Web app + Razorpay + Stripe + user accounts.** (S, ₹₹₹)
   - Next.js 14 SaaS frontend over existing FastAPI backend.
   - Email + magic-link auth via Clerk or Supabase.
   - Razorpay for India, Stripe for international.
   - **Demand: H. Effort: S. Revenue: ₹₹₹.**

2. **Compatibility (궁합) product.** (M, ₹₹₹)
   - New engine module: `tools/saju_engine/compatibility.py`.
   - Inputs: two charts (or two DOB+time+location).
   - Outputs: 합/충/형/파/해 mapping + element balance + day master relationship + ten-god cross-matrix + PDF deliverable.
   - Pricing: ₹999 standalone; ₹499 bundled into Reading+ upsell.
   - **Demand: H (Korean Saju's #1 requested feature). Effort: M. Revenue: ₹₹₹.**

3. **SEO content engine foundation.** (S, ₹₹₹₹)
   - 4 long-form pillar blog posts published.
   - Pricing page, FAQ page, about page, contact page.
   - Schema markup for Article + FAQ + Product.
   - Google Search Console + Naver Search Advisor setup.
   - **Demand: H (top-of-funnel). Effort: S. Revenue: ₹₹₹₹ (compounding over 6–12 months).**

4. **Instagram Reels kickoff.** (S, ₹₹₹₹)
   - 30 Reels filmed + posted in 30 days (Day Master Mondays etc.).
   - Cross-post to YouTube Shorts + TikTok.
   - **Demand: H. Effort: S. Revenue: ₹₹₹₣ (indirect).**

5. **Email list + welcome sequence.** (XS, ₹₹₣₹₣)
   - Resend (or ConvertKit) for email.
   - Welcome series: 5 emails over 14 days, education + soft sell to Spark.
   - **Demand: H. Effort: XS. Revenue: ₹₹₹₣ (compounding).**

#### Operational improvements

6. **Engine-draft → human-review workflow.** (S, ₹₹)
   - Simple admin UI showing incoming Reading/Full Map orders + the engine's premium markdown.
   - Founder reviews in 45–90 min, applies edits, generates final PDF, sends to client.
   - **Effort: S. Revenue: enables Phase-1 Reading/Full Map scaling.**

7. **Refund policy + admin tooling.** (XS, ₹)
   - Documented refund policy in CLAUDE.md.
   - Simple refund-via-Razorpay flow in admin UI.
   - **Effort: XS. Revenue: enables risk-managed scaling.**

#### Skip in Phase 1

- Native iOS / Android apps.
- Companion subscription infrastructure.
- Hindi / Korean localization.
- Course content.
- B2B API.

### Phase 2 — Months 5–8 (build the retention loop)

#### Big bets

1. **Daily content engine.** (M, ₹₹₣)
   - For each free email subscriber, generate a daily "your Day Master today" 1-paragraph reading.
   - Push via email (Resend) + web push (Firebase Cloud Messaging).
   - Drives free → Spark conversion via repeated exposure.
   - **Demand: H. Effort: M. Revenue: ₹₹₣₣₣ (compounding).**

2. **Companion subscription scaffolding.** (M, ₹₹₣₣₣)
   - User accounts already in place from Phase 1.
   - Add subscription billing (Razorpay Subscriptions + Stripe Subscriptions).
   - Build "Companion dashboard" showing quarterly check-in dates + monthly energetic guidance.
   - **Demand: M (unproven in our product). Effort: M. Revenue: ₹₹₣₣₣ (highest single MRR line).**

3. **PWA + Capacitor wrap → Android.** (M, ₹₹₣)
   - Convert web app to PWA (manifest + service worker).
   - Wrap with Capacitor for Play Store submission.
   - Play Store listing + ASO (Korean + English description, screenshots).
   - **Demand: H. Effort: M. Revenue: ₹₣ (indirect + app store discovery).**

4. **Year-ahead reminder campaign.** (S, ₹₹₣)
   - Each December: email all past customers "Your 2027 forecast is ready — order now."
   - Auto-generated from Full Map-tier structure; one-time per year.
   - **Demand: H. Effort: S. Revenue: ₹₹₣₣₣ (high-LTV repeat purchases).**

5. **Compatibility as upsell to Reading/Full Map.** (XS, ₹₹)
   - After Reading purchase, automated email: "Add partner compatibility for ₹499 — 50% off."
   - **Effort: XS. Revenue: ₹₹ (incremental).**

#### Optimization

6. **Engine-draft quality improvements.** (S, ₹₣)
   - Reduce human-review time from 45–90 min → 20–30 min by improving the prose scaffold.
   - Add named-entity recognition for client name + partner name (if compatibility).
   - Better default 용신 reasoning.
   - **Effort: S. Revenue: ₹₣ (margin improvement, not direct).**

7. **Conversion rate optimization on web app.** (S, ₹₣)
   - A/B test Spark at ₹399 vs ₹499.
   - A/B test Reading page layout.
   - Add exit-intent popup with "Free 2027 forecast preview."
   - **Effort: S. Revenue: ₹₣.**

#### Skip in Phase 2

- Native iOS app (Phase 4).
- Hindi localization (Phase 3).
- Course / cohort.
- B2B API.

### Phase 3 — Months 9–12 (scale + diversity)

#### Big bets

1. **Companion subscription launch.** (S, ₹₣₣₣₣₣)
   - Marketing push to existing Full Map buyers.
   - Quarterly check-in content cadence.
   - **Demand: M (unproven). Effort: S (already built in Phase 2). Revenue: ₹₣₣₣₣₣ (target: 50–200 subscribers by month 12).**

2. **Hindi localization.** (M, ₹₣)
   - Translate landing page + intake form + Spark into Hindi.
   - Hire Hindi-speaking astrologer consultant for translation review.
   - **Demand: M. Effort: M. Revenue: ₹₣ (India Tier-2 unlock).**

3. **Year-ahead free report as lead magnet.** (S, ₹₣₣₣₣₣)
   - "Free 2027 year-ahead Saju preview" — give the first 1,000 words for free, gate the rest.
   - Email capture → nurture → Spark / Reading conversion.
   - **Demand: H. Effort: S. Revenue: ₹₣₣₣₣₣₣ (top-of-funnel volume).**

4. **Paid Instagram ads.** (S, ₹₣)
   - After Phase 1 organic has reached 5,000 followers + 1,000 email subs.
   - Start with ₹20k/month budget.
   - **Demand: H. Effort: S. Revenue: ₹₣ (paid acquisition).**

5. **First influencer collaboration.** (S, ₹₣)
   - One Tier-1 micro-influencer in astrology / Korean culture.
   - Sponsored Reel + coupon code.
   - **Demand: M. Effort: S. Revenue: ₹₣ (brand awareness + direct).**

6. **Hire first part-time reader.** (S, ₹₣₣₣)
   - 1 part-time Saju reader at ₹200–300/hour in India.
   - Takes over Phase 2 review workload.
   - **Effort: S. Revenue: ₹₣₣₣ (margin improvement + throughput).**

#### Optimization

7. **Engine-draft → AI-assisted human review.** (M, ₹₣₣)
   - Use Claude (or similar LLM) to pre-edit the engine draft.
   - Human reviewer only checks + adds nuance.
   - **Effort: M. Revenue: ₹₣₣ (margin + scale).**

8. **Conversion to Companion from Full Map.** (S, ₹₣₣₣₣)
   - Automated email after Full Map delivery: "Stay on track with quarterly check-ins — ₹799/month."
   - **Effort: S. Revenue: ₹₣₣₣₣ (highest-LTV line).**

### Phase 4 — Year 2 (B2B + iOS + courses)

#### Big bets

1. **Native iOS app via Capacitor.** (M, ₹₣)
   - Wrap PWA for App Store.
   - Justified only if Android shows 10k+ installs and 4★+.
   - **Demand: H (Korean diaspora). Effort: M. Revenue: ₹₣ (Korean diaspora).**

2. **API / B2B white-label.** (L, ₹₣₣₣₣₣₣)
   - Package engine + premium report as API.
   - Onboard 3–5 B2B partners in Year 2.
   - **Demand: M (B2B). Effort: L. Revenue: ₹₣₣₣₣₣₣ (wide range).**

3. **Course / cohort.** (M, ₹₣₣₣₣₣)
   - "Introduction to Korean 명리" — 6-week paid cohort.
   - 30–100 students per cohort × 2 cohorts/year.
   - **Demand: L (long-tail). Effort: M. Revenue: ₹₣₣₣₣₣₣ (low volume, high margin).**

4. **Hire second part-time reader + operations person.** (S, ₹₣₣)
   - 1 part-time reader for Reading/Full Map.
   - 1 part-time ops person for admin + customer support.
   - **Effort: S. Revenue: ₹₣₣ (throughput).**

5. **YouTube long-form cadence.** (S, ₹₣₣₣)
   - 4 long-form videos per month.
   - **Effort: S. Revenue: ₹₣₣₣ (long-tail organic).**

### Phase 5 — Year 3 (international expansion + course ecosystem)

1. **Korean-language product.** (L, ₹₣₣₣₣₣)
   - Korean-language web app + Korean-reading team.
   - Targeting Korea domestic market via Naver + Korean-language content.
   - **Effort: L. Revenue: significant if executed.**

2. **"Master of Korean 명리" certification.** (L, ₹₣₣₣₣₣)
   - Long-form paid certification for serious students.
   - 6-month program at ₹50,000+ per student.
   - **Effort: L. Revenue: ₹₣₣₣₣₣ (small but high-margin).**

3. **Strategic exit options.** (XL, varies)
   - Acqui-hire by larger astrology platform.
   - Acquired by Hallyu Wave consumer product company.
   - Continue as lifestyle business at ₹2–4 crore ARR.

## 4. What to optimize (don't rebuild, refine)

### Engine (Python)

| Item | What to optimize | Effort |
|---|---|---|
| `lookup.py` Korean 명리 tables | Cross-check against 2–3 additional Korean classical texts | S |
| `pillars.py` solar-term boundary handling | Add the Korean textbook 만세력 case from validation wishlist | S |
| `premium_report.py` engine-draft quality | Improve prose scaffold so human-review time drops from 45–90 min → 20–30 min | M |
| `sewoon.py` daily-luck overlay | Make daily output JSON-serializable for web app consumption | S |
| `patterns.py` 천간합/화격/종격 | Lower false-positive rate; reduce [UNCERTAIN] noise | S |
| PDF rendering | Add Korean font fallback for international users; fix the day-master tofu bug (already fixed) | S |
| Test coverage | Add Korean textbook chart; add 1 Vedic edge case (irrelevant to us but useful for cross-Tradition compatibility) | S |

### PDF toolchain

| Item | What to optimize | Effort |
|---|---|---|
| Color palette | Strengthen brand identity; make sure Element Balance color coding is consistent | XS |
| Cover page | Improve typography; add Day Master emoji or symbol | XS |
| Page layout | Better table spacing; section dividers | XS |
| Citation handling | Verify citations stay in `.md` but never reach PDF | XS |

### Marketing site (Phase 1 build)

| Item | What to optimize | Effort |
|---|---|---|
| Page speed | <2s LCP on Indian 4G | M |
| Schema markup | Article + FAQ + Product + LocalBusiness | S |
| Content | 4 pillar posts + 4 service pages + 4 FAQ pages | M |

## 5. What to enhance (extend, not rebuild)

1. **Add Korean 명리 vocabulary inline.** Enhance the existing glossary + use it in report PDFs to teach the user the Korean term alongside the English. (CLAUDE.md ground rule #6.)
2. **Strengthen citation ground rules in every report.** Enhance the audit trail — every interpretive claim should be traceable to a `knowledge/*.md` file.
3. **Add classic-text references** (Gyeonglakgoyo, Jeokcheon-su, Yeonhae-japyeong, Gungtong-bogam) for serious buyers who want the citations.
4. **Enhance Element Balance visualization** with a circular chart (already color-coded table; add SVG radar chart).
5. **Enhance compatibility module** with 십신 cross-mapping and partner elemental analysis.
6. **Enhance daily-content engine** with lunar-phase + transit-overlay notes.

## 6. What to skip entirely

### Anti-feature list (do NOT build)

1. **Tarot readings.** Out of scope per CLAUDE.md.
2. **Dream interpretation (꿈해몽).** Out of scope.
3. **Face reading (관상).** Out of scope + privacy concerns.
4. **Numerology / life-path numbers.** Different tradition; dilutes positioning.
5. **AI chatbot UX.** 사주GPT already does this; the chatbot UX produces lowest-quality interpretations.
6. **Per-minute chat marketplace.** Requires reader network; not feasible for solo founder.
7. **Gemstone / yantra shop.** Separate business (inventory + fulfillment).
8. **Live streaming / video consultations.** Same constraint as per-minute chat.
9. **Generic "Will I be rich?" fortune-telling.** Brand-killer + ASCI violation.
10. **Vedic Jyotish features.** Out of scope + risks credibility with both traditions.
11. **Western astrology features.** Out of scope per CLAUDE.md.
12. **Custom ephemeris.** sajupy is sufficient.
13. **Building a native ephemeris from scratch.** Categorically no.

### Things to skip for now (defer but don't delete)

- iOS native app.
- Korean-language product.
- Companion subscription before Month 9.
- B2B API before Year 2.
- Course / cohort before Year 2.
- Hindi localization before Month 9.

## 7. The single most important product decision

**The single highest-impact product decision for Year 1 is: ship a self-service Spark that works end-to-end, and use that as the wedge to validate the funnel.**

Every other feature (Compatibility, Companion, PWA, etc.) is dependent on:
1. The Spark funnel working.
2. The Reading/Full Map conversion working.
3. The marketing engine producing qualified leads.

If the funnel doesn't convert at 2–5%, the rest of the product is irrelevant.

## 8. Sequenced delivery plan (Year 1)

| Week | Milestone |
|---|---|
| 0–4 | Web app shell + Razorpay + Stripe + user accounts + self-service Spark live |
| 4–8 | Compatibility (궁합) module + product page + ₹999 standalone |
| 8–12 | SEO content engine (4 pillar posts + 4 service pages) + Instagram Reels kickoff |
| 12–16 | Daily content engine (email + web push) + email welcome sequence |
| 16–20 | PWA conversion + Capacitor wrap for Android + Play Store submission |
| 20–24 | Year-ahead reminder campaign + Companion subscription scaffolding |
| 24–28 | Hindi localization + paid Instagram ads (after organic engine mature) |
| 28–32 | Companion launch + first part-time reader hire |
| 32–36 | First influencer collaboration + conversion rate optimization |
| 36–40 | Hindi marketing push + first paid Google Search ads test |
| 40–44 | iOS Capacitor wrap (if Android metrics support) |
| 44–48 | Year-1 review + Year-2 planning |

## 9. Risk-adjusted roadmap

If the founder has less time or runway than expected, **drop in this order** (least painful first):

1. **Drop:** iOS Capacitor wrap (Phase 4).
2. **Drop:** B2B API (Phase 4).
3. **Drop:** Course / cohort (Phase 4).
4. **Drop:** Hindi localization (Phase 3).
5. **Drop:** Influencer collaborations (Phase 3).
6. **Drop:** Companion subscription (Phase 3 — but this is the biggest revenue line; cut last).
7. **Drop:** Daily content engine (Phase 2 — but this is the retention loop; cut last).
8. **NEVER drop:** Web app + Razorpay + SEO + Instagram Reels. This is the foundation.

## 10. Sources

- See `04-feature-demand.md` for the demand ranking.
- See `06-monetization-strategy.md` for revenue projections.
- See `07-app-platform-decision.md` for platform picks.
- See `08-marketing-strategy.md` for marketing channels.
- See `11-financial-model.md` for detailed P&L.
