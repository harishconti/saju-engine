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
    # 甲 (Wood) matches candidate_unfavorable, 戌 (Earth) matches
    # candidate_favorable — a genuine conflicting stem/branch signal.
    # F-7 (2026-09-26 audit): this used to let "favorable" win
    # unconditionally, discarding the conflicting branch signal. A
    # conflicting signal nets to neutral, not a false "favorable".
    assert overlay["favorable_status"] == "neutral"


def test_daeun_overlay_conflicting_stem_branch_signal_is_neutral_not_favorable():
    """F-7 (2026-09-26 audit): a decade whose stem is the 용신 but whose
    branch is the 기신 (or vice versa) must not be silently reported as
    flatly "favorable" — that discards the conflicting signal entirely.
    """
    # 庚 (Metal) = favorable, 午 (Fire) = unfavorable: opposite elements.
    period = DaeunPeriod(start_age=30, end_age=39, stem="庚", branch="午")
    overlay = derive_daeun_overlay(
        day_master="丙",
        natal_branches=["寅"],
        natal_stems=["甲", "丙", "戊"],
        strength_assessment={
            "candidate_favorable": "Metal",
            "candidate_unfavorable": "Fire",
        },
        period=period,
    )
    assert overlay["stem_element"] == "Metal"
    assert overlay["branch_element"] == "Fire"
    assert overlay["favorable_status"] == "neutral"


def test_derive_daeun_overlay_uses_resolved_favorable_over_raw_candidate():
    """resolved_favorable must win over strength_assessment's raw candidate.

    Regression for the bug found 2026-09-19: daeun_overlay compared each
    period's element against the RAW strength-heuristic candidate_favorable
    (pre-climate), not the climate-resolved 용신 — the same bug class already
    fixed in premium_report.py's callouts and career-tier pool. This silently
    mis-labelled the "Lifetime Decade Roadmap" favorable/neutral lean for
    every balanced-DM chart where climate resolved a different element than
    the raw least-represented-element pick (e.g. Harish: raw Fire, resolved
    Water).
    """
    period = DaeunPeriod(start_age=50, end_age=59, stem="辛", branch="亥")
    overlay = derive_daeun_overlay(
        day_master="辛",
        natal_branches=["申", "巳", "亥", "丑"],
        natal_stems=["壬", "乙", "辛", "己"],
        strength_assessment={
            # Raw candidate (pre-climate) says Fire; the branch 亥 is Water.
            "candidate_favorable": "Fire",
            "candidate_unfavorable": None,
        },
        period=period,
        resolved_favorable="Water",  # climate-resolved 용신 for this chart
    )
    # Against the raw candidate (Fire) this branch would be "neutral" (no
    # Fire in {Metal-stem, Water-branch}); against the resolved value (Water)
    # it is "favorable" because the branch element matches.
    assert overlay["favorable_status"] == "favorable"


def test_harish_regression_daeun_roadmap_uses_climate_resolved_favorable():
    """End-to-end: Harish's real chart must show climate-resolved (Water)
    favorability in chart.daeun, not the raw candidate (Fire)."""
    chart = compute_chart(
        name="harish-daeun-regression", year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5, gender="M",
    )
    by_age = {p.start_age: p for p in chart.daeun}
    # 50-59 (辛亥) and 60-69 (壬子) both carry the Water branch/stem that
    # matches the resolved 용신 (Water) — under the pre-fix raw candidate
    # (Fire) these rendered "neutral".
    assert by_age[50].favorable_status == "favorable"
    assert by_age[60].favorable_status == "favorable"


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


# ── E-6 (2026-09-25 audit) ────────────────────────────────────────────────


def test_daeun_overlay_surfaces_dual_status_pair():
    """A 대운 branch that is simultaneously combine+break against a natal
    branch (寅亥, 巳申) must report both, not just the first match."""
    period = DaeunPeriod(start_age=30, end_age=39, stem="壬", branch="寅")
    overlay = derive_daeun_overlay(
        day_master="丙",
        natal_branches=["亥"],
        natal_stems=["壬", "甲", "丙", "戊"],
        strength_assessment=None,
        period=period,
    )
    rels = {r for _, n, r in overlay["activated_branches"] if n == "亥"}
    assert rels == {"combine", "break"}


def test_daeun_overlay_detects_harmony_completion():
    """A 대운 branch completing a 삼합 with two natal branches must be
    surfaced via harmony_completions — this never existed before E-6."""
    period = DaeunPeriod(start_age=40, end_age=49, stem="甲", branch="辰")
    overlay = derive_daeun_overlay(
        day_master="丙",
        natal_branches=["申", "子", "寅", "丑"],
        natal_stems=["壬", "甲", "丙", "戊"],
        strength_assessment=None,
        period=period,
    )
    samhap = [h for h in overlay["harmony_completions"] if h.kind == "삼합"]
    assert samhap and samhap[0].status == "full" and samhap[0].element == "Water"


def test_build_daeun_overlays_populates_harmony_completions_field():
    periods = [DaeunPeriod(start_age=40, end_age=49, stem="甲", branch="辰")]
    build_daeun_overlays(
        day_master="丙",
        natal_branches=["申", "子"],
        natal_stems=["丙", "甲", "丙", "戊"],
        strength_assessment=None,
        periods=periods,
    )
    assert periods[0].harmony_completions
    assert periods[0].harmony_completions[0].kind == "삼합"


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
