"""Tests for classical star derivations."""
from __future__ import annotations

from saju_engine import stars as stars_module
from saju_engine.stars import derive_stars


def test_peach_blossom_present():
    # Day branch 午 → 도화 at 卯. Include 卯 in branches.
    stars = derive_stars(day_stem="丙", day_branch="午", branches=["午", "卯", "戌"])
    assert "卯" in stars["peach_blossom"]


def test_peach_blossom_absent():
    stars = derive_stars(day_stem="丙", day_branch="午", branches=["午", "戌"])
    assert stars["peach_blossom"] == []


def test_void_for_day_pillar():
    # Day pillar 甲子 belongs to the 甲子旬; 空亡 = 戌亥.
    stars = derive_stars(day_stem="甲", day_branch="子", branches=["戌", "亥", "寅"])
    assert set(stars["kong_mang"]) == {"戌", "亥"}


def test_noble_and_literary():
    # 丙 day master → 천을 at 亥/酉; 문창 at 申.
    stars = derive_stars(day_stem="丙", day_branch="子", branches=["亥", "酉", "申"])
    assert "亥" in stars["heavenly_noble"]
    assert "酉" in stars["heavenly_noble"]
    assert "申" in stars["literary_star"]


def test_hongyeom_present_when_day_branch_matches():
    # 甲 day master → 홍염 at 午. Day branch 午 matches.
    stars = derive_stars(day_stem="甲", day_branch="午", branches=["午", "子"])
    assert stars["hongyeom"] == ["午"]


def test_hongyeom_absent_when_day_branch_does_not_match():
    # 甲 day master → 홍염 at 午, but day branch is 子 → no 홍염 in spouse palace.
    stars = derive_stars(day_stem="甲", day_branch="子", branches=["子"])
    assert stars["hongyeom"] == []


def test_yangin_present_when_day_branch_matches():
    # 甲 day master → 양인 at 卯. Day branch 卯 matches.
    stars = derive_stars(day_stem="甲", day_branch="卯", branches=["卯"])
    assert stars["yangin"] == ["卯"]


def test_yangin_absent_for_yin_day_master():
    # 乙 is a Yin Day Master — no canonical 양인. Branch 卯 should NOT register.
    stars = derive_stars(day_stem="乙", day_branch="卯", branches=["卯"])
    assert stars["yangin"] == []


def test_hongyeom_table_all_stems_covered():
    # Sanity: every stem has a 홍염 mapping.
    for stem in ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]:
        assert stem in stars_module.HONGYEOM_BRANCHES, f"missing 홍염 for {stem}"


def test_hongyeom_alternate_branch_detected():
    """홍염 has two valid branches for 丙/丁, 庚/辛, 壬/癸.

    Regression for engine-audit A14: the engine previously stored only the
    primary alternate and missed the secondary one.
    *(see knowledge/11-gunghap.md §I)*
    """
    # 丁 DM → 홍염 at 寅 or 未.
    stars = derive_stars(day_stem="丁", day_branch="寅", branches=["寅"])
    assert "寅" in stars["hongyeom"]
    stars = derive_stars(day_stem="丁", day_branch="未", branches=["未"])
    assert "未" in stars["hongyeom"]
    # 辛 DM → 홍염 at 戌 or 酉.
    stars = derive_stars(day_stem="辛", day_branch="戌", branches=["戌"])
    assert "戌" in stars["hongyeom"]
    stars = derive_stars(day_stem="辛", day_branch="酉", branches=["酉"])
    assert "酉" in stars["hongyeom"]
    # 癸 DM → 홍염 at 子 or 申.
    stars = derive_stars(day_stem="癸", day_branch="子", branches=["子"])
    assert "子" in stars["hongyeom"]
    stars = derive_stars(day_stem="癸", day_branch="申", branches=["申"])
    assert "申" in stars["hongyeom"]


def test_year_anchor_peach_blossom():
    """B10: 도화 can be anchored off the year branch instead of day branch."""
    # Year branch 午 → 도화 at 卯; day branch 子 would give 도화 at 酉.
    stars = derive_stars(
        day_stem="丙", day_branch="子", branches=["午", "卯"],
        anchor="year", year_branch="午",
    )
    assert stars["peach_blossom"] == ["卯"]


def test_year_anchor_post_horse():
    """B10: 역마 can be anchored off the year branch."""
    # Year branch 巳 → 역마 at 亥.
    stars = derive_stars(
        day_stem="丙", day_branch="子", branches=["巳", "亥"],
        anchor="year", year_branch="巳",
    )
    assert stars["post_horse"] == ["亥"]


def test_year_anchor_canopy():
    """B10: 화개 can be anchored off the year branch."""
    # Year branch 亥 → 화개 at 未.
    stars = derive_stars(
        day_stem="丙", day_branch="子", branches=["亥", "未"],
        anchor="year", year_branch="亥",
    )
    assert stars["canopy"] == ["未"]


def test_twelve_stars_present():
    """Day branch 午 → triplet 寅午戌; twelve-star targets are derived."""
    # Include a few target branches to verify the lookup table.
    stars = derive_stars(
        day_stem="丙", day_branch="午",
        branches=["午", "戌", "亥", "子", "卯"],
    )
    assert stars["robbery_star"] == ["亥"]
    assert stars["disaster_star"] == ["子"]
    assert stars["general_star"] == ["午"]
    assert stars["annual_bane"] == ["卯"]
    # Targets not present should be empty.
    assert stars["lost_spirit"] == []
    assert stars["saddle_star"] == []


def test_twelve_stars_absent():
    """Twelve-star targets that are not in the four pillars return empty lists."""
    stars = derive_stars(
        day_stem="丙", day_branch="午", branches=["午", "戌"],
    )
    assert stars["robbery_star"] == []
    assert stars["disaster_star"] == []
    assert stars["heaven_bane"] == []


def test_deep_grudge_pair_detected():
    stars = derive_stars(
        day_stem="甲", day_branch="子",
        branches=["子", "未", "寅"],
    )
    assert "子-未" in stars["deep_grudge"]


def test_ghost_gate_pair_detected():
    stars = derive_stars(
        day_stem="甲", day_branch="寅",
        branches=["寅", "未", "酉"],
    )
    assert "寅-未" in stars["ghost_gate"]


def test_white_tiger_pillar():
    stars = derive_stars(
        day_stem="甲", day_branch="辰",
        branches=["辰"],
        day_pillar=("甲", "辰"),
    )
    assert stars["white_tiger"] == ["甲辰"]


def test_sky_hero_pillar():
    stars = derive_stars(
        day_stem="庚", day_branch="辰",
        branches=["辰"],
        day_pillar=("庚", "辰"),
    )
    assert stars["sky_hero"] == ["庚辰"]


def test_heavenly_virtue_stem():
    # Month branch 寅 → 천덕귀인 target 丁.
    stars = derive_stars(
        day_stem="甲", day_branch="子",
        branches=["子"],
        month_branch="寅", stems=["甲", "丙", "丁", "戊"],
    )
    assert stars["heavenly_virtue"] == ["丁"]


def test_monthly_virtue_stem():
    # Month branch 寅 → 월덕귀인 target 丙.
    stars = derive_stars(
        day_stem="甲", day_branch="子",
        branches=["子"],
        month_branch="寅", stems=["甲", "丙", "丁", "戊"],
    )
    assert stars["monthly_virtue"] == ["丙"]


def test_star_label_mapping():
    assert "겁살" in stars_module.STAR_LABELS["robbery_star"]
    assert "천덕귀인" in stars_module.STAR_LABELS["heavenly_virtue"]


def test_xun_kong_hand_table_matches_algorithmic_derivation():
    """Moved from a module-level loop in `stars.py` (2026-09-20, external
    code-quality review): a module-level `assert` is stripped under
    `python -O`, silently disabling this check, and re-ran the 60-entry
    comparison on every import for no benefit. The hand-built
    `_DAY_PILLAR_TO_XUN_KONG` table must agree with `_xun_kong_algorithmic`
    for every pillar in the 60-갑자 cycle."""
    from saju_engine import lookup as L
    for pillar in L.JIAZI_CYCLE:
        assert (
            stars_module._xun_kong_algorithmic(*pillar)
            == stars_module._DAY_PILLAR_TO_XUN_KONG[pillar]
        ), f"공망 table mismatch for {pillar}"


def test_year_anchor_twelve_stars_harish():
    """E-7 (2026-09-25 audit): the 12신살 follow the same anchor as 도화/역마/화개.

    Harish (壬申/乙巳/辛亥/己丑). Year-branch basis (申 → 申子辰 triplet) gives
    巳=겁살, 申=지살, 亥=망신, 丑=반안 — the traditional Korean basis the audit
    cross-checked. Day-branch basis (亥 → 亥卯未) gives 申=겁살, 亥=지살, 丑=월살.
    """
    common = dict(day_stem="辛", day_branch="亥", branches=["申", "巳", "亥", "丑"])
    year = derive_stars(**common, anchor="year", year_branch="申")
    assert year["robbery_star"] == ["巳"]
    assert year["earth_bane"] == ["申"]
    assert year["lost_spirit"] == ["亥"]
    assert year["saddle_star"] == ["丑"]
    assert year["monthly_bane"] == []

    day = derive_stars(**common)
    assert day["robbery_star"] == ["申"]
    assert day["earth_bane"] == ["亥"]
    assert day["monthly_bane"] == ["丑"]
