"""Korean 명리 lookups sourced from the project's `knowledge/` directory.

All tables here are derived from:
  - knowledge/01-stems.md
  - knowledge/02-branches.md
  - knowledge/03-five-elements.md
  - knowledge/04-yin-yang.md
  - knowledge/05-ten-gods.md
  - knowledge/06-twelve-stages.md
  - knowledge/08-luck-pillars.md

Do not add a table here that isn't backed by a knowledge file.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple


# ── Element + polarity per stem ──────────────────────────────────────────────
# From knowledge/01-stems.md and 04-yin-yang.md
STEM_INFO: Dict[str, Dict[str, str]] = {
    "甲": {"element": "Wood",  "polarity": "Yang", "hanja": "甲", "korean": "갑"},
    "乙": {"element": "Wood",  "polarity": "Yin",  "hanja": "乙", "korean": "을"},
    "丙": {"element": "Fire",  "polarity": "Yang", "hanja": "丙", "korean": "병"},
    "丁": {"element": "Fire",  "polarity": "Yin",  "hanja": "丁", "korean": "정"},
    "戊": {"element": "Earth", "polarity": "Yang", "hanja": "戊", "korean": "무"},
    "己": {"element": "Earth", "polarity": "Yin",  "hanja": "己", "korean": "기"},
    "庚": {"element": "Metal", "polarity": "Yang", "hanja": "庚", "korean": "경"},
    "辛": {"element": "Metal", "polarity": "Yin",  "hanja": "辛", "korean": "신"},
    "壬": {"element": "Water", "polarity": "Yang", "hanja": "壬", "korean": "임"},
    "癸": {"element": "Water", "polarity": "Yin",  "hanja": "癸", "korean": "계"},
}


# ── Element + polarity per branch ───────────────────────────────────────────
# From knowledge/02-branches.md and 04-yin-yang.md
BRANCH_INFO: Dict[str, Dict[str, str]] = {
    "子": {"element": "Water", "polarity": "Yang", "animal": "Rat",    "korean": "자", "hanja": "子", "month": 11, "hour": "23-01"},
    "丑": {"element": "Earth", "polarity": "Yin",  "animal": "Ox",     "korean": "축", "hanja": "丑", "month": 12, "hour": "01-03"},
    "寅": {"element": "Wood",  "polarity": "Yang", "animal": "Tiger",  "korean": "인", "hanja": "寅", "month":  1, "hour": "03-05"},
    "卯": {"element": "Wood",  "polarity": "Yin",  "animal": "Rabbit", "korean": "묘", "hanja": "卯", "month":  2, "hour": "05-07"},
    "辰": {"element": "Earth", "polarity": "Yang", "animal": "Dragon", "korean": "진", "hanja": "辰", "month":  3, "hour": "07-09"},
    "巳": {"element": "Fire",  "polarity": "Yin",  "animal": "Snake",  "korean": "사", "hanja": "巳", "month":  4, "hour": "09-11"},
    "午": {"element": "Fire",  "polarity": "Yang", "animal": "Horse",  "korean": "오", "hanja": "午", "month":  5, "hour": "11-13"},
    "未": {"element": "Earth", "polarity": "Yin",  "animal": "Goat",   "korean": "미", "hanja": "未", "month":  6, "hour": "13-15"},
    "申": {"element": "Metal", "polarity": "Yang", "animal": "Monkey", "korean": "신", "hanja": "申", "month":  7, "hour": "15-17"},
    "酉": {"element": "Metal", "polarity": "Yin",  "animal": "Rooster","korean": "유", "hanja": "酉", "month":  8, "hour": "17-19"},
    "戌": {"element": "Earth", "polarity": "Yang", "animal": "Dog",    "korean": "술", "hanja": "戌", "month":  9, "hour": "19-21"},
    "亥": {"element": "Water", "polarity": "Yin",  "animal": "Pig",    "korean": "해", "hanja": "亥", "month": 10, "hour": "21-23"},
}

# Branch → 순서 (0-indexed in the 12-cycle). Used for major-luck stepping.
BRANCH_ORDER: List[str] = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_INDEX: Dict[str, int] = {b: i for i, b in enumerate(BRANCH_ORDER)}

# Same idea for stems (10-cycle).
STEM_ORDER: List[str] = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEM_INDEX: Dict[str, int] = {s: i for i, s in enumerate(STEM_ORDER)}


# ── 60-cycle (육십갑자) math ─────────────────────────────────────────────────
# The 60-cycle is a fixed pairing of stems (10) and branches (12) whose
# lcm is 60. The cycle starts at 甲子 = (0, 0) and proceeds in stem+1,
# branch+1 steps. saju_calculators + classical tables agree on this ordering.
#
# Verifying against sajupy: 1900-01-01 day pillar = 甲戌 → index 10 in cycle.
# Index 10 = 甲子(0), 乙丑(1), 丙寅(2), 丁卯(3), 戊辰(4), 己巳(5), 庚午(6),
#            辛未(7), 壬申(8), 癸酉(9), 甲戌(10). ✓

JIAZI_CYCLE: List[Tuple[str, str]] = [
    (s, b)
    for i in range(60)
    for s, b in [(STEM_ORDER[i % 10], BRANCH_ORDER[i % 12])]
    if True
][:60]

# Sanity checks for JIAZI_CYCLE live in tests/test_lookup.py, not here as
# module-level asserts (moved 2026-09-20, external code-quality review: a
# module-level `assert` is stripped entirely under `python -O`, silently
# disabling the check, and re-runs this cheap-but-pointless work on every
# import instead of once in the test suite).


def cycle_index(stem: str, branch: str) -> int:
    """Return the position (0–59) of (stem, branch) in the 60-cycle."""
    s_idx = STEM_INDEX[stem]
    b_idx = BRANCH_INDEX[branch]
    if s_idx % 2 != b_idx % 2:
        raise ValueError(f"{stem}{branch} is not a valid 60-cycle pair (yin/yang mismatch)")
    for i in range(60):
        if i % 10 == s_idx and i % 12 == b_idx:
            return i
    raise ValueError(f"no cycle index for {stem}{branch}")


def step_cycle(stem: str, branch: str, n: int) -> Tuple[str, str]:
    """Return the pillar `n` steps forward (n>0) or backward (n<0) in the 60-cycle."""
    i = cycle_index(stem, branch)
    j = (i + n) % 60
    return JIAZI_CYCLE[j]


# ── 五虎遁 (Oho-dun): first-month (寅月) stem from year stem ─────────────────
# Classical month-stem derivation used for 월운 / monthly-luck calculations.
# Year stem → stem of the first Saju month (寅月). Branches then step 寅卯辰...
_OHO_DUN: Dict[str, str] = {
    "甲": "丙",
    "己": "丙",
    "乙": "戊",
    "庚": "戊",
    "丙": "庚",
    "辛": "庚",
    "丁": "壬",
    "壬": "壬",
    "戊": "甲",
    "癸": "甲",
}


# ── 天干合 (Ten Stem Combinations / 천간합) ──────────────────────────────────
# From knowledge/07-special-formations.md — 화격 conditions.
# Pair is unordered; combined element is the transformation element.
TEN_STEM_COMBINATIONS: List[Tuple[str, str, str, str]] = [
    # (stem_a, stem_b, combined_element, korean_name)
    ("甲", "己", "Earth", "갑기합토"),
    ("乙", "庚", "Metal", "을경합금"),
    ("丙", "辛", "Water", "병신합수"),
    ("丁", "壬", "Wood", "정임합목"),
    ("戊", "癸", "Fire", "무계합화"),
]

# 天干沖 (Stem Clashes / 천간충) — the four standard 칠충 pairs.
# Source: knowledge/01-stems.md §Stem Clashes (E-7, 2026-09-25 audit).
STEM_CLASHES: List[Tuple[str, str]] = [
    ("甲", "庚"), ("乙", "辛"), ("丙", "壬"), ("丁", "癸"),
]


def stem_clash(a: str, b: str) -> bool:
    """True when the unordered stem pair is one of the four 천간충 pairs."""
    return frozenset([a, b]) in {frozenset(p) for p in STEM_CLASHES}


# Branch element map for transformation-grid season check.
BRANCH_ELEMENT: Dict[str, str] = {
    "寅": "Wood", "卯": "Wood", "辰": "Earth",
    "巳": "Fire", "午": "Fire", "未": "Earth",
    "申": "Metal", "酉": "Metal", "戌": "Earth",
    "亥": "Water", "子": "Water", "丑": "Earth",
}


def stem_combination(a: str, b: str) -> Optional[Tuple[str, str, str]]:
    """Return the ten-stem combination result for an unordered pair, or None.

    Returns (combined_element, korean_name, pair_label).
    """
    pair = frozenset([a, b])
    for sa, sb, elem, ko in TEN_STEM_COMBINATIONS:
        if frozenset([sa, sb]) == pair:
            return elem, ko, f"{a}{b}"
    return None


# ── Hidden stems per branch (지장간) ─────────────────────────────────────────
# From knowledge/02-branches.md
# Each branch lists its Main / Middle / Residual hidden stems.
#
# Fixed 2026-09-25 (external report review, E-2): the four storage/tomb
# branches (辰戌丑未, 四庫) had their 중기 (middle) and 여기 (residual) stems
# swapped. The standard classical table (by day-count through the branch's
# month: 여기 first as a carry-over from the preceding season, then 중기,
# then 본기 as the dominant majority) is:
#   丑 (prior month 子=Water): 癸(여기) 辛(중기) 己(본기)
#   辰 (prior month 卯=Wood):  乙(여기) 癸(중기) 戊(본기)
#   未 (prior month 午=Fire):  丁(여기) 乙(중기) 己(본기)
#   戌 (prior month 酉=Metal): 辛(여기) 丁(중기) 戊(본기)
# This is not cosmetic: strength.py weights middle=0.3 vs residual=0.1
# differently, so the swap changed computed element percentages and
# strength scores for any chart containing one of these four branches —
# confirmed live on Harish's chart (day branch 亥's neighbor 丑 in his hour
# pillar), where correcting this flips which of Water/Metal reads higher.
# The four "growth" branches (寅申巳亥) and the four single/double-stem
# branches (子午卯酉) were already correctly ordered and are unaffected.
HIDDEN_STEMS: Dict[str, Dict[str, str]] = {
    "子": {"main": "癸"},
    "丑": {"main": "己", "middle": "辛", "residual": "癸"},
    "寅": {"main": "甲", "middle": "丙", "residual": "戊"},
    "卯": {"main": "乙"},
    "辰": {"main": "戊", "middle": "癸", "residual": "乙"},
    "巳": {"main": "丙", "middle": "庚", "residual": "戊"},
    "午": {"main": "丁", "middle": "己"},
    "未": {"main": "己", "middle": "乙", "residual": "丁"},
    "申": {"main": "庚", "middle": "壬", "residual": "戊"},
    "酉": {"main": "辛"},
    "戌": {"main": "戊", "middle": "丁", "residual": "辛"},
    "亥": {"main": "壬", "middle": "甲"},
}


# ── 월률분야 (月律分野): day shares of each branch's 30-day month ──────────
# N-12 (2026-09-26 audit; user decision: the traditional method). Element
# weights used to come from fixed role weights (main 0.6 / middle 0.3 /
# residual 0.1) over the HIDDEN_STEMS table above, so a branch's total qi
# depended on how many stems it lists: 子卯酉 = 0.6, 午亥 = 0.9, the rest
# 1.0 — the purest 왕지 underweighted by up to 40%. 월률분야 assigns each
# stem its share of the branch's 30 days (초기 → 중기 → 정기), so every branch
# totals exactly 30 days = 1.0. Table per knowledge/02-branches.md
# §월률분야 (source: 연해자평 / 삼명통회 lineage, as tabulated at
# https://www.sajustudy.com/133). It includes the 초기 stems of the 왕지 and
# of 午/亥 (子 壬, 卯 甲, 酉 庚, 午 丙, 亥 戊) that the simplified HIDDEN_STEMS
# table omits; those count toward element weight only, not toward 투출 or
# the hidden-stem ten-god lists, which keep using HIDDEN_STEMS.
WOLRYUL_BUNYA: Dict[str, List[Tuple[str, int]]] = {
    "子": [("壬", 10), ("癸", 20)],
    "丑": [("癸", 9), ("辛", 3), ("己", 18)],
    "寅": [("戊", 7), ("丙", 7), ("甲", 16)],
    "卯": [("甲", 10), ("乙", 20)],
    "辰": [("乙", 9), ("癸", 3), ("戊", 18)],
    "巳": [("戊", 7), ("庚", 7), ("丙", 16)],
    "午": [("丙", 10), ("己", 9), ("丁", 11)],
    "未": [("丁", 9), ("乙", 3), ("己", 18)],
    "申": [("戊", 7), ("壬", 7), ("庚", 16)],
    "酉": [("庚", 10), ("辛", 20)],
    "戌": [("辛", 9), ("丁", 3), ("戊", 18)],
    "亥": [("戊", 7), ("甲", 7), ("壬", 16)],
}


def branch_qi_elements(branch: str) -> Dict[str, float]:
    """Element weights of `branch`'s qi from its 월률분야 day shares (sums to 1.0)."""
    out: Dict[str, float] = {}
    for stem, days in WOLRYUL_BUNYA[branch]:
        el = STEM_INFO[stem]["element"]
        out[el] = out.get(el, 0.0) + days / 30.0
    return out


# ── Five-elements generating and overcoming cycles ──────────────────────────
# From knowledge/03-five-elements.md
GENERATES: Dict[str, str] = {
    "Wood": "Fire", "Fire": "Earth", "Earth": "Metal",
    "Metal": "Water", "Water": "Wood",
}
OVERCOMES: Dict[str, str] = {
    "Wood": "Earth", "Earth": "Water", "Water": "Fire",
    "Fire": "Metal", "Metal": "Wood",
}


# ── Ten-god derivation ──────────────────────────────────────────────────────
# From knowledge/05-ten-gods.md
# Logic:
#   same-element                → 비겁
#   Day Master generates it     → 식상
#   Day Master controls it      → 재성
#   it controls Day Master      → 관성
#   it generates Day Master     → 인성
# Within a class: same polarity = yang variant (비견/식신/편재/편관/편인),
# different polarity = yin variant (겁재/상관/정재/정관/정인).
def element_relation(day_master_element: str, other_element: str) -> str:
    """Classify the relation of `other_element` to the Day Master's element.

    Returns one of: "self" | "output" | "wealth" | "authority" | "resource"
    """
    if day_master_element == other_element:
        return "self"
    if GENERATES[day_master_element] == other_element:
        return "output"
    if OVERCOMES[day_master_element] == other_element:
        return "wealth"
    if OVERCOMES[other_element] == day_master_element:
        return "authority"
    if GENERATES[other_element] == day_master_element:
        return "resource"
    raise ValueError(f"unrelated elements: {day_master_element}, {other_element}")


_TENGOD_YANG = {
    "self":     "비견",
    "output":   "식신",
    "wealth":   "편재",
    "authority":"편관",
    "resource": "편인",
}
_TENGOD_YIN = {
    "self":     "겁재",
    "output":   "상관",
    "wealth":   "정재",
    "authority":"정관",
    "resource": "정인",
}


def ten_god(day_master: str, other_stem: str) -> str:
    """Return the 십신 name (Korean) of `other_stem` relative to `day_master`.

    Polarity: the *same* polarity as the Day Master → 편 (indirect) relations
    (편재/편관/편인/비견/식신); the *opposite* polarity → 정 (direct) relations
    (정재/정관/정인/겁재/상관). Wealth/authority use the overcoming cycle
    (水 overcomes 火), so a Day Master of Fire sees Water as authority, not wealth.

    Examples: ten_god("丙", "庚") → "편재"  (Fire controls Metal = wealth; both Yang → 편)
              ten_god("丙", "壬") → "편관"  (Water overcomes Fire = authority; both Yang → 편)
    """
    dm = STEM_INFO[day_master]
    other = STEM_INFO[other_stem]
    rel = element_relation(dm["element"], other["element"])
    if dm["polarity"] == other["polarity"]:
        return _TENGOD_YANG[rel]
    return _TENGOD_YIN[rel]


# ── 12운성 per (day master, branch) ──────────────────────────────────────────
# From knowledge/06-twelve-stages.md
STAGES_12 = ["장생","목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양"]

# Each stem: which branch is its 장생 start, and which direction (forward / backward).
# From 06-twelve-stages.md Stage Starting Point by Stem.
_LONG_LIFE_START: Dict[str, Tuple[str, str]] = {
    "甲": ("亥", "forward"),  "乙": ("午", "backward"),
    "丙": ("寅", "forward"),  "丁": ("酉", "backward"),
    "戊": ("寅", "forward"),  "己": ("酉", "backward"),
    "庚": ("巳", "forward"),  "辛": ("子", "backward"),
    "壬": ("申", "forward"),  "癸": ("卯", "backward"),
}


# English 십신 names — paired with the Korean names from `ten_god()`.
# Long-form variant used by `engine.py`, `daeun_overlay.py`, and `chart.py`
# for the `tengod_en` field. Short-form variants live in `prose_fillers.py`
# and `prose_scaffold.py` because their prose output has different needs.
TENGOD_EN: Dict[str, str] = {
    "비견": "Companion (比肩)",
    "겁재": "Robber (劫財)",
    "식신": "Eating God (食神)",
    "상관": "Hurting Officer (傷官)",
    "편재": "Indirect Wealth (偏財)",
    "정재": "Direct Wealth (正財)",
    "편관": "Seven Killings (偏官)",
    "정관": "Direct Officer (正官)",
    "편인": "Indirect Resource (偏印)",
    "정인": "Direct Resource (正印)",
}


def twelve_stage(day_master: str, branch: str) -> str:
    """Return the 12운성 (twelve life stage) of `branch` for the given Day Master.

    Example: twelve_stage("甲", "卯") → "제왕"

    Reference: knowledge/06-twelve-stages.md (Stage Starting Point by Stem table)
    + knowledge/01-stems.md (Day Master Cheat Sheet, 12 Stages Start column).

    Note: the engine derives 12운성 algorithmically from each stem's 장생 start
    branch (see the "Stage Starting Point by Stem" table above), so the per-stem
    tables in this knowledge file and the engine's output are always consistent
    by construction. Cross-checked against validate.py:test_twelve_stage.
    """
    start, direction = _LONG_LIFE_START[day_master]
    start_idx = BRANCH_INDEX[start]
    target_idx = BRANCH_INDEX[branch]
    if direction == "forward":
        offset = (target_idx - start_idx) % 12
    else:
        offset = (start_idx - target_idx) % 12
    return STAGES_12[offset]


# ── Branch relationships (합 / 충 / 형 / 파 / 해) ────────────────────────────
# From knowledge/02-branches.md
SIX_COMBINATIONS: List[Tuple[str, str, str]] = [
    # (branch_a, branch_b, combined_element)
    ("子","丑","Earth"),
    ("寅","亥","Wood"),
    ("卯","戌","Fire"),
    ("辰","酉","Metal"),
    ("巳","申","Water"),
    ("午","未","Earth"),  # classical "오미합 화토" — Fire/Earth alliance
]

SIX_CLASHES: List[Tuple[str, str]] = [
    ("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥"),
]

THREE_HARMONIES: List[Tuple[str, str, str, str]] = [
    # (a, b, c, element)
    ("申","子","辰","Water"),
    ("亥","卯","未","Wood"),
    ("寅","午","戌","Fire"),
    ("巳","酉","丑","Metal"),
]

# Directional harmonies (방합, 方合) — three consecutive branches of a cardinal direction.
# Source: knowledge/02-branches.md §Directional Harmonies.
DIRECTIONAL_HARMONIES: List[Tuple[str, str, str, str]] = [
    # (a, b, c, element / direction)
    ("寅","卯","辰","Wood / East"),
    ("巳","午","未","Fire / South"),
    ("申","酉","戌","Metal / West"),
    ("亥","子","丑","Water / North"),
]

SELF_PUNISHMENTS: List[str] = ["辰","午","酉","亥"]

SIX_HARMS: List[Tuple[str, str]] = [
    ("子","未"),("丑","午"),("寅","巳"),("卯","辰"),("申","亥"),("酉","戌"),
]
SIX_BREAKS: List[Tuple[str, str]] = [
    ("子","酉"),("午","卯"),("辰","丑"),("未","戌"),("申","巳"),("寅","亥"),
]

# Three-punishment groups (삼형, 三刑)
# From knowledge/07-special-formations.md
THREE_PUNISHMENTS: List[Tuple[str, str, str, str]] = [
    ("寅","巳","申","Wood-Metal-Fire punishment"),
    ("丑","戌","未","Earth triad punishment"),
    ("子","卯","—","Water-Wood punishment (lacks a third member in natal 4 branches)"),
]
# 子卯 is a two-member punishment; we detect it as a special case in the engine.


# ── Major-luck direction table ──────────────────────────────────────────────
# From knowledge/08-luck-pillars.md (Part 1)
# Yang year + Male  → forward
# Yang year + Female → backward
# Yin year  + Male  → backward
# Yin year  + Female → forward
def daeun_direction(year_stem: str, gender: str) -> str:
    """Return 'forward' or 'backward' for the major-luck sequence.

    Raises ValueError if ``gender`` is not ``"M"`` or ``"F"``.
    """
    if gender not in ("M", "F"):
        raise ValueError(f"gender must be 'M' or 'F', got {gender!r}")
    yp = STEM_INFO[year_stem]["polarity"]
    is_yang = (yp == "Yang")
    is_male = (gender == "M")
    same_sign = is_yang == is_male
    return "forward" if same_sign else "backward"
