"""W2 세운/월운 harness — fixture-driven cross-validation.

See docs/superpowers/specs/2026-09-13-engine-validation-campaign-design.md.
Seed expectations cross-validate sewoon's 1984=甲子 annual anchor and the
五虎遁 monthly anchor against the W1-certified pillar layer (non-circular).
Appending fixture entries auto-extends the suite.
"""
from __future__ import annotations

import pytest

from saju_engine.validation import load_fixtures, run_sewoon_fixture

ENTRIES = load_fixtures("sewoon")


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_sewoon_fixture(entry):
    result = run_sewoon_fixture(entry)
    if entry["status"] == "documented_interpretation" and result["status"] != "PASS":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]