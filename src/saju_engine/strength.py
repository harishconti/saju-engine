"""Day-Master strength heuristic for the Saju engine.

This module provides a **non-interpretive, numerical aid** for estimating
신강/신약 (strong vs. weak Day Master) and candidate 용신/희신/기신/한신.
It is a heuristic, not a classical ruling: the final favorable element must
still be argued from the full chart context per `knowledge/09-interpretation-method.md`.

Rules sourced from:
  - knowledge/03-five-elements.md (generating/overcoming cycles)
  - knowledge/09-interpretation-method.md §Step 2 (seasonal support: the month
    branch's own element vs. the Day Master's element) — this is the 득령
    signal that now drives the verdict.
  - knowledge/06-twelve-stages.md (12운성 stage — retained as *descriptive*
    metadata only; see the N-5 note below).

N-5 (2026-09-26 doctrinal decision, user-approved, implemented here): the
month-branch support term is scored from the **element relation** (season/
element, knowledge/09 Step 2) rather than from the Day Master's 12운성 stage.
The 12운성 cycle runs backward for yin stems (음생양사), so scoring strength off
the stage inverted yin Day Masters — 乙 in 午 (its 장생) scored as strongly
supported and 乙 in 亥 (its 사) as unsupported, whereas by season both are the
opposite. The 2026-09-26 audit cites 임철초's 적천수 commentary as explicitly
critical of using 음장생 for strength (not independently verified here), and
knowledge/06's stage cheat sheet and knowledge/09 Step 2 genuinely disagreed
for yin stems. The stage table stays authoritative for its own
descriptive purpose (12운성 narrative, 대운/세운 stage readings); only the
strength *scoring* input changed.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Dict, List, Tuple

from . import lookup as L


# Inverse of the generating cycle: for each element, the element that generates it.
_GENERATED_BY: Dict[str, str] = {v: k for k, v in L.GENERATES.items()}


# Seasonal strength of each element by month branch (solar-term month).
# Simplified: each branch's season strongly favors its own element and the
# element it generates. Values are relative weights.
#
# This table is the 득령 (in-season) signal used by the strength verdict
# (knowledge/09 Step 2). It is keyed on the Day Master's element, so it is
# yin/yang-neutral — a 乙 and an 甲 born in 亥 read the same seasonal support,
# which is the whole point of the N-5 fix (see the module docstring).
_MONTH_BRANCH_SEASON = {
    "寅": {"Wood": 2.0, "Fire": 1.0},
    "卯": {"Wood": 2.0, "Fire": 1.0},
    "辰": {"Wood": 1.0, "Earth": 1.5, "Water": 0.5},  # late spring, earth storing
    "巳": {"Fire": 2.0, "Earth": 1.0, "Metal": 0.5},  # 巳 hides 庚 (Metal 長生)
    "午": {"Fire": 2.0, "Earth": 1.0},
    "未": {"Fire": 1.0, "Earth": 2.0},
    "申": {"Metal": 2.0, "Water": 1.0, "Earth": 0.5},  # 申 hides 戊 (Earth 餘氣)
    "酉": {"Metal": 2.0, "Water": 1.0},
    "戌": {"Metal": 1.0, "Earth": 2.0, "Fire": 0.5},  # late autumn, earth storing
    "亥": {"Water": 2.0, "Wood": 1.0},
    "子": {"Water": 2.0, "Wood": 1.0},
    "丑": {"Water": 1.0, "Earth": 2.0, "Metal": 0.5},  # late winter, earth storing
}

# 12운성 strength signal for the Day Master in the month branch.
# These are relative weights; 제왕/건록/관대/장생 are supportive, 사/묘/절 are depleted.
#
# N-5: DESCRIPTIVE ONLY — since the 2026-09-26 decision this table no longer
# feeds the strength verdict (month_stage_score is still exported for the
# 12운성 narrative prose, but the verdict uses month_season_score instead).
# Kept because prose_fillers' stage narrative and the report's "stage in the
# month branch" line are legitimate 12운성 readings, not strength claims.
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


# Relative qi of a branch's hidden stems (본기 > 중기 > 여기). These are
# normalised **per branch** so every branch contributes the same total qi
# (N-12, 2026-09-26), then scaled by `_HIDDEN_BRANCH_QI` so a branch still
# weighs less than a visible stem (its qi is submerged).
_HIDDEN_ROLE_RATIO = {"main": 0.6, "middle": 0.3, "residual": 0.1}
# Total qi of one branch's hidden stems, relative to one visible stem (1.0).
_HIDDEN_BRANCH_QI = 0.6


def _element_counts(
    stems: List[str],
    hidden_stems: List[Tuple[str, str]],
) -> Counter:
    """Count element occurrences across visible stems and hidden stems.

    Visible stems weigh 1.0 each. Each **branch's** hidden stems are normalised
    so the branch contributes a fixed total qi (`_HIDDEN_BRANCH_QI`, < 1.0) split
    among its 본기/중기/여기 by `_HIDDEN_ROLE_RATIO`.

    N-12 (2026-09-26 audit): the old scheme gave each role a fixed absolute
    weight (main 0.6, middle 0.3, residual 0.1), so a one-stem branch (子卯酉)
    totalled 0.6 while a three-stem branch totalled 1.0 — the 王地 (pure
    branches) were underweighted by 10–40%. Branch boundaries are detected by the
    `main` role, which begins each branch's group in the (main → middle →
    residual) order the hidden-stem table is built in. Because a branch totals
    0.6 instead of the 1.0 a normalization-to-1.0 would give, the absolute score
    scale is preserved (only the *relative* branch weights change) — this keeps
    the strength thresholds stable while correcting the inequality.
    """
    counts: Counter = Counter()
    for s in stems:
        counts[L.STEM_INFO[s]["element"]] += 1.0

    # Split the flat list into per-branch groups (each starts at a "main").
    group: List[Tuple[str, str]] = []
    groups: List[List[Tuple[str, str]]] = []
    for role, s in hidden_stems:
        if role == "main" and group:
            groups.append(group)
            group = []
        group.append((role, s))
    if group:
        groups.append(group)

    for branch_stems in groups:
        total_ratio = sum(_HIDDEN_ROLE_RATIO.get(r, 0.3) for r, _ in branch_stems) or 1.0
        for role, s in branch_stems:
            share = _HIDDEN_ROLE_RATIO.get(role, 0.3) / total_ratio
            counts[L.STEM_INFO[s]["element"]] += share * _HIDDEN_BRANCH_QI
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
      - month_season_score: seasonal (element-relation) support from the month
        branch — the scored 월령 signal (N-5)
      - month_stage_score: 12운성 support in the month branch (descriptive
        only since N-5; still exported for the stage narrative)
      - total_score: combined numeric score
      - verdict: 'strong', 'weak', 'extreme_weak', 'balanced', or 'extreme'
      - candidate_favorable: candidate 용신 element
      - candidate_supporting: candidate 희신 element
      - candidate_unfavorable: candidate 기신 element
      - candidate_draining: candidate 한신 element
    """
    dm_element = L.STEM_INFO[day_master]["element"]
    counts = _element_counts(stems, hidden_stems)

    # 득령 (seasonal/in-season support) from the month branch — the element
    # relation per knowledge/09 Step 2. This is the scored 월령 signal (N-5).
    season_weights = _MONTH_BRANCH_SEASON.get(month_branch, {})
    month_season_score = season_weights.get(dm_element, 0.0)

    # 12운성 support in month branch — descriptive metadata only since N-5
    # (see the module docstring); no longer contributes to total_score.
    month_stage = L.twelve_stage(day_master, month_branch)
    month_stage_score = _STAGE_WEIGHT.get(month_stage, 0.5)

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
        + month_season_score * 1.5
        - drain_score * 0.7
    )

    # Verdict thresholds — tuned to be conservative; extreme scores are rare.
    # N-5 (2026-09-26): month_season_score (element relation, knowledge/09
    # Step 2) is the scored 월령 signal. The old D1 fix had removed the
    # season term in favour of month_stage_score, which inverted yin DMs; the
    # element-relation term is yin/yang-neutral and replaces it.
    # Because the season term's maximum (2.0, weighted ×1.5 = 3.0) is larger
    # than the stage term's (2.0 ×1.5 = 3.0 but stage rarely reaches 제왕;
    # the effective old ceiling was ~2.25), the extreme bands are widened
    # from 4.0 to 5.0 so "extreme" stays genuinely rare (≈3% of charts) and
    # the published strong/weak verdicts are unchanged by this decision.
    # D3 fix: symmetric extreme bands for very weak Day Masters.
    if total_score >= 5.0:
        verdict = "extreme"
    elif total_score >= 1.5:
        verdict = "strong"
    elif total_score <= -5.0:
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
    least_present_elements: List[str] = []
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
        # N-19 (2026-09-26 audit): `min()` over the fixed element order resolved
        # ties to its first entry — always Wood — silently. Collect the tied
        # minima and pick deterministically *for display*, but record the tie so
        # the reading can flag it rather than present one element as the clear
        # least-represented. The pick stays a folk heuristic either way.
        least_value = min(counts.get(e, 0.0) for e in all_elements)
        least_present_elements = [e for e in all_elements
                                  if abs(counts.get(e, 0.0) - least_value) < 1e-9]
        least_present = least_present_elements[0]
        candidate_favorable = least_present
        # Supporting element is the one that generates (nourishes) the least-present element.
        candidate_supporting = _GENERATED_BY.get(least_present, least_present)
        candidate_unfavorable = None
        candidate_draining = None

    return {
        "element_counts": dict(counts),
        "month_branch": month_branch,
        "month_stage": month_stage,
        "month_season_score": month_season_score,
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
        # N-19: the balanced-fallback least-present tie set (empty unless the
        # verdict is balanced AND ≥2 elements share the minimum). When non-empty,
        # `candidate_favorable` is just the deterministic first pick, not a
        # unique answer.
        "balanced_tie_elements": least_present_elements if verdict == "balanced" else [],
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


_ELEMENT_ORDER = ["Wood", "Fire", "Earth", "Metal", "Water"]


def element_balance_pct(chart) -> Dict[str, float]:
    """Return element percentages (0–100) using ``element_balance_counts``.

    Guarantees all five elements are present and that the values sum to exactly
    100.0 (largest-remainder rounding). N-12 (2026-09-26): the branch-qi
    normalisation changed the raw counts enough that naive per-element rounding
    could sum to 99.9; the display is anchored to 100.
    """
    counts = element_balance_counts(chart)
    total = sum(counts.values()) or 1
    raw = {e: counts.get(e, 0) / total * 100 for e in _ELEMENT_ORDER}
    floored = {e: math.floor(raw[e] * 10) / 10 for e in _ELEMENT_ORDER}
    # Distribute the remaining tenths to the largest fractional remainders.
    remainder = round(1000 - sum(v * 10 for v in floored.values()))
    order = sorted(_ELEMENT_ORDER, key=lambda e: (raw[e] - floored[e]), reverse=True)
    for e in order[:max(0, remainder)]:
        floored[e] = round(floored[e] + 0.1, 1)
    return floored
