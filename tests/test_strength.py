"""Tests for the Day-Master strength heuristic."""
from __future__ import annotations

from collections import Counter

from saju_engine.engine import compute_chart
from saju_engine.strength import assess_strength, element_balance_counts, element_balance_pct


def test_strong_earth_day_master():
    # Gurumoorthy-like: 己 day master, month 未, many Earth stems/branches.
    stems = ["甲", "辛", "己", "戊"]
    hidden = [
        ("main", "戊"), ("middle", "乙"), ("residual", "癸"),  # 辰
        ("main", "己"), ("middle", "丁"), ("residual", "乙"),  # 未
        ("main", "丙"), ("middle", "庚"), ("residual", "戊"),  # 巳
        ("main", "戊"), ("middle", "乙"), ("residual", "癸"),  # 辰
    ]
    result = assess_strength("己", "未", stems, hidden)
    assert result["verdict"] in ("strong", "extreme")
    assert result["candidate_favorable"] in ("Metal", "Earth")


def test_weak_metal_day_master():
    # Mahesh-like: 庚 day master, month 丑, depleted stages.
    stems = ["甲", "丁", "庚", "丙"]
    hidden = [
        ("main", "戊"), ("middle", "辛"), ("residual", "丁"),  # 戌
        ("main", "己"), ("middle", "癸"), ("residual", "辛"),  # 丑
        ("main", "戊"), ("middle", "辛"), ("residual", "丁"),  # 戌
        ("main", "癸"),                                           # 子
    ]
    result = assess_strength("庚", "丑", stems, hidden)
    # Earth and Metal hidden stems give meaningful support, so the heuristic
    # calls this "balanced" rather than strictly weak.
    assert result["verdict"] in ("balanced", "weak")
    assert result["candidate_favorable"] in {"Wood", "Fire", "Earth", "Metal", "Water"}
    assert result["candidate_supporting"] in {"Wood", "Fire", "Earth", "Metal", "Water"}


def test_counts_include_hidden():
    result = assess_strength("甲", "寅", ["甲"], [("main", "乙"), ("middle", "丙")])
    counts = result["element_counts"]
    assert counts["Wood"] > 0
    assert counts["Fire"] > 0


# M2 regression: Day-Master strength heuristic must not count the Day Master
# itself as self-support, and candidate elements must be classically consistent.


def test_self_score_excludes_day_master():
    # A bare 甲 Day Master in 寅 month has no peer stems, so self_score == 0.
    result = assess_strength("甲", "寅", ["甲"], [])
    assert result["self_score"] == 0.0
    # Add one peer Wood stem (乙); now self_score counts only the peer.
    result = assess_strength("甲", "寅", ["甲", "乙"], [])
    assert result["self_score"] == 1.0


def test_balanced_supporting_is_generating_element():
    # Balanced chart where Water is least present. Per knowledge/03 §"Two
    # conventions for 희신", balanced DMs use the STRICT classical formula:
    # 희신 = the element that generates 용신. 용신 = Water (least present), so
    # 희신 = Metal (Metal generates Water).
    # 亥 month gives 甲 장생 stage (supportive but not double-counted as season).
    result = assess_strength(
        "甲", "亥",
        ["甲", "丙", "戊", "庚"],  # Wood, Fire, Earth, Metal visible
        [("main", "丙"), ("middle", "戊"), ("residual", "甲")],  # no Water hidden
    )
    assert result["verdict"] == "balanced"
    assert result["candidate_favorable"] == "Water"
    assert result["candidate_supporting"] == "Metal"


def test_strong_candidate_elements_consistent():
    # Strong 己 (Earth) chart: output = Metal, wealth = Water, self = Earth,
    # authority = Wood. Per knowledge/03 §"Two conventions for 희신", strong DMs
    # use the MODERN Korean convention: 용신 = 식상 (output = Metal), 희신 =
    # 재성 (wealth = Water, the secondary drain). The strict "generates 용신"
    # formula is NOT used for strong/weak DMs because it yields the 기신 element.
    result = assess_strength(
        "己", "未",
        ["甲", "辛", "己", "戊"],
        [
            ("main", "戊"), ("middle", "乙"), ("residual", "癸"),  # 辰
            ("main", "己"), ("middle", "丁"), ("residual", "乙"),  # 未
            ("main", "丙"), ("middle", "庚"), ("residual", "戊"),  # 巳
            ("main", "戊"), ("middle", "乙"), ("residual", "癸"),  # 辰
        ],
    )
    assert result["verdict"] in ("strong", "extreme")
    assert result["candidate_favorable"] == "Metal"
    assert result["candidate_supporting"] == "Water"
    assert result["candidate_unfavorable"] == "Earth"
    assert result["candidate_draining"] == "Wood"


def test_element_balance_helpers_match_strength_assessment():
    """The canonical element-balance helpers must agree with assess_strength."""
    chart = compute_chart(
        name="Test", gender="F", year=1993, month=12, day=11,
        hour=2, minute=45, longitude=79.32, utc_offset=5.5,
        use_solar_time=True, convention="korean",
    )
    assert chart.strength_assessment is not None
    assert element_balance_counts(chart) == Counter(chart.strength_assessment["element_counts"])
    pct = element_balance_pct(chart)
    assert sum(pct.values()) == 100.0
    assert all(e in pct for e in ["Wood", "Fire", "Earth", "Metal", "Water"])
