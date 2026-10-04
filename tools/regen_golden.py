"""Regenerate tests/golden/*.md (default) or, with --html, the rendered-HTML
snapshots in tests/golden_html/*.html (derived from the committed golden .md,
which --html never rewrites). Only run when a change to client output is
INTENDED and reviewed (see docs/superpowers/plans/2026-10-02-p2-report-primitives.md)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tests.golden.cases import golden_outputs, render_golden_html  # noqa: E402

if "--html" in sys.argv[1:]:
    md_dir = ROOT / "tests" / "golden"
    html_dir = ROOT / "tests" / "golden_html"
    html_dir.mkdir(exist_ok=True)
    n = 0
    for md in sorted(md_dir.glob("*.md")):
        (html_dir / (md.stem + ".html")).write_text(
            render_golden_html(md.name, md.read_text(encoding="utf-8")), encoding="utf-8")
        n += 1
    print(f"wrote {n} golden HTML files to {html_dir}")
    sys.exit(0)

out_dir = ROOT / "tests" / "golden"
outputs = golden_outputs()
for name, text in outputs.items():
    (out_dir / name).write_text(text, encoding="utf-8")
print(f"wrote {len(outputs)} golden files to {out_dir}")
