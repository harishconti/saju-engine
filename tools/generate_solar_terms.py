#!/usr/bin/env python3
"""Generate the engine's 절기 (month-opener solar term) table from an ephemeris.

N-3 (2026-09-26 deep engine audit): sajupy's bundled ``calendar_data.csv``
lists 절기 instants with a median error of ~22 min and a maximum of ~114 min
against an ephemeris (see ``docs/audits/scripts/check_solar_terms.py``). A
birth inside that error window gets the wrong month pillar — and with it the
wrong 격국, strength, 용신 and the whole 대운 sequence. This script computes
the 12 month-opener terms directly from JPL DE440s via Skyfield
(the instant the Sun's apparent geocentric ecliptic longitude, of date,
crosses a multiple of 15°) and writes them, to the second, as package data.

The output is checked into the repo; neither Skyfield nor the ephemeris is a
runtime dependency. Regenerate only if the covered range must grow:

    pip install skyfield
    python3 tools/generate_solar_terms.py            # downloads de440s.bsp (~32 MB) on first run
    python3 tools/generate_solar_terms.py --bsp /path/to/de440s.bsp

Output: ``src/saju_engine/data/solar_terms.csv`` with columns
``year,term,utc`` where ``year`` is the KST calendar year of the instant (the
same year keying sajupy's CSV used), ``term`` the Hanja name, and ``utc`` an
ISO-8601 UTC timestamp rounded to the second.
"""
from __future__ import annotations

import argparse
import csv
from datetime import timedelta
from pathlib import Path

# Term index i  <->  apparent solar longitude 15*i degrees.
MONTH_OPENER_BY_INDEX = {
    21: "立春",  # 315°
    23: "驚蟄",  # 345°
    1: "淸明",   # 15°
    3: "立夏",   # 45°
    5: "芒種",   # 75°
    7: "小暑",   # 105°
    9: "立秋",   # 135°
    11: "白露",  # 165°
    13: "寒露",  # 195°
    15: "立冬",  # 225°
    17: "大雪",  # 255°
    19: "小寒",  # 285°
}

FIRST_YEAR = 1899
LAST_YEAR = 2101
OUT = Path(__file__).resolve().parents[1] / "src" / "saju_engine" / "data" / "solar_terms.csv"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--bsp", default="de440s.bsp", help="JPL ephemeris file (default: de440s.bsp, downloaded if absent)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    from skyfield import almanac
    from skyfield.api import load
    from skyfield.framelib import ecliptic_frame

    ts = load.timescale()
    eph = load(args.bsp)
    # Pad by a month either side so the KST-year grouping at the edges is complete.
    t0 = ts.utc(FIRST_YEAR - 1, 12, 1)
    t1 = ts.utc(LAST_YEAR + 1, 2, 1)
    earth, sun = eph["earth"], eph["sun"]

    def term_index(t):
        _, lon, _ = earth.at(t).observe(sun).apparent().frame_latlon(ecliptic_frame)
        return (lon.degrees // 15).astype(int) % 24

    term_index.step_days = 7  # terms are ~15 days apart
    times, indices = almanac.find_discrete(t0, t1, term_index)

    rows = []
    for t, i in zip(times, indices):
        name = MONTH_OPENER_BY_INDEX.get(int(i))
        if name is None:
            continue
        utc = t.utc_datetime()
        utc = (utc + timedelta(microseconds=500_000)).replace(microsecond=0)
        kst_year = (utc + timedelta(hours=9)).year
        if FIRST_YEAR <= kst_year <= LAST_YEAR:
            rows.append((kst_year, name, utc.strftime("%Y-%m-%dT%H:%M:%SZ")))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write("# 12 month-opener 節氣 instants, JPL DE440s via Skyfield "
                "(tools/generate_solar_terms.py). year = KST calendar year.\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["year", "term", "utc"])
        w.writerows(rows)
    print(f"wrote {len(rows)} terms ({FIRST_YEAR}-{LAST_YEAR}) to {out}")


if __name__ == "__main__":
    main()
