# 10 · Risks & Do-Not-Do

**Date:** 2026-06-26
**Scope:** Risks (regulatory, ethical, business, operational) and a list of things to actively avoid building, saying, or doing.

---

## 1. The risk register, in priority order

### Risk 1 — Interpretive quality risk (HIGH, MOST LIKELY)

**What it is:** The engine draft for Reading and Full Map tiers is marked `[ENGINE DRAFT — REVIEW REQUIRED]`. If we ship Reading or Full Map PDFs without human review, the interpretive quality is uneven. Some reports will resonate; some won't. The mismatch between client expectation (₹1,499 / ₹3,499 for "deep" insight) and engine-draft quality is the #1 refund-risk and #1 review-risk.

**Mitigation:**
- Phase 1 ships Reading/Full Map with a **mandatory 45–90 minute human-review SLA**. Founder does it.
- Phase 2 builds **AI-assisted review** to cut human time to 20–30 min.
- Phase 3 hires **1–2 part-time readers** to absorb the review workload.
- Never promise instant delivery on Reading or Full Map. Always say "48–72 hour delivery."

**Severity if ignored:** Every refund case becomes a public Trustpilot / Google Review. Brand damage compounds. The first 10 negative reviews can kill a paid product before it gains traction.

### Risk 2 — Regulatory risk: ASCI + Google Ads + Meta Ads (HIGH)

**What it is:**
- **Google Ads** explicitly prohibits "Destiny, fortune telling, spiritual, or psychic content" including astrology, horoscopes, numerology, tarot. ([Google Ads Policy](https://support.google.com/adspolicy/answer/4651367))
- **Meta Ads** has similar restrictions for "fortune telling" content.
- **ASCI (India)** requires astrological claims to carry clear disclaimers ("For entertainment purposes only").
- **Apple App Store** is friendlier to astrology apps but rejects misleading health/financial claims.

**Mitigation:**
- Never run Google Search ads directly. Use SEO + organic + influencer.
- For Instagram/Facebook paid: frame as "educational content about classical Korean tradition" + include disclaimer.
- Every report PDF must carry a disclaimer: "Saju describes tendencies and timing. It does not predict specific events."
- Every ad copy must avoid absolute predictive language ("You will..." → "Tendencies suggest...").

**Severity if ignored:** Account ban + ad spend wasted + potential ASCI complaint to ad-standards body.

### Risk 3 — Refund risk on the high tier (HIGH)

**What it is:** Full Map at ₹3,499 is a 3-figure USD-equivalent purchase. If the client reads it and feels "this doesn't apply to me," they will demand a refund. Razorpay/Stripe dispute processes are slow (14–60 days) and the dispute goes against the merchant by default if no documentation is provided.

**Mitigation:**
- **Documented refund policy in CLAUDE.md and on every receipt** (see `06-monetization-strategy.md` §9 for the recommended policy).
- For Full Map, offer an **optional 30-minute clarification call** post-delivery. Most "I'm not satisfied" complaints dissolve after a live conversation.
- For Spark, **no refunds** (it's an impulse purchase; instant delivery).
- For Reading, **refund only on calculation error or SLA breach**.
- For Full Map, **refund on calculation error, SLA breach, or post-clarification-call dissatisfaction**.
- **Keep engine drafts for every paid order** as evidence in dispute resolution.

**Severity if ignored:** Chargeback rate above 1% triggers Razorpay / Stripe enhanced monitoring. Above 3% triggers account review. Above 5% triggers account hold.

### Risk 4 — Cultural / tradition backlash (MEDIUM-HIGH)

**What it is:** Korean 명리 has internal schools (Gyeonglakgoyo, Jeokcheon-su, Yeonhae-japyeong, Gungtong-bogam, Myeongrijeongjong) that disagree on edge cases. A serious Korean 명리 practitioner who reads one of our reports and spots a "wrong" interpretation (per their school) will publicly call it out. The risk is highest in Korea itself and among Korean diaspora on Reddit / Naver.

**Mitigation:**
- Always cite the source `knowledge/*.md` file for interpretive claims.
- Use `[UNCERTAIN]` flags where the tradition is divided.
- Use `[ENGINE DRAFT — REVIEW REQUIRED]` for AI-drafted prose.
- Don't claim "this is the only correct interpretation" — present interpretations as "according to X tradition."
- Engage seriously with Korean 명리 practitioners who push back. Public respectful responses build credibility.

**Severity if ignored:** A single well-publicized takedown by a credible Korean 명리 scholar could collapse the brand in the Korean diaspora market. The brand's defense is the citation-grounded knowledge base.

### Risk 5 — Founder burnout (HIGH)

**What it is:** Solo founder doing interpretation + engineering + marketing + sales + support. 60–80 hour weeks are common in Year 1. Burnout is the most common failure mode for solo-founder consumer products.

**Mitigation:**
- **Phase 1 cap Reading/Full Map at 3–5 per week** (founder review bandwidth).
- **Phase 2 introduce AI-assisted review** to drop review time per order.
- **Phase 3 hire first part-time reader** to absorb the review workload.
- **Strict 50-hour week cap** for the founder after Month 6.
- **Quarterly 1-week breaks** to prevent cumulative burnout.

**Severity if ignored:** Burnout → product abandonment → existing customers stranded → refund requests spike → brand damaged.

### Risk 6 — Bus factor of one (MEDIUM)

**What it is:** Solo founder. If the founder is unavailable (illness, family emergency, vacation, anything), all interpretation halts. There is no one else who can do the work.

**Mitigation:**
- **Phase 2 start training a part-time reader** (even before the workload requires it).
- **Phase 3 always have 2 trained readers** (founder + 1 backup).
- **Document everything** — every interpretation rule, every client interaction pattern.
- **Engine output is auditable** — even without the founder, the engine can produce an automated Spark tier.

**Severity if ignored:** A 2-week founder absence at the wrong moment could trigger a wave of refund requests and lost customers.

### Risk 7 — Content commoditization (MEDIUM)

**What it is:** If the interpretive layer is purely engine-drafted, a competitor can replicate it cheaply. The moat is the citation-grounded knowledge base + the founder's interpretive voice. Both are vulnerable to being copied by an LLM with the right prompt.

**Mitigation:**
- **Build the citation ground rules into the public-facing content.** Show the classical-tradition references. The citations themselves are a brand asset.
- **Build the founder's interpretive voice into the brand.** "Read by [founder name], classically trained in Korean 명리" is the human signature competitors can't replicate.
- **The Companion subscription** with quarterly check-ins is the human-relationship moat.
- **Don't share the knowledge base publicly.** Keep `knowledge/*.md` private.

**Severity if ignored:** Competitor with similar engine + LLM-prompt-driven interpretation + lower price can undercut us within 12 months.

### Risk 8 — Market timing (LOW-MEDIUM)

**What it is:** Astrology app market is currently in a "boom" (per AstroTalk FY24, Redseer reporting, market.us 16% CAGR). Will it still be hot in 24–36 months?

**Mitigation:**
- Don't rely on market tailwinds. Build a product that works in a flat market.
- The Korean Saju niche is less saturated than Vedic Jyotish; the demand is real even if the overall astrology market cools.
- The Hallyu Wave is a 20+ year trend (since 1997); it's not a fad.

**Severity if ignored:** If the astrology market contracts 30%, our revenue scenario drops proportionally. But the worst case is still "lifestyle business" not "company failure."

### Risk 9 — Data privacy (MEDIUM)

**What it is:** Birth data is sensitive PII. Email + name + DOB + time + location = full identity reconstruction. Storage and processing must be GDPR-compliant (for EU customers) and DPDP-compliant (for India).

**Mitigation:**
- Store only what's needed for service delivery.
- Encrypt PII at rest.
- Provide data export + deletion on request (DPDP requirement).
- Don't sell or share PII with third parties (no marketing data co-ops).
- Privacy policy on website from Day 1.

**Severity if ignored:** A data breach exposing client birth data is a brand-killer. GDPR fine up to 4% of revenue.

### Risk 10 — Payment processor de-platforming (LOW)

**What it is:** Razorpay / Stripe / PayPal sometimes de-platform astrology merchants. AstroTalk has navigated this; smaller players are more vulnerable.

**Mitigation:**
- Maintain accounts with both Razorpay (India) and Stripe (international) for redundancy.
- Have a backup plan: Cashfree (India) + Paddle (international).
- Comply with all merchant policies from Day 1.

**Severity if ignored:** Account suspension = revenue halt.

## 2. Things to actively NOT do (the anti-feature / anti-behavior list)

### Anti-features (don't build)

1. **Tarot readings.** Out of scope per CLAUDE.md + cheapens brand.
2. **Dream interpretation (꿈해몽).** Out of scope.
3. **Face reading (관상).** Out of scope + privacy risk (requires photo upload).
4. **Numerology / life-path numbers.** Different tradition; dilutes Korean 명리 positioning.
5. **AI chatbot UX (text-message interface).** 사주GPT does this; lowest-quality interpretation possible.
6. **Per-minute chat marketplace.** Requires reader network; not feasible for solo founder.
7. **Gemstone / yantra shop.** Separate business.
8. **Live streaming / video consultations.** Same constraint.
9. **Generic fortune-telling features.** "Will I be rich?" — brand-killer.
10. **Vedic Jyotish features.** Out of scope; risks credibility with both traditions.
11. **Western astrology features.** Out of scope per CLAUDE.md.
12. **Zi Wei Dou Shu (紫微斗數) features.** Out of scope.
13. **Custom ephemeris.** sajupy is sufficient.
14. **Native ephemeris from scratch.** Categorically no.

### Anti-behaviors (don't do)

1. **Don't ship Reading or Full Map without human review.** Period.
2. **Don't run Google Search ads or Facebook ads with "astrology" / "fortune-telling" copy.** Banned.
3. **Don't make absolute predictive claims in copy.** "You will marry in 2027" → "Tendencies in your chart support marriage timing in 2027." Always tendency language.
4. **Don't claim medical / legal / financial certainty.** Saju describes tendencies, not diagnoses or guarantees.
5. **Don't undercut the price.** No ₹99 / ₹199 Spark. ₹499 is the floor.
6. **Don't fake reviews or testimonials.** Astrology buyers are sophisticated; fakes destroy trust.
7. **Don't use AI-generated talking-head videos.** The brand is "classical tradition + genuine expertise."
8. **Don't use emojis inappropriately in serious contexts.** The Element Balance colors (🔴🟡⚪🔵🟢) are appropriate; "✨🔮💫" branding is not.
9. **Don't over-discount.** Use trial tiers + Companion subscription instead.
10. **Don't bundle Reading + Full Map.** Forces the customer to choose. Let them self-select.
11. **Don't spam Reddit or forums.** One promotional mention per subreddit per quarter max.
12. **Don't ignore email.** Email is the highest-converting channel.
13. **Don't promise instant Reading/Full Map delivery.** The 48–72 hour SLA is part of the value.
14. **Don't send Reading/Full Map without at least one round of personal review.** The reader's eye is the differentiator.
15. **Don't make claims that can't be cited from `knowledge/`.** Every interpretive claim is auditable.

### Anti-strategies (don't pursue)

1. **Don't raise outside capital before crossing ₹1 lakh/month self-service revenue.** Bootstrapping preserves founder control of the classical-tradition positioning.
2. **Don't try to win the Indian mass market head-to-head against AstroTalk.** Unit economics don't work for solo founder.
3. **Don't try to compete with Korean Saju apps in Korea itself.** Saturated market + language barrier.
4. **Don't pretend to be Vedic Jyotish.** The traditions are different and Indian practitioners will spot it.
5. **Don't dilute into Western astrology.** Classical-tradition positioning is the moat.
6. **Don't pursue B2B API before Year 2.** Founder focus is needed for direct-to-consumer.
7. **Don't hire full-time in Year 1.** Use part-time readers and part-time ops.
8. **Don't expand to iOS until Android metrics support it.**
9. **Don't build a course before Companion subscription is proven.**
10. **Don't expand language (Korean, Hindi) before English product-market-fit is proven.**

## 3. Risk-mitigation matrix (one-page summary)

| Risk | Severity | Likelihood | Mitigation cost | Mitigation owner |
|---|---|---|---|---|
| Interpretive quality | High | High | Phase 2 AI-assisted review | Founder |
| ASCI / Google Ads policy | High | Medium | Disclaimer + compliance framing | Founder + agency |
| Refund on high tier | High | Medium | Clear policy + clarification call | Founder + support |
| Tradition backlash | Med-High | Low-Med | Citation-grounded knowledge base | Founder |
| Founder burnout | High | High | Hire part-time readers by month 9 | Founder |
| Bus factor of one | Medium | Medium | Documentation + part-time reader | Founder |
| Content commoditization | Medium | Medium | Founder voice + citations as moat | Founder |
| Market timing | Low-Med | Low | Product that works in flat market | N/A (built-in) |
| Data privacy | Medium | Low | GDPR + DPDP compliance | Founder + lawyer |
| Payment de-platforming | Low | Low | Multi-processor redundancy | Founder |

## 4. The "what kills the product" scenarios

In rough order of likelihood:

1. **Solo founder burnout in months 4–8.** Mitigation: part-time reader by month 9, 50-hour cap.
2. **Wave of refund requests on Full Map in months 2–4.** Mitigation: human-review mandatory, optional clarification call, documented refund policy.
3. **A credible Korean 명리 practitioner publicly criticizes the product.** Mitigation: citation-grounded interpretation, `[UNCERTAIN]` flags, `[ENGINE DRAFT — REVIEW REQUIRED]` markers.
4. **ASCI complaint / Google Ads ban wipes out marketing.** Mitigation: organic SEO + Instagram first, paid ads later, careful compliance.
5. **A larger competitor (e.g., a Korean astrology app) launches English version and undercuts us.** Mitigation: build founder voice moat + Companion subscription by then.
6. **A data breach exposes client birth data.** Mitigation: encrypt + minimize storage + GDPR/DPDP compliance.
7. **Razorpay / Stripe de-platforms the merchant account.** Mitigation: multi-processor redundancy + clean policy compliance.

## 5. The "what makes the product succeed" scenarios

1. **A Reel goes viral in months 2–3.** "丙 Day Master, this week is..." hits 1M views, drives 5,000 Spark orders in a week.
2. **A K-content creator in the Korean diaspora organically mentions us.** 50,000 visitors in a week, 500 Reading orders.
3. **An SEO pillar post ranks #1 on Google for "Korean Saju reading English."** 50,000 monthly organic visitors, 1,000+ Spark orders/month.
4. **A media outlet (e.g., The Print, The Hindu, Vogue India) does a feature on classical Korean traditions in India.** 200,000 visitors in a week, 2,000 orders.
5. **An influencer in Tier-1 India (e.g., @akankshahazari, @thecomedyfeed) shares a personal Full Map reading on Instagram.** 500,000 views, 1,000 Reading orders.
6. **A Reddit post on r/Korean asking "where can I get a Saju reading in English?" gets 5,000 upvotes and our product is the top answer.** 10,000 visitors, 200 Reading orders.

## 6. Compliance checklist (Day 1 requirements)

- [ ] Privacy policy on website (GDPR + DPDP compliant).
- [ ] Refund policy in CLAUDE.md and on every receipt.
- [ ] Disclaimer in every report PDF: "Saju describes tendencies and timing. It does not predict specific events."
- [ ] Disclaimer on landing page: "For educational and entertainment purposes."
- [ ] Email opt-in (double opt-in recommended).
- [ ] Cookie banner on website.
- [ ] Data export + deletion endpoint.
- [ ] Razorpay + Stripe accounts compliant with merchant policies.
- [ ] No fake reviews / testimonials.
- [ ] All ad copy reviewed for compliance language before launch.

## 7. Sources

- [Google Ads Policy: Destiny, fortune telling, spiritual, or psychic content](https://support.google.com/adspolicy/answer/4651367)
- [ASCI Code (Advertising Standards Council of India)](https://asci.social/complaints/)
- [Razorpay prohibited businesses policy](https://razorpay.com/support/policies/)
- [Stripe prohibited and restricted businesses](https://stripe.com/legal/restricted-businesses)
- [Apple App Store Review Guidelines 5.3.4 (Astrology)](https://developer.apple.com/app-store/review/guidelines/)
- [Meta Advertising Standards: Personal Health and Wellness](https://transparency.meta.com/policies/ad-standards/)
- [GDPR (EU data protection)](https://gdpr-info.eu/)
- [DPDP Act 2023 (India)](https://www.meity.gov.in/data-protection-framework)
- [Indian Penal Code § 508 (criminal intimidation by threat of divine displeasure)](https://indiankanoon.org/doc/615953/)
- Existing project: [CLAUDE.md](../../CLAUDE.md)
- Existing project: [tasks.md](../../tasks.md)
- Existing project: [ISSUES_FOUND.md](../../ISSUES_FOUND.md)
