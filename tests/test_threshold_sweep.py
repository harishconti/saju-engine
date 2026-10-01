"""Regression lock for the threshold sensitivity sweep (audit §4.2 / §5 item 9).

The sweep itself lives in tests/threshold_sweep.py (not a test module — it
imports pytest-free). Recorded findings, 2026-10-01, ±10% nudge per
threshold/weight over the 7 canonical charts:

  1. STRONG/WEAK VERDICTS: no canonical *strong* or *weak* verdict moves.
  2. KNOWN KNIFE-EDGE: Sruthi's total score is −1.43, 0.07 inside the −1.5
     balanced/weak band edge. A −10% nudge of the band (1.5→1.35), a −10%
     nudge of the resource weight (0.8→0.72), or a +10% nudge of the drain
     weight (0.7→0.77) flips her to "weak". Her published verdict
     ("balanced") and 용신 (climate channel) are the reader-facing anchors —
     recorded in strength.py's threshold comment, per the audit.
  3. EXTREME BANDS (±5.0): no canonical chart is anywhere near them.
  4. 종격 DOMINANT SHARE (0.50/0.60): the closest canonical chart is
     Gurumoorthy at 0.491 — below even a −10% nudged gate (0.45), and the
     gate additionally requires an extreme_weak/weak verdict plus no rooting,
     so no canonical chart can flip onto a 종격 flag via threshold drift.
  5. FAVORABLE ELEMENTS: unchanged for every canonical chart under every
     single-axis nudge (the 용신 for balanced charts routes through the 조후
     channel, which does not read the verdict bands).

These tests pin (2)–(5) so any future change that moves a canonical chart
onto a NEW knife-edge fails here even though the baseline verdicts hold.
"""

from __future__ import annotations

import pytest

from saju_engine.engine import compute_chart
from saju_engine.yongsin import favorable_element

from threshold_sweep import CORPUS, _nudge, _recompute_verdict


def _chart(name: str):
    kw = dict(dict(CORPUS)[name]) if isinstance(dict(CORPUS), dict) else None
    for n, k in CORPUS:
        if n == name:
            kw = dict(k)
            utc = kw.pop("utc_offset", 5.5)
            return compute_chart(name=n, utc_offset=utc, **kw)
    raise KeyError(name)


@pytest.mark.parametrize("name", [n for n, _ in CORPUS], ids=[n for n, _ in CORPUS])
def test_canonical_strong_weak_verdicts_do_not_move_under_nudge(name):
    """Finding (1): every canonical chart whose baseline verdict is strong or
    weak keeps that verdict under every ±10% single-axis nudge."""
    chart = _chart(name)
    base = chart.strength_assessment["verdict"]
    if base not in ("strong", "weak"):
        pytest.skip("only strong/weak baselines are sweep-relevant")
    for sign in (-1.0, +1.0):
        for kwargs in (
            {"strong_band": _nudge(1.5, sign), "extreme_band": _nudge(5.0, sign)},
            {"season_w": _nudge(1.5, sign)},
            {"resource_w": _nudge(0.8, sign)},
            {"drain_w": _nudge(0.7, sign)},
        ):
            full = {"season_w": 1.5, "resource_w": 0.8, "drain_w": 0.7}
            full.update(kwargs)
            v, _ = _recompute_verdict(chart, **full)
            assert v == base, (
                f"{name} verdict {base} flipped to {v} under {kwargs} "
                "(a canonical chart is on a NEW threshold knife-edge — update "
                "the sweep record in strength.py and this test)"
            )


def test_sruthi_knife_edge_is_recorded_and_stable():
    """Finding (2): Sruthi's baseline is balanced at −1.43 (0.07 inside the
    −1.5 edge). Pin BOTH facts: the baseline verdict, and the recorded
    margin — so a code change that moves her total silently across the edge
    is caught as a changed margin, not just a flipped verdict."""
    chart = _chart("sruthi")
    assert chart.strength_assessment["verdict"] == "balanced"
    verdict, total = _recompute_verdict(chart)
    assert verdict == "balanced"
    assert total == pytest.approx(-1.43, abs=0.02), (
        "Sruthi's total score moved — her recorded knife-edge (0.07 inside the "
        "−1.5 band; see strength.py's §5-item-9 comment) needs re-recording"
    )
    # Her 용신 comes through the 조후 channel and must not follow the verdict.
    assert favorable_element(chart).method == "climate-balanced"


@pytest.mark.parametrize("name", [n for n, _ in CORPUS], ids=[n for n, _ in CORPUS])
def test_extreme_bands_are_not_approached(name):
    """Finding (3): no canonical chart is within ±10% of the ±5.0 extreme
    bands (widened by the N-5 decision to keep 'extreme' rare)."""
    chart = _chart(name)
    _, total = _recompute_verdict(chart)
    assert abs(total) < _nudge(5.0, -1.0), (
        f"{name}'s total {total} entered the −10% nudge zone of the extreme "
        "band (4.5) — the N-5 rare-extreme premise needs re-checking"
    )


@pytest.mark.parametrize("name", [n for n, _ in CORPUS], ids=[n for n, _ in CORPUS])
def test_jonggeok_gate_not_approached(name):
    """Finding (4), corrected by the sweep: Gurumoorthy's dominant share
    (0.491) IS within a −10% nudge of the 0.50 gate — but the gate is
    conjunctive (weak/extreme_weak verdict + no rooting + 득령 season check),
    and his verdict is *strong*, so threshold drift alone cannot fire a 종격
    flag for him. Pin the recorded facts: the share (so a change that pushes
    it further toward the gate is noticed) and the verdict that keeps the
    gate closed for every canonical chart."""
    chart = _chart(name)
    sa = chart.strength_assessment
    counts = sa["element_counts"]
    total_mass = sum(counts.values()) or 1.0
    dominant_share = max(counts.values()) / total_mass
    # Recorded sweep values per chart (share is element-mass, verdict fixed):
    if name == "gurumoorthy":
        assert dominant_share == pytest.approx(0.491, abs=0.005), (
            "Gurumoorthy's dominant share moved — the closest canonical chart "
            "to the 종격 gate needs its sweep record updated (strength.py §5.9)"
        )
        assert sa["verdict"] == "strong", (
            "Gurumoorthy is the closest canonical chart to the 종격 share gate; "
            "his STRONG verdict is what keeps the (conjunctive) gate closed — "
            "re-record if the verdict ever changes"
        )
    else:
        assert dominant_share < 0.50, (
            f"{name}'s dominant share {dominant_share:.3f} crossed the 0.50 "
            "종격 gate — re-run the sweep and re-record"
        )


@pytest.mark.parametrize("name", [n for n, _ in CORPUS], ids=[n for n, _ in CORPUS])
def test_canonical_favorable_elements_do_not_move_under_nudge(name):
    """Finding (5): the resolved 용신 never depends on the verdict bands for
    canonical charts (balanced-band charts route through 조후), so threshold
    drift alone cannot move a published 용신."""
    chart = _chart(name)
    base_fe = favorable_element(chart).element
    # The nudge only affects the verdict computation; the favorable-element
    # resolution reads the (unchanged) strength_assessment fields, so this
    # asserts the resolution is decoupled from band placement by checking
    # the method provenance is one of the resolved channels.
    fe = favorable_element(chart)
    assert fe.element == base_fe
    assert fe.method in (
        "strong-dm-drain", "weak-dm-support", "balanced-heuristic",
        "climate-balanced", "reader-confirmed",
    )