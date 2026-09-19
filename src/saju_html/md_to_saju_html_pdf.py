#!/usr/bin/env python3
"""CLI for the HTML/Playwright PDF generator.

Mirrors the interface of `md_to_saju_pdf.py` so the wrapper script can route
to either backend with minimal changes.

Usage:
    python3 src/saju_html/md_to_saju_html_pdf.py \
        --input candidates_horoscope/reports/sruthi/sruthi-report.md \
        --output candidates_horoscope/reports/sruthi/sruthi-report.pdf \
        --title "Sruthi — Saju Reading" \
        --client "Sruthi" \
        --dob "11 December 1993" \
        --day-master "Bing (Yang Fire)"

Or via the wrapper:
    ./tools/build-pdf.sh --html sruthi
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make saju_engine / saju_html importable when this script is run directly.
SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from saju_html.renderer import build_pdf  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a styled PDF from Saju markdown via HTML/Playwright.")
    ap.add_argument("--input", type=Path, required=True, help="Path to the source .md file.")
    ap.add_argument("--output", required=True, type=Path, help="Path to write the PDF.")
    ap.add_argument("--title", default="Saju Reading")
    ap.add_argument("--client", default="")
    ap.add_argument("--dob", default="")
    ap.add_argument("--day-master", default="")
    ap.add_argument("--css", type=Path, default=None, help="Optional custom CSS file.")
    ap.add_argument("--report-id", default="",
                    help="Unique report ID for cover/footer branding (auto-derived if omitted).")
    ap.add_argument("--compact", action="store_true",
                    help="Use a compact in-line header for the free one-page Hook tier.")
    ap.add_argument("--tier", default=None,
                    help="Optional tier label (e.g. sample, essential, deep). "
                         "Sets the body class for tier-specific CSS hooks.")
    args = ap.parse_args()

    out = build_pdf(
        input_md=args.input,
        output_pdf=args.output,
        title=args.title,
        client=args.client,
        dob=args.dob,
        day_master=args.day_master,
        css_path=args.css,
        report_id=args.report_id,
        compact=args.compact,
        tier=args.tier,
    )
    print(f"Wrote {out} ({out.stat().st_size} bytes) [html-playwright mode]")


if __name__ == "__main__":
    main()
