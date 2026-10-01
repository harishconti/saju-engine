#!/usr/bin/env python3
"""Generate the cross-candidate business analysis for Sruthi, Pawan, Harish.

Canonical trio + relationships live here so the report is reproducible from
one command. Writes to candidates_horoscope/cross-candidate-reports/.

Usage:
    PYTHONPATH=src python3 tools/gen_cross_candidate_report.py [--output PATH]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from saju_engine.engine import compute_chart  # noqa: E402
from saju_engine.cross_candidate_report import generate_cross_candidate_report  # noqa: E402

REF = dict(reference_year=2026, reference_month=9, reference_day=26)


def _build_members():
    harish = compute_chart(
        name="Harish", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5, **REF,
    )
    sruthi = compute_chart(
        name="Sruthi", gender="F", year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.45, utc_offset=5.5, **REF,
    )
    pawan = compute_chart(
        name="Pawan", gender="M", year=1991, month=10, day=3, hour=23, minute=45,
        longitude=79.19, utc_offset=5.5, **REF,
    )
    return [
        {"name": "Harish", "chart": harish, "override": None},
        {"name": "Sruthi", "chart": sruthi, "override": "Earth"},
        {"name": "Pawan", "chart": pawan, "override": "Water"},
    ]


RELATIONSHIPS = [
    {"a": "Harish", "b": "Sruthi", "kind": "siblings"},
    {"a": "Pawan", "b": "Sruthi", "kind": "spouses"},
    {"a": "Harish", "b": "Pawan", "kind": "co-founders"},
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the cross-candidate business report.")
    ap.add_argument(
        "--output", type=Path,
        default=Path("candidates_horoscope/cross-candidate-reports/"
                     "cross-candidate-business-analysis.md"),
        help="Output .md path.",
    )
    ap.add_argument("--reference-date", default="2026-09-26")
    args = ap.parse_args()

    md = generate_cross_candidate_report(
        _build_members(), RELATIONSHIPS, reference_date=args.reference_date,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md, encoding="utf-8")
    print(f"Wrote {args.output} ({len(md)} bytes)")


if __name__ == "__main__":
    main()
