"""End-to-end engine tests for known candidates."""
from __future__ import annotations

import pytest

from saju_engine.engine import compute_chart


@pytest.mark.parametrize(
    "name,year,month,day,hour,minute,longitude,utc_offset,gender,expected",
    [
        ("Sruthi", 1993, 12, 11, 2, 45, 79.32, 5.5, "F", ("癸酉", "甲子", "丙寅", "己丑")),
        ("Pawan", 1991, 10, 3, 23, 45, 79.19, 5.5, "M", ("辛未", "丁酉", "丙午", "庚子")),
        # 79.42 (Pallipattu, Tiruvallur), not 76.33: 76.33 is the known-wrong
        # `--city Pallipat` geocoder output (src/saju_engine/pillars.py:218,
        # audit C4). Both land in the 丑 hour, so the expected pillars are equal.
        ("Harish", 1992, 6, 4, 3, 10, 79.42, 5.5, "M", ("壬申", "乙巳", "辛亥", "己丑")),
        ("Gurumoorthy", 1964, 7, 19, 8, 30, 79.422, 5.5, "M", ("甲辰", "辛未", "己巳", "戊辰")),
        ("Mahesh", 1995, 1, 19, 23, 50, 78.713454, 5.5, "M", ("甲戌", "丁丑", "庚戌", "戊子")),
    ],
)
def test_known_candidates(name, year, month, day, hour, minute, longitude, utc_offset, gender, expected):
    c = compute_chart(
        name=name, gender=gender,
        year=year, month=month, day=day, hour=hour, minute=minute,
        longitude=longitude, utc_offset=utc_offset, use_solar_time=True,
        convention="korean",
    )
    got = (c.year.combined, c.month.combined, c.day.combined, c.hour.combined)
    assert got == expected, f"{name}: expected {expected}, got {got}"


def test_anchor_1900():
    c = compute_chart(
        name="Anchor", gender="M",
        year=1900, month=1, day=1, hour=12, minute=0,
        longitude=127.0, utc_offset=9, use_solar_time=True,
    )
    assert c.day.combined == "甲戌"


def test_chinese_convention_advances_day():
    # Pawan's 23:45 under Chinese convention rolls to next day's day pillar.
    c = compute_chart(
        name="Pawan", gender="M",
        year=1991, month=10, day=3, hour=23, minute=45,
        longitude=79.19, utc_offset=5.5, use_solar_time=True,
        convention="chinese",
    )
    assert (c.year.combined, c.month.combined, c.day.combined, c.hour.combined) == \
           ("辛未", "丁酉", "丁未", "庚子")


# ── Reference-date threading (P4 audit) ─────────────────────────────────────


def test_reference_date_overrides_current_overlays():
    """A past/future reference date must pin sewoon, woon, ilwoon, current_age, and current_daeun."""
    c = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
        reference_year=2030, reference_month=6, reference_day=15,
    )
    assert c.reference_date == "2030-06-15"
    assert c.current_age is not None
    # All overlays should be centered on the reference date.
    assert c.sewoon[2].year == 2030  # window: 2028, 2029, 2030, 2031, 2032
    assert c.woon[2].year == 203006  # YYYYMM synthetic
    assert c.ilwoon[2].year == 20300615  # YYYYMMDD synthetic
    assert c.current_daeun is not None
    assert c.current_daeun.start_age <= c.current_age <= c.current_daeun.end_age


def test_reference_date_defaults_to_today():
    """When no reference date is supplied, overlays default to today."""
    from datetime import date
    c = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
    )
    today = date.today()
    assert c.reference_date == f"{today.year:04d}-{today.month:02d}-{today.day:02d}"
    assert c.sewoon[2].year == today.year


def test_reference_date_changes_current_daeun():
    """Different reference years can land in different major-luck periods."""
    c_now = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
        reference_year=2026, reference_month=1, reference_day=1,
    )
    c_then = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
        reference_year=2005, reference_month=1, reference_day=1,
    )
    assert c_now.current_daeun is not None
    assert c_then.current_daeun is not None
    assert c_now.current_daeun.combined != c_then.current_daeun.combined
