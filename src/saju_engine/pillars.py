"""Four-pillar computation via sajupy with solar-time-aware Zi handling.

This module wraps sajupy to return a normalized dict for the rest of the engine.
sajupy handles the heavy lifting:
  - 만세력 table 1900–2100
  - 절기 month-boundary crossings
  - True solar time correction (longitude or city geocoding)

We add two things sajupy does not fully expose in a single convention:
  1. A clean, user-facing ``convention`` parameter (``korean`` / ``chinese``)
     that controls the 23:00–00:59 hour-stem day归属.
  2. A safety recomputation of the hour stem when solar-time correction pushes
     the effective birth time into or out of the 子 hour.

All interpretation rules come from the project's ``knowledge/`` directory.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import contextlib
import io
import math
import os
import sys

# sajupy is a declared project dependency (`pyproject.toml` / `requirements.txt`),
# so it should already be importable from sys.path. The only escape hatch needed
# for non-standard installs is the explicit `$SAJU_SITE` override. (The previous
# auto-insert of `site.getusersitepackages()` was a no-op: Python already places
# the user site-packages on sys.path by default.)
try:
    from sajupy import calculate_saju  # noqa: E402
except ImportError:
    _SAJU_SITE = os.environ.get("SAJU_SITE")
    if _SAJU_SITE and _SAJU_SITE not in sys.path:
        sys.path.insert(0, _SAJU_SITE)
    try:
        from sajupy import calculate_saju  # noqa: E402
    except ImportError as _exc:
        raise ImportError(
            f"sajupy not importable. Tried {_SAJU_SITE!r} (from $SAJU_SITE). "
            f"Install it with `pip install --user --break-system-packages sajupy` "
            f"or `pip install -e .`. Underlying error: {_exc}"
        )

from . import lookup as L


# ── 5-rule 五鼠遁 (hour-stem derivation) ─────────────────────────────────────
# The classical 5-rule maps a day-stem to the hour-stem at 子시:
#   甲/己 day → 甲子시, 乙/庚 day → 丙子시, 丙/辛 day → 戊子시,
#   丁/壬 day → 庚子시, 戊/癸 day → 壬子시.
# From 子, the hour-stem advances by 1 with each branch.
_HOUR_STEM_START = {
    "甲": 0, "己": 0,
    "乙": 2, "庚": 2,
    "丙": 4, "辛": 4,
    "丁": 6, "壬": 6,
    "戊": 8, "癸": 8,
}


def _hour_branch(hour: int, minute: int) -> str:
    """Return the 2-hour Earthly Branch for the given clock/solar time."""
    t = hour + minute / 60.0
    if t < 1 or t >= 23:
        return "子"
    if t < 3:
        return "丑"
    if t < 5:
        return "寅"
    if t < 7:
        return "卯"
    if t < 9:
        return "辰"
    if t < 11:
        return "巳"
    if t < 13:
        return "午"
    if t < 15:
        return "未"
    if t < 17:
        return "申"
    if t < 19:
        return "酉"
    if t < 21:
        return "戌"
    return "亥"


def _hour_stem(day_stem: str, hour_branch: str) -> str:
    """Return the hour-stem for (day_stem, hour_branch) per the 5-rule 五鼠遁."""
    start = _HOUR_STEM_START[day_stem]
    branch_idx = L.BRANCH_INDEX[hour_branch]
    return L.STEM_ORDER[(start + branch_idx) % 10]


# Boundary-chart policy (codified 2026-09-20, external report review I7):
# hour branches are 2-hour solar windows starting on odd hours (子 23:00,
# 丑 01:00, 寅 03:00, …). A corrected solar time within this many minutes of a
# window edge is a "knife-edge" birth — a few minutes of recorded-clock error
# would flip the hour pillar. Policy: never silently pick a side. The engine
# always reports the branch its own math lands on as `hour_pillar`, but when
# within the margin it also emits `hour_boundary` (distance + the neighboring
# alternate pillar) in `solar_correction`, so JSON/CLI consumers and report
# authors see both readings and the reader decides which to narrate — see
# `knowledge/09-interpretation-method.md` Step 0 and premium_report.py's
# `_solar_time_note`, which renders this as the "⚠ Hour-boundary note".
HOUR_BOUNDARY_MARGIN_MIN = 10

_BRANCH_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _hour_boundary_info(
    eff_hour: int,
    eff_minute: int,
    correct_branch: str,
    correct_stem: str,
    day_stem: str,
) -> Optional[Dict[str, Any]]:
    """Return boundary-margin metadata when the hour is a knife-edge case.

    Returns None when the corrected time is not within
    ``HOUR_BOUNDARY_MARGIN_MIN`` of a branch-window edge, or when the
    ambiguous edge is the 子 (23:00/01:00) boundary — that boundary also
    flips which calendar day (and therefore which day-stem) drives the hour
    stem under the Korean 야자시 convention, a compound decision this helper
    does not attempt to re-derive; the existing 子 handling in
    `_hour_stem_day_stem` already covers that case on its own terms.
    """
    minutes = eff_hour * 60 + eff_minute
    raw_mod = (minutes - 60) % 120
    dist = min(raw_mod, 120 - raw_mod)
    if dist > HOUR_BOUNDARY_MARGIN_MIN:
        return None
    idx = _BRANCH_ORDER.index(correct_branch)
    alt_branch = _BRANCH_ORDER[(idx - 1) % 12] if raw_mod <= 60 else _BRANCH_ORDER[(idx + 1) % 12]
    if correct_branch == "子" or alt_branch == "子":
        return None
    alt_stem = _hour_stem(day_stem, alt_branch)
    return {
        "distance_minutes": dist,
        "primary_hour_pillar": f"{correct_stem}{correct_branch}",
        "alternate_hour_pillar": f"{alt_stem}{alt_branch}",
        "note": (
            "Corrected solar time is within the boundary margin of a 2-hour "
            "branch window; the alternate hour pillar is a plausible reading "
            "if the recorded clock time carries a few minutes of error."
        ),
    }


def _day_stem_for_date(year: int, month: int, day: int) -> str:
    """Return the day-stem for a calendar date using the 60-cycle anchor.

    Anchor: 1900-01-01 = 甲戌 (index 10), verified against sajupy.
    """
    anchor = date(1900, 1, 1)
    target = date(year, month, day)
    delta = (target - anchor).days
    idx = (10 + delta) % 60
    return L.JIAZI_CYCLE[idx][0]


def _parse_solar_time(raw: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    """Parse the solar-corrected time string from sajupy output.

    Returns (hour, minute) or None if no correction was applied.
    """
    info = raw.get("solar_correction")
    if not info:
        return None
    solar_time = info.get("solar_time")
    if not solar_time:
        return None
    try:
        h, m = map(int, solar_time.split(":"))
        return h, m
    except (ValueError, AttributeError):
        return None


def _effective_time(
    hour: int,
    minute: int,
    raw: Dict[str, Any],
    use_solar_time: bool,
) -> Tuple[int, int]:
    """Return the effective (hour, minute) used for branch/stem derivation."""
    if use_solar_time:
        parsed = _parse_solar_time(raw)
        if parsed is not None:
            return parsed
    return hour, minute


def _compute_adjusted_date(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    solar_correction: Optional[Dict[str, Any]],
) -> Tuple[Tuple[int, int, int], int]:
    """Return the solar-adjusted (effective) calendar date and day delta.

    The delta is the number of calendar days the true solar time has rolled
    backward or forward from the original birth date. Example: a birth at
    2000-01-01 00:30 with a -60 minute solar correction lands on
    1999-12-31 23:30, so the adjusted date is (1999, 12, 31) and delta is -1.
    """
    if not solar_correction:
        return (year, month, day), 0
    correction_minutes = solar_correction.get("correction_minutes", 0)
    if not correction_minutes:
        return (year, month, day), 0
    original = datetime(year, month, day, hour, minute)
    adjusted = original + timedelta(minutes=correction_minutes)
    adjustment_days = (adjusted.date() - date(year, month, day)).days
    return (adjusted.year, adjusted.month, adjusted.day), adjustment_days


def _effective_calendar_date(
    year: int,
    month: int,
    day: int,
    raw: Dict[str, Any],
    use_solar_time: bool,
) -> Tuple[int, int, int]:
    """Return the calendar date that sajupy used after solar-time adjustment."""
    info = raw.get("solar_correction")
    if use_solar_time and info:
        adjusted = raw.get("adjusted_date")
        if adjusted:
            return adjusted
    return year, month, day


def _hour_stem_day_stem(raw: Dict[str, Any], eff_hour: int, convention: str) -> str:
    """Return the day-stem that should drive the hour-stem 五鼠遁 calculation.

    sajupy has already computed the effective day-pillar, including solar-time
    date rollbacks and the Chinese 早子時 day advancement. We therefore derive
    the hour-stem from `raw['day_stem']` rather than from the original input
    date, which avoids the old bug where a solar-rollback birth used the wrong
    day for the 23:00 子 hour stem.

    Korean 야자시 refinement (2026-09-13): for a birth whose effective hour is
    23 under the korean convention, sajupy retains the current day's pillar
    (夜子時), but the Korean 명리 school derives the hour-stem from the NEXT
    day's 일간 in that window. Verified against two independent 만세력 sites in
    야자시 mode (1990-06-15 23:40 서울 → 일주 辛亥 retained, 시주 庚子 from
    next-day 일간 壬). The chinese convention needs no adjustment: sajupy has
    already advanced the day pillar there, and 五鼠遁 from the advanced stem is
    the mainland rule. With this, both conventions agree on the hour-stem
    (next-day 일간) and differ only in whether the day pillar advances.
    """
    day_stem = raw["day_stem"]
    if eff_hour == 23 and convention == "korean":
        return L.STEM_ORDER[(L.STEM_INDEX[day_stem] + 1) % 10]
    return day_stem


def _equation_of_time_minutes(year: int, month: int, day: int) -> float:
    """Equation of time (분시차, 均時差), in minutes, for the given calendar date.

    True (apparent) solar time — the basis for classical 사주 hour-branch
    determination — is Local Mean Time (LMT, the pure longitude correction
    sajupy already applies) PLUS the equation of time: the seasonal
    difference between the mean sun and the true sun caused by Earth's
    orbital eccentricity and axial tilt. It ranges roughly -14 to +16 minutes
    across the year and is NOT a classical-interpretation question — it is
    physics that classical 진태양시 (true solar time) already assumes, the
    same way the longitude correction does.

    Added 2026-09-19 (external report review): sajupy's own solar-time
    correction (`sajupy/core.py::_calculate_solar_time_correction`) is pure
    `(longitude - standard_longitude) * 4`, with no equation-of-time term —
    confirmed by reading its source. This under-states true-solar-time
    uncertainty for any birth near an hour-branch boundary (e.g. Harish's,
    whose stated ~3-minute margin was really closer to ~1 minute once EoT is
    included). This engine applies EoT itself, on top of sajupy's longitude
    term, rather than modifying the third-party dependency.

    Formula: the standard Spencer (1971) / NOAA approximation,
    EoT = 9.87·sin(2B) − 7.53·cos(B) − 1.5·sin(B) minutes, where
    B = (360/365)·(N − 81) degrees and N is the day of year. Accurate to
    within about 30 seconds across the year — consistent with the
    whole-minute precision already used elsewhere in this module.
    """
    n = date(year, month, day).timetuple().tm_yday
    b = math.radians(360.0 / 365.0 * (n - 81))
    return 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)


def _apply_equation_of_time(
    raw: Dict[str, Any],
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
) -> None:
    """Add the equation of time to sajupy's longitude-only solar correction, in place.

    No-op if sajupy reports no solar correction (e.g. ``use_solar_time=False``
    or no city/longitude supplied) — there is nothing to refine.
    """
    sc = raw.get("solar_correction")
    if not sc:
        return
    base_minutes = sc.get("correction_minutes", 0) or 0
    eot_minutes = _equation_of_time_minutes(year, month, day)
    total_minutes = base_minutes + eot_minutes
    adjusted = datetime(year, month, day, hour, minute) + timedelta(minutes=total_minutes)
    sc["correction_minutes"] = round(total_minutes, 1)
    sc["equation_of_time_minutes"] = round(eot_minutes, 1)
    sc["solar_time"] = adjusted.strftime("%H:%M")


# Time-zone standard meridians (utc_offset * 15) are a political convention,
# not a geographic one: a zone can be adopted to match a neighbor rather than
# the zone's own longitude. Korea Standard Time (UTC+9) uses Japan's 135°E
# meridian, but Korean cities sit near 124-131°E, and classical Korean Saju
# practice corrects against 127.5°E (the meridian Korea used 1908-1912 and
# 1954-1961) rather than 135°E. Without this override, every correctly
# geocoded Korean city trips the "verify the city name" warning below.
_KOREAN_SAJU_STANDARD_MERIDIAN = 127.5


def _warn_if_suspicious_longitude(
    raw: Dict[str, Any],
    city: Optional[str],
    user_longitude: Optional[float],
    utc_offset: float,
    convention: str = "korean",
) -> None:
    """Emit a stderr warning if the resolved longitude looks suspicious.

    City geocoding can be unreliable (e.g. "Pallipat" returning ~76.33°E while the
    real location is ~79.32°E). We warn when the geocoded longitude deviates from
    the user's explicit longitude or from the UTC-offset standard meridian by
    more than 5°, which corresponds to ~20 minutes of solar time.
    """
    if not city:
        return
    info = raw.get("solar_correction")
    if not info:
        return
    source = info.get("longitude_source")
    geocoded = info.get("longitude")
    if geocoded is None:
        # C6: geocoding failed to return a longitude.
        fallback = user_longitude if user_longitude is not None else utc_offset * 15.0
        info["longitude"] = fallback
        info["longitude_source"] = "fallback_standard_meridian" if user_longitude is None else "fallback_user_longitude"
        if user_longitude is None:
            sys.stderr.write(
                f"Warning: city '{city}' geocoding did not return a longitude. "
                f"Falling back to standard meridian {fallback}° (utc_offset * 15). "
                "For accurate solar-time correction, pass --longitude explicitly.\n"
            )
        return
    if source != "geocoded":
        return

    if convention == "korean" and utc_offset == 9.0:
        standard_lon = _KOREAN_SAJU_STANDARD_MERIDIAN
    else:
        standard_lon = utc_offset * 15.0
    if user_longitude is not None and abs(geocoded - user_longitude) > 5.0:
        sys.stderr.write(
            f"Warning: geocoded longitude for '{city}' is {geocoded}°, but "
            f"you passed --longitude {user_longitude}°. The values differ by "
            f"more than 5° (~20 min solar time). Using --longitude value.\n"
        )
        return
    if abs(geocoded - standard_lon) > 5.0:
        sys.stderr.write(
            f"Warning: geocoded longitude for '{city}' is {geocoded}°, which is "
            f"more than 5° from the standard meridian {standard_lon}° for UTC offset "
            f"{utc_offset}. Verify the city name or pass --longitude explicitly.\n"
        )


def _derive_zi_time_type(effective_hour: int, convention: str) -> Optional[str]:
    """Return a clear metadata label for the Zi hour handling."""
    if effective_hour != 23:
        return None
    if convention == "korean":
        return "夜子時 (Korean 야자시)"
    return "早子時 (Chinese 조자시)"


def compute_pillars(
    *,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    city: Optional[str] = None,
    longitude: Optional[float] = None,
    utc_offset: float = 9.0,
    use_solar_time: bool = True,
    convention: str = "korean",
    early_zi_time: Optional[bool] = None,
    korean_yazi: Optional[bool] = None,
) -> Dict[str, Any]:
    """Return the four pillars + extra metadata from sajupy, corrected for convention.

    Parameters
    ----------
    convention:
        ``"korean"`` (default) uses Korean 명리 야자시 semantics:
        23:00–00:59 belongs to the current calendar day's 子 hour with the day
        pillar retained; the hour-stem in the 23:00–24:00 window is derived
        from the NEXT day's day-stem (夜子時), while a 00:00–00:59 birth uses
        the current day's day-stem (早子時).

        ``"chinese"`` uses mainland BaZi-style 조자시 semantics:
        23:00–23:59 belongs to the next calendar day's 子 hour, and the
        day-pillar advances; the hour-stem is derived from the next day's
        day-stem.

    early_zi_time / korean_yazi:
        Legacy parameters kept for backward compatibility. ``korean_yazi``
        overrides ``convention`` if provided. ``early_zi_time`` is ignored
        because the correct sajupy flag is chosen internally from ``convention``.
    """
    # Backward compatibility: korean_yazi boolean overrides convention.
    if korean_yazi is not None:
        convention = "korean" if korean_yazi else "chinese"
    convention = convention.lower()
    if convention not in ("korean", "chinese"):
        raise ValueError(f"convention must be 'korean' or 'chinese', got {convention!r}")

    # sajupy internal flag: True = keep current day at 23:00 (Korean day pillar),
    # False = advance to next day at 23:00 (Chinese day pillar).
    sajupy_early_zi = convention == "korean"

    raw = None
    # sajupy prints a "Warning: Could not get longitude information..." line to
    # **stdout** when neither --city nor --longitude is supplied. That corrupts
    # --format json output (the warning lands ahead of the opening `{` and
    # breaks json.loads). Capture stdout during the sajupy call and re-emit any
    # captured text to stderr so JSON/table output stays clean.
    _captured = io.StringIO()
    with contextlib.redirect_stdout(_captured):
        raw = calculate_saju(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            city=city,
            longitude=longitude,
            utc_offset=utc_offset,
            use_solar_time=use_solar_time,
            early_zi_time=sajupy_early_zi,
        )
    _captured_text = _captured.getvalue().strip()
    if _captured_text:
        sys.stderr.write(_captured_text + "\n")

    # Geocoding sanity checks.
    _warn_if_suspicious_longitude(raw, city, longitude, utc_offset, convention)

    # Refine sajupy's longitude-only solar correction with the equation of
    # time (see _apply_equation_of_time docstring). No-op if sajupy applied
    # no correction at all.
    if use_solar_time:
        _apply_equation_of_time(raw, year, month, day, hour, minute)

    # Compute the solar-adjusted calendar date and expose it as metadata.
    # This is needed both for the hour-stem correction and for downstream
    # reporting (Chart.effective_date / CLI output).
    adjusted_date, date_adjustment = _compute_adjusted_date(
        year, month, day, hour, minute, raw.get("solar_correction")
    )
    raw["adjusted_date"] = adjusted_date
    raw["date_adjustment"] = date_adjustment

    # Determine the effective time and date that sajupy used.
    eff_hour, eff_minute = _effective_time(hour, minute, raw, use_solar_time)
    eff_date = _effective_calendar_date(year, month, day, raw, use_solar_time)

    # Recompute the hour branch from the effective time. sajupy already does this
    # when use_solar_time=True, but we repeat it here as an auditable check.
    correct_hour_branch = _hour_branch(eff_hour, eff_minute)

    # Determine the day-stem that drives the hour-stem under the chosen convention.
    hour_stem_day_stem = _hour_stem_day_stem(raw, eff_hour, convention)

    # Compute the correct hour stem.
    correct_hour_stem = _hour_stem(hour_stem_day_stem, correct_hour_branch)

    # Update raw if anything differs.
    if correct_hour_branch != raw.get("hour_branch"):
        raw["hour_branch"] = correct_hour_branch
    if correct_hour_stem != raw.get("hour_stem"):
        raw["hour_stem"] = correct_hour_stem
    raw["hour_pillar"] = f"{raw['hour_stem']}{raw['hour_branch']}"

    boundary_info = _hour_boundary_info(
        eff_hour, eff_minute, correct_hour_branch, correct_hour_stem, hour_stem_day_stem
    )
    if boundary_info is not None and raw.get("solar_correction"):
        raw["solar_correction"]["hour_boundary"] = boundary_info

    raw["zi_time_type"] = _derive_zi_time_type(eff_hour, convention)
    raw["convention"] = convention

    return raw


# Light validation: print the result in a fixed order for use in tests / debugging.
def pretty(result: Dict[str, Any]) -> str:
    keys = [
        "year_pillar", "month_pillar", "day_pillar", "hour_pillar",
        "year_stem", "year_branch", "month_stem", "month_branch",
        "day_stem", "day_branch", "hour_stem", "hour_branch",
        "birth_date", "birth_time", "zi_time_type", "convention",
    ]
    lines = [f"  {k}: {result.get(k)}" for k in keys if k in result]
    return "\n".join(lines)
