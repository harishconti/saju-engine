"""Tests for classical grid/pattern detection."""
from __future__ import annotations

from saju_engine.patterns import detect_patterns


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
    # Grid-level 양인격 excludes the month pillar (positions 0,2,3 only).
    assert result["yangin_grid"]["present"] is True
    assert 1 not in result["yangin_grid"]["positions"]


def test_yangin_star_vs_grid_distinction():
    """B11: 양인 in the month pillar registers as a star but not as a grid."""
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
    assert result["yangin_grid"]["present"] is False


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
    assert result["jianlu"]["present"] is True


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
