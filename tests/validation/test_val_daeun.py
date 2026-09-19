"""W2 대운 harness — fixture-driven cross-validation.

See docs/superpowers/specs/2026-09-13-engine-validation-campaign-design.md.
Migrated 1:1 from the seven textbook daeun regression tests in
tests/test_textbook_cases.py (Plan 1 kept them until this plan).
Appending fixture entries auto-extends the suite.
"""
from __future__ import annotations

import pytest

from saju_engine.validation import load_fixtures, run_daeun_fixture

ENTRIES = load_fixtures("daeun")


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_daeun_fixture(entry):
    result = run_daeun_fixture(entry)
    if entry["status"] == "documented_interpretation" and result["status"] != "PASS":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]