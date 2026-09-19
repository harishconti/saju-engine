# Project Tasks

**Date opened:** 2026-06-02  
**Last updated:** 2026-09-14  
**Test count:** 885 pytest cases passing / 10 xfailed (`python3 -m pytest`); engine validation gate
`python3 tools/run_validation.py` → 194 checks (189 PASS / 5 INTERPRETATION / 0 FAIL); landing page
`npm run build` + 133 vitest cases green.
**Status:** The **engine** is complete and validated (four Korean 만세력 textbook cross-validation cases, parametrized lookup-table tests, 30×30 Nayin table on the 5-element fallback, special-formations tests). **As of 2026-09-07 the project pivoted the go-to-market from India / ₹ to English-speaking-global / USD** — see `improvements_issues.md` (master doc) and `docs/market-research-2026-09.md` (sourced research). The 3 client-facing engine defects that blocked a paid launch are **fixed** (G1 reviewer-note leak, G2 per-pillar template grammar, G3 용신 single source of truth), plus ₹→USD across the engine, docs, and landing page. **Open P0/P1 (see `improvements_issues.md` §12):** real testimonials, Merchant-of-Record checkout, self-service-app PII/queue hardening, deployment. **Package layout:** engine and PDF packages live under `src/` with direct-run shims and a ReportLab fallback.

This file is the persistent to-do list for the saju project. Items here were either explicitly deferred or surfaced during research.

---

## Priority B — Business / Go-to-Market (opened 2026-09-07)

Full detail, rationale, and the prioritised P0–P3 backlog live in **`improvements_issues.md`** (root).
Sourced market research: **`docs/market-research-2026-09.md`**. Design spec:
`docs/superpowers/specs/2026-09-07-saju-business-refinement-design.md`.

**Done 2026-09-07:**
- ✅ Market/strategy pivot to English-speaking-global / USD; all docs + engine text + landing prices ₹→USD.
- ✅ G1 — reviewer-note leak into client PDFs (`premium_report._reviewer_note`, `strip_source_citations`).
- ✅ G2 — per-pillar template grammar + repeated filler (`premium_report._four_pillars_one_by_one`).
- ✅ G3 / A1 — 용신 single source of truth: `src/saju_engine/yongsin.py::favorable_element()` +
  `FavorableElement` provenance; consumed by `generate_premium_report` (`favorable_override`) and
  `generate_compat_report` (`favorable_element_a`/`_b`); regression test `tests/test_yongsin_consistency.py`.
- ✅ Landing page (`apps/landing-page`) repositioned; USD pricing; India/matrimonial framing removed;
  7-day guarantee + honest "not a Korean master" FAQ added; testimonials flagged illustrative (LP3).
- ✅ RM + pawan_sruthi demo reports/PDFs regenerated leak-free (compat composite 64→55 after the 용신 override; DemoReports + index synced).
- ✅ LP3 hardened — `TESTIMONIALS_APPROVED = false` gate; `<Testimonials>` renders nothing until real reviews exist AND the flag is flipped.
- ✅ LP6 (comparison table), LP7 (guarantee: FAQ + trust card + line under pricing + Hero/About chips), LP11 (Companion off the grid), SEO metadata (`en_IN`→`en_US`, 궁합 framing), Hero + AboutReader copy, G5 (`compat.py` year-branch narrative).
- ✅ Repo housekeeping: deleted cruft; archived the 3 audit reports → `docs/audits/`; deleted 4
  completed plan docs; `misc/market_research/` kept with a SUPERSEDED banner; `.gitignore` +
  `.claude/settings.local.json` cleaned; `docs/issues_bugs.md` paths `tools/ → src/`; refreshed the
  file maps in `README.md` / `docs/MEMORY.md` / `AGENTS.md` / `docs/codex/instructions.md`.

**Landing-page redesign (shipped 2026-09-07):**
- ✅ **LP13 — full landing-page redesign** (shipped 2026-09-07). Restructure ~15 sections → ~9 with a
  proof-first arc; build a reusable Saju visual system (`src/components/viz/`: `FourPillarsChart`,
  `ElementBalance`, `LuckTimeline`, `DayMasterBadge`, `SectionHeading`, `ElementalRule`,
  `KoreanWatermark`) fed by `src/data/demo-chart.ts` (RM's real numbers); premium-editorial aesthetic;
  elemental palette tokens + `四柱` watermark + staggered reveal. Deletes `WhatIsSaju`,
  `WhatYouReceive`, `TrustClarity`, `ImportantDetails`, `ComparisonTable`. Spec:
  `docs/superpowers/specs/2026-09-07-landing-page-redesign-design.md`; plan:
  `docs/superpowers/plans/2026-09-07-landing-page-redesign.md`. See `improvements_issues.md` §5a.

**Open (see `improvements_issues.md` §12):**
- ⏳ P0 — add real reviews and flip `TESTIMONIALS_APPROVED` (section is safely hidden until then).
- ⏳ P1 — Merchant-of-Record checkout (Lemon Squeezy / Paddle); nothing is charged today.
- ⏳ P1 — self-service app: encrypt PII, background queue, auth (`tools/client_intake_app.py`).
- ⏳ P1 — deploy + harden landing page and calculator; real WhatsApp number; sample sections on page.
- ⏳ P2 — saju quiz funnel, embedded free calculator, move Companion off the pricing grid, Year-Ahead product.
- ⏳ P2 — G4 (two prose classes) / G5 (client-voice polish of `[UNCERTAIN]` notes).
- ⏳ P3 — Nayin table from a published source; PPP/geo-priced variants; API/MCP (only if the §10 trigger is met).

---

## Completed

### ✅ Priority 1 — Calculation Engine

- **Location:** `src/saju_engine/`
- **Done:** 2026-06-03; refactored 2026-06-21
- **Summary:** Wraps `sajupy` with our own lookups, solar-time correction, Korean/Chinese Zi-hour convention switch, 60-cycle helpers, 신살 overlays, Day-Master strength heuristic, **grid/pattern candidates**, **annual-luck (세운) overlay**, **monthly-luck (월운) overlay**, **daily-luck (일운) overlay**, **major-luck (대운) activation overlay**, an **engine-driven markdown skeleton generator** with optional **interpretive prose scaffold**, and a **premium client-facing report generator**.
- **Tests:** 520 pytest cases pass (`python3 -m pytest tests/ -v`).
- **Coverage:** candidate end-to-end cases, solar-time / Zi-hour boundaries, solar-term month boundaries, Honolulu high-longitude day rollover, leap-month handling, full year-stem/gender 대운 direction matrix, lookup tables, 신살 stars, strength heuristic, grid candidates, 세운 overlay, 월운 overlay, 일운 overlay, 대운 activation overlay, 천간합 / 화격 / 종격 detection, skeleton generation, prose scaffold, premium report generation, CLI smoke tests, PDF smoke test, PDF citation stripping, element-balance color rendering.
- **Key modules:** `pillars.py`, `lookup.py`, `daeun.py`, `daeun_overlay.py`, `stars.py`, `strength.py`, `patterns.py`, `sewoon.py`, `prose_scaffold.py`, `skeleton.py`, `premium_report.py`, `chart.py`, `engine.py`, `cli.py`.

### ✅ Priority 2 — PDF Toolchain

- **Location:** `src/saju_html/md_to_saju_pdf.py` + `src/saju_html/md_to_saju_html_pdf.py` + `tools/build-pdf.sh`
- **Done:** 2026-06-03; extended 2026-06-21
- **Summary:** Generates presentable PDFs from either a markdown report or directly from a `Chart` object (`--from-chart`). Supports `--convention` for Korean/Chinese Zi-hour handling and `--overwrite-report` to protect hand-written reports.

### ✅ Priority 3 — Chart→PDF Path

- **Done:** 2026-06-03; re-verified 2026-06-21
- **Summary:** `src/saju_html/md_to_saju_pdf.py --from-chart` + `tools/build-pdf.sh --from-chart` produce PDFs without an intermediate `.md` file.

### ✅ Priority A — HTML/CSS → Playwright PDF Backend

- **Location:** `src/saju_html/`, `src/saju_html/md_to_saju_html_pdf.py`, `tools/build-pdf.sh --html`
- **Done:** 2026-06-21
- **Summary:** New optional PDF backend renders markdown through Jinja2 + markdown-it-py + Playwright/Chromium for richer typography, proper table rendering, and easy theming. The reportlab generator remains the default; `--html` switches to the Playwright backend. Translation maps are shared in `src/saju_html/__init__.py` to keep both backends consistent.
- **Tests:** `tests/test_html_pdf.py` (5 cases). Total pytest suite is now 520.
- **Dependencies:** `playwright` (runtime) + `markdown-it-py` (already present).
- **Note (2026-06-22):** The HTML backend now strips internal `*(see knowledge/...)*` citations and color-codes Element Balance rows via CSS classes (`element-fire`, `element-earth`, etc.).

### ✅ Priority 4 — Test-Suite Migration (pytest)

- **Location:** `tests/`
- **Done:** 2026-06-21; extended 2026-06-21 (later)
- **Summary:** Migrated the standalone `src/saju_engine/validate.py` suite into `tests/` under pytest. Added focused test modules for pillars, lookup tables, 대운, stars, strength, engine end-to-end, PDF smoke test, and later for grid/pattern detection, annual-luck overlay, and skeleton generation.
- **Run:** `python3 -m pytest tests/ -v`
- **Note:** `pytest` is declared as a dev extra in `pyproject.toml`.

### ✅ Priority 5 — Cross-Validation Harness

- **Location:** `tests/test_cross_validate.py` (the standalone `tools/cross_validate.py` was folded into pytest and deleted 2026-08-22)
- **Done:** 2026-06-21; migrated to pytest 2026-08-22
- **Summary:** Runs all six candidates (Sruthi, Pawan, Harish, Gurumoorthy, Mahesh, Vishnu Priya) plus edge cases (solar-Zi boundaries, solar-term month boundary, Honolulu west-longitude day rollover) as pytest cases. Tests pillar correctness; overlays (stars, strength, patterns, 세운) are covered by their own test modules.

### ✅ Priority 7 — Engine-Driven Skeleton (Token-Reduction Aid)

- **Location:** `src/saju_engine/skeleton.py`, `cli.py`
- **Done:** 2026-06-21
- **Summary:** Generates a structured markdown skeleton from any `Chart` object. It pre-fills the four-pillar table, ten-god distribution, branch relationships, stars, strength heuristic, grid candidates, major-luck table, a 5-year annual-luck window, and a monthly-luck window. The reader still adds interpretive prose, but the engine handles all deterministic transcription. Exposed via CLI as `--format skeleton --year YYYY --month MM --focus "..."`.
- **Token-reduction rationale:** For each reading, the /saju agent no longer needs to recompute tables or query hidden-stem lookups; it receives an engine-produced scaffold and only fills in reasoning and synthesis.

### ✅ Priority 8 — Major-Luck (대운) Activation Overlay

- **Location:** `src/saju_engine/daeun_overlay.py`, `chart.py`, `engine.py`, `skeleton.py`
- **Done:** 2026-06-21
- **Summary:** Every `DaeunPeriod` now carries an activation overlay: 십신 of the 대운天干 relative to the Day Master, branch relationships between the 대운地支 and natal branches, 천간합 with natal stems, element favorability against the strength-heuristic candidate 용신/기신, and activated natal positions. The skeleton renders this in the major-luck table so current/coming 10-year themes are visible without manual derivation.
- **Tests:** `tests/test_daeun_overlay.py` (4 cases) + existing engine end-to-end coverage.
- **Token-reduction rationale:** Time-based readings no longer need the AI to look up which natal palace each 대운 pillar touches; the engine pre-computes ten-god, 합/충/형/파/해, and favorability.

### ✅ Priority 9 — Daily-Luck (일운) Overlay

- **Location:** `src/saju_engine/sewoon.py`, `chart.py`, `engine.py`, `skeleton.py`, `cli.py`
- **Done:** 2026-06-21
- **Summary:** Added daily pillar derivation (`_daily_pillar`) and `derive_ilwoon()` / `current_ilwoon_window()` to compute a 5-day 일운 window around a reference date. The skeleton renders it alongside the 월운 window. CLI gained `--day DD` to set the reference day.
- **Tests:** `tests/test_sewoon.py` (3 new cases) + `tests/test_cli.py::test_cli_skeleton_with_year_month_and_day`.
- **Token-reduction rationale:** Short-term date-picking questions no longer require manual day-pillar lookup or activation mapping.

### ✅ Priority 10 — Engine-Driven Interpretive Prose Scaffold

- **Location:** `src/saju_engine/prose_scaffold.py`, `skeleton.py`, `cli.py`
- **Done:** 2026-06-21
- **Summary:** New module drafts template paragraphs for Day Master strength reasoning, 용신 reasoning, personality, career/wealth, relationships, health, and current time-based themes directly from the computed `Chart`. Output is explicitly marked as engine-drafted and requiring reader review. Skeleton includes the scaffold by default; `--no-prose-scaffold` disables it.
- **Tests:** `tests/test_prose_scaffold.py` (5 cases).
- **Token-reduction rationale:** The AI interpreter receives a factual first draft for each major section and only needs to refine, nuance, and cite — rather than deriving obvious sentences from tables from scratch.

### ✅ Priority 11 — Premium Client-Facing Report Generator

- **Location:** `src/saju_engine/premium_report.py`, `cli.py`
- **Done:** 2026-06-21
- **Summary:** New module generates a polished 9-section markdown report from a fully-derived `Chart` following the 9-section template in `knowledge/10-output-template.md` (Cover, Chart at a Glance, Day Master Portrait, Career & Wealth, Relationships, Health & Vitality, Timing, Practical Guidance Summary, Closing Note). The engine fills all deterministic content; interpretive prose is explicitly marked `[ENGINE DRAFT — REVIEW REQUIRED]`. Exposed via CLI as `--format premium --output-file PATH`.
- **Tests:** `tests/test_premium_report.py` (14 cases at the time) + `tests/test_cli.py` premium cases + `tests/test_pdf.py::test_build_pdf_from_premium_markdown`. Total pytest suite is now 520.
- **Token-reduction rationale:** The AI interpreter receives a structured client-ready draft with tables, element balance, career tiers, compatibility matrix, lucky attributes, and timing windows already filled; it only needs to refine, personalize, and remove the engine-draft markers before delivery.
- **Note (2026-06-22):** Element Balance now emits a colored-emoji markdown table (🔴 Fire, 🟡 Earth, ⚪ Metal, 🔵 Water, 🟢 Wood). The reportlab PDF generator strips the emoji and renders colored text/bars; the HTML backend keeps the emoji and colors rows via CSS.

### ✅ Priority 12 — Tiered Client Report Products

- **Location:** `src/saju_engine/premium_report.py`, `src/saju_engine/cli.py`, `src/saju_html/md_to_saju_pdf.py`
- **Done:** 2026-06-21
- **Summary:** Added three client-facing report tiers at the time: **The Spark** (₹499, 4–5 pages), **The Reading** (₹1,499, 10–12 pages, default anchor), and **The Full Map** (₹3,499, 18–22 pages). These were later superseded by the landing-page products — **The Hook** (sample, complimentary), **The Essential Report** (essential, ₹799), and **The Deep Destiny Report** (deep, ₹1,499). `generate_premium_report(chart, tier=...)` accepts all six values today (`sample`/`essential`/`deep` plus legacy aliases `spark`→`essential`, `reading`/`fullmap`→`deep`). CLI gained `--tier {sample,essential,deep,spark,reading,fullmap}` under `--format premium`; `src/saju_html/md_to_saju_pdf.py --from-chart` also accepts `--tier`. The **Companion** subscription tier (₹799/month, Cosmic Companion) is implemented as an email-intake subscription product: the engine accepts `tier="companion"`, the landing page advertises it as a monthly/annual subscription, and submissions flow through the existing `/api/submit` email handler for manual onboarding and billing. Real payment gateway integration (Stripe/Razorpay) remains future work.
- **Tests:** `tests/test_premium_report.py` extended with tier-specific assertions (14 cases at the time). Total pytest suite is now 520.
- **Documentation:** Added to `CLAUDE.md` and memory files `saju-tiered-report-products.md` and `saju-deep-tier-expanded.md`.

### ✅ Priority 13 — Client Intake Form + Tier Selection

- **Location:** `tools/client_intake_form.html`, `tools/client_intake_server.py`
- **Done:** 2026-06-22
- **Summary:** Created a self-contained HTML intake form for clients: name, DOB, birth time, birth location, email, gender, marriage/relationship status, and tier selection (The Hook / Essential Report / Deep Destiny Report with pricing). The "main concern" textarea is enabled only when The Deep Destiny Report is selected. A small Python server (`client_intake_server.py`) serves the form and writes each submission as JSON to `candidates_horoscope/intake/YYYYMMDD-HHMMSS-{name-slug}.json`.
- **Tests:** Smoke-tested server manually; no new pytest cases (form is frontend + thin HTTP handler).
- **Documentation:** Added to `candidates_horoscope/README.md`, `README.md`, and new memory file `saju-client-intake-form.md`.

### ✅ Priority 14 — Landing-Page Report Tiers & Client Order Skill

- **Location:** `src/saju_engine/premium_report.py`, `src/saju_engine/cli.py`, `src/saju_html/md_to_saju_pdf.py`, `.claude/commands/saju-client.md`
- **Done:** 2026-06-27
- **Summary:** Added the three products shown on the legacy landing page (`misc/landing-page/archive/cosmicsaju_landing.html`) to the engine: **The Hook** (complimentary 1-page sample, `--tier sample`), **The Essential Report** (₹799, `--tier essential`), and **The Deep Destiny Report** (₹1,499, `--tier deep`, includes 2025–2030 timing + business-launch guidance). Added a project slash command `/saju-client` that ingests client details + tier and runs the full intake → engine draft → polished report → PDF → index-update pipeline. Legacy tiers `spark/reading/fullmap` remain engine-supported.
- **Tests:** Extended `tests/test_premium_report.py` with 4 new cases for sample/essential/deep + tier aliases. Full pytest suite: 135 passed.
- **Documentation:** Updated `CLAUDE.md`, `candidates_horoscope/README.md`, and memory files `saju-tiered-report-products.md` + `saju-client-order-skill.md`.

### ✅ Priority 6 — Anthropic Community Skills

- **Done:** 2026-06-12
- **Summary:** Six skills (pdf, theme-factory, canvas-design, docx, pptx, xlsx) symlinked into `~/.claude/skills/`.

### ✅ Documentation Skeleton

- **Done:** 2026-06-21 (retired 2026-06-28 as part of repo cleanup).
- **Note:** The original `docs/engine-architecture.md` and `docs/cross-validation.md` were deleted during the 2026-06-28 cleanup. The documentation surface now lives in `README.md` (project overview), `CLAUDE.md` (persona + ground rules + tier surface), `knowledge/` (interpretive reference), `candidates_horoscope/README.md` (per-candidate folder conventions), and the memory index under `~/.claude/projects/-mnt-data2-git-repos-saju/memory/`.

### ✅ Priority 15 — src Layout, PDF Package Formalization, and ReportLab Fallback

- **Done:** 2026-08-22
- **Summary:** Moved `saju_engine` and `saju_html` packages under `src/` (`src/saju_engine/`, `src/saju_html/`). Updated `pyproject.toml` package discovery and `pytest` `pythonpath` to `src`. Added `src/` direct-run shims to all script entry points so `python3 src/saju_html/md_to_saju_pdf.py`, `src/saju_html/md_to_saju_html_pdf.py`, `src/saju_html/md_to_saju_compat_pdf.py`, and the engine CLI continue to work when invoked directly. Moved `tools/combine_candidate_report.py` into `src/saju_html/combine_candidate_report.py` and updated its tests. Added a ReportLab fallback in `src/saju_html/renderer.py::build_pdf` so the HTML/Playwright backend automatically routes to the reportlab renderer when Playwright or a browser is unavailable. Updated all active documentation (`README.md`, `CLAUDE.md`, `docs/MEMORY.md`, `candidates_horoscope/README.md`, `AGENTS.md`, `docs/openwiki/`, slash commands, and `knowledge/` files) to reference the new `src/` paths.
- **Tests:** Full pytest suite: **568 passed, 8 warnings**. Direct-run smoke tests for `build-pdf.sh`, `md_to_saju_pdf.py`, `md_to_saju_html_pdf.py`, `md_to_saju_compat_pdf.py`, and the engine CLI all pass.

---

## Remaining (optional / deferred)


### ✅ Priority B — Expand Validation Coverage Further

**Status:** ✅ Completed 2026-07-12. Ten externally-sourced Korean 만세력 textbook cases now cross-validate the engine. The 30×30 Nayin pair table was implemented with source tagging; a full published 서전구미록 table was not found in the open literature (Kim Man-tae’s dissertation pp. 214–215 is behind a paywall), so the table remains on the documented 5-element fallback. Remaining presidential cases (노태우, 전두환, 이재용, etc.) are optional data-gathering work; no open engine-validation gaps remain.

**What:** The pytest suite now has **568 tests**. Ten externally-sourced Korean 만세력 cases are cross-validated:

1. **박정희 (Park Chung-hee, 5th–9th President)** — `丁巳 辛亥 庚申 辛巳` (사시, 1917-11-14 10:00, Gimhae). Corrected the previous test that followed the minority 寅時 / 戊寅 reading; the majority published view (김재원 동아일보 2013-05-03, sajupalery 2026-04, sajuforum) is 巳時 → 辛巳.
2. **노무현 (Roh Moo-hyun, 10th President)** — `丙戌 丙申 戊寅 丙辰` (진시, 음 1946-08-06 = 양 1946-09-01 08:00, Gimhae). Sourced from 조용헌 중앙일보 강좌 (上·下) and corroborated by 김재원 동아일보 comparative analysis.
3. **김대중 (Kim Dae-jung, 15th President)** — published non-hour pillars `癸亥 甲子 甲申` match the official birth date **1924-01-06**. Exact birth time is not publicly documented; the test asserts only the three verified non-hour pillars. 대운 is reverse (역행) and 丁巳 covers 1997 (age 73), matching published analyses. Sources: pisgah.tistory.com/3824 and moneyluckk.com.
4. **김영삼 (Kim Young-sam, 14th President)** — `戊辰 乙丑 己未 甲戌` (술시, 1929-01-14 20:00, Geoje). Official birth date from the Presidential Archives (1928.12.4 음력 ≈ 1929-01-14). The hour pillar corresponds to the widely published 戌시 assumption; exact birth time is not officially public. 대운 is forward (순행) and 壬申/癸酉 cover the 1992 election and 1993 inauguration, matching published analyses. Sources: Presidential Archives, career-consulting-center.tistory.com/997 (격국용신정해 excerpt), winwinstory.tistory.com/entry/김영삼-사주풀이, sank1001.tistory.com/13498365.
5. **이명박 (Lee Myung-bak, 17th President)** — `辛巳 庚子 辛丑 辛卯` (묘시, 1941-12-19 06:00, Osaka). Two independent sources: 김기승 『격국용신정해』 excerpt and 김광일철학원장 주간경향. 대운 reverse sequence verified starting at age 4.
6. **이건희 (Lee Kun-hee, Samsung)** — `辛巳 辛丑 壬戌 乙巳` (사시, 1942-01-09 10:00, Daegu). Sources: 청허의 명리즉설, 류동학 대구신문, 역학동 Daum cafe. 대운 reverse sequence verified starting at age 1 (Korean age 2).
7. **정주영 (Chung Ju-yung, Hyundai founder)** — `乙卯 丁亥 庚申 丁丑` (축시, 1915-11-25 02:00, Tongcheon/Goseong). Official birthdate plus Saju-site and newspaper consensus. 대운 reverse sequence verified starting at age 5.
8. **박근혜 (Park Geun-hye, 18th President)** — `辛卯 辛丑 戊寅 癸丑` (축시 assumption, 1952-02-02 02:00, Daegu). Sources: 박민찬 도선풍수과학원장 주간한국 and 김기승 『격국용신정해』 excerpt.
9. **문재인 (Moon Jae-in, 19th President)** — `壬辰 癸丑 乙亥 丙戌` (술시 theory, 1953-01-24 20:00, Geoje). Hour disputed (some sources argue 해시). 2017 presidential win at age 64 falls in engine's 庚申 대운, matching published commentary.
10. **이병철 (Lee Byung-chul, Samsung founder)** — `庚戌 戊寅 戊申 壬戌` (술시 majority theory, 1910-02-12 20:00, Uiryeong). Hour is debated (alternative 酉시 theory). Sources: 류동학 경북일보, 시사저널.

**Tests in `tests/test_textbook_cases.py`:**
- `test_textbook_case_four_pillars[Park ... sa-si theory]` — asserts `丁巳 辛亥 庚申 辛巳`.
- `test_textbook_case_four_pillars[Roh ... jin-si theory]` — asserts `丙戌 丙申 戊寅 丙辰`.
- `test_textbook_case_four_pillars[Kim Young-sam ... sul-si theory]` — asserts `戊辰 乙丑 己未 甲戌`.
- `test_textbook_case_four_pillars[Lee Myung-bak ... myo-si theory]` — asserts `辛巳 庚子 辛丑 辛卯`.
- `test_textbook_case_four_pillars[Lee Kun-hee ... sa-si theory]` — asserts `辛巳 辛丑 壬戌 乙巳`.
- `test_textbook_case_four_pillars[Chung Ju-yung ... chuk-si theory]` — asserts `乙卯 丁亥 庚申 丁丑`.
- `test_textbook_case_four_pillars[Park Geun-hye ... chuk-si theory]` — asserts `辛卯 辛丑 戊寅 癸丑`.
- `test_textbook_case_four_pillars[Moon Jae-in ... sul-si theory]` — asserts `壬辰 癸丑 乙亥 丙戌`.
- `test_textbook_case_four_pillars[Lee Byung-chul ... sul-si majority theory]` — asserts `庚戌 戊寅 戊申 壬戌`.
- `test_textbook_case_park_chung_hee_daeun` — asserts the published 7-period reverse-stepped sequence (庚戌, 己酉, 戊申, 丁未, 丙午, 乙巳, 甲辰) starting at age 2.
- `test_textbook_case_roh_moo_hyun_daeun` — asserts the reverse-stepped sequence (丁酉, 戊戌, 己亥, 庚子, 辛丑, 壬寅) starting at age 2 or 3.
- `test_textbook_case_park_both_readings` — cross-validates both 巳時 and 寅時 readings as documented points of disagreement; only the 寅時 reading produces the canonical 사맹격 (寅申巳亥).
- `test_textbook_case_kim_dae_jung_three_pillars` — asserts the published non-hour pillars `癸亥 甲子 甲申`.
- `test_textbook_case_kim_dae_jung_daeun` — asserts reverse-stepped sequence starting at 癸亥 age 9, with 丁巳 at age 69 covering 1997.
- `test_textbook_case_kim_young_sam_daeun` — asserts forward-stepped sequence (丙寅, 丁卯, 戊辰, 己巳, 庚午, 辛未, 壬申, 癸酉) starting at age 6, with 壬申/癸酉 covering 1992–1993.
- `test_textbook_case_lee_myung_bak_daeun` — asserts reverse-stepped sequence (己亥, 戊戌, 丁酉, 丙申, 乙未, 甲午, 癸巳) starting at age 4.
- `test_textbook_case_lee_kun_hee_daeun` — asserts reverse-stepped sequence (庚子, 己亥, 戊戌, 丁酉, 丙申, 乙未, 甲午, 癸巳) starting at age 1 or 2.
- `test_textbook_case_chung_ju_yung_daeun` — asserts reverse-stepped sequence (丙戌, 乙酉, 甲申, 癸未, 壬午, 辛巳, 庚辰, 己卯) starting at age 5 or 6.

**Cases researched but not added:**
- **노태우 (Roh Tae-woo)** — actual (1932-12-04) vs. registered (1932-08-17) birthdate; published charts do not reconcile.
- **전두환 (Chun Doo-hwan)** — month/day mismatch across sources; engine output does not match published chart.
- **이재용 (Lee Jae-yong)** — no official birth time; hour speculative.
- **이승만 (Syngman Rhee)** — `sajupy` ephemeris range is 1900–2100.
- **윤보선, 최규하, 김일성·김정일·김정은** — only one compiled source; insufficient independent verification.

**Already-covered edge cases (not part of Priority B):
- ✅ Solar-term boundary birth — tested in `tests/test_pillars.py::test_solar_term_month_boundary` (1993-12-07 大雪 flip, 亥→子).
- ✅ Leap-month birth — tested in `tests/test_pillars.py::test_leap_month_date_accepted` (1995 leap 8th lunar month).
- ✅ High-latitude / off-grid longitude — tested in `tests/test_pillars.py::test_high_longitude_honolulu_rolls_day` and `test_honolulu_solar_correction_minutes`.
- ✅ Additional year-stem yin/yang gender combinations — tested in `tests/test_daeun.py::test_daeun_direction` for all 10 stems × 2 genders.

**Estimated effort for any future optional cases:** 1–2 hours per additional textbook case (data gathering is the slow part).

### ✅ Priority C — Self-Service Calculator (Web App / API)

- **Location:** `tools/client_intake_app.py`, `tools/client_intake_app.html`
- **Done:** 2026-06-22
- **Summary:** Built a FastAPI self-service calculator. Serves the intake form at `/` and exposes `/generate`, which computes the chart from the submitted birth data, runs `generate_premium_report(..., tier=...)` for the selected tier, renders it to PDF via the reportlab backend, and returns the PDF as a download. Each request is saved as JSON to `candidates_horoscope/intake/`, and the generated PDF + intermediate markdown are saved alongside it. The form includes a UTC-offset field and enables the "main concern" textarea only for **The Deep Destiny Report**.
- **Dependencies:** Added `web` optional dependencies to `pyproject.toml` (`fastapi`, `uvicorn`, `python-multipart`).
- **Usage:** `pip install --user --break-system-packages -e ".[web]"` then `python3 tools/client_intake_app.py 8080`.
- **Caveat:** Essential/Deep Destiny PDFs are engine drafts marked `[ENGINE DRAFT — REVIEW REQUIRED]`; restrict fully automated delivery to **The Hook** or review the draft before sending.
- **2026-07-01 note:** The self-service app now accepts an optional IANA timezone and uses `zoneinfo` to derive the UTC offset (including historical DST). Local unencrypted JSON storage and synchronous PDF generation are documented as demo-deployment limitations, not production architecture.
- **2026-07-12 note:** The landing-page Next.js app (`apps/landing-page`) is now wired to the calculator for the free sample tier. A new `/api/generate` route proxies `reportType: "free"` requests to the FastAPI `/generate` endpoint, streams the PDF back to the browser, and enforces the same origin/rate-limit/honeypot/validation rules as `/api/submit`. Paid tiers continue to use the existing email/payment flow via `/api/submit`. The landing-page form gained a UTC-offset field for accurate solar-time conversion.

### ✅ Priority D — Stem Combination / Transformation-Grid Detection (천간합 / 화격 / 종격)

**Source:** continuation of engine feature work, 2026-06-21.

**Done:** 2026-06-21.

**What:** Extended `patterns.py` to detect classical stem-level grid candidates and combinations:
1. **천간합 (stem combinations / 天干合)**: 甲己合土, 乙庚合金, 丙辛合水, 丁壬合木, 戊癸合火.
2. **화격 (transformation grids)**: When a stem combination is reinforced by the matching element appearing in month branch (化格 candidates, e.g., 甲己 + 辰戌丑未 for 化土格).
3. **종격 (follower grids)**: Conservative 종재/종관/종식상/종인 candidates when the chart is weak and one element dominates.

**2026-07-01 refinement:** Added a 통근 (rooting) check to `detect_special_forms()`. A true 종격 requires the Day Master to have no allies in its own element or resource element; rooted charts are now downgraded from `"likely"` to `"possible"` with an explanatory `[UNCERTAIN]` note.
- **2026-07-12 refinement:** Extended `tests/test_patterns.py` with deeper boundary and priority tests: regular-grid 투출 priority (본기 → 중기 → 여기), transformation-grid breaker/rooting/season edge cases, special-form threshold (50% boundary) and subtype coverage (종관, 종인), and structural-note / 양인 edge cases. Test suite: **535 passing**.

**Why it reduces tokens:** These rule-based classical signatures are flagged deterministically; the AI verifies whether the special form holds rather than deriving the candidate list.

**Files touched:** `src/saju_engine/lookup.py`, `src/saju_engine/patterns.py`, `src/saju_engine/engine.py`, `src/saju_engine/chart.py`, `src/saju_engine/skeleton.py`, `tests/test_patterns.py`.

### ✅ Priority E — Marriage Compatibility (궁합) Reading

**Source:** continuation of engine feature work, 2026-06-28.

**Done:** 2026-06-28.

**What:** Added a full partner-matching / marriage-compatibility (궁합) engine, grounded in classical Korean Myeongri:
- **`src/saju_engine/compat.py`** — Top-level orchestrator (`compat_score()`) + 11 sub-system functions (A 일간합 / B 일지 합충형파해 / C Nayin / D 용신 궁합 / E 일주 궁합 / F 결합 오행 / G 십신 교차 / H 대운·세운 동기 / I 신살 궁합 / J 음양 / K 띠). Composite weighting per `knowledge/11-gunghap.md`; verdict bands Excellent / Strong / Mixed / Challenging.
- **`src/saju_engine/nayin.py`** — 60 jiazi → 30 Nayin (납음오행) lookup + 서전구미록 6-relationship grammar (相合/相沖/相刑/相害/相求/相代).
- **`src/saju_engine/stars.py`** — Extended with 홍염 (紅艶殺) + 양인 (羊刃殺) overlays required by sub-system I.
- **`src/saju_engine/compat_report.py`** — `generate_compat_report(chart_a, chart_b, name_a, name_b)` — 16-section standalone markdown report.
- **`src/saju_engine/premium_report.py`** — Added `_render_compat_snapshot()` that emits a deep-tier partner-compatibility section when `ctx.partner_chart` is set.
- **Two-chart intake form** — `tools/client_compat_intake_form.html` + `tools/client_compat_intake_server.py` (stdlib HTTP, JSON intake).
- **Self-service route** — `tools/client_intake_app.py` now exposes `/compat` (form) and `/compat/generate` (PDF).
- **Standalone PDF renderer** — `src/saju_html/md_to_saju_compat_pdf.py` wraps the existing `md_to_saju_pdf.build_pdf()` with compat-specific cover metadata.
- **Tests** — `tests/test_compat.py` (20 cases including a Pawan × Sruthi fixture-style demo pair + the original Mahesh × Vishnu Priya in-engine demo); `tests/test_stars.py` extended with 홍염 + 양인 assertions (5 new cases).
- **Knowledge base** — `knowledge/11-gunghap.md` (1002 lines): 적천수 / 연해자평 / 궁통보감 / 명리정종 / 자평진전 / 서전구미록 + 권인성·곽임성·정봉재·송기영 Korean schools + KCI empirical studies (남기동·김만태 2018, 이수동 2023, 김우정 2025).

**Files touched:** `src/saju_engine/compat.py` (new), `src/saju_engine/compat_report.py` (new), `src/saju_engine/nayin.py` (new), `src/saju_engine/stars.py` (extended), `src/saju_engine/premium_report.py` (extended), `src/saju_engine/__init__.py` (exports), `tools/client_compat_intake_form.html` (new), `tools/client_compat_intake_server.py` (new), `src/saju_html/md_to_saju_compat_pdf.py` (new), `tools/client_intake_app.py` (extended), `tests/test_compat.py` (new, 20 cases), `tests/test_stars.py` (extended), `knowledge/11-gunghap.md` (new).

**Demo pair:** `candidates_horoscope/marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility.{md,pdf}` (basic) and `pawan_sruthi/pawan_sruthi_compatibility_deep.{md,pdf}` (deep) — Pawan (丙 day master, Wood-favorable, male) × Sruthi (丙 day master, Metal-favorable, female) produces a composite of **64 / 100 (Mixed)**, with the strongest favorable: 일지 육합 (丙午 ↔ 丙寅 = no, but the chart-to-chart 십신 cross shows 겁재-정관 pairing), 巳午未 三合 fire in Pawan's pillar set amplifies Sruthi's Wood support; cross-용신 supply (Pawan needs Wood → Sruthi's chart supplies Wood through 寅); Yellow flags: 10-십신 cross (same Day Master = 겁재 동질 — classical caution per 적천수), 午-巳 self-punishment potential; 띠 (辛未 vs 癸酉) is neutral.

**Original engine-draft demo:** Mahesh (庚, male) × Vishnu Priya (辛, female) → 58/100 Mixed is still available as a second demonstration pair; see `tests/test_compat.py::test_compat_mahesh_x_vishnu_priya_demo_pair`.

**Storage convention:** Each pair gets its own subfolder under `candidates_horoscope/marriage_compatibility/`: `{name_a_slug}_{name_b_slug}/`. The filename base is `{name_a_slug}_{name_b_slug}_compatibility`. Basic reports use the unsuffixed base (`{...}_compatibility.{md,pdf}`); deep reports append `_deep` (`{...}_compatibility_deep.{md,pdf}`). Partners' actual slugified names are used, not role labels. Canonical order is Partner A first, Partner B second; for heterosexual pairs Partner A is the male.

**Decision applied:** 從格 thresholds are conservative (>50% weighted element mass + weak/balanced verdict) and marked `possible` / `[UNCERTAIN]`; 화격 requires in-season month branch and no breaker.


---

## Items explicitly decided against

- Build a custom ephemeris from scratch — `sajupy` is sufficient.
- Use stem-branch (DE441, TypeScript) — sub-second accuracy not needed.
- Use `lunar-python` — wrong conventions for Korean 명리.
- Continuous-integration pipeline — personal project, overkill.

---

## File references

- `README.md` — project overview and quickstart
- `docs/MEMORY.md` — persistent project memory (state, conventions, quick commands)
- `pyproject.toml` — packaging, dependencies, pytest config
- `requirements.txt` + `requirements-dev.txt` — dependency files
- `src/saju_engine/` — calculation engine
- `tests/` — pytest suite
- `tools/cross_validate.py` — cross-validation harness
- `src/saju_html/md_to_saju_pdf.py` + `tools/build-pdf.sh` — PDF pipeline
- `src/saju_html/combine_candidate_report.py` — premium report combiner
- `tools/client_intake_form.html` / `client_intake_server.py` / `client_intake_app.html` / `client_intake_app.py` — client intake + self-service calculator
- `knowledge/10-output-template.md` — report output structure
- `knowledge/09-interpretation-method.md` — 9-step interpretation procedure
- `~/.claude/projects/-mnt-data2-git-repos-saju/memory/` — persistent memory index

---

## Change log

- **2026-09-14 (client-visible item 1 fixed + Harish base report regenerated — Suite 883 → 885)** —
  Fixed the last known instance of the raw-vs-resolved favorable-element bug class:
  `premium_report.py`'s "What This Year Means for You" callout and the Hook-tier one-liner were
  reading the raw, un-resolved favorable element instead of the engine's actual resolved value
  (climate-merged or reader-overridden). Both now thread the report's override through and read the
  resolved value, matching the fix already applied to the career sections. Regenerated
  `candidates_horoscope/reports/harish/harish-report.md` + `.pdf` from scratch (his folder had been
  cleared for a full rebuild); the corrected text now appears natively with no manual patch. His
  `career.md` / `land-workshop-business.md` / `luck-timeline.md` follow-ups still need re-authoring
  onto Water/Metal — not done in this pass. Suite **885 passed / 10 xfailed / 0 failed**; validation
  CLI unchanged.
- **2026-09-13 → 2026-09-14 (Engine Validation Campaign, COMPLETE — Suite 649 → 883)** — Ran an
  independent, source-cited validation of the whole engine as Plans 1–6 (foundation/pillars,
  대운/세운, lookups, 용신, 조후, compat+career). Built a permanent harness
  (`src/saju_engine/validation.py`, `tools/run_validation.py`, `tests/validation/`) certifying
  **194 checks / 189 PASS / 5 INTERPRETATION / 0 FAIL** across 8 subsystems, each backed by a
  research doc citing ≥2 independent Korean sources per rule family
  (`docs/research/2026-09-validation-{yongsin,climate,compat-career}.md`). The campaign was
  validation-only by design (defects pinned as tests, not fixed), except the user-ordered 야자시
  hour-stem fix in `pillars.py`. Found 13 loose ends (3 client-visible, 10 other). The six plan
  documents are deleted post-certification (superseded by the research docs + the rendered report
  `docs/audits/2026-09-engine-validation-report.md` + this entry).
- **2026-09-14 (post-campaign defect fixes, user-directed — Suite → 883 passed / 12 xfailed)** —
  Fixed 9 of the campaign's 13 carried loose ends: **nayin order-dependence** (compat scores now
  symmetric regardless of partner order — `compat.py::_canonical_nayin_pair`); **career tier pool**
  re-keyed from the Day Master's own element family onto the resolved 용신+희신 families per
  `knowledge/12-career-and-vocation.md:130-152`, which also fixed a client-visible bug where career
  sections argued the raw un-resolved favorable element instead of the reader/climate-resolved one;
  **`md_to_saju_compat_pdf.py --output`** path bug (missing directory creation); **Harish's
  longitude** reconciled across 3 data sites (pillar-neutral, 79.42); the **辰/戌 climate-model
  divergence** resolved as documentation + declared scope limit (not a behaviour change); an
  **unsourced climate claim** removed from `knowledge/17-climate-method.md`; a **dead test
  registry** pruned; and a **육합 (six-combination) dead-code bug** in `compat.py` fixed together
  with documenting the 삼형 branch-punishment chain position as an unsourced scope limit — the only
  fixture this moved was `compat-mahesh-vp` (64/Mixed → 68/Strong); the two published compat
  anchors did not move. **Still open:** `premium_report.py`'s "What This Year Means for You"
  callout still reads the raw favorable element instead of the resolved one (pinned by 2 xfail
  tests in `tests/validation/test_val_climate.py`); client-report regeneration for the 야자시 fix
  (Pawan done, Mahesh + the `pawan_sruthi` compat PDF pending) and for Harish's stale follow-ups
  (base report regenerated, `career.md`/`land-workshop-business.md`/`luck-timeline.md`/PDF not yet
  re-authored — his candidate folder was deliberately cleared to regenerate from scratch); and two
  open product decisions surfaced but not decided (whether 조후 should outrank 억부 more broadly;
  whether `climate.py` should expand to the full 寒暖燥濕 궁통보감 model). Final gates: suite
  **883 passed / 12 xfailed / 0 failed**; validation CLI `194 (PASS 189, INTERPRETATION 5, FAIL 0)`
  exit 0.
- **2026-09-08 (candidate regen — Sruthi / Pawan / Gurumoorthy)** — Continued the candidate
  regen for the three with `career.md` deep-dives. **Pillars re-validated** against external
  sources (day pillars cross-checked against the engine's verified 노무현 textbook anchor + web;
  month solar-term boundaries confirmed via the engine): Sruthi 癸酉/甲子/丙寅/己丑, Pawan
  辛未/丁酉/丙午/戊子 (야자시 hour), Gurumoorthy 甲辰/辛未/己巳/戊辰 — all confirmed, no hour
  knife-edge. **Base reports regenerated** as engine `--tier deep` premium with the new
  **`--favorable-override`** CLI flag set to each reader-argued 용신 (Sruthi Earth, Pawan Water,
  Gurumoorthy Metal) so the engine report agrees with the hand-crafted 궁통보감 analysis; the
  original hand-written bases kept as `{name}-report-legacy.md`. **Each `career.md` re-grounded**
  in `knowledge/12` (Element→Industry Families, Ten-God→Career Mode, 용신 vs. DM, Employment vs.
  Entrepreneurship), `knowledge/13` (식상생재, carrying capacity, 재고, Wealth Preservation) and
  `knowledge/16` (택일 by event type) with each file's modern-convention caveat. Gurumoorthy
  combined report regenerated. **Engine fixes:** `--favorable-override` CLI flag added;
  `combine_candidate_report.PROJECT_ROOT` fixed (`.parent.parent` → `.parent.parent.parent` —
  broke after the src/ migration); reportlab title translation gap (stray Russian "карьера").
  All PDFs clean (0 leaks / drafts / residual CJK). Suite **627**.

- **2026-09-08 (candidate regen — Harish, full)** — Re-validated Harish's four pillars against
  external sources and regenerated his full report set. **Pillar validation:** year 壬申 / month
  乙巳 / day 辛亥 / hour 己丑 — year & day confirmed (day pillar cross-checked against the engine's
  verified 노무현 textbook anchor + web), month 乙巳 confirmed (June 4 1992 is before 芒種; the
  engine flips 乙巳→丙午 between June 5–6), hour 己丑 correct for the recorded 03:10 but the
  corrected solar time (**02:57**, −12.2 min at the Wikipedia coordinate **13.33°N, 79.45°E**)
  sits only ~3–5 min from the 丑→寅 boundary — flagged lower-confidence. Longitude corrected
  79.32 → **79.45°E** (pillars unchanged). **Regenerated:** `harish-report.md`+`.pdf` (engine
  `--tier deep`, plain-language layer); `career.md`+`.pdf` and `land-workshop-business.md`+`.pdf`
  **re-grounded** in the new `knowledge/12` (Element→Industry Families, Ten-God→Career Mode, 용신
  vs. DM, Employment vs. Entrepreneurship), `knowledge/13` (식상생재, carrying capacity, 겁재奪財
  mitigations, Wealth Timing/Preservation), `knowledge/14` (directions, Scope Boundary — Not 풍수),
  `knowledge/16` (택일 by event type, almanac-layer boundary) — the old "not in the knowledge
  base / extrapolation" disclaimers in the industry and direction sections replaced with proper
  citations + each file's modern-convention caveat; `luck-timeline` front-matter re-validated;
  README row updated. All 4 PDFs: 0 citation leaks, 0 engine-draft markers, 0 residual CJK.
  **Engine hardening (benefits all reports):** `gloss_first_use` word-boundary + TOC / paren /
  slash-list / emphasis-span / attributive-noun skips, `collect_used_terms` reuses the filter;
  `strip_source_citations` newline-tolerant `*(see\s…)*`, `*(knowledge/…)*` no-see form, short
  `knowledge/13` form + trailing `§clause` (internal `§N` refs preserved); translation maps +20
  compound terms (편인식신, 겁재奪財, 재다신약, 풍수/風水, 하도낙서, 상생/상극, 택일, …);
  `premium_report._section_practical_guidance` + "Three Things to Be Mindful Of" now emit `-`
  bullets instead of `1.` (the reportlab backend rendered every `1.` literally as "1."); the
  reportlab inline renderer (`md_to_saju_pdf.md_inline_to_html`) now handles `_underscore
  italic_` (word-boundary-guarded so `day_branch_middle` is untouched) — the engine's `> _Methodology…_`
  and `> _For business-critical decisions…_` footnotes had been leaking literal underscores;
  +月運/日運/일운 translations. 2 new regression tests; suite → **627**. RM demo set rebuilt.

- **2026-09-08** — Executed the **Better Reports** plan (`docs/superpowers/plans/2026-09-07-better-reports.md`) inline, Tasks 1–16. **Track B (KB expansion):** `knowledge/16-date-selection.md` (택일) added; KB cleanup sweep across `knowledge/12`–`16` (Hanja-on-first-use, `재생관` attribution → `knowledge/03` generating cycle, `형` gloss 刑=penalty, `겁재奪財` normalisation, depersonalised `knowledge/14` scope note); wired 12–16 into `09-interpretation-method.md` / `00-glossary.md` (+재고·재다신약·택일·개업·양택) / `CLAUDE.md` / `.claude/commands/saju.md` / `docs/openwiki`; added `# source:` provenance to the 5 interpretive tables in `report_data.py` + new `tests/test_knowledge_grounding.py`; reconciled `prose_fillers`/`prose_scaffold` citations. **Track A (plain-language layer):** new `src/saju_engine/plain_glossary.py` (`PlainDef`, `PLAIN_GLOSSARY`, `gloss_first_use`, `collect_used_terms`, `render_terms_section`) + `tests/test_plain_glossary.py`; 7 `plain_words_*` "In plain words" section-callout fillers in `prose_fillers.py`; `prose_scaffold.generate_plain_words`; wired into `premium_report.py`, `skeleton.py`, `compat_report.py` (inline first-use glosses + callouts + a tier-scaled `## What the Terms Mean` appendix after the Closing Note); `strip_source_citations` now eats the preceding space; `combine_candidate_report.py` keeps the glossary last. RM demo set (sample/essential/deep `.md` + PDFs + landing assets) regenerated leak-free. Full suite **625 passed** (was 594 after plan Task 4); both PDF backends + compat renderer + `apps/landing-page` `npm run build` green.

- **2026-08-22** — Completed Phase 0 + Phase 1 consolidation from the engine audit addendum (`docs/audits/2026-08-22-engine-audit-addendum.md`). Phase 0: compat engine cluster, daeun backward floor, client-visible report leaks. Phase 1: unified element-balance computation in `strength.py`; split `Chart` into `BirthData`/`NatalData`/`LuckData`/`ReferenceData` cluster views; moved `ELEMENT_EMOJI`/`ELEMENT_COLORS` to `saju_engine.report_data` removing engine->presentation inversion; deleted orphan `validate.py`/`cross_validate.py` and dead helpers in `daeun.py`/`sewoon.py`/`pillars.py`; reconciled Sources strippers so `saju_html` stops at the next heading. Updated `README.md` and `docs/MEMORY.md` to remove deleted-script references. Full test suite: **563 passed, 8 warnings** (was 557; +6 new regression tests). Updated `docs/audits/2026-08-22-engine-audit-addendum.md`, `tasks.md`, and `memory/audit-2026-08-handoff.md`.

- **2026-07-12 (latest)** — Created landing-page demo reports for all three single-chart tiers using RM (Kim Nam-joon, BTS) as a recent-born public figure. Birth data: 1994-09-12, 13:28 KST, Seoul, South Korea (birth time from his publicly shared hospital wristband, cited by Astro.com / Astro-Databank). Generated `candidates_horoscope/reports/rm/` with `rm-report.{md,pdf}` (Deep Destiny), `rm-essential.{md,pdf}` (Essential), and `rm-sample.{md,pdf}` (1-page Hook). Copied the PDFs to `apps/landing-page/public/demo-rm-{sample,essential,deep}.pdf` and updated the landing-page "See Real Demo Reports" section to feature RM's chart snapshot and offer all three downloads. Added RM to the candidate index in `candidates_horoscope/README.md`. Landing-page `npm run lint` and `npm run build` pass. Updated `docs/MEMORY.md`, `memory/MEMORY.md`, and `tasks.md`.

- **2026-07-12** — Added six more externally-sourced Korean 만세력 textbook validation cases to `tests/test_textbook_cases.py`: 이명박 (Lee Myung-bak, `辛巳 庚子 辛丑 辛卯`), 이건희 (Lee Kun-hee, `辛巳 辛丑 壬戌 乙巳`), 정주영 (Chung Ju-yung, `乙卯 丁亥 庚申 丁丑`), 박근혜 (Park Geun-hye, `辛卯 辛丑 戊寅 癸丑`), 문재인 (Moon Jae-in, `壬辰 癸丑 乙亥 丙戌` — hour disputed), and 이병철 (Lee Byung-chul, `庚戌 戊寅 戊申 壬戌` — hour debated). Added 대운 regression tests for the three highest-confidence new cases (Lee Myung-bak, Lee Kun-hee, Chung Ju-yung). Also updated the OpenWiki toolchain page with the current Nayin-table source-research finding (no open 30×30 named-Nayin table found; Kim Man-tae’s dissertation pp. 214–215 is paywalled). Full test suite: **557 passed, 8 warnings** (was 548; +9 tests). Updated `docs/MEMORY.md`, `memory/MEMORY.md`, and `tasks.md`.

- **2026-07-12 (latest)** — Completed the `docs/openwiki/` structured documentation site. Added `docs/openwiki/README.md` (index), `docs/openwiki/architecture/engine.md`, `docs/openwiki/domain/knowledge-and-skill.md`, `docs/openwiki/products/reports.md`, and `docs/openwiki/operations/toolchain-and-testing.md`; the existing `docs/openwiki/quickstart.md` remains as the entry page. Added an OpenWiki pointer section to `CLAUDE.md` and created `AGENTS.md` with agent onboarding defaults. This is documentation-only; no code changes. Full test suite: **548 passed, 8 warnings**.

- **2026-07-12** — Completed the last broader Saju deferred task by adding a fourth externally-sourced Korean 만세력 textbook case, 김영삼 (Kim Young-sam, 1929-01-14, Geoje, 戌시 assumption), to `tests/test_textbook_cases.py`. Added `test_textbook_case_four_pillars[Kim Young-sam ... sul-si theory]` asserting the published four pillars `戊辰 乙丑 己未 甲戌` and `test_textbook_case_kim_young_sam_daeun` asserting the forward-stepped 대운 sequence (丙寅, 丁卯, 戊辰, 己巳, 庚午, 辛未, 壬申, 癸酉) starting at age 6, with 壬申/癸酉 covering the 1992–1993 presidency window. Sources: Presidential Archives, career-consulting-center.tistory.com/997 (격국용신정해 excerpt), winwinstory.tistory.com/entry/김영삼-사주풀이, sank1001.tistory.com/13498365. With this, all broader Saju items from the 2026-07-12 batch are resolved. Full test suite: **548 passed, 8 warnings** (was 546; +2 tests). Updated `tasks.md` and memory.

- **2026-07-12 (earlier)** — Closed broader Saju tasks 13–16: (13) added 15 deeper special-formations validation tests in `tests/test_patterns.py` covering regular-grid priority, transformation-grid breaker/rooting/season, special-form threshold/subtypes, and 양인 edge cases; (14) wired the landing-page free sample tier to the FastAPI self-service calculator via a secure Next.js `/api/generate` proxy with origin allowlist, rate limit, honeypot, and UTC-offset validation; (15) implemented the **Cosmic Companion** subscription tier (₹799/month) as an email-intake product across the engine, CLI, landing page, and `/api/submit` flow; (16) eliminated the remaining `[ENGINE DRAFT — REVIEW REQUIRED]` placeholders by adding six chart-derived prose fillers (`dm_arrival_narrative`, `regular_grid_narrative`, `special_grid_note`, `branch_relationship_snapshot`, `depleted_element_health`, `spouse_palace_tengod`) and wiring them into `premium_report.py`. Full test suite: **546 passed, 8 warnings**. Updated `tasks.md`, `CLAUDE.md`, landing-page files, and memory.

- **2026-07-06 (later)** — Implemented the 30×30 Nayin (납음) pair table infrastructure in `src/saju_engine/nayin.py`: added `NAYIN_PAIR_TABLE` (900 ordered cells), `NAYIN_PAIR_SOURCE` tags (`element-grammar-fallback` vs `sourced`), and `nayin_relation_detail()` API. Updated `src/saju_engine/compat.py` to map the six relationship types to the full ±5 weight budget, expose the source tag in flags, and keep the narrative honest about fallback data. Updated `knowledge/11-gunghap.md §C` with a data-gathering note documenting the gap for a true published 서전구미록 30×30 table. Added 4 regression tests in `tests/test_nayin.py` (table completeness, diagonal 상대, source-tag presence, detail API) and 2 in `tests/test_compat.py` (weight budget, fallback flag); updated the Mahesh × VP demo-pair nayin anchor from 2 to 3. Extended `_classify_flag()` to surface Nayin 상합/상구/상해/상충 flags in favorable/yellow/red buckets. Full test suite: **519 passed, 8 warnings** (was 513; +6 tests). Updated `tasks.md` and memory.

- **2026-07-06** — Completed Priority B by adding the third externally-sourced Korean 만세력 textbook case, 김대중 (Kim Dae-jung, 1924-01-06, Ha-ui-do, longitude ≈ 126.0°E), to `tests/test_textbook_cases.py`. Added `test_textbook_case_kim_dae_jung_three_pillars` asserting the published non-hour pillars `癸亥 甲子 甲申` and `test_textbook_case_kim_dae_jung_daeun` asserting reverse-stepped 대운 with `丁巳` at age 69 (covering the 1997 presidential election). Birth hour is not publicly documented, so the test deliberately does not assert the hour pillar. Sources: pisgah.tistory.com/3824 and moneyluckk.com. Full test suite: **513 passed, 8 warnings** (was 511; +2 tests). Updated `tasks.md` and memory.

- **2026-07-05** — Closed engine-audit B9 by documenting and implementing additional classical 신살 in `knowledge/07-special-formations.md` and `src/saju_engine/stars.py`: the remaining 십이신살 stars (겁살, 재살, 천살, 지살, 연살, 월살, 망신, 장성, 반안, 육해), 원진살, 귀문관살, 백호대살, 괴강살, 천덕귀인, and 월덕귀인. Added 9 regression tests in `tests/test_stars.py`, wired month-branch/stem/day-pillar data through `engine.py` into `derive_stars`, updated `skeleton.py` to use human-readable Korean/Hanja star labels, and extended `hanja_glossary.py` with the new terms. Ambiguous/non-standard terms (혈각, 관부, 폐문, 고각, 사의, 양록, 음록, 삼기귀인, 학당, 문곡) remain unimplemented per Ground Rule 1. Full test suite: **511 passed, 8 warnings** (was 502; +9 tests). Updated `docs/audits/2026-07-05-engine-audit.md`, `tasks.md`, and memory.

- **2026-07-02 (evening)** — Hardened the engine's foundation tables with 51 new parametrized regression tests in `tests/test_lookup.py`. Coverage now locks down `HIDDEN_STEMS` (12 branches + 1 coverage), `STEM_INFO` (10 stems + 1 coverage), `BRANCH_INFO` (12 branches + 1 coverage), `SIX_COMBINATIONS` (6 pairs + symmetry), `SIX_CLASHES` / `SIX_HARMS` / `SIX_BREAKS` (6 pairs + symmetry each), and `THREE_HARMONIES` (4 frames + complete coverage check + element consistency with `BRANCH_INFO`) and `THREE_PUNISHMENTS` (3 frames). Also added `tests/test_pdf.py::test_pdf_no_camelcase_hanja_pair_transliteration` to prevent the 2026-07-02 Hanja-pair defect from silently recurring — builds a fresh PDF containing 丙寅 / 辛未 / 甲子 / 丙辛之日起戊子 / 甲己合土 / 乙庚合金 / 丙辛合水 and asserts that none of the camelCase defect tokens (`BingIn` / `BingO` / `SinMi` / `SinMu` / `GapJa` / `GapIn` / `EulMi` / `ImJa` / `GyeMi`) appear in the rendered `pdftotext` output. Full test suite: **441 passed, 8 warnings** (was 391; +50 tests). Updated `docs/issues_bugs.md`, `tasks.md`, and memory.

- **2026-07-02 (later)** — RESOLVED known unfixed defect `saju-singlechart-hanja-pair-transliteration` (single-chart reportlab PDF Hanja pairs rendered as camelCase: 丙寅→"BingIn", 甲子→"GapJa", 辛未→"SinMi"). Root cause was stale PDFs generated with the pre-2026-06-21 fix; the `translate_inline()` function in `src/saju_html/__init__.py` was already correct. Regenerated 10 legacy PDFs (sruthi, pawan, harish, mahesh, vishnu-priya, gurumoorthy × 2, mahesh × 2, cross-candidate) with the current `tools/build-pdf.sh`. Verification: `pdftotext <pdf> | grep -oE "(BingIn|SinMi|GapJa|BingO)"` returns 0 for all 10 files. Memory updated; no code change required.

- **2026-07-02** — Extended `tests/test_textbook_cases.py` with a second externally-sourced Korean 만세력 case (노무현, `丙戌 丙申 戊寅 丙辰`, source: 조용헌 중앙일보 강좌 + 김재원 동아일보 comparative analysis). Corrected the existing 박정희 test from the minority 寅時/戊寅 reading to the majority 巳時/辛巳 reading (sources: 김재원 동아일보 2013-05-03, sajupalery 2026-04, sajuforum). Added `test_textbook_case_roh_moo_hyun_daeun` and `test_textbook_case_park_both_readings` to cross-validate the documented 寅時/巳時 controversy and confirm the canonical 사맹격 is only formed under the 寅時 reading. Full test suite: **391 passed, 8 warnings**. Updated `tasks.md` header + Priority B.

- **2026-07-01 (later)** — Closed the remaining reviewer deep-dive items: added 통근 (rooting) check to 종격 detection (H13); replaced silent element-emoji stripping in reportlab with colored bullets (L19); tightened `tests/test_compat.py` demo-pair assertions to exact deterministic values (L20); and documented the demo-deployment privacy/synchronous-generation limitations in `client_intake_app.py`, `README.md`, and both intake forms (M15). Full test suite: **386 passed, 8 warnings**. Updated `docs/issues_bugs.md` and `tasks.md`.

- **2026-07-01 (latest)** — Closed D1, the last open item in `docs/issues_bugs.md`, by adding `tests/test_textbook_cases.py` with an external Korean Saju validation case for Park Chung-hee (박정희): four pillars (`丁巳 辛亥 庚申 戊寅`) and the first seven 대운 periods (starting age 2 with `庚戌`, stepping backward) matched against a published Korean Saju blog. Full test suite: **388 passed, 8 warnings**. Updated `docs/issues_bugs.md`, `tasks.md`, and memory.

- **2026-07-01** — Closed the entire `docs/issues_bugs.md` backlog. Final fixes: standardized legacy base reports (Sruthi, Pawan, Harish, Gurumoorthy) to parenthetical `*(see knowledge/...)*` citations and tagged them as *legacy-format*; verified the 己 (Yin Earth) 12운성 table and removed the incorrect `[UNCERTAIN]` note; merged Harish `youtube-channel-ideas.md` into `career.md` per the overlap-merge rule; stripped Vishnu Priya engine-draft boilerplate, added citations, and regenerated all PDFs. Full test suite: **383 passed, 8 warnings**. Updated `docs/issues_bugs.md`, `docs/PLAN.md`, `candidates_horoscope/README.md`, `tasks.md`, and memory.

- **2026-06-28 (later)** — Added Codex support: created `docs/codex/instructions.md` (project-level agent context) and two user-level Codex skills (`saju-reading` and `saju-client-order`) in `~/.codex/skills/`, validated with `quick_validate.py`. Updated `docs/MEMORY.md` and `README.md` to reference the new Codex surface.

- **2026-06-22 (latest)** — Completed documentation audit: updated `README.md`, `CLAUDE.md`, `candidates_horoscope/README.md`, `docs/engine-architecture.md`, `docs/cross-validation.md`, `ENGINE_SPEC.md`, `ENGINE_RESEARCH.md`, `.claude/commands/saju.md`, and `tasks.md` to reflect the current engine modules, tiered reports, intake forms, self-service calculator, 520-test pytest suite and 12/12 cross-validation harness. Note: the old `docs/` contents, `ENGINE_SPEC.md`, and `ENGINE_RESEARCH.md` were deleted 2026-06-28; a fresh `docs/` folder was created 2026-07-06 for project memory, issue log, audit records, and plan artifacts.

- **2026-06-22 (later)** — Implemented the deferred **self-service calculator**: added `tools/client_intake_app.py` (FastAPI) + `tools/client_intake_app.html`. The form at `/` collects the same intake fields as `client_intake_form.html`; the `/generate` endpoint computes the chart, runs `generate_premium_report(..., tier=...)`, renders the PDF via reportlab, and returns it as a download. Saves intake JSON, engine markdown, and generated PDF to `candidates_horoscope/intake/`. Added `web` optional dependencies to `pyproject.toml` (`fastapi`, `uvicorn`, `python-multipart`). Documented in `README.md`, `candidates_horoscope/README.md`, `CLAUDE.md`, and new memory file `saju-self-service-calculator.md`. Total pytest suite is now 520.

- **2026-06-21** — Implemented three-tier client report products in `src/saju_engine/premium_report.py` and `src/saju_engine/cli.py`: **The Spark** (₹499, 4–5 pages), **The Reading** (₹1,499, 10–12 pages, default anchor), and **The Full Map** (₹3,499, 18–22 pages). `generate_premium_report(chart, tier=...)` now gates sections per tier; CLI gained `--tier {spark,reading,fullmap}` under `--format premium`; `src/saju_html/md_to_saju_pdf.py --from-chart` accepts `--tier` and uses the premium generator. Added `tests/test_premium_report.py` tier-specific assertions and unknown-tier error test. Updated `CLAUDE.md` with the tier strategy and created memory file `saju-tiered-report-products.md`. Total pytest suite is now 520.

- **2026-06-22 (late)** — Applied paid-product PDF audit to Vishnu Priya combined report and then recreated Mahesh's combined PDFs with the same pattern. Created `src/saju_html/combine_candidate_report.py` to merge base report + follow-ups: Closing Note moved to final page, duplicate `### Career Archetypes` table replaced with a transition, and `## Sources` sections stripped from client output. Expanded `src/saju_engine/premium_report.py` with `_right_now_callout()` and 9-field `Lucky Attributes` reference card. Upgraded `src/saju_html/theme.css` with premium cover page, Quick Reference card, Right Now callout, Lucky Attributes grid, SVG Element Balance chart, table keep-together, and branded footer. Updated `src/saju_html/renderer.py` to inject the SVG chart and wrap Quick Reference / Right Now / Lucky Attributes sections in styled cards. Improved `src/saju_html/md_to_saju_pdf.py` footer branding with confidentiality line. Added `--combined` flag to `tools/build-pdf.sh` for combined-report PDFs. Updated `CLAUDE.md`, `candidates_horoscope/README.md`, and memory files (`standard-client-report-pipeline.md`, `client-report-pdf-readiness-standard.md`, `saju-paid-product-pdf-audit.md`, `docs/MEMORY.md`) to document the new premium pipeline so future reports repeat the same pattern. Regenerated `vishnu-priya-combined.md` and `mahesh-combined.md` plus their reportlab and HTML/Playwright PDFs.

- **2026-06-22** — Added color-coded Element Balance rendering and internal citation stripping. Markdown source now uses colored emoji indicators (🔴 Fire, 🟡 Earth, ⚪ Metal, 🔵 Water, 🟢 Wood). Both PDF backends render colors: reportlab strips emoji and colors text/bars; HTML/Playwright keeps emoji and colors rows via CSS. Internal citations such as `*(see knowledge/05-ten-gods.md)*` may remain in `.md` files but are automatically stripped from client PDFs. Updated `src/saju_html/__init__.py`, `src/saju_engine/premium_report.py`, `src/saju_html/md_to_saju_pdf.py`, `src/saju_html/renderer.py`, `src/saju_html/theme.css`, and Vishnu Priya reports/PDFs. Added `tests/test_premium_report.py` emoji assertion, `tests/test_pdf.py::test_build_pdf_strips_source_citations`, and `tests/test_html_pdf.py::test_html_pdf_strips_source_citations_and_colors_elements`.

- **2026-06-21 (latest)** — Added daily-luck (일운) overlay in `sewoon.py` with `_daily_pillar()`, `derive_ilwoon()`, `current_ilwoon_window()`; wired into `engine.py`, `chart.py`, `skeleton.py`, and CLI `--day`. Added `src/saju_engine/prose_scaffold.py` to draft interpretive paragraphs for Day Master strength, 용신, personality, career/wealth, relationships, health, and current time themes; included in skeleton by default with `--no-prose-scaffold` to disable. Added `tests/test_sewoon.py` 일운 cases, `tests/test_cli.py::test_cli_skeleton_with_year_month_and_day`, and `tests/test_prose_scaffold.py` (5 cases). Total pytest suite is now 520.
- **2026-06-21 (latest)** — Built `src/saju_engine/premium_report.py` to generate a 9-section premium client-facing markdown report from a `Chart`: Cover Page, Chart at a Glance (four pillars + element-balance bars + quick reference), Day Master Portrait, Career & Wealth, Relationships, Health & Vitality, Timing, Practical Guidance Summary, and Closing Note. The engine fills deterministic content; interpretive prose is marked `[ENGINE DRAFT — REVIEW REQUIRED]`. Wired `--format premium` and `--output-file` into `src/saju_engine/cli.py`. Added `tests/test_premium_report.py` (9 cases), `tests/test_cli.py` premium cases, and `tests/test_pdf.py::test_build_pdf_from_premium_markdown`. Total pytest suite is now 520.
- **2026-06-21 (latest)** — Added `src/saju_engine/daeun_overlay.py` to compute major-luck (대운) activation overlays: ten-god of 대운天干, branch relationships vs. natal branches, 천간합 with natal stems, element favorability vs. strength-heuristic 용신/기신. Wired into `engine.py`, rendered in `skeleton.py` major-luck table, serialized in `chart.py` JSON export. Added `tests/test_daeun_overlay.py` (4 cases). Total pytest suite is now 520.
- **2026-06-21 (later)** — Expanded validation suite to 93 pytest cases and cross-validation harness to 11/11 checks (the suite is now 520; the harness is 12/12). Added solar-term boundary test (1993-12-07 大雪), Honolulu high-longitude day rollover, leap-month handling, full year-stem/gender 대운 direction matrix. Added new engine overlays (`patterns.py` for grid candidates + 천간합 / 화격 / 종격 detection, `sewoon.py` for annual-luck and monthly-luck activations, `skeleton.py` for engine-driven markdown scaffolds) and CLI `--format skeleton --year YYYY --month MM`. Added 五虎遁 (Oho-dun) lookup for correct monthly pillar stem derivation. Updated `docs/engine-architecture.md`, `docs/cross-validation.md`, and `tasks.md` (the `docs/` files were deleted 2026-06-28).
- **2026-06-21** — Completed professionalization pass: rewrote `src/saju_engine/pillars.py` for correct solar-time + Zi-hour handling, split out `lookup.py` / `stars.py` / `strength.py`, added CLI (`saju-engine`), cross-validation harness (`tools/cross_validate.py`, 11/11 passing at the time, 12/12 today), migrated validation to pytest (`tests/`, 75/75 passing at the time; the suite is now 520), created `docs/engine-architecture.md` and `docs/cross-validation.md` (deleted 2026-06-28), updated `pyproject.toml` / `requirements.txt` / `requirements-dev.txt` / `.gitignore` / `tools/build-pdf.sh`.
- **2026-06-12** — Installed `sajupy 0.2.0` + `reportlab 4.5.1`, verified 10/10 engine tests, symlinked 6 Anthropic community skills, created 8 memory files + `docs/MEMORY.md` index, corrected 7 of 10 per-stem 12운성 tables in `knowledge/06-twelve-stages.md`.
- **2026-06-03** — Built engine, installed Anthropic skills, added Chart→PDF path, fixed Korean `야자시` rule, regenerated Sruthi/Pawan/Harish reports with two pillar corrections for Harish.
- **2026-06-02** — File created with initial priorities 1–6.
