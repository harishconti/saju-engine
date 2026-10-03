"""Golden snapshot: every report generator's markdown must be byte-identical
to tests/golden/*.md (P2 refactor safety net, 2026-10-02). Regenerate only for
an intended, reviewed output change: `python3 tools/regen_golden.py`."""
from pathlib import Path

import pytest

from tests.golden.cases import golden_outputs

GOLDEN = Path(__file__).resolve().parent / "golden"
OUTPUTS = golden_outputs()


@pytest.mark.parametrize("name", sorted(OUTPUTS))
def test_report_matches_golden(name):
    expected = (GOLDEN / name).read_text(encoding="utf-8")
    assert OUTPUTS[name] == expected, f"{name} drifted from its golden snapshot"


def test_golden_set_is_complete():
    on_disk = {p.name for p in GOLDEN.glob("*.md")}
    assert on_disk == set(OUTPUTS)
