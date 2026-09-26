"""Tests for classical grid/pattern detection."""
from __future__ import annotations

from saju_engine.patterns import detect_patterns, detect_tengod_conflicts


def test_regular_grid_from_month_stem():
    # 丙 day master, month branch 子 (본기 癸), visible stems 癸/甲/丙/己.
    # Classical 투출 method (knowledge/07 §Part 1): 월지 子 본기 癸 투출 on the
    # year stem → 정관격. The visible 월간 甲 is 편인 of 丙 but 甲 is NOT a hidden
    # stem of 子, so under 투출 it does NOT name the grid. (The legacy 월간-direct
    # method would have labeled this 편인격 — the 투출 fix corrects that.)
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="子",
        branches=["酉", "子", "寅", "丑"],
        stems=["癸", "甲", "丙", "己"],
        hidden_stems=[("main", "辛"), ("main", "癸"), ("main", "甲"), ("main", "己")],
    )
    # Visible month-stem ten-god is still exposed for reference.
    assert result["month_tengod"] == "편인"
    # Grid is named by the 투출 stem (癸 → 정관 of 丙), not by the visible 월간.
    assert any(g.name_ko == "정관격" for g in result["regular_grid"])


def test_regular_grid_visible_month_stem_tuochul():
    # When the visible 월간 IS a 투출 of a 월지 hidden stem, both methods agree.
    # 丙 DM, month branch 寅 (본기 甲, 중기 丙, 여기 戊), visible stems 甲/丙/戊/庚.
    # 본기 甲 투출 on the month stem → 편인격 (甲 is 편인 of 丙).
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="寅",
        branches=["寅", "寅", "寅", "寅"],
        stems=["甲", "甲", "丙", "庚"],
        hidden_stems=[("main", "甲"), ("middle", "丙"), ("residual", "戊")],
    )
    assert any(g.name_ko == "편인격" for g in result["regular_grid"])


def test_regular_grid_no_tuochul_falls_back_to_bonki():
    # 丙 DM, month branch 卯 (본기 乙 only), visible stems 甲/丙/戊/庚 — none is 乙.
    # No 투출 → 본기 fallback → 乙 → 정인격 (乙 is 정인 of 丙).
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="卯",
        branches=["卯", "卯", "寅", "寅"],
        stems=["甲", "甲", "丙", "庚"],
        hidden_stems=[("main", "乙")],
    )
    assert any(g.name_ko == "정인격" for g in result["regular_grid"])


def test_yangin_detection():
    # 丙 day master in 午 branch
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="午",
        branches=["午", "午", "午", "午"],
        stems=["丙", "甲", "丙", "己"],
        hidden_stems=[("main", "丁")],
    )
    # Star-level 양인 appears anywhere the blade branch is found.
    assert result["yangin"]["present"] is True
    assert 0 in result["yangin"]["positions"]
    # N-9: the month-branch blade is the classical 양인격 (자평진전 월령)...
    assert result["yangin_grid"]["present"] is True
    assert result["yangin_grid"]["positions"] == [1]
    # ...and the year/day/hour blades are the distinct non-month pattern.
    assert result["yangin_non_month"]["positions"] == [0, 2, 3]
    assert result["yangin_non_month"]["day_blade"] is True


def test_yangin_month_branch_is_the_grid():
    """N-9 (2026-09-26 audit): 양인 in the month pillar is the 양인격 grid
    (자평진전 월령 convention); B11 used to exclude exactly this case."""
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="午",
        branches=["子", "午", "寅", "丑"],
        stems=["丙", "甲", "丙", "己"],
        hidden_stems=[("main", "丁")],
    )
    assert result["yangin"]["present"] is True
    assert result["yangin"]["positions"] == [1]
    assert result["yangin_grid"]["present"] is True
    assert result["yangin_non_month"]["present"] is False


def test_yangin_outside_month_is_non_month_pattern_not_grid():
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="子",
        branches=["午", "子", "寅", "丑"],
        stems=["丙", "甲", "丙", "己"],
        hidden_stems=[("main", "癸")],
    )
    assert result["yangin_grid"]["present"] is False
    assert result["yangin_non_month"]["positions"] == [0]
    assert result["yangin_non_month"]["day_blade"] is False


def test_month_bijie_grid_renamed_yangin_and_jianlu():
    """자평진전 names a month-branch 양인/건록 structure 양인격/건록격, not
    겁재격/비견격 (the 투출 method's name for it)."""
    blade = detect_patterns(
        day_master="丙", month_stem="甲", month_branch="午",
        branches=["子", "午", "寅", "丑"], stems=["丁", "甲", "丙", "己"],
        hidden_stems=[("main", "丁"), ("middle", "己")],
    )
    assert blade["regular_grid"][0].name_ko == "양인격"
    assert "자평진전" in blade["regular_grid"][0].basis
    lu = detect_patterns(
        day_master="丙", month_stem="癸", month_branch="巳",
        branches=["子", "巳", "寅", "丑"], stems=["壬", "癸", "丙", "己"],
        hidden_stems=[("main", "丙"), ("middle", "戊"), ("residual", "庚")],
    )
    assert lu["regular_grid"][0].name_ko == "건록격"
    assert lu["jianlu"]["present"] is True and lu["jianlu"]["positions"] == [1]


def test_jianlu_detection():
    # 丙 day master, 巳 is 建祿 branch
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="巳",
        branches=["巳", "子", "寅", "丑"],
        stems=["丙", "甲", "丙", "己"],
        hidden_stems=[("main", "丙")],
    )
    # N-9: month branch 巳 is the 건록 branch → 건록격; the year-branch 巳 is
    # the distinct non-month pattern.
    assert result["jianlu"]["present"] is True
    assert result["jianlu_non_month"]["positions"] == [0]
    assert result["jianlu_non_month"]["hour_lu"] is False


def test_jianlu_outside_month_is_not_the_grid_and_hour_is_guilu():
    result = detect_patterns(
        day_master="丙", month_stem="甲", month_branch="子",
        branches=["寅", "子", "寅", "巳"], stems=["丙", "甲", "丙", "癸"],
        hidden_stems=[("main", "癸")],
    )
    assert result["jianlu"]["present"] is False
    assert result["jianlu_non_month"]["positions"] == [3]
    assert result["jianlu_non_month"]["hour_lu"] is True


def test_element_balance():
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="子",
        branches=["酉", "子", "寅", "丑"],
        stems=["癸", "甲", "丙", "己"],
        hidden_stems=[("main", "辛"), ("main", "癸"), ("main", "甲"), ("main", "己")],
    )
    assert "Water" in result["element_balance"]
    assert result["dominant_element"] in result["element_balance"]


def test_stem_combination_detection():
    # 甲 day master with 己 in year stem, month branch is Earth season (辰).
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "卯", "寅", "丑"],
        stems=["己", "戊", "甲", "乙"],
        hidden_stems=[("main", "戊")],
    )
    combos = result["stem_combinations"]
    assert any({c["stem_a"], c["stem_b"]} == {"甲", "己"} for c in combos)
    match = next(c for c in combos if {c["stem_a"], c["stem_b"]} == {"甲", "己"})
    assert match["combined_element"] == "Earth"


def test_transformation_grid_candidate():
    # 甲 day master + 己 month stem + Earth branch (辰) + no breaker (乙/庚).
    result = detect_patterns(
        day_master="甲",
        month_stem="己",
        month_branch="辰",
        branches=["辰", "卯", "寅", "丑"],
        stems=["甲", "己", "丙", "丁"],
        hidden_stems=[("main", "戊")],
    )
    trans = result["transformation_grid"]
    assert trans is not None
    assert trans["name_ko"] == "화격"
    assert trans["combined_element"] == "Earth"


def test_transformation_grid_requires_month_stem_partner():
    # 화격 must NOT fire when the combining pair is the Day Master + hour stem
    # and the month stem is uninvolved (knowledge/07 requires the month stem
    # to be a combining partner). 甲 day master + 乙 hour stem does not exist
    # as a combo; use 甲(day)+己(hour) with a non-combining month stem 戊.
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",          # 戊 does not combine with 甲
        month_branch="辰",
        branches=["辰", "卯", "寅", "丑"],
        stems=["戊", "戊", "甲", "己"],   # 甲(year? no) — day=甲, hour=己 combo, month=戊
        hidden_stems=[("main", "戊")],
    )
    trans = result["transformation_grid"]
    assert trans is None, f"화격 should not fire without month-stem involvement: {trans}"


def test_special_form_candidate():
    # 甲 day master; chart overwhelmingly Earth (controlled by Wood → 종재).
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[("main", "戊"), ("main", "己"), ("main", "戊"), ("main", "己")],
        strength_verdict="weak",
    )
    special = result["special_forms"]
    assert any(s["name_ko"] == "종재" for s in special)


def test_special_form_unrooted_is_likely():
    # Same unrooted extremely weak chart: no Day Master or resource element in branches/hidden stems.
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[("main", "戊"), ("main", "己"), ("main", "戊"), ("main", "己")],
        strength_verdict="extreme_weak",
    )
    special = result["special_forms"]
    match = next(s for s in special if s["name_ko"] == "종재")
    assert match["confidence"] == "likely"


def test_special_form_rooted_downgraded():
    # Weak chart with overwhelming Earth, but Day Master 甲 gets resource support (Water/亥)
    # in a branch → rooted; 종격 must not be flagged as "likely".
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "亥", "丑", "未"],  # 亥 brings Water resource for Wood
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[("main", "戊"), ("main", "癸"), ("main", "戊"), ("main", "己")],
        strength_verdict="weak",
    )
    special = result["special_forms"]
    assert any(s["name_ko"] == "종재" for s in special)
    match = next(s for s in special if s["name_ko"] == "종재")
    assert match["confidence"] != "likely"
    assert "통근" in match["note"]


def test_special_form_balanced_not_likely():
    # A15 B4b: a 'balanced' verdict must NOT produce a 'likely' 종격. With an
    # overwhelming Earth mass (≥60%) it may surface as 'possible' for review,
    # but never auto-flagged as a true 종격.
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[("main", "戊"), ("main", "己"), ("main", "戊"), ("main", "己")],
        strength_verdict="balanced",
    )
    special = result["special_forms"]
    if any(s["name_ko"] == "종재" for s in special):
        match = next(s for s in special if s["name_ko"] == "종재")
        assert match["confidence"] != "likely"
        assert "balanced" in match["note"]


def test_special_form_out_of_season_downgraded():
    # A15 B4a: dominant Earth in a Wood month (卯) is not 득령 → downgrade to
    # 'possible' even when unrooted and weak.
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="卯",  # Wood season — Earth is not in season here
        branches=["辰", "戌", "丑", "未"],
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[("main", "戊"), ("main", "己"), ("main", "戊"), ("main", "己")],
        strength_verdict="weak",
    )
    special = result["special_forms"]
    if any(s["name_ko"] == "종재" for s in special):
        match = next(s for s in special if s["name_ko"] == "종재")
        assert match["confidence"] != "likely"
        assert "득령" in match["note"]


# B7: 화격 requires the Day Master to be isolated (weak).

def test_transformation_grid_strong_dm_is_none():
    result = detect_patterns(
        day_master="甲",
        month_stem="己",
        month_branch="辰",
        branches=["辰", "卯", "寅", "丑"],
        stems=["甲", "己", "丙", "丁"],
        hidden_stems=[("main", "戊")],
        strength_verdict="strong",
    )
    assert result["transformation_grid"] is None


def test_transformation_grid_weak_dm_allowed():
    result = detect_patterns(
        day_master="甲",
        month_stem="己",
        month_branch="辰",
        branches=["辰", "卯", "寅", "丑"],
        stems=["甲", "己", "丙", "丁"],
        hidden_stems=[("main", "戊")],
        strength_verdict="weak",
    )
    assert result["transformation_grid"] is not None
    assert result["transformation_grid"]["name_ko"] == "화격"


# B5–B6: structural notes and 종자 alias.

def test_structural_note_jeonguk_all_four_same_element():
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[("main", "戊")],
    )
    notes = result["structural_notes"]
    assert any(n["name_ko"] == "전국" for n in notes)


def test_structural_note_pyeonguk_three_same_element():
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "寅"],
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[("main", "戊")],
    )
    notes = result["structural_notes"]
    assert any(n["name_ko"] == "편국" for n in notes)


def test_structural_note_samhapguk():
    # All four branches inside 寅午戌 Fire frame (午 repeated).
    result = detect_patterns(
        day_master="甲",
        month_stem="丙",
        month_branch="寅",
        branches=["寅", "午", "戌", "午"],
        stems=["甲", "丙", "戊", "庚"],
        hidden_stems=[("main", "甲")],
    )
    notes = result["structural_notes"]
    assert any(n["name_ko"] == "삼합국" for n in notes)


def test_jongja_alias_appears_with_output_following():
    # 丙 DM produces Earth; overwhelming Earth → 종식상 and 종자 alias.
    result = detect_patterns(
        day_master="丙",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["戊", "己", "丙", "戊"],
        hidden_stems=[("main", "戊"), ("main", "己"), ("main", "戊"), ("main", "己")],
        strength_verdict="weak",
    )
    special = result["special_forms"]
    assert any(s["name_ko"] == "종식상" for s in special)
    assert any(s["name_ko"] == "종자" for s in special)


# ── Deeper regular-grid (정격) tests ──────────────────────────────────────────


def test_regular_grid_bonki_priority_over_middle_tuochul():
    # 寅 month branch hides 甲(main), 丙(middle), 戊(residual). Both 甲 and 丙
    # appear in the visible stems. Classical 투출 gives 본기 priority
    # (knowledge/07-special-formations.md §Part 1), so 甲 names the grid: for
    # 丙 DM, 甲 is 편인 → 편인격.
    result = detect_patterns(
        day_master="丙",
        month_stem="丙",
        month_branch="寅",
        branches=["寅", "寅", "寅", "寅"],
        stems=["甲", "丙", "戊", "庚"],
        hidden_stems=[("main", "甲"), ("middle", "丙"), ("residual", "戊")],
    )
    grid = result["regular_grid"]
    assert any(g.name_ko == "편인격" for g in grid)
    assert not any(g.name_ko == "비견격" for g in grid)


def test_regular_grid_middle_used_when_bonki_absent():
    # 寅 month branch, visible stems contain 중기 丙 but not 본기 甲.
    # For 丙 DM, 丙 is 비견 → 비견격.
    result = detect_patterns(
        day_master="丙",
        month_stem="戊",
        month_branch="寅",
        branches=["寅", "寅", "寅", "寅"],
        stems=["丙", "戊", "庚", "壬"],
        hidden_stems=[("main", "甲"), ("middle", "丙"), ("residual", "戊")],
    )
    assert any(g.name_ko == "비견격" for g in result["regular_grid"])


def test_regular_grid_residual_used_when_main_middle_absent():
    # 寅 month branch, visible stems contain only 여기 戊 (no 甲, no 丙).
    # For 丙 DM, 戊 is 식신 → 식신격.
    result = detect_patterns(
        day_master="丙",
        month_stem="庚",
        month_branch="寅",
        branches=["寅", "寅", "寅", "寅"],
        stems=["戊", "己", "庚", "壬"],
        hidden_stems=[("main", "甲"), ("middle", "丙"), ("residual", "戊")],
    )
    assert any(g.name_ko == "식신격" for g in result["regular_grid"])


# ── Deeper transformation-grid (화격) tests ───────────────────────────────────


def test_transformation_grid_rooted_breaker_blocks():
    # 甲己合化土 in 辰 (Earth season), but 乙 (competing breaker) is rooted in the
    # month branch hidden stem (knowledge/07-special-formations.md breaker
    # table + rooting rule). 화격 must not form.
    result = detect_patterns(
        day_master="甲",
        month_stem="己",
        month_branch="辰",
        branches=["辰", "卯", "寅", "丑"],
        stems=["乙", "己", "甲", "丙"],
        hidden_stems=[("main", "戊"), ("middle", "乙"), ("residual", "癸")],
        strength_verdict="weak",
    )
    assert result["transformation_grid"] is None


def test_transformation_grid_floating_breaker_does_not_block():
    # 甲己合化土 in 辰, breaker 乙 appears in stems but has no root in branches
    # or hidden stems and its element (Wood) is not in season at 辰. A floating
    # breaker is too weak to cancel the 합 per knowledge/07-special-formations.md.
    result = detect_patterns(
        day_master="甲",
        month_stem="己",
        month_branch="辰",
        branches=["辰", "卯", "寅", "丑"],
        stems=["乙", "己", "甲", "丙"],
        hidden_stems=[("main", "戊"), ("residual", "癸")],
        strength_verdict="weak",
    )
    trans = result["transformation_grid"]
    assert trans is not None
    assert trans["name_ko"] == "화격"


def test_transformation_grid_out_of_season_is_none():
    # 甲己合 requires the combined Earth element to be in season at the month
    # branch (knowledge/07-special-formations.md §B.2). 寅 is Wood season, so
    # 화격 must not form.
    result = detect_patterns(
        day_master="甲",
        month_stem="己",
        month_branch="寅",
        branches=["寅", "卯", "寅", "丑"],
        stems=["戊", "己", "甲", "丙"],
        hidden_stems=[("main", "甲"), ("middle", "丙"), ("residual", "戊")],
        strength_verdict="weak",
    )
    assert result["transformation_grid"] is None


def test_transformation_grid_bing_xin_water_combo():
    # 丙 DM + 辛 month stem → 병신합수. Month branch 子 is Water season, no
    # breaker 丁/壬 present → a true 화격 candidate.
    result = detect_patterns(
        day_master="丙",
        month_stem="辛",
        month_branch="子",
        branches=["子", "子", "子", "子"],
        stems=["戊", "辛", "丙", "庚"],
        hidden_stems=[("main", "癸")],
        strength_verdict="weak",
    )
    trans = result["transformation_grid"]
    assert trans is not None
    assert trans["name_ko"] == "화격"
    assert trans["combined_element"] == "Water"


# ── E-9 (2026-09-25 audit) — 격국 naming had no 성격/파격 (broken-grid) check ──


def test_regular_grid_downgraded_when_sanggwan_gyeon_gwan_present():
    """Same chart as test_regular_grid_from_month_stem (a real 정관격), which
    also happens to carry 상관 (己, visible hour stem + hidden). Per
    knowledge/05-ten-gods.md ("상관견관 = 상관 directly clashing with 정관"),
    this classically complicates a 정관격 reading — but the two detectors
    used to run in total isolation, so the grid was asserted 'likely'
    regardless."""
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="子",
        branches=["酉", "子", "寅", "丑"],
        stems=["癸", "甲", "丙", "己"],
        hidden_stems=[("main", "辛"), ("main", "癸"), ("main", "甲"), ("main", "己")],
    )
    grid = next(g for g in result["regular_grid"] if g.name_ko == "정관격")
    assert grid.confidence == "possible"
    assert "파격" in grid.note and "상관견관" in grid.note
    assert any(c["name_ko"] == "상관견관" for c in result["tengod_conflicts"])


def test_regular_grid_stays_likely_without_conflicting_god():
    """Same 정관격 setup but with no 상관 anywhere in the chart — the grid
    must stay at full ('likely') confidence with no 파격 note."""
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="子",
        branches=["酉", "子", "寅", "丑"],
        # Hour stem 乙 (was 壬 until 2026-09-26: 壬 is 편관, so 癸 정관 + 壬
        # 편관 on the visible stems is a genuine 관살혼잡 파격 now detected).
        stems=["癸", "甲", "丙", "乙"],
        hidden_stems=[("main", "癸")],
    )
    grid = next(g for g in result["regular_grid"] if g.name_ko == "정관격")
    assert grid.confidence == "likely"
    assert grid.note == ""


def test_regular_grid_downgrade_confined_to_the_targeted_god():
    """상관견관 present in the chart, but the named grid is 편인격, not
    정관격 — knowledge/05-ten-gods.md's own wording only names 상관견관 as
    breaking a 정관 reading, so a 편인격 must NOT be downgraded by it."""
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="寅",
        branches=["寅", "寅", "寅", "寅"],
        stems=["甲", "甲", "丙", "庚"],
        hidden_stems=[
            ("main", "甲"), ("middle", "丙"), ("residual", "戊"),
            ("main", "癸"), ("main", "己"),
        ],
    )
    grid = next(g for g in result["regular_grid"] if g.name_ko == "편인격")
    assert grid.confidence == "likely"
    assert grid.note == ""
    # The conflict itself is still independently detected and reported.
    assert any(c["name_ko"] == "상관견관" for c in result["tengod_conflicts"])


# ── Special-form (종격) threshold & subtype tests ──────────────────────────────


def test_special_form_exact_fifty_percent_triggers():
    # Dominant Earth is exactly 50% of the weighted element count with no hidden
    # stems. The >= 0.5 threshold should trigger for an extreme_weak DM.
    result = detect_patterns(
        day_master="丙",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["丙", "戊", "己", "庚"],
        hidden_stems=[],
        strength_verdict="extreme_weak",
    )
    special = result["special_forms"]
    assert any(s["name_ko"] == "종식상" for s in special)
    match = next(s for s in special if s["name_ko"] == "종식상")
    assert match["confidence"] == "likely"


def test_special_form_below_threshold_no_trigger():
    # Earth share is only 25% — well below the 50% minimum — so no 종격
    # candidate should surface regardless of strength verdict.
    result = detect_patterns(
        day_master="丙",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["丙", "戊", "庚", "壬"],
        hidden_stems=[],
        strength_verdict="extreme_weak",
    )
    assert result["special_forms"] == []


def test_special_form_strong_verdict_returns_empty():
    # 종격 requires 신약 (weak DM). A strong verdict must never return a 종격.
    result = detect_patterns(
        day_master="甲",
        month_stem="戊",
        month_branch="辰",
        branches=["辰", "戌", "丑", "未"],
        stems=["戊", "己", "甲", "戊"],
        hidden_stems=[
            ("main", "戊"),
            ("main", "己"),
            ("main", "戊"),
            ("main", "己"),
        ],
        strength_verdict="strong",
    )
    assert result["special_forms"] == []


def test_special_form_jonggwan_metal_authority():
    # 甲 DM overwhelmed by Metal (Metal controls Wood) → 종관. Metal hidden in
    # 酉 branches only, so the DM has no Wood/Water rooting → likely.
    result = detect_patterns(
        day_master="甲",
        month_stem="庚",
        month_branch="申",
        branches=["酉", "酉", "酉", "酉"],
        stems=["甲", "庚", "辛", "壬"],
        hidden_stems=[
            ("main", "辛"),
            ("main", "辛"),
            ("main", "辛"),
            ("main", "辛"),
        ],
        strength_verdict="extreme_weak",
    )
    special = result["special_forms"]
    assert any(s["name_ko"] == "종관" for s in special)
    match = next(s for s in special if s["name_ko"] == "종관")
    assert match["confidence"] == "likely"


def test_special_form_jongin_resource_downgraded_by_rooting():
    # 丙 DM with Wood dominating. Branches are Wood, so the DM is rooted via
    # 인성 support; 종인 is flagged but downgraded to possible
    # (knowledge/07-special-formations.md precondition: no rooting for a true
    # 종격).
    result = detect_patterns(
        day_master="丙",
        month_stem="甲",
        month_branch="寅",
        branches=["寅", "卯", "寅", "卯"],
        stems=["丙", "甲", "乙", "戊"],
        hidden_stems=[
            ("main", "甲"),
            ("main", "乙"),
            ("main", "甲"),
            ("main", "乙"),
        ],
        strength_verdict="extreme_weak",
    )
    special = result["special_forms"]
    assert any(s["name_ko"] == "종인" for s in special)
    match = next(s for s in special if s["name_ko"] == "종인")
    assert match["confidence"] == "possible"
    assert "통근" in match["note"]


# ── Structural-note edge cases ───────────────────────────────────────────────


def test_structural_note_no_jeonguk_pyeonguk_when_balanced():
    # Two Wood and two Fire branches: no 전국 or 편국 should be flagged.
    result = detect_patterns(
        day_master="甲",
        month_stem="丙",
        month_branch="寅",
        branches=["寅", "卯", "巳", "午"],
        stems=["甲", "丙", "戊", "庚"],
        hidden_stems=[
            ("main", "甲"),
            ("main", "乙"),
            ("main", "丙"),
            ("main", "丁"),
        ],
    )
    notes = result["structural_notes"]
    assert not any(n["name_ko"] in {"전국", "편국"} for n in notes)


def test_structural_note_samhapguk_hai_mao_wei():
    # All four branches inside the 亥卯未 Wood frame.
    result = detect_patterns(
        day_master="甲",
        month_stem="乙",
        month_branch="卯",
        branches=["亥", "卯", "未", "卯"],
        stems=["甲", "乙", "丙", "丁"],
        hidden_stems=[
            ("main", "壬"),
            ("main", "乙"),
            ("main", "己"),
            ("main", "乙"),
        ],
    )
    notes = result["structural_notes"]
    assert any(n["name_ko"] == "삼합국" for n in notes)


# ── Yangin / Jianlu edge cases ────────────────────────────────────────────────


def test_yangin_absent_for_yin_day_master():
    # Yin day masters (乙, 丁, 己, 辛, 癸) have no blade branch in the engine's
    # classical mapping, so 양인 must not be flagged.
    result = detect_patterns(
        day_master="乙",
        month_stem="戊",
        month_branch="卯",
        branches=["卯", "卯", "卯", "卯"],
        stems=["乙", "戊", "乙", "己"],
        hidden_stems=[("main", "乙")],
    )
    assert result["yangin"]["present"] is False
    assert result["yangin_grid"]["present"] is False


# ── 상관견관 (Output Meets Authority) — added 2026-09-19, external review ────


def test_tengod_conflict_detects_output_meets_authority_harish_chart():
    """Harish's real chart (壬申/乙巳/辛亥/己丑, DM 辛): 상관 (壬, year stem + two
    hidden) and 정관 (hidden 丙 in the month branch 巳) are both present.
    Confirmed missing from the engine before this fix (external report
    review, 2026-09-19) — knowledge/05-ten-gods.md documents 상관견관 as a
    named classical conflict, but nothing detected it.
    """
    conflicts = detect_tengod_conflicts(
        day_master="辛",
        stems=["壬", "乙", "辛", "己"],
        hidden_stems=[
            ("main", "庚"), ("middle", "壬"), ("residual", "戊"),  # 申
            ("main", "丙"), ("middle", "庚"), ("residual", "戊"),  # 巳
            ("main", "壬"), ("middle", "甲"),                      # 亥
            ("main", "己"), ("middle", "癸"), ("residual", "辛"),  # 丑
        ],
    )
    assert len(conflicts) == 1
    assert conflicts[0]["name_ko"] == "상관견관"
    assert conflicts[0]["name_en"] == "Output Meets Authority"


def test_tengod_conflict_absent_without_direct_officer():
    """상관 present but no 정관 anywhere (visible or hidden) must not flag
    상관견관 — this is the specific documented pairing, not a generic
    식상-vs-관성 check."""
    conflicts = detect_tengod_conflicts(
        day_master="辛",  # 상관 = 壬
        stems=["壬", "乙", "辛", "己"],
        hidden_stems=[("main", "庚")],  # 겁재, no 관성 at all
    )
    assert conflicts == []


def test_tengod_conflict_absent_with_seven_killings_only():
    """편관 (Seven Killings) alone must NOT trigger 상관견관 — that pairing
    forms separately-named patterns (e.g. 식신제살), not this one. Only the
    specific 상관+정관 pairing is documented and checked."""
    conflicts = detect_tengod_conflicts(
        day_master="辛",  # 상관 = 壬, 편관 = 丁 (not 정관 丙)
        stems=["壬", "乙", "辛", "己"],
        hidden_stems=[("main", "丁")],  # 편관, not 정관
    )
    assert conflicts == []


def test_tengod_conflict_absent_without_output():
    """정관 present but no 상관 anywhere must not flag 상관견관."""
    conflicts = detect_tengod_conflicts(
        day_master="辛",  # 정관 = 丙
        stems=["丙", "乙", "辛", "己"],
        hidden_stems=[("main", "戊")],  # 정인, no 식상 at all
    )
    assert conflicts == []


def test_detect_patterns_surfaces_tengod_conflicts_key():
    """detect_patterns()'s return dict must expose tengod_conflicts."""
    result = detect_patterns(
        day_master="辛",
        month_stem="乙",
        month_branch="巳",
        branches=["申", "巳", "亥", "丑"],
        stems=["壬", "乙", "辛", "己"],
        hidden_stems=[
            ("main", "庚"), ("middle", "壬"), ("residual", "戊"),
            ("main", "丙"), ("middle", "庚"), ("residual", "戊"),
            ("main", "壬"), ("middle", "甲"),
            ("main", "己"), ("middle", "癸"), ("residual", "辛"),
        ],
    )
    assert "tengod_conflicts" in result
    assert any(c["name_ko"] == "상관견관" for c in result["tengod_conflicts"])


# ── E-9 residual (2026-09-26): 관살혼잡, 정관 합거, 월지 충·형, 신약 ──


def _officer_grid(stems, branches=("酉", "子", "寅", "丑"), verdict=""):
    result = detect_patterns(
        day_master="丙", month_stem=stems[1], month_branch=branches[1],
        branches=list(branches), stems=list(stems), hidden_stems=[("main", "癸")],
        strength_verdict=verdict,
    )
    return next(g for g in result["regular_grid"] if g.name_ko == "정관격")


def test_officer_grid_broken_by_mixed_officers():
    grid = _officer_grid(["癸", "甲", "丙", "壬"])
    assert grid.confidence == "possible" and "관살혼잡" in grid.note


def test_officer_grid_broken_when_officer_is_combined_away():
    grid = _officer_grid(["癸", "甲", "丙", "戊"])   # 戊癸合
    assert grid.confidence == "possible" and "정관 합거" in grid.note


def test_month_branch_clash_is_a_caveat_not_a_break():
    grid = _officer_grid(["癸", "甲", "丙", "乙"], branches=("酉", "子", "午", "丑"))
    assert grid.confidence == "likely"
    assert "午子 충" in grid.note and "purity" in grid.note


def test_weak_day_master_officer_grid_names_resource_need():
    grid = _officer_grid(["癸", "甲", "丙", "乙"], verdict="weak")
    assert grid.confidence == "likely"
    assert "인성 is present" in grid.note
