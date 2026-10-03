"""S8a (2026-10-01 audit): transit (세운/월운) pillars came from sajupy's
calendar_data.csv while natal/대운 used the engine's own ephemeris
(data/solar_terms.csv) — two clocks in one product. Transit lookups now use
the engine table, evaluated at 12:00 KST for a calendar date."""
from datetime import date, timedelta

from saju_engine import sewoon as SW
from saju_engine.pillars import _independent_year_month_pillar


def test_transit_pillars_match_engine_term_table_at_noon_kst():
    d = date(1990, 1, 1)
    while d < date(2031, 1, 1):
        ref = _independent_year_month_pillar(d.year, d.month, d.day, 12, 0, 9.0)
        assert "".join(SW._annual_pillar_for_date(d.year, d.month, d.day)) == ref["year_stem"] + ref["year_branch"]
        assert "".join(SW._monthly_pillar_for_date(d.year, d.month, d.day)) == ref["month_stem"] + ref["month_branch"]
        d += timedelta(days=1)


def test_sajupy_calendar_no_longer_loaded():
    assert not hasattr(SW, "_load_sajupy_calendar")


def test_out_of_range_fallback_still_works():
    assert SW._annual_pillar_for_date(2150, 1, 10) == SW._annual_pillar(2149)
