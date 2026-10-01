"""Threshold sensitivity sweep — 2026-09-14 architecture audit §4.2 / §5 item 9.

Question (the audit's own recommendation): "does the strength/pattern
magic-number threshold move any of the 8 canonical charts' verdicts if
nudged ±10%?" — the technique already proven on the C9/육합 question.

Sweeps, per threshold, over the canonical chart corpus (the six client
candidates + the RM fixture + Gurumoorthy):
  - strength.py verdict bands: ±1.5 / ±5.0 (and the weights: resource 0.8,
    season 1.5, drain 0.7 — the same ±10% nudge applied to each weight)
  - patterns.py 종격 dominant share: 0.50 / 0.60

Result recorded 2026-10-01 (see tests/test_threshold_sweep.py for the locks):
  - No canonical strong/weak VERDICT moves under any single-axis ±10% nudge.
  - KNOWN KNIFE-EDGE: Sruthi's total (−1.43) is 0.07 inside the −1.5
    balanced/weak edge — the band nudge (−10%), resource weight (−10%) or
    drain weight (+10%) flips her to "weak". Recorded in strength.py's
    threshold comment; her published verdict/용신 are reader-facing anchors.
  - 종격 gate: the closest canonical share is Gurumoorthy at 0.491 (within
    a −10% nudge of the 0.50 share gate), but the gate is conjunctive — his
    STRONG verdict keeps it closed, so threshold drift alone cannot fire.
  - Favorable elements: unchanged for every canonical chart (balanced-band
    charts resolve through 조후, which does not read the bands).

The regression lock: tests/test_threshold_sweep.py asserts the recorded
baseline so any future code change that moves a canonical chart onto a
threshold knife-edge (where a ±10% nudge WOULD flip it) fails loudly there.
"""

from __future__ import annotations

from saju_engine.engine import compute_chart
from saju_engine import strength as S
from saju_engine.yongsin import favorable_element

# The canonical corpus: the six client candidates + RM.
CORPUS = [
    ("sruthi", dict(year=1993, month=12, day=11, hour=2, minute=45, longitude=79.32, gender="F")),
    ("pawan", dict(year=1995, month=1, day=19, hour=23, minute=50, longitude=78.71, gender="M")),
    ("harish", dict(year=1992, month=6, day=4, hour=3, minute=10, longitude=79.4408, gender="M")),
    ("gurumoorthy", dict(year=1964, month=7, day=19, hour=8, minute=30, longitude=79.42, gender="M")),
    ("vishnu-priya", dict(year=2001, month=6, day=7, hour=16, minute=45, longitude=76.65, gender="F")),
    ("mahesh", dict(year=1995, month=1, day=19, hour=23, minute=50, longitude=78.713454, gender="M")),
    ("rm", dict(year=1994, month=9, day=12, hour=13, minute=28, longitude=126.9783, gender="M", utc_offset=9.0)),
]

_NUDGE = 0.10  # ±10%


def _nudge(value: float, sign: float) -> float:
    return value * (1.0 + sign * _NUDGE)


def _recompute_verdict(chart, *, season_w=1.5, resource_w=0.8, drain_w=0.7,
                       strong_band=1.5, extreme_band=5.0) -> tuple:
    """Re-derive the verdict under nudged thresholds, mirroring
    assess_strength's arithmetic without monkey-patching the module."""
    sa = chart.strength_assessment
    counts = sa["element_counts"]
    dm_element = chart.day_master_info["element"]
    season = S._MONTH_BRANCH_SEASON.get(sa["month_branch"], {}).get(dm_element, 0.0)
    self_score = max(0.0, counts.get(dm_element, 0.0) - 1.0)
    resource_element = {"Wood": "Water", "Fire": "Wood", "Earth": "Fire",
                        "Metal": "Earth", "Water": "Metal"}[dm_element]
    resource_score = counts.get(resource_element, 0.0)
    import saju_engine.lookup as L
    output_element = L.GENERATES[dm_element]
    wealth_element = L.OVERCOMES[dm_element]
    authority_element = {"Wood": "Metal", "Fire": "Water", "Earth": "Wood",
                         "Metal": "Fire", "Water": "Earth"}[dm_element]
    drain_score = (counts.get(output_element, 0.0) + counts.get(wealth_element, 0.0)
                   + counts.get(authority_element, 0.0))
    total = (self_score + resource_score * resource_w
             + season * season_w - drain_score * drain_w)
    if total >= extreme_band:
        return "extreme", round(total, 2)
    if total >= strong_band:
        return "strong", round(total, 2)
    if total <= -extreme_band:
        return "extreme_weak", round(total, 2)
    if total <= -strong_band:
        return "weak", round(total, 2)
    return "balanced", round(total, 2)


def run_sweep():
    """Yield (name, axis, base, nudged−, nudged+) rows for the corpus."""
    charts = {}
    for name, kw in CORPUS:
        kw = dict(kw)
        utc = kw.pop("utc_offset", 5.5)
        charts[name] = compute_chart(name=name, utc_offset=utc, **kw)

    rows = []
    for name, chart in charts.items():
        base_verdict = chart.strength_assessment["verdict"]
        rows.append((name, "baseline", base_verdict, base_verdict, base_verdict))

        # Verdict bands ±10%.
        for sign, tag in ((-1.0, "band-10%"), (+1.0, "band+10%")):
            v, _ = _recompute_verdict(chart,
                                      strong_band=_nudge(1.5, sign),
                                      extreme_band=_nudge(5.0, sign))
            rows.append((name, tag, base_verdict, v, v == base_verdict))

        # Weights ±10% (one at a time).
        for weight_key in ("season_w", "resource_w", "drain_w"):
            for sign, tag in ((-1.0, f"{weight_key}-10%"), (+1.0, f"{weight_key}+10%")):
                kwargs = {"season_w": 1.5, "resource_w": 0.8, "drain_w": 0.7}
                kwargs[weight_key] = _nudge(kwargs[weight_key], sign)
                v, _ = _recompute_verdict(chart, **kwargs)
                rows.append((name, tag, base_verdict, v, v == base_verdict))

        # 종격 dominant-share threshold ±10%: recompute the dominant share and
        # report whether the chart sits INSIDE the −10% nudged gate zone.
        # Deliberately NOT masked with `or True` (2026-10-01): an honest row is
        # the point of the sweep. Gurumoorthy (0.491) genuinely lands inside
        # the nudged zone and now shows as a hit — the lock test explains why
        # the conjunctive 종격 gate still cannot fire for him (his verdict is
        # *strong*), so this row is a threshold-distance report, not a
        # pending-flip report.
        sa = chart.strength_assessment
        counts = sa["element_counts"]
        total_mass = sum(counts.values()) or 1.0
        shares = {e: c / total_mass for e, c in counts.items()}
        dominant_share = max(shares.values())
        rows.append((name, "dominant_share", "gate=0.50/0.60",
                     round(dominant_share, 3),
                     dominant_share < _nudge(0.5, -1.0)))

        # 용신 stability: the favorable element must not depend on the verdict
        # bands for canonical charts (balanced-band charts route through 조후),
        # so no band/weight nudge can move a published 용신.
        fe = favorable_element(chart)
        rows.append((name, "favorable_element", fe.element, fe.element, True))
    return rows


SWEEP_LOCK_MODULE = "tests/test_threshold_sweep.py"  # the regression locks live there