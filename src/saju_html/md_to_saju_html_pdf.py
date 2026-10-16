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

Or compute the chart and render it directly (same flags as md_to_saju_pdf.py):
    python3 src/saju_html/md_to_saju_html_pdf.py --from-chart --tier essential \
        --output out/sruthi-report.pdf --gender F --birth-year 1993 --birth-month 12 \
        --birth-day 11 --birth-hour 2 --birth-minute 45 --city Pallipat --utc-offset 5.5

Or via the wrapper (HTML is its default backend):
    ./tools/build-pdf.sh sruthi
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make saju_engine / saju_html importable when this script is run directly.
SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from saju_html.chart_input import (  # noqa: E402
    TIER_CHOICES,
    add_chart_args,
    chart_from_args,
    intermediate_md_path,
    prepare_chart_render,
)
from saju_html.renderer import build_pdf_with_backend  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Build a styled PDF from Saju markdown via HTML/Playwright.")
    ap.add_argument("--input", type=Path, help="Path to the source .md file (omit with --from-chart).")
    ap.add_argument("--output", required=True, type=Path, help="Path to write the PDF.")
    ap.add_argument("--title", default="Saju Reading")
    ap.add_argument("--client", default="")
    ap.add_argument("--dob", default="")
    ap.add_argument("--day-master", default="")
    ap.add_argument("--css", type=Path, default=None, help="Optional custom CSS file.")
    ap.add_argument("--report-id", default="",
                    help="Unique report ID for cover/footer branding (auto-derived if omitted).")
    ap.add_argument("--web", action="store_true",
                    help="Write the standalone web document (HTML) instead of a PDF. "
                         "Output stays a single self-contained file: inline CSS and SVG, "
                         "no external requests.")
    ap.add_argument("--audio-url", default="",
                    help="With --web, place an audio player in the MP3 Audio Summary section.")
    ap.add_argument("--compact", action="store_true",
                    help="Use a compact in-line header for the free one-page Hook tier.")
    ap.add_argument("--tier", choices=TIER_CHOICES, default=None,
                    help="Optional tier label (e.g. sample, essential, deep). "
                         "Sets the body class for tier-specific CSS hooks.")
    add_chart_args(ap)
    args = ap.parse_args()

    created_md: Path | None = None
    if args.web:
        # The web document is written directly: no browser, no PDF step, nothing to
        # install. It is the same `markdown_to_html` the PDF path uses, in web mode.
        from saju_html.renderer import markdown_to_html

        out = args.output
        if out.suffix.lower() not in (".html", ".htm"):
            ap.error("--web writes HTML; give --output a .html path")
        created = None
        if args.from_chart:
            chart = chart_from_args(ap, args)
            md_target = intermediate_md_path(out, args.overwrite_report)
            if not md_target.exists():
                created = md_target
            kw = prepare_chart_render(
                chart, out, title=args.title, client=args.client, dob=args.dob,
                day_master=args.day_master, overwrite_report=args.overwrite_report,
                tier=args.tier, report_id=args.report_id)
            md_path = kw["input_md"]
        else:
            if not args.input:
                ap.error("--input is required (or pass --from-chart with birth data)")
            md_path = args.input
        try:
            document = markdown_to_html(
                Path(md_path).read_text(encoding="utf-8"),
                title=args.title, client=args.client, dob=args.dob,
                day_master=args.day_master, report_id=args.report_id,
                compact=args.compact, tier=args.tier, web=True,
                audio_url=args.audio_url,
            )
        except Exception as exc:  # noqa: BLE001 - report the cause, drop the sidecar
            if created is not None:
                created.unlink(missing_ok=True)
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(document, encoding="utf-8")
        if created is not None:
            created.unlink(missing_ok=True)   # the sidecar .md is not wanted here
        print(f"Wrote {out} ({out.stat().st_size} bytes) [web document]")
        return

    if args.from_chart:
        md_target = intermediate_md_path(args.output, args.overwrite_report)
        if not md_target.exists():
            created_md = md_target  # only remove it on failure if this run made it
        chart = chart_from_args(ap, args)
        kw = prepare_chart_render(
            chart, args.output, title=args.title, client=args.client, dob=args.dob,
            day_master=args.day_master, overwrite_report=args.overwrite_report,
            tier=args.tier, report_id=args.report_id)
    else:
        if not args.input:
            ap.error("--input is required (or pass --from-chart with birth data)")
        kw = {"input_md": args.input, "client": args.client, "dob": args.dob,
              "day_master": args.day_master, "report_id": args.report_id}

    try:
        out, backend = build_pdf_with_backend(
            output_pdf=args.output,
            title=args.title,
            css_path=args.css,
            compact=args.compact,
            tier=args.tier,
            **kw,
        )
    except RuntimeError as exc:
        if created_md is not None:
            created_md.unlink(missing_ok=True)
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    mode = {"html-playwright": "html-playwright mode",
            "reportlab-fallback": "reportlab fallback mode"}[backend]
    print(f"Wrote {out} ({out.stat().st_size} bytes) [{mode}]")


if __name__ == "__main__":
    main()
