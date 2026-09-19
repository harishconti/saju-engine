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

This module *merges* the two: for a balanced verdict, 조후 is the classical
tie-breaker and wins the headline 용신 over the least-represented-element
fallback. For a strong/weak verdict, 억부 stays authoritative and 조후 is
surfaced only as a secondary note. A reader override always wins outright.
This module never invents a new derivation beyond that merge.
"""
from __future__ import annotations

from dataclasses import dataclass
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
        "as a starting point only. The final 용신 needs a classical reading of "
        "temperature, season, and blockage."
    ),
    "reader-confirmed": (
        "Favorable element confirmed by the reader from the full classical analysis."
    ),
}

# Season label used in climate-related note text.
_SEASON_LABEL = {"hot": "hot summer", "cold": "cold winter"}

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
        climate_band: "hot" | "cold" | "temperate" — the chart's 조후 band.
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
    if override:
        return _reader_confirmed(override)

    sa = getattr(chart, "strength_assessment", None) or {}

    reader_override = sa.get("reader_override_favorable")
    if reader_override:
        return _reader_confirmed(reader_override)

    verdict = sa.get("verdict", "balanced")
    raw_favorable = sa.get("candidate_favorable") or "—"
    raw_supporting = sa.get("candidate_supporting") or "—"

    climate = assess_climate(sa.get("month_branch", ""))
    climate_element = climate["climate_favorable"]
    climate_agrees = (climate_element == raw_favorable) if climate_element else None
    season_label = _SEASON_LABEL.get(climate["band"])

    if verdict == "balanced" and climate_element:
        # 조후 is the classical tie-breaker when 억부 gives no clear strong/weak signal.
        element = climate_element
        supporting = climate["climate_supporting"]
        method = "climate-balanced"
        if climate_agrees:
            agreement_clause = (
                "This matches the chart's own least-represented element, reinforcing the pick."
            )
        else:
            agreement_clause = (
                f"This overrides the numeric least-represented-element pick ({raw_favorable}), "
                "which is a weaker signal than the classical climate check for a balanced chart."
            )
        note = (
            "The Day Master reads as balanced, so the classical 조후 (climate-balance) check "
            f"applies: this chart peaks in {season_label} weather, and the classical remedy is "
            f"{climate_element}. {agreement_clause}"
        )
        return FavorableElement(
            element=element, method=method, confidence="heuristic", note=note,
            supporting=supporting, climate_band=climate["band"],
            climate_element=climate_element, climate_agrees=climate_agrees,
        )

    # Strong / weak / extreme_weak / extreme, OR a balanced chart born in a
    # climate-neutral (temperate) month: 억부 stays authoritative.
    element = raw_favorable
    supporting = raw_supporting
    method = _METHOD_BY_VERDICT.get(verdict, "balanced-heuristic")
    base_note = _NOTE_BY_METHOD[method]

    if verdict == "balanced":
        note = base_note + " Born in a climate-neutral month (spring/autumn), so no 조후 override applies here."
    elif climate_element:
        if climate_agrees:
            note = base_note + (
                f" (조후 cross-check: this chart's {season_label} climate also favors "
                f"{climate_element}, agreeing with the strength-based pick.)"
            )
        else:
            note = base_note + (
                f" (조후 cross-check: this chart's {season_label} climate would favor "
                f"{climate_element}, but strength-balance takes priority for a strong/weak "
                "Day Master.)"
            )
    else:
        note = base_note

    return FavorableElement(
        element=element, method=method, confidence="heuristic", note=note,
        supporting=supporting, climate_band=climate["band"],
        climate_element=climate_element, climate_agrees=climate_agrees,
    )
