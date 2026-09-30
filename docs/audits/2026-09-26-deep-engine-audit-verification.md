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
| N-3 | P1 | **FIXED** | — | sajupy's 절기 table is imprecise by up to 114 min. **Fixed 2026-09-26**: `_parse_calendar` now reads our own `src/saju_engine/data/solar_terms.csv`, regenerated from an ephemeris (PyEphem VSOP87; calibrated to published KASI/HKO 2024 within ~30 s at minute resolution) by `tools/generate_solar_terms.py`, covering 1899–2101. Month/year pillars and 대운 starting age now use accurate term instants. |
| N-4 | P1 | **FIXED** | `abfc6c1` | Current 대운 selected 1.3–2.4 years early (세수 vs. floored-elapsed-year convention mismatch). |
| N-5 | P1 | **FIXED** *(2026-09-26, decision implemented)* | — | Yin Day Master strength inversion. Strength scoring switched from the 12운성 month-stage to the element-relation 득령 signal (knowledge/09 Step 2); extreme bands widened to 5.0 to keep "extreme" rare and held published verdicts stable. See "Doctrinal decisions" below. |
| N-6 | P1 | **FIXED (industry-standard whole-chart gate)** | — | 조후 overrode 용신 from month branch alone, not chart extremeness. **Implemented 2026-09-26** per the industry standard (정해 만세력/8-codes + 사주플러스 both judge 한난 from the whole chart): a weighted whole-chart temperature score (`climate.climate_temperature`) gates the override via two threshold-free tests — a direction gate for the 寒暖 axis (chart must not clearly oppose its month) and the remedy-dominance guard. Corrects both audit examples, changes zero published deliverables. The *element* stays month/stem-derived (궁통보감; a temperature-derived element would flip Harish's validated Water). See `docs/research/2026-09-26-climate-extremeness-threshold.md`. |
| N-7 | P1 | **FIXED** | `23f92d2` | Web compat path forwarded a chart's raw pre-climate 억부 pick as a "reader-confirmed" override. |
| N-8 | P1 | **FIXED** | `23f92d2` | HTML/Playwright backend rendered markdown with `html: True` — a client name containing `<script>`/`<iframe>` reached Chromium unescaped. |
| N-9 | P2 | **FIXED** *(2026-09-26, decision implemented)* | `10c3706` + follow-up | 문창귀인 갑→해 typo fixed (→사); 천덕귀인 doc/table contradiction fixed (engine already fixed prior session, F-2). 양인격/건록격: the month-branch (월령) case is now the classical grid; the year/day/hour case is relabelled a related-but-distinct pattern. See "Doctrinal decisions" below. |
| N-10 | P2 | **FIXED** | `d95c10b` | Compat cover's "top 3 red flags" were picked alphabetically, not by severity. |
| N-11 | P2 | **FIXED** | `6a106a2` | "This year" prose stated the Gregorian year instead of the 사주 year (사주 year is prior year before 입춀). |
| N-12 | P2 | **FIXED** | 2026-09-26 | Hidden-stem qi weights gave unequal branch totals (왕지 子卯酉 0.6 vs 3-stem 1.0). `_element_counts` now normalises each branch to `_HIDDEN_BRANCH_QI` (0.6) — every branch contributes equal qi, absolute scale unchanged. Resolved verdicts/favorable elements/compat scores unchanged; only the displayed Element Balance percentages shift (e.g. Harish Fire 7.6%→5.6%). |
| N-13 | P2 | NOT STARTED | — | No DST/historical-offset handling; intake default offset still 5.5 in one path per the audit (superseded by F-10 for the two HTML forms — verify `client_intake_form.html`/CLI still need it). |
| N-14 | P2 | **FIXED** | `b63fbfd` | Web app overwrote curated client deliverables, blocked the event loop, and echoed raw exception text to clients. |
| N-15 | P2 | **FIXED** | `8693ca3` + 2026-09-26 | 子-hour boundary disclosed; **절기-proximity disclosure added 2026-09-26** (`pillars._term_boundary_info` → `Chart.term_boundary` → report "⚠ Solar-term boundary note"). |
| N-16 | P3 | **FIXED** | `33fef13` | Remaining F821/F601/F401/F541/F811/F841 lint debt; `ruff check --select F` added to CI. |
| N-17 | P3 | **FIXED** | `c96be17` | `sajupy` was unpinned (`>=0.2.0`); pinned to `==0.2.0` + a test pinning the CSV's own SHA-256. |
| N-18 | P3 | **PARTIAL** | 2026-09-26 | (2) late-2100 forward start-age silent-0 → **fixed** by the N-3 table extension (2100-12-31 now returns 1); (3) `saju_age` now compares the 입춘 **instant** when a birth time is supplied (`saju_age(..., birth_time_str=)`; `saju_year` accepts datetime) → **fixed**. (1) the 1900-01-01 solar-rollback crash originates **inside sajupy** (its table starts 1900-01-01) and needs a sajupy-side or pre-1900 guard — **open**. |
| N-19 | P3 | **FIXED** | 2026-09-26 | `month_season_score` is the live scored 월령 signal (N-5). Balanced-fallback ties are now surfaced via `strength_assessment["balanced_tie_elements"]` instead of silently resolving to Wood. |
| N-20 | P3 | **FIXED** | `c96be17` | Duplicate pairwise 삼형 entries when a branch repeats across pillars. |
| N-21 | P3 | NOT ACTIONABLE HERE | — | `apps/landing-page`'s `src/`/`src/proxy.ts` is not in this repo at all — nothing to fix from inside `saju-engine`. |
| N-22 | P3 | **FIXED** | `33fef13` | Test suite overwrote the tracked client PDF `sruthi-report.pdf` (and two Playwright tests with the same pattern) on every run. |

**Tally:** 18 FIXED, 1 PARTIAL (N-18), 0 research-pending, 1 NOT STARTED (N-13), 1 not actionable
in this repo (N-21). *(Updated 2026-09-26: N-5/N-9 implemented; N-6 implemented with the
industry-standard whole-chart gate; N-3 (ephemeris term table), N-12 (branch qi normalisation),
N-15 (절기-proximity), and N-19 (balanced-tie surfacing) fixed; N-18 partly fixed — the
sajupy-internal 1900 crash remains open. Only N-13 (IANA timezone/DST) is left, plus that N-18
remainder.)*

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

**IMPLEMENTED 2026-09-26.** `strength.py::assess_strength` now scores the month term from
`month_season_score` (the element-relation 득령 table, `_MONTH_BRANCH_SEASON`) rather than
`month_stage_score`; `month_stage_score` is retained and exported as descriptive metadata.
Because the season term (max 2.0 × 1.5 = 3.0) exceeds the stage term's effective ceiling, the
extreme bands were widened from 4.0 to 5.0 so "extreme" stays rare (≈3% of charts) — this keeps
all published/named-fixture verdicts unchanged. Verified: the yin inversion is gone (乙 in 亥 is
now strong=resource, 乙 in 午 not strong; 乙 and 甲 agree by season); all published fixtures
(rm, gurumoorthy, harish, vishnu-priya, sruthi, pawan, mahesh) hold their existing strength
metadata. Re-baselined six synthetic *climate merge* fixtures whose raw pre-merge strength/candidate
moved (their climate-resolved `fe` — the client-facing doctrine — is unchanged); `damp-strong-synth`
was re-pointed to a chart that is genuinely strong under the new scoring. Client-facing effect:
existing `*-report.md` `**Strength:**` reasoning lines name the seasonal baseline by stage and are
now stale; regenerate via `tools/regen_client_reports.sh` (verdicts/favorable elements are
unchanged, so only the reasoning line + N-9 pattern lines move).

### N-6 — 조후 climate-override gate

**Finding:** `climate.assess_climate()` takes only the month branch, so the climate override
applies to every chart born in a non-temperate month regardless of whether the chart itself is
actually climate-extreme — in 9% of sampled charts the prescribed remedy element is already the
chart's most abundant one.

**Investigated:** knowledge/17's own cited source is explicit that the gate should be "사주가 너무
차거나 너무 더우면" (**if the chart** is too cold or hot) — i.e. a whole-chart-extremeness
condition — but no source in this repo (or found by the audit) gives a **numeric threshold** for
what counts as "too cold/hot." Implementing the audit's suggested fix (weigh Fire/Water across
stems and hidden stems, gate on that) would mean inventing that threshold, which is exactly what
Ground Rule 1 says to decline and flag instead of doing unilaterally.

**Decision (user, 2026-09-26): research it more first**, rather than approve a threshold or leave
as-is.

**Research done (2026-09-26)** — `docs/research/2026-09-26-climate-extremeness-threshold.md`.
Findings:
- The **primary classical source** (적천수 滴天髓 §29 寒暖 / §30 燥濕 + 임철초 註) confirms the
  *principle* — a chart must be "過/偏" (extreme/one-sided), not merely born in-season — and even
  says to **withhold** the remedy for absolute excess ("若原局全是极寒...反不宜调候"). It gives
  **no number**.
- Two **independent Korean practitioner sources** give a concrete criterion: month in the season
  **and** a majority of the chart in that temperature class — 네이버/촌노: **≥3 of the 4 branches**
  (month included), with a ≥5-of-8 whole-chart fallback; 사주플러스: **≥4 of the 8 characters**.
- A commercial engine (정해 만세력 / 8-codes) documents the same whole-chart weighted-score method
  but publishes no cutoff — method corroboration only.
- **Measured impact** (4,000 random charts): the branch-weighted gate suppresses **49%** of current
  climate overrides and drops the "remedy already the chart's most-abundant element" rate from
  14.7% to 4.8% of fired. The branch gate corrects the 2010 example; the 1963 example needs the
  separate remedy-dominance guard (option C). Together they would change the resolved 용신 for
  **Harish** (Water→Wood) and **Mahesh** (Fire→Water) — a client-visible move that needs explicit
  approval.

**IMPLEMENTED (industry-standard whole-chart gate), 2026-09-26.** Research established the
industry standard: **정해 만세력 (8-codes)** documents a weighted per-character 한난 score with
month/hour weighted higher ("월지와 시지에 더 큰 가산점"), and **사주플러스** publishes a per-character
한난 table judged "월지 중심" — i.e. the audit's own N-6 recommendation (weigh Fire/Water across the
whole chart). Implemented as `climate.climate_temperature()` + two threshold-free gates:
`is_climate_extreme()` (direction gate on the 寒暖 axis — a hot/cold month whose whole chart clearly
leans the other way withdraws the override) and `is_remedy_dominant()` (remedy already the most
abundant element). `FavorableElement` carries `climate_temperature` / `climate_extreme` /
`remedy_dominant`; knowledge/17 §"The Whole-Chart Extremeness Gate" + knowledge/09 Step 3 document
it. Verified: both audit examples corrected (1963 → Wood, 2010 → Earth); **zero** published
deliverables changed; fixtures `dry-remedy-dominant` + re-pointed `dry-balanced-synth-v2`.

**Why the element stays month/stem-derived:** 궁통보감's 四月辛金 entry prescribes 壬水
**unconditionally**, and Harish's canonical chart is exactly 四月辛金 — deriving the element from the
whole-chart temperature (Harish scores ≈0.0, neutral) would flip his validated Water, violating
Ground Rule 1. Only the *priority* is gated. `_NEUTRAL_TEMPERATURE_MARGIN` is an operational
constant (no engine publishes its cutoff) flagged `[UNCERTAIN]`; it withholds only the ~9% of
climate charts that clearly oppose their month, so a future precise threshold could widen it
without changing current output.

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

**IMPLEMENTED 2026-09-26.** `patterns.py::detect_patterns` now flags `yangin_grid.present` /
`jianlu_grid.present` only when the blade/건록 branch is the **month** branch (월령), and surfaces a
new `yangin_related` block plus a relabelled `jianlu.note` for the year/day/hour case.
`yangin_grid` keeps its key name (backward-compatible) but now means the classical month grid.
`skeleton.py` renders 양인격/건록격 (월령) and the related patterns distinctly. knowledge/07 §3–4
rewritten with both patterns and citations (자평진전 월령 격국 theory; 淵海子平/명리정종/三命通會
branch tables). Regression tests added in `tests/test_patterns.py` (month-is-grid,
non-month-is-related, for both 양인 and 건록).

---

## Not yet started (no investigation this pass beyond the summary table)

- **N-3** (ephemeris-accurate 절기 table) — the single largest remaining item; needs an accurate
  term table shipped as package data (DE440/Skyfield or KASI), replacing sajupy's CSV for term
  lookups while keeping sajupy for day pillar and lunar data. `docs/audits/scripts/
  check_solar_terms.py` (added alongside the audit) is the starting point for verification.
- **N-12** (hidden-stem qi weights) — touches the element-balance percentages, strength verdict,
  `dominant_element`, 종격 thresholds, and compat's element strength; would need a validation
  fixture re-baseline same as N-5/N-6.
- **N-13** (timezone/DST) — the intake-default-India-offset half is already fixed (F-10, prior
  session); the IANA-timezone-as-primary-input redesign and DST-era historical-offset handling are
  not.
- **N-15** (remainder) — a 절기-proximity boundary disclosure, parallel to the 子-hour one already
  added, using the term-candidate list `_independent_year_month_pillar` already builds.
- **N-18** (range-edge crashes), **N-19** (the dead `month_season_score` half is now fixed by N-5;
  the Wood tie-break half remains) — smaller P3
  items, not yet investigated.
- **N-21** — not fixable from inside this repo; `apps/landing-page`'s own source tree (and
  `DEPLOY.md`'s described `src/proxy.ts`) is simply not present here to audit or fix.

## Client-report exposure

Per the audit's own note: N-4 (already fixed) can change an existing report's "Current Major Luck"
headline. **N-5 is now implemented** (verdicts and favorable elements held stable for all published
charts, but the `**Strength:**` reasoning line changed shape and now names the element-relation
baseline instead of the 12운성 stage), and **N-9 is now implemented** (양인격/건록격 pattern lines
can move position). N-6 and N-12 are still open and will change deliverables once implemented.
**All candidate deliverables were regenerated 2026-09-26 (second pass)** via
`tools/regen_client_reports.sh` — verdicts, favorable elements, and compat scores were all
confirmed unchanged; the diff is the N-5 strength/arrival lines plus accumulated F-1..F-16 /
N-series catch-up (Hanja first-use, tier price, 대운수 precision). The regen also exposed and
fixed a flaw in the N-22 regression test (it asserted a clean `git status`, so any legitimate
regen of a tracked deliverable failed it) — the test now asserts unchanged bytes instead.
