"""조후 (climate/temperature-balance) cross-check for the favorable-element engine.

Implements the full four-way 寒暖燥濕 (hán-nuǎn-zào-shī) classical model:
적천수's "天道有寒暖 … 地道有燥湿" couplet gives climate two axes — 寒/暖
(cold/hot, by season) and 燥/濕 (dry/damp, carried by the four earth-storage
branches 辰戌丑未, which are not one undifferentiated class). This captures
the general classical principle shared by 궁통보감 and 적천수: a chart peaking
in summer heat wants Water, one peaking in winter cold wants Fire, one peaking
in dry-earth conditions wants Water, and one peaking in damp-earth conditions
wants Fire.

This is NOT the full per-stem × per-month 궁통보감 lookup table (10 stems ×
12 months) — no classical source text for that table was available to
transcribe, so the Day-Master stem is still not an input here; only the
month branch is. See knowledge/17-climate-method.md for the doctrinal basis,
sources, and this remaining scope limit.

2026-09-19: expanded from a 寒暖-only (hot/cold/temperate) model to the full
four-axis 寒暖燥濕 model, adding remedies for 辰 (濕 → Fire) and 戌 (燥 → Water).
The per-branch 燥/濕 assignments are sourced (not invented) — see
docs/research/2026-09-validation-climate.md §3, citing cantian.ai's 한난조습
table (directly reviewed 2026-09-13) and corroborated by OpenFate's 사계절
토와 월령 page. This was a deliberate, user-approved product decision (the
divergence had been pinned by tests specifically so any expansion would be
signalled, not silent) — it is not a bug fix.
"""
from __future__ import annotations

from typing import Dict, Optional

from . import lookup as L

# Inverse of the generating cycle: for each element, the element that generates it.
_GENERATED_BY: Dict[str, str] = {v: k for k, v in L.GENERATES.items()}

_HOT_BRANCHES = {"巳", "午", "未"}
_COLD_BRANCHES = {"亥", "子", "丑"}
# 燥/濕 (dry/damp) axis — sourced per-branch (see module docstring). 辰 and 丑
# are both 濕 (damp) in the source, but 丑 already lands on the same remedy
# (Fire) via the 寒暖 axis above, so only 辰 needs a distinct entry here. The
# same holds for 戌/未 on the dry side: 未 already gets Water via 暖. Only 辰
# and 戌 are branches the 寒暖-only model left temperate that the 燥濕 axis
# resolves.
_DAMP_BRANCHES = {"辰"}
_DRY_BRANCHES = {"戌"}


def assess_climate(month_branch: str) -> Dict[str, Optional[str]]:
    """Return the 조후 (climate) band for a chart, from its month branch's season.

    Returns a dict with:
      - band: "hot" | "cold" | "damp" | "dry" | "temperate"
      - climate_favorable: the classical climate-balancing element, or None
        if the month is climate-neutral (真 spring/autumn branches only, per
        the sourced four-axis model).
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
    if month_branch in _DAMP_BRANCHES:
        favorable = "Fire"
        return {
            "band": "damp",
            "climate_favorable": favorable,
            "climate_supporting": _GENERATED_BY[favorable],
        }
    if month_branch in _DRY_BRANCHES:
        favorable = "Water"
        return {
            "band": "dry",
            "climate_favorable": favorable,
            "climate_supporting": _GENERATED_BY[favorable],
        }
    return {"band": "temperate", "climate_favorable": None, "climate_supporting": None}
