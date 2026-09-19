"""Plan 4 (W4 yongsin) validation-harness tests.

Fixtures: tests/validation/fixtures/yongsin.json — 5 layer-A entries at Task 1
(3 synthetic merge-logic charts + 2 published verdicts), growing to 13 in
Task 2. Expected values are grounded in knowledge/09-interpretation-method.md
Step 3 (용신 derivation) + knowledge/17-climate-method.md (조후 merge rules),
with the synthetic pillars probe-verified 2026-09-13.
"""
import pytest

from saju_engine.validation import _ALLOWED_INPUT, _YONGSIN_EXTRA_INPUT, load_fixtures

ENTRIES = load_fixtures("yongsin")

VALID_METHODS = {"strong-dm-drain", "weak-dm-support", "balanced-heuristic",
                 "climate-balanced", "reader-confirmed"}
VALID_ELEMENTS = {"Wood", "Fire", "Earth", "Metal", "Water"}


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_yongsin_fixture(entry):
    """Each yongsin fixture must match engine output.

    Same contract as test_val_lookups: a documented_interpretation entry that
    does NOT match marks itself xfail (renders INTERPRETATION in the CLI
    report) instead of failing the suite.
    """
    from saju_engine.validation import run_yongsin_fixture

    result = run_yongsin_fixture(entry)
    if result["status"] != "PASS" and entry["status"] == "documented_interpretation":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]


def test_method_label_coverage():
    """Across all entries, the expected fe.method set must hit every one of the
    five FavorableElement.method labels (exercises all merge branches).

    Layer A (5 entries) covers only strong-dm-drain + weak-dm-support; the
    balanced-heuristic / climate-balanced / reader-confirmed branches arrive
    with the T2 corpus (13 entries). The strict equality pin activates then;
    before that, only the subset check (no invalid labels) applies — mirroring
    the Plan-3 coverage-test escalation pattern.
    """
    seen = {e["expected"]["fe"]["method"] for e in ENTRIES
            if (e.get("expected", {}).get("fe") or {}).get("method") is not None}
    assert seen <= VALID_METHODS, f"invalid labels: {seen - VALID_METHODS}"
    if len(ENTRIES) >= 13:
        assert seen == VALID_METHODS, f"missing: {VALID_METHODS - seen}"


def test_input_keys_guarded():
    """The two yongsin override channels must not overlap compute_chart kwargs."""
    assert _YONGSIN_EXTRA_INPUT.isdisjoint(_ALLOWED_INPUT)