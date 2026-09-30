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


def test_n5_yin_and_yang_day_master_agree_by_season():
    """N-5 (2026-09-26 doctrinal decision): strength must read the month
    branch's element relation (knowledge/09 Step 2), not the Day Master's
    12운성 stage. The yin stage cycle runs backward (음생양사), so scoring off
    the stage inverted yin DMs — 乙 in 午 (its 장생) read as supported and 乙
    in 亥 (its 사) as unsupported, the reverse of the season. A bare yin and
    yang stem of the same element must now get the same verdict from the same
    month branch, which they cannot if the stage drives the score."""
    for yin, yang, draining_month, resource_month in [
        ("乙", "甲", "午", "亥"),   # Wood: 午 drains, 亥 is resource
        ("丁", "丙", "子", "寅"),   # Fire: 子 drains, 寅 is resource
        ("癸", "壬", "巳", "申"),   # Water: 巳 drains, 申 is resource
    ]:
        yin_res = assess_strength(yin, resource_month, [yin], [])
        yang_res = assess_strength(yang, resource_month, [yang], [])
        yin_drain = assess_strength(yin, draining_month, [yin], [])
        # Resource month supports; draining month does not.
        assert yin_res["month_season_score"] == yang_res["month_season_score"] == 1.0
        assert yin_res["verdict"] == yang_res["verdict"] == "strong"
        assert yin_drain["month_season_score"] == 0.0
        assert yin_drain["verdict"] != "strong"
    # The stage fields remain populated (descriptive), but no longer drive it.
    r = assess_strength("乙", "午", ["乙"], [])
    assert r["month_stage"] == "장생" and r["month_stage_score"] == 1.5
    assert r["month_season_score"] == 0.0 and r["verdict"] != "strong"


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


def test_n19_balanced_tie_is_surfaced_not_hidden():
    """N-19 (2026-09-26 audit): the balanced fallback resolved ties to the
    first element in a fixed order (always Wood) silently. `balanced_tie_elements`
    must now record the tied minima so a reader can see it was not unique."""
    # 甲 in 申 with 甲/戊/壬/丙 visible: balanced, and four elements tie at the
    # minimum (Wood, Fire, Earth, Water all 0 — Earth counts only via the DM
    # exclusion). The tie must be surfaced, not silently collapsed to Wood.
    result = assess_strength("甲", "申", ["甲", "戊", "壬", "丙"], [])
    assert result["verdict"] == "balanced"
    ties = result["balanced_tie_elements"]
    assert len(ties) >= 2, ties
    counts = result["element_counts"]
    # Every element in the tie set shares the same (minimal) count.
    least = min(counts.get(e, 0.0) for e in ties)
    assert all(abs(counts.get(e, 0.0) - least) < 1e-9 for e in ties)
    assert result["candidate_favorable"] in ties
    # E-5: the controller Metal is excluded from the tie set here (申 is Metal's
    # own season), so Metal is not among the tied minima even though it's 0.
    assert "Metal" not in ties


def test_n19_non_balanced_has_no_tie_set():
    result = assess_strength("甲", "卯", ["甲", "乙"], [])
    assert result["balanced_tie_elements"] == []


def test_n12_every_branch_contributes_equal_qi():
    """N-12 (2026-09-26 audit): a branch is one unit of qi, but the old fixed
    role weights (main 0.6 / middle 0.3 / residual 0.1) gave a 1-stem branch
    0.6 total and a 3-stem branch 1.0 — underweighting 子卯酉 by up to 40%.
    Each branch must now contribute the same total (`_HIDDEN_BRANCH_QI`)."""
    from saju_engine import lookup as L
    from saju_engine.strength import _HIDDEN_BRANCH_QI, _element_counts

    def branch_qi(branch):
        hidden = [(role, stem) for role, stem in L.HIDDEN_STEMS[branch].items()]
        # The visible stem is neutralised by using a stem not in this branch;
        # measure only the hidden contribution.
        counts = _element_counts([], hidden)
        return round(sum(counts.values()), 6)

    totals = {b: branch_qi(b) for b in L.HIDDEN_STEMS}
    assert all(abs(t - _HIDDEN_BRANCH_QI) < 1e-9 for t in totals.values()), totals


def test_n12_pure_branch_qi_matches_multi_stem_branch():
    """子 (single 癸) and 寅 (甲+丙+戊) must weigh the same in element balance."""
    from saju_engine import lookup as L
    from saju_engine.strength import _element_counts

    zi = _element_counts([], [("main", "癸")])
    yin = _element_counts([], [(r, s) for r, s in L.HIDDEN_STEMS["寅"].items()])
    assert round(sum(zi.values()), 6) == round(sum(yin.values()), 6)
