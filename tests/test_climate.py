"""Tests for the 조후 (climate/temperature-balance) cross-check module."""
from __future__ import annotations

import pytest

from saju_engine.climate import (
    assess_climate,
    climate_temperature,
    is_climate_extreme,
    is_remedy_dominant,
)


class _P:
    """Minimal pillar stand-in for climate_temperature()."""
    def __init__(self, stem, branch, hidden=()):
        self.stem = stem
        self.branch = branch
        self.hidden_stems = list(hidden)


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


# ── N-6 remedy-dominance guard (2026-09-26) ──────────────────────────────────


def test_remedy_dominant_true_when_remedy_is_most_abundant():
    """戌 (dry → Water): a Water-dominant chart must be flagged, so the 조후
    override can be withheld (adding Water cannot balance the chart)."""
    counts = {"Water": 2.7, "Earth": 1.8, "Fire": 1.6, "Metal": 1.5, "Wood": 0.3}
    assert is_remedy_dominant("戌", counts) is True


def test_remedy_dominant_false_when_another_element_leads():
    """A dry month whose chart is Fire-dominant still genuinely needs Water."""
    counts = {"Fire": 2.9, "Metal": 1.4, "Water": 1.2, "Wood": 1.0, "Earth": 0.7}
    assert is_remedy_dominant("戌", counts) is False


def test_remedy_dominant_false_for_temperate_month():
    """No remedy → nothing to gate, never dominant."""
    counts = {"Water": 3.0, "Fire": 0.1}
    assert is_remedy_dominant("酉", counts) is False


def test_remedy_dominant_false_without_counts():
    """Missing/empty counts must not suppress on absent data."""
    assert is_remedy_dominant("戌", None) is False
    assert is_remedy_dominant("戌", {}) is False


# ── N-6 whole-chart temperature gate (industry standard, 2026-09-26) ─────────


def test_climate_temperature_warm_vs_cool_sign():
    """A warm-dominant chart scores positive; a cool-dominant chart negative.

    Uses the 사주플러스 per-character assignment (stems 한 甲辛壬癸 / 난 乙丙丁庚;
    branches 한 寅酉戌亥子丑 / 난 卯辰巳午未申)."""
    warm = [_P("丙", "午"), _P("乙", "巳"), _P("丙", "未"), _P("乙", "卯")]
    cool = [_P("壬", "子"), _P("癸", "亥"), _P("辛", "酉"), _P("癸", "丑")]
    assert climate_temperature(warm) > 0
    assert climate_temperature(cool) < 0


def test_climate_temperature_weights_month_and_hour_branches_more():
    """Per 8-codes, the month/hour branches carry more weight than year/day.

    Start from a cool chart (all 丑 branches) and warm one branch at a time;
    warming the month (weight 2.0) must move the score more than warming the
    day (weight 1.0)."""
    base = [_P("戊", "丑"), _P("戊", "丑"), _P("戊", "丑"), _P("戊", "丑")]
    month_hot = [_P("戊", "丑"), _P("戊", "午"), _P("戊", "丑"), _P("戊", "丑")]
    day_hot = [_P("戊", "丑"), _P("戊", "丑"), _P("戊", "午"), _P("戊", "丑")]
    month_delta = climate_temperature(month_hot) - climate_temperature(base)
    day_delta = climate_temperature(day_hot) - climate_temperature(base)
    assert month_delta > day_delta > 0


def test_direction_gate_suppresses_hot_month_on_cool_chart():
    """A hot month whose whole chart leans cool is not 'too hot' — override off."""
    assert is_climate_extreme("巳", -5.5) is False


def test_direction_gate_allows_hot_month_on_warm_chart():
    assert is_climate_extreme("午", 5.0) is True
    assert is_climate_extreme("子", -4.0) is True


def test_direction_gate_false_for_temperate_month():
    assert is_climate_extreme("酉", 9.0) is False


def test_direction_gate_has_no_temperature_opinion_for_damp_dry():
    """辰/戌 are the 燥濕 (humidity) axis — a temperature score cannot judge them,
    so the direction gate passes them through for the dominance guard to handle."""
    assert is_climate_extreme("辰", 9.0) is True
    assert is_climate_extreme("戌", -9.0) is True
