# Saju Report Business — Refinement & Go-to-Market Design Spec

**Date:** 2026-09-07
**Status:** IMPLEMENTED (2026-09-07) — see `docs/superpowers/plans/2026-09-07-saju-business-refinement.md` and `improvements_issues.md`
**Owner:** Harish NG (solo founder)

## Implementation notes (2026-09-07)

- **Q1 resolved:** G1–G3/G6 rows added to `docs/issues_bugs.md` under a new "Reopened / New — 2026-09-07" heading (all FIXED), pointing at `improvements_issues.md`.
- **Q2 resolved:** landing-page prices are bare `"$19"` strings; no currency helper (Phase-2 PPP work).
- **G3 finding:** the two engine generators were *already* internally consistent (both read `candidate_favorable`). The real gap was (a) no shared API / provenance and (b) reader-argued classical 용신 not flowing to both products. Fix delivers a single `favorable_element()` resolver + `FavorableElement` provenance + `favorable_override` / `favorable_element_a`/`_b`, plus a regression guard. The compat "Engine note:" leak (really G1) is fixed in the same change.
- **Scope added beyond the spec:** the `pawan_sruthi` compatibility demo `.md`/`.pdf` and the landing `public/demo-compat-*.pdf` were regenerated (with `favorable_override` = the hand-crafted 용신) so they are leak-free and consistent; the `.claude/commands/saju.md` and `saju-client.md` slash-command pricing was updated to USD (found in the final sweep).
- **Not done (unchanged from Non-goals):** MoR checkout, API/MCP, PPP infra, real testimonials, deployment, the `boy`/`girl` internal payload-key rename.
- **Tests:** 568 → 590 pytest; landing `npm run build` clean + 107 vitest pass.
- **Git:** repo root is not a git repo (no commit). `apps/landing-page` has a large pre-existing uncommitted staged changeset from earlier work — this session's landing edits were made on top and left uncommitted for the user to review/separate.

## Source inputs

1. **Research report:** `/mnt/data2/git_repos/research-engine/output/2026-09-07/report-saju.html`
   ("Selling Saju Reports Online — Deep Validation & Growth Strategy", run_id `20260907T070820Z-182b647b`, v2 with §3.8 report-quality audit).
2. **This repo:** `src/saju_engine/`, `src/saju_html/`, `apps/landing-page/`, `candidates_horoscope/`, all root and `docs/` markdown.
3. **Independent web research** run 2026-09-07 (15 searches / fetches), summarized in §3 and to be written in full to `docs/market-research-2026-09.md`.

## User-approved scope decisions (2026-09-07)

| Question | Decision |
|---|---|
| Target market / currency | **Adopt the pivot** — English-speaking global, USD primary. India → Phase-2 PPP experiment only. |
| Deliverable depth | **Docs + fix the 3 launch blockers + landing-page copy/pricing.** |
| Research | **Run fresh web research; verify and extend the report's numbers; flag what cannot be verified.** |
| Doc edit aggressiveness | **New file + full rewrite of strategy sections** across the other `.md` files. |
| Fabricated testimonials | **Leave the code for now; flag in docs** as a pre-launch blocker (FTC endorsement risk). |
| Process | **Full spec + implementation plan before executing.** |

---

## 1. Context & Problem

The repo contains a mature Korean Saju calculation engine (568 passing tests), a PDF toolchain, a
tiered report generator, a compatibility engine, a Next.js landing page, and intake tooling. Every
client-facing artifact is framed for an **India / ₹ / Vedic-adjacent NRI** audience.

The research report concludes that framing is wrong: the winnable market is **English-speaking
global** (US/West K-culture fans, diaspora), priced in **USD**, and India is "LATER / SKIP" because it
is a Vedic-native, live-consultation market ~80%-dominated by AstroTalk (verified: FY25 revenue
₹1,214 Cr ≈ US$145M, +85% YoY, ~$1B valuation, IPO 2026–27).

The report also found **three client-facing defects** in the engine's generated reports that would
undermine a paid launch, plus a set of polish issues and a two-class prose-quality problem.

**Problem statement:** align the repo's product, pricing, positioning, documentation, and the three
engine defects with a defensible USD/global go-to-market — and record the analysis, with honest
numbers, in a way that is auditable and does not oversell the opportunity.

## 2. Goals / Non-goals

### Goals

- G-1. A single master document (`improvements_issues.md`) that a solo founder can execute against.
- G-2. A sourced, caveated market-research writeup (`docs/market-research-2026-09.md`).
- G-3. Strategy/pricing/market sections of all other `.md` files rewritten to the USD/global strategy,
  with existing structure preserved.
- G-4. The three launch blockers (G1–G3 in the report's §3.8) fixed, with regression tests, full
  pytest suite still green.
- G-5. `apps/landing-page` pricing data and positioning copy updated to USD/global; fabricated
  testimonials flagged (not removed) with a pre-launch TODO.
- G-6. No claim in any deliverable that exceeds what a cited source or the repo supports. Every
  market number carries a confidence flag.

### Non-goals

- N-1. Wiring a real payment gateway / checkout (documented as P1, not built here).
- N-2. Building the API/MCP product (documented as a parked Phase-3 bet with a revisit trigger).
- N-3. Rewriting the engine's interpretive prose quality (the "two prose classes" G4 issue) — it is
  documented and backlogged, not fixed here.
- N-4. Deploying the landing page or the FastAPI calculator.
- N-5. Building PPP/geo-pricing infrastructure (documented as Phase-2, cheap-discrimination approach).
- N-6. Any India-market content or funnel work.
- N-7. Creating or sourcing real testimonials.

## 3. Market reality — verified findings (condensed)

Full writeup with every URL → `docs/market-research-2026-09.md`. Confidence: **[H]** high (primary
source or multi-source), **[M]** medium (single credible source), **[L]** low / directional only.

### 3.1 Demand is real but shallow-engagement

- **[H]** 30% of US adults consult astrology/tarot/fortune-tellers at least yearly (Pew, fielded
  Oct 2024, released May 2025, n=9,593). **But**: 20% "just for fun", 10% for "helpful insight",
  **1% rely on it "a lot"** for real decisions. This is a low-intent, low-repeat, low-LTV audience.
- **[H]** 225M Hallyu fans worldwide (Dec 2023, Korea Foundation, 119 countries); Americas is the
  fastest-growing region (Mexico +~80% YoY).
- **[H]** K-occult pop-culture wave is real: *KPop Demon Hunters* (Netflix, ~210–266M views,
  most-watched film ever), Disney+ *Battle of Fates*, K-shaman fan-meets selling out in Thailand.
  **Caveat:** this is aesthetic/soundtrack-driven fandom, not demonstrated purchase intent for paid
  saju reports.

### 3.2 Market-size numbers — mostly unusable for planning

- **[M]** Korean fortune-telling market ≈ **₩1.4T (~US$988M)**, InnoForest 2024. The "$3.7B / ₩4T"
  figure circulating online is from a **2018 Economist** article — stale; Korean traditional
  fortune-tellers are now *losing* revenue to AI (Taipei Times, Aug 2026).
- **[L]** Global astrology-app market estimates for 2026 span **$1.3B–$16B** across research firms;
  CAGR 8–25%. **Do not build any projection on these.** Mid-estimate: Research & Markets $4.7B
  (2025) → $5.7B (2026).
- **[L]** "US online astrology $1.37B → $2.77B by 2031" (Ken Research) — single-source, kept as
  directional only.

### 3.3 Competition occupies every price rung; two are funded/automated

- **[H]** Cheok Cheok / sajuplus.com (direct-verified): **$9.99** personal, **$8.99** compatibility,
  **$7.99** year-ahead, **$2.99** tarot; 7 free tools; instant email delivery; PayPal. AI-generated.
  This is the automated price floor.
- **[H]** saju.com launched an English version **30 Mar 2026** (5M Korean users). Best-funded new
  entrant. **Caveat:** all "traction" coverage is identical press-release syndication across ~20
  spam-network domains — the launch is real, overseas traction is unproven.
- **[M]** Mid band: Sajumuse ~$29 (100+ pp), Saju Atelier $39–69 (named master, calligraphy),
  K-Saju $10.99. Premium hand-written band $75–150 still sells (Tinhan, Lumen Tao, etc.).
- **[M]** Fiverr Korean-saju gigs ($15 basic → premium multi-person); sellers explicitly cite
  *Demon Hunters* as a demand driver. Real but small-volume.
- **The only defensible gap:** hand-crafted depth at the **mid band ($19–69)** + honest
  "engine + human, not a Korean master" positioning + the **compatibility product**, whose
  structure (composite score, 11 sub-systems, per-partner snapshots, couple timing overlay) has
  **no English-language equivalent**.

### 3.4 Channel: organic short-form is the only proven CAC≈0 path

- **[M]** Starcrossed reached "$70K MRR in 90 days" via founder TikTok. **Heavy caveats:** the
  founder had **2 years + 163M views** of audience-building *before* those 90 days; the product is
  an **AI soulmate-drawing subscription app**, not a report business; the number is founder-reported
  via secondary blogs. Treat as directional, not a template.
- **[M]** The *pattern* — organic short-form video is this niche's lowest-CAC acquisition, and it
  works content-first not ad-first — is independently corroborated (Forbes "Moonlight & Sage",
  Seoulz, multiple growth writeups).
- **[H]** Landing-page conversion: cross-industry median **4.0%** (2026) / **2.35%** (WordStream).
  No astrology-specific benchmark exists. **Plan on 1–2% for cold social traffic.**
- **[M]** Etsy metaphysical shops: median earns **< $100/mo**; income scales with hours not sales;
  Etsy periodically deactivates metaphysical listings. Use as a zero-CAC validation channel only,
  always driving to an owned email list.

### 3.5 API/MCP — a parked bet, not a plan

- **[H]** Astrology APIs are commoditized: Vedika $12–240/mo (166+ endpoints), RoxyAPI $39/mo (now
  ships remote MCP), AstrologyAPI stackable to ~$95/mo.
- **[H]** MCP monetization: **12,000+ servers, <5% monetize, "most make $0"**; realistic first-year
  $500–5,000/mo; 21st.dev hit $10K MRR in 6 weeks. Winning pattern: free MCP in front of a paid API.
- **Verdict:** only sensible *after* B2C proves the English-saju-narrative asset has weekly active
  users. Revisit trigger defined in §4.3.

### 3.6 Operational reality

- **[M]** Manual craft time 30–90 min/report → ~15–25 reports/week ceiling → **~$1–3K/mo revenue
  ceiling** at a ~$20–30 blended AOV. This is a side-income validation, not a scalable startup, by
  construction.
- **[H]** Merchant-of-Record checkout (Lemon Squeezy — Stripe-owned since 2024 — or Paddle,
  ~5% + $0.50) works from India, handles global sales tax/VAT, supports region-priced variants.
- Fixed monthly cost of the whole operation: **< $50/mo** (domain + free hosting + email free tier).
  The real currency is founder hours.

### 3.7 Honest outcome distribution (12 months, consistent daily posting)

| Scenario | Probability (author estimate, not sourced) | Monthly revenue |
|---|---|---|
| Kill / skip — no format hits, < 5 sales | most likely | $0–500 |
| Marginal — sells but hour-bound, no viral format | plausible | $500–1,500 |
| Good case — ≥ 1 repeatable format, compat niche pulls | upside | $1,500–3,000 |
| Break-out — requires luck + 3–6 mo runway + relentlessness | tail | $3,000+ |

Format lock-in typically takes **3–6 weeks of daily posting minimum**; often longer.

## 4. Strategic decisions

### 4.1 Target market & positioning

- **Primary market:** English-speaking global. Persona: women 20–40, K-culture-adjacent (K-pop /
  K-drama / curious about saju cafés), impulse buyer at $10–40, primary concern dating/relationships
  then career & money timing. Seasonal spike Dec–Feb.
- **Positioning line (canonical, to appear verbatim across docs + landing page):**
  > "The Saju engine Korean apps are built on — read in clear English by a human, with the classical
  > texts cited. Not a Korean master; an accurate engine and an honest interpreter."
- **Do not** compete with Cheok Cheok on price or speed. Compete on depth, specificity, honesty, and
  the compatibility structure.
- **Authenticity guardrail:** never claim master credentials; always cite the classical texts the
  engine's knowledge base uses; always carry the "for reflection / entertainment — not medical,
  legal, or financial advice" disclaimer.

### 4.2 Pricing ladder (USD) — grounded in audited engine output

Reconciled from the report's §3.3 ladder and §4.4 catalog (which the audit confirmed maps onto
content that already exists in the repo).

| Engine tier | Product name | Launch price | Range | Content basis (verified in repo) |
|---|---|---|---|---|
| `sample` | **The Hook** (free) | $0 | — | 1-page: pillars + element balance + Day Master + lucky cues + upgrade CTA. Fully automatable. |
| `essential` | **Essential Natal** | **$9 intro → $19** | $9–19 | 9-section premium scaffold (~12 pp). **Only after G1–G2 fixed.** |
| `compat` basic | **Compatibility Snapshot** | **$24** | $19–29 | Composite 0–100 + 4-band verdict, 4 decisive sub-systems, R/Y/G flags, condensed guidance. |
| `deep` | **Deep Destiny Natal** | **$55** | $49–69 | Hand-crafted class: solar-time correction, ten-god deep analysis, 대운 decade table, 세운 annual windows, Sources & Limits, +1 follow-up question. 12–31 pp. |
| `compat` deep | **Deep Compatibility** *(hero — lead marketing here)* | **$45** | $39–49 | All 11 sub-systems + school attribution, per-partner element/Day-Master/용신 snapshots, 대운 synchrony, year-by-year couple timing overlay. No English competitor has this. |
| follow-up topic | **Topic Add-on** (career / relationships / health / finance / relocation / year-ahead) | **$19** | $15–25 | Existing per-candidate generators. À-la-carte upsell + bundle component. |
| bundle | **Premium Bundle** | **$89** | $79–99 | Deep Natal + Deep Compatibility + 2 topic add-ons + combined branded PDF. Anchor product. |
| `companion` | **Cosmic Companion** (subscription) | **$9/mo or $79/yr** | — | Keep, but move OFF the primary pricing grid to a post-purchase upsell. Manual billing. |

**Year-ahead** report: sell hard Dec–Feb (documented +20% seasonal usage spike).

**Pricing risk to record:** current India prices (₹799 ≈ $9, ₹1,499 ≈ $17) already sit at the USD
impulse floor. Moving Essential to $19 and Deep to $55 is a genuine price increase justified only by
the higher willingness-to-pay of the new market — recommend intro pricing + A/B on the first ~50
orders.

### 4.3 What we are explicitly NOT doing

- **Not** India-primary. India = a Phase-2 experiment: PPP discount codes surfaced only on
  regional-language content, capped at ~50%, never the public anchor. No content effort in Phase 1.
- **Not** building API/MCP now. **Revisit trigger:** B2C has ≥ 200 paid orders AND ≥ 1 free tool
  with ≥ 1,000 weekly active users AND inbound B2B interest. Until all three, it stays parked.
- **Not** running paid ads in Phase 1. Phase 2: $5–15/day, reposting *only* proven organic winners.
- **Not** promising scale. The docs must state the ~$1–3K/mo ceiling plainly.

### 4.4 Marketing plan (summary; full version in `improvements_issues.md`)

- **Funnel:** short-form video → link-in-bio → free chart calculator + saju quiz (email capture) →
  $9 Essential → follow-up / compat / deep upsells. Every touchpoint drives to the owned email list.
- **Platforms:** one TikTok + one Instagram (Reels crosspost). Founder-led: "I built a Saju engine
  and I read charts with it." Pinterest later; YouTube Shorts optional.
- **Content pillars (rotate 5):** (1) per-pillar hooks; (2) psychological call-outs; (3) **K-pop idol
  saju breakdowns** — proven viral genre in Korea, near-unoccupied in English; (4) event timing
  (year-pillar transitions, K-occult trend tie-ins); (5) reading reveals (blurred page → reveal →
  sample-PDF link).
- **Validation channels:** Etsy listing (zero-CAC demand test), Reddit value-only posts.
- **Trust stack from day 1:** 7-day guarantee, sample report sections on the landing page, named
  human-QA line, disclaimers.

### 4.5 Execution phases (with honest kill criteria)

| Phase | Window | Actions | Gate |
|---|---|---|---|
| **0 — Setup** | Wk 0–2 | Fix G1–G3. Landing page → USD + new positioning + samples + disclaimers + working MoR checkout. Free calculator + quiz. Etsy listing. Email capture. | All live; checkout works. |
| **1 — Organic validation** | Wk 2–12 | 1–4 posts/day, one TikTok + one IG. Fulfilment = engine draft → human polish, ≤ 45 min/report. Collect reviews via discounted early orders. | **GO/SCALE:** ≥ 25–50 sales, ≥ 3% site conversion, ≥ 1 format repeatably 100K+ views, refunds < 10%. **KILL:** < 5 sales after 90 days of consistent effort, or < 1% conversion on ≥ 5K targeted visits. **PIVOT:** sales only for compat → narrow the whole brand to compatibility. |
| **2 — Double down** | Mo 3–6 | Scale the winning format. Year-ahead product for Dec–Feb. $5–15/day ads on proven creative. Upsell stacks. | First $1–3K revenue month; known blended CAC. |
| **3 — API/MCP (conditional)** | Mo 6+ | Only if §4.3 revisit trigger met. Freemium MCP in front of a paid English-saju-narrative API; list on MCPize/Apify; white-label B2B. | First 10 paying API users → invest-or-park decision. |

---

## 5. Deliverables

| # | Path | Type | Status target |
|---|---|---|---|
| D1 | `improvements_issues.md` (repo root) | new | complete |
| D2 | `docs/market-research-2026-09.md` | new | complete |
| D3 | `CLAUDE.md` | rewrite: "Tiered Client Products", add positioning + market note | edited |
| D4 | `README.md` | rewrite: "Client products" table + project framing paragraph | edited |
| D5 | `docs/MEMORY.md` | rewrite: "Current State", product table, add strategy pointer | edited |
| D6 | `tasks.md` | add "Priority B — Business / GTM" section pointing at D1; status line update | edited |
| D7 | `candidates_horoscope/README.md` | pricing references → USD | edited |
| D8 | `docs/openwiki/products/reports.md` | tier table → USD + positioning | edited |
| D9 | `apps/landing-page/worklog.md` | append a "Strategy shift 2026-09-07" entry | edited |
| D10 | `src/saju_engine/premium_report.py` + tests | G1 + G2 fixes | edited + tests green |
| D11 | `src/saju_engine/strength.py` (or new `yongsin.py`) + `premium_report.py` + `compat_report.py` + tests | G3: 용신 single source of truth + provenance + cross-product consistency test | edited + tests green |
| D12 | `src/saju_html/__init__.py` and/or `premium_report.py` + tests | G1: ensure review-note blockquotes never reach client output | edited + tests green |
| D13 | `apps/landing-page/src/data/landing-data.ts` + affected section components | USD pricing, positioning copy, comparison table, FAQ; testimonials left but flagged | edited; `npm run build` + `npm test` green |

---

## 6. Detailed change specs

### 6.1 `improvements_issues.md` — structure

```
# Cosmic Saju — Improvements, Issues & Go-to-Market
> Master execution doc. Companion research: docs/market-research-2026-09.md. Spec: docs/superpowers/specs/2026-09-07-...

## 0. Executive reality check
   - one-paragraph honest frame (side-income validation, $1–3K/mo ceiling, low-LTV market)
   - the §3.7 outcome-distribution table
   - the one defensible wedge

## 1. Verified market facts   (condensed §3 table with [H]/[M]/[L] flags + inline source refs)

## 2. Corrections to the research report
   - stale $3.7B market size
   - Starcrossed context (2yr runway, subscription app, secondary sourcing)
   - conversion is cross-industry not niche; plan 1–2%
   - saju.com "traction" is PR syndication
   - astrology-app market-size figures unusable

## 3. Strategic position
   - target market + persona
   - canonical positioning line
   - authenticity guardrails

## 4. Pricing (the §4.2 USD ladder) + pricing risk note

## 5. Landing-page issues            (itemized table: id, issue, file, severity, fix)
   LP1  ₹ pricing throughout                       landing-data.ts        P0
   LP2  India/NRI/Vedic framing in copy            multiple sections      P0
   LP3  fabricated testimonials (FTC risk)         landing-data.ts:360    P0 (flag; do not ship)
   LP4  WhatsApp placeholder +91 number            landing-data.ts:134    P1
   LP5  no real checkout / payment               api/*, forms             P1
   LP6  comparison table India-tier framed         ComparisonTable        P2
   LP7  no 7-day guarantee shown                   TrustClarity/FAQ       P1
   LP8  no sample-report sections on page          new section            P1
   LP9  quiz funnel absent                         new                    P2
   LP10 free calculator not embedded/linked        Hero / new             P2
   ...

## 6. Product / report issues
   G1  QA review-notes leak into client PDF        premium_report.py:294,341,454 ; saju_html/__init__.py strip gap   P0
   G2  per-pillar template grammar + filler        premium_report.py:358-363        P0
   G3  용신 disagrees across natal vs compat        strength.py:205 ↔ report_data.py:482 ↔ compat_report.py:75        P0
   G4  two prose classes (crafted vs scaffold)     premium_report.py / prose_fillers.py    P2 (backlog, not fixed here)
   G5  raw editor voice in [UNCERTAIN] notes       knowledge/ + report templates           P2
   G6  ₹ in engine-emitted report text             premium_report.py, cli defaults         P0 (part of pricing rewrite)

## 7. Engine / architecture issues
   A1  용신 SSOT + provenance metadata + regression test   (= G3 fix, detailed)
   A2  self-service app: unencrypted PII JSON, sync PDF gen in HTTP worker, no queue   tools/client_intake_app.py   P1
   A3  no payment-gateway integration for paid tiers / Companion                       P1
   A4  landing page + calculator not deployed / hardened                               P1
   A5  Nayin 30×30 table still on 5-element fallback                                    P3

## 8. Marketing plan            (the §4.4 content, expanded)
## 9. Execution plan            (the §4.5 table, expanded)
## 10. API / MCP — parked       (rationale + revisit trigger from §4.3)
## 11. Open risks & unknowns
## 12. Prioritized backlog      (P0 → P3, single consolidated list with owners/effort)
```

### 6.2 `docs/market-research-2026-09.md` — structure

Full prose writeup of §3 with: every claim, the search query used, the source URL(s), the confidence
flag, and the caveat. Sections mirror §3.1–3.7. Ends with a "Sources" list (all URLs, grouped).
Explicitly reproduces the report's own verification verdicts (§6 of the HTML) and notes where this
research agreed, extended, or downgraded them.

### 6.3 `.md` strategy rewrites — file by file

**D3 `CLAUDE.md`** — replace the "## Tiered Client Products" table with the §4.2 USD ladder; keep the
engine-`--tier` mapping. Add a short "## Market & Positioning" subsection above it with the canonical
positioning line and the "primary market = English-speaking global; India = Phase-2 only" statement.
Update the legacy-tier paragraph's ₹ references. Leave all persona / ground-rules / knowledge-file /
report-convention content untouched.

**D4 `README.md`** — replace the "## Client products" table with the USD ladder; update the
intro/"What this gives you" framing sentence to name the English-global audience; update the
`client_intake_form.html` bullet that hardcodes "₹1,499". Leave the directory map, toolchain, and
developer-command sections untouched.

**D5 `docs/MEMORY.md`** — rewrite "## Current State" product bullets to USD; rewrite the
"### Client products" table; add a "## Strategy (2026-09-07)" section with a one-paragraph summary +
a pointer to `improvements_issues.md` and `docs/market-research-2026-09.md`; update "Active Wishes /
Open Items" to reference the new P0/P1 backlog. Add the strategy shift to "Recent Changes to
Remember". Leave decisions 1–8 (except pricing-adjacent wording) and conventions untouched.

**D6 `tasks.md`** — add a new "## Priority B — Business / Go-to-Market (opened 2026-09-07)" section
under the existing priorities, summarizing the P0 blockers and pointing at `improvements_issues.md`
as the detail doc. Update the top-of-file status line to note the strategy pivot and the 3 open P0
blockers (so it is no longer "Zero open issues").

**D7 `candidates_horoscope/README.md`** — update every ₹ price and the tier table to the USD ladder;
keep all folder-convention / index content.

**D8 `docs/openwiki/products/reports.md`** — update the tier table to USD; add the positioning line.

**D9 `apps/landing-page/worklog.md`** — append one dated task entry: "Strategy shift — USD/global
pivot; pricing + positioning rewrite; testimonials flagged for replacement; see
`../../improvements_issues.md`."

### 6.4 Code — G1: review-notes leak into client PDF

**Symptom (from audit):** the audited RM Essential PDF (priced ₹799) contains
`>*Chart-derived first draft — verify against the relevant knowledge files before client delivery.*`
and a mangled `>*Chart-derived per-pillar walk — refine each entry by reading the relevant  and .*`
(the `knowledge/*.md` paths were stripped, leaving dangling "and .").

**Root cause:** `src/saju_engine/premium_report.py` emits these italic blockquote review notes at
lines ~294, ~341, ~454. `src/saju_html/__init__.py` only strips `*(see ...)*` citations,
`*see ...knowledge...*` spans, and bare `knowledge/....md` paths (`_SOURCE_CITATION_RE`,
`_SOURCE_SEE_RE`, `_SOURCE_PATH_RE`). None of them removes the *whole* review-note line, so the
sentence survives (Essential) or is left mangled (per-pillar).

**Fix (chosen approach):** stop emitting reviewer notes into client-tier output at the source.
- In `premium_report.py`, gate every `>*Chart-derived …*` / `>*… verify against …*` /
  `>*… refine each entry …*` blockquote behind a check: emit only when the report is an internal
  draft, never for `tier in {"sample", "essential", "deep", "spark", "reading", "fullmap"}` client
  output. Simplest implementation: introduce a module-level helper `_reviewer_note(ctx, text)` that
  returns `[]` for client tiers and `[f">*{text}*", ""]` otherwise, and route all three call sites
  through it. (The engine-draft markers `[ENGINE DRAFT — REVIEW REQUIRED]` are a separate,
  already-handled mechanism and are left as-is.)
- Belt-and-braces: add `_REVIEW_NOTE_RE = re.compile(r"^\s*>\s*\*(?:Chart-derived|Engine note)[^\n]*\*\s*$", re.M)`
  to `src/saju_html/__init__.py` and apply it in the same place the other source-strippers run, so
  any stray note in a hand-written `.md` is also removed at render time.

**Tests:**
- `tests/test_premium_report.py`: assert no generated client-tier markdown contains
  `"Chart-derived"`, `"verify against"`, or `"Engine note:"`.
- `tests/test_pdf.py` (or `test_html_pdf.py`): render an Essential PDF-markdown pipeline and assert
  the rendered text contains none of those strings.
- Regenerate `candidates_horoscope/reports/rm/` Essential artifacts and spot-check.

### 6.5 Code — G2: per-pillar template grammar + repeated filler

**Symptom:** `premium_report.py::_four_pillars_one_by_one` (lines ~358–363) produces
`"…shaping the **ancestral and social-root energy**. sits as **Direct Wealth**. The branch's Water
energy blends with the stem's polarity to colour how this life area expresses."` — the ten-god
clause `" sits as **X**"` has no subject (`tengod_phrase` is prepended with a bare space after a
full stop), and the third sentence is structurally identical for all four pillars.

**Fix:**
- Rebuild the 2-sentence (Essential) form so the ten-god is a grammatical clause with a subject,
  emitted only when `tengod` is non-empty, e.g.:
  `"The {combined} pillar pairs the {stem} stem ({stem_en}) with the {branch} branch, together
  shaping {area}."` + (if tengod) `" Its stem reads as **{tengod}** relative to your Day Master,
  so {area} tends to carry that dynamic."`
- Replace the identical third sentence with one that varies on real per-pillar data (branch element
  + stem element + position), so a client comparing pillars sees distinct content. Reuse
  `L.STEM_INFO[...]["element"]` and `branch_elem` which are already in scope.
- Keep the 4-sentence (Deep) block but apply the same subject fix and de-duplicate its opening
  against the 2-sentence form.

**Tests:** `tests/test_premium_report.py`:
- assert the rendered per-pillar section never contains `". sits as"` or `". Its "` mid-sentence
  artifacts (regex for `\.\s+(sits|Its)\b` where not sentence-initial is hard — instead assert the
  known-bad substring `"**. sits as **"` is absent);
- assert the four per-pillar paragraphs are not string-identical after removing the pillar name;
- snapshot one full Essential + one full Deep per-pillar section for a fixed chart.

### 6.6 Code — G3: 용신 single source of truth + provenance

**Symptom:** for one person, the natal report's Favorable Element and the compatibility report's
Favorable Element can differ (audit: natal "Earth" via 궁통보감 method, compat table "Metal" via raw
strength heuristic).

**Root cause:** two independent derivations —
- natal: `report_data.py::_element_priority_table(favorable_element, …)` consumes a `favorable_element`
  that `premium_report.py` computes from strength verdict + element-priority logic;
- compat: `compat_report.py:75` reads `strength_assessment["candidate_favorable"]` straight from
  `strength.py::assess()` (line ~205, explicitly labelled "Heuristic only").

There is no shared resolver, and `compat_report.generate_compat_report` accepts optional
`favorable_element_a/b` overrides that the default pipeline never populates.

**Fix:**
- Add one resolver, `favorable_element(chart) -> FavorableElement` where
  `FavorableElement = namedtuple/dataclass(element: str, method: str, confidence: str, note: str)`.
  Location: `src/saju_engine/strength.py` (new public function) or a small new
  `src/saju_engine/yongsin.py` imported by both — decide during implementation based on import
  cycles; `yongsin.py` is preferred if `strength.py` would need to import report logic.
- The resolver encapsulates the current natal logic (strength verdict → 식상/재성/관성 vs 인성/비겁,
  balanced-chart heuristic fallback) and returns `method` = one of
  `{"strong-dm-drain", "weak-dm-support", "balanced-heuristic"}` and `confidence`
  `{"heuristic", "reader-confirmed"}`.
- `premium_report.py` and `compat_report.py` both call it. `compat_report` stops reading
  `candidate_favorable` directly for the displayed 용신; it uses `favorable_element(chart).element`.
  The `favorable_element_a/b` override path stays (a reader who has argued a specific 용신 can still
  pass it, and that sets `confidence="reader-confirmed"`).
- Render the `method`/`confidence` as provenance in both reports' "Sources & Limits" (natal) /
  per-partner snapshot (compat), e.g. "Favorable element: Earth *(engine heuristic — balanced chart;
  final 용신 requires classical review)*".

**Tests:** new `tests/test_yongsin_consistency.py`:
- for each of the ~8 bundled candidate charts, assert
  `favorable_element(chart).element` is identical to the value that appears in the generated
  premium (natal) report AND in the generated compat report when that chart is Partner A and again
  when Partner B;
- assert `method` is one of the allowed values and `note` is non-empty;
- assert passing `favorable_element_a=` to `generate_compat_report` overrides the displayed value and
  flips `confidence` to `reader-confirmed`.

### 6.7 Landing page — `apps/landing-page`

**`src/data/landing-data.ts`:**
- `PERSONAL_REPORTS`: `free` → "Free" (rename "Free Report Sample" → "The Hook" optional);
  `essential` price `"₹799"` → `"$19"` (add `priceNote: "Intro $9"` or similar);
  `deep` price `"₹1,499"` → `"$55"`;
  `companion` price `"₹799"` → `"$9"`, `priceNote: "per month"` — and remove `companion` from the
  array that renders the primary grid (move to a constant used only by a post-purchase upsell block,
  or leave in array but mark `popular:false` and note in `improvements_issues.md` LP that it should
  move off-grid). **Decision needed at implementation:** simplest is to keep it in the array and
  down-rank; cleaner is a separate `SUBSCRIPTION_UPSELL` const. Spec choice: **separate const**,
  referenced only by a small section below the grid.
- `COMPAT_REPORTS`: basic `"₹799"` → `"$24"`; detailed `"₹1,499"` → `"$45"`; rename "Marriage
  Compatibility" → "Compatibility" (the product is not marriage-specific for the global market;
  keep 궁합 as a subtitle).
- `FAQS`: rewrite the Companion answer (₹ → $), the Essential/Deep answer (no change needed beyond
  currency-free wording), add a "Do you offer a guarantee?" Q/A (7-day), add a "Are you a Korean
  master?" Q/A (honest positioning answer).
- `TESTIMONIALS`: **leave the array as-is** but add a top-of-block code comment:
  `// ⚠️ PRE-LAUNCH BLOCKER: these are illustrative, not real customers. Publishing invented reviews
  // as genuine violates FTC endorsement guidance. Replace with real, permissioned reviews or remove
  // this section before the site goes live. See improvements_issues.md LP3.`
- `WHATSAPP_NUMBER`: leave the placeholder, add a comment pointing at LP4; the copy rewrite should
  de-emphasize WhatsApp in favour of email (US buyers expect email + PDF).
- `ABOUT_READER.bio`: rewrite to the canonical positioning ("engine + human, not a Korean master",
  classical texts cited, English-language craft). Keep the name.
- `WHAT_IS_SAju_CARDS`, `WHAT_YOU_RECEIVE_CARDS`, `TRUST_CARDS`: swap "Eastern metaphysical system"
  generic framing for the K-culture / "higher-resolution than a sun sign" / honest-craft angle;
  add a "7-day guarantee" trust card.
- `COMPARISON_ROWS`: no structural change; verify labels don't imply India tiers.
- `LANGUAGE_OPTIONS`: reorder English first (already is); leave the Indian-language options (still
  valid for diaspora) but they are no longer the emphasis.

**Section components** (`src/sections/*.tsx`): update any hardcoded ₹ strings, India city
references, or "NRI" copy found by grep. Known: `Hero.tsx`, `PersonalReports.tsx`,
`CompatibilityReports.tsx`, `AboutReader.tsx`, `FAQ.tsx`, `ComparisonTable.tsx`, `Testimonials.tsx`,
`ImportantDetails.tsx`. Enumerate exhaustively during implementation via
`grep -rn '₹\|NRI\|Bangalore\|Chennai\|Vedic\|WhatsApp' src/`.

**Out of scope for this change:** checkout wiring, quiz funnel, embedded calculator, deployment.
Those are LP5/LP9/LP10 in `improvements_issues.md`, tagged P1/P2.

## 7. Testing & verification

| Deliverable | Verification |
|---|---|
| D10–D12 (engine fixes) | `python3 -m pytest` from repo root — must stay green and grow by the new tests (target ≥ 571). Report the exact before/after count. |
| G1 | grep the regenerated `candidates_horoscope/reports/rm/*essential*` md + a freshly rendered PDF-text for the banned strings → zero hits. |
| G2 | new snapshot tests + manual read of one Essential + one Deep per-pillar section. |
| G3 | `tests/test_yongsin_consistency.py` green; manual cross-check of one candidate's natal vs compat PDF. |
| D13 (landing page) | `cd apps/landing-page && npm run build` (zero errors) and `npm test` (existing 74+ tests green). `grep -rn '₹\|NRI\|Vedic' src/` → only intentional diaspora-language references remain. |
| D1–D9 (docs) | self-review pass (§ below); no ₹ prices remain except where explicitly discussing the old India pricing as history; every market number in D1/D2 has a confidence flag and a source. |

## 8. Build order

1. **D2** market-research writeup (locks the facts everything else cites).
2. **D1** `improvements_issues.md` (the master doc; references D2).
3. **D10–D12** engine fixes G1/G2/G3 + tests; full pytest run.
4. **D13** landing page (grep-driven); `npm run build` + `npm test`.
5. **D3–D9** strategy rewrites of the other `.md` files (done last so they can point at final D1/D2
   and describe the now-fixed engine state).
6. Final: full pytest + npm build re-run; update `tasks.md` status line; write the memory file.

## 9. Risks & open questions

- **R1.** Author-estimated probabilities in §3.7 are judgement, not data — must be labelled as such
  in D1.
- **R2.** The pricing increase (₹→$19/$55) may depress conversion. Mitigation: intro pricing + A/B;
  documented, not resolved.
- **R3.** G3's resolver may surface that some bundled candidate reports were generated with the old
  (inconsistent) value — regenerating them is in scope for the RM report only; others are noted.
- **R4.** `favorable_element` resolver location (strength.py vs new yongsin.py) is deferred to
  implementation pending an import-cycle check.
- **R5.** Landing-page copy rewrite is broad; the grep list in §6.7 may miss copy embedded in JSX —
  implementation must do a full visual pass of the built page or a full `src/` read.
- **Q1.** Should `docs/issues_bugs.md` (currently "all closed") get the G1–G3 rows too, or do they
  live only in `improvements_issues.md`? *Proposed: add them to `docs/issues_bugs.md` as OPEN with a
  pointer to `improvements_issues.md`, so the historical tracker stays authoritative for engine bugs.*
- **Q2.** Keep `apps/landing-page` prices as bare `"$19"` strings, or introduce a currency-aware
  helper now? *Proposed: bare strings now; currency helper is Phase-2 PPP work.*

## 10. Sources

To be enumerated in full in `docs/market-research-2026-09.md`. Primary: Pew Research (May 2025),
Korea Foundation (Mar 2024), InnoForest via Seoulz, sajuplus.com (direct fetch), Research & Markets /
Business Research Company (astrology-app market), Entrackr / Outlook Business (AstroTalk FY25),
mcp-marketplace.io / mcpize.com (MCP monetization), LanderLab / WordStream (conversion benchmarks),
Korea JoongAng Daily / Korea Times / Korea Bizwire (K-occult wave), Lemon Squeezy / Paddle (MoR),
plus the research report's own §7 source list.
