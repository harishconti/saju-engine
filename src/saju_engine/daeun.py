"""Compute the major-luck (대운) sequence.

The rules are in knowledge/08-luck-pillars.md, Part 1:
  - Direction: yang-year-male or yin-year-female → forward; else backward
  - Starting age: count days from birth to the previous or next solar term of
    the month branch, divide by 3
  - Each major luck lasts 10 years
  - Forward = month_pillar + 1 step in the 60-cycle, then +2, etc.
  - Backward = month_pillar - 1 step, then -2, etc.

This module:
  - Computes the 60-cycle index for a given pillar
  - Steps the 60-cycle forward or backward by N
  - Computes the starting age (delegating the solar-term math to sajupy)
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

from . import lookup as L
from .chart import DaeunPeriod


def _ipchun_date(year: int) -> Optional[datetime]:
    """Return the 입춘 (立春) datetime for `year`, or None if unavailable.

    입춘 is the 사주 new-year boundary: a person's 사주 age (세수) increments at
    입춘, not on Jan 1 or the solar birthday. Used by `saju_age()`.
    """
    terms = _parse_calendar().get(str(year), [])
    for dt, hanja, term_time in terms:
        if hanja == "立春":
            return _parse_term_time(term_time, dt)
    return None


def saju_year(d: date) -> int:
    """Return the 사주 year (연도) of a Gregorian date: on/after that year's
    입춀 belongs to that year; before it belongs to the prior year.

    N-11 (2026-09-26 audit): client-facing "What This Year Means"/annual-luck
    prose used `reference_date.year` (the raw Gregorian year) as the CURRENT
    세운's label. For a reference date between Jan 1 and 입춀 (~Feb 4), the
    active 세운 is still the PRIOR year's — the pillar shown was already
    correct (the lookup keys off the same Gregorian year the sewoon window
    was built from), but the prose then said e.g. "As of 2026, the annual
    pillar is 乙巳" even though 乙巳 is 2025's canonical pillar, contradicting
    the chart's own 입춀-based `current_age`/대운 timing. Factored out of
    `saju_age()`, which already computed this same thing internally for both
    the birth year and "today".
    """
    ipchun = _ipchun_date(d.year)
    if ipchun is not None and d < ipchun.date():
        return d.year - 1
    return d.year


def saju_age(birth_date_str: str, today: Optional[date] = None) -> Optional[int]:
    """Return the 사주 세수 (Korean counting age, 입춀-based) on `today`.

    The 대운 ``start_age`` is computed by the 3-day=1-year rule and is expressed
    in **세수** (birth = 1, +1 at each 입춘). To select the current 대운 period,
    the current age must be in the **same** 세수 convention — mixing 세수
    start_age with a 만 나이 (western age) current_age can select the wrong
    10-year period by 1–2 years (A5 fix; see knowledge/08-luck-pillars.md).

    세수 = (saju_year_today - saju_year_of_birth) + 1, where the saju year is
    reckoned from 입춀: a date on/after 입춀 belongs to that solar year; a date
    before 입춀 belongs to the prior year. Returns None if the birth string or
    입춀 data is unavailable.
    """
    try:
        by, bm, bd = (int(x) for x in birth_date_str.split("-"))
    except (ValueError, AttributeError):
        return None
    today = today or datetime.now().date()
    if isinstance(today, datetime):
        today = today.date()

    birth = date(by, bm, bd)
    return saju_year(today) - saju_year(birth) + 1


# ── 60-cycle (육십갑자) math ─────────────────────────────────────────────────
# Imported from lookup.py so the whole engine shares one canonical cycle.


def step_cycle(stem: str, branch: str, n: int) -> Tuple[str, str]:
    """Return the pillar `n` steps forward (n>0) or backward (n<0) in the 60 cycle."""
    return L.step_cycle(stem, branch, n)


# ── Starting-age calculation ───────────────────────────────────────────────
# Per knowledge/08-luck-pillars.md: count days from birth date to the
# previous or next 節氣 (month-opener, one of 12), divide by 3.
# (1 day = 4 months, 3 days = 1 year.)
#
# sajupy's calendar_data.csv has all 24 jieqi per year. The 12 節氣 (立春,
# 驚蟄, 淸明, 立夏, 芒種, 小暑, 立秋, 白露, 寒露, 立冬, 大雪, 小寒) are the
# month-opener terms that define the 12 Saju months. We use those as the
# term boundaries.
#
# The classical Korean 명리 rule (per 적천수, 궁통보감, and standard
# Korean-school textbooks):
#   - 순행 (forward): count to the NEXT 節氣 after the birth date
#   - 역행 (backward): count to the PREVIOUS 節氣 before the birth date
# The "same season" qualifier in knowledge/08-luck-pillars.md is a
# refinement that doesn't match the canonical tradition — the actual
# tradition just uses the next/previous 節氣 in the 12-節氣 cycle.
#
# Schema of sajupy/calendar_data.csv:
#   year,month,day,year_pillar,month_pillar,day_pillar,lunar_year,
#   lunar_month,lunar_day,solar_term_hanja,solar_term_korean,term_time
# Only rows with solar_term_hanja non-empty are jieqi rows.

# The 12 month-opener 節氣.
_MONTH_OPENER_TERMS = frozenset({
    "立春", "驚蟄", "淸明", "立夏", "芒種", "小暑",
    "立秋", "白露", "寒露", "立冬", "大雪", "小寒",
})

# Cache the parsed calendar CSV (re-read if file changes between calls)
# Value is {year: [(date, hanja, term_time), ...]} where term_time is the raw
# sajupy string YYYYMMDDHHMM (may be empty for non-term rows, but those are
# filtered out here).
_CALENDAR_CACHE: Optional[Dict[str, List[Tuple[date, str, str]]]] = None


def _parse_calendar() -> Dict[str, List[Tuple[date, str, str]]]:
    """Read sajupy/calendar_data.csv and return {year: [(date, hanja, term_time), ...]}.

    Only month-opener 節氣 rows are kept, sorted by date.
    """
    global _CALENDAR_CACHE
    if _CALENDAR_CACHE is not None:
        return _CALENDAR_CACHE
    import csv
    import os
    # Locate the sajupy package via importlib — robust to install location.
    import importlib.util
    spec = importlib.util.find_spec("sajupy")
    if spec is None or spec.origin is None:
        raise ImportError("sajupy is not importable; cannot locate calendar_data.csv")
    sajupy_dir = os.path.dirname(spec.origin)
    csv_path = os.path.join(sajupy_dir, "calendar_data.csv")
    if not os.path.isfile(csv_path):
        # Bug found 2026-09-20 (external code-quality review): this file
        # lives inside sajupy's own install directory (a third-party
        # dependency's internal data file, not this package's own data —
        # sajupy exposes no public API for it), so a raw `open()` failure
        # here surfaces as an unhelpful bare `FileNotFoundError` with no
        # hint about the actual cause (a stripped/incomplete sajupy
        # install). Fail loudly with a diagnostic instead.
        raise FileNotFoundError(
            f"sajupy is importable but its calendar_data.csv is missing at "
            f"{csv_path!r}. This usually means an incomplete or corrupted "
            f"sajupy install — reinstall with "
            f"`pip install --user --break-system-packages --force-reinstall sajupy`."
        )
    by_year: Dict[str, List[Tuple[date, str, str]]] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hanja = (row.get("solar_term_hanja") or "").strip()
            if hanja not in _MONTH_OPENER_TERMS:
                continue
            try:
                y = int(row["year"]); m = int(row["month"]); d = int(row["day"])
                dt = date(y, m, d)
            except (KeyError, ValueError):
                continue
            by_year.setdefault(str(y), []).append((dt, hanja, row.get("term_time", "")))
    for lst in by_year.values():
        lst.sort()
    _CALENDAR_CACHE = by_year
    return by_year


# Bug found 2026-09-25 (external report review, E-1): sajupy's
# calendar_data.csv stores `term_time` in Korea Standard Time regardless of
# the querent's own timezone — confirmed against the raw CSV (1992 芒種:
# `199206051923`, i.e. 19:23 KST = 10:23 UTC, matching an independent
# ephemeris's 10:21 UTC) and against sajupy's own source (`core.py`'s
# `_check_term_time` does a naive `datetime` comparison with no timezone
# conversion at all, and its docstrings assume "UTC 오프셋 (기본값: 9, 한국
# 표준시)"). This engine's own `_term_boundary_datetimes` inherited the same
# naive comparison. For a birth far from KST (the audit's example: New York,
# UTC-5, a 14-hour gap), this is large enough to flip which side of a 절기
# boundary a birth falls on, producing a month pillar that doesn't even fit
# its own year pillar (reproduced and confirmed: 2024-02-04 10:00 EST -> 乙丑,
# which only fits a 戊/癸-year under the 오호둔 rule, not 2024's 甲). For births
# near KST (Korea, India — a 3.5h gap), pillars themselves are rarely
# affected, but the 대운수 (starting-age) day-count still drifts by hours.
KST_OFFSET_HOURS = 9.0


def _term_boundary_datetimes(
    year: int, month: int, day: int, hour: int, minute: int, utc_offset: float,
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Return (prev_term_datetime, next_term_datetime), converted to the
    birth's own timezone, with term times if available.

    ``utc_offset`` is required (no default) so a caller can't silently
    reintroduce the KST/local mismatch bug above by forgetting to pass it.

    Boundary convention (classical, moment-level — see knowledge/08-luck-pillars.md):
      - prev = the last 節氣 whose moment is **at or before** the birth moment.
      - next = the first 節氣 whose moment is **at or after** the birth moment.
      - If the birth moment coincides with a 節기 moment, prev == next == that
        moment, so the starting age is 0 in BOTH directions.
      - Sub-day precision: the birth hour/minute and the CSV term_time are both
        treated as datetimes, so a birth *after* the 절기 moment on a 절기 date
        correctly counts forward to the *following* 절기 (and vice-versa).
    """
    by_year = _parse_calendar()
    # KST -> the birth's own local timezone: local = KST + (utc_offset - 9).
    tz_shift = timedelta(hours=utc_offset - KST_OFFSET_HOURS)
    candidates: List[Tuple[datetime, str]] = []
    for y in (year - 1, year, year + 1):
        for dt, h, term_time in by_year.get(str(y), []):
            candidates.append((_parse_term_time(term_time, dt) + tz_shift, h))
    candidates.sort()

    birth_dt = datetime(year, month, day, hour, minute)

    prev: Optional[datetime] = None  # last term_dt <= birth (inclusive)
    nxt: Optional[datetime] = None   # first term_dt >= birth (inclusive)
    for term_dt, h in candidates:
        if term_dt <= birth_dt and (prev is None or term_dt > prev):
            prev = term_dt
        if term_dt >= birth_dt and nxt is None:
            nxt = term_dt
    return (prev, nxt)


def _parse_term_time(term_time: str, fallback_date: date) -> datetime:
    """Parse sajupy ``term_time`` (YYYYMMDDHHMM) into a naive datetime.

    If the string is missing or malformed, fall back to the term date at
    00:00. The calendar CSV stores term times in a compressed 12-digit format.
    """
    if not term_time:
        return datetime.combine(fallback_date, time(0, 0))
    try:
        y = int(term_time[:4])
        m = int(term_time[4:6])
        d = int(term_time[6:8])
        h = int(term_time[8:10])
        mi = int(term_time[10:12])
        return datetime(y, m, d, h, mi)
    except (ValueError, IndexError):
        return datetime.combine(fallback_date, time(0, 0))


def starting_age(
    year: int,
    month: int,
    day: int,
    direction: str,
    hour: int = 0,
    minute: int = 0,
    utc_offset: float = 9.0,
) -> int:
    """Return the integer starting age of the first major-luck period.

    Direction: 'forward' (순행) means we count to the *next* 節氣;
    'backward' (역행) means we count to the *previous* 節氣.
    Result is complete days // 3 (1 day = 4 months, 3 days = 1 year).

    ``hour`` and ``minute`` are optional. When supplied, the term boundary is
    treated as a datetime (using the term_time in the calendar CSV) and the
    birth moment is compared to the 절기 **moment** — so a birth *after* the
    절기 moment on a 절기 date correctly counts forward to the following 절기,
    and a birth *before* the moment counts backward to the previous 절기.

    ``utc_offset`` defaults to 9.0 (Korea) for convenience, but production
    callers (``compute_daeun``) always pass the chart's real value — see
    ``_term_boundary_datetimes``'s KST-conversion note (E-1, 2026-09-25).
    """
    prev, nxt = _term_boundary_datetimes(year, month, day, hour, minute, utc_offset)
    birth_dt = datetime(year, month, day, hour, minute)
    if direction == "forward":
        target = nxt   # first 절기 at or after the birth moment
    else:
        target = prev  # last 절기 at or before the birth moment
    if target is None:
        # Fall back: use sajupy's lunar→solar to at least get a sensible
        # approximation, or just return 0 and let the caller flag it.
        return 0
    # Birth exactly on a 節氣 date is handled by _term_boundary_datetimes,
    # which returns (birth_dt, birth_dt) and yields 0 days.
    # Use absolute seconds before floor division to avoid rounding toward -inf
    # for 역행 (backward) charts at fractional-day boundaries.
    days = int(abs((target - birth_dt).total_seconds()) // 86400)
    return days // 3


def starting_age_days(
    year: int,
    month: int,
    day: int,
    direction: str,
    hour: int = 0,
    minute: int = 0,
    utc_offset: float = 9.0,
) -> Optional[float]:
    """Return the raw, **fractional** day-count to the qualifying 節氣 that
    `starting_age` floors to a whole year via `days // 3`.

    Bug found 2026-09-20 (external report review, 3rd pass, R19): the report
    never states the precise 대운수 — knowledge/08's own rule is "3 days = 1
    year," so a starting age of, say, 0 actually means "somewhere in [0, 3)
    years," and a chart whose true offset is ~0.3 years (~4 months) reads
    identically to one whose offset is 2.9 years under the rounded integer
    alone. This exposes the underlying day count so report prose can state
    the precise starting age instead of only the rounded decade label.

    Bug found 2026-09-25 (external report review, 4th pass): the R19 fix
    above still truncated to a *whole* day (`int(... // 86400)`) before
    returning, silently discarding up to just-under-1-day of precision. For
    Harish, the true offset is 1.68 days (~0.56 years, ~6.7 months); flooring
    to 1 day first and *then* dividing by 3 produced "~0.3 years (~4
    months)" — understating the true starting-age offset by roughly a factor
    of two. This now returns the unfloored fractional day count so
    `round(days / 3, 1)` downstream is actually precise, not
    falsely-precise-looking. `starting_age()`'s own integer day-count (used
    for the decade-boundary year, via its own separate `days // 3`) is
    unaffected either way — flooring a sub-3-day offset to a whole day
    before or after does not change which whole year it floors into.

    Bug found 2026-09-25 (external report review, E-1): also inherited the
    KST/local timezone mismatch — see ``_term_boundary_datetimes``. For
    Harish (IST), this alone shifted the "1.68 days" figure above to the
    correct ~1.53 days once both bugs were fixed together.
    """
    prev, nxt = _term_boundary_datetimes(year, month, day, hour, minute, utc_offset)
    birth_dt = datetime(year, month, day, hour, minute)
    target = nxt if direction == "forward" else prev
    if target is None:
        return None
    return abs((target - birth_dt).total_seconds()) / 86400.0


def first_period_start_date(
    year: int,
    month: int,
    day: int,
    direction: str,
    hour: int = 0,
    minute: int = 0,
    utc_offset: float = 9.0,
) -> Optional[date]:
    """Return the precise calendar date the first major-luck period begins.

    N-4 (2026-09-26 audit): `starting_age()`'s `days // 3` is a **floored,
    elapsed-year** count for the decade LABEL — it runs 1-2 years below
    `saju_age()`'s 세수 (birth = 1, +1 at every 입춀), so comparing them
    directly (as `engine.py` used to, to pick the "current" 대운) selected
    the next decade 1.3-2.4 years before it actually starts. This returns
    the real calendar date instead.

    Per the "3 days = 1 year" rule, the fractional day count to the
    qualifying 節氣 maps to years as ``days / 3`` (NOT a ``days``-long
    offset) — the whole-year part is added as calendar years and the
    remainder as ``fraction * 365.25`` days, matching how
    `_daeun_starting_age_note` already states the precise starting age.
    """
    days = starting_age_days(year, month, day, direction, hour=hour, minute=minute, utc_offset=utc_offset)
    if days is None:
        return None
    precise_years = days / 3.0
    whole_years = int(precise_years)
    birth = date(year, month, day)
    try:
        shifted = birth.replace(year=birth.year + whole_years)
    except ValueError:
        shifted = birth.replace(year=birth.year + whole_years, day=28)
    return shifted + timedelta(days=(precise_years - whole_years) * 365.25)


# ── Top-level: build the full major-luck sequence ───────────────────────────
def compute_daeun(
    *,
    year_stem: str,
    month_stem: str,
    month_branch: str,
    year: int,
    month: int,
    day: int,
    gender: str,
    n_periods: int = 8,
    hour: int = 0,
    minute: int = 0,
    utc_offset: float = 9.0,
) -> List[DaeunPeriod]:
    """Build `n_periods` major-luck periods starting from the calculated age.

    Returns a list of DaeunPeriod. The first one starts at `starting_age`
    and ends at `starting_age + 9`. The next is +10 years, etc.

    ``hour`` and ``minute`` give sub-day precision for the starting-age count
    (see `starting_age`): the birth moment is compared to the 절기 moment, not
    just the calendar date. Pass the **civil** birth time (not the
    solar-corrected time), since the calendar's 절기 moments, once converted
    to this timezone, are civil-clock instants (N-2, 2026-09-26 audit).

    ``utc_offset`` must be the chart's real birth timezone offset — the
    calendar's 절기 moments are stored in KST and need this to compare
    correctly against a non-KST birth (E-1, 2026-09-25).
    """
    direction = L.daeun_direction(year_stem, gender)
    start_age = starting_age(year, month, day, direction, hour=hour, minute=minute, utc_offset=utc_offset)
    periods: List[DaeunPeriod] = []
    stem, branch = month_stem, month_branch
    for k in range(1, n_periods + 1):
        if direction == "forward":
            stem, branch = step_cycle(month_stem, month_branch, k)
        else:
            stem, branch = step_cycle(month_stem, month_branch, -k)
        periods.append(DaeunPeriod(start_age=start_age + (k - 1) * 10, end_age=0,
                                   stem=stem, branch=branch))
    return periods
