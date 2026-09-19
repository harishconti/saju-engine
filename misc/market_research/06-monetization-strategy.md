# 06 · Monetization Strategy

**Date:** 2026-06-26
**Scope:** How the Saju project makes money. Existing tiered pricing is ₹499 / ₹1,499 / ₹3,499; this doc analyzes whether to keep that pricing, what adjacent revenue lines to add, and the revenue scenarios that result.

---

## 1. Existing monetization (built)

The project already ships three one-time report tiers via the premium report generator and self-service calculator:

| Tier | Name | Price (INR) | Price (USD approx) | Length | Delivery | Status |
|---|---|---|---|---|---|---|
| 1 | The Spark ✦ | ₹499 | ~$6 | 4–5 pages | Instant PDF | ✅ Built + self-service automated |
| 2 | The Reading ✦✦ | ₹1,499 | ~$18 | 10–12 pages | 48-hour SLA with human review | ✅ Built; review step is manual |
| 3 | The Full Map ✦✦✦ | ₹3,499 | ~$42 | 18–22 pages | 72-hour SLA with human review | ✅ Built; review step is manual |
| 4 (future) | The Companion ✦✦✦✦ | ₹799/month | ~$9.50/month | Quarterly check-in + monthly energetic guidance | Email + dashboard | ❌ Not built |

## 2. Is the existing pricing right?

**Yes — and here's why:**

1. **₹499 / $6 is the proven impulse-buy threshold** for spiritual content in India. AstroTalk's free chat + first-paid-question model operates in this band. A Spark-tier entry is exactly the right "yes, I'll try it" price.
2. **₹1,499 / $18 is the sweet spot for "considered purchase with strong value perception."** Comparable to Western astrology apps' "Your Year Ahead" at $11.99/year, and below the Korean Saju app segment's per-consultation range (₹300–1,500 / $3.50–$18 for human reader time).
3. **₹3,499 / $42 is high enough to feel premium but below the wedding-astrology tier.** Wedding astrology in India commands ₹10,000–50,000 per consultation; we're below that. We're also below the Korean long-form human reader rate of ~30,000원/~$22 per 5–10 minutes, which is session-based.
4. **The 7× ratio between tiers is correct.** It gives clear upsell logic without making Spark feel like a tease.
5. **The 6 paid pilots all bought Full Map at ₹3,499.** This is the highest-converting tier in our direct-fulfilment pipeline because the price-to-depth ratio is best.

**Recommendation:** keep the three tiers at the existing prices for India. Add a **USD-priced mirror** for Korean diaspora: $9.99 / $29.99 / $69.99 (the 7× ratio preserved, currency rounding).

## 3. Pricing for the Korean diaspora market (new tier structure)

For Korean-American / Korean-Canadian / Korean-Australian / Korean-British buyers, the price points need to be 1.5–2× higher than India to signal quality and to match US app pricing norms.

| Tier | India price | International price (USD) | Korean diaspora price (USD) |
|---|---|---|---|
| Spark | ₹499 | $9.99 | $14.99 |
| Reading | ₹1,499 | $29.99 | $49.99 |
| Full Map | ₹3,499 | $69.99 | $99.99 |
| Companion (future) | ₹799/mo | $14.99/mo | $19.99/mo |

For tier-3 global Hallyu-curious audience, the international USD pricing is correct.

## 4. Adjacent revenue lines to add (in priority order)

### Revenue Line 1: Compatibility add-on (₹999 standalone, or ₹499 bundled)
- **Demand:** Very high. Korean Saju 궁합 is a top-3 requested feature.
- **Build cost:** Medium — needs a new module in the engine.
- **Operational cost:** Low if template-based, medium if human-reviewed.
- **Pricing rationale:** Half the price of a Reading, because the input is two charts not one.
- **Time to launch:** ~6–8 weeks (build + test + payment integration).

### Revenue Line 2: Companion subscription (₹799/month)
- **Demand:** Unproven in our codebase. Western astrology apps (Co-Star, The Pattern) sustain large subscription bases.
- **Build cost:** High — needs user accounts, daily content engine, push notifications, quarterly review infrastructure.
- **Operational cost:** Medium — quarterly check-ins + monthly content.
- **Pricing rationale:** Below Co-Star's $8.99/month. Targeted at Full Map buyers as the natural upsell.
- **Time to launch:** ~16–20 weeks (full build).
- **Projected impact:** At 10% conversion of Full Map buyers = ~₹80k–3.5 lakh MRR in Year 1 depending on Full Map volume. This is the largest single revenue-line opportunity.

### Revenue Line 3: Auspicious-date picking (₹499 standalone or bundled into Full Map)
- **Demand:** Medium — useful for weddings, business launches, relocations.
- **Build cost:** Low — already supported by the engine's `sewoon.py` daily-luck overlay.
- **Pricing rationale:** Low ticket, fun add-on.
- **Time to launch:** ~2–3 weeks once the engine output is exposed via web UI.

### Revenue Line 4: Yearly "Year Ahead" subscription (₹999/year, or ₹499/year bundled)
- **Demand:** High (Western apps: "Your Year Ahead" at $11.99/year is the most-cloned feature).
- **Build cost:** Low — re-uses the Full Map annual section with personalization.
- **Pricing rationale:** Subscription lite, low commitment.
- **Time to launch:** ~6–8 weeks once the annual forecast engine is web-exposed.

### Revenue Line 5: Course / cohort (₹4,999–9,999 per person, 6-week cohort)
- **Demand:** Low initial, builds over 12–24 months.
- **Build cost:** Medium — needs curriculum, video, cohort management.
- **Pricing rationale:** Premium education tier.
- **Time to launch:** ~12+ months (post-Companion).
- **Projected impact:** 30–100 students per cohort × 2 cohorts/year × ₹7,000 avg = ₹4–14 lakh/year.

### Revenue Line 6: API / B2B white-label (revenue share + per-call fee)
- **Demand:** Low initial, builds over 24–36 months.
- **Build cost:** High — needs API, auth, rate limiting, partner onboarding.
- **Pricing rationale:** Per-call or per-month + rev-share.
- **Time to launch:** ~24+ months.
- **Projected impact:** 5–20 B2B partners × ₹2–10 lakh/year each = ₹10–200 lakh/year. Wide range.

## 5. Revenue model scenarios

Three scenarios with realistic numbers. All assume a solo founder for Year 1; a 2–4 person team by Year 2.

### Scenario A: Solo, slow growth (conservative)

| Quarter | What happens | Spark | Reading | Full Map | Companion | Monthly revenue |
|---|---|---|---|---|---|---|
| Q3 2026 | Self-service Spark launches; founder hand-delivers Reading + Full Map | 30 | 12 | 6 | 0 | ~₹65k/mo |
| Q4 2026 | Year-ahead push; first content marketing investments | 60 | 25 | 12 | 0 | ~₹1.25L/mo |
| Q1 2027 | Compatibility launches; PWA launches | 120 | 50 | 25 | 5 | ~₹2.7L/mo |
| Q2 2027 | Android app; first paid ads | 200 | 90 | 40 | 15 | ~₹4.9L/mo |
| **Q2 2027 ARR run-rate** | | | | | | **~₹59 Lakh/year** |

### Scenario B: Solo, fast growth (realistic base case)

| Quarter | What happens | Spark | Reading | Full Map | Companion | Monthly revenue |
|---|---|---|---|---|---|---|
| Q3 2026 | Self-service Spark launches; Reading/Full Map via personal referral | 80 | 35 | 15 | 0 | ~₹1.7L/mo |
| Q4 2026 | Year-ahead push; content engine active; first ₹20k ad spend | 200 | 80 | 40 | 5 | ~₹4.2L/mo |
| Q1 2027 | Compatibility launches; first Instagram Reels go viral | 500 | 180 | 80 | 30 | ~₹10.4L/mo |
| Q2 2027 | PWA + Android; 1 part-time reader hired; first B2B conversation | 800 | 300 | 140 | 80 | ~₹19.3L/mo |
| **Q2 2027 ARR run-rate** | | | | | | **~₹2.3 Crore/year** |

### Scenario C: With team + B2B (Year 2-3 upside)

Year 2–3 with 2 part-time readers, B2B API in beta, and content engine producing 20 articles/month + 30 reels/month:

| Quarter | Spark | Reading | Full Map | Companion | B2B | Course | Monthly revenue |
|---|---|---|---|---|---|---|---|
| Q3 2027 | 1500 | 500 | 250 | 200 | 2 | 0 | ~₹40L/mo |
| Q1 2028 | 3000 | 1000 | 500 | 500 | 8 | 30 | ~₹85L/mo |
| Q3 2028 | 5000 | 1800 | 900 | 1000 | 15 | 50 | ~₹1.5Cr/mo |
| **Year 3 ARR run-rate** | | | | | | | **~₹18 Crore/year** |

**Reality check:** Scenario C is optimistic but plausible if Year 1 hits Scenario B. The bottleneck is interpretation throughput — that's why hiring part-time readers is the critical Year 2 move.

## 6. Revenue mix target (Year 2)

```
One-time reports (Spark + Reading + Full Map): 60%
Companion subscription:                       25%
Compatibility / add-on:                        8%
Course / cohort:                               4%
B2B / API:                                     3%
```

This mirrors the mature Western astrology app revenue mix (Co-Star: ~72% subscription), but with a heavier one-time-report component because the Full Map at ₹3,499 is a high-margin, high-value product that the solo founder can hand-deliver.

## 7. Pricing experiments to run

1. **A/B test Spark at ₹399 vs ₹499.** ₹399 is the impulse-buy ceiling; ₹499 is the standard. If conversion drops less than 30% at ₹399, switch to ₹399.
2. **A/B test Reading at ₹999 vs ₹1,499.** ₹999 is the "considered purchase" sweet spot; ₹1,499 is premium. The Full Map buyers all went to ₹3,499 — they were not price-sensitive. The Reading tier is where price sensitivity is highest.
3. **Test a ₹7,999 "Full Map + 60-min personal consultation" tier.** Combines the PDF + a 60-minute call with the founder. Pricing test, not permanent.
4. **Test annual discount on Companion.** ₹799/month = ₹9,588/year. ₹6,999/year is a 27% discount; ₹4,999/year is 48% off. The 27% discount is the proven SaaS sweet spot.
5. **Test dynamic pricing for tier-2 (Korean diaspora).** The proposed $14.99/$49.99/$99.99 is the entry tier; raise to $19.99/$69.99/$149.99 if conversion holds.

## 8. What NOT to monetize

1. **Don't add per-minute chat.** Requires a reader network. Out of scope.
2. **Don't add a free + ads tier.** The brand position is premium; ads cheapen it.
3. **Don't add a "gemstones" or "yantras" shop.** Out of scope, separate business.
4. **Don't add a "buy a question" micro-payment.** Confuses the value ladder.
5. **Don't add tipping / donations.** Astrology + donation is a bad combination.
6. **Don't discount aggressively.** Discounts signal "the product isn't worth the price." Use trial tiers instead.
7. **Don't bundle Reading + Full Map.** Forces the customer to choose. Let them self-select.
8. **Don't add "premium add-ons" to Spark.** Spark is the funnel; up-sell to Reading, not within Spark.

## 9. Refund policy (must have from Day 1)

The single biggest business-killing risk is the refund dispute on a ₹3,499 Full Map that didn't resonate. A defensible refund policy is essential:

**Recommended policy:**

- **Spark (₹499):** No refunds. This is a digital product delivered instantly; the impulse-buy threshold is low.
- **Reading (₹1,499):** Refund within 7 days if the report is not delivered within the promised 48-hour SLA, OR if the report contains verifiable factual errors in the chart calculation (pillar wrong, hidden-stems wrong).
- **Full Map (₹3,499):** Refund within 14 days if the report is not delivered within 72 hours, OR contains chart errors, OR if the client attended the (optional) 30-minute clarification call and is still dissatisfied.

**Why this works:**
- Refunds-on-delivery-failure are standard and acceptable.
- Refunds-on-calculation-error are defensible because the calculation is verifiable.
- Refunds-on-subjective-dissatisfaction are the dangerous category — but the optional clarification call converts most "I'm not satisfied" into "actually I see it now."

**Communicate this clearly** on the intake form, on the receipt, and in the report itself.

## 10. Net revenue per order (after Razorpay / Stripe fees)

Assume Razorpay 2% + GST for India, Stripe 2.9% + $0.30 per transaction for international.

| Tier | Price (INR) | Gateway fee | Net revenue (INR) |
|---|---|---|---|
| Spark | ₹499 | ~₹14 | **₹485** |
| Reading | ₹1,499 | ~₹35 | **₹1,464** |
| Full Map | ₹3,499 | ~₹80 | **₹3,419** |
| Companion (monthly) | ₹799 | ~₹20 | **₹779** |

For USD-priced tiers, Stripe fees are ~3% of revenue. Margin is preserved.

## 11. Cost of revenue (the human-review bottleneck)

| Tier | Human review time | Cost per order at ₹500/hour |
|---|---|---|
| Spark | 0 min (automated) | ₹0 |
| Reading | 45 min | ₹375 |
| Full Map | 90–120 min | ₹750–1,000 |

**The Reading and Full Map margins are razor-thin** if the founder does the review at "founder opportunity cost" of ₹500/hour.

**Two ways to restore margin:**
1. **Hire part-time readers** at ₹200–300/hour in India. Reading margin improves to ~₹1,090. Full Map margin to ~₹2,440.
2. **AI-assisted review** where the engine does 70% of the draft, the human reviews in 15–20 minutes. Reading cost drops to ~₹125. Full Map cost to ~₹250. **This is the path to scale.**

## 12. Source-of-truth references

- Tiered pricing structure: [CLAUDE.md — Tiered Client Products](../../CLAUDE.md)
- Self-service calculator: [tools/client_intake_app.py](../../tools/client_intake_app.py)
- Intake form: [tools/client_intake_app.html](../../tools/client_intake_app.html)
- Premium report generator: [tools/saju_engine/premium_report.py](../../tools/saju_engine/premium_report.py)
- 6 paid pilots: [candidates_horoscope/reports/](../../candidates_horoscope/reports/)
