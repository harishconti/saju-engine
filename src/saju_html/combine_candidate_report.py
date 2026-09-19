#!/usr/bin/env python3
"""Combine a base Saju report with topic follow-ups into one client-facing document.

Rules:
  - The base report's "## Closing Note" section is extracted and moved to the very end.
  - If a "career" follow-up exists, the base report's "### Career Archetypes" table is
    replaced with a short transition so the deep-dive becomes the canonical career table.
  - Internal "## Sources" sections are stripped from follow-ups before inclusion.
  - The output is a single markdown file ready for PDF conversion.

Usage:
    python3 src/saju_html/combine_candidate_report.py vishnu-priya
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# src/saju_html/combine_candidate_report.py -> repo root is three parents up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "candidates_horoscope" / "reports"


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_file(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _strip_sources_section(text: str) -> str:
    """Remove standalone ## Sources / ## Sources & Limits sections.

    Stops at the next Markdown heading of the same or higher rank so that
    content after a Sources heading is preserved.
    """
    match = re.search(r"\n(#+)\s+Sources\b", text, flags=re.IGNORECASE)
    if not match:
        return text
    start = match.start()
    rank = len(match.group(1))
    # Find the next heading with rank <= the Sources heading rank.
    next_heading = re.search(r"\n#{1," + str(rank) + r"}\s+\S", text[match.end():])
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(text)
    return text[:start].rstrip() + text[end:]


def _strip_closing_note(text: str) -> str:
    """Remove a standalone ## Closing Note section.

    Everything from the heading to EOF, or to a following
    ``## What the Terms Mean`` (the plain-language glossary), which must survive
    and stay last.
    """
    match = re.search(
        r"\n##\s+Closing Note\b[\s\S]*?(?=\n##\s+What the Terms Mean|\Z)",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return text
    return (text[: match.start()].rstrip() + "\n" + text[match.end():]).rstrip() + "\n"


def _extract_terms_section(text: str) -> tuple[str, str]:
    """Return (text_without_terms, terms_section_md).

    The plain-language glossary starts at '## What the Terms Mean' and runs to
    EOF. If absent, returns (text, '').
    """
    match = re.search(r"\n##\s+What the Terms Mean\b.*", text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return text, ""
    terms = match.group(0).lstrip("\n")
    base = text[: match.start()].rstrip() + "\n"
    return base, terms


def _strip_terms_section(text: str) -> str:
    """Remove a '## What the Terms Mean' section (heading to EOF)."""
    return _extract_terms_section(text)[0]


_ENGINE_DRAFT_INLINE_RE = re.compile(r" ?\[ENGINE DRAFT — REVIEW REQUIRED\] ?")
_ENGINE_DRAFT_LINE_RE = re.compile(
    r"^\s*>\s*\[ENGINE DRAFT — REVIEW REQUIRED\]\s*$", re.MULTILINE
)


def _strip_engine_drafts(text: str) -> str:
    """Remove `[ENGINE DRAFT — REVIEW REQUIRED]` markers from combined output.

    The engine inserts these tags inline or as standalone blockquote lines so a
    reader can spot which prose still needs human review. The combiner must
    drop them so they never reach the client. Inline markers consume only
    adjacent single-space whitespace so paragraph structure is preserved.
    """
    out = _ENGINE_DRAFT_LINE_RE.sub("", text)
    out = _ENGINE_DRAFT_INLINE_RE.sub("", out)
    out = re.sub(r"  +", " ", out)
    out = re.sub(r"\n\n\n+", "\n\n", out)
    return out


def _extract_closing_note(text: str) -> tuple[str, str]:
    """Return (base_without_closing, closing_note_md).

    Closing Note starts at the first '## Closing Note' heading and goes to EOF.
    If no closing note is found, returns (text, '').
    """
    match = re.search(r"\n##\s+Closing Note\b.*", text, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return text, ""
    closing = match.group(0).lstrip("\n")
    base = text[: match.start()].rstrip() + "\n"
    return base, closing


def _has_career_deep_dive(topic_paths: list[Path]) -> bool:
    """Return True if any follow-up is a career deep-dive."""
    for p in topic_paths:
        name = p.stem.lower()
        if "career" in name:
            return True
    return False


def _dedupe_career_table(base_text: str) -> str:
    """Replace the base report's Career Archetypes table with a transition line.

    The base report contains a full career table under '### Career Archetypes'.
    When a dedicated career.md deep-dive is included later, we remove that table
    to avoid the "two career tables" duplication problem flagged in client audits.
    """
    # Match the "### Career Archetypes" heading and the markdown table that follows it.
    # A markdown table header is one row, the separator is one row of |---|---|...,
    # and the data rows continue until a non-table line or next heading.
    # The heading-to-table gap may be one or two newlines (markdown allows a
    # table to follow a heading on the next line), so use \s*\n (one+).
    pattern = re.compile(
        r"(###\s+Career Archetypes\s*\n)"
        r"(\|[^\n]+\|\s*\n)"
        r"(\|(?:[-:]+\|)+\s*\n)"
        r"((?:\|[^\n]+\|\s*\n)+)",
        re.IGNORECASE,
    )

    def _replace(match: re.Match) -> str:
        return (
            "### Career Archetypes\n\n"
            "*A detailed career analysis follows in the Career Deep-Dive section below.*\n\n"
        )

    return pattern.sub(_replace, base_text)


def combine_report(name: str, topic_files: list[str] | None = None) -> Path:
    """Combine the base report for `name` with the requested topic follow-ups.

    If `topic_files` is None, all .md files in the candidate folder except the base
    report and the combined file are included, in alphabetical order.
    """
    candidate_dir = REPORTS_DIR / name
    base_path = candidate_dir / f"{name}-report.md"
    output_path = candidate_dir / f"{name}-combined.md"

    if not base_path.exists():
        raise FileNotFoundError(f"Base report not found: {base_path}")

    base_text = _read_file(base_path)
    base_text = _strip_sources_section(base_text)
    # The plain-language glossary must end the document, after the moved Closing
    # Note — pull it out before the Closing Note extraction so it is not caught
    # by the "heading to EOF" match.
    base_text, terms_section = _extract_terms_section(base_text)
    base_text, closing_note = _extract_closing_note(base_text)
    closing_note = _strip_sources_section(closing_note)

    # Determine topic files to include
    if topic_files is None:
        excluded = {
            f"{name}-report.md",
            f"{name}-combined.md",
            f"{name}-skeleton.md",
        }
        # Exclude engine-generated tier files to avoid duplicate Closing Notes
        # and duplicated tiered content in the default combined output.
        excluded_tier_substrings = (
            "-engine",
            "-sample",
            "-essential",
            "-deep",
        )
        topic_paths = sorted(
            p
            for p in candidate_dir.glob("*.md")
            if p.name not in excluded
            and not any(sub in p.stem for sub in excluded_tier_substrings)
        )
    else:
        topic_paths = [candidate_dir / f for f in topic_files]

    if _has_career_deep_dive(topic_paths):
        base_text = _dedupe_career_table(base_text)

    parts = [base_text.rstrip()]
    for p in topic_paths:
        if not p.exists():
            print(f"Warning: topic file not found, skipping: {p}", file=sys.stderr)
            continue
        topic_text = _read_file(p)
        topic_text = _strip_sources_section(topic_text)
        topic_text = _strip_terms_section(topic_text)
        topic_text = _strip_closing_note(topic_text)
        parts.append(f"\n\n---\n\n{topic_text.strip()}")

    if closing_note:
        parts.append(f"\n\n---\n\n{closing_note.strip()}")

    if terms_section:
        parts.append(f"\n\n---\n\n{terms_section.strip()}")

    combined = "\n".join(parts)
    # Strip engine-draft markers so client-facing output never shows them.
    combined = _strip_engine_drafts(combined)
    # Normalize multiple blank lines
    combined = re.sub(r"\n{3,}", "\n\n", combined)
    _write_file(output_path, combined + "\n")
    return output_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Combine a base Saju report with topic follow-ups.")
    ap.add_argument("name", help="Candidate folder name (e.g. vishnu-priya).")
    ap.add_argument(
        "--topics",
        nargs="*",
        help="Specific topic .md files to include (default: all non-base .md files).",
    )
    args = ap.parse_args()

    out = combine_report(args.name, args.topics)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
