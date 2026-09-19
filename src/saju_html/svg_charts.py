"""SVG chart builders for the HTML/Playwright renderer.

Two charts live here:
  - `_build_element_balance_chart` — horizontal stacked bar of the five elements.
  - `_build_decade_roadmap_svg` — horizontal timeline of the 8 major-luck periods.

Both return HTML wrappers (a `<div class="... no-break">` around an `<svg>`)
so the renderer can drop them straight into the document body.

The renderer in `saju_html.renderer` calls into this module; splitting
SVG assembly away from markdown parsing keeps each file focused.
"""
from __future__ import annotations

import html
import re
from typing import List, Tuple

from saju_html import ELEMENT_COLORS, ELEMENT_EMOJI


# Color tokens used by the lifetime-decade roadmap SVG.
_DECADE_COLORS = {
    "favorable": "#27ae60",     # green
    "neutral": "#f39c12",       # amber
    "challenging": "#c0392b",   # red
}


def _build_element_balance_chart(html_table: str) -> str:
    """Build an SVG bar chart from an element-balance HTML table.

    Returns an empty string if percentages cannot be parsed reliably.
    """
    rows: list[tuple[str, float]] = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html_table, re.DOTALL):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL)
        if len(tds) < 3:
            continue
        first_cell = re.sub(r"<[^>]+>", "", tds[0]).strip()
        pct_cell = re.sub(r"<[^>]+>", "", tds[-1]).strip()
        pct_match = re.search(r"([0-9]+(?:\.[0-9]+)?)", pct_cell)
        if not pct_match:
            continue
        pct = float(pct_match.group(1))
        element = ""
        for e in ELEMENT_COLORS:
            if e in first_cell:
                element = e
                break
        if element:
            rows.append((element, pct))

    if not rows or abs(sum(p[1] for p in rows) - 100) > 15:
        return ""

    # Sort rows to a stable element order if all five are present.
    order = ["Wood", "Fire", "Earth", "Metal", "Water"]
    ordered = []
    for e in order:
        for r in rows:
            if r[0] == e:
                ordered.append(r)
                break
    if len(ordered) != len(rows):
        ordered = rows

    width = 500
    height = 120
    bar_y = 50
    bar_height = 28
    total_width = width - 20
    x = 10
    segments: list[str] = []
    for element, pct in ordered:
        seg_w = total_width * (pct / 100.0)
        color = ELEMENT_COLORS.get(element, "#888888")
        emoji = ELEMENT_EMOJI.get(element, "")
        label = f"{emoji} {element} {pct:.1f}%"
        text_x = x + seg_w / 2
        text_color = "#ffffff"
        segments.append(
            f'<rect x="{x:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_height}" '
            f'fill="{color}" rx="3"/>'
        )
        if seg_w > 40:
            segments.append(
                f'<text x="{text_x:.1f}" y="{bar_y + bar_height / 2 + 4}" '
                f'text-anchor="middle" font-size="11" fill="{text_color}" '
                f'font-family="Helvetica,Arial,sans-serif">{label}</text>'
            )
        x += seg_w

    svg = (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">\n'
        f'  <text x="10" y="30" font-size="13" font-weight="bold" '
        f'fill="#2a4d6e" font-family="Helvetica,Arial,sans-serif">'
        "Element Balance Distribution"
        "</text>\n"
        + "\n".join(f"  {s}" for s in segments)
        + "\n</svg>"
    )
    return f'<div class="element-balance-chart no-break">\n{svg}\n</div>'


def inject_element_balance_chart(html: str, style_fn) -> str:
    """Insert an SVG bar chart before the Element Balance table.

    Also color-codes the table rows via `style_fn(table_html)`.
    Only tables whose header contains Element/Presence/Percentage are treated
    as element-balance tables.
    """

    def _transform(match: re.Match) -> str:
        table = match.group(0)
        chart = _build_element_balance_chart(table)
        styled_table = style_fn(table)
        return chart + "\n" + styled_table

    def _is_balance_table(match: re.Match) -> str:
        table = match.group(0)
        header = re.search(r"<thead\b.*?</thead>", table, flags=re.DOTALL)
        header_text = header.group(0) if header else table
        if all(h in header_text for h in ("Element", "Presence", "Percentage")):
            return _transform(match)
        return table

    return re.sub(r"<table\b.*?</table>", _is_balance_table, html, flags=re.DOTALL)


def _build_decade_roadmap_svg(rows: list[tuple[str, str, str]]) -> str:
    """Render an SVG horizontal timeline of all 8 major-luck periods.

    `rows` is a list of (label, pillar, lean) tuples where `lean` ∈
    {"favorable", "neutral", "challenging"}. Returns an empty string if
    there are fewer than 2 rows.
    """
    if len(rows) < 2:
        return ""

    width = 720
    margin_x = 20
    margin_y = 16
    bar_height = 28
    label_gap = 6
    seg_gap = 4
    total_bar_y = margin_y + 18
    seg_width = (width - 2 * margin_x - seg_gap * (len(rows) - 1)) / len(rows)
    bar_total_width = seg_width * len(rows) + seg_gap * (len(rows) - 1)

    segments: list[str] = []
    for i, (_label, pillar, lean) in enumerate(rows):
        x = margin_x + i * (seg_width + seg_gap)
        color = _DECADE_COLORS.get(lean, _DECADE_COLORS["neutral"])
        segments.append(
            f'<rect x="{x:.1f}" y="{total_bar_y}" width="{seg_width:.1f}" '
            f'height="{bar_height}" fill="{color}" rx="3">'
            f'<title>{html.escape(pillar)} · {html.escape(lean)}</title>'
            "</rect>"
        )
        # Pillar label centered horizontally inside the segment.
        text_x = x + seg_width / 2
        if seg_width > 40:
            segments.append(
                f'<text x="{text_x:.1f}" y="{total_bar_y + bar_height / 2 + 4}" '
                f'text-anchor="middle" font-size="11" fill="#ffffff" '
                f'font-family="Helvetica,Arial,sans-serif">{html.escape(pillar)}</text>'
            )

    # Legend below the bar.
    legend_y = total_bar_y + bar_height + 24
    legend_items = [
        ("Favorable", _DECADE_COLORS["favorable"]),
        ("Neutral", _DECADE_COLORS["neutral"]),
        ("Challenging", _DECADE_COLORS["challenging"]),
    ]
    legend_x = margin_x
    legend_segments: list[str] = []
    for label, color in legend_items:
        legend_segments.append(
            f'<rect x="{legend_x:.1f}" y="{legend_y - 9}" width="12" height="12" '
            f'fill="{color}" rx="2"/>'
        )
        legend_segments.append(
            f'<text x="{legend_x + 18:.1f}" y="{legend_y + 1}" font-size="11" '
            f'fill="#444444" font-family="Helvetica,Arial,sans-serif">{html.escape(label)}</text>'
        )
        legend_x += 18 + 8 * len(label) + 12

    # Age range labels under each segment.
    age_labels: list[str] = []
    for i, (label, _pillar, _lean) in enumerate(rows):
        x = margin_x + i * (seg_width + seg_gap)
        text_x = x + seg_width / 2
        age_labels.append(
            f'<text x="{text_x:.1f}" y="{total_bar_y + bar_height + label_gap + 6}" '
            f'text-anchor="middle" font-size="10" fill="#666666" '
            f'font-family="Helvetica,Arial,sans-serif">{html.escape(label)}</text>'
        )

    svg = (
        f'<svg viewBox="0 0 {width} {legend_y + 18}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Lifetime decade roadmap">\n'
        f'  <text x="{margin_x}" y="{margin_y + 6}" font-size="13" '
        f'font-weight="bold" fill="#2a4d6e" '
        f'font-family="Helvetica,Arial,sans-serif">Lifetime Decade Roadmap</text>\n'
        + "\n".join(f"  {s}" for s in segments)
        + "\n"
        + "\n".join(f"  {l}" for l in age_labels)
        + "\n"
        + "\n".join(f"  {s}" for s in legend_segments)
        + "\n</svg>"
    )
    return f'<div class="decade-roadmap no-break">\n{svg}\n</div>'