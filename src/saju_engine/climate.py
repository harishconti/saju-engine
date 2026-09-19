"""조후 (climate/temperature-balance) cross-check for the favorable-element engine.

Conservative, general model: derives a chart's climate need purely from the
month branch's season, using the four standard seasonal quartets (already
implicit in strength.py's ``_MONTH_BRANCH_SEASON`` grouping). This is NOT a
full 궁통보감 (窮通寶鑑) per-stem-per-month lookup table — no source text for
that was available, so this captures only the general classical principle,
shared by 궁통보감 and 적천수, that a chart peaking in summer heat wants Water
to cool it, and a chart peaking in winter cold wants Fire to warm it.

This module implements the 寒暖 (hot/cold) axis ONLY. The fuller classical 조후
treatment is the four-way 寒暖燥濕 reading (적천수: 天道有寒暖 … 地道有燥湿), which
also gives 辰 (濕 → Fire) and 戌 (燥 → Water) a remedy; this module bands both
temperate. That is a deliberate scope limit, not an oversight: the per-branch
assignments rest on a modern practitioner source rather than a transcribed
classical text, and widening the model moves the client-facing ``band`` value.
The divergence is pinned by tests/test_climate.py and the band-chen / band-xu
validation fixtures, so an expansion is a signalled change rather than a silent
one.

See knowledge/17-climate-method.md for the doctrinal basis and scope note.
"""
from __future__ import annotations

from typing import Dict, Optional

from . import lookup as L

# Inverse of the generating cycle: for each element, the element that generates it.
_GENERATED_BY: Dict[str, str] = {v: k for k, v in L.GENERATES.items()}

_HOT_BRANCHES = {"巳", "午", "未"}
_COLD_BRANCHES = {"亥", "子", "丑"}


def assess_climate(month_branch: str) -> Dict[str, Optional[str]]:
    """Return the 조후 (climate) band for a chart, from its month branch's season.

    Returns a dict with:
      - band: "hot" | "cold" | "temperate"
      - climate_favorable: the classical climate-balancing element, or None
        if the month is climate-neutral (spring/autumn, or unrecognized).
      - climate_supporting: the element that generates climate_favorable
        (희신, strict classical formula), or None.
    """
    if month_branch in _HOT_BRANCHES:
        favorable = "Water"
        return {
            "band": "hot",
            "climate_favorable": favorable,
            "climate_supporting": _GENERATED_BY[favorable],
        }
    if month_branch in _COLD_BRANCHES:
        favorable = "Fire"
        return {
            "band": "cold",
            "climate_favorable": favorable,
            "climate_supporting": _GENERATED_BY[favorable],
        }
    return {"band": "temperate", "climate_favorable": None, "climate_supporting": None}
