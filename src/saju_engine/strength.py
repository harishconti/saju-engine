"""Day-Master strength heuristic for the Saju engine.

This module provides a **non-interpretive, numerical aid** for estimating
신강/신약 (strong vs. weak Day Master) and candidate 용신/희신/기신/한신.
It is a heuristic, not a classical ruling: the final favorable element must
still be argued from the full chart context per `knowledge/09-interpretation-method.md`.

Rules sourced from:
  - knowledge/03-five-elements.md (generating/overcoming cycles)
  - knowledge/06-twelve-stages.md (12운성 stage weights)
  - knowledge/09-interpretation-method.md Step 2 (the 월령 signal is the month
    branch's season relative to the Day Master's *element*)
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from . import lookup as L


# Inverse of the generating cycle: for each element, the element that generates it.
_GENERATED_BY: Dict[str, str] = {v: k for k, v in L.GENERATES.items()}


# 월령 (month-command) support by the month branch's element relation to the
# Day Master's element — knowledge/09 Step 2, "Seasonal support (월지)":
#   - month branch is the DM's peak season            -> strongest support
#   - month branch is the DM's own element             -> strong support
#   - month branch generates the DM (인성, resource)    -> supportive (Step 2
#     factor 3: 인성 strengthens), below the DM's own season
#   - output / wealth / authority month ("off-season") -> no seasonal support
# Weights reuse the scale `_STAGE_WEIGHT` had (제왕 2.0 / 건록 1.5 ... 사 0.0)
# so the verdict thresholds below stay calibrated.
_PEAK_BRANCHES = frozenset("子午卯酉")  # 왕지: the single-element peak of each season
_MONTH_RELATION_WEIGHT: Dict[str, float] = {
    "peak": 2.0,
    "same": 1.5,
    "resource": 1.0,
    "output": 0.0,
    "wealth": 0.0,
    "authority": 0.0,
}


def month_relation(day_master: str, month_branch: str) -> str:
    """The month branch's element relation to the Day Master's element — the
    월령 input to strength scoring.

    N-5 (2026-09-26 audit; decision recorded in
    docs/audits/2026-09-26-deep-engine-audit-verification.md): strength used
    to score the Day Master's own 12운성 stage in the month branch. For yin
    stems that stage runs the backward 음생양사 cycle, so 乙 in 午 (its
    draining month) scored 장생 (supported) and 乙 in 亥 (its resource month)
    scored 사 (depleted), inverting yin Day Masters; even for yang stems a
    few stages sit against the season (庚 장생 in 巳, 戊 장생 in 寅 — both
    months whose element controls the DM). knowledge/09 Step 2 defines the
    seasonal signal by element, independent of stem polarity, and that is
    what this returns. The Day Master's own 12운성 stage (`month_stage`)
    stays the descriptive reading (knowledge/06).

    Returns one of "peak", "same", "resource", "output", "wealth", "authority".
    """
    dm_element = L.STEM_INFO[day_master]["element"]
    month_element = L.BRANCH_ELEMENT[month_branch]
    if month_element == dm_element:
        return "peak" if month_branch in _PEAK_BRANCHES else "same"
    if L.GENERATES[month_element] == dm_element:
        return "resource"
    if L.GENERATES[dm_element] == month_element:
        return "output"
    if L.OVERCOMES[dm_element] == month_element:
        return "wealth"
    return "authority"


_YANG_STEM_OF: Dict[str, str] = {
    "Wood": "甲", "Fire": "丙", "Earth": "戊", "Metal": "庚", "Water": "壬",
}

# 12운성 relative weights; 제왕/건록/관대/장생 are supportive, 사/묘/절 are
# depleted. No longer the 월령 input (see `month_relation`); kept as the
# season-weakness tie-break in the balanced fallback.
_STAGE_WEIGHT = {
    "장생": 1.5,
    "목욕": 0.8,
    "관대": 1.2,
    "건록": 1.5,
    "제왕": 2.0,
    "쇠": 0.5,
    "병": 0.2,
    "사": 0.0,
    "묘": 0.3,  # stored/hidden qi, weak but not zero (knowledge/06-twelve-stages.md)
    "절": 0.0,
    "태": 0.5,
    "양": 0.7,
}


def _element_counts(
    stems: List[str],
    hidden_stems: List[Tuple[str, str]],
) -> Counter:
    """Count element occurrences across visible stems and hidden stems.

    Hidden stems are weighted lower than visible stems because they are
    submerged qi.
    """
    counts: Counter = Counter()
    for s in stems:
        counts[L.STEM_INFO[s]["element"]] += 1.0
    for role, s in hidden_stems:
        weight = {"main": 0.6, "middle": 0.3, "residual": 0.1}.get(role, 0.3)
        counts[L.STEM_INFO[s]["element"]] += weight
    return counts


def assess_strength(
    day_master: str,
    month_branch: str,
    stems: List[str],
    hidden_stems: List[Tuple[str, str]],
) -> Dict:
    """Return a heuristic strength assessment for the Day Master.

    The result contains:
      - element_counts: weighted stem counts by element
      - month_stage: the Day Master's own (descriptive) 12운성 stage in the month branch
      - month_relation: month branch element vs DM element (strength input)
      - month_stage_score: 월령 support, from `month_relation`
      - total_score: combined numeric score
      - verdict: 'strong', 'weak', 'extreme_weak', 'balanced', or 'extreme'
      - candidate_favorable: candidate 용신 element
      - candidate_supporting: candidate 희신 element
      - candidate_unfavorable: candidate 기신 element
      - candidate_draining: candidate 한신 element
    """
    dm_element = L.STEM_INFO[day_master]["element"]
    counts = _element_counts(stems, hidden_stems)

    # Descriptive 12운성 stage of the Day Master itself (knowledge/06).
    month_stage = L.twelve_stage(day_master, month_branch)
    # 월령 support: the month branch's element relative to the DM's element
    # (knowledge/09 Step 2; N-5).
    relation = month_relation(day_master, month_branch)
    month_stage_score = _MONTH_RELATION_WEIGHT[relation]

    # Self-element score (visible + hidden peers of the Day Master).
    # The Day Master stem itself must not count as self-support; only peer
    # same-element stems (비견/겁재) strengthen the self. Subtract the DM's
    # own 1.0 contribution so that a bare Day Master has self_score == 0.
    self_score = max(0.0, counts.get(dm_element, 0.0) - 1.0)

    # Resource element score (element that generates the Day Master)
    resource_element = {
        "Wood": "Water", "Fire": "Wood", "Earth": "Fire",
        "Metal": "Earth", "Water": "Metal",
    }[dm_element]
    resource_score = counts.get(resource_element, 0.0)

    # Drain elements: output (generated by DM), wealth (controlled by DM),
    # authority (controls DM). These press against the Day Master.
    output_element = L.GENERATES[dm_element]
    wealth_element = L.OVERCOMES[dm_element]
    authority_element = {
        "Wood": "Metal", "Fire": "Water", "Earth": "Wood",
        "Metal": "Fire", "Water": "Earth",
    }[dm_element]
    drain_score = (
        counts.get(output_element, 0.0)
        + counts.get(wealth_element, 0.0)
        + counts.get(authority_element, 0.0)
    )

    total_score = (
        self_score * 1.0
        + resource_score * 0.8
        + month_stage_score * 1.5
        - drain_score * 0.7
    )

    # Verdict thresholds — tuned to be conservative; extreme scores are rare.
    # D1 fix: month_stage_score alone carries the 월령 signal (the old
    # `_MONTH_BRANCH_SEASON` score was dropped from the total then, and — N-19,
    # 2026-09-26 audit — from the module and its JSON output too, since
    # readers assumed an exported score fed the verdict).
    # D3 fix: symmetric extreme bands for very weak Day Masters.
    if total_score >= 4.0:
        verdict = "extreme"
    elif total_score >= 1.5:
        verdict = "strong"
    elif total_score <= -4.0:
        verdict = "extreme_weak"
    elif total_score <= -1.5:
        verdict = "weak"
    else:
        verdict = "balanced"

    # Candidate favorable / supporting / unfavorable / draining elements.
    # Convention (see knowledge/03-five-elements.md §"Two conventions for 희신"):
    #   - Strong/weak DMs: MODERN Korean convention — 희신 = secondary favorable
    #     element in the same balancing direction as 용신 (strong: 용신=식상,
    #     희신=재성; weak: 용신=인성, 희신=비겁). The strict classical "희신 =
    #     generates 용신" formula yields the 기신 element here, so it is not used.
    #   - Balanced DM: STRICT classical formula — 희신 = the element that
    #     generates the under-represented 용신 element (unambiguous in this case).
    # All outputs are heuristic candidates only; the final 용신/희신 must be
    # argued from the full chart per knowledge/09-interpretation-method.md.
    balanced_tie = None
    if verdict in ("strong", "extreme"):
        # Strong Day Master needs outlets, not more support.
        candidate_favorable = output_element      # 食傷 / output channel (drains)
        candidate_supporting = wealth_element     # 財星 / wealth channel (also drains)
        candidate_unfavorable = dm_element        # 比劫 / self echo strengthens the strong
        candidate_draining = authority_element  # 官殺 / authority pressure on strong self
    elif verdict in ("weak", "extreme_weak"):
        candidate_favorable = resource_element    # 印綬 / resource support
        candidate_supporting = dm_element         # 比劫 / peer support
        candidate_unfavorable = authority_element # authority controls weak self
        candidate_draining = wealth_element       # wealth drains weak self
    else:
        # Balanced: the element that is most under-represented in the chart
        # is a folk heuristic, not a classical ruling. The final 용신 must be
        # argued from temperature, blockage, and season per knowledge/09.
        all_elements = ["Wood", "Fire", "Earth", "Metal", "Water"]
        # E-5 (2026-09-25 audit): never offer the element that controls the
        # Day Master (관성) when the month branch is that element's own
        # season — an in-season controller is already commanding the chart
        # (득령), so a low raw count understates it and "adding more" is the
        # opposite of balancing. This is the audit's minimum guard; the pick
        # remains a folk heuristic that the reader must argue (see
        # yongsin.py's balanced-heuristic note).
        if L.BRANCH_ELEMENT.get(month_branch) == authority_element:
            all_elements = [e for e in all_elements if e != authority_element]
        # N-19 (2026-09-26 audit): `min()` over this fixed list silently
        # resolved ties to the first entry (Wood). Ties are now surfaced in
        # `balanced_tie`; the pick among tied elements prefers the one the
        # month season supports least (weakest 12운성 weight of that
        # element's yang stem, i.e. its seasonal lifecycle) — only then list
        # order.
        lowest = min(counts.get(e, 0.0) for e in all_elements)
        tied = [e for e in all_elements if abs(counts.get(e, 0.0) - lowest) < 1e-9]
        least_present = min(
            tied,
            key=lambda e: _STAGE_WEIGHT.get(L.twelve_stage(_YANG_STEM_OF[e], month_branch), 0.5),
        )
        if len(tied) > 1:
            balanced_tie = tied
        candidate_favorable = least_present
        # Supporting element is the one that generates (nourishes) the least-present element.
        candidate_supporting = _GENERATED_BY.get(least_present, least_present)
        candidate_unfavorable = None
        candidate_draining = None

    return {
        "element_counts": dict(counts),
        "month_branch": month_branch,
        "month_stage": month_stage,
        "month_relation": relation,
        "month_stage_score": month_stage_score,
        "self_score": self_score,
        "resource_score": resource_score,
        "drain_score": drain_score,
        "total_score": round(total_score, 2),
        "verdict": verdict,
        "candidate_favorable": candidate_favorable,
        "candidate_supporting": candidate_supporting,
        "candidate_unfavorable": candidate_unfavorable,
        "candidate_draining": candidate_draining,
        "balanced_tie": balanced_tie,
        "note": "Heuristic only; final 용신 must be argued from the full chart context.",
    }


# ── Public element-balance helpers (single source of truth) ───────────────────

def element_balance_counts(chart) -> Counter:
    """Return canonical weighted element counts for `chart`.

    Prefers the already-computed ``strength_assessment["element_counts"]`` so
    the balance used by the strength heuristic matches the balance shown in
    reports. Falls back to recomputing from visible stems and hidden stems
    with the same weights used by ``assess_strength``.
    """
    sa = getattr(chart, "strength_assessment", None) or {}
    if sa.get("element_counts"):
        return Counter(sa["element_counts"])

    stems: List[str] = []
    hidden: List[Tuple[str, str]] = []
    if hasattr(chart, "stems"):
        stems = chart.stems
    if hasattr(chart, "pillars"):
        for p in chart.pillars:
            hidden.extend(getattr(p, "hidden_stems", []))
    return _element_counts(stems, hidden)


def element_balance_pct(chart) -> Dict[str, float]:
    """Return element percentages (0–100) using ``element_balance_counts``.

    Guarantees all five elements are present in the returned dict.
    """
    counts = element_balance_counts(chart)
    total = sum(counts.values()) or 1
    return {
        e: round(counts.get(e, 0) / total * 100, 1)
        for e in ["Wood", "Fire", "Earth", "Metal", "Water"]
    }
