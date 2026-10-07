"""C1 (2026-10-07): the renderer's document/cover templates are Jinja2.

The rendered output is byte-identical to the previous hand-built strings (the
tests/golden_html snapshots enforce that). These tests pin the templating
itself: that Jinja2 renders the shapes, and that cover inputs stay escaped.
"""
from __future__ import annotations

from saju_html.renderer import (
    _COVER_TEMPLATE,
    _COMPACT_COVER_TEMPLATE,
    _DOCUMENT_TEMPLATE,
    _build_compact_cover_html,
    _build_cover_html,
    _jinja_env,
    markdown_to_html,
)


def test_renderer_templates_are_jinja2():
    # The template source is present and renderable through the env.
    env = _jinja_env()
    assert env.from_string(_DOCUMENT_TEMPLATE).render(
        title="T", css="b", cover="C", body="B", body_class="x"
    ).startswith("<!DOCTYPE html>")
    assert "class=\"cover\"" in env.from_string(_COVER_TEMPLATE).render(
        title="T", subtitle="S", meta_block="", footnote="F",
        generation_date="D", report_id="")
    assert "class=\"compact-cover\"" in env.from_string(_COMPACT_COVER_TEMPLATE).render(
        title="T", subtitle="S", meta="M", report_line="", generation_date="D")


def test_cover_escapes_user_input():
    out = _build_cover_html(
        title="A & <b>",
        subtitle="S",
        meta_rows=[("For", "<script>alert(1)</script>")],
        footnote="F",
        generation_date="June 1, 2026",
        report_id="ID<1>",
    )
    assert "<script>" not in out and "<b>" not in out
    assert "&lt;script&gt;" in out
    assert "A &amp; &lt;b&gt;" in out


def test_compact_cover_escapes_user_input():
    out = _build_compact_cover_html(
        title="A & <b>", subtitle="S", meta_rows=[("For", "<i>")],
        generation_date="June 1, 2026", report_id="")
    assert "<b>" not in out and "<i>" not in out
    assert "A &amp; &lt;b&gt;" in out


def test_cover_meta_rows_render_each_p():
    out = _build_cover_html(
        "T", "S", [("For", "Alice"), ("Born", "1990")], "F", "D", "ID")
    assert out.count('<p class="meta">') == 2
    assert "<strong>For</strong>Alice" in out
    assert '<p class="report-id">Report ID: ID' in out


def test_cover_without_report_id_omits_report_line():
    out = _build_cover_html("T", "S", [], "F", "D", "")
    assert "report-id" not in out


def test_markdown_to_html_document_shape():
    out = markdown_to_html("# Test\n\nHello.", title="T", client="C")
    assert out.lstrip().startswith("<!DOCTYPE html>")
    assert "<title>T</title>" in out
    assert out.endswith("</html>\n")
