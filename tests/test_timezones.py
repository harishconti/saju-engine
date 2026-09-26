"""N-13 (2026-09-26 audit): IANA timezone input with DST and historical offsets."""
from __future__ import annotations

import importlib.util
import io
from pathlib import Path

import pytest

from saju_engine.timezones import resolve_utc_offset

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "tz,when,offset,dst",
    [
        ("America/New_York", (1990, 7, 1, 12, 0), -4.0, True),
        ("America/New_York", (1990, 1, 15, 12, 0), -5.0, False),
        ("Europe/London", (2000, 6, 1, 9, 0), 1.0, True),
        ("Asia/Seoul", (1960, 1, 1, 12, 0), 8.5, False),   # +8:30 in 1954-61
        ("Asia/Seoul", (1955, 6, 1, 12, 0), 9.5, True),    # DST on top of +8:30
        ("Asia/Seoul", (1987, 7, 1, 12, 0), 10.0, True),   # 1987-88 DST
        ("Asia/Seoul", (1990, 7, 1, 12, 0), 9.0, False),
        ("Asia/Kathmandu", (2000, 1, 1, 12, 0), 5.75, False),
    ],
)
def test_resolves_dst_and_historical_offsets(tz, when, offset, dst):
    r = resolve_utc_offset(tz, *when)
    assert r.utc_offset == offset and r.dst is dst and r.notes == []


def test_ambiguous_fall_back_hour_is_flagged():
    r = resolve_utc_offset("America/New_York", 2024, 11, 3, 1, 30)
    assert r.utc_offset == -4.0
    assert r.notes and "occurs twice" in r.notes[0] and "-5" in r.notes[0]


def test_nonexistent_spring_forward_time_is_flagged():
    r = resolve_utc_offset("America/New_York", 2024, 3, 10, 2, 30)
    assert r.notes and "does not exist" in r.notes[0]


def test_unknown_zone_raises():
    with pytest.raises(ValueError, match="unknown IANA timezone"):
        resolve_utc_offset("Mars/Base", 2000, 1, 1, 0, 0)


def test_cli_timezone_sets_dst_offset():
    import json

    from saju_engine.cli import main

    out, err = io.StringIO(), io.StringIO()
    rc = main(["--date", "1990-07-01", "--time", "12:00", "--timezone", "America/New_York",
               "--longitude", "-74", "--gender", "M", "--format", "json"], stdout=out, stderr=err)
    assert rc in (0, None)
    assert json.loads(out.getvalue())["utc_offset"] == -4.0


def test_cli_requires_timezone_or_offset():
    from saju_engine.cli import main

    out, err = io.StringIO(), io.StringIO()
    rc = main(["--date", "1990-07-01", "--time", "12:00"], stdout=out, stderr=err)
    assert rc not in (0, None)
    assert "--timezone" in err.getvalue()


def _load_app():
    spec = importlib.util.spec_from_file_location(
        "client_intake_app", PROJECT_ROOT / "tools" / "client_intake_app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_web_app_has_no_india_default_and_rejects_bad_zone():
    app = _load_app()
    source = (PROJECT_ROOT / "tools" / "client_intake_app.py").read_text()
    assert "Form(5.5)" not in source and '"utc_offset", 5.5' not in source
    with pytest.raises(ValueError, match="unknown IANA timezone"):
        app._derive_utc_offset("1990-07-01", "12:00", "Mars/Base", 9.0)
    with pytest.raises(ValueError, match="timezone"):
        app._derive_utc_offset("1990-07-01", "12:00", "", None)
    assert app._derive_utc_offset("1990-07-01", "12:00", "America/New_York", None) == -4.0
    assert app._derive_utc_offset("1990-07-01", "12:00", "", -4.0) == -4.0


def test_single_chart_form_accepts_quarter_hour_offsets():
    html = (PROJECT_ROOT / "tools" / "client_intake_app.html").read_text()
    start = html.index('id="utc_offset"')
    tag = html[start:html.index(">", start)]
    assert 'step="0.25"' in tag


def test_json_intake_form_collects_timezone_and_offset():
    html = (PROJECT_ROOT / "tools" / "client_intake_form.html").read_text()
    assert 'name="timezone"' in html and 'name="utc_offset"' in html
