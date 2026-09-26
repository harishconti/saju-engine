# Engine Audit — Independent Verification & Fix Tracker (2026-09-25)

**Source:** an external Claude Code session ran a from-scratch audit (`docs/audits/2026-09-25-engine-audit.md`
+ `candidates_horoscope/reports/harish/validation-2026-09-25.md`, pushed to branch
`claude/saju-engine-audit-s626hx`, not yet reviewed directly — findings were relayed as text) triggered
by Harish's freshly-regenerated combined report. It recomputed his chart independently (ephemeris-based
solar terms, JDN day pillar, true solar time from the actual hour angle) and cross-checked the engine's
code paths.

**Method for this document:** every claim below was re-derived independently against the live code and
data in this repo — reading the actual source, running the actual computation, or checking the actual
CSV/knowledge-file content — before being marked CONFIRMED. Nothing here is taken on the other session's
word alone. This file is a live tracker: status per item is updated as each is fixed, with evidence.

**Scope note:** the source report also references a 23-item claim-by-claim validation of Harish's report
prose (`validation-2026-09-25.md`) beyond the calculation-layer table already relayed. Only the
calculation-layer table (15 rows) has been seen so far; the interpretation-layer claims are not yet
available to verify. This tracker covers the 13 engine-level findings (E-1 to E-13) plus the
calculation-layer table.

---

## Status legend
CONFIRMED = independently reproduced against live code/data. PARTIAL = core claim confirmed, some
detail unverified or disputed. NOT YET CHECKED = claim relayed but not independently verified.
FIXED = confirmed and corrected, with regression test and evidence linked below.

## Summary

| # | Sev | Area | Status | One-line finding |
|---|---|---|---|---|
| E-1 | P0 | Solar-term timezone mismatch | **FIXED** | `daeun.py::_term_boundary_datetimes` compared a KST-labeled CSV term time against the birth's raw local clock time with zero timezone conversion, and this propagated into a wrong natal month pillar for births far from KST. See fix log below. |
| E-2 | P0 | Hidden-stem order swap (辰戌丑未) | **FIXED** | `lookup.py`'s `HIDDEN_STEMS` had 중기/여기 swapped for all four storage branches; `strength.py` weights them differently (0.3 vs 0.1), so this was a real element-percentage/strength-score bug, not cosmetic. See fix log below. |
| E-3 | P1 | 기신 not plumbed past Quick Reference | **FIXED** (uncovered 5 more dormant bugs in the process) | `_avoid_watch_text` derived 기신/구신/한신 for display only; never wrote back to `strength_assessment["candidate_unfavorable"]`, so every decade/annual/business consumer still saw the placeholder `"—"`. See fix log below. |
| E-4 | P1 | Strength verdict vs. prose | **FIXED** | Confirmed as a UX inconsistency, not an arithmetic bug — the verdict is correctly inside the current `[-1.5, 1.5]` "balanced" band by definition, but the band is wide enough that unqualified directional prose ("drain outweighs support") reads as contradicting a flat "Balanced" label. Fixed by adding a reconciling clause naming what actually pulls the total back to balanced, only for balanced-verdict charts. |
| E-5 | P1 | Balanced-DM 용신 folk heuristic | **CONFIRMED as an architecture risk, not live for Harish** | `yongsin.py` falls back to "least-represented element" for balanced DMs not caught by another rule; for Harish 조후 overrides it (already disclosed in-report). Not fixed here — flagged for any balanced chart the 조후 gate doesn't cover. |
| E-6 | P1 | Annual/decade interaction detector incomplete | **FIXED** | `sewoon.py::_detect_branch_relationship` returned on the *first* match (clash→combine→harm→break→self-punish priority), silently dropping a pair's second, simultaneous relationship; and no 3-branch (삼합/방합) completion check existed at all. See fix log below. |
| E-7 | P1 | Knowledge-base star meanings + stem-clash inconsistency | **PARTIAL — stem-clash fixed; 지살/월살 wording deliberately left alone** | The `01-stems.md` "stems don't clash" vs. `08-luck-pillars.md` "check 천간충" inconsistency is fixed (cross-reference added, no new claim invented). The 지살/월살 meaning correction was **not** applied: my own recollection of the classical distinction (지살 as a travel-adjacent but distinct-from-역마 star; 월살 as 고초살/stagnation rather than romance) has real uncertainty, and the original audit's own sourcing for its claimed corrections was not available to verify against — rewriting a knowledge-base doctrine claim on uncertain memory would violate Ground Rule 1 as much as leaving a possibly-wrong claim in place. Left as an open, documented item for whoever has the classical source to confirm. |
| E-8 | P1 | Relationship section ignores gender | **FIXED** | `relationship_style()` read only `day_branch_main`'s ten-god; no gendered 재성/관성 (spouse-star) scan across the whole chart existed anywhere in `prose_fillers.py`. Fixed by reusing the classical mapping already applied in `compat.py::_gendered_spouse_star_note` (knowledge/11-gunghap.md §G). |
| E-9 | P2 | 격국 named with no 성격/파격 check | **FIXED** | `patterns.py` computed grid-naming (regular_grid) and named ten-god conflicts (상관견관) in total isolation; 정관격 was asserted at "likely" confidence regardless of a same-chart 상관견관. See fix log below. |
| E-10 | P2 | PDF tests hard-fail without `pdftotext` | **FIXED** | `tests/test_pdf.py` called `subprocess.run(["pdftotext", ...])` with no `FileNotFoundError` handling or `skipif` guard, in exactly the 5 functions that shell out to it. Fixed with a `shutil.which`-based `skipif` marker; verified both that the 5 skip when `pdftotext` is unavailable and that the other 7 (which don't need it) still run. |
| E-11 | P2 | Date filter misses 형/자형/원진 | **FIXED (형/자형); 원진 deliberately not added** | `_candidate_day_conflicts` checked only 충/해/파. Fixed for 형 (pairwise three-punishment membership, including the 子卯 2-member special case) and 자형 (self-punishment). 원진 was **not** added — `knowledge/16-date-selection.md` names only 충/형/파/해 as date-selection criteria, so adding 원진 would invent a requirement beyond the cited doctrine (Ground Rule 1). |
| E-12 | P2 | Misc. template-prose defects | **NOT YET CHECKED** | Relayed list (§E-12 in the source report) not yet seen in full. |
| E-13 | P3 | Daeun decade-label display convention | **NOT YET CHECKED** | Claim: Korean apps show 대운수 as 1/11/21… (ordinal start), this engine shows 0-9/10-19… (age-range). Plausible, cosmetic, not yet verified against a reference app. |

## Calculation-layer cross-check (Harish, from the source report's Table 1)

Independently re-run against this repo's own engine (not the external ephemeris) where checkable in-repo:

| Item | External report's independent value | This session's check |
|---|---|---|
| Pillars 壬申/乙巳/辛亥/己丑 | ✅ matches | Already re-validated this session (regression-tested, `test_engine.py`). |
| Solar time 02:59:32 | ✅ matches (LMT −12.24 + EoT +1.77 = −10.5min) | Matches this engine's own `-10.5 min → 02:59` output exactly. |
| Hour boundary: **28 seconds**, not the ~1 minute this session's I7 fix reported | Not yet reconciled | This session's `_hour_boundary_info` rounds to whole minutes (`distance_minutes: int`); the true sub-minute margin (28s) rounds to "0 minutes," which is *more* alarming than "~1 minute," not less — worth a follow-up fix to show sub-minute precision when the margin is this tight. |
| 대운수 ~0.51y (1.53 days), not this session's ~0.6y (1.68 days) fix | Consistent with E-1 | This session's earlier fix (floor-before-divide) was real and correct in isolation, but built on the still-timezone-wrong `_term_boundary_datetimes` result — so the shipped "~0.6/7 months" is itself still wrong. Confirms E-1's downstream impact concretely. |
| Hidden stems of 丑: 己(본) 辛(중) 癸(여), not 己(본) 癸(중) 辛(여) | Consistent with E-2 | Confirmed via `lookup.py` read above. |
| Element balance: Metal 27.8% / Water 25.3% (swapped from this session's Water/Metal) | Consistent with E-2 | Follows directly from the hidden-stem fix once applied. |

---

## Fix log

*(updated as each item is resolved — newest first)*

### E-2 — FIXED (2026-09-25)

- `src/saju_engine/lookup.py::HIDDEN_STEMS` — swapped 중기/여기 back to the classical order for
  辰(戊/癸/乙), 戌(戊/丁/辛), 丑(己/辛/癸), 未(己/乙/丁). The other 8 branches were already correct and
  untouched.
- `knowledge/02-branches.md` — same correction, plus a dated note explaining the swap and its numeric
  (not cosmetic) impact via `strength.py`'s middle/residual weighting.
- `tests/test_lookup.py::test_hidden_stems_for_branch` — updated the 4 hardcoded expected tuples that
  had encoded the bug.
- **Blast radius, verified empirically (not assumed):** ran the full suite after the fix. Only 2 of 956
  tests broke, both synthetic climate-module fixtures (`damp-weak-synth`, `dry-balanced-synth`) whose
  `expected` blocks had been "probe-verified" against the pre-fix engine, i.e. they encoded the bug's
  output as ground truth. No externally-sourced/"certified" pillar fixtures were affected — pillars
  (stem+branch identity) don't depend on hidden-stem role labels, only element-percentage/strength
  outputs do, and apparently no certified fixture asserts those for a 辰/戌/丑/未-heavy chart.
- Fixed both climate fixtures' `expected` blocks to match the corrected (and now classically accurate)
  computation, with dated notes explaining what changed and why:
  - `damp-weak-synth` (four 辰 branches, maximally sensitive to this bug): `strength.verdict`
    weak→balanced. This meant the fixture no longer filled the intended "damp × weak" cell of the
    climate-model validation matrix (`test_val_climate.py::test_band_verdict_matrix_complete`), so it
    now documents that it fills "damp × balanced" instead, and a **new** fixture `damp-weak-synth-v2`
    (1976-04-09 12:00, pillars 丙辰/壬辰/辛卯/甲午 — computed and verified against the corrected engine,
    not hand-guessed) was added to refill the damp×weak cell, preserving the original's
    `climate_agrees: false` demonstration (raw candidate Earth disagrees with climate-prescribed Fire).
  - `dry-balanced-synth`: `strength.candidate` Metal→Water, `fe.climate_agrees` false→true. Verdict
    (balanced) unaffected, so it still fills its intended matrix cell — but it no longer demonstrates
    the "raw candidate disagrees with climate" scenario (climate_agrees is now true). **Not yet
    replaced** — a fresh `dry × balanced × climate_agrees=false` synthetic fixture is an open follow-up
    (lower priority: the cell itself is still covered, just not that specific sub-case).
- Full suite: **957 passed, 10 xfailed, 0 failed** (was 956/10/0 before this fix; +1 from the new
  fixture).

### E-1 — FIXED (2026-09-25)

Two independent sub-fixes, both root-caused to the same underlying issue: sajupy's `calendar_data.csv`
stores 절기 moments in KST, but both sajupy itself (`core.py::_check_term_time`, naive `datetime`
comparison, no conversion) and this engine's `daeun.py::_term_boundary_datetimes` (inherited the same
pattern) compared that KST-labeled time directly against the birth's raw local clock time with zero
conversion. Confirmed against the raw CSV (1992 芒種: `199206051923` = 19:23 KST = 10:23 UTC, matching an
independent ephemeris's claimed 10:21 UTC almost exactly) and against sajupy's own docstrings ("UTC
오프셋 (기본값: 9, 한국 표준시)").

1. **`daeun.py::_term_boundary_datetimes`** now takes a required `utc_offset` parameter and converts the
   KST-stored term time to the birth's own timezone (`local = KST + (utc_offset - 9)`) before comparing.
   Threaded through `starting_age`, `starting_age_days`, `compute_daeun`, `engine.py::_build_daeun`, and
   `premium_report.py::_daeun_starting_age_note` (which now reads the newly-added `chart.utc_offset`
   field — Chart didn't store its own birth timezone as a first-class field before this).
   - **Result for Harish (IST, a 3.5h gap from KST):** the previous session's "~0.6 years / ~1.68 days /
     ~7 months" figure was itself still wrong. The corrected value — 1.5375 days, 0.5125 years, 6.15
     months — independently matches **both** external reviewers almost exactly (one estimated ~0.51
     years/6.1 months via a Beijing-time-based method, the other ~1.53 days via an ephemeris), strong
     triangulated confirmation the fix is right.
   - Test: `tests/test_daeun.py::test_term_boundary_requires_utc_offset_conversion` pins both the
     corrected (1.5375d) and unconverted (1.6833d) values so a future regression can't silently reappear.
2. **New: independent month/year-pillar verification**, `pillars.py::_independent_year_month_pillar`.
   The daeun fix alone only addressed the *starting-age* symptom — the more severe part of E-1 is that
   sajupy's **natal month pillar itself** can be wrong for a birth far enough from KST. Reproduced the
   audit's exact example: 2024-02-04 10:00 **EST** (UTC-5, a 14-hour gap from KST — large enough to flip
   which side of a 절기 boundary the birth falls on, unlike IST's 3.5h gap) — sajupy returned month
   pillar **乙丑**, which does not even fit its own year pillar **甲辰** under the 오호둔 (five-tigers)
   rule (乙 as a 丑-month stem only occurs for a 戊/癸-year, e.g. 2023 癸卯 — never for 甲). That
   internal inconsistency is decisive, independent-of-any-"correct answer" proof of a real bug.
   - New function independently recomputes the Saju year (via the same, now-timezone-correct term
     search, finding the most recent 立춘 at-or-before the birth moment) and the month branch (from
     whichever of the 12 month-opener terms most recently passed), then derives the month stem via the
     standard 오호둔 table. **Only overrides sajupy's raw year/month when they disagree** — for the
     New York case, corrected month pillar is **丙寅**, exactly matching the audit's claimed answer.
   - A disclosure note (`_year_month_correction_note`, mirroring the existing 해-boundary/solar-time
     transparency pattern) surfaces in the report whenever this override fires, naming exactly what
     changed. It never fires for Harish (his 3.5h IST/KST gap isn't enough to flip a boundary) or for
     any KST-adjacent chart.
3. **Blast radius, verified empirically:** ran the full suite after each sub-fix. The daeun-level fix
   broke only the one test whose assertion (`~0.6`) itself encoded the still-incomplete earlier fix —
   updated to `~0.5`/`roughly 6 months`. The month-pillar fix broke only
   `test_solar_term_month_boundary`, whose own comment ("boundary between 11:40 and 11:45 IST") had
   baked in the exact bug — the raw CSV value `199312071141` is 11:41 **KST**, converting to 08:11 IST,
   not 11:41 IST; updated with empirically-verified correct boundary times (08:00→亥, 08:11→子). No
   externally-sourced/"certified" pillar fixtures were affected (none apparently sit close enough to a
   term boundary at a far-from-KST offset to trigger the override).
4. Full suite: **962 passed, 10 xfailed, 0 failed** (up from 957/10/0 after E-2; +5 new/updated tests:
   the daeun timezone-conversion pin, the New York month-pillar regression in both `test_daeun.py` and
   `test_pillars.py`, and the two new disclosure-note tests).

### E-3 — FIXED (2026-09-25), uncovered 5 more dormant bugs in the process

**Root fix:** `_ReportContext.__init__` (`premium_report.py`) used to set `self.unfavorable = sa.get("candidate_unfavorable", "—")` directly — the raw, un-derived `strength.py` value, which is `None` for every balanced/climate-gated chart (`strength.py`'s balanced branch never computes a DM-relative 기신; that formula only applies to strong/weak charts). Extracted the derivation `_avoid_watch_text` already did for display purposes into a shared `_derive_gisin_gusin_hansin(fav)` function, and now call it in `__init__` too, so `ctx.unfavorable` is a real element for every chart, not just the Quick Reference line's display text.

**This exposed a second, independent, more severe bug**, previously dormant because `ctx.unfavorable` could never hold a real value for a balanced chart: **5 separate call sites do `"favor" in status`, which also matches the string `"unfavorable"`** (it contains "favor") — so the moment `period_favorable_status` could actually return `"unfavorable"`, all five silently *inverted* it to "favorable" instead. Found and fixed, all keyed to exact-match against the function's only 3 return values (`"favorable"`/`"unfavorable"`/`"neutral"`) instead of substring search:
- `prose_fillers.py::decade_career_strategy` — decade career-phase framing.
- `prose_fillers.py`'s sustainable-habits period lister (supportive vs. conserving periods).
- `prose_fillers.py::major_luck_theme_row` — decade career/relationship theme.
- `prose_fillers.py`'s current-decade "do/avoid" advice line.
- `premium_report.py`'s Lifetime Decade Roadmap table (`period_favorable_status(p, ctx).lower()` branch) — the table this whole chain feeds; this is the one the original audit actually saw as "Fire decades rated neutral" (it was worse than neutral — post-partial-fix it would have shown "favorable", the exact opposite of correct, before this second fix).
(One further occurrence, `plain_words_timing`, checks `"unfavor" in status` *before* `"favor" in status` via `elif` — already correct by construction; left as-is.)

**A third, distinct issue** (also part of the audit's "Fire years appear in Favorable Windows" complaint, but a different root cause): the Business & Launch Timing section's `### Favorable Windows` table lists **every** year in its 6-year window unconditionally — it was never actually filtered to favorable years, so the heading overclaimed for any "mixed" (i.e. unfavorable-element) year, e.g. Harish's 2026/2027 (both Fire, his actual 기신). Renamed to `### Year-by-Year Launch Timing`, which accurately describes what the table already does (a full-window reference with tailored best-use/watch-out guidance per year), rather than filtering years out of a table whose per-row content is designed to cover the whole window.

**Verified end-to-end on Harish's real chart:** Lifetime Decade Roadmap now shows `challenging` for both Fire decades (0-9, 10-19) instead of `neutral`; the 10-Year Forecast's "Watch Out For" column for 2026/2027 now says "the Fire element drains rather than feeds — slow down" (previously generic "a neutral year for this chart").

Two pre-existing tests had encoded the bug's absence as correct behavior and needed updating (not weakening — both now assert the *more* informative, correct outcome): `test_lifetime_decade_roadmap_honours_override_not_chart_baked_status` (0-9 decade: `neutral` → `challenging`) and `test_balanced_chart_growth_area_has_no_doubled_phrase` (the generic "chart's challenging element" fallback text is dead code now that every chart names a real element — updated to assert the specific named element instead).

Full suite: **962 passed, 10 xfailed, 0 failed** throughout (verified after each of the three sub-fixes).

### E-4 — FIXED (2026-09-25)

`prose_fillers.py::strength_reasoning` — when a chart's verdict is "balanced" but its support/drain
ratio is skewed >1.3x in either direction (the condition that produces the flat "X outweighs Y"
sentence), the function now appends a clause naming what actually reconciles the two: the month-stage
term (weighted 1.5x in `total_score`), which is what pulls the total back into the balanced band despite
the skew. Strong/weak charts are unaffected — there a skew in the verdict's own direction reinforces
rather than contradicts the label, so no reconciling clause is added (verified with a dedicated test).
Note: Harish's own chart no longer exhibits this skew after the E-2 hidden-stem fix (support/drain moved
to 3.0/3.9, just inside the 1.3x threshold) — verified against a different real chart (1970-03-15,
Korea) that does. 2 new tests. Full suite: **964 passed, 10 xfailed, 0 failed**.

### E-8 — FIXED (2026-09-25)

Added `prose_fillers.py::gendered_spouse_star_note`, the single-chart counterpart of `compat.py`'s
existing `_gendered_spouse_star_note` (same classical source, `knowledge/11-gunghap.md §G`: male's
spouse indicator is 재성 wherever it appears in the chart, female's is 관성). Scans `chart.ten_gods`
(all positions, visible and hidden) for the gender-appropriate star and names every position it
appears at, flagging explicitly when it lands in the spouse palace itself (a classically stronger
placement). Appended to `relationship_style`'s existing paragraph rather than replacing it. Verified
against Harish's real chart: correctly finds 정재/편재 at the month stem *and* the day branch's middle
hidden stem (甲) — exactly the placement the audit named ("정재 甲 sits in his spouse palace") — and
correctly names the palace placement. Also verified for a female chart (관성) and for no-gender charts
(note correctly suppressed). 3 new tests. Full suite: **967 passed, 10 xfailed, 0 failed**.

### E-11 — FIXED (형/자형); 원진 deliberately excluded (2026-09-25)

`premium_report.py::_candidate_day_conflicts` now also flags `자형` (self-punishment — candidate day
repeats a natal branch that is itself in `L.SELF_PUNISHMENTS`) and `형` (pairwise membership in the same
`L.THREE_PUNISHMENTS` triad, plus the documented 子卯 2-member special case). Verified against every
qualifying October 2026 day for Harish's actual chart by hand — all 8 exclusions (3/15→형, 4/16→자형,
13/23/25→해, 24→충+형) are individually correct. Feeds both `_section_auspicious_dates` and
`_section_monthly_lucky_dates` (shared function). 원진 (deep-grudge star) was considered and
deliberately **not** added: `knowledge/16-date-selection.md`'s own filter criteria are explicitly
충/형/파/해 plus harmony — 원진 is a real, separately-documented star (`knowledge/07-special-
formations.md`) but is not named as a date-selection filter, so adding it would exceed the cited
doctrine.

Two existing regression tests had their count expectations tied to the pre-fix (충/해/파-only) baseline;
manually re-verified every exclusion for Harish's real October 2026 candidates before updating them —
not just loosened to make the suite pass. 7 new parametrized unit tests. Full suite: **974 passed, 10
xfailed, 0 failed**.

### E-10 — FIXED (2026-09-25)

`tests/test_pdf.py` — added a module-level `requires_pdftotext = pytest.mark.skipif(shutil.which(...)
is None, ...)` marker and applied it to exactly the 5 test functions that shell out to `pdftotext`
(identified by tracing each call site to its enclosing function, not a blanket file-level skip, since
7 of the file's 12 tests don't need it). Verified both directions: normal run still passes all 12; with
`shutil.which` monkeypatched to return `None` for `pdftotext`, exactly the 5 affected tests skip and the
other 7 still run and pass. Full suite: **974 passed, 10 xfailed, 0 failed**.

### E-6 — FIXED (2026-09-26)

Two independent sub-fixes, both in `sewoon.py` (consumed by `derive_sewoon`/`derive_woon`/
`derive_ilwoon` and, via `daeun_overlay.py`, by every 대운 period):

1. **Dual-status pairs silently dropped.** `_detect_branch_relationship(a, b)` used to `return` on
   the first table match, in a fixed clash→combine→harm→break→self-punish order. But
   `knowledge/02-branches.md`'s own "Dual-status pairs" note (added in the 2026-09-20 review) already
   documents that **寅亥** and **巳申** are simultaneously a 육합 (combine) *and* a 파 (break) — "not a
   data error... classical 명리 holds both readings simultaneously." The early-return design meant
   the engine could only ever report one side. Changed the function to return `List[str]` of every
   match instead of the first, and updated all 4 call sites (3 in `sewoon.py`, 1 in
   `daeun_overlay.py`) to iterate the list instead of testing truthiness of a single value. Verified
   against real annual pillars, not synthetic-only: 2022's real 壬寅 sewoon branch against a natal 亥
   now reports both `combine` and `break` (previously `combine` only, per the priority order).
2. **No 3-branch (삼합/방합) completion check existed at all.** Added
   `HarmonyCompletion` (dataclass) + `_detect_harmony_completions(branch, natal_branches)`, grounded
   in `knowledge/02-branches.md` §Three Harmonies / §Directional Harmonies ("When all three appear...
   highly empowered. When two appear... partial empowerment (반합)."). For each of `L.THREE_HARMONIES`
   / `L.DIRECTIONAL_HARMONIES` triads containing the incoming branch, checks how many of the other two
   members are present in the natal branches: 2 → `status="full"`, 1 → `status="half"`, 0 → no hit.
   Threaded through `SeWoonHit.harmony_completions` / `DaeunPeriod.harmony_completions`,
   `chart.py`'s `to_dict()` serialization (`_harmony_completions_dicts`), and
   `prose_fillers.py::annual_activation_note` (the only prose consumer of this overlay layer).
   Verified end-to-end against Harish's real chart (natal branches 申/巳/亥/丑, from his 壬申/乙巳/辛亥/
   己丑 pillars): his real generated report now shows, e.g., 2032's 壬子 sewoon branch fully completing
   亥子丑 (Water/North) 방합 with his natal 亥+丑, and half-completing 申子辰 (Water) 삼합 with his
   natal 申 — both entirely absent before this fix, on a year the report already covers.
3. **Cosmetic fix found while verifying end-to-end:** the half-completion note's own "(반합)" gloss
   collided with the general first-use Hanja-glossary pass (반합 is in `HANJA_GLOSSARY`), producing
   doubled parens "(반합 (半合))" the first time it appeared in a document. Removed the note's own
   wrapping parens (now "— 반합", letting the glossary pass add "(半合)" once) — same pattern already
   used for `combo_hanja` in the same function.
4. **Blast radius, verified empirically:** ran the full suite after each sub-fix; zero pre-existing
   tests broke (the dual-status and triad-completion behavior was previously entirely absent, not
   asserted-wrong anywhere) — all 14 new tests are additive. Full suite: **988 passed, 10 xfailed, 0
   failed** (up from 974/10/0).

### E-9 — FIXED (2026-09-26)

Deliberately narrow, per Ground Rule 1: `knowledge/07-special-formations.md` (the file `patterns.py`
cites throughout) has **zero** occurrences of 성격/파격 doctrine — no general theory of what breaks a
grid is documented anywhere in this codebase, so inventing one would violate the same rule this
tracker has already declined to cross once (E-7's 지살/월살). But `knowledge/05-ten-gods.md` §Ten-God
Conflict Patterns already, explicitly, names what 상관견관 does to a 정관 reading ("상관 directly
clashing with 정관, the classical 'rebellion against authority' pattern") — and `patterns.py` already
implements both halves (`regular_grid`'s 투출 naming, and `detect_tengod_conflicts`'s 상관견관 check)
without ever letting them talk to each other. The fix only wires those two already-implemented,
already-cited detectors together — it adds no new classical claim.

- `patterns.py::_GRID_BREAKING_CONFLICTS` maps `"상관견관" → "정관"` (the one pairing the knowledge file
  actually names). `detect_patterns` now checks, after computing both `regular_grid` and
  `tengod_conflicts`, whether the named grid's ten-god matches a present conflict's target; if so, the
  candidate's `confidence` drops from `"likely"` to `"possible"` and its `note` explains why (파격 risk),
  citing `knowledge/05-ten-gods.md`. No other grid type or conflict pairing is touched — 편인격/식신격/etc.
  are structurally exempt since `_GRID_BREAKING_CONFLICTS` only names 정관.
- **Verified against Harish's real chart** (the exact case the original audit named — "정관격 is
  asserted... independent of the 상관견관/clash facts the same report lists"): his 정관격 (from 癸 투출)
  now correctly downgrades to `possible` with a note naming 상관견관, since his chart carries three 상관
  sources against one hidden 정관.
- **This exposed a second, dormant bug while verifying end-to-end**, same failure shape as E-3's
  "favor"/"unfavorable" substring bug: `prose_fillers.py::regular_grid_narrative` gated strictly on
  `confidence == "likely"` and returned `""` otherwise — since a regular grid could previously *only*
  ever be `"likely"` (nothing downgraded it), this silently dropped the *entire* grid-theme sentence
  the moment E-9 made `"possible"` reachable at all, for every future report with a 정관격+상관견관 chart,
  including Harish's own regenerated report. Fixed by widening the gate to `("likely", "possible")` and,
  for `"possible"`, surfacing the 파격 caveat text itself instead of silently vanishing — verified
  end-to-end: Harish's real report now reads "The engine flags **정관격**... but with a caveat: 파격
  (broken-grid) risk: 상관견관 is also present..." where it previously would have said nothing at all.
- 4 new tests (3 in `test_patterns.py` — downgrade fires, stays `likely` without the conflicting god,
  and confined to the one targeted god only; 1 in `test_prose_fillers.py` — the narrative fix,
  end-to-end against Harish's real chart). Full suite: **992 passed, 10 xfailed, 0 failed** (up from
  988/10/0).

### Remaining: E-5 (documentation-only, no live bug for Harish), E-7 (KB star meanings + stem-clash
inconsistency), E-12 (misc. template prose — never seen in detail), E-13 (daeun display convention —
cosmetic, never independently verified).
