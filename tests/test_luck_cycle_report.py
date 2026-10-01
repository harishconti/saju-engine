"""Regression tests for the luck-cycle / lifetime-roadmap report.

The report is a client deliverable, so these pin its *structural* invariants
(counts, non-overlapping classifications, marker integrity, groundedness)
rather than exact prose, which is allowed to evolve.
"""
from __future__ import annotations

import re

from saju_engine.engine import compute_chart
from saju_engine.luck_cycle_report import year_status
from saju_html.renderer import markdown_to_html


def _harish():
    return compute_chart(
        name="Harish", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
        reference_year=2026, reference_month=9, reference_day=26,
    )


def _report():
    from saju_engine.luck_cycle_report import generate_luck_cycle_report
    return generate_luck_cycle_report(_harish())


def test_report_has_16_blocks_and_all_sections():
    md = _report()
    headings = re.findall(r"^### \d+\. ", md, flags=re.MULTILINE)
    assert len(headings) == 16, f"expected 8 decades × 2 halves = 16 blocks, got {len(headings)}"
    for section in ("## Chart at a Glance", "## Lifetime Timeline",
                    "## Favorable-Cycle Chart", "## Ten-God Class Rhythm",
                    "## Element Rhythm", "## The Five-Year Blocks",
                    "## Sources & Limits"):
        assert section in md, f"missing section: {section}"


def test_every_block_has_wealth_business_family_investment():
    md = _report()
    assert md.count("- **Wealth:**") == 16
    assert md.count("- **Business:**") == 16
    assert md.count("- **Family:**") == 16
    assert md.count("- **Investment pattern:**") == 16


def test_years_are_non_overlapping_and_cover_the_lifetime():
    md = _report()
    blocks = re.findall(r"^### \d+\. (\d{4})–(\d{4})", md, flags=re.MULTILINE)
    assert len(blocks) == 16
    spans = [(int(a), int(b)) for a, b in blocks]
    for (a, b), (c, d) in zip(spans, spans[1:]):
        assert c == b + 1, f"blocks must be contiguous 5-year spans; {a}-{b} then {c}-{d}"
        assert b - a == 4, f"each block must span exactly 5 years; got {a}-{b}"


def test_year_status_is_exclusive_so_counts_sum_to_five():
    """favorable + unfavorable + neutral must equal 5 (never double-counted)."""
    assert year_status("Water", "Fire", "Water", "Metal", "Fire") == "neutral"
    assert year_status("Water", "Earth", "Water", "Metal", "Fire") == "favorable"
    assert year_status("Fire", "Fire", "Water", "Metal", "Fire") == "unfavorable"
    assert year_status("Wood", "Earth", "Water", "Metal", "Fire") == "neutral"

    md = _report()
    rows = re.findall(r"^\| (\d{4}–\d{4}) \| (\d+) \| (\d+) \| (\d+) \|$", md, flags=re.MULTILINE)
    assert len(rows) == 16, f"favorable table should have 16 rows, got {len(rows)}"
    for _span, fav, neutral, unfav in rows:
        assert int(fav) + int(neutral) + int(unfav) == 5


def test_report_is_deterministic():
    assert _report() == _report()


def test_markers_are_balanced_and_only_known_ones():
    md = _report()
    starts = re.findall(r"<!-- (\w[-\w]*):start -->", md)
    ends = re.findall(r"<!-- (\w[-\w]*):end -->", md)
    assert sorted(starts) == sorted(ends)
    assert set(starts) <= {"luck-timeline", "luck-favorable", "luck-classes"}


def test_grounded_in_knowledge():
    md = _report()
    for cite in ("knowledge/08-luck-pillars.md",
                 "knowledge/13-wealth-and-business.md",
                 "knowledge/12-career-and-vocation.md"):
        assert cite in md, f"report must cite {cite}"
    assert "## Sources & Limits" in md


def test_html_renders_the_three_svgs_and_leaks_no_markers():
    md = _report()
    html = markdown_to_html(
        md, title="Harish — Luck Cycle", client="Harish",
        dob="4 June 1992", day_master="Sin (Yin Metal)", tier="deep",
    )
    assert 'class="luck-timeline' in html
    assert 'class="luck-bars' in html
    assert 'class="luck-classes' in html
    # The marker comments must not survive into the rendered HTML.
    assert "luck-timeline:start" not in html
    assert "luck-favorable:start" not in html
    assert "luck-classes:start" not in html


def test_current_block_is_flagged():
    md = _report()
    assert "you are here" in md
    # On the 2026 reference date the current five-year block is 2023–2027.
    m = re.search(r"^### \d+\. (2023–2027).*\*\*current\*\*", md, flags=re.MULTILINE)
    assert m, "the 2023–2027 block must be marked current on the 2026 reference date"


def test_requires_gender_via_cli():
    """The luck-cycle format drives 대운, so the CLI must require --gender."""
    import io

    from saju_engine.cli import main
    err = io.StringIO()
    out = io.StringIO()
    rc = main([
        "--date", "1992-06-04", "--time", "03:10",
        "--longitude", "79.4408", "--utc-offset", "5.5",
        "--format", "luck-cycle",
    ], stdout=out, stderr=err)
    assert rc == 2
    assert "gender" in err.getvalue().lower()
