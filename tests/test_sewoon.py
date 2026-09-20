"""Tests for annual-luck (세운) and monthly-luck (월운) overlays."""
from __future__ import annotations

from saju_engine.sewoon import (
    _annual_pillar, _annual_pillar_for_date, _monthly_pillar,
    _monthly_pillar_for_date, _daily_pillar, derive_sewoon,
    build_sewoon_range, derive_woon, current_woon_window,
    derive_ilwoon, current_ilwoon_window,
)


def test_annual_pillar_anchor():
    # 1984 is 甲子 in classical tables.
    assert _annual_pillar(1984) == ("甲", "子")
    assert _annual_pillar(1985) == ("乙", "丑")
    assert _annual_pillar(2026) == ("丙", "午")
    assert _annual_pillar(2027) == ("丁", "未")


def test_annual_pillar_tengod_and_activation():
    # Sruthi chart: Day Master 丙, branches [酉, 子, 寅, 丑]
    hit = derive_sewoon("丙", ["酉", "子", "寅", "丑"], 2026)
    assert hit.combined == "丙午"
    assert hit.stem_tengod == "비견"
    types = set(hit.relationship_types)
    assert "clash" in types  # 午 vs 子
    assert "harm" in types  # 午 vs 丑


def test_build_range():
    hits = build_sewoon_range("丙", ["酉", "子", "寅", "丑"], 2024, 2028)
    years = [h.year for h in hits]
    assert years == [2024, 2025, 2026, 2027, 2028]
    assert hits[2].combined == "丙午"


def test_monthly_pillar_anchor():
    # 1984 year pillar is 甲子; year stem 甲 → 寅月 stem 丙 per 五虎遁.
    assert _monthly_pillar(1984, 2) == ("丙", "寅")
    # 2026 year pillar is 丙午; year stem 丙 → 寅月 stem 庚.
    assert _monthly_pillar(2026, 2) == ("庚", "寅")
    # Gregorian Jan belongs to previous Saju year (2025 = 乙巳);
    # year stem 乙 → 寅月 stem 戊, month 丑 is 12th → stem 己.
    assert _monthly_pillar(2026, 1) == ("己", "丑")


def test_derive_woon_tengod_and_activation():
    # Sruthi chart: Day Master 丙, branches [酉, 子, 寅, 丑]
    hit = derive_woon("丙", ["酉", "子", "寅", "丑"], 2026, 6)
    assert hit.year == 202606
    # 2026 June → Saju month 5 (午). 2026 寅月 stem 庚 → 午月 stem 甲.
    assert hit.combined == "甲午"
    assert hit.stem_tengod == "편인"  # 甲 vs 丙
    types = set(hit.relationship_types)
    assert "clash" in types  # 午 vs 子
    assert "harm" in types  # 午 vs 丑


def test_current_woon_window_shape():
    hits = current_woon_window("丙", ["酉", "子", "寅", "丑"], 2026, 6, window=2)
    ids = [h.year for h in hits]
    assert ids == [202604, 202605, 202606, 202607, 202608]


def test_current_woon_window_steps_calendar_months_not_30_day_offsets():
    """A window centered on Jan 15 must include the previous December and current February."""
    hits = current_woon_window("丙", ["酉", "子", "寅", "丑"], 2026, 1, reference_day=15, window=1)
    ids = [h.year for h in hits]
    assert ids == [202512, 202601, 202602]


def test_daily_pillar_anchor():
    # Anchor: 1900-01-01 = 甲戌.
    assert _daily_pillar(1900, 1, 1) == ("甲", "戌")
    # Day before anchor.
    assert _daily_pillar(1899, 12, 31) == ("癸", "酉")
    # 2026-06-21: verify against sajupy expectation via anchor math.
    assert _daily_pillar(2026, 6, 21) == ("丙", "寅")


def test_derive_ilwoon_tengod_and_activation():
    # Use a chart whose natal branches include 申 so we can verify activation.
    hit = derive_ilwoon("丙", ["申", "子", "寅", "丑"], 2026, 6, 21)
    assert hit.year == 20260621
    # 2026-06-21 day pillar should be 丙寅 per anchor math.
    assert hit.combined == "丙寅"
    assert hit.stem_tengod == "비견"  # 丙 vs 丙
    types = set(hit.relationship_types)
    assert "clash" in types  # 寅 vs 申


def test_current_ilwoon_window_shape():
    hits = current_ilwoon_window("丙", ["酉", "子", "寅", "丑"], 2026, 6, 21, window=2)
    ids = [h.year for h in hits]
    assert len(ids) == 5
    assert ids[2] == 20260621  # center day
    # The dates should be contiguous.
    assert ids[0] + 1 == ids[1]
    assert ids[1] + 1 == ids[2]


# C2 regression: annual and monthly pillars must respect Lichun (立春) boundaries.


def test_annual_pillar_respects_lichun():
    # 2026-01-15 is before Lichun (Feb 4), so it belongs to the 乙巳 Saju year.
    assert _annual_pillar_for_date(2026, 1, 15) == ("乙", "巳")
    # 2026-02-04 is on Lichun, so it belongs to the 丙午 Saju year.
    assert _annual_pillar_for_date(2026, 2, 4) == ("丙", "午")
    # Mid-year query returns the post-Lichun pillar.
    assert _annual_pillar_for_date(2026, 7, 1) == ("丙", "午")


def test_monthly_pillar_respects_lichun():
    # 2026-02-03 is before Lichun (Feb 4), so it is still the 丑 month of 乙巳.
    assert _monthly_pillar_for_date(2026, 2, 3) == ("己", "丑")
    # 2026-02-04 is Lichun, the first day of 寅 month of 丙午.
    assert _monthly_pillar_for_date(2026, 2, 4) == ("庚", "寅")
    # 2026-01-15 is the 丑 month of 乙巳.
    assert _monthly_pillar_for_date(2026, 1, 15) == ("己", "丑")


def test_sewoon_date_lichun_rollback():
    # 2026-01-15 should report the 乙巳 annual pillar, not 丙午.
    hit = derive_sewoon("丙", ["酉", "子", "寅", "丑"], 2026, 1, 15)
    assert hit.combined == "乙巳"
    # 乙 (Yin Wood) is 정인 (Direct Resource) to 丙 (Yang Fire).
    assert hit.stem_tengod == "정인"


# ── R12 — annual stem-vs-Day-Master 천간합 was never computed ─────────────
# ── (found 2026-09-20, external report review, 3rd pass) ─────────────────


def test_annual_stem_combines_with_day_master():
    """2026's annual stem 丙 forms 병신합수 with a 辛 Day Master (Harish's
    real case) — knowledge/08 Part 2 step 3 requires checking "Annual stem
    vs. natal stems -> 합?", but this was never implemented at all."""
    hit = derive_sewoon("辛", ["亥", "巳", "亥", "丑"], 2026)
    assert hit.stem_combinations == [("丙", "辛", "Water", "병신합수")]


def test_annual_stem_no_combination_with_day_master_is_empty():
    hit = derive_sewoon("丙", ["酉", "子", "寅", "丑"], 2026)  # 丙 vs 丙: no combo
    assert hit.stem_combinations == []
