#!/usr/bin/env python3
"""Build the searchable place index the birthplace picker loads on demand.

Why
---
The picker shipped with a hand-written table of **156** cities, **12** of them in India. That is not a
short list, it is a wall: `/sample` refuses to submit unless the typed place resolves
(`"Pick your birthplace from the suggestions"`), and the profiles form requires the same. Every
birthplace this repository's own client reports use — Pallipattu, Vellore, Ambur, Tirupati, Kolar,
Mysore — was absent from it.

The table is served as a static asset and fetched in the browser **only when someone types in the
place field**, so nothing here is a request-time geocode: coordinates still resolve once, from data we
ship, and the engine still receives explicit values (engine change E2). What changes is how much of the
world we ship.

Source: GeoNames (CC-BY 4.0 — attribution required, see the site footer). `cities5000` is the smallest
file that contains the towns this product actually needs (Pallipattu is in it; it is not in
`cities15000`).

    python3 tools/build-cities.py               # download if needed, write the index
    python3 tools/build-cities.py --check       # verify coverage of places this repo uses
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT = REPO_ROOT / "apps" / "web" / "public" / "city-index.json"
CACHE = REPO_ROOT / "tmp" / "geonames"

SOURCE_URL = "https://download.geonames.org/export/dump/cities5000.zip"
SOURCE_NAME = "cities5000.txt"

# Columns in the GeoNames dump: 0 id, 1 name, 2 asciiname, 3 alternatenames, 4 lat, 5 lon,
# 6 feature class, 7 feature code, 8 country code, 9 cc2, 10 admin1, 11 admin2, 12 admin3,
# 13 admin4, 14 population, 15 elevation, 16 dem, 17 timezone, 18 modification date.
COL_ASCII, COL_LAT, COL_LON, COL_CC, COL_TZ = 2, 4, 5, 8, 17

# Places this repository must be able to express, because its own reports were built from them.
# A dataset swap that broke one of these would still be a regression, so `--check` fails on any miss.
REQUIRED = [
    ("Pallipattu", "IN"),
    ("Tiruvallur", "IN"),
    ("Vellore", "IN"),
    ("Ambur", "IN"),
    ("Tirupati", "IN"),
    ("Kolar", "IN"),
    ("Mysuru", "IN"),      # GeoNames' modern name; the curated overlay keeps "Mysore" working
    ("Seoul", "KR"),
    ("Busan", "KR"),
    ("New Delhi", "IN"),
    ("Mumbai", "IN"),
    ("Bengaluru", "IN"),
]

# Alternate names are what make an exonym work ("Cologne" for Köln, "Bangalore" for Bengaluru). They
# cost more than everything else in the file combined, because the dump carries each name in dozens of
# scripts. Measured: keeping four per city took the asset to 5.44 MB (1.68 MB gzipped) — minutes on the
# mobile connections this feature exists to serve. So they are dropped here and the handful that matter
# are kept as a curated alias map in `apps/web/src/lib/cities.ts`, where they can be read, reviewed and
# added to. Coordinates are rounded to 3 decimals (~110 m), which is far finer than solar-time
# correction needs.
COORD_DECIMALS = 3

# Names people type that are *not* the name we ship, as (alias, shipped name, country).
#
# Verified against the built index at build time, and **the build fails on a dead entry**. That check
# is not ceremony: the first hand-written version of this list had **15 dead targets out of 45**,
# because GeoNames' ascii name is the *English* exonym for most cities ("Munich", "Vienna", "Prague",
# "The Hague") but a transliteration for others ("Zuerich"), and guessing which is which is exactly how
# you ship an alias that never matches anything. A person born in a renamed city does not necessarily
# know it was renamed, and "that is not a real place" is both wrong and insulting.
ALIASES = [
    # India — renames, and the colonial spellings people still write.
    ("mysore", "Mysuru", "IN"),
    ("bangalore", "Bengaluru", "IN"),
    ("bombay", "Mumbai", "IN"),
    ("calcutta", "Kolkata", "IN"),
    ("madras", "Chennai", "IN"),
    ("cochin", "Kochi", "IN"),
    ("trivandrum", "Thiruvananthapuram", "IN"),
    ("pondicherry", "Puducherry", "IN"),
    ("baroda", "Vadodara", "IN"),
    ("poona", "Pune", "IN"),
    ("simla", "Shimla", "IN"),
    ("banaras", "Varanasi", "IN"),
    ("benares", "Varanasi", "IN"),
    ("tuticorin", "Thoothukudi", "IN"),
    ("mangalore", "Mangaluru", "IN"),
    ("gulbarga", "Kalaburagi", "IN"),
    ("hubli", "Hubballi", "IN"),
    ("belgaum", "Belagavi", "IN"),
    ("allahabad", "Prayagraj", "IN"),
    # Local spellings, for cities the index carries under another name.
    ("munchen", "Munich", "DE"),
    ("koln", "Koeln", "DE"),
    ("wien", "Vienna", "AT"),
    ("praha", "Prague", "CZ"),
    ("milano", "Milan", "IT"),
    ("napoli", "Naples", "IT"),
    ("torino", "Turin", "IT"),
    ("roma", "Rome", "IT"),
    ("lisboa", "Lisbon", "PT"),
    ("seville", "Sevilla", "ES"),
    ("kobenhavn", "Copenhagen", "DK"),
    ("goteborg", "Gothenburg", "SE"),
    ("den haag", "The Hague", "NL"),
    ("brussel", "Brussels", "BE"),
    ("antwerpen", "Antwerp", "BE"),
    ("geneve", "Geneva", "CH"),
    ("zurich", "Zuerich", "CH"),
    ("peking", "Beijing", "CN"),
    ("rangoon", "Yangon", "MM"),
    ("saigon", "Ho Chi Minh City", "VN"),
    ("dacca", "Dhaka", "BD"),
]


def _ascii(value: str) -> str:
    """Strip to printable ASCII, so the index stays a single-byte-per-char JSON string."""
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(c for c in decomposed if c.isascii() and c.isprintable()).strip()



def fetch(source: Path | None) -> Path:
    if source is not None:
        return source
    CACHE.mkdir(parents=True, exist_ok=True)
    txt = CACHE / SOURCE_NAME
    if txt.exists():
        return txt
    archive = CACHE / SOURCE_NAME.replace(".txt", ".zip")
    print(f"downloading {SOURCE_URL} …", file=sys.stderr)
    urllib.request.urlretrieve(SOURCE_URL, archive)
    with zipfile.ZipFile(archive) as zf:
        zf.extract(SOURCE_NAME, CACHE)
    return txt


def build(source: Path | None, check_only: bool) -> int:
    txt = fetch(source)
    rows: list[list] = []
    zones: list[str] = []
    zone_index: dict[str, int] = {}
    covered: set[tuple[str, str]] = set()

    with txt.open(encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 18:
                continue
            name = _ascii(parts[COL_ASCII]) or _ascii(parts[1])
            tz = parts[COL_TZ].strip()
            cc = parts[COL_CC].strip().upper()
            if not name or not tz or len(cc) != 2:
                continue
            try:
                lat = round(float(parts[COL_LAT]), COORD_DECIMALS)
                lon = round(float(parts[COL_LON]), COORD_DECIMALS)
            except ValueError:
                continue

            # The zone string repeats for every city in it, and there are only a few hundred distinct
            # ones: storing them once and an index per row is worth well over a megabyte.
            zi = zone_index.get(tz)
            if zi is None:
                zi = len(zones)
                zones.append(tz)
                zone_index[tz] = zi

            rows.append([name, cc, lat, lon, zi])
            covered.add((name.lower(), cc))

    rows.sort(key=lambda r: (r[1], r[0]))

    # Every alias must point at a place that is actually in the index. A dead alias is worse than no
    # alias: the user types their birthplace, is told it does not exist, and has no way to know why.
    shipped = {(r[0].lower(), r[1]) for r in rows}
    dead = [f"{alias} → {name} ({cc})" for alias, name, cc in ALIASES if (name.lower(), cc) not in shipped]

    if check_only:
        missing = [f"{n} ({cc})" for n, cc in REQUIRED if (n.lower(), cc) not in covered]
        print(f"{len(rows):,} places loaded from {txt.name}")
        if missing:
            print(f"MISSING required place(s): {', '.join(missing)}")
            return 1
        if dead:
            print(f"DEAD alias target(s): {', '.join(dead)}")
            return 1
        print(f"all {len(REQUIRED)} required places and {len(ALIASES)} aliases covered")
        return 0

    if dead:
        print("DEAD alias target(s) — fix ALIASES before shipping:\n  " + "\n  ".join(dead), file=sys.stderr)
        return 1
        return 1

    # `[name, cc, lat, lon, zoneIndex]` — arrays rather than objects, because this asset is ~70k rows
    # and the field names would cost more than the data.
    payload = {
        "v": 1,
        "source": "GeoNames cities5000 (CC BY 4.0)",
        "zones": zones,
        "places": rows,
        # alias → [shipped name, cc]
        "aliases": {alias: [name, cc] for alias, name, cc in ALIASES},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=True), encoding="utf-8")

    raw = OUT.stat().st_size
    print(f"wrote {OUT.relative_to(REPO_ROOT)} — {len(rows):,} places, {len(zones)} zones, {raw / 1_000_000:.2f} MB")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", type=Path, help="a GeoNames .txt already on disk (skips the download)")
    ap.add_argument("--check", action="store_true", help="verify coverage; write nothing")
    args = ap.parse_args()
    return build(args.source, args.check)


if __name__ == "__main__":
    sys.exit(main())
