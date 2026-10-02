"""S1 (2026-10-01 audit): the 세수/age path compared a naive LOCAL birth
datetime against the KST-wall-clock 입춘 instant, while the pillar path
shifts terms by (utc_offset - 9). 2024 立春 = 2024-02-04 17:27 KST = 03:27 EST,
so a New York birth on Feb 4 between 03:27 and 17:26 local got the 2024 (甲辰)
year pillar but was aged as a 2023 (癸卯) birth."""
from datetime import date, datetime

from saju_engine.daeun import saju_age, saju_year
from saju_engine.engine import compute_chart


def test_saju_year_shifts_ipchun_into_local_time():
    # 10:00 EST = 00:00 KST Feb 5 -> after 立春 in absolute time.
    assert saju_year(datetime(2024, 2, 4, 10, 0), utc_offset=-5.0) == 2024
    # 03:00 EST = 17:00 KST -> still before 立春 (17:27 KST).
    assert saju_year(datetime(2024, 2, 4, 3, 0), utc_offset=-5.0) == 2023


def test_saju_year_default_is_kst_unchanged():
    assert saju_year(datetime(2024, 2, 4, 10, 0)) == 2023
    assert saju_year(datetime(2024, 2, 4, 17, 30)) == 2024
    assert saju_year(date(2024, 2, 5)) == 2024


def test_saju_age_threads_offset():
    ref = date(2026, 6, 1)
    assert saju_age("2024-02-04", ref, "10:00", utc_offset=-5.0) == 3
    assert saju_age("2024-02-04", ref, "10:00") == 4  # KST birth: before 立春


def test_chart_age_agrees_with_year_pillar_for_new_york_birth():
    kw = dict(year=2024, month=2, day=4, minute=0, gender="F",
              utc_offset=-5.0, longitude=-74.0,
              reference_year=2026, reference_month=6, reference_day=1)
    after = compute_chart(hour=10, **kw)
    assert after.year.stem + after.year.branch == "甲辰"
    assert after.current_age == 3
    before = compute_chart(hour=3, **kw)
    assert before.year.stem + before.year.branch == "癸卯"
    assert before.current_age == 4
