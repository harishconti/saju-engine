"""Tests for major-luck (대운) activation overlay."""
from __future__ import annotations

from saju_engine.chart import DaeunPeriod
from saju_engine.daeun_overlay import derive_daeun_overlay, build_daeun_overlays
from saju_engine.engine import compute_chart


def test_daeun_overlay_ten_god_and_branch_relationship():
    """Overlay should tag ten-god and detect a known branch relationship."""
    period = DaeunPeriod(start_age=10, end_age=19, stem="庚", branch="申")
    overlay = derive_daeun_overlay(
        day_master="丙",
        natal_branches=["午", "寅", "亥"],
        natal_stems=["壬", "甲", "丙", "戊"],
        strength_assessment={
            "candidate_favorable": "Earth",
            "candidate_unfavorable": "Water",
        },
        period=period,
    )
    # 庚 to 丙 day master → 편재 (Indirect Wealth)
    assert overlay["stem_tengod"] == "편재"
    assert "Indirect Wealth" in overlay["stem_tengod_en"]
    # 申 vs 寅 is a 六沖 clash
    assert any(rel == "clash" for _, _, rel in overlay["activated_branches"])
    # 庚/申 elements are Metal → neutral vs Earth favorable / Water unfavorable
    assert overlay["favorable_status"] == "neutral"


def test_daeun_overlay_stem_combination_and_favorable():
    """천간합 and element favorability should both be flagged."""
    period = DaeunPeriod(start_age=20, end_age=29, stem="甲", branch="戌")
    overlay = derive_daeun_overlay(
        day_master="己",
        natal_branches=["子", "丑"],
        natal_stems=["己", "丙", "丁", "戊"],
        strength_assessment={
            "candidate_favorable": "Earth",
            "candidate_unfavorable": "Wood",
        },
        period=period,
    )
    # 甲 + 己 is 천간합 → 甲己合土
    assert overlay["stem_combinations"]
    assert any(c["combined_element"] == "Earth" for c in overlay["stem_combinations"])
    # 甲 (Wood) matches candidate_unfavorable, 戌 (Earth) matches candidate_favorable.
    # Earth favorable wins → favorable.
    assert overlay["favorable_status"] == "favorable"


def test_build_daeun_overlays_populates_periods():
    """build_daeun_overlays should mutate periods in place and return them."""
    periods = [
        DaeunPeriod(start_age=0, end_age=9, stem="癸", branch="亥"),
        DaeunPeriod(start_age=10, end_age=19, stem="壬", branch="戌"),
    ]
    result = build_daeun_overlays(
        day_master="丁",
        natal_branches=["卯", "巳"],
        natal_stems=["丁", "乙", "己", "辛"],
        strength_assessment=None,
        periods=periods,
    )
    assert result is periods
    for p in periods:
        assert p.stem_tengod
        assert p.stem_tengod_en
        assert p.favorable_status is None  # no strength assessment provided


def test_engine_populates_daeun_overlay():
    """compute_chart should attach overlays to every 대운 period."""
    c = compute_chart(
        name="Tester", gender="F",
        year=1993, month=12, day=11, hour=10, minute=0,
        city="Seoul", utc_offset=9, use_solar_time=True,
    )
    assert c.daeun
    for p in c.daeun:
        assert p.stem_tengod, f"대운 {p.combined} missing stem_tengod"
        assert p.stem_tengod_en
        assert p.stem_element
        assert p.branch_element
        assert p.favorable_status in ("favorable", "unfavorable", "neutral")
