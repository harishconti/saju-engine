# Cosmic Saju — Improvements, Issues & Go-to-Market

> **What this is:** the single execution document for turning the Saju engine + landing page into a
> working micro-business, and the punch-list of defects blocking a paid launch.
>
> **Companion documents:**
> - `docs/market-research-2026-09.md` — the sourced fact base (every number, every URL, every caveat).
> - `docs/superpowers/specs/2026-09-07-saju-business-refinement-design.md` — the design spec this doc implements.
> - `research-engine/output/2026-09-07/report-saju.html` — the external deep-dive research report that triggered this work.
>
> **Last updated:** 2026-09-07

---

## 0. Executive reality check

**This is a side-income validation, not a startup.** With manual (AI-draft → human-polish)
fulfilment at 30–90 minutes per report, the hard revenue ceiling is **~$1–3K/month**. That is by
construction, not pessimism.

The market is real but **shallow**: 30% of US adults engage with astrology/tarot/fortune-telling
yearly, but only 1% "rely on it a lot" for decisions and 20% do it "just for fun" (Pew, May 2025).
That means high impulse-purchase potential at low prices, **low repeat rate, low lifetime value**,
and a buyer who will not tolerate a report that reads as machine-generated at a craft price.

The impulse price tier **is already occupied and automated**: Cheok Cheok (sajuplus.com) sells an
AI-instant personal reading for **$9.99** behind a 7-tool free funnel, and saju.com (5M Korean users)
launched an English version in March 2026. **Manual fulfilment cannot win on price or speed.**

### The one defensible wedge

Hand-crafted depth at the **mid price band ($19–69)** + **honest positioning** ("an accurate engine
and an honest interpreter — not a Korean master") + the **compatibility (궁합) product**, whose
structure (composite 0–100 score, 11 sub-systems, per-partner snapshots, year-by-year couple timing
overlay) has **no English-language equivalent**. Lead marketing with the compatibility product.

### Honest 12-month outcome distribution

Probabilities below are the author's estimate, **not sourced data**. Assumes consistent daily
short-form posting for the full period.

| Scenario | Likelihood | Monthly revenue |
|---|---|---|
| **Kill / skip** — no content format lands, < 5 sales in 90 days | most likely | $0–500 |
| **Marginal** — sells but stays hour-bound, no repeatable viral format | plausible | $500–1,500 |
| **Good case** — ≥ 1 repeatable format, the compatibility niche pulls | upside | $1,500–3,000 |
| **Break-out** — needs luck + a 3–6 month runway + relentlessness | tail | $3,000+ |

Content-format lock-in typically takes **3–6 weeks of daily posting minimum**, often longer.

### Fixed cost of the whole operation: **< $50/month**

Domain (~$12/yr) + free hosting (Cloudflare Pages) + email free tier (Resend 3K/mo) + marginal LLM
drafting. The real currency is founder hours.

---

## 1. Verified market facts (condensed)

Full detail and sources in `docs/market-research-2026-09.md`. Confidence: `[H]` corroborated /
primary · `[M]` single credible source · `[L]` single self-interested source or directional only.

| Fact | Value | Confidence |
|---|---|---|
| US adults engaging with astrology/tarot/fortune-telling yearly | 30% (but 1% "rely a lot", 20% "just for fun") | `[H]` |
| Hallyu fans worldwide (Dec 2023); fastest-growing region | 225M; the Americas (Mexico +~80% YoY) | `[H]` |
| KPop Demon Hunters Netflix views | ~210–266M+, most-watched film ever — but this is fandom, not proven purchase intent | `[H]` fact / `[M]` relevance |
| Korean fortune-telling market | ≈ ₩1.4T (~$988M), InnoForest 2024 — **not** the stale 2018 "$3.7B" figure | `[M]` |
| Global astrology-app market, 2026 | estimates span $1.3B–$16B — **unusable for planning** | `[L]` |
| Cheok Cheok / sajuplus.com pricing (direct-verified) | $9.99 personal / $8.99 compat / $7.99 year-ahead / $2.99 tarot; instant email; 7 free tools | `[H]` |
| saju.com English version | launched 30 Mar 2026; "traction" coverage is PR syndication only | `[M]` |
| Mid-band English competitors | Saju Atelier $39–69, Sajumuse $29, Fiverr masters $15–50, Etsy $19–70 | `[M]` |
| Landing-page conversion, cross-industry median | 4.0% (LanderLab) / 2.35% (WordStream) — **no niche data; plan 1–2% cold** | `[H]` |
| Starcrossed "$70K MRR in 90 days" | founder had 2 yrs / 163M views first; subscription app, not reports; founder-reported | `[L]` number / `[M]` pattern |
| Etsy metaphysical shop, median monthly income | < $100 | `[M]` |
| Astrology APIs | commoditised at $12–240/mo; RoxyAPI ships remote MCP | `[H]` |
| MCP servers; share that monetise | 12,000+; < 5%; "most make $0"; realistic yr-1 $500–5K/mo | `[H]` |
| AstroTalk (India) FY25 revenue; market share | ₹1,214 Cr (~$145M), +85% YoY; ~80%; IPO 2026–27; live-consultation model | `[H]` |
| Merchant-of-Record checkout from India | Lemon Squeezy / Paddle, ~5% + $0.50, handle global tax, region-priced variants | `[H]` |
| Craft time per report; capacity ceiling | 30–90 min; ~15–25 reports/wk → ~$1–3K/mo | `[M]` |

---

## 2. Corrections to the external research report

The deep-dive report's **GO verdict stands**, but five claims need tightening (detail in
`docs/market-research-2026-09.md` §8):

1. **Korean market "$1B+".** Correct at ~$1B (₩1.4T, InnoForest 2024). The larger "$3.7B / ₩4T"
   number circulating online is a **stale 2018 Economist figure**; the sector is now *shrinking*
   against AI apps. Never cite $3.7B.
2. **Starcrossed "$70K MRR in 90 days".** The founder spent **~2 years and 163M views** building the
   audience *before* the 90-day window — it was not a cold start. It is a **subscription app**, not a
   report business. The number is founder-reported. Use the *pattern* (organic short-form = the CAC-0
   channel), not the number, as a template.
3. **Conversion "2–4%".** That is the optimistic end of a **cross-industry** range. No
   astrology-specific benchmark exists. **Plan on 1–2%** for cold social traffic.
4. **saju.com "best-funded new entrant".** The English launch is real; all "traction" coverage is
   byte-identical press-release syndication across ~20 low-quality domains. Treat as "a funded
   competitor entered", not "is winning".
5. **Astrology-app / API market-size figures.** The report already downgraded the API market-size
   claim; extend that to *all* astrology-app market-size numbers — the 2026 range is $1.3B–$16B.
   Don't build projections on any of them.

---

## 3. Strategic position

### Target market

**English-speaking global** — US / Western K-culture fans, the Korean diaspora, and the "astrology
fatigue" crowd looking for a "higher-resolution" system.

**Persona:** women 20–40, K-culture-adjacent (K-pop / K-drama / curious about saju cafés), impulse
buyer at $10–40, primary concern **dating/relationships**, then **career & money timing**. Peak
consultation day is Sunday; seasonal spike December–February (New Year).

### Canonical positioning line (use verbatim everywhere)

> "The Saju engine Korean apps are built on — read in clear English by a human, with the classical
> texts cited. Not a Korean master; an accurate engine and an honest interpreter."

### Authenticity guardrails (non-negotiable)

- Never claim master credentials.
- Always cite the classical texts the knowledge base uses (적천수, 연해자평, 궁통보감, 명리정종, …).
- Always carry the disclaimer: *"for reflection and entertainment — not medical, legal, or financial
  advice."*
- The report's `Sources & Limits` / `[UNCERTAIN]` transparency is a **trust asset** — keep it, but
  polish the editor voice into client voice (see G5).

### India

Phase-2 experiment only. PPP discount codes surfaced **only** on regional-language content, capped at
~50%, never the public anchor. **Zero content effort in Phase 1.** Rationale: AstroTalk owns ~80% of
a Vedic-native, live-consultation market and is about to IPO.

---

## 4. Pricing — USD ladder

Grounded in the deep-dive report's §3.3 ladder and §4.4 catalogue, which its own quality audit
confirmed maps onto content that **already exists in the repo**.

| Engine tier | Product | Launch price | Range | Content basis |
|---|---|---|---|---|
| `sample` | **The Hook** (free) | $0 | — | 1 page: pillars + element balance + Day Master + lucky cues + upgrade CTA. Fully automatable. |
| `essential` | **Essential Natal** | **$9 intro → $19** | $9–19 | 9-section scaffold (~12 pp). **Only after G1–G2 fixed.** |
| `compat` basic | **Compatibility Snapshot** | **$24** | $19–29 | Composite 0–100 + 4-band verdict, 4 decisive sub-systems, red/yellow/green flags. |
| `deep` | **Deep Destiny Natal** | **$55** | $49–69 | Hand-crafted class: solar-time correction, ten-god deep analysis, 대운 decade table, 세운 annual windows, `Sources & Limits`, +1 follow-up question. 12–31 pp. |
| `compat` deep | **Deep Compatibility** — *hero; lead marketing here* | **$45** | $39–49 | All 11 sub-systems + school attribution, per-partner snapshots, 대운 synchrony, year-by-year couple timing overlay. No English competitor has this. |
| follow-up topic | **Topic Add-on** (career / relationships / health / finance / relocation / year-ahead) | **$19** | $15–25 | Existing per-candidate generators. À-la-carte + bundle component. |
| bundle | **Premium Bundle** | **$89** | $79–99 | Deep Natal + Deep Compatibility + 2 topic add-ons + combined branded PDF. Anchor product. |
| `companion` | **Cosmic Companion** (subscription) | **$9/mo or $79/yr** | — | Keep, but move **off** the primary pricing grid to a post-purchase upsell. Manual billing. |

Sell the **Year-Ahead** product hard December–February (documented +20% seasonal usage spike).

### Pricing risk

The current India prices (₹799 ≈ $9, ₹1,499 ≈ $17) already sit at the USD impulse floor. Moving
Essential to $19 and Deep to $55 is a **genuine price increase**, justified only by the higher
willingness-to-pay of the new market. Mitigation: intro pricing + A/B test on the first ~50 orders.
Do not treat the $19/$55 numbers as settled until validated.

---

## 5. Landing-page issues (`apps/landing-page`)

| ID | Issue | Severity | Status |
|---|---|---|---|
| **LP1** | ₹ pricing throughout (3 label maps + CTAs + engine text) | **P0** | ✅ done 2026-09-07 — USD ladder |
| **LP2** | India / matrimonial framing ("the boy and the girl", "Marriage Compatibility", NRI copy) | **P0** | ✅ done 2026-09-07 (internal `boy`/`girl` payload keys pending — R9) |
| **LP3** | Fabricated testimonials presented as real — FTC risk | **P0 (do not ship)** | ✅ hardened 2026-09-07 — `TESTIMONIALS_APPROVED = false` gate; real reviews + flag flip still required |
| **LP4** | WhatsApp placeholder number `+91-98765-43210` | **P1** | ⏳ comment added; real number + email-first flow still needed |
| **LP5** | No real checkout / payment path — nothing is charged | **P1** | ⏳ open — Merchant of Record (Lemon Squeezy / Paddle) |
| **LP6** | Comparison table India-tier framed | **P2** | ✅ 2026-09-07 (headers → USD/궁합); **folded into the redesign** — becomes `<CompareTiers>` styled grid |
| **LP7** | No 7-day guarantee shown | **P1** | ✅ done 2026-09-07 — FAQ + trust card + line under pricing + Hero/About chips |
| **LP8** | Proof (real reading) buried at section #10, below generic claims | **P1** | 🔄 **in the redesign** — `DemoReports` rebuilt with viz components and moved to section #4 |
| **LP9** | No quiz funnel | **P2** | ⏳ open |
| **LP10** | Free chart calculator not embedded/linked | **P2** | ⏳ open (free-sample flow already hits the FastAPI calculator via `/api/generate`) |
| **LP11** | Cosmic Companion in the primary pricing grid | **P2** | ✅ 2026-09-07 (3-col grid + strip below); revisited in the redesign's `<Pricing>` |
| **LP12** | `ABOUT_READER.bio` not honest positioning | **P1** | ✅ done 2026-09-07 |
| **LP13** | Whole page was monotonous / redundant / CTA-sprawl / no Saju visual language | **P1** | ✅ done 2026-09-07 — see §5a |

### 5a. Landing Page Redesign (approved 2026-09-07)

> **Design spec:** `docs/superpowers/specs/2026-09-07-landing-page-redesign-design.md`
> **Implementation plan:** `docs/superpowers/plans/2026-09-07-landing-page-redesign.md`

**Direction (user-approved):** full restructure + a reusable Saju visual system; **premium-editorial**
aesthetic (dark cosmic + gold + serif, but diagrams/data over ornament — mysticism as accent); build
theme-aware SVG components; keep the RM/couple demo but restyle and move it up.

**Status: shipped 2026-09-07.** What changed:
1. **~15 sections → ~9** with a proof-first arc: Hero → *Why it's different* → **See a real reading**
   (moved up) → *What's inside* → Pricing → *How it's built* → The reader → FAQ → one Final CTA.
2. **New visual system** `src/components/viz/`: `<FourPillarsChart>`, `<ElementBalance>` (bars + wheel),
   `<LuckTimeline>`, `<DayMasterBadge>`, `<SectionHeading>` (eyebrow labels), `<ElementalRule>`,
   `<KoreanWatermark>` — fed by `src/data/demo-chart.ts` (RM's real numbers).
3. **Elemental palette tokens** in `globals.css` (`--el-wood/fire/earth/metal/water`, `--lean-*`),
   an elemental gradient rule motif, `四柱` watermark, staggered scroll-reveal, one hero "chart draws
   itself" animation (all `prefers-reduced-motion`-safe).
4. **Deleted sections:** `WhatIsSaju`, `WhatYouReceive`, `TrustClarity`, `ImportantDetails`,
   `ComparisonTable` (content merged into `WhySaju` / `WhatsInside` / `Pricing` / `HowItsBuilt`).
5. **CTA system:** one canonical primary label ("Get your free chart snapshot"), 2 button styles + 1
   text link; `FinalCTA` drops its 5 tier buttons.
6. **Not touched:** intake form contract, API routes, checkout, `Testimonials` gate, security/proxy.

**Acceptance:** `npm run build` + `lint` + `test` green (update the few tests asserting deleted copy);
screenshot pass desktop+mobile / light+dark for every section; 0 hydration warnings;
`prefers-reduced-motion` clean; Lighthouse ≥ pre-redesign; no horizontal body scroll.

---

## 6. Product / report issues

From the deep-dive report's §3.8 quality audit, cross-checked against the code.

| ID | Defect | Where | Why it matters | Severity |
|---|---|---|---|---|
| **G1** | Internal QA review-notes leak into client PDFs: *"Chart-derived first draft — verify against the relevant knowledge files before client delivery"*, *"Engine note: Heuristic only …"*, and a mangled *"…refine each entry by reading the relevant  and ."* (paths stripped, leaving dangling "and .") | `src/saju_engine/premium_report.py:294,341,454`; the strip logic in `src/saju_html/__init__.py` (`_SOURCE_PATH_RE` etc.) does not remove the whole note line | Pipeline notes visible to a paying client destroy the premium positioning instantly — the audited leaking report was priced ₹799 | **P0** |
| **G2** | Per-pillar template: `.{tengod_phrase}. ` renders as *"**…energy**. sits as **Direct Wealth**."* — no sentence subject; plus a structurally identical filler sentence for all 4 pillars | `src/saju_engine/premium_report.py::_four_pillars_one_by_one` (~358–363) | A client comparing pillars sees the template — reads as machine-generated at exactly the price point where craft is claimed | **P0** |
| **G3** | 용신 (favorable element) **disagrees across products for the same person**: natal report derives it one way (`report_data.py` element-priority logic), the compat report reads the raw strength heuristic (`compat_report.py:75` → `strength.assess()['candidate_favorable']`, `strength.py:205`). Audit found natal "Earth" vs compat "Metal" for one client | cross-product | 용신 is the single most-repeated claim in every report; if a client buys both products and the favorable elements disagree, the trust story collapses | **P0** |
| **G4** | Two prose classes coexist: knowledge-file-crafted readings (Sruthi/Harish class) read like craft; `premium_report.py` scaffold readings read like fill-in-the-blank | `premium_report.py`, `prose_fillers.py` | Same engine, wildly different perceived value. Decide: Essential stays scaffolded at $9–19, or gets a "knowledge-file pass" to justify $19–29 | **P2** (backlog) |
| **G5** | `[UNCERTAIN]` / `Sources & Limits` transparency is a trust asset, but raw editor phrasing ("folk 점술 sites inflate this") needs client-voice polish | `knowledge/`, report templates | Undermines the professionalism the transparency is meant to convey | **P2** |
| **G6** | ₹ appears in engine-emitted report text and CLI defaults | `premium_report.py`, `cli.py` defaults, `docs/` | Currency mismatch with the target market | **P0** (folded into the pricing rewrite) |

**Fixed in the 2026-09-07 change:** G1, G2, G3, G6. **Backlogged:** G4, G5.

---

## 7. Engine / architecture issues

| ID | Issue | File(s) | Severity |
|---|---|---|---|
| **A1** | No single source of truth for 용신 + no provenance metadata + no cross-product consistency test (= the G3 fix) | new `src/saju_engine/yongsin.py`; `premium_report.py`; `compat_report.py` | **P0** |
| **A2** | Self-service calculator: intake records stored as **unencrypted local JSON**; PDF generation is **synchronous in the HTTP worker**; no task queue; no auth | `tools/client_intake_app.py` | **P1** (before any public deploy) |
| **A3** | No payment-gateway integration for paid tiers or the Companion subscription | landing page + intake apps | **P1** |
| **A4** | Landing page (Next.js) and FastAPI calculator are not deployed or production-hardened | `apps/landing-page`, `tools/client_intake_app.py` | **P1** |
| **A5** | Nayin 30×30 pair table still populated from the 5-element fallback, not a published source | `src/saju_engine/nayin.py` | **P3** |
| **A6** | The `/saju` slash command does not auto-calculate pillars from a date; the engine is not wired into it | `.claude/commands/saju.md` | **P3** (deliberate — documented in README Limitations) |

---

## 8. Marketing plan

**Funnel:** short-form video → link-in-bio landing page → **free chart calculator + saju quiz**
(email capture) → **$9 Essential** → follow-up / compatibility / deep upsells. Every touchpoint
drives to the **owned email list** — the hedge against Etsy deactivation and algorithm changes.

**Platforms:** one TikTok + one Instagram (crosspost Reels). Pinterest later for evergreen search;
YouTube Shorts optional. **One account each — focus beats spread.**

**Account identity:** founder-led. *"I built a Saju engine and I read charts with it."* Builder +
interpreter is a distinctive crossover in a niche full of "master" personas — and it is the honest
positioning.

**Content pillars (rotate 5):**
1. **Per-pillar hooks** — "what your Day Master says about how you fight."
2. **Psychological call-outs** — "the toxic partner your chart craves."
3. **K-pop idol saju breakdowns** — a proven viral genre in Korea, **near-unoccupied in English**.
   Rides the Demon Hunters wave; converts the target persona directly. Always respectful + disclaimer.
4. **Event timing** — saju year-pillar transitions as the "retrograde" analog; K-occult trend tie-ins.
5. **Reading reveals** — blurred report page → dramatic reveal → sample-PDF link.

**Cadence:** 1–4 posts/day. Expect ~40–80K average IG views and ~200–400K TikTok *once a format
locks in* (3–6 weeks of daily posting minimum). Weekly review; kill formats below threshold; double
down on the one that repeats 100K+.

**Validation channels:** Etsy listing (zero-CAC demand test — always drive to email), Reddit
(r/bazi and similar) value-only posts, never hard-sell.

**Trust stack from day 1:** 7-day guarantee, sample report sections on the page, named human-QA line,
disclaimers.

**Budget discipline (< $500):** $0 on ads in Phase 1. Phase 2: $5–15/day Meta/TikTok tests
**reposting only proven organic winners** (documented pattern: ads work with proven creative, fail
cold).

---

## 9. Execution plan

| Phase | Window | Actions | Gate |
|---|---|---|---|
| **0 — Setup** | Wk 0–2 | Fix G1–G3, G6. Landing page → USD + honest positioning + sample sections + disclaimers + working MoR checkout (LP5). Free calculator + quiz (LP9, LP10). Etsy listing. Email capture from day 1. | All live; checkout works. |
| **1 — Organic validation** | Wk 2–12 | 1–4 posts/day, one TikTok + one IG. Fulfilment = engine draft → human polish, ≤ 45 min/report. Collect reviews via discounted early orders. Reddit value posts. | **GO/SCALE:** ≥ 25–50 sales, ≥ 3% site conversion, ≥ 1 format repeatably 100K+ views, refunds < 10%, fulfilment ≤ 45 min. **KILL:** < 5 sales after 90 days of consistent effort, or < 1% conversion on ≥ 5K targeted visits. **PIVOT:** sales only for compatibility → narrow the whole brand to compatibility. |
| **2 — Double down** | Mo 3–6 | Scale the winning format. Ship the Year-Ahead product for the Dec–Feb push. $5–15/day ads on proven creative. Upsell stacks (follow-up questions). | First $1–3K revenue month; known blended CAC. |
| **3 — API/MCP (conditional)** | Mo 6+ | Only if §10 revisit trigger is met. Freemium MCP in front of a paid English-saju-narrative API; list on MCPize/Apify; approach white-label B2B (matrimony/dating/wellness apps). | First 10 paying API users → invest-or-park decision. |

---

## 10. API / MCP — parked

**Do not build this now.** The generic astrology-API market is commoditised ($12–240/mo, 166–516
endpoints, RoxyAPI already ships remote MCP). MCP monetisation is early: < 5% of 12,000+ servers
monetise, "most make $0", realistic year-1 revenue $500–5K/mo.

The **only** differentiated angle is the English-language narrative/interpretation layer, and it is
only worth packaging once B2C has proven that asset has real usage.

**Revisit trigger — all three must be true:**
1. B2C has ≥ 200 paid orders, AND
2. ≥ 1 free tool (calculator / quiz / mini-reading) has ≥ 1,000 weekly active users, AND
3. There is unsolicited inbound B2B interest.

Until then: parked.

---

## 11. Open risks & unknowns

- **R1.** The outcome-distribution probabilities in §0 are judgement, not data.
- **R2.** The ₹→$19/$55 price increase may depress conversion. Not resolved — needs A/B + intro pricing.
- **R3.** Some already-generated candidate reports were produced with the old (inconsistent) 용신
  value. Only the RM demo report is regenerated in the 2026-09-07 change; others are noted as stale.
- **R4.** Organic short-form is a **skill and a grind**, not a plumbing task. If the founder will not
  post daily for 3+ months, the whole plan fails at Phase 1 — be honest about this before starting.
- **R5.** Legal: unregulated category; the disclaimer is standard practice, but refund disputes are
  the real operational risk — a clear 7-day guarantee reduces them.
- **R6.** Platform risk: Etsy deactivates metaphysical listings; TikTok/IG algorithm dependence.
  Mitigation: own the email list from day 1.
- **R7.** Competitive timing: saju.com and Cheok Cheok are funded/automated. Do not try to out-volume
  them — differentiate on depth and the compatibility structure.
- **R8.** `misc/market_research/` (six files) is the **old India-market research corpus** and now
  contradicts this strategy. It is retained as history; `docs/market-research-2026-09.md` is the
  canonical research going forward. Don't cite `misc/market_research/` for current decisions.
- **R9.** The compat intake still uses internal `boy` / `girl` payload keys and `compatBoy` /
  `compatGirl` identifiers (not user-visible; visible strings are fixed). Renaming the API contract
  to `partnerA` / `partnerB` is a follow-up (touches forms, `submit-handlers`, `/api/submit`,
  `/api/generate`, and `api.test.ts`).

---

## 12. Prioritised backlog

### P0 — blocks the first paid sale

| Item | Where | Effort | Status |
|---|---|---|---|
| G1 — scrub reviewer-notes from client output | `premium_report.py`, `saju_html/__init__.py` | ~2h | done 2026-09-07 |
| G2 — fix per-pillar template grammar + filler | `premium_report.py` | ~1h | done 2026-09-07 |
| G3 / A1 — 용신 single source of truth + provenance + regression test | new `yongsin.py`, `premium_report.py`, `compat_report.py` | ~4h | done 2026-09-07 |
| G6 / LP1 — ₹ → USD everywhere (3 landing label maps + engine text + docs) | landing page, `premium_report.py`, all `.md` | ~3h | done 2026-09-07 (docs + landing) |
| LP2 — remove India/matrimonial framing | landing sections | ~2h | done 2026-09-07 |
| LP3 — testimonials now a **safe default**: `TESTIMONIALS_APPROVED = false` → `<Testimonials>` renders nothing; must add real reviews AND flip the flag before showing any | `landing-data.ts`, `Testimonials.tsx` | done 2026-09-07 (hardened; real reviews still needed) |

### P1 — needed to actually operate

| Item | Where | Effort | Status |
|---|---|---|---|
| LP5 / A3 — Merchant-of-Record checkout (Lemon Squeezy or Paddle) | landing page + intake | ~1–2 days | open |
| LP4 — real WhatsApp number; email-first delivery flow | landing page + fulfilment | ~2h | comment added; number still needed |
| LP7 — 7-day guarantee on page + FAQ | landing page | ~1h | done 2026-09-07 (FAQ + trust card + guarantee line under pricing + Hero/About chips) |
| LP8 — proof buried; move + rebuild the demo | landing page | — | 🔄 in the redesign (`DemoReports` → viz card, section #4) |
| **LP13 — full landing-page redesign** (restructure + Saju visual system; §5a) | `apps/landing-page/` | ~1.5 days | ✅ done 2026-09-07 — spec + plan in `docs/superpowers/`; build/lint/133 vitest green; screenshot pass |
| LP12 — `ABOUT_READER` honest positioning | landing page | 30m | done 2026-09-07 |
| A2 — self-service app: encrypt PII, background queue, auth | `tools/client_intake_app.py` | ~1 day | open (limitation is documented in the module docstring) |
| A4 — deploy + harden landing page & calculator | infra | ~1 day | open |
| SEO — `locale` was `en_IN`; metadata/OG/JSON-LD said "marriage compatibility" | `layout.tsx` | 30m | done 2026-09-07 (`en_US`, 궁합/Four-Pillars framing, K-pop keyword) |

### P2 — growth mechanics

| Item | Where | Effort | Status |
|---|---|---|---|
| LP9 — saju quiz funnel | new | ~2 days | open |
| LP10 — embed free four-pillar calculator | landing page + FastAPI | ~1 day | open (free-sample flow already hits the FastAPI calculator via `/api/generate`) |
| LP6 — comparison table re-label | landing page | ~1h | done 2026-09-07; **rebuilt as `<CompareTiers>` styled grid in the redesign** |
| LP11 — move Companion off the primary grid | landing page | ~1h | done 2026-09-07; revisited in the redesign's `<Pricing>` |
| G5 — client-voice polish of `[UNCERTAIN]` / editor phrasing | `compat.py`, `knowledge/` | ~1 day | partial — fixed the "folk 점술 sites inflate this" line in `compat.py`; `knowledge/` `[UNCERTAIN]` tags are fine (stripped from PDFs) |
| G4 — decide + apply a "knowledge-file pass" for Essential prose | `premium_report.py` | ~1–2 days | open |
| Year-Ahead product for the Dec–Feb push | engine + landing | ~2 days | open |

### P3 — later / optional

| Item | Where |
|---|---|
| A5 — populate the Nayin 30×30 table from a published source | `nayin.py` |
| A6 — wire the engine into the `/saju` slash command | `.claude/commands/saju.md` |
| PPP / geo-priced variants for a Phase-2 India experiment | MoR config |
| API / MCP packaging (only if §10 trigger met) | new |
