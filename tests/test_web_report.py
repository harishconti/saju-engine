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


# ── the app's design system, mirrored ──────────────────────────────────────────────

APP_CSS = REPO_ROOT / "apps" / "web" / "src" / "app" / "globals.css"
WEB_CSS = REPO_ROOT / "src" / "saju_html" / "theme-web.css"


def _vars_in(text: str, start: int) -> dict:
    """`--name: value;` pairs from the block that begins at ``start``."""
    depth = 0
    body = []
    for ch in text[start:]:
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                break
            continue
        if depth >= 1:
            body.append(ch)
    found = {}
    for match in re.finditer(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", "".join(body)):
        found[match.group(1)] = match.group(2).strip()
    return found


def _app_tokens(*, light: bool) -> dict:
    css = APP_CSS.read_text(encoding="utf-8")
    if light:
        media = css.index("@media (prefers-color-scheme: light) {")
        return _vars_in(css, css.index(":root", media))
    return _vars_in(css, css.index(":root {"))


def _report_tokens(*, light: bool) -> dict:
    css = WEB_CSS.read_text(encoding="utf-8")
    if light:
        media = css.index("@media (prefers-color-scheme: light) {")
        return _vars_in(css, css.index(":root", media))
    return _vars_in(css, css.index(":root {"))


@pytest.mark.parametrize("light", [False, True], ids=["dark", "light"])
def test_report_tokens_match_the_webapp(light):
    """The reading is styled from the app's own tokens, and this is what keeps it true.

    A rebrand that updates `globals.css` and forgets the report would ship a reading that
    looks like a different product — the complaint this redesign fixes. Only the tokens the
    report actually mirrors are compared, so the app can add its own without failing here.
    """
    app = _app_tokens(light=light)
    report = _report_tokens(light=light)
    assert report, "no tokens found in the report stylesheet"
    mismatched = {
        name: (value, app.get(name))
        for name, value in report.items()
        if name in app and app[name] != value
    }
    assert not mismatched, mismatched
    # The palette that matters most: the five elements, which colour every chart.
    for name in ("--el-wood", "--el-fire", "--el-earth", "--el-metal", "--el-water"):
        assert name in report and name in app
        assert report[name] == app[name], name


def test_report_remaps_the_print_sheet_tokens(print_doc):
    """Every block in `theme.css` was written against `--color-*`, so the web layer re-points them.

    Without this, the print sheet's light chips, stripes and card backgrounds leak into a dark
    reading — a light table on a near-black page, which is exactly how the first version looked.
    """
    assert "--color-card-bg: transparent" in WEB_CSS.read_text(encoding="utf-8")
    for token in ("--color-heading", "--color-rule", "--color-accent", "--color-callout-bg"):
        assert token in WEB_CSS.read_text(encoding="utf-8")
    # And the stylesheet is the *web* layer only: the print document carries none of it —
    # that is what keeps the PDF and its snapshots byte-identical.
    assert "--color-card-bg: transparent" not in print_doc


# ── layout: sections as cards, the way the app is laid out ─────────────────────────

def test_sections_are_grouped_into_panels_with_an_eyebrow(web):
    panels = re.findall(r'<section class="panel">(.*?)</section>', web, re.DOTALL)
    assert len(panels) >= 4, f"expected sections as panels, found {len(panels)}"
    for index, panel in enumerate(panels, start=1):
        assert f'<span class="panel-eyebrow">{index:02d}</span>' in panel, panel[:120]
        assert panel.lstrip().startswith("<h2"), "a panel must open with its heading"
    # Headings outside a panel would render as unstyled text between cards.
    loose = re.findall(r'(?<!</section>)\s*<h2', web)
    assert len(loose) <= len(panels)


def test_the_readable_column_is_a_wrapper(web, print_doc):
    """The column is a wrapper, not a rule on `body > *`.

    It was `body.web-mode > * { margin: auto; max-width: 46rem }`, which the *next* block-level
    rule in the same sheet (`p { margin: 0 0 0.9rem }`) silently undid: the front matter sat hard
    left while the panels below it were centred, because panels had no competing `margin` rule.
    A wrapper cannot be undone that way.
    """
    assert '<div class="page">' in web
    assert "</div>" in web
    # …on screen. The `@media print` block is allowed to reset the top level, because it is
    # handing the page back to the A4 sheet.
    screen_only = WEB_CSS.read_text(encoding="utf-8").split("@media print")[0]
    assert "body.web-mode > *" not in screen_only, \
        "the screen column must not depend on every top-level child behaving"
    # Print gets no wrapper, so its markup and snapshots are unchanged.
    assert '<div class="page">' not in print_doc


def test_the_markdown_title_block_does_not_repeat_the_cover():
    """The cover already names the client and the tier.

    The markdown's own title block runs to the first `<hr>`, which in the Deep report is well
    past the title — so the reading opened with a card repeating both. The heading and its
    tagline go; the "Time method" paragraph that follows is content and stays.
    """
    md = "# Report Title\n\n## A Client — Deep Destiny Report\n\n*A tagline.*\n\n" \
         "**Born:** 2000-01-01\n\n**Time method:** corrected to 12:59.\n\n---\n\n" \
         "## Chart at a Glance\n\nBody.\n"
    web = markdown_to_html(md, title="A Client — Deep Destiny Report", tier="deep", web=True)
    assert "A tagline" not in web, "the tagline under the repeated title should go too"
    assert "Time method" in web, "real content must survive"
    # Once on the cover. (The `<title>` tag is not the body, so count within it.)
    body = web[web.index("<body"):]
    assert body.count("A Client — Deep Destiny Report") == 1, "the title appears once"


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
