"""N-17 (2026-09-26 audit): the engine reads sajupy's private
calendar_data.csv directly and works around its internal KST-only term-time
behaviour (E-1) — a future sajupy release could change
the CSV's schema, content, or location, and the compensations here would
silently stop matching it. `pyproject.toml` now pins `sajupy==0.2.0`; this
also pins the CSV itself by content hash, so a `pip install --upgrade sajupy`
that swaps the file is caught immediately instead of silently drifting.

Since N-3 the engine's 절기 instants come from its own packaged ephemeris
table, but sajupy's CSV still supplies the day pillar and the per-day
year/month pillars `sewoon.py` uses for annual/monthly luck.
"""
from __future__ import annotations

import hashlib
import importlib.util
import os

# Known-good hash for the sajupy 0.2.0 calendar_data.csv this engine's
# corrections (E-1, N-2, N-3 disclosure notes) were derived against.
_EXPECTED_SHA256 = "0d79ee68f78a1e4ef2a9fc42bd2ed765f47d18e88a22e9cf0264621e699e8811"


def test_sajupy_calendar_csv_matches_pinned_hash():
    spec = importlib.util.find_spec("sajupy")
    assert spec is not None and spec.origin is not None, "sajupy is not importable"
    csv_path = os.path.join(os.path.dirname(spec.origin), "calendar_data.csv")
    digest = hashlib.sha256(open(csv_path, "rb").read()).hexdigest()
    assert digest == _EXPECTED_SHA256, (
        "sajupy's calendar_data.csv content changed since this engine's "
        "term-time corrections (E-1/N-2/N-3) were derived against it — "
        "re-verify them against the new file before updating this hash."
    )
