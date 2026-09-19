# Full Engine Architecture Audit — 2026-09-14

**Scope:** every calculation subsystem in `src/saju_engine/` — how each is designed, what's good,
what needs improvement, where it can silently go wrong, and concrete steps to make it more robust.
Written as a companion to the three prior audits (`2026-07-05-engine-audit.md`,
`2026-08-10-architecture-audit.md`, `2026-08-22-engine-audit-addendum.md`) and the 2026-09
validation campaign (`docs/audits/2026-09-engine-validation-report.md`,
`docs/research/2026-09-validation-*.md`). Those documents certify **what matches classical
sources** (194 checks, 189 PASS). This document asks a different question: **is the engine built
in a way that stays correct as it grows, and does it fail loudly or silently when something is
wrong?**

**Method:** full read of `engine.py`, `pillars.py`, `daeun.py`, `sewoon.py`, `lookup.py`,
`strength.py`, `chart.py`; targeted read of `patterns.py`, `stars.py`, `nayin.py`; reference to
this session's already-verified deep audits of `yongsin.py`, `climate.py`, `compat.py`,
`report_data.py`, `premium_report.py`; repo-wide greps for error-handling and code-quality
patterns; external comparison against two open-source BaZi engines found via web search
(**[bazi-analyzer](https://github.com/Tonyyiixn/bazi-analyzer)**,
**[viet-bazi-engine](https://github.com/iZenDeveloper/viet-bazi-engine)**) and Chinese-language
reference material on 大运/起运 remainder handling.

---

> ### ⚠️ Validation revision — 2026-09-14 (later same day)
>
> Every claim in this audit was **independently re-checked against the live tree** before being
> acted on. Of the §2 subsystem claims re-checked, four held up exactly as written (§2.3, §2.5,
> §2.6, §2.12) and four needed correction (§2.1, §2.2, §2.7, §2.11); §4.1's `except Exception:`
> inventory was exact. Four §2 subsections were **not** re-checked this pass and are listed in
> §8.6 as unvalidated rather than confirmed (§2.4, §2.8, §2.9, §2.10 — the last three were
> summaries in the original audit, not new findings). **One section did not survive, and it was
> wrong in a way that inverts its conclusion** — §4.5's module list names three modules as buggy;
> all three are in fact already fixed, while four modules the audit never names contain six *live*
> instances of the very bug §4.5 describes. That section has been rewritten in place (see §4.5),
> and the measurement that establishes its real severity is recorded in **§8 (Validation
> addendum)** — including the finding that the §4.5 "rename the field" recommendation, as
> originally written, **would not have fixed the live defects**.
>
> Five smaller claims were corrected in place: §2.1 (the longitude warning's actual trigger
> condition — and a new finding that it fires on essentially every Korean chart), §2.2 (the
> starting-age docstring is *already* documented — the real gap is narrower), §2.7 and §2.11 (two
> miscounts), and §4.3 (four grounding tables, not five). §5's closing framing — that none of the
> listed items currently produce wrong client output — is also corrected there, because the §4.5
> measurement falsifies it for the top row.
> Corrections are marked inline with 🔁 and carry their evidence. Claims that were verified
> unchanged are marked ✅ in §5. Two findings beyond the original audit are recorded in §8.4: a
> sentinel collision at `daeun.py:238-241`, and the Korean longitude false positive.
>
> **Three claims are deliberately left unvalidated and are listed as such in §8.6** — do not read
> their presence in §2/§4 as confirmation: §2.5/§2.6 threshold sensitivity, §4.4's performance
> ceiling, and §4.6's ephemeris cross-check.
>
> **§9 is new — appended after the §8 addendum, not part of the original audit.** §1–§8 ask whether
> the engine is *correct* and *fails loudly*. §9 asks a different question, raised in a follow-up
> pass: whether each report block emits what `knowledge/` already supports, or a fixed
> simplification of it. Nothing in §9 is a correctness defect in the §4.5 sense — the findings are
> *versatility* gaps, and they are sequenced as their own backlog (V1–V12 in §9.13) **after** §5's
> live defects, which they do not compete with. Four of §9's claims are the sharpest in the document
> and each was verified directly: **7 of the 8 `knowledge/` citations in `premium_report.py` are
> unreachable in client output** (6 reviewer-note bodies plus 1 docstring), and **two knowledge
> files — KB13 wealth and KB16 date-selection — have zero engine coupling** despite the report
> blocks that should consume them existing; then, in the second pass, that **both products ship
> zero client-visible citations** — the compat reporter's 37 mentions all name one file and all
> strip at render (§9.11) — and that **`FavorableElement` computes eight provenance fields of which
> reports render three**, so the 조후-vs-억부 disagreement is calculated, test-pinned, and never
> shown (§9.12). §9.14 records what the pass did not verify: its
> per-block and per-file inventories are *worklist-grade*, not line-verified, and three of its most
> consequential claims were re-read directly while the rest were not.

---

## 1. Architecture overview

```
                        ┌─────────────────────────────────────────────┐
                        │              cli.py / API callers            │
                        └───────────────────────┬───────────────────────┘
                                                  │
                                    engine.py::compute_chart()
                                    (single orchestration entry point)
                                                  │
        ┌───────────────┬────────────┬───────────┼───────────┬──────────────┬─────────────┐
        ▼               ▼            ▼           ▼           ▼              ▼             ▼
   pillars.py       lookup.py    daeun.py     stars.py   strength.py   patterns.py    sewoon.py
  (4 pillars,      (십신/12운성/   (대운        (신살)     (억부         (격국/종격)   (세운/월운/
   solar time,      60-cycle/     direction+                strength)                일운)
   Zi-hour)         relations)    starting age)
        │               │            │           │           │              │             │
        └───────────────┴────────────┴─────┬─────┴───────────┴──────────────┴─────────────┘
                                             ▼
                                   chart.py::Chart (flat dataclass)
                                             │
                              ┌──────────────┼──────────────────┐
                              ▼              ▼                  ▼
                     daeun_overlay.py    yongsin.py          compat.py
                     (활성화 overlay)    (조후+억부 merge,     (11-subsystem
                                          single source        pairwise scoring)
                                          of truth)
                                             │
                              ┌──────────────┴──────────────┐
                              ▼                              ▼
                    prose_scaffold.py /              report_data.py
                    prose_fillers.py                 (career tables,
                    (engine-drafted prose)             lookups)
                              │                              │
                              └──────────────┬───────────────┘
                                             ▼
                          skeleton.py / premium_report.py / compat_report.py
                                  (markdown report generators)
                                             │
                                             ▼
                               src/saju_html/ (PDF backends)
```

**Design pattern:** a **single mutable orchestrator** (`compute_chart()`) calls each subsystem
module as a pure function and writes the result onto one flat `Chart` dataclass
(`chart.py`, 446 lines). Every subsystem module is otherwise **stateless and side-effect-free** —
`daeun.py`, `sewoon.py`, `stars.py`, `strength.py`, `patterns.py` all take primitives in and
return primitives/dataclasses out, with no shared mutable state except two `functools.lru_cache`
memo tables (`sewoon.py::_load_sajupy_calendar`, `daeun.py::_CALENDAR_CACHE`). This is a **good**
architecture for a calculation engine: every subsystem is independently unit-testable (confirmed —
`tests/test_daeun.py`, `test_sewoon.py`, `test_strength.py`, `test_patterns.py`, `test_stars.py`
all exist and construct inputs directly, with no `Chart` object needed), and there is exactly one
place (`engine.py`) where the wiring can go wrong.

**Downstream layering is also clean**: `Chart` → overlays (`daeun_overlay.py`, `yongsin.py`) →
presentation (`report_data.py`, `prose_scaffold.py`, `prose_fillers.py`) → renderers
(`premium_report.py`, `compat_report.py`, `skeleton.py`) → PDF backends
(`src/saju_html/`). Nothing in the calculation layer imports from the presentation layer — a
one-way dependency arrow that the 2026-08-22 audit specifically fixed (moved `ELEMENT_EMOJI` out of
the engine). That fix has held: a repo-wide `grep` for presentation imports in the calculation
modules today returns nothing.

**Ground-truth binding:** every lookup table module docstring names its source
`knowledge/NN-*.md` file, and `lookup.py`'s own module docstring states the rule explicitly: *"Do
not add a table here that isn't backed by a knowledge file."* This is enforced only by convention,
not by tooling (see §4.3), but it is consistently followed in the modules read for this audit.

---

## 2. Subsystem deep dives

### 2.1 Four Pillars + solar time (`pillars.py`, 389 lines)

**How it's calculated:** the module wraps `sajupy.calculate_saju()` for the ephemeris/solar-term
math (1900–2100 lookup table) and then **independently recomputes** the hour branch and hour stem
itself as an auditable cross-check, rather than trusting sajupy's hour pillar directly — see
`_hour_branch()` (a 12-branch table by clock time) and `_hour_stem()` (5-rule 五鼠遁 from
`_HOUR_STEM_START`). The `convention` parameter (`korean`/`chinese`) controls Zi-hour semantics
independently of sajupy's own `early_zi_time` flag, with an extra Korean-specific correction
(`_hour_stem_day_stem`) for the 23:00–23:59 window: sajupy keeps the current day's pillar (야자시)
but the Korean school derives the **hour**-stem from the **next** day's day-stem — a real,
previously-fixed defect (see `docs/MEMORY.md`'s 2026-09-13 entry) now locked by this function.

**What's good:**
- **Double computation as a correctness check** — recomputing the hour pillar from first
  principles instead of trusting the underlying library once is a genuinely strong pattern; it
  would have caught the 야자시 defect immediately if it had existed when the function was written.
- **Geocoding sanity check** (`_warn_if_suspicious_longitude`) — warns to stderr when a
  city-geocoded longitude differs from an explicit `--longitude` or from the UTC-offset's standard
  meridian by more than 5° (~20 min of solar time). This is exactly the class of bug that caused
  carried defect #9 (Harish's 76.33° vs the correct 79.42°) — the warning exists, but see §4.1 for
  why it didn't prevent that defect from shipping in report content. 🔁 **Validated, with a
  precision the original text omitted:** the function opens with `if not city: return`
  (`pillars.py:223`), so this check guards **only the city-geocoding path** — a caller who passes
  `longitude=` explicitly (or a numeric coordinate from the intake form) bypasses it entirely, and
  a caller who passes a *wrong* explicit longitude gets no warning at all. The defect-#9 class it
  was written to catch is a *geocoding* error, and that is exactly the only case it covers.
- **Sub-day precision carried through**: the solar-corrected time (not just the date) is threaded
  into the 대운 starting-age calculation (`engine.py::_build_daeun`), so a birth minutes from a
  절기 boundary is handled at moment-level, not date-level. This matches (and in the day-boundary
  handling resembles) **viet-bazi-engine**'s explicit early-zi/midnight convention toggle — both
  projects treat Zi-hour handling as a first-class, explicit parameter rather than an implicit
  default, which is the right call given how much classical-school disagreement exists here.

**Where it can go wrong:**
- **No independent solar-term verification.** The engine trusts `sajupy`'s bundled
  `calendar_data.csv` for every 절기 boundary (used by both `pillars.py`'s month derivation via
  sajupy and `daeun.py`'s starting-age term lookup) with no cross-check against an external
  ephemeris. **viet-bazi-engine**, by contrast, documents a validated error bound: *"maximum
  observed error: 11 minutes against NAOJ [Japan's National Astronomical Observatory]; 36.84
  minutes against JPL [NASA's Jet Propulsion Laboratory]"* over a 1600–2400 date range. This
  project has no equivalent number — sajupy's CSV could be off by minutes-to-hours for any given
  term and nothing in the test suite would catch it, because the tests validate *consistency*
  (does the engine's own hour recomputation match sajupy's day pillar) rather than *external
  accuracy* (does sajupy's term timestamp match a real ephemeris).
- **The `_warn_if_suspicious_longitude` warning is stderr-only.** It does not raise, does not get
  captured into the `Chart` object, and does not appear anywhere in a generated report. A CLI user
  piping output to a file, or the FastAPI self-service app (which likely doesn't surface stderr to
  the browser), would never see it. This is exactly how defect #9 (Harish's longitude) shipped
  silently into three fixture files despite the warning code existing.
- 🔁 **NEW — the warning fires unconditionally for every Korean chart, which is the engine's
  primary user base.** The standard meridian for a UTC offset is `utc_offset * 15`, so for
  `utc_offset=9.0` (Korea, and the `compute_chart()` default) the standard meridian is **135°E**.
  Korea actually sits at **~127°E**. That is an **8.0° gap against a 5° threshold**, so the
  `abs(geocoded - standard_lon) > 5.0` branch trips on *every* correctly-geocoded Korean city —
  verified by direct call: `compute_chart(city="Seoul", utc_offset=9.0)` emits
  *"geocoded longitude for 'Seoul' is 126.9783°, which is more than 5° from the standard meridian
  135.0°…"*. The underlying cause is that UTC+9's meridian was set for Japan (135°E), while Korea
  keeps the same offset despite lying 8° west of it — a real and well-known quirk of Korean
  civil time, not a data error. **Consequence:** the single warning the audit credits with
  protecting against the defect-#9 class is noise for essentially every chart this engine was
  built to read, and a warning that always fires trains its reader to ignore it. **Fix:** the
  threshold should be measured against the *city's own* timezone meridian, or the check should be
  suppressed when the geocoded longitude is consistent with the country (e.g. Korea 124–132°E at
  UTC+9); alternatively raise the tolerance for offsets whose zone spans an unusually wide
  longitude band. Note this is a *diagnostic-quality* defect, not a calculation error — the
  resolved longitude and the resulting chart are still correct.

### 2.2 Major Luck / 대운 (`daeun.py`, 286 lines) — the subsystem you asked about by name

**How it's calculated**, step by step:
1. **Direction** (`lookup.py::daeun_direction`): Yang year-stem + Male, or Yin year-stem + Female
   → forward (순행); the opposite pairing → backward (역행). Pure table lookup, matches
   `knowledge/08-luck-pillars.md` Part 1 exactly.
2. **Starting age** (`daeun.py::starting_age`): find the nearest of the **12 month-opener 節氣**
   (立春, 驚蟄, 淸明, 立夏, 芒種, 小暑, 立秋, 白露, 寒露, 立冬, 大雪, 小寒 — deliberately *not*
   all 24 jieqi; the knowledge file has a note on this distinction) — the *next* one for forward,
   the *previous* one for backward — then `days_between // 3`.
3. **Content of each period** (`compute_daeun`): step the month pillar ±1, ±2, ±3… through the
   60-cycle (`lookup.py::step_cycle`), one step per 10-year period.

**What's good:**
- **Moment-level, not date-level, boundary comparison.** `_term_boundary_datetimes` parses the
  term's exact HH:MM from sajupy's CSV (`_parse_term_time`) and compares it against the birth
  **datetime**, not just the date — so a birth an hour before or after a 절기 on the same calendar
  day correctly counts toward the opposite term. Many simplified calculators only compare dates.
- **Absolute-value day arithmetic to avoid floor-toward-negative-infinity bugs** — the code
  comment at `daeun.py:244-246` explicitly documents *why* it takes `abs()` before floor division:
  naive floor division on a negative timedelta would round the wrong direction for backward
  (역행) charts sitting at a fractional-day boundary. This is a real, non-obvious correctness
  detail that's been thought through rather than copy-pasted.
- **The single 60-cycle math is centralized** in `lookup.py` and reused by `daeun.py`,
  `daeun_overlay.py`, and `sewoon.py` (`step_cycle`, `cycle_index`, `JIAZI_CYCLE`) — one canonical
  implementation with a self-check (`assert JIAZI_CYCLE[10] == ("甲","戌")` at module load,
  matching sajupy's own anchor). This eliminates an entire class of possible divergent-table bugs.

**Where it can go wrong / robustness gap — the remainder-handling question:**

You specifically asked how this is calculated, so here is the one genuine design gap found: the
code computes `days // 3` (integer floor division) and returns a **whole-year integer**, silently
discarding the remainder. I checked this against the classical convention directly (search query:
*"大运 起运 三天一岁 余数"*): the standard rule, confirmed by multiple independent Chinese-language
sources, is **not** a pure floor — it explicitly converts the leftover 1 or 2 days into **months**
(1 extra day ≈ 4 months; 2 extra days ≈ 8 months), producing a starting age like "6 years 4
months," not a truncated "6 years." `knowledge/08-luck-pillars.md` itself hints at this without
committing to it — its own illustrative example says *"10 days = ~3.3 years,"* i.e., a fractional
value, and then the code returns `10 // 3 = 3`, discarding the `.3` entirely rather than expressing
it as ~4 months.

**Concretely, this means:** for a chart whose birth date sits 1–2 days past an exact 3-day
boundary, this engine's starting age is *up to 8 months younger* than the fuller classical
convention would produce, with no flag anywhere that a remainder was discarded (the return type is
a bare `int`). Since the whole engine (from `current_daeun` selection in `engine.py:328-331` down
to every report's "Current Major Luck" line) treats 대운 transitions as happening on an exact
birthday-anniversary year boundary, this is a **coherent, self-consistent simplification** — it
just isn't the full classical precision, and neither of the two external reference engines
document their own remainder handling either (I checked — **bazi-analyzer**'s README doesn't
address it), so this project is not unusual in the ecosystem.

🔁 **Correction after validation — the gap is narrower than the paragraph above states, and this
recommendation is already partly done.** `daeun.py:224`'s docstring already reads: *"Result is
complete days // 3 (1 day = 4 months, 3 days = 1 year)."* That sentence **is** the classical
month-conversion the section above says is missing — it states the 1-day = 4-month equivalence
explicitly. So the "undocumented as a deliberate scope decision" claim is **stale**: the choice is
documented. What is *genuinely* still missing is only the **residual** half:

- The docstring states the equivalence but never says the **1–2 leftover days are discarded**. A
  reader must compose "complete days // 3" with "1 day = 4 months" themselves to notice that a
  10-day chart returns 3 years and silently drops ~4 months.
- The return type is a bare `int` (`daeun.py:219`), so the discarded remainder is not recoverable
  by any caller.

**Severity is unchanged** (up to 8 months on charts 1–2 days past a boundary), but the fix is
smaller than §5's original item 3 implied — it is a two-sentence docstring addition plus an optional
`remainder_days` field, not a documentation gap to be written from scratch. (After validation this
is §5 **item 5**, re-scoped down; the sentinel collision below took the higher rank as item 4.)

🔁 **NEW — silent-sentinel collision at `daeun.py:238-241`, a more serious find than the remainder
question.** When `_term_boundary_datetimes` returns `None`, the function does this:

```python
if target is None:
    # Fall back: use sajupy's lunar→solar to at least get a sensible
    # approximation, or just return 0 and let the caller flag it.
    return 0
```

The comment says *"or just return 0 and let the caller flag it"* — **no caller flags it.**
Repo-wide, nothing checks for a zero starting age (`grep` for `start_age == 0` in `src/` returns
nothing). Worse, `0` is **also a legitimate value**: a birth exactly on a 절기 moment correctly
yields starting age 0, which `tests/test_daeun.py:81` asserts deliberately
(`test_starting_age_at_exact_term_moment_is_zero`). So the sentinel for *"could not compute"* is
**indistinguishable from a valid answer**, and the one code path that represents a genuine
calculation failure is currently untestable — a test that asserted `start_age == 0` would pass
whether the calculation succeeded or gave up. This is the exact silent-degradation shape §4.1
describes, in the calculation core rather than the presentation layer, and it belongs in the same
fix batch (raise, or return `None`/a sentinel the caller must handle).


**Recommendation (revised after validation):** the docstring half of this is **already
implemented** (`daeun.py:224`), so what remains is (a) one added sentence stating that the leftover
1–2 days are discarded rather than converted, and (b) exposing the discarded remainder as metadata
(`DaeunPeriod` already has room for extra fields) so a reader near a boundary can see how close the
chart is to the next classical month-adjustment, the same way the pillars layer already flags
hour-boundary proximity in `premium_report.py`'s cover-page note. **The higher-priority item in this
section is now the sentinel collision above, not the remainder** — a "could not compute" path that
returns the same value as a valid result is a correctness risk; an undisclosed 4-month rounding is a
precision limit.

### 2.3 Annual / Monthly / Daily Luck (`sewoon.py`, 399 lines)

**How it's calculated:** all three overlays share one shape — resolve a 60-cycle pillar for a
target date, compute its ten-god relative to the Day Master, and check its branch against each
natal branch for 합/충/해/파/자형. The annual and monthly pillars have **two paths**: a solar-term
-aware primary path that looks up sajupy's own precomputed `calendar_data.csv` per exact date
(`_annual_pillar_for_date`, `_monthly_pillar_for_date`), and a **naive fallback** (`_annual_pillar`
— anchor-year modular arithmetic; `_monthly_pillar` — hardcoded `lichun_month=2`) used only when a
date falls outside sajupy's 1900–2100 range.

**What's good:** the primary path is genuinely solar-term-correct (it doesn't approximate 입춘 as
always falling on Feb 4 — it reads the exact date from the ephemeris), and the fallback is clearly
commented as a fallback, not silently presented as equally accurate.

**Where it can go wrong:**
- **The fallback's accuracy is not tested.** `_annual_pillar`'s docstring admits *"the annual pillar
  still belongs to Y-1's cycle year in classical convention [for pre-Lichun births]"* but the
  function's own modular-arithmetic implementation doesn't apply that correction — it purely maps
  `(year - 1984) % 60`. There is no test in `tests/test_sewoon.py` that exercises a year outside
  1900–2100 to confirm the fallback's stated caveat is actually harmless in practice (or to confirm
  it fires at all — a silent, untested code path is a risk by definition). Low real-world impact
  (a client born or asking about a date outside 1900–2100 is rare) but worth a regression test
  given the code already anticipates the edge case in its own comments.
- **`_monthly_pillar`'s `lichun_month=2` fallback** hardcodes the Saju-year start to Gregorian
  February for every year, which is wrong for the ~4-day range where 입춘 actually falls (Feb 3–5
  depending on the year) — again, only reachable outside the ephemeris range, and again untested.

### 2.4 Lookup tables — 십신 / 12운성 / 60-cycle / branch relations (`lookup.py`, 373 lines)

**How it's calculated:** 십신 (`ten_god`) is **derived algorithmically** from a 5-way element
relation classifier (`element_relation`) crossed with stem polarity match/mismatch — not a
hardcoded 10×10 table. 12운성 (`twelve_stage`) is likewise derived algorithmically from each stem's
장생-start branch + direction (`_LONG_LIFE_START`), stepping a fixed 12-stage sequence — not a
hardcoded 120-cell table. This is a **strong design choice**: because both derivations are formulas
over small fixed tables rather than large hand-transcribed tables, there is no way for the "table"
and the "formula" to silently drift apart, which is exactly the failure mode the W3 validation
workstream spent effort ruling out for the *other* large tables (납음, 공망) that genuinely are
hand-transcribed.

**What's good:** `twelve_stage()`'s own docstring states this explicitly — *"the engine derives
12운성 algorithmically ... so the per-stem tables in this knowledge file and the engine's output
are always consistent by construction."* This is the single best piece of defensive design found
in the whole audit: it converts an entire class of potential data-entry bug (mistyping one cell of
a 120-cell table) into a class of bug that's structurally impossible.

**Where it can go wrong:** none found specific to this module — it's small, single-purpose, and
every table traces to a named knowledge file. The one soft spot is that `cycle_index()`'s inner
loop is `O(60)` per call and is called from hot paths (`step_cycle`, used inside `daeun.py`'s
per-period loop and `sewoon.py`'s day-pillar derivation) — at current scale (single-chart, human-
paced report generation) this is irrelevant, but see §4.4 for when it would start to matter.

### 2.5 Day-Master Strength — 억부 heuristic (`strength.py`, 243 lines)

**How it's calculated:** a weighted linear score — `self_score*1.0 + resource_score*0.8 +
month_stage_score*1.5 - drain_score*0.7` — thresholded into `extreme` / `strong` / `balanced` /
`weak` / `extreme_weak` at fixed cut points (±1.5, ±4.0). Element counts weight hidden stems at
0.6/0.3/0.1 (main/middle/residual) vs. 1.0 for visible stems, reflecting that hidden qi is
"submerged."

**What's good:** the module is explicit and unusually honest about its own limits — the docstring
states *"a heuristic, not a classical ruling"* twice, and the function's return dict includes a
`"note"` field carrying the same caveat all the way to any downstream consumer. Both external
reference engines converge on the same 抑扶/억부 (support-suppress) method as their primary
strength model, with **bazi-analyzer**'s own README going out of its way to call it *"one of
several valid traditional approaches, not an uncontested truth"* — near-identical language to this
project's framing. That convergence is reassuring: this project isn't an outlier method choice, and
its self-aware framing matches how the wider ecosystem treats this inherently contested step.

**Where it can go wrong:**
- **`month_season_score` is computed but dead.** It's derived from `_MONTH_BRANCH_SEASON`
  (lines 27–40), returned in the output dict, and documented in the function's own docstring as
  part of the assessment — but a repo-wide grep confirms it is **never read anywhere downstream**
  (not `total_score`, not any report, not any prose filler). A code comment even explains why it
  was excluded (*"D1 fix: month_season_score removed from total"*), but the value is still computed
  and still returned as if it mattered, which is genuinely misleading to any future reader of the
  dict (including, notably, a future audit — this took a repo-wide grep to confirm it was actually
  inert). **Recommendation:** either wire it back in with a documented reason, or delete the dead
  computation and the misleading field, per this project's own "no half-finished implementations"
  convention.
  - **Verified from this repo, not merely asserted:** `grep -rn "month_season_score" src/saju_engine/ | grep -v strength.py` returns nothing.
- **No 합/충/화 (combination/clash/transformation) adjustment to element counts.** The strength
  score is a flat tally of stems by element; it does not discount an element that's been "clashed
  away," nor boost one that's been strengthened by a natal 삼합/육합 forming its element. This is a
  real, documented-nowhere simplification relative to fuller classical practice (where a 합化 that
  actually transforms can meaningfully shift the balance) — worth a `knowledge/`-cited scope note
  the same way `climate.py` and the compat engine's C-none decision both got one this session.
- **Threshold constants (±1.5 / ±4.0) are unsourced magic numbers.** The code comment calls them
  *"tuned to be conservative"* but doesn't say tuned against what corpus, and no knowledge file
  states these exact cut points (strength is a spectrum in classical texts, not a 4-band
  discretization with these specific numbers). The validation campaign's W4 workstream certified
  the yongsin *merge logic* built on top of these verdicts, but did not independently re-derive the
  threshold values themselves against an external corpus — a gap worth naming explicitly since it's
  the literal foundation every downstream 용신/격국/career/compat judgment sits on.

### 2.6 Patterns / Grids — 격국 and 종격 (`patterns.py`, 564 lines)

**How it's calculated:** four independent detectors — regular grid (透出 stem selection from the
month branch's hidden stems), transformation grid (천간합 + season + breaker-strength check),
follower grid / 종격 (dominant-element share ≥ 50%/60% + 득령 + no-통근 preconditions), and
structural notes (전국/편국/삼합국). All are **confidence-graded, not binary** — `detect_special_forms`
returns `"likely"` or `"possible"` with an explicit note explaining *why* it was downgraded (rooted
DM present, not in season, etc.), and the docstring states plainly: *"All candidates are flags for
the reader; the engine does not rule."*

**What's good:** this is the most epistemically careful module in the engine. Every classical
precondition from `knowledge/07-special-formations.md §B1` is checked individually and reported
individually rather than collapsed into a single opaque score — exactly the shape CLAUDE.md's
Ground Rule 2 ("no speculation … say so explicitly") asks for, implemented in code rather than
left to the reader's memory.

**Where it can go wrong:**
- **The 50%/60% dominant-share thresholds are, like strength.py's, unsourced magic numbers** — no
  citation to a specific classical percentage. This class of finding recurs enough across
  `strength.py` and `patterns.py` that it's worth treating as one systemic gap (§4.2), not two
  separate ones.
- `_grid_stem_by_tuochul` (regular-grid stem selection) was read only at the docstring level for
  this audit given time constraints — it's flagged here as **not yet re-verified** in this pass and
  should be first in line for the next subsystem-focused audit.

### 2.7 Stars — 신살 (`stars.py`, 559 lines)

Surveyed at the structural level (function list) rather than fully read this pass. Implements
~15–20 individual star derivations (공망 via two paths — an algorithmic 60-cycle method and a
lookup-table method, cross-checked per the 2026-07 audit's regression test — plus 홍염, 양인, and
the 십이신살 set added per the 2026-07-05 audit). **Not independently re-verified in this pass**;
the 2026-07-05 audit already covers correctness for the classical stars implemented, and W3's
validation campaign covered 공망 (6 순 blocks, 56-entry fixture set). Flagged for the next
audit pass along with `patterns.py`'s regular-grid stem selection.

🔁 **Miscount corrected on validation.** "~15–20 individual star derivations" understates the
surface. Measured: `stars.py` holds **10 module-level `def`s** (only ~6 of which are star rules —
`_xun_kong_algorithmic`, `_xun_kong`, `_hongyeom`, `_yangin`, plus the `_triplet_*`/`_matched_pairs`
helpers), and `derive_stars()` emits **24 distinct star keys** at runtime (verified by computing a
chart and enumerating `chart.stars`): `annual_bane`, `canopy`, `deep_grudge`, `disaster_star`,
`earth_bane`, `general_star`, `ghost_gate`, `heaven_bane`, `heavenly_noble`, `heavenly_virtue`,
`hongyeom`, `kong_mang`, `literary_star`, `lost_spirit`, `monthly_bane`, `monthly_virtue`,
`peach_blossom`, `post_horse`, `robbery_star`, `saddle_star`, `six_harm_bane`, `sky_hero`,
`white_tiger`, `yangin`. The structural point stands — most of those 24 come from **data tables
driven by `_triplet_target`/`_matched_pairs`** rather than 24 hand-written functions, which is the
same formula-over-table strength §2.4 praises, and it means a line-by-line function review would
reach only a quarter of the output. **The next pass should audit the 24 emitted keys against
`knowledge/` tables, not the 10 functions.**

### 2.8 Favorable Element / 용신+조후 (`yongsin.py`, `climate.py`) — summary

Already exhaustively audited and fixed this session (see `docs/MEMORY.md`'s "Post-campaign fix
wave" entries and Claude's own `saju-open-defects-triage` memory for the full record). Design is
sound: a single `favorable_element(chart, override)` resolver merges 억부 (strength.py's raw
verdict) with a conservative 3-band 조후 override (`climate.py`: 巳午未→Water, 亥子丑→Fire, else
none) and an optional reader override, in a documented precedence order. The one architectural
lesson worth restating here because it generalizes: **every consumer of the favorable element must
call the resolver, never read `strength_assessment["candidate_favorable"]` directly** — three
separate modules (`premium_report.py`, `report_data.py`, `compat.py`) independently made this exact
mistake at different times, which is a strong signal that the *raw* field should not be as easy to
reach as the *resolved* one. See §4.5 for a concrete API-shape recommendation that would have
prevented all three instances structurally instead of catching them one at a time.

### 2.9 Compatibility / 궁합 (`compat.py`, 1483 lines) — summary

Already exhaustively audited this session (11 sub-systems A–K, weight table, the 육합 dead-code
fix, the C8 nayin-symmetry fix, the C9 삼형-priority scope decision). The one point worth adding
for this architecture pass: at 1483 lines, `compat.py` is the second-largest module in the engine
and mixes three concerns in one file — pairwise scoring math, narrative-string generation, and the
`_canonical_nayin_pair`/`_branch_pair_lookup` plumbing helpers. It has weathered three real bugs in
as many months (육합 arity, nayin asymmetry, 삼형 priority) — not evidence the code is bad, but
evidence the module has outgrown a single-file shape. **Recommendation:** if another compat-scoring
defect surfaces, that's the trigger to split scoring (`compat_score.py`) from narrative
(`compat_narrative.py`), not before — premature splitting here would just move the coupling
around without reducing it.

### 2.10 Nayin (`nayin.py`, 261 lines) — summary

The 60-jiazi → 30-nayin category table (`JIAZI_TO_NAYIN`) is a real, correctly-sourced classical
table (`knowledge/11-gunghap.md §C`) and is not in question. The separate 900-cell **nayin-pair
relation matrix** (which of the 30×30 category pairs count as 상합/상충/상형/…) remains on the
documented "element-grammar-fallback" — a real 서전구미록 30×30 published table was never located,
so the engine derives pair relations from the five-element generating/overcoming cycle instead.
This is already flagged in the module's own docstring and in `docs/MEMORY.md`'s Active Wishes list
as an open item ("Populate the 30×30 Nayin pair table from a published source"); nothing new found
here, included for completeness.

### 2.11 Presentation layer — `report_data.py`, `premium_report.py`, `prose_scaffold.py`,
`prose_fillers.py`, `skeleton.py` (summary; ~5,300 lines combined)

This is the largest part of the codebase by line count and the part with the most `except
Exception:` blocks — 🔁 **9 of 13 repo-wide, not 10** (see §4.1). Verified on validation by
enumerating every `except Exception:` in `src/`: `prose_fillers.py` 6 + `premium_report.py` 3 = 9
inside the five files this section names; the remaining 4 are `compat.py` 3 (audited in §2.9) and
`cli.py` 1. The original "10" appears to have counted a file outside this section's own list. It
was not re-read line-by-line this pass beyond the two files already deeply audited this session
(`report_data.py`, `premium_report.py`). The architectural shape is sound (engine data in,
markdown prose out, tier-gated sections), but its size and its exception-handling density make it
the highest-risk area for *silent* wrongness (a caught exception that degrades gracefully to a
generic sentence, rather than a crash a test would catch) rather than *loud* wrongness (a crash).
See §4.1 for the concrete recommendation.

🔁 **One correction to the "highest-risk area" framing.** This section is the highest-risk area
for *silent degradation* — but validation found the highest-risk area for *silently wrong
numbers* to be §4.5's two-channel read sites, which sit in **`daeun_overlay.py`,
`prose_scaffold.py`, and `skeleton.py`** — the latter two inside this section, the former not.
The distinction matters for prioritization: a degraded exception produces a vague sentence a
reader can spot, while a raw-vs-resolved divergence produces a **fluent, confident, wrong**
sentence (measured at 18.8% of charts — see §4.5 and §8). Severity ordering should follow the
second, not the first.

### 2.12 Validation harness (`validation.py`, 1296 lines) — meta-layer

Not re-audited here — it was built, exercised, and independently re-verified extensively earlier
this session (194 checks certified, gate re-run multiple times). One architecture note for
completeness: it is the single largest module in the engine (1296 lines) and, being a
meta-validation tool, is *not itself covered by the fixture-driven validation it runs* — its own
correctness rests entirely on `tests/validation/test_val_*.py` and this session's manual
independent re-measurement discipline (never trusting a subagent's reported numbers without
re-running the gate). That discipline is a process control, not a code control — worth eventually
backing with a lighter-weight structural self-test (e.g., a test asserting `_GATE_HISTORY`'s total
matches the sum of its rows) so the next person maintaining this file has a safety net that doesn't
depend on remembering to re-run everything by hand.

---

## 3. What's good — engine-wide strengths

1. **Formula-over-table wherever possible** (§2.4) — 십신 and 12운성 are derived, not
   transcribed, eliminating an entire bug class for the tables that matter most.
2. **Confidence-graded, not binary, classical judgments** (§2.6) — 격국/종격 candidates carry
   `"likely"`/`"possible"` plus an explanation, matching the project's own epistemic ground rules
   in code, not just in prose instructions.
3. **Self-auditing solar-time layer** (§2.1) — independently recomputing the hour pillar rather
   than trusting the underlying library once.
4. **A real, working single-source-of-truth pattern for 용신** (§2.8) — even though three modules
   violated it independently before being caught, the *pattern itself* (one resolver function,
   documented precedence) is correct; the violations were a symptom of the raw field being too
   easy to reach, not of the pattern being wrong.
   🔁 **Validation qualifier:** the *pattern* is a genuine strength and this item stands — but the
   "three modules violated it before being caught" framing reads as a closed incident, and it is
   not. Validation found **six further live violations** (§4.5), so the pattern's correctness has
   not been sufficient to keep consumers on the resolver path. The strength is real; the
   enforcement around it is what's missing, and §4.5 now recommends fixing the six read sites
   *before* the defensive rename so the correctness fix is not deferred behind a review aid.
5. **Honest, load-bearing self-doubt** — `strength.py`'s `"note"` field, `patterns.py`'s
   `[UNCERTAIN]` tagging, `nayin.py`'s fallback-grammar docstring, and `climate.py`'s
   scope-limit docstring all carry their own caveats *in the data*, not just in separate
   documentation that a report-writer could forget to consult.
6. **Clean one-way layering** — calculation modules never import from the presentation layer
   (verified by grep this pass); the 2026-08-22 architecture fix has held.
7. **Genuinely good external alignment** — the two comparable open-source engines found this pass
   independently converge on the same 抑扶 primary strength method and the same "explicit,
   selectable Zi-hour convention" design this project already has. This project is not out on a
   limb methodologically.

## 4. Cross-cutting risks and concrete recommendations

### 4.1 Silent-failure risk in the presentation layer (highest priority)

13 bare `except Exception:` blocks exist outside the calculation core, concentrated in
`prose_fillers.py` (6), `compat.py` (3, all narrative-string helpers, not scoring),
`premium_report.py` (3), and `cli.py` (1). 🔁 **The `cli.py` site was missing from the original
breakdown, which listed only 12 of the 13** — the total was right, the enumeration was not. Every
one inspected this pass degrades gracefully to a safe placeholder
(`"—"`, an empty list, a generic sentence) **with no logging** — so a genuine bug (a typo'd lookup
key, an unexpected `None`, a future refactor that breaks an assumption) would silently ship a
slightly-worse-but-plausible-looking sentence into a paid client PDF rather than crash a test or
surface anywhere a developer would see it.

**Note on scope:** these 13 are the *silent-degradation* risk. Validation found a separate and
higher-severity *silently-wrong-number* risk in the same layer — six live raw-field reads, §4.5.
Both live in the presentation layer, but only §4.5 currently produces incorrect client output.

**Recommendation:** this is not "remove the try/except" — graceful degradation in a report
generator is the right instinct. It's "log before falling back." A one-line addition —
`logger.warning("…", exc_info=True)` inside each `except Exception:` — turns 13 silent risk points
into 13 observable ones at near-zero cost, and would have shortened this session's own defect
hunts (several of which involved manually re-deriving *why* a value was wrong, when a log line
would have pointed straight at the swallowed exception).

### 4.2 Unsourced magic-number thresholds (medium priority, recurring pattern)

Found independently in `strength.py` (±1.5/±4.0 verdict bands) and `patterns.py` (50%/60%
dominant-share thresholds for 종격) — both are "tuned to be conservative" per their own comments,
neither cites a specific classical or corpus-derived source for the exact cut point. This isn't
necessarily wrong (some thresholds genuinely have to be chosen, not derived), but it's currently
indistinguishable, by inspection, from an untested guess. **Recommendation:** the next validation
workstream (if the campaign resumes) should treat "does this threshold move any of the 8 canonical
charts' verdicts if nudged ±10%?" as a standard sensitivity check — the same technique the C9/육합
investigation already used successfully this session (`/tmp/variant.py`-style parameter sweeps) —
and record the answer next to the constant, the same way `climate.py`'s docstring now records its
own deliberate scope choice.

### 4.3 The "no table without a knowledge citation" rule is convention-only

`lookup.py`'s docstring states the rule; nothing enforces it mechanically. `tests/
test_knowledge_grounding.py` (added 2026-09-08 per `tasks.md`) checks this for `report_data.py`'s
🔁 **four** interpretive tables specifically — not five, as originally stated. Verified by reading
the test module's imports: it pulls exactly `_CAREER_DOMAINS`, `_ELEMENT_ASSOCIATIONS`,
`_ELEMENT_ORGAN_ORGANS`, and `_GROUNDING_PRACTICES` from `report_data`, across 4 test functions.
The correction slightly *strengthens* the finding rather than weakening it: the grounding test
covers four named tables by explicit import, so **any table added to `report_data.py` later is
uncovered by default** — the test enumerates its subjects rather than discovering them. It does
not cover the calculation-layer lookup tables audited here. **Recommendation:** extend that same
grounding test (or a lightweight variant of it) to `lookup.py`, `strength.py`'s weight tables, and
`patterns.py`'s threshold constants, so a future edit that adds an unsourced number fails a test
instead of waiting for an audit to notice. When doing so, prefer a discovery-based sweep
(introspect `report_data`'s module-level dicts, assert each has a citation comment) over four more
hand-added imports — otherwise the same coverage gap reappears at the next table.

### 4.4 No performance ceiling has been tested, and one exists

`lookup.cycle_index()` is `O(60)` per call via linear scan and sits in hot loops
(`daeun.compute_daeun`'s per-period stepping, `sewoon`'s per-window day-pillar derivation). At
today's usage pattern (one chart, human-paced report generation, occasional compat pairs) this is
immaterial. It would start to matter if this engine were ever used for **batch** work — e.g., the
kind of multi-thousand-chart sensitivity sweep §4.2 just recommended, or a hypothetical future
API/MCP surface (`improvements_issues.md` §10 already flags an API as a P3 "only if triggered"
item). **Recommendation:** no code change now; if batch usage becomes real, replace the linear scan
with the `O(1)` closed-form `(stem_idx * 6 - stem_idx // 2 ...)` 60-cycle index formula (standard
CRT-style derivation) or a precomputed dict — cheap fix, not worth doing speculatively today per
this project's own "don't design for hypothetical requirements" convention.

### 4.5 The two-channel favorable-element bug class is a design smell, not just three bugs

> 🔁 **This section's module list did not survive validation — it is wrong in a way that inverts
> its conclusion, and its recommendation is therefore insufficient. Rewritten in place.**

Three independent modules read the raw `strength_assessment["candidate_favorable"]` field instead
of calling `yongsin.favorable_element()` — found and fixed one at a time, on three different days,
by three different discoveries (`compat.py` mid-climate-implementation, `report_data.py` during
the validation campaign, `premium_report.py` this session). That's a pattern, not a coincidence: a
correct-but-inconvenient API (call a resolver function) sitting next to an incorrect-but-convenient
one (read a dict key directly) will keep getting the wrong one reached for under time pressure.

**🔁 Correction 1 — the three named modules are all already fixed, and the live reads are in
modules this section never names.** A repo-wide grep for `candidate_favorable` on validation day
found:

| File | Status | What is actually there |
|---|---|---|
| `premium_report.py` | ✅ **fixed** | comments/docstrings only — no live read |
| `report_data.py` (`:463`, `:504`) | ✅ **fixed** | comments/docstrings only |
| `compat.py` (`:50`, `:1407`) | ✅ **fixed** | comments/docstrings only |
| `daeun_overlay.py:76` | ❌ **live raw read** | `fav = strength_assessment.get("candidate_favorable")` → drives per-대운 `favorable_status` |
| `skeleton.py:259` | ❌ **live raw read** | renders `- **Candidate 용신**: {sa['candidate_favorable']}` into the scaffold |
| `prose_scaffold.py:73` | ❌ **live raw read** | `_strength_draft` — "candidate 용신 of **X**" in the strength paragraph |
| `prose_scaffold.py:116` | ❌ **live raw read** | `_yongsin_draft` — the entire 용신/희신 paragraph |
| `prose_scaffold.py:169` | ❌ **live raw read** | `_career_draft` — "fields aligned with the favorable element **X**" |
| `prose_scaffold.py:307` | ❌ **live raw read** | `generate_plain_words` `ctx["favorable"]` → 5 downstream prose-filler callouts |
| `cli.py:165` | ⚠️ **arguable** | `Favorable candidate: {…}` — the label literally says *candidate*, so this may be intentional |

So the audit's own summary sentence for this class ("three modules… all fixed") is stale in the
direction that **understates** the defect: three were fixed, but **six live read sites remain**
across four modules the audit never inspected for this pattern. The class was not closed; it moved.

**🔁 Correction 2 — the severity was never measured, and it is much larger than "three bugs"
implies.** The audit asserted a design smell and left the blast radius unquantified. Measured this
pass over **2,016 charts** (a date sweep with the engine's own `compute_chart`, comparing the raw
field against `yongsin.favorable_element()` on each): **380 charts (18.8%) diverge.** Verdict
distribution across the sweep: `balanced` 926, `strong` 570, `weak` 350, `extreme` 166,
`extreme_weak` 4. **Every single divergent chart has `method == 'climate-balanced'`** — i.e. the
divergence is fully explained by the 조후 override, and the two channels agree everywhere else.
Examples: 1970-01-03 (子, balanced, raw **Wood** → resolved **Fire**); 1970-01-07 (丑, balanced,
raw Water → resolved Fire); 1970-05-23 (巳, balanced, raw Wood → resolved Water); 1970-06-11
(午, balanced, raw Wood → resolved Water).

The derived rule, exact and testable:

```
resolved ≠ raw   iff   reader_override_favorable is set
                  or  ( verdict == "balanced"  and  month_branch ∈ 巳午未 / 亥子丑 )
```

End-to-end confinement confirmed by contrast: a 1990-06-11 chart (month branch 午, verdict
**strong**) gives RAW = Earth / RESOLVED = Earth via `strong-dm-drain` — the channels agree outside
the climate band, so the defect is confined to `balanced` + climate-band months and does **not**
leak into ordinary strong/weak charts. That confinement is what makes the 18.8% figure credible
rather than alarming: it is a large fraction of a specific, identifiable band, not a diffuse
uncertainty everywhere.

**🔁 Correction 3 — the recommended fix (rename only) does not fix the live defects.** §4.5 as
written recommends renaming the raw field so direct reads self-flag. That is a reasonable
*prevention* measure, but it is not a *remedy*: a rename makes the six existing read sites louder
in review without changing a single number they emit. `favorable_status` — the value derived from
the raw field at `daeun_overlay.py:76` — reaches **14+ client-visible sites**
(`premium_report.py:1006`, `:1035`; `compat_report.py:142`, `:158`; `chart.py:59`, `:361`, `:402`;
`skeleton.py:84`; `prose_fillers.py` ×10; `prose_scaffold.py:257`). Every one of those renders a
fluent sentence on the strength of a number that is wrong for 18.8% of charts. **The remedy is to
have the read site call `favorable_element()`, not to rename the field.** A rename alone would
leave all 380 charts wrong and merely make the code easier to review.

**Recommendation (revised after validation), in priority order:**

1. **Fix the read sites** — `daeun_overlay.py:76`, `skeleton.py:259`, `prose_scaffold.py:73/116/169/307`
   should call `yongsin.favorable_element(chart)`. This is the correctness fix. Decide `cli.py:165`
   deliberately: keep it if the "candidate" framing is intended, or route it through the resolver
   and relabel.
2. **Then rename** the raw field to `strength_assessment["_raw_unresolved_favorable"]` so the
   *next* direct read self-flags in review — the same defensive-naming trick already used
   elsewhere in this codebase (leading-underscore "private" helpers). Keep the producer
   (`strength.py:169/174/184/201`), the resolver (`yongsin.py:147`), and the validation harness
   (`validation.py:719`, `:812` — which compares raw vs resolved **by design** and must keep the
   raw access) on the raw field.
3. **Add the pin** — a test asserting the derived rule above (`verdict == "balanced"` + climate
   band ⇒ resolved ≠ raw) so the two channels cannot silently re-converge or re-diverge.

The ordering matters: doing (2) before (1) produces a codebase that is easier to review but still
wrong, and the "easy to review" state makes it *less* likely anyone goes back to do (1).

### 4.6 No independent ephemeris cross-check (see §2.1/§2.3)

The engine's correctness ceiling for solar-term-dependent calculations (month pillar, 대운 starting
age, annual/monthly pillar boundary) is exactly sajupy's `calendar_data.csv` accuracy — untested
against an external source. **viet-bazi-engine**'s public validation methodology (NAOJ/JPL
cross-check with a stated error bound) is a concrete, cheap-to-adopt reference: even a handful of
spot-checks against a public ephemeris (NASA/JPL solar longitude tables, or a second independent
Saju calculator's published term times) for a few 절기 boundaries per decade would convert an
unverified assumption into a bounded, documented number — the same shift this project already made
for its own textbook-case validation (`tests/test_textbook_cases.py`'s externally-sourced
published charts).

### 4.7 No-git repo remains the single largest operational risk, independent of code quality

Already documented extensively in this session's memory (the compat.py variant-contamination
near-miss during the C9 investigation) but worth restating in an architecture document because it
changes the cost-benefit of every other recommendation here: in a normal repo, a bad experimental
edit is a `git stash` away from safe. In this repo, it is not, and the only reason the C9
contamination didn't ship was disciplined manual restoration from a `/tmp` backup. **This is the
one item on this list that isn't a code change** — it's a process gap that makes every code-level
robustness improvement above slightly more urgent than it would otherwise be, because there's no
safety net underneath any of them.

---

## 5. Priority-ordered action list

🔁 **Revised after validation.** Each row now carries a ✅/🔁 status. ✅ = claim independently
re-verified this pass and unchanged. 🔁 = the row's premise was corrected, or the row is new /
re-ranked as a result of validation. Two rows changed rank materially: item 2 is no longer a
rename (the rename does not fix the live defects — see §4.5) and the stars/patterns row (now item
10) had its scope measured — **24 emitted star keys**, not "~15 derivations".

| # | Finding | Effort | Impact | Status |
|---|---|---|---|---|
| 1 | Fix the **six live** raw-field read sites to call `yongsin.favorable_element()` — `daeun_overlay.py:76`, `skeleton.py:259`, `prose_scaffold.py:73/116/169/307` (§4.5) | Low (6 call sites) | **Highest — measured wrong on 380/2016 charts (18.8%), reaching 14+ client-visible sites.** This is the only row that is a live correctness defect, not a robustness investment | 🔁 re-scoped + re-ranked |
| 2 | *Then* rename the raw field to `_raw_unresolved_favorable` to self-flag future direct reads (§4.5) | Low (one rename + grep) | Medium *as prevention only* — a rename alone changes no output; it must follow item 1, not replace it | 🔁 premise corrected |
| 3 | Log before falling back in the 13 `except Exception:` blocks (§4.1) | Low (13 one-liners) | High — closes the silent-degradation class this session spent the most time hunting | ✅ verified (count exact: cli 1, compat 3, prose_fillers 6, premium_report 3) |
| 4 | Fix the `daeun.py:238-241` `return 0` sentinel — it collides with a legitimate 0 and no caller flags it (§2.2) | Low | Medium-High — a "could not compute" path indistinguishable from a valid answer; the failure branch is currently untestable | 🔁 **new** |
| 5 | Document the 대운 starting-age remainder: the 1-day-=-4-months equivalence is **already** in the docstring; what remains is one sentence on the discarded 1–2 days (§2.2) | Low (docstring only) | Low-Medium — smaller than originally scoped | 🔁 reduced scope |
| 6 | Delete or wire in the dead `month_season_score` (§2.5) | Low | Medium — removes a misleading field from the strength-assessment API | ✅ verified unchanged |
| 7 | Suppress or re-base the Korean longitude false positive — the 5°-vs-135°E check fires on essentially every Korean chart (§2.1) | Low-Medium | Medium — the warning the audit credits with protecting against defect #9 is noise for this engine's primary market | 🔁 **new** |
| 8 | Extend `test_knowledge_grounding.py`-style checks to `lookup.py`/`strength.py`/`patterns.py` constants, via **discovery** not more hand-added imports (§4.3) | Medium | Medium — converts a convention into an enforced rule; note the existing test names 4 tables, so new tables are uncovered by default | 🔁 corrected (4, not 5) |
| 9 | Sensitivity-sweep the strength/pattern magic-number thresholds against the canonical chart corpus (§4.2) | Medium | Medium — same technique already proven this session on the C9/육합 question | ✅ verified unchanged |
| 10 | Re-verify `patterns.py::_grid_stem_by_tuochul` and audit `stars.py`'s **24 emitted star keys** against `knowledge/` tables rather than its 10 module-level functions (§2.6, §2.7) | Medium | Not yet scoped — next pass should go deep here; the function-level review would reach only ~1/4 of the output | 🔁 corrected (24 keys) |
| 11 | Add a regression test for the `sewoon.py` sub-1900/post-2100 fallback paths (§2.3) | Low | Low — rare real-world hit, but genuinely untested (confirmed: `tests/test_sewoon.py`'s only anchor is the 1900-01-01 (甲,戌) check) | ✅ verified unchanged |
| 12 | Spot-check a handful of solar-term boundaries against an external ephemeris (§4.6) | Medium | Low-Medium — bounds an assumption that's currently just trusted | ✅ verified unchanged |

🔁 **Correction to the framing paragraph that followed this table.** It previously read that none
of these items are urgent "in the sense of 'currently producing wrong client output'." Validation
**falsifies that for item 1**: six live read sites produce a wrong favorable element for 18.8% of
charts, and `favorable_status` derived from them reaches 14+ client-visible render sites — which
is exactly "currently producing wrong client output." The 189/194 certification the paragraph
cites does not cover this, because the campaign validated the **calculation layer** (raw and
resolved both behave correctly) while the defect is in the **read channel** — a module reading the
raw field is not a calculation error and no fixture-driven calculation test can see it. The
remaining eleven rows are still robustness investments in the original sense: the difference
between a defect being caught by a log line or a naming convention next time, versus being caught
the way this session's defects were caught — by a person noticing a report looked slightly off,
months after it shipped.

**Where §9's backlog sits relative to this table.** The versatility findings raise their own
prioritised list (**V1–V12**, §9.13). It is deliberately *not* merged into the table above and it
does not re-rank any row: every §9 item is an addition to output that is already correct, so the
live defects (rows 1–3) come first on severity, not merely on effort. Two connections are worth
noting. **Row 8 is the natural enforcement mechanism for §9's findings** — grounding tests that
*discover* constants rather than importing them by hand would catch a KB12/KB13/KB16 dimension
silently dropping out of the reports, which is precisely the drift §9.3–§9.4 measure; §9's findings
are the concrete test fixtures row 8 lacks. And **row 10's 24 emitted star keys** is the same
question §9 asks of every other block, already scoped and measured — it is the one block where the
versatility audit has been done rather than proposed.

---

## 6. External references consulted

- **[bazi-analyzer](https://github.com/Tonyyiixn/bazi-analyzer)** — Python BaZi engine; confirmed
  independent convergence on the 抑扶/억부 strength method as primary, with similarly honest
  framing of it as one valid school among several.
- **[viet-bazi-engine](https://github.com/iZenDeveloper/viet-bazi-engine)** — TypeScript/Python/WASM
  BaZi engine; source of the NAOJ/JPL ephemeris cross-check methodology (§4.6) and confirmation of
  the explicit-Zi-convention-toggle design pattern (§2.1).
- Chinese-language sources on 大运/起运 remainder handling (search: *"大运 起运 三天一岁 余数 四个月
  计算方法"*) — source of the months-not-floor remainder convention discussed in §2.2.
- Internal: `knowledge/` (18 files), `docs/audits/2026-07-05-engine-audit.md`,
  `docs/audits/2026-08-10-architecture-audit.md`,
  `docs/audits/2026-08-22-engine-audit-addendum.md`,
  `docs/audits/2026-09-engine-validation-report.md`,
  `docs/research/2026-09-validation-{yongsin,climate,compat-career}.md`.

---

## 7. What this audit does *not* cover (be honest about the boundary)

- Line-by-line re-verification of `stars.py` (559 lines; 🔁 **24 emitted star keys** from 10
  module-level functions, not "~15-20 individual star rules" — see §2.7) and `patterns.py`'s
  regular-grid stem-selection method (`_grid_stem_by_tuochul`) — surveyed at the structural level
  only; flagged in §2.6/§2.7/§5 item 10 as the next audit's starting point.
- `report_data.py`, `premium_report.py`, `prose_scaffold.py`, `prose_fillers.py`, `skeleton.py`
  beyond what was already independently verified earlier this session — ~5,300 combined lines,
  originally surveyed only for the error-handling sweep in §4.1. 🔁 **Validation partially closed
  this gap**: a targeted grep for the raw favorable-element field found live read sites in
  `prose_scaffold.py` (×4) and `skeleton.py` (§4.5) — enough to establish that the layer was *not*
  clean, but not a substitute for reading it. The remaining prose-generation logic is still
  unexamined.
- `compat_report.py` (968 lines) and the PDF rendering backends under `src/saju_html/` — out of
  scope for this pass, which focused on the calculation core per your "major luck" example.
- Any independent re-derivation of the classical source texts themselves (적천수, 궁통보감,
  연해자평, 명리정종) — this audit checked code-against-knowledge-file and code-against-two-other-
  engines consistency, not knowledge-file-against-original-classical-text fidelity, which is the
  validation campaign's job (`docs/research/2026-09-validation-*.md`), not an architecture audit's.

---

## 8. Validation addendum — 2026-09-14 (same day, later)

Every claim in §2 and §4 was re-checked against the live tree before any of the corrections above
were written. This section records what was measured, what changed, and what remains unvalidated —
so a later reader can tell the difference between a claim this audit *checked* and one it merely
*asserted*.

### 8.1 Method

Claim-by-claim re-verification against the working tree, not against the audit's own prose:
`grep`/`Read` for every file-and-line citation, direct execution of the engine for every behavioral
claim (`compute_chart` on real and synthetic dates), and an enumeration sweep where a *count* was
asserted rather than a behavior. Where a probe could not reach the code path under test, the result
was discarded as non-evidence rather than recorded as a pass — see 8.4, which is the one place this
method caught itself.

Test baseline at validation time: **885 passed, 10 xfailed, 9 warnings in 26.05s** (the 9 warnings
are all the pre-existing `urllib3` Brotli `DependencyWarning`). No failures. Baseline was measured
before and after the validation work to confirm the documentation pass changed no behavior.

### 8.2 Claims that held up

| Claim | How verified |
|---|---|
| §2.3 — `sewoon.py`'s sub-1900/post-2100 fallback paths are untested | `tests/test_sewoon.py` read in full: its only anchor is `_daily_pillar(1900,1,1) == ("甲","戌")` at `:73-74`. No fallback test exists. **Stands.** |
| §2.5 — `month_season_score` is dead | Confirmed no live consumer. **Stands.** |
| §2.6 — `_grid_stem_by_tuochul` is unverified | Defined at `patterns.py:31`, called at `:488`, no direct test. **Stands.** |
| §2.12 — the validation harness has no structural self-test | Grep for `def test_` / `self.test` inside `validation.py` returns nothing. **Stands.** |
| §4.1 — 13 `except Exception:` sites repo-wide | Enumerated exactly: `cli.py` 1, `compat.py` 3, `prose_fillers.py` 6, `premium_report.py` 3. **Exact — stands.** (§2.11's *attribution* of them to the presentation layer was wrong; see 8.3.) |
| §4.5 — "three modules… fixed" | True as stated, but stale and misleading — it names the three *fixed* modules and omits the six live ones. Corrected in place. |
| §3.6 — calculation never imports presentation (one-way layering) | Grep confirmed. **Stands.** |
| §4.7 — no-git repo | Independently confirmed (`fatal: not a git repository`). **Stands**, and remains the largest operational risk. |

### 8.3 Claims corrected

1. **§4.5's module list — inverted.** The audit names `premium_report.py`, `report_data.py`, and
   `compat.py` as the offenders; all three are fixed (their remaining mentions are comments and
   docstrings), while four modules the audit never names hold **six live reads**. The section's
   conclusion ("the class was found three times and closed") is wrong in the direction that
   understates the defect. Full detail and the corrected recommendation in §4.5.
2. **§2.11 — "10 of 13" → 9 of 13.** The presentation layer's exception density is 9
   (`prose_fillers` 6 + `premium_report` 3); the other 4 are `compat.py` 3 + `cli.py` 1.
3. **§4.3 — "five interpretive tables" → four.** `test_knowledge_grounding.py` imports exactly
   `_CAREER_DOMAINS`, `_ELEMENT_ASSOCIATIONS`, `_ELEMENT_ORGAN_ORGANS`, `_GROUNDING_PRACTICES`,
   across 4 test functions.
4. **§2.7 / §7 — "~15-20 individual star derivations" → 24 emitted star keys** from 10
   module-level functions. The structural recommendation changes accordingly (§5 item 10): audit
   the 24 *outputs* against `knowledge/`, not the 10 functions.
5. **§2.2 / §5 — the 대운 remainder is partly already documented.** `daeun.py:224`'s docstring
   already states the 1-day-=-4-months equivalence, so the recommended docstring note is half
   implemented; the residual gap is only that the 1–2 leftover days are discarded unstated. Row
   re-scoped down.
6. **§2.1 — the longitude check's scope is narrower than described.** The function opens with
   `if not city: return` (`pillars.py:223`), so it guards **only** the city-geocoding path; a
   caller passing `longitude=` explicitly bypasses it entirely and gets no warning at all.
7. **§5's framing — "none of these are currently producing wrong client output" is false** for
   item 1, per the 18.8% measurement below.

### 8.4 New findings (not in the original audit)

**F1 — `daeun.py:238-241`: a sentinel that collides with a valid answer.** When the starting-age
computation cannot resolve a target, the function returns `0` with a comment that says *"just
return 0 and let the caller flag it."* No caller flags it — a grep for `start_age == 0` across
`src/` returns nothing — and `0` is also a *legitimate* result (a birth exactly on a 절기 moment,
deliberately asserted by `tests/test_daeun.py:81`
`test_starting_age_at_exact_term_moment_is_zero`). The failure path is therefore both silent and
untestable: a test that pinned the error behavior would fail the legitimate case, and a test that
pins the legitimate case cannot distinguish it from the failure. **This is the same
sentinel-collides-with-valid-value class the engine has hit before; it belongs above the
remainder-rounding issue on the priority list (§5 item 4).** The fix is a distinguishable return
(e.g. `None` or a result object carrying `(age, remainder_days, resolved: bool)`), not a different
magic number.

**F2 — the Korean longitude warning is a systematic false positive.**
`_warn_if_suspicious_longitude` computes the standard meridian as `utc_offset * 15` = **135°E** for
UTC+9 and warns when the geocoded longitude is more than 5° away. Korea sits at **~127°E**, so
every Korean chart is **8.0° off against a 5° threshold** and the warning fires unconditionally.
Verified directly: `compute_chart(city="Seoul", utc_offset=9.0)` emits *"geocoded longitude for
'Seoul' is 126.9783°, which is more than 5° from the standard meridian 135.0°…"*. The cause is
historical, not a bug in the check's intent: UTC+9's meridian was set for Japan, and Korea keeps
the offset while lying 8° west of it. **Consequence:** the guard the audit credits (§3.3) with
catching solar-time defects is noise for essentially every chart this engine's primary market
produces, which means it will be tuned out and stop catching the real cases. **This is a
diagnostic-quality defect, not a calculation error** — the chart itself is right. Fix: measure
against the city's own timezone meridian, or suppress when the longitude is consistent with the
country (Korea: 124–132°E at UTC+9).

**F3 — the two-channel divergence rate, measured: 380 of 2,016 charts (18.8%).** The original
audit treated this class as a design smell with no blast radius attached. Measured, it is the
largest live correctness defect in the engine; full data, the exact divergence rule, and the
confinement proof are in §4.5.

### 8.5 A note on method — the probe that proved nothing

Worth recording because it nearly produced a false "clean" result. The first attempt to verify F2
passed an explicit longitude:

```python
compute_chart(longitude=126.978, utc_offset=9.0, ...)   # → no warning observed
```

That looked like a contradiction of the finding. It was not evidence of anything: the function
returns immediately at `if not city: return`, so **the probe could not reach the code under test**.
Re-running through the path that actually executes it (`compute_chart(city="Seoul",
utc_offset=9.0)`) produced the warning immediately. The general lesson, which applies to anyone
extending this validation work: **a probe that cannot reach the branch returns the same empty
result as a clean pass, and a negative result from an unreachable branch is not evidence.** The
same trap produced an earlier vacuous sweep in this session that reported "0 divergences" across
0 computed charts. Where a sweep is used as evidence, it must also report **how many subjects it
actually reached** — the 2,016-chart figure in §4.5 is quoted with its denominator for exactly
this reason.

### 8.6 Deliberately left unvalidated

Recorded so these are not mistaken for verified claims:

- **§2.5 / §2.6 threshold sensitivity** — the ±10% sweep recommended in §4.2 was not run here; it
  is a proposed workstream, and treating it as done would be the exact error this addendum exists
  to prevent.
- **§4.4's performance ceiling** — `cycle_index()`'s `O(60)` cost was reasoned about, not measured.
  No benchmark was run.
- **§4.6 ephemeris cross-check** — not performed. The engine's solar-term accuracy ceiling remains
  sajupy's `calendar_data.csv`, unverified against an external source.
- **`compat_report.py` and the `src/saju_html/` PDF backends** — still out of scope, unchanged from
  §7.
- **Whether the six live read sites change any *actual client deliverable*.** The 18.8% figure is a
  chart-population rate, not a delivered-report rate. No existing candidate report was re-rendered
  and diffed to confirm which shipped documents are affected — that is a concrete, cheap next check
  and should be the first thing done when item 1 of §5 is actioned.

---

## 9. Report versatility — block × knowledge coverage

§1–§8 asked whether the engine is **correct** and whether it **fails loudly**. This section asks a
different question, and it is the one a client actually experiences: **does each report block emit
what the knowledge base already supports, or a fixed simplification of it?** The gap this section
measures is not a bug in the sense of §4.5 — nothing here is *wrong*. It is the distance between a
report that is *simple* and one that is *versatile*, where "versatile" means the output *branches on
the chart's actual condition* instead of asserting one of a small number of pre-written paragraphs.

Two layers were inventoried for this pass: the **report blocks** each generator emits, and the
**analytical dimensions** each knowledge file contains. The claim being tested is that the second
layer is substantially richer than the first, and that the shortfall is concentrated in specific,
nameable places.

### 9.1 There are two coupling modes, and only one of them is versatile

🔁 **New framing.** The knowledge base reaches the engine through two mechanisms that fail
differently and are easy to confuse:

| Mode | Mechanism | Example | Failure mode |
|---|---|---|---|
| **Table coupling** | A KB table is *reproduced* as engine data | `report_data.py:179` reproduces KB12's element→industry families; `report_data.py:121` reproduces KB14's direction/colour/number/material table; `_ELEMENT_ORGANS`/`_GROUNDING_PRACTICES` reproduce KB15 (`knowledge/15-health-and-body.md:39-41`, `:94-95`) | The dimension is wired but **frozen** at whatever the table said — it cannot branch, and it silently drifts if the KB table is edited |
| **Citation coupling** | The reporter *emits* an inline `*(see knowledge/NN)*` reference | `plain_glossary.py:330`: `insertion = f" — {pd.plain} *(see {pd.source})*"`; `compat_report.py:255` | The authority is named, which is what the product's positioning promises — but only for the files actually in the citation set |

The distinction matters because the two are checked by different greps and only one of them is
visible to a client. It also explains the shape of this section: several "unwired" dimensions below
are in fact *table-coupled* (so the engine emits something) while the **branching rule that would
make the output versatile is the part that was left behind**.

### 9.2 The census — which knowledge files any engine code names

Method, stated because it bounds the claim: a literal `grep -F` for each filename across
`src/`, `tests/`, `tools/`. This counts **mentions of the filename**, which is a proxy for coupling,
not coupling itself — and it is blind to dynamically-constructed citations, of which this codebase
has exactly one (`plain_glossary.py:330`). That blind spot was closed separately: the `source`
literal set in that file enumerates to **8 files** (00, 02, 03, 05, 06, 07, 08, 09), so the dynamic
channel's reach is not merely uncounted but *enumerable* — and it does not include KB13 or KB16
either. Both routes agree.

| Knowledge file | `src/` | non-`src` | Reading |
|---|---|---|---|
| `11-gunghap.md` | 67 | 66 | The compat product's spine — cited at nearly every sub-system |
| `07-special-formations.md` | 42 | 7 | Star/pattern layer, richly cited |
| `05-ten-gods.md` | 26 | 16 | Core interpretive lens |
| `06-twelve-stages.md` | 23 | 10 | |
| `03-five-elements.md` | 17 | 4 | |
| `08-luck-pillars.md` | 15 | 0 | |
| `02-branches.md` | 12 | 6 | |
| `09-interpretation-method.md` | 10 | 17 | |
| `15-health-and-body.md` | 6 | 4 | Table-coupled only (organ/grounding contracts) |
| `01-stems.md` | 5 | 6 | |
| `12-career-and-vocation.md` | **5** | **36** | ⚠️ See §9.3 — the 5 are comments/docstrings, and the tests outnumber `src/` 7:1 |
| `17-climate-method.md` | 5 | 37 | |
| `00-glossary.md` | 4 | 8 | |
| `10-output-template.md` | 4 | 0 | |
| `04-yin-yang.md` | 3 | 0 | |
| `14-directions-and-relocation.md` | **1** | 2 | One comment (`report_data.py:121`) |
| `13-wealth-and-business.md` | **0** | 2 | ⚠️ See §9.3 |
| `16-date-selection.md` | **0** | 1 | ⚠️ See §9.3 |

✅ **Verified.** The two zero rows hold under two independent methods, and the `non-src` counts were
traced to their sites: KB13's two mentions are `tests/test_knowledge_files.py:32` (a file-exists
check) and `tests/test_html_pdf.py:459` (a **hand-written input fixture** asserting the citation
*stripper* removed it — it traces to `knowledge/07-special-formations.md:24`, not to engine output);
KB16's single mention is `tests/test_knowledge_files.py:91`. **No engine code path emits either
file's name.** The KB12 row is the more revealing one, and it is new:

### 9.3 The tests know the doctrine better than the reports do

🔁 **New finding.** KB12 (career) is named 5 times in `src/` and 36 times in `tests/`. Reading the
`src/` sites, **all five are comments or docstrings, not consumers**:

- `report_data.py:179` — `# source: knowledge/12-career-and-vocation.md § Element → Industry Families` (this one *does* sit above real table data — the only genuine coupling)
- `report_data.py:487` — docstring prose
- `validation.py:384`, `:609`, `:1172` — comments and a rendered validation-report string

So the engine consumes KB12 for **one dimension** (element→industry families) while its branching
doctrine — `knowledge/12-career-and-vocation.md:138-147` ("Too-strong Day Master (신강): favour fields
that drain or channel…" / "Too-weak (신약): favour Resource or Companion first") and `:157-170`
(employment-vs-entrepreneurship signals, 겁재 partnership caution) — is consumed by nothing, even
though `_section_career_wealth` is a client-facing block in **4 of the 7 tiers** — `essential`,
`deep`, `reading`, `fullmap` (it is absent only from `sample`, `spark`, and `companion`), so it
ships in every tier anyone is likely to buy. The dimension that would make the career block
*branch on the chart* is present in the KB, asserted in the tests, and absent from the report.

### 9.4 Two knowledge files with zero engine coupling — and the blocks that should be using them

These are the starkest instances of the user-facing concern, because in both cases **the report block
exists and the doctrine is unwired**.

**KB13 — wealth (223 lines, 9 dimensions, 0 engine mentions).** The file separates wealth into three
questions (income style / producing chain / carrying capacity) and supplies the branching rules:
정재 vs 편재 income shape (`13:23-44`), 식상생재 (`13:58-68`), 재생관 (`13:70-77`), 재고 (`13:79-92`),
can-the-Day-Master-hold-wealth 신강/신약/재다신약 (`13:99-113`), 겁재奪財 shared-money risk
(`13:118-142`), wealth timing (`13:144-168`), preservation (`13:170-189`). The engine emits **three**
wealth-bearing blocks — `_section_career_wealth` (`essential`/`deep`/`reading`/`fullmap`),
`_section_wealth_timing` and `_section_business_launch` (both `deep`/`fullmap`) — and between them
they name KB13 **zero times.** The 정재/편재 table alone supplies an income-shape branch (steady vs
variable vehicle) that nothing consumes.

**KB16 — date selection (156 lines, 6 principles, 0 engine mentions).** The file's chart-relative
layer gives six ranked rules (`16:20-54`): avoid a day branch clashing the natal **day or hour**
branch; avoid a day running the **기신**; avoid repeating natal **형/파/해**; favour a day whose
stem/branch is **용신 or 희신**; favour a day branch harmonising (**육합/삼합**) with the natal day
branch; and `16:62-83` maps per-event rules (moving / business opening / signing / wedding / surgery
each to a ten-god class).

`_section_monthly_lucky_dates` (`premium_report.py:1616`) already exists and its own methodology
blockquote (`:1624`) describes filtering daily-luck stems to the favourable element and dropping days
that clash the natal day branch — i.e. **roughly 2 of the 6 principles**. Three others are
implementable from data the engine already has (기신 avoidance, 형/파/해 repetition, 육합/삼합
harmonisation), and the per-event map (`16:62-83`) is unused entirely. Note also that
`_section_30_day_plan` (`premium_report.py:1578`) is **dead code with no call site** — and a 30-day
plan is precisely the block KB16's per-event rules were written for.

### 9.5 The citation ceiling — the report names its method file, never its topic files

🔁 **New finding, and the sharpest one in this section.** Counting filename mentions understates how
starved the single-chart report is. The module contains exactly **8 citation texts** (excluding the
module docstring at `:4`); mapping each to its enclosing function and asking whether a client can
reach it gives:

| Line | Enclosing function (def line) | Cited file | Reaches a client? |
|---|---|---|---|
| 479 | `_four_pillars_one_by_one` (`:466`, via note call `:476`) | KB01, KB02 | ❌ reviewer-note body |
| 603 | `_section_career_wealth` (`:590`, via `:600`) | KB03, KB05 | ❌ reviewer-note body |
| 692-693 | `_section_relationships` (`:679`, via `:690`) | KB07, KB05 | ❌ reviewer-note body |
| 794 | `_render_compat_snapshot` (`:787`) — **docstring** | KB11 | ❌ docstring |
| **805** | `_render_compat_snapshot` | KB11 §Composite Weight | ✅ **the sole client-visible citation** |
| 833 | `_section_health_vitality` (`:826`, via `:831`) | KB03 | ❌ reviewer-note body |
| 874-875 | `_health_deep_dive` (`:866`, via `:872`) | KB03, KB06 | ❌ reviewer-note body |
| 1434 | `_section_business_launch` (via `:1432`) | KB08 | ❌ reviewer-note body |

🔁 **Self-correction recorded.** An earlier draft of this section claimed "7 of the 8 sit inside
`_reviewer_note` bodies" and attributed a citation to the note call at `:429`. Both were wrong, and
the second error is instructive: `_reviewer_note` is called **7** times (`:429`, `:476`, `:600`,
`:690`, `:831`, `:872`, `:1432`) but only **6** of those calls name a file — `:429` lives in
`_section_day_master_portrait` (`:422`) and says only *"verify against the relevant knowledge
files"* with no filename, so a filename-grep cannot see that call site at all. The count was right
by coincidence (6 notes + 1 docstring = 7 unreachable) but the attribution was not. This is the same
class of error §8.5 records: a count inferred from a grep's output rather than from reading the
call sites.

`_reviewer_note` (`premium_report.py:127-134`) returns `[]` when `ctx.tier in _CLIENT_TIERS`, and
`_CLIENT_TIERS` (`:124`) is `{"sample", "essential", "deep", "spark", "reading", "fullmap",
"companion"}` — **every reachable tier**. So every one of those citations is unreachable in client
output, by construction. ✅ Verified directly, and it is *locked in*: `tests/test_premium_report.py:530`
`test_no_reviewer_notes_in_client_report` is parametrized over tiers and asserts the suppression.

**Consequence.** The only citation path that actually reaches a client from the 1820-line
single-chart module is `_render_compat_snapshot`'s `*(see knowledge/11-gunghap.md §Composite Weight)*`
(`:805`) — a **cross-sell** into the compat product. The gate's *intent* is sound (internal review
notes must not ship), but its *effect* is that the thematic files have no client-facing citation
channel at all: the internal-note channel was the only channel. This is a direct tension with the
positioning line — "read in clear English by a human, **with the classical texts cited**" — which the
compat product satisfies and the single-chart product does not. It is also the clearest structural
reason the single-chart reports read as "simple": they never tell the client which doctrine is
speaking.

Relatedly, **Sources & Limits is emitted only by `skeleton.py:366`** (the internal reader scaffold)
and by neither client-facing reporter, while `knowledge/10-output-template.md` calls it mandatory —
and `src/saju_html/__init__.py:455-461` (`_strip_sources_section`) deliberately removes it before
layout. Net: the one provenance section the template mandates never reaches a client in any tier.

### 9.6 한신 / 구신 — a whole axis of the 용신 model computed and never emitted

🔁 **Verified, with one correction.** `strength.py:157-204` computes `candidate_draining` (= the
authority element for a strong self at `:172`; = the wealth element for a weak self at `:177`;
`None` at `:188`) and writes it into the strength-assessment dict at `:204`. **Within `src/` it
appears only in `strength.py`** — 5 occurrences, all definitional (the docstring at `:95`, the three
assignments, and the dict write at `:204`). Its sole read anywhere in the tree is
`tests/test_strength.py:97`, which asserts the field's value. So the field is computed, unit-tested,
and **consumed by nothing that produces output.**

🔁 **Self-correction recorded.** An earlier draft said "zero reads outside `strength.py`" and
compared against "21 / 12 / 3 reads" for the sibling fields. The first was falsified by that test
read; the second set was not reproducible, so the comparison is restated here in terms that are —
**module spread**, which shows the gap more clearly than a raw read count:

| Field | `src/` occurrences | `src/` modules referencing it |
|---|---|---|
| `candidate_favorable` | 27 | **10** — `cli.py`, `daeun_overlay.py`, `skeleton.py`, `prose_scaffold.py`, `strength.py`, `compat.py`, `yongsin.py`, `report_data.py`, `premium_report.py`, `validation.py` |
| `candidate_unfavorable` (기신) | 18 | 4+ |
| `candidate_supporting` (희신) | 9 | 2+ |
| **`candidate_draining` (한신)** | **5** | **1 — the module that defines it** |

한신 is the only one of the four that never leaves its defining module.

The concept is fully established in the knowledge base and the glossaries, in five places:
`knowledge/03-five-elements.md:98-104` classifies **희신 / 기신 / 구신 / 한신**; `knowledge/00-glossary.md:17-18`
defines 한신 and 구신; `knowledge/09-interpretation-method.md:98-102` uses them; and both translation
tables carry labels — `hanja_glossary.py:17` (`"한신": "閒神"`) and `plain_glossary.py:71,73`
("Draining Element (閒神)" sourced to KB00). **The engine resolves 5 classifications, the report
emits 3.** 한신 in particular is the natural output of a feature the report *already describes*
elsewhere (the draining/output channel), so surfacing it is not new doctrine — it is an existing
computed field reaching an existing block.

### 9.7 The `[UNCERTAIN]` asymmetry — three survive the strip, six do not

**Verified.** `knowledge/11-gunghap.md:16` is explicit: *"Mark [UNCERTAIN] where schools disagree — the
engine output must keep the uncertainty tag visible to the client."* The PDF pipeline strips them at
`src/saju_html/__init__.py:496-497`:

```python
out = re.sub(r"\s*\[UNCERTAIN:[^\]]*\]", "", out, flags=re.IGNORECASE)
```

The regex **requires a colon**. The consequence is a split that no one designed:

| Survives the strip (bare `[UNCERTAIN]`) | Stripped (colon form `[UNCERTAIN: …]`) |
|---|---|
| `compat.py:221` — `합화 원소 … 월령 불분명 [UNCERTAIN]` | `compat.py:257` — 명리정종 strict view on in-season proof |
| `prose_fillers.py:1189` — `[UNCERTAIN] The engine flags a special-grid candidate: …` | `compat.py:719` — 궁통보감 on 용신 alignment |
| `patterns.py:375` — `" Mark as [UNCERTAIN] until verified."` | `compat.py:864` — 권인성·곽임성 vs 명리정종 classification |
| | `compat.py:1139` — 권인성·송기영 fixed pair table |
| | `compat.py:1340` — 적천수 8-stem vs modern polarity balance |
| | `compat.py:1375` — schools differ on the exact weight |

**Three findings in one.** (a) The strip contradicts KB11:16 for the six it removes — and those six
are exactly the *most* scholarly hedges in the compat engine, all six in one module whose own
docstring (`compat.py:24`) claims to carry `[UNCERTAIN]` markers. (b) The behaviour is **internally
inconsistent**: the same tag class gets opposite treatment based on punctuation, so which hedges
reach a client is an accident of syntax. (c) It is a **versatility** loss, not just a compliance one
— "the schools disagree here, and here is how" is a richness axis the KB supplies and the pipeline
deletes. The fix is a two-line regex widening (`\[UNCERTAIN[^\]]*\]`) *plus* a product decision about
which tags should ship, since the colon form was plausibly stripped on purpose.

### 9.8 Structural versatility gaps — where tier and block structure defeat richness

Four items that are not about knowledge coverage at all:

1. **`deep` ≡ `fullmap`, byte-identical.** ✅ Verified: the two dispatch branches
   (`premium_report.py:1745-1764` and `:1784-1803`) append the **same 19 sections in the same order**,
   with identical arguments. `deep` is the current $55 hero tier and `fullmap` the legacy $129 tier, so
   the tier grid's differentiation is fictional at the top end, and the shipped `deep` report is
   *larger* than `CLAUDE.md`'s tier table describes (which lists ~9 contents, omitting
   `_section_natal_patterns`, `_section_wealth_timing`, `_section_relocation_directions`,
   `_section_lifetime_decade_roadmap`, `_section_auspicious_dates`, `_health_deep_dive`,
   `_section_monthly_lucky_dates`, `_section_audio_summary_note`). This is value-positive and
   grid-negative, and it should be an explicit decision rather than an accident.
2. **`_section_30_day_plan` (`:1578`) is dead** — no call site in `src/`, `tools/`, or `tests/`
   (✅ verified). Combined with §9.4, a KB16-shaped block exists, is unwired, and the KB16 rules that
   would fill it are unused.
3. **The reviewer-note channel is a no-op for every tier** (§9.5) — the mechanism that would carry
   citations and caveats is disabled for the entire audience.
4. **`_right_now_callout` (`:181`) and `ctx_favorable_phrase` (`:1395`) read the raw
   `candidate_favorable`** rather than `yongsin.favorable_element()` — already tracked as the last
   open instance of the two-channel class (§4.5), pinned by two `xfail(strict=False)` tests. Listed
   here because its *versatility* consequence is that the same report can describe the favourable
   element two ways in different blocks.

### 9.9 The compat breakdown displays 112 against a stated 100

✅ **Verified.** `compat_report.py:254` renders `**Composite Score (종합 점수):** **{report.score} / 100**`,
and `:296` renders per-row `| {sub.label} | {sub.label_kr} | {sub.score:+d} | {sub.max} | {sub.band} |`.
Because **every** construction site passes `max=WEIGHT[...]` (15 sites: `compat.py:202, 263, 515, 577,
615, 726, 870, 946, 1146, 1167, 1174, 1209, 1290, 1344, 1379`), the displayed `max` column sums to
**112** next to a stated "/100".

The *scoring* is correct — `compat_score` (`compat.py:1387-1483`) excludes `combined_elements` from
`raw_total`, so nothing is double-counted and the composite is genuinely out of 100. The
**display and attribution** are not self-consistent, and `knowledge/11-gunghap.md:19` explicitly says
the engine "should expose the breakdown so the client sees the composite." Two attribution problems
compound: the 12-point row is labelled **D (yongshin)** while KB11's Composite Weight table
(`11:18-45`) has no separate D row and states D is *"included in F"* — so the row carrying weight the
KB folds elsewhere is the one the client sees with a 12 next to it. Client-visible, cosmetic in
effect, and cheap to fix by labelling the descriptive row or showing the 100-point column only.

### 9.10 Knowledge dimensions available but unconsumed — the versatility levers

Drawn from the knowledge-file inventory. Each row is a **branching rule that already exists in
`knowledge/`** and a block that currently emits fixed prose where it could branch. These are the
concrete answers to "where can reports become more versatile":

| Branching dimension | KB ref | Block that should consume it | Currently |
|---|---|---|---|
| 신강/신약 career mode (drain vs resource-first) | `12:138-147` | `_section_career_wealth` (`essential`+`deep`) | Fixed prose; KB12 uncited (§9.3) |
| Employment vs entrepreneurship signals | `12:157-170` | `_section_career_wealth`, `_section_business_launch` | Unused |
| 정재 vs 편재 income shape | `13:23-44` | `_section_career_wealth`, `_section_wealth_timing` | Unused (§9.4) |
| Wealth carrying capacity (신강/신약/재다신약) | `13:99-113` | `_section_wealth_timing` | Unused |
| 겁재奪財 shared-money caution | `13:118-142` | `_section_wealth_timing`, relationships | Unused |
| Per-event date rules (5 event types) | `16:62-83` | `_section_auspicious_dates`, dead `_section_30_day_plan` | Unused (§9.4) |
| 기신 / 형·파·해 / 육합·삼합 date filters | `16:29-48` | `_section_monthly_lucky_dates` | ~2 of 6 principles (`:1624`) |
| 12-stage strength cheat sheet (건록/제왕 = peak) | `06:145-149` | Day-master portrait, strength block | Partially (stages emitted, strength-by-stage not) |
| Per-class best/worst vs DM strength (5 classes) | `05:68-69, 80-81, 92-93, 104-105, 116-117` | Ten-god distribution block | Class distribution emitted; conditional reading not |
| 조후 vs 억부 by DM strength, tension stated | `17:112-122` | `_section_chart_at_a_glance`, favourable-element note | Cross-check note exists; **tension not stated when they disagree** (see §4.5) |
| Excess-vs-depleted health tendency per element | `15:54-58` | `_section_health_vitality`, `_health_deep_dive` | Table-coupled only |
| Controlling-cycle strain cascade | `15:64-85` | `_health_deep_dive` | Unused |
| 용신 → direction for face/bed/desk/move | `14:44-58` | `_section_relocation_directions` | Table-coupled (`report_data.py:121`) |
| 한신 / 구신 (draining / restraining) | `03:98-104`, `00:17-18` | Favourable-element blocks, quick reference | Computed, never emitted (§9.6) |

Note the pattern in the last column: in almost every row the engine already **computes or tables** the
input and stops one step short of the *conditional reading* that makes the output chart-specific.
That is the whole of the versatility gap in one sentence.

### 9.11 The compat product's blocks — mono-sourced, and stripped before the client sees them

§9.14 previously recorded this surface as unaudited. Audited, it produces a finding that is the
**exact inverse** of §9.5 and lands in the same place.

The compat module (`compat_report.py`, 961 lines) contains **37 `knowledge/` mentions — and all 37
name the same file, `11-gunghap.md`.** Not one names any other knowledge file. (✅ verified: every
hit listed and read, `:9, 255, 358, 379, 389, 397, 404, 416, 427, 434, 443, 452, 461, 470, 480, 487,
497, 509, 564, 613, 630, 675, 795, 801, 807, 813, 861, 866, 874, 879, 884, 889, 894, 901, 906, 911,
916`.) Where the single-chart reporter cites **eight** files but gates almost all of them off (§9.5),
the compat reporter cites **one** file and gates *all* of them off.

**They reach no client.** The module's own docstring (`:8-10`) states the intent — "inline
`*(see knowledge/11-gunghap.md §X)*` references stay in the markdown and are removed at render time"
— and the intent holds: `strip_source_citations` (`saju_html/__init__.py:474`) has a dedicated step
**1b** for exactly this shape ("Drop non-parenthetical italic 'see `<path>` §X' citations (compat
blocks)"), and the compat PDF renderer delegates to it (`md_to_saju_compat_pdf.py:39` imports
`build_pdf` from `md_to_saju_pdf`, which calls the stripper at `:660`).

**So both products ship zero client-visible citations — by two different mechanisms.** The
single-chart product never emits them outside the tier-gated `_reviewer_note` (§9.5); the compat
product emits 37 and the renderer deletes them. The net effect is identical, and it means the
positioning promise *"with the classical texts cited"* currently reaches no client in **either**
product. That is a stronger statement than §9.5 alone could make.

Which blocks carry the (unreachable) citations: `_deep_sections` (`:208`), `_sub_system_block`
(`:322`), `_practical_guidance` (`:355`), `_verdict_narrative` (`:525`), `_couple_narrative`
(`:569`), `_daeun_callout` (`:618`) — i.e. every KB11-derived scoring and explanatory block.

Which blocks carry **none**, and should: `_element_balance_lines` (`:92`) and `_day_master_snapshot`
(`:107`). The latter asserts a seasonal strength verdict, 용신, 희신 and a watch element (`:120-123`)
— natal-analytical claims in **KB03 / KB09 / KB17** territory — with no citation at all.
Mono-sourcing KB11 is *by design* for the 11 sub-system scores (`CLAUDE.md` grounds them there), but
these two snapshot blocks render **natal analysis**, not compat scoring, and they are the two blocks
in the compat report whose doctrine lives outside KB11.

**Two things recorded to prevent false findings.** (i) `_day_master_snapshot:124-125` renders
`fe.note` — the derivation sentence — client-side, and so does the single-chart reporter
(`premium_report.py:400`, `- **Favorable Element:** {favorable} — {favorable_note}`). A working
hypothesis that the compat product surfaced its derivation while the single-chart product did not was
**tested and is false**; both do. This is a shared strength, not a contrast. (ii) `:123` reads the
raw `candidate_unfavorable`. That is **not** a two-channel defect of the §4.5 class:
`FavorableElement` (`yongsin.py:75-102`) publishes no resolved unfavorable field, and
`report_data.py:515-523` documents the asymmetry as deliberate — *"There is no resolver to read, and
inventing one would mean asserting a rule the knowledge files do not state."* It is the same posture
as §9.6's 한신/구신: a concept with no display channel, left unrendered rather than invented.

### 9.12 The provenance census — five fields computed, three rendered

🔁 **New finding.** `FavorableElement` (`yongsin.py:75-102`) carries **eight** fields. Three are
rendered into reports: `element`, `note`, `supporting`. The other five are read by **no report block
anywhere**:

| Field | Read by | Rendered? |
|---|---|---|
| `method` (`strong-dm-drain` / `weak-dm-support` / `balanced-heuristic` / `climate-balanced` / `reader-confirmed`) | captured at `premium_report.py:234` as `self.favorable_method`; otherwise only the validation serializer | ❌ never |
| `confidence` (`heuristic` / `reader-confirmed`) | validation serializer only | ❌ never |
| `climate_band` (`hot`/`cold`/`temperate`) | validation serializer only | ❌ never |
| `climate_element` | validation serializer only | ❌ never |
| `climate_agrees` (bool or None) | validation serializer only | ❌ never |

✅ **Verified exhaustively:** outside `yongsin.py` itself, every occurrence of these five names across
`src/`, `tests/` and `tools/` is either `validation.py:698-822` (the validation harness's serializer)
or a `tests/` fixture/assertion. **No report module reads any of them.**

Two consequences, and the first is the sharpest thing in §9:

**(a) `climate_agrees` is the V2 fix, already computed and already pinned.** §9.10 and V2 ask the
engine to *state* the 조후-vs-억부 tension when the two channels disagree rather than silently
reporting one. The engine does not merely omit to state it — it **computes the exact boolean that
encodes it**, and the test suite pins it in *both* polarities (`tests/validation/test_val_climate.py:
151-167` asserts the corpus must contain `climate_agrees` both `True` and `False`; the yongsin and
climate fixtures between them carry 6 `false`, 3 `true`, 7 `null`). The fixtures also record the
resolution rule verbatim: `climate.json:246` — *"억부 Metal wins, climate Fire differs —
climate_agrees False; **the weak branch takes priority over 조후**"*, and `:302` — *"억부 Water drain
wins over 조후 Fire … **the strong/weak branch takes priority over 조후**"*. So when the channels
disagree, **억부 silently wins and the client sees only the merged `element`.** V2 therefore needs
**one field of wiring, not a new derivation** — which raises its severity and lowers its effort, and
means the mandate in KB09/KB17 is violated by an omission rather than by an unknown.

**(b) `confidence` would surface the human in the loop, and is invisible.** The product's canonical
positioning is *"read in clear English by a human"*, and `reader-confirmed` is precisely the flag
that distinguishes a reader-argued 용신 from the engine's heuristic. The override is *applied* —
`_ReportContext` routes it through `favorable_element(chart, favorable_override)` (`:231`) so the
value is right — but the fact that a human supplied it is never disclosed in any block. ✅ verified
there is no alternate route: grepping `reader|override|confirmed` across `premium_report.py` returns
only plumbing and internal comments, no rendered disclosure.

Note the shape this repeats: §9.2 found *the tests know the doctrine the reports don't*. Here the same
asymmetry appears one level down — **the tests know the provenance the reports don't.** All five
fields are pinned by `tests/test_yongsin_consistency.py` and the validation fixtures, which is exactly
why this census was cheap to take and is unlikely to be caught by any test failure.

### 9.13 Prioritised recommendations

Ordered by (client-visible value ÷ effort). None of these is a correctness fix, so none competes with
§5 items 1–3; they are the backlog *after* the live defects.

| # | Recommendation | Effort | Impact |
|---|---|---|---|
| V1 | **Give the single-chart reporter a client-facing citation channel** — either a separate non-gated citation form distinct from `_reviewer_note`, or a `ctx.tier`-aware citation emitter. Requires updating `tests/test_premium_report.py:530`'s lock. (§9.5) | Low-Med | **High** — restores the positioning promise in the product that most clients buy; the highest-leverage single change here |
| V2 | **State the 조후-vs-억부 tension when the two channels disagree** rather than reporting one. (§9.10, §9.12a, §4.5) — **now known to be one field of wiring**: `fe.climate_agrees` already encodes exactly this and is simply never read | **Very Low** | **High** — mandated by KB09/KB17, currently violated, and the fix already exists computed |
| V3 | **Widen the `[UNCERTAIN]` strip to the bare form** (`\[UNCERTAIN[^\]]*\]`), then decide per-tag what ships. (§9.7) | Low | Med-High — resolves a KB11:16 contradiction and an internal inconsistency at once |
| V4 | **Wire KB13 into the wealth blocks** — start with the 정재/편재 income-shape branch and carrying capacity, both single-condition. (§9.4) | Med | Med-High — four wealth blocks currently cite nothing |
| V5 | **Emit 한신/구신** where the favourable-element card is rendered — a computed field seeking an existing surface. (§9.6) | Low | Med |
| V6 | **Extend `_section_monthly_lucky_dates` toward KB16's remaining principles** and revive or delete `_section_30_day_plan`. (§9.4) | Med | Med |
| V7 | **Decide the `deep` ≡ `fullmap` question explicitly** and reconcile the tier table with what `deep` ships. (§9.8) | Low | Med — product/pricing, not code |
| V8 | **Fix the compat breakdown display** — either show the 100-point column or relabel the descriptive row, and settle the D-vs-F attribution against KB11. (§9.9) | Low | Low-Med (client-visible cosmetic) |
| V9 | **Surface KB12's career branching** in `_section_career_wealth`. (§9.3) | Med | Med |
| V10 | **Reconcile Sources & Limits**: either the template's mandate is real (emit it client-side) or it is not (amend `knowledge/10-output-template.md`). (§9.5) | Low | Low-Med — currently contradictory either way |
| V11 | **Disclose `fe.confidence` where the favourable element is rendered** — mark a reader-confirmed 용신 as such. (§9.12b) | Very Low | Med — it is the one field that makes the "read by a human" positioning *visible in the artifact* rather than only in the marketing |
| V12 | **Give the two compat snapshot blocks a citation channel** — `_element_balance_lines` and `_day_master_snapshot` make KB03/KB09/KB17 claims and cite nothing; the rest of the compat module is mono-sourced on KB11 by design. (§9.11) | Low | Low-Med — only matters once a compat citation channel exists (V1) |

### 9.14 What this pass did not verify

Recorded in the same spirit as §8.6:

- **The block inventory is inventory-level.** The per-block versatility taxonomy (hardcoded prose,
  fixed-length lists, single-variant tables, trim-only tier branches, duplicated fallbacks,
  two-channel notes) and its block counts come from a survey pass, not from the line-by-line reading
  given to §2. Three of its most consequential claims were re-verified directly and all three held
  (`_reviewer_note`'s no-op, `_section_30_day_plan`'s deadness, `deep` ≡ `fullmap`), but the
  distribution across the remaining blocks should be treated as a worklist, not a measured result.
- **The per-file dimension lists are inventory-level.** The KB line references in §9.4 and §9.10 come
  from a knowledge-file inventory pass (headers cross-checked against table separators) and were not
  individually re-opened for this section. The KB files with **zero** `src/` coupling (KB13, KB16)
  were independently confirmed by two methods (§9.2).
- **No code was changed and no report was re-rendered.** Every finding here is a static claim about
  what the code *can* emit. Whether any specific shipped candidate PDF is missing a given dimension is
  untested — the same gap §8.6 records for the §4.5 read sites.
- **`compat_report.py`'s block set was audited in the second pass (§9.11) and remains partial.** The
  citation census there is exact (37 mentions, all KB11, reachability traced through
  `strip_source_citations` step 1b), and the two uncited snapshot blocks were read directly. What was
  *not* done is the per-block versatility taxonomy of §9.1's D1–D6 applied to the compat module's ~14
  block functions — it has been characterised by its citation behaviour and its two snapshot blocks,
  not surveyed block by block as the single-chart module was.
- **Three inventory discrepancies noticed and not chased** (recorded so they are not lost):
  `knowledge/07-special-formations.md` defines 귀문관살 twice with **different pair sets**
  (prose `07:153` = 子/午 vs table `07:239-244` = 子酉, 丑午, 寅未, 卯申, 辰亥, 巳戌);
  `knowledge/05-ten-gods.md:97` carries an uncorrected in-text self-correction
  ("— wait, that's wrong. The correct control cycle is: …") — **this is in a file the engine cites
  26 times**; and `knowledge/16-date-selection.md` has no lookup tables at all, unlike every other
  numbered file, which is part of why nothing consumes it mechanically.
