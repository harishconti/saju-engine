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