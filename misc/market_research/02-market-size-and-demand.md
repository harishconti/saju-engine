# 02 · Market Size & Demand

**Date:** 2026-06-26
**Scope:** Global astrology/spiritual wellness market, Indian astrology segment, Korean Saju niche, English-language gap, demand signals relevant to the Saju project.

---

## 1. Headline numbers

| Market | Size (2025) | Growth | Source / Confidence |
|---|---|---|---|
| **Global spiritual wellness + astrology** | ~USD 4.2B (astrology apps alone, per Raft Labs industry analysis) | ~9.1% CAGR | [Raft Labs](https://www.raftlabs.com/blog/how-to-build-astrology-app) — single-source estimate, treat as [estimate]. |
| **Global spiritual wellness market (broader)** | Multi-billion, growing at ~16.1% CAGR (per Market.us) | 16.1% CAGR | [Market.us](https://market.us/report/spiritual-wellness-astrology-market/) — single-source, [estimate]. |
| **India astrology services market (broader, includes offline)** | **USD 10–12B annually** | ~12% CAGR | [The Tribune / InstaAstro reporting](https://www.tribuneindia.com/news/impact-feature/instaastro-gains-popularity-among-gen-z-for-astrological-guidance/) and FICCI/KPMG 2022 figures cited at $10B. |
| **India online astrology market** | **USD 102–106M (FY24)** | Projected to decuple by FY30 (~10x by 2030) | [Redseer Astro-Tech 2024](https://redseer.com/articles/astro-tech-cosmic-trends-digital-era/) — credible venture-research source. |
| **India astrology app market** | **USD 1.0B in 2025**, projected **USD 3.5B by 2032** (~14.4% CAGR) | 14.4% CAGR | Industry estimate, consistent across multiple secondary sources. |
| **Korean Saju apps (domestic, paid + ad-supported)** | **Not publicly broken out** — apps classified under Lifestyle/Entertainment | Limited public data | Sensor Tower / data.ai behind paywall; most market data in Korean only. [estimate]. |
| **English-language Saju app niche** | **Very small**, virtually unmonetized at scale | Underserved | Confirmed by multiple Reddit threads on r/Korean, r/ChineseAstrology asking where to find English saju apps; "The Saju Booth" and "Lucky Saju" (iOS, $3.99) are among the only credible English products. |
| **Global Four Pillars / BaZi app market (Chinese-language)** | Estimated low-hundreds of millions USD annually across major apps | Subscription-shift underway | [astrologytechinsights.com](https://astrologytechinsights.com/bazi-monetization-2025) — single-source [estimate]. |

## 2. India: the headline opportunity

India is by far the largest single-country opportunity because:

1. **Population + cultural penetration.** ~1.4 billion population, ~70% of urban Indians consult astrologers for major life decisions (2019 YouGov, cited via Redseer).
2. **AstroTalk is a proven unicorn-scale business.** ₹651 crore FY24 revenue (~USD 78M at 2024 rates), ₹94 crore net profit (10x YoY growth), 30M+ users, 4.5M paid sessions/month, IPO planned for 2026 (targeting ₹2,000 crore). ([The Economic Times](https://economictimes.indiatimes.com/tech/startups/astrotalk-rides-online-astrology-boom-to-double-fy24-revenue-to-rs-651-crore/articleshow/113500403.cms))
3. **Gen Z is the dominant growth segment.** 60–61% of users on AstroTalk, InstaAstro, Astroyogi are Gen Z (born 1997–2012). Gen Z uses astrology 11% month-on-month at AstroSage. ([Republic World](https://www.republicworld.com/tech/apps/genz-accounts-for-60-user-base-on-astrology-apps-report))
4. **Subscription and paid chat is the proven model.** Per-minute chat is the dominant monetization (₹10–200/min). Subscription tiers are emerging but less proven than per-minute chat.

**But** the Indian market is dominated by Vedic astrology (Jyotish), not Korean Saju. Korean Saju is a **prestige niche** that has to position as "premium / classical / different" to avoid direct head-to-head with AstroTalk.

## 3. Korean Saju: the heritage market

In Korea, Saju is mainstream cultural literacy, not niche:

- **~30% of 20-somethings** in Korea use astrology apps vs. ~10% over 60 (Nielsen 2021, cited via Gitnux).
- **25% pandemic-era increase** in astrology consultations.
- The dominant app is **"신점 당신의사주"** by 사주닷컴 (founded 2001): 1M+ Google Play downloads, ~4.4★ rating, ~4.5★ iOS, #67 Lifestyle on iOS. Features include Saju calendar, Tojeong bigyeol, Tarot, dream interpretation, 궁합 (compatibility), New Year fortunes, monthly/daily fortunes. ([App Store / Play Store listings, via WebSearch])
- Other notable Korean apps: **사주닷컴 (stjpbl.com)**, **당신의 사주**, **만세력**, **별다줄**, **운세다**. Most monetize via ads + premium subscription + paid one-off consultations.

**Reality check:** the Korean Saju app market is **saturated, mature, and dominated by well-funded incumbents**. New entrants compete on UX and content, not on the calculation itself — the calculation tables are public domain.

## 4. The English-language gap: our real wedge

Multiple signals confirm that **English-language, internationally-available Korean Saju is an underserved niche**:

- Reddit threads on r/Korean and r/ChineseAstrology regularly ask "is there a saju app in English?" with the answer usually being "the most popular Korean apps don't work outside Korea."
- "The Saju Booth" exists but has no public revenue / user metrics — implying small.
- "Lucky Saju" is a $3.99 one-off iOS app — too cheap to be a sustainable business, suggesting limited commercial validation.
- "Aha Chat" and "Korean Saju Palja Chat" are AI chatbot apps; they exist but are not premium products.

**Demand estimate for English-language Korean Saju [estimate, low confidence]:**

- **Addressable global audience:** 5–15M English-speaking adults interested in Korean astrology (rough estimate based on Hallyu Wave reach: K-pop, K-drama audiences are 50–100M+, of whom an astrology-curious minority is 5–15%). Cross-reference: Korean Wave content reaches ~200M+ globally per Korean Foundation surveys.
- **Realistic paying segment (Year 1):** 0.5–2% conversion = 25k–300k potential paying users globally over 5 years.
- **India-specific Korean-Saju-curious segment:** smaller, ~50–200k paying users over 5 years (Korean Wave interest is real but smaller than Korean diaspora; India doesn't have a Korean diaspora anywhere near US/Canada/Australia scale).

## 5. Demand signals we already have (from this codebase)

The project itself is evidence of demand:

1. **6 paid pilots already executed** at the Full Map tier (₹3,499), each with a bespoke Markdown + PDF deliverable: Sruthi, Pawan, Harish, Gurumoorthy, Mahesh, Vishnu Priya. All on the same South-Indian client network, mostly via referral.
2. **Existing intake submissions** in `candidates_horoscope/intake/` from the self-service calculator (4 test files as of 2026-06-22).
3. **Cross-candidate joint analysis** (`reports/cross-candidate-business-analysis.md`) was the highest-value deliverable to the trio — a clear signal that **business / venture analysis is the most demanded use case**, not generic "what does my chart say."

## 6. Demand by use case

| Use case | Demand intensity | Willingness to pay | Notes |
|---|---|---|---|
| **Business / venture timing** | **Very high** (proven by cross-candidate analysis) | High (₹3,499 Full Map) | The 5-business analysis was the single most-praised deliverable in this project. |
| **Year-ahead outlook** (2027 outlook, etc.) | High | High | The annual forecast in Full Map aligns well. |
| **Career / domain fit** | High | High | The `career.md` follow-up files exist for 5 of 6 candidates — universally demanded. |
| **Compatibility / matchmaking** | High in India specifically | Medium | Vedic Kundli Milan is dominant in India; Korean 궁합 has to differentiate. |
| **Daily / monthly horoscope** | Medium-high | Low (free tier expectation) | Highest volume but lowest ARPU. Should be a free funnel, not a paid product. |
| **Marriage timing** | High | Medium | Year-specific deliverable. |
| **Children / parenting analysis** | Low-Medium | Low | Niche. |
| **Health tendencies** | Medium | Medium | Important to position as "tendencies, not diagnosis" — see CLAUDE.md ground rules. |
| **Relocation / feng shui** | Low-Medium | Low | Niche in English market. |

## 7. Demand seasonality

- **New Year (Jan 1–15):** massive spike in "year ahead" queries. Indian + Korean + Chinese New Year periods all concentrate demand.
- **Wedding season (Oct–Feb in India):** matchmaking / compatibility demand spikes.
- **April–June (exam season in India):** parent-driven academic timing queries.
- **Career season (March–June):** job-switch / business-launch queries spike.

**Implication:** the annual forecast window in Full Map should be **heavy on Jan, light on Jul**. The Companion subscription model has natural retention logic around new year / new quarter.

## 8. What this means for the project

| Insight | Implication |
|---|---|
| India is the biggest single market by value but most contested. | Enter India via Tier 1 only (Spark ₹499) initially; avoid head-to-head with AstroTalk on Vedic. |
| English-language Korean Saju is underserved globally. | This is the durable wedge — Indian diaspora + Korean diaspora + Hallyu-curious global audience. |
| The 6 paid pilots prove the Full Map price point works in person. | The bottleneck is interpretation throughput, not pricing. |
| Business / venture / career use cases are most in demand. | Lean the marketing and product copy toward career + business, not "destiny." |
| Daily horoscope is a funnel, not a product. | Free tier = daily / monthly fortune; paid tier = deep natal + timing. |

## 9. Sources

- [Market.us: Spiritual Wellness Astrology Market](https://market.us/report/spiritual-wellness-astrology-market/)
- [Grand View Research: Spiritual Wellness Astrology](https://www.grandviewresearch.com/industry-analysis/spiritual-wellness-astrology-market-report)
- [Redseer: Astro-Tech Cosmic Trends in the Digital Era](https://redseer.com/articles/astro-tech-cosmic-trends-digital-era/)
- [The Economic Times: AstroTalk FY24 revenue](https://economictimes.indiatimes.com/tech/startups/astrotalk-rides-online-astrology-boom-to-double-fy24-revenue-to-rs-651-crore/articleshow/113500403.cms)
- [The Tribune: InstaAstro Gen Z trends](https://www.tribuneindia.com/news/impact-feature/instaastro-gains-popularity-among-gen-z-for-astrological-guidance/)
- [Entrackr: InstaAstro funding](https://entrackr.com/2024/05/instaastro-raises-2-3-mn-led-by-artha-venture-fund/)
- [Republic World: Gen Z on astrology apps](https://www.republicworld.com/tech/apps/genz-accounts-for-60-user-base-on-astrology-apps-report)
- [NumroVani: AI Astrology 2025 Consumer Trends](https://numrovani.com/ai-astrology-2025-mid-year-study/)
- [Raft Labs: How to Build an Astrology App](https://www.raftlabs.com/blog/how-to-build-astrology-app)
- [Axios: Co-Star $15M Series A](https://www.axios.com/2021/04/14/astrology-app-co-star-raises-15-million-funding)
- [CB Insights: Co-Star financials](https://www.cbinsights.com/company/co-star-astrology-society/financials)
- [Gitnux: Astrology Statistics 2026](https://gitnux.org/astrology-statistics/)
- [Astrology Tech Insights: BaZi monetization 2025](https://astrologytechinsights.com/bazi-monetization-2025)