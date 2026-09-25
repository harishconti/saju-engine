"""Tests for lookup tables (십신, 12운성, branch relationships)."""
from __future__ import annotations

import pytest

from saju_engine import lookup as L


# Independent reference for the 10×10 ten-god relation table.
# Same element: same polarity → 비견, opposite polarity → 겁재.
# Output element (DM generates): same polarity → 식신, opposite → 상관.
# Wealth element (DM overcomes): same polarity → 편재, opposite → 정재.
# Authority element (overcomes DM): same polarity → 편관, opposite → 정관.
# Resource element (generates DM): same polarity → 편인, opposite → 정인.
_TENGOD_RULES = {
    "비견": ("same", "same"),
    "겁재": ("same", "diff"),
    "식신": ("output", "same"),
    "상관": ("output", "diff"),
    "편재": ("wealth", "same"),
    "정재": ("wealth", "diff"),
    "편관": ("authority", "same"),
    "정관": ("authority", "diff"),
    "편인": ("resource", "same"),
    "정인": ("resource", "diff"),
}


def _relation_type(dm_element: str, other_element: str) -> str:
    if dm_element == other_element:
        return "same"
    if L.GENERATES.get(dm_element) == other_element:
        return "output"
    if L.OVERCOMES.get(dm_element) == other_element:
        return "wealth"
    if L.GENERATES.get(other_element) == dm_element:
        return "resource"
    if L.OVERCOMES.get(other_element) == dm_element:
        return "authority"
    raise ValueError(f"unexpected element pair: {dm_element}, {other_element}")


def _expected_tengod(day_master: str, other: str) -> str:
    dm_info = L.STEM_INFO[day_master]
    ot_info = L.STEM_INFO[other]
    rel = _relation_type(dm_info["element"], ot_info["element"])
    same_polarity = dm_info["polarity"] == ot_info["polarity"]
    polarity_key = "same" if same_polarity else "diff"
    for name, (r, p) in _TENGOD_RULES.items():
        if r == rel and p == polarity_key:
            return name
    raise ValueError(f"no ten-god rule for {day_master}, {other}")


@pytest.mark.parametrize(
    "day_master,other,expected",
    [
        ("甲", "甲", "비견"),
        ("甲", "乙", "겁재"),
        ("甲", "丙", "식신"),
        ("甲", "戊", "편재"),
        ("甲", "庚", "편관"),
        ("甲", "壬", "편인"),
        ("甲", "辛", "정관"),
        ("甲", "癸", "정인"),
        ("丙", "壬", "편관"),
        ("丙", "癸", "정관"),
        ("丙", "甲", "편인"),
    ],
)
def test_ten_god(day_master, other, expected):
    assert L.ten_god(day_master, other) == expected


@pytest.mark.parametrize("day_master", L.STEM_ORDER)
@pytest.mark.parametrize("other", L.STEM_ORDER)
def test_ten_god_exhaustive(day_master, other):
    assert L.ten_god(day_master, other) == _expected_tengod(day_master, other)


@pytest.mark.parametrize(
    "year_stem,expected",
    [
        # 甲己之年丙作首， 乙庚之岁戊为头
        ("甲", "丙"),
        ("己", "丙"),
        ("乙", "戊"),
        ("庚", "戊"),
        # 丙辛之岁寻庚起， 丁壬壬位顺行流
        ("丙", "庚"),
        ("辛", "庚"),
        ("丁", "壬"),
        ("壬", "壬"),
        # 若问戊癸何方发， 甲寅之上好追求
        ("戊", "甲"),
        ("癸", "甲"),
    ],
)
def test_oho_dun_classical_verse(year_stem, expected):
    assert L._OHO_DUN[year_stem] == expected


@pytest.mark.parametrize(
    "day_master,branch,expected",
    [
        ("丙", "寅", "장생"),
        ("丙", "午", "제왕"),
        ("丙", "亥", "절"),
        ("甲", "亥", "장생"),
        ("甲", "卯", "제왕"),
        ("甲", "午", "사"),
        ("辛", "子", "장생"),
        ("辛", "亥", "목욕"),
        ("辛", "戌", "관대"),
        ("癸", "卯", "장생"),
        ("癸", "亥", "제왕"),
    ],
)
def test_twelve_stage(day_master, branch, expected):
    assert L.twelve_stage(day_master, branch) == expected


def test_cycle_index_and_step():
    assert L.cycle_index("甲", "子") == 0
    assert L.cycle_index("甲", "戌") == 10
    assert L.step_cycle("甲", "子", 1) == ("乙", "丑")
    assert L.step_cycle("甲", "子", -1) == ("癸", "亥")
    assert L.step_cycle("癸", "亥", 1) == ("甲", "子")


def test_branch_relationships_present():
    # Spot-check that the relationship tables are populated.
    assert ("子", "丑", "Earth") in L.SIX_COMBINATIONS
    assert ("子", "午") in L.SIX_CLASHES
    assert ("子", "未") in L.SIX_HARMS
    assert ("子", "酉") in L.SIX_BREAKS
    assert "辰" in L.SELF_PUNISHMENTS
    assert ("申", "子", "辰", "Water") in L.THREE_HARMONIES
    assert any(a == "寅" and b == "巳" and c == "申" for a, b, c, _ in L.THREE_PUNISHMENTS)


# Hidden stems (지장간) — the table that underpins strength and ten-god
# distribution. Independent reference from `knowledge/02-branches.md` §2.
# Each branch lists the Main (본기), and where present Middle (중기) and
# Residual (여기) hidden stems. The first stem is always the main, and a
# branch may have 1, 2, or 3 hidden stems. Spot-check the table for
# completeness and lock it down to prevent typos.


@pytest.mark.parametrize(
    "branch,expected",
    [
        # 4 pure branches (1 hidden stem each, all main only).
        ("子", ("癸",)),
        ("卯", ("乙",)),
        ("酉", ("辛",)),
        # 亥: 2 hidden stems (main 壬 + middle 甲).
        ("亥", ("壬", "甲")),
        # 午: 2 hidden stems (main 丁 + middle 己).
        ("午", ("丁", "己")),
        # 寅: 3 hidden stems (main 甲 + middle 丙 + residual 戊).
        ("寅", ("甲", "丙", "戊")),
        # 巳: 3 hidden stems (main 丙 + middle 庚 + residual 戊).
        ("巳", ("丙", "庚", "戊")),
        # 申: 3 hidden stems (main 庚 + middle 壬 + residual 戊).
        ("申", ("庚", "壬", "戊")),
        # 丑: 3 hidden stems (main 己 + middle 辛 + residual 癸).
        # Corrected 2026-09-25 (external report review, E-2): 중기/여기 were
        # swapped for all four storage branches (辰戌丑未) — see lookup.py.
        ("丑", ("己", "辛", "癸")),
        # 辰: 3 hidden stems (main 戊 + middle 癸 + residual 乙).
        ("辰", ("戊", "癸", "乙")),
        # 未: 3 hidden stems (main 己 + middle 乙 + residual 丁).
        ("未", ("己", "乙", "丁")),
        # 戌: 3 hidden stems (main 戊 + middle 丁 + residual 辛).
        ("戌", ("戊", "丁", "辛")),
    ],
)
def test_hidden_stems_for_branch(branch, expected):
    """Each branch must have the correct list of Main/Middle/Residual stems
    in the order documented in knowledge/02-branches.md. The tuple contains
    the stem names in document order: main first, then middle, then residual.
    """
    info = L.HIDDEN_STEMS[branch]
    got = tuple(info.get(role) for role in ("main", "middle", "residual") if role in info)
    assert got == expected, (
        f"Hidden stems for {branch} expected {expected}, got {got}. "
        f"This table underpins strength and ten-god distribution; "
        f"see knowledge/02-branches.md."
    )


def test_hidden_stems_table_covers_all_twelve_branches():
    """Sanity: the table must cover all 12 branches, no more, no less."""
    assert set(L.HIDDEN_STEMS.keys()) == {
        "子", "丑", "寅", "卯", "辰", "巳",
        "午", "未", "申", "酉", "戌", "亥",
    }


# STEM_INFO and BRANCH_INFO are the foundation tables: element + polarity
# for every stem and branch. A typo in either would silently corrupt every
# ten-god, strength, and 용신 derivation. Lock them down with an exhaustive
# parametric check from an independent reference.


@pytest.mark.parametrize(
    "stem,element,polarity",
    [
        # Wood: 甲(양) 乙(음)
        ("甲", "Wood", "Yang"),
        ("乙", "Wood", "Yin"),
        # Fire: 丙(양) 丁(음)
        ("丙", "Fire", "Yang"),
        ("丁", "Fire", "Yin"),
        # Earth: 戊(양) 己(음)
        ("戊", "Earth", "Yang"),
        ("己", "Earth", "Yin"),
        # Metal: 庚(양) 辛(음)
        ("庚", "Metal", "Yang"),
        ("辛", "Metal", "Yin"),
        # Water: 壬(양) 癸(음)
        ("壬", "Water", "Yang"),
        ("癸", "Water", "Yin"),
    ],
)
def test_stem_info_element_and_polarity(stem, element, polarity):
    assert L.STEM_INFO[stem]["element"] == element
    assert L.STEM_INFO[stem]["polarity"] == polarity


def test_stem_info_covers_all_ten_stems():
    """Sanity: STEM_INFO must cover exactly the 10 heavenly stems."""
    assert set(L.STEM_INFO.keys()) == {
        "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸",
    }


@pytest.mark.parametrize(
    "branch,element,polarity",
    [
        # 子(수 양) — Rat
        ("子", "Water", "Yang"),
        # 丑(토 음) — Ox
        ("丑", "Earth", "Yin"),
        # 寅(목 양) — Tiger
        ("寅", "Wood", "Yang"),
        # 卯(목 음) — Rabbit
        ("卯", "Wood", "Yin"),
        # 辰(토 양) — Dragon
        ("辰", "Earth", "Yang"),
        # 巳(화 음) — Snake
        ("巳", "Fire", "Yin"),
        # 午(화 양) — Horse
        ("午", "Fire", "Yang"),
        # 未(토 음) — Goat
        ("未", "Earth", "Yin"),
        # 申(금 양) — Monkey
        ("申", "Metal", "Yang"),
        # 酉(금 음) — Rooster
        ("酉", "Metal", "Yin"),
        # 戌(토 양) — Dog
        ("戌", "Earth", "Yang"),
        # 亥(수 음) — Pig
        ("亥", "Water", "Yin"),
    ],
)
def test_branch_info_element_and_polarity(branch, element, polarity):
    assert L.BRANCH_INFO[branch]["element"] == element
    assert L.BRANCH_INFO[branch]["polarity"] == polarity


def test_branch_info_covers_all_twelve_branches():
    """Sanity: BRANCH_INFO must cover exactly the 12 earthly branches."""
    assert set(L.BRANCH_INFO.keys()) == {
        "子", "丑", "寅", "卯", "辰", "巳",
        "午", "未", "申", "酉", "戌", "亥",
    }


# 합/충/형/파/해 tables (six-harmonies, six-clashes, six-harms, six-breaks)
# are the foundation for finding pair-level relationships inside a chart.
# Each has 6 entries. A typo or omission would silently miss a relationship,
# so we lock down the full table contents from an independent reference.


SIX_COMBINATIONS_REFERENCE = {
    ("子", "丑"): "Earth",
    ("寅", "亥"): "Wood",
    ("卯", "戌"): "Fire",
    ("辰", "酉"): "Metal",
    ("巳", "申"): "Water",
    ("午", "未"): "Earth",  # 오미합 화토 — Fire/Earth alliance
}


SIX_CLASHES_REFERENCE = {
    ("子", "午"), ("丑", "未"), ("寅", "申"),
    ("卯", "酉"), ("辰", "戌"), ("巳", "亥"),
}


SIX_HARMS_REFERENCE = {
    ("子", "未"), ("丑", "午"), ("寅", "巳"),
    ("卯", "辰"), ("申", "亥"), ("酉", "戌"),
}


SIX_BREAKS_REFERENCE = {
    ("子", "酉"), ("午", "卯"), ("辰", "丑"),
    ("未", "戌"), ("申", "巳"), ("寅", "亥"),
}


def test_six_combinations_table():
    """All 6 육합 pairs with their combined elements per knowledge/02."""
    got = {(a, b): elem for a, b, elem in L.SIX_COMBINATIONS}
    assert got == SIX_COMBINATIONS_REFERENCE


def test_six_combinations_is_symmetric():
    """SIX_COMBINATIONS is stored canonically (one direction per pair), but
    the lookup is symmetric by convention. The two actual lookup sites
    (`compat._branch_pair_lookup` and `engine.compute_chart`) both check
    (a, b) OR (b, a). This test guards that contract for the canonical
    pairs by asserting the table stores exactly 6 pairs (not 12) covering
    all 12 branches.
    """
    canonical = {(a, b) for a, b, _ in L.SIX_COMBINATIONS}
    assert len(canonical) == 6, f"Expected 6 canonical combinations, got {len(canonical)}"
    flat = {branch for pair in canonical for branch in pair}
    assert len(flat) == 12, (
        f"Expected 12 unique branches across the 6 combinations, got {flat}"
    )


def test_six_clashes_table():
    """All 6 육충 pairs (子午, 丑未, 寅申, 卯酉, 辰戌, 巳亥)."""
    got = {(a, b) for a, b in L.SIX_CLASHES}
    assert got == SIX_CLASHES_REFERENCE


def test_six_clashes_is_symmetric():
    """SIX_CLASHES is stored canonically (one direction per pair); the engine
    looks it up via `pair_set == {a, c}` to enforce symmetry at the call site.
    """
    canonical = {tuple(sorted(p)) for p in L.SIX_CLASHES}
    assert len(canonical) == 6, f"Expected 6 canonical clashes, got {len(canonical)}"
    flat = {branch for pair in canonical for branch in pair}
    assert len(flat) == 12, (
        f"Expected 12 unique branches across the 6 clashes, got {flat}"
    )


def test_six_harms_table():
    """All 6 육해 pairs (子未, 丑午, 寅巳, 卯辰, 申亥, 酉戌)."""
    got = {(a, b) for a, b in L.SIX_HARMS}
    assert got == SIX_HARMS_REFERENCE


def test_six_harms_is_symmetric():
    """SIX_HARMS is stored canonically; lookup is symmetric via pair-set."""
    canonical = {tuple(sorted(p)) for p in L.SIX_HARMS}
    assert len(canonical) == 6, f"Expected 6 canonical harms, got {len(canonical)}"
    flat = {branch for pair in canonical for branch in pair}
    assert len(flat) == 12, (
        f"Expected 12 unique branches across the 6 harms, got {flat}"
    )


def test_six_breaks_table():
    """All 6 육파 pairs (子酉, 午卯, 辰丑, 未戌, 申巳, 寅亥)."""
    got = {(a, b) for a, b in L.SIX_BREAKS}
    assert got == SIX_BREAKS_REFERENCE


def test_six_breaks_is_symmetric():
    """SIX_BREAKS is stored canonically; lookup is symmetric via pair-set."""
    canonical = {tuple(sorted(p)) for p in L.SIX_BREAKS}
    assert len(canonical) == 6, f"Expected 6 canonical breaks, got {len(canonical)}"
    flat = {branch for pair in canonical for branch in pair}
    assert len(flat) == 12, (
        f"Expected 12 unique branches across the 6 breaks, got {flat}"
    )


# Three-Harmony (삼합, 申子辰 / 亥卯未 / 寅午戌 / 巳酉丑) and Three-Punishment
# (삼형) groups — both are detected as frame-level structures in a chart.
# Three-Harmony forms 4 groups × 3 branches = 12 unique branches (a complete
# coverage of the 12 branches). Three-Punishment has 3 groups with one
# partial (子卯 alone) for natal charts that lack a third member.


THREE_HARMONIES_REFERENCE = [
    ("申", "子", "辰", "Water"),
    ("亥", "卯", "未", "Wood"),
    ("寅", "午", "戌", "Fire"),
    ("巳", "酉", "丑", "Metal"),
]


def test_three_harmonies_table():
    """All 4 삼합 frames with their elements per knowledge/07 §2."""
    got = list(L.THREE_HARMONIES)
    assert got == THREE_HARMONIES_REFERENCE


def test_three_harmonies_cover_all_twelve_branches_exactly_once():
    """The 4 삼합 groups partition the 12 branches (each branch in exactly 1 group)."""
    flat = {branch for triple in L.THREE_HARMONIES for branch in triple[:3]}
    assert flat == {
        "子", "丑", "寅", "卯", "辰", "巳",
        "午", "未", "申", "酉", "戌", "亥",
    }, f"삼합 groups must cover all 12 branches exactly once, got {flat}"


def test_three_harmonies_elements_match_생극_cycle():
    """Sanity: each 삼합 group produces the element of its 합 member
    (申子辰 → Water, etc.), matching the element of the middle/seasonal branch.
    """
    for _, mid, _, element in L.THREE_HARMONIES:
        assert L.BRANCH_INFO[mid]["element"] == element, (
            f"삼합 {mid} should produce {L.BRANCH_INFO[mid]['element']} "
            f"per its seasonal branch element, got {element}"
        )


def test_three_punishments_table():
    """All 3 삼형 groups (寅巳申, 丑戌未, 子卯) per knowledge/07 §4.

    Note: 子卯 is a 2-member (incomplete) punishment group because natal charts
    have only 4 branches, so the engine treats it as a special case with an
    em-dash (—) placeholder for the absent third member.
    """
    assert len(L.THREE_PUNISHMENTS) == 3
    # Strip the em-dash placeholder and any '—' member from each triple.
    real_branches = [
        tuple(sorted(b for b in t[:3] if b and b != "—"))
        for t in L.THREE_PUNISHMENTS
    ]
    assert real_branches == [
        tuple(sorted(["寅", "巳", "申"])),
        tuple(sorted(["丑", "戌", "未"])),
        tuple(sorted(["子", "卯"])),
    ]


def test_jiazi_cycle_sanity_points():
    """Moved from a module-level `assert` in `lookup.py` (2026-09-20, external
    code-quality review): a module-level assert is stripped under `python -O`,
    silently disabling the check, and re-ran on every import for no benefit."""
    assert L.JIAZI_CYCLE[0] == ("甲", "子")
    assert L.JIAZI_CYCLE[1] == ("乙", "丑")
    assert L.JIAZI_CYCLE[10] == ("甲", "戌")
    assert L.JIAZI_CYCLE[-1] == ("癸", "亥")
    assert len(L.JIAZI_CYCLE) == 60
