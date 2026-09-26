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


# 성격/파격 (grid completion / grid-breaking) cross-reference.
# E-9 (2026-09-25 audit): 격국 naming (regular_grid) and named ten-god
# conflict patterns (detect_tengod_conflicts) were computed independently —
# a 정관격 was asserted at "likely" confidence with zero regard for whether
# 상관견관 (the *same* chart's own already-detected conflict, sourced from
# knowledge/05-ten-gods.md: "상관견관 = 상관 directly clashing with 정관")
# was present. This is deliberately narrow: it maps a conflict pattern to
# the single grid ten-god that knowledge/05-ten-gods.md's own wording names
# it as breaking, and only downgrades that grid — it does not invent a
# general 파격 theory beyond what the two already-implemented, already-cited
# detectors (regular_grid + detect_tengod_conflicts, below) jointly support.
_GRID_BREAKING_CONFLICTS: Dict[str, str] = {
    "상관견관": "정관",
}


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


def detect_tengod_conflicts(
    day_master: str,
    stems: List[str],
    hidden_stems: List[Tuple[str, str]],
) -> List[Dict[str, str]]:
    """Detect classical ten-god-vs-ten-god conflict patterns.

    Added 2026-09-19 (external report review): 상관견관 (傷官見官) — 상관
    (Hurting Officer) meeting 정관 (Direct Officer) — is documented as a named
    classical conflict pattern in `knowledge/05-ten-gods.md` ("often read as
    causing problems with 관성 ... 상관 directly clashing with 정관, the
    classical 'rebellion against authority' pattern") but had no engine
    detection anywhere, so a "deep" report never surfaced it even when
    present — confirmed missing for Harish's chart, which carries three 상관
    sources (year stem + two hidden) against one hidden 정관.

    This is deliberately narrow and Ground-Rule-1-conservative: only the
    specific documented pairing (상관 + 정관) is checked. 편관 (Seven Killings)
    is NOT included — it forms different, separately-named classical patterns
    (e.g. 식신제살) and conflating it here would invent an undocumented rule.
    """
    all_stems = list(stems) + [s for _, s in hidden_stems]
    tengods = {L.ten_god(day_master, s) for s in all_stems}
    conflicts: List[Dict[str, str]] = []
    if "상관" in tengods and "정관" in tengods:
        conflicts.append({
            "name_ko": "상관견관",
            "name_en": "Output Meets Authority",
            "basis": "Both 상관 (Hurting Officer) and 정관 (Direct Officer) are present among the chart's stems (visible or hidden)",
            "confidence": "likely",
            "note": "Classical conflict pattern (knowledge/05-ten-gods.md): 상관's output tends to clash with 정관's orderly authority — often read as friction with rules, institutions, or superiors. A structural tendency to watch, not a fixed event.",
        })
    return conflicts


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

    set(branches)
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


def _officer_grid_breakers(day_master: str, stems: List[str]) -> List[str]:
    """관살혼잡 and 정관 합거 on the visible stems (knowledge/07 §정관격 파격).

    ``stems`` is year/month/day/hour; the Day Master (index 2) is neither an
    officer nor counted as a 합거 partner (a 정관 combining with the Day
    Master itself is not read as "taken away").
    """
    out: List[str] = []
    visible = [(i, s, L.ten_god(day_master, s)) for i, s in enumerate(stems) if i != 2]
    gods = {g for _i, _s, g in visible}
    if "정관" in gods and "편관" in gods:
        out.append("관살혼잡 (정관 and 편관 both on the visible stems)")
    for i, officer, g in visible:
        if g != "정관":
            continue
        partner = next(
            (o for j, o, _g in visible if j != i and L.stem_combination(officer, o)), None
        )
        if partner:
            out.append(f"정관 합거 ({officer} bound by 천간합 with {partner})")
            break
    return out


def _officer_grid_caveats(
    day_master: str,
    stems: List[str],
    hidden_stems: List[Tuple[str, str]],
    month_branch: str,
    branches: List[str],
    strength_verdict: str,
) -> List[str]:
    """Non-breaking 정관격 caveats: 충·형 on the month branch (purity lowered)
    and a weak Day Master (needs 인성). knowledge/07 §정관격 — 성격 / 파격."""
    out: List[str] = []
    others = [b for i, b in enumerate(branches) if i != 1]
    hits = []
    for b in others:
        if any({month_branch, b} == {x, y} for x, y in L.SIX_CLASHES):
            hits.append(f"{b}{month_branch} 충")
        for b1, b2, b3, _label in L.THREE_PUNISHMENTS:
            members = {m for m in (b1, b2, b3) if m != "—"}
            if b != month_branch and b in members and month_branch in members:
                hits.append(f"{b}{month_branch} 형")
    if hits:
        out.append(
            f"The month branch is struck ({', '.join(dict.fromkeys(hits))}), which lowers the "
            "grid's purity without fully breaking it."
        )
    if strength_verdict in ("weak", "extreme_weak"):
        all_stems = list(stems) + [s for _, s in hidden_stems]
        has_resource = any(L.ten_god(day_master, s) in ("정인", "편인") for s in all_stems)
        out.append(
            "With a weak Day Master the officer can feel like a burden; classically 인성 (Resource) "
            "must protect the self — "
            + ("and 인성 is present here." if has_resource else "and 인성 is absent here, so read this grid cautiously.")
        )
    return out


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
      - yangin: star-level 양인 (blade branch anywhere).
      - yangin_grid: 양인격 — blade branch is the month branch (자평진전).
      - yangin_non_month: blade branch in year/day/hour (distinct pattern).
      - jianlu: 건록격 — 건록 branch is the month branch (자평진전).
      - jianlu_non_month: 건록 branch in year/day/hour (distinct pattern).
      - stem_combinations: list of ten-stem combination candidates.
      - transformation_grid: 화격 candidate, or None.
      - special_forms: list of 종격 candidates (conservative thresholds).
      - structural_notes: 전국 / 편국 / 삼합국 detections.
      - tengod_conflicts: named ten-god-vs-ten-god conflicts (currently only
        상관견관 — see detect_tengod_conflicts).
      - dominant_element: element with highest weighted count.
      - element_balance: weighted element counts.
    """
    L.STEM_INFO[day_master]["element"]
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


    # 양인 / 건록 (N-9, 2026-09-26 audit; decision recorded in
    # docs/audits/2026-09-26-deep-engine-audit-verification.md: support both
    # conventions, labeled differently — knowledge/07 §B.3-4):
    #   - blade / 건록 branch AS THE MONTH BRANCH (월령) → the classical grid
    #     양인격 / 건록격 (자평진전 convention). The month-비겁 regular grid is
    #     renamed accordingly, since 자평진전 names that structure by 월령,
    #     not 비견격/겁재격.
    #   - blade / 건록 branch in the year, day or hour pillar → a related but
    #     distinct non-month pattern (the rule this file used before N-9):
    #     day-branch blade = 일인 (日刃), hour-branch 건록 = 귀록 (歸祿).
    #   - the star-level 양인 appears wherever the blade branch is found.
    blade = _BLADE_BRANCH.get(day_master)
    yangin_positions_star = []
    yangin_positions_non_month = []
    if blade:
        yangin_positions_star = [p for p, b in enumerate(branches) if b == blade]
        yangin_positions_non_month = [p for p in yangin_positions_star if p in {0, 2, 3}]
    yangin_month = blade is not None and month_branch == blade

    jianlu = _JIANLU_BRANCH.get(day_master)
    jianlu_positions = []
    if jianlu:
        jianlu_positions = [p for p, b in enumerate(branches) if b == jianlu]
    jianlu_positions_non_month = [p for p in jianlu_positions if p in {0, 2, 3}]
    jianlu_month = jianlu is not None and month_branch == jianlu

    for candidate in regular_grid:
        if yangin_month and grid_tengod in ("비견", "겁재"):
            candidate.name_ko, candidate.name_en = "양인격", "Blade Grid"
            candidate.basis = (
                f"월령 {month_branch} is the 양인 (제왕) branch of Day Master {day_master} — "
                f"자평진전 names this month-비겁 structure 양인격 rather than {grid_tengod}격 "
                f"(knowledge/07 §B.3); {candidate.basis}"
            )
        elif jianlu_month and grid_tengod in ("비견", "겁재"):
            candidate.name_ko, candidate.name_en = "건록격", "Established Salary Grid"
            candidate.basis = (
                f"월령 {month_branch} is the 건록 branch of Day Master {day_master} — "
                f"자평진전 names this month-비겁 structure 건록격 rather than {grid_tengod}격 "
                f"(knowledge/07 §B.4); {candidate.basis}"
            )

    element_counts = _element_counts(stems, hidden_stems, branches)
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
    tengod_conflicts = detect_tengod_conflicts(day_master, stems, hidden_stems)

    # 성격/파격 cross-reference (E-9, 2026-09-25 audit) — see
    # _GRID_BREAKING_CONFLICTS above for scope and sourcing, and
    # knowledge/07-special-formations.md §정관격 — 성격 / 파격 for the
    # 2026-09-26 additions (관살혼잡, 정관 합거; 월지 충·형 and 신약 caveats).
    conflict_names = {c["name_ko"] for c in tengod_conflicts}
    for candidate in regular_grid:
        breaking = [
            name for name, broken_god in _GRID_BREAKING_CONFLICTS.items()
            if name in conflict_names and broken_god == grid_tengod
        ]
        caveats: List[str] = []
        if grid_tengod == "정관":
            breaking += _officer_grid_breakers(day_master, stems)
            caveats = _officer_grid_caveats(
                day_master, stems, hidden_stems, month_branch, branches, strength_verdict
            )
        notes: List[str] = []
        if breaking:
            candidate.confidence = "possible"
            notes.append(
                f"파격 (broken-grid) risk: {', '.join(breaking)} is also present in this "
                f"chart (knowledge/05-ten-gods.md, knowledge/07-special-formations.md), which "
                f"classically complicates a {candidate.name_ko} reading. Read this grid's usual "
                "meaning with that caveat rather than at full strength."
            )
        notes += caveats
        if notes:
            candidate.note = " ".join(notes)

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
            "positions": [1] if yangin_month else [],
            "present": yangin_month,
            "note": (
                "양인격 (blade grid): the blade branch is the month branch (월령 양인), the "
                "자평진전 grid definition per knowledge/07-special-formations.md §B.3."
            ) if yangin_month else None,
        },
        "yangin_non_month": {
            "day_master": day_master,
            "blade_branch": blade,
            "positions": yangin_positions_non_month,
            "present": len(yangin_positions_non_month) > 0,
            "day_blade": 2 in yangin_positions_non_month,
            "note": (
                "Blade branch in the year, day or hour pillar — a strong-self pattern related to, "
                "but distinct from, the month-branch 양인격"
                + ("; in the day branch it is the 일인 (日刃) case" if 2 in yangin_positions_non_month else "")
                + " (knowledge/07-special-formations.md §B.3)."
            ) if yangin_positions_non_month else None,
        },
        "jianlu": {
            "day_master": day_master,
            "jianlu_branch": jianlu,
            "positions": [1] if jianlu_month else [],
            "present": jianlu_month,
            "note": (
                "건록격: the 건록 branch is the month branch (월령 건록), the 자평진전 grid definition "
                "per knowledge/07-special-formations.md §B.4 — natural self-sufficiency and earning capacity."
            ) if jianlu_month else None,
        },
        "jianlu_non_month": {
            "day_master": day_master,
            "jianlu_branch": jianlu,
            "positions": jianlu_positions_non_month,
            "present": len(jianlu_positions_non_month) > 0,
            "hour_lu": 3 in jianlu_positions_non_month,
            "note": (
                "건록 branch in the year, day or hour pillar — self-reliance support related to, "
                "but distinct from, the month-branch 건록격"
                + ("; in the hour branch it is the 귀록 (歸祿) case" if 3 in jianlu_positions_non_month else "")
                + " (knowledge/07-special-formations.md §B.4)."
            ) if jianlu_positions_non_month else None,
        },
        "stem_combinations": stem_combos,
        "transformation_grid": transformation,
        "special_forms": special,
        "structural_notes": structural,
        "tengod_conflicts": tengod_conflicts,
        "dominant_element": dominant_element,
        "element_balance": dict(element_counts),
        "month_tengod": month_tengod,
    }
