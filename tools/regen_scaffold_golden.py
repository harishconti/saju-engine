"""Regenerate tests/golden_scaffold/*.md (P3-golden, 2026-10-07).

These snapshot the engine's prose-scaffold + plain-words drafts per golden
chart. Only run when a change to those drafts is INTENDED and reviewed.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tests.golden.cases import scaffold_outputs  # noqa: E402

out_dir = ROOT / "tests" / "golden_scaffold"
out_dir.mkdir(exist_ok=True)
outputs = scaffold_outputs()
for name, text in outputs.items():
    (out_dir / name).write_text(text, encoding="utf-8")
print(f"wrote {len(outputs)} scaffold goldens to {out_dir}")
