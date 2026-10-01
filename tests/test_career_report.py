"""Regression tests for the career / business / wealth deep-dive report."""
from __future__ import annotations

import io
import re

from saju_engine.engine import compute_chart
from saju_html.renderer import markdown_to_html


def _pawan():
    return compute_chart(
        name="Pawan", gender="M",
        year=1991, month=10, day=3, hour=23, minute=45,
        longitude=79.19, utc_offset=5.5,
        reference_year=2026, reference_month=9, reference_day=26,
    )


def _report(override="Water"):
    from saju_engine.career_report import generate_career_report
    return generate_career_report(_pawan(), favorable_override=override)


def test_has_all_sections():
    md = _report()
    for section in (
        "## Suitable Career Domains — Ranked",
        "## Concrete Role Ladders",
        "## Ten-God → Career Mode",
        "## Employment vs. Entrepreneurship",
        "## Income Style & Carrying Capacity",
        "## Investment Behaviour",
        "## Wealth Preservation",
        "## Career Transition Timing — Decade by Decade",
        "## Sources & Limits",
    ):
        assert section in md, f"missing section: {section}"


def test_all_ranked_domains_have_a_role_ladder():
    md = _report()
    # Domains listed in the ranked table must each appear in the role table.
    ranked = re.findall(r"^\| \*\*(?:Best Fit|Good Fit|Possible)\*\* \| ([^|]+) \|", md, flags=re.MULTILINE)
    assert len(ranked) == 12, f"expected 12 ranked domains (2 families × 6), got {len(ranked)}"
    role_block = md.split("## Concrete Role Ladders", 1)[1]
    for domain in ranked:
        assert f"| {domain.strip()} |" in role_block, f"no role ladder for {domain.strip()}"


def test_ranked_domains_are_grounded_in_knowledge_12():
    from saju_engine.report_data import _CAREER_DOMAINS
    valid = {d for domains in _CAREER_DOMAINS.values() for d, _ in domains}
    md = _report()
    ranked = re.findall(r"^\| \*\*(?:Best Fit|Good Fit|Possible)\*\* \| ([^|]+) \|", md, flags=re.MULTILINE)
    for domain in ranked:
        assert domain.strip() in valid, f"ranked domain not in KB12 families: {domain.strip()}"


def test_respects_reader_override():
    """A reader override must change the ranked families (Water/Metal for Pawan,
    not the engine's own pick)."""
    md = _report(override="Water")
    assert "**Favorable (용신):** Water" in md
    # The Best-Fit block must be Water-family domains.
    best = md.split("## Suitable Career Domains", 1)[1].split("## Concrete", 1)[0]
    best_fit = [l for l in best.splitlines() if "**Best Fit**" in l]
    assert best_fit, "expected Best Fit rows"
    for line in best_fit:
        assert any(d in line for d in ("Strategy & Consulting", "Diplomacy & International Business",
                                       "Psychology & Counseling", "Arts & Curation",
                                       "Journalism & Investigation", "Logistics & Shipping")), line


def test_timing_table_has_one_row_per_decade_and_valid_reads():
    md = _report()
    timing = md.split("## Career Transition Timing", 1)[1]
    rows = re.findall(r"^\| \d{4}–\d{4} \| \d+–\d+ \| \S+ \| .+? \| \d+/10 \| (.+?) \|$",
                      timing, flags=re.MULTILINE)
    assert len(rows) == 8, f"expected 8 decade rows, got {len(rows)}"
    assert all(r in {"expansion window", "steady build", "consolidation / defend"} for r in rows)


def test_deterministic():
    assert _report() == _report()


def test_cli_career_requires_gender():
    from saju_engine.cli import main
    err, out = io.StringIO(), io.StringIO()
    rc = main(["--date", "1991-10-03", "--time", "23:45",
               "--longitude", "79.19", "--utc-offset", "5.5",
               "--format", "career"], stdout=out, stderr=err)
    assert rc == 2
    assert "gender" in err.getvalue().lower()


def test_html_renders_without_citation_leaks():
    html = markdown_to_html(_report(), title="Pawan — Career", client="Pawan",
                            dob="3 October 1991", day_master="Byeong (Yang Fire)", tier="deep")
    assert "knowledge/" not in html, "citation paths must be stripped from client HTML"
    assert "Sources & Limits" not in html, "Sources section must be stripped from client HTML"
