"""Tests for annual-luck (세운) and monthly-luck (월운) overlays."""
from __future__ import annotations

from saju_engine.sewoon import (
    _annual_pillar, _annual_pillar_for_date, _monthly_pillar,
    _monthly_pillar_for_date, _daily_pillar, derive_sewoon,
    build_sewoon_range, derive_woon, current_woon_window,
    derive_ilwoon, current_ilwoon_window,
    _detect_branch_relationship, _detect_harmony_completions,
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


def test_annual_pillar_for_date_out_of_range_fallback_respects_lichun():
    """F-8 (2026-09-26 audit): outside sajupy's 1900-2100 ephemeris, the
    fallback ignored month/day entirely, so a pre-입춘 January (or early
    February) date got the CURRENT year's cycle instead of the previous
    one — the exact bug _annual_pillar_for_date's in-range path already
    guards against (test_annual_pillar_respects_lichun).
    """
    # 1899-01-15 is before Lichun, outside the 1900-2100 range → must fall
    # back to 1898's pillar (戊戌), not 1899's (己亥).
    assert _annual_pillar_for_date(1899, 1, 15) == _annual_pillar(1898)
    # 2101-02-01 is before the ~Feb-4 Lichun approximation, outside range →
    # must fall back to 2100's pillar (庚申), not 2101's (辛酉).
    assert _annual_pillar_for_date(2101, 2, 1) == _annual_pillar(2100)


def test_monthly_pillar_for_date_out_of_range_fallback_respects_lichun():
    """F-8 (2026-09-26 audit): `_saju_month_index`'s hardcoded lichun_month=2
    treated every February date as post-입춘 even before the real ~Feb-4
    boundary, so an out-of-range early-February date got Saju month 1 (寅)
    of the current year instead of month 12 (丑) of the previous year.
    """
    assert _monthly_pillar_for_date(2101, 2, 1) == _monthly_pillar(2101, 1)


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


# ── E-6 (2026-09-25 audit) ────────────────────────────────────────────────
# _detect_branch_relationship used to return on the first match in a fixed
# priority order, silently dropping a pair's second, simultaneous
# relationship; and no 3-branch (삼합/방합) completion check existed at all.


def test_detect_branch_relationship_returns_dual_status_pairs():
    """knowledge/02-branches.md documents 寅亥 and 巳申 as pairs that are
    simultaneously a 육합 (combine) and a 파 (break) — not either/or."""
    assert set(_detect_branch_relationship("寅", "亥")) == {"combine", "break"}
    # 巳申 is also a member pair of the 寅巳申 삼형 (E-6 residual: pairwise 형).
    assert set(_detect_branch_relationship("巳", "申")) == {"combine", "break", "punish"}


def test_detect_branch_relationship_single_match_unaffected():
    """An ordinary (non-dual-status) pair still returns exactly one type."""
    assert _detect_branch_relationship("子", "午") == ["clash"]
    assert _detect_branch_relationship("子", "丑") == ["combine"]


def test_detect_branch_relationship_no_match_returns_empty_list():
    assert _detect_branch_relationship("子", "辰") == []


def test_detect_harmony_completions_full_samhap():
    """申子辰 (Water) 삼합: incoming 辰 + natal 申,子 present -> full."""
    hits = _detect_harmony_completions("辰", ["申", "子", "丑"])
    samhap = [h for h in hits if h.kind == "삼합"]
    assert len(samhap) == 1
    assert samhap[0].status == "full"
    assert samhap[0].element == "Water"
    assert set(samhap[0].matched_natal) == {"申", "子"}


def test_detect_harmony_completions_half_samhap():
    """Only one of 申/子 present -> 반합 (half)."""
    hits = _detect_harmony_completions("辰", ["申", "丑"])
    samhap = [h for h in hits if h.kind == "삼합"]
    assert len(samhap) == 1
    assert samhap[0].status == "half"
    assert samhap[0].matched_natal == ("申",)


def test_detect_harmony_completions_full_banghap():
    """寅卯辰 (Wood/East) 방합: incoming 卯 + natal 寅,辰 present -> full."""
    hits = _detect_harmony_completions("卯", ["寅", "辰", "丑"])
    banghap = [h for h in hits if h.kind == "방합"]
    assert len(banghap) == 1
    assert banghap[0].status == "full"
    assert set(banghap[0].matched_natal) == {"寅", "辰"}


def test_detect_harmony_completions_no_natal_members_present():
    assert _detect_harmony_completions("辰", ["丑", "未"]) == []


def test_derive_sewoon_populates_harmony_completions_end_to_end():
    """2024's real annual pillar is 甲辰 — verified end-to-end against a
    chart whose natal branches contain 申 and 子, completing 申子辰 (Water)."""
    hit = derive_sewoon("丙", ["申", "子", "寅", "丑"], 2024)
    assert hit.combined == "甲辰"
    samhap = [h for h in hit.harmony_completions if h.kind == "삼합"]
    assert samhap and samhap[0].status == "full" and samhap[0].element == "Water"


def test_derive_sewoon_surfaces_dual_status_pair_end_to_end():
    """2022's real annual pillar is 壬寅 — against a natal 亥 this is
    simultaneously combine (寅亥合木) and break (寅亥파), not just one."""
    hit = derive_sewoon("丙", ["亥"], 2022)
    assert hit.combined == "壬寅"
    rels = {r for a, n, r in hit.activated_branches if n == "亥"}
    assert rels == {"combine", "break"}


# ── E-6 residuals (2026-09-26): pairwise 형, 삼형 completion, stem checks ──
# Harish's natal chart 壬申 / 乙巳 / 辛亥 / 己丑 — the audit's worked examples.
_H_BRANCHES = ["申", "巳", "亥", "丑"]
_H_STEMS = ["壬", "乙", "辛", "己"]


def test_pairwise_punishment_detected():
    assert "punish" in _detect_branch_relationship("丑", "戌")
    assert "punish" in _detect_branch_relationship("寅", "巳")
    assert "punish" in _detect_branch_relationship("子", "卯")
    assert "punish" not in _detect_branch_relationship("子", "午")
    # A branch never pairwise-punishes itself (that is 자형).
    assert "punish" not in _detect_branch_relationship("午", "午")


def test_2030_gengxu_punishes_natal_chou():
    hit = derive_sewoon("辛", _H_BRANCHES, 2030, natal_stems=_H_STEMS)
    assert hit.combined == "庚戌"
    assert ("戌", "丑", "punish") in hit.activated_branches
    # 庚 + natal 乙 → 을경합금
    assert [c[4] for c in hit.natal_stem_combinations] == ["乙"]


def test_2034_jiayin_completes_yinsishen_punishment_and_jiaji_combo():
    hit = derive_sewoon("辛", _H_BRANCHES, 2034, natal_stems=_H_STEMS)
    assert hit.combined == "甲寅"
    kinds = {(hc.kind, hc.status) for hc in hit.harmony_completions}
    assert ("삼형", "full") in kinds
    assert [c[3] for c in hit.natal_stem_combinations] == ["갑기합토"]


def test_2027_dingwei_combines_natal_ren():
    hit = derive_sewoon("辛", _H_BRANCHES, 2027, natal_stems=_H_STEMS)
    assert [(c[3], c[4]) for c in hit.natal_stem_combinations] == [("정임합목", "壬")]


def test_stem_clashes_against_all_natal_stems():
    assert derive_sewoon("辛", _H_BRANCHES, 2026, natal_stems=_H_STEMS).stem_clashes == [("丙", "壬")]
    assert derive_sewoon("辛", _H_BRANCHES, 2031, natal_stems=_H_STEMS).stem_clashes == [("辛", "乙")]


def test_without_natal_stems_only_day_master_checked():
    """Backward compatibility: callers that don't pass natal_stems get no
    non-DM combos and only a DM clash check."""
    hit = derive_sewoon("辛", _H_BRANCHES, 2027)
    assert hit.natal_stem_combinations == []
    assert hit.stem_clashes == []
    assert derive_sewoon("辛", _H_BRANCHES, 2031).stem_clashes == []  # 辛 vs DM 辛: no clash
    assert derive_sewoon("甲", _H_BRANCHES, 2030).stem_clashes == [("庚", "甲")]


def test_module_level_type_hints_resolve():
    """F-16 (2026-09-26 audit): same as daeun.py — `Dict` was used in
    module-level annotations without being imported from `typing`."""
    import typing
    from saju_engine import sewoon as sewoon_module
    typing.get_type_hints(sewoon_module._load_sajupy_calendar)
