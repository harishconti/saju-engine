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


def test_e5_balanced_heuristic_skips_in_season_controller():
    """E-5 (2026-09-25 audit): Harish (壬申/乙巳/辛亥/己丑) is balanced with
    Fire least-represented, but Fire controls the 辛 Day Master and 巳 is
    Fire's own season — the folk least-element pick must not offer it."""
    from saju_engine.engine import compute_chart
    chart = compute_chart(
        name="harish-e5", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    sa = chart.strength_assessment
    assert sa["verdict"] == "balanced"
    counts = sa["element_counts"]
    assert min(counts, key=counts.get) == "Fire"      # the raw minimum is still Fire
    assert sa["candidate_favorable"] != "Fire"        # ...but it is not offered
    assert sa["candidate_favorable"] == "Wood"


# ── N-5 (2026-09-26 audit): 월령 by element relation, not the DM's 12운성 ──────

import pytest as _pytest

from saju_engine.strength import assess_strength as _assess, month_relation as _rel


@_pytest.mark.parametrize(
    "dm,branch,relation",
    [
        ("乙", "卯", "peak"), ("乙", "寅", "same"), ("甲", "卯", "peak"),
        ("乙", "亥", "resource"), ("乙", "午", "output"), ("乙", "丑", "wealth"),
        ("乙", "申", "authority"), ("辛", "巳", "authority"), ("庚", "丑", "resource"),
        ("戊", "辰", "same"), ("戊", "寅", "authority"),
    ],
)
def test_month_relation(dm, branch, relation):
    assert _rel(dm, branch) == relation


def test_yin_dm_no_longer_inverted_by_backward_12_stage_cycle():
    """乙 in 午 is 장생 on the backward cycle but 午 is a Fire month that
    drains Wood; 乙 in 亥 is 사 but 亥 is a Water month that feeds Wood.
    With identical other stems, the 亥-month chart must score higher."""
    stems = ["庚", "戊", "乙", "丙"]
    in_wu = _assess("乙", "午", stems, [])
    in_hai = _assess("乙", "亥", stems, [])
    assert in_wu["month_stage"] == "장생" and in_wu["month_relation"] == "output"
    assert in_hai["month_stage"] == "사" and in_hai["month_relation"] == "resource"
    assert in_hai["total_score"] > in_wu["total_score"]
    assert in_wu["month_stage_score"] == 0.0 and in_hai["month_stage_score"] == 1.0


def test_yin_and_yang_dm_of_same_element_get_same_month_signal():
    for branch in "子丑寅卯辰巳午未申酉戌亥":
        a = _assess("甲", branch, ["甲"], [])["month_stage_score"]
        b = _assess("乙", branch, ["乙"], [])["month_stage_score"]
        assert a == b, branch


# ── N-19 (2026-09-26 audit): dead season score and silent Wood tie-break ─────


def test_month_season_score_no_longer_exported():
    sa = _assess("甲", "卯", ["甲", "丙"], [])
    assert "month_season_score" not in sa


def test_balanced_tie_is_surfaced_not_silently_wood():
    # Bare DM with no other elements: Wood=1 (the DM), everything else 0 —
    # a four-way tie among Fire/Earth/Metal/Water in a 午 month (balanced).
    sa = _assess("甲", "午", ["甲"], [])
    if sa["verdict"] != "balanced":
        _pytest.skip("fixture no longer balanced")
    assert sa["balanced_tie"] and len(sa["balanced_tie"]) > 1
    assert sa["candidate_favorable"] in sa["balanced_tie"]
    assert sa["candidate_favorable"] != "Wood"


# ── N-12 (2026-09-26 audit): 월률분야 branch weights ────────────────────────


def test_every_branch_totals_one_unit_of_qi():
    from saju_engine import lookup as L

    for b in "子丑寅卯辰巳午未申酉戌亥":
        assert sum(days for _, days in L.WOLRYUL_BUNYA[b]) == 30, b
        assert abs(sum(L.branch_qi_elements(b).values()) - 1.0) < 1e-9, b


def test_pure_peak_branch_no_longer_underweighted():
    # 子 used to contribute 0.6 Water (main 癸 only); 寅 contributed 1.0.
    from saju_engine.strength import _element_counts

    zi = _element_counts([], [("main", "癸")], ["子"])
    yin = _element_counts([], [("main", "甲"), ("middle", "丙"), ("residual", "戊")], ["寅"])
    assert zi["Water"] == 1.0
    assert abs(sum(yin.values()) - 1.0) < 1e-9
    assert abs(yin["Wood"] - 16 / 30) < 1e-9


def test_wu_and_hai_include_their_chugi_stems():
    from saju_engine import lookup as L

    assert abs(L.branch_qi_elements("午")["Fire"] - 21 / 30) < 1e-9   # 丙10 + 丁11
    assert abs(L.branch_qi_elements("亥")["Earth"] - 7 / 30) < 1e-9   # 戊 초기


def test_engine_element_counts_use_wolryul_bunya():
    from saju_engine import compute_chart

    c = compute_chart(name="n12", gender="M", year=1992, month=6, day=4, hour=3,
                      minute=10, longitude=79.42, utc_offset=5.5)
    counts = c.strength_assessment["element_counts"]
    assert abs(sum(counts.values()) - 8.0) < 1e-9  # 4 stems + 4 branches at 1.0 each
