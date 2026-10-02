"""Fixed inputs for the golden-snapshot report test (P2, 2026-10-02).

Every report generator is rendered for fixed charts with a fixed reference
date so output is deterministic. A refactor that changes any byte of these
files changed client output.
"""
from __future__ import annotations

from typing import Dict

from saju_engine.compat_report import generate_compat_report
from saju_engine.cross_candidate_report import generate_cross_candidate_report
from saju_engine.engine import compute_chart
from saju_engine.premium_report import generate_premium_report

REF = dict(reference_year=2026, reference_month=6, reference_day=1)
GEN_DATE = "2026-06-01"

CHARTS = {
    # Textbook case (tests/test_textbook_cases.py) — Korea, male.
    "park": dict(year=1917, month=11, day=14, hour=10, minute=0, gender="M",
                 utc_offset=9.0, longitude=128.74, name="Park"),
    # Non-KST chart (exercises the S1 offset path) — New York, female.
    "ny": dict(year=1990, month=6, day=15, hour=10, minute=0, gender="F",
               utc_offset=-5.0, longitude=-74.0, name="Nova"),
    # Winter Water-month chart, Korea, female.
    "seoul": dict(year=1985, month=12, day=20, hour=6, minute=30, gender="F",
                  utc_offset=9.0, longitude=126.98, name="Seo"),
}
TIERS = ["sample", "essential", "deep", "career", "luck-cycle"]


def _chart(key: str):
    return compute_chart(**CHARTS[key], **REF)


def golden_outputs() -> Dict[str, str]:
    out: Dict[str, str] = {}
    charts = {k: _chart(k) for k in CHARTS}
    for key, chart in charts.items():
        for tier in TIERS:
            out[f"{key}-{tier}.md"] = generate_premium_report(
                chart, tier=tier, generation_date=GEN_DATE)
    for a, b in (("park", "seoul"), ("ny", "seoul")):
        for tier in ("basic", "deep"):
            out[f"compat-{a}-{b}-{tier}.md"] = generate_compat_report(
                charts[a], charts[b], charts[a].name, charts[b].name,
                generation_date=GEN_DATE, tier=tier)
    out["cross-candidate.md"] = _cross_candidate(charts)
    return out


def _cross_candidate(charts) -> str:
    members = [
        {"name": "Park", "chart": charts["park"], "override": None},
        {"name": "Seo", "chart": charts["seoul"], "override": None},
    ]
    relationships = [{"a": "Park", "b": "Seo", "kind": "co-founders"}]
    return generate_cross_candidate_report(
        members, relationships, reference_date="2026-06-01")
