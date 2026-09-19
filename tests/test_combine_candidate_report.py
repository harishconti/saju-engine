"""Tests for `src/saju_html/combine_candidate_report.py`.

The combiner strips sources, moves Closing Note to the end, and (optionally)
dedupes the base Career Archetypes table. These tests lock in the
"FAQ block + Closing Note ordering" invariant needed by the blueprint-aligned
Deep Destiny reports: when the base contains `## How to Use This Report`
before `## Closing Note`, the FAQ must remain in the body and only the
Closing Note must move to the end.
"""
from __future__ import annotations

from pathlib import Path

from saju_html.combine_candidate_report import (  # noqa: E402
    _extract_closing_note,
    combine_report,
)


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_extract_closing_note_picks_closing_not_faq(tmp_path: Path) -> None:
    text = (
        "# Title\n\n"
        "## How to Use This Report\n\n"
        "FAQ content.\n\n"
        "## Closing Note\n\n"
        "Closing paragraph.\n"
    )
    base, closing = _extract_closing_note(text)
    assert "## How to Use This Report" in base
    assert "FAQ content" in base
    assert closing.lstrip().startswith("## Closing Note")
    assert "Closing paragraph" in closing


def test_combined_report_glossary_follows_moved_closing_note(tmp_path: Path) -> None:
    """'## What the Terms Mean' must survive combine and stay after the Closing Note."""
    name = "glossary-tester"
    candidate_dir = tmp_path / "candidates_horoscope" / "reports" / name
    _write(
        candidate_dir / f"{name}-report.md",
        (
            "# X\n\n## Chart at a Glance\n\nstuff\n\n"
            "## Closing Note\n\nfinal words\n\n"
            "## What the Terms Mean\n\n- **Major Luck (大運):** ten-year chapters\n"
        ),
    )
    _write(candidate_dir / "career.md", "## Career\n\nTopic body.\n")

    import saju_html.combine_candidate_report as ccr
    original_dir = ccr.REPORTS_DIR
    ccr.REPORTS_DIR = tmp_path / "candidates_horoscope" / "reports"
    try:
        out = combine_report(name)
    finally:
        ccr.REPORTS_DIR = original_dir

    combined = out.read_text(encoding="utf-8")
    assert combined.index("## What the Terms Mean") > combined.index("## Closing Note")
    assert combined.count("## What the Terms Mean") == 1
    assert combined.rstrip().endswith("ten-year chapters")


def test_combine_report_faq_stays_before_closing(tmp_path: Path) -> None:
    """The How to Use block must remain in the body; only Closing Note moves to the end."""
    name = "vishnu-priya"
    candidate_dir = tmp_path / "candidates_horoscope" / "reports" / name
    _write(
        candidate_dir / f"{name}-report.md",
        (
            "# Title\n\n"
            "## Chart at a Glance\n\n"
            "Body content.\n\n"
            "## How to Use This Report\n\n"
            "FAQ block — stays in the body.\n\n"
            "## Closing Note\n\n"
            "Moved to end.\n"
        ),
    )

    # Run combine_report against our temp dir by monkey-patching the reports dir.
    import saju_html.combine_candidate_report as ccr
    original_dir = ccr.REPORTS_DIR
    ccr.REPORTS_DIR = tmp_path / "candidates_horoscope" / "reports"
    try:
        out = combine_report(name)
    finally:
        ccr.REPORTS_DIR = original_dir

    combined = out.read_text(encoding="utf-8")
    # FAQ stays before Closing Note.
    faq_pos = combined.index("## How to Use This Report")
    closing_pos = combined.index("## Closing Note")
    assert faq_pos < closing_pos, "FAQ must come before the Closing Note"
    # And there is exactly one Closing Note heading (the moved one).
    assert combined.count("## Closing Note") == 1


def test_combine_report_default_excludes_engine_tier_files(tmp_path: Path) -> None:
    """Default topic selection must not pull in *-sample/essential/deep/engine*.md files."""
    name = "vishnu-priya"
    candidate_dir = tmp_path / "candidates_horoscope" / "reports" / name
    base = (
        "# Title\n\n"
        "## Chart at a Glance\n\n"
        "Body content.\n\n"
        "## Closing Note\n\n"
        "Closing paragraph.\n"
    )
    _write(candidate_dir / f"{name}-report.md", base)
    _write(candidate_dir / "career.md", "## Career\n\nCareer deep-dive.\n")
    _write(candidate_dir / "relationships.md", "## Relationships\n\nRelationship deep-dive.\n")
    # Engine-generated tier files that should be excluded by default.
    _write(candidate_dir / f"{name}-sample.md", "## Sample\n\nDuplicate.\n")
    _write(candidate_dir / f"{name}-essential.md", "## Essential\n\nDuplicate.\n")
    _write(candidate_dir / f"{name}-deep.md", "## Deep\n\nDuplicate.\n")
    _write(candidate_dir / f"{name}-engine-draft.md", "## Engine\n\nDuplicate.\n")

    import saju_html.combine_candidate_report as ccr
    original_dir = ccr.REPORTS_DIR
    ccr.REPORTS_DIR = tmp_path / "candidates_horoscope" / "reports"
    try:
        out = combine_report(name)
    finally:
        ccr.REPORTS_DIR = original_dir

    combined = out.read_text(encoding="utf-8")
    assert "## Career" in combined
    assert "## Relationships" in combined
    assert "## Sample" not in combined
    assert "## Essential" not in combined
    assert "## Deep" not in combined
    assert "## Engine" not in combined


def test_combine_report_explicit_topics_can_include_tier_files(tmp_path: Path) -> None:
    """Explicit --topics should still be able to include a tier file if requested."""
    name = "vishnu-priya"
    candidate_dir = tmp_path / "candidates_horoscope" / "reports" / name
    base = "# Title\n\n## Closing Note\n\nClosing.\n"
    _write(candidate_dir / f"{name}-report.md", base)
    _write(candidate_dir / f"{name}-deep.md", "## Deep\n\nDeep tier content.\n")

    import saju_html.combine_candidate_report as ccr
    original_dir = ccr.REPORTS_DIR
    ccr.REPORTS_DIR = tmp_path / "candidates_horoscope" / "reports"
    try:
        out = combine_report(name, topic_files=[f"{name}-deep.md"])
    finally:
        ccr.REPORTS_DIR = original_dir

    combined = out.read_text(encoding="utf-8")
    assert "## Deep" in combined


def test_combine_report_strips_duplicate_sources_and_closing_notes(tmp_path: Path) -> None:
    """Base Sources and follow-up Closing Notes must not duplicate the base Closing Note."""
    name = "vishnu-priya"
    candidate_dir = tmp_path / "candidates_horoscope" / "reports" / name
    base = (
        "# Title\n\n"
        "## Chart at a Glance\n\n"
        "Body content.\n\n"
        "## Closing Note\n\n"
        "Base closing.\n\n"
        "## Sources & Limits\n\n"
        "Sources from base.\n"
    )
    _write(candidate_dir / f"{name}-report.md", base)
    _write(
        candidate_dir / "relationships.md",
        (
            "## Relationships\n\n"
            "Relationship deep-dive.\n\n"
            "## Closing Note\n\n"
            "Follow-up closing.\n\n"
            "## Sources & Limits\n\n"
            "Follow-up sources.\n"
        ),
    )

    import saju_html.combine_candidate_report as ccr
    original_dir = ccr.REPORTS_DIR
    ccr.REPORTS_DIR = tmp_path / "candidates_horoscope" / "reports"
    try:
        out = combine_report(name)
    finally:
        ccr.REPORTS_DIR = original_dir

    combined = out.read_text(encoding="utf-8")
    assert combined.count("## Closing Note") == 1
    assert "Base closing." in combined
    assert "Follow-up closing." not in combined
    assert "## Sources" not in combined
