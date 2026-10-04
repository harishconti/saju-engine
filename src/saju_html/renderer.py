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

import html
import logging
import os
import re
from datetime import date
from pathlib import Path

# Markdown-It preserves raw HTML (e.g. <b>) and parses GFM tables.
from markdown_it import MarkdownIt

from saju_html import (
    _CJK_RE,
    ELEMENT_EMOJI,
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


# Inlined default template so the script is self-contained.
_DEFAULT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{{ title }}</title>
<style>
{{ css }}
</style>
</head>
<body class="{{ body_class }}">
{{ cover|safe }}
{{ body|safe }}
</body>
</html>
"""


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

    return translate_inline(text, keep_unmapped=True, unmapped=unmapped)


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
    meta_lines = [
        f'<p class="meta"><strong>{html.escape(label)}</strong>{html.escape(value)}</p>'
        for label, value in meta_rows
    ]
    report_line = ""
    if report_id:
        report_line = f'  <p class="report-id">Report ID: {html.escape(report_id)} · CosmicSaju · cosmicsaju.com</p>\n'
    return (
        '<div class="cover">\n'
        '  <div class="watermark">命</div>\n'
        f'  <h1>{html.escape(title)}</h1>\n'
        f'  <p class="subtitle">{html.escape(subtitle)}</p>\n'
        '  <div class="meta-block">\n'
        + "\n".join(f"    {m}" for m in meta_lines)
        + "\n  </div>\n"
        + f'  <p class="foot">{html.escape(footnote)}</p>\n'
        + f'  <p class="date">Generated {html.escape(generation_date)}</p>\n'
        + report_line
        + "</div>\n"
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
    report_line = ""
    if report_id:
        report_line = f"Report ID: {html.escape(report_id)} · "
    return (
        '<div class="compact-cover">\n'
        f'  <h1>{html.escape(title)}</h1>\n'
        f'  <p class="subtitle">{html.escape(subtitle)}</p>\n'
        f'  <p class="meta">{meta}</p>\n'
        f'  <p class="report-line">{report_line}Generated {html.escape(generation_date)} · '
        'CosmicSaju · cosmicsaju.com</p>\n'
        '</div>\n'
    )


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

    Returns
    -------
    str
        Full HTML document.
    """
    generation_date = generation_date or date.today().strftime("%B %d, %Y")
    css = _load_css(css_path)

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

    body_class = ""
    if compact:
        body_class = "compact-mode"
    elif tier:
        body_class = f"tier-{tier}"
    template = _DEFAULT_TEMPLATE
    return (
        template.replace("{{ title }}", html.escape(title))
        .replace("{{ css }}", css)
        .replace("{{ cover|safe }}", cover_html)
        .replace("{{ body|safe }}", body_html)
        .replace("{{ body_class }}", body_class)
    )


def _launch_browser(playwright) -> None:
    """Launch Playwright's bundled Chromium (the same binary on every machine).

    Install it with ``pip install -e .[html]`` and
    ``python -m playwright install chromium``. A system Google Chrome
    (``channel="chrome"``) is used as a fallback ONLY when the operator opts in
    with ``SAJU_ALLOW_SYSTEM_CHROME=1``; by default output must not depend on
    whichever Chrome a machine happens to have.

    Raises PdfBackendUnavailable (a RuntimeError) naming the fix when no
    permitted browser can be launched.
    """
    try:
        return playwright.chromium.launch()
    except Exception as exc:  # pragma: no cover - environment-specific
        bundled_error = str(exc)
    if os.environ.get("SAJU_ALLOW_SYSTEM_CHROME") == "1":
        try:
            return playwright.chromium.launch(channel="chrome")
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
        "(or set SAJU_ALLOW_SYSTEM_CHROME=1 to allow a system Google Chrome, "
        "which may render slightly differently). "
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
        # Bundled Chromium only, unless SAJU_ALLOW_SYSTEM_CHROME=1 (see
        # _launch_browser); otherwise fail with an actionable error.
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