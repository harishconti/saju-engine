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
| N-3 | P1 | NOT STARTED | — | sajupy's 절기 table is imprecise by up to 114 min; needs an ephemeris-sourced replacement table shipped as package data. |
| N-4 | P1 | **FIXED** | `abfc6c1` | Current 대운 selected 1.3–2.4 years early (세수 vs. floored-elapsed-year convention mismatch). |
| N-5 | P1 | NEEDS DECISION → **recorded, not yet implemented** | — | Yin Day Master strength inversion. Decision: switch to season/element relation (knowledge/09 Step 2), away from 12운성-stage reading (knowledge/06). See "Doctrinal decisions" below. |
| N-6 | P1 | NEEDS DECISION → **research requested, not yet implemented** | — | 조후 overrides 용신 from month branch alone, not chart-level extremeness. User asked for more research before deciding a threshold. |
| N-7 | P1 | **FIXED** | `23f92d2` | Web compat path forwarded a chart's raw pre-climate 억부 pick as a "reader-confirmed" override. |
| N-8 | P1 | **FIXED** | `23f92d2` | HTML/Playwright backend rendered markdown with `html: True` — a client name containing `<script>`/`<iframe>` reached Chromium unescaped. |
| N-9 | P2 | **PARTIAL** | `10c3706` | 문창귀인 갑→해 typo fixed (→사); 천덕귀인 doc/table contradiction fixed (engine already fixed prior session, F-2). 양인격/건록격 month-branch question: decision recorded (support both, labeled differently), not yet implemented. |
| N-10 | P2 | **FIXED** | `d95c10b` | Compat cover's "top 3 red flags" were picked alphabetically, not by severity. |
| N-11 | P2 | **FIXED** | `6a106a2` | "This year" prose stated the Gregorian year instead of the 사주 year (사주 year is prior year before 입춀). |
| N-12 | P2 | NOT STARTED | — | Hidden-stem qi weights give unequal branch totals (왕지 underweighted by 10–40%). |
| N-13 | P2 | NOT STARTED | — | No DST/historical-offset handling; intake default offset still 5.5 in one path per the audit (superseded by F-10 for the two HTML forms — verify `client_intake_form.html`/CLI still need it). |
| N-14 | P2 | **FIXED** | `b63fbfd` | Web app overwrote curated client deliverables, blocked the event loop, and echoed raw exception text to clients. |
| N-15 | P2 | **PARTIAL** | `8693ca3` | 子-hour boundary now disclosed (compound-edge flag, no false alternate pillar claimed). 절기-proximity disclosure not yet added. |
| N-16 | P3 | **FIXED** | `33fef13` | Remaining F821/F601/F401/F541/F811/F841 lint debt; `ruff check --select F` added to CI. |
| N-17 | P3 | **FIXED** | `c96be17` | `sajupy` was unpinned (`>=0.2.0`); pinned to `==0.2.0` + a test pinning the CSV's own SHA-256. |
| N-18 | P3 | NOT STARTED | — | Range-edge crashes (1900 rollback, silent start-age-0 post-2100, 입춀-day-vs-instant comparison). |
| N-19 | P3 | NOT STARTED | — | `month_season_score` computed but unused in the verdict; balanced-fallback ties always resolve to Wood. |
| N-20 | P3 | **FIXED** | `c96be17` | Duplicate pairwise 삼형 entries when a branch repeats across pillars. |
| N-21 | P3 | NOT ACTIONABLE HERE | — | `apps/landing-page`'s `src/`/`src/proxy.ts` is not in this repo at all — nothing to fix from inside `saju-engine`. |
| N-22 | P3 | **FIXED** | `33fef13` | Test suite overwrote the tracked client PDF `sruthi-report.pdf` (and two Playwright tests with the same pattern) on every run. |

**Tally:** 11 FIXED, 3 PARTIAL, 2 NEEDS DECISION (recorded), 5 NOT STARTED, 1 not actionable in this repo.

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

**Not yet implemented.** This requires: rewriting `strength.py`'s `month_stage_score` term to use
an element-relation lookup instead of `twelve_stage()`, re-baselining the strength/climate
validation fixtures, and reviewing existing client reports whose strength verdict may change
(same review step the audit recommends for N-4/N-6/N-12).

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

**Not yet implemented.** Requires: adding the month-branch check to `patterns.py`'s grid-detection
logic, renaming/re-scoping the existing year/day/hour check to a distinct pattern name, rewriting
knowledge/07 §3–4 to document both patterns with their own citations, and re-baselining any
pattern-dependent validation fixtures.

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
- **N-18** (range-edge crashes), **N-19** (dead `month_season_score`, Wood tie-break) — smaller P3
  items, not yet investigated.
- **N-21** — not fixable from inside this repo; `apps/landing-page`'s own source tree (and
  `DEPLOY.md`'s described `src/proxy.ts`) is simply not present here to audit or fix.

## Client-report exposure

Per the audit's own note: N-4 (already fixed) can change an existing report's "Current Major Luck"
headline. N-5, N-6, N-12 (not yet fixed) can also change existing deliverables once implemented.
No candidate reports have been regenerated as part of this tracker — `tools/regen_client_reports.sh`
should be run and the Quick Reference blocks diffed before re-sending anything, once the doctrinal
items above are actually implemented.
