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


def test_report_has_no_frozen_narrative():
    from pathlib import Path
    from saju_engine.validation import _GATE_HISTORY, collect_results
    for g in _GATE_HISTORY:
        note = g.get("note", "")
        assert "\n" not in note and len(note) <= 160, g["workstream"]
    text = render_report(collect_results())
    assert "Full certification history: docs/validation/gate-history.md" in text
    assert "documented divergences" not in text  # narrative moved to the doc
    doc = Path(__file__).resolve().parents[2] / "docs" / "validation" / "gate-history.md"
    assert "documented divergences" in doc.read_text(encoding="utf-8")
