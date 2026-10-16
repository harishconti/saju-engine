#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
R=candidates_horoscope/reports
HT=src/saju_html/md_to_saju_html_pdf.py
# All canonical deliverable names are rendered with the HTML/Chromium backend ($HT).
# Any reportlab output must use a *-reportlab.pdf name (none are produced here).
pdf() { # tool in out title client dob dm tier
  python3 "$1" --input "$2" --output "$3" --title "$4" --client "$5" --dob "$6" --day-master "$7" ${8:+--tier $8} >/dev/null && echo "built $3"
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
  pdf $HT $R/$n/$n-report.md $R/$n/$n-report.pdf "${NAME[$n]} — Deep Destiny Report" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
for n in harish mahesh gurumoorthy vishnu-priya; do
  pdf $HT $R/$n/$n-combined.md $R/$n/$n-combined.pdf "${NAME[$n]} — Deep Destiny Report" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
for n in harish pawan sruthi gurumoorthy bindu rm; do
  pdf $HT $R/$n/career.md $R/$n/career.pdf "${NAME[$n]} — Career & Wealth Deep-Dive" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}"
done
n=vishnu-priya
for t in sample essential deep; do
  pdf $HT $R/$n/$n-$t.md $R/$n/$n-$t.pdf "${NAME[$n]} — ${LABEL[$t]}" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" $t
done
n=rm
for t in sample essential; do
  pdf $HT $R/$n/rm-$t.md $R/$n/rm-$t-report.pdf "${NAME[$n]} — ${LABEL[$t]}" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" $t
done
# Luck-cycle reports: HTML/Playwright backend so the SVG charts render.
for n in harish sruthi pawan bindu mahesh gurumoorthy vishnu-priya rm; do
  python3 "$HT" --input "$R/$n/$n-luck-cycle.md" --output "$R/$n/$n-luck-cycle.pdf" \
    --title "${NAME[$n]} — Luck Cycle & Lifetime Decade Roadmap" --client "${NAME[$n]}" \
    --dob "${DOB[$n]}" --day-master "${DM[$n]}" --tier deep >/dev/null \
    && echo "built $R/$n/$n-luck-cycle.pdf"
done
C=candidates_horoscope/marriage_compatibility
# Compat pairs. harish_vinothini is omitted (birth data not on record — its
# markdown is tracked as-is with a provenance warning and has no PDF).
compat() { # slug name_a name_b dob_a dob_b dm_a dm_b tier
  local slug=$1 na=$2 nb=$3 da=$4 db=$5 ma=$6 mb=$7 t=$8 sfx=""
  [ "$t" = deep ] && sfx=_deep
  python3 src/saju_html/md_to_saju_compat_pdf.py "$C/$slug/${slug}_compatibility$sfx.md" \
    --name-a "$na" --name-b "$nb" --dob-a "$da" --dob-b "$db" \
    --day-master-a "$ma" --day-master-b "$mb" --tier "$t" \
    --output "$C/$slug/${slug}_compatibility$sfx.pdf" >/dev/null \
    && echo "built $slug $t"
}
for t in basic deep; do
  compat harish_manvitha Harish Manvitha "4 June 1992, 03:10 IST" "3 December 1996, 21:15 IST" 辛 甲 $t
  compat pawan_sruthi Pawan Sruthi "3 October 1991, 23:45 IST" "11 December 1993, 02:45 IST" 丙 丙 $t
  compat harish_bindu Harish Bindu "4 June 1992, 03:10 IST" "24 March 1995, 10:10 IST" 辛 甲 $t
  compat harish_srinidhi Harish Srinidhi "4 June 1992, 03:10 IST" "9 April 1994, 20:47 IST" 辛 乙 $t
  compat harish_priyanka Harish Priyanka "4 June 1992, 03:10 IST" "3 June 1996, 10:20 IST" 辛 辛 $t
  compat harish_priyanka_1998 Harish Priyanka "4 June 1992, 03:10 IST" "12 July 1998, 21:43 IST" 辛 庚 $t
done
# ── Public demo PDFs ──────────────────────────────────────────────────────────────
# These are served by the WEBAPP (apps/web/public/demo/), not by the legacy landing page,
# and they are rendered with the **ReportLab** backend *from the chart* — the same backend the
# deployed engine service uses (SAJU_PDF_BACKEND=reportlab).
#
# Rendering from the chart matters: the stored markdown embeds its own cover, so re-rendering
# an existing .md would freeze a stale price/wording into the public artefact forever. That is
# exactly what happened — demo-rm-essential.pdf advertised a retired "$9 intro → $19" long
# after the product sold at $19.
DEMO=apps/web/public/demo
# Render into a scratch dir and copy ONLY the PDF. `--from-chart` always writes a sidecar
# `*-engine.md` beside the output, and that markdown still carries its knowledge/ citations —
# which the PDF renderer strips but the .md does not. `public/` is served verbatim and
# robots.txt allows /demo/, so a sidecar landing there would publish internal citations.
SCRATCH=tmp/demo-render
mkdir -p "$SCRATCH"
# Both artefacts, from one chart: the web document is what a client reads, the PDF is the
# keepsake. The marketing page links the reading first — keep the two in step.
demo_rm() { # tier
  local t=$1
  python3 src/saju_html/md_to_saju_pdf.py --from-chart \
    --name "RM (Kim Nam-joon)" --gender M \
    --birth-year 1994 --birth-month 9 --birth-day 12 --birth-hour 13 --birth-minute 28 \
    --city "Seoul" --longitude 126.978 --utc-offset 9 --tier "$t" \
    --output "$SCRATCH/demo-rm-$t.pdf" >/dev/null \
    && cp "$SCRATCH/demo-rm-$t.pdf" "$DEMO/demo-rm-$t.pdf" \
    && echo "built $DEMO/demo-rm-$t.pdf  (sidecar kept in $SCRATCH)"
  python3 src/saju_html/md_to_saju_html_pdf.py --from-chart --web \
    --name "RM (Kim Nam-joon)" --gender M \
    --birth-year 1994 --birth-month 9 --birth-day 12 --birth-hour 13 --birth-minute 28 \
    --city "Seoul" --longitude 126.978 --utc-offset 9 --tier "$t" \
    --output "$DEMO/demo-rm-$t.html" >/dev/null \
    && echo "built $DEMO/demo-rm-$t.html  (the reading)"
}

demo_rm sample
demo_rm essential
demo_rm deep

# Compat demos are copies of the tracked pair report above. NOTE: `compat()` renders with the
# HTML backend by default (better local typography), while the shipped demos and every deployed
# report are ReportLab — so if the compat demos ever need regenerating, render them explicitly
# with `md_to_saju_compat_pdf.py … --backend reportlab` rather than copying a Chromium render.
cp $C/pawan_sruthi/pawan_sruthi_compatibility.pdf      $DEMO/demo-compat-basic.pdf
cp $C/pawan_sruthi/pawan_sruthi_compatibility_deep.pdf $DEMO/demo-compat-deep.pdf
echo "copied webapp demos into $DEMO"
