"""Regenerate tests/golden/*.md. Only run when a change to client output is
INTENDED and reviewed (see docs/superpowers/plans/2026-10-02-p2-report-primitives.md)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tests.golden.cases import golden_outputs  # noqa: E402

out_dir = ROOT / "tests" / "golden"
outputs = golden_outputs()
for name, text in outputs.items():
    (out_dir / name).write_text(text, encoding="utf-8")
print(f"wrote {len(outputs)} golden files to {out_dir}")
