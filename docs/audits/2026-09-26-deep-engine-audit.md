# Deep Engine Audit (2026-09-26)

**Requester:** Harish, via Claude Code session.
**Baseline going in:** `python3 -m pytest tests/` → 1034 passed, 9 skipped, 9 xfailed.
`tools/run_validation.py` → 202 checks (198 PASS / 4 INTERPRETATION / 0 FAIL). Both green; this
audit did not touch either number (any incidental file changes from running the suite/validation
gate during this audit were reverted — no test/report files are modified by this document).

**Context:** this repo was already audited hard just one day earlier
(`docs/audits/2026-09-25-engine-audit-verification.md`, E-1..E-13, all fixed) and again for the
2026-09-26 "next set" (7 items, all closed). This audit's job was to find what that pass *didn't*
catch, not to repeat it — every finding below is confirmed against a previously-untouched code
path, and every P0/P1 item was independently reproduced (not just taken on a subagent's word)
before being included here.

**Method:** four parallel deep-dives, each scoped to a different layer (core calculation math;
report/prose generation; compatibility/궁합 engine; validation+CLI+infra+security), each told to
avoid re-reporting E-1..E-13 and to prove any claim by reading the real code and running it against
this repo's actual dependencies (sajupy is pip-installed here). I then independently re-derived the
highest-severity claim from each of the four reports by reading the cited lines and running a
minimal repro myself. Every P0/P1 finding below was reproduced twice, once by the subagent and once
by me, with matching output. `ruff check src/` and a scan for bare/blind `except` were also run
directly.

---

## Summary

| # | Sev | Area | One-line finding |
|---|---|---|---|
| F-1 | **P0** | Core calc — `pillars.py` | Day pillar is not recomputed when the equation-of-time correction alone (not the longitude term) pushes the true solar time past midnight — a dead helper (`_day_stem_for_date`) built for exactly this exists but is never called. |
| F-2 | **P1** | Core calc — `stars.py` | 천덕귀인 (Heavenly Virtue) can never fire for 4 of 12 birth months (卯/午/酉/子), because the code always compares the month's target character against natal *stems*, even for the months where the classical table's target is a *branch* character. |
| F-3 | **P1** | Infra — `tools/client_intake_app.py` | The self-service calculator FastAPI app, marked "✅ DONE" in CLAUDE.md/tasks.md, cannot even be imported: `NameError: name 'TOOLS_DIR' is not defined`. Confirmed broken since the file's introduction (2026-09-19). |
| F-4 | **P1** | Report/prose — `hanja_glossary.py::inject_hanja` | Systemic double-parenthesis corruption — `(대운)` written in ordinary prose becomes `(대운 (大運))` in every generated report, because the function only checks for an *existing* annotation immediately *after* a term, never checks whether the term is already sitting inside an open paren. Reproduced live on 6+ real report sections. |
| F-5 | **P1** | Compat — `compat.py::compat_daybranch` | Day-branch scoring double-dips: 寅亥 and 巳申 are simultaneously a 육합 (+20) and a 육파 (-3) per the lookup tables, and the code checks both unconditionally instead of gating harm/break behind the combine/clash `if/elif`. `寅亥` nets +17 instead of the doctrine's unqualified "++ very favorable" +20. |
| F-6 | **P1** | Compat — `compat_report.py` | The $24 "Compatibility Snapshot" (basic tier) renders the *identical* full 11-sub-system verdict table, red/yellow/favorable flag lists, and cross-references to Ten-God Cross (G) and Major Luck Synchrony (H) that the $45 "Deep Compatibility" tier is supposed to reserve — `_verdict_block()` takes no tier parameter and is called unconditionally from both. |
| F-7 | P2 | Core calc — `daeun_overlay.py` | A decade whose stem is the 용신 but whose branch is the 기신 (or vice versa) is silently reported as flatly "favorable," discarding the conflicting branch signal. |
| F-8 | P2 | Core calc — `sewoon.py` | The pre-1900/post-2100 fallback path (outside sajupy's calendar range) ignores month/day entirely, so a pre-입춘 January date in that range gets next year's cycle instead of the previous one; `_saju_month_index`'s hardcoded `lichun_month=2` also treats every February date as post-입춘 even before the real ~Feb 4 boundary. Reachable only for forecasts extending past 2100 or before 1900. |
| F-9 | P2 | Compat — `compat.py::_classify_flag` | "도화스쳐" (-5, spouse-palace 도화 hit / affair-risk flag per §I) is never bucketed into red or yellow — it silently never appears in the client-facing flag lists despite contributing to the composite score. |
| F-10 | P2 | Infra — `tools/client_intake_app.html` / `client_compat_intake_form.html` | Both self-service intake forms hard-code `value="5.5"` (India UTC offset) as the pre-filled default, contradicting the 2026-09-07 India→English-global pivot; a client who doesn't overwrite it gets a silently wrong chart. Currently moot only because F-3 makes the app unrunnable. |
| F-11 | P2 | Core calc — `engine.py` / `stars.py` | `star_anchor` is validated by the CLI's `argparse(choices=...)` but not by the public `compute_chart()` API itself — a direct caller passing e.g. `"YEAR"` silently falls back to day-anchor with no error. |
| F-12 | P2 | Infra — `validation.py` (the 200-check gate) | Two structural blind spots: no `hidden_stems` check kind exists at all (so a repeat of E-2's 중기/여기 swap would be invisible to this gate), and every `daeun.json` fixture uses `utc_offset: 9.0` (KST), so a repeat of E-1's cross-timezone term-boundary bug would also be invisible. Both of the two most severe bugs the 2026-09-25 audit found were, and would still be, undetectable by this "certified" gate. |
| F-13 | P3 | Report/prose | `TIER_CONFIG["essential"]["price"]` is hardcoded `"$19"` in `report_data.py`; CLAUDE.md describes it as "$9 intro → $19" — copy drift, not a logic bug. |
| F-14 | P3 | Chart serialization | `chart.py::to_dict()` emits the `"reference_date"` key twice (lines 355 and 410, identical value both times) and duplicates the daeun-period serialization shape between the inline comprehension and `_daeun_period_dict()` — harmless today, but a DRY violation of exactly the shape that caused E-3. |
| F-15 | P3 | Glossary tables | `hanja_glossary.py` defines `"육해"`, `"일주"`, `"월지"` twice each with identical values (harmless, redundant). |
| F-16 | P3 | Code quality | `daeun.py`/`sewoon.py` use `Dict`/`List`/`Tuple` in module-level annotations without importing them from `typing` (harmless only because `from __future__ import annotations` defers evaluation — would `NameError` under `typing.get_type_hints()`). 587+132 more `ruff` UP006/UP045 hits for the same deprecated-typing pattern repo-wide; cosmetic. |
| — | info | Process | `docs/issues_bugs.md` (819 lines, last touched around "590 passing") is now badly stale against the current 1034-test baseline and the 2026-09-25/26 fixes — several of its open items may already be fixed elsewhere and it should be reconciled or archived rather than left as a second, contradictory tracker next to `docs/audits/`. |
| — | info | Process | `stem_profiles.py` and `cli_validators.py` have no dedicated test file — they're only exercised indirectly through callers. Low priority, but worth a direct unit test given how much client-facing prose depends on `stem_profiles`. |

---

## Detailed findings

### F-1 (P0) — Day pillar wrong when equation-of-time alone crosses midnight

**Where:** `src/saju_engine/pillars.py` — `_apply_equation_of_time` (line ~309), `compute_pillars`
(line ~490, calls it at ~568), dead helper `_day_stem_for_date` (line 166, defined, never called).

`_apply_equation_of_time` layers the ±16-minute equation-of-time correction on top of sajupy's
own longitude-only solar-time correction, and correctly updates this engine's own
`solar_correction`, `adjusted_date`, and `date_adjustment` fields. But sajupy had already computed
`day_pillar`/`day_stem`/`day_branch` from *its own*, longitude-only-corrected date — before this
engine's EoT term was added — and nothing re-derives those three fields from the final,
EoT-adjusted date. A helper that does exactly that (`_day_stem_for_date`) already exists in this
same file but is called from nowhere.

**Reproduced independently:**
```
compute_pillars(year=2000, month=11, day=1, hour=23, minute=50, longitude=135.0,
                 utc_offset=9.0, use_solar_time=True, convention="korean")
→ day_pillar: 癸亥          (Nov 1's pillar)
→ adjusted_date: (2000, 11, 2)   (the engine's own EoT-corrected date)
→ solar_correction.equation_of_time_minutes: 16.4  (135° is an exact standard meridian,
                                                     so the longitude term is 0 — EoT is
                                                     the entire correction here)
_day_stem_for_date(2000, 11, 2) → 甲   (i.e. the correct day stem is 甲, pillar 甲子 —
                                        not the 癸 the engine actually returned)
```

**Why it matters:** `chart.effective_date` is documented (chart.py:164) as "the actual day-pillar
date after solar/zi adjustment" — here it names the *right* date while the day pillar itself is
*wrong* for that date. Day Master, ten-gods, hidden stems, 12운성, strength, 용신, and 대운 starting
age (`saju_age()`, engine.py:290, reads this same `effective_date`) are all built on top of the
mismatched day pillar. This is reachable whenever EoT alone (not longitude) is the deciding factor
near a 23:00–00:30ish boundary — not a rare edge case; EoT swings ±16 minutes year-round and every
birth at a longitude that happens to be an exact 15°-multiple standard meridian (many major cities)
gets zero longitude correction, leaving EoT as the sole determinant.

**Suggested fix:** after `_apply_equation_of_time` finalizes `adjusted_date`, compare it against the
date sajupy's `day_pillar` was computed for; if they differ, recompute `day_stem`/`day_branch`/
`day_pillar` via the existing `_day_stem_for_date`, and audit whatever else in `pillars.py` derives
from the day pillar (12운성, hour-stem 오서둔 lookup) to confirm it reads the corrected value, not
sajupy's raw one. Add a regression test pinned to this exact case (135°E, 23:50, EoT ≈ +16.4 min).

### F-2 (P1) — 천덕귀인 dead for 4 of 12 months

**Where:** `src/saju_engine/stars.py:299-312` (`_HEAVENLY_VIRTUE_STEM` table) and `:511-512`
(`derive_stars`).

The classical table (`knowledge/07-special-formations.md`) mixes Stem and Branch targets by month:
most months target a Stem, but 卯→申, 午→亥, 酉→寅, 子→巳 target a *Branch*. The table itself is
transcribed correctly. But the lookup that consumes it always does
`[s for s in stems if s == hv]` — comparing against the natal *stems* list regardless of whether
`hv` is actually a branch character. Since a stem character can never equal a branch character,
the star is unconditionally empty for these 4 months, no matter what the chart contains.

**Reproduced independently:** confirmed the four "wrong-type" table entries (申/亥/寅/巳) directly in
the source; the bug is structural, not conditional — any chart with `month_branch` in {卯,午,酉,子}
gets `heavenly_virtue: []` even when the target branch is present in the chart's four branches.
Only `month=寅` (a genuine Stem case) appears to be covered by `tests/test_stars.py`, which is why
this went unnoticed.

**Suggested fix:** when `hv` is a branch character (i.e. `hv in BRANCHES`), check it against the
natal branches list instead of `stems`.

### F-3 (P1) — Self-service calculator app is dead on import

**Where:** `tools/client_intake_app.py:76-77`.

```python
FORM_PATH = TOOLS_DIR / "client_intake_app.html"
COMPAT_FORM_PATH = TOOLS_DIR / "client_compat_intake_form.html"
```
`TOOLS_DIR` is never defined anywhere in the file — only `PROJECT_ROOT` and `SRC_ROOT` are.

**Reproduced independently:**
```
$ python3 -c "import tools.client_intake_app"
NameError: name 'TOOLS_DIR' is not defined
```
`git log` shows this has been broken since the file's introduction. tasks.md marks "Priority 5 —
Self-service calculator" as ✅ DONE and CLAUDE.md documents it as a working client intake path; as
committed, the FastAPI app cannot start at all. No test imports or exercises this module, which is
why it shipped broken and stayed that way.

**Suggested fix:** add `TOOLS_DIR = PROJECT_ROOT / "tools"` before line 76; add a smoke-import test
for every `tools/*.py` that's meant to run as a service, so this class of failure can't ship silently
again.

### F-4 (P1) — `inject_hanja` produces doubled parentheses

**Where:** `src/saju_engine/hanja_glossary.py::inject_hanja` (~lines 95-148), consumed from
`premium_report.py:2303`.

`inject_hanja` finds the first occurrence of a glossary term and checks whether it's "already
annotated" only by looking *after* the term for an opening `(`. It never checks whether the term
is already sitting *inside* an existing parenthetical from ordinary prose — e.g. "...new stem and
branch (대운)..." (the term written parenthetically as normal English-sentence style, not yet
Hanja-annotated). When it hits that pattern, it inserts the gloss *inside* the existing parens.

**Reproduced independently:**
```python
inject_hanja("The Daeun brings a new stem and branch (대운) into play.", set())
→ "The Daeun brings a new stem and branch (대운 (大運)) into play."
```
Confirmed live in real generated deep-tier report markdown at (at least): `premium_report.py:1971`
(→ `(대운 (大運))`), `:1177` ("Stem Clash" table label → `(천간충 (天干沖))`), `:1167` (→
`(반합 (半合))`), `:723` (→ `(십신 (十神))`), `:2104` (→ `(일운 (日運))`), `report_data.py:667` (→
`(희신 (喜神))`). The 2026-09-25/26 audit already found and patched *one instance* of this exact
defect shape (E-6's 반합 fix, by rewriting that one call site's own parens away) but never fixed the
general function — every other site using the natural `(term)` prose convention still corrupts.
`plain_glossary.py::gloss_first_use` in the same file family shows the correct pattern for
comparison (it detects and skips an existing parenthetical, and loops past a failed first match
instead of abandoning the term).

**Suggested fix:** before inserting, scan backward from the match for an unclosed `(` on the same
line/sentence; if found, insert the Hanja before that pair's closing `)` instead of wrapping again.
Also switch to a `search_from`-cursor loop like `gloss_first_use` so a term isn't abandoned
document-wide just because its first occurrence fails the check.

### F-5 (P1) — Day-branch compat scoring double-dips on dual-status pairs

**Where:** `src/saju_engine/compat.py::compat_daybranch`, ~lines 430-474.

```python
if _branch_pair_lookup(b1, b2, L.SIX_COMBINATIONS):
    primary_score += 20; ...
elif _branch_pair_lookup(b1, b2, L.SIX_CLASHES):
    primary_score -= 25; ...
else: ...
...
if _branch_pair_lookup(b1, b2, L.SIX_HARMS):
    primary_score -= 5
if _branch_pair_lookup(b1, b2, L.SIX_BREAKS):
    primary_score -= 3
```
`lookup.py` has two pairs that are simultaneously in `SIX_COMBINATIONS` and `SIX_BREAKS`: 寅亥
(Wood 육합) and 巳申 (Water 육합). The combine/clash check is a mutually-exclusive `if/elif`, but the
harm/break check underneath is unconditional — it fires regardless of whether 육합 already matched.

**Reproduced independently:** for `b1="寅", b2="亥"`, line 430 matches `SIX_COMBINATIONS` (+20),
then line 472 also matches `SIX_BREAKS` (-3) — net +17 with both flags emitted
(`일지 육합 寅亥` and `일지 파 寅亥`). `knowledge/11-gunghap.md` §B1 lists 寅亥 as unconditionally
"++ very favorable" with no caveat (unlike 巳申's noted "+ favorable but often turbulent") — so this
-3 penalty is an emergent side effect of two uncoordinated `if` blocks, not a sourced rule. Notably,
`compat.py`'s own `_cross_branch_score` (the secondary/cross-chart ladder, a few lines below)
already handles the identical dual-status-pair fact differently (deliberately reports only the first
match, per an earlier documented self-audit) — so the same classical fact is handled two
incompatible ways in one file.

**Suggested fix:** gate the harm/break checks behind `elif` (excluded once 육합/육충 matched), or —
if the intent is genuinely to apply both readings simultaneously per the dual-status doctrine
already documented in `knowledge/02-branches.md` — make that an explicit, sourced adjustment (e.g.
a partial-magnitude penalty) rather than the current full -3/-5 stacking with no citation.

### F-6 (P1) — Basic compat tier leaks the deep tier's full sub-system table

**Where:** `src/saju_engine/compat_report.py::_basic_report_lines` (line 809, via `_verdict_block`),
vs. `_deep_report_lines` (line 882, same `_verdict_block` call).

`_verdict_block(report)` unconditionally renders the full "Sub-System | Score | Max | Verdict"
table over `report.sub_systems()` — all 11 — plus the Top Red/Yellow/Favorable Flags pulled from
all 11 sub-systems, with no tier parameter to restrict it. CLAUDE.md's Tiered Client Products table
specifies Basic ($24) should show only "the four most decisive sub-systems: day-branch, day-stem,
용신 cross-supply, yin-yang."

**Reproduced independently (structural):** both `_basic_report_lines:809` and the deep path at
`:882` call the identical `_verdict_block(report)` with no tier-scoping argument; `_verdict_block`
itself (line 319-351) has no tier parameter and iterates `report.sub_systems()` unconditionally.
The subagent additionally generated an actual basic-tier report and confirmed it prints scores for
Nayin (C), Ten-God Cross (G), Combined Elements (F), and Major Luck Synchrony (H) — none of which
are among the 4 named basic-tier sub-systems — and that `_couple_narrative`/`_daeun_callout` also
pull in G/H content in the basic path.

**Why it matters:** this gives the $24 tier the $45 tier's main differentiator (the full 11-system
breakdown) for free, directly undermining the pricing structure CLAUDE.md documents.

**Suggested fix:** give `_verdict_block` (and the narrative helpers that reference specific
sub-systems by letter) a `tier` parameter, and build a basic-only version restricted to the 4 named
sub-systems for the basic path.

### F-7 through F-16 (P2/P3)

See the summary table above — each was reported with a file:line and a concrete mechanism by the
relevant subagent; F-7, F-9, F-10, F-11, F-12 describe real, structurally-confirmed gaps (verified
by reading the cited code) but are lower severity (rarer trigger conditions, or — for F-10 —
currently unreachable because F-3 blocks the whole app). F-8's fallback-path bug is real but only
reachable for forecasts before 1900 or after 2100. F-13 through F-16 are cosmetic/cleanup, listed
for completeness so they can be batched with other polish work rather than re-discovered later.

---

## What's *not* broken (checked and clean)

- E-1 through E-13 from the 2026-09-25/26 audit: still fixed, re-spot-checked (hidden-stem order,
  dual-status branch pairs, harmony completions, 격국/파격 wiring, gendered spouse-star note).
- `Chart.to_dict()`/`to_json()` field coverage is complete — no E-3-style silent field omission
  found anywhere in the current serialization.
- No new instances of the "favor"/"unfavorable" substring-inversion bug pattern found beyond what
  was already fixed — every status-keyed branch checked now uses exact-match/exhaustive lookups.
- CLI date/time/UTC-offset validation (`cli.py`/`cli_validators.py`) is real: uses `strptime` +
  explicit range checks, correctly rejects invalid calendar dates.
- No hardcoded secrets, no bare `except:` clauses anywhere in `src/`, no path-traversal risk in the
  intake-form file-naming (`slugify` strips to `\w`/whitespace/`-` and truncates).
- Compat `favorable_element_a`/`_b` overrides thread through consistently to every consumer.
- Compat composite score is symmetric under partner-order swap on a real test pair; gender/missing-
  data edge cases degrade gracefully with explicit guards, no crashes.
- All 11 compat sub-systems are genuinely implemented — no constant-return stubs.
- `ruff check src/` surfaces ~1020 findings, but on inspection the overwhelming majority are
  deprecated-typing-import noise (`UP006`/`UP045`/`UP035`, ~770 of the total) and import-order
  nits — nothing beyond what's listed above rose to an actual behavioral bug.

---

## Suggested priority order

1. **F-1** (day pillar wrong on EoT-only midnight crossing) — this silently corrupts the entire
   downstream chart for an unknown but non-trivial fraction of past deliverables; worth a quick
   audit of whether any existing candidate report sits in the affected band before fixing forward.
2. **F-3** (self-service app doesn't import) — trivial one-line fix, unblocks a feature currently
   marked done that isn't.
3. **F-5, F-6** (compat scoring/tier-leak) — both affect real client-facing pricing/quality and are
   cheap, well-understood fixes.
4. **F-4** (glossary double-parens) — cosmetic but appears in every Deep-tier PDF; cheap fix.
5. **F-2** (천덕귀인 dead for 4 months) — a real, silent doctrine gap, moderate fix.
6. Everything else (F-7 through F-16) — batch as routine cleanup.
7. **Process:** reconcile or archive the stale `docs/issues_bugs.md` so there's one live tracker,
   not two disagreeing ones; consider a `hidden_stems` check kind and a non-KST fixture in
   `validation.py`'s gate so a repeat of E-1/E-2's bug shape wouldn't again slip past a "certified"
   200-check suite (F-12).
