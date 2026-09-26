"""Regression tests for natal branch-relationship detection."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from saju_engine.engine import _derive_branch_relationships
from saju_engine.chart import Chart, Pillar


def _make_chart(branches: list[str]) -> Chart:
    """Build a minimal Chart with the given branch order (year/month/day/hour)."""
    stems = ["甲", "乙", "丙", "丁"]
    chart = Chart(
        year=Pillar(position="year", stem=stems[0], branch=branches[0]),
        month=Pillar(position="month", stem=stems[1], branch=branches[1]),
        day=Pillar(position="day", stem=stems[2], branch=branches[2]),
        hour=Pillar(position="hour", stem=stems[3], branch=branches[3]),
    )
    return chart


def test_half_harmony_detected_when_two_of_three_samhap_present():
    """A chart with 寅 + 午 (no 戌) should record a 반합 in the Fire frame."""
    chart = _make_chart(["寅", "子", "午", "亥"])
    _derive_branch_relationships(chart)
    assert any(
        frame == "寅午戌" and elem == "Fire"
        for _, _, frame, elem in chart.half_harmonies
    ), chart.half_harmonies


def test_full_samhap_not_duplicated_as_half_harmony():
    """A chart with all three 삼합 branches should only record the full harmony."""
    chart = _make_chart(["寅", "午", "戌", "子"])
    _derive_branch_relationships(chart)
    assert chart.three_harmonies == [("寅", "午", "戌", "Fire")]
    assert chart.half_harmonies == []


def test_directional_harmony_full_triple_detected():
    """A chart with 巳 + 午 + 未 should record a 방합 (Fire / South)."""
    chart = _make_chart(["巳", "午", "未", "子"])
    _derive_branch_relationships(chart)
    assert chart.directional_harmonies == [("巳", "午", "未", "Fire / South")]


def test_pairwise_three_punishment_detected():
    """A chart with 寅 + 巳 (no 申) should record a pairwise 삼형."""
    chart = _make_chart(["寅", "子", "巳", "亥"])
    _derive_branch_relationships(chart)
    assert any(
        a == "寅" and b == "巳" and c == "—"
        for a, b, c, _ in chart.three_punishments
    ), chart.three_punishments


def test_full_three_punishment_not_duplicated_as_pairwise():
    """A chart with all three 寅巳申 branches should record only the full triple."""
    chart = _make_chart(["寅", "巳", "申", "子"])
    _derive_branch_relationships(chart)
    full = [t for t in chart.three_punishments if t[2] != "—"]
    pairwise = [t for t in chart.three_punishments if t[2] == "—"]
    assert len(full) == 1
    assert pairwise == []


def test_repeated_branch_does_not_duplicate_pairwise_punishment():
    """N-20 (2026-09-26 audit): a repeated branch matches the same 삼형 frame
    via more than one pillar pair — 丑寅丑未 (year/day both 丑, hour 未) hits
    the 丑戌未 frame through both the (year, hour) and (day, hour) pairs — so
    the identical 丑未 pairwise entry must appear only once, not twice."""
    chart = _make_chart(["丑", "寅", "丑", "未"])
    _derive_branch_relationships(chart)
    pairwise = [t for t in chart.three_punishments if t[2] == "—"]
    matches = [t for t in pairwise if {t[0], t[1]} == {"丑", "未"}]
    assert len(matches) == 1, chart.three_punishments


def test_zimao_punishment_still_detected():
    """The two-member 子卯 punishment is still captured."""
    chart = _make_chart(["子", "卯", "寅", "亥"])
    _derive_branch_relationships(chart)
    assert any(
        a == "子" and b == "卯" and c == "—"
        for a, b, c, _ in chart.three_punishments
    ), chart.three_punishments
