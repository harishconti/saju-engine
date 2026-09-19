# Engine Validation Campaign — Design (2026-09-13)

## Goal

Revalidate every subsystem of the Saju engine against external ground truth, using a
sequential per-subsystem campaign with hard completion gates. The outcome is a
**validation harness + report** — not a fix campaign. Bugs found are logged and
prioritized separately.

Approved approach: **Approach 1 (sequential per-subsystem)**, over research fan-out
(Approach 2) and two-track (Approach 3), because interpretive expected values depend on
pillar correctness — only a sequential ordering makes a "pass" trustworthy.

## Deliverables

1. `tests/validation/fixtures/*.json` — cited ground-truth fixtures per subsystem
   (`pillars.json`, `daeun.json`, `lookups.json`, `yongsin.json`, `climate.json`,
   `compat.json`, `career.json`)
2. `tests/validation/test_val_*.py` — harness pytest modules (one per workstream)
3. `tools/run_validation.py` — runs all fixtures, emits the report
4. `docs/audits/2026-09-engine-validation-report.md` — per-workstream matrices + scorecard
5. `docs/research/2026-09-validation-<subsystem>.md` — deep sourced research per
   interpretive workstream (W4–W6), market-research style with quotes and citations
6. Regression locks for Phase-0/1/2 fixes (daeun floor, climate merge, compat routing)

## Harness Architecture

### Fixture schema

```json
{
  "id": "example-chart-001",
  "input": {"date": "1985-04-21", "time": "06:10", "city": "Seoul",
             "utc_offset": 9.0, "gender": "M"},
  "source": {"type": "web", "citation": "만세력 tool X",
             "url_or_ref": "..."},
  "expected": {"pillars": {"day": "갑오"}},
  "notes": "school disagreement recorded here, if any"
}
```

- One JSON file per workstream. The 10 textbook cases migrate from hard-coded inline
  values in `test_textbook_cases.py` into `pillars.json` / `daeun.json` (tests stay;
  values become cited data).

### Check statuses

Three statuses per check (the key design decision for interpretive work):

- **PASS** — engine matches ground truth
- **INTERPRETATION** — engine follows the cited classical rule correctly; the external
  source differs because of a school/method difference → documented in `notes`, not a failure
- **FAIL** — engine bug or unsupported rule → logged for later fixing

### Report

`docs/audits/2026-09-engine-validation-report.md`, one section per workstream: pass/fail/
disagreement matrix, inline source citations, summary scorecard at the top.

## Corpus

10 published figures + 12 candidate charts already in tests + ~20–30 edge-stratified
additions (~40–50 charts total). Edge additions stress: births within ±10 min of hour
boundaries, births within ±1 day of 절기 edges (leap months included), DST-era
historical dates, extreme element imbalance, special formations (합/충/형/파/해).

## Workstreams

| # | Subsystem | Checks | Sources |
|---|---|---|---|
| W1 | Pillars | year/month/day/hour pillars, 절기 month boundary, solar-time adjustment, 子時 hour-boundary convention, korean/chinese convention flag | 10 published-figure charts + web 만세력 tools (browser automation, screenshots as evidence). W1–W2 fixtures need ≥2 independent source agreements for PASS |
| W2 | Luck pillars (대운/세운) | 대운 direction (gender-year parity), start age (daeun-floor regression lock), pillar sequence, 세운/월운 year boundaries | published-figure 대운 tables + textbook cases |
| W3 | Derived lookups | 십신 (all 10 stem pairs), 12운성 cycle per stem-branch, Nayin 30×30 pairs, 空亡 | classical tables in `knowledge/` (연해자평) cross-checked against 2–3 independent Korean references from research |
| W4 | Favorable element (용신) | merge logic (strength + climate + reader override); final verdicts vs published readings + our own `knowledge/09-interpretation-method.md` derivation | PASS requires agreement with ≥2 independent sources or a cited classical argument |
| W5 | Climate (조후) | season/climate score per chart; cross-check's effect on 용신 for the corpus | 궁통보감-based rules per `knowledge/17-climate-method.md` + sourced classical commentary examples |
| W6 | Compat / spouse + career | 11 compat sub-systems, favorable-spouse signals (day-branch relations), career-domain tiers | `knowledge/11-gunghap.md` + `knowledge/12-career-and-vocation.md` rule base; deep research into 명리정종, 자평진전, 서전구미록, 권인성·곽임성·정봉재·송기영 to confirm each sub-system rule as implemented |

Known compat.py dead-code/weight issues from the 2026-08 audit get regression-checked in W6.

## Execution Order & Gates

W1 → W2 → W3 → W4 → W5 → W6, hard gate between each: W_n does not start until W_(n−1)
is certified — all FAILs resolved or accepted as documented INTERPRETATION, and the report
section written. Research agents for W_(n+1) may read-only prefetch while W_n runs, but no
expected values are locked until the prior gate passes.

## Source Plan

- **Web 만세력 tools:** browser automation against 2–3 independent public Korean 만세력
  sites; screenshot + URL captured into each fixture's `source` field. Every fixture cites
  ≥1 external source; W1–W2 need ≥2 independent agreements for PASS.
- **Deep sourced research (W4–W6):** one research doc per subsystem covering classical
  texts (적천수, 연해자평, 궁통보감, 명리정종) and modern Korean schools, with quotes and
  citations. Research agents gather; the interpreter compares rule vs engine.
- **Classical rule base:** `knowledge/` files remain the auditable bridge — every engine
  rule checked must trace to a cited passage.

## Exit Criteria

Per workstream: 100% of corpus checks are PASS or documented INTERPRETATION with ≥1
external citation; no FAIL open without an explicit accepted-in-notes rationale.
Overall: full suite (existing 649 tests + new harness) green; report committed.

## Out of Scope

- Bug fixes found by the harness (logged and prioritized separately)
- The stale Harish follow-up rewrites
- Any new engine features
- Known-bug fixes (premium_report stale `candidate_favorable`, compat-PDF output path,
  stale Harish follow-ups) — but regression checks for these are written into the harness

## Known Open Bugs Tracked

1. `premium_report.py` "What This Year Means": `_right_now_callout()` (~L181) and
   `ctx_favorable_phrase()` (~L1394) read stale `strength_assessment["candidate_favorable"]`
   instead of resolved `favorable_element()` — live-wrong in published reports.
2. `src/saju_html/md_to_saju_compat_pdf.py` default `--output` writes to stray
   `src/candidates_horoscope/` (workaround: pass `--output` explicitly).
3. Stale Harish `career.md` / `land-workshop-business.md` / `luck-timeline.md` argue old
   Fire/Wood 용신.