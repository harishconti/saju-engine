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

from datetime import date, datetime, time
from typing import List, Optional, Tuple

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
    ipchun_birth = _ipchun_date(by)
    ipchun_today = _ipchun_date(today.year)

    # 사주 year of birth: birth on/after 입춀 → birth_year; else birth_year - 1.
    if ipchun_birth is not None and birth < ipchun_birth.date():
        saju_birth_year = by - 1
    else:
        saju_birth_year = by

    # 사주 year of today: today on/after 입춀 → today.year; else today.year - 1.
    if ipchun_today is not None and today < ipchun_today.date():
        saju_today_year = today.year - 1
    else:
        saju_today_year = today.year

    return saju_today_year - saju_birth_year + 1


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


def _term_boundary_datetimes(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0,
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Return (prev_term_datetime, next_term_datetime) with term times if available.

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
    candidates: List[Tuple[datetime, str]] = []
    for y in (year - 1, year, year + 1):
        for dt, h, term_time in by_year.get(str(y), []):
            candidates.append((_parse_term_time(term_time, dt), h))
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
    """
    prev, nxt = _term_boundary_datetimes(year, month, day, hour, minute)
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
    """
    prev, nxt = _term_boundary_datetimes(year, month, day, hour, minute)
    birth_dt = datetime(year, month, day, hour, minute)
    target = nxt if direction == "forward" else prev
    if target is None:
        return None
    return abs((target - birth_dt).total_seconds()) / 86400.0


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
) -> List[DaeunPeriod]:
    """Build `n_periods` major-luck periods starting from the calculated age.

    Returns a list of DaeunPeriod. The first one starts at `starting_age`
    and ends at `starting_age + 9`. The next is +10 years, etc.

    ``hour`` and ``minute`` give sub-day precision for the starting-age count
    (see `starting_age`): the birth moment is compared to the 절기 moment, not
    just the calendar date. Pass the **solar-corrected** birth time when the
    chart was computed with `use_solar_time=True`, so the 대운 boundary aligns
    with the same moment the pillars were derived from.
    """
    direction = L.daeun_direction(year_stem, gender)
    start_age = starting_age(year, month, day, direction, hour=hour, minute=minute)
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
