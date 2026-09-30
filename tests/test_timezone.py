"""N-13 (2026-09-26 audit): IANA timezone → historical UTC-offset resolution.

The engine's birth input is a numeric UTC offset, which cannot express DST or
historic offset changes (US summer = −4 not −5; Korea used +8:30 in 1954–61 and
DST in 1948–60/1987–88). `saju_engine.timezone.derive_utc_offset` resolves the
exact historical offset from an IANA zone.
"""
from __future__ import annotations

import pytest

from saju_engine.timezone import UnknownTimezone, derive_utc_offset, is_known_timezone


def test_known_timezone_detection():
    assert is_known_timezone("America/New_York")
    assert is_known_timezone("Asia/Seoul")
    assert not is_known_timezone("Not/AZone")
    assert not is_known_timezone("")


def test_new_york_summer_uses_dst_offset():
    """July is EDT (−4), not the standard −5."""
    off, from_tz = derive_utc_offset(2024, 7, 15, 10, 0, "America/New_York")
    assert from_tz is True
    assert off == -4.0


def test_new_york_winter_uses_standard_offset():
    off, _ = derive_utc_offset(2024, 1, 15, 10, 0, "America/New_York")
    assert off == -5.0


def test_korea_1960_uses_historical_offset():
    """Korea used UTC+8:30 in 1954–61 (DST also applied in some years); the
    resolved offset for a 1960 birth must not be the modern +9."""
    off, _ = derive_utc_offset(1960, 8, 15, 12, 0, "Asia/Seoul")
    assert off in (8.5, 9.5)  # +8:30 standard, or +9:30 if DST was in effect


def test_fallback_offset_when_no_timezone():
    off, from_tz = derive_utc_offset(1992, 6, 4, 3, 10, None, 5.5)
    assert off == 5.5
    assert from_tz is False


def test_missing_timezone_and_offset_raises():
    """N-13: no silent region default."""
    with pytest.raises(UnknownTimezone):
        derive_utc_offset(1992, 6, 4, 3, 10, None, None)


def test_unknown_timezone_raises():
    with pytest.raises(UnknownTimezone):
        derive_utc_offset(1992, 6, 4, 3, 10, "Not/AZone", 5.5)


def test_cli_timezone_flag_resolves_offset():
    """The CLI --timezone flag flows through to the chart's utc_offset."""
    from saju_engine.cli import main
    import io
    import json
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        main(["--date", "2024-07-15", "--time", "10:00",
              "--timezone", "America/New_York", "--longitude", "-74.0",
              "--gender", "M", "--format", "json"])
    data = json.loads(buf.getvalue())
    assert data["utc_offset"] == -4.0
