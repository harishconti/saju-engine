#!/usr/bin/env python3
"""Regenerate the accurate solar-term (節氣) table shipped as package data.

The engine's month/year pillars depend on the exact instant of the 12
month-opener 節氣 (立春, 驚蟄, … 小寒). sajupy's bundled ``calendar_data.csv``
stores those instants with errors up to ~114 min (deep-audit N-3), which flips
the month pillar for births near a term boundary. This script recomputes them
from an ephemeris and writes ``src/saju_engine/data/solar_terms.csv``.

Method: apparent geocentric solar longitude from PyEphem (libastro VSOP87),
corrected for nutation (four largest terms) and aberration (-20.496"), matching
``docs/audits/scripts/check_solar_terms.py``. Calibrated to published 2024 KASI/
HKO values within ~3 s (立春 08:26:53 UTC, 芒種 04:09:56, 立冬 22:19:46).

Usage::

    pip install --user --break-system-packages ephem
    python3 tools/generate_solar_terms.py

The output column is KST wall-clock (UTC+9), matching the convention the engine
already assumes for term times — see ``daeun.KST_OFFSET_HOURS``. The table
covers 1899–2101 (a one-year margin either side of the engine's 1900–2100
supported range; the extra year supplies the "previous term" for early-January
1900 births).
"""
from __future__ import annotations

import csv
import datetime as dt
import math
import sys
from pathlib import Path

try:
    import ephem
except ImportError:  # pragma: no cover - documented setup step
    sys.exit("PyEphem not installed. Run: pip install --user --break-system-packages ephem")

# Month-opener 節氣 → target apparent solar longitude (degrees).
_TERMS = [
    (285, "小寒"), (315, "立春"), (345, "驚蟄"), (15, "淸明"),
    (45, "立夏"), (75, "芒種"), (105, "小暑"), (135, "立秋"),
    (165, "白露"), (195, "寒露"), (225, "立冬"), (255, "大雪"),
]
# Approximate (month, day) each term falls on, to bracket the search.
_APPROX_MD = {
    285: (1, 5), 315: (2, 4), 345: (3, 5), 15: (4, 5),
    45: (5, 5), 75: (6, 5), 105: (7, 7), 135: (8, 7),
    165: (9, 7), 195: (10, 8), 225: (11, 7), 255: (12, 7),
}
_UTC_OFFSET_HOURS = 9  # KST — the stored-term-time convention (daeun.KST_OFFSET_HOURS)


def _nutation_deg(d: ephem.Date) -> float:
    t = (float(d) + 2415020.0 - 2451545.0) / 36525
    om = math.radians(125.04452 - 1934.136261 * t)
    ls = math.radians(280.4665 + 36000.7698 * t)
    lm = math.radians(218.3165 + 481267.8813 * t)
    return (-17.20 * math.sin(om) - 1.32 * math.sin(2 * ls)
            - 0.23 * math.sin(2 * lm) + 0.21 * math.sin(2 * om)) / 3600


def _apparent_solar_longitude(d: ephem.Date) -> float:
    sun = ephem.Sun()
    sun.compute(d, epoch=d)
    return math.degrees(ephem.Ecliptic(sun, epoch=d).lon) + _nutation_deg(d) - 20.496 / 3600


def _find_term_utc(target_deg: float, lo: dt.datetime, hi: dt.datetime) -> dt.datetime:
    """Return the UTC instant apparent solar longitude crosses ``target_deg`` in [lo, hi]."""
    d = ephem.Date(lo)
    end = ephem.Date(hi)
    prev_lon = _apparent_solar_longitude(d)
    prev_d = d
    while d < end:
        d = ephem.Date(d + 0.25)  # 6-hour coarse steps
        cur_lon = _apparent_solar_longitude(d)
        a = (prev_lon - target_deg + 180) % 360 - 180
        b = (cur_lon - target_deg + 180) % 360 - 180
        if a <= 0 <= b or b <= 0 <= a:
            x = ephem.Date((float(prev_d) + float(d)) / 2)
            for _ in range(80):
                diff = (_apparent_solar_longitude(x) - target_deg + 180) % 360 - 180
                if abs(diff) < 1e-9:
                    break
                x = ephem.Date(x - diff / 0.9856)
            return x.datetime()
        prev_lon, prev_d = cur_lon, d
    raise RuntimeError(f"no crossing for {target_deg} in {lo}..{hi}")


def main() -> None:
    out_path = Path(__file__).resolve().parents[1] / "src" / "saju_engine" / "data" / "solar_terms.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for year in range(1899, 2102):
        for target, name in _TERMS:
            m, d = _APPROX_MD[target]
            lo = dt.datetime(year, m, d) - dt.timedelta(days=6)
            hi = dt.datetime(year, m, d) + dt.timedelta(days=6)
            utc = _find_term_utc(target, lo, hi)
            # Round to the nearest minute — the engine's boundary logic is
            # minute-resolution, and the ephemeris precision here is ~3 s.
            kst = utc + dt.timedelta(hours=_UTC_OFFSET_HOURS, seconds=30)
            rows.append([year, name, kst.strftime("%Y%m%d%H%M")])
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["year", "term", "kst"])
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {out_path}")

    # Sanity check against the published 2024 KASI/HKO values (UTC).
    published = {("2024", "立春"): "2024-02-04 08:26:53", ("2024", "芒種"): "2024-06-05 04:09:56",
                 ("2024", "立冬"): "2024-11-06 22:19:46"}
    for (y, name), expected in published.items():
        got = next(r[2] for r in rows if str(r[0]) == y and r[1] == name)
        got_utc = dt.datetime.strptime(got, "%Y%m%d%H%M") - dt.timedelta(hours=_UTC_OFFSET_HOURS)
        delta = abs((got_utc - dt.datetime.strptime(expected, "%Y-%m-%d %H:%M:%S")).total_seconds())
        print(f"  {y} {name}: {got_utc} UTC (published {expected} UTC, Δ{delta:.0f}s)")


if __name__ == "__main__":
    main()
