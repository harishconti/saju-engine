"""Section wrappers for the HTML/Playwright renderer.

Each `_wrap_*` function finds a markdown-rendered section by its heading and
re-styles it as a styled card / callout / grid. The markdown-it parser
emits clean HTML for each section, so these wrappers work on the rendered
output (post-`markdown_to_html`).

Chart-style wrappers (e.g. `_wrap_decade_roadmap`) compose with the SVG
builders in `saju_html.svg_charts`.
"""
from __future__ import annotations

import re

from saju_html.svg_charts import _build_decade_roadmap_svg


def _section_bounds(html: str, heading_re: str) -> tuple[int, int] | None:
    """Return (start, end) indices of a section headed by `heading_re`.

    `heading_re` must capture the heading tag/level in group 1 and the heading
    text in group 2, e.g. r"<(h[23])\b[^>]*>(Quick Reference)</\1>".

    The section runs from the matched heading through the content before the
    next heading of the same or higher rank.
    """
    match = re.search(heading_re, html, re.IGNORECASE)
    if not match:
        return None
    start = match.start()
    rank = int(match.group(1)[1:])
    # Find next heading of same or higher rank (smaller number = higher rank).
    next_match = re.search(rf"<h([1-{rank}])\b", html[match.end() :], re.IGNORECASE)
    end = match.end() + next_match.start() if next_match else len(html)
    return start, end


def _wrap_quick_ref(html: str) -> str:
    """Style the Quick Reference section as a card."""
    bounds = _section_bounds(html, r"<(h[23])\b[^>]*>(Quick Reference)</\1>")
    if not bounds:
        return html
    start, end = bounds
    section = html[start:end]
    wrapped = f'<div class="quick-ref-card">\n{section}\n</div>'
    return html[:start] + wrapped + html[end:]


def _wrap_right_now(html: str) -> str:
    """Style the 'What This Year Means for You' callout."""
    bounds = _section_bounds(
        html, r"<(h3)\b[^>]*>(What This Year Means for You)</\1>"
    )
    if not bounds:
        return html
    start, end = bounds
    section = html[start:end]
    wrapped = f'<div class="right-now-callout">\n{section}\n</div>'
    return html[:start] + wrapped + html[end:]


def _parse_lucky_list(section_html: str) -> str:
    """Transform a Lucky Attributes bullet list into a grid of attribute cards."""
    # Extract the first <ul> in the section.
    list_match = re.search(r"<ul>(.*?)</ul>", section_html, re.DOTALL)
    if not list_match:
        return section_html

    items_html = list_match.group(1)
    # Split on <li> ... </li>
    li_parts = re.findall(r"<li>(.*?)</li>", items_html, re.DOTALL)
    if not li_parts:
        return section_html

    cards: list[str] = []
    for item in li_parts:
        item = item.strip()
        # Label is text before the first ':' or the first <strong> content.
        label = ""
        value = item
        strong_match = re.search(r"<strong>(.*?)</strong>", item)
        if strong_match:
            label = strong_match.group(1).strip()
            value = re.sub(r"<strong>.*?</strong>", "", item, count=1).strip()
            value = re.sub(r"^\s*:?\s*", "", value)
        elif ":" in item:
            label, value = item.split(":", 1)
            label = re.sub(r"<[^>]+>", "", label).strip()
            value = value.strip()
        else:
            label = "Attribute"

        # Render markdown-ish bold inside value as HTML if needed (already HTML).
        cards.append(
            '<div class="lucky-attribute-item">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            "</div>"
        )

    grid = '<div class="lucky-attributes">\n' + "\n".join(cards) + "\n</div>"
    # Replace the original <ul> block with the grid, keeping the heading.
    return section_html.replace(list_match.group(0), grid)


def _wrap_lucky_attributes(html: str) -> str:
    """Style the Lucky Attributes section as a reference-card grid."""
    bounds = _section_bounds(html, r"<(h[23])\b[^>]*>(Lucky Attributes.*?)<\/\1>")
    if not bounds:
        return html
    start, end = bounds
    section = html[start:end]
    styled = _parse_lucky_list(section)
    return html[:start] + styled + html[end:]


def _wrap_decade_roadmap(html: str) -> str:
    """Replace the Lifetime Decade Roadmap markdown table with an SVG.

    The engine emits a table wrapped in HTML comments
    `<!-- decade-roadmap:start -->` / `<!-- decade-roadmap:end -->`.
    """
    start_match = re.search(
        r"<!--\s*decade-roadmap:start\s*-->", html, re.IGNORECASE
    )
    end_match = re.search(r"<!--\s*decade-roadmap:end\s*-->", html, re.IGNORECASE)
    if not start_match or not end_match or end_match.start() < start_match.end():
        return html
    # Extract the table content between the markers.
    inner_start = start_match.end()
    inner_end = end_match.start()
    inner = html[inner_start:inner_end]
    table_match = re.search(r"<table\b.*?</table>", inner, re.DOTALL)
    if not table_match:
        return html
    table = table_match.group(0)
    rows: list[tuple[str, str, str]] = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
        if len(tds) < 4:
            continue
        ages = re.sub(r"<[^>]+>", "", tds[0]).strip()
        pillar = re.sub(r"<[^>]+>", "", tds[1]).strip()
        lean = re.sub(r"<[^>]+>", "", tds[3]).strip().lower()
        if not ages or not pillar:
            continue
        rows.append((ages, pillar, lean))
    svg = _build_decade_roadmap_svg(rows)
    if not svg:
        return html
    replacement = (
        f"<!-- decade-roadmap:start -->\n{svg}\n<!-- decade-roadmap:end -->"
    )
    return html[: start_match.start()] + replacement + html[end_match.end():]


def _wrap_chart_signature(html: str) -> str:
    """Style the Chart Signature blockquote as a pull-quote (Deep tier).

    Detects the first <blockquote> immediately after a Quick Reference card
    and applies the `chart-signature` class.
    """
    # Find the first blockquote — that is the chart signature on the cover.
    match = re.search(r"<blockquote\b[^>]*>", html, re.IGNORECASE)
    if not match:
        return html
    return html[: match.start()] + match.group(0).replace(
        "<blockquote", '<blockquote class="chart-signature"', 1
    ) + html[match.end():]


def _wrap_audio_included(html: str) -> str:
    """Style the Deep-tier '🎧 Your MP3 audio summary is included' callout."""
    pattern = re.compile(
        r"<p>\s*🎧\s*<strong>Your MP3 audio summary is included[^<]*</strong>\s*</p>",
        re.IGNORECASE,
    )
    return pattern.sub(
        '<div class="audio-included">🎧 Your MP3 audio summary is included — '
        "delivered with this report.</div>",
        html,
    )


def _wrap_partner_upsell(html: str) -> str:
    """Wrap the Partner Chart Add-On paragraph in an accent box."""
    # Match the heading and following italic line as a unit.
    pattern = re.compile(
        r"<h4>Partner Chart Add-On</h4>\s*<p>\s*<em>([^<]+)</em>\s*</p>",
        re.IGNORECASE,
    )
    return pattern.sub(
        r'<h4>Partner Chart Add-On</h4>\n'
        r'<div class="partner-compat-upsell">'
        r"<em>\1</em></div>",
        html,
    )