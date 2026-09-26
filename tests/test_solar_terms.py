"""N-3 (2026-09-26 audit): 절기 instants come from the packaged ephemeris
table (src/saju_engine/data/solar_terms.csv), not sajupy's calendar_data.csv,
whose term times were off by a median of ~22 min and up to ~114 min.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

import pytest

from saju_engine import compute_chart
from saju_engine.daeun import _MONTH_OPENER_TERMS, _parse_calendar, _parse_term_time

KST = timedelta(hours=9)


def _term_kst(year: int, hanja: str) -> datetime:
    for d, h, tt in _parse_calendar()[str(year)]:
        if h == hanja:
            return _parse_term_time(tt, d)
    raise KeyError((year, hanja))


def test_table_covers_1899_to_2101_with_twelve_terms_each_year():
    cal = _parse_calendar()
    assert min(map(int, cal)) == 1899 and max(map(int, cal)) == 2101
    for y in range(1899, 2102):
        terms = Counter(h for _, h, _ in cal[str(y)])
        assert set(terms) == set(_MONTH_OPENER_TERMS), y
        assert all(n == 1 for n in terms.values()), y


@pytest.mark.parametrize(
    "year,hanja,published_utc",
    [
        # Published values (HKO / KASI) the audit calibrated against.
        (2024, "立春", datetime(2024, 2, 4, 8, 26, 53)),
        (2024, "芒種", datetime(2024, 6, 5, 4, 9, 56)),
        (2024, "立冬", datetime(2024, 11, 6, 22, 19, 46)),
    ],
)
def test_term_instants_match_published_values_within_a_minute(year, hanja, published_utc):
    got_utc = _term_kst(year, hanja) - KST
    assert abs((got_utc - published_utc).total_seconds()) < 60


def test_terms_are_ordered_and_roughly_a_month_apart():
    instants = sorted(
        _parse_term_time(tt, d) for y in _parse_calendar().values() for d, _, tt in y
    )
    gaps = [(b - a).total_seconds() / 86400 for a, b in zip(instants, instants[1:])]
    assert all(29.0 < g < 32.5 for g in gaps)


def test_2024_ipchun_boundary_uses_true_instant_not_sajupy_1700():
    """sajupy lists 2024 立春 at 17:00 KST; the true instant is 17:27:08.
    A Seoul civil birth at 17:15 is still in 癸卯 year / 乙丑 month."""
    before = compute_chart(name="N3", gender="M", year=2024, month=2, day=4,
                           hour=17, minute=15, longitude=127.0, utc_offset=9.0)
    after = compute_chart(name="N3", gender="M", year=2024, month=2, day=4,
                          hour=17, minute=28, longitude=127.0, utc_offset=9.0)
    assert (before.year.combined, before.month.combined) == ("癸卯", "乙丑")
    assert (after.year.combined, after.month.combined) == ("甲辰", "丙寅")


# ── N-15 (절기 half): knife-edge disclosure near a month-opener term ──────────


def test_term_boundary_flagged_just_before_ipchun_with_both_pillars():
    c = compute_chart(name="N15", gender="M", year=2024, month=2, day=4,
                      hour=17, minute=15, longitude=127.0, utc_offset=9.0)
    tb = c.term_boundary
    assert tb is not None
    assert tb["term"] == "立春"
    assert tb["distance_minutes"] == 12
    assert tb["birth_is_after_term"] is False
    assert (tb["primary_year_pillar"], tb["primary_month_pillar"]) == ("癸卯", "乙丑")
    assert (tb["alternate_year_pillar"], tb["alternate_month_pillar"]) == ("甲辰", "丙寅")
    assert c.to_dict()["term_boundary"] == tb


def test_term_boundary_flagged_after_non_year_term_keeps_year_pillar():
    # 2024 芒種 = 04:09:54 UTC = 13:09:54 KST.
    c = compute_chart(name="N15", gender="F", year=2024, month=6, day=5,
                      hour=13, minute=30, longitude=127.0, utc_offset=9.0)
    tb = c.term_boundary
    assert tb is not None and tb["term"] == "芒種" and tb["birth_is_after_term"] is True
    assert tb["primary_year_pillar"] == tb["alternate_year_pillar"] == "甲辰"
    assert tb["primary_month_pillar"] == c.month.combined == "庚午"
    assert tb["alternate_month_pillar"] == "己巳"


def test_no_term_boundary_far_from_any_term():
    c = compute_chart(name="N15", gender="M", year=2024, month=2, day=20,
                      hour=12, minute=0, longitude=127.0, utc_offset=9.0)
    assert c.term_boundary is None


def test_term_boundary_note_rendered_in_premium_report():
    from saju_engine.premium_report import generate_premium_report

    c = compute_chart(name="N15", gender="M", year=2024, month=2, day=4,
                      hour=17, minute=15, longitude=127.0, utc_offset=9.0)
    md = generate_premium_report(c, tier="essential")
    assert "Solar-term boundary note" in md
    assert "year pillar **甲辰** and month pillar **丙寅**" in md
