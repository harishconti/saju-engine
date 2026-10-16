"""Tests for the web report: the document a client reads on a phone.

`markdown_to_html(..., web=True)` produces the *web* artefact — the one served at the
report link and downloaded as a single file. `theme.css` is a print stylesheet (A4 page
boxes, repeated table headers), so the web layer exists to make the same document work on
a screen: readable measure, scrollable tables, working navigation.

The properties asserted here are the ones that make it shippable: it must be a single
self-contained file (it is served *and* downloaded, so nothing may depend on our origin),
it must not be indexable, its contents list must actually navigate, and the print
document and its snapshots must be untouched.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from saju_html.renderer import markdown_to_html  # noqa: E402

MD = """# Report Title

## Table of Contents

- Chart at a Glance
- Career & Wealth — incl. A Subsection
- A Section That Does Not Exist

---

## Chart at a Glance

| Pillar | Stem | Branch |
|---|---|---|
| Year | 甲 | 子 |
| Day | 辛 | 丑 |

Body text for the glance.

## Career & Wealth

More text.

### A Subsection

Deeper text.

## MP3 Audio Summary — Included by Default

Your audio summary follows this report by email.
"""


@pytest.fixture(scope="module")
def web() -> str:
    return markdown_to_html(MD, title="A Client — Deep Destiny Report", client="A Client",
                            dob="1 January 2000", day_master="Sin (Yin Metal)",
                            report_id="WEB-1", tier="deep", web=True)


@pytest.fixture(scope="module")
def print_doc() -> str:
    return markdown_to_html(MD, title="A Client — Deep Destiny Report", client="A Client",
                            dob="1 January 2000", day_master="Sin (Yin Metal)",
                            report_id="WEB-1", tier="deep")


# ── self-contained ────────────────────────────────────────────────────────────────

def test_web_document_is_self_contained(web):
    """Served from the report route *and* downloaded as one file, so nothing may point
    outside it — no scripts, no stylesheets, no webfonts, no images."""
    external = [u for u in re.findall(r'(?:src|href)="([^"#]+)"', web)
                if u.startswith(("http", "//"))]
    assert external == [], external
    assert "<script" not in web.lower()
    assert not re.search(r"<link\b", web, re.IGNORECASE)
    assert not re.search(r"url\(\s*['\"]?https?:", web, re.IGNORECASE)
    assert "@import" not in web
    assert "@font-face" not in web
    # …and the styling is present inline. (A chart SVG only appears when the report has
    # an element-balance table; the real-report test below checks that separately.)
    assert web.count("<style") == 1
    assert "theme" not in external


def test_web_document_is_mobile_ready_and_not_indexable(web):
    assert 'name="viewport"' in web and "width=device-width" in web
    assert "noindex" in web


# ── navigation ────────────────────────────────────────────────────────────────────

def test_headings_get_unique_ids_and_anchor_links(web):
    ids = re.findall(r'<h[23][^>]*\bid="([^"]+)"', web)
    assert ids, "no heading ids: the document cannot be linked to"
    assert len(ids) == len(set(ids)), "duplicate ids are invalid HTML and break links"
    assert all(re.fullmatch(r"[a-z0-9-]+", i) for i in ids), ids
    assert web.count('class="anchor"') == len(ids)


def test_contents_list_navigates_to_real_sections(web):
    nav = re.search(r'<nav class="toc"[^>]*>(.*?)</nav>', web, re.DOTALL)
    assert nav, "the contents list was not linked"
    links = re.findall(r'href="#([^"]+)"', nav.group(1))
    assert len(links) == 2, links  # the third label has no matching heading
    ids = set(re.findall(r'id="([^"]+)"', web))
    assert [t for t in links if t not in ids] == []

    # A composite label resolves to the heading it names, and a label with no heading
    # stays plain text rather than becoming a link to nowhere.
    assert "career-wealth" in links
    items = re.findall(r"<li>(.*?)</li>", nav.group(1), re.DOTALL)
    plain = [i for i in items if not i.lstrip().startswith("<a ")]
    assert len(plain) == 1 and "Does Not Exist" in plain[0], plain


def test_wide_tables_scroll_inside_their_own_box(web):
    """A six-column table is wider than a phone; the page must not scroll sideways."""
    assert web.count("<table") == web.count('class="table-scroll"')
    for wrapper in re.findall(r'<div class="table-scroll"[^>]*>(.*?)</div>', web, re.DOTALL):
        assert "<table" in wrapper
    assert 'tabindex="0"' in web and 'role="region"' in web


# ── the extras the web page makes possible ─────────────────────────────────────────

def test_audio_player_lands_in_the_audio_section():
    with_audio = markdown_to_html(MD, title="T", tier="deep", web=True,
                                  audio_url="https://example.test/audio.mp3")
    heading = with_audio.find("MP3 Audio Summary")
    player = with_audio.find("<audio")
    assert 0 < heading < player, "the player must sit in the section the copy promises"
    assert 'controls' in with_audio[player:player + 120]
    # Silent when there is nothing to play.
    assert "<audio" not in markdown_to_html(MD, title="T", tier="deep", web=True)


def test_toolbar_is_injected_above_the_cover(web):
    # The CSS mentions the class; the *element* is what must be absent.
    assert '<div class="report-toolbar"' not in web, \
        "the downloadable file ships without the toolbar"
    with_bar = markdown_to_html(
        MD, title="T", tier="deep", web=True,
        toolbar_html='<div class="report-toolbar"><a href="/x.pdf">Download PDF</a></div>')
    assert with_bar.find("report-toolbar") < with_bar.find('class="cover"')


# ── the print document is untouched ───────────────────────────────────────────────

def test_print_mode_gains_nothing_from_the_web_layer(print_doc):
    assert "web-mode" not in print_doc
    assert "report-toolbar" not in print_doc
    assert 'class="table-scroll"' not in print_doc
    assert 'class="anchor"' not in print_doc
    assert 'id="career-wealth"' not in print_doc
    # The viewport tag is shared on purpose: the review console previews this HTML in a
    # browser, and a phone-width preview is unreadable without it.
    assert 'name="viewport"' in print_doc


# ── against a real report ──────────────────────────────────────────────────────────

def test_a_real_report_renders_web_clean():
    from tools.qa_client_ready import _html_text, scan

    md = (REPO_ROOT / "tests" / "golden" / "wren-deep.md").read_text(encoding="utf-8")
    document = markdown_to_html(md, title="Golden wren-deep", tier="deep", web=True)
    assert document.count("<style") == 1 and "<svg" in document
    findings = scan(_html_text(document), source="html", rendered=True, tier="deep")
    assert findings == [], [f"{f.code}: {f.note}" for f in findings]


def test_a_repeated_gloss_is_collapsed():
    """The engine writes some terms in both scripts inside one gloss.

    "(합이불화, 合而不化)" translated both to "binding without transforming", so the
    delivered report read it twice — three times over (external audit, 2026-10-16,
    §2.1 #3). Collapsed in the parenthetical, and only there.
    """
    from saju_html import translate_inline

    out = translate_inline("**합이불화 (합이불화, 合而不化)** holds", gloss=True)
    assert "binding without transforming" in out
    assert out.count("binding without transforming") == 1, out
    # A legitimate list of two different things is untouched.
    assert translate_inline("(Yin Earth, Yin Metal)", gloss=True) == "(Yin Earth, Yin Metal)"
