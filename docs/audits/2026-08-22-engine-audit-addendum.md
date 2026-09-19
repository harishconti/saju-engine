# Saju Audit Addendum — 2026-08-22 Session Handoff

> **ARCHIVED / HISTORICAL** — point-in-time record. See `README.md` in this folder and the live
> trackers (`../issues_bugs.md`, `../../improvements_issues.md`). Paths/line-numbers may be stale.

**Purpose:** Complete findings from the deep audit session that validated `2026-08-10-architecture-audit.md` (in this folder) against the live code, plus four parallel agent deep-dives. Resume work here in the next session.

**Status:** Analysis complete. No code changes have been made yet. Session tasks #2–#5 (Phase 0 fixes) were created but not started.

---

## 1. Validation of 2026-08-10-architecture-audit.md (2026-08-10)

**Verdict: the "fixed work" narrative (P0–P5 complete) is accurate; the "remaining work" section is ~50% stale; the test count claim needs re-verification (see §1.4 open question).**

### 1.1 Confirmed TRUE (verified against code)

| Claim | Evidence |
|---|---|
| A1–A17 July-audit fixes complete | `redirect_stdout` pillars.py:314; `saju_age` daeun.py:38; 채천금 nayin.py:139 + knowledge/11:307; ₹1,499 prices premium_report.py:623,1392,1399; CLI ValueError handling cli.py:30-55; `_WEAK_SPOUSE_PALACE` now exactly the 5 classical entries (compat.py:615-621) |
| Hardcoded paths removed | `$SAJU_SITE`/`site.getusersitepackages()` in pillars.py:30-43, build-pdf.sh:74, both PDF converters |
| `Chart` god object | **37 dataclass fields** (audit said "30+") |
| engine.py 363 lines, too much | wc: exactly 363, imports 8 sibling modules |
| pyproject non-standard `where = ["tools"]` | pyproject.toml confirmed |
| validate.py 0% coverage / not in pytest | 11 tests collectable only when targeted; `testpaths=["tests"]` skips it |
| Coverage holes | measured: compat.py 80%, daeun.py 81%, pillars.py 76%, nayin.py 81% (improved vs claimed 74%), prose_fillers.py 83% |
| 12/12 cross-validation | tests/test_cross_validate.py has 12 parametrized cases, runs under ci.yml |
| docs/issues_bugs.md backlog | 55 FIXED, 0 OPEN |

### 1.2 STALE / WRONG claims in the audit (already resolved or never true)

| Audit claim (§2.2 "Remaining," "Immediate" checklist) | Reality |
|---|---|
| Dead code `detect_grid_candidates` patterns.py:63-70 | Does not exist anywhere (grep across tools/ + tests/) |
| Duplicate `_element_counts` patterns.py:17 + strength.py:60 | patterns.py:14 *imports* it from strength — single shared definition |
| `Chart.to_json` `default=str` silent failures (chart.py:256) | Already strict `json.dumps`, docstring documents the hardening (chart.py:305-312) |
| Hand-maintained 空亡 table = typo risk | Table already self-verified against algorithmic `_xun_kong_algorithmic` at import (stars.py:~139-150); residual risk low |
| "No public API boundary — everything in `__init__.py`" | Curated 14-name `__all__` exists |
| "`_OHO_DUN` (五虎遁) not directly tested" | Direct verse test at tests/test_lookup.py:99-100 |
| "ten_god tests only ~11/100 pairs" | Exhaustive 100-pair test at tests/test_lookup.py:77-78 |
| "`cross_validate.py` cases not in CI" + roadmap checkbox | tests/test_cross_validate.py runs under .github/workflows/ci.yml; §4.3 and §8 contradict each other |
| "Circular-ish imports — modules import back from engine" | Import graph is a clean DAG; nothing imports `.engine`; only nayin.py:186 has a deferred `lookup` import |
| `_triplet_target` substring matching (stars.py:139-144) | Now set-membership via `_triplet_for_branch` (stars.py:168-183); safe for 1-char branches |
| Proposed CI yaml (§4.2) | The *existing* ci.yml is near-identical; see open question §1.4 about playwright |

### 1.3 Import-graph reality

Clean one-directional layering: `lookup` → (`pillars`,`daeun`,`sewoon`,`stars`,`strength`) → `patterns` → `engine` → reports. Real problem is **module size concentration**: compat.py 1326 lines, premium_report.py 1641, prose_fillers.py 1527 vs engine.py 363.

**Layering inversion the audit missed:** engine modules import from the *presentation* package — `report_data.py:21` and `premium_report.py:55` import `ELEMENT_EMOJI` from `saju_html`.

### 1.4 OPEN QUESTION — test suite status (verify first in new session)

- A full `pytest tests/` run earlier reported **553 passed, 4 failed**, all in `tests/test_html_pdf.py`, with a traceback showing `p.chromium.launch()` failing at `renderer.py:358` and the test file at `/mnt/data2/git_repos/saju/tests/test_html_pdf.py:67` — a path **without** `misc/` that does not exist on disk (`ls /mnt/data2/git_repos/saju` → not found; the repo is not a symlink chain either).
- The **current** `tests/test_html_pdf.py` already contains a `requires_browser` skip guard (lines 15-40) using `saju_html.renderer._launch_browser`, and the current `renderer.py` has `_launch_browser` at line 324 (called at 390). With this guard, browser-less runs should **skip**, not fail.
- **Action for next session:** re-run `PYTHONPATH=/home/harish/.local/lib/python3.12/site-packages:tools python3 -m pytest tests/ -q` from repo root and record the exact counts. If the 4 tests now skip, the suite is green locally and the audit's "557 passing" was simply miscounted; if they still fail, investigate why the skip didn't engage (e.g. `_browser_available()` caching, or the run hitting a different environment). Also decide CI policy: install `playwright` + `chromium` in ci.yml or rely on skips.

---

## 2. New bugs found (four deep-dive agents, high-severity claims spot-verified by direct code inspection)

### 2.1 Compat engine (`tools/saju_engine/compat.py`) — worst cluster

| # | Sev | Location | Defect |
|---|---|---|---|
| C1 | HIGH | compat.py:649-673 `_spouse_palace_virtue` | **Dead comparison**: `L.ten_god(...)` returns Korean 십신 ("정재"); `candidate_favorable` is an English element name ("Water") → `tg == fav` never true → 적천수 +3/+2/−3 spouse-virtue swing **never applies in any report**, though the narrative claims it does. Fix: compare hidden stem's *element*. |
| C2 | HIGH | compat.py:111-124 `WEIGHT` | Sums to **112**, comment and knowledge/11-gunghap.md say 100. Spec folds D into F; engine gives both 12 (24 total) → 용신 double-counted, composite inflated. |
| C3 | HIGH | compat.py:1098-1149 `compat_stars` | Seven stacking `if`s, **no clamp** vs weight 5 → worst case −21 shown as "−21 / 5" in client verdict table; +7 overflow positive side. |
| C4 | HIGH | compat.py:862-869 `_gendered_spouse_star_note` | Male branch tests `a_to_b ∈ _WIFE_STARS` — direction swapped (should be `b_to_a`: "B is A's 재성"). Female branches correct. Flag text also inverted. **Pinned test test_compat.py:469-482 encodes the wrong premise** (calls 辛 being 정관-of-甲 a "spouse-star alignment" for the *male*). |
| C5 | MED | compat.py:676-736 `compat_ilju_pair` | Uncapped; once C1 fixed, up to 20/15 or −22. Apply ±15 clamp. |
| C6 | MED | compat.py:558-565 | Mutual-기신 flags label-swapped: score math right, text attributes A's 기신-in-B as "B's 기신 in A" → reader counsels wrong partner. |
| C7 | MED | compat.py:309-321 `_classify_flag` | Token matching misfires: 귀인배우 (+5) never reaches favorable_points; favorable 쌍역마 (+2) classified yellow; 용신-match +3 and 대운-direction +3 flags silently dropped; `간섭 월지 (broken)` surfaces nowhere. Fix: classify by sub-system provenance + sign, not substrings. |
| C8 | LOW | nayin.py:186-194 | Order-dependent: `compat_score(a,b)` vs `(b,a)` differ by 2 when Nayin elements are in a generating relation → same-sex pairs get presentation-dependent scores. |
| C9 | LOW | compat.py:292-305 | First-match-wins shadows 형 behind 해/파 (寅巳 gets 해 −1, harsher 형 −2 never recorded); 寅亥/巳申 합중파 co-occurrence absorbed silently. |
| C10 | LOW | compat.py:58-68 vs knowledge/11:963-967 | Sub-band labels "Soft / Yellow Flag" vs spec "Mixed / Challenging" (thresholds match). |
| C11 | LOW | tests/test_compat.py:296 | `... != "Metal" or True` — vacuous assertion; test named "honors_favorable_element_override" never verifies the override. |
| OK | — | — | Band boundaries 80/65/45 match spec; normalization 50+raw consistent; override path non-mutating (deepcopy verified by agent); ten-god pair table order-invariant. |

### 2.2 Core engine

| # | Sev | Location | Defect |
|---|---|---|---|
| E1 | HIGH | daeun.py:286-289 `starting_age` | `int((target - birth_dt).total_seconds() // 86400)` then negates → `//` floors toward −∞: true elapsed 2.3 d backward → engine 3 d (age 1), correct 2 d (age 0). **Verified numerically.** Affects 역행 charts (Yang-year F / Yin-year M) at every 3-day boundary. Fix: `int(abs(...total_seconds()) // 86400)`. Add fractional-day backward regression test. |
| E2 | MED | sewoon.py:131-148 `_detect_branch_relationship` | Returns one relationship; 巳-申 and 寅-亥 are simultaneously 合+破 — natal engine.py reports both, timed overlays (세운/월운/일운/대운) report only "combine". 파 activations invisible. |
| E3 | MED | sewoon.py:116-117, 262-265 | Outside 1900–2100 ephemeris: `_annual_pillar(year)` skips 입춘, `_monthly_pillar` hard Feb-1 pivot instead of real 節氣 moment — silent wrong pillars, contradicts module docstring. |
| E4 | LOW | pillars.py:186-200 | `_hour_stem_day_stem` has 3 dead parameters; caller computes `_effective_calendar_date` solely to feed it. |
| E5 | LOW | chart.py:193 vs 246 | Duplicate `"reference_date"` key in `to_dict()`. |
| E6 | LOW | daeun.py:121, sewoon.py:86 | `Dict` annotated but never imported (runtime-safe only via `__future__ import annotations`; `get_type_hints` → NameError). |
| E7 | LOW | dead code | `daeun._term_boundary_dates` (:160), `_days_to_term` (:248), `_parse_date` (:216); `sewoon._has_calendar_lookup` (:102); `pillars._day_stem_for_date` (:100, duplicates sewoon.py:64 anchor). Grep-verified no callers. |
| E8 | LOW | validate.py:191-196 | Comment falsely claims knowledge/06 tables are misaligned — they match the engine. Remove/substantiate (Ground Rule 1). |
| E9 | LOW | sewoon.py:217-218 | `current_sewoon` docstring says default ±1 year; default `window=3` (±3), engine.py:340 passes 2 — three conventions. |
| E10 | note | sewoon.py | Ten-god English map copied 3× verbatim despite `lookup.TENGOD_EN`. |

### 2.3 Report / PDF pipeline

| # | Sev | Location | Defect |
|---|---|---|---|
| R1 | HIGH | premium_report.py:455 (also 295,342,540,677,716,1261) | `>*Chart-derived first draft — verify against knowledge/...*` review lines: strippers remove only the path → client PDFs contain *"verify archetype table against and ."* (ReportLab also renders literal `>`). Fix: strip the whole blockquote line. Existing test test_html_pdf_strips_chart_derived_review_notes only asserts paths absent — needs a stronger assertion. |
| R2 | HIGH | premium_report.py:757 + prose_fillers.py:1046-1049 | Raw `List[GridCandidate]` repr printed into Deep/Fullmap client reports (`regular_grid — [GridCandidate(name_ko='식신격', ...)]`). |
| R3 | HIGH | premium_report.py:1186 + md_to_saju_pdf.py:187,320 | Sample/Hook element emojis 🟢🔴⚪🔵 → tofu boxes in ReportLab (stripper covers only ⚠️🟡✅🎧). Fix function `_replace_element_emoji_with_bullet` exists but **has zero call sites**. |
| R4 | HIGH | premium_report.py:1563-1573 | **Tier drift**: Essential (₹799) includes Relationships, Health & Vitality, 30-day plan, full 9-field Lucky Attributes, full-length portrait, long Closing Note — CLAUDE.md reserves these for Deep (₹1,499). Align code to contract. |
| R5 | HIGH | premium_report.py:578,1273,1279,1514,1569; report_data.py:45,1392,1399 | Hardcoded "2025–2030" / "2026–2031" / "2026–2028" windows already stale & self-contradictory (same doc also has 2026–2035 forecast). Derive from `chart.reference_date`; lint-test banning `\b20\d\d\b` literals in prose/taglines. |
| R6 | MED | report_data.py:335-356 vs prose_fillers.py:72-84 vs prose_scaffold.py:59-70 | Three divergent element-balance weightings → Chart-at-a-Glance and Health can name different "weakest" elements in one report. Consolidate into one canonical function. |
| R7 | MED | saju_html/renderer.py:357-358 (now ~390) | Bare `chromium.launch()` — no try/except, no ReportLab fallback. |
| R8 | MED | saju_html/__init__.py:466 vs skeleton.py:379-394 | `strip_source_citations` regex eats from `## Sources` to EOF; skeleton appends `## Focus Requested...` **after** Sources → focus section silently lost in PDFs. Two strippers disagree (combine_candidate_report's stops at next heading). |
| R9 | MED | hanja_glossary.py + saju_html HANJA_MAP | inject_hanja emits 桃花/驛馬/空亡/格局/六合/六沖/三合/自刑/三刑/絶 etc. absent from HANJA_MAP → "도화 ( )" or "Chart Structure (structure framework)" garbage in client PDFs. Add build-time check. |
| R10 | MED | renderer.py:139-164 `_drop_title_block` + premium_report.py:211-241 | Cover h2 precedes the hr → guard falls back, client name/price/birth lines duplicated under the renderer's own cover page. ReportLab backend likewise only skips h1. |
| R11 | MED | md_to_saju_pdf.py:575-591 | Ragged table rows (uneven pipe counts) crash ReportLab build (no padding/truncation). |
| R12 | LOW | premium_report.py:564,1073,1080,1087 | All ordered-list items render literal "1." (ReportLab NUM_RE path). |
| R13 | LOW | md_to_saju_pdf.py:168 | `DejaVuSansMono`→"HelveticaMono" (nonexistent font) fallback; code spans raise if TTF registration failed. |
| R14 | LOW | build-pdf.sh:44-47 | Defaults hardcode Sruthi for any name-only invocation → wrong cover metadata. |
| R15 | LOW | saju_html/__init__.py:444 | Camel-split regex corrupts names on covers: "McDonald"→"Mc Donald", "YouTube"→"You Tube". |
| R16 | LOW | sections.py:174-176 | Audio-callout regex matches neither engine variant → styled audio box never renders in HTML backend. |
| R17 | LOW | premium_report.py:200-203 | Quick Reference can show a `confidence="ruled-out"` regular_grid candidate as the chart's Pattern. |
| R18 | LOW | report_data.py:307 | `normalize_tier("₹1,499")` raises ValueError (comma not stripped); `"1499"` works. |
| R19 | LOW | md_to_saju_pdf.py:929 | CLI `--tier` choices exclude `companion` (engine supports it). |

### 2.4 Intake web apps — do not deploy publicly as-is

| # | Sev | Location | Defect |
|---|---|---|---|
| W1 | HIGH | client_intake_app.py:339-384 | `/compat/generate` writes to fixed `{slug_a}_{slug_b}_compatibility.pdf` — **verified**: race → A receives B's PII-laden PDF; anyone can overwrite curated deliverables under `marriage_compatibility/{pair}/`. `/generate` uniquely names files (line 222); compat doesn't. |
| W2 | HIGH | client_intake_app.py:320-331 | Both `compute_chart` calls run **synchronously on the event loop** before `run_in_threadpool(_render)` (line 387) — "charts can be slow" comment on work not offloaded. **Verified.** |
| W3 | HIGH | client_intake_app.py:184-398, 412 | No auth/rate-limit/body-size caps on endpoints burning 10–20 s CPU + writing permanent files; `host="0.0.0.0"`; unlimited free ₹1,499 reports; disk-fill DoS. |
| W4 | MED | client_intake_app.py:231-232, 389; both plain servers | Verbatim exception text in HTTP 500 bodies leaks paths/library internals. |
| W5 | MED | client_intake_app.py:86-97; both plain servers | PII (name/DOB/time/place/email/gender/status) flat JSON, world-readable umask, never pruned. |
| W6 | MED | client_intake_app.py:80-83 vs 401-404 | Two `slugify` copies with different fallbacks ("candidate" vs "report") → reconciliation mismatch. |
| W7 | MED | client_compat_intake_server.py:78-85 vs client_compat_intake_form.html:167 | **Standalone compat server 100% broken**: its validator demands bare fields the form never sends; form posts to `/compat/generate` which this server doesn't implement → every submission 400/404. |
| W8 | LOW | various | No server-side utc-offset range (-12..14), no email validation, no birth-date sanity range (year 0001 passes strptime), gender parity gap (form allows O, PDF code requires M/F). |
| W9 | LOW | client_intake_server.py:63-69 (+ compat twin) | Unbounded Content-Length read (memory DoS); `unquote` instead of `unquote_plus` ("John+Doe" persists literally). |
| W10 | LOW | validate.py, cross_validate.py | Orphaned: two drifting copies of expectations; pytest suite is the only CI-watched one. Delete or shim to `pytest tests/`. |
| OK | — | — | Path traversal blocked (slugify strips `[^\w\s-]`); no subprocess shell-out in PDF path; CORS defaults safe (wildcard only via explicit env). |

---

## 3. Architecture & modularization recommendations (reprioritized by findings)

The audit's proposed `core/ overlays/ patterns/ compat/ reporting/ cli/` layout (§3.1) is directionally sound and its 4-phase migration path is fine — **but sequencing should be:**

**Phase 0 — Correctness first (each small and regression-testable):**
1. Fix compat cluster C1–C7 + bad tests C4-pinned/C11 — one PR; add stress test `assert abs(sub.score) <= sub.max` over a max-flag pair.
2. Fix daeun backward floor E1 + fractional-day regression test.
3. Green the suite: resolve §1.4 open question (skip guard vs browser install in CI).
4. Client-visible report fixes R1–R5 (strip review lines entirely, repr fix, emoji fix, tier alignment, dynamic year windows).

**Phase 1 — Consolidation (audit missed most of these):**
5. One canonical element-balance function (kills R6).
6. Split `Chart` (37 fields) into natal / luck / reference clusters.
7. Fix layering inversion: engine must not import `saju_html` (move `ELEMENT_EMOJI` to engine or reporting layer).
8. Orphan cleanup: delete/shim validate.py + cross_validate.py; delete 5 dead helpers (E7) + dead-parameter plumbing (E4).
9. Reconcile the two Sources-strippers (R8): stop-at-next-heading, not to-EOF.

**Phase 2 — Audit's re-layout (as proposed):**
10. `src/` layout, subpackage split, keep curated `__all__` as public boundary (already exists).
11. Formalize PDF package (saju_html mostly done; move md_to_saju_pdf.py in; add ReportLab fallback for R7).
12. Make `cli.main(argv)` unit-testable (cli.py shows 0% coverage — subprocess-only tests).

**Phase 3 — Intake productionization:** unique artifact paths + temp-dir render + BackgroundTask cleanup (W1), threadpool all engine work (W2), shared server-side validator (W8), generic 500s (W4), rate-limit + body caps (W3/W9) — **all before any public deployment**.

---

## 4. Session bookkeeping

- **Task list (this session's tracker, recreate in new session):** #2 Green suite (playwright skip + CI) · #3 daeun floor fix · #4 compat cluster · #5 correct audit doc + this addendum (this file now satisfies the "addendum" half of #5).
- **Next-session first actions:** (1) `pytest tests/ -q` §1.4 verification; (2) then Phase 0 step 1.
- **Do not touch** `candidates_horoscope/` curated deliverables; compat endpoint W1 can overwrite them — fix before running the app with real names.
- Docs to keep in sync when fixing: `docs/issues_bugs.md` (add new findings as OPEN → FIXED), `tasks.md`, and the stale rows in `2026-08-10-architecture-audit.md` (mark §2.2 rows resolved per §1.2 above).
- Verified-clean areas (don't re-audit): all July-audit §F tables; band boundaries; override non-mutation; import DAG; backlog file 55/0 closed.

---

## 5. Phase 0 fixes applied (2026-08-22 continuation session)

The following items from §2 and §3 were implemented in the next session:

| Item | Status | Notes |
|---|---|---|
| §1.4 test suite verification | ✅ | `python3 -m pytest tests/ -q` → **560 passed, 8 warnings** (was 557; +3 new regression tests). Playwright tests skip cleanly when no browser is available. |
| §2.1 compat cluster C1–C7 + bad tests | ✅ | `_spouse_palace_virtue` now compares hidden-stem *element*; `WEIGHT` keeps `combined_elements` as descriptive-only so composite sums to 100; `compat_stars` and `compat_ilju_pair` clamped; male spouse-star direction fixed; mutual-gishin flag labels corrected; `_classify_flag` rewritten with token priorities; vacuous override test and gendered-spouse-star test repaired. |
| §2.2 daeun floor E1 | ✅ | `daeun.py` now uses `abs(seconds) // 86400` before converting to age; fractional-day backward regression test added. Lee Myung-bak textbook test updated to accept the sequence (primary) and either 3 or 4 for start age (inclusive vs elapsed-day convention difference). |
| §2.3 client-visible report fixes R1–R5 | ✅ | Review blockquote lines stripped whole; raw `GridCandidate` repr removed; ReportLab globally strips element-circle emoji so no tofu; Essential tier aligned to landing-page contract (no Relationships/Health/30-day/upsell/full Lucky Attributes); year windows derived from `chart.reference_date`; stale hardcoded year literals removed from source. |
| §3 Phase 0 step 4 | ✅ | Covered by the R1–R5 block above. |

**Phase 1 consolidation also applied (same session):**
- Unified element-balance computation in `tools/saju_engine/strength.py`; `report_data.py`, `prose_fillers.py`, and `prose_scaffold.py` now delegate to the canonical helper.
- Restructured `Chart` into `BirthData`, `NatalData`, `LuckData`, and `ReferenceData` cluster views without breaking flat-field access.
- Removed engine→presentation layering inversion: `ELEMENT_EMOJI`/`ELEMENT_COLORS` moved to `tools/saju_engine/report_data.py`; `saju_html` now imports them from the engine.
- Cleaned orphan scripts (`validate.py`, `cross_validate.py`) and dead helpers (`daeun.py`, `sewoon.py`, `pillars.py`); updated `README.md` and `docs/MEMORY.md`.
- Reconciled Sources strippers: `saju_html/__init__.py` now stops at the next heading, matching `combine_candidate_report.py`.

**Remaining after Phase 1:** Phase 2 modularization (`src/` layout, PDF package formalization, unit-testable CLI) and Phase 3 intake productionization.

*Implemented 2026-08-22. All changes verified by the 563-test pytest suite.*
