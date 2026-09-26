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
from .sewoon import _detect_branch_relationship, _detect_harmony_completions


def derive_daeun_overlay(
    day_master: str,
    natal_branches: List[str],
    natal_stems: List[str],
    strength_assessment: Optional[Dict],
    period: DaeunPeriod,
    resolved_favorable: Optional[str] = None,
) -> Dict:
    """Return an overlay dictionary for a single DaeunPeriod.

    The returned dictionary contains:
      - stem_tengod / stem_tengod_en: 십신 of the 대운天干
      - activated_branches: list of (daeun_branch, natal_branch, relationship_type)
      - relationship_types: deduplicated relationship names
      - harmony_completions: list of HarmonyCompletion — 삼합/방합 triads the
        대운 branch completes (two natal members present) or half-completes
        (one natal member present) with the natal chart
      - stem_combinations: list of {stem_a, stem_b, combined_element, in_season,
        breaker_present, confidence} for 천간합 with natal stems
      - stem_element / branch_element: 오행 elements
      - favorable_status: 'favorable', 'unfavorable', or 'neutral' vs. the
        chart's resolved 용신 (``resolved_favorable`` when given, else the raw
        heuristic candidate) / the raw heuristic 기신 (None if
        strength_assessment unavailable)
    """
    # 십신 of 대운天干
    tengod = L.ten_god(day_master, period.stem)
    tengod_en = _TENGOD_EN.get(tengod, tengod)

    # Branch activations
    activated: List[Tuple[str, str, str]] = []
    rel_types: set[str] = set()
    for nb in natal_branches:
        for rel in _detect_branch_relationship(period.branch, nb):
            activated.append((period.branch, nb, rel))
            rel_types.add(rel)
    harmony_completions = _detect_harmony_completions(period.branch, natal_branches)

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

    # Favorability vs. the chart's ACTUAL favorable element. Uses
    # ``resolved_favorable`` (the climate-merged 용신 from
    # ``yongsin.favorable_element()``) when the caller supplies it, falling
    # back to the raw strength-heuristic candidate only if it doesn't (e.g. a
    # caller that hasn't been updated, or a chart with no strength_assessment
    # at all). There is no climate-resolved 기신 (unfavorable) concept
    # anywhere in this codebase — ``candidate_unfavorable`` is the raw
    # strength-heuristic value everywhere it is used (e.g. the "Avoid /
    # Watch" field in premium_report.py), so it is kept as-is here too.
    favorable_status: Optional[str] = None
    if strength_assessment:
        fav = resolved_favorable if resolved_favorable is not None else strength_assessment.get("candidate_favorable")
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
        "harmony_completions": harmony_completions,
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
    resolved_favorable: Optional[str] = None,
) -> List[DaeunPeriod]:
    """Populate each DaeunPeriod with its activation overlay in-place.

    ``resolved_favorable``: the chart's climate-merged 용신 element (from
    ``yongsin.favorable_element(chart).element``), used for the
    favorable/neutral/unfavorable lean instead of the raw strength-heuristic
    candidate. See ``derive_daeun_overlay`` for why.

    Returns the same list so callers can assign it back to the chart.
    """
    for period in periods:
        overlay = derive_daeun_overlay(
            day_master=day_master,
            natal_branches=natal_branches,
            natal_stems=natal_stems,
            strength_assessment=strength_assessment,
            period=period,
            resolved_favorable=resolved_favorable,
        )
        period.stem_tengod = overlay["stem_tengod"]
        period.stem_tengod_en = overlay["stem_tengod_en"]
        period.activated_branches = overlay["activated_branches"]
        period.relationship_types = overlay["relationship_types"]
        period.harmony_completions = overlay["harmony_completions"]
        period.stem_combinations = overlay["stem_combinations"]
        period.stem_element = overlay["stem_element"]
        period.branch_element = overlay["branch_element"]
        period.favorable_status = overlay["favorable_status"]
    return periods
