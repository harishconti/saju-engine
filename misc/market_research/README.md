# Market Research — Saju Reading App & Service

> ## ⚠️ SUPERSEDED (2026-09-07)
>
> This folder is the **June 2026 research corpus**, framed around an **India /
> ₹ / Vedic-adjacent** go-to-market. That strategy was **reversed** on
> 2026-09-07 in favour of an English-speaking-global / USD positioning.
>
> **Do not use this folder for current decisions.** The canonical research and
> strategy now live at:
> - `../../docs/market-research-2026-09.md` — sourced facts, confidence-flagged
> - `../../improvements_issues.md` — strategy, pricing, backlog
>
> Kept only as history: the competitor detail, financial-model scaffolding, and
> feature-demand analysis here may still be useful reference, but every
> India-market and pricing conclusion is stale.

**Date opened:** 2026-06-26
**Last updated:** 2026-06-26 (frozen — see the SUPERSEDED notice above)
**Project:** Korean Saju (사주) reading engine + tiered client report products + self-service calculator. See `README.md`, `CLAUDE.md`, `tasks.md` for project state.

This directory collects the market, competitor, audience, monetization, and feasibility research for turning the existing toolchain (engine + PDF toolchain + intake + self-service app) into a profitable consumer product.

## Documents in this folder

| File | Topic | Status |
|---|---|---|
| `01-executive-summary.md` | One-page go/no-go and headline numbers | ✅ |
| `02-market-size-and-demand.md` | Global astrology market, Korean Saju segment, India audience sizing, demand signals | ✅ |
| `03-competitor-landscape.md` | Direct competitors (Korean Saju apps), adjacent (BaZi, Vedic, Western astrology), Indian local players | ✅ |
| `04-feature-demand.md` | Most in-demand features, what users actually pay for, what they complain about | ✅ |
| `05-audience-demographics.md` | Age, gender, geography, income, psychographics for the paying user | ✅ |
| `06-monetization-strategy.md` | Tiered reports, subscription, ads, B2B, wholesale — modeled revenue scenarios | ✅ |
| `07-app-platform-decision.md` | Web app vs Android vs iOS vs hybrid — what fits this product best | ✅ |
| `08-marketing-strategy.md` | Acquisition channels, content strategy, SEO, partnerships, paid ads | ✅ |
| `09-product-roadmap.md` | What to build, what to optimize, what to enhance, what to skip | ✅ |
| `10-risks-and-do-not-do.md` | Risks, regulatory/ethical landmines, things explicitly not to do | ✅ |
| `11-financial-model.md` | Revenue model, unit economics, break-even, 12-month and 36-month P&L | ✅ |
| `12-feasibility-verdict.md` | Final go/no-go with reasoning and milestones | ✅ |

## Headline verdict (read this first)

**Verdict: Conditional GO.** The product has unusually strong fundamentals for a niche consumer app — calculation engine already built, classical-tradition credibility, tiered pricing validated by 6 paid pilots, and a self-service calculator that already produces PDFs. The realistic 12-month opportunity is **₹40–80 lakh revenue (₹4–8M / ~$48k–96k)** from a lean solo operator, scaling to **₹2–4 crore (₹20–40M)** in 24–36 months with a small team and content engine. The two dominant risks are **(a) over-reliance on AI-generated interpretive prose that the corpus says is [ENGINE DRAFT — REVIEW REQUIRED] for any paid tier above ₹499**, and **(b) regulatory/cultural risk around astrology claims in advertising**.

Read `12-feasibility-verdict.md` for the full reasoning.

---

## Sources & methodology

Numbers in these documents come from publicly available data as of 2026-06-26, including:

- Market.us, Grand View Research, IBISWorld, and IMARC Group reports on the global astrology / spiritual wellness market.
- Play Store, App Store, and similarweb public listings for app competitors.
- Public revenue / pricing disclosures from competitors where available (Co-Star, Sanctuary, The Pattern, Nebula, MyMu; Korean Saju apps: 사주닷컴, 운세다, 만세력달력, 신점 — most do not disclose revenue).
- Existing project artifacts: candidate reports under `candidates_horoscope/reports/`, the tiered pricing in `CLAUDE.md` (Spark ₹499 / Reading ₹1,499 / Full Map ₹3,499), the test suite (129 pytest cases), and the self-service calculator at `tools/client_intake_app.py`.
- Realistic, conservative estimates are used throughout. Where a number is a guess, it is flagged **[estimate]** and a range is given rather than a point.

This is **not** investment-grade due diligence. It is decision-support material for a solo founder / small team deciding how (or whether) to commercialize the project.