"""Tests for major-luck (대운) direction and starting age."""
from __future__ import annotations

import pytest

from saju_engine.daeun import starting_age, starting_age_days
from saju_engine.lookup import daeun_direction


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
    """`starting_age_days() // 3` must equal `starting_age()` for the same
    inputs — `starting_age_days` exposes the raw day count that `starting_age`
    silently floors, so report prose can state the precise 대운수 (e.g.
    Harish: ~1 day -> ~0.3 years, not a bare "age 0")."""
    days = starting_age_days(1992, 6, 4, "forward", 2, 59)
    assert days is not None
    assert days // 3 == starting_age(1992, 6, 4, "forward", 2, 59)


def test_harish_starting_age_days_is_small_not_a_clean_zero():
    """Harish's real starting age rounds to the integer 0, but the true
    offset is ~1 day (~0.3 years, ~4 months) — the reviewer's exact
    complaint that "the first 대운 begins ~4 months after birth" was
    invisible behind the clean "0" decade label."""
    days = starting_age_days(1992, 6, 4, "forward", 2, 59)
    assert days is not None
    assert 0 <= days <= 3
    assert starting_age(1992, 6, 4, "forward", 2, 59) == 0


def test_compute_daeun_n_periods():
    from saju_engine.daeun import compute_daeun
    periods = compute_daeun(
        year_stem="甲", month_stem="丙", month_branch="寅",
        year=1993, month=12, day=11,
        gender="F", n_periods=10,
    )
    assert len(periods) == 10
    assert periods[0].start_age == starting_age(1993, 12, 11, "backward")

