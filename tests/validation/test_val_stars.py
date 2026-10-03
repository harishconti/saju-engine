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


def test_invalid_star_anchor_raises():
    entry = copy.deepcopy(ENTRIES[0])
    entry["input"]["star_anchor"] = "month"
    with pytest.raises(ValueError, match="star_anchor"):
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
