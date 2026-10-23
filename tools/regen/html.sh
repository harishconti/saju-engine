#!/usr/bin/env bash
# Regenerate the *web document* (the reading) beside every engine-generated
# client report. Mirrors tools/regen/pdfs.sh's deliverable list: whatever has a
# canonical PDF gets a sibling .html, rendered with `--web` (no browser needed).
#
# The web document is the artefact a client reads; the PDF is the keepsake. It
# is one self-contained file (inline CSS + SVG, embedded fonts, no requests) so
# the same bytes can be served at the report link and kept. See
# docs/openwiki/products/reports.md § "The web document".
#
# The public demo readings (apps/web/public/demo/*.html) are already written by
# pdfs.sh's demo_rm/demo_compat helpers; this script does not touch them.
set -euo pipefail
cd "$(dirname "$0")/../.."
R=candidates_horoscope/reports
HT=src/saju_html/md_to_saju_html_pdf.py
PY="${PYTHON:-python3}"
# web() — single-chart reading. tool in out title client dob dm [tier]
web() {
  "$PY" "$1" --input "$2" --output "$3" --title "$4" --client "$5" \
    --dob "$6" --day-master "$7" ${8:+--tier $8} --web >/dev/null && echo "built $3"
}
declare -A NAME DOB DM LABEL
LABEL[sample]="The Hook · Complimentary Reading"; LABEL[essential]="Essential Report"; LABEL[deep]="Deep Destiny Report"
NAME[harish]="Harish"; DOB[harish]="4 June 1992, 03:10 AM IST (Pallipattu, Tamil Nadu)"; DM[harish]="Sin (Yin Metal)"
NAME[mahesh]="Mahesh"; DOB[mahesh]="19 January 1995, 11:50 PM IST (Ambur, Tamil Nadu)"; DM[mahesh]="Gyeong (Yang Metal)"
NAME[pawan]="Pawan"; DOB[pawan]="3 October 1991, 11:45 PM IST (Vellore, Tamil Nadu)"; DM[pawan]="Byeong (Yang Fire)"
NAME[sruthi]="Sruthi"; DOB[sruthi]="11 December 1993, 02:45 AM IST (Pallipattu, Tamil Nadu)"; DM[sruthi]="Byeong (Yang Fire)"
NAME[gurumoorthy]="Gurumoorthy"; DOB[gurumoorthy]="19 July 1964, 08:30 AM IST (Tirupati, Andhra Pradesh)"; DM[gurumoorthy]="Gi (Yin Earth)"
NAME[vishnu-priya]="Vishnu Priya"; DOB[vishnu-priya]="7 June 2001, 04:45 PM IST (Mysore)"; DM[vishnu-priya]="Sin (Yin Metal)"
NAME[rm]="RM (Kim Nam-joon)"; DOB[rm]="12 September 1994, 01:28 PM KST (Seoul)"; DM[rm]="Sin (Yin Metal)"
NAME[bindu]="Bindu"; DOB[bindu]="24 March 1995, 10:10 AM IST (Kolar, Karnataka)"; DM[bindu]="Gap (Yang Wood)"
for n in harish mahesh pawan sruthi gurumoorthy vishnu-priya rm bindu; do
  web $HT $R/$n/$n-report.md $R/$n/$n-report.html "${NAME[$n]} — Deep Destiny Report" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
for n in harish mahesh gurumoorthy vishnu-priya; do
  web $HT $R/$n/$n-combined.md $R/$n/$n-combined.html "${NAME[$n]} — Deep Destiny Report" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
for n in harish pawan sruthi gurumoorthy bindu rm; do
  web $HT $R/$n/career.md $R/$n/career.html "${NAME[$n]} — Career & Wealth Deep-Dive" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}"
done
n=vishnu-priya
for t in sample essential deep; do
  web $HT $R/$n/$n-$t.md $R/$n/$n-$t.html "${NAME[$n]} — ${LABEL[$t]}" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" $t
done
n=rm
for t in sample essential; do
  web $HT $R/$n/rm-$t.md $R/$n/rm-$t.html "${NAME[$n]} — ${LABEL[$t]}" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" $t
done
for n in harish sruthi pawan bindu mahesh gurumoorthy vishnu-priya rm; do
  web $HT $R/$n/$n-luck-cycle.md $R/$n/$n-luck-cycle.html \
    "${NAME[$n]} — Luck Cycle & Lifetime Decade Roadmap" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
C=candidates_horoscope/marriage_compatibility
# Compat pairs — same list as pdfs.sh. harish_vinothini is omitted (no birth data).
compat() { # slug name_a name_b dob_a dob_b dm_a dm_b tier
  local slug=$1 na=$2 nb=$3 da=$4 db=$5 ma=$6 mb=$7 t=$8 sfx=""
  [ "$t" = deep ] && sfx=_deep
  "$PY" src/saju_html/md_to_saju_compat_pdf.py "$C/$slug/${slug}_compatibility$sfx.md" \
    --name-a "$na" --name-b "$nb" --dob-a "$da" --dob-b "$db" \
    --day-master-a "$ma" --day-master-b "$mb" --tier "$t" --web \
    --output "$C/$slug/${slug}_compatibility$sfx.html" >/dev/null \
    && echo "built $slug $t (html)"
}
for t in basic deep; do
  compat harish_manvitha Harish Manvitha "4 June 1992, 03:10 IST" "3 December 1996, 21:15 IST" 辛 甲 $t
  compat pawan_sruthi Pawan Sruthi "3 October 1991, 23:45 IST" "11 December 1993, 02:45 IST" 丙 丙 $t
  compat harish_bindu Harish Bindu "4 June 1992, 03:10 IST" "24 March 1995, 10:10 IST" 辛 甲 $t
  compat harish_srinidhi Harish Srinidhi "4 June 1992, 03:10 IST" "9 April 1994, 20:47 IST" 辛 乙 $t
  compat harish_priyanka Harish Priyanka "4 June 1992, 03:10 IST" "3 June 1996, 10:20 IST" 辛 辛 $t
  compat harish_priyanka_1998 Harish Priyanka "4 June 1992, 03:10 IST" "12 July 1998, 21:43 IST" 辛 庚 $t
  compat harish_keerthana Harish Keerthana "4 June 1992, 03:10 IST" "3 October 1996, 09:35 IST" 辛 癸 $t
  compat harish_prethivika Harish Prethivika "4 June 1992, 03:10 IST" "19 March 1993, 03:17 IST" 辛 己 $t
done
echo "done: web readings written beside every canonical report"
