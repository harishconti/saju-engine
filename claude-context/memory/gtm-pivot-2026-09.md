---
name: gtm-pivot-2026-09
description: 2026-09-07 go-to-market pivot to English-global/USD; G1–G3/G6 engine fixes; master doc improvements_issues.md
metadata: 
  node_type: memory
  type: project
  originSessionId: 9832a710-e4cd-4b97-8919-39507682236a
  modified: 2026-09-08T05:40:10.986Z
---

On 2026-09-07 the Saju project pivoted its go-to-market from **India / ₹ / Vedic-adjacent NRI** to
**English-speaking-global / USD**, triggered by the deep-dive report
`research-engine/output/2026-09-07/report-saju.html`.

**Canonical docs (read these before any strategy/pricing/product work):**
- `improvements_issues.md` (repo root) — master execution doc: issues (LP1–LP12, G1–G6, A1–A6),
  prioritised backlog P0–P3, USD pricing ladder, marketing + phased plan.
- `docs/market-research-2026-09.md` — every market number with an `[H]/[M]/[L]` confidence flag + source.
- `docs/superpowers/specs/2026-09-07-saju-business-refinement-design.md` + the plan alongside it.
- The old `misc/market_research/` corpus is **superseded** — do not cite it for current decisions.

**Positioning line (verbatim):** "The Saju engine Korean apps are built on — read in clear English by
a human, with the classical texts cited. Not a Korean master; an accurate engine and an honest
interpreter."

**USD pricing:** Hook free · Essential $9 intro→$19 · Compat Snapshot $24 · Deep Destiny $55 ·
Deep Compatibility $45 (marketing hero) · Bundle $89 · Companion $9/mo or $79/yr (off-grid).
Realistic ceiling with manual fulfilment ≈ $1–3K/mo; most likely outcome is kill/skip.

**Engine fixes landed 2026-09-07 (suite 568 → 590):**
- **G1** reviewer-note leak into client PDFs — `premium_report._reviewer_note()` (all tiers are
  client tiers) + `strip_source_citations` drops `>*Chart-derived…*` / `- *Engine note:*`.
- **G2** per-pillar template grammar (`premium_report._four_pillars_one_by_one`).
- **G3 / A1** 용신 single source of truth: new `src/saju_engine/yongsin.py` —
  `favorable_element(chart, override=None) -> FavorableElement(element, method, confidence, note)`.
  `generate_premium_report(..., favorable_override=)` and `generate_compat_report(...,
  favorable_element_a/_b=)` both consume it. **Always pass the reader-argued 용신 from a hand-crafted
  natal reading into the compat generator** so the two products agree. Test:
  `tests/test_yongsin_consistency.py`.
- **G6** ₹→USD across engine text (`report_data.TIER_CONFIG`), all `.md` docs, the two slash
  commands, and `apps/landing-page`.

**Landing page (`apps/landing-page`):** repositioned; USD prices; "the boy and the girl" → "both
people"; form steps "Boy/Girl Details" → "Partner A/B"; 7-day-guarantee + "not a Korean master" FAQ.
Demo PDFs (`public/demo-rm-*`, `demo-compat-*`) + `candidates_horoscope/.../pawan_sruthi/*` and
`candidates_horoscope/reports/rm/*` regenerated leak-free. `npm run build` + 107 vitest green.
Internal `boy`/`girl` payload keys NOT renamed (follow-up).

**Round 2 (also 2026-09-07):** LP3 is now a *safe default* — `TESTIMONIALS_APPROVED = false` in
`landing-data.ts`, `<Testimonials>` returns null until real reviews exist AND the flag flips. Also
done: LP6 comparison table, LP7 guarantee (FAQ + trust card + `GUARANTEE_LINE` under pricing + Hero /
AboutReader chips), LP11 (Companion moved to a strip below a 3-col grid), SEO metadata
(`en_IN`→`en_US`, 궁합/Four-Pillars framing, K-pop keyword), Hero + AboutReader copy, G5
(`compat.py` year-branch narrative — dropped "folk 점술 sites inflate this"). The pawan_sruthi
compat composite dropped 64→55 once the reader-argued 용신 (Water/Earth) flows through — `DemoReports`
+ candidates index synced. Suite still 590; landing build/lint/107 vitest green.

**Round 3 — repo housekeeping (2026-09-07):** deleted cruft (`!`, `.coverage`, `.pytest_cache`,
`.playwright-mcp`, root PNGs, `rm-deep.md` dup, intake test files). Audit reports archived →
`docs/audits/` (with index). 4 completed plan docs deleted (`docs/PLAN.md`, `docs/plans/*`,
`.claude/plan.md`). `misc/market_research/` kept + SUPERSEDED banner. `.gitignore` extended
(node_modules, .next, intake/, .remember/, settings.local.json). `.claude/settings.local.json`
trimmed ~250→~40 entries. `docs/issues_bugs.md` paths `tools/→src/` + new header. File maps
refreshed in README / docs/MEMORY.md / AGENTS.md / docs/codex/instructions.md; all now point at
`improvements_issues.md`. New engine module in the map: `src/saju_engine/yongsin.py`. Suite still
590; landing build + 107 vitest green.

**Round 4 — landing-page redesign (SHIPPED 2026-09-07):** full `apps/landing-page` restructure —
~15 sections → 9 (Hero → WhySaju → **DemoReports** (moved up, `id="demo"`) → Testimonials (gated) →
WhatsInside → Pricing → forms → HowItsBuilt → AboutReader → FAQ → FinalCTA). New theme-aware SVG
system `src/components/viz/` — `FourPillarsChart` (vertical almanac columns, the signature),
`ElementBalance` (bars + donut wheel), `LuckTimeline`, `DayMasterBadge`, `SectionHeading` (mono
eyebrow labels), `ElementalRule`, `KoreanWatermark`, `SealMark` (cinnabar 人 "hand-checked") — fed by
`src/data/demo-chart.ts` (RM real numbers) and `src/lib/elements.ts` (stem/branch→element + var
helpers). **오방색** elemental palette tokens (`--el-*`, `--lean-*`, `--seal`) + `IBM Plex Mono` as
`--font-mono` + `四柱`/`사주`/`命` watermarks in `globals.css`. Premium-editorial ("the almanac, set in
type"). Deleted `WhatIsSaju`/`WhatYouReceive`/`TrustClarity`/`ImportantDetails`/`ComparisonTable` +
their landing-data exports + the fake "15 slots/week" line. New sections `WhySaju`/`WhatsInside`
(Essential⇄Deep toggle TOC)/`Pricing`/`CompareTiers`/`HowItsBuilt`. One canonical CTA label
("Get your free chart snapshot"); `#reports`→`#pricing`. vitest.config node include → `src/**/*.test.ts`;
test-setup `afterEach(cleanup)`. **Verify:** build/lint clean, 133 vitest pass, 0 hydration errors,
no horizontal body scroll (390/768/1440), reduced-motion safe, light+dark render. Not touched: form
contract, API routes, checkout, Testimonials gate, security/proxy. Follow-ups (non-blocking) noted in
the spec's status section. Spec+plan in `docs/superpowers/`; tracker `improvements_issues.md` §5a.

**Round 5 — Better Reports plan (COMPLETE 2026-09-08):** executed
`docs/superpowers/plans/2026-09-07-better-reports.md` Tasks 1–16 inline (resume ledger
`.superpowers/sdd/progress.md`). Track B: `knowledge/12`–`16` (career/wealth/directions/health/
택일) created + Hanja-swept + wired into method/glossary/`CLAUDE.md`/`.claude/commands/saju.md`/
openwiki + `report_data.py` `# source:` provenance (`tests/test_knowledge_grounding.py`). Track A:
new `src/saju_engine/plain_glossary.py` — inline first-use jargon glosses, `> **In plain words:**`
section callouts (`prose_fillers.plain_words_*` + `prose_scaffold.generate_plain_words`), tier-scaled
`## What the Terms Mean` appendix after the Closing Note — wired into `premium_report.py` /
`skeleton.py` / `compat_report.py`. `strip_source_citations` now eats the leading space;
`combine_candidate_report.py` keeps the glossary last. RM demo set + landing `demo-rm-*` PDFs
regenerated leak-free. **Suite 594→625**; both PDF backends + compat renderer + landing
`npm run build` green.

**Still open (P0/P1):** real reviews + flip the testimonials flag; Merchant-of-Record checkout
(nothing is charged today); self-service app PII/queue hardening; deployment; real WhatsApp number.
See `improvements_issues.md` §12.

Supersedes the planning half of [[audit-2026-08-handoff]] for business scope (the engine-audit
Phase-0 items there are a separate track).
