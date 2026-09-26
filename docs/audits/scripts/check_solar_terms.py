#!/usr/bin/env python3
"""Cross-check sajupy's calendar_data.csv 절기 (month-opener term) times
against an independent ephemeris.

Used by docs/audits/2026-09-26-deep-engine-audit.md (finding N-3).

    pip install ephem
    python3 docs/audits/scripts/check_solar_terms.py

Reference: PyEphem's geometric solar longitude, corrected to apparent longitude
(aberration −20.496", nutation in longitude with the four largest terms).
Calibrated against published 2024 values (HKO/KASI): 立春 08:26:53 UTC,
芒種 04:09:56 UTC, 立冬 22:19:46 UTC (Nov 6). This script reproduces all three
to within about 5 seconds.
"""
from __future__ import annotations

import collections
import datetime as dt
import math
import statistics
import sys
from pathlib import Path

import ephem

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from saju_engine.daeun import _parse_calendar, _parse_term_time  # noqa: E402

TERM_LONGITUDE = {
    "立春": 315, "驚蟄": 345, "淸明": 15, "立夏": 45, "芒種": 75, "小暑": 105,
    "立秋": 135, "白露": 165, "寒露": 195, "立冬": 225, "大雪": 255, "小寒": 285,
}


def _nutation_deg(d: ephem.Date) -> float:
    t = (float(d) + 2415020.0 - 2451545.0) / 36525
    om = math.radians(125.04452 - 1934.136261 * t)
    ls = math.radians(280.4665 + 36000.7698 * t)
    lm = math.radians(218.3165 + 481267.8813 * t)
    return (-17.20 * math.sin(om) - 1.32 * math.sin(2 * ls)
            - 0.23 * math.sin(2 * lm) + 0.21 * math.sin(2 * om)) / 3600


def apparent_solar_longitude(d: ephem.Date) -> float:
    sun = ephem.Sun()
    sun.compute(d, epoch=d)
    lon = math.degrees(ephem.Ecliptic(sun, epoch=d).lon)
    return lon + _nutation_deg(d) - 20.496 / 3600


def term_moment_utc(approx_utc: dt.datetime, target_deg: float) -> dt.datetime:
    d = ephem.Date(approx_utc)
    for _ in range(60):
        diff = (apparent_solar_longitude(d) - target_deg + 180) % 360 - 180
        if abs(diff) < 1e-8:
            break
        d = ephem.Date(d - diff / 0.9856)
    return d.datetime()


def main() -> None:
    for iso, name in (("2024-02-04 08:00", "立春"), ("2024-06-05 04:00", "芒種"),
                      ("2024-11-06 22:00", "立冬")):
        print(f"calibration {name}: {term_moment_utc(dt.datetime.fromisoformat(iso), TERM_LONGITUDE[name])} UTC")

    rows = []
    for year, terms in sorted(_parse_calendar().items()):
        for date_, name, term_time in terms:
            csv_kst = _parse_term_time(term_time, date_)
            csv_utc = csv_kst - dt.timedelta(hours=9)
            true_utc = term_moment_utc(csv_utc, TERM_LONGITUDE[name])
            rows.append((int(year), name, (csv_utc - true_utc).total_seconds() / 60))

    by_era = collections.defaultdict(list)
    for year, _, err in rows:
        by_era[year // 20 * 20].append(err)
    print("\nCSV minus true, minutes (positive = CSV late)")
    for era in sorted(by_era):
        v = by_era[era]
        print(f"{era}s  median {statistics.median(v):+6.1f}  min {min(v):+6.1f}  "
              f"max {max(v):+6.1f}  |err|>15min {sum(abs(x) > 15 for x in v)}/{len(v)}")
    a = [abs(e) for _, _, e in rows]
    print(f"\noverall: median |err| {statistics.median(a):.1f} min, max {max(a):.1f} min, "
          f">15 min {sum(x > 15 for x in a)}/{len(a)}, >30 min {sum(x > 30 for x in a)}")


if __name__ == "__main__":
    main()
