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
from typing import Any, Dict, List, Optional, Tuple

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
    precise_minutes: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Return boundary-margin metadata when the hour is a knife-edge case.

    ``precise_minutes`` (minutes since midnight, fractional) is the corrected
    solar time before rounding to HH:MM. When given, the result also carries
    ``distance_seconds``: the audit (2026-09-25, calculation-layer table)
    found Harish's true margin is ~28 seconds, which the whole-minute
    ``distance_minutes`` rounds to 0 or 1 depending on the path.

    Returns None when the corrected time is not within
    ``HOUR_BOUNDARY_MARGIN_MIN`` of a branch-window edge.

    When the ambiguous edge is the 子 (23:00/01:00) boundary, that boundary
    *also* flips which calendar day (and therefore which day-stem) drives
    the hour stem under the Korean 야자시 convention — and, right at 23:00,
    the day pillar itself under the Chinese 조자시 convention. N-15
    (2026-09-26 audit): this used to return None here with no disclosure at
    all for the single costliest edge in the whole chart. This helper still
    does not re-derive the alternate day/hour-stem combination (the existing
    logic in `_hour_stem_day_stem` covers that on its own terms) but now
    flags the compound edge so the report can at least warn the reader.
    """
    minutes = eff_hour * 60 + eff_minute
    raw_mod = (minutes - 60) % 120
    dist = min(raw_mod, 120 - raw_mod)
    if dist > HOUR_BOUNDARY_MARGIN_MIN:
        return None
    idx = _BRANCH_ORDER.index(correct_branch)
    alt_branch = _BRANCH_ORDER[(idx - 1) % 12] if raw_mod <= 60 else _BRANCH_ORDER[(idx + 1) % 12]
    if correct_branch == "子" or alt_branch == "子":
        return {
            "distance_minutes": dist,
            "is_zi_boundary": True,
            "primary_hour_pillar": f"{correct_stem}{correct_branch}",
            "note": (
                "Corrected solar time is within the boundary margin of the 子 "
                "(23:00/01:00) hour edge. Unlike other hour boundaries, this one "
                "can also change which calendar day's stem drives the hour pillar "
                "(and, right at 23:00, the day pillar itself) — a compound "
                "decision this note does not attempt to resolve automatically."
            ),
        }
    alt_stem = _hour_stem(day_stem, alt_branch)
    info: Dict[str, Any] = {
        "distance_minutes": dist,
        "primary_hour_pillar": f"{correct_stem}{correct_branch}",
        "alternate_hour_pillar": f"{alt_stem}{alt_branch}",
        "note": (
            "Corrected solar time is within the boundary margin of a 2-hour "
            "branch window; the alternate hour pillar is a plausible reading "
            "if the recorded clock time carries a few minutes of error."
        ),
    }
    if precise_minutes is not None:
        p_mod = (precise_minutes - 60) % 120
        info["distance_seconds"] = int(round(min(p_mod, 120 - p_mod) * 60))
    return info




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
    # Unrounded total, so the hour-boundary check can measure sub-minute
    # margins (see _hour_boundary_info's precise_minutes).
    sc["correction_minutes_exact"] = total_minutes
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


# ── Independent month/year pillar verification (E-1, 2026-09-25) ───────────
# sajupy's month-pillar determination compares a KST-stored 절기 moment
# against the birth's raw local time with no timezone conversion — the same
# root cause as daeun.py's starting-age bug (see daeun.KST_OFFSET_HOURS's
# docstring for the CSV-timezone evidence). For a birth far from KST (the
# reproduction case: New York, UTC-5, a 14-hour gap — large enough to flip
# which side of a 절기 boundary the birth falls on, unlike Korea/India's
# 0-3.5h gaps) this produces a month pillar that does not even fit its own
# year pillar under 오호둔: 2024-02-04 10:00 EST -> sajupy gives 乙丑, valid
# only for a 戊/癸-year, while the year pillar stays 甲辰 — sajupy's year and
# month determinations are evidently inconsistent internally, not just
# individually wrong. This independently recomputes both the Saju year and
# the month pillar using the same, now-timezone-correct term-boundary logic
# 대운수 uses, and *only overrides sajupy's raw values when they disagree* —
# verified to agree with every externally-sourced ("certified") pillar
# fixture in this repo's validation suite before being wired in, so the
# override path is exercised only by the class of birth it targets.

_TERM_TO_MONTH_BRANCH: Dict[str, str] = {
    "立春": "寅", "驚蟄": "卯", "淸明": "辰", "立夏": "巳",
    "芒種": "午", "小暑": "未", "立秋": "申", "白露": "酉",
    "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑",
}

# 오호둔 (五虎遁, "five tigers"): the 寅-month stem for each year-stem pair.
_FIVE_TIGERS: Dict[str, str] = {
    "甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
    "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲",
}

# 1984 is the standard 갑자 (甲子) anchor year — JIAZI_CYCLE[0].
_YEAR_CYCLE_ANCHOR = 1984


# N-15 (2026-09-26 audit, 절기 half): a civil birth time within this many
# minutes of a month-opener 절기 instant gets a knife-edge disclosure. The
# term instants themselves are now accurate to seconds (N-3), so the
# remaining risk is the recorded birth time — and a 절기 flips the month
# pillar (and at 立春 the year pillar), the 격국, strength, 용신 and the
# whole 대운 sequence, so the margin is wider than the hour boundary's.
TERM_BOUNDARY_MARGIN_MIN = 30


def _term_candidates(
    year: int, utc_offset: float,
) -> List[Tuple[datetime, str]]:
    """Month-opener 절기 instants around `year`, in the birth's civil time."""
    from .daeun import KST_OFFSET_HOURS, _parse_calendar, _parse_term_time

    by_year = _parse_calendar()
    tz_shift = timedelta(hours=utc_offset - KST_OFFSET_HOURS)
    candidates: List[Tuple[datetime, str]] = []
    for y in (year - 1, year, year + 1):
        for dt, hanja, term_time in by_year.get(str(y), []):
            candidates.append((_parse_term_time(term_time, dt) + tz_shift, hanja))
    candidates.sort()
    return candidates


def _year_month_pillar_at(
    candidates: List[Tuple[datetime, str]], moment: datetime,
) -> Optional[Dict[str, str]]:
    prev_month_term: Optional[Tuple[datetime, str]] = None
    lichun_year: Optional[int] = None
    for term_dt, hanja in candidates:
        if term_dt > moment:
            break
        prev_month_term = (term_dt, hanja)
        if hanja == "立春":
            lichun_year = term_dt.year
    if prev_month_term is None or lichun_year is None:
        return None

    month_branch = _TERM_TO_MONTH_BRANCH[prev_month_term[1]]
    idx60 = (lichun_year - _YEAR_CYCLE_ANCHOR) % 60
    year_stem, year_branch = L.JIAZI_CYCLE[idx60]
    branch_steps = (L.BRANCH_INDEX[month_branch] - L.BRANCH_INDEX["寅"]) % 12
    month_stem = L.STEM_ORDER[(L.STEM_ORDER.index(_FIVE_TIGERS[year_stem]) + branch_steps) % 10]

    return {
        "year_stem": year_stem, "year_branch": year_branch,
        "month_stem": month_stem, "month_branch": month_branch,
    }


def _independent_year_month_pillar(
    year: int, month: int, day: int, hour: int, minute: int, utc_offset: float,
) -> Optional[Dict[str, str]]:
    """Independently derive the Saju year and month pillar from
    properly-timezone-converted 절기 boundaries.

    Returns None if the birth falls outside the term table's covered
    range — callers should then trust sajupy's raw value unchecked, the same
    fallback `starting_age()` uses.
    """
    return _year_month_pillar_at(
        _term_candidates(year, utc_offset), datetime(year, month, day, hour, minute)
    )


def _term_boundary_info(
    year: int, month: int, day: int, hour: int, minute: int, utc_offset: float,
) -> Optional[Dict[str, Any]]:
    """Return knife-edge metadata when the civil birth time is within
    ``TERM_BOUNDARY_MARGIN_MIN`` of a month-opener 절기 instant, else None.

    Carries the pillars on both sides of the term so the report can name the
    alternate reading, like `_hour_boundary_info` does for the hour pillar.
    """
    candidates = _term_candidates(year, utc_offset)
    birth_dt = datetime(year, month, day, hour, minute)
    nearest = min(candidates, key=lambda c: abs((c[0] - birth_dt).total_seconds()), default=None)
    if nearest is None:
        return None
    term_dt, hanja = nearest
    delta_s = (birth_dt - term_dt).total_seconds()
    if abs(delta_s) > TERM_BOUNDARY_MARGIN_MIN * 60:
        return None
    # The pillar on the far side of the term from the recorded birth moment.
    other_side = term_dt - timedelta(minutes=1) if delta_s >= 0 else term_dt + timedelta(minutes=1)
    primary = _year_month_pillar_at(candidates, birth_dt)
    alternate = _year_month_pillar_at(candidates, other_side)
    if primary is None or alternate is None:
        return None
    return {
        "term": hanja,
        "term_time_local": term_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "distance_minutes": int(round(abs(delta_s) / 60)),
        "birth_is_after_term": delta_s >= 0,
        "primary_year_pillar": primary["year_stem"] + primary["year_branch"],
        "primary_month_pillar": primary["month_stem"] + primary["month_branch"],
        "alternate_year_pillar": alternate["year_stem"] + alternate["year_branch"],
        "alternate_month_pillar": alternate["month_stem"] + alternate["month_branch"],
    }


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

    # Capture sajupy's own (pre-EoT) longitude-only correction so we can
    # later isolate exactly how many EXTRA calendar days the equation of
    # time contributes on top of it (see below).
    _sc_before_eot = raw.get("solar_correction")
    _own_correction_minutes = (_sc_before_eot or {}).get("correction_minutes", 0) or 0

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

    # Recompute the day pillar for the EXTRA calendar-day crossing the
    # equation of time contributes beyond sajupy's own longitude-only
    # correction (F-1, 2026-09-26 audit: a dead helper existed for exactly
    # this but was never wired in). sajupy's raw day_pillar already reflects
    # its own correction plus any zi-hour day-advance convention (see
    # _hour_stem_day_stem's docstring), so we shift that pillar by the delta
    # rather than recomputing it outright from `adjusted_date` — recomputing
    # from scratch would silently discard the zi-advance convention sajupy
    # already applied (regression caught by test_chinese_zi_solar_rollback_hour_stem).
    _own_date_adjustment = _compute_adjusted_date(
        year, month, day, hour, minute, {"correction_minutes": _own_correction_minutes}
    )[1]
    _extra_day_delta = date_adjustment - _own_date_adjustment
    if _extra_day_delta:
        _current_pillar = (raw.get("day_stem"), raw.get("day_branch"))
        if _current_pillar in L.JIAZI_CYCLE:
            _idx = (L.JIAZI_CYCLE.index(_current_pillar) + _extra_day_delta) % 60
            correct_day_stem, correct_day_branch = L.JIAZI_CYCLE[_idx]
            raw["day_stem"] = correct_day_stem
            raw["day_branch"] = correct_day_branch
            raw["day_pillar"] = f"{correct_day_stem}{correct_day_branch}"

    # Determine the effective time that sajupy used.
    eff_hour, eff_minute = _effective_time(hour, minute, raw, use_solar_time)

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

    precise_minutes = None
    sc_exact = (raw.get("solar_correction") or {}).get("correction_minutes_exact")
    if use_solar_time and sc_exact is not None:
        precise_minutes = (hour * 60 + minute + sc_exact) % 1440
    boundary_info = _hour_boundary_info(
        eff_hour, eff_minute, correct_hour_branch, correct_hour_stem, hour_stem_day_stem,
        precise_minutes=precise_minutes,
    )
    if boundary_info is not None and raw.get("solar_correction"):
        raw["solar_correction"]["hour_boundary"] = boundary_info

    raw["zi_time_type"] = _derive_zi_time_type(eff_hour, convention)
    raw["convention"] = convention

    # Independent year/month-pillar cross-check (E-1) — override sajupy's raw
    # values only when they disagree with the timezone-correct recomputation.
    # N-2 (2026-09-26 audit): a 절기 is an absolute instant. The calendar's
    # term times, once converted to the birth's own timezone, are civil-clock
    # instants — so they must be compared against the civil birth time, not
    # the solar-corrected `eff_hour`/`eff_date` (which differ by the
    # longitude correction + equation of time, e.g. ~30 min in Seoul). Using
    # solar time here previously flipped the year/month pillar for any birth
    # within that gap of a 절기.
    independent = _independent_year_month_pillar(
        year, month, day, hour, minute, utc_offset
    )
    if independent is not None:
        disagreement = {
            k: {"sajupy": raw.get(k), "corrected": v}
            for k, v in independent.items()
            if raw.get(k) != v
        }
        if disagreement:
            raw["year_stem"] = independent["year_stem"]
            raw["year_branch"] = independent["year_branch"]
            raw["month_stem"] = independent["month_stem"]
            raw["month_branch"] = independent["month_branch"]
            raw["year_pillar"] = f"{independent['year_stem']}{independent['year_branch']}"
            raw["month_pillar"] = f"{independent['month_stem']}{independent['month_branch']}"
            raw["year_month_correction"] = disagreement

    term_boundary = _term_boundary_info(year, month, day, hour, minute, utc_offset)
    if term_boundary is not None:
        raw["term_boundary"] = term_boundary

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
