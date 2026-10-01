#!/usr/bin/env bash
# Regenerate every engine-generated client report (markdown, compat pairs, combined
# reports, PDFs). Edit REF in regen step for a new reference date.
set -euo pipefail
cd "$(dirname "$0")/.."
# The engine is a src/ layout package, not an installed distribution. Every
# step below (saju_engine CLI, tools/regen/compat.py, combine_candidate_report,
# pdfs.sh) imports it, so export the path here rather than relying on the
# caller's shell — the script previously only worked if the caller happened
# to have PYTHONPATH=src set (2026-10-01).
export PYTHONPATH="${PWD}/src${PYTHONPATH:+:${PYTHONPATH}}"
bash tools/regen/markdown.sh
python3 tools/regen/compat.py
for n in harish mahesh gurumoorthy vishnu-priya; do python3 src/saju_html/combine_candidate_report.py "$n"; done
bash tools/regen/pdfs.sh
