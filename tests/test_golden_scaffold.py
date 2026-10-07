"""Golden snapshot of the engine's prose-scaffold + plain-words drafts.

P3-golden (2026-10-07): the client-report golden harness does not render these
draft paragraphs verbatim, so a label regression (e.g. the raw strength verdict
leaking into a plain-words label) could slip through. These snapshots pin the
scaffold for each golden chart. Regenerate only for an intended, reviewed
change: `python3 tools/regen_scaffold_golden.py`.
"""
from pathlib import Path

import pytest

from tests.golden.cases import scaffold_outputs

GOLDEN = Path(__file__).resolve().parent / "golden_scaffold"
OUTPUTS = scaffold_outputs()


@pytest.mark.parametrize("name", sorted(OUTPUTS))
def test_scaffold_matches_golden(name):
    expected = (GOLDEN / name).read_text(encoding="utf-8")
    assert OUTPUTS[name] == expected, f"{name} drifted from its golden snapshot"


def test_scaffold_golden_set_is_complete():
    on_disk = {p.name for p in GOLDEN.glob("*.md")}
    assert on_disk == set(OUTPUTS)
