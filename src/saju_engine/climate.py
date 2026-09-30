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

2026-09-26 (deep-audit N-6): the 조후 override is now gated on the **whole
chart**, not the month branch alone. The classical doctrine (적천수 §29/§30 +
임철초 註) requires the *chart* to be climate-extreme ("不可過/不可偏"), and the
industry standard operationalises that as a whole-chart temperature score:
정해 만세력 (8-codes) documents its method as *"천간, 지지의 각 글자마다 각각
한난... 점수를 부여하고 이를 조합하여 사주의 온도와 습도를 구합니다. 이때,
월지와 시지에 더 큰 가산점을 주어 구합니다"* — a weighted per-character
temperature score with month/hour branches weighted higher — and *"조후가
중화되어 있을수록 조후 용신의 중요성은 떨어집니다"* (the more neutral the chart,
the less 조후 matters). 사주플러스 agrees the temperature is judged from the
whole chart with the month central ("한난은 월지 중심으로 판단").

This module implements that: `climate_temperature()` scores every 천간/지지
(with hidden stems) as warm (木火) or cool (金水), weighting the month and hour
branches higher. Two threshold-free gates then decide whether the override
fires: `is_climate_extreme()` withholds it when a **hot/cold month's whole chart
clearly leans the opposite way** (the "사주가 너무 차거나 너무 더우면" condition
is not met of the chart), and `is_remedy_dominant()` withholds it when the
prescribed remedy is already the chart's most abundant element. The element
itself is still taken from the month table (as the classical per-stem 궁통보감
rule and sajuplus both do); only the *priority* is gated. See
`docs/research/2026-09-26-climate-extremeness-threshold.md`.
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


# ── Whole-chart temperature (N-6, 2026-09-26) ────────────────────────────────
# The industry-standard way to read 한난 (temperature) is the whole chart, not
# the month alone. The per-character 한/난 assignment below is transcribed from
# 사주플러스's published 한난조습 조견표 (mase.sajuplus.net, directly reviewed
# 2026-09-26) — the only major Korean engine found that publishes its full table:
#   stems:  한(cold) 甲 辛 壬 癸 · 난(warm) 乙 丙 丁 庚 · neutral 戊 己
#   branches: 한(cold) 寅 酉 戌 亥 子 丑 · 난(warm) 卯 辰 巳 午 未 申
# The 적천수 原注's principle ("金水為寒，木火為暖") matches the warm/cool split.
_WARM_STEMS = {"乙", "丙", "丁", "庚"}
_COLD_STEMS = {"甲", "辛", "壬", "癸"}
_WARM_BRANCHES = {"卯", "辰", "巳", "午", "未", "申"}
_COLD_BRANCHES_TEMP = {"寅", "酉", "戌", "亥", "子", "丑"}

# Position weighting. 8-codes documents that the month and hour *branches* are
# weighted more heavily ("월지와 시지에 더 큰 가산점을 주어 구합니다"); the
# remaining positions are 1.0. Hidden stems count at a fraction of their pillar.
_BRANCH_POSITION_WEIGHT = {"year": 1.0, "month": 2.0, "day": 1.0, "hour": 1.5}
_HIDDEN_STEM_WEIGHT = {"main": 0.5, "middle": 0.25, "residual": 0.1}
_POSITIONS = ("year", "month", "day", "hour")


def _temp_sign(char: str, warm: set, cold: set) -> float:
    if char in warm:
        return 1.0
    if char in cold:
        return -1.0
    return 0.0


def climate_temperature(pillars) -> float:
    """Return a weighted whole-chart 한난 (temperature) score.

    Positive = the chart leans warm (木火), negative = cool (金水). Each pillar's
    visible stem and branch are scored plus its hidden stems (at reduced weight);
    the month and hour branches are weighted higher, per the industry method
    (정해 만세력 / 8-codes). This is the chart's *climate extremeness*: the
    larger the magnitude, the more strongly 조후 applies.

    `pillars` is any iterable of 4 objects with `.stem`, `.branch`, and
    `.hidden_stems` (a list of (role, stem) tuples) — i.e. a `Chart.pillars`.
    """
    total = 0.0
    for position, p in zip(_POSITIONS, pillars):
        weight = _BRANCH_POSITION_WEIGHT[position]
        total += _temp_sign(p.stem, _WARM_STEMS, _COLD_STEMS)
        total += weight * _temp_sign(p.branch, _WARM_BRANCHES, _COLD_BRANCHES_TEMP)
        for role, stem in p.hidden_stems:
            frac = _HIDDEN_STEM_WEIGHT.get(role, 0.1)
            total += weight * frac * _temp_sign(stem, _WARM_STEMS, _COLD_STEMS)
    return round(total, 2)


# Neutrality margin (operational, not a transcribed classical number — marked
# [UNCERTAIN] in knowledge/17). The industry engines grade 조후 by how one-sided
# the whole-chart temperature is but do not publish their cutoff. This margin
# sets how far the chart must lean *against* its month band before the remedy is
# withheld: within ±margin the chart is treated as climate-consistent enough to
# keep the classical month/stem remedy (Ground Rule 1 — e.g. 궁통보감's
# unconditional 四月辛金→壬水).
_NEUTRAL_TEMPERATURE_MARGIN = 1.0


def is_climate_extreme(month_branch: str, temperature: float) -> bool:
    """Return True unless the chart's temperature clearly opposes its month (寒暖 axis).

    The hot/cold bands are the 寒暖 (temperature) axis: a hot month (巳午未) wants
    Water, a cold month (亥子丑) wants Fire. The classical condition is "사주가
    너무 차거나 너무 더우면" — the *chart*, not just the month, must lean that way.
    This test suppresses the override only when the whole chart clearly leans
    opposite its month, beyond `_NEUTRAL_TEMPERATURE_MARGIN`: a hot month whose
    chart reads cool, or a cold month whose chart reads warm.

    The damp/dry bands (辰戌) are the 燥濕 (humidity) axis, and this module's
    temperature score is a *temperature* (金水/木火) measure that cannot judge
    humidity, so those bands always return True here — their oversaturation is
    caught by `is_remedy_dominant` instead. A temperate month returns False.

    Per the module docstring, the element stays month-derived (classical); only
    the priority is gated.
    """
    band = assess_climate(month_branch)["band"]
    m = _NEUTRAL_TEMPERATURE_MARGIN
    if band == "hot":
        return temperature >= -m
    if band == "cold":
        return temperature <= m
    if band in ("damp", "dry"):
        return True  # 燥濕 axis — no temperature opinion; dominance guard handles it
    return False


def is_remedy_dominant(
    month_branch: str,
    element_counts: Optional[Dict[str, float]],
) -> bool:
    """Return True if the 조후 remedy element is already the chart's most abundant.

    Second, threshold-free guard (N-6, 2026-09-26): if the element 조후 would
    add is already the chart's most-abundant element, adding more cannot balance
    the chart, so the override is withheld and 억부 governs. This catches charts
    that are genuinely climate-extreme in direction but already saturated with
    their own remedy.

    A temperate month (no remedy) returns False. An empty/None `element_counts`
    returns False (nothing to compare — do not suppress on missing data).
    """
    remedy = assess_climate(month_branch)["climate_favorable"]
    if not remedy or not element_counts:
        return False
    return remedy == max(element_counts, key=element_counts.get)


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
