"""Resolve a birth's UTC offset from an IANA timezone (N-13, 2026-09-26 audit).

A numeric ``--utc-offset`` silently goes wrong for the primary (US-first)
market and for historical Korean births: New York in July is UTC-4, not -5;
Korea ran on UTC+8:30 in 1954-61 and observed daylight saving in 1948-60 and
1987-88. A one-hour error moves the hour pillar for about half of births and
the solar-time correction by 60 minutes. The IANA database (via ``zoneinfo``)
already knows every one of those rules, so an IANA zone name plus the civil
birth date/time is the preferred input; the numeric offset is a fallback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones


@dataclass
class ResolvedOffset:
    utc_offset: float                  # hours east of UTC, DST included
    timezone: str
    dst: bool                          # daylight saving in effect at birth
    notes: List[str] = field(default_factory=list)


def resolve_utc_offset(
    timezone: str, year: int, month: int, day: int, hour: int, minute: int,
) -> ResolvedOffset:
    """Return the UTC offset in force for a civil birth time in ``timezone``.

    Raises ValueError for an unknown zone name. Flags the two DST edge cases
    in ``notes`` rather than guessing silently:
      - an **ambiguous** time (the repeated hour when clocks fall back): the
        first occurrence (pre-transition offset) is used;
      - a **non-existent** time (the skipped hour when clocks spring forward):
        the pre-transition offset is used, as zoneinfo does.
    """
    name = (timezone or "").strip()
    if not name or name not in available_timezones():
        raise ValueError(
            f"unknown IANA timezone {timezone!r} — use a zone name such as "
            f"'America/New_York', 'Asia/Seoul' or 'Asia/Kolkata'"
        )
    try:
        tz = ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:  # pragma: no cover - guarded above
        raise ValueError(f"unknown IANA timezone {timezone!r}") from exc

    local = datetime(year, month, day, hour, minute)
    first = local.replace(tzinfo=tz, fold=0)
    second = local.replace(tzinfo=tz, fold=1)
    off0, off1 = first.utcoffset(), second.utcoffset()
    notes: List[str] = []
    if off0 != off1:
        # Round-trip through UTC: a real wall time maps back to itself.
        if (first.astimezone(ZoneInfo("UTC")).astimezone(tz).replace(tzinfo=None) == local):
            notes.append(
                f"{local:%Y-%m-%d %H:%M} occurs twice in {name} (clocks fell back); "
                f"used the first occurrence (UTC{_fmt(off0)}). If the birth was in the "
                f"repeated hour, re-run with --utc-offset {_hours(off1):g}."
            )
        else:
            notes.append(
                f"{local:%Y-%m-%d %H:%M} does not exist in {name} (clocks sprang forward); "
                f"used UTC{_fmt(off0)}. Check the recorded birth time."
            )
    dst = bool(first.dst())
    return ResolvedOffset(utc_offset=_hours(off0), timezone=name, dst=dst, notes=notes)


def _hours(td: timedelta) -> float:
    return td.total_seconds() / 3600.0


def _fmt(td: timedelta) -> str:
    total = int(td.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    h, m = divmod(abs(total), 60)
    return f"{sign}{h:02d}:{m:02d}"
