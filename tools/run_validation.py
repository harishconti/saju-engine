#!/usr/bin/env python3
"""Run all validation fixtures and write the campaign report.

Exit code: 0 when no FAIL, 1 otherwise (gate enforcement).
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from saju_engine.validation import collect_results, render_report  # noqa: E402


def main() -> int:
    results = collect_results()
    report = render_report(results)
    out = REPO / "docs" / "audits" / "2026-09-engine-validation-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    fails = sum(1 for rows in results.values() for r in rows if r["status"] == "FAIL")
    interp = sum(1 for rows in results.values() for r in rows
                 if r["status"] == "INTERPRETATION")
    total = sum(len(rows) for rows in results.values())
    print(f"report written: {out}")
    print(f"checks: {total} (PASS {total - fails - interp}, INTERPRETATION {interp}, FAIL {fails})")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())