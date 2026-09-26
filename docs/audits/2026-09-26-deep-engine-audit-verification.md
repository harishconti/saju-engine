# Deep Engine Audit — Fix Tracker (2026-09-26)

**Source:** `docs/audits/2026-09-26-deep-engine-audit.md` (N-1 through N-22), an independent
fresh audit against the same baseline (`6255f0b`, after every E-1…E-13 fix) the prior
`2026-09-26 audit F-1..F-16` pass started from, run by a separate session in parallel and merged
via PR #4 (`7cd0960`).

**Method for this document:** every row below reflects a fix actually made in this repo —
root-caused first (systematic-debugging), a failing regression test written and verified RED,
then the minimal fix, then verified GREEN — not a re-statement of the audit's own claim. Full
suite and `tools/run_validation.py` were run after each fix; commit hashes are the source of
truth for exact diffs.

**Baseline commit:** `7cd0960` (PR #4 merge). **This tracker as of:** `10c3706`.

---

## Status legend

FIXED = root-caused, fixed, regression test added, suite + validation gate green.
PARTIAL = part of the finding fixed; the rest documented as remaining below.
NEEDS DECISION = marked **[doctrinal]** by the audit; requires a sourced ruling before any
code/knowledge-file change, per CLAUDE.md Ground Rule 1. Decision recorded where made.
NOT STARTED = not yet investigated or fixed this pass.

## Summary

| # | Sev | Status | Commit | One-line finding |
|---|---|---|---|---|
| N-1 | P0 | **FIXED** *(prior session)* | `3fc4d1f` (F-3) | `client_intake_app.py` crashed on import — undefined `TOOLS_DIR`. |
| N-2 | P1 | **FIXED** | `d57d1ee` | 절기 override compared solar-corrected birth time against civil-clock term instants — corrupted year/month pillars near a boundary. |
| N-3 | P1 | **FIXED** | `b5b4e5d` | sajupy's 절기 table is imprecise by up to 114 min; needs an ephemeris-sourced replacement table shipped as package data. |
| N-4 | P1 | **FIXED** | `abfc6c1` | Current 대운 selected 1.3–2.4 years early (세수 vs. floored-elapsed-year convention mismatch). |
| N-5 | P1 | **FIXED** (decision implemented) | `5fc7d40` | Yin Day Master strength inversion. 월령 input is now the month branch's element relation (knowledge/09 Step 2), applied to all stems; knowledge/06/09 updated first. |
| N-6 | P1 | **FIXED** (option A, user decision) | see fix log | 조후 overrides 용신 from month branch alone, not chart-level extremeness. User asked for more research before deciding a threshold. |
| N-7 | P1 | **FIXED** | `23f92d2` | Web compat path forwarded a chart's raw pre-climate 억부 pick as a "reader-confirmed" override. |
| N-8 | P1 | **FIXED** | `23f92d2` | HTML/Playwright backend rendered markdown with `html: True` — a client name containing `<script>`/`<iframe>` reached Chromium unescaped. |
| N-9 | P2 | **FIXED** | `10c3706`, `60d0f79` | 문창귀인 갑→해 typo fixed (→사); 천덕귀인 doc/table contradiction fixed (engine already fixed prior session, F-2). 양인격/건록격: month branch = classical grid, year/day/hour = distinct non-month pattern (decision implemented). |
| N-10 | P2 | **FIXED** | `d95c10b` | Compat cover's "top 3 red flags" were picked alphabetically, not by severity. |
| N-11 | P2 | **FIXED** | `6a106a2` | "This year" prose stated the Gregorian year instead of the 사주 year (사주 year is prior year before 입춀). |
| N-12 | P2 | **FIXED** (월률분야, user decision) | see fix log | Hidden-stem qi weights give unequal branch totals (왕지 underweighted by 10–40%). |
| N-13 | P2 | **FIXED** | `14d3b9b` | No DST/historical-offset handling; intake default offset still 5.5 in one path per the audit (superseded by F-10 for the two HTML forms — verify `client_intake_form.html`/CLI still need it). |
| N-14 | P2 | **FIXED** | `b63fbfd` | Web app overwrote curated client deliverables, blocked the event loop, and echoed raw exception text to clients. |
| N-15 | P2 | **FIXED** | `8693ca3`, `b5b4e5d` | 子-hour boundary disclosed (compound-edge flag); 절기-proximity (±30 min) disclosure with both-side pillars added. |
| N-16 | P3 | **FIXED** | `33fef13` | Remaining F821/F601/F401/F541/F811/F841 lint debt; `ruff check --select F` added to CI. |
| N-17 | P3 | **FIXED** | `c96be17` | `sajupy` was unpinned (`>=0.2.0`); pinned to `==0.2.0` + a test pinning the CSV's own SHA-256. |
| N-18 | P3 | **FIXED** | `580e9e8` | Range-edge crashes (1900 rollback, silent start-age-0 post-2100, 입춀-day-vs-instant comparison). |
| N-19 | P3 | **FIXED** | `5fc7d40` | `month_season_score` computed but unused in the verdict; balanced-fallback ties always resolve to Wood. |
| N-20 | P3 | **FIXED** | `c96be17` | Duplicate pairwise 삼형 entries when a branch repeats across pillars. |
| N-21 | P3 | NOT ACTIONABLE HERE | — | `apps/landing-page`'s `src/`/`src/proxy.ts` is not in this repo at all — nothing to fix from inside `saju-engine`. |
| N-22 | P3 | **FIXED** | `33fef13` | Test suite overwrote the tracked client PDF `sruthi-report.pdf` (and two Playwright tests with the same pattern) on every run. |

**Tally (updated 2026-09-26, second session):** 21 FIXED, 1 not actionable in this repo (N-21).

---

## Fix log (chronological)

- **`33fef13` — N-16 + N-22.** Added missing `List`/`Dict` typing imports (F821); removed 6
  duplicate translation-map dict keys (F601), grounding each keep/drop choice in the canonical
  source where one existed (knowledge/00-glossary.md's "Generating cycle" for 상생); cleared
  remaining F401/F541/F811/F841 (65 findings, mostly `ruff --fix`, each diff reviewed — one,
  `report_data.py`'s `_STEM_PROFILE` re-export, needed restoring after the auto-fix broke a
  cross-module import). Added `ruff check --select F` to CI. Gave `build-pdf.sh` a
  `SAJU_OUT_DIR` override and pointed `test_pdf.py` + two Playwright tests at `tmp_path` instead
  of the tracked `candidates_horoscope/reports/sruthi/` folder.
- **`d57d1ee` — N-2.** `_independent_year_month_pillar`'s call site in `pillars.py` and
  `_build_daeun`/`premium_report.py`'s precise-starting-age helper now compare the **civil** birth
  date/time against 절기 instants, not the solar-corrected one. Fixed `compute_daeun`'s docstring,
  which had told callers to pass solar time.
- **`23f92d2` — N-7 + N-8.** `client_intake_app.py`'s compat path now forwards only the form
  field itself as a favorable-element override, never a chart's own raw candidate pick.
  `saju_html/renderer.py`'s markdown parser now runs with `html: False` (verified no generator
  relies on raw HTML passthrough except the decade-roadmap HTML-comment markers, whose consumer
  regex was updated to match the now-escaped form); added JS-disabled + non-`data:`-request-blocked
  defense in depth to the Playwright page itself.
- **`b63fbfd` — N-14.** `/compat/generate` now renders into a per-request scratch directory under
  `intake/` instead of the curated `marriage_compatibility/` folder; both `compute_chart()` calls
  moved into the worker thread; unexpected-failure exception text is now logged server-side with a
  generic message returned to the client; `client_intake_server.py` decodes with `unquote_plus`,
  not `unquote`.
- **`abfc6c1` — N-4.** `current_daeun` is now selected by comparing the reference date against
  each period's precise calendar start date (`daeun.first_period_start_date`, converting the
  existing fractional day-count to years via "3 days = 1 year"), not by comparing 세수 against the
  floored elapsed-year `start_age`/`end_age` labels. First implementation attempt used the wrong
  units (days instead of years) — caught by the `sewoon-kdj-1997-daeun-window` validation fixture
  (an externally-sourced fact about Kim Dae-jung's 1997 election-year 대운), not by the unit test,
  which is why the validation gate is run after every fix in this pass, not just pytest.
- **`d95c10b` — N-10.** Compat's top-3 red flags now sort by a severity table grounded in each
  token's actual point delta at its point of origin in `compat.py` (day-branch 육충 −25, ilju_pair
  RED FLAG −12, day-branch 자형 −8, nayin 상충/cross-star 홍양교차 both −5, 간섭 −4 as a dampener),
  not alphabetically.
- **`c96be17` — N-17 + N-20.** Pinned `sajupy==0.2.0`, added a CSV SHA-256 pin test. Deduplicated
  `_derive_branch_relationships`'s pairwise-삼형 loop by branch pair (matching the existing
  `seen_half` pattern already used for 반합 in the same function).
- **`6a106a2` — N-11.** Added `daeun.saju_year(date)` (factored out of `saju_age()`, which already
  computed this internally) and used it for the **displayed label only** in
  `prose_scaffold._current_time_draft` and `premium_report._year_one_liner` — the underlying
  `chart.sewoon` lookups stay keyed on the raw Gregorian year, since that already finds the
  doctrinally-correct pillar (only the year *number* stated alongside it was wrong).
- **`8693ca3` — N-15 (partial).** `_hour_boundary_info` now returns a compound-edge flag
  (`is_zi_boundary=True`) for the 子 (23:00/01:00) edge instead of `None`, without claiming a
  specific (unresolved) alternate hour pillar. The 절기-proximity half of this finding is not done.
- **`10c3706` — N-9 (partial).** 문창귀인's 甲→亥 entry was conflated with 甲's 학당귀인 (a
  different star, its 12운성 장생 branch); corrected to 甲→巳 per the classical mnemonic
  「甲乙巳午報君知, 丙戊申宮丁己雞, 庚猪辛鼠壬逢虎, 癸人見兔」, cross-checked against all nine
  other (unaffected) entries in the same table. 천덕귀인's knowledge-file prose said the target
  "is looked for among the four natal 천간" (stems) while 4 of its 12 table entries are branches —
  corrected the prose to describe the table's actual mixed stem/branch targets (the engine itself
  was already fixed for this in the prior pass, F-2).

- **`b5b4e5d` — N-3 + N-15 (절기 half).** Package-data 절기 table `src/saju_engine/data/solar_terms.csv`
  (12 month-opener terms 1899–2101 to the second, JPL DE440s via Skyfield,
  `tools/generate_solar_terms.py`), replacing sajupy's CSV as the term source. Cross-checked against
  the audit's PyEphem script: median 1 s, ±1 min to 2060, ±3 min by 2100. New `chart.term_boundary` +
  "Solar-term boundary note" for births within 30 min of a term. Also removed the dead `eff_date` left
  by N-2, which had put `ruff --select F` (and so CI) red.
- **`580e9e8` — N-18.** Clear error for the 1900-01-01 solar rollback; `starting_age()` raises
  instead of returning 0; `saju_age()` takes the birth's 사주 year from the year pillar (instant-level
  입춘), not the date.
- **`5fc7d40` — N-5 + N-19.** `strength.month_relation()` (peak 2.0 / own 1.5 / resource 1.0 /
  output·wealth·authority 0.0, same scale as before). Applied to **all** stems, not just yin: the
  "they agree for yang stems" note below turned out to be not quite true (庚 장생 in 巳 and 戊 장생 in
  寅 sit in months whose element controls the DM). Seven synthetic climate fixtures re-probed to keep
  their matrix cells; mahesh-published strength re-pinned. Dead `month_season_score` removed; balanced
  ties surfaced as `balanced_tie`.
- **`60d0f79` — N-9 remainder.** Month-branch blade/건록 = 양인격/건록격 (the month-비겁 regular grid is
  renamed); year/day/hour = `yangin_non_month` (day = 일인) / `jianlu_non_month` (hour = 귀록).
  knowledge/07 §B.3–4 rewritten first.
- **`14d3b9b` — N-13.** `saju_engine.timezones.resolve_utc_offset()` (IANA, DST, historical Korean
  offsets, ambiguous/skipped-hour notes); CLI `--timezone`; web app has no 5.5 default and 400s on an
  unknown zone; forms take .25 offsets; the JSON intake form now collects timezone/offset.

- **N-6 + N-12 (user decisions: "follow the suggestion and the traditional method").**
  **N-12:** branch qi now follows the traditional 월률분야 (月律分野) day shares: every branch = 30 days
  = 1.0, split 초기/중기/정기 (`lookup.WOLRYUL_BUNYA`, `lookup.branch_qi_elements`; table and source in
  knowledge/02 §월률분야). This is used by the natal element balance / strength (`strength._element_counts`
  when given branches) and by the 궁합 union balance (`compat._element_strength`). Natal and 궁합 are
  now on one scale, which resolves knowledge/11 §F's documented mismatch. The 초기 stems missing from
  the simplified 지장간 table (子壬 卯甲 酉庚 午丙 亥戊) count for weight only, not for 투출 or ten-gods.
  **N-6 (option A):** when the month's 조후 remedy is already the chart's most abundant element,
  `favorable_element()` falls back to 억부 with `requires_reader=True` and
  `climate_gate="remedy-already-dominant"` (knowledge/17 and knowledge/09 Step 3 updated first).
  Re-baseline: three synthetic climate fixtures re-probed; dry-balanced-synth-v2 became the N-6 gate
  lock; new cold-balanced-synth fills the cold×balanced cell sruthi-published left; compat fixtures
  harish-manvitha (combined_elements 9→4), -override-b-earth (11→6), -combined-elements, mahesh-vp
  (62/Mixed → 65/Strong) and pawan-sruthi-stale (50→47) re-pinned, with notes saying the published
  reports predate N-12. Client natal impact: only Sruthi's engine strength moves (balanced → weak); her
  reader-confirmed Earth 용신 is unchanged. No client chart hits the N-6 gate.

---

## Doctrinal decisions (Ground Rule 1)

Three items are marked **[doctrinal]** by the audit. Each was investigated against the actual
knowledge files (not taken on the audit's word) before being brought to the user, per Ground Rule 1
("if a question requires a rule that isn't in those files, say so explicitly and decline to invent
one") — in these three cases the files exist but conflict with each other or with the audit's cited
classical source, which is exactly the kind of fork that needs a human decision, not a unilateral
fix.

### N-5 — Yin Day Master strength

**Finding:** `strength.py` weighs the month branch's support via each stem's own 12운성 stage
(음생양사 for yin stems — the backward cycle), which the audit says inverts yin Day Masters: a yin
DM born in its own draining month can read "strong."

**Investigated:** knowledge/06's Twelve-Stages cheat sheet (line 149) explicitly instructs reading
strength from the DM's own 12운성 stage in the month branch — i.e., what the code already does.
But knowledge/09 Step 2 (the actual interpretation-method file, one level up) defines strength from
season/element relation instead ("Is the month branch the Day Master's own element? peak season?")
— a criterion that does **not** depend on stem yin/yang direction, and which the audit's own
6,000-chart sample shows gives a materially different (and more classically-expected) distribution
for yin stems. The two knowledge files genuinely disagree for yin stems (they agree for yang
stems, where the forward 12운성 cycle happens to line up with season anyway).

**Decision (user, 2026-09-26): switch to season/element relation** (knowledge/09 Step 2), moving
away from reading strength off the 12운성 stage table for yin stems. knowledge/06's stage table
stays as-is for its own descriptive purpose (12운성 narrative, 대운/세운 stage readings) — only the
strength *scoring* input changes.

**Implemented in `5fc7d40`.** (Was: requires rewriting `strength.py`'s `month_stage_score` term to use
an element-relation lookup instead of `twelve_stage()`, re-baselining the strength/climate
validation fixtures, and reviewing existing client reports whose strength verdict may change
(same review step the audit recommends for N-4/N-6/N-12).)

### N-6 — 조후 climate-override gate

**Finding:** `climate.assess_climate()` takes only the month branch, so the climate override
applies to every chart born in a non-temperate month regardless of whether the chart itself is
actually climate-extreme — in 9% of sampled charts the prescribed remedy element is already the
chart's most abundant one.

**Investigated:** knowledge/17's own cited source is explicit that the gate should be "사주가 너무
차거나 너무 더우면" (**if the chart** is too cold or hot) — i.e., a whole-chart-extremeness
condition — but no source in this repo (or found by the audit) gives a **numeric threshold** for
what counts as "too cold/hot." Implementing the audit's suggested fix (weigh Fire/Water across
stems and hidden stems, gate on that) would mean inventing that threshold, which is exactly what
Ground Rule 1 says to decline and flag instead of doing unilaterally.

**Decision (user, 2026-09-26): research it more first**, rather than approve a threshold or leave
as-is. Not yet done — this is open, pending that research (candidate next step: look for a
secondary 궁통보감/적천수 commentary source that gives a concrete chart-extremeness criterion,
rather than deriving one from scratch).

**Research done (2026-09-26, second session):** `docs/research/2026-09-26-climate-gate-n6.md`. 적천수
「寒暖」 ("不可過也") and 임철초's commentary (don't judge cold/warm by position alone) support a
chart-level test; no source gives a numeric threshold. Recommended option A: when the remedy element is
already the chart's most abundant element, fall back to 억부 with `requires_reader=True` (ordinal, no
invented number; ~8% of sampled charts). Awaiting the user's choice.

### N-9 — 양인격/건록격 month-branch position

**Finding:** knowledge/07 currently defines 양인격/건록격 as firing when the blade/건록 branch
appears in the **year, day, or hour** pillar (explicitly excluding month). The audit says 자평진전
defines these grids by 월령 (month command) specifically — a different grid-definition convention.

**Investigated:** confirmed knowledge/07's current text word-for-word excludes month ("that branch
appears in the year, day, or hour pillar"). Could not independently verify the 자평진전 citation
itself (no primary source available in this repo) — the audit's claim is plausible (자평진전 is
well known for a 월령-centric 격국 theory) but unconfirmed here.

**Decision (user, 2026-09-26): support both, labeled differently** — keep the month-branch case as
the classical 양인격/건록격 (자평진전 convention), and relabel the existing year/day/hour case as a
related-but-distinct pattern rather than dropping it.

**Implemented in `60d0f79`.** (Was: requires adding the month-branch check to `patterns.py`'s grid-detection
logic, renaming/re-scoping the existing year/day/hour check to a distinct pattern name, rewriting
knowledge/07 §3–4 to document both patterns with their own citations, and re-baselining any
pattern-dependent validation fixtures.)

---

## Still open

- **N-21** — not fixable from inside this repo; `apps/landing-page`'s own source tree (and
  `DEPLOY.md`'s described `src/proxy.ts`) is simply not present here to audit or fix.

## Client-report exposure

Per the audit's own note: N-4 (already fixed) can change an existing report's "Current Major Luck"
headline. N-5 is now implemented: across the eight client charts in `tools/regen/`, only **Mahesh's**
strength verdict changes (balanced → strong; 丑 is a resource month for 庚), and no headline 용신
changes. N-3/N-9 change no client pillars or reported grid names. N-12 changes every report's
Element Balance percentages, Sruthi's engine strength (balanced → weak; reader 용신 unchanged), and
the compat scores Mahesh×VP (62 → 65, Mixed → Strong) and Pawan×Sruthi (50 → 47). No client hits
the N-6 gate.
No candidate reports have been regenerated as part of this tracker — `tools/regen_client_reports.sh`
should be run and the Quick Reference blocks diffed before re-sending anything, once the doctrinal
items above are actually implemented.
