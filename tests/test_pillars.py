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


def test_equation_of_time_alone_crossing_midnight_recomputes_day_pillar():
    """F-1 (2026-09-26 audit): EoT-only midnight crossing must roll the day pillar.

    Birth at 23:50 on 2000-11-03 at longitude 135°E (== utc_offset*15, so
    sajupy's own longitude-only correction is ~0 and it reports day pillar
    for 11-03, 乙丑). The equation of time on 11-03 is ~+16.3 min — added on
    top by this engine, not by sajupy — which alone pushes the true solar
    time to 00:06 on 2000-11-04. The day pillar must roll forward to that
    date's 丙寅, not remain stuck on 乙丑.
    """
    c = compute_chart(
        name="EoT-midnight", gender="M",
        year=2000, month=11, day=3, hour=23, minute=50,
        longitude=135.0, utc_offset=9.0, use_solar_time=True,
    )
    assert c.day.combined == "丙寅", (
        f"expected day pillar 丙寅 (2000-11-04) after EoT rolls past midnight, got {c.day.combined}"
    )


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
    with pytest.raises(ValueError):
        # F-11 (2026-09-26 audit): star_anchor was validated by the CLI's
        # argparse(choices=...) but not by compute_chart() itself — a direct
        # caller passing e.g. "YEAR" silently fell back to day-anchor.
        compute_chart(year=2000, month=1, day=1, hour=12, star_anchor="YEAR")


@pytest.mark.parametrize(
    "hour,minute,expected_month",
    [
        # 1993-12-07: 大雪 (Daeseol). The calendar CSV's raw term_time is
        # 199312071141 — 11:41 **KST**, not IST (see E-1, 2026-09-25:
        # sajupy stores 절기 moments in Korea Standard Time regardless of the
        # querent's own timezone). Converted to IST (UTC+5:30, a -3.5h shift
        # from KST UTC+9): 11:41 - 3:30 = 08:11 IST — the true boundary,
        # confirmed empirically (08:00 -> 亥, 08:11 -> 子). An earlier version
        # of this test compared the raw 11:41 directly against IST clock time
        # with no conversion, encoding the exact bug this now guards against.
        # Before the boundary the month branch is 亥; at/after it is 子.
        (8, 0, "亥"),
        (8, 11, "子"),
    ],
)
def test_solar_term_month_boundary(hour, minute, expected_month):
    c = compute_chart(
        name="SolarTermProbe", gender="M",
        year=1993, month=12, day=7, hour=hour, minute=minute,
        longitude=82.5, utc_offset=5.5, use_solar_time=True,
    )
    assert c.month.branch == expected_month


def test_solar_term_boundary_far_from_kst_still_correct():
    """Regression for E-1 (2026-09-25): a birth timezone far from KST (New
    York, UTC-5, a 14-hour gap — versus IST's 3.5h) must still land on the
    correct side of a 절기 boundary. Reproduces the audit's exact example:
    2024-02-04 10:00 EST used to produce month pillar 乙丑, which does not
    even fit its own year pillar 甲辰 under 오호둔 (乙 as a 丑-month stem only
    occurs for a 戊/癸-year). The correct pillar is 丙寅."""
    c = compute_chart(
        name="NY-E1-regression2", gender="M",
        year=2024, month=2, day=4, hour=10, minute=0,
        utc_offset=-5, longitude=-74.0, use_solar_time=True, convention="korean",
    )
    assert c.month.combined == "丙寅"
    assert c.year.combined == "甲辰"


@pytest.mark.parametrize(
    "hour,minute,expected_year,expected_month",
    [
        # N-2 (2026-09-26 audit): the CSV's 立春 term_time for 2024 is
        # 17:00 KST. Seoul (longitude 127, utc_offset 9) has a real solar
        # correction (~-32 min, since Korea's civil clock runs on the 135°E
        # meridian, not 127°E) — the bug compared this SOLAR time against the
        # civil-converted term instant, so civil births up to ~17:47 KST were
        # wrongly pushed into the previous year/month (癸卯/乙丑) instead of
        # 甲辰/丙寅. Reproduces the audit's own table exactly.
        (17, 20, "甲辰", "丙寅"),
        (17, 40, "甲辰", "丙寅"),
        (17, 55, "甲辰", "丙寅"),
    ],
)
def test_year_month_override_compares_civil_not_solar_time_seoul(
    hour, minute, expected_year, expected_month
):
    c = compute_chart(
        name="N2-Seoul", gender="M",
        year=2024, month=2, day=4, hour=hour, minute=minute,
        longitude=127.0, utc_offset=9.0, use_solar_time=True,
    )
    assert c.year.combined == expected_year
    assert c.month.combined == expected_month


@pytest.mark.parametrize(
    "hour,minute,expected_year,expected_month",
    [
        # Same 2024 立春 (17:00 KST), converted to IST (utc_offset 5.5):
        # 13:30 IST. Mumbai's real longitude (72.9) sits ~38 min west of the
        # +5.5 standard meridian (82.5), so a civil birth at 13:35-14:10 IST
        # (after the term) has a SOLAR time of 12:42-13:17 (before the term),
        # which the bug used to compare instead of the civil clock.
        (13, 20, "癸卯", "乙丑"),  # before the term either way
        (13, 35, "甲辰", "丙寅"),  # after the term civilly; solar time still isn't
        (14, 10, "甲辰", "丙寅"),
    ],
)
def test_year_month_override_compares_civil_not_solar_time_mumbai(
    hour, minute, expected_year, expected_month
):
    c = compute_chart(
        name="N2-Mumbai", gender="M",
        year=2024, month=2, day=4, hour=hour, minute=minute,
        longitude=72.9, utc_offset=5.5, use_solar_time=True,
    )
    assert c.year.combined == expected_year
    assert c.month.combined == expected_month


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


# ── Boundary-chart policy (codified 2026-09-20, external report review I7) ──
# The engine never silently picks a side on a knife-edge hour: when the
# corrected solar time falls within HOUR_BOUNDARY_MARGIN_MIN of a branch-
# window edge, it must also emit the neighboring alternate pillar in
# `solar_correction["hour_boundary"]`, so JSON/CLI consumers and report
# authors see both readings rather than one silently-chosen hour pillar.

def test_hour_boundary_flag_present_for_knife_edge_chart():
    # 03:10 clock at 79.12°E -> 02:58 solar (2 min before the 寅 boundary at
    # 03:00) — same fixture as test_premium_report.py's partial-punishment
    # chart. Effective hour branch is 丑; the neighboring 寅 pillar is the
    # plausible alternative if the clock time carries a few minutes of error.
    c = compute_chart(
        name="Harish", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.12, utc_offset=5.5, use_solar_time=True,
        convention="korean",
    )
    boundary = (c.solar_correction or {}).get("hour_boundary")
    assert boundary is not None, "a 2-minute-margin birth must be flagged as a knife-edge hour"
    assert boundary["distance_minutes"] == 2
    assert boundary["primary_hour_pillar"] == c.hour.combined
    assert boundary["alternate_hour_pillar"][1] == "寅"


def test_hour_boundary_flag_absent_mid_window():
    # 10:00 clock at 82.5°E is the exact IST meridian (zero longitude term);
    # any residual correction is EoT-only and lands well inside the 巳 window.
    c = compute_chart(
        name="MidWindow", gender="M",
        year=2000, month=6, day=13, hour=10, minute=0,
        longitude=82.5, utc_offset=5.5, use_solar_time=True,
        convention="korean",
    )
    assert (c.solar_correction or {}).get("hour_boundary") is None


def test_hour_boundary_flags_the_zi_hour_edge_without_an_alternate_pillar():
    # 23:30 clock at 127°E/UTC+9 (Seoul-like) -> solar 22:54, 6 minutes
    # before the 子 boundary (23:00) — within the margin. N-15 (2026-09-26
    # audit): this used to return no disclosure at all for the 子 edge (see
    # pillars.py::_hour_boundary_info) because it also flips which calendar
    # day's stem drives the hour stem under 야자시, a compound decision this
    # mechanism does not attempt to re-derive — it now still flags the edge
    # (is_zi_boundary=True) rather than staying silent about it.
    c = compute_chart(
        name="ZiEdge", gender="M",
        year=2000, month=1, day=1, hour=23, minute=30,
        longitude=127.0, utc_offset=9.0, use_solar_time=True,
        convention="korean",
    )
    boundary = (c.solar_correction or {}).get("hour_boundary")
    assert boundary is not None
    assert boundary["is_zi_boundary"] is True
    assert "alternate_hour_pillar" not in boundary


def test_rm_boundary_case_pinned():
    # RM (Kim Nam-joon), 1994-09-12 13:28 KST, Seoul (candidates_horoscope/
    # reports/rm/). Longitude pinned explicitly (126.9783°E, Nominatim's
    # answer for "Seoul" as of 2026-09-20) rather than re-geocoding, because
    # sajupy's city geocoder is a live network call and is not guaranteed
    # stable run-to-run (see docs/audits/2026-09-20-i4-i7-followup.md) — the
    # committed rm-report.md was in fact generated against a different
    # geocoded longitude than this test observes today. This fixture pins
    # the CURRENT engine's reading so a future geocoder/formula change can't
    # silently flip RM's hour pillar without a test failing; it does not
    # assert which of 乙未/甲午 is the "correct" hour for RM — that is an
    # open reader decision (see the audit doc).
    c = compute_chart(
        name="RM", gender="M",
        year=1994, month=9, day=12, hour=13, minute=28,
        longitude=126.9783, utc_offset=9.0, use_solar_time=True,
        convention="korean",
    )
    boundary = (c.solar_correction or {}).get("hour_boundary")
    assert boundary == {
        "distance_minutes": 0,
        "primary_hour_pillar": "乙未",
        "alternate_hour_pillar": "甲午",
        "note": (
            "Corrected solar time is within the boundary margin of a 2-hour "
            "branch window; the alternate hour pillar is a plausible reading "
            "if the recorded clock time carries a few minutes of error."
        ),
        # True solar time 13:00:17 — 17 s past the 午/未 edge (sub-minute
        # margin added 2026-09-26 per the 2026-09-25 audit).
        "distance_seconds": 17,
    }


def test_hour_boundary_reports_sub_minute_margin_for_harish():
    """2026-09-25 audit (calculation-layer table): Harish's corrected solar
    time is ~02:59:31, i.e. under 30 seconds from the 丑/寅 boundary — the
    whole-minute distance hid that. distance_seconds carries it."""
    from saju_engine.engine import compute_chart
    chart = compute_chart(
        name="harish-boundary", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    hb = chart.solar_correction["hour_boundary"]
    assert 20 <= hb["distance_seconds"] <= 35
    assert hb["alternate_hour_pillar"] == "庚寅"


def test_hour_boundary_distance_seconds_math():
    from saju_engine.pillars import _hour_boundary_info
    # 02:59:30 → 30 s before the 03:00 丑/寅 edge.
    info = _hour_boundary_info(2, 59, "丑", "己", "辛", precise_minutes=2 * 60 + 59.5)
    assert info["distance_seconds"] == 30
    # Without precise_minutes the key is absent (backward compatible).
    assert "distance_seconds" not in _hour_boundary_info(2, 59, "丑", "己", "辛")
