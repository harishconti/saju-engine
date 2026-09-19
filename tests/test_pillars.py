"""Tests for solar-time correction and Zi-hour boundary handling."""
from __future__ import annotations

import pytest

from saju_engine.engine import compute_chart
from saju_engine.pillars import _equation_of_time_minutes


# ── Equation of time (added 2026-09-19, external report review) ──────────
# sajupy's own solar correction is longitude-only; this engine adds the
# equation of time on top (pillars.py::_apply_equation_of_time). Reference
# values below are well-known landmarks of the EoT curve (Spencer/NOAA
# approximation): the two extrema (~mid-Feb minimum, ~early-Nov maximum) and
# the zero-crossings (~mid-Apr, ~mid-Jun, ~Sep 1, ~Dec 25).

@pytest.mark.parametrize("month,day,expected_minutes,tolerance", [
    (2, 11, -14.2, 0.5),   # near the annual minimum
    (11, 3, 16.4, 0.5),    # near the annual maximum
    (4, 15, 0.0, 0.3),     # zero-crossing (sundial behind -> ahead of clock)
    (6, 13, 0.0, 0.3),     # zero-crossing (sundial ahead -> behind clock)
    (9, 1, 0.0, 1.0),      # zero-crossing (loosely dated — see NOAA figure)
])
def test_equation_of_time_matches_known_landmarks(month, day, expected_minutes, tolerance):
    got = _equation_of_time_minutes(2000, month, day)
    assert abs(got - expected_minutes) <= tolerance, (
        f"{month}/{day}: expected ~{expected_minutes} min, got {got:.2f} min"
    )


def test_equation_of_time_shifts_solar_time_relative_to_longitude_only():
    """A chart's solar_time must reflect longitude + EoT, not longitude alone.

    Uses a birth on the exact IST meridian (82.5°E, zero longitude term) on a
    date with a well-known non-trivial EoT (~Nov 3, near +16 min) — any
    correction that appears must come entirely from EoT.
    """
    chart = compute_chart(
        name="EoT-check", gender="M",
        year=2000, month=11, day=3, hour=10, minute=0,
        longitude=82.5, utc_offset=5.5, use_solar_time=True,
    )
    sc = chart.solar_correction or {}
    assert sc.get("longitude") == 82.5 == sc.get("standard_longitude")
    eot = sc.get("equation_of_time_minutes")
    assert eot is not None and eot > 10, f"expected EoT near +16 min on Nov 3, got {eot}"
    assert sc.get("correction_minutes") == pytest.approx(eot, abs=0.2), (
        "correction_minutes should equal the EoT term alone when the longitude term is zero"
    )
    assert sc.get("solar_time") != "10:00", "a ~16-minute EoT shift must move the reported solar time"


@pytest.mark.parametrize(
    "label,convention,year,month,day,hour,minute,longitude,expected",
    [
        # Clock 22:30 at 92°E → solar 23:08. Korean keeps current day's pillar
        # (야자시); hour-stem uses the NEXT day's day-stem 己 → 甲子.
        ("Korean into Zi", "korean", 2000, 1, 1, 22, 30, 92.0,
         ("己卯", "丙子", "戊午", "甲子")),
        # Clock 22:30 at 92°E → solar 23:08. Chinese advances day to 己未;
        # hour-stem uses next day's stem 己 → 甲子.
        ("Chinese into Zi", "chinese", 2000, 1, 1, 22, 30, 92.0,
         ("己卯", "丙子", "己未", "甲子")),
        # Clock 23:05 at 70°E → solar 22:15. Effective hour is 亥, not 子.
        ("Korean out of Zi", "korean", 2000, 1, 1, 23, 5, 70.0,
         ("己卯", "丙子", "戊午", "癸亥")),
        # Clock 02:55 at 92°E → solar 03:33. Hour branch becomes 寅.
        ("Chou to Yin", "korean", 2000, 1, 1, 2, 55, 92.0,
         ("己卯", "丙子", "戊午", "甲寅")),
    ],
)
def test_solar_zi_boundary(label, convention, year, month, day, hour, minute, longitude, expected):
    c = compute_chart(
        name=label, gender="M",
        year=year, month=month, day=day, hour=hour, minute=minute,
        longitude=longitude, utc_offset=5.5, use_solar_time=True,
        convention=convention,
    )
    got = (c.year.combined, c.month.combined, c.day.combined, c.hour.combined)
    assert got == expected, f"{label}: expected {expected}, got {got}"


def test_korean_yazi_hour_stem_asymmetry():
    # 야자시 asymmetry regression (engine bug #1, fixed 2026-09-13).
    # Same date, two 子-hour windows, one day pillar each:
    #   23:40 (야자시): day 辛亥 RETAINED, hour-stem from NEXT day's 일간 壬 → 庚子
    #   00:15 (조자시): day 辛亥, hour-stem from the current day's 일간 辛 → 戊子
    # Ground truth: forceteller + manseryeok.com 야자시 mode (screenshots in
    # tests/validation/evidence/hour-boundary-2340-*.png).
    ya = compute_chart(
        name="Yazi", gender="M",
        year=1990, month=6, day=15, hour=23, minute=40,
        longitude=127.0, utc_offset=9.0, use_solar_time=True,
        convention="korean",
    )
    assert (ya.day.combined, ya.hour.combined) == ("辛亥", "庚子")
    assert ya.zi_time_type == "夜子時 (Korean 야자시)"
    jo = compute_chart(
        name="Jozi", gender="M",
        year=1990, month=6, day=15, hour=0, minute=15,
        longitude=127.0, utc_offset=9.0, use_solar_time=False,
        convention="korean",
    )
    # Solar correction OFF: 00:15 stays on 06-15, day 辛亥, hour-stem from the
    # current day's 일간 辛 → 戊子. (With solar time ON at 127°E the ~-32 min
    # correction legitimately rolls 00:15 back to 23:43 of 06-14 → day 庚戌.)
    assert (jo.day.combined, jo.hour.combined) == ("辛亥", "戊子")


def test_input_validation():
    with pytest.raises(ValueError):
        compute_chart(year=1899, month=1, day=1, hour=12)
    with pytest.raises(ValueError):
        compute_chart(year=2000, month=13, day=1, hour=12)
    with pytest.raises(ValueError):
        compute_chart(year=2000, month=1, day=1, hour=24)
    with pytest.raises(ValueError):
        compute_chart(year=2000, month=1, day=1, hour=12, gender="X")
    with pytest.raises(ValueError):
        compute_chart(year=2000, month=1, day=1, hour=12, convention="unknown")


@pytest.mark.parametrize(
    "hour,minute,expected_month",
    [
        # 1993-12-07: 大雪 (Daeseol) boundary is between 11:40 and 11:45 IST per sajupy.
        # Before the boundary the month branch is 亥; after it is 子.
        (11, 30, "亥"),
        (11, 50, "子"),
    ],
)
def test_solar_term_month_boundary(hour, minute, expected_month):
    c = compute_chart(
        name="SolarTermProbe", gender="M",
        year=1993, month=12, day=7, hour=hour, minute=minute,
        longitude=82.5, utc_offset=5.5, use_solar_time=True,
    )
    assert c.month.branch == expected_month


def test_high_longitude_honolulu_rolls_day():
    # Honolulu: 157.86°W, UTC-10. Solar correction pushes 2000-01-01 00:00 back
    # to 23:28 of the previous day, so the day pillar belongs to 1999-12-31.
    c = compute_chart(
        name="Honolulu", gender="M",
        year=2000, month=1, day=1, hour=0, minute=0,
        longitude=-157.86, utc_offset=-10, use_solar_time=True,
    )
    assert c.day.combined == "丁巳"
    # Effective hour is 23 (야자시): day pillar 丁巳 retained, hour-stem from
    # the next day's day-stem 戊 → 壬子.
    assert c.hour.combined == "壬子"


def test_chinese_zi_solar_rollback_hour_stem():
    # C1 regression: Chinese convention birth where solar correction rolls the
    # calendar day backward. The hour-stem must be derived from the effective
    # (solar-adjusted) day, not the original input date.
    # 2000-01-01 00:30, UTC 0, 15°W → solar 1999-12-31 23:30.
    # Effective day is 1999-12-31 (丁巳). At effective hour 23 (Chinese 조자시),
    # the 子 hour belongs to the next day, 2000-01-01 (戊午). Stem at 子 on a
    # 戊 day is 壬, so the hour pillar should be 壬子.
    c = compute_chart(
        name="ChineseRollback", gender="M",
        year=2000, month=1, day=1, hour=0, minute=30,
        longitude=-15, utc_offset=0, use_solar_time=True,
        convention="chinese",
    )
    assert c.day.combined == "戊午"
    assert c.hour.combined == "壬子"
    assert c.effective_date == "1999-12-31"


def test_honolulu_solar_correction_minutes():
    c = compute_chart(
        name="Honolulu", gender="M",
        year=1990, month=6, day=15, hour=12, minute=0,
        longitude=-157.86, utc_offset=-10, use_solar_time=True,
    )
    assert c.solar_correction is not None
    assert c.solar_correction["correction_minutes"] < -25
    assert c.solar_correction["correction_minutes"] > -35


def test_leap_month_date_accepted():
    # 1995 had a leap 8th lunar month. Saju month branches follow solar terms,
    # so the month pillar is still 乙酉. This test only verifies the engine does
    # not crash and the day pillar advances normally around the leap date.
    c_before = compute_chart(
        name="LeapBefore", gender="M",
        year=1995, month=9, day=14, hour=12, minute=0,
        longitude=82.5, utc_offset=5.5, use_solar_time=True,
    )
    c_during = compute_chart(
        name="LeapDuring", gender="M",
        year=1995, month=9, day=15, hour=12, minute=0,
        longitude=82.5, utc_offset=5.5, use_solar_time=True,
    )
    c_after = compute_chart(
        name="LeapAfter", gender="M",
        year=1995, month=9, day=16, hour=12, minute=0,
        longitude=82.5, utc_offset=5.5, use_solar_time=True,
    )
    assert c_before.month == c_during.month == c_after.month
    assert c_before.day.combined == "戊申"
    assert c_during.day.combined == "己酉"
    assert c_after.day.combined == "庚戌"
