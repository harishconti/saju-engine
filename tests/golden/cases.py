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
    # --- Fix round 1 (2026-10-02): verdict / 용신-method coverage. Found by scan.
    # verdict "extreme", 용신 method strong-dm-drain — Los Angeles, male.
    "lux": dict(year=2000, month=9, day=20, hour=2, minute=0, gender="M",
                utc_offset=-8.0, longitude=-118.2, name="Lux"),
    # verdict "extreme", 용신 method climate-balanced (조후 override) — India, female.
    "kiran": dict(year=1983, month=1, day=4, hour=6, minute=0, gender="F",
                  utc_offset=5.5, longitude=78.0, name="Kiran"),
    # verdict "weak", 용신 method weak-dm-support — London, male.
    "wren": dict(year=1965, month=9, day=22, hour=20, minute=0, gender="M",
                 utc_offset=0.0, longitude=0.0, name="Wren"),
    # verdict "strong", 용신 method climate-balanced (조후 override) — Paris, male.
    "clive": dict(year=1971, month=11, day=2, hour=5, minute=0, gender="M",
                  utc_offset=1.0, longitude=2.35, name="Clive"),
    # NOTE: verdict "extreme_weak" is unreachable (min total_score over ~92k
    # scanned charts is -3.78 vs the -5.0 threshold), so it cannot be pinned.
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
    # lux/kiran compat flags a 육파 (six-break) pair.
    for a, b in (("park", "seoul"), ("ny", "seoul"), ("lux", "kiran")):
        for tier in ("basic", "deep"):
            out[f"compat-{a}-{b}-{tier}.md"] = generate_compat_report(
                charts[a], charts[b], charts[a].name, charts[b].name,
                generation_date=GEN_DATE, tier=tier)
    # Legacy tiers still engine-supported (CLAUDE.md "Tiered Client Products").
    for tier in ("fullmap", "companion"):
        out[f"park-{tier}.md"] = generate_premium_report(
            charts["park"], tier=tier, generation_date=GEN_DATE)
    # Reader-argued 용신 override path (ny resolves to Wood; override to Fire).
    out["ny-deep-override-fire.md"] = generate_premium_report(
        charts["ny"], tier="deep", generation_date=GEN_DATE,
        favorable_override="Fire")
    # Compat favorable_element_a/_b override path.
    out["compat-lux-kiran-deep-override.md"] = generate_compat_report(
        charts["lux"], charts["kiran"], charts["lux"].name, charts["kiran"].name,
        generation_date=GEN_DATE, tier="deep",
        favorable_element_a="Wood", favorable_element_b="Water")
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


# --- Rendered-HTML snapshots (P5 Task 3, 2026-10-04) -------------------------
HTML_REPORT_ID_PREFIX = "GOLDEN-"


def html_tier_for(md_name: str):
    """Renderer ``tier`` argument for a golden markdown file name."""
    stem = md_name[:-3]
    if stem.startswith("compat-"):
        return "compat"
    if stem == "cross-candidate":
        return None
    for tier in ("luck-cycle", "career", "sample", "essential", "deep",
                 "fullmap", "companion"):
        if stem.endswith(tier) or f"-{tier}-" in stem:
            return tier
    return None


def render_golden_html(md_name: str, md_text: str) -> str:
    """The exact HTML string ``renderer.build_pdf`` prints to PDF, with fixed
    metadata so it is deterministic."""
    from saju_html.renderer import markdown_to_html

    stem = md_name[:-3]
    return markdown_to_html(
        md_text,
        title=f"Golden {stem}",
        client="Golden Client",
        dob="1 January 1990",
        day_master="Byeong (Yang Fire)",
        generation_date=GEN_DATE,
        report_id=f"{HTML_REPORT_ID_PREFIX}{stem}",
        tier=html_tier_for(md_name),
    )
