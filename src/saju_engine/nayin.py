"""납음오행 (Nayin / 納音五行) — the 60-jiazi Nayin classification.

Each of the 60 Heavenly-Stem + Earthly-Branch pairs is assigned a fixed Nayin
element (海中金, 爐中火, etc.). The 60 pairs group into **30 Nayin categories**
— each Nayin covers 2 consecutive jiazi. Classical Korean 명리 (especially the
서전구미록 commentary, 권인성·곽임성·정봉재·송기영 schools) uses Nayin in 궁합
as a **soft "deep-tone" indicator**, not a primary factor.

Reference: knowledge/11-gunghap.md §C.

Six-relationship table (서전구미록 commentary, cited in modern Korean Myeongri):
  상합 (相合)  +3   mutually harmonious
  상충 (相沖)  −5   mutually clashing
  상형 (相刑)  −4   mutually punishing
  상해 (相害)  −3   mutually harming
  상구 (相求)  +2   mutually seeking (one reinforces the other)
  상대 (相代)  +1   mutually substituting (similar tones)
  default      0   neutral
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# ── 30 Nayin categories, 60 jiazi ────────────────────────────────────────────
# Each (stem, branch) → Nayin name. Two jiazi share one Nayin.
# Source: knowledge/11-gunghap.md §C, table of 30 nayin pairs.
JIAZI_TO_NAYIN: Dict[Tuple[str, str], str] = {
    # 海中金 (Gold in the Sea) — Metal
    ("甲", "子"): "海中金", ("乙", "丑"): "海中金",
    # 爐中火 (Fire in the Furnace) — Fire
    ("丙", "寅"): "爐中火", ("丁", "卯"): "爐中火",
    # 大林木 (Forest Wood) — Wood
    ("戊", "辰"): "大林木", ("己", "巳"): "大林木",
    # 路傍土 (Roadside Earth) — Earth
    ("庚", "午"): "路傍土", ("辛", "未"): "路傍土",
    # 劍鋒金 (Sword-Edge Metal) — Metal
    ("壬", "申"): "劍鋒金", ("癸", "酉"): "劍鋒金",
    # 山頭火 (Mountain-Top Fire) — Fire
    ("甲", "戌"): "山頭火", ("乙", "亥"): "山頭火",
    # 澗下水 (Water Under the Stream) — Water
    ("丙", "子"): "澗下水", ("丁", "丑"): "澗下水",
    # 城頭土 (City-Wall Earth) — Earth
    ("戊", "寅"): "城頭土", ("己", "卯"): "城頭土",
    # 白蠟金 (White Wax Metal) — Metal
    ("庚", "辰"): "白蠟金", ("辛", "巳"): "白蠟金",
    # 楊柳木 (Willow Wood) — Wood
    ("壬", "午"): "楊柳木", ("癸", "未"): "楊柳木",
    # 泉中水 (Spring Water) — Water
    ("甲", "申"): "泉中水", ("乙", "酉"): "泉中水",
    # 屋上土 (Rooftop Earth) — Earth
    ("丙", "戌"): "屋上土", ("丁", "亥"): "屋上土",
    # 霹靂火 (Thunder Fire) — Fire
    ("戊", "子"): "霹靂火", ("己", "丑"): "霹靂火",
    # 松柏木 (Pine-Cypress Wood) — Wood
    ("庚", "寅"): "松柏木", ("辛", "卯"): "松柏木",
    # 長流水 (Long-Flowing Water) — Water
    ("壬", "辰"): "長流水", ("癸", "巳"): "長流水",
    # 沙中金 (Sand Gold) — Metal
    ("甲", "午"): "沙中金", ("乙", "未"): "沙中金",
    # 山下火 (Mountain-Foot Fire) — Fire
    ("丙", "申"): "山下火", ("丁", "酉"): "山下火",
    # 平地木 (Flatland Wood) — Wood
    ("戊", "戌"): "平地木", ("己", "亥"): "平地木",
    # 壁上土 (Wall Earth) — Earth
    ("庚", "子"): "壁上土", ("辛", "丑"): "壁上土",
    # 金箔金 (Gold-Leaf Metal) — Metal
    ("壬", "寅"): "金箔金", ("癸", "卯"): "金箔金",
    # 覆燈火 (Lamp Fire) — Fire
    ("甲", "辰"): "覆燈火", ("乙", "巳"): "覆燈火",
    # 天河水 (Milky-Way Water) — Water
    ("丙", "午"): "天河水", ("丁", "未"): "天河水",
    # 大驛土 (Post-Horse Earth) — Earth
    ("戊", "申"): "大驛土", ("己", "酉"): "大驛土",
    # 釵釧金 (Hairpin-Bracket Metal) — Metal
    ("庚", "戌"): "釵釧金", ("辛", "亥"): "釵釧金",
    # 桑柘木 (Mulberry Wood) — Wood
    ("壬", "子"): "桑柘木", ("癸", "丑"): "桑柘木",
    # 大溪水 (Great Stream Water) — Water
    ("甲", "寅"): "大溪水", ("乙", "卯"): "大溪水",
    # 沙中土 (Sand Earth) — Earth
    ("丙", "辰"): "沙中土", ("丁", "巳"): "沙中土",
    # 天上火 (Heavenly Fire) — Fire
    ("戊", "午"): "天上火", ("己", "未"): "天上火",
    # 石榴木 (Pomegranate Wood) — Wood
    ("庚", "申"): "石榴木", ("辛", "酉"): "石榴木",
    # 大海水 (Great Sea Water) — Water
    ("壬", "戌"): "大海水", ("癸", "亥"): "大海水",
}

# Nayin → element. Korean Myeongri (modern) sometimes treats Nayin as the
# "deep tone" of the chart independent of the Day Master's primary element.
NAYIN_ELEMENT: Dict[str, str] = {
    "海中金": "Metal", "爐中火": "Fire", "大林木": "Wood",
    "路傍土": "Earth", "劍鋒金": "Metal", "山頭火": "Fire",
    "澗下水": "Water", "城頭土": "Earth", "白蠟金": "Metal",
    "楊柳木": "Wood", "泉中水": "Water", "屋上土": "Earth",
    "霹靂火": "Fire", "松柏木": "Wood", "長流水": "Water",
    "沙中金": "Metal", "山下火": "Fire", "平地木": "Wood",
    "壁上土": "Earth", "金箔金": "Metal", "覆燈火": "Fire",
    "天河水": "Water", "大驛土": "Earth", "釵釧金": "Metal",
    "桑柘木": "Wood", "大溪水": "Water", "沙中土": "Earth",
    "天上火": "Fire", "石榴木": "Wood", "大海水": "Water",
}

# Canonical 30 Nayin names in the standard display order (1–30).
NAYIN_ORDER: List[str] = [
    "海中金", "爐中火", "大林木", "路傍土", "劍鋒金", "山頭火",
    "澗下水", "城頭土", "白蠟金", "楊柳木", "泉中水", "屋上土",
    "霹靂火", "松柏木", "長流水", "沙中金", "山下火", "平地木",
    "壁上土", "金箔金", "覆燈火", "天河水", "大驛土", "釵釧金",
    "桑柘木", "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]

# Korean display name for each Nayin.
NAYIN_KOREAN: Dict[str, str] = {
    "海中金": "해중금 (Gold in the Sea)",
    "爐中火": "노중화 (Fire in the Furnace)",
    "大林木": "대림목 (Forest Wood)",
    "路傍土": "노방토 (Roadside Earth)",
    "劍鋒金": "검봉금 (Sword-Edge Metal)",
    "山頭火": "산두화 (Mountain-Top Fire)",
    "澗下水": "간하수 (Water Under the Stream)",
    "城頭土": "성두토 (City-Wall Earth)",
    "白蠟金": "백랍금 (White Wax Metal)",
    "楊柳木": "양류목 (Willow Wood)",
    "泉中水": "천중수 (Spring Water)",
    "屋上土": "옥상토 (Rooftop Earth)",
    "霹靂火": "벽력화 (Thunder Fire)",
    "松柏木": "송백목 (Pine-Cypress Wood)",
    "長流水": "장류수 (Long-Flowing Water)",
    "沙中金": "사중금 (Sand Gold)",
    "山下火": "산하화 (Mountain-Foot Fire)",
    "平地木": "평지목 (Flatland Wood)",
    "壁上土": "벽상토 (Wall Earth)",
    "金箔金": "금박금 (Gold-Leaf Metal)",
    "覆燈火": "복등화 (Lamp Fire)",
    "天河水": "천하수 (Milky-Way Water)",
    "大驛土": "대역토 (Post-Horse Earth)",
    "釵釧金": "채천금 (Hairpin-Bracket Metal)",
    "桑柘木": "상저목 (Mulberry Wood)",
    "大溪水": "대계수 (Great Stream Water)",
    "沙中土": "사중토 (Sand Earth)",
    "天上火": "천상화 (Heavenly Fire)",
    "石榴木": "석류목 (Pomegranate Wood)",
    "大海水": "대해수 (Great Sea Water)",
}


def nayin_of(stem: str, branch: str) -> Optional[str]:
    """Return the Nayin name for a (stem, branch) jiazi pair, or None."""
    return JIAZI_TO_NAYIN.get((stem, branch))


def nayin_element_of(nayin_name: str) -> Optional[str]:
    """Return the element of a Nayin name, or None."""
    return NAYIN_ELEMENT.get(nayin_name)


# ── Element-grammar helper for the 30 × 30 relation table ─────────────────────
# The classical Korean table pairs each Nayin with one of six relationship types
# toward every other Nayin. The six-relationship grammar reduced to 5 elements
# (documented in knowledge/11-gunghap.md §C) is:
#
#   같은 element        → 상대 (相代)  +1   "similar tone"
#   GENERATES (생)      → 상합 (相合)  +3   "mutually harmonious"
#   OVERCOMES (극)      → 상충 (相沖)  −5   "mutually clashing"
#   reversed OVERCOMES  → 상해 (相害)  −3   "mutually harming" (subtle friction)
#   reversed GENERATES  → 상구 (相求)  +2   "mutually seeking"
#
# This grammar seeds the 30×30 table below. Per Ground Rule 1, pair-specific
# values from the original 서전구미록 text must be sourced and cited before
# replacing the fallback entries.
_ELEMENT_TO_NAYINS: Dict[str, List[str]] = {}
for _n, _e in NAYIN_ELEMENT.items():
    _ELEMENT_TO_NAYINS.setdefault(_e, []).append(_n)


def _element_relation(elem_a: str, elem_b: str) -> Tuple[str, int]:
    """Return (relation_label, weight_delta) for a pair of Nayin elements.

    Returns the canonical six-relationship grammar reduced to 5 elements.
    """
    if elem_a == elem_b:
        return "상대", 1
    # GENERATES = A generates B
    from . import lookup as L  # local import to avoid circular
    if L.GENERATES.get(elem_a) == elem_b:
        return "상합", 3
    if L.GENERATES.get(elem_b) == elem_a:
        return "상구", 2
    if L.OVERCOMES.get(elem_a) == elem_b:
        return "상충", -5
    if L.OVERCOMES.get(elem_b) == elem_a:
        return "상해", -3
    return "neutral", 0


# ── 30 × 30 pair-specific relation table (서전구미록) ─────────────────────────
# The full classical 서전구미록 commentary assigns a relationship type to every
# ordered pair of the 30 Nayin categories. The complete table is 30 × 30 = 900
# cells. Ground Rule 1 forbids inventing pair-specific values, so the table is
# seeded with the documented 5-element grammar above as a deterministic fallback.
# Each cell carries a source tag: "element-grammar-fallback" until replaced by a
# published pair-specific value with citation.
#
# Source tagging lets the compatibility report be honest about whether a given
# Nayin verdict comes from the generic element reduction or from a sourced text.


NAYIN_PAIR_TABLE: Dict[Tuple[str, str], Tuple[str, int]] = {}
NAYIN_PAIR_SOURCE: Dict[Tuple[str, str], str] = {}

for _a in NAYIN_ORDER:
    for _b in NAYIN_ORDER:
        _key = (_a, _b)
        _elem_a = NAYIN_ELEMENT.get(_a)
        _elem_b = NAYIN_ELEMENT.get(_b)
        if not _elem_a or not _elem_b:
            NAYIN_PAIR_TABLE[_key] = ("neutral", 0)
        else:
            NAYIN_PAIR_TABLE[_key] = _element_relation(_elem_a, _elem_b)
        NAYIN_PAIR_SOURCE[_key] = "element-grammar-fallback"


def nayin_relation_detail(
    nayin_a: str, nayin_b: str
) -> Tuple[str, int, str]:
    """Return (relation_label, weight_delta, source_tag) for a Nayin pair.

    Looks up the 30×30 pair table first, then falls back to element grammar
    for any unknown Nayin names. The source tag is "element-grammar-fallback"
    until pair-specific sourced values are added to NAYIN_PAIR_TABLE.
    """
    if not nayin_a or not nayin_b:
        return "neutral", 0, "element-grammar-fallback"

    key = (nayin_a, nayin_b)
    if key in NAYIN_PAIR_TABLE:
        rel, delta = NAYIN_PAIR_TABLE[key]
        return rel, delta, NAYIN_PAIR_SOURCE.get(key, "element-grammar-fallback")

    # Unknown Nayin names → generic element grammar (defensive fallback).
    elem_a = NAYIN_ELEMENT.get(nayin_a)
    elem_b = NAYIN_ELEMENT.get(nayin_b)
    if not elem_a or not elem_b:
        return "neutral", 0, "element-grammar-fallback"
    rel, delta = _element_relation(elem_a, elem_b)
    return rel, delta, "element-grammar-fallback"


def nayin_relation(nayin_a: str, nayin_b: str) -> Tuple[str, int]:
    """Return (relation_label, weight_delta) per 서전구미록 six-relationship table.

    Same Nayin (e.g. two 海中金) → 상대 (相代) "similar tone", +1.
    Different Nayin → looked up from the 30×30 table (currently populated from
    the documented 5-element fallback).

    Backward-compatible wrapper around nayin_relation_detail().
    """
    rel, delta, _ = nayin_relation_detail(nayin_a, nayin_b)
    return rel, delta
