# 12 · Feasibility Verdict — Final Go / No-Go

**Date:** 2026-06-26
**Decision-maker:** Solo founder (Harish)
**Decision:** **CONDITIONAL GO** — proceed with commercialization under specific conditions, with milestone gates that allow graceful exit if early signals fail.

---

## 1. The verdict, in one paragraph

**The Korean Saju project has unusually strong fundamentals for a niche consumer product — a working calculation engine with 129 passing tests, a citation-grounded classical-tradition knowledge base, a self-service PDF generation pipeline that already produces tiered client reports, and 6 paid pilots validating the Full Map price point. The realistic 12-month opportunity for a solo operator is ₹40–80 lakh in revenue (Scenario B = ₹45 lakh base case), scaling to ₹2–4 crore annual run rate in 24–36 months with a small team and content engine. The two dominant risks are interpretive quality on the higher tiers (mitigated by mandatory human review) and regulatory/compliance exposure around predictive astrology claims (mitigated by careful compliance framing). The recommended path is a phased 4-quarter launch — web app + self-service Spark → Compatibility add-on + Companion scaffolding → Android app + Companion launch → iOS via Capacitor + first hires.**

## 2. Why this is a GO (the strengths)

### 2.1 The hard part is built

The calculation engine at `tools/saju_engine/` is non-trivial to build from scratch:
- 11 knowledge files totaling ~95KB of classical-tradition interpretation rules.
- A 60-cycle day-pillar engine with Korean 야자시 convention (vs. mainland Chinese 조자시).
- 십신, 12운성, 대운 direction + starting age, 신살 overlays, strength heuristic, grid/pattern detection, annual/monthly/daily luck windows, prose scaffold, premium tiered report generator.
- 129 pytest cases passing.

**This took 18 months of focused work** and would take a competent new entrant 6–12 months to replicate. The moat is real.

### 2.2 The classical-tradition positioning is defensible

Most Saju / BaZi / astrology apps produce generic LLM-prompted interpretations that any serious practitioner spots immediately. The `knowledge/` corpus in this project is **citation-grounded from primary Korean 명리 texts** (Gyeonglakgoyo, Jeokcheon-su, Yeonhae-japyeong, Gungtong-bogam, Myeongrijeongjong). This is the credibility moat for the Full Map tier (₹3,499) where the client expects depth.

### 2.3 The tiered pricing is validated

6 paid pilot candidates have already purchased Full Map-tier reports at ₹3,499. Each pilot took 90–120 minutes of founder time. The willingness to pay is real and the price-to-depth ratio is right.

### 2.4 The market has a real, underserved niche

**English-language Korean Saju is genuinely underserved.** The dominant Korean Saju apps are Korean-only and Korean-App-Store-only. Western astrology apps (Co-Star, The Pattern, Sanctuary) don't cover Korean 명리. Indian astrology apps (AstroTalk, InstaAstro, GaneshaSpeaks) are Vedic Jyotish, not Korean Saju. "The Saju Booth" and "Lucky Saju" exist in English but are small and underfunded.

### 2.5 The audience is reachable

The intersection of Hallyu Wave audience (50–100M+ globally per Korean Foundation surveys) × English-strong × Indian urban Tier-1 + Korean diaspora = a defensible ~5–15M addressable audience globally, with realistic ~25k–300k paying users over 5 years. India alone has 1.4B population with ~70% astrology engagement and growing K-content consumption.

### 2.6 The intake → PDF → delivery pipeline already works

`tools/client_intake_app.py` accepts an intake form submission, computes the chart from birth data, runs the premium report generator for the chosen tier, and returns a PDF. This is the entire functional path from signup to delivery, working today.

## 3. Why this could be a NO-GO (the risks)

### 3.1 The interpretive quality bottleneck

Every Reading or Full Map order requires 45–120 minutes of human review by the founder. At 50 orders/month, that's 40–100 hours/month — half the founder's available time. Without AI-assisted review or hired readers, the business caps at ~150 Reading/Full Map orders/month. This caps Year 1 revenue at ~₹30–50 lakh regardless of demand.

### 3.2 The marketing compliance wall

Google Search ads and Facebook/Meta ads disallow "fortune telling, spiritual, or psychic content" outright. This forces reliance on SEO + organic social + influencer marketing, which is slower and more founder-labor-intensive than paid acquisition. Mitigations exist (organic SEO, Instagram Reels, micro-influencers) but the absolute ceiling on growth velocity is lower than a paid-ads-friendly product would have.

### 3.3 The cultural / tradition backlash risk

A credible Korean 명리 practitioner who reads our report and spots a "wrong" interpretation per their school can publicly damage the brand. The mitigation is the citation-grounded knowledge base + `[UNCERTAIN]` flags + `[ENGINE DRAFT — REVIEW REQUIRED]` markers, but the risk is real.

### 3.4 The refund risk on the high tier

Full Map at ₹3,499 is a 3-figure USD-equivalent purchase. If the client reads it and feels "this doesn't apply to me," they'll demand a refund. The mitigation is a documented refund policy + optional 30-minute clarification call, but chargeback rates must be monitored carefully.

### 3.5 The founder burnout risk

Solo founder. 60–80 hour weeks are common. Burnout is the most common failure mode. The mitigation is strict 50-hour-week cap + part-time reader by month 9 + quarterly breaks.

## 4. The conditions for GO

The conditional GO requires these specific preconditions:

1. **Founder has ₹8–15 lakh personal runway** (3–6 months of living expenses + initial costs).
2. **Founder commits 30–40 hours/week for 12 months** (not "evenings and weekends" — that's insufficient).
3. **Founder is willing to hand-deliver Reading/Full Map in Year 1** with 48–72 hour SLA. No fully-automated delivery until AI-assisted review is built in Phase 2.
4. **Founder has access to a part-time Saju reader** (for Phase 3 hire) — at least identified, even if not hired yet.
5. **Founder is willing to invest in SEO + content engine** as the primary acquisition channel (not relying on paid ads alone).
6. **Founder accepts the classical-tradition positioning** as the durable brand — not as a limitation.

## 5. The milestone gates (decision points)

| Gate | When | Pass criteria | If fails |
|---|---|---|---|
| **G0: Pre-launch** | Month 0 | Web app + Razorpay + self-service Spark live. 4 SEO posts published. 30 Instagram Reels filmed. Personal runway ≥ ₹8 lakh. | Stop. Do not launch. |
| **G1: First paying customer** | Month 1 | 1+ Spark self-service purchase OR 5+ Reading/Full Map requests via referral. | Pause marketing spend. Re-evaluate positioning. |
| **G2: Traction** | Month 4 | 50+ paying customers cumulatively. ₹4 lakh revenue. SEO traffic >1,000 visits/month. Instagram followers >2,000. | Pivot to higher-touch (less self-service, more founder-led). |
| **G3: Profitability** | Month 6 | Monthly revenue >₹1.5 lakh. Monthly costs <₹1.5 lakh. Founder 50-hour-week cap is sustainable. | Stay solo; defer hiring. |
| **G4: Hire decision** | Month 9 | ₹5 lakh/month revenue run rate. Founder review bandwidth saturated. | Hire 1 part-time reader. |
| **G5: Companion launch** | Month 10 | Companion subscription infrastructure ready. 50+ Full Map buyers in customer base. | Launch Companion. If <30 Full Map buyers, defer to month 18. |
| **G6: Year-1 review** | Month 12 | ₹40+ lakh annual revenue (Scenario B or better). Founder not burned out. Customer NPS >30. | Continue if NPS OK; pivot if not. |

## 6. What the GO looks like, week-by-week

### Weeks 1–4: Foundation (G0)
- Deploy Next.js web app at custom domain.
- Integrate Razorpay (India) + Stripe (international).
- Self-service Spark live and selling.
- 4 long-form SEO pillar posts published.
- 30 Instagram Reels filmed + posted.
- Email list + welcome sequence live.

### Weeks 5–8: Compatibility + Iteration (G1)
- Compatibility (궁합) module built + product page + ₹999 standalone.
- Convert Reading/Full Map to formal paid product with intake + payment + 48–72 hour SLA.
- Documented refund policy in CLAUDE.md.
- 4 more SEO posts (comparison + service pages).

### Weeks 9–16: Funnel + retention (G2)
- Daily content engine (email + web push).
- First 2 YouTube long-form videos.
- First Reddit organic contributions.
- ₹10k first paid Instagram ad test.
- Founder review queue (admin UI).

### Weeks 17–24: PWA + Android (G3)
- PWA conversion (manifest + service worker).
- Capacitor wrap for Android + Play Store submission.
- Companion subscription infrastructure ready.
- Year-ahead reminder campaign for December buyers.

### Weeks 25–36: Scale + Companion (G4, G5)
- Companion launch + push to existing Full Map buyers.
- Hindi localization (landing page + intake + Spark).
- First paid Instagram ads at scale (₹30k/month).
- First influencer collaboration (₹15k spend).
- First part-time reader hire (₹20k/month).

### Weeks 37–48: Optimize + Year-2 planning (G6)
- AI-assisted review to cut human time 50%.
- Conversion rate optimization (A/B tests).
- Year-1 review + Year-2 planning.
- Decision on iOS Capacitor wrap (depends on Android metrics).

## 7. What the NO-GO looks like (graceful exit)

If at any milestone gate the criteria are not met, the founder should:

1. **Stop new marketing spend.** Stop paying for content production, paid ads, influencer collaborations.
2. **Stop self-service acquisition.** Switch to "request-only" intake.
3. **Continue fulfilling existing orders** to maintain brand reputation.
4. **Maintain the project as a paid-pilot hobby.** Accept 1–3 orders/month via personal referral at Full Map tier.
5. **Document lessons learned.** Add a post-mortem to `market_research/`.
6. **Re-evaluate in 6 months.** The market may have shifted; the founder's situation may have shifted.

The exit is **not a failure**. A niche lifestyle business generating ₹3–5 lakh/year from 12–20 Full Map orders is a valid outcome. The Year-1 GO is to attempt scale; the NO-GO is to recognize when scale isn't working and settle into a sustainable niche business.

## 8. The decision matrix (when to GO vs NO-GO)

| Founder situation | Decision |
|---|---|
| ₹20+ lakh runway, 40 hrs/week, part-time reader identified, willingness to do SEO | **Strong GO.** Pursue aggressively. Target Scenario C upside. |
| ₹8–15 lakh runway, 30 hrs/week, willing to do SEO + Reels, no part-time reader yet | **Conditional GO.** Pursue Scenario B. Plan for milestone gates. |
| ₹5–8 lakh runway, 20 hrs/week, mostly evenings | **Minimum viable commercialization.** Self-service Spark + Reels + 1 SEO post. Target ₹3–5 lakh Year-1. |
| <₹5 lakh runway, <20 hrs/week | **NO-GO.** Maintain as paid-pilot hobby. |
| No runway, no time, no interest in marketing | **NO-GO.** Maintain codebase; do not commercialize. |

## 9. The verdict, restated

**GO if and only if:**
- You have ₹8+ lakh personal runway.
- You can commit 30+ hours/week for 12 months.
- You're willing to be the face of the brand (Reels, YouTube, possibly in-person readings).
- You accept the citation-grounded classical-tradition positioning as a feature.
- You're willing to hand-deliver Reading/Full Map in Year 1 (no shortcuts on quality).

**If you GO, the realistic outcomes are:**
- **Scenario B (base):** ₹45 lakh Year-1 revenue, ₹31 lakh net, ₹25+ lakh/year lifestyle business.
- **Scenario A (conservative):** ₹7 lakh Year-1 revenue, ₹-6 lakh Year-1 (treated as learning investment).
- **Scenario C (optimistic):** ₹2 crore Year-1 revenue, ₹1.7 crore net, validation for ₹5+ crore Year-3 ARR.

**The single most important factor is whether the SEO + Instagram Reels flywheel works.** If it does, the rest follows. If it doesn't, fall back to personal referral niche.

## 10. The one-sentence verdict

**The project should be commercialized. The engine, knowledge base, and PDF pipeline are already built. The market has an underserved niche. The pricing is validated. The risks are manageable. The conditions are clear. The founder must commit.**

---

## 11. Final notes

This research is **decision-support, not investment-grade due diligence**. The numbers are realistic and conservative — many are flagged as `[estimate]` to indicate uncertainty. Real outcomes will vary.

The strongest signal that this is the right project at the right time is that **6 paid pilots have already happened organically, without any marketing spend, via personal referral.** The product-market fit signal is already there; the question is whether it can scale.

If the founder chooses to GO, the most important next step is **to start writing the SEO pillar posts and filming the first 30 Reels today.** The product is built. The market is waiting. The only missing piece is distribution.

---

## 12. Sources

- All 11 prior docs in this folder.
- Project state: [CLAUDE.md](../../CLAUDE.md), [README.md](../../README.md), [tasks.md](../../tasks.md).
- Engine + tests: [tools/saju_engine/](../../tools/saju_engine/), [tests/](../../tests/).
- 6 paid pilots: [candidates_horoscope/reports/](../../candidates_horoscope/reports/).
- Self-service calculator: [tools/client_intake_app.py](../../tools/client_intake_app.py).
- Premium report generator: [tools/saju_engine/premium_report.py](../../tools/saju_engine/premium_report.py).
- Knowledge base: [knowledge/](../../knowledge/).

External market research (cited throughout this folder):
- [Market.us: Spiritual Wellness Astrology Market](https://market.us/report/spiritual-wellness-astrology-market/)
- [Grand View Research: Spiritual Wellness Astrology](https://www.grandviewresearch.com/industry-analysis/spiritual-wellness-astrology-market-report)
- [Redseer: Astro-Tech Cosmic Trends](https://redseer.com/articles/astro-tech-cosmic-trends-digital-era/)
- [The Economic Times: AstroTalk FY24](https://economictimes.indiatimes.com/tech/startups/astrotalk-rides-online-astrology-boom-to-double-fy24-revenue-to-rs-651-crore/articleshow/113500403.cms)
- [The Tribune: InstaAstro Gen Z](https://www.tribuneindia.com/news/impact-feature/instaastro-gains-popularity-among-gen-z-for-astrological-guidance/)
- [Republic World: Gen Z on astrology apps](https://www.republicworld.com/tech/apps/genz-accounts-for-60-user-base-on-astrology-apps-report)
- [NumroVani: AI Astrology 2025 Consumer Trends](https://numrovani.com/ai-astrology-2025-mid-year-study/)
- [CB Insights: Co-Star financials](https://www.cbinsights.com/company/co-star-astrology-society/financials)
- [Rev.now: Co-Star revenue](https://rev.now/app/ios/co-star-personalized-astrology-82561/)
- [Axios: Co-Star Series A](https://www.axios.com/2021/04/14/astrology-app-co-star-raises-15-million-funding)
- [한국데이터신문 사주GPT](http://www.kdsnews.co.kr/news/466875)
- [운빨 사주 요금제](https://saju.s-mon.net/plans?tab=subscription)
- [Google Ads Policy: fortune telling](https://support.google.com/adspolicy/answer/4651367)
- [Raft Labs: How to Build an Astrology App](https://www.raftlabs.com/blog/how-to-build-astrology-app)
- [The Debuggers: Flutter vs React Native vs Capacitor 2026](https://thedebuggersitsolutions.com/blog/cross-platform-app-2026-flutter-react-native-capacitor)
- [LikesWeb: Instagram Reels for Astrologers](https://likesweb.com/blog/instagram-reels-ideas-for-astrologers/)
- [SocialPilot: Astrology Instagram Growth 30-Day](https://www.socialpilot.ai/blog/instagram-reels-strategy)
- [Gitnux: Astrology Statistics 2026](https://gitnux.org/astrology-statistics/)
- [Astrology Tech Insights: BaZi monetization 2025](https://astrologytechinsights.com/bazi-monetization-2025)
