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


# ── P4 review (2026-10-03): reused reference day vs shorter months ──────────

def test_current_woon_window_day31_across_feb_and_april():
    hits = SW.current_woon_window("甲", ["子", "午", "卯", "酉"], 2026, 1, 31)
    assert [h.year for h in hits] == [202511, 202512, 202601, 202602, 202603]
    hits = SW.current_woon_window("甲", ["子", "午", "卯", "酉"], 2026, 3, 31, window=2)
    assert [h.year for h in hits] == [202601, 202602, 202603, 202604, 202605]


def test_term_pillars_clamp_invalid_day_instead_of_raising():
    assert SW._monthly_pillar_for_date(2026, 2, 31) == SW._monthly_pillar_for_date(2026, 2, 28)
    assert SW._annual_pillar_for_date(2027, 2, 29) == SW._annual_pillar_for_date(2027, 2, 28)


def test_compute_chart_reference_day_31_in_january():
    from saju_engine.engine import compute_chart
    chart = compute_chart(year=1990, month=5, day=15, hour=10, minute=30,
                          reference_year=2026, reference_month=1, reference_day=31)
    assert chart is not None


def test_monthly_fallback_out_of_range_pinned():
    assert SW._monthly_pillar_for_date(2150, 6, 10) == SW._monthly_pillar(2150, 6, 10)


def test_corrected_sajupy_error_dates():
    assert "".join(SW._monthly_pillar_for_date(1903, 7, 15)) == "己未"
    assert "".join(SW._monthly_pillar_for_date(2019, 6, 4)) == "己巳"
