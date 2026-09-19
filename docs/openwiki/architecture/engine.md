# Engine and Architecture

## Overview

The Saju engine is a Python package at `src/saju_engine/`. It takes a Gregorian birth date, time, and location and returns a fully-derived Korean Saju (사주, 四柱) chart, including the four pillars, hidden stems, ten gods, twelve stages, major-luck sequence, branch relationships, classical stars, strength heuristic, special-grid candidates, and annual/monthly/daily luck windows.

The engine is intentionally **deterministic and auditable**: every computed value is either derived from `sajupy` (solar terms + 60-cycle math) or from the project's own Korean-Myeongri lookup tables in `src/saju_engine/lookup.py`.

## High-level flow

```
engine.compute_chart(name, gender, year, month, day, hour, minute,
                     longitude, utc_offset, ...)
    │
    ├── pillars.py          ──▶ raw four pillars + solar-time/zi adjustments
    ├── lookup.py           ──▶ hidden stems, 십신, 12운성, branch relations
    ├── chart.py            ──▶ Pillar / Chart dataclasses
    ├── engine.py           ──▶ orchestrates derivation, attaches overlays
    │     ├── daeun.py        ──▶ major-luck (대운) sequence + starting age
    │     ├── stars.py        ──▶ classical 신살 overlays
    │     ├── strength.py     ──▶ Day-Master strength heuristic + 용신/희신
    │     ├── patterns.py     ──▶ 천간합 / 화격 / 종격 grid candidates
    │     ├── daeun_overlay.py ──▶ major-luck activation overlay
    │     ├── sewoon.py       ──▶ annual/monthly/daily luck windows
    │     └── prose_fillers.py ──▶ engine-drafted paragraph fragments
```

## Key modules

| Module | Responsibility |
|---|---|
| `engine.py` | Top-level `compute_chart()`; wires all sub-modules into a `Chart`. |
| `pillars.py` | Wraps `sajupy.calculate_saju()` and normalizes the result. Handles solar-time correction, Korean `야자시` vs Chinese `조자시`, and hour-stem safety recomputation. |
| `lookup.py` | All Korean/Myeongri lookup tables: 60-cycle, hidden stems, ten gods, 12 stages, 5-element interactions, six combinations/clashes/harms/breaks, three harmonies/punishments, day-pillar stem rules. |
| `chart.py` | `Pillar`, `TenGodHit`, `DaeunPeriod`, and `Chart` dataclasses. `Chart` is the single object consumed by report generators and the `/saju` skill. |
| `daeun.py` | Computes the 10-year major-luck (대운) sequence: direction (순행/역행) from year-stem gender polarity, stepping through the 60-cycle from the birth-month pillar, and the starting age from days to the next solar term. |
| `daeun_overlay.py` | Adds activation metadata to each `DaeunPeriod`: 십신 of the period stem relative to the Day Master, branch relationships vs. natal branches, 천간합 with natal stems, and element favorability against the candidate 용신. |
| `stars.py` | Classical 신살 overlays including 홍염 and 양인 required by the compatibility engine. |
| `strength.py` | Day-Master strength heuristic and candidate favorable/supporting/avoid elements. |
| `patterns.py` | Detects 천간합 (stem combinations), 화격 (transformation grids), and 종격 (follower/special grids) candidates. |
| `sewoon.py` | Annual (세운), monthly (월운), and daily (일운) luck derivation, respecting Lichun year boundaries. |
| `skeleton.py` | Generates a structured markdown scaffold from any `Chart`, pre-filling tables and deterministic reasoning. |
| `premium_report.py` | Generates the 9-section client-facing markdown report. |
| `compat.py` | Two-chart marriage-compatibility engine: 11 sub-systems, composite 0–100 score. |
| `compat_report.py` | Standalone 두 분 궁합 markdown report generator. |
| `nayin.py` | 60-jiazi → 30 Nayin lookup + 30×30 pair table with source tagging. |
| `cli.py` | `saju-engine` command-line entry point. |

## Conventions that matter

### Zi-hour convention
- **Korean `야자시` (default, `convention="korean"`)**: 23:00–00:59 belongs to the *current* day's 子 hour.
- **Chinese `조자시` (`convention="chinese"`)**: 23:00–00:59 belongs to the *next* day's 子 hour.

The engine recomputes the hour stem when solar-time correction pushes the effective birth time across the 子 boundary.

### Solar-time correction
- Enabled by default (`use_solar_time=True`).
- Non-standard longitudes (e.g., Indian births far from the IST meridian 82.5°E) are corrected to true solar time before deriving the hour branch and day pillar.
- `Chart.effective_date` records the actual day-pillar date after adjustments.

### 60-cycle and month boundaries
- `sajupy` provides the solar-term month boundaries and base 60-cycle math.
- The engine adds the 五虎遁 (month-stem) and 五鼠遁 (hour-stem) lookups that `sajupy` does not fully expose.

## Data model

The `Chart` object is the canonical output. It contains:

- Birth metadata (`name`, `gender`, `birth_date`, `effective_date`, `birth_time`, `city`, `longitude`, `utc_offset`, `convention`, `reference_date`).
- Four `Pillar`s (`year`, `month`, `day`, `hour`), each with `stem`, `branch`, `hidden_stems`, and `combined`.
- Derived lists: `ten_gods`, `twelve_stages`, `daeun`, `combinations_6`, `clashes`, `self_punishments`, `three_harmonies`, `half_harmonies`, `directional_harmonies`, `six_harms`, `six_breaks`, `three_punishments`.
- Strength and grid candidates (`strength_verdict`, `favorable_element`, `supporting_element`, `avoid_element`, `grid_candidates`, `special_form_candidates`).
- Current luck windows (`current_sewoon`, `current_woon`, `current_ilwoon`).

Everything is plain dataclasses/dicts, so it serializes cleanly to JSON for APIs or storage.

## Entry points

### From Python
```python
from saju_engine.engine import compute_chart

c = compute_chart(
    name="Example", gender="M",
    year=1993, month=12, day=11, hour=2, minute=45,
    longitude=79.32, utc_offset=5.5,
    use_solar_time=True, convention="korean",
)
print(c.day.combined)   # e.g. 丙辰
```

### From the CLI
```bash
PYTHONPATH=src python3 -m saju_engine \
  --date 1993-12-11 --time 02:45 --gender M --city "Pallipat" \
  --format table
```

Supported formats: `table`, `json`, `skeleton`, `premium`. Premium supports `--tier {sample,essential,deep,companion,spark,reading,fullmap}`.

## Design principles

1. **No invented rules.** All interpretive rules live in `knowledge/`. Engine code only implements deterministic lookup and derivation.
2. **No speculation in output.** Engine-generated prose is marked `[ENGINE DRAFT — REVIEW REQUIRED]` until a human reader verifies it.
3. **Backward compatibility.** Legacy tier names (`spark`, `reading`, `fullmap`) still map to the new landing-page products.
4. **Convention-aware.** The engine exposes Korean vs. Chinese Zi-hour conventions as a first-class parameter, not an afterthought.

## Source anchors

- `src/saju_engine/engine.py`
- `src/saju_engine/pillars.py`
- `src/saju_engine/chart.py`
- `src/saju_engine/lookup.py`
- `src/saju_engine/daeun.py`
- `src/saju_engine/compat.py`
- `knowledge/09-interpretation-method.md`
- `knowledge/11-gunghap.md`
