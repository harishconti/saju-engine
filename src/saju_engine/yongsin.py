"""Single source of truth for a chart's favorable element (용신, 用神).

Both the natal premium report (``premium_report.py``) and the compatibility
report (``compat_report.py``) resolve the client-facing 용신 through
:func:`favorable_element`. This guarantees that the two products never disagree
for the same person, and that a reader who has argued a classical 용신 by hand
can pass it once as an ``override`` and have it flow to every product.

The engine's underlying heuristics live in two places:
  - ``strength.assess_strength`` (exposed on ``chart.strength_assessment``) —
    the 抑扶 (strength-balance) heuristic: strong DM → drain/control elements,
    weak DM → support elements, balanced DM → the numerically
    least-represented element as a fallback.
  - ``climate.assess_climate`` — the 조후 (climate-balance) cross-check: a
    chart peaking in summer heat wants Water, one peaking in winter cold
    wants Fire. See knowledge/17-climate-method.md.

This module *merges* the two. 2026-09-19 (user-approved product decision,
grounded in docs/research/2026-09-validation-climate.md §5): 조후 governs the
headline 용신 whenever the chart sits in a non-temperate climate band (hot,
cold, damp, or dry) — i.e. priority is gated on **climate extremeness**, not
on the 억부 strength verdict. This matches the sourced doctrine ("조후와
부억에는 명식을 떠난 고정 순서가 없습니다... 극단적 기후가 다른 기능을 막으면
조후가 전제가 된다" — OpenFate; "사주가 너무 차거나 너무 더우면 조후를 우선"
— 두루미사주) more closely than the previous verdict-gated rule, which had no
direct source support (see the same research doc §5, "그 전제는 뒷받침되지
않습니다"). For a temperate-month chart, 억부 stays authoritative, since 조후
has no opinion to offer. A reader override always wins outright over both
methods, unchanged. This module never invents a new derivation beyond that
merge.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from . import lookup as L
from .climate import assess_climate

# Strength verdict → the method label we expose to the reader/client, when
# climate does not override the headline (see favorable_element()).
_METHOD_BY_VERDICT = {
    "strong": "strong-dm-drain",
    "extreme": "strong-dm-drain",
    "weak": "weak-dm-support",
    "extreme_weak": "weak-dm-support",
    "balanced": "balanced-heuristic",
}

_NOTE_BY_METHOD = {
    "strong-dm-drain": (
        "The Day Master reads as strong, so the favorable element is the one that "
        "channels and expresses its excess. This is an engine reading — a full "
        "classical analysis may refine it."
    ),
    "weak-dm-support": (
        "The Day Master reads as weak, so the favorable element is the one that "
        "resources and steadies it. This is an engine reading — a full classical "
        "analysis may refine it."
    ),
    "balanced-heuristic": (
        "The chart is close to balanced, so the least-represented element is offered "
        "as a starting point only — it is a folk heuristic, not a classical ruling, and "
        "the final 용신 requires the reader's argument from temperature, season, and "
        "blockage."
    ),
    "reader-confirmed": (
        "Favorable element confirmed by the reader from the full classical analysis."
    ),
}

# Season label used in climate-related note text.
_SEASON_LABEL = {
    "hot": "hot summer",
    "cold": "cold winter",
    "damp": "damp earth-storage",
    "dry": "dry earth-storage",
}

# Prose label for the Day Master strength verdict, used only in the climate-
# governs branch below (the balanced-chart note has its own fixed wording).
_STRENGTH_LABEL = {
    "strong": "strong",
    "extreme": "strong",
    "weak": "weak",
    "extreme_weak": "weak",
}

# Inverse of the generating cycle: for each element, the element that generates it.
# Used as the strict-classical 희신 default for a reader override (Metal generates
# Water, Wood generates Fire, etc.) — see knowledge/03-five-elements.md.
_GENERATED_BY = {v: k for k, v in L.GENERATES.items()}

_VALID_ELEMENTS = {"Wood", "Fire", "Earth", "Metal", "Water"}


@dataclass(frozen=True)
class FavorableElement:
    """Resolved 용신 with provenance.

    Attributes:
        element: one of Wood / Fire / Earth / Metal / Water (or "—" if unknown).
        method: "strong-dm-drain" | "weak-dm-support" | "balanced-heuristic"
            | "climate-balanced" | "reader-confirmed".
        confidence: "heuristic" | "reader-confirmed".
        note: a client-safe one-sentence explanation of how this was derived.
        supporting: the 희신 (supporting element) that matches ``element`` —
            always the strict-classical generator of ``element`` except for
            the strong/weak 억부 methods, which use the modern Korean
            secondary-favorable convention (see strength.py).
        climate_band: "hot" | "cold" | "damp" | "dry" | "temperate" — the
            chart's 조후 band.
        climate_element: the classical climate-balancing element, or None for
            a temperate-month chart.
        climate_agrees: whether the climate element matches the raw 억부
            candidate_favorable, or None when the month is temperate.
    """

    element: str
    method: str
    confidence: str
    note: str
    supporting: str = "—"
    climate_band: str = "temperate"
    climate_element: Optional[str] = None
    climate_agrees: Optional[bool] = None
    # E-3/E-5 single resolution (2026-09-26): the rest of the five-role set,
    # resolved once here so every product reads the same values.
    unfavorable: Optional[str] = None   # 기신 (忌神)
    gusin: Optional[str] = None         # 구신 (仇神)
    hansin: Optional[str] = None        # 한신 (閑神)
    unfavorable_method: str = ""        # "dm-relative" | "derived-from-yongsin"
    requires_reader: bool = False       # True for the balanced folk heuristic


def _derive_from_yongsin(fav: str):
    """(기신, 구신, 한신) from a 용신 via the classical cycles
    (knowledge/03-five-elements.md worked example: 용신=Water → 기신=Fire,
    구신=Earth, 한신=Wood)."""
    if not fav or fav == "—":
        return None, None, None
    gisin = L.OVERCOMES.get(fav)
    gusin = next((k for k, v in L.OVERCOMES.items() if v == fav), None)
    hansin = L.GENERATES.get(fav)
    return gisin, gusin, hansin


def _with_unfavorable(fe: "FavorableElement", sa: dict) -> "FavorableElement":
    """Attach the resolved 기신/구신/한신 to ``fe``.

    Rule: for a pure 억부 resolution (strong/weak Day Master, temperate
    month, no reader override) the Day-Master-relative 기신 from
    strength.py stays authoritative — it is the 억부 method's own answer.
    Everywhere else (climate-resolved, balanced, reader-confirmed), and
    whenever the raw 기신 would collide with the resolved 용신/희신, 기신 is
    derived from the resolved 용신 so it can never contradict it. 구신/한신
    always follow the 용신 cycle. Before this, strength.py's raw
    ``candidate_unfavorable`` was read directly by compat scoring, the
    decade overlay, report_data and the compat report, while the natal
    report derived its own — two answers for one chart (E-3).
    """
    gisin, gusin, hansin = _derive_from_yongsin(fe.element)
    method = "derived-from-yongsin"
    raw = sa.get("candidate_unfavorable")
    if (
        fe.method in ("strong-dm-drain", "weak-dm-support")
        and raw
        and raw not in (fe.element, fe.supporting)
    ):
        gisin = raw
        method = "dm-relative"
    return replace(
        fe,
        unfavorable=gisin,
        gusin=gusin if gusin not in (fe.element, fe.supporting) else None,
        hansin=hansin if hansin not in (fe.element, fe.supporting) else None,
        unfavorable_method=method,
        requires_reader=fe.method == "balanced-heuristic",
    )


def _reader_confirmed(element: str) -> FavorableElement:
    """Build the outright-winning FavorableElement for any reader override,
    whether passed explicitly via ``override=`` or via a chart-level
    ``strength_assessment["reader_override_favorable"]`` (set by
    ``compat.py::compat_score``'s ``favorable_element_a``/``_b`` parameters)."""
    element = element.strip().capitalize()
    return FavorableElement(
        element=element,
        method="reader-confirmed",
        confidence="reader-confirmed",
        note=_NOTE_BY_METHOD["reader-confirmed"],
        supporting=_GENERATED_BY.get(element, "—"),
    )


def favorable_element(chart, override: Optional[str] = None) -> FavorableElement:
    """Resolve the favorable element (용신) for ``chart``.

    Args:
        chart: a computed ``Chart`` (must carry ``strength_assessment``).
        override: an element name a qualified reader has argued by hand. When
            given, it wins and ``confidence`` becomes ``"reader-confirmed"``.
            A chart-level ``strength_assessment["reader_override_favorable"]``
            (set by ``compat.py``'s override mechanism) wins the same way when
            no explicit ``override`` argument is given — this lets a single
            reader-argued value flow correctly through both compat scoring
            (which reads ``strength_assessment`` fields directly) and this
            resolver (used for display), without the two disagreeing.

    Returns:
        A :class:`FavorableElement`.
    """
    sa = getattr(chart, "strength_assessment", None) or {}
    if override:
        return _with_unfavorable(_reader_confirmed(override), sa)

    reader_override = sa.get("reader_override_favorable")
    if reader_override:
        return _with_unfavorable(_reader_confirmed(reader_override), sa)

    verdict = sa.get("verdict", "balanced")
    raw_favorable = sa.get("candidate_favorable") or "—"
    raw_supporting = sa.get("candidate_supporting") or "—"

    climate = assess_climate(sa.get("month_branch", ""))
    climate_element = climate["climate_favorable"]
    climate_agrees = (climate_element == raw_favorable) if climate_element else None
    season_label = _SEASON_LABEL.get(climate["band"])

    if climate_element:
        # 조후 governs the headline whenever the climate band is non-temperate
        # (hot/cold/damp/dry), regardless of the 억부 verdict — climate
        # extremeness is the sourced gate, not the strength verdict. See the
        # module docstring and docs/research/2026-09-validation-climate.md §5.
        element = climate_element
        supporting = climate["climate_supporting"]
        method = "climate-balanced"
        if climate_agrees:
            agreement_clause = (
                "This matches the chart's own least-represented element, reinforcing the pick."
            )
        elif verdict == "balanced":
            # Validation 2026-09-25 #6: the balanced-chart least-element pick
            # is a folk heuristic (E-5) — don't surface it by name in client
            # text, where it read as a rival 용신 candidate.
            agreement_clause = (
                "This takes priority over the chart's simple element count, which is a weaker "
                "signal than the classical climate check here."
            )
        else:
            agreement_clause = (
                f"This takes priority over the strength-balance (억부) pick ({raw_favorable})."
            )
        if verdict == "balanced":
            verdict_clause = "The Day Master reads as balanced, so the classical 조후 (climate-balance) check applies"
        else:
            strength_label = _STRENGTH_LABEL.get(verdict, verdict)
            verdict_clause = (
                f"The Day Master reads as {strength_label}, but the classical 조후 "
                "(climate-balance) check takes priority ahead of 억부 (strength-balance) here, "
                "because the chart's climate is extreme rather than mild"
            )
        note = (
            f"{verdict_clause}: this chart peaks in {season_label} conditions, and the classical "
            f"remedy is {climate_element}. {agreement_clause}"
        )
        return _with_unfavorable(FavorableElement(
            element=element, method=method, confidence="heuristic", note=note,
            supporting=supporting, climate_band=climate["band"],
            climate_element=climate_element, climate_agrees=climate_agrees,
        ), sa)

    # No climate opinion (temperate month): 억부 stays authoritative regardless
    # of verdict, since there is nothing for 조후 to govern with.
    element = raw_favorable
    supporting = raw_supporting
    method = _METHOD_BY_VERDICT.get(verdict, "balanced-heuristic")
    base_note = _NOTE_BY_METHOD[method]
    note = base_note + " Born in a climate-neutral month, so no 조후 override applies here."

    return _with_unfavorable(FavorableElement(
        element=element, method=method, confidence="heuristic", note=note,
        supporting=supporting, climate_band=climate["band"],
        climate_element=climate_element, climate_agrees=climate_agrees,
    ), sa)
