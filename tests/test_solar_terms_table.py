"""N-3 (2026-09-26 deep audit): the accurate solar-term table shipped as package data.

The engine's month pillar depends on the exact instant of the 12 month-opener
節氣. sajupy's bundled table was wrong by a median ~22 min (up to ~114 min),
which flips the month pillar for births near a boundary. `data/solar_terms.csv`
is generated from an ephemeris (`tools/generate_solar_terms.py`) and pinned here.
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from saju_engine.daeun import (
    KST_OFFSET_HOURS,
    _MONTH_OPENER_TERMS,
    _parse_calendar,
    _parse_term_time,
)

_CSV = Path(__file__).resolve().parents[1] / "src" / "saju_engine" / "data" / "solar_terms.csv"


def test_table_covers_engine_range_with_margin():
    """The table spans 1899–2101 (the engine's 1900–2100 range ± 1 year for the
    'previous term' lookup)."""
    years = sorted(int(r["year"]) for r in csv.DictReader(_CSV.open(encoding="utf-8")))
    assert min(years) == 1899
    assert max(years) == 2101


def test_table_has_all_twelve_terms_every_year():
    rows = list(csv.DictReader(_CSV.open(encoding="utf-8")))
    by_year: dict[int, set] = {}
    for r in rows:
        by_year.setdefault(int(r["year"]), set()).add(r["term"])
    for year, terms in by_year.items():
        assert terms == _MONTH_OPENER_TERMS, f"{year}: {terms ^ _MONTH_OPENER_TERMS}"


def test_published_2024_values_match_within_a_minute():
    """Calibration anchor: the table must reproduce published KASI/HKO 2024 term
    instants to within 1 min (the generator's documented precision)."""
    published_utc = {
        "立春": dt.datetime(2024, 2, 4, 8, 26, 53),
        "芒種": dt.datetime(2024, 6, 5, 4, 9, 56),
        "立冬": dt.datetime(2024, 11, 6, 22, 19, 46),
    }
    rows = {r["term"]: r["kst"] for r in csv.DictReader(_CSV.open(encoding="utf-8"))
            if r["year"] == "2024"}
    for term, expected in published_utc.items():
        got_kst = dt.datetime.strptime(rows[term], "%Y%m%d%H%M")
        got_utc = got_kst - dt.timedelta(hours=KST_OFFSET_HOURS)
        assert abs((got_utc - expected).total_seconds()) <= 60, (term, got_utc, expected)


def test_loaders_read_the_accurate_table():
    """`_parse_calendar` must expose the new table's instants, not sajupy's
    (the old CSV said 2024 立春 was 17:00 KST; the accurate value is 17:27)."""
    terms = _parse_calendar()["2024"]
    lichun = next(tt for _d, h, tt in terms if h == "立春")
    assert _parse_term_time(lichun, dt.date(2024, 2, 4)) == dt.datetime(2024, 2, 4, 17, 27)
