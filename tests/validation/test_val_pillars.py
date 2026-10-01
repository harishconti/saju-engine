"""W1 pillar harness — fixture-driven cross-validation.

See the 2026-09 validation campaign design (removed 2026-10-01).
Every fixture entry is checked by run_fixture; documented_interpretation
entries that mismatch are reported as xfail (visible, non-failing) so school
disagreements never mask engine bugs.
"""
from __future__ import annotations

import pytest

from saju_engine.validation import load_fixtures, run_fixture

ENTRIES = load_fixtures("pillars")


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_pillar_fixture(entry):
    result = run_fixture(entry)
    if entry["status"] == "documented_interpretation" and result["status"] != "PASS":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]