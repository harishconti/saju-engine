"""External textbook / published 만세력 validation cases.

These tests cross-check the engine against Saju charts published by independent
Korean sources (blogs, books, or almanacs), not against the engine's own fixtures
or against `sajupy` directly. Each case cites its source and documents any
convention assumptions (Korean vs. Chinese Zi hour, solar-time correction, etc.).

When a source does not apply solar-time correction, the test uses
`use_solar_time=False` so the engine reproduces the published chart under the
same assumptions. This is not an endorsement of ignoring solar time; it is a
regression check that the engine can match a documented external chart.
"""
from __future__ import annotations

from saju_engine.engine import compute_chart


# ---------------------------------------------------------------------------
# Park Chung-hee (박정희)
# 5th–9th President of South Korea.
#
# Birth data: 1917-11-14 (양력), 사시 (巳時, 9–11 AM), Gimsang-myeon (present-day
# Gimhae) — longitude ≈ 128.74°E. Solar-time correction at that longitude shifts
# the wall-clock time by approximately 24 minutes earlier (true solar noon is
# ~96 minutes early at 128.74°E, divided by 4 gives ~24 min). For a 10:00 birth
# in 巳시 the correction stays inside the same 巳시 range, so the engine
# produces the same hour pillar under both conventions.
#
# Chart: 丁巳 辛亥 庚申 辛巳
#   - "丁巳년 辛亥월 庚申일 辛巳시"
#
# Sources (all assert the same chart under 巳時):
#   - 김재원, "[김재원의 주역이야기]박정희 대통령 사주," 동아일보, 2013-05-03.
#     https://www.donga.com/news/Opinion/article/all/20130503/54869960/1
#   - 사주갤러리, "박정희 대통령 사주풍경," 2026-04.
#     https://www.sajugallery.com/2026/04/park-chung-hee-saju.html
#   - 사주포럼, "박정희 전 대통령" 사례연구.
#     https://www.sajuforum.com/01forum/nm/sarye.php
#
# Note on 寅時 vs 巳時: One blog (woojin2383.tistory.com/13551302) lists
# 寅時 (3–5 AM) → 戊寅 시주. This is the minority view; the three sources
# above (including the named Dongyang-gojeon-hak scholar 김재원) all give
# 巳時 → 辛巳. The test here follows the majority / more authoritative
# reading. The woojin2383 대운 table (庚戌 시작, 역방향) is consistent with
# BOTH 寅時 and 巳時 readings because Park's year/month are identical —
# the 대운 step direction is fixed by the 양년/남명 polarity, not by the
# hour pillar — so the 대운 regression check below passes either way.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Roh Moo-hyun (노무현)
# 10th President of South Korea.
#
# Birth data: 1946년 음력 8월 6일 진시 (辰時, 7–9 AM), Gimhae (Kimhae),
# longitude ≈ 128.74°E. 음 1946-08-06 = 양 1946-09-01.
#
# Chart: 丙戌 丙申 戊寅 丙辰
#   - "丙戌년 丙申월 戊寅일 丙辰시"
#   - 丙(병화) 3개가 천간에 균일하게 분포 — 편인(偏印) 과다 구조.
#   - 寅申沖 + 辰戌沖이 동시에 작동하는 "쌍권총 사주."
#
# Sources (all assert the same chart):
#   - 조용헌, "[조용헌의 江湖동양학] 上·下. 노무현 대통령 사주," 중앙일보.
#     https://www.joongang.co.kr/article/304898 (上)
#     https://www.joongang.co.kr/article/311575 (下)
#   - 김재원 (Dong-A Ilbo column) comparative analysis with 박정희.
#     https://www.donga.com/news/Opinion/article/all/20130503/54869960/1
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Kim Dae-jung (김대중)
# 15th President of South Korea.
#
# Birth data: 1924-01-06 (양력), early-morning birth (exact time not published),
# Ha-ui-do, Sinan-gun, Jeollanam-do, longitude ≈ 126.0°E.
#
# Published non-hour pillars:
#   Year:  癸亥 (계해)
#   Month: 甲子 (갑자) — 子월 (11th lunar month), not 丑월
#   Day:   甲申 (갑신)
#
# Why 子월: 1924-01-06 falls before 小寒 in the solar-term reckoning used by
# the published Korean Myeongri sources, so the 11th lunar month maps to 子.
# The engine reproduces 甲子 on this date for morning hours.
#
# Sources (both agree on the three non-hour pillars):
#   - pisgah.tistory.com/3824 — "김대중 대통령 정인격 갑신일주 편관(사주와운세)"
#   - moneyluckk.com — "이재명과 김대중 사주 운의 충격적 연결고리"
#
# Hour pillar: not independently verified. The most common early-morning
# tradition gives 丙寅 (인시); this test deliberately asserts only the three
# published non-hour pillars.
# ---------------------------------------------------------------------------


# The four-pillars published-chart cases have moved to the cited fixture set:
#   fixtures: tests/validation/fixtures/pillars.json
#   harness:  tests/validation/test_val_pillars.py
# (Campaign spec: docs/superpowers/specs/2026-09-13-engine-validation-campaign-design.md)


# ---------------------------------------------------------------------------
# Kim Dae-jung — three non-hour pillars only (hour is not published)
# ---------------------------------------------------------------------------


def test_textbook_case_kim_dae_jung_three_pillars():
    """Published year/month/day pillars must be reproducible.

    Exact birth time is not publicly documented, so this regression test
    asserts only the three non-hour pillars that two independent sources
    agree on: 癸亥년 甲子월 甲申일.
    """
    c = compute_chart(
        name="Kim Dae-jung (김대중)",
        gender="M",
        year=1924,
        month=1,
        day=6,
        hour=12,  # arbitrary safe hour; assertion intentionally ignores hour
        minute=0,
        longitude=126.0,
        utc_offset=9.0,
        use_solar_time=True,
        convention="korean",
    )
    assert c.year.combined == "癸亥"
    assert c.month.combined == "甲子"
    assert c.day.combined == "甲申"


# ---------------------------------------------------------------------------
# Kim Young-sam (김영삼)
# 14th President of South Korea.
#
# Birth data: 1929-01-14 (양력 1928-12-04 음력), birth location Geoje,
# Gyeongsangnam-do (경상남도 거제), longitude ≈ 128.7°E. Exact birth time is not
# officially published; the widely cited Saju chart assumes 술시 (戌時, 19–21:00),
# giving hour pillar 甲戌.
#
# Published chart: 戊辰 乙丑 己未 甲戌
#   - "무진년 을축월 기미일 갑술시"
#   - 일간 己土, 축월생, 비겁(比劫) 왕성 / 겁재격(劫財格) or 종왕격(從旺格) readings.
#
# Sources:
#   - Presidential Archives: birth 1928.12.4 (음) ≈ 1929-01-14, Geoje.
#     https://www.pa.go.kr/online_contents/president/history14.jsp
#   - 선천진로상담연구소, "제6장 명인들의 사주탐방 _ 1. 한국 역대 대통령".
#     https://career-consulting-center.tistory.com/997
#   - winwinstory, "김영삼 사주풀이(feat. 제 14대 대한민국 대통령)".
#     https://winwinstory.tistory.com/entry/김영삼-사주풀이feat-제-14대-대한민국-대통령
#   - sank1001, "김영삼 대통령의 사주와 비겁(比劫)" (clues confirm the same pillars).
#     https://sank1001.tistory.com/13498365
#
# Published analyses place his presidency (1992 election / 1993 inauguration)
# in the 壬申 and 癸酉 대운 windows. The engine's classical 순행 from birth month
# 乙丑 produces 壬申 at period index 6 and 癸酉 at index 7, matching that timing.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Cross-check: both 寅時 and 巳時 readings must produce internally consistent
# four-pillar charts with matching year/month pillars. The hour pillar is
# the documented point of disagreement between sources.
# ---------------------------------------------------------------------------


def test_textbook_case_park_both_readings():
    """Both the 巳時 (Kim Jae-won, Donga) and 寅時 (woojin2383) readings must
    produce consistent year/month/day pillars, with hour differing only in
    the (寅 vs 巳) branch and (戊 vs 辛) stem.

    巳時 reading: 丁巳 辛亥 庚申 辛巳
    寅時 reading: 丁巳 辛亥 庚申 戊寅

    The structural difference is:
      - branches: 巳時 = {巳, 亥, 申, 巳}, 寅時 = {巳, 亥, 申, 寅}
      - 사맹격 (寅申巳亥) is ONLY formed under the 寅時 reading.
      - The 巳時 reading is the more-cited chart in modern Korean Myeongri
        pedagogy; the 寅時 reading is the older woojin blog variant.
    """
    c_sa = compute_chart(
        name="Park sa-si", gender="M",
        year=1917, month=11, day=14, hour=10, minute=0,
        longitude=128.74, utc_offset=9.0,
        use_solar_time=True, convention="korean",
    )
    c_in = compute_chart(
        name="Park in-si", gender="M",
        year=1917, month=11, day=14, hour=4, minute=0,
        longitude=128.74, utc_offset=9.0,
        use_solar_time=True, convention="korean",
    )

    # Year / month / day must match BOTH readings.
    assert c_sa.year.combined == c_in.year.combined == "丁巳", (
        f"year pillar should be 丁巳 in both readings, got "
        f"sa={c_sa.year.combined}, in={c_in.year.combined}"
    )
    assert c_sa.month.combined == c_in.month.combined == "辛亥", (
        f"month pillar should be 辛亥 in both readings, got "
        f"sa={c_sa.month.combined}, in={c_in.month.combined}"
    )
    assert c_sa.day.combined == c_in.day.combined == "庚申", (
        f"day pillar should be 庚申 in both readings, got "
        f"sa={c_sa.day.combined}, in={c_in.day.combined}"
    )

    # Hour pillars must DIFFER as documented (this is the point of
    # disagreement between sources).
    assert c_sa.hour.combined == "辛巳", (
        f"사시 reading should give 辛巳, got {c_sa.hour.combined}"
    )
    assert c_in.hour.combined == "戊寅", (
        f"인시 reading should give 戊寅, got {c_in.hour.combined}"
    )

    # 사맹격 check is conditional on the 寅時 reading only.
    samyeokguk_branches = {"寅", "申", "巳", "亥"}
    in_branches = {
        c_in.year.branch, c_in.month.branch, c_in.day.branch, c_in.hour.branch
    }
    assert in_branches == samyeokguk_branches, (
        f"寅시 reading should give 사맹격 {samyeokguk_branches}, got {in_branches}"
    )
    sa_branches = {
        c_sa.year.branch, c_sa.month.branch, c_sa.day.branch, c_sa.hour.branch
    }
    assert "寅" not in sa_branches, (
        f"사시 reading should NOT include 寅 branch (사맹격 only under 寅시), "
        f"got {sa_branches}"
    )
