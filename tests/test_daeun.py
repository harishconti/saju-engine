"""Tests for major-luck (대운) direction and starting age."""
from __future__ import annotations

import pytest

from saju_engine.daeun import starting_age, starting_age_days
from saju_engine.lookup import daeun_direction
from saju_engine import lookup as L


@pytest.mark.parametrize(
    "year_stem,gender,expected",
    [
        # Yang year stems
        ("甲", "M", "forward"),
        ("甲", "F", "backward"),
        ("丙", "M", "forward"),
        ("丙", "F", "backward"),
        ("戊", "M", "forward"),
        ("戊", "F", "backward"),
        ("庚", "M", "forward"),
        ("庚", "F", "backward"),
        ("壬", "M", "forward"),
        ("壬", "F", "backward"),
        # Yin year stems
        ("乙", "M", "backward"),
        ("乙", "F", "forward"),
        ("丁", "M", "backward"),
        ("丁", "F", "forward"),
        ("己", "M", "backward"),
        ("己", "F", "forward"),
        ("辛", "M", "backward"),
        ("辛", "F", "forward"),
        ("癸", "M", "backward"),
        ("癸", "F", "forward"),
    ],
)
def test_daeun_direction(year_stem, gender, expected):
    assert daeun_direction(year_stem, gender) == expected


@pytest.mark.parametrize("bad_gender", [None, "x", "female", "male", ""])
def test_daeun_direction_rejects_invalid_gender(bad_gender):
    with pytest.raises(ValueError):
        daeun_direction("甲", bad_gender)


@pytest.mark.parametrize(
    "name,year,month,day,gender,expected",
    [
        ("Sruthi", 1993, 12, 11, "F", 8),
        ("Pawan", 1991, 10, 3, "M", 8),
        ("Harish", 1992, 6, 4, "M", 0),
    ],
)
def test_starting_age(name, year, month, day, gender, expected):
    from saju_engine.engine import compute_chart
    c = compute_chart(
        name=name, gender=gender,
        year=year, month=month, day=day, hour=12, minute=0,
        city="Seoul", utc_offset=9, use_solar_time=True,
    )
    direction = daeun_direction(c.year.stem, gender)
    assert starting_age(year, month, day, direction) == expected


def test_starting_age_on_solar_term_zero_only_at_or_after_moment():
    # 2024 立春 falls on 2024-02-04 at 17:00 (per the calendar CSV).
    # A3 fix: the boundary is the 절기 MOMENT, not the calendar date.
    # Birth at 00:00 (before the 17:00 moment):
    #   forward  → next 절기 at-or-after birth = 입춘 17:00 same day → 0 days → 0
    #   backward → prev 절기 at-or-before birth = 소한 2024-01-06 → ~29 days → 9
    assert starting_age(2024, 2, 4, "forward", 0, 0) == 0
    assert starting_age(2024, 2, 4, "backward", 0, 0) == 9
    # Birth at 23:59 (after the 17:00 moment):
    #   forward  → next 절기 = 경칩 2024-03-05 → ~29 days → 9
    #   backward → prev 절기 at-or-before birth = 입춘 17:00 same day → 0 days → 0
    assert starting_age(2024, 2, 4, "forward", 23, 59) == 9
    assert starting_age(2024, 2, 4, "backward", 23, 59) == 0


def test_starting_age_at_exact_term_moment_is_zero():
    # Birth exactly at the 절기 moment (2024-02-04 17:00) → 0 in both directions.
    assert starting_age(2024, 2, 4, "forward", 17, 0) == 0
    assert starting_age(2024, 2, 4, "backward", 17, 0) == 0


def test_starting_age_backward_fractional_day_floors_correctly():
    """Backward elapsed time must be truncated, not rounded toward -inf.

    Birth at 2024-02-06 20:00 is 2 days 3 hours after the previous term
    (입춘 2024-02-04 17:00). The old code did `int(negative // 86400)` and
    produced 3 days → age 1; the fix uses `abs(seconds) // 86400` and yields
    2 days → age 0.
    """
    assert starting_age(2024, 2, 6, "backward", 20, 0) == 0


# ── R19 — precise 대운수 was never exposed, only the rounded integer year ──
# ── (found 2026-09-20, external report review, 3rd pass) ─────────────────


def test_starting_age_days_matches_starting_age_floor_division():
    """`int(starting_age_days()) // 3` must equal `starting_age()` for the
    same inputs — `starting_age_days` exposes the raw (fractional) day count
    that `starting_age` silently floors, so report prose can state the
    precise 대운수 (e.g. Harish, IST: ~1.54 days -> ~0.5 years, not a bare
    "age 0"). `starting_age_days` itself returns a float since 2026-09-25
    (external report review, 4th pass) — see its docstring — so the
    floor-to-whole-day step happens here, not inside it. `utc_offset=5.5`
    (Harish's real IST offset) is passed explicitly — see E-1 below for why
    the default (9.0, Korea) would silently give a different, wrong answer."""
    days = starting_age_days(1992, 6, 4, "forward", 2, 59, utc_offset=5.5)
    assert days is not None
    assert int(days) // 3 == starting_age(1992, 6, 4, "forward", 2, 59, utc_offset=5.5)


def test_harish_starting_age_days_is_small_not_a_clean_zero():
    """Harish's real starting age rounds to the integer 0, but the true
    offset is ~1.54 days (~0.51 years, ~6 months) — not the clean "0" the
    decade label alone would suggest, and not the ~1.68 days/~0.6 years/~7
    months an earlier (2026-09-25, external report review, 4th pass) fix
    reported before the E-1 timezone bug (immediately below) was also
    fixed. `utc_offset=5.5` is Harish's real IST offset."""
    days = starting_age_days(1992, 6, 4, "forward", 2, 59, utc_offset=5.5)
    assert days is not None
    assert 0 <= days <= 3
    assert starting_age(1992, 6, 4, "forward", 2, 59, utc_offset=5.5) == 0


# ── E-1 — 절기 term times are stored in KST but were compared against the ──
# ── birth's raw local time with no conversion (found 2026-09-25, external ──
# ── report review) ──────────────────────────────────────────────────────


def test_term_boundary_requires_utc_offset_conversion():
    """The raw CSV term_time for 1992 芒種 is `199206051923` — 19:23 **KST**
    (= 10:23 UTC, matching an independent ephemeris's 10:21 UTC). Comparing
    that directly against an IST (UTC+5:30) birth with no conversion (the
    pre-fix behavior) overstates the elapsed time by the 3.5-hour KST/IST
    gap: pre-fix ~1.68 days, correct ~1.54 days."""
    days_correct = starting_age_days(1992, 6, 4, "forward", 2, 59, utc_offset=5.5)
    days_no_conversion = starting_age_days(1992, 6, 4, "forward", 2, 59, utc_offset=9.0)
    assert days_correct == pytest.approx(1.5375, abs=0.01)
    assert days_no_conversion == pytest.approx(1.6833, abs=0.01)
    assert days_correct != days_no_conversion


def test_new_york_birth_month_pillar_matches_its_own_year_pillar():
    """Reproduces the audit's headline example: a 2024-02-04 10:00 EST birth
    (UTC-5, a 14-hour gap from KST — large enough to flip which side of a
    절기 boundary the birth falls on, unlike Harish's 3.5-hour IST gap).

    Before this fix, `compute_chart` returned month pillar 乙丑 — which does
    not even fit its own year pillar 甲辰: under the 오호둔 (five-tigers) rule,
    乙 as a 丑-month stem only occurs for a 戊/癸-year (e.g. 2023 癸卯), never
    for 甲. That mismatch is decisive proof of a bug, independent of what the
    "true" pillar should be. This is the pillars-page's own regression test;
    see engine.py's independent month/year-pillar recomputation for the fix.
    """
    from saju_engine.engine import compute_chart

    chart = compute_chart(
        name="NY-E1-regression", gender="M",
        year=2024, month=2, day=4, hour=10, minute=0,
        utc_offset=-5, longitude=-74.0, use_solar_time=True, convention="korean",
    )
    FIVE_TIGERS = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
                   "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}
    STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    year_stem = chart.year.stem
    # Branches step through a 12-cycle from 寅; stems only cycle through 10 —
    # reduce mod 12 first (11 branch-steps from 寅 to 丑) before applying that
    # step count to the 10-stem cycle, or the two moduli interfere and can
    # coincidentally reproduce a wrong stem (caught in review: an earlier
    # version of this formula combined both steps under a single `% 10` and
    # silently matched the buggy engine output instead of catching it).
    branch_steps = (L.BRANCH_INDEX[chart.month.branch] - L.BRANCH_INDEX["寅"]) % 12
    dz_stem = STEMS[(STEMS.index(FIVE_TIGERS[year_stem]) + branch_steps) % 10]
    assert chart.month.stem == dz_stem, (
        f"month pillar {chart.month.combined} does not fit year pillar {chart.year.combined} "
        f"under the 오호둔 rule: expected stem {dz_stem} for branch {chart.month.branch}, got {chart.month.stem}"
    )


def test_compute_daeun_n_periods():
    from saju_engine.daeun import compute_daeun
    periods = compute_daeun(
        year_stem="甲", month_stem="丙", month_branch="寅",
        year=1993, month=12, day=11,
        gender="F", n_periods=10,
    )
    assert len(periods) == 10
    assert periods[0].start_age == starting_age(1993, 12, 11, "backward")

