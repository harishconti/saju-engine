#!/usr/bin/env bash
# Regenerate every engine-generated client report markdown after the
# 2026-09-25 audit fixes. Reference date: 2026-09-26.
set -euo pipefail
cd "$(dirname "$0")/../.."
R=candidates_horoscope/reports
REF=(--year 2026 --month 9 --day 26)
gen() { # out tier args...
  local out=$1 tier=$2; shift 2
  python -m saju_engine --format premium --tier "$tier" "${REF[@]}" --output-file "$out" "$@" >/dev/null
  echo "wrote $out"
}
H=(--date 1992-06-04 --time 03:10 --longitude 79.4408 --city "Pallipattu, Tamil Nadu" --utc-offset 5.5 --gender M --name Harish)
M=(--date 1995-01-19 --time 23:50 --longitude 78.7135 --city "Ambur, Tamil Nadu" --utc-offset 5.5 --gender M --name Mahesh)
P=(--date 1991-10-03 --time 23:45 --longitude 79.19 --city "Vellore, Tamil Nadu" --utc-offset 5.5 --gender M --name Pawan --favorable-override Water)
S=(--date 1993-12-11 --time 02:45 --longitude 79.45 --city "Pallipattu, Tamil Nadu" --utc-offset 5.5 --gender F --name Sruthi --favorable-override Earth)
G=(--date 1964-07-19 --time 08:30 --longitude 79.42 --city "Tirupati, Andhra Pradesh" --utc-offset 5.5 --gender M --name Gurumoorthy --favorable-override Metal)
V=(--date 2001-06-07 --time 16:45 --longitude 80.27 --city "Mysore" --utc-offset 5.5 --gender F --name "Vishnu Priya")
RM=(--date 1994-09-12 --time 13:28 --longitude 126.9783 --city "Seoul" --utc-offset 9 --gender M --name "RM (Kim Nam-joon)" --convention korean)
gen $R/harish/harish-report.md deep "${H[@]}"
gen $R/mahesh/mahesh-report.md deep "${M[@]}"
gen $R/pawan/pawan-report.md deep "${P[@]}"
gen $R/sruthi/sruthi-report.md deep "${S[@]}"
gen $R/gurumoorthy/gurumoorthy-report.md deep "${G[@]}"
gen $R/vishnu-priya/vishnu-priya-report.md deep "${V[@]}"
gen $R/vishnu-priya/vishnu-priya-sample.md sample "${V[@]}"
gen $R/vishnu-priya/vishnu-priya-essential.md essential "${V[@]}"
gen $R/vishnu-priya/vishnu-priya-deep.md deep "${V[@]}"
gen $R/rm/rm-report.md deep "${RM[@]}"
gen $R/rm/rm-sample.md sample "${RM[@]}"
gen $R/rm/rm-essential.md essential "${RM[@]}"
