"""Compatibility engine — two-chart 궁합 (궁합, 宮合 / 合婚) scoring.

Produces a structured `CompatReport` from two fully-derived `Chart` objects,
covering all 11 sub-systems described in `knowledge/11-gunghap.md`:

  A — Day-stem combination (일간합)
  B — Day-branch 합·충·형·파·해 (일지 합충)        — 30 weight, highest
  C — Nayin five elements (납음오행)
  D — Favorable element cross-supply (용신 궁합)
  E — Day-pillar pair classification (일주 궁합)
  F — Combined element balance (결합 오행)
  G — Ten-god cross-relationship (십신 교차)
  H — Major luck synchrony (대운·세운 동기)
  I — Compatibility star overlays (신살 궁합)
  J — Yin-Yang polarity (음양 조화)
  K — Year-branch zodiac pair (띠 궁합)

Composite score is a weighted sum capped at 0–100, mapped to a 4-band verdict
("Excellent" / "Strong" / "Mixed" / "Challenging"). Each sub-system returns
its own weighted contribution, narrative, and flag list; the orchestrator
collects the top favorable points and red flags for the report cover.

All rules are sourced from `knowledge/11-gunghap.md` — 권인성·곽임성·정봉재·
송기영 modern Korean Myeongri consensus weighting, with [UNCERTAIN] markers
preserved at the sub-system level for school disagreements.

Ground rules (per knowledge/11-gunghap.md):
  - No single factor decides 궁합; B (일지) outweighs others, but every layer
    is checked.
  - 궁 > 성 — spouse-palace (day branch) outweighs spouse-star (십신 of
    spouse) per KCI 2018 divorce study.
  - Never claim a perfect or failing marriage. Use tendency / pattern /
    resonance / friction language.
"""
from __future__ import annotations

from copy import copy, deepcopy
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from . import lookup as L
from .chart import Chart, Pillar
from .nayin import NAYIN_ORDER, nayin_of, nayin_relation, nayin_relation_detail
from .yongsin import favorable_element


def _resolved_favorable(chart: Chart) -> Optional[str]:
    """The favorable element for scoring/display, via the single source of
    truth (climate-aware, override-aware) — never the raw, pre-climate
    ``strength_assessment["candidate_favorable"]`` field directly."""
    element = favorable_element(chart).element
    return element if element and element != "—" else None


def _resolved_unfavorable(chart: Chart) -> Optional[str]:
    """The 기신 for scoring, via the single source of truth (E-3, 2026-09-26)
    — never the raw ``strength_assessment["candidate_unfavorable"]``, which
    is None for balanced charts and can contradict a climate/reader 용신."""
    return favorable_element(chart).unfavorable or None


def _resolved_supporting(chart: Chart) -> Optional[str]:
    """The supporting (희신) element for scoring, via the single source of truth."""
    supporting = favorable_element(chart).supporting
    return supporting if supporting and supporting != "—" else None


# ── Public dataclasses ───────────────────────────────────────────────────────

@dataclass
class CompatSubResult:
    """One sub-system's verdict."""
    label: str                    # e.g. "Day-branch interaction"
    label_kr: str                 # Korean label
    score: int                    # weighted contribution (-X to +Y)
    max: int                      # maximum possible (positive)
    narrative: str                # 1–3 sentence interpretation
    flags: List[str] = field(default_factory=list)   # short tags for the reader

    @property
    def band(self) -> str:
        """Sub-system verdict band (used by compat_report.py for tone)."""
        ratio = (self.score / self.max) if self.max else 0
        if ratio >= 0.65:
            return "Strong"
        if ratio >= 0.30:
            return "Moderate"
        if ratio >= 0.0:
            return "Soft"
        return "Yellow Flag"


@dataclass
class CompatReport:
    """The full verdict across all 11 sub-systems."""
    score: int                    # composite, 0–100
    band: str                     # Excellent / Strong / Mixed / Challenging
    chart_a: Chart
    chart_b: Chart
    daystem_combo: CompatSubResult
    daybranch: CompatSubResult
    nayin: CompatSubResult
    yongshin: CompatSubResult
    ilju_pair: CompatSubResult
    combined_elements: CompatSubResult
    tengod_cross: CompatSubResult
    daeun_sync: CompatSubResult
    compat_stars: CompatSubResult
    yin_yang: CompatSubResult
    year_branch: CompatSubResult
    red_flags: List[str] = field(default_factory=list)
    yellow_flags: List[str] = field(default_factory=list)
    favorable_points: List[str] = field(default_factory=list)

    def sub_systems(self) -> List[CompatSubResult]:
        """Ordered list of all 11 sub-systems for iteration in the report."""
        return [
            self.daystem_combo,
            self.daybranch,
            self.nayin,
            self.yongshin,
            self.ilju_pair,
            self.combined_elements,
            self.tengod_cross,
            self.daeun_sync,
            self.compat_stars,
            self.yin_yang,
            self.year_branch,
        ]


# ── Composite weight table ───────────────────────────────────────────────────
# Sub-system display maximums. Source: knowledge/11-gunghap.md §Composite Weight.
# D (용신 cross-supply) is folded into F (combined element balance) in the spec;
# we keep F as a descriptive sub-system with its own max/band but exclude it
# from the composite sum so 용신 is not double-counted.
WEIGHT = {
    "daystem_combo": 12,
    "daybranch": 30,
    "nayin": 5,
    "yongshin": 12,         # active 용신 cross-supply weight
    "ilju_pair": 15,
    "combined_elements": 12, # descriptive; not included in composite (see below)
    "tengod_cross": 10,
    "daeun_sync": 5,
    "compat_stars": 5,
    "yin_yang": 3,
    "year_branch": 3,
}


def _band_for(score: int) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Strong"
    if score >= 45:
        return "Mixed"
    return "Challenging"


# ── Sub-system A · Day-stem combination (일간합) ────────────────────────────

# Breaking-stem (간섭) map from knowledge/11-gunghap.md §A.
_BREAKING_STEMS: Dict[frozenset, List[str]] = {
    frozenset(["甲", "己"]): ["乙", "庚"],
    frozenset(["乙", "庚"]): ["甲", "辛"],
    frozenset(["丙", "辛"]): ["丁", "壬"],
    frozenset(["丁", "壬"]): ["丙", "癸"],
    frozenset(["戊", "癸"]): ["己", "甲"],
}


def _breaker_in_month_branch(stem: str, chart: Chart) -> bool:
    """Return True if `stem` sits in `chart`'s month position (천간 or 지장간).

    The month branch is the most powerful position, so a breaking stem lodged
    there "breaks" the day-stem combination more severely than a breaker in
    other positions. *(see knowledge/11-gunghap.md §A)*
    """
    if chart.month.stem == stem:
        return True
    hidden = L.HIDDEN_STEMS.get(chart.month.branch, {})
    return any(s == stem for s in hidden.values())


def _element_in_season(element: str, branch: str) -> bool:
    """Return True if `element` is the season-element of `branch`.

    Conservative in-season check used for the 합화 season test in 일간합:
    the combined element must match the month-branch's element. Modern
    schools differ on whether the generating element also counts; we emit
    the result as a flag rather than gate the score. *(see knowledge/11-
    gunghap.md §A step 3)*
    """
    return L.BRANCH_ELEMENT.get(branch) == element


def compat_daystem_combo(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system A: Day-stem 천간합 between the two Day Masters."""
    label = "Day-stem combination"
    label_kr = "일간합 (天干合)"
    s_a, s_b = a.day.stem, b.day.stem

    combo = L.stem_combination(s_a, s_b)
    if not combo:
        return CompatSubResult(
            label=label, label_kr=label_kr,
            score=0, max=WEIGHT["daystem_combo"],
            narrative=(
                f"The two Day Masters ({s_a} and {s_b}) do not form a 천간합. "
                "Attraction through this layer is neutral; the relationship "
                "must lean on day-branch, element balance, and ten-god cross-relations."
            ),
        )

    combined_elem, korean_name, pair_label = combo
    base = WEIGHT["daystem_combo"]
    score = base
    flags = [f"일간합 {korean_name} → {combined_elem}", f"결합 원소: {combined_elem}"]

    # 합화 in-season check at either partner's month branch.
    in_season_a = _element_in_season(combined_elem, a.month.branch)
    in_season_b = _element_in_season(combined_elem, b.month.branch)
    if in_season_a or in_season_b:
        flags.append(f"합화 원소 {combined_elem} 월령 양호")
    else:
        flags.append(f"합화 원소 {combined_elem} 월령 불분명 [UNCERTAIN]")

    # Breaking-stem check across all 8 visible stems, then by position.
    breakers = _BREAKING_STEMS.get(frozenset([s_a, s_b]), [])
    broken_in_a = [s for s in a.stems if s in breakers]
    broken_in_b = [s for s in b.stems if s in breakers]

    if broken_in_a or broken_in_b:
        # Month-branch breaker → "broken" (−80%); elsewhere → "half-binding" (−50%).
        # *(see knowledge/11-gunghap.md §A step 4)*
        broken_month = any(
            _breaker_in_month_branch(s, a) for s in broken_in_a
        ) or any(_breaker_in_month_branch(s, b) for s in broken_in_b)
        if broken_month:
            score = int(base * 0.2)
            flags.append(f"간섭 월지: {broken_in_a + broken_in_b} (broken)")
            narrative = (
                f"The two Day Masters form {korean_name}, but a breaking stem "
                f"({'/'.join(broken_in_a + broken_in_b)}) sits in a month position, "
                "severely weakening the 합. Classical reading: attraction exists but "
                "is heavily moderated by chart structure."
            )
        else:
            score = int(base * 0.5)
            flags.append(f"간섭 존재: {broken_in_a + broken_in_b} (half-binding)")
            narrative = (
                f"The two Day Masters form {korean_name} (combined element {combined_elem}) — "
                f"a natural attraction layer — but a breaking stem "
                f"({'/'.join(broken_in_a + broken_in_b) or '—'}) partially dissolves the 합. "
                "The bond is present but moderated; the rest of the chart has to carry more weight."
            )
    else:
        narrative = (
            f"The two Day Masters form {korean_name}, combining into {combined_elem}. "
            "Classical 적천수 commentary lists this as a primary spouse indicator — "
            "a strong magnetic layer without breaking interference. "
            "[UNCERTAIN: 명리정종 strict view requires in-season proof for full 합화; "
            "modern Korean Myeongri (권인성·송기영) treats any 합 as meaningful.]"
        )

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["daystem_combo"],
        narrative=narrative,
        flags=flags,
    )


# ── Sub-system B · Day-branch interaction (일지 합·충·형·파·해) ────────────

def _branch_pair_lookup(
    b1: str, b2: str, table: Sequence[Tuple[str, ...]]
) -> bool:
    """Return True if (b1, b2) matches the first two columns of a `table` row.

    The related-branch tables in `lookup` are deliberately not uniformly
    shaped. SIX_CLASHES / SIX_HARMS / SIX_BREAKS are plain (branch, branch)
    pairs, but SIX_COMBINATIONS is (branch, branch, combined_element) --
    the third column is the element the 六合 produces, per
    knowledge/02-branches.md (see lookup.py:305).

    Testing the pair against whole rows therefore matched 충/해/파 but could
    never match 육합, which left every 육합 branch unreachable at
    compat.py:310 (+4), :407 (spouse palace +20), :428 (반합 suppression) and
    :1343 (띠 +3) -- the engine reported "no direct 합/충" for pairs the
    classical sources treat as the strongest favorable indicator in 궁합.

    Matching only the branch columns makes this shape-agnostic, which is the
    contract all four call sites already assume. Chain order is unchanged.
    """
    return any(tuple(row[:2]) in ((b1, b2), (b2, b1)) for row in table)


def _three_harmony_match(b1: str, b2: str) -> Optional[Tuple[str, str]]:
    """If both branches are distinct and in the same 삼합 frame, return (frame_label, element)."""
    if b1 == b2:
        return None
    for triple in L.THREE_HARMONIES:
        a, b, c, element = triple
        if b1 in (a, b, c) and b2 in (a, b, c):
            return (f"{a}{b}{c}", element)
    return None


def _pairwise_three_punishment(b1: str, b2: str) -> Optional[str]:
    """Return a label if two distinct branches form a pairwise 삼형 / 자형."""
    if b1 == b2:
        if b1 in L.SELF_PUNISHMENTS:
            return f"자형 {b1}{b1}"
        return None
    for triple in L.THREE_PUNISHMENTS:
        a, b, c, _label = triple
        # Some frames use a placeholder (—) for the third member.
        members = {x for x in (a, b, c) if x != "—"}
        if b1 in members and b2 in members:
            return f"삼형 {b1}{b2}"
    return None


def _cross_branch_score(b1: str, b2: str) -> Tuple[int, Optional[str]]:
    """Score a single cross-chart branch pair (day vs non-day).

    Returns (delta, flag_label) or (0, None). Implements 합/충/해/파/형/반합
    at half the primary day-to-day weights per knowledge/11-gunghap.md §B7.
    """
    if _branch_pair_lookup(b1, b2, L.SIX_COMBINATIONS):
        return 4, f"육합 {b1}{b2}"
    if _branch_pair_lookup(b1, b2, L.SIX_CLASHES):
        return -5, f"육충 {b1}{b2}"
    if _branch_pair_lookup(b1, b2, L.SIX_HARMS):
        return -1, f"육해 {b1}{b2}"
    if _branch_pair_lookup(b1, b2, L.SIX_BREAKS):
        return -1, f"육파 {b1}{b2}"
    pun = _pairwise_three_punishment(b1, b2)
    if pun:
        return -2, pun
    th = _three_harmony_match(b1, b2)
    if th:
        return 2, f"반합 {th[0]} ({th[1]})"
    return 0, None


def _classify_flag(flag: str) -> Optional[str]:
    """Classify a single sub-system flag as 'red', 'yellow', 'favorable', or None.

    Uses multi-character/classical tokens to avoid naive single-char substring
    misclassification (e.g. "충" inside "충분" must not be treated as a clash).
    Order matters: favorable patterns are checked before yellow ones because a
    few flags (e.g. spouse-palace 역마 in day branch) carry a favorable form of
    a token that is otherwise a yellow flag.
    """
    # Red flags: hard clashes, broken combinations, or severe caution patterns.
    if any(token in flag for token in ["RED FLAG", "육충", "상충", "자형", "간섭", "홍양교차"]):
        return "red"
    # Favorable patterns: combinations, supply, noble star, aligned spouse
    # star, 용신/희신 matches, and 대운 direction harmony.
    if any(
        token in flag
        for token in [
            "천간합",
            "육합",
            "반합",
            "공급",
            "양호",
            "상합",
            "상구",
            "귀인배우",
            "천을",
            "역마 in spouse palace",
            "용신",
            "희신",
            "대운 방향",
            "배우자 지표",
            "재성 일치",
            "관성 일치",
            "용신 일치",
            "희신 일치",
        ]
    ):
        return "favorable"
    # Yellow flags: soft friction, dual negative stars, gishin exposure,
    # missing/over-dominant elements, and the unfavorable form of dual stars.
    if any(
        token in flag
        for token in [
            "육해",
            "육파",
            "삼형",
            "기신",
            "상해",
            "쌍도화",
            "쌍화개",
            "쌍양인",
            "쌍역마",
            "쌍홍염",
            "홍염",
            "양인",
            "불균형",
            "과다",
            "결핍",
        ]
    ):
        return "yellow"
    return None


def compat_daybranch(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system B: Day-branch relationship — the heart of 궁합.

    Weight = 30 (highest). Day-to-day interaction is primary; cross-chart
    branch relationships are secondary at half weight, capped to prevent
    over-counting.
    """
    label = "Day-branch interaction (spouse palaces)"
    label_kr = "일지 합충형파해 (배우자궁)"
    b1, b2 = a.day.branch, b.day.branch
    flags: List[str] = []

    # Primary day-to-day scoring.
    primary_score = 0
    primary_narrative_parts: List[str] = []

    if _branch_pair_lookup(b1, b2, L.SIX_COMBINATIONS):
        primary_score += 20
        flags.append(f"일지 육합 {b1}{b2}")
        primary_narrative_parts.append(
            f"the two spouse palaces form 육합 ({b1}{b2}) — the strongest "
            "favorable indicator in classical 궁합"
        )
    elif _branch_pair_lookup(b1, b2, L.SIX_CLASHES):
        primary_score -= 25
        flags.append(f"일지 육충 {b1}{b2} (RED FLAG)")
        primary_narrative_parts.append(
            f"the two spouse palaces are in direct 충 ({b1}{b2}) — a hard red flag "
            "in classical 적천수 commentary; KCI 2018 divorce study confirms high correlation"
        )
    else:
        primary_narrative_parts.append(
            f"the two spouse palaces ({b1} and {b2}) have no direct 합/충"
        )

    # Three-harmony partial.
    th = _three_harmony_match(b1, b2)
    if th and not _branch_pair_lookup(b1, b2, L.SIX_COMBINATIONS):
        primary_score += 8
        flags.append(f"일지 반합 {th[0]} ({th[1]})")
        primary_narrative_parts.append(
            f"the two spouse palaces are two-of-three in the {th[0]} 삼합 frame "
            f"({th[1]}) — partial harmony"
        )

    # Self-punishment (자형) — both branches in {辰,午,酉,亥}.
    if b1 == b2 and b1 in L.SELF_PUNISHMENTS:
        primary_score -= 8
        flags.append(f"일지 자형 {b1}{b1}")
        primary_narrative_parts.append(
            f"both spouse palaces are {b1} (자형 self-punishment) — 'double-down' "
            "amplifies inner-torment pattern"
        )

    # Harm (해) and break (파) — softer flags.
    if _branch_pair_lookup(b1, b2, L.SIX_HARMS):
        primary_score -= 5
        flags.append(f"일지 해 {b1}{b2}")
    if _branch_pair_lookup(b1, b2, L.SIX_BREAKS):
        primary_score -= 3
        flags.append(f"일지 파 {b1}{b2}")

    # Cross-chart secondary (half weight per pair, capped at ±15 to avoid runaway).
    # Score A's day-branch against B's month/year/hour, and B's day-branch
    # against A's month/year/hour. Each partner's spouse palace is read against
    # the other's non-spouse palaces. Implements 합/충/형/파/해/반합 per
    # knowledge/11-gunghap.md §B7.
    secondary_score = 0
    secondary_count = 0
    day_b = b.day.branch
    for branch_b in [b.year.branch, b.month.branch, b.hour.branch]:
        if branch_b == day_b:
            continue  # already counted as primary
        secondary_count += 1
        delta, flag = _cross_branch_score(b1, branch_b)
        if flag:
            secondary_score += delta
            flags.append(f"A일지·B지지 {flag}")

    # Reverse direction: B's day branch vs A's non-day branches.
    day_a = a.day.branch
    for branch_a in [a.year.branch, a.month.branch, a.hour.branch]:
        if branch_a == day_a:
            continue
        secondary_count += 1
        delta, flag = _cross_branch_score(b2, branch_a)
        if flag:
            secondary_score += delta
            flags.append(f"B일지·A지지 {flag}")

    secondary_score = max(-15, min(15, secondary_score))

    total = max(-30, min(30, primary_score + secondary_score))

    # Build narrative.
    narr = (
        "Day-branch interaction (일지 합충) is the **heart of classical 궁합**. "
        + "; ".join(primary_narrative_parts)
        + "."
    )
    if secondary_count and secondary_score:
        narr += (
            f" Cross-chart branch interactions add a secondary layer "
            f"(net {secondary_score:+d}, capped at ±15)."
        )

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=total, max=WEIGHT["daybranch"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system C · Nayin (납음오행) ─────────────────────────────────────────

# Subject canonicalization for the ordered 30×30 Nayin table (C8 fix). The
# 서전구미록 table is *ordered* — each ordered cell stores one of six
# direction-bearing relationship types (A generates B → 상합; B generates A →
# 상구), so *which* direction is read is part of the reading, not an accident of
# the call. The engine's defect was letting the *caller's argument order* supply
# that axis, so `compat_score(a, b)` and `compat_score(b, a)` returned two
# different scores — and, measured, two different bands — for one relationship.
#
# The direction is now a property of the couple, resolved to the product's own
# canonical partner order (CLAUDE.md: "The full canonical order is preserved as
# given; for heterosexual pairs Partner A is the male"):
#
#   * genders known and opposite → the male partner is the subject;
#   * otherwise                  → the lower NAYIN_ORDER index is the subject.
#
# The index tiebreak is a *stability rule* for the unknown- or same-gender case,
# not a classical claim: it exists so the verdict is a function of the pair
# alone. This mirrors _gendered_spouse_star_note() below, which keys the §G
# spouse-star mapping on gender the same way and declines the gendered read when
# gender is unknown. It is a NO-OP for every already-canonical (male-first) call,
# so no published deliverable moves. See knowledge/11-gunghap.md §C — "Canonical
# subject order".
_NAYIN_INDEX: Dict[str, int] = {_n: _i for _i, _n in enumerate(NAYIN_ORDER)}


def _canonical_nayin_pair(
    a: Chart, b: Chart, nayin_a: str, nayin_b: str
) -> Tuple[str, str]:
    """Return (na, nb) in the engine's canonical subject order.

    Both call orders of a given couple resolve to ONE ordered pair, so the Nayin
    relation — and therefore the sub-system score and the composite — is a
    function of the couple rather than of the argument order.
    """
    ga, gb = a.gender, b.gender
    if ga and gb and ga != gb:
        return (nayin_a, nayin_b) if ga == "M" else (nayin_b, nayin_a)
    ia, ib = _NAYIN_INDEX.get(nayin_a), _NAYIN_INDEX.get(nayin_b)
    if ia is None or ib is None:
        return nayin_a, nayin_b  # unknown Nayin name — defensive, leave as given
    return (nayin_a, nayin_b) if ia <= ib else (nayin_b, nayin_a)


def compat_nayin(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system C: Nayin compatibility per 서전구미록 6-relationship table."""
    label = "Nayin harmony"
    label_kr = "납음오행 (納音五行)"
    nayin_a = nayin_of(a.day.stem, a.day.branch)
    nayin_b = nayin_of(b.day.stem, b.day.branch)
    flags: List[str] = []

    if not nayin_a or not nayin_b:
        return CompatSubResult(
            label=label, label_kr=label_kr,
            score=0, max=WEIGHT["nayin"],
            narrative="Nayin classification unavailable for one of the day pillars.",
        )

    # Resolve the direction from the COUPLE, not from the call order, and read
    # (and display) the relation in that canonical order — the six relationship
    # labels name which element generates/overcomes which, so computing on one
    # order while printing another would assert a wrong direction.
    na, nb = _canonical_nayin_pair(a, b, nayin_a, nayin_b)
    rel, delta, source_tag = nayin_relation_detail(na, nb)

    # Map the six relationship types to the sub-system's ±5 weight budget.
    # The raw delta from the table is kept for reference; the score is the
    # normalized contribution used in the composite total.
    _score_map = {
        "상합": 5,
        "상구": 3,
        "상대": 1,
        "neutral": 0,
        "상해": -3,
        "상충": -5,
    }
    score = _score_map.get(rel, 0)

    flag = f"납음 {na} vs {nb} → {rel}"
    if source_tag == "element-grammar-fallback":
        flag += " [element-grammar-fallback]"
    flags.append(flag)

    fallback_note = ""
    if source_tag == "element-grammar-fallback":
        fallback_note = (
            " The 30×30 pair-specific 서전구미록 table is not yet sourced; "
            "this verdict uses the documented 5-element grammar as a fallback."
        )

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["nayin"],
        narrative=(
            f"The two day pillars carry the Nayin tones {na} and {nb} "
            f"({rel}). In classical 서전구미록 commentary this is a soft "
            "'deep-tone' indicator — neither a red flag nor a primary factor, "
            "but it colors the relationship's underlying feel."
            f"{fallback_note}"
        ),
        flags=flags,
    )


# ── Sub-system D · Yongshin (용신) cross-supply ──────────────────────────────

def _element_strength(chart: Chart) -> Dict[str, float]:
    """Return a percent distribution of elements (0–100 each) for `chart`.

    Weights follow knowledge/11-gunghap.md §F: visible stems = 1; hidden stems
    main=1, middle=0.5, residual=0.3.
    """
    counts: Dict[str, float] = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    for s in chart.stems:
        counts[L.STEM_INFO[s]["element"]] += 1.0
    for b in chart.branches:
        hidden = L.HIDDEN_STEMS.get(b, {})
        for role, s in hidden.items():
            weight = {"main": 1.0, "middle": 0.5, "residual": 0.3}.get(role, 0.0)
            if weight:
                counts[L.STEM_INFO[s]["element"]] += weight
    total = sum(counts.values()) or 1
    return {e: v / total * 100 for e, v in counts.items()}


def compat_yongshin(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system D: Cross-용신 and mutual-gishin test.

    Sub-weight 12/100. F (combined element balance) is kept as a descriptive
    sub-system; the active scoring for 용신 alignment lives here per the spec.
    """
    label = "Favorable element cross-supply"
    label_kr = "용신 궁합 (用神 宮合)"
    fav_a = _resolved_favorable(a)
    fav_b = _resolved_favorable(b)
    gish_a = _resolved_unfavorable(a)
    gish_b = _resolved_unfavorable(b)

    flags: List[str] = []
    score = 0

    if fav_a and fav_b:
        # Cross-need: does B's chart supply A's 용신, and vice versa?
        b_dist = _element_strength(b)
        a_dist = _element_strength(a)
        a_need = b_dist.get(fav_a, 0)
        b_need = a_dist.get(fav_b, 0)
        if a_need >= 15:
            score += 6
            flags.append(f"B → A 용신 {fav_a} 공급 양호 ({a_need:.0f}%)")
        elif a_need >= 5:
            score += 3
            flags.append(f"B → A 용신 {fav_a} 일부 공급 ({a_need:.0f}%)")
        if b_need >= 15:
            score += 6
            flags.append(f"A → B 용신 {fav_b} 공급 양호 ({b_need:.0f}%)")
        elif b_need >= 5:
            score += 3
            flags.append(f"A → B 용신 {fav_b} 일부 공급 ({b_need:.0f}%)")

    # Mutual-gishin penalty.
    if gish_a and gish_b:
        a_dist = _element_strength(a)
        b_dist = _element_strength(b)
        # gish_in_a = amount of A's gishin element present in B's chart.
        # gish_in_b = amount of B's gishin element present in A's chart.
        gish_in_a = b_dist.get(gish_a, 0)
        gish_in_b = a_dist.get(gish_b, 0)
        if gish_in_a >= 20:
            score -= 4
            flags.append(f"B에 A의 기신 {gish_a} 과다 ({gish_in_a:.0f}%)")
        if gish_in_b >= 20:
            score -= 4
            flags.append(f"A에 B의 기신 {gish_b} 과다 ({gish_in_b:.0f}%)")

    narr = (
        "용신 cross-supply is the **궁통보감 deciding factor**: does each "
        "partner's chart carry the element the other needs? "
    )
    if score > 6:
        narr += (
            "Both partners bring meaningful supply of the other's favorable element. "
            "This is a structural complementarity — '서로 용신이 되는' reading."
        )
    elif score > 0:
        narr += "Partial cross-supply exists; one partner brings more than the other."
    elif score == 0 and (fav_a and fav_b):
        narr += "Neither chart strongly supplies the other's 용신; the relationship leans on other factors."
    elif score < 0:
        narr += "Mutual gishin exposure — one or both charts carry what the other should avoid. Conscious work needed."
    else:
        narr += "Favorable element data unavailable for one or both charts."

    narr += (
        " [UNCERTAIN: 궁통보감 treats 용신 alignment as the deciding factor; "
        "적천수 weights it equal with 일지 궁 interaction; modern Korean "
        "Myeongri consensus is ~12/100.]"
    )

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["yongshin"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system E · 일주 pair classification (60 jiazi day-pillar pairs) ────

# Strong spouse-palace day pillars (knowledge/11-gunghap.md Table E2).
_STRONG_SPOUSE_PALACE: Dict[str, str] = {
    "甲子": "Yang wood rooted in deep water",
    "丙寅": "Sun rising in spring",
    "戊辰": "Mountain earth",
    "庚午": "Sword in refining fire",
    "壬申": "Great river in metal source",
    "丁卯": "Candle with wood",
    "己未": "Garden earth",
    "辛酉": "Jewel in jewel",
    "癸亥": "Dew in deep water",
}

# Weak spouse-palace day pillars (knowledge/11-gunghap.md Table E3).
_WEAK_SPOUSE_PALACE: Dict[str, str] = {
    "甲申": "Wood in metal — easily wounded",
    "丙午": "Sun at peak — strong partner conflicts",
    "庚子": "Metal in water — eroded by partner",
    "壬寅": "Water in wood — absorbed by partner",
    "戊戌": "Mountain earth vs mountain",
}


# Good day-pillar pairs (Table E4).
_GOOD_PAIRS: Dict[frozenset, str] = {
    frozenset(["甲子", "己丑"]): "천생 부부 (heaven-made couple) — 1순위",
    frozenset(["乙亥", "甲午"]): "따뜻한 결합 (warm combination)",
    frozenset(["丙寅", "辛酉"]): "정열적 결합 (passionate)",
    frozenset(["丁卯", "壬寅"]): "성장 결합 (growth)",
    frozenset(["戊辰", "癸未"]): "안정적 결합 (stable)",
    frozenset(["己巳", "甲戌"]): "균형 잡힌 결합 (balanced)",
    frozenset(["庚午", "乙丑"]): "정밀한 결합 (precise)",
    frozenset(["辛未", "丙子"]): "따뜻한 결합 (warm)",
    frozenset(["壬申", "丁巳"]): "용과 봉황 결합 (dragon-phoenix)",
    frozenset(["癸酉", "戊寅"]): "잠재력 결합 (potential)",
}

# Challenging pairs (Table E5).
_CHALLENGING_PAIRS: Dict[frozenset, str] = {
    frozenset(["甲子", "庚午"]): "일지 子午충 — RED FLAG",
    frozenset(["乙丑", "辛未"]): "일지 丑未충 — RED FLAG",
    frozenset(["丙寅", "壬申"]): "일지 寅申충 — RED FLAG",
    frozenset(["丁卯", "癸酉"]): "일지 卯酉충 — RED FLAG",
    frozenset(["戊辰", "甲戌"]): "일지 辰戌충 — RED FLAG",
    frozenset(["己巳", "乙亥"]): "일지 巳亥충 — RED FLAG",
}


def _spouse_palace_virtue(chart: Chart) -> Tuple[int, List[str]]:
    """Score the day-branch hidden-stem element against 용신/희신/기신.

    Returns (score_delta, flags). 적천수 원칙: 일지 본기 오행이 용신이면 +3,
    희신이면 +2, 기신이면 −3.
    """
    fav = _resolved_favorable(chart)
    gish = _resolved_unfavorable(chart)
    hee = _resolved_supporting(chart)
    main_hidden = L.HIDDEN_STEMS.get(chart.day.branch, {}).get("main")
    if not main_hidden or not fav:
        return (0, [])
    try:
        elem = L.STEM_INFO[main_hidden]["element"]
    except Exception:
        return (0, [])
    tg = L.ten_god(chart.day.stem, main_hidden)
    flags = [f"일지 본기 {main_hidden} → {tg} ({elem})"]
    if elem == fav:
        return (3, flags + ["배우자 복덕 (용신 일치)"])
    if elem == hee:
        return (2, flags + ["배우자 복덕 (희신 일치)"])
    if elem == gish:
        return (-3, flags + ["배우자 복덕 (기신 일치)"])
    return (0, flags)


def compat_ilju_pair(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system E: Day-pillar pair classification (60 jiazi)."""
    label = "Day-pillar pair classification"
    label_kr = "일주 궁합 (日柱 宮合)"
    pair_a = a.day.combined
    pair_b = b.day.combined
    pair_key = frozenset([pair_a, pair_b])
    flags: List[str] = []
    score = 0

    if pair_key in _GOOD_PAIRS:
        score += 8
        flags.append(f"{pair_a} + {pair_b} → {_GOOD_PAIRS[pair_key]}")
    if pair_key in _CHALLENGING_PAIRS:
        score -= 12
        flags.append(f"{pair_a} + {pair_b} → {_CHALLENGING_PAIRS[pair_key]}")

    # Spouse-palace strength checks (각 chart 독립).
    if pair_a in _STRONG_SPOUSE_PALACE:
        score += 3
        flags.append(f"{pair_a} 배우자궁 강함")
    elif pair_a in _WEAK_SPOUSE_PALACE:
        score -= 2
        flags.append(f"{pair_a} 배우자궁 약함")
    if pair_b in _STRONG_SPOUSE_PALACE:
        score += 3
        flags.append(f"{pair_b} 배우자궁 강함")
    elif pair_b in _WEAK_SPOUSE_PALACE:
        score -= 2
        flags.append(f"{pair_b} 배우자궁 약함")

    # Spouse virtue per partner (적천수 원칙).
    va, fla = _spouse_palace_virtue(a)
    vb, flb = _spouse_palace_virtue(b)
    score += va + vb
    flags.extend(fla)
    flags.extend(flb)

    # Clamp to the stated sub-system max; virtue/pair bonuses can stack.
    score = max(-WEIGHT["ilju_pair"], min(WEIGHT["ilju_pair"], score))

    narr = (
        "The two day pillars are "
        f"**{pair_a}** (Partner A) and **{pair_b}** (Partner B). "
    )
    if pair_key in _GOOD_PAIRS:
        narr += f"Classical lists this as a {_GOOD_PAIRS[pair_key]} pair. "
    if pair_key in _CHALLENGING_PAIRS:
        narr += f"Classical lists this as {_CHALLENGING_PAIRS[pair_key]}. "
    if not flags:
        narr += "No specific classical classification; falls into the general case. "
    narr += (
        "Each partner's spouse palace (day-branch 본기 hidden stem) is read against "
        "their own favorable element (적천수 principle). "
        "[UNCERTAIN: 권인성·곽임성 classification differs from 명리정종's gender-based "
        "spouse-star mapping; modern consensus uses the 용신 test.]"
    )

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["ilju_pair"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system F · Combined element balance ─────────────────────────────────

def compat_combined_elements(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system F: Sum of two charts' element distributions → union balance."""
    label = "Combined element balance"
    label_kr = "결합 오행 (結合 五行)"
    dist_a = _element_strength(a)
    dist_b = _element_strength(b)
    union = {e: (dist_a.get(e, 0) + dist_b.get(e, 0)) / 2 for e in dist_a}

    flags: List[str] = []
    score = 0

    # Missing-element flag.
    missing = [e for e, v in union.items() if v == 0]
    if missing:
        flags.append(f"결합에서 결핍: {missing}")

    # Over-dominant element.
    over = [e for e, v in union.items() if v > 30]
    if over:
        flags.append(f"결합 과다: {over}")

    # Deviation from ideal 20% per element (lower is better).
    ideal = 20.0
    deviation = sum(abs(v - ideal) for v in union.values()) / 2  # normalize
    if deviation < 8:
        score = 12  # very balanced
        flags.append("결합 오행 균형 양호")
    elif deviation < 15:
        score = 7
    elif deviation < 25:
        score = 2
    else:
        score = -4
        flags.append("결합 오행 불균형 심함")

    # Yongshin-union check: does each partner's 용신 appear in the union?
    sa = a.strength_assessment or {}
    sb = b.strength_assessment or {}
    fav_a = _resolved_favorable(a)
    fav_b = _resolved_favorable(b)
    if fav_a and union.get(fav_a, 0) >= 15:
        score += 2
        flags.append(f"A 용신 {fav_a} 결합에서 충분")
    if fav_b and union.get(fav_b, 0) >= 15:
        score += 2
        flags.append(f"B 용신 {fav_b} 결합에서 충분")

    # Cap at the stated sub-system max so the verdict table never shows >100%.
    score = max(-WEIGHT["combined_elements"], min(WEIGHT["combined_elements"], score))

    narr = (
        f"Combined element distribution (avg of both charts): "
        + ", ".join(f"{e}={v:.0f}%" for e, v in union.items())
        + ". "
    )
    if deviation < 8:
        narr += "The union is well-balanced across all five elements."
    elif missing:
        narr += f"The union is missing {missing}, which classical 명리 reads as a 결합 결핍."
    else:
        narr += "The union has some imbalance — over-dominant elements 'rule' the relationship."
    narr += (
        " 궁통보감 framing: one chart may be 寒 (cold), the other 熱 (hot) — "
        "complementary climates balance the union."
    )

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["combined_elements"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system G · Ten-god cross-relationship (십신 교차) ──────────────────

_TENGOD_GOOD_PAIRS: Dict[Tuple[str, str], str] = {
    ("정관", "정인"): "서로 신뢰·안정 — 가장 좋은 궁합 (best)",
    ("정재", "정관"): "따뜻한 부부 — 재물·안정·질서",
    ("식신", "정인"): "부드러운 부부 — 표현·보호",
    ("정관", "정재"): "사회적 부부 — 권위·안정",
}

_TENGOD_BAD_PAIRS: Dict[Tuple[str, str], str] = {
    ("편관", "편관"): "강렬한 부부 — 둘 다 압박적",
    ("상관", "상관"): "갈등 부부 — 둘 다 날카로움",
    ("겁재", "겁재"): "갈등 부부 — 둘 다 갈등",
}

# Spouse-star tags used by the 자평진전 gendered mapping in §G.
_WIFE_STARS = {"정재", "편재"}
_HUSBAND_STARS = {"정관", "편관"}


def _gendered_spouse_star_note(a: Chart, b: Chart, a_to_b: str, b_to_a: str) -> Tuple[int, List[str], List[str]]:
    """Apply 자평진전 gendered spouse-star mapping from knowledge/11-gunghap.md §G.

    Male → 재성 (wealth star) = wife indicator.
    Female → 관성 (officer star) = husband indicator.
    For same-sex pairs the classical gendered mapping is noted but not enforced.

    Returns a small score delta (+2 when the mapping aligns), plus flags and
    narrative fragments.
    """
    flags: List[str] = []
    narr: List[str] = []
    score = 0
    ga, gb = a.gender, b.gender
    if ga is None or gb is None:
        return score, flags, narr

    if ga == gb:
        narr.append(
            "Same-sex couple — the classical 자평진전 gendered spouse-star mapping "
            "(male→재성, female→관성) is not applied by polarity; read the 십신 "
            "pattern through 용신 and shared values instead."
        )
        return score, flags, narr

    # Heterosexual pair: enforce canonical order A=male, B=female per CLAUDE.md.
    # If the caller passed female first, we still read what each partner receives.
    # For a male, his spouse star is 재성 (wealth star), so we ask:
    #   "B is what 십신 of A?"  →  b_to_a.
    # For a female, her spouse star is 관성 (officer star), so we ask:
    #   "B is what 십신 of A?"  →  b_to_a.
    if ga == "M":
        if b_to_a in _WIFE_STARS:
            score += 2
            flags.append(f"A(남)의 배우자 지표 재성 일치: B는 A의 {b_to_a}")
    if gb == "M":
        if a_to_b in _WIFE_STARS:
            score += 2
            flags.append(f"B(남)의 배우자 지표 재성 일치: A는 B의 {a_to_b}")
    if ga == "F":
        if b_to_a in _HUSBAND_STARS:
            score += 2
            flags.append(f"A(여)의 배우자 지표 관성 일치: B는 A의 {b_to_a}")
    if gb == "F":
        if a_to_b in _HUSBAND_STARS:
            score += 2
            flags.append(f"B(여)의 배우자 지표 관성 일치: A는 B의 {a_to_b}")

    if score:
        narr.append(
            "The 자평진전 gendered spouse-star mapping aligns for at least one "
            "partner — a soft classical confirmation beyond the 용신 modifier."
        )
    return score, flags, narr


def compat_tengod_cross(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system G: 십신 cross-relationship (Partner A's day_stem as 십신 of B, etc.)."""
    label = "Ten-god cross-relationship"
    label_kr = "십신 교차 (十神 交叉)"
    s_a, s_b = a.day.stem, b.day.stem

    # A → B : A's day_stem seen as 십신 of B.
    try:
        a_to_b = L.ten_god(s_b, s_a)
    except Exception:
        a_to_b = "—"
    try:
        b_to_a = L.ten_god(s_a, s_b)
    except Exception:
        b_to_a = "—"

    flags: List[str] = []
    score = 0
    narr_parts: List[str] = []

    flags.append(f"A ({s_a})는 B ({s_b})의 {a_to_b}")
    flags.append(f"B ({s_b})는 A ({s_a})의 {b_to_a}")

    pair = (a_to_b, b_to_a)
    rev_pair = (b_to_a, a_to_b)
    # Order-insensitive lookup per knowledge/11-gunghap.md §G: the pair table
    # lists a canonical direction, but swapping A/B should not change the verdict.
    matched_pair = None
    if pair in _TENGOD_GOOD_PAIRS:
        matched_pair = pair
    elif rev_pair in _TENGOD_GOOD_PAIRS:
        matched_pair = rev_pair
    if matched_pair:
        score += 10
        narr_parts.append(
            f"A→B/B→A 십신 pattern ({a_to_b}/{b_to_a}) is classically favorable: "
            f"{_TENGOD_GOOD_PAIRS[matched_pair]}"
        )
    elif pair in _TENGOD_BAD_PAIRS or rev_pair in _TENGOD_BAD_PAIRS:
        bad_key = pair if pair in _TENGOD_BAD_PAIRS else rev_pair
        score -= 8
        narr_parts.append(
            f"A→B/B→A 십신 pattern ({a_to_b}/{b_to_a}) is a classical caution: "
            f"{_TENGOD_BAD_PAIRS[bad_key]}"
        )
    elif a_to_b == "비견" and b_to_a == "비견":
        # Same Day-Master stem (e.g. both 丙): the 'mirror' companion dynamic.
        narr_parts.append(
            f"A→B/B→A 십신 pattern is 비견/비견 (比肩/比肩) — both Day Masters "
            f"share the same stem ({s_a}). This is the mirror-companion dynamic: "
            "peer-energy, equals rather than complements. The classical table "
            "(§G) reads 비견배우 as 동등한 관계, 때로 경쟁 (an equal bond, "
            "sometimes competitive); the 권인성 school reads same-polarity "
            "unions as 편의 (familiar, easy) but at risk of going stale — a "
            "friendship-over-romance tendency where mutual competition surfaces "
            "when both reach for the same role. The classical offset is "
            "deliberate asymmetry: take turns leading and following so the "
            "bond does not flatten into a sibling dynamic. Base score is neutral "
            "(0); a 용신-element match between partners can lift it."
        )
    else:
        narr_parts.append(
            f"A→B 십신: {a_to_b}. B→A 십신: {b_to_a}. No specific classical "
            "pair-table verdict — read with the chart's 용신 modifier."
        )

    # Apply 용신 modifier (적천수): if the partner's day_stem IS my 용신
    # element-class, treat as favorable; if 기신, treat as caution.
    fav_a = _resolved_favorable(a)
    fav_b = _resolved_favorable(b)
    gish_a = _resolved_unfavorable(a)
    gish_b = _resolved_unfavorable(b)
    elem_a = L.STEM_INFO[s_a]["element"]
    elem_b = L.STEM_INFO[s_b]["element"]
    modifier = 0
    if fav_a and elem_b == fav_a:
        modifier += 3
        flags.append(f"B의 일간 원소 {elem_b} = A의 용신")
    if fav_b and elem_a == fav_b:
        modifier += 3
        flags.append(f"A의 일간 원소 {elem_a} = B의 용신")
    if gish_a and elem_b == gish_a:
        modifier -= 2
        flags.append(f"B의 일간 원소 {elem_b} = A의 기신 [주의]")
    if gish_b and elem_a == gish_b:
        modifier -= 2
        flags.append(f"A의 일간 원소 {elem_a} = B의 기신 [주의]")
    score += modifier

    if a_to_b == "비견" and b_to_a == "비견" and modifier:
        narr_parts.append(
            f"The 용신 modifier lifted the score by +{modifier}: the same-stem "
            "mirror is also an element-class match for at least one partner's "
            "favorable element."
        )

    # 자평진전 gendered spouse-star mapping (knowledge/11-gunghap.md §G Ground Rule 5).
    gender_score, gender_flags, gender_narr = _gendered_spouse_star_note(a, b, a_to_b, b_to_a)
    score += gender_score
    flags.extend(gender_flags)
    narr_parts.extend(gender_narr)

    # Cap at the stated sub-system max so bonuses never overflow the table.
    score = max(-WEIGHT["tengod_cross"], min(WEIGHT["tengod_cross"], score))

    narr = (
        "In 십신 cross-reading, each partner is classified as a specific 십신 of the "
        "other's Day Master. "
        + " ".join(narr_parts)
        + " [UNCERTAIN: 권인성·송기영 uses the fixed pair table above; "
        "적천수 overrides with 용신 여부 (gender-agnostic); 자평진전 adds "
        "gendered spouse-star mapping for heterosexual pairs.]"
    )

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["tengod_cross"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system H · Daeun sync ───────────────────────────────────────────────

def compat_daeun_sync(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system H: Direction similarity + starting-element similarity.

    Static, time-invariant. For time-bound queries use the separate
    `compat_daeun_sync_at_year()` API (planned for v2).
    """
    label = "Major luck synchrony"
    label_kr = "대운·세운 동기 (大運·歲運 同期)"
    score = 0
    flags: List[str] = []
    if not a.daeun or not b.daeun:
        return CompatSubResult(
            label=label, label_kr=label_kr,
            score=0, max=WEIGHT["daeun_sync"],
            narrative="Daeun data unavailable for one or both charts.",
        )

    if a.gender is None or b.gender is None:
        return CompatSubResult(
            label=label, label_kr=label_kr,
            score=0, max=WEIGHT["daeun_sync"],
            narrative="Gender unknown for one or both charts; Daeun direction comparison skipped.",
            flags=["gender unknown — Daeun direction skipped"],
        )

    dir_a = L.daeun_direction(a.year.stem, a.gender)
    dir_b = L.daeun_direction(b.year.stem, b.gender)
    if dir_a == dir_b:
        score += 3
        flags.append(f"대운 방향 동일 ({dir_a})")
    else:
        flags.append(f"대운 방향 상이 ({dir_a} vs {dir_b})")

    # Starting-element similarity.
    start_a = a.daeun[0].stem if hasattr(a.daeun[0], "stem") else None
    start_b = b.daeun[0].stem if hasattr(b.daeun[0], "stem") else None
    if start_a and start_b:
        ea = L.STEM_INFO[start_a]["element"]
        eb = L.STEM_INFO[start_b]["element"]
        if ea == eb:
            score += 2
            flags.append(f"시작 대운 원소 동일 ({ea})")
        elif L.GENERATES.get(ea) == eb or L.GENERATES.get(eb) == ea:
            score += 1
            flags.append(f"시작 대운 상생 ({ea}↔{eb})")

    narr = (
        f"Daeun directions: A = {dir_a}, B = {dir_b}. "
        + ("Same direction means major life-stage transitions happen in parallel — "
           "the couple walks through similar life-cycle phases." if dir_a == dir_b
           else "Different directions mean major life-stage transitions often diverge in timing.")
        + " Time-bound commentary for a specific year should use a separate 세운 overlay."
    )
    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["daeun_sync"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system I · Compatibility star overlays ─────────────────────────────

def compat_stars(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system I: Cross-star patterns (도화·역마·화개·천을귀인·홍염·양인)."""
    label = "Compatibility star overlays"
    label_kr = "신살 궁합 (神殺 宮合)"
    sa = a.stars or {}
    sb = b.stars or {}
    score = 0
    flags: List[str] = []

    peach_a = set(sa.get("peach_blossom", []))
    peach_b = set(sb.get("peach_blossom", []))
    horse_a = set(sa.get("post_horse", []))
    horse_b = set(sb.get("post_horse", []))
    canopy_a = set(sa.get("canopy", []))
    canopy_b = set(sb.get("canopy", []))
    noble_a = set(sa.get("heavenly_noble", []))
    noble_b = set(sb.get("heavenly_noble", []))
    hy_a = set(sa.get("hongyeom", []))
    hy_b = set(sb.get("hongyeom", []))
    ya_a = set(sa.get("yangin", []))
    ya_b = set(sb.get("yangin", []))

    # Cross patterns.
    if peach_a and peach_b:
        score -= 3
        flags.append("쌍도화 — both have 도화 present")
    if a.day.branch in peach_b or b.day.branch in peach_a:
        score -= 5
        flags.append("도화스쳐 — 도화 hits spouse palace")
    # 쌍역마: +2 when both have 역마 in the spouse palace (day branch) and the
    # yang partner's career benefits from movement; -2 otherwise (parallel but
    # peripatetic lives). Per knowledge/11-gunghap.md §I table.
    if a.day.branch in horse_a and b.day.branch in horse_b:
        score += 2
        flags.append("쌍역마 — both have 역마 in spouse palace; yang partner's career benefits")
    elif horse_a and horse_b:
        score -= 2
        flags.append("쌍역마 — both have 역마 but not anchored in spouse palace; parallel travel lives")
    if a.day.branch in noble_b or b.day.branch in noble_a:
        score += 5
        flags.append("귀인배우 — partner is my 천을")
    if canopy_a and canopy_b:
        score -= 2
        flags.append("쌍화개 — both have 화개")
    if ya_a and ya_b:
        score -= 3
        flags.append("쌍양인 — both have 양인")
    if hy_a and hy_b:
        score -= 3
        flags.append("쌍홍염 — both have 홍염")
    if (hy_a and ya_b) or (ya_a and hy_b):
        score -= 5
        flags.append("홍양교차 — classical caution pattern")

    narr = (
        "Cross-star overlays are **descriptive**, not primary factors. "
        "도화 cross patterns suggest magnetic attraction but caution against "
        "exclusivity issues; 역마 dual-presence suggests parallel but peripatetic "
        "lives; 화개 dual suggests a tendency to grow apart emotionally. "
        "천을 in the partner's day branch is the most favorable cross-star pattern."
    )
    if score > 0:
        narr += " Net positive cross-star signature."
    elif score < 0:
        narr += " Net yellow-flag cross-star signature."
    else:
        narr += " No significant cross-star signature."

    # Clamp to the stated sub-system max so the verdict table never overflows.
    score = max(-WEIGHT["compat_stars"], min(WEIGHT["compat_stars"], score))

    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["compat_stars"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system J · Yin-Yang polarity ────────────────────────────────────────

def compat_yin_yang(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system J: Day-Master polarity match + union polarity balance."""
    label = "Yin-Yang polarity"
    label_kr = "음양 조화 (陰陽 調和)"
    pa = L.STEM_INFO[a.day.stem]["polarity"]
    pb = L.STEM_INFO[b.day.stem]["polarity"]
    flags: List[str] = []
    score = 0
    if pa != pb:
        score += 3
        flags.append(f"일간 음양 상보 ({pa} ↔ {pb})")
    else:
        score -= 1
        flags.append(f"일간 음양 동일 ({pa}/{pb})")

    # Union polarity balance (count all stems + branches).
    union_yang = 0
    union_yin = 0
    for s in a.stems + b.stems:
        if L.STEM_INFO[s]["polarity"] == "Yang":
            union_yang += 1
        else:
            union_yin += 1
    for b1 in a.branches + b.branches:
        if L.BRANCH_INFO[b1]["polarity"] == "Yang":
            union_yang += 1
        else:
            union_yin += 1
    total = union_yang + union_yin or 1
    yg_pct = union_yang / total * 100
    if 40 <= yg_pct <= 60:
        flags.append(f"결합 음양 균형 양호 ({yg_pct:.0f}% 양)")
        # no score change beyond Day-Master polarity
    else:
        flags.append(f"결합 음양 불균형 ({yg_pct:.0f}% 양)")
        score -= 1

    narr = (
        f"Day Masters: A={pa}, B={pb}. "
        + ("Opposite polarity — complementary dynamic." if pa != pb
           else "Same polarity — similar wavelength, can drift into complacency.")
        + f" Union polarity balance: {yg_pct:.0f}% Yang. "
        + "[UNCERTAIN: 적천수 uses 8-stem polarity balance; modern Korean reads day-to-day polarity as primary.]"
    )
    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["yin_yang"],
        narrative=narr,
        flags=flags,
    )


# ── Sub-system K · Year-branch zodiac pair (띠 궁합) ────────────────────────

def compat_year_branch(a: Chart, b: Chart) -> CompatSubResult:
    """Sub-system K: 띠 궁합 — folk-layer opener, capped at 3 weight."""
    label = "Year-branch zodiac pair (띠)"
    label_kr = "띠 궁합 (支 宮合)"
    b1, b2 = a.year.branch, b.year.branch
    score = 0
    flags: List[str] = []
    if _branch_pair_lookup(b1, b2, L.SIX_COMBINATIONS):
        score = 3
        flags.append(f"띠 육합 {b1}{b2}")
    elif _branch_pair_lookup(b1, b2, L.SIX_CLASHES):
        score = -3
        flags.append(f"띠 육충 {b1}{b2}")
    elif _three_harmony_match(b1, b2):
        th = _three_harmony_match(b1, b2)
        score = 2
        flags.append(f"띠 반합 {th[0]}")
    else:
        score = 0
    narr = (
        f"Year-branch pair ({b1}/{b2}) — the zodiac-sign layer of 궁합. It is the "
        "lightest signal in the reading: a useful intuitive opener, never a verdict. "
        "Modern Korean 명리 weights it at most 3 of 100; popular fortune sites tend to "
        "over-emphasise it. [UNCERTAIN: schools differ on the exact weight.]"
    )
    return CompatSubResult(
        label=label, label_kr=label_kr,
        score=score, max=WEIGHT["year_branch"],
        narrative=narr,
        flags=flags,
    )


# ── Orchestrator ─────────────────────────────────────────────────────────────

def compat_score(
    a: Chart,
    b: Chart,
    favorable_element_a: Optional[str] = None,
    favorable_element_b: Optional[str] = None,
) -> CompatReport:
    """Compute the full CompatReport for two charts.

    Returns the composite score (0–100) plus all 11 sub-system results and
    the top 3 red flags and favorable points for the report cover.

    ``favorable_element_a`` / ``favorable_element_b`` override the resolved
    용신 (see ``yongsin.favorable_element()``) when a human reader has already
    argued a specific favorable element for one or both charts. The override
    is stored as ``strength_assessment["reader_override_favorable"]``, which
    both this module's scoring helpers and ``favorable_element()`` treat as
    an outright win — so scoring and client-facing display never diverge.
    """
    # Apply optional 용신 overrides by operating on shallow copies so the input
    # Chart objects remain immutable from the caller's perspective (thread-safe).
    # Set as "reader_override_favorable" (not "candidate_favorable") so
    # yongsin.favorable_element() treats it as an outright reader override —
    # see yongsin.py's _reader_confirmed() — rather than raw engine input that
    # the climate merge (knowledge/17-climate-method.md) could otherwise
    # override again for a balanced chart born in a hot/cold month.
    if favorable_element_a and a.strength_assessment:
        a = copy(a)
        a.strength_assessment = deepcopy(a.strength_assessment)
        a.strength_assessment["reader_override_favorable"] = favorable_element_a
    if favorable_element_b and b.strength_assessment:
        b = copy(b)
        b.strength_assessment = deepcopy(b.strength_assessment)
        b.strength_assessment["reader_override_favorable"] = favorable_element_b

    subs = {
        "daystem_combo": compat_daystem_combo(a, b),
        "daybranch": compat_daybranch(a, b),
        "nayin": compat_nayin(a, b),
        "yongshin": compat_yongshin(a, b),
        "ilju_pair": compat_ilju_pair(a, b),
        "combined_elements": compat_combined_elements(a, b),
        "tengod_cross": compat_tengod_cross(a, b),
        "daeun_sync": compat_daeun_sync(a, b),
        "compat_stars": compat_stars(a, b),
        "yin_yang": compat_yin_yang(a, b),
        "year_branch": compat_year_branch(a, b),
    }
    # Sum all sub-systems except combined_elements, which is descriptive-only.
    # Per the spec, D+F together contribute 12 points; we score D and keep F
    # visible so the client sees the union element distribution without
    # double-counting the 용신 alignment in the composite.
    raw_total = sum(subs[k].score for k in subs if k != "combined_elements")
    # Weights sum to 100; raw_total can be negative or > 100 due to bonuses.
    # Normalize into 0–100.
    # Anchor: raw=0 → 50, raw=100 → 100, raw=-50 → 0. Linear.
    normalized = round(max(0, min(100, 50 + raw_total)))
    band = _band_for(normalized)

    # Collect flags: red = negative contributions; favorable = positive.
    red_flags: List[str] = []
    yellow_flags: List[str] = []
    favorable: List[str] = []
    for sub in subs.values():
        for flag in sub.flags:
            bucket = _classify_flag(flag)
            if bucket == "red":
                red_flags.append(f"{sub.label}: {flag}")
            elif bucket == "yellow":
                yellow_flags.append(f"{sub.label}: {flag}")
            elif bucket == "favorable":
                favorable.append(f"{sub.label}: {flag}")

    # Top 3 of each.
    red_flags = sorted(set(red_flags))[:3]
    yellow_flags = sorted(set(yellow_flags))[:5]
    favorable = sorted(set(favorable))[:3]

    return CompatReport(
        score=normalized,
        band=band,
        chart_a=a,
        chart_b=b,
        daystem_combo=subs["daystem_combo"],
        daybranch=subs["daybranch"],
        nayin=subs["nayin"],
        yongshin=subs["yongshin"],
        ilju_pair=subs["ilju_pair"],
        combined_elements=subs["combined_elements"],
        tengod_cross=subs["tengod_cross"],
        daeun_sync=subs["daeun_sync"],
        compat_stars=subs["compat_stars"],
        yin_yang=subs["yin_yang"],
        year_branch=subs["year_branch"],
        red_flags=red_flags,
        yellow_flags=yellow_flags,
        favorable_points=favorable,
    )
