"""Unit tests for the validation fixture loader."""
from __future__ import annotations

import json

import pytest

from saju_engine.validation import load_fixtures


def test_load_pillars_returns_cited_entries():
    entries = load_fixtures("pillars")
    assert len(entries) >= 10, "textbook migration must seed at least 10 cases"
    ids = [e["id"] for e in entries]
    assert "park-chung-hee" in ids
    assert len(ids) == len(set(ids)), "fixture ids must be unique"
    for e in entries:
        assert set(e) >= {"id", "subsystem", "input", "source", "expected", "status"}
        assert e["subsystem"] == "pillars"
        assert e["source"], f"{e['id']}: missing source citation"
        assert e["status"] in {"expect_match", "documented_interpretation"}


def test_load_unknown_subsystem_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_fixtures("no-such-subsystem", fixtures_dir=tmp_path)


def test_rejects_bad_status(tmp_path):
    bad = {"id": "x", "subsystem": "pillars", "input": {}, "source": [],
           "expected": {"pillars": {}}, "status": "maybe"}
    (tmp_path / "pillars.json").write_text(json.dumps([bad]), encoding="utf-8")
    with pytest.raises(ValueError, match="maybe"):
        load_fixtures("pillars", fixtures_dir=tmp_path)


from saju_engine.validation import check_pillars  # noqa: E402  (appended after loader tests)


class _FakePillar:
    def __init__(self, combined: str) -> None:
        self.combined = combined


class _FakeChart:
    def __init__(self, pillars: dict) -> None:
        for pos, val in pillars.items():
            setattr(self, pos, _FakePillar(val))
        self.solar_correction = None
        self.zi_time_type = None


def test_check_pillars_pass():
    entry = {"id": "t1", "status": "expect_match",
             "expected": {"pillars": {"year": "丁巳", "month": "辛亥"}}}
    # _FakeChart wraps each value in _FakePillar itself — pass plain strings.
    chart = _FakeChart({"year": "丁巳", "month": "辛亥"})
    assert check_pillars(chart, entry)["status"] == "PASS"


def test_check_pillars_fail_reports_mismatches():
    entry = {"id": "t2", "status": "expect_match",
             "expected": {"pillars": {"hour": "辛巳"}}}
    chart = _FakeChart({"hour": "戊寅"})
    result = check_pillars(chart, entry)
    assert result["status"] == "FAIL"
    assert result["mismatches"]["hour"] == {"expected": "辛巳", "got": "戊寅"}


def test_check_pillars_interpretation():
    entry = {"id": "t3", "status": "documented_interpretation",
             "expected": {"pillars": {"hour": "辛巳"}}}
    chart = _FakeChart({"hour": "戊寅"})
    assert check_pillars(chart, entry)["status"] == "INTERPRETATION"


def test_check_pillars_solar_correction():
    entry = {"id": "t4", "status": "expect_match",
             "expected": {"pillars": {}, "solar_correction_minutes": -24}}
    chart = _FakeChart({})
    chart.solar_correction = {"correction_minutes": -24}
    assert check_pillars(chart, entry)["status"] == "PASS"


def test_check_pillars_zi_time_type():
    entry = {"id": "t5", "status": "expect_match",
             "expected": {"pillars": {}, "zi_time_type": "夜子時 (Korean 야자시)"}}
    chart = _FakeChart({})
    chart.zi_time_type = "夜子時 (Korean 야자시)"
    assert check_pillars(chart, entry)["status"] == "PASS"


from saju_engine.validation import run_fixture  # noqa: E402  (appended after loader tests)


def test_run_fixture_accepts_newly_allowed_input_keys():
    """A fixture input using one of the compute_chart kwargs newly added to
    _ALLOWED_INPUT (e.g. n_periods) is passed through, not silently dropped."""
    entry = {"id": "t7", "subsystem": "pillars",
             "input": {"year": 1990, "month": 6, "day": 15, "hour": 12,
                       "n_periods": 8},
             "source": [], "expected": {"pillars": {}},
             "status": "expect_match"}
    result = run_fixture(entry)
    assert result["status"] == "PASS"


def test_run_fixture_rejects_unknown_input_key():
    """An input key that compute_chart does not accept raises ValueError
    naming the offending key and the fixture id (fixture typo guard)."""
    entry = {"id": "t8", "subsystem": "pillars",
             "input": {"year": 1990, "month": 6, "day": 15, "hour": 12,
                       "hourz": 12},
             "source": [], "expected": {"pillars": {}},
             "status": "expect_match"}
    with pytest.raises(ValueError, match="hourz"):
        run_fixture(entry)


def test_check_pillars_skips_null_expected_fields():
    """A null (None) expected field is skipped — not compared, not a mismatch.

    Mirrors the kim-dae-jung fixture, whose unpublished hour is `null`.
    """
    entry = {"id": "t6", "status": "expect_match",
             "expected": {"pillars": {"day": "甲申", "hour": None}}}
    chart = _FakeChart({"day": "甲申", "hour": "丙寅"})
    result = check_pillars(chart, entry)
    assert result["status"] == "PASS"
    assert result["mismatches"] == {}
    assert "hour" not in result["detail"]