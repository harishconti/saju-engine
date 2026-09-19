# 08 · Marketing Strategy

**Date:** 2026-06-26
**Scope:** How to acquire the first 1,000 paying customers for the Saju product, given the audience, the channel economics, and the solo-founder constraint.

---

## 1. The acquisition math, in one paragraph

A solo founder needs to reach **~1,000 paying customers in Year 1** to hit the conservative revenue scenario (~₹40 lakh). At an average order value of ₹1,500 (mix of Spark/Reading/Full Map), that's ~₹1.5 lakh/month in revenue or ~50 orders/month. To generate 50 orders/month from organic + low-cost paid channels, the funnel needs to produce ~500–1,000 qualified leads/month at a 5–10% conversion rate. **The lowest-cost channel that produces qualified astrology leads at this scale is SEO + Instagram Reels + YouTube Shorts**, in that order of ROI.

## 2. Channel ranking (cost-per-acquisition × volume)

| Rank | Channel | Est. CPA (India) | Est. CPA (Korean diaspora) | Volume | Time to ROI | Best for |
|---|---|---|---|---|---|---|
| 1 | **SEO blog (Google + Naver)** | ₹50–200 | $5–20 | Very high (long-tail) | 6–12 months | India Tier-1 + Korean diaspora |
| 2 | **Instagram Reels** | ₹30–150 | $3–15 | High | 3–6 months | India Tier-1 + Hallyu-curious |
| 3 | **YouTube Shorts** | ₹30–150 | $3–15 | High | 3–6 months | All segments |
| 4 | **YouTube long-form** | ₹100–400 | $10–30 | Medium | 6–12 months | Korean diaspora + serious India buyers |
| 5 | **Reddit (organic)** | ₹100–300 | $10–30 | Medium | 6–12 months | Korean diaspora |
| 6 | **WhatsApp broadcast** | ₹20–100 | N/A | Medium | 1–3 months | India existing customers |
| 7 | **Personal referral / network** | ₹0–50 | $0–5 | Low-medium | 0–1 month | All segments |
| 8 | **Paid Meta ads (Instagram + Facebook)** | ₹200–800 | $20–80 | High (with spend) | 1–3 months | India Tier-1 |
| 9 | **Paid Google search ads** | ₹300–1,000 | $30–100 | Medium | 1–3 months | High-intent India Tier-1 |
| 10 | **Influencer / KOL partnerships** | ₹500–5,000 per collab | $50–500 per collab | Variable | Per campaign | Brand awareness |
| 11 | **LinkedIn (organic + paid)** | ₹500+ | $50+ | Low | 6+ months | B2B / high-LTV |
| 12 | **Naver Blog / Naver Café** | N/A | $5–15 (KRW) | High (in Korea) | 6–12 months | Korean diaspora |
| 13 | **TikTok** | Similar to Reels | Similar | High | 3–6 months | Gen Z |
| 14 | **Twitter/X** | Variable | Variable | Low-medium | Variable | Brand-building |
| 15 | **Quora / Yahoo Answers** | ₹50–200 | $5–20 | Medium | 6+ months | SEO long-tail |

**Google Ads and Facebook Ads are blocked for "destiny / fortune telling" content** ([Google Ads Policy](https://support.google.com/adspolicy/answer/4651367)). We must use SEO, organic social, and content marketing as primary channels. Paid ads require careful compliance framing ("educational content" rather than "fortune-telling").

## 3. SEO strategy (the foundation)

### Target keyword categories

1. **Informational keywords (top-of-funnel):**
   - "What is Korean Saju?"
   - "Korean Four Pillars reading"
   - "Korean astrology vs Vedic astrology"
   - "What is my Day Master?"
   - "Korean Saju explained in English"
   - "Best Korean Saju apps in English"

2. **Comparison keywords (mid-funnel):**
   - "Korean Saju vs BaZi"
   - "Korean Saju vs Chinese astrology"
   - "Korean Saju vs Vedic Jyotish"
   - "Korean 만세력 vs Vedic Kundli"

3. **Transactional keywords (bottom-of-funnel):**
   - "Korean Saju reading online"
   - "Korean Saju reading in English"
   - "Korean astrologer English consultation"
   - "Korean Four Pillars personal report"
   - "Korean Saju year ahead 2027"
   - "Korean Saju career analysis"

4. **Long-tail (high-conversion):**
   - "Korean Saju reading for [zodiac] Day Master"
   - "Korean Saju compatibility [with non-Korean partner]"
   - "Korean Saju business timing 2027"
   - "Korean Saju marriage timing for [year]"
   - "Korean Saju reading + career analysis"

### SEO content calendar (Year 1)

| Month | Posts | Format | Target keyword |
|---|---|---|---|
| Month 1 | 4 pillar posts | Long-form (2000–3000 words) | "What is Korean Saju", "Korean Saju vs Vedic", "Korean Four Pillars explained", "Korean Saju Day Master meaning" |
| Month 2 | 4 pillar posts | Long-form | "Korean Saju app English", "Korean Saju calculation", "Korean Saju 용신 favorable element", "Korean Saju 십신 ten gods explained" |
| Month 3 | 4 pillar posts | Long-form + comparison | "Korean Saju vs BaZi", "Korean Saju vs Chinese astrology", "Korean 만세력 vs Vedic Kundli", "Korean Saju compatibility analysis" |
| Month 4 | 4 pillar posts | Long-form + service pages | "Korean Saju reading online", "Korean astrologer English", "Korean Saju year ahead 2027", pricing page |
| Month 5 | 8 posts | Mix of long-form + comparison + FAQ | FAQ schema: "How much does a Korean Saju reading cost?", "How is Korean Saju different from Vedic?", etc. |
| Month 6+ | 8 posts/month | Mix | Steady-state content engine |

**Total Year-1 SEO output:** ~80–100 articles.

**SEO success metric:** organic traffic to site = 20k–50k visits/month by month 12, converting at 2–5% to a Spark (₹499) trial = 400–2,500 Spark orders/year from organic SEO alone. [estimate, conservative.]

### Technical SEO requirements

- **Site:** Next.js 14+ with App Router (server-rendered for SEO).
- **Schema markup:** FAQ schema for "What is X?" pages; Article schema for blog posts; Product schema for pricing.
- **Hreflang:** English / Korean / (later) Hindi.
- **Sitemap:** Auto-generated, submitted to Google Search Console + Naver Search Advisor.
- **Page speed:** <2s LCP for India mobile (3G/4G fallback).
- **Internal linking:** Every blog post links to the pricing page and to 2–3 related posts.
- **Author E-E-A-T:** Founder bio with credentials, Korean 명리 training, classical-tradition references. This matters for YMYL ("Your Money or Your Life") categories — Google is stricter on astrology/health/finance.

## 4. Instagram Reels strategy

### Content pillars (5 rotating themes)

1. **Day Master Mondays** — "If your Day Master is 丙 (Bing Fire), this week is about…" 30-second voiceover + Korean text overlay.
2. **Transit Tuesdays** — "Mercury retrograde is hitting your chart here — what it means for you."
3. **Compatibility Wednesdays** — "丙 Day Master + 辛 Day Master = what kind of couple?"
4. **Career Thursdays** — "Three best businesses for a 甲 Day Master."
5. **Year Ahead Fridays** — "2027 forecast for 丙 Day Master (preview)."

Plus: monthly **"Saju term of the month"** explainer (60-second long-form), and **"Korean 명리 vocabulary"** short (15-second "사주 = four pillars").

### Posting cadence

- **Daily Reels, 7–15 seconds each** (proven sweet spot for astrology niche — see `Hootsuite: Astrology Influencer Marketing Trends 2025`).
- **Cross-post to YouTube Shorts and TikTok** (compounding reach).
- **Reply to every comment within 60 minutes** for the first 7 days of a Reel (boosts algorithmic ranking).

### Projected growth

Based on `LikesWeb: 15+ Best Instagram Reels Ideas for Astrologers` and `SocialPilot: Astrology Instagram Growth 30-Day Calendar`:

- **30 days at 1 Reel/day:** ~1,500–3,000 new organic followers.
- **90 days at 1–2 Reels/day:** ~5,000–10,000 followers.
- **Year 1:** ~30,000–50,000 followers (achievable but requires consistency).

**Conversion estimate:** 30k followers × 1–2% engaged = 300–600 warm leads/month × 5–10% conversion = 15–60 orders/month from Instagram alone.

## 5. YouTube long-form strategy

### Channel positioning

The "thinking person's Korean Saju" channel. Long-form, educational, citation-grounded. Different from the astrology TikToks which are pure entertainment.

### Content types (3 formats)

1. **Educational explainers** (15–25 min): "Korean 명리 — the classical tradition explained" series. SEO-target the top-of-funnel keywords.
2. **Reading walkthroughs** (30–45 min): "Reading a real chart" series where the founder reads an anonymized chart and explains each interpretive step. Demonstrates expertise.
3. **Q&A and reaction** (15–30 min): "Reacting to free 만세력 apps — what's right, what's wrong" + viewer question responses.

### Posting cadence

- **2 long-form videos per month** (one explainer + one reading walkthrough).
- **8–12 Shorts per month** (re-purposed from Instagram Reels).

### Projected growth

Year 1 realistic: 5,000–15,000 YouTube subscribers with consistent posting.

**Conversion estimate:** 5–10k subs × ~2% conversion = 100–200 customers/year. [estimate, conservative.]

## 6. WhatsApp strategy (India retention + acquisition)

### Use cases

1. **Broadcast list for existing customers:** weekly "your week ahead" based on Day Master. Drives repeat Spark / Reading purchases.
2. **Welcome series for new Spark buyers:** nurture into Reading / Full Map with case studies.
3. **Year-ahead December push:** "Your 2027 forecast is ready — order now."

### Tools

- **Interakt, Wati, or AiSensy** — WhatsApp Business API providers. ~₹0.50–1 per message + monthly platform fee.
- **WhatsApp Click-to-Chat** on website for low-friction inquiry.

## 7. Paid ads strategy (post-product-market-fit)

### Timing

Do NOT start paid ads until **organic content engine has produced 50+ pieces of content and has at least 5,000 Instagram followers + 100 email subscribers**. Paid ads without social proof waste money.

### Channel priorities (when started)

1. **Instagram paid ads** (₹20–50k/month to start). Target interest categories: Korean Wave, K-drama, K-pop, astrology, Vedic astrology, tarot.
2. **YouTube in-stream ads** (₹10–30k/month). Target "Korean Saju" + adjacent keywords.
3. **Google Search ads** (₹20–50k/month). Only for high-intent transactional keywords. Need careful compliance framing.
4. **Avoid Facebook / Meta ads broadly** — same policy issues as Google.

### Compliance framing for paid

Google Ads disallows "destiny, fortune telling, spiritual, or psychic content" outright. The workaround is **frame the product as educational content + entertainment**:

- Headline: "Understand your Korean Four Pillars chart — educational reading"
- Landing page: emphasizes "tradition", "classical Korean 명리", "learn about yourself"
- Disclaimer: clearly visible "For educational and entertainment purposes. Not a prediction of specific events."

This is a gray area. **Be prepared for ad disapprovals and have an appeal process ready.**

## 8. Influencer / KOL partnerships

### Tier 1 — Micro-influencers (10k–100k followers, niche astrology)

- Cost: ₹5k–25k per collaboration in India; $200–1,000 in US.
- Best for: India Tier-1 (Hindi + English astrology creators), Korean diaspora (English Korean-culture creators).
- Format: sponsored Reel, sponsored YouTube Short, joint Instagram Live.
- KPI: track coupon code redemptions.

### Tier 2 — Mid-tier (100k–1M followers)

- Cost: ₹25k–2 lakh per collaboration; $1k–10k in US.
- Best for: brand awareness, not direct conversion.
- Risk: expensive, low ROI unless the influencer's audience is well-aligned.

### Tier 3 — Macro (1M+ followers)

- Skip in Year 1. Out of budget and the audience is too broad.

### Specific creator archetypes to approach

- "Korean culture" English-language creators (K-drama reaction, K-pop analysis, Korean food).
- "Astrology" English-language creators (Western + Vedic, but open to Korean Saju).
- "Career coaching" / "founder" creators in India.
- "Compatibility / relationship" creators.

## 9. Reddit strategy (Korean diaspora + Hallyu-curious)

### Target subreddits

- r/Korean (1.2M+ members)
- r/KDRAMA (700k+ members)
- r/kpop (1M+ members)
- r/ChineseAstrology (300k+)
- r/astrology (1M+)
- r/AskAstrologers (small but high-intent)

### Approach

- **Do NOT spam.** Reddit users detect and punish.
- **Contribute genuine value:** answer questions, share educational content, occasionally mention the product as a resource.
- **One promotional post per subreddit per quarter max.**
- **Long-term brand building, not direct sales.**

## 10. Naver strategy (Korean diaspora — only if Korea-expansion is in scope)

If we expand to Korean-speaking audiences in Korea itself:

- **Naver Blog:** Korean-language blog with educational content.
- **Naver Café:** Join relevant 만세력/사주 cafés, contribute.
- **Naver Search:** SEO via Naver Search Advisor (different algorithm than Google).

**Verdict: defer to Year 3 unless the founder is Korean-speaking and has the bandwidth.** Korean-language content marketing is a separate full-time job.

## 11. Content-driven SEO + social flywheel

The full marketing flywheel:

```
       ┌──────────────────┐
       │  Blog post / SEO  │ ──→ Organic Google traffic
       │  (1 long-form /    │     ↓
       │   week, 2000+ wd) │     Email subscriber
       └──────────────────┘     ↓
                               Spark ₹499 trial
                               ↓
                ┌──────────────┴──────────────┐
                ↓                             ↓
       ┌──────────────────┐         ┌──────────────────┐
       │ Instagram Reel    │ ←───    │ YouTube Short /   │
       │ (1 / day, 15 sec) │         │ Long-form (8/mo)  │
       └──────────────────┘         └──────────────────┘
                ↓                             ↓
       Brand discovery                 Deep-dive audience
       ↓                             ↓
       ──────────────────────────────
                       ↓
              Warm lead → Spark → Reading → Full Map → Companion
```

## 12. First-90-day marketing plan

### Days 1–30: Foundation

- [ ] Set up Next.js web app at custom domain.
- [ ] Write 4 long-form pillar blog posts (2000+ words each).
- [ ] Set up Instagram + YouTube + TikTok handles.
- [ ] Film and post 30 daily Instagram Reels (Day Master Mondays + concept + 5 compat + 5 career).
- [ ] Set up email list (Resend or ConvertKit) with welcome sequence.
- [ ] Publish pricing page + intake form.

### Days 31–60: Iteration

- [ ] Double down on top-performing Reel formats (top 3 from Month 1).
- [ ] Write 4 more long-form posts (comparison + service pages).
- [ ] First 2 YouTube long-form videos.
- [ ] First Reddit organic contributions (3–5 high-value comments).
- [ ] First paid Instagram ad (₹10k spend, narrow targeting).

### Days 61–90: Scale

- [ ] Hit 3,000+ Instagram followers.
- [ ] Hit 1,000+ email subscribers.
- [ ] Hit 5,000+ organic Google impressions/month.
- [ ] First 50 paying customers (mix of Spark + Reading + Full Map).
- [ ] Decide on first influencer collaboration (if budget allows).

## 13. What NOT to do

1. **Don't run paid Google or Facebook ads before organic content engine is mature.** Without social proof, paid ads waste money on astrology-policy grey areas.
2. **Don't spam Reddit.** One promotional mention per subreddit per quarter.
3. **Don't use AI-generated talking-head videos.** The brand is "classical tradition + genuine expertise" — AI faces break the brand.
4. **Don't compete on price.** No ₹99 / ₹199 Spark. Undercutting cheapens the brand.
5. **Don't fake reviews or testimonials.** Astrology buyers are sophisticated; fakes destroy trust.
6. **Don't ignore YouTube Shorts.** It's a free distribution channel that compounds Instagram Reels.
7. **Don't over-promise in copy.** "Find your true love in 2027" violates ASCI + damages brand. Always phrase as tendencies.
8. **Don't ignore email.** Email has 5–10× the conversion rate of social. Build the list from Day 1.

## 14. Success metrics (Year 1)

| Metric | Target month 6 | Target month 12 |
|---|---|---|
| Organic Google traffic | 5,000 visits/month | 30,000 visits/month |
| Email subscribers | 1,000 | 5,000 |
| Instagram followers | 5,000 | 25,000 |
| YouTube subscribers | 500 | 5,000 |
| Reddit karma / trust | 1,000 karma across relevant subs | 5,000 karma |
| Total paying customers | 50 | 250–500 |
| Total revenue | ₹5–10 lakh | ₹40–80 lakh |
| Conversion rate (lead → paying) | 3–5% | 5–8% |
| Customer acquisition cost (blended) | ₹500–1,500 | ₹400–800 |

## 15. Sources

- [Google Ads Policy: Destiny, fortune telling, spiritual, or psychic content](https://support.google.com/adspolicy/answer/4651367)
- [LikesWeb: Best Instagram Reels Ideas for Astrologers 2025](https://likesweb.com/blog/instagram-reels-ideas-for-astrologers/)
- [SocialPilot: Astrology Instagram Growth 30-Day Calendar](https://www.socialpilot.ai/blog/instagram-reels-strategy)
- [Buffer: How to Grow an Astrology Niche on Instagram 2024](https://buffer.com/library/instagram-astrology-niche)
- [Hootsuite: Astrology Influencer Marketing Trends 2025](https://www.hootsuite.com/research/astrology-trends)
- [Later: Instagram Reels Algorithm 2024-2025](https://later.com/blog/instagram-reels-algorithm)
- [AstroVed: Growing a Spiritual Brand on Instagram Reels](https://www.astroved.com/blog/instagram-reels-astrology)
- [Neil Patel: 30-Day Instagram Growth Plan](https://neilpatel.com/blog/30-day-instagram-growth)
- [Mangools: Astrology Keywords and Hashtags](https://mangools.com/blog/astrology-hashtags)
- [Sprout Social: Instagram Reels Benchmarks 2024](https://sproutsocial.com/insights/instagram-reels-benchmarks)
- [Backlinko: Instagram SEO and Reels Discovery 2025](https://backlinko.com/instagram-seo)
- [Redseer: Astro-Tech trends](https://redseer.com/articles/astro-tech-cosmic-trends-digital-era/)
- [Indian Express: Gen Z + astrology apps](https://preprod.indianexpress.com/article/lifestyle/why-gen-z-is-turning-to-astrology-apps-to-find-solutions-to-life-problems-10031516/)
- [NumroVani: AI Astrology 2025 Consumer Trends](https://numrovani.com/ai-astrology-2025-mid-year-study/)
