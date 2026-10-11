#!/usr/bin/env python3
"""Compliance QA gate for a generated Saju report (markdown).

Usage:
  python3 tools/qa_compliance.py candidates_horoscope/reports/rm/rm_deep.md
  python3 tools/qa_compliance.py --json report.md      # machine-readable
  python3 tools/qa_compliance.py --warn-only report.md # never exit non-zero

Exit codes: 0 clean, 1 flagged, 2 classifier unavailable/error.
Requires the optional TYPESAFE_API_KEY. Never edits the report.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from saju_qa import TypesafeClient, TypesafeError, scan_report


def main() -> int:
    ap = argparse.ArgumentParser(description="Saju report compliance QA gate.")
    ap.add_argument("report", help="path to a report markdown file")
    ap.add_argument("--json", action="store_true", help="print full JSON report")
    ap.add_argument("--warn-only", action="store_true",
                    help="never exit non-zero on flags")
    args = ap.parse_args()

    client = TypesafeClient()
    if not client.available():
        print("TYPESAFE_API_KEY not set — compliance QA skipped.", file=sys.stderr)
        return 2

    md = Path(args.report).read_text(encoding="utf-8")
    try:
        report = scan_report(md, client=client)
    except TypesafeError as exc:
        print(f"compliance QA failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status = "CLEAN" if report["clean"] else "FLAGGED"
        print(f"{status}: {report['n_blocks']} blocks, "
              f"{len(report['flagged'])} flagged, counts={report['counts']}")
        for f in report["flagged"]:
            print(f"  [{f['index']}] {', '.join(f['flags'])} :: {f['excerpt'][:90]}…")

    if report["clean"] or args.warn_only:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
