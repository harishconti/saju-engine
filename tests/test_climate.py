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


@pytest.mark.parametrize("branch", ["寅", "卯", "辰", "申", "酉", "戌"])
def test_temperate_branches_have_no_override(branch):
    """No 조후 override for spring/autumn months — including the two storage
    months (辰, 戌) the fuller 寒暖燥濕 reading would give a remedy to.

    辰 (濕) and 戌 (燥) are the pinned divergence, not an oversight: the engine
    implements the 寒暖 (hot/cold) axis only, and widening it moves the
    client-facing ``band`` value. See knowledge/17-climate-method.md §The Fuller
    寒暖燥濕 Reading. If that scope ever widens, THIS test is the signal — it is
    the unit-level half of the pin whose fixture half is band-chen / band-xu.
    """
    result = assess_climate(branch)
    assert result["band"] == "temperate"
    assert result["climate_favorable"] is None
    assert result["climate_supporting"] is None


def test_unknown_branch_is_temperate():
    """A missing/unrecognized branch must not crash — defaults to no override."""
    result = assess_climate("")
    assert result["band"] == "temperate"
    assert result["climate_favorable"] is None
