"""HTML/Playwright renderer for Saju markdown reports.

Converts a markdown document into a styled HTML string and then prints it to
PDF using Playwright/Chromium. The translation maps are imported from
`saju_html.__init__` so they stay in sync with the reportlab generator.

Section styling (`_wrap_*`) lives in `saju_html.sections`; SVG chart builders
(`_build_element_balance_chart`, `_build_decade_roadmap_svg`) live in
`saju_html.svg_charts`. This module orchestrates them and owns the markdown
parser, cover-page builder, and PDF printer.
"""
from __future__ import annotations

import base64
from functools import lru_cache

import html
import logging
import os
import warnings
import re
from datetime import date
from pathlib import Path

# Markdown-It preserves raw HTML (e.g. <b>) and parses GFM tables.
from markdown_it import MarkdownIt

# Jinja2 renders the document/cover templates (C1, 2026-10-07). Autoescape is
# OFF so pre-escaped values and the CSS pass through unchanged; every cover
# value is still ``html.escape``-d before it reaches the template.
from jinja2 import Environment as _JinjaEnvironment

from saju_html import (
    _CJK_RE,
    ELEMENT_EMOJI,
    fix_articles,
    resolve_toc_target,
    strip_engine_drafts,
    strip_source_citations,
)
from saju_html.sections import (
    _wrap_audio_included,
    _wrap_chart_signature,
    _wrap_decade_roadmap,
    _wrap_luck_classes,
    _wrap_luck_favorable,
    _wrap_luck_timeline,
    _wrap_lucky_attributes,
    _wrap_partner_upsell,
    _wrap_quick_ref,
    _wrap_right_now,
)
from saju_html.svg_charts import inject_element_balance_chart


# Document + cover templates (Jinja2, autoescape off). The outer <title> is
# escaped by the renderer before it is passed in; cover values likewise. Kept
# inline so the module stays self-contained.
_DOCUMENT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
{% if web_head %}{{ web_head }}
{% endif %}<style>
{{ css }}
</style>
</head>
<body class="{{ body_class }}">
{% if toolbar %}{{ toolbar }}
{% endif %}{{ page_open }}{{ cover }}
{{ body }}
{{ page_close }}</body>
</html>
"""

_COVER_TEMPLATE = """<div class="cover">
  <div class="watermark">命</div>
  <h1>{{ title }}</h1>
  <p class="subtitle">{{ subtitle }}</p>
{% if meta_block %}  <div class="meta-block">
{{ meta_block }}
  </div>
{% endif %}  <p class="foot">{{ footnote }}</p>
  <p class="date">Generated {{ generation_date }}</p>
{% if report_id %}  <p class="report-id">Report ID: {{ report_id }} · CosmicSaju · cosmicsaju.com</p>
{% endif %}</div>
"""

# In web mode the report is a page that happens to be token-gated. `noindex` is
# belt-and-braces: the link is unguessable and the route is private, but a reader's
# report must never turn up in a search result.
_WEB_HEAD = (
    '<meta name="robots" content="noindex, nofollow">\n'
    '<meta name="color-scheme" content="light dark">'
)

_COMPACT_COVER_TEMPLATE = """<div class="compact-cover">
  <h1>{{ title }}</h1>
  <p class="subtitle">{{ subtitle }}</p>
  <p class="meta">{{ meta }}</p>
  <p class="report-line">{{ report_line }}Generated {{ generation_date }} · CosmicSaju · cosmicsaju.com</p>
</div>
"""


def _jinja_env() -> _JinjaEnvironment:
    # keep_trailing_newline reproduces the exact byte output of the previous
    # hand-built strings (the rendered-HTML goldens pin this).
    return _JinjaEnvironment(autoescape=False, trim_blocks=False,
                             lstrip_blocks=False, keep_trailing_newline=True)


_HEADER_TEMPLATE = (
    '<div style="font-size:8px;color:#888;width:100%;text-align:center;'
    'font-family:Helvetica,Arial,sans-serif;padding:0 18px;">'
    "Saju Reading — Korean Four Pillars"
    "</div>"
)

_FOOTER_TEMPLATE = (
    '<div style="font-size:8px;color:#888;width:100%;'
    'font-family:Helvetica,Arial,sans-serif;padding:0 18px;">'
    '<span style="float:left;">CosmicSaju · cosmicsaju.com</span>'
    '<span style="float:right;">'
    'Page <span class="pageNumber"></span> / <span class="totalPages"></span>'
    ' · Report ID: {report_id}'
    ' · Personal &amp; Confidential'
    "</span>"
    "</div>"
)


def _load_css(css_path: Path | None) -> str:
    """Load CSS from disk; fall back to bundled CSS if no path given."""
    if css_path is not None:
        return Path(css_path).read_text(encoding="utf-8")
    here = Path(__file__).resolve().parent
    return (here / "theme.css").read_text(encoding="utf-8")


# The faces the reading embeds, subsetted by `tools/build-web-fonts.py`. Weights match the
# tokens in the app (`--font-display` 400/600/700, `--font-sans` 300–600, `--font-mono` 400).
# Inter and Cormorant are variable fonts, so one file serves every weight.
_WEB_FACES = (
    ("Inter", "Inter-web.woff2", "100 900"),
    ("Cormorant Garamond", "CormorantGaramond-web.woff2", "300 700"),
    ("IBM Plex Mono", "IBMPlexMono-web.woff2", "400"),
)


@lru_cache(maxsize=1)
def _web_font_css() -> str:
    """`@font-face` rules with the app's faces inlined as data URIs.

    The webapp loads these from Google's CDN. A delivered reading cannot: it has to be one
    self-contained file, and a third-party font request would also tell someone when a client
    opened their report. Subsetted to the glyphs a report sets, the three faces add ~230 KB to
    a document that is served once and kept — cheaper than the four requests the app makes, and
    it removes the dependency on the reader having any of these fonts.

    Cached for the life of the process: a batch of reports should not re-encode them each time.
    """
    rules = []
    fonts_dir = Path(__file__).resolve().parent / "fonts"
    for family, filename, weight in _WEB_FACES:
        path = fonts_dir / filename
        if not path.exists():  # pragma: no cover - the files are bundled
            _log.warning("web font %s missing; the reading will fall back", filename)
            continue
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            "@font-face {"
            f" font-family: '{family}'; font-style: normal; font-weight: {weight};"
            " font-display: swap;"
            f" src: url(data:font/woff2;base64,{encoded}) format('woff2');"
            " }"
        )
    return "\n".join(rules)


def _load_web_css() -> str:
    """The screen layer, bundled beside `theme.css`.

    `theme.css` is built for A4 (page boxes, running footers, repeated table headers); it
    renders a document, but a phone would get one squeezed column and tables hanging off
    the viewport. This layer is appended in web mode only, so the print result is byte-for-
    byte what it was.
    """
    return (Path(__file__).resolve().parent / "theme-web.css").read_text(encoding="utf-8")


def _make_md_parser() -> MarkdownIt:
    """Return a MarkdownIt instance with tables enabled.

    N-8 (2026-09-26 audit): `html: True` let literal HTML in the markdown
    body (e.g. a client's name/city/main_concern, interpolated verbatim by
    the report generators) survive into the HTML that Chromium renders —
    `<script>`/`<iframe>` included. The report generators never rely on raw
    HTML passthrough (only CommonMark constructs), so `html: False` closes
    the injection vector at its source: markdown-it escapes it as literal
    text instead of parsing it as HTML.
    """
    md = MarkdownIt("commonmark", {"html": False, "linkify": False})
    md.enable(["table", "strikethrough"])
    return md


_log = logging.getLogger(__name__)


class PdfBackendUnavailable(RuntimeError):
    """The HTML/Playwright PDF backend cannot run (no Playwright or no browser)."""


def _translate_html(text: str, unmapped: set | None = None) -> str:
    """Apply CJK/Hanja translation to HTML text.

    We intentionally translate *after* markdown has been rendered to HTML, so
    that terms appearing in headings, paragraphs, table cells, and links are
    all handled uniformly.
    """
    from saju_html import translate_inline

    # gloss=True keeps the Hanja/Korean term beside its English ("Direct Officer
    # (正官)") — the delivered artefact's convention. The browser's own font stack
    # (theme.css lists Noto CJK) draws it.
    out = translate_inline(text, keep_unmapped=True, unmapped=unmapped, gloss=True)
    return fix_articles(out)


def _translate_cover(text: str, unmapped: set | None = None) -> str:
    """Translate a cover field (title / client / dob / Day Master) like the body.

    Day Masters may arrive as raw Hanja ("壬 (Water Yang)" -> "Im (Water Yang)",
    compat "庚/辛" -> "Gyeong/Sin"), exactly as the reportlab cover renders them.
    """
    if not text or not _CJK_RE.search(text):
        return text  # plain-ASCII fields (names!) are never touched
    # Translate only the CJK spans, so Latin text around them is left exactly
    # as given (translate_inline's post-processing would e.g. split "McKay").
    out = _CJK_RE.sub(lambda m: _translate_html(m.group(0), unmapped), text)
    return out


def _build_cover_html(
    title: str,
    subtitle: str,
    meta_rows: list[tuple[str, str]],
    footnote: str,
    generation_date: str,
    report_id: str = "",
) -> str:
    # Escape all cover-page inputs — they flow into HTML that Chromium
    # renders (via page.set_content), so unescaped user input (e.g. a name
    # from the intake form) is an injection sink. Labels are constants but
    # are escaped too for defense in depth.
    escaped = [(html.escape(label), html.escape(value)) for label, value in meta_rows]
    meta_block = "\n".join(f'    <p class="meta"><strong>{label}</strong>{value}</p>'
                           for label, value in escaped)
    template = _jinja_env().from_string(_COVER_TEMPLATE)
    return template.render(
        title=html.escape(title),
        subtitle=html.escape(subtitle),
        meta_block=meta_block,
        footnote=html.escape(footnote),
        generation_date=html.escape(generation_date),
        report_id=html.escape(report_id),
    )


def _drop_first_h1(html: str) -> str:
    """Remove the first <h1>...</h1> from markdown body (it is on the cover)."""
    return re.sub(r"<h1\b[^>]*>.*?</h1>", "", html, count=1, flags=re.IGNORECASE)


def _drop_title_block(html: str) -> str:
    """Remove the first <h1> and everything up to the next <hr> (inclusive).

    Used in compact one-page mode so the renderer's compact banner is the
    only title header.

    Safety guard: only consider an <hr> that appears *before* the first real
    section heading (<h2>..<h6>). Otherwise a later horizontal rule (for example
    before a Sources section) would swallow the whole report body.
    """
    # Find first h1 start.
    h1_match = re.search(r"<h1\b[^>]*>", html, re.IGNORECASE)
    if not h1_match:
        return html

    body = html[h1_match.start():]
    # First real section heading after the h1.
    section_match = re.search(r"<h[2-6]\b", body, re.IGNORECASE)
    section_pos = section_match.start() if section_match else len(body)

    # Only look for <hr> inside the pre-section title block.
    hr_match = re.search(r"<hr\b[^>]*>", body[:section_pos], re.IGNORECASE)
    if not hr_match:
        return _drop_first_h1(html)
    end = h1_match.start() + hr_match.end()
    return html[: h1_match.start()] + html[end:]


def _style_element_balance_tables(html_table: str) -> str:
    """Add element-specific CSS classes to element-balance rows.

    markdown-it renders the table with plain <tr><td>🔴 Fire</td>...</tr>.
    We post-process so the theme.css can color the text consistently.
    """
    # Only touch tables whose header row contains the expected columns.
    if not all(h in html_table for h in ("Element", "Presence", "Percentage")):
        return html_table

    # Add a class to each data row based on its first cell text.
    table = html_table
    for element, cls in {
        "Fire": "element-fire",
        "Earth": "element-earth",
        "Metal": "element-metal",
        "Water": "element-water",
        "Wood": "element-wood",
    }.items():
        emoji = ELEMENT_EMOJI.get(element, "")
        # Match a <tr> whose first <td> contains the emoji + element text.
        table = re.sub(
            rf'(<tr[^>]*>\s*<td[^>]*>){re.escape(emoji)}\s*{re.escape(element)}',
            rf'\1<span class="{cls}">{emoji} {element}</span>',
            table,
            flags=re.IGNORECASE,
        )
    return table


def _render_markdown(md_text: str, tier: str | None = None) -> str:
    """Render markdown to HTML, applying all post-processing wrappers."""
    md = _make_md_parser()
    md_text = strip_source_citations(md_text)
    md_text = strip_engine_drafts(md_text)
    # All client-facing PDFs are English-primary; translate Korean/Hanja
    # annotations just like single-chart reports.
    unmapped: set = set()
    translated = _translate_html(md_text, unmapped)
    if unmapped:
        _log.warning(
            "Unmapped CJK characters kept as-is in rendered HTML (add them to "
            "the saju_html translation maps): %s",
            "".join(sorted(unmapped)),
        )
    html_doc = md.render(translated)
    html_doc = inject_element_balance_chart(html_doc, _style_element_balance_tables)
    html_doc = _wrap_quick_ref(html_doc)
    html_doc = _wrap_right_now(html_doc)
    html_doc = _wrap_lucky_attributes(html_doc)
    html_doc = _wrap_decade_roadmap(html_doc)
    html_doc = _wrap_luck_timeline(html_doc)
    html_doc = _wrap_luck_favorable(html_doc)
    html_doc = _wrap_luck_classes(html_doc)
    html_doc = _wrap_chart_signature(html_doc)
    html_doc = _wrap_audio_included(html_doc)
    html_doc = _wrap_partner_upsell(html_doc)
    return html_doc


def _build_compact_cover_html(
    title: str,
    subtitle: str,
    meta_rows: list[tuple[str, str]],
    generation_date: str,
    report_id: str = "",
) -> str:
    """A one-page-hook style banner that sits at the top of the body."""
    meta = " · ".join(f"{html.escape(label)}: {html.escape(value)}" for label, value in meta_rows)
    report_line = f"Report ID: {html.escape(report_id)} · " if report_id else ""
    template = _jinja_env().from_string(_COMPACT_COVER_TEMPLATE)
    return template.render(
        title=html.escape(title),
        subtitle=html.escape(subtitle),
        meta=meta,
        report_line=report_line,
        generation_date=html.escape(generation_date),
    )


_HEADING_RE = re.compile(r"<(h[23])([^>]*)>(.*?)</\1>", re.DOTALL)
_TOC_HEADING_RE = re.compile(r"<h2[^>]*>\s*Table of Contents\s*</h2>", re.IGNORECASE)
_UL_RE = re.compile(r"<ul>(.*?)</ul>", re.DOTALL)
_TABLE_RE = re.compile(r"(<table\b.*?</table>)", re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")


def _slugify_heading(text: str, seen: dict) -> str:
    """A readable, unique anchor for a heading.

    Readable rather than hashed because these ids end up in an address a client can share
    or bookmark (#career-wealth, not #saju-c0737a). Non-ASCII is dropped — the Hanja gloss
    is a label, not a URL — and a repeated heading gets a numeric suffix, because
    duplicate ids are invalid HTML and break the second occurrence's link.
    """
    plain = html.unescape(_TAG_RE.sub("", text)).strip()
    slug = re.sub(r"[^a-z0-9]+", "-", plain.casefold()).strip("-")[:60]
    slug = slug or "section"
    seen[slug] = seen.get(slug, 0) + 1
    return slug if seen[slug] == 1 else f"{slug}-{seen[slug]}"


def _add_heading_anchors(html_text: str) -> tuple[str, list]:
    """Give every h2/h3 an id and a tappable anchor. Returns (html, [(text, id)]).

    The HTML report had **no ids at all**, so a twenty-page reading could not be
    navigated, linked to, or jumped to from its own contents list.
    """
    collected: list = []
    seen: dict = {}
    out: list = []
    cursor = 0
    for match in _HEADING_RE.finditer(html_text):
        tag, attrs, inner = match.group(1), match.group(2), match.group(3)
        plain = html.unescape(_TAG_RE.sub("", inner)).strip()
        slug = _slugify_heading(plain, seen)
        out.append(html_text[cursor:match.start()])
        out.append(f'<{tag} id="{slug}"{attrs}>{inner}'
                   f'<a class="anchor" href="#{slug}" aria-label="Link to this section">#</a>'
                   f'</{tag}>')
        cursor = match.end()
        # The offset of the heading *in the new document*, so the contents pass can look
        # forward from it. (Re-matching the heading after this rewrite is what failed
        # first: the h2 now contains its own anchor link.)
        collected.append((plain, slug, len("".join(out))))
    out.append(html_text[cursor:])
    return "".join(out), collected


def _link_contents(html_text: str, headings: list) -> str:
    """Turn the contents list into real links, matching labels the way the PDF does.

    Labels are not always literal headings (see `resolve_toc_target`), and an entry that
    cannot be resolved stays plain text: a contents list must never ship a link to
    nowhere.
    """
    if not headings:
        return html_text
    contents_end = next((end for plain, _slug, end in headings
                         if plain.casefold() == "table of contents"), None)
    if contents_end is None:
        return html_text
    listed = _UL_RE.search(html_text, contents_end)
    if not listed:
        return html_text

    by_heading = {plain: slug for plain, slug, _end in headings}

    def replace_item(item: "re.Match") -> str:
        inner = item.group(1)
        label = html.unescape(_TAG_RE.sub("", inner)).strip()
        target = resolve_toc_target(label, list(by_heading))
        if not target:
            return f"<li>{inner}</li>"
        return f'<li><a href="#{by_heading[target]}">{inner}</a></li>'

    items_html = re.sub(r"<li>(.*?)</li>", replace_item, listed.group(1), flags=re.DOTALL)
    nav = f'<nav class="toc" aria-label="Contents"><ul>{items_html}</ul></nav>'
    return html_text[: listed.start()] + nav + html_text[listed.end():]


def _drop_repeated_title(html_text: str, title: str) -> str:
    """Drop a leading section heading that only repeats the cover title.

    The markdown's own title block runs to the first `<hr>`, which in the Deep report is well
    past the title — so the reading opened with a card saying the client's name and the tier
    again, directly under a cover that already said both. Only the heading and its tagline go:
    the "Time method" paragraph that follows is real content (and the audit named it a
    strength), so it stays in the first panel.
    """
    from saju_html import toc_key

    match = re.match(r"\s*<h2\b[^>]*>(.*?)</h2>\s*", html_text, re.DOTALL)
    if not match:
        return html_text
    plain = html.unescape(_TAG_RE.sub("", match.group(1))).strip()
    if not plain or toc_key(plain) != toc_key(title):
        return html_text
    rest = html_text[match.end():]
    # …and the italic tagline that always follows it, if that is what is there.
    rest = re.sub(r"^\s*<p>\s*<em>.*?</em>\s*</p>\s*", "", rest, count=1, flags=re.DOTALL)
    return rest


def _group_sections(html_text: str) -> str:
    """Wrap each top-level section in a card, with a numbered eyebrow.

    The app lays out a dashboard as cards on a dark surface; a reading that runs as one
    undifferentiated column of headings is what made it look like a document rather than
    the same product. Each `<h2>` — and everything up to the next one — becomes a panel,
    and the heading gains a monospace ordinal, which is the app's eyebrow idiom.

    Runs *after* the anchor and contents passes on purpose: those compute a heading's slug
    and match contents labels from the heading's own text, and the eyebrow would otherwise
    leak a number into both.
    """
    parts = re.split(r"(?=<h2\b)", html_text)
    out: list = []
    number = 0
    for part in parts:
        if not re.match(r"<h2\b", part):
            out.append(part)          # the cover, and anything before the first section
            continue
        number += 1
        part = re.sub(
            r"^(<h2\b[^>]*>)",
            lambda m: f'{m.group(1)}<span class="panel-eyebrow">{number:02d}</span>',
            part, count=1,
        )
        out.append(f'<section class="panel">{part}</section>')
    return "".join(out)


def _wrap_tables_for_web(html_text: str) -> str:
    """Let wide tables scroll inside their own box instead of the page sideways.

    A six-column ten-god table is wider than a phone; without this the *page* scrolls
    horizontally, which is the commonest mobile defect. The wrapper is focusable so a
    keyboard user can scroll it without a pointer.
    """
    return _TABLE_RE.sub(
        lambda m: (f'<div class="table-scroll" tabindex="0" role="region" '
                   f'aria-label="Table, scrollable">{m.group(1)}</div>'),
        html_text)


def _inject_audio_player(html_text: str, audio_url: str) -> str:
    """Put the MP3 on the page, where the report says it lives.

    The Deep tier's copy promises the audio "appears on the same page as your reading",
    which a PDF cannot honour and a web page can. Silent when there is no URL.
    """
    if not audio_url:
        return html_text
    match = re.search(r"(<h2[^>]*>\s*MP3 Audio Summary[^<]*</h2>)", html_text, re.IGNORECASE)
    if not match:
        return html_text
    url = html.escape(audio_url, quote=True)
    block = (
        '<div class="audio-summary">'
        "<p>Listen to your audio summary</p>"
        f'<audio controls preload="none" src="{url}">'
        "Your browser cannot play this audio file. "
        f'<a href="{url}">Download it instead</a>.'
        "</audio></div>"
    )
    return html_text[: match.end()] + block + html_text[match.end():]


def markdown_to_html(
    md_text: str,
    *,
    title: str = "Saju Reading",
    client: str = "",
    dob: str = "",
    day_master: str = "",
    css_path: Path | None = None,
    generation_date: str | None = None,
    report_id: str = "",
    compact: bool = False,
    tier: str | None = None,
    web: bool = False,
    audio_url: str = "",
    toolbar_html: str = "",
) -> str:
    """Render a Saju markdown report into a styled HTML document.

    Parameters
    ----------
    md_text : str
        Source markdown text (Korean/Hanja is translated into English).
    title, client, dob, day_master : str
        Cover page values.
    css_path : Path | None
        Optional external CSS file. Defaults to bundled `theme.css`.
    generation_date : str | None
        Date string for the cover footer. Defaults to today's date.
    report_id : str
        Unique report ID printed on the cover and in the footer.
    compact : bool
        If True, render a compact in-line header instead of a full cover page.
        Intended for the free one-page Hook tier.
    tier : str | None
        Optional tier label (e.g. "sample", "essential", "deep"). When set,
        the body gets a `tier-{tier}` class so theme.css can apply tier-
        specific styles. Default: no class.
    web : bool
        Render the **web document** rather than the print one: a screen layer on top of
        `theme.css`, heading ids, a linked contents list, scrollable tables, and
        `noindex`. The output stays a single self-contained file (inline CSS and SVG, no
        external requests), so it can be served *and* downloaded as-is.
    audio_url : str
        When given, a player is placed in the MP3 Audio Summary section — the page the
        Deep tier's copy promises.
    toolbar_html : str
        Optional markup injected above the cover. The webapp uses it for the download bar
        when it serves the report; the downloadable file is rendered without it.

    Returns
    -------
    str
        Full HTML document.
    """
    generation_date = generation_date or date.today().strftime("%B %d, %Y")
    css = _load_css(css_path)
    if web:
        # Order matters: the faces, then the layer that puts them to work.
        css = (f"{css}\n\n/* ---- embedded faces (the app's own, subsetted) ---- */\n"
               f"{_web_font_css()}"
               f"\n\n/* ---- web layer (screen only; print rules above still apply) ---- */\n"
               f"{_load_web_css()}")

    subtitle = "A Reading in the Korean Four Pillars Tradition"
    footnote = (
        "Grounded in the Five Elements and Yin-Yang philosophy. "
        "Interpreted through classical Myeongri (Korean Saju) tradition: "
        "Jeokcheon-su, Yeonhae-japyeong, Gungtong-bogam, Myeongri-jeongjong."
    )

    cover_unmapped: set = set()
    title = _translate_cover(title, cover_unmapped)
    client = _translate_cover(client, cover_unmapped)
    dob = _translate_cover(dob, cover_unmapped)
    day_master = _translate_cover(day_master, cover_unmapped)
    if cover_unmapped:
        _log.warning(
            "Unmapped CJK characters kept as-is on the cover (add them to "
            "the saju_html translation maps): %s",
            "".join(sorted(cover_unmapped)),
        )

    meta_rows: list[tuple[str, str]] = []
    if client:
        meta_rows.append(("For", client))
    if dob:
        meta_rows.append(("Born", dob))
    if day_master:
        meta_rows.append(("Day Master", day_master))

    if compact:
        cover_html = _build_compact_cover_html(title, subtitle, meta_rows, generation_date, report_id)
    else:
        cover_html = _build_cover_html(title, subtitle, meta_rows, footnote, generation_date, report_id)

    body_html = _render_markdown(md_text, tier=tier)
    # The renderer builds its own cover page (compact or full), so drop the
    # markdown's own title/cover block (h1 through the first horizontal rule)
    # to avoid duplicate headers and blank pages.
    body_html = _drop_title_block(body_html)

    if web:
        # Order matters. The audio block goes in while the headings are still bare (its
        # matcher looks for a plain "…</h2>"); the contents list can only link to anchors
        # that already exist, so it runs after the anchor pass.
        body_html = _drop_repeated_title(body_html, title)
        body_html = _inject_audio_player(body_html, audio_url)
        body_html, headings = _add_heading_anchors(body_html)
        body_html = _link_contents(body_html, headings)
        body_html = _group_sections(body_html)
        body_html = _wrap_tables_for_web(body_html)
        body_html += (
            '<p class="colophon">Typeset in Inter, Cormorant Garamond and IBM Plex Mono, '
            "embedded under the SIL Open Font License.</p>"
        )

    classes = []
    if compact:
        classes.append("compact-mode")
    elif tier:
        classes.append(f"tier-{tier}")
    if web:
        classes.append("web-mode")

    template = _jinja_env().from_string(_DOCUMENT_TEMPLATE)
    return template.render(
        title=html.escape(title),
        css=css,
        cover=cover_html,
        body=body_html,
        body_class=" ".join(classes),
        web_head=_WEB_HEAD if web else "",
        toolbar=toolbar_html,
        # The readable column is a *wrapper*, not a rule on every top-level child: a
        # `body > *` rule with `margin: auto` is silently undone by the next `p { margin: … }`
        # that comes after it, which is exactly what left the front matter ragged while the
        # panels below it were centred. Print gets nothing, so its bytes are unchanged.
        page_open='<div class="page">' if web else "",
        page_close="</div>" if web else "",
    )


def _launch_browser(playwright) -> None:
    """Launch Playwright's bundled Chromium (the same binary on every machine).

    Install it with ``pip install -e .[html]`` and
    ``python -m playwright install chromium``. If the bundled Chromium is not
    installed, a system Google Chrome (``channel="chrome"``) is used with a
    warning (it may render slightly differently). Set
    ``SAJU_ALLOW_SYSTEM_CHROME=0`` to require the bundled Chromium (identical
    output on every machine).

    Raises PdfBackendUnavailable (a RuntimeError) naming the fix when no
    permitted browser can be launched.
    """
    try:
        return playwright.chromium.launch()
    except Exception as exc:  # pragma: no cover - environment-specific
        bundled_error = str(exc)
    if os.environ.get("SAJU_ALLOW_SYSTEM_CHROME", "1") != "0":
        try:
            browser = playwright.chromium.launch(channel="chrome")
            warnings.warn(
                "Bundled Playwright Chromium not installed; rendering with system "
                "Google Chrome (output may differ slightly between machines). Run "
                "`python -m playwright install chromium` or set "
                "SAJU_ALLOW_SYSTEM_CHROME=0 to require the bundled browser.",
                stacklevel=2,
            )
            return browser
        except Exception as exc:  # pragma: no cover - environment-specific
            raise PdfBackendUnavailable(
                "No usable browser for the HTML/Playwright PDF backend. Install "
                "Playwright's Chromium with `python -m playwright install chromium`. "
                f"Bundled Chromium error: {bundled_error!r}; "
                f"system Chrome error: {exc!r}"
            ) from exc
    raise PdfBackendUnavailable(
        "No usable browser for the HTML/Playwright PDF backend. Install "
        "Playwright's Chromium with `python -m playwright install chromium` "
        "(SAJU_ALLOW_SYSTEM_CHROME=0 is set, so a system Google Chrome was not "
        "tried). "
        f"Bundled Chromium error: {bundled_error!r}"
    )


def html_to_pdf(
    html_doc: str,
    output_pdf: Path,
    *,
    header: str = _HEADER_TEMPLATE,
    footer: str = _FOOTER_TEMPLATE,
    report_id: str = "",
) -> Path:
    """Print the given HTML to PDF using Playwright/Chromium.

    Parameters
    ----------
    html_doc : str
        Full HTML document.
    output_pdf : Path
        Destination PDF path.
    header, footer : str
        Native header/footer HTML templates for Chromium PDF printing.
    report_id : str
        Unique report ID interpolated into the footer template.

    Returns
    -------
    Path
        The output PDF path.
    """
    from playwright.sync_api import sync_playwright

    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    footer_html = footer.format(report_id=html.escape(report_id))

    with sync_playwright() as p:
        # Bundled Chromium preferred; system Chrome with a warning unless
        # SAJU_ALLOW_SYSTEM_CHROME=0 (see _launch_browser).
        browser = _launch_browser(p)
        # N-8 (2026-09-26 audit) defense-in-depth: the report is static markup
        # printed to PDF, so it never needs to run script or fetch a network
        # resource. Disabling JS and aborting every non-data: request means
        # even HTML that slipped past `html: False` above (e.g. a future
        # bug, or a caller that renders raw HTML directly) can't execute
        # script or reach an SSRF target.
        page = browser.new_page(java_script_enabled=False)
        page.route("**/*", lambda route: (
            route.continue_() if route.request.url.startswith("data:")
            else route.abort()
        ))
        page.set_content(html_doc)
        page.pdf(
            path=str(output_pdf),
            format="A4",
            print_background=True,
            margin={
                "top": "18mm",
                "bottom": "22mm",
                "left": "18mm",
                "right": "18mm",
            },
            display_header_footer=True,
            header_template=header,
            footer_template=footer_html,
        )
        browser.close()
    return output_pdf


def build_pdf(*args, **kwargs) -> Path:
    """Read markdown from disk and produce a styled PDF (see ``build_pdf_with_backend``)."""
    return build_pdf_with_backend(*args, **kwargs)[0]


def build_pdf_with_backend(
    input_md: Path,
    output_pdf: Path,
    *,
    title: str = "Saju Reading",
    client: str = "",
    dob: str = "",
    day_master: str = "",
    css_path: Path | None = None,
    generation_date: str | None = None,
    report_id: str = "",
    compact: bool = False,
    tier: str | None = None,
    allow_fallback: bool = False,
) -> tuple[Path, str]:
    """Convenience: read markdown from disk and produce a styled PDF.

    Returns ``(pdf_path, backend)`` where backend is ``"html-playwright"`` or
    ``"reportlab-fallback"`` (the backend that actually produced the file).

    Uses the HTML/Playwright backend when Playwright and a Chromium-compatible
    browser are available. If either is missing or the browser cannot launch,
    falls back silently to the ReportLab-based ``md_to_saju_pdf.build_pdf`` so
    that CI runners and minimal environments still produce a PDF.
    """
    output_pdf = Path(output_pdf)
    if not report_id:
        report_id = f"CID-{output_pdf.stem}-{date.today().strftime('%Y%m%d')}"
    md_text = Path(input_md).read_text(encoding="utf-8")
    html = markdown_to_html(
        md_text,
        title=title,
        client=client,
        dob=dob,
        day_master=day_master,
        css_path=css_path,
        generation_date=generation_date,
        report_id=report_id,
        compact=compact,
        tier=tier,
    )
    try:
        return html_to_pdf(html, output_pdf, report_id=report_id), "html-playwright"
    except (ImportError, RuntimeError) as exc:
        if not (allow_fallback or os.environ.get("SAJU_PDF_FALLBACK") == "reportlab"):
            raise PdfBackendUnavailable(
                f"HTML/Playwright PDF backend unavailable: {exc}. Install with "
                "`pip install playwright && python -m playwright install chromium`, "
                "or opt in to the ReportLab fallback explicitly: pass "
                "allow_fallback=True, set env SAJU_PDF_FALLBACK=reportlab, or "
                "use the ReportLab tool src/saju_html/md_to_saju_pdf.py."
            ) from exc
        # Explicitly opted in: ReportLab ignores CSS, compact mode and a custom
        # generation date, but produces a presentable PDF from the same markdown.
        import warnings

        warnings.warn(
            f"HTML/Playwright PDF backend unavailable ({exc!r}); "
            "falling back to ReportLab PDF output.",
            stacklevel=2,
        )
        from saju_html.md_to_saju_pdf import build_pdf as _reportlab_build_pdf

        return _reportlab_build_pdf(
            input_md,
            output_pdf,
            title,
            client,
            dob,
            day_master,
            report_id=report_id,
            tier=tier,
        ), "reportlab-fallback"


__all__ = [
    "PdfBackendUnavailable",
    "build_pdf",
    "build_pdf_with_backend",
    "markdown_to_html",
    "html_to_pdf",
    "_wrap_decade_roadmap",       # re-exported for tests
    "_wrap_luck_timeline",        # re-exported for tests
    "_wrap_luck_favorable",
    "_wrap_luck_classes",
]