"""IANA-timezone → historical UTC-offset resolution (N-13, 2026-09-26 audit).

The engine's birth input is a numeric UTC offset, which cannot express DST or
historical offset changes. A US summer birth (New York in July is UTC−4, not
−5) or a Korean birth in 1954–61 (UTC+8:30) or 1948–60/1987–88 (DST) needs the
offset *for that specific local date*, not a fixed number.

This module resolves a historical offset from an IANA zone name using the
stdlib `zoneinfo` (tzdata), so the CLI and the web app share one implementation.
A numeric offset remains the fallback when no zone is supplied.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

try:  # Python 3.9+
    from zoneinfo import ZoneInfo, available_timezones
except ImportError:  # pragma: no cover - stdlib backport always present on 3.10+
    ZoneInfo = None  # type: ignore
    available_timezones = None  # type: ignore


class UnknownTimezone(ValueError):
    """Raised when a supplied IANA zone name is not recognised."""


def is_known_timezone(name: str) -> bool:
    """Return True when `name` is a recognised IANA timezone key."""
    if not name or available_timezones is None:
        return False
    return name.strip() in available_timezones()


def derive_utc_offset(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    timezone_name: Optional[str],
    fallback: Optional[float] = None,
) -> Tuple[float, bool]:
    """Return `(utc_offset_hours, from_timezone)` for a local birth moment.

    If `timezone_name` is a recognised IANA zone, the exact historical offset
    (including DST) for that local date/time is used and `from_timezone` is True.
    Otherwise `fallback` is returned (and `from_timezone` is False); if no
    fallback was given either, `UnknownTimezone` is raised so the caller must ask
    for an offset rather than silently defaulting to a region (the audit's N-13
    complaint about the old +5.5 default).
    """
    tz = (timezone_name or "").strip()
    if tz:
        if not is_known_timezone(tz):
            raise UnknownTimezone(
                f"unknown IANA timezone {tz!r}; pass --utc-offset instead "
                f"(e.g. 5.5 for India, 9 for Korea)"
            )
        local = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo(tz))  # type: ignore[misc]
        offset = local.utcoffset()
        if offset is not None:
            return offset.total_seconds() / 3600.0, True
    if fallback is None:
        raise UnknownTimezone(
            "a --timezone (IANA) or --utc-offset is required; no default is assumed"
        )
    return fallback, False
