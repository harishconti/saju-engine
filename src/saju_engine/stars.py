"""Classical 신살 (star) overlays derived from the chart.

All rules are sourced from `knowledge/07-special-formations.md`. Stars are
returned as a dictionary of lists; they are descriptive overlays, not
standalone predictions.
"""
from __future__ import annotations

from . import lookup as L

from typing import Dict, Iterable, List, Optional, Tuple


# ── Display labels for engine output ─────────────────────────────────────────
# Used by report builders so that star keys render as Korean (한글) + Hanja
# rather than bare English snake_case.
STAR_LABELS: Dict[str, str] = {
    "kong_mang": "공망 (空亡)",
    "peach_blossom": "도화 (桃花)",
    "post_horse": "역마 (驛馬)",
    "canopy": "화개 (華蓋)",
    "heavenly_noble": "천을귀인 (天乙貴人)",
    "literary_star": "문창귀인 (文昌貴人)",
    "hongyeom": "홍염 (紅艶)",
    "yangin": "양인 (羊刃)",
    # Twelve-stars family (도화/역마/화개 duplicated above, so omitted below)
    "robbery_star": "겁살 (劫煞)",
    "disaster_star": "재살 (災煞)",
    "heaven_bane": "천살 (天煞)",
    "earth_bane": "지살 (地煞)",
    "annual_bane": "연살 (年煞)",
    "monthly_bane": "월살 (月煞)",
    "lost_spirit": "망신 (亡神)",
    "general_star": "장성 (將星)",
    "saddle_star": "반안 (攀鞍)",
    "six_harm_bane": "육해 (六害)",
    # Pair / pillar / month-based stars
    "deep_grudge": "원진 (怨嗔)",
    "ghost_gate": "귀문관 (鬼門關)",
    "white_tiger": "백호 (白虎)",
    "sky_hero": "괴강 (魁罡)",
    "heavenly_virtue": "천덕귀인 (天德貴人)",
    "monthly_virtue": "월덕귀인 (月德貴人)",
}


def star_label(key: str) -> str:
    """Return a display label for a star key."""
    return STAR_LABELS.get(key, key)


# ── 空亡 (Void / Emptiness) ──────────────────────────────────────────────────
# In the 60-cycle, every 10-day block (a "旬") has two branches that do not
# appear — those are the 空亡 branches for that block. Day pillar determines
# the 旬.
# The hand-maintained table below is kept as a cache and is verified at module
# load against an algorithmic derivation from the 60-cycle.
_DAY_PILLAR_TO_XUN_KONG: Dict[Tuple[str, str], List[str]] = {
    # Jia-Zi 旬 (day pillars 甲子–癸酉): 戌亥 absent
    ("甲", "子"): ["戌", "亥"],
    ("乙", "丑"): ["戌", "亥"],
    ("丙", "寅"): ["戌", "亥"],
    ("丁", "卯"): ["戌", "亥"],
    ("戊", "辰"): ["戌", "亥"],
    ("己", "巳"): ["戌", "亥"],
    ("庚", "午"): ["戌", "亥"],
    ("辛", "未"): ["戌", "亥"],
    ("壬", "申"): ["戌", "亥"],
    ("癸", "酉"): ["戌", "亥"],
    # Jia-Xu 旬 (day pillars 甲戌–癸未): 申酉 absent
    ("甲", "戌"): ["申", "酉"],
    ("乙", "亥"): ["申", "酉"],
    ("丙", "子"): ["申", "酉"],
    ("丁", "丑"): ["申", "酉"],
    ("戊", "寅"): ["申", "酉"],
    ("己", "卯"): ["申", "酉"],
    ("庚", "辰"): ["申", "酉"],
    ("辛", "巳"): ["申", "酉"],
    ("壬", "午"): ["申", "酉"],
    ("癸", "未"): ["申", "酉"],
    # Jia-Shen 旬 (day pillars 甲申–癸巳): 午未 absent
    ("甲", "申"): ["午", "未"],
    ("乙", "酉"): ["午", "未"],
    ("丙", "戌"): ["午", "未"],
    ("丁", "亥"): ["午", "未"],
    ("戊", "子"): ["午", "未"],
    ("己", "丑"): ["午", "未"],
    ("庚", "寅"): ["午", "未"],
    ("辛", "卯"): ["午", "未"],
    ("壬", "辰"): ["午", "未"],
    ("癸", "巳"): ["午", "未"],
    # Jia-Wu 旬 (day pillars 甲午–癸卯): 辰巳 absent
    ("甲", "午"): ["辰", "巳"],
    ("乙", "未"): ["辰", "巳"],
    ("丙", "申"): ["辰", "巳"],
    ("丁", "酉"): ["辰", "巳"],
    ("戊", "戌"): ["辰", "巳"],
    ("己", "亥"): ["辰", "巳"],
    ("庚", "子"): ["辰", "巳"],
    ("辛", "丑"): ["辰", "巳"],
    ("壬", "寅"): ["辰", "巳"],
    ("癸", "卯"): ["辰", "巳"],
    # Jia-Chen 旬 (day pillars 甲辰–癸丑): 寅卯 absent
    ("甲", "辰"): ["寅", "卯"],
    ("乙", "巳"): ["寅", "卯"],
    ("丙", "午"): ["寅", "卯"],
    ("丁", "未"): ["寅", "卯"],
    ("戊", "申"): ["寅", "卯"],
    ("己", "酉"): ["寅", "卯"],
    ("庚", "戌"): ["寅", "卯"],
    ("辛", "亥"): ["寅", "卯"],
    ("壬", "子"): ["寅", "卯"],
    ("癸", "丑"): ["寅", "卯"],
    # Jia-Yin 旬 (day pillars 甲寅–癸亥): 子丑 absent
    ("甲", "寅"): ["子", "丑"],
    ("乙", "卯"): ["子", "丑"],
    ("丙", "辰"): ["子", "丑"],
    ("丁", "巳"): ["子", "丑"],
    ("戊", "午"): ["子", "丑"],
    ("己", "未"): ["子", "丑"],
    ("庚", "申"): ["子", "丑"],
    ("辛", "酉"): ["子", "丑"],
    ("壬", "戌"): ["子", "丑"],
    ("癸", "亥"): ["子", "丑"],
}


def _xun_kong_algorithmic(day_stem: str, day_branch: str) -> List[str]:
    """Return the two 空亡 branches derived from the 60-cycle.

    For the 旬 starting at index ``n * 10`` in the 60-cycle, the ten used
    branches are ``BRANCH_ORDER[start .. start+9]`` modulo 12. The two absent
    branches are the next two in order.
    """
    pillar = (day_stem, day_branch)
    if pillar not in L.JIAZI_CYCLE:
        return []
    idx = L.JIAZI_CYCLE.index(pillar)
    xun_start = (idx // 10) * 10
    start_branch_idx = xun_start % 12
    absent = [
        L.BRANCH_ORDER[(start_branch_idx + 10) % 12],
        L.BRANCH_ORDER[(start_branch_idx + 11) % 12],
    ]
    return absent


# The hand-built _DAY_PILLAR_TO_XUN_KONG table is verified against this
# algorithmic derivation in tests/test_stars.py, not here as a module-level
# loop (moved 2026-09-20, external code-quality review: a module-level
# `assert` is stripped entirely under `python -O`, silently disabling the
# check, and re-runs the 60-entry comparison on every import for no benefit).


def _xun_kong(day_stem: str, day_branch: str) -> List[str]:
    """Return the two 空亡 branches for the day pillar's 旬."""
    return _xun_kong_algorithmic(day_stem, day_branch)


# ── Day-branch-based star triplets ───────────────────────────────────────────
# 도화 (Peach Blossom), 역마 (Post Horse), 화개 (Canopy) all use the same
# four triplet groups with different target branches.

_TARGET_PEACH_BLOSSOM = {"寅午戌": "卯", "巳酉丑": "午", "申子辰": "酉", "亥卯未": "子"}
_TARGET_POST_HORSE = {"寅午戌": "申", "巳酉丑": "亥", "申子辰": "寅", "亥卯未": "巳"}
_TARGET_CANOPY = {"寅午戌": "戌", "巳酉丑": "丑", "申子辰": "辰", "亥卯未": "未"}


def _triplet_for_branch(branch: str, triplets: Iterable[str]) -> Optional[str]:
    """Return the triplet string that contains ``branch``."""
    for triplet in triplets:
        if branch in set(triplet):
            return triplet
    return None


def _triplet_target(anchor_branch: str, target_map: Dict[str, str]) -> Optional[str]:
    """Return the target branch for a branch-anchored star, or None.

    The same triplet lookup applies to both day-branch (common) and year-branch
    (고법) anchoring per knowledge/07-special-formations.md.
    """
    triplet = _triplet_for_branch(anchor_branch, target_map.keys())
    return target_map.get(triplet) if triplet else None


# ── 십이신살 (十二神殺) — Twelve Stars ────────────────────────────────────────
# Derived from the day-branch's three-harmony triplet. 도화/역마/화개 are
# handled separately above, so this table covers the remaining nine.
_TWELVE_STARS: Dict[str, Dict[str, str]] = {
    "寅午戌": {
        "robbery_star": "亥",
        "disaster_star": "子",
        "heaven_bane": "丑",
        "earth_bane": "寅",
        "annual_bane": "卯",
        "monthly_bane": "辰",
        "lost_spirit": "巳",
        "general_star": "午",
        "saddle_star": "未",
        "six_harm_bane": "酉",
    },
    "申子辰": {
        "robbery_star": "巳",
        "disaster_star": "午",
        "heaven_bane": "未",
        "earth_bane": "申",
        "annual_bane": "酉",
        "monthly_bane": "戌",
        "lost_spirit": "亥",
        "general_star": "子",
        "saddle_star": "丑",
        "six_harm_bane": "卯",
    },
    "巳酉丑": {
        "robbery_star": "寅",
        "disaster_star": "卯",
        "heaven_bane": "辰",
        "earth_bane": "巳",
        "annual_bane": "午",
        "monthly_bane": "未",
        "lost_spirit": "申",
        "general_star": "酉",
        "saddle_star": "戌",
        "six_harm_bane": "子",
    },
    "亥卯未": {
        "robbery_star": "申",
        "disaster_star": "酉",
        "heaven_bane": "戌",
        "earth_bane": "亥",
        "annual_bane": "子",
        "monthly_bane": "丑",
        "lost_spirit": "寅",
        "general_star": "卯",
        "saddle_star": "辰",
        "six_harm_bane": "午",
    },
}
_TWELVE_STAR_KEYS = list(next(iter(_TWELVE_STARS.values())).keys())


# ── Branch-pair stars ────────────────────────────────────────────────────────
# 원진살 (Deep Grudge) and 귀문관살 (Ghost Gate) are triggered when both
# branches of a listed pair appear in the four pillars.
_DEEP_GRUDGE_PAIRS: List[Tuple[str, str]] = [
    ("子", "未"),
    ("丑", "午"),
    ("寅", "酉"),
    ("卯", "申"),
    ("辰", "亥"),
    ("巳", "戌"),
]

_GHOST_GATE_PAIRS: List[Tuple[str, str]] = [
    ("子", "酉"),
    ("丑", "午"),
    ("寅", "未"),
    ("卯", "申"),
    ("辰", "亥"),
    ("巳", "戌"),
]


def _matched_pairs(
    pairs: List[Tuple[str, str]],
    present: set,
) -> List[str]:
    """Return joined branch-pair strings for every pair found in ``present``."""
    matches: List[str] = []
    for a, b in pairs:
        if a in present and b in present:
            matches.append(f"{a}-{b}")
    return matches


# ── Day-pillar stars ─────────────────────────────────────────────────────────
_WHITE_TIGER_PILLARS: set = {
    ("甲", "辰"),
    ("乙", "未"),
    ("丙", "戌"),
    ("丁", "丑"),
    ("戊", "辰"),
    ("壬", "戌"),
    ("癸", "丑"),
}

_SKY_HERO_PILLARS: set = {
    ("戊", "戌"),
    ("庚", "辰"),
    ("庚", "戌"),
    ("壬", "辰"),
}


# ── Month-based virtue stars ─────────────────────────────────────────────────
# The target stem is determined by the month branch (월지). It "appears" when
# that stem is found among the four natal 천간.
_HEAVENLY_VIRTUE_STEM: Dict[str, str] = {
    "寅": "丁",
    "卯": "申",
    "辰": "壬",
    "巳": "辛",
    "午": "亥",
    "未": "甲",
    "申": "癸",
    "酉": "寅",
    "戌": "丙",
    "亥": "乙",
    "子": "巳",
    "丑": "庚",
}

_MONTHLY_VIRTUE_STEM: Dict[str, str] = {
    "寅": "丙",
    "卯": "甲",
    "辰": "壬",
    "巳": "庚",
    "午": "丙",
    "未": "甲",
    "申": "壬",
    "酉": "庚",
    "戌": "丙",
    "亥": "甲",
    "子": "壬",
    "丑": "庚",
}


# ── Day-stem-based noble/literary stars ─────────────────────────────────────
# From knowledge/07-special-formations.md

_HEAVENLY_NOBLE: Dict[str, List[str]] = {
    "甲": ["丑", "未"],
    "乙": ["子", "申"],
    "丙": ["亥", "酉"],
    "丁": ["亥", "酉"],
    "戊": ["丑", "未"],
    "己": ["子", "申"],
    "庚": ["丑", "未"],
    "辛": ["寅", "午"],
    "壬": ["卯", "巳"],
    "癸": ["卯", "巳"],
}

_LITERARY_STAR: Dict[str, str] = {
    "甲": "亥",
    "乙": "午",
    "丙": "申",
    "丁": "酉",
    "戊": "申",
    "己": "酉",
    "庚": "亥",
    "辛": "子",
    "壬": "寅",
    "癸": "卯",
}


# ── 紅艶殺 (Red Flame / 홍염살) ──────────────────────────────────────────────
# From knowledge/11-gunghap.md Section I. Each day stem maps to one or two
# valid 홍염 branches. 일지에 홍염이 있으면 배우자 매력 포인트가 큰 편 —
# soft indicator in 궁합.
HONGYEOM_BRANCHES: Dict[str, List[str]] = {
    "甲": ["午"],
    "乙": ["午"],
    "丙": ["寅", "未"],
    "丁": ["寅", "未"],
    "戊": ["辰"],
    "己": ["辰"],
    "庚": ["戌", "酉"],
    "辛": ["戌", "酉"],
    "壬": ["子", "申"],
    "癸": ["子", "申"],
}


def _hongyeom(day_stem: str, day_branch: str) -> List[str]:
    """Return [branch] if the day-branch matches a 홍염 position for day_stem.

    A 일지 홍염 is the strongest placement: it puts the magnetic-fire star
    directly in the spouse palace, marking the partner as a major attractor.
    """
    targets = HONGYEOM_BRANCHES.get(day_stem, [])
    return [day_branch] if day_branch in targets else []


# ── 羊刃殺 (Blade of the Sheep / 양인살) ─────────────────────────────────────
# From knowledge/07-special-formations.md Part 1.D and 11-gunghap.md §I.
# Day Master at its 제왕 (peak) branch. 양인격 charts are powerful but
# impulsive; in 궁합, 양인 cross-patterns are a yellow flag.
YANGIN_BRANCHES: Dict[str, str] = {
    "甲": "卯",
    "丙": "午",
    "戊": "午",
    "庚": "酉",
    "壬": "子",
    # 乙 / 丁 / 己 / 辛 / 癸 have no 양인 (Yin stems ride differently).
}


def _yangin(day_stem: str, day_branch: str) -> List[str]:
    """Return [branch] if the day-branch is the 양인 branch for day_stem.

    Note: only Yang Day Masters have a 양인. Yin Day Masters ride on their
    Yang counterpart (e.g. 丁 follows 丙 to 午; 己 follows 戊 to 午) but classical
    Korean Myeongri treats only the five Yang stems as canonical 양인 holders.
    """
    target = YANGIN_BRANCHES.get(day_stem)
    return [target] if target and day_branch == target else []


def derive_stars(
    day_stem: str,
    day_branch: str,
    branches: List[str],
    anchor: str = "day",
    year_branch: Optional[str] = None,
    *,
    month_branch: Optional[str] = None,
    stems: Optional[List[str]] = None,
    day_pillar: Optional[Tuple[str, str]] = None,
) -> Dict[str, List[str]]:
    """Return a dictionary of classical stars present in the natal chart.

    Keys:
      - kong_mang (空亡): void branches for the day pillar's 旬.
      - peach_blossom (桃花): 도화 branch.
      - post_horse (驛馬): 역마 branch.
      - canopy (華蓋): 화개 branch.
      - heavenly_noble (天乙貴人): noble branches.
      - literary_star (文昌貴人): literary branch.
      - hongyeom (紅艶殺): red-flame star (single branch match on day-branch).
      - yangin (羊刃殺): blade-of-the-sheep star (single branch match on day-branch).
      - robbery_star (劫煞), disaster_star (災煞), heaven_bane (天煞),
        earth_bane (地煞), annual_bane (年煞), monthly_bane (月煞),
        lost_spirit (亡神), general_star (將星), saddle_star (攀鞍),
        six_harm_bane (六害): the remaining 십이신살 stars keyed by the anchor
        branch's triplet (see ``anchor`` below).
      - deep_grudge (怨嗔): branch pairs matched in the chart.
      - ghost_gate (鬼門關): branch pairs matched in the chart.
      - white_tiger (白虎): day pillar match, if provided.
      - sky_hero (魁罡): day pillar match, if provided.
      - heavenly_virtue (天德貴人): matching 천간, if month_branch + stems provided.
      - monthly_virtue (月德貴人): matching 천간, if month_branch + stems provided.

    ``anchor`` selects the school for 도화/역마/화개 and the other 십이신살:
      - ``"day"`` (default): day-branch anchoring, the most common Korean convention.
      - ``"year"``: year-branch anchoring (고법 / alternative school).
    The day-stem-based stars (천을귀인, 문창, 홍염, 양인) are unaffected.

    Each value is a list; an empty list means the star's branch/stem/pillar is
    not present in the natal chart (the star exists abstractly but is not
    activated natally).
    """
    present = set(branches)
    stars: Dict[str, List[str]] = {}

    # 空亡
    stars["kong_mang"] = [b for b in _xun_kong(day_stem, day_branch) if b in present]

    # 도화 / 역마 / 화개 — anchor school
    if anchor == "year" and year_branch:
        anchor_branch = year_branch
    else:
        anchor_branch = day_branch

    peach = _triplet_target(anchor_branch, _TARGET_PEACH_BLOSSOM)
    stars["peach_blossom"] = [peach] if peach and peach in present else []

    horse = _triplet_target(anchor_branch, _TARGET_POST_HORSE)
    stars["post_horse"] = [horse] if horse and horse in present else []

    canopy = _triplet_target(anchor_branch, _TARGET_CANOPY)
    stars["canopy"] = [canopy] if canopy and canopy in present else []

    # 천을귀인 and 문창
    stars["heavenly_noble"] = [b for b in _HEAVENLY_NOBLE.get(day_stem, []) if b in present]
    lit = _LITERARY_STAR.get(day_stem)
    stars["literary_star"] = [lit] if lit and lit in present else []

    # 홍염 / 양인 (day-stem-based, day-branch-as-position)
    stars["hongyeom"] = _hongyeom(day_stem, day_branch)
    stars["yangin"] = _yangin(day_stem, day_branch)

    # 십이신살 (十二神殺) — remaining stars keyed by the same anchor branch as
    # 도화/역마/화개 (day by default; year for the traditional Korean basis —
    # knowledge/07-special-formations.md §십이신살 school note, E-7).
    triplet = _triplet_for_branch(anchor_branch, _TWELVE_STARS.keys())
    if triplet:
        for key, target in _TWELVE_STARS[triplet].items():
            stars[key] = [target] if target in present else []
    else:
        for key in _TWELVE_STAR_KEYS:
            stars[key] = []

    # Branch-pair stars
    stars["deep_grudge"] = _matched_pairs(_DEEP_GRUDGE_PAIRS, present)
    stars["ghost_gate"] = _matched_pairs(_GHOST_GATE_PAIRS, present)

    # Day-pillar stars
    if day_pillar:
        stars["white_tiger"] = [f"{day_pillar[0]}{day_pillar[1]}"] if day_pillar in _WHITE_TIGER_PILLARS else []
        stars["sky_hero"] = [f"{day_pillar[0]}{day_pillar[1]}"] if day_pillar in _SKY_HERO_PILLARS else []
    else:
        stars["white_tiger"] = []
        stars["sky_hero"] = []

    # Month-branch → virtue stars. 천덕귀인's classical table targets a stem
    # for 8 of the 12 months, but a BRANCH for 卯/午/酉/子 (knowledge/
    # 07-special-formations.md) — those four can never appear among natal
    # stems, so they must be checked against the natal branches instead.
    if month_branch:
        hv = _HEAVENLY_VIRTUE_STEM.get(month_branch)
        if hv is None:
            stars["heavenly_virtue"] = []
        elif hv in L.STEM_INDEX:
            stars["heavenly_virtue"] = [s for s in (stems or []) if s == hv]
        else:
            stars["heavenly_virtue"] = [hv] if hv in present else []
        mv = _MONTHLY_VIRTUE_STEM.get(month_branch)
        stars["monthly_virtue"] = [s for s in (stems or []) if s == mv] if mv else []
    else:
        stars["heavenly_virtue"] = []
        stars["monthly_virtue"] = []

    return stars


def derive_star_positions(
    day_stem: str,
    day_branch: str,
    position_branches: List[Tuple[str, str]],
    anchor: str = "day",
    year_branch: Optional[str] = None,
    *,
    month_branch: Optional[str] = None,
    stems: Optional[List[str]] = None,
    day_pillar: Optional[Tuple[str, str]] = None,
) -> Dict[str, List[str]]:
    """Return the palace positions where each classical star is activated.

    ``position_branches`` is a list of ``(position_name, branch)`` pairs, e.g.
    ``[("year", "午"), ("month", "卯"), ...]``. The returned dictionary maps
    star keys to lists of position names. This lets callers distinguish, for
    example, 桃花 in the day branch (spouse palace) from 桃花 in the hour
    branch (children/romance palace).
    """
    positions_by_branch: Dict[str, List[str]] = {}
    for pos, branch in position_branches:
        positions_by_branch.setdefault(branch, []).append(pos)

    branch_stars = derive_stars(
        day_stem=day_stem,
        day_branch=day_branch,
        branches=list(positions_by_branch.keys()),
        anchor=anchor,
        year_branch=year_branch,
        month_branch=month_branch,
        stems=stems,
        day_pillar=day_pillar,
    )

    star_positions: Dict[str, List[str]] = {}
    for star, branches in branch_stars.items():
        star_positions[star] = [
            pos
            for b in branches
            for pos in positions_by_branch.get(b, [])
        ]
    return star_positions
