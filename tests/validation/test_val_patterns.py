"""W8 격국 harness — fixture-driven cross-validation of patterns.detect_patterns
via compute_chart. Ground truth: knowledge/07-special-formations.md Part 1, each
fixture cross-checked against an independent Korean reference."""
from __future__ import annotations

import copy

import pytest

from saju_engine.validation import load_fixtures, run_patterns_fixture

ENTRIES = load_fixtures("patterns")


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_patterns_fixture(entry):
    result = run_patterns_fixture(entry)
    if entry["status"] == "documented_interpretation" and result["status"] != "PASS":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]


def test_unknown_input_key_raises():
    entry = copy.deepcopy(ENTRIES[0])
    entry["input"]["bogus"] = 1
    with pytest.raises(ValueError):
        run_patterns_fixture(entry)


def test_unknown_pattern_key_raises():
    entry = copy.deepcopy(ENTRIES[0])
    entry["expected"]["patterns"] = {"not_a_pattern": True}
    with pytest.raises(ValueError):
        run_patterns_fixture(entry)


# Patterns the engine can emit but that no compute_chart birth can reach, or
# that the engine does not implement. Each needs a comment + report mention.
UNREACHABLE = {
    # 종격 at confidence "likely" needs strength verdict extreme_weak, which
    # compute_chart never produces (same as strength `extreme_weak`); only the
    # "possible" 종격 candidates are reachable, and those are fixtured.
    "special_forms_likely",
    # 방합국 (cardinal-direction frame): knowledge/02 documents 방합 but
    # patterns.detect_structural_notes has no 방합국 detector.
    "방합국",
}


def test_coverage_every_documented_pattern():
    """≥1 positive fixture for each pattern that is reachable via compute_chart."""
    exps = [e["expected"]["patterns"] for e in ENTRIES if e["status"] == "expect_match"]
    assert any(x.get("regular_grid_name") for x in exps), "regular grid"
    assert any(x.get("yangin_grid") for x in exps), "양인격"
    assert any(x.get("jianlu_grid") for x in exps), "건록격"
    assert any(x.get("transformation_grid") for x in exps), "화격"
    assert any(x.get("special_forms_names") for x in exps), "종격"
    assert any("삼합국" in x.get("structural_notes_kinds", []) for x in exps), "삼합국"
    assert any("상관견관" in x.get("tengod_conflicts_names", []) for x in exps), "상관견관"
    # every one of the ten regular grids is exercised
    names = {x["regular_grid_name"] for x in exps if x.get("regular_grid_name")}
    assert names >= {"비견격", "겁재격", "식신격", "상관격", "편재격",
                     "정재격", "편관격", "정관격", "편인격", "정인격"}, sorted(names)
    # the declared UNREACHABLE set is not silently covered
    asserted = {k for x in exps for k in x} | {
        n for x in exps for n in x.get("structural_notes_kinds", [])}
    assert not (UNREACHABLE & asserted), UNREACHABLE & asserted
