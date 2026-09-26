#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
R=candidates_horoscope/reports
RL=src/saju_html/md_to_saju_pdf.py
HT=src/saju_html/md_to_saju_html_pdf.py
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
for n in harish mahesh pawan sruthi gurumoorthy vishnu-priya rm; do
  pdf $RL $R/$n/$n-report.md $R/$n/$n-report.pdf "${NAME[$n]} — Deep Destiny Report" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
for n in harish mahesh gurumoorthy vishnu-priya; do
  pdf $RL $R/$n/$n-combined.md $R/$n/$n-combined.pdf "${NAME[$n]} — Deep Destiny Report" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
for n in mahesh vishnu-priya; do
  pdf $HT $R/$n/$n-combined.md $R/$n/$n-combined-html.pdf "${NAME[$n]} — Deep Destiny Report" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" deep
done
for n in harish pawan sruthi gurumoorthy; do
  pdf $RL $R/$n/career.md $R/$n/career.pdf "${NAME[$n]} — Career & Wealth Deep-Dive" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}"
done
n=vishnu-priya
for t in sample essential deep; do
  pdf $RL $R/$n/$n-$t.md $R/$n/$n-$t.pdf "${NAME[$n]} — ${LABEL[$t]}" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" $t
done
n=rm
for t in sample essential; do
  pdf $RL $R/$n/rm-$t.md $R/$n/rm-$t-report.pdf "${NAME[$n]} — ${LABEL[$t]}" "${NAME[$n]}" "${DOB[$n]}" "${DM[$n]}" $t
done
C=candidates_horoscope/marriage_compatibility
for t in basic deep; do
  sfx=""; [ $t = deep ] && sfx=_deep
  python3 src/saju_html/md_to_saju_compat_pdf.py $C/harish_manvitha/harish_manvitha_compatibility$sfx.md --name-a Harish --name-b Manvitha \
    --dob-a "4 June 1992, 03:10 IST" --dob-b "3 December 1996, 21:15 IST" --day-master-a 辛 --day-master-b 甲 --tier $t \
    --output $C/harish_manvitha/harish_manvitha_compatibility$sfx.pdf >/dev/null && echo "built harish_manvitha $t"
  python3 src/saju_html/md_to_saju_compat_pdf.py $C/pawan_sruthi/pawan_sruthi_compatibility$sfx.md --name-a Pawan --name-b Sruthi \
    --dob-a "3 October 1991, 23:45 IST" --dob-b "11 December 1993, 02:45 IST" --day-master-a 丙 --day-master-b 丙 --tier $t \
    --output $C/pawan_sruthi/pawan_sruthi_compatibility$sfx.pdf >/dev/null && echo "built pawan_sruthi $t"
done
cp $R/rm/rm-sample-report.pdf apps/landing-page/public/demo-rm-sample.pdf
cp $R/rm/rm-essential-report.pdf apps/landing-page/public/demo-rm-essential.pdf
cp $R/rm/rm-report.pdf apps/landing-page/public/demo-rm-deep.pdf
echo "copied landing demos"
cp candidates_horoscope/marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility.pdf apps/landing-page/public/demo-compat-basic.pdf
cp candidates_horoscope/marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility_deep.pdf apps/landing-page/public/demo-compat-deep.pdf
# Rich HTML/Playwright backend (falls back to ReportLab if no browser is available).
for n in mahesh vishnu-priya; do
  python3 "$HT" --input "$R/$n/$n-combined.md" --output "$R/$n/$n-combined-html.pdf" \
    --title "${NAME[$n]} — Deep Destiny Report" --client "${NAME[$n]}" --dob "${DOB[$n]}" \
    --day-master "${DM[$n]}" --tier deep >/dev/null && echo "built $R/$n/$n-combined-html.pdf"
done
