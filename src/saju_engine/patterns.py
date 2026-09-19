"""Classical pattern / grid (격국) detection for the Saju engine.

This module detects candidate structural patterns from knowledge/07-special-formations.md.
It does NOT make interpretive rulings; it only flags candidates and supplies evidence so
that the human/AI interpreter can decide.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import lookup as L
from .strength import _element_counts


@dataclass
class GridCandidate:
    name_ko: str          # e.g. "식신격"
    name_en: str          # e.g. "Eating God Grid"
    basis: str            # brief evidence string
    confidence: str       # "likely" | "possible" | "ruled-out"
    note: str = ""


# 월지 hidden-stem priority order for 격국 determination (본기 → 중기 → 여기).
# Source: knowledge/07-special-formations.md §Part 1 (classical 투출 method).
_MONTH_HIDDEN_PRIORITY = ["main", "middle", "residual"]


def _grid_stem_by_tuochul(month_branch: str, stems: List[str]) -> Tuple[str, str]:
    """Return (grid_stem, basis) for the regular-grid 결정 stem.

    Classical 투출 (透出) method (자평진전/연해자평/명리정종):
      - Scan the 월지 hidden stems in 본기 → 중기 → 여기 order.
      - The first hidden stem that transparently appears on any pillar's 천간
        (the visible `stems` list) is the 격국 stem (투출).
      - If several 투출, 본기 wins (enforced by the scan order).
      - If none 투출, fall back to the 월지 본기 hidden stem.
    """
    hidden = L.HIDDEN_STEMS.get(month_branch, {})
    visible = set(stems)
    for role in _MONTH_HIDDEN_PRIORITY:
        h_stem = hidden.get(role)
        if h_stem and h_stem in visible:
            return h_stem, (
                f"month branch {month_branch} {role} hidden stem {h_stem} "
                f"투출 (transparently appears on a 천간)"
            )
    # No 투출 — fall back to 본기.
    fallback = hidden.get("main")
    if not fallback:
        raise KeyError(f"no hidden stems recorded for month branch {month_branch}")
    return fallback, (
        f"month branch {month_branch} 본기 hidden stem {fallback} "
        f"(no hidden stem 투출; 본기 fallback per classical rule)"
    )


# Regular grid mapping: month stem ten-god → grid name.
_REGULAR_GRID: Dict[str, Tuple[str, str]] = {
    "비견": ("비견격", "Companion Grid"),
    "겁재": ("겁재격", "Robber Grid"),
    "식신": ("식신격", "Eating God Grid"),
    "상관": ("상관격", "Hurting Officer Grid"),
    "편재": ("편재격", "Indirect Wealth Grid"),
    "정재": ("정재격", "Direct Wealth Grid"),
    "편관": ("편관격", "Seven Killings Grid"),
    "정관": ("정관격", "Direct Officer Grid"),
    "편인": ("편인격", "Indirect Resource Grid"),
    "정인": ("정인격", "Direct Resource Grid"),
}


# 양인 (blade of the sheep) mapping: day master → blade branch.
_BLADE_BRANCH: Dict[str, str] = {
    "甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子",
}

# 건록 (self-sufficiency) mapping: day master → 建祿 branch.
_JIANLU_BRANCH: Dict[str, str] = {
    "甲": "寅", "丙": "巳", "戊": "巳", "庚": "申", "壬": "亥",
}


# Breaking stems that can disturb a ten-stem combination.
# Each entry maps a combination pair label to the list of stems that classical
# texts regard as disruptive (competing or clashing with the combining stems).
_COMBO_BREAKERS: Dict[str, List[str]] = {
    "甲己": ["乙", "庚"],
    "乙庚": ["甲", "辛"],
    "丙辛": ["丁", "壬"],
    "丁壬": ["丙", "癸"],
    "戊癸": ["己", "甲"],
}


def _breaker_is_powerful(
    breaker: str,
    month_branch: str,
    branches: Optional[List[str]] = None,
    hidden_stems: Optional[List[Tuple[str, str]]] = None,
) -> bool:
    """Return True if a breaker stem is rooted or in season.

    Per knowledge/07-special-formations.md: a breaker is effective only when it
    is rooted in a natal branch (visible or hidden) or its element matches the
    month-branch element.
    """
    # In season: breaker element matches the month branch element.
    breaker_elem = L.STEM_INFO.get(breaker, {}).get("element", "")
    if breaker_elem and breaker_elem == L.BRANCH_ELEMENT.get(month_branch, ""):
        return True
    # Rooted: breaker appears as a visible branch or as any hidden stem.
    if branches and breaker in branches:
        return True
    if hidden_stems and any(stem == breaker for _, stem in hidden_stems):
        return True
    return False


def detect_stem_combinations(
    stems: List[str],
    month_branch: str,
    branches: Optional[List[str]] = None,
    hidden_stems: Optional[List[Tuple[str, str]]] = None,
) -> List[Dict[str, str]]:
    """Return all ten-stem combination candidates among the four stems.

    Each result includes the combined element, Korean name, the two stems,
    whether the combined element is in season at the month branch, and whether
    a powerful breaking stem is present.
    """
    results: List[Dict[str, str]] = []
    n = len(stems)
    for i in range(n):
        for j in range(i + 1, n):
            combo = L.stem_combination(stems[i], stems[j])
            if combo is None:
                continue
            elem, ko_name, pair_label = combo
            month_elem = L.BRANCH_ELEMENT.get(month_branch, "")
            in_season = month_elem == elem
            # `pair_label` is in pillar-position order (f"{a}{b}"), but
            # _COMBO_BREAKERS keys are canonical (lower STEM_INDEX first).
            # Canonicalize so the breaker check is order-independent —
            # otherwise ~half of charts (stems in the opposite order) miss
            # the breaker and wrongly flag a 화격 candidate as "likely".
            canonical_label = "".join(
                sorted([stems[i], stems[j]], key=lambda s: L.STEM_INDEX[s])
            )
            breaker_present = any(
                _breaker_is_powerful(b, month_branch, branches, hidden_stems)
                for b in _COMBO_BREAKERS.get(canonical_label, [])
                if b in stems
            )
            results.append({
                "stem_a": stems[i],
                "stem_b": stems[j],
                "combined_element": elem,
                "korean_name": ko_name,
                "in_season": in_season,
                "breaker_present": breaker_present,
                "confidence": "likely" if in_season and not breaker_present else "possible",
                "note": f"{ko_name}; month branch {month_branch} is {month_elem}",
            })
    return results


def detect_transformation_grid(
    day_master: str,
    stems: List[str],
    month_branch: str,
    month_stem: str = "",
    strength_verdict: str = "",
    branches: Optional[List[str]] = None,
    hidden_stems: Optional[List[Tuple[str, str]]] = None,
) -> Optional[Dict[str, str]]:
    """Detect 화격 (transformation grid) candidates.

    Conditions from knowledge/07-special-formations.md:
      - the **month stem** is a 합 partner of either the Day Master or the
        year stem (i.e. the month stem must be one of the two combining stems).
      - combined element is in season at the month branch.
      - Day Master is isolated (no strong support) — classical doctrine
        requires a **weak** Day Master; we enforce that when `strength_verdict`
        is supplied.
      - no breaking stem present.

    Returns the first classical candidate found, or None.
    """
    # B7: 화격 requires DM isolation. If a strength verdict is supplied, only
    # a weak or extremely weak Day Master can form a true 화격.
    if strength_verdict and strength_verdict not in {"weak", "extreme_weak"}:
        return None

    # Candidate anchors: Day Master and year stem (first stem in the list).
    anchors = {day_master}
    if stems:
        anchors.add(stems[0])

    for combo in detect_stem_combinations(
        stems, month_branch, branches=branches, hidden_stems=hidden_stems
    ):
        combo_stems = {combo["stem_a"], combo["stem_b"]}
        # The month stem must be one of the combining partners (knowledge/07
        # requires it), and the other partner must be an anchor (DM or year).
        if month_stem and month_stem not in combo_stems:
            continue
        other = next((s for s in combo_stems if s != month_stem), None) if month_stem else None
        if month_stem and other not in anchors:
            continue
        # Fallback (no month_stem passed): keep the legacy anchor-only check.
        if not month_stem and combo["stem_a"] not in anchors and combo["stem_b"] not in anchors:
            continue
        if not combo["in_season"]:
            continue
        if combo["breaker_present"]:
            continue
        return {
            "name_ko": "화격",
            "name_en": "Transformation Grid",
            "basis": f"{combo['stem_a']}{combo['stem_b']} combine into {combo['combined_element']}",
            "combined_element": combo["combined_element"],
            "confidence": "possible",
            "note": (
                f"Candidate {combo['korean_name']} with month branch {month_branch} "
                f"({L.BRANCH_ELEMENT.get(month_branch)}); Day Master is flagged weak, "
                f"so isolation is satisfied per knowledge/07-special-formations.md. "
                f"Still verify that no breaking month stem appears."
            ),
        }
    return None


def _has_rooting(
    day_master: str,
    branches: List[str],
    hidden_stems: List[Tuple[str, str]],
) -> bool:
    """Return True if the Day Master has classical 통근 (rooting) support.

    Rooting means the Day Master's own element (비견/겁재 root) or its resource
    element (인성 root) appears in a visible branch or in any hidden stem.
    A rooted Day Master cannot form a true 종격 (從格) because it still has
    allies (see knowledge/07-special-formations.md).
    """
    dm_element = L.STEM_INFO[day_master]["element"]
    resource_element = next(k for k, v in L.GENERATES.items() if v == dm_element)
    rooted_elements = {dm_element, resource_element}

    for branch in branches:
        if L.BRANCH_ELEMENT.get(branch) in rooted_elements:
            return True
    for role, stem in hidden_stems:
        if L.STEM_INFO.get(stem, {}).get("element") in rooted_elements:
            return True
    return False


def detect_special_forms(
    day_master: str,
    stems: List[str],
    branches: List[str],
    hidden_stems: List[Tuple[str, str]],
    element_counts: Counter,
    strength_verdict: str,
    month_branch: str = "",
) -> List[Dict[str, str]]:
    """Detect 종격 (follower-grid) candidates for extremely weak charts.

    Classical preconditions (knowledge/07 §B1; 적천수/명리정종):
      1. **신약 (weak DM)** — 종격 requires the Day Master to be too weak to
         stand. A `balanced` verdict does NOT qualify; it only surfaces a
         borderline candidate at a stricter ≥60% dominant share, downgraded to
         'possible' for reader review (not auto-flagged as a true 종격).
      2. **득령 (in season)** — the dominant element must be supported by the
         월지 season: dominant == the month branch's element, or generated by it.
         If not 득령, the candidate is downgraded to 'possible' (a 60% Earth mass
         in a Wood month is not a true 종재).
      3. **No rooting (통근)** — the Day Master has no 비겁/인성 ally in the
         branches or hidden stems. If rooting is present, downgrade to 'possible'.
      4. **Dominant share ≥ 50%** (≥ 60% for borderline-balanced surfacing).

    All candidates are flags for the reader; the engine does not rule.
    """
    forms: List[Dict[str, str]] = []
    # D3 fix: true 종격 requires extreme weakness. Weak charts may produce a
    # 'possible' flag; balanced charts no longer qualify at all.
    if strength_verdict == "extreme_weak":
        max_confidence = "likely"
        min_share = 0.5
    elif strength_verdict == "weak":
        max_confidence = "possible"
        min_share = 0.5
    else:
        return forms

    total = sum(element_counts.values())
    if total == 0:
        return forms

    dm_element = L.STEM_INFO[day_master]["element"]
    dominant, dominant_count = element_counts.most_common(1)[0]
    share = dominant_count / total
    if share < min_share:
        return forms

    # B4a: 득령 (in season) — dominant must be the month-branch element or
    # generated by it. If not in season, downgrade to 'possible'.
    in_season = False
    if month_branch:
        month_elem = L.BRANCH_ELEMENT.get(month_branch)
        if month_elem:
            in_season = (
                dominant == month_elem
                or L.GENERATES.get(month_elem) == dominant
            )

    # Subtype mapping: which element is overwhelming.
    # Day Master controls → wealth (재); controls Day Master → authority (관);
    # produced by Day Master → output (식상); nurtures Day Master → resource (인).
    element_generates = {
        "Wood": "Fire",
        "Fire": "Earth",
        "Earth": "Metal",
        "Metal": "Water",
        "Water": "Wood",
    }
    element_controls = {
        "Wood": "Earth",
        "Earth": "Water",
        "Water": "Fire",
        "Fire": "Metal",
        "Metal": "Wood",
    }
    controlled_by_dm = element_controls.get(dm_element)
    controls_dm = next(k for k, v in element_controls.items() if v == dm_element)
    produced_by_dm = element_generates.get(dm_element)
    nurtures_dm = next(k for k, v in element_generates.items() if v == dm_element)

    subtype = None
    if dominant == controlled_by_dm:
        subtype = ("종재", "Wealth-Following Grid")
    elif dominant == controls_dm:
        subtype = ("종관", "Authority-Following Grid")
    elif dominant == produced_by_dm:
        subtype = ("종식상", "Output-Following Grid")
    elif dominant == nurtures_dm:
        subtype = ("종인", "Resource-Following Grid")

    if subtype:
        ko, en = subtype
        rooted = _has_rooting(day_master, branches, hidden_stems)
        # Confidence: start from the maximum allowed by strength verdict, then
        # downgrade for any failed precondition.
        confidence = max_confidence
        notes = []
        if rooted:
            confidence = "possible"
            notes.append(
                "Day Master has rooting support (통근) in a branch or hidden stem; "
                "true 종격 requires no 비겁/인성 allies."
            )
        if month_branch and not in_season:
            confidence = "possible"
            notes.append(
                f"dominant {dominant} is not 득령 (in season) at month branch "
                f"{month_branch} ({L.BRANCH_ELEMENT.get(month_branch, '?')} season); "
                "a true 종격 requires the dominant element to be in season."
            )
        if notes:
            note = (
                f"Candidate {ko} ({en}) downgraded: " + " | ".join(notes)
                + " Mark as [UNCERTAIN] until verified."
            )
        else:
            note = (
                f"Candidate {ko} ({en}). No rooting (통근), dominant {dominant} is "
                f"득령 at month branch {month_branch}, and the DM is 신약 — a true "
                f"종격 is plausible. Still verify hidden-stem allies."
            )
        entry = {
            "name_ko": ko,
            "name_en": en,
            "basis": f"{dominant} dominates {share:.0%} of weighted elements; strength verdict is {strength_verdict}",
            "confidence": confidence,
            "note": note,
        }
        forms.append(entry)
        # B6: 종자 (從子) is the rare child/output subtype, often folded into
        # 종식상 by modern schools. Surface it as a separate alias when the
        # dominant element is produced by the Day Master.
        if ko == "종식상":
            forms.append({
                "name_ko": "종자",
                "name_en": "Child-Following Grid",
                "basis": entry["basis"],
                "confidence": confidence,
                "note": (
                    "Same structural basis as 종식상, read through the "
                    "'child / output' lens per knowledge/07-special-formations.md §B1. "
                    "Some schools list this as 종자; others fold it into 종식상."
                ),
            })
    return forms


def detect_structural_notes(
    branches: List[str],
) -> List[Dict[str, str]]:
    """Detect 전국 / 편국 / 삼합국 structural formations.

    These are not grids (격국) but descriptive structural patterns recognized
    in classical 명리: all four branches dominated by one element, three-of-four
    dominated by one element, or all four branches confined within a single
    삼합 frame (one branch repeated).
    """
    notes: List[Dict[str, str]] = []
    branch_elements = [L.BRANCH_ELEMENT[b] for b in branches]
    elem_counts = Counter(branch_elements)

    if len(elem_counts) == 1:
        elem = list(elem_counts.keys())[0]
        notes.append({
            "name_ko": "전국",
            "name_en": "Exclusive Nation",
            "basis": f"All four branches are {elem} ({''.join(branches)})",
            "confidence": "likely",
            "note": "The chart's substance is overwhelmingly one element; temperament and events tend to be saturated by that element.",
        })
    else:
        for elem, cnt in elem_counts.items():
            if cnt == 3:
                notes.append({
                    "name_ko": "편국",
                    "name_en": "Partial Nation",
                    "basis": f"Three of four branches are {elem} ({''.join(branches)})",
                    "confidence": "likely",
                    "note": f"A strong {elem} bias in the earthly foundation; the chart leans heavily in that direction.",
                })

    branches_set = set(branches)
    for a, b, c, elem in L.THREE_HARMONIES:
        frame = {a, b, c}
        if all(br in frame for br in branches):
            notes.append({
                "name_ko": "삼합국",
                "name_en": "Three-Harmony Nation",
                "basis": f"All four branches are inside the {a}{b}{c} {elem} frame ({''.join(branches)})",
                "confidence": "likely",
                "note": f"The chart's substance is wholly gathered in the {elem} 삼합 frame, strongly empowering that element.",
            })

    return notes


def detect_patterns(
    day_master: str,
    month_stem: str,
    month_branch: str,
    branches: List[str],
    stems: List[str],
    hidden_stems: List[Tuple[str, str]],
    strength_verdict: str = "",
) -> Dict[str, any]:
    """Return a structured dictionary of pattern candidates and structural notes.

    Keys:
      - regular_grid: list of GridCandidate for the month-stem grid.
      - yangin: 양인격 evidence.
      - jianlu: 건禄格 evidence.
      - stem_combinations: list of ten-stem combination candidates.
      - transformation_grid: 화격 candidate, or None.
      - special_forms: list of 종격 candidates (conservative thresholds).
      - structural_notes: 전국 / 편국 / 삼합국 detections.
      - dominant_element: element with highest weighted count.
      - element_balance: weighted element counts.
    """
    dm_element = L.STEM_INFO[day_master]["element"]
    # Visible month-stem ten-god (retained in the return dict for reference;
    # NOT used to name the regular grid — see the 투출 method below).
    month_tengod = L.ten_god(day_master, month_stem)

    # Regular grid (정격) — classical 투출 method, see knowledge/07 §Part 1.
    # Determine the 격국 stem from the 월지 hidden stem that 투출 (본기 → 중기 →
    # 여기, first match wins; 본기 fallback), NOT from the visible 월간 alone.
    grid_stem, grid_basis = _grid_stem_by_tuochul(month_branch, stems)
    grid_tengod = L.ten_god(day_master, grid_stem)

    regular_grid: List[GridCandidate] = []
    if grid_tengod in _REGULAR_GRID:
        ko, en = _REGULAR_GRID[grid_tengod]
        regular_grid.append(GridCandidate(
            name_ko=ko, name_en=en,
            basis=f"{grid_basis}; {grid_stem} is {grid_tengod} of Day Master {day_master}",
            confidence="likely",
        ))


    blade = _BLADE_BRANCH.get(day_master)
    yangin_positions_star = []
    yangin_positions_grid = []
    if blade:
        yangin_positions_star = [p for p, b in enumerate(branches) if b == blade]
        # B11: 양인격 (grid) is traditionally read when the blade branch appears
        # in the year, day, or hour pillar; the star-level 양인 may appear anywhere.
        yangin_positions_grid = [
            p for p in yangin_positions_star if p in {0, 2, 3}
        ]

    jianlu = _JIANLU_BRANCH.get(day_master)
    jianlu_positions = []
    if jianlu:
        jianlu_positions = [p for p, b in enumerate(branches) if b == jianlu]

    element_counts = _element_counts(stems, hidden_stems)
    dominant_element = element_counts.most_common(1)[0][0] if element_counts else None

    stem_combos = detect_stem_combinations(
        stems, month_branch, branches=branches, hidden_stems=hidden_stems
    )
    transformation = detect_transformation_grid(
        day_master, stems, month_branch, month_stem,
        strength_verdict=strength_verdict,
        branches=branches, hidden_stems=hidden_stems,
    )
    special = detect_special_forms(
        day_master, stems, branches, hidden_stems, element_counts,
        strength_verdict, month_branch=month_branch,
    )
    structural = detect_structural_notes(branches)

    return {
        "regular_grid": regular_grid,
        "yangin": {
            "day_master": day_master,
            "blade_branch": blade,
            "positions": yangin_positions_star,
            "present": len(yangin_positions_star) > 0,
            "note": "양인 (blade star) appears wherever the blade branch is found; it is an energy overlay, not necessarily a grid.",
        },
        "yangin_grid": {
            "day_master": day_master,
            "blade_branch": blade,
            "positions": yangin_positions_grid,
            "present": len(yangin_positions_grid) > 0,
            "note": "양인격 (blade grid) is read when the blade branch sits in the year, day, or hour pillar per knowledge/07-special-formations.md.",
        },
        "jianlu": {
            "day_master": day_master,
            "jianlu_branch": jianlu,
            "positions": jianlu_positions,
            "present": len(jianlu_positions) > 0,
            "note": "건禄格 indicates natural self-sufficiency and earning capacity." if jianlu_positions else None,
        },
        "stem_combinations": stem_combos,
        "transformation_grid": transformation,
        "special_forms": special,
        "structural_notes": structural,
        "dominant_element": dominant_element,
        "element_balance": dict(element_counts),
        "month_tengod": month_tengod,
    }
