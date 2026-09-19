#!/usr/bin/env python3
"""Render the 두 분 궁합 (Compatibility Reading) markdown to a PDF.

This wraps `src/saju_html/md_to_saju_pdf.py::build_pdf` so the compat product gets
the same premium visual treatment as the single-chart tiers, with the only
differences being:
  - Title is "두 분 궁합 — {name_a} × {name_b}"
  - Cover metadata lists both DOBs and Day Masters
  - Footer brands the report as a Compat reading

Usage:
    python3 src/saju_html/md_to_saju_compat_pdf.py path/to/compat-with-{name}.md \\
        --name-a "Mahesh" --name-b "Vishnu Priya" \\
        --dob-a "19 January 1995" --dob-b "7 June 2001" \\
        --day-master-a "庚" --day-master-b "辛" \\
        --output path/to/compat-with-{name}.pdf

Default output (no --output): candidates_horoscope/marriage_compatibility/{name_a}_{name_b}/{name_a}_{name_b}_compatibility.pdf for basic, or ..._compatibility_deep.pdf for deep.
(storage convention: all two-chart 궁합 readings live in a per-pair subfolder under
`marriage_compatibility/`, named with the partners' slugified actual names. Basic
reports use the unsuffixed name; deep reports append "_deep".)
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

_SAJU_SITE = os.environ.get("SAJU_SITE")
if _SAJU_SITE and _SAJU_SITE not in sys.path:
    sys.path.insert(0, _SAJU_SITE)

from saju_html.md_to_saju_pdf import build_pdf  # type: ignore  # noqa: E402


def _slugify(name: str) -> str:
    import re
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    return re.sub(r"[-\s]+", "-", name) or "compat"


def main() -> int:
    p = argparse.ArgumentParser(description="Render a compat markdown to PDF.")
    p.add_argument("input_md", type=Path, help="Path to compat markdown report")
    p.add_argument("--name-a", required=True, help="Partner A name")
    p.add_argument("--name-b", required=True, help="Partner B name")
    p.add_argument("--dob-a", required=True, help="Partner A formatted DOB")
    p.add_argument("--dob-b", required=True, help="Partner B formatted DOB")
    p.add_argument("--day-master-a", required=True, help="Partner A Day Master (e.g., 庚)")
    p.add_argument("--day-master-b", required=True, help="Partner B Day Master (e.g., 辛)")
    p.add_argument("--output", type=Path, help="Output PDF path (default: candidates_horoscope/marriage_compatibility/{name_a}_{name_b}/{name_a}_{name_b}_compatibility.pdf for basic, ..._compatibility_deep.pdf for deep)")
    p.add_argument("--report-id", default="", help="Custom report ID for footer")
    p.add_argument("--tier", default="basic", choices=("basic", "deep"),
                   help=(
                       "Compat report tier: basic (default, compact ~4-page snapshot), "
                       "or deep (full 11-sub-system report + individual snapshots + timing overlay)."
                   ))
    args = p.parse_args()

    input_md: Path = args.input_md.resolve()
    if not input_md.exists():
        print(f"Input markdown not found: {input_md}", file=sys.stderr)
        return 2

    if args.output:
        output_pdf: Path = args.output.resolve()
        # The default branch below creates its pair directory; an explicit
        # --output must do the same, or reportlab's SaveToFile fails with a
        # bare FileNotFoundError on a path whose parent does not yet exist.
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Storage convention (2026-07-06, revised): each pair gets its own
        # subfolder under marriage_compatibility/, named with the partners'
        # actual slugified names. Basic reports use the unsuffixed name;
        # deep reports append "_deep".
        repo_root = Path(__file__).resolve().parent.parent
        slug_a = _slugify(args.name_a)
        slug_b = _slugify(args.name_b)
        pair_dir = repo_root / "candidates_horoscope" / "marriage_compatibility" / f"{slug_a}_{slug_b}"
        pair_dir.mkdir(parents=True, exist_ok=True)
        suffix = "_deep" if args.tier == "deep" else ""
        default_name = f"{slug_a}_{slug_b}_compatibility{suffix}.pdf"
        output_pdf = pair_dir / default_name

    if args.tier == "deep":
        title = f"Deep Compatibility Reading — {args.name_a} × {args.name_b}"
    else:
        title = f"Compatibility Reading — {args.name_a} × {args.name_b}"
    # Composite "client" line — used by build_pdf() for the cover metadata.
    client = f"{args.name_a} ({args.day_master_a}) · {args.name_b} ({args.day_master_b})"
    dob = f"{args.dob_a} · {args.dob_b}"
    day_master = f"{args.day_master_a}/{args.day_master_b}"

    # The PDF backend still expects the legacy "compat" tier for styling.
    build_tier = "compat"
    report_id = args.report_id or f"COMP-{_slugify(args.name_a)}-x-{_slugify(args.name_b)}-{date.today().strftime('%Y%m%d')}-{args.tier}"

    build_pdf(
        input_md=input_md,
        output_pdf=output_pdf,
        title=title,
        client=client,
        dob=dob,
        day_master=day_master,
        report_id=report_id,
        tier=build_tier,
    )
    print(f"Wrote: {output_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())