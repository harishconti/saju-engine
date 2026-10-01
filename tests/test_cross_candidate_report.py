"""Regression tests for the cross-candidate business analysis."""
from __future__ import annotations

import re

from saju_engine.cross_candidate_report import generate_cross_candidate_report
from saju_engine.engine import compute_chart
from saju_html.renderer import markdown_to_html

REF = dict(reference_year=2026, reference_month=9, reference_day=26)


def _members():
    return [
        {"name": "Harish", "override": None, "chart": compute_chart(
            name="Harish", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
            longitude=79.4408, utc_offset=5.5, **REF)},
        {"name": "Sruthi", "override": "Earth", "chart": compute_chart(
            name="Sruthi", gender="F", year=1993, month=12, day=11, hour=2, minute=45,
            longitude=79.45, utc_offset=5.5, **REF)},
        {"name": "Pawan", "override": "Water", "chart": compute_chart(
            name="Pawan", gender="M", year=1991, month=10, day=3, hour=23, minute=45,
            longitude=79.19, utc_offset=5.5, **REF)},
    ]


RELATIONSHIPS = [
    {"a": "Harish", "b": "Sruthi", "kind": "siblings"},
    {"a": "Pawan", "b": "Sruthi", "kind": "spouses"},
    {"a": "Harish", "b": "Pawan", "kind": "co-founders"},
]


def _report():
    return generate_cross_candidate_report(_members(), RELATIONSHIPS, reference_date="2026-09-26")


def test_all_sections_present():
    md = _report()
    for s in ("## 1. The Charts at a Glance", "## 2. Pairwise Partnership Compatibility",
              "## 3. Element & Role Coverage", "## 4. Domain Fit",
              "## 5. Venture Shapes", "## 6. Role Assignment",
              "## 7. Five-Year Luck-Cycle Effect", "## 8. What Is Missing",
              "## 9. Verdict", "## Sources & Limits"):
        assert s in md, f"missing: {s}"


def test_three_pairwise_blocks():
    md = _report()
    assert md.count("### 2.") == 3
    for pair in ("Harish × Sruthi", "Harish × Pawan", "Sruthi × Pawan"):
        assert pair in md


def test_relationships_named():
    md = _report()
    assert "siblings" in md
    assert "husband & wife" in md


def test_role_seats_are_distinct():
    """No two members may be handed the same recommended seat."""
    md = _report()
    block = md.split("## 6. Role Assignment", 1)[1].split("## 7.", 1)[0]
    seats = [line.split("|")[4].strip() for line in block.splitlines()
             if line.startswith("| ") and line.count("|") >= 6 and "Member" not in line]
    assert len(seats) == 3
    assert len(set(seats)) == 3, f"role seats must be distinct, got {seats}"


def test_luck_table_covers_all_members_and_flags_windows():
    md = _report()
    block = md.split("## 7. Five-Year Luck-Cycle Effect", 1)[1].split("## 8.", 1)[0]
    rows = re.findall(r"^\| (20\d\d) \| ([FMC—]) \| ([FMC—]) \| ([FMC—]) \| (.+?) \|$",
                      block, flags=re.MULTILINE)
    assert rows, "luck-cycle table must have year rows"
    for y, h, s, p, group in rows:
        assert group in ("**full alignment**", "workable", "partial", "stalled")
    # The engine found 2041-2042 fully aligned for this trio; the report must
    # surface at least one actionable window statement.
    assert "Recommended action windows" in block


def test_missing_function_stated_for_this_trio():
    """The trio has no Wood in any favorable set, so §8 must say Wood is absent."""
    md = _report()
    assert "Wood function absent" in md


def test_states_shared_money_risk():
    md = _report()
    assert "겁재奪財" in md
    assert "Companion" in md


def test_deterministic():
    assert _report() == _report()


def test_html_strips_citations_and_markers():
    html = markdown_to_html(_report(), title="Cross-Candidate", client="Trio",
                            dob="", day_master="Multiple", tier="deep")
    assert "knowledge/" not in html
    assert "Sources & Limits" not in html
    # The §7 luck table must survive as a table (no chart-marker leakage).
    assert "Five-Year Luck-Cycle Effect" in html
