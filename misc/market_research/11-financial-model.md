# 11 · Financial Model — Revenue, Costs, Break-Even, P&L

**Date:** 2026-06-26
**Scope:** Realistic unit economics, three revenue scenarios (conservative / base / optimistic), 12-month and 36-month P&L, break-even analysis, and the funding question.

---

## 1. Unit economics

### Revenue per order (after gateway fees)

| Tier | Price (INR) | Razorpay fee (~2% + GST) | Net revenue |
|---|---|---|---|
| Spark | ₹499 | ~₹14 | **₹485** |
| Reading | ₹1,499 | ~₹35 | **₹1,464** |
| Full Map | ₹3,499 | ~₹80 | **₹3,419** |
| Companion (monthly) | ₹799 | ~₹20 | **₹779** |
| Compatibility (standalone) | ₹999 | ~₹24 | **₹975** |

For international orders (Stripe ~3% fee):
- Spark $9.99 → $9.69 net
- Reading $29.99 → $29.09 net
- Full Map $69.99 → $67.89 net
- Companion $14.99/mo → $14.54 net

### Cost of revenue (CoR) per order

| Tier | Human review time | Review cost (₹500/hr founder / ₹250/hr part-time reader) | Other CoR (PDF gen, email) | Total CoR |
|---|---|---|---|---|
| Spark | 0 min (automated) | ₹0 | ₹5 | **₹5** |
| Reading | 45 min founder / 25 min part-time | ₹375 / ₹104 | ₹10 | **₹385 / ₹114** |
| Full Map | 90 min founder / 50 min part-time | ₹750 / ₹208 | ₹15 | **₹765 / ₹223** |
| Companion (per month served) | 15 min (email/quarterly) | ₹62 | ₹5 | **₹67** |
| Compatibility | 30 min founder / 15 min part-time | ₹250 / ₹62 | ₹10 | **₹260 / ₹72** |

**Gross margin per order (founder reviewing):**
- Spark: ₹480 (96%)
- Reading: ₹1,079 (74%)
- Full Map: ₹2,654 (78%)
- Companion: ₹712 (91% per month)
- Compatibility: ₹715 (73%)

**Gross margin per order (part-time reader reviewing, Phase 3+):**
- Reading: ₹1,350 (92%)
- Full Map: ₹3,196 (93%)
- Compatibility: ₹903 (93%)

### Customer acquisition cost (CAC)

| Channel | Est. CAC (India, blended) |
|---|---|
| Organic SEO | ₹50–200 |
| Instagram organic | ₹30–150 |
| Personal referral | ₹0–100 |
| Paid Instagram ads | ₹200–800 |
| Paid Google ads (high-intent only) | ₹300–1,000 |
| Influencer collaboration (micro) | ₹500–2,000 per attributed customer |
| Blended target (Phase 3+) | **₹400–800 per paying customer** |

### LTV (lifetime value per paying customer)

Conservative estimate based on Western astrology app churn benchmarks (22% annual churn for subscription, ~50% repeat purchase for one-time reports):

- **Spark buyer LTV:** ₹499 (one-time, low repeat). 30% buy Reading within 12 months = +₹450 LTV. **Total LTV: ~₹950.**
- **Reading buyer LTV:** ₹1,499 (one-time). 25% buy Full Map within 12 months = +₹875 LTV. 10% buy Companion (₹799 × 12 = ₹9,588 if annual) = +₹960 blended = +₹96 (since 10% buy monthly and average 4 months). **Total LTV: ~₹2,470.**
- **Full Map buyer LTV:** ₹3,499 (one-time). 30% buy Companion (avg 6 months) = +₹1,438. 40% buy year-ahead renewal next year = +₹1,400. **Total LTV: ~₹6,337.**
- **Compatibility buyer LTV:** ₹999. 20% buy Reading within 6 months = +₹300. **Total LTV: ~₹1,299.**

### LTV : CAC ratio

| Tier | LTV | Blended CAC | LTV : CAC |
|---|---|---|---|
| Spark | ₹950 | ₹400 | 2.4 : 1 |
| Reading | ₹2,470 | ₹600 | 4.1 : 1 |
| Full Map | ₹6,337 | ₹800 | 7.9 : 1 |
| Compatibility | ₹1,299 | ₹500 | 2.6 : 1 |

**Target LTV : CAC ratio:** ≥ 3 : 1 for sustainable paid acquisition. We're at or above this for all tiers except Spark (which is fine — Spark is the funnel, not the profit center).

### Payback period

- Spark: 1 order pays back acquisition cost in <1 month.
- Reading: 1.5 months to pay back.
- Full Map: 1.5 months to pay back (lowest payback because LTV is highest).

## 2. Cost structure (monthly, solo founder)

### Fixed costs (Phase 1, solo founder)

| Item | Monthly cost (INR) |
|---|---|
| Founder "salary" (living expenses, not profit) | ₹1,00,000 |
| Hosting (Railway / Fly.io) | ₹2,000 |
| Domain + email (Resend) | ₹1,500 |
| Razorpay + Stripe fees (variable, ~2% of revenue) | variable |
| S3 / R2 storage (PDFs) | ₹500 |
| Plausible / PostHog analytics | ₹0 (free tier) |
| Misc (Zoom, Notion, software) | ₹3,000 |
| **Total fixed costs** | **₹1,07,000** |

### Variable costs (Phase 1)

- Gateway fees: 2% of revenue.
- PDF generation: ~₹5–15 per order (negligible).
- Email delivery: ~₹0.10 per email (negligible).
- Founder review time: 45–90 min per Reading/Full Map.

### One-time costs (Phase 1)

| Item | Cost (INR) |
|---|---|
| Domain | ₹800/year |
| Play Console account | ₹2,000 (one-time) |
| Apple Developer account | ₹8,800/year (only when needed) |
| Razorpay setup | ₹0 |
| Stripe setup | ₹0 |
| Initial Next.js web app build (founder dev time) | founder's hours |
| Initial SEO content (4 posts) | founder's hours |

**Phase 1 total one-time cost: ~₹10,000** (excluding founder time).

### Scaling costs (Phase 3+)

| Item | Monthly cost (INR) |
|---|---|
| Part-time reader (₹250/hr × 80 hrs) | ₹20,000 |
| Part-time ops/support (₹250/hr × 40 hrs) | ₹10,000 |
| Paid Instagram ads | ₹20,000 |
| Influencer collaborations (1/month) | ₹15,000 |
| Translation services (Hindi) | ₹5,000 |
| Email list growth tools (ConvertKit) | ₹5,000 |
| **Total Phase 3 scaling cost** | **₹75,000** + variable |

## 3. Three revenue scenarios

### Scenario A — Conservative (slow growth, no viral moment)

**Assumptions:**
- Self-service Spark launches month 1.
- Reading/Full Map hand-delivered via founder + personal network.
- SEO content engine produces 8 articles/month.
- Instagram Reels produce modest growth (no viral moment).
- No paid ads in Year 1.
- Companion subscription doesn't launch.

| Month | Spark | Reading | Full Map | Compatibility | Companion | Monthly revenue | Monthly costs | Net |
|---|---|---|---|---|---|---|---|---|
| M1 | 5 | 2 | 1 | 0 | 0 | ₹8,265 | ₹1,07,000 | -₹98,735 |
| M2 | 8 | 3 | 2 | 0 | 0 | ₹14,374 | ₹1,07,000 | -₹92,626 |
| M3 | 12 | 5 | 3 | 0 | 0 | ₹22,063 | ₹1,07,500 | -₹85,437 |
| M4 | 18 | 7 | 4 | 0 | 0 | ₹31,900 | ₹1,08,000 | -₹76,100 |
| M5 | 25 | 10 | 5 | 0 | 0 | ₹42,750 | ₹1,08,500 | -₹65,750 |
| M6 | 30 | 12 | 6 | 0 | 0 | ₹50,964 | ₹1,09,000 | -₹58,036 |
| M7 | 35 | 14 | 7 | 0 | 0 | ₹59,153 | ₹1,09,500 | -₹50,347 |
| M8 | 40 | 16 | 8 | 0 | 0 | ₹67,432 | ₹1,10,000 | -₹42,568 |
| M9 | 45 | 18 | 9 | 5 | 0 | ₹85,500 | ₹1,11,000 | -₹25,500 |
| M10 | 50 | 20 | 10 | 8 | 0 | ₹99,712 | ₹1,12,000 | -₹12,288 |
| M11 | 55 | 22 | 12 | 12 | 0 | ₹120,375 | ₹1,13,000 | +₹7,375 |
| M12 | 60 | 25 | 15 | 15 | 0 | ₹141,825 | ₹1,14,000 | +₹27,825 |
| **Year 1 total** | **383** | **154** | **82** | **40** | **0** | **~₹7,44,313** | **~₹13,16,000** | **~₹-5,71,687** |

**Scenario A interpretation:** Solo founder loses ~₹5.7 lakh in Year 1 (mostly opportunity cost of founder time). Break-even at month 11. Annual revenue ~₹7.4 lakh. **Realistic only if founder has personal runway and treats Year 1 as a learning investment.**

### Scenario B — Base case (realistic growth)

**Assumptions:**
- SEO content engine produces 10 articles/month from M3.
- Instagram Reels produce 2–3k new followers/month.
- One viral Reel around month 6.
- Paid Instagram ads start month 9 at ₹20k/month.
- Companion launches month 10.
- One part-time reader hired month 9.

| Month | Spark | Reading | Full Map | Compat. | Companion | Monthly revenue | Monthly costs | Net |
|---|---|---|---|---|---|---|---|---|
| M1 | 15 | 6 | 3 | 0 | 0 | ₹23,212 | ₹1,07,000 | -₹83,788 |
| M2 | 25 | 10 | 5 | 0 | 0 | ₹39,225 | ₹1,07,500 | -₹68,275 |
| M3 | 50 | 18 | 8 | 0 | 0 | ₹70,152 | ₹1,08,000 | -₹37,848 |
| M4 | 80 | 28 | 14 | 0 | 0 | ₹1,12,546 | ₹1,09,000 | +₹3,546 |
| M5 | 110 | 38 | 18 | 0 | 0 | ₹1,49,962 | ₹1,10,000 | +₹39,962 |
| M6 | 200 | 60 | 25 | 0 | 0 | ₹2,28,750 | ₹1,11,000 | +₹1,17,750 |
| M7 | 300 | 80 | 35 | 15 | 0 | ₹3,35,775 | ₹1,12,000 | +₹2,23,775 |
| M8 | 400 | 110 | 50 | 25 | 0 | ₹4,57,125 | ₹1,13,000 | +₹3,44,125 |
| M9 | 500 | 140 | 65 | 40 | 5 | ₹5,77,575 | ₹1,42,000 | +₹4,35,575 |
| M10 | 600 | 170 | 80 | 55 | 15 | ₹7,07,775 | ₹1,52,000 | +₹5,55,775 |
| M11 | 700 | 200 | 95 | 70 | 30 | ₹8,41,950 | ₹1,62,000 | +₹6,79,950 |
| M12 | 800 | 230 | 110 | 85 | 50 | ₹9,84,950 | ₹1,72,000 | +₹8,12,950 |
| **Year 1 total** | **3,780** | **1,090** | **508** | **290** | **100** | **~₹45,27,997** | **~₹14,12,500** | **~₹31,15,497** |

**Scenario B interpretation:** Solo founder profitable from month 4. Annual revenue ~₹45 lakh. Net ~₹31 lakh. **This is the realistic base case assuming the SEO + Reels flywheel works as expected.**

### Scenario C — Optimistic (viral moment + influencer)

**Assumptions:**
- One major viral moment (Reel or YouTube video) in months 3–6.
- Major influencer collaboration in month 6 (₹1 lakh spend).
- SEO content engine + daily-content engine drives 50k monthly visitors by month 9.
- Companion launches month 8 with strong conversion.
- Two part-time readers + ops person by month 9.

| Month | Spark | Reading | Full Map | Compat. | Companion | Monthly revenue | Monthly costs | Net |
|---|---|---|---|---|---|---|---|---|
| M1 | 30 | 12 | 5 | 0 | 0 | ₹42,475 | ₹1,07,000 | -₹64,525 |
| M2 | 80 | 25 | 10 | 0 | 0 | ₹96,725 | ₹1,08,000 | -₹11,275 |
| M3 | 200 | 60 | 25 | 0 | 0 | ₹2,33,725 | ₹1,09,000 | +₹1,24,725 |
| M4 | 500 | 150 | 60 | 0 | 0 | ₹5,90,900 | ₹1,12,000 | +₹4,78,900 |
| M5 | 800 | 220 | 90 | 0 | 0 | ₹9,21,950 | ₹1,15,000 | +₹8,06,950 |
| M6 | 1200 | 350 | 140 | 30 | 0 | ₹13,49,250 | ₹2,15,000 | +₹11,34,250 |
| M7 | 1500 | 450 | 180 | 60 | 0 | ₹17,17,800 | ₹1,80,000 | +₹15,37,800 |
| M8 | 1800 | 550 | 220 | 90 | 30 | ₹21,16,300 | ₹1,90,000 | +₹19,26,300 |
| M9 | 2000 | 650 | 260 | 120 | 80 | ₹24,70,650 | ₹2,30,000 | +₹22,40,650 |
| M10 | 2200 | 750 | 300 | 150 | 150 | ₹28,79,750 | ₹2,50,000 | +₹26,29,750 |
| M11 | 2400 | 850 | 340 | 180 | 250 | ₹33,40,750 | ₹2,70,000 | +₹30,70,750 |
| M12 | 2500 | 950 | 380 | 210 | 400 | ₹38,71,150 | ₹2,90,000 | +₹35,81,150 |
| **Year 1 total** | **15,010** | **5,067** | **2,010** | **840** | **910** | **~₹1,96,31,425** | **~₹22,26,000** | **~₹1,74,05,425** |

**Scenario C interpretation:** ~₹2 crore annual revenue, ~₹1.74 crore net. **This is the upside scenario if a viral moment lands.**

### Year 1 — Summary

| Scenario | Annual revenue | Annual costs | Net | Break-even month |
|---|---|---|---|---|
| A — Conservative | ₹7.4 lakh | ₹13.2 lakh | -₹5.7 lakh | Month 11 |
| B — Base | ₹45 lakh | ₹14 lakh | +₹31 lakh | Month 4 |
| C — Optimistic | ₹1.96 crore | ₹22 lakh | +₹1.74 crore | Month 2 |

## 4. 36-month P&L (Scenario B — base case)

| Year | Annual revenue | Annual costs | Net | Cumulative net |
|---|---|---|---|---|
| Year 1 | ₹45 lakh | ₹14 lakh | +₹31 lakh | +₹31 lakh |
| Year 2 | ₹1.2 crore | ₹35 lakh | +₹85 lakh | +₹1.16 crore |
| Year 3 | ₹2.5 crore | ₹70 lakh | +₹1.8 crore | +₹2.96 crore |

**Year 2 assumptions:**
- Self-service Spark + Reading + Full Map at scale.
- Companion subscription at 500+ subscribers.
- Compatibility as upsell to all tiers.
- 1 part-time reader + 1 part-time ops person.
- Paid ads scaling to ₹1–2 lakh/month.
- Hindi launch.
- Android app on Play Store.

**Year 3 assumptions:**
- iOS app on App Store (if Android supports).
- Course / cohort launches.
- B2B API beta with 5–10 partners.
- 2 part-time readers + 1 full-time ops person.
- Possibly Korean-language product.
- Content engine producing 20 articles + 30 reels/month.

## 5. Break-even analysis (Year 1)

**Solo founder break-even (Scenario B):**
- Monthly revenue to cover ₹1.1 lakh/month costs = **~30 Spark + 12 Reading + 6 Full Map = ~₹70k.**
- This is the M3-M4 inflection point. Until then, founder relies on personal runway.

**Team break-even (Year 2):**
- Monthly costs ₹3 lakh → need **₹3 lakh/month revenue** = **100 Spark + 30 Reading + 20 Full Map + 50 Companion** = **₹3.1 lakh.**

**Scale break-even (Year 3):**
- Monthly costs ₹6 lakh → need **₹6 lakh/month revenue** = **400 Spark + 100 Reading + 50 Full Map + 80 Companion + 50 Compatibility + 2 B2B partners** = **₹6.1 lakh.**

## 6. Funding the launch

### Required personal runway

- **Scenario A (conservative):** founder needs ₹15–20 lakh personal runway (6 months living expenses + initial costs).
- **Scenario B (base):** founder needs ₹8–10 lakh personal runway (3 months living expenses + initial costs; profitable from M4).
- **Scenario C (optimistic):** founder needs ₹5–8 lakh personal runway (profitable from M2).

### Should we raise outside capital?

**Strong NO for Year 1.** Reasoning:

1. **Bootstrapping preserves founder control** of the classical-tradition positioning. VC-funded astrology startups often drift toward mass-market entertainment, which is the opposite of what we're building.
2. **Outside capital expects 10× returns.** AstroTalk raised $20M+ and is targeting ₹2,000 crore revenue + IPO. We don't need to play that game.
3. **The product is profitable at small scale.** Scenario B reaches ₹31 lakh net in Year 1 on a solo founder. That's a ₹25 lakh/year lifestyle business before considering scale.
4. **The market is too early for venture-scale.** The English-language Korean Saju niche is not yet large enough to support a Series A. Wait for traction before approaching investors.
5. **The classical-tradition positioning is a feature, not a limitation.** A VC-backed company would be pushed to "maximize TAM" by adding Vedic Jyotish, Western astrology, tarot, dream interpretation — all the things CLAUDE.md says we shouldn't do.

**When would we consider raising capital?**

- **Year 3+** if revenue run rate is ₹5+ crore and we want to expand to a multi-language product (Korean, Hindi, Mandarin).
- **Strategic acquirer interest:** a Korean entertainment conglomerate (Kakao, Naver, CJ) might want to acquire a Korean Saju product for cultural-relevance reasons. If approached, evaluate carefully.
- **Never for product expansion** (don't dilute the brand).

## 7. Pricing assumptions and sensitivities

The base case assumes:
- Spark ₹499: 70% of orders by volume, 25% of revenue.
- Reading ₹1,499: 20% of orders by volume, 30% of revenue.
- Full Map ₹3,499: 10% of orders by volume, 35% of revenue.
- Compatibility ₹999: 5% of orders by volume, 5% of revenue.
- Companion ₹799/mo: by month 12, ~50 active subscribers.

**Sensitivity analysis:**

| Variable | -20% | Base | +20% |
|---|---|---|---|
| Spark conversion rate | ₹36 lakh | **₹45 lakh** | ₹54 lakh |
| Reading conversion rate | ₹38 lakh | **₹45 lakh** | ₹52 lakh |
| Full Map conversion rate | ₹38 lakh | **₹45 lakh** | ₹52 lakh |
| Companion subscriber count | ₹42 lakh | **₹45 lakh** | ₹48 lakh |
| Founder review hours (Reading/Full Map) | ₹49 lakh | **₹45 lakh** | ₹41 lakh |
| CAC blended | ₹51 lakh | **₹45 lakh** | ₹39 lakh |

**Key sensitivities:**
1. **Spark volume** is the largest single revenue driver. -20% Spark = -20% total revenue.
2. **Full Map conversion** is the highest-margin lever. +20% Full Map conversion = +15% total revenue.
3. **Founder review time** is the biggest cost lever. AI-assisted review (Phase 2) saves ~₹4 lakh/year in founder opportunity cost.

## 8. Sensitivity to "what if" scenarios

**What if SEO content engine doesn't drive traffic?**
- Drop Spark volume by 50%. Year 1 revenue drops to ~₹25 lakh.
- Mitigation: double down on Instagram + influencer marketing. Higher CAC, but still profitable.

**What if Instagram Reels don't go viral?**
- Slower follower growth. Year 1 revenue: ~₹30 lakh instead of ₹45 lakh.
- Mitigation: paid Instagram ads starting month 6 instead of month 9.

**What if a competitor launches first in English Korean Saju?**
- Slower organic growth. Year 1 revenue: ~₹35 lakh instead of ₹45 lakh.
- Mitigation: lean into founder voice + citations as differentiator. Companion subscription as moat.

**What if Google penalizes the site for YMYL astrology content?**
- Organic traffic drops 50–80%. Year 1 revenue: ~₹15–25 lakh.
- Mitigation: emphasize E-E-A-T (founder bio, classical-tradition references, disclaimers); diversify traffic to Instagram + Reddit.

**What if the founder has health issues / burnout?**
- Review bandwidth halves. Year 1 revenue drops to ~₹20 lakh.
- Mitigation: Phase 1 should already have a part-time reader identified (even if not hired).

**What if a major refund / review crisis hits?**
- Revenue drops 20% for 2–3 months. Year 1 revenue: ~₹35 lakh.
- Mitigation: documented refund policy + clarification calls + active review management.

## 9. The "minimum viable commercialization" path

If the founder has very limited time / runway, the **minimum viable commercialization** is:

1. Self-service Spark on existing FastAPI app + Razorpay. **Cost: ₹0** (already built). **Time: 2 weeks.**
2. Reading + Full Map via personal referral. **Cost: ₹0.** **Time: ongoing.**
3. Single Instagram account with daily Reels. **Cost: ₹0.** **Time: 1 hour/day.**
4. Single SEO pillar post. **Cost: ₹0.** **Time: 4 hours one-time.**

**Minimum viable Year 1 outcome:** ~₹3–5 lakh revenue, no hires, founder breaks even on opportunity cost. Validates the market without committing to scaling.

This is the right starting point for a founder who is testing the waters.

## 10. Sources

- See `02-market-size-and-demand.md` for market sizing that informs the funnel assumptions.
- See `03-competitor-landscape.md` for competitor pricing benchmarks.
- See `04-feature-demand.md` for feature prioritization.
- See `05-audience-demographics.md` for audience volume assumptions.
- See `06-monetization-strategy.md` for the pricing model.
- See `08-marketing-strategy.md` for CAC assumptions.
- See `09-product-roadmap.md` for sequencing.
- See `10-risks-and-do-not-do.md` for risk-adjusted scenarios.

Internal references:
- [CLAUDE.md — Tiered Client Products](../../CLAUDE.md)
- [tasks.md — project status](../../tasks.md)
- [candidates_horoscope/reports/](../../candidates_horoscope/reports/)
