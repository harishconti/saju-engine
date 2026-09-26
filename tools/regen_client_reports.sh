#!/usr/bin/env bash
# Regenerate every engine-generated client report (markdown, compat pairs, combined
# reports, PDFs). Edit REF in regen step for a new reference date.
set -euo pipefail
cd "$(dirname "$0")/.."
bash tools/regen/markdown.sh
python3 tools/regen/compat.py
for n in harish mahesh gurumoorthy vishnu-priya; do python3 src/saju_html/combine_candidate_report.py "$n"; done
bash tools/regen/pdfs.sh
