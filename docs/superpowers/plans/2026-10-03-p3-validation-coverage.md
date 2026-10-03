# P3 — Validation Coverage (신살 + 격국 gates, report hygiene, extreme_weak review) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Source:** audit `/mnt/data2/git_repos/research-engine/output/2026-10-01/saju-engine-audit-2026-10-01.md` §4.4 (gaps), §9 B7; tracker item P2-W (`extreme_weak` unreachable).

**Goal:** Put the engine's 신살 (`stars.py`) and 격국 (`patterns.py`) outputs under the same cited-fixture validation gate as pillars/daeun/compat; stop the validation report's embedded certification prose from going stale; produce a sourced analysis of the unreachable `extreme_weak` verdict for a user decision.

**Architecture:** Two new fixture subsystems (`stars`, `patterns`) with runners in `validation.py` that call `compute_chart` and compare a declared subset of `chart.stars` / `chart.patterns`. Fixtures cite `knowledge/07-special-formations.md` line ranges plus at least one independent Korean reference (the house standard used by `lookups.json`). The historical gate narrative moves from Python string literals to `docs/validation/gate-history.md`; `render_report` keeps only data.

**Tech Stack:** Python, pytest, JSON fixtures; WebSearch / firecrawl for external cross-checks.

## Global Constraints

- Test prefix: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages`
- Baseline: 1345 passed, 5 skipped, 9 xfailed; `tools/run_validation.py` 206 checks (PASS 202, INTERPRETATION 4, FAIL 0); golden snapshots (tests/golden/) byte-identical — this plan changes NO engine behaviour.
- **Ground rule (CLAUDE.md):** every expected value must be derivable from a `knowledge/` file; cite `knowledge/<file>.md:<lines>` in each fixture's `source`, plus ≥1 independent external reference (URL) checked on 2026-10-03. Never invent a rule. Where knowledge/ and external sources disagree, or the engine disagrees with knowledge/, record it — do not change the engine in this plan.
- Fixture `status`: `expect_match` when engine == knowledge/; `documented_interpretation` when the engine deliberately follows one school and the fixture documents the other (explain in `notes`); a genuine engine-vs-knowledge mismatch is left as `expect_match` and reported as a FAIL → it becomes a tracker bug, and the task reports DONE_WITH_CONCERNS (the gate must not be silenced).
- Branch: `test/p3-validation-coverage` off `develop`; one commit per task; messages end with a blank line + `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Don't touch `candidates_horoscope/` (user's uncommitted work).

---

### Task 1: `stars` fixture subsystem (신살 gate, W7)

**Files:**
- Modify: `src/saju_engine/validation.py` (runner, checker, registries `_SUBSYSTEM_ORDER`, `_WORKSTREAM`, `_RUNNERS`)
- Create: `tests/validation/fixtures/stars.json`, `tests/validation/test_val_stars.py`

**Interfaces:**
- Produces: `validation.check_stars(chart, entry) -> dict`, `validation.run_stars_fixture(entry) -> dict` (same result-dict shape as `check_daeun`: keys `id`, `subsystem`, `status` ∈ PASS/FAIL/INTERPRETATION, `detail`, … — copy the exact shape `check_daeun` returns).

**Fixture schema**
```json
{
  "id": "peach-blossom-day-anchor-yin-wu-xu",
  "subsystem": "stars",
  "input": { "year": 1990, "month": 6, "day": 15, "hour": 10, "minute": 0,
             "utc_offset": 9.0, "longitude": 127.0, "gender": "F" },
  "source": [
    {"citation": "knowledge/07-special-formations.md:166-183 — 도화살: 寅午戌 → 卯"},
    {"citation": "<external Korean reference title> (external cross-check 2026-10-03)", "url": "https://..."}
  ],
  "expected": { "stars": { "peach_blossom": ["卯"] } },
  "status": "expect_match",
  "notes": "Day branch 午 (寅午戌 triplet) → 도화 卯; chart contains 卯 in the hour branch."
}
```
`expected.stars` is a SUBSET: only listed keys are checked; each listed key's list must equal `chart.stars[key]` exactly (order-insensitive — compare sorted). An empty list asserts the star is NOT activated. Optional `input.star_anchor` (`"day"`/`"year"`) is allowed and passed to `compute_chart`.

- [ ] **Step 1: Runner tests first** (`tests/validation/test_val_stars.py`)

```python
"""W7 신살 harness — fixture-driven cross-validation of stars.derive_stars via
compute_chart. Ground truth: knowledge/07-special-formations.md Part 2, each
fixture cross-checked against an independent Korean reference."""
from __future__ import annotations

import copy

import pytest

from saju_engine.validation import load_fixtures, run_stars_fixture

ENTRIES = load_fixtures("stars")


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_stars_fixture(entry):
    result = run_stars_fixture(entry)
    if entry["status"] == "documented_interpretation" and result["status"] != "PASS":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]


def test_unknown_input_key_raises():
    entry = copy.deepcopy(ENTRIES[0])
    entry["input"]["bogus"] = 1
    with pytest.raises(ValueError):
        run_stars_fixture(entry)


def test_unknown_star_key_raises():
    entry = copy.deepcopy(ENTRIES[0])
    entry["expected"]["stars"] = {"not_a_star": []}
    with pytest.raises(ValueError):
        run_stars_fixture(entry)


def test_coverage_every_documented_star():
    """Every star implemented in stars.derive_stars that knowledge/07 Part 2
    documents has ≥1 positive fixture (non-empty expected list)."""
    positive = {k for e in ENTRIES for k, v in e["expected"]["stars"].items() if v}
    required = {
        "kong_mang", "peach_blossom", "post_horse", "canopy", "heavenly_noble",
        "literary_star", "deep_grudge", "ghost_gate", "white_tiger", "sky_hero",
        "heavenly_virtue", "monthly_virtue", "yangin", "hongyeom",
    }
    assert required <= positive, sorted(required - positive)
```
Run → FAIL (`stars.json` missing / `run_stars_fixture` undefined).

- [ ] **Step 2: Implement runner + checker in `validation.py`**

```python
_STARS_ALLOWED_INPUT = _ALLOWED_INPUT | {"star_anchor"}


def check_stars(chart: Any, entry: dict) -> dict:
    """Check a declared subset of chart.stars against a stars fixture.

    expected.stars: {star_key: [branches/stems/pillars]} — each listed key must
    equal chart.stars[key] (order-insensitive); an empty list asserts the star
    is not activated. Unlisted keys are not checked. Unknown keys raise.
    """
    exp = entry.get("expected", {}).get("stars") or {}
    unknown = set(exp) - set(chart.stars)
    if unknown:
        raise ValueError(f"stars/{entry['id']}: unknown star key(s) {sorted(unknown)}")
    mismatches = {
        k: {"expected": sorted(v), "got": sorted(chart.stars.get(k, []))}
        for k, v in exp.items() if sorted(v) != sorted(chart.stars.get(k, []))
    }
    return _result(entry, mismatches)   # see below


def run_stars_fixture(entry: dict) -> dict:
    unknown = set(entry["input"]) - _STARS_ALLOWED_INPUT
    if unknown:
        raise ValueError(f"stars/{entry['id']}: unknown input key(s) {sorted(unknown)}")
    kwargs = dict(entry["input"])
    kwargs.setdefault("name", entry["id"])
    return check_stars(compute_chart(**kwargs), entry)
```
`_result(entry, mismatches)`: if `validation.py` already has a helper that turns a mismatches dict into the result dict (look at the tail of `check_daeun`), reuse it; otherwise extract the tail of `check_daeun` into `_result` and make `check_daeun` call it (behaviour-identical). Register `"stars"` in `_SUBSYSTEM_ORDER` (append), `_WORKSTREAM["stars"] = "W7"`, `_RUNNERS["stars"] = run_stars_fixture`. Check that `compute_chart` accepts `star_anchor` (it does — `engine.py:239`).

- [ ] **Step 3: Author `stars.json` (research)**

For each required star (and the 십이신살 set where knowledge/07:253-285 documents it), author ≥1 positive fixture and, for the anchor-sensitive stars (도화/역마/화개), one `star_anchor: "year"` fixture. Method per fixture:
1. Read the rule in knowledge/07 (cite exact lines).
2. Pick a birth whose chart activates the star (scan `compute_chart` outputs with a throwaway script — not committed); record pillars in `notes`.
3. Cross-check the rule on ≥1 independent Korean reference (search e.g. "도화살 인오술 묘", "천을귀인 표", "괴강살 일주"); cite title + URL with "(external cross-check 2026-10-03)". Prefer the same reference families `lookups.json` already uses (sajumyth.com, sazasaju.com) when they cover the star.
4. If knowledge/07 and the engine disagree → keep `expect_match` (it will FAIL), record the discrepancy in the report; if knowledge/07 documents two schools and the engine follows one → `documented_interpretation` with `notes`.
Target: ~20–30 entries. Also add 3 negative fixtures (empty list = not activated) for stars whose trigger is absent.

- [ ] **Step 4: Verify** — `pytest tests/validation/test_val_stars.py -v`; `tools/run_validation.py` (new total = 206 + N; FAIL must be 0 unless a real engine-vs-knowledge mismatch was found — then DONE_WITH_CONCERNS with details); full suite; golden test unchanged.
- [ ] **Step 5: Commit** — `test(validation): W7 신살 fixture gate (stars)`

---

### Task 2: `patterns` fixture subsystem (격국 gate, W8)

**Files:** `src/saju_engine/validation.py`, `tests/validation/fixtures/patterns.json`, `tests/validation/test_val_patterns.py`

**Interfaces:** Produces `check_patterns(chart, entry)`, `run_patterns_fixture(entry)`; reuses `_result` from Task 1.

**What `chart.patterns` holds:** the dict returned by `patterns.detect_patterns` (`patterns.py:594-603` docstring: `regular_grid`, `yangin`, `jianlu`, `stem_combinations`, `transformation_grid`, `special_forms`, `structural_notes`, `tengod_conflicts`, `dominant_element`, `element_balance`). Read `chart._patterns_dict` (`chart.py:456`) for the JSON-serialisable shape and compare against THAT shape.

**Fixture `expected.patterns` (subset, declarative):**
```json
"expected": { "patterns": {
  "regular_grid_name": "정관격",
  "yangin": true,
  "jianlu": false,
  "transformation_grid": null,
  "special_forms_names": [],
  "structural_notes_kinds": ["삼합국"]
}}
```
Supported keys (each optional): `regular_grid_name` (name of the top `regular_grid` candidate), `yangin` (bool — evidence present), `jianlu` (bool), `transformation_grid` (name or null), `special_forms_names` (sorted list of names), `structural_notes_kinds` (sorted list), `tengod_conflicts_names` (sorted list). Define each extractor in `check_patterns` from the `_patterns_dict` shape; an unknown expected key raises.

- [ ] **Step 1: Tests first** — same four tests as Task 1 adapted (`run_patterns_fixture`; coverage test requires ≥1 positive fixture for each of: a regular grid via 투출 (`regular_grid_name` non-null), 양인격 (`yangin: true`), 건록격 (`jianlu: true`), 화격 (`transformation_grid` non-null), 종격 (`special_forms_names` non-empty) if reachable, 삼합국/방합국 structural note, 상관견관 conflict). If a pattern is unreachable through `compute_chart` (as `extreme_weak` is), the coverage test lists it in an explicit `UNREACHABLE = {...}` set with a comment, and the report says so.
- [ ] **Step 2: Implement** `check_patterns` / `run_patterns_fixture`; register `"patterns"` → W8.
- [ ] **Step 3: Author `patterns.json`** — same research method as Task 1 Step 3, citing knowledge/07 Part 1 lines (정격 16-52, 종격 57-74, 화격 75-99, 양인격 100-130, 건록격 131-153) and an external reference. Include the three textbook charts already used by the engine (박정희 1917-11-14 10:00 M lon 128.74; 노무현; 김대중 — inputs in `tests/validation/fixtures/daeun.json`) where published sources name their 격국; if sources disagree with each other, use `documented_interpretation` and record both.
- [ ] **Step 4: Verify** (as Task 1) — **Step 5: Commit** `test(validation): W8 격국 fixture gate (patterns)`

---

### Task 3: Validation report hygiene — gate history out of source

**Files:**
- Create: `docs/validation/gate-history.md`
- Modify: `src/saju_engine/validation.py` (`_GATE_HISTORY` notes, `render_report` embedded narrative ~`:919-992, :1025-1139` at plan time), `tests/validation/test_run_validation.py` if it asserts on removed text

- [ ] **Step 1:** Move every long narrative `note` string in `_GATE_HISTORY` and every hard-coded certification paragraph in `render_report` into `docs/validation/gate-history.md` (one section per workstream, verbatim, dated). Keep `_GATE_HISTORY` as data only: `workstream`, `gate_date`, `checks`, `passed`, and a short ≤1-line `note`. Add W7/W8 entries with today's gate date and their measured counts.
- [ ] **Step 2:** `render_report` emits: live per-subsystem tables (as today), the `_GATE_HISTORY` table, and one line: "Full certification history: docs/validation/gate-history.md". Live totals stay derived from the run (never literals).
- [ ] **Step 3:** Test: `tests/validation/test_run_validation.py` — add `test_report_has_no_frozen_narrative`: render the report and assert its length is below a bound (e.g. < 60% of the pre-change length, measured once and hard-coded with a comment) and that it contains the gate-history link. Update any existing assertion that depended on moved text to check the doc instead.
- [ ] **Step 4:** Verify — validation exit 0 with same counts; full suite. **Commit** `refactor(validation): move certification narrative to docs/validation/gate-history.md`

---

### Task 4: `extreme_weak` doctrine analysis (no engine change)

**Files:** Create `docs/analysis/2026-10-03-extreme-weak-verdict.md`

- [ ] **Step 1:** Measure: a throwaway scan over ≥50k `compute_chart` births (1930–2030, all hours, KST) recording `strength_assessment["total_score"]`; report min, 0.1/1/5 percentiles, and the count ≤ each of −3.0/−3.5/−4.0/−4.5/−5.0. Same for the upper tail vs the `extreme` threshold, to show the asymmetry.
- [ ] **Step 2:** Doctrine: read `strength.py` (score formula + thresholds and their comments/citations), `knowledge/` strength material (grep `신약`, `극신약`, `종격`, `extreme` across knowledge/), and `knowledge/07-special-formations.md:57-74` (종격 — a chart too weak to stand). State what knowledge/ actually says about a "very weak" class and how it relates to 종격.
- [ ] **Step 3:** Options for the user, each with consequences (which reports/labels/용신 paths change, golden impact): (A) leave as-is, document as unreachable; (B) recalibrate the `extreme_weak` threshold symmetric to the observed distribution (e.g. the percentile mirroring how often `extreme` fires); (C) route very-weak charts to the 종격 candidate check only, removing the label. Recommend one, grounded in knowledge/ citations. No code changes.
- [ ] **Step 4:** Commit `docs: extreme_weak verdict analysis (P2-W)`.

---

### Task 5: Docs + tracker

- [ ] `docs/issues_bugs.md`: B7 FIXED (stars + patterns gates, SHAs); §4.4 stale-prose item FIXED; P2-W → "ANALYSED — awaiting user decision (docs/analysis/2026-10-03-extreme-weak-verdict.md)"; add any engine-vs-knowledge FAILs found in Tasks 1–2 as new OPEN bugs.
- [ ] `docs/MEMORY.md`: validation gate now 10 subsystems (W7 stars, W8 patterns added); how to add a stars/patterns fixture (schema pointer).
- [ ] `docs/openwiki/operations/toolchain-and-testing.md`: list the new fixture files.
- [ ] Full suite + validation; commit `docs: record P3 validation coverage`.
