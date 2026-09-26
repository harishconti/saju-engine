"""Tests for the HTML/Playwright PDF generator."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}


@lru_cache(maxsize=1)
def _browser_available() -> bool:
    """Return True if a Chromium-compatible browser can be launched.

    The PDF-rendering tests need a real browser (bundled Playwright Chromium
    or a system Chrome). Skip them instead of failing when neither is
    installed (e.g. a minimal CI runner that only runs the reportlab backend).
    """
    try:
        from saju_html.renderer import _launch_browser
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as p:
            browser = _launch_browser(p)
            browser.close()
        return True
    except Exception:
        return False


requires_browser = pytest.mark.skipif(
    not _browser_available(),
    reason="no Chromium/Chrome browser available for Playwright PDF tests",
)


def test_html_pdf_imports():
    """Smoke: renderer module imports and Jinja-less default template works."""
    from saju_html.renderer import markdown_to_html

    html = markdown_to_html("# Test\n\nHello 甲 world.")
    assert "<html" in html
    # Korean/Hanja translation should have run
    assert "甲" not in html
    assert "Gap" in html or "Test" in html


def test_reportlab_inline_handles_underscore_italic_without_leaking_underscores():
    from saju_html.md_to_saju_pdf import md_inline_to_html

    out = md_inline_to_html("_For business-critical decisions, consult a qualified reader._")
    assert out == "<i>For business-critical decisions, consult a qualified reader.</i>"
    # snake_case identifiers must never be italicised
    assert md_inline_to_html("the day_branch_middle stem") == "the day_branch_middle stem"


def test_build_pdf_falls_back_to_reportlab_when_playwright_unavailable(tmp_path, monkeypatch):
    """If the HTML/Playwright backend cannot print, build_pdf routes to ReportLab."""
    import warnings
    from saju_html.renderer import build_pdf

    def _fake_html_to_pdf(*args, **kwargs):
        raise RuntimeError("no browser available")

    monkeypatch.setattr("saju_html.renderer.html_to_pdf", _fake_html_to_pdf)

    md = tmp_path / "test.md"
    pdf = tmp_path / "test.pdf"
    md.write_text(
        "# Sample Report\n\n| Pillar | Stem | Branch |\n|---|---|---|\n| Year | 甲 | 子 |\n\n- Point one\n- Point two\n",
        encoding="utf-8",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        out = build_pdf(
            md,
            pdf,
            title="Sample Report",
            client="Candidate",
            dob="1 January 2000",
            day_master="Gap (Yang Wood)",
            tier="essential",
        )
    assert out == pdf
    assert pdf.stat().st_size > 1024
    assert any("falling back to ReportLab" in str(w.message) for w in caught), (
        f"expected fallback warning, got: {[str(w.message) for w in caught]}"
    )


def test_drop_title_block_stops_at_first_section():
    """_drop_title_block must not swallow body content when a later <hr> exists."""
    from saju_html.renderer import _drop_title_block

    html = (
        "<h1>Cover Title</h1>"
        "<p>Subtitle</p>"
        "<hr>"
        "<h2>Chart</h2>"
        "<p>Body text</p>"
        "<hr>"
        "<h2>Sources & Limits</h2>"
    )
    result = _drop_title_block(html)
    assert "<h1>Cover Title</h1>" not in result
    assert "Subtitle" not in result
    assert "<h2>Chart</h2>" in result
    assert "Body text" in result
    assert "<h2>Sources & Limits</h2>" in result


def test_drop_title_block_falls_back_to_h1_only_when_no_hr():
    """If no pre-section <hr> exists, only the first <h1> is dropped."""
    from saju_html.renderer import _drop_title_block

    html = "<h1>Title</h1><h2>Section</h2><p>Body</p>"
    result = _drop_title_block(html)
    assert "<h1>Title</h1>" not in result
    assert "<h2>Section</h2>" in result
    assert "Body" in result


@requires_browser
def test_html_pdf_from_markdown(tmp_path):
    """End-to-end: markdown file -> HTML renderer -> PDF on disk."""
    from saju_html.renderer import build_pdf

    md = tmp_path / "test.md"
    pdf = tmp_path / "test.pdf"
    md.write_text(
        "# Sample Report\n\n| Pillar | Stem | Branch |\n|---|---|---|\n| Year | 甲 | 子 |\n\n- Point one\n- Point two\n",
        encoding="utf-8",
    )
    out = build_pdf(
        md,
        pdf,
        title="Sample Report",
        client="Candidate",
        dob="1 January 2000",
        day_master="Gap (Yang Wood)",
    )
    assert out == pdf
    assert pdf.stat().st_size > 1024


@requires_browser
def test_html_pdf_compact_mode(tmp_path):
    """Compact mode produces a one-page style hook without a separate cover page."""
    from saju_html.renderer import build_pdf, markdown_to_html

    md = tmp_path / "hook.md"
    md.write_text(
        "# The Hook\n\n## Your Chart Snapshot\n\n- **Day Master:** Xin (Yin Metal)\n- **Favorable Element:** Water\n\n---\n\n## Upgrade",
        encoding="utf-8",
    )
    html = markdown_to_html(
        md.read_text(encoding="utf-8"),
        title="The Hook",
        client="Candidate",
        dob="1 January 2000",
        day_master="Xin (Yin Metal)",
        compact=True,
    )
    assert "compact-cover" in html
    # Compact mode should not use the full-page cover div
    assert '<div class="cover">' not in html

    pdf = tmp_path / "hook.pdf"
    out = build_pdf(
        md,
        pdf,
        title="The Hook",
        client="Candidate",
        dob="1 January 2000",
        day_master="Xin (Yin Metal)",
        compact=True,
    )
    assert out == pdf
    assert pdf.stat().st_size > 1024


@requires_browser
def test_html_pdf_cli_smoke(tmp_path):
    """CLI wrapper exits 0 and writes a PDF."""
    import subprocess

    name = "sruthi"
    input_md = PROJECT_ROOT / "candidates_horoscope" / "reports" / name / f"{name}-report.md"
    # N-22 (2026-09-26 audit): write to a scratch path, not the tracked
    # client deliverable in candidates_horoscope/reports/sruthi/.
    output_pdf = tmp_path / f"{name}-html.pdf"
    if not input_md.exists():
        pytest.skip("Sruthi report markdown not present")

    result = subprocess.run(
        [
            "python3",
            str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_html_pdf.py"),
            "--input",
            str(input_md),
            "--output",
            str(output_pdf),
            "--title",
            "Sruthi — Saju Reading",
            "--client",
            "Sruthi",
            "--dob",
            "11 December 1993",
            "--day-master",
            "Bing (Yang Fire)",
        ],
        env=ENV,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output_pdf.stat().st_size > 1024
    assert "html-playwright mode" in result.stdout


@requires_browser
def test_html_pdf_wrapper_flag(tmp_path):
    """build-pdf.sh --html routes to the HTML backend."""
    import subprocess

    name = "sruthi"
    # N-22 (2026-09-26 audit): SAJU_OUT_DIR redirects the build away from the
    # tracked client deliverable in candidates_horoscope/reports/sruthi/.
    output_pdf = tmp_path / f"{name}-report.pdf"
    input_md = PROJECT_ROOT / "candidates_horoscope" / "reports" / name / f"{name}-report.md"
    if not input_md.exists():
        pytest.skip("Sruthi report markdown not present")

    result = subprocess.run(
        [str(PROJECT_ROOT / "tools" / "build-pdf.sh"), "--html", name],
        env={**ENV, "SAJU_OUT_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 1024
    assert "html-playwright mode" in result.stdout


def test_html_pdf_strips_source_citations_and_colors_elements():
    """HTML renderer strips internal citations and adds element color classes."""
    from saju_html.renderer import markdown_to_html

    md = (
        "# Test\n\n"
        "Yin Metal is the image of the polished jewel. "
        "*(see knowledge/01-stems.md)*.\n\n"
        "| Element | Presence | Percentage |\n"
        "|---|---|---|\n"
        "| 🔴 Fire | ████░░░░░░░░░░░░░░░░ | 20% |\n"
        "| 🟢 Wood | ████░░░░░░░░░░░░░░░░ | 20% |\n"
    )
    html = markdown_to_html(md, title="Test", client="Candidate")
    assert "see knowledge" not in html
    assert "knowledge/01-stems.md" not in html
    assert '<span class="element-fire">🔴 Fire</span>' in html
    assert '<span class="element-wood">🟢 Wood</span>' in html


def test_html_pdf_strips_chart_derived_review_notes():
    """The `*Chart-derived first draft — verify against knowledge/...*` review notes
    used in the premium report engine must be stripped entirely, not just the
    knowledge/ paths inside them."""
    from saju_html.renderer import markdown_to_html

    md = (
        "# Test\n\n"
        ">*Chart-derived first draft — verify against `knowledge/05-ten-gods.md` "
        "and `knowledge/03-five-elements.md`.*\n\n"
        ">*Chart-derived per-pillar walk — refine each entry by reading the relevant "
        "`knowledge/01-stems.md` and `knowledge/02-branches.md`.*\n\n"
        "Body prose that mentions knowledge/01-stems.md in plain text should also be stripped.\n"
    )
    html = markdown_to_html(md, title="Test", client="Candidate")
    assert "knowledge/" not in html, (
        f"knowledge/ path leaked into HTML output: {html!r}"
    )
    # The whole review-note line must disappear, not leave dangling words.
    assert "Chart-derived first draft" not in html
    assert "Chart-derived per-pillar walk" not in html
    assert "verify against" not in html
    assert "refine each entry" not in html


def test_html_pdf_sources_section_stops_at_next_heading():
    """A Sources section followed by another heading must not swallow the rest."""
    from saju_html.renderer import markdown_to_html

    md = (
        "# Test\n\n"
        "Some content.\n\n"
        "## Sources\n\n"
        "*(see knowledge/05-ten-gods.md)*\n\n"
        "## Focus Requested\n\n"
        "This follow-up section must be preserved.\n"
    )
    html = markdown_to_html(md, title="Test", client="Candidate")
    assert "knowledge/" not in html
    assert "Focus Requested" in html
    assert "This follow-up section must be preserved." in html


def test_html_pdf_premium_report_has_no_knowledge_paths():
    """End-to-end: full premium engine markdown → HTML must contain zero knowledge/ refs."""
    from saju_html.renderer import markdown_to_html
    from saju_engine.engine import compute_chart
    from saju_engine.premium_report import generate_premium_report

    chart = compute_chart(
        name="VP", gender="F", year=2001, month=6, day=7, hour=16, minute=45,
        longitude=80.27, utc_offset=5.5, use_solar_time=True, convention="korean",
    )
    for tier in ("sample", "essential", "deep"):
        md = generate_premium_report(chart, tier=tier)
        html = markdown_to_html(md, title="VP", client="VP", tier=tier)
        assert "knowledge/" not in html, (
            f"{tier} tier HTML still leaks knowledge/ path: {html[:200]!r}"
        )


# ── Blueprint-alignment tests (CosmicSaju Three-Tier Architecture) ────────


def test_html_pdf_tier_body_class():
    """`tier` kwarg sets body_class so CSS can target tier-specific styling."""
    from saju_html.renderer import markdown_to_html

    md = "# Test\n\nHello."
    for tier in ("sample", "essential", "deep"):
        html = markdown_to_html(md, title="Test", client="C", tier=tier)
        assert f'<body class="tier-{tier}">' in html, f"missing tier-{tier} body class"


def test_html_pdf_tier_default_no_body_class():
    """When no tier is supplied, body class should be empty (or compact-mode only)."""
    from saju_html.renderer import markdown_to_html
    import re

    html = markdown_to_html("# Test\n\nHello.", title="Test", client="C")
    m = re.search(r'<body\s+class="([^"]*)"', html)
    body_class = m.group(1) if m else ""
    # No `tier-*` class should appear on <body>.
    assert "tier-" not in body_class


def test_html_pdf_decade_roadmap_svg_renders():
    """Engine markers around the roadmap table get replaced by an SVG."""
    from saju_html.renderer import _wrap_decade_roadmap

    html = (
        "<h2>Lifetime Decade Roadmap</h2>\n"
        "<!-- decade-roadmap:start -->\n"
        "<table>"
        "<thead><tr><th>Age</th><th>Pillar</th><th>Element Theme</th><th>Favorable Lean</th></tr></thead>"
        "<tbody>"
        "<tr><td>3-12</td><td>壬寅</td><td>Yang Water</td><td>Favorable</td></tr>"
        "<tr><td>13-22</td><td>癸卯</td><td>Yin Water</td><td>Favorable</td></tr>"
        "<tr><td>23-32</td><td>甲辰</td><td>Yang Wood</td><td>Neutral</td></tr>"
        "<tr><td>33-42</td><td>乙巳</td><td>Yin Wood</td><td>Challenging</td></tr>"
        "</tbody></table>\n"
        "<!-- decade-roadmap:end -->\n"
    )
    out = _wrap_decade_roadmap(html)
    assert '<div class="decade-roadmap no-break">' in out
    assert "<svg" in out
    # Original table is gone, replaced by SVG.
    assert "<table" not in out
    # Favorable/neutral/challenging colours are used.
    assert "#27ae60" in out  # favorable green
    assert "#f39c12" in out  # neutral amber
    assert "#c0392b" in out  # challenging red


def test_html_pdf_decade_roadmap_no_markers_unchanged():
    """If markers are absent, the HTML is left untouched."""
    from saju_html.renderer import _wrap_decade_roadmap

    html = "<table><tr><td>no markers</td></tr></table>"
    assert _wrap_decade_roadmap(html) == html


def test_html_pdf_chart_signature_gets_class():
    """First <blockquote> becomes a styled pull-quote."""
    from saju_html.renderer import _wrap_chart_signature

    html = "<blockquote><p>Polished blade, autumn wind.</p></blockquote>"
    out = _wrap_chart_signature(html)
    assert '<blockquote class="chart-signature">' in out


def test_html_pdf_audio_included_wrapper():
    """The '🎧 Your MP3 audio summary is included' paragraph is wrapped."""
    from saju_html.renderer import _wrap_audio_included

    html = "<p>🎧 <strong>Your MP3 audio summary is included — delivered with this report.</strong></p>"
    out = _wrap_audio_included(html)
    assert '<div class="audio-included">' in out
    assert "🎧 Your MP3 audio summary is included" in out


def test_html_pdf_partner_upsell_wrapper():
    """The Partner Chart Add-On paragraph is wrapped in an accent box."""
    from saju_html.renderer import _wrap_partner_upsell

    html = (
        "<h4>Partner Chart Add-On</h4>\n"
        "<p><em>Want a side-by-side compatibility reading? Add a Partner Chart.</em></p>"
    )
    out = _wrap_partner_upsell(html)
    assert '<div class="partner-compat-upsell">' in out
    assert "Want a side-by-side compatibility reading" in out


def test_html_pdf_render_passes_through_all_wrappers(tmp_path):
    """End-to-end: full markdown → HTML via markdown_to_html, Deep tier, with
    a roadmap table + audio line + partner-upsell block."""
    from saju_html.renderer import markdown_to_html

    md = (
        "# Deep Destiny Report\n\n"
        "## Lifetime Decade Roadmap\n\n"
        "<!-- decade-roadmap:start -->\n"
        "| Age | Pillar | Element Theme | Favorable Lean |\n"
        "|---|---|---|---|\n"
        "| 3-12 | 壬寅 | Yang Water | Favorable |\n"
        "| 13-22 | 癸卯 | Yin Water | Favorable |\n"
        "| 23-32 | 甲辰 | Yang Wood | Neutral |\n"
        "<!-- decade-roadmap:end -->\n\n"
        "<blockquote>Polished blade in autumn wind.</blockquote>\n\n"
        "🎧 **Your MP3 audio summary is included — delivered with this report.**\n\n"
        "#### Partner Chart Add-On\n\n"
        "*Want a side-by-side compatibility reading? Add a Partner Chart.*\n"
    )
    html = markdown_to_html(md, title="Deep", client="Vishnu Priya", tier="deep")
    assert '<body class="tier-deep">' in html
    assert '<div class="decade-roadmap no-break">' in html
    assert '<blockquote class="chart-signature">' in html
    assert '<div class="audio-included">' in html
    assert '<div class="partner-compat-upsell">' in html


# ── Engine-draft marker stripping (client output must never show the marker) ──


def test_strip_keeps_plain_words_callout_and_glossary():
    from saju_html import strip_source_citations, strip_engine_drafts

    md = (
        "> **In plain words:** steady earning suits you *(see knowledge/13-wealth-and-business.md)*.\n\n"
        "## What the Terms Mean\n\n"
        "- **Direct Wealth (正財):** steady, earned income *(see knowledge/05-ten-gods.md)*\n"
    )
    out = strip_engine_drafts(strip_source_citations(md))
    assert "> **In plain words:** steady earning suits you." in out
    assert "## What the Terms Mean" in out
    assert "Direct Wealth" in out
    assert "see knowledge/" not in out


def test_strip_engine_drafts_drops_inline_marker():
    """Inline [ENGINE DRAFT — REVIEW REQUIRED] markers are removed from the prose."""
    from saju_html import strip_engine_drafts

    text = (
        "Hello world.\n\n"
        "[ENGINE DRAFT — REVIEW REQUIRED] This paragraph needs review.\n\n"
        "Closing line.\n"
    )
    out = strip_engine_drafts(text)
    assert "ENGINE DRAFT" not in out
    assert "This paragraph needs review." in out
    assert "Hello world." in out
    assert "Closing line." in out


def test_strip_engine_drafts_drops_blockquote_marker_line():
    """A blockquote line containing only the marker is removed entirely."""
    from saju_html import strip_engine_drafts

    text = (
        "## Day Master Portrait\n\n"
        "> [ENGINE DRAFT — REVIEW REQUIRED]\n"
        "> Some legitimate prose that should survive.\n\n"
        "Next paragraph.\n"
    )
    out = strip_engine_drafts(text)
    assert "ENGINE DRAFT" not in out
    assert "Some legitimate prose that should survive." in out
    assert "Next paragraph." in out


def test_html_pdf_marks_engine_draft_absent():
    """Full markdown_to_html pipeline drops all [ENGINE DRAFT — REVIEW REQUIRED] markers."""
    from saju_html.renderer import markdown_to_html

    md = (
        "# Deep\n\n"
        "[ENGINE DRAFT — REVIEW REQUIRED] Refine before delivery.\n\n"
        "> [ENGINE DRAFT — REVIEW REQUIRED]\n"
        "> Verify against knowledge/03-five-elements.md.\n"
    )
    html = markdown_to_html(md, title="Deep", client="VP", tier="deep")
    assert "ENGINE DRAFT" not in html
    assert "Refine before delivery." in html
    # The knowledge/ path is stripped; the surrounding prose survives (sans path).
    assert "knowledge/" not in html


def test_html_pdf_premium_report_output_has_no_engine_draft(tmp_path):
    """End-to-end: premium engine output → HTML drops every [ENGINE DRAFT] marker.

    As of the chart-derived prose fillers, the engine markdown itself no longer
    contains `[ENGINE DRAFT — REVIEW REQUIRED]` placeholders for the populated
    sections — every site is filled with chart-grounded prose. The HTML render
    still passes through `strip_engine_drafts()` as a defensive guard for any
    residual markers.
    """
    from saju_html.renderer import markdown_to_html
    from saju_engine.engine import compute_chart
    from saju_engine.premium_report import generate_premium_report

    chart = compute_chart(
        name="VP", gender="F", year=2001, month=6, day=7, hour=16, minute=45,
        longitude=80.27, utc_offset=5.5, use_solar_time=True, convention="korean",
    )
    for tier in ("sample", "essential", "deep"):
        md = generate_premium_report(chart, tier=tier)
        # Engine markdown no longer contains prompt-shaped placeholders.
        assert "ENGINE DRAFT" not in md, (
            f"engine markdown for {tier} still contains [ENGINE DRAFT] placeholders"
        )
        html = markdown_to_html(md, title="VP", client="VP", tier=tier)
        assert "ENGINE DRAFT" not in html, (
            f"{tier} tier HTML output still contains an [ENGINE DRAFT] marker"
        )


def test_combine_candidate_report_strips_engine_drafts(tmp_path, monkeypatch):
    """The combiner drops [ENGINE DRAFT] markers from the combined file."""
    import importlib
    from pathlib import Path

    # Build a fake candidate folder with a base + 1 topic carrying the marker.
    candidate = tmp_path / "vishnu-priya"
    candidate.mkdir()
    (candidate / "vishnu-priya-report.md").write_text(
        "# Base\n\n[ENGINE DRAFT — REVIEW REQUIRED] First draft.\n\n## Closing Note\n\nGoodbye.\n",
        encoding="utf-8",
    )
    (candidate / "career.md").write_text(
        "## Career\n\n> [ENGINE DRAFT — REVIEW REQUIRED]\n> Refine against knowledge/05.\n",
        encoding="utf-8",
    )

    # Patch REPORTS_DIR so combine_candidate_report operates on tmp_path.
    mod = importlib.import_module("saju_html.combine_candidate_report")
    monkeypatch.setattr(mod, "REPORTS_DIR", tmp_path)

    out = mod.combine_report("vishnu-priya")
    combined = Path(out).read_text(encoding="utf-8")
    assert "ENGINE DRAFT" not in combined
    assert "Refine against knowledge/05." in combined
    assert "Goodbye." in combined
