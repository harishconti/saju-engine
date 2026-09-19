"""W3 lookups harness — fixture-driven cross-validation.

See docs/superpowers/specs/2026-09-13-engine-validation-campaign-design.md.
Ground truth: the classical lookup tables in knowledge/ (연해자평 ten-god
framework, 12운성 stage tables, 납음오행 30-nayin table, 공망 旬 rule),
cross-checked against independent Korean references (Plan 3 Task 4).
Appending fixture entries auto-extends the suite.
"""
from __future__ import annotations

import pytest

from saju_engine.lookup import BRANCH_ORDER, STEM_INFO
from saju_engine.validation import load_fixtures, run_lookups_fixture

ENTRIES = load_fixtures("lookups")
STEMS = list(STEM_INFO)
BRANCHES = list(BRANCH_ORDER)


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_lookups_fixture(entry):
    result = run_lookups_fixture(entry)
    if entry["status"] == "documented_interpretation" and result["status"] != "PASS":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]


def test_coverage_exhaustive():
    """The lookups fixtures must cover every cell of all four lookup tables."""
    ten_god = [e for e in ENTRIES if e["input"]["lookup"] == "ten_god"]
    stage = [e for e in ENTRIES if e["input"]["lookup"] == "twelve_stage"]
    nayin = [e for e in ENTRIES if e["input"]["lookup"] == "nayin"]
    xun = [e for e in ENTRIES if e["input"]["lookup"] == "xunkong"]

    # 십신: one row per Day Master, each row covering all 10 stems.
    assert {e["input"]["day_master"] for e in ten_god} == set(STEMS)
    for e in ten_god:
        assert set(e["expected"]["gods"]) == set(STEMS)
    # 12운성: one row per Day Master, each row covering all 12 branches.
    assert {e["input"]["day_master"] for e in stage} == set(STEMS)
    for e in stage:
        assert set(e["expected"]["stages"]) == set(BRANCHES)
    # Nayin: all 30 categories, whose jiazi partition all 60 cycle pairs.
    assert len({e["input"]["nayin"] for e in nayin}) == 30
    pairs = [tuple(p) for e in nayin for p in e["expected"]["jiazi"]]
    assert len(pairs) == 60 and len(set(pairs)) == 60
    # 空亡: all six 旬 blocks.
    assert {e["input"]["xun_start"] for e in xun} == {
        "甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"}