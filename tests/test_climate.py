"""Tests for the 조후 (climate/temperature-balance) cross-check module."""
from __future__ import annotations

import pytest

from saju_engine.climate import assess_climate


@pytest.mark.parametrize("branch", ["巳", "午", "未"])
def test_hot_branches_favor_water(branch):
    result = assess_climate(branch)
    assert result["band"] == "hot"
    assert result["climate_favorable"] == "Water"
    assert result["climate_supporting"] == "Metal"


@pytest.mark.parametrize("branch", ["亥", "子", "丑"])
def test_cold_branches_favor_fire(branch):
    result = assess_climate(branch)
    assert result["band"] == "cold"
    assert result["climate_favorable"] == "Fire"
    assert result["climate_supporting"] == "Wood"


@pytest.mark.parametrize("branch", ["寅", "卯", "申", "酉"])
def test_temperate_branches_have_no_override(branch):
    """No 조후 override for the four "true" spring/autumn months.

    辰 and 戌 are NOT in this list — as of 2026-09-19 they carry their own
    燥/濕 (dry/damp) remedy via the four-axis model (see
    test_damp_branch_favors_fire / test_dry_branch_favors_water below), per
    the sourced table in knowledge/17-climate-method.md §The Fuller 寒暖燥濕
    Reading (docs/research/2026-09-validation-climate.md §3).
    """
    result = assess_climate(branch)
    assert result["band"] == "temperate"
    assert result["climate_favorable"] is None
    assert result["climate_supporting"] is None


def test_damp_branch_favors_fire():
    """辰 (濕, damp) wants Fire, per the sourced 寒暖燥濕 four-axis reading."""
    result = assess_climate("辰")
    assert result["band"] == "damp"
    assert result["climate_favorable"] == "Fire"
    assert result["climate_supporting"] == "Wood"


def test_dry_branch_favors_water():
    """戌 (燥, dry) wants Water, per the sourced 寒暖燥濕 four-axis reading."""
    result = assess_climate("戌")
    assert result["band"] == "dry"
    assert result["climate_favorable"] == "Water"
    assert result["climate_supporting"] == "Metal"


def test_unknown_branch_is_temperate():
    """A missing/unrecognized branch must not crash — defaults to no override."""
    result = assess_climate("")
    assert result["band"] == "temperate"
    assert result["climate_favorable"] is None
