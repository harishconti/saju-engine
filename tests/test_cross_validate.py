"""Pytest regression tests formerly exercised by tools/cross_validate.py.

This file replaces the standalone cross-validation harness with pytest cases so
that the candidate and edge-case matrix runs automatically in CI.
"""
from __future__ import annotations

import pytest

from saju_engine.engine import compute_chart


CANDIDATES = [
    ("Sruthi", 1993, 12, 11, 2, 45, 79.32, 5.5, "F", "Pallipat", ("癸酉", "甲子", "丙寅", "己丑")),
    ("Pawan", 1991, 10, 3, 23, 45, 79.19, 5.5, "M", "Vellore", ("辛未", "丁酉", "丙午", "庚子")),
    # 79.42 (Pallipattu, Tiruvallur) — not 76.33, which is the known-wrong
    # `--city Pallipat` geocoder output (src/saju_engine/pillars.py:218,
    # docs/audits/2026-07-05-engine-audit.md C4). Both land in the 丑 hour, so
    # the expected pillars and the anchor value are unchanged.
    ("Harish", 1992, 6, 4, 3, 10, 79.42, 5.5, "M", "Pallipat", ("壬申", "乙巳", "辛亥", "己丑")),
    ("Gurumoorthy", 1964, 7, 19, 8, 30, 79.422, 5.5, "M", "Tirupati", ("甲辰", "辛未", "己巳", "戊辰")),
    ("Mahesh", 1995, 1, 19, 23, 50, 78.713454, 5.5, "M", "Ambur", ("甲戌", "丁丑", "庚戌", "戊子")),
    ("Vishnu Priya", 2001, 6, 7, 16, 45, 76.65, 5.5, "F", "Mysore", ("辛巳", "甲午", "辛丑", "丙申")),
]


@pytest.mark.parametrize(
    "name,year,month,day,hour,minute,longitude,utc_offset,gender,city,expected", CANDIDATES
)
def test_candidate_cross_validation(name, year, month, day, hour, minute, longitude, utc_offset, gender, city, expected):
    c = compute_chart(
        name=name, gender=gender,
        year=year, month=month, day=day, hour=hour, minute=minute,
        longitude=longitude, utc_offset=utc_offset,
        use_solar_time=True, convention="korean",
    )
    got = (c.year.combined, c.month.combined, c.day.combined, c.hour.combined)
    assert got == expected, f"{name} ({city}): expected {expected}, got {got}"


EDGE_CASES = [
    (
        "Solar moves into Zi (Korean)", 2000, 1, 1, 22, 30,
        92.0, 5.5, "korean", ("己卯", "丙子", "戊午", "甲子"),
    ),
    (
        "Solar moves into Zi (Chinese)", 2000, 1, 1, 22, 30,
        92.0, 5.5, "chinese", ("己卯", "丙子", "己未", "甲子"),
    ),
    (
        "Solar moves out of Zi", 2000, 1, 1, 23, 5,
        70.0, 5.5, "korean", ("己卯", "丙子", "戊午", "癸亥"),
    ),
    (
        "Solar moves Chou to Yin", 2000, 1, 1, 2, 55,
        92.0, 5.5, "korean", ("己卯", "丙子", "戊午", "甲寅"),
    ),
    (
        "Solar-term month boundary (Hai→Zi)", 1993, 12, 7, 11, 50,
        82.5, 5.5, "korean", ("癸酉", "甲子", "壬戌", "丙午"),
    ),
    (
        "Honolulu west longitude rolls day", 2000, 1, 1, 0, 0,
        -157.86, -10.0, "korean", ("己卯", "丙子", "丁巳", "壬子"),
    ),
]


@pytest.mark.parametrize(
    "label,year,month,day,hour,minute,longitude,utc_offset,convention,expected", EDGE_CASES
)
def test_edge_case_cross_validation(label, year, month, day, hour, minute, longitude, utc_offset, convention, expected):
    c = compute_chart(
        name="X", gender="M",
        year=year, month=month, day=day, hour=hour, minute=minute,
        longitude=longitude, utc_offset=utc_offset,
        use_solar_time=True, convention=convention,
    )
    got = (c.year.combined, c.month.combined, c.day.combined, c.hour.combined)
    assert got == expected, f"{label}: expected {expected}, got {got}"
