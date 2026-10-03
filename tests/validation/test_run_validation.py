"""Unit tests for the validation report renderer."""
from saju_engine.validation import render_report


SYNTHETIC = {
    "pillars": [
        {"id": "a", "status": "PASS", "mismatches": {}, "detail": "all checks matched"},
        {"id": "b", "status": "INTERPRETATION", "mismatches": {"hour": {"expected": "辛巳", "got": "戊寅"}},
         "detail": "hour: expected 辛巳, got 戊寅"},
        {"id": "c", "status": "FAIL", "mismatches": {"day": {"expected": "庚申", "got": "庚戌"}},
         "detail": "day: expected 庚申, got 庚戌"},
    ]
}


def test_render_report_scorecard_counts():
    text = render_report(SYNTHETIC)
    assert "| pillars |" in text
    assert text.count("PASS") >= 1 and text.count("FAIL") >= 1


def test_render_report_rows_carry_detail_and_status():
    text = render_report(SYNTHETIC)
    assert "| a |" in text
    assert "| b |" in text
    assert "INTERPRETATION" in text


def test_render_report_escapes_pipes():
    text = render_report({"pillars": [
        {"id": "we|ird", "status": "PASS", "mismatches": {}, "detail": "ok|fine"}]})
    assert "we\\|ird" in text

# Pre-change full report (all 10 subsystems) measured 2026-10-03: 36821 bytes /
# 526 lines, of which ~40% was frozen certification narrative. 60% bound = 22092.
_PRE_CHANGE_REPORT_BYTES = 36821


def test_report_has_no_frozen_narrative():
    from pathlib import Path
    from saju_engine.validation import collect_results
    text = render_report(collect_results())
    assert len(text.encode("utf-8")) < 0.6 * _PRE_CHANGE_REPORT_BYTES
    assert "Full certification history: docs/validation/gate-history.md" in text
    assert "documented divergences" not in text  # narrative moved to the doc
    doc = Path(__file__).resolve().parents[2] / "docs" / "validation" / "gate-history.md"
    assert "documented divergences" in doc.read_text(encoding="utf-8")
