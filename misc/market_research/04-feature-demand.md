# 04 · Feature Demand — What Users Actually Pay For

**Date:** 2026-06-26
**Scope:** Most in-demand features for Saju / astrology apps, what users actually pay for vs. expect free, what they complain about, and how the existing Saju codebase maps to demand.

---

## 1. Feature demand ranking (consolidated from market signals)

The market signal across Western astrology apps, Korean Saju apps, Indian astrology apps, and the BaZi/ZWDS segment converges on a clear hierarchy of feature value.

| Rank | Feature | Demand intensity | What users expect | What users will pay for | Free or paid |
|---|---|---|---|---|---|
| 1 | **Daily horoscope / today's fortune** | Very high | Personalized daily text in the app | Email / push delivery | **Free** (funnel) |
| 2 | **Natal chart / four pillars calculation** | Very high | Always free | — | **Free** (top of funnel) |
| 3 | **Compatibility / synastry / 궁합** | Very high | Basic free comparison | Detailed partner analysis | **Freemium** (basic free, deep paid) |
| 4 | **Year-ahead / annual forecast** | High | Year-themed marketing | Per-year personal PDF | **Paid** ($10–$50) |
| 5 | **Career / money / business timing** | High | Vague free guidance | Detailed deep-dive | **Paid** ($30–$200) |
| 6 | **Compatibility deep-dive (relationship analysis)** | High | Basic numeric score | Long-form compatibility analysis | **Paid** ($30–$150) |
| 7 | **Lucky attributes (colors, numbers, directions, foods)** | Medium-high | Always free | Personal reference card | **Free** (PDF supplement) |
| 8 | **Push notifications for transits / luck windows** | Medium-high | Expected free | — | **Free** (retention lever) |
| 9 | **Monthly / weekly outlook** | Medium | Free preview | Personal PDF | **Freemium** |
| 10 | **Daily-luck (일운) and auspicious date picking** | Medium | Free preview | Date-picking tool | **Freemium** |
| 11 | **Compatibility with multiple partners (saved list)** | Medium | — | Persistent feature | **Paid** (subscription) |
| 12 | **Marriage timing / wedding-date picking** | Medium | Vague free | Specific year/month | **Paid** |
| 13 | **Children / parenting analysis** | Low-medium | Free preview | Personal reading | **Paid** (niche) |
| 14 | **Health tendencies** | Medium | Free preview | Detailed analysis | **Paid** (regulatory-sensitive) |
| 15 | **Relocation / geography** | Low-medium | Free preview | City comparison | **Paid** (niche) |
| 16 | **Relocation / feng shui / directions** | Low | Free preview | Detailed home/office analysis | **Paid** (niche) |
| 17 | **Live chat with human reader** | High (in India) | Per-minute | — | **Paid per minute** |
| 18 | **Course / certification content** | Low | — | Cohort-based | **Paid** (niche) |
| 19 | **Community / social feed** | Medium (Western apps) | Free | — | **Free** (engagement lever) |
| 20 | **API / white-label B2B** | Low (B2B only) | — | Per-call pricing | **B2B** |

## 2. What users actually pay for (the monetization pyramid)

```
        ┌─────────────────────────┐
        │  Live chat with human    │  AstroTalk-style, India only
        │  reader (per-minute)     │  Not in scope for our solo founder
        └─────────────────────────┘
            ▲
        ┌─────────────────────────┐
        │  Full Map ₹3,499         │  ← Our top tier
        │  (18-22 pages, deep-dive │     Demand validated by 6 paid pilots
        │   career, relationships, │
        │   10-year forecast,       │
        │   auspicious dates)      │
        └─────────────────────────┘
            ▲
        ┌─────────────────────────┐
        │  Reading ₹1,499          │  ← Our anchor tier (default)
        │  (10-12 pages, full      │     Most popular — 10–12 pages
        │   natal reading)        │     maps to Western apps'
        └─────────────────────────┘     $11.99 "Your Year Ahead"
            ▲
        ┌─────────────────────────┐
        │  Spark ₹499              │  ← Our entry tier
        │  (4-5 pages, snapshot +  │     Self-service, automated
        │   year-ahead paragraph)  │     Top of funnel
        └─────────────────────────┘
            ▲
        ┌─────────────────────────┐
        │  Companion ₹799/month    │  ← Future (not yet built)
        │  Quarterly check-in +    │     Recurring revenue, retention
        │   monthly energetic      │
        │   guidance               │
        └─────────────────────────┘
            ▲
        ┌─────────────────────────┐
        │  FREE: chart snapshot +  │  Top of funnel — drives
        │  daily/weekly fortune +  │  awareness and Spark conversion
        │  monthly outlook         │
        └─────────────────────────┘
```

## 3. User complaints (the things to actively avoid)

From UK/US astrology app data, these are the most common 1-star review triggers. We should design the product to avoid each one.

1. **Recycled content becoming obvious.** Long-term users notice when "daily horoscopes" repeat. → Personalize by day master, not by zodiac; surface genuinely different content each day.
2. **Aggressive upsells disguised as horoscope previews.** "Your week is intense — unlock the full report to find out why!" → Don't gate basic natal interpretation; gate only deep analysis.
3. **Notification fatigue.** Apps sending 2–3 push notifications per day get punished with 1-star reviews. → 1 high-quality notification per day, max.
4. **Hidden auto-renewal.** Subscription trials that auto-renew without warning. → No trial-to-paid traps; clear pricing, clear cancellation.
5. **Manipulative notification copy.** "Big energy shift today, open to see!" → Plain, classical-tradition language, not wellness-influencer copy.
6. **Server outages on significant days.** Retrogrades, eclipses, New Year — the day your app crashes is the day you lose paying users. → Architecture matters.
7. **Refund denied on legitimately bad reports.** Reading tier at ₹1,499 with content that doesn't resonate is a refund dispute waiting to happen. → Have a clear refund policy and honor it.
8. **"AI said my boyfriend is wrong for me."** Generic interpretations that produce confidently-wrong claims damage trust. → The engine already marks [UNCERTAIN] and [ENGINE DRAFT — REVIEW REQUIRED] for exactly this reason. Keep the review step.
9. **Predictions that don't come true.** "You will get married in 2026." → ASCI violation + trust damage. Always frame as tendencies.
10. **Health / financial claims with no disclaimer.** "Your chart says you'll have a liver issue in 2027." → The CLAUDE.md ground rules forbid this regardless of platform.

## 4. Feature gaps in the current Saju codebase

| Feature | Status in codebase | What to do |
|---|---|---|
| **Four pillars calculation** | ✅ Built — 129 pytest cases pass | Done. |
| **십신 / 12운성 / 대운 / 신살 / strength heuristic** | ✅ Built | Done. |
| **Solar-term + solar-time + Korean 야자시 handling** | ✅ Built | Done. |
| **Natal chart snapshot (the "free tier chart")** | ✅ Built (`generate_premium_report` chart-at-a-glance) | Free with email gate. |
| **Tiered reports Spark / Reading / Full Map** | ✅ Built | Done. |
| **Self-service PDF generation** | ✅ Built (`tools/client_intake_app.py`) | Deploy. |
| **PDF toolchain (reportlab + HTML/Playwright)** | ✅ Built | Done. |
| **Citation-grounded knowledge base** | ✅ Built (11 files) | Done — the moat. |
| **Intake form** | ✅ Built | Deploy. |
| **Daily / weekly / monthly fortune engine output** | 🟡 Partial — `sewoon.py` has daily/monthly overlay; not packaged for push delivery | **Build**: package as a daily-content engine. |
| **Compatibility (궁합) analysis** | ❌ Missing | **Build** — single most-demanded feature in Korean Saju market. |
| **Compatibility with multiple saved partners** | ❌ Missing | **Defer** to Companion subscription. |
| **Push notifications / email delivery** | ❌ Missing | **Build** (Firebase Cloud Messaging + SendGrid/Resend). |
| **User accounts / login / history** | ❌ Missing | **Build** — required for Companion and any retention loop. |
| **Mobile app (Android)** | ❌ Missing | **Build** — see `07-app-platform-decision.md`. |
| **Payment gateway (Razorpay / Stripe)** | ❌ Missing | **Build** — required for self-service. |
| **Live human chat / marketplace** | ❌ Missing | **Skip** — wrong shape for solo founder. |
| **Course / certification content** | ❌ Missing | **Defer** to month 18+. |
| **API / B2B white-label** | ❌ Missing | **Defer** to month 24+. |
| **Hindi language localization** | ❌ Missing | **Defer** to month 12+. |
| **Korean language localization** | ❌ Missing | **Defer** — minor opportunity. |

## 5. Where the existing codebase over-invests vs. under-invests

### Over-invests (gilding the lily for current scale)
- **HTML/Playwright PDF backend** — premium typography is nice but reportlab covers 95% of client perception. Keep both backends, but don't spend more engineering time on typography polish.
- **Grid / pattern detection (천간합 / 화격 / 종격)** — useful for the [ENGINE DRAFT — REVIEW REQUIRED] notes, but few clients actually want to discuss 종격 candidates in their reading. The interpretive value is small.
- **Daily-luck (일운) overlay** — academically interesting, but only ~1% of paying clients will ask for 일운 by name. Keep in skeleton; don't feature in marketing.

### Under-invests (the actual product gaps)
- **Compatibility analysis (궁합)** — this is the **single most-demanded feature in the Korean Saju market**, and we have no implementation. The market signal is unambiguous. Build it next.
- **Daily-content packaging** — the engine has all the data (daily pillar, monthly pillar, 세운, 월운, 일운), but no packaging for daily push / daily email. This is the **retention gap** — without daily content, there's no reason for a free user to convert to paid Companion.
- **User accounts + payment** — without login, you can't build a subscription, can't store multiple partner comparisons, can't show a purchase history. This is the **infrastructure gap**.
- **Mobile app** — without Android, the Indian + Korean diaspora audience can't discover and share the product organically.

## 6. Most-wanted features NOT to build (anti-feature list)

1. **Daily generic horoscope feed.** "Aries today: be careful with money." These are noise; they cheapen the brand.
2. **Tarot readings.** Out of scope per CLAUDE.md. Also cheapens the brand.
3. **Dream interpretation (꿈해몽).** Out of scope. Adds clutter.
4. **Face reading (관상).** Out of scope. Cannot be done without a photo, which raises privacy concerns.
5. **Numerology / life-path numbers.** Western numerology is a separate tradition; mixing dilutes the Korean 명리 positioning.
6. **AI chatbot UX.** 사주GPT, Aha Chat, and Palja Chat all do this. The chatbot UX is the lowest-quality interpretation possible. We should not compete here.
7. **Per-minute chat marketplace.** Requires a reader network. Cannot be built by solo founder.
8. **Astro-shop (gemstones, yantras, rudraksha).** Indian players monetize this well, but it's a separate business (inventory, fulfillment). Out of scope.
9. **Live streaming / video consultations.** Same reason as per-minute chat. Out of scope.
10. **Generic "Will I be rich?" fortune-telling.** Brand-killer. ASCI violation risk. Avoid.

## 7. Demand signal: what the 6 paid pilots actually bought

Looking at `candidates_horoscope/reports/` — what did the 6 paid pilot candidates actually ask for, beyond the base reading?

| Topic | How many candidates asked | Existing file |
|---|---|---|
| Career / business / venture timing | **6 of 6** | career.md (5 candidates), cross-candidate-business-analysis.md |
| Relationships / marriage / compatibility | 2 of 6 (Mahesh, Vishnu Priya) | relationships.md |
| Year-specific outlook | 0 explicit files (covered in base Full Map) | — |
| Current major luck (대운) | 0 explicit files (covered in base Full Map) | — |
| Health | 0 | — |
| Parenting / children | 0 | — |
| Relocation / geography | 0 | — |
| Compatibility with a specific named person | 0 explicit, but asked verbally in 2 cases | — |

**Insight:** Career / business / venture timing is **the dominant paid use case** for this audience. Compatibility with named partners is the second-most demanded, and it's currently delivered verbally without a dedicated file. The base reading already covers year-outlook and current-대운 in the Full Map tier — the additional-file upsell isn't needed there.

## 8. Recommendations

### Build now (months 1–6)
1. **Web app intake → payment → PDF download pipeline.** Spark (₹499) self-service. Razorpay integration.
2. **Compatibility (궁합) deep-dive** as a paid add-on (₹999 standalone or ₹499 bundled into Reading+).
3. **Daily-content engine** — emails "today's pillar" with a personalized one-paragraph reading for free users.
4. **Push notifications** for free users: "today is a 丙 day, your Day Master — favorable for launching."
5. **Android PWA** (see `07-app-platform-decision.md`).

### Build later (months 7–18)
6. **Companion subscription (₹799/month)** — quarterly check-in + monthly energetic guidance.
7. **User accounts + purchase history + saved partners.**
8. **Hindi language localization.**
9. **Compatibility deep-dive with multiple saved partners.**

### Build much later (months 19–36)
10. **Course / certification** — "Introduction to Korean 명리" paid cohort course for serious enthusiasts.
11. **API / B2B white-label** — license the engine + report generator to other astrology platforms.
12. **iOS native app** — only after Android demand is validated.

### Skip entirely
- Tarot, dream interpretation, face reading, numerology, AI chatbot UX, per-minute chat marketplace, gemstone shop, live video consultations, generic fortune-telling features.

## 9. Sources

- [ElectroIQ: Astrology App Statistics 2026](https://electroiq.com/stats/astrology-app-statistics/)
- [Vedika: Profitable Astrology SaaS Guide](https://vedika.io/blog/astrology-saas-business-guide)
- [Unstar: 5 Astrology Apps Ranked 2026](https://unstar.app/blog/co-star-sanctuary-pattern-nebula-stellium-astrology-apps-ranked-2026)
- [ApPark: Best Astrology App 2026 Data Analysis](https://appark.ai/en/blog/market-insights-best-astrology-app-2026-growth-analysis)
- [BestTechSols: UK Astrology App Stats 2026](https://bestechsols.co.uk/astrology-app-statistics-uk/)
- [Astrology Tech Insights: BaZi monetization 2025](https://astrologytechinsights.com/bazi-monetization-2025)
- [Redseer: Astro-Tech trends](https://redseer.com/articles/astro-tech-cosmic-trends-digital-era/)
- [Indian Express: Gen Z + astrology apps](https://preprod.indianexpress.com/article/lifestyle/why-gen-z-is-turning-to-astrology-apps-to-find-solutions-to-life-problems-10031516/)
- [NumroVani: AI Astrology 2025 Consumer Trends](https://numrovani.com/ai-astrology-2025-mid-year-study/)
- [The Economic Times: AstroTalk FY24](https://economictimes.indiatimes.com/tech/startups/astrotalk-rides-online-astrology-boom-to-double-fy24-revenue-to-rs-651-crore/articleshow/113500403.cms)
