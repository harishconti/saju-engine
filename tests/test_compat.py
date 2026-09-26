"""Tests for the marriage-compatibility (궁합) engine."""
from __future__ import annotations

import pytest

import saju_engine.compat as compat
from saju_engine.compat import (
    compat_score,
    CompatReport,
    CompatSubResult,
    compat_daystem_combo,
    compat_daybranch,
    compat_nayin,
    compat_yongshin,
    compat_ilju_pair,
    compat_combined_elements,
    compat_tengod_cross,
    compat_daeun_sync,
    compat_stars,
    compat_yin_yang,
    compat_year_branch,
    _band_for,
    _cross_branch_score,
)
from saju_engine.engine import compute_chart


# ── Helpers ─────────────────────────────────────────────────────────────────

def _chart(year, month, day, hour, minute, longitude, utc_offset, gender, name="X"):
    """Convenience wrapper for compute_chart."""
    return compute_chart(
        name=name, gender=gender, year=year, month=month, day=day,
        hour=hour, minute=minute, longitude=longitude, utc_offset=utc_offset,
        use_solar_time=True,
    )


# ── Demo pair (Mahesh × Vishnu Priya) ──────────────────────────────────────

MAHESH = _chart(1995, 1, 19, 23, 50, 78.713454, 5.5, "M", "Mahesh")
VP = _chart(2001, 6, 7, 16, 45, 76.65, 5.5, "F", "Vishnu Priya")

# Plan 6 W6 anchors — the harish × manvitha published pair.
# Birth data verified 2026-09-14 against the repo record, NOT recalled:
#   harish   — the "harish-published" input in tests/validation/fixtures/yongsin.json
#              and .../climate.json: 1992-06-04 03:10, lon 79.42, utc+5.5
#   manvitha — has NO fixture entry; her data was re-derived and confirmed to
#              reproduce the published four pillars in
#              candidates_horoscope/marriage_compatibility/harish_manvitha/
#              harish_manvitha_compatibility_deep.md (丙子 / 己亥 / 甲戌 / 乙亥)
#              byte-exactly.
# This pair is the W6 certification anchor: compat_score(HARISH, MANVITHA) is
# 70/100 Strong, all 11 sub-systems matching the published table, zero overrides.
HARISH = _chart(1992, 6, 4, 3, 10, 79.42, 5.5, "M", "Harish")
MANVITHA = _chart(1996, 12, 3, 21, 15, 78.8242, 5.5, "F", "Manvitha")

# Exact deterministic sub-system scores for the Mahesh × VP pair.
# These are regression anchors: a scoring bug that shifts a sub-system will
# now fail the test instead of hiding inside a wide range. The values were
# captured from the current engine with fixed chart inputs.
#
# "yongshin" and "combined_elements" were recaptured under Task 2b: both
# sub-systems now read Mahesh's favorable element via the single source of
# truth `yongsin.favorable_element()` (climate-corrected to Fire for his
# balanced + cold-month chart) instead of the raw, pre-climate
# `candidate_favorable` field (Water) — see compat.py's `_resolved_favorable`.
#
# 2026-09-26 (E-3/E-5 single resolution): "yongshin" 9 -> 5 and
# "tengod_cross" -8 -> -10 — both now read the resolved 기신 via
# `_resolved_unfavorable` (derived from each partner's resolved 용신) instead
# of strength.py's raw `candidate_unfavorable`, which was None for balanced
# charts, so 기신 penalties could never fire for them.
#
# 2026-09-26 (N-12): "yongshin" 5 -> 8 — cross-supply reads each partner's
# element percentages, which now weight every branch at 1.0 by 월률분야 day
# shares instead of the old main 1 / middle 0.5 / residual 0.3.
_MA_VP_SCORES = {
    "daystem_combo": 0,
    "daybranch": 6,
    "nayin": 3,
    "yongshin": 8,
    "ilju_pair": 0,
    "combined_elements": 4,
    "tengod_cross": -10,
    "daeun_sync": 3,
    "compat_stars": 3,
    "yin_yang": 2,
    "year_branch": 0,
}


# ── 1. Day-stem combination ────────────────────────────────────────────────

def test_compat_daystem_combo_present():
    # 甲 + 己 → 甲己합토 (Earth). Canonical pairs per knowledge/05-ten-gods.md.
    a = _chart(2000, 3, 12, 14, 0, 78.7, 5.5, "F")   # day_master = 己
    b = _chart(1990, 6, 8, 12, 0, 78.7, 5.5, "M")   # day_master = 甲 (verified)
    assert b.day_master == "甲"
    sub = compat_daystem_combo(a, b)
    assert sub.score > 0
    # Flag uses Korean reading 갑기합토
    assert any("갑기합토" in f or "甲己" in f for f in sub.flags)


def test_compat_daystem_combo_absent():
    # 庚 + 甲 → no 천간합 (pair table only has 甲己/乙庚/丙辛/丁壬/戊癸)
    a = MAHESH                                        # day_master = 庚
    b = _chart(1990, 6, 8, 12, 0, 78.7, 5.5, "M")    # day_master = 甲
    assert b.day_master == "甲"
    sub = compat_daystem_combo(a, b)
    assert sub.score == 0
    assert sub.flags == []  # no flags when no combo


# ── 2. Day-branch interaction ──────────────────────────────────────────────

def test_compat_daybranch_returns_exact_demo_score():
    sub = compat_daybranch(MAHESH, VP)
    assert sub.score == _MA_VP_SCORES["daybranch"]


def test_compat_daybranch_self_is_safe():
    """Compatibility of a chart with itself must not crash and must produce
    a defensible number (same branch → possible self-punishment, no 합/충)."""
    sub = compat_daybranch(MAHESH, MAHESH)
    assert -30 <= sub.score <= 30  # range kept: self-compat is a sanity bound, not a regression anchor


def test_compat_daybranch_same_branch_no_three_harmony():
    """Identical day branches must not receive a false 삼합 partial-harmony bonus."""
    sub = compat_daybranch(MAHESH, MAHESH)
    assert not any("반합" in f or "삼합" in f for f in sub.flags)


# ── 3. Nayin ────────────────────────────────────────────────────────────────

def test_compat_nayin_returns_relation_label():
    sub = compat_nayin(MAHESH, VP)
    # Different nayin, different element → relation label should appear
    assert "납음" in sub.flags[0]


def test_compat_nayin_shape():
    sub = compat_nayin(MAHESH, VP)
    assert isinstance(sub, CompatSubResult)
    assert sub.max == 5
    assert sub.score == _MA_VP_SCORES["nayin"]


def test_compat_nayin_uses_weight_budget():
    """Nayin sub-system score must stay within the ±5 weight budget."""
    sub = compat_nayin(MAHESH, VP)
    assert -5 <= sub.score <= 5
    assert abs(sub.score) <= sub.max


def test_compat_nayin_flag_shows_fallback():
    """Until pair-specific values are sourced, the Nayin flag must tag the fallback."""
    sub = compat_nayin(MAHESH, VP)
    assert any("element-grammar-fallback" in f for f in sub.flags)


# ── 4. Yongshin cross-supply ────────────────────────────────────────────────

def test_compat_yongshin_cross_supply():
    sub = compat_yongshin(MAHESH, VP)
    assert isinstance(sub, CompatSubResult)
    # Mahesh's resolved favorable element is Fire (climate-corrected), VP's is
    # Water → some cross-supply possible in both directions.
    assert sub.score == _MA_VP_SCORES["yongshin"]


# ── 5. Day-pillar pair ──────────────────────────────────────────────────────

def test_compat_ilju_pair_returns_score():
    sub = compat_ilju_pair(MAHESH, VP)
    assert sub.score == _MA_VP_SCORES["ilju_pair"]


# ── 6. Combined element balance ─────────────────────────────────────────────

def test_compat_combined_elements_returns_balance():
    sub = compat_combined_elements(MAHESH, VP)
    assert sub.score == _MA_VP_SCORES["combined_elements"]


# ── 7. Ten-god cross ────────────────────────────────────────────────────────

def test_compat_tengod_cross_returns_result():
    sub = compat_tengod_cross(MAHESH, VP)
    assert isinstance(sub, CompatSubResult)
    assert sub.score == _MA_VP_SCORES["tengod_cross"]


# ── 8. Daeun sync ───────────────────────────────────────────────────────────

def test_compat_daeun_sync_returns_result():
    sub = compat_daeun_sync(MAHESH, VP)
    assert sub.score == _MA_VP_SCORES["daeun_sync"]


def test_compat_daeun_sync_safe_when_gender_unknown():
    """A chart with gender=None must not silently default to male Daeun direction."""
    with_gender = _chart(1990, 6, 8, 12, 0, 78.7, 5.5, "M", "WithGender")
    without_gender = _chart(1992, 6, 4, 8, 0, 78.7, 5.5, "F", "NoGender")
    # Simulate the unsafe scenario: daeun exists but gender is missing.
    without_gender.gender = None

    sub = compat_daeun_sync(with_gender, without_gender)
    assert sub.score == 0
    assert any("gender unknown" in f for f in sub.flags)


# ── 9. Stars ────────────────────────────────────────────────────────────────

def test_compat_stars_returns_result():
    sub = compat_stars(MAHESH, VP)
    assert isinstance(sub, CompatSubResult)
    assert sub.score == _MA_VP_SCORES["compat_stars"]


# ── 10. Yin-yang ────────────────────────────────────────────────────────────

def test_compat_yin_yang_returns_score():
    sub = compat_yin_yang(MAHESH, VP)
    assert sub.score == _MA_VP_SCORES["yin_yang"]


# ── 11. Year-branch ─────────────────────────────────────────────────────────

def test_compat_year_branch_returns_score():
    sub = compat_year_branch(MAHESH, VP)
    assert sub.score == _MA_VP_SCORES["year_branch"]


def test_compat_year_branch_same_branch_no_three_harmony():
    """Identical year branches must not receive a false 삼합 partial-harmony bonus."""
    sub = compat_year_branch(MAHESH, MAHESH)
    assert not any("반합" in f or "삼합" in f for f in sub.flags)


# ── 12. Composite orchestrator ──────────────────────────────────────────────

def test_compat_composite_returns_compat_report():
    r = compat_score(MAHESH, VP)
    assert isinstance(r, CompatReport)
    assert 0 <= r.score <= 100
    assert r.band in {"Excellent", "Strong", "Mixed", "Challenging"}


def test_compat_flag_classification_avoids_chungbun_substring():
    """A flag containing '충분' (sufficient) must not be misclassified as a red flag."""
    from saju_engine.compat import _classify_flag

    assert _classify_flag("용신 Metal 결합에서 충분") != "red"
    assert _classify_flag("일지 육충 자축 (RED FLAG)") == "red"
    assert _classify_flag("띠 반합 인묘진 (Wood)") == "favorable"
    assert _classify_flag("A → B 용신 Metal 공급 양호 (24%)") == "favorable"
    assert _classify_flag("일지 자형 오오") == "red"


def test_compat_flag_classification_hae_token_not_overmatched():
    """A bare '해' token must not match unrelated words like 해결/해당/해석.

    Regression for engine-audit D22: the yellow bucket previously used a
    single-character '해' check, misclassifying unrelated flags.
    """
    from saju_engine.compat import _classify_flag

    assert _classify_flag("일지 육해 축자") == "yellow"
    # Unrelated words containing '해' must stay unclassified.
    assert _classify_flag("결합에서 해결 방안") is None
    assert _classify_flag("해당 사항 없음") is None
    assert _classify_flag("해석은 reader가 진행") is None


def test_compat_top_red_flags_ranked_by_severity_not_alphabetically():
    """N-10 (2026-09-26 audit): `red_flags = sorted(set(red_flags))[:3]` picked
    the top 3 alphabetically by sub-system label, so a -25 day-branch 육충
    could lose its cover slot to weaker folk flags whose label happens to
    sort earlier ("Combined..." before "Day-branch...")."""
    from saju_engine.compat import _flag_severity

    flags = [
        "Combined element cross-supply: A → B 용신 木 일부 공급 (40%)",
        "Cross-star overlays: 쌍화개 — both have 화개",
        "Day-branch interaction (spouse palaces): 일지 육충 子午 (RED FLAG)",
        "Nayin pair (30x30): 납음 A vs B → 상충",
    ]
    ranked = sorted(flags, key=lambda f: (-_flag_severity(f), f))[:3]
    assert any("육충" in f for f in ranked), (
        f"the -25 day-branch clash must survive the top-3 cut: {ranked}"
    )
    assert ranked[0] == "Day-branch interaction (spouse palaces): 일지 육충 子午 (RED FLAG)"


def test_compat_flag_classification_dohwa_seuchyeo_is_yellow():
    """F-9 (2026-09-26 audit): '도화스쳐' (-5, spouse-palace 도화 hit / affair-
    risk flag per knowledge/11-gunghap.md §I) was never bucketed into red or
    yellow, so it silently never appeared in the client-facing flag lists
    despite contributing to the composite score.
    """
    from saju_engine.compat import _classify_flag

    assert _classify_flag("도화스쳐 — 도화 hits spouse palace") == "yellow"


def test_compat_band_thresholds():
    # Sanity check the band assignment via _band_for directly
    assert _band_for(85) == "Excellent"
    assert _band_for(80) == "Excellent"
    assert _band_for(79) == "Strong"
    assert _band_for(65) == "Strong"
    assert _band_for(64) == "Mixed"
    assert _band_for(45) == "Mixed"
    assert _band_for(44) == "Challenging"
    assert _band_for(0) == "Challenging"


def test_compat_demo_pair_runs_clean():
    """Canonical Mahesh × Vishnu Priya demo pair: runs end-to-end with a
    valid composite in one of the 4 bands."""
    r = compat_score(MAHESH, VP)
    assert 0 <= r.score <= 100
    assert r.band in {"Excellent", "Strong", "Mixed", "Challenging"}
    # The day-branch interaction should at least mention 'spouse'
    assert "spouse" in r.daybranch.label.lower()
    # All sub-systems should have non-empty labels and narratives
    for sub in r.sub_systems():
        assert sub.label
        assert sub.narrative


# ── 13. Engine integrates with compute_chart (no exceptions) ────────────────

def test_compat_self_score_runs():
    """Compatibility of a chart with itself should be a clean baseline."""
    r = compat_score(MAHESH, MAHESH)
    assert 0 <= r.score <= 100
    assert isinstance(r.score, int)


# ── 14. Flags lists are well-formed ─────────────────────────────────────────

def test_compat_flags_are_lists():
    r = compat_score(MAHESH, VP)
    assert isinstance(r.red_flags, list)
    assert isinstance(r.yellow_flags, list)
    assert isinstance(r.favorable_points, list)
    assert len(r.red_flags) <= 3
    assert len(r.favorable_points) <= 3


# ── 15. Markdown report generator ──────────────────────────────────────────

def test_compat_score_honors_favorable_element_override():
    """compat_score should accept explicit favorable-element overrides."""
    from saju_engine.yongsin import favorable_element

    # Mahesh's engine heuristic is climate-corrected to Fire (see Task 2); force
    # it to Metal and assert the resolved value used by both scoring and the
    # compat report display reflects the override, while the caller's chart
    # remains unchanged.
    original_a = favorable_element(MAHESH).element
    r = compat_score(MAHESH, VP, favorable_element_a="Metal")
    assert favorable_element(r.chart_a).element == "Metal"
    assert favorable_element(MAHESH).element == original_a


def test_compat_yongshin_scoring_uses_resolved_favorable_element():
    """Sub-system D (cross-용신 supply) must score against the SAME favorable
    element `favorable_element()` resolves for display — not the raw,
    pre-climate `candidate_favorable` field. Mahesh is balanced + cold month,
    so his resolved favorable element (Fire, per Task 2's climate merge)
    differs from the raw engine pick (Water)."""
    from saju_engine.yongsin import favorable_element
    from saju_engine.compat import compat_yongshin

    assert favorable_element(MAHESH).element == "Fire"
    assert MAHESH.strength_assessment.get("candidate_favorable") == "Water"

    sub = compat_yongshin(MAHESH, VP)
    # The sub-system's flags/narrative reference the resolved element (Fire),
    # never the stale raw pick (Water), when it names Mahesh's 용신 by name.
    joined = " ".join(sub.flags)
    if "용신" in joined:
        assert "Fire" in joined or "Water" not in joined, (
            f"compat_yongshin flags reference the stale raw pick, not the resolved element: {sub.flags}"
        )


def _day_branch_only_chart(branch: str):
    """Minimal Chart with all four branches equal, isolating the PRIMARY
    day-branch score (the secondary cross-chart loop skips a branch equal to
    the day branch, so this contributes nothing but the primary term)."""
    from saju_engine.chart import Chart, Pillar

    p = Pillar(position="x", stem="甲", branch=branch)
    return Chart(year=p, month=p, day=p, hour=p)


@pytest.mark.parametrize("b1,b2", [("寅", "亥"), ("巳", "申")])
def test_compat_daybranch_combination_not_double_dipped_by_break(b1, b2):
    """F-5 (2026-09-26 audit): 寅亥 and 巳申 are simultaneously a 육합 (+20)
    and a 육파 (-3) per the lookup tables. Classical priority (knowledge/
    11-gunghap.md:181, 육합 → 육충 → 육해 → 육파 → 삼형 → 반합) says 육합 is
    tested first and wins outright — the pair must net the full +20, not
    +17 from an unconditional break penalty stacking on top.
    """
    a = _day_branch_only_chart(b1)
    b = _day_branch_only_chart(b2)
    sub = compat_daybranch(a, b)
    assert sub.score == 20, f"{b1}{b2}: expected +20 (pure 육합), got {sub.score}"
    assert not any("파" in f for f in sub.flags), f"break flag must not also fire: {sub.flags}"


def test_compat_daybranch_asymmetric_scoring():
    """Reverse cross-chart branch scoring must detect B's day vs A's non-day branches."""
    # Build a chart pair where only the reverse direction has a combination.
    a = _chart(1990, 6, 8, 12, 0, 78.7, 5.5, "M")  # day branch depends on date
    b = _chart(1991, 8, 15, 12, 0, 78.7, 5.5, "F")
    sub = compat_daybranch(a, b)
    # The score must be bounded and the function must not crash.
    assert -30 <= sub.score <= 30


def test_compat_sub_scores_capped_at_max():
    """Every sub-system score must stay within its stated max."""
    r = compat_score(MAHESH, VP)
    for sub in r.sub_systems():
        assert abs(sub.score) <= sub.max, f"{sub.label}: {sub.score} / {sub.max}"


def test_compat_composite_normalization_neutral_is_mixed():
    """A perfectly neutral raw_total should land at 50/100 (Mixed)."""
    # The band mapping is deterministic via _band_for.
    assert _band_for(50) == "Mixed"


def test_compat_daystem_combo_distinct_guidance():
    """The day-stem section states clearly whether the combination is present, partial, or absent/neutral."""
    from saju_engine.compat_report import generate_compat_report
    md = generate_compat_report(MAHESH, VP, "Mahesh", "Vishnu Priya")
    # At least one of the explicit phrases should appear (full, half-binding, absent/neutral).
    assert (
        "is fully present" in md
        or "is a half-binding" in md
        or "is absent" in md
        or "do not form a" in md
    )


def test_compat_report_has_plain_words_and_glossary():
    from saju_engine.compat_report import generate_compat_report
    md_basic = generate_compat_report(MAHESH, VP, "Mahesh", "Vishnu Priya", tier="basic")
    md_deep = generate_compat_report(MAHESH, VP, "Mahesh", "Vishnu Priya", tier="deep")
    for md in (md_basic, md_deep):
        assert "> **In plain words:**" in md
        assert "## What the Terms Mean" in md
        gi = md.index("## What the Terms Mean")
        ci = md.index("## Closing Note")
        assert gi > ci


def test_generate_compat_report_default_is_basic():
    """Default compat report is the basic compact snapshot."""
    from saju_engine.compat_report import generate_compat_report
    md = generate_compat_report(MAHESH, VP, "Mahesh", "Vishnu Priya")
    assert isinstance(md, str)
    assert len(md) > 1000
    # Cover should include both names
    assert "Mahesh" in md
    assert "Vishnu Priya" in md
    # Basic tier surfaces the four decisive sub-systems, not all 11 full sections.
    assert "Key Sub-Systems" in md
    for korean in ["일간합", "용신 궁합", "음양 조화"]:
        assert korean in md, f"Missing sub-system section: {korean}"
    # Day-branch is the heart section
    assert "일지 합충형파해" in md
    # Deep-tier heading must not appear
    assert "Deep Compatibility Layer" not in md
    # Closing note should appear
    assert "Closing Note" in md
    # Score + band must appear on cover
    assert "/ 100" in md
    assert "Mixed" in md or "Strong" in md or "Excellent" in md or "Challenging" in md


def test_basic_tier_does_not_leak_deep_tier_verdict_detail():
    """F-6 (2026-09-26 audit): the $24 basic ("Compatibility Snapshot") tier
    rendered the identical full 11-sub-system verdict table and red/yellow/
    favorable flag lists that the $45 deep tier is supposed to reserve —
    `_verdict_block()` took no tier parameter. Basic must show only the
    composite score/band plus its four decisive sub-systems, never the full
    breakdown table nor references to deep-only sub-systems like Ten-God
    Cross (G) or Major Luck Synchrony (H).
    """
    from saju_engine.compat_report import generate_compat_report
    md = generate_compat_report(MAHESH, VP, "Mahesh", "Vishnu Priya", tier="basic")
    assert "| Sub-System | Korean | Score | Max | Verdict |" not in md, (
        "basic tier must not render the full 11-row verdict table"
    )
    for leaked_label in ["Ten-god cross-relationship", "Major luck synchrony",
                         "Nayin harmony", "Day-pillar pair classification",
                         "Combined element balance", "Compatibility star overlays",
                         "Year-branch zodiac pair"]:
        assert leaked_label not in md, f"basic tier must not reference {leaked_label!r}"


def test_annual_couple_timing_overlay_uses_chart_reference_date_not_wall_clock():
    """Regression for a 2026-09-20 external code-quality review finding:
    `_annual_overlay` used to call `date.today().year` directly to decide
    which years to show, so the visible range silently shifted with the
    real-world date the report happened to be generated on, and could not
    be pinned for a reproducible test. It now reads `Chart.reference_date_obj()`
    (the mechanism `premium_report.py` already uses for the same purpose),
    falling back to `date.today()` only when the chart has no reference date."""
    from saju_engine.compat_report import generate_compat_report
    pinned_a = compute_chart(
        name="Mahesh", gender="M", year=1995, month=1, day=19, hour=23, minute=50,
        longitude=78.713454, utc_offset=5.5, use_solar_time=True,
        reference_year=2020, reference_month=1, reference_day=1,
    )
    pinned_b = compute_chart(
        name="Vishnu Priya", gender="F", year=2001, month=6, day=7, hour=16, minute=45,
        longitude=76.65, utc_offset=5.5, use_solar_time=True,
        reference_year=2020, reference_month=1, reference_day=1,
    )
    md = generate_compat_report(pinned_a, pinned_b, "Mahesh", "Vishnu Priya", tier="deep")
    assert "#### Annual Couple Timing Overlay" in md
    section = md[md.index("#### Annual Couple Timing Overlay"):]
    section = section[:section.index("\n\n", section.index("|---"))]
    years_shown = [int(row.split("|")[1].strip()) for row in section.splitlines() if row.startswith("| 20")]
    assert years_shown, f"expected at least one year row: {section!r}"
    # Pinned reference year is 2020; `chart.sewoon` precomputes ref_year ± 2
    # (2018-2022), and the overlay drops anything before current_year - 1
    # (2019), so the visible range must be exactly [2019, 2022] — not
    # whatever `date.today()` (e.g. 2026) would have pulled in.
    assert min(years_shown) == 2019 and max(years_shown) == 2022, (
        f"years shown ({years_shown}) should be [2019, 2022] for the pinned "
        f"reference year 2020, not the wall-clock date: {section!r}"
    )


def test_generate_compat_report_deep_has_all_subsystems():
    """Deep compat report includes the full eleven-sub-system breakdown + timing overlay."""
    from saju_engine.compat_report import generate_compat_report
    md = generate_compat_report(MAHESH, VP, "Mahesh", "Vishnu Priya", tier="deep")
    assert "Deep Compatibility Layer" in md
    for korean in ["일간합", "일지 합충형파해", "납음오행", "용신 궁합",
                   "일주 궁합", "결합 오행", "십신 교차", "대운·세운 동기",
                   "신살 궁합", "음양 조화", "띠 궁합"]:
        assert korean in md, f"Missing sub-system section: {korean}"
    assert "Major Luck Timeline" in md
    assert "Annual Couple Timing Overlay" in md


# ── 16. P2 doctrine-gap regression tests ────────────────────────────────────

def test_compat_removed_weak_spouse_palace_entries():
    """The three invented weak-spouse-palace entries must no longer be penalized.

    Regression for engine-audit A8: knowledge/11-gunghap.md Table E3 lists only
    5 classical weak 일주 (甲申, 丙午, 庚子, 壬寅, 戊戌). 庚戌, 甲午, 壬子 were
    engine inventions and must not appear in the lookup.
    """
    from saju_engine.compat import _WEAK_SPOUSE_PALACE
    for invented in ["庚戌", "甲午", "壬子"]:
        assert invented not in _WEAK_SPOUSE_PALACE
    for classical in ["甲申", "丙午", "庚子", "壬寅", "戊戌"]:
        assert classical in _WEAK_SPOUSE_PALACE


def test_compat_daystem_combo_breaker_in_month_branch_is_broken():
    """Month-position breaker reduces the 일간합 to 20%; elsewhere is 50%.

    Regression for engine-audit B12: knowledge/11-gunghap.md §A step 4 says a
    breaking stem in the month branch is 'broken' (−80%), elsewhere is
    'half-binding' (−50%). We test the helper directly because constructing a
    real chart with an exact month-position breaker is brittle.
    """
    from saju_engine.compat import _breaker_in_month_branch
    # Construct a minimal Chart-like object with the needed attributes.
    class _FakeChart:
        class _Pillar:
            def __init__(self, stem, branch):
                self.stem = stem
                self.branch = branch
        def __init__(self, month_stem, month_branch):
            self.month = self._Pillar(month_stem, month_branch)

    chart = _FakeChart("乙", "寅")  # 寅 hidden stems: 甲 丙 戊
    assert _breaker_in_month_branch("乙", chart) is True       # month stem
    assert _breaker_in_month_branch("甲", chart) is True     # main hidden
    assert _breaker_in_month_branch("丙", chart) is True       # middle hidden
    assert _breaker_in_month_branch("戊", chart) is True       # residual hidden
    assert _breaker_in_month_branch("辛", chart) is False


def test_compat_daystem_combo_in_season_helper():
    """The 합화 in-season helper matches the month-branch element."""
    from saju_engine.compat import _element_in_season
    # 寅 month = Wood; 甲己合토 is not in season, 丁壬合목 is in season.
    assert _element_in_season("Wood", "寅") is True
    assert _element_in_season("Earth", "寅") is False


def test_compat_cross_branch_score_covers_punishment_and_break():
    """Cross-chart secondary scoring must include 파, 형, and 반합.

    Regression for engine-audit B14: knowledge/11-gunghap.md §B7 requires
    합/충/형/파/해 across cross-palace comparisons.
    """
    from saju_engine.compat import _cross_branch_score, _pairwise_three_punishment
    # 子酉 is a six-break (육파).
    score, flag = _cross_branch_score("子", "酉")
    assert score == -1
    assert "육파" in flag
    # 丑戌 is a pairwise three-punishment (Earth triad 삼형).
    score, flag = _cross_branch_score("丑", "戌")
    assert score == -2
    assert "삼형" in flag
    # 寅午 is a half-harmony (반합) in the 寅午戌 Fire frame.
    score, flag = _cross_branch_score("寅", "午")
    assert score == 2
    assert "반합" in flag
    # 辰辰 is self-punishment.
    score, flag = _cross_branch_score("辰", "辰")
    assert score == -2
    assert "자형" in flag
    # Distinct branches in different punishment frames → neutral.
    assert _pairwise_three_punishment("子", "午") is None


def test_compat_tengod_cross_pair_table_is_order_invariant():
    """Swapping A/B must not change the pair-table verdict.

    Regression for engine-audit B15: the classical pair table in
    knowledge/11-gunghap.md §G is conceptually unordered; the engine must
    recognize a good pattern regardless of which partner is passed first.
    """
    # Use Mahesh and VP but compute in both orders.
    sub_ab = compat_tengod_cross(MAHESH, VP)
    sub_ba = compat_tengod_cross(VP, MAHESH)
    # The absolute score and the presence of pair-table narrative should match.
    assert sub_ab.score == sub_ba.score
    # Both should contain the same pair pattern (겁재/겁재 bad pair).
    assert any("겁재" in f for f in sub_ab.flags)
    assert any("겁재" in f for f in sub_ba.flags)


def test_compat_tengod_cross_gendered_spouse_star_bonus():
    """Heterosexual pair with aligned spouse-star mapping receives a soft bonus.

    Regression for engine-audit C4: knowledge/11-gunghap.md §G Ground Rule 5
    maps male→재성 and female→관성 as spouse indicators. For a male 甲 (Yang Wood)
    the wife star is Earth (己/戊); we use a female 己 day master so B is A's
    편재 (wealth star), which should trigger the 재성 일치 flag.
    """
    male = _chart(1990, 6, 8, 12, 0, 78.7, 5.5, "M")   # day master 甲
    female = _chart(1990, 6, 3, 12, 0, 78.7, 5.5, "F") # day master 己
    assert male.day.stem == "甲"
    assert female.day.stem == "己"
    sub = compat_tengod_cross(male, female)
    assert any("재성 일치" in f for f in sub.flags), sub.flags


def test_compat_score_override_is_non_mutating():
    """compat_score with favorable-element overrides must not mutate the caller's
    Chart objects (engine-audit D21 — thread-safety regression).
    """
    original_a = MAHESH.strength_assessment.get("candidate_favorable")
    original_b = VP.strength_assessment.get("candidate_favorable")
    compat_score(MAHESH, VP, favorable_element_a="Metal", favorable_element_b="Wood")
    assert MAHESH.strength_assessment.get("candidate_favorable") == original_a
    assert VP.strength_assessment.get("candidate_favorable") == original_b


# ── Plan 6 T1 bug-lock: C9 삼형 shadowing ────────────────────────────────────
# _cross_branch_score early-returns 육충/육해/육파 before 삼형, so 삼형 is
# unreachable for these 5 unordered pairs. Pinned, NOT fixed (spec §Out of
# Scope). strict=False deliberately: a later sanctioned fix turns these XPASS
# (delete-the-marker signal) rather than failing the build.
#
# STATUS 2026-09-14 — resolved as C-none, the lock stays. The 육합 arity defect
# (the separate issue locked in tests/validation/test_val_compat.py) was fixed
# on its own authority. The 삼형 chain POSITION was not touched, because no
# `knowledge/` file sanctions one: KB11 ranks 형 against nothing (only
# 11-gunghap.md:1052 names 형 and 충 together, without ordering them), and no
# `knowledge/` file DEFINES 삼형, TABLES its triples, WEIGHTS it, or RANKS it —
# a repo-wide grep for 삼형|三刑|寅巳申|丑戌未 across knowledge/ returns zero
# hits. (Precisely: KB11 does reference 형 as a CATEGORY five times, so the gap
# is not silence about 형 — it is that nothing settles 삼형. KB11 delegates its
# 형 tables to 02-branches.md (see-also at 11-gunghap.md:1039), and that file
# has no 삼형 section at all — a dead pointer — while 07-special-formations.md's
# Part 3 relation table lists 합·충·자형·해·파 and omits 삼형 as a row. KB11 is
# also self-contradicting on its one named instance: :137 says 인신형, :166
# tabulates the same pair as 인신충. 자형, by contrast, IS documented --
# 02-branches.md:96, 07-special-formations.md:320, 00-glossary.md:79,189.)
# Every candidate
# position would encode an unsourced priority, so the engine keeps the existing
# order and this lock stands as the documented scope limit -- the same shape as
# the accepted #11 resolution. See knowledge/11-gunghap.md §B4-C9 note.
#
# MEASURED, correcting an earlier guess recorded here: the two fixes are NOT
# coupled. The arity fix ALONE flips 0 of these 5 rows (it moves 巳申 육파 ->
# 육합, which is still not 삼형). The 4/5 figure previously written here came
# from hoisting 삼형 above 육충 -- a different, unsanctioned change -- and the
# full-chain reorder is a NO-OP on all 27 compat fixtures, moving no published
# anchor, no client-visible value and no fixture expectation.
#
# The 巳申 row is therefore unsatisfiable *given the current chain* and that is
# the intended state: 巳申 is simultaneously 六合 and 六破, 육합 is checked first
# (:310), so it reports 육합. Whichever priority is classical is exactly the
# question C-none declines to answer without a source. Do not "fix" the row.
_SHADOWED_BY_PRIORITY = [
    ("丑", "未", "육충 丑未", -5),
    ("寅", "巳", "육해 寅巳", -1),
    ("寅", "申", "육충 寅申", -5),
    ("巳", "申", "육파 巳申", -1),
    ("未", "戌", "육파 未戌", -1),
]


@pytest.mark.xfail(strict=False, reason="C9: 삼형 shadowed by higher-priority 합충파해 (Plan 6 T1 lock) -- carried as C-none, 2026-09-14")
@pytest.mark.parametrize("b1,b2,expected_flag,expected_score", _SHADOWED_BY_PRIORITY)
def test_three_punishment_shadowed_by_priority(b1, b2, expected_flag, expected_score):
    score, flag = _cross_branch_score(b1, b2)
    assert flag == f"삼형 {b1}{b2}", f"{b1}{b2} should report 삼형, got {flag!r}"
    assert score == -2


# Guard 1 (passing): proves the lock is not vacuous — 삼형 IS reachable when no
# higher-priority relation matches, so _pairwise_three_punishment really works.
def test_three_punishment_reachable_when_unshadowed():
    assert _cross_branch_score("子", "卯") == (-2, "삼형 子卯")


# Guard 2 (passing): proves the priority ladder itself is intact. Deliberately
# uses pairs that are NOT punishment pairs, so a sanctioned C9 fix — which would
# make the five locked pairs report 삼형 — cannot break this guard. (Using the
# locked pairs here would make the guard fail on the very fix the lock invites.)
@pytest.mark.parametrize("b1,b2,expected", [("子", "午", "육충 子午"), ("卯", "酉", "육충 卯酉"),
                                            ("子", "未", "육해 子未"), ("丑", "午", "육해 丑午"),
                                            ("子", "酉", "육파 子酉"), ("丑", "辰", "육파 丑辰")])
def test_priority_ladder_reports_each_relation_kind(b1, b2, expected):
    assert _cross_branch_score(b1, b2)[1] == expected


# ── C8, order-dependence — FIXED 2026-09-14 ──────────────────────────────────
#
# History: `compat_score(a, b)` was NOT symmetric. The `nayin` sub-system is
# direction-dependent (the six relation labels name which tone generates or
# overcomes which), and `compat_nayin` read that direction off the *caller's*
# argument order rather than off the couple — so one couple had two verdicts:
#
#   Mahesh x VP        forward 64 / Mixed   reverse 66 / Strong   nayin +3 vs +5
#   Harish x Manvitha  forward 70 / Strong  reverse 68 / Strong   nayin -3 vs -5
#
# Plan 6 T2 pinned this as a defect (lock + 2 defect pins). The fix landed
# 2026-09-14: `compat.py::_canonical_nayin_pair()` now resolves the subject
# order from the couple (male-first when both genders are known and differ,
# else lower NAYIN_ORDER index) before the relation is computed AND displayed.
# See knowledge/11-gunghap.md §C — "Canonical subject order".
#
# The lock XPASSed on the fix — the delete-the-marker signal — so the marker is
# retired and the test below now stands as a positive symmetry guard. The two
# former defect pins asserted the asymmetric values, so they FAILED under the
# fix; they are re-pinned here to the corrected, order-independent values.
#
# What the fix deliberately does NOT touch: the `_score_map` normalization
# (상합 +3→+5, 상구 +2→+3) and the sub-system `max`. Only the *subject* becomes
# stable — no documented weight and no published verdict moves, because both
# branches are a NO-OP for every already-canonical (male-first) pair.

def test_compat_score_is_symmetric():
    """A couple has ONE verdict: the composite is invariant under argument order."""
    fwd = compat_score(MAHESH, VP)
    rev = compat_score(VP, MAHESH)
    assert fwd.score == rev.score, f"forward {fwd.score} vs reverse {rev.score}"


# Guard 1: the band-FLIPPING instance, re-pinned to order-independence. It was
# the sharpest symptom (64/Mixed -> 66/Strong for one couple), so pinning it
# both ways is what keeps the symmetry guard from going vacuous.
#
# The band has since moved once more, from a second, unrelated fix: the 육합
# arity repair (2026-09-14, see the item-3 history above `_cross_branch_score`)
# gave this couple's day-branch sub-system a real score (2 -> 6), lifting the
# composite 64 -> 68 and the band Mixed -> Strong. The symmetric property is
# what this guard exists for, so it is re-pinned to the new value in both
# directions rather than being relaxed to a band-set membership test.
#
# 2026-09-26: 68/Strong -> 62/Mixed in both directions once 기신 penalties
# could fire for balanced charts (E-3/E-5 single resolution, see
# _MA_VP_SCORES). Order-independence — the property guarded — still holds.
#
# 2026-09-26 (N-12): 62/Mixed -> 65/Strong in both directions (yongshin
# cross-supply 5 -> 8 under 월률분야 branch weights).
def test_compat_order_independence_band_flipping_instance():
    assert compat_score(MAHESH, VP).band == "Strong"
    assert compat_score(VP, MAHESH).band == "Strong"
    assert compat_score(MAHESH, VP).nayin.score == 3
    assert compat_score(VP, MAHESH).nayin.score == 3


# Guard 2: the band-STABLE instance, re-pinned. It also asserts that order no
# longer touches ANY sub-system — a fix that re-introduced the dependence
# through a different sub-system fails here even though the composite matches.
def test_compat_order_independence_band_stable_all_subsystems_identical():
    # 2026-09-19: score moved 70->68 (still Strong) after the 조후-vs-억부 gate
    # broadened to band-extremeness rather than verdict (docs/research/
    # 2026-09-19-validation-climate.md §5) — Manvitha's 희신 changed from the
    # strong-DM convention (Earth) to the climate-resolved one (Wood), since
    # her chart is strong but sits in a cold month (조후 now governs there
    # too). Her headline 용신 (Fire) is unchanged; order-independence itself
    # still holds (both directions move together).
    # 2026-09-26: 68/Strong -> 64/Mixed (both directions) once the resolved
    # 기신 reached compat scoring (E-3/E-5 single resolution).
    fwd, rev = compat_score(HARISH, MANVITHA), compat_score(MANVITHA, HARISH)
    assert (fwd.score, rev.score) == (64, 64)
    assert (fwd.band, rev.band) == ("Mixed", "Mixed")
    differing = [k for k in compat.WEIGHT
                 if getattr(fwd, k).score != getattr(rev, k).score]
    assert differing == []
