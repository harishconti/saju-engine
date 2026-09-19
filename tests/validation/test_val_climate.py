"""Plan 5 (W5 climate) validation-harness tests.

Fixtures: tests/validation/fixtures/climate.json — 16 layer-A classifier
entries at Task 1, growing to 30 in Task 2 (16 band + 14 merge). Expected
values are grounded in knowledge/17-climate-method.md (three-band model +
§How This Combines With 억부) with every value probe-verified 2026-09-13.
"""
import pytest

from saju_engine.validation import (
    _CLIMATE_ALLOWED_INPUT,
    _CLIMATE_BAND_INPUT,
    _CLIMATE_MERGE_INPUT,
    _ALLOWED_INPUT,
    load_fixtures,
)

ENTRIES = load_fixtures("climate")

ALL_BRANCHES = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]
HOT_BRANCHES = {"巳", "午", "未"}
COLD_BRANCHES = {"亥", "子", "丑"}


def _band_entries():
    return [e for e in ENTRIES if e["input"]["probe"] == "band"]


def _merge_entries():
    return [e for e in ENTRIES if e["input"]["probe"] == "merge"]


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_climate_fixture(entry):
    """Each climate fixture must match engine output.

    Same contract as test_val_yongsin: a documented_interpretation entry that
    does NOT match marks itself xfail (renders INTERPRETATION in the CLI
    report) instead of failing the suite.
    """
    from saju_engine.validation import run_climate_fixture

    result = run_climate_fixture(entry)
    if result["status"] != "PASS" and entry["status"] == "documented_interpretation":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]


def test_band_coverage_exhaustive():
    """All 12 month branches must appear as band probes, plus >=4 edge probes.

    The 12-branch sweep is the spec's "season/climate score per chart" clause
    at classifier level; the edges pin the defensive fall-through.
    """
    band = _band_entries()
    branches = {e["input"]["month_branch"] for e in band}
    missing = set(ALL_BRANCHES) - branches
    assert not missing, f"branches with no band probe: {sorted(missing)}"
    edges = branches - set(ALL_BRANCHES)
    assert len(edges) >= 4, f"expected >=4 non-branch edge probes, got {sorted(edges)}"


def test_temperate_rows_have_no_climate_element():
    """Temperate bands must carry no climate element at all.

    This cannot be asserted through the fixture (null means skip), so it is
    asserted directly: a temperate band means the 조후 override is OFF, and a
    non-None climate_favorable there would silently fire the merge.

    Every storage month lands on one side or the other here — 丑/未 in the
    hot/cold sets, 辰/戌 in the temperate branch. The latter two are the pinned
    寒暖-only scope limit (knowledge/17-climate-method.md §The Fuller 寒暖燥濕
    Reading), so this assertion is deliberately coupled to the HOT/COLD sets
    above: widening the engine's model to the full four-way reading fails HERE.
    """
    from saju_engine import climate

    for branch in ALL_BRANCHES:
        got = climate.assess_climate(branch)
        if branch in HOT_BRANCHES or branch in COLD_BRANCHES:
            assert got["band"] in {"hot", "cold"}
            assert got["climate_favorable"] is not None
            assert got["climate_supporting"] is not None
        else:
            assert got["band"] == "temperate", branch
            assert got["climate_favorable"] is None, branch
            assert got["climate_supporting"] is None, branch


def test_climate_probe_input_guarded():
    """The two climate probe input sets must be well-formed and disjoint."""
    assert _CLIMATE_ALLOWED_INPUT == {"band", "merge"}
    assert _CLIMATE_BAND_INPUT - _CLIMATE_MERGE_INPUT, (
        "band must not be a subset of merge, or the exact-key guard is unreachable"
    )
    assert _CLIMATE_MERGE_INPUT - _ALLOWED_INPUT == {"probe"}, (
        "merge input must be _ALLOWED_INPUT plus exactly {probe}"
    )


# The strength verdict enum has FIVE values (strength.py::assess_strength
# docstring L91) — the corpus exercises three of them, so the mapping folds
# the extreme forms into their class. Keeping the full enum here means a
# future chart that lands on `extreme` still classifies instead of erroring.
_VERDICT_CLASS = {"strong": "strong", "extreme": "strong",
                  "weak": "weak", "extreme_weak": "weak",
                  "balanced": "balanced"}
_BANDS = {"hot", "cold", "temperate"}
_VERDICT_CLASSES = {"strong", "weak", "balanced"}


def test_verdict_enum_is_fully_mapped():
    """Every value the engine can emit must be in _VERDICT_CLASS.

    Guards against strength.py growing a sixth verdict that this matrix test
    would silently fail to classify.
    """
    import inspect

    from saju_engine import strength

    src = inspect.getsource(strength)
    for verdict in _VERDICT_CLASS:
        assert f"'{verdict}'" in src, (
            f"_VERDICT_CLASS lists {verdict!r} but strength.py never mentions it — "
            "the enum moved; update this mapping"
        )


def test_band_verdict_matrix_complete():
    """The corpus must fill every band x verdict-class cell, both polarities
    of climate_agrees where the band is non-temperate.

    This is the spec's "cross-check's effect on 용신 for the corpus" clause:
    without all 9 cells, a regression in one merge branch would go unseen.
    """
    cells: dict[tuple[str, str], list[str]] = {}
    for e in _merge_entries():
        band = e["expected"]["climate"]["band"]
        verdict = e["expected"]["strength"]["verdict"]
        assert verdict in _VERDICT_CLASS, f"{e['id']}: unmapped verdict {verdict!r}"
        assert band in _BANDS, f"{e['id']}: unknown band {band!r}"
        cells.setdefault((band, _VERDICT_CLASS[verdict]), []).append(e["id"])

    expected_cells = {(b, v) for b in _BANDS for v in _VERDICT_CLASSES}
    missing = expected_cells - set(cells)
    assert not missing, f"band x verdict cells with no corpus chart: {sorted(missing)}"
    assert len(cells) == 9, f"expected exactly 9 cells, got {len(cells)}: {sorted(cells)}"


def test_climate_agrees_covered_both_polarities():
    """For hot/cold bands the corpus must show climate_agrees True AND False.

    A corpus where 조후 always disagrees (or always agrees) would pass the
    fixture checks while never exercising the agree path in the merge.
    """
    seen: dict[str, set] = {"True": set(), "False": set()}
    for e in _merge_entries():
        if e["expected"]["climate"]["band"] == "temperate":
            continue
        agrees = e["expected"]["fe"]["climate_agrees"]
        assert isinstance(agrees, bool), (
            f"{e['id']}: non-temperate band must assert a bool climate_agrees, got {agrees!r}"
        )
        seen["True" if agrees else "False"].add(e["id"])
    assert seen["True"], "no corpus chart has climate_agrees True"
    assert seen["False"], "no corpus chart has climate_agrees False"


# ---------------------------------------------------------------------------
# Regression lock for the formerly-known bug (Plan 5 T4 / spec §Known Open
# Bugs Tracked #1) — FIXED 2026-09-14. premium_report.py's
# `_right_now_callout` (~L181) and `ctx_favorable_phrase` (~L1399) used to
# read the raw `strength_assessment["candidate_favorable"]` instead of the
# resolved `yongsin.favorable_element()`; both now take an `override` param
# threaded from `_ReportContext.favorable_override` and read the resolved
# channel. The two `xfail(strict=False)` markers that pinned the wrong
# behaviour are retired (they XPASSed, which was the delete-the-marker
# signal) and these now stand as plain regression locks on the fix.
# ---------------------------------------------------------------------------

REGRESSION_INPUT = {
    "name": "harish-regression",
    "year": 1992, "month": 6, "day": 4, "hour": 3, "minute": 10,
    "longitude": 79.42, "utc_offset": 5.5,
    # Frozen so the callout's year text is deterministic.
    "reference_year": 2026, "reference_month": 9, "reference_day": 13,
}


def _regression_chart():
    from saju_engine.engine import compute_chart

    return compute_chart(**REGRESSION_INPUT)


def test_regression_input_keys_are_allowed():
    """The regression chart must be expressible through the fixture schema."""
    assert set(REGRESSION_INPUT) - {"name"} <= _ALLOWED_INPUT, (
        f"regression input carries keys the harness rejects: "
        f"{sorted(set(REGRESSION_INPUT) - _ALLOWED_INPUT)}"
    )


def test_resolved_fe_differs_from_raw_candidate():
    """This PASSES and documents why the bug is observable at all.

    The raw 억부 candidate (Fire) and the resolved element (Water, via the
    조후 climate-balanced branch) genuinely differ for this chart, so a
    renderer reading the raw field produces a different answer from one
    reading the resolved field. Without this divergence the bug would be
    latent — which is why the lock is worth having.
    """
    from saju_engine import yongsin

    chart = _regression_chart()
    raw = chart.strength_assessment["candidate_favorable"]
    resolved = yongsin.favorable_element(chart)
    assert resolved.method == "climate-balanced", resolved.method
    assert raw != resolved.element, (
        "raw candidate and resolved element agree — the regression lock below "
        "would be vacuous for this chart; pick a chart where they differ"
    )


def test_right_now_callout_uses_resolved_element():
    """The callout must name the RESOLVED favorable element, not the raw one."""
    from saju_engine import yongsin
    from saju_engine.premium_report import _right_now_callout

    chart = _regression_chart()
    resolved = yongsin.favorable_element(chart).element
    raw = chart.strength_assessment["candidate_favorable"]
    callout = _right_now_callout(chart)
    assert f"**{resolved}**" in callout, (
        f"callout names the raw candidate, not the resolved element — "
        f"resolved={resolved} raw={raw}; tail: {callout[-160:]!r}"
    )


def test_ctx_favorable_phrase_uses_resolved_element():
    """The narrative phrase must name the RESOLVED favorable element."""
    from saju_engine import yongsin
    from saju_engine.premium_report import ctx_favorable_phrase

    chart = _regression_chart()
    resolved = yongsin.favorable_element(chart).element
    phrase = ctx_favorable_phrase(chart)
    assert phrase == f"{resolved.lower()} energy", (
        f"phrase reads the raw candidate, not the resolved element — "
        f"resolved={resolved}, phrase={phrase!r}"
    )
