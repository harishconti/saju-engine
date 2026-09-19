#!/usr/bin/env bash
# Build a polished PDF for a candidate's Saju report.
#
# Usage (mode 1: from .md):
#   tools/build-pdf.sh sruthi
#   tools/build-pdf.sh sruthi "Sruthi — A Saju Reading" "Sruthi" "11 December 1993, 02:45 IST" "Bing Fire (Yang Fire)"
#
# Usage (mode 2: from chart, Priority 3):
#   tools/build-pdf.sh sruthi "Title" "Client" "DOB" "DayMaster" \
#       --from-chart --tier essential --gender F --birth-year 1993 --birth-month 12 --birth-day 11 \
#       --birth-hour 2 --birth-minute 45 --city Pallipat --utc-offset 5.5
#
# All "--flag value" pairs after the 5 positional args are forwarded to
# the Python script untouched. This avoids the bash array-splitting
# pitfall where flag values get accidentally classified as positionals.
#
# For just running on Sruthi with the default cover-page values, call with no args.
#
# Compat (두 분 궁합) reading:
#   Use `python3 src/saju_html/md_to_saju_compat_pdf.py <compat.md> --name-a ... --name-b ...`
#   instead — build-pdf.sh is for single-chart reports.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Backend selection: scan all args for --html / --combined; remove them before positional logic.
USE_HTML=0
COMBINED=0
NEW_ARGS=()
for a in "$@"; do
  if [ "$a" = "--html" ]; then
    USE_HTML=1
  elif [ "$a" = "--combined" ]; then
    COMBINED=1
  else
    NEW_ARGS+=("$a")
  fi
done
set -- "${NEW_ARGS[@]}"

# The 5 positional args come first. Anything after is a flag/value pair to forward.
NAME="${1:-sruthi}"
TITLE="${2:-Sruthi — A Saju Reading}"
CLIENT="${3:-Sruthi}"
DOB="${4:-11 December 1993, 02:45 IST (Pallipat, Tamil Nadu)}"
DAY_MASTER="${5:-Bing Fire (Yang Fire) — the 'Red Tiger'}"
shift 5 2>/dev/null || shift $#   # remove the positional args; leave flags

if [ "$COMBINED" = "1" ]; then
  INPUT="$PROJECT_ROOT/candidates_horoscope/reports/$NAME/$NAME-combined.md"
  if [ "$USE_HTML" = "1" ]; then
    OUTPUT="$PROJECT_ROOT/candidates_horoscope/reports/$NAME/$NAME-combined-html.pdf"
  else
    OUTPUT="$PROJECT_ROOT/candidates_horoscope/reports/$NAME/$NAME-combined.pdf"
  fi
else
  INPUT="$PROJECT_ROOT/candidates_horoscope/reports/$NAME/$NAME-report.md"
  OUTPUT="$PROJECT_ROOT/candidates_horoscope/reports/$NAME/$NAME-report.pdf"
fi

# Did the user pass --from-chart?
FROM_CHART=0
for a in "$@"; do
  if [ "$a" = "--from-chart" ]; then FROM_CHART=1; fi
done

if [ ! -f "$INPUT" ] && [ "$FROM_CHART" = "0" ]; then
  echo "ERROR: input not found: $INPUT"
  echo "Tip: pass --from-chart to compute the chart from birth data instead."
  exit 1
fi

: "${SAJU_SITE:=$(python3 -c "import site; print(site.getusersitepackages())")}"
# Derive the user local root from the site-packages path (e.g. .../.local/lib/python3.x/site-packages → .../.local/lib).
USER_LOCAL="${SAJU_SITE%/*/*}"
export LD_LIBRARY_PATH="$USER_LOCAL/usr/lib/x86_64-linux-gnu:$USER_LOCAL/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="$SAJU_SITE${PYTHONPATH:+:$PYTHONPATH}"

if [ "$USE_HTML" = "1" ]; then
  PDF_TOOL="$PROJECT_ROOT/src/saju_html/md_to_saju_html_pdf.py"
else
  PDF_TOOL="$PROJECT_ROOT/src/saju_html/md_to_saju_pdf.py"
fi

if [ "$FROM_CHART" = "1" ]; then
  python3 "$PDF_TOOL" \
    --from-chart \
    --output "$OUTPUT" \
    --title "$TITLE" \
    --client "$CLIENT" \
    --dob "$DOB" \
    --day-master "$DAY_MASTER" \
    "$@"
else
  python3 "$PDF_TOOL" \
    --input "$INPUT" \
    --output "$OUTPUT" \
    --title "$TITLE" \
    --client "$CLIENT" \
    --dob "$DOB" \
    --day-master "$DAY_MASTER" \
    "$@"
fi

echo ""
echo "Built: $OUTPUT"
