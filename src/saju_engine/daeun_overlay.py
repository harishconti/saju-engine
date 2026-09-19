"""Major-luck (대운, 大運) activation overlay.

Each 10-year 대운 period carries a stem and branch. This module computes how
that period interacts with the natal chart deterministically, so time-based
readings need not re-derive the relationships by hand.

Detected overlays:
  - ten-god (십신) of the 대운天干 relative to the Day Master
  - branch relationships between the 대운地支 and each natal branch
  - stem combinations (천간합) between the 대운天干 and natal stems
  - element favorability vs. the strength-heuristic candidate 용신/기신
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from . import lookup as L
from .chart import DaeunPeriod
from .lookup import TENGOD_EN as _TENGOD_EN
from .sewoon import _detect_branch_relationship


def derive_daeun_overlay(
    day_master: str,
    natal_branches: List[str],
    natal_stems: List[str],
    strength_assessment: Optional[Dict],
    period: DaeunPeriod,
) -> Dict:
    """Return an overlay dictionary for a single DaeunPeriod.

    The returned dictionary contains:
      - stem_tengod / stem_tengod_en: 십신 of the 대운天干
      - activated_branches: list of (daeun_branch, natal_branch, relationship_type)
      - relationship_types: deduplicated relationship names
      - stem_combinations: list of {stem_a, stem_b, combined_element, in_season,
        breaker_present, confidence} for 천간합 with natal stems
      - stem_element / branch_element: 오행 elements
      - favorable_status: 'favorable', 'unfavorable', or 'neutral' vs. the
        heuristic candidate 용신/기신 (None if strength_assessment unavailable)
    """
    # 십신 of 대운天干
    tengod = L.ten_god(day_master, period.stem)
    tengod_en = _TENGOD_EN.get(tengod, tengod)

    # Branch activations
    activated: List[Tuple[str, str, str]] = []
    rel_types: set[str] = set()
    for nb in natal_branches:
        rel = _detect_branch_relationship(period.branch, nb)
        if rel:
            activated.append((period.branch, nb, rel))
            rel_types.add(rel)

    # Stem combinations (천간합) with natal stems
    stem_combos: List[Dict] = []
    for ns in natal_stems:
        combo = L.stem_combination(period.stem, ns)
        if combo:
            elem, ko_name, pair_label = combo
            stem_combos.append({
                "stem_a": period.stem,
                "stem_b": ns,
                "combined_element": elem,
                "korean_name": ko_name,
                "pair_label": pair_label,
            })

    # Elements
    stem_element = L.STEM_INFO.get(period.stem, {}).get("element", "")
    branch_element = L.BRANCH_ELEMENT.get(period.branch, "")

    # Favorability vs. heuristic strength assessment
    favorable_status: Optional[str] = None
    if strength_assessment:
        fav = strength_assessment.get("candidate_favorable")
        unfav = strength_assessment.get("candidate_unfavorable")
        hits = {stem_element, branch_element}
        if fav in hits:
            favorable_status = "favorable"
        elif unfav in hits:
            favorable_status = "unfavorable"
        else:
            favorable_status = "neutral"

    return {
        "stem_tengod": tengod,
        "stem_tengod_en": tengod_en,
        "activated_branches": activated,
        "relationship_types": sorted(rel_types),
        "stem_combinations": stem_combos,
        "stem_element": stem_element,
        "branch_element": branch_element,
        "favorable_status": favorable_status,
    }


def build_daeun_overlays(
    day_master: str,
    natal_branches: List[str],
    natal_stems: List[str],
    strength_assessment: Optional[Dict],
    periods: List[DaeunPeriod],
) -> List[DaeunPeriod]:
    """Populate each DaeunPeriod with its activation overlay in-place.

    Returns the same list so callers can assign it back to the chart.
    """
    for period in periods:
        overlay = derive_daeun_overlay(
            day_master=day_master,
            natal_branches=natal_branches,
            natal_stems=natal_stems,
            strength_assessment=strength_assessment,
            period=period,
        )
        period.stem_tengod = overlay["stem_tengod"]
        period.stem_tengod_en = overlay["stem_tengod_en"]
        period.activated_branches = overlay["activated_branches"]
        period.relationship_types = overlay["relationship_types"]
        period.stem_combinations = overlay["stem_combinations"]
        period.stem_element = overlay["stem_element"]
        period.branch_element = overlay["branch_element"]
        period.favorable_status = overlay["favorable_status"]
    return periods
