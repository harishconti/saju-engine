# 조후 (Climate) Cross-Check for the Favorable-Element Engine

**Date:** 2026-09-13
**Status:** Approved, pending implementation
**Trigger:** Harish's report gave 용신 = Fire; an independent reading of the same
chart gave 용신 = Water (partner-element guidance: Water best, Earth next).
Investigation confirmed the four pillars are correct (verified against
`tests/test_textbook_cases.py`'s 9 independently-sourced public figures, and by
direct recomputation of Harish's own chart). The discrepancy traces to the
용신 (favorable element) methodology, not the pillar computation.

## Root cause

`src/saju_engine/strength.py::assess_strength` and `knowledge/09-interpretation-method.md`
Step 3 implement only the 抑扶 (strength-balance) method:

- Strong Day Master → 용신 = drain/control elements (식상/재성/관성).
- Weak Day Master → 용신 = support elements (인성/비겁).
- **Balanced Day Master → whichever element is numerically least-represented in
  the chart.** This third branch is an engine-invented fallback, not a
  classical rule, and the report already self-flags it as a "starting point
  only."

Harish's chart scores -0.43 (inside the [-1.5, 1.5) "balanced" band), so the
engine falls back to the least-represented heuristic and picks Fire (7.6% of
the chart). But this chart's Day Master is 辛 (Yin Metal), born in 巳月 — the
threshold of summer. 적천수's stem stanza for 辛金 ("辛金软弱，温润而清，畏土
之叠，乐水之盈") is one of the most cited passages in the whole text: 辛金
classically wants abundant Water to wash it into brilliance. More generally,
궁통보감's organizing principle — 조후 (climate/temperature balance) — says a
chart peaking in summer heat wants Water to cool it, largely independent of
whether the Day Master reads as strong, weak, or balanced by count. This
concept is cited throughout `knowledge/11-gunghap.md` (compatibility) but was
never wired into the natal 용신 determination in `knowledge/09` or
`strength.py`.

This is the gap: two of this project's own named classical sources
(궁통보감, 적천수 — see CLAUDE.md persona) are not represented in the natal
용신 algorithm at all.

## Scope decision (confirmed with the user)

1. **Source material:** no 궁통보감 source text is available to transcribe, so
   we build a **conservative, general temperature-balance model** derived only
   from the month branch's season — not a fabricated per-stem-per-month
   lookup table. This stays inside the project's ground rule against
   inventing undocumented classical rules.
2. **Application scope:** climate is computed and surfaced for **every**
   chart, not only "balanced" verdicts, as a cross-check annotation.
3. **Conflict rule:** when 조후 and 억부 disagree —
   - **Balanced verdict:** 조후 wins the headline 용신 (this is the classical
     tie-breaker role 조후 plays when 억부 gives no clear strong/weak signal).
   - **Strong/weak verdict:** 억부 stays authoritative for the headline; 조후
     is shown only as a secondary FYI note.

## Design

### 1. `src/saju_engine/climate.py` (new module)

```python
def assess_climate(month_branch: str) -> dict:
    """Classical 조후 (climate) band for a chart, from the month branch's season.

    Conservative model: only the general principle that a chart peaking in
    summer heat wants Water to cool it, and a chart peaking in winter cold
    wants Fire to warm it. Spring/autumn are climate-neutral. This is NOT a
    full 궁통보감 per-stem-per-month table (see knowledge/17-climate-method.md).
    """
```

Returns `{"band": "hot"|"cold"|"temperate", "climate_favorable": Optional[str],
"climate_supporting": Optional[str]}`.

Season bands (the four standard seasonal quartets, already implicit in
`strength.py`'s `_MONTH_BRANCH_SEASON` table — nothing new invented here):

| Band | Branches | Climate 용신 | Climate 희신 (generates it) |
|---|---|---|---|
| hot | 巳 午 未 | Water | Metal |
| cold | 亥 子 丑 | Fire | Wood |
| temperate | 寅 卯 辰 申 酉 戌 | — (no override) | — |

### 2. `src/saju_engine/yongsin.py` — merge point

`FavorableElement` gains fields:

```python
supporting: str = "—"
climate_band: str = "temperate"
climate_element: Optional[str] = None
climate_agrees: Optional[bool] = None
```

`favorable_element()` logic (override branch unchanged, wins outright):

```
sa = chart.strength_assessment
climate = assess_climate(sa["month_branch"])
verdict = sa["verdict"]

if verdict == "balanced":
    if climate.climate_favorable:
        element, supporting = climate.climate_favorable, climate.climate_supporting
        method = "climate-balanced"
        climate_agrees = (element == sa["candidate_favorable"])
        note = <explains 조후 reasoning, and whether it agrees with the
               least-represented-element pick that would otherwise apply>
    else:  # temperate month, no override
        element, supporting = sa["candidate_favorable"], sa["candidate_supporting"]
        method = "balanced-heuristic"        # unchanged from today
        note = <existing note + "no climate override — born in a temperate month">
else:  # strong / extreme / weak / extreme_weak
    element, supporting = sa["candidate_favorable"], sa["candidate_supporting"]  # unchanged
    method = _METHOD_BY_VERDICT[verdict]      # unchanged
    climate_agrees = (element == climate.climate_favorable) if climate.climate_favorable else None
    note = <existing note + FYI clause: "climate agrees" / "climate suggests X,
           but strength-balance takes priority for a strong/weak Day Master">
```

For Harish's chart specifically: verdict `balanced`, month `巳` (hot) →
headline becomes **Water**, supporting **Metal**, `climate_agrees = False`
(the old least-represented pick was Fire), and the note explains both the
조후 reasoning and that it overrode the least-represented fallback.

### 3. Consumer fix (uncovered during design, necessary for correctness)

`premium_report.py` and `compat_report.py::_day_master_snapshot` both read
`chart.strength_assessment["candidate_supporting"]` **directly**, bypassing
`favorable_element()`. Today that's harmless because the two always agreed.
Once climate can move the headline element without moving
`candidate_supporting` (which stays 억부-derived), "Supporting Element" would
silently go stale — e.g. headline Water but supporting still shows Wood
(generator of the old Fire pick) instead of Metal (generator of Water).

Fix: both call sites switch from `sa.get("candidate_supporting")` to
`fe.supporting`, so they always track the resolved headline element. No other
call site needs a change — `report_data.py::_compatibility_rows` already
derives its own "Good" (희신) row dynamically from whatever `favorable_element`
value it's given, so it self-corrects automatically.

### 4. Knowledge files

- **New `knowledge/17-climate-method.md`**: documents the 조후 concept
  (citing 궁통보감 and 적천수 for the *general classical principle*, explicitly
  scoped as a conservative simplification, not a per-stem table), the three
  season bands, and the conflict-resolution rule. Includes an explicit note
  that 辰戌丑未 (storage months) are grouped with their adjacent
  spring/autumn quartets as "temperate" for now — a simplification, flagged
  as such, pending a fuller classical source.
- **`knowledge/09-interpretation-method.md` Step 3**: add a sub-step
  describing when 조후 is consulted and which method wins the headline on
  disagreement, referencing the new knowledge file.

### 5. Tests

- `tests/test_climate.py` (new): band classification for all 12 branches;
  hot/cold pairs return the correct climate element + supporting element;
  temperate branches return `None`.
- Extend `tests/test_yongsin_consistency.py`:
  - balanced + hot/cold month → climate wins, fields populated correctly.
  - balanced + temperate month → unchanged fallback behavior (regression).
  - strong/weak verdict (any month) → headline unchanged, climate note is FYI
    only, `climate_agrees` computed correctly.
  - `fe.supporting` always consistent with `fe.element` (generator relationship
    for balanced/climate cases).
- A named regression test reproducing Harish's exact chart (1992-06-04, 03:10,
  Pallipattu → 辛 Day Master, 巳월, balanced verdict) asserting the headline
  flips to Water/Metal — this is the test that closes the loop on the
  original investigation.

## Out of scope (for this change)

- Regenerating Harish's or any other candidate's existing report files — a
  separate follow-up once the engine change lands and tests pass.
- A full 궁통보감 per-stem-per-month table — needs real source material, not
  available today (see Scope decision §1).
- Any change to the 억부 strength-scoring formula itself (thresholds, weights).
- Any change to `compat.py`'s internal override plumbing (lines ~1311-1332) —
  unaffected, since a manual override already bypasses climate/억부 logic
  entirely, in both `yongsin.py` and `compat.py`.
