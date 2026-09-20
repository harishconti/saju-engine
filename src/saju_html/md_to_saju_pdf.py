#!/usr/bin/env python3
"""
Build a clean, presentable PDF from a Saju candidate's markdown report.

Designed for the saju project. Uses reportlab + markdown-it-py.

Usage:
    python3 src/saju_html/md_to_saju_pdf.py \
        --input candidates_horoscope/reports/sruthi/sruthi-report.md \
        --output candidates_horoscope/reports/sruthi/sruthi-report.pdf \
        --title "Sruthi — Saju Reading" \
        --client "Sruthi" \
        --dob "11 December 1993" \
        --day-master "Bing (Yang Fire)"

    # Or use the wrapper which sets up PYTHONPATH for you:
    ./tools/build-pdf.sh sruthi

The script intentionally:
  - Translates Korean/Hanja to English where possible (e.g. 갑 → Gap, Yang Wood)
  - Uses English-primary labels
  - Renders tables as proper reportlab Tables
  - Uses a serif body, sans-serif headings, and a clean cover page
  - Adds a footer with page numbers and a generation date
"""

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

SRC_ROOT = Path(__file__).resolve().parent.parent
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# reportlab is a declared project dependency, so it should already be importable
# from sys.path. The only escape hatch needed is the explicit `$SAJU_SITE`
# override for non-standard installs.
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
except ImportError:
    _USER_LIB = os.environ.get("SAJU_SITE")
    if _USER_LIB and os.path.isdir(_USER_LIB) and _USER_LIB not in sys.path:
        sys.path.insert(0, _USER_LIB)
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
    except ImportError as _exc:
        raise ImportError(
            f"reportlab not importable. Tried {_USER_LIB!r} (from $SAJU_SITE). "
            f"Install it with `pip install --user --break-system-packages reportlab` "
            f"or `pip install -e .`. Underlying error: {_exc}"
        )
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.pdfbase.cidfonts import UnicodeCIDFont  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    BaseDocTemplate,
    Flowable,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from saju_engine.cli_validators import utc_offset_float  # noqa: E402
from saju_html import (  # noqa: E402
    ELEMENT_COLORS,
    ELEMENT_EMOJI,
    BRANCH_MAP,
    HANJA_MAP,
    KOR_REPL,
    STEM_MAP,
    TENGOD_MAP,
    strip_engine_drafts,
    strip_source_citations,
    translate_inline,
)


# ---------- Font registration ----------
# Helvetica lacks the Indian Rupee sign (₹) and many Unicode glyphs. We use
# DejaVu Sans as the primary typeface because it covers Latin, Greek, Cyrillic,
# the rupee symbol, and the block characters we need for the visual elements.
_DEJAVU_DIR = Path("/usr/share/fonts/truetype/dejavu")


def _register_dejavu_fonts() -> None:
    """Register DejaVu Sans faces with reportlab if they are present."""
    faces = [
        ("DejaVuSans", "DejaVuSans.ttf"),
        ("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"),
        ("DejaVuSans-Oblique", "DejaVuSans-Oblique.ttf"),
        ("DejaVuSans-BoldOblique", "DejaVuSans-BoldOblique.ttf"),
        ("DejaVuSansMono", "DejaVuSansMono.ttf"),
    ]
    for name, filename in faces:
        path = _DEJAVU_DIR / filename
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
            except Exception as exc:
                print(f"Warning: could not register font {name}: {exc}", file=sys.stderr)
        else:
            print(f"Warning: font file not found: {path}", file=sys.stderr)


_register_dejavu_fonts()


# ---------- CJK font (compat tier) ----------
# DejaVu has no Hangul/Hanja coverage, so the bilingual compat (두 분 궁합)
# report would render Korean/Hanja as "tofu" boxes. The Noto CJK OTF/TTC on
# disk is rejected by reportlab's TTFont ("postscript outlines are not
# supported"), so instead we use reportlab's built-in Korean CID font. CID
# fonts need no font file — the glyphs come from the PDF viewer's Adobe-Korea1
# CMap, which covers both Hangul and the Hanja used in Saju (丙午 辛未 甲子 …).
# We register two faces and route CJK runs to them via inline <font face=...>
# tags, leaving Latin in DejaVu so the existing visual design is preserved.
_CJK_SANS = "HYGothic-Medium"   # sans (matches the DejaVu sans body)
_CJK_SERIF = "HYSMyeongJo-Medium"  # serif (unused for now; available if needed)
_CJK_FONT = _CJK_SANS


def _register_cjk_fonts() -> None:
    for name in (_CJK_SANS, _CJK_SERIF):
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(name))
        except Exception as exc:  # pragma: no cover - environment-dependent
            print(f"Warning: could not register CID font {name}: {exc}", file=sys.stderr)


_register_cjk_fonts()


# CJK runs (Hangul syllables, compat jamo, Hanja ideographs) routed to the
# Korean CID font so they render instead of becoming tofu boxes.
_CJK_RE = re.compile(
    r"[㄰-㆏㐀-䶿一-鿿豈-﫿가-힯]+"
)


def _wrap_cjk_in_cid_font(text: str) -> str:
    """Wrap each CJK run in an inline <font> tag pointing at the Korean CID font."""
    return _CJK_RE.sub(
        lambda m: f"<font face='{_CJK_FONT}'>{m.group(0)}</font>", text
    )


# If DejaVu registration failed for any face, fall back to the built-in names.
def _font(name: str) -> str:
    """Return the registered font name, or a built-in fallback if unavailable."""
    try:
        pdfmetrics.getFont(name)
        return name
    except Exception:
        return name.replace("DejaVuSans", "Helvetica").replace("-Bold", "-Bold").replace("-Oblique", "-Oblique")

from saju_engine.premium_report import generate_premium_report  # noqa: E402


# ---------- Markdown parsing ----------

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")
# `_emphasis_` — underscore form. Word-boundary flanked so snake_case
# identifiers (day_branch_middle) are never touched.
UNDERSCORE_ITALIC_RE = re.compile(r"(?<![A-Za-z0-9_])_([^_\n]+?)_(?![A-Za-z0-9_])")
CODE_RE = re.compile(r"`([^`]+)`")
LIST_RE = re.compile(r"^\s*[-*]\s+(.+)$")
NUM_RE = re.compile(r"^\s*(\d+)\.\s+(.+)$")
HRULE_RE = re.compile(r"^---+$")


# Client-marker emojis that DejaVu cannot render and that should not reach PDF text.
_CLIENT_EMOJI_MARKERS = {"⚠️", "🟡", "✅", "🎧"}


def _strip_client_emojis(text: str) -> str:
    """Remove warning/favorable/headphone emojis that reportlab fonts lack."""
    for emoji in _CLIENT_EMOJI_MARKERS:
        text = text.replace(emoji, "")
    return text


def md_inline_to_html(text: str, tier: str | None = None) -> str:
    """Convert inline markdown to minimal HTML for reportlab Paragraph."""
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # All client-facing PDFs are English-primary. Korean/Hanja in the markdown
    # source are translated where possible and stripped otherwise, consistent
    # with the single-chart tiers.
    text = translate_inline(text)
    # DejaVu/Helvetica do not contain warning/favorable/headphone emojis.
    text = _strip_client_emojis(text)
    # Bold, italic, code
    text = BOLD_RE.sub(r"<b>\1</b>", text)
    text = ITALIC_RE.sub(r"<i>\1</i>", text)
    text = UNDERSCORE_ITALIC_RE.sub(r"<i>\1</i>", text)
    text = CODE_RE.sub(r"<font face='DejaVuSansMono'>\1</font>", text)
    return text


# ---------- Styles ----------

def make_styles():
    base = getSampleStyleSheet()
    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title", parent=base["Title"],
        fontName=_font("DejaVuSans-Bold"), fontSize=28, leading=34,
        textColor=colors.HexColor("#1a1a1a"), alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    styles["cover_subtitle"] = ParagraphStyle(
        "cover_subtitle", parent=base["Normal"],
        fontName=_font("DejaVuSans-Oblique"), fontSize=16, leading=20,
        textColor=colors.HexColor("#555555"), alignment=TA_CENTER,
        spaceAfter=6 * mm,
    )
    styles["cover_meta"] = ParagraphStyle(
        "cover_meta", parent=base["Normal"],
        fontName=_font("DejaVuSans"), fontSize=11, leading=15,
        textColor=colors.HexColor("#333333"), alignment=TA_CENTER,
    )
    styles["cover_audio"] = ParagraphStyle(
        "cover_audio", parent=base["Normal"],
        fontName=_font("DejaVuSans-Bold"), fontSize=10, leading=14,
        textColor=colors.HexColor("#8a5a00"),
        backColor=colors.HexColor("#fff7e6"),
        borderColor=colors.HexColor("#f0c674"),
        borderWidth=0.8, borderPadding=4,
        alignment=TA_CENTER, spaceBefore=2 * mm, spaceAfter=4 * mm,
    )
    styles["chart_signature"] = ParagraphStyle(
        "chart_signature", parent=base["Normal"],
        fontName=_font("DejaVuSans-Oblique"), fontSize=12, leading=17,
        textColor=colors.HexColor("#2a4d6e"),
        leftIndent=4 * mm, rightIndent=4 * mm,
        backColor=colors.HexColor("#eef5fa"),
        borderColor=colors.HexColor("#2a4d6e"),
        borderWidth=0, leftBorderWidth=2,
        borderPadding=4, spaceBefore=2 * mm, spaceAfter=4 * mm,
    )
    styles["h1"] = ParagraphStyle(
        "h1", parent=base["Heading1"],
        fontName=_font("DejaVuSans-Bold"), fontSize=18, leading=24,
        textColor=colors.HexColor("#222222"), spaceBefore=8 * mm,
        spaceAfter=4 * mm,
    )
    styles["h2"] = ParagraphStyle(
        "h2", parent=base["Heading2"],
        fontName=_font("DejaVuSans-Bold"), fontSize=14, leading=20,
        textColor=colors.HexColor("#2a4d6e"), spaceBefore=6 * mm,
        spaceAfter=3 * mm,
    )
    styles["h3"] = ParagraphStyle(
        "h3", parent=base["Heading3"],
        fontName=_font("DejaVuSans-Bold"), fontSize=12, leading=17,
        textColor=colors.HexColor("#3a5d7e"), spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    styles["h4"] = ParagraphStyle(
        "h4", parent=base["Heading4"],
        fontName=_font("DejaVuSans-Bold"), fontSize=11, leading=15,
        textColor=colors.HexColor("#444444"), spaceBefore=3 * mm,
        spaceAfter=1 * mm,
    )
    styles["body"] = ParagraphStyle(
        "body", parent=base["Normal"],
        fontName=_font("DejaVuSans"), fontSize=10, leading=14,
        textColor=colors.HexColor("#222222"), alignment=TA_LEFT,
        spaceAfter=3 * mm,
    )
    styles["bullet"] = ParagraphStyle(
        "bullet", parent=styles["body"],
        leftIndent=6 * mm, bulletIndent=0, spaceAfter=1 * mm,
    )
    styles["note"] = ParagraphStyle(
        "note", parent=styles["body"],
        fontName=_font("DejaVuSans-Oblique"), fontSize=9, leading=12,
        textColor=colors.HexColor("#666666"),
        leftIndent=4 * mm, spaceAfter=2 * mm,
    )
    styles["cell"] = ParagraphStyle(
        "cell", parent=base["Normal"],
        fontName=_font("DejaVuSans"), fontSize=8, leading=10,
        textColor=colors.HexColor("#222222"), alignment=TA_LEFT,
        spaceAfter=0, spaceBefore=0,
    )
    styles["cell_header"] = ParagraphStyle(
        "cell_header", parent=styles["cell"],
        fontName=_font("DejaVuSans-Bold"), textColor=colors.white,
    )
    styles["footer"] = ParagraphStyle(
        "footer", parent=base["Normal"],
        fontName=_font("DejaVuSans"), fontSize=8, leading=10,
        textColor=colors.HexColor("#888888"), alignment=TA_CENTER,
    )
    return styles


# ---------- Element-balance colorization for reportlab ----------

_ELEMENT_EMOJI_TO_ELEMENT = {v: k for k, v in ELEMENT_EMOJI.items()}
_ELEMENT_EMOJI_SET = set(ELEMENT_EMOJI.values())


def _replace_element_emoji_with_bullet(text: str) -> str:
    """Replace element-circle emoji with a colored bullet glyph.

    DejaVu/Helvetica do not contain color-emoji glyphs, and Noto Color Emoji
    uses the CBDT/CBLC bitmap format that reportlab's TTFont cannot load
    (`missing location table`). Instead of silently stripping the emoji, we
    map each one to a solid bullet (`●`) tinted with the element's color so
    the visual cue is preserved.
    """
    for emoji in _ELEMENT_EMOJI_SET:
        if emoji in text:
            element = _ELEMENT_EMOJI_TO_ELEMENT[emoji]
            color = ELEMENT_COLORS.get(element, "#333333")
            text = text.replace(emoji, f'<font color="{color}">●</font>')
    return text.strip()


# Kept for backward compatibility; new code should use the bullet replacement.
def _strip_element_emoji(text: str) -> str:
    """Remove element-circle emoji from table cells before reportlab layout."""
    for emoji in _ELEMENT_EMOJI_SET:
        text = text.replace(emoji, "")
    return text.strip()


def _element_from_text(text: str) -> str | None:
    """Return the element name if it appears in the cell text."""
    for element in ELEMENT_COLORS:
        if re.search(rf"\b{re.escape(element)}\b", text, re.IGNORECASE):
            return element
    return None


def _escape_html(text: str) -> str:
    """Escape HTML special characters for reportlab Paragraph text."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class ElementBarFlowable(Flowable):
    """A small horizontal bar colored by element balance percentage.

    Draws a filled rectangle whose width is proportional to the percentage,
    sitting on a light-grey background track.
    """

    def __init__(self, width: float, height: float, color: str, fill_ratio: float):
        super().__init__()
        self.width = width
        self.height = height
        self.color = colors.HexColor(color) if isinstance(color, str) else color
        self.fill_ratio = max(0.0, min(1.0, fill_ratio))

    def __repr__(self):
        return f"ElementBarFlowable({self.width:.1f}, {self.height:.1f}, {self.fill_ratio:.2f})"

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        # Light track
        self.canv.setFillColor(colors.HexColor("#e8e8e8"))
        self.canv.rect(0, 0, self.width, self.height, stroke=0, fill=1)
        # Filled portion
        if self.fill_ratio > 0:
            self.canv.setFillColor(self.color)
            self.canv.rect(0, 0, self.width * self.fill_ratio, self.height, stroke=0, fill=1)


def _parse_percentage(text: str) -> float:
    """Extract the leading numeric percentage from text like '26.1%'."""
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    return float(m.group(1)) if m else 0.0


def _colorize_element_table(cells: list[str], styles: dict, bar_width: float) -> list:
    """Render an element-balance row with colored name, visual bar, and percentage.

    Input cells: ["🔴 Fire", "██████████░░░░░░░░░░", "26.1%"]
    Output: a list containing a colored Paragraph, an ElementBarFlowable, and a
    colored Paragraph.
    """
    element = _element_from_text(cells[0])
    color = ELEMENT_COLORS.get(element) if element else None
    pct = _parse_percentage(cells[2]) if len(cells) > 2 else 0.0

    out = []
    for idx, raw in enumerate(cells):
        if color and idx == 0:
            # Element name cell: strip the emoji, color the bullet and the element name.
            text = _strip_element_emoji(raw)
            text = _escape_html(text)
            text = re.sub(
                rf"\b{re.escape(element)}\b",
                f'<font color="{color}" face="{_font("DejaVuSans-Bold")}" size="9">{element}</font>',
                text,
                flags=re.IGNORECASE,
            )
            text = f'<font color="{color}">●</font> {text}'
            out.append(Paragraph(text, styles["cell"]))
        elif color and idx == 1:
            # Replace the ASCII bar with a colored rectangle.
            bar = ElementBarFlowable(bar_width, 8, color, pct / 100.0)
            out.append(bar)
        elif color and idx == 2:
            text = _strip_element_emoji(raw)
            text = _escape_html(text)
            text = f'<font color="{color}" face="{_font("DejaVuSans-Bold")}">{text}</font>'
            out.append(Paragraph(text, styles["cell"]))
        else:
            text = _strip_element_emoji(raw)
            out.append(Paragraph(_escape_html(text), styles["cell"]))
    return out


# ---------- Page template with footer ----------

class SajuDoc(BaseDocTemplate):
    def __init__(self, filename, *, report_id: str = "", client: str = "",
                 brand: str = "CosmicSaju · cosmicsaju.com", total_pages: int = 0, **kw):
        BaseDocTemplate.__init__(self, filename, pagesize=A4,
                                 leftMargin=18 * mm, rightMargin=18 * mm,
                                 topMargin=18 * mm, bottomMargin=18 * mm,
                                 **kw)
        self.report_id = report_id
        self.client = client
        self.brand = brand
        self.total_pages = total_pages
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="normal")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=self.draw_cover_chrome),
            PageTemplate(id="normal", frames=[frame], onPage=self.draw_chrome),
        ])

    def _page_number_text(self, doc) -> str:
        if self.total_pages and self.total_pages > 0:
            return f"Page {doc.page} / {self.total_pages}"
        return f"Page {doc.page}"

    def draw_chrome(self, canvas, doc):
        canvas.saveState()
        # Footer
        canvas.setFont(_font("DejaVuSans"), 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(18 * mm, 10 * mm, f"{self.brand}")
        canvas.drawCentredString(A4[0] / 2, 10 * mm, self._page_number_text(doc))
        right_text = f"Report ID: {self.report_id}  ·  Personal & Confidential  ·  {date.today().isoformat()}"
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, right_text)
        # Top rule
        canvas.setStrokeColor(colors.HexColor("#cccccc"))
        canvas.setLineWidth(0.4)
        canvas.line(18 * mm, A4[1] - 12 * mm, A4[0] - 18 * mm, A4[1] - 12 * mm)
        canvas.restoreState()

    def draw_cover_chrome(self, canvas, doc):
        # Lighter footer on cover
        canvas.saveState()
        canvas.setFont(_font("DejaVuSans"), 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawCentredString(A4[0] / 2, 10 * mm,
                                 f"Korean Four Pillars of Destiny  ·  {self.brand}")
        canvas.restoreState()


# ---------- Markdown -> story conversion ----------

def _md_to_story(text: str, title: str, client: str, dob: str, day_master: str,
                 report_id: str, tier: str | None = None) -> list:
    """Convert stripped markdown text into a reportlab flowable story (cover + content)."""
    lines = text.splitlines()
    styles = make_styles()
    story = []

    # ---- Cover page ----
    # Translate cover-page strings so Hanja/Korean glyphs don't render as
    # "tofu" boxes (DejaVu has no CJK). md_inline_to_html also escapes XML
    # special chars, keeping the Paragraph markup valid.
    title_h = md_inline_to_html(title, tier)
    client_h = md_inline_to_html(client, tier)
    dob_h = md_inline_to_html(dob, tier)
    dm_h = md_inline_to_html(day_master, tier) if day_master else ""
    story.append(Spacer(1, 50 * mm))
    story.append(Paragraph(title_h, styles["cover_title"]))
    story.append(Paragraph("A Reading in the Korean Four Pillars Tradition", styles["cover_subtitle"]))
    story.append(Spacer(1, 25 * mm))
    story.append(Paragraph(f"<b>For</b>  {client_h}", styles["cover_meta"]))
    story.append(Paragraph(f"<b>Born</b>  {dob_h}", styles["cover_meta"]))
    if dm_h:
        story.append(Paragraph(f"<b>Day Master</b>  {dm_h}", styles["cover_meta"]))
    # Deep tier cover: confirm the MP3 audio summary is included by default.
    if tier == "deep":
        story.append(Spacer(1, 8 * mm))
        story.append(Paragraph(
            "(Audio summary included) Your MP3 audio summary is included — delivered with this report.",
            styles["cover_audio"],
        ))
    story.append(Spacer(1, 20 * mm))
    story.append(Paragraph(
        "Grounded in the Five Elements and Yin-Yang philosophy. "
        "Interpreted through classical Myeongri (Korean Saju) tradition: "
        "Jeokcheon-su, Yeonhae-japyeong, Gungtong-bogam, Myeongri-jeongjong.",
        ParagraphStyle("cover_foot", parent=styles["cover_meta"],
                       fontSize=10, textColor=colors.HexColor("#555555"),
                       leftIndent=20 * mm, rightIndent=20 * mm, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        f"Generated {date.today().strftime('%B %d, %Y')}  ·  Report ID: {report_id}",
        ParagraphStyle("cover_date", parent=styles["cover_meta"],
                       fontSize=10, textColor=colors.HexColor("#888888"))
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "CosmicSaju · cosmicsaju.com",
        ParagraphStyle("cover_brand", parent=styles["cover_meta"],
                       fontSize=10, textColor=colors.HexColor("#2a4d6e"),
                       fontName=_font("DejaVuSans-Bold"))
    ))
    story.append(PageBreak())

    # ---- Content ----
    i = 0
    skipped_title = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if HRULE_RE.match(stripped):
            story.append(Spacer(1, 2 * mm))
            i += 1
            continue

        m = HEADING_RE.match(stripped)
        if m:
            level = len(m.group(1))
            content = md_inline_to_html(m.group(2), tier)
            if level == 1 and not skipped_title:
                skipped_title = True
                i += 1
                continue
            style = styles.get(f"h{level}", styles["h4"])
            story.append(Paragraph(content, style))
            i += 1
            continue

        if TABLE_ROW_RE.match(stripped):
            tbl_lines = []
            while i < len(lines) and TABLE_ROW_RE.match(lines[i].strip()):
                tbl_lines.append(lines[i].strip())
                i += 1
            header_cells = [c.strip() for c in tbl_lines[0].strip("|").split("|")]
            data = [header_cells]
            for row_line in tbl_lines[2:]:
                cells = [c.strip() for c in row_line.strip("|").split("|")]
                data.append(cells)

            is_element_balance = header_cells[:3] == ["Element", "Presence", "Percentage"]
            header_data = [Paragraph(md_inline_to_html(c, tier), styles["cell_header"]) for c in data[0]]
            n_cols = len(header_cells)
            total_w = A4[0] - 36 * mm
            if is_element_balance:
                colWidths = [total_w * 0.22, total_w * 0.56, total_w * 0.22]
                bar_width = colWidths[1] - 6
                body_data = [_colorize_element_table(row, styles, bar_width) for row in data[1:]]
            else:
                colWidths = [total_w / n_cols] * n_cols
                body_data = [[Paragraph(md_inline_to_html(_strip_element_emoji(c), tier), styles["cell"]) for c in row] for row in data[1:]]
            data = [header_data] + body_data

            t = Table(data, colWidths=colWidths, repeatRows=1)
            table_style = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2a4d6e")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f3f6fa")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ]
            if is_element_balance:
                table_style.append(("ALIGN", (2, 1), (2, -1), "RIGHT"))
            t.setStyle(TableStyle(table_style))
            story.append(t)
            story.append(Spacer(1, 3 * mm))
            continue

        m = LIST_RE.match(line)
        if m:
            content = md_inline_to_html(m.group(1), tier)
            story.append(Paragraph(f"&bull; {content}", styles["bullet"]))
            i += 1
            continue

        m = NUM_RE.match(line)
        if m:
            num, content = m.group(1), m.group(2)
            story.append(Paragraph(f"{num}. {md_inline_to_html(content, tier)}", styles["bullet"]))
            i += 1
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if (HEADING_RE.match(nxt) or TABLE_ROW_RE.match(nxt) or
                LIST_RE.match(lines[i]) or NUM_RE.match(lines[i]) or
                HRULE_RE.match(nxt)):
                break
            para_lines.append(nxt)
            i += 1
        para = " ".join(para_lines)
        para = md_inline_to_html(para, tier)
        # Chart signature line is rendered as a pull-quote (Deep tier cover).
        if "Chart signature:" in para and "<b>Chart signature:</b>" in para:
            story.append(Paragraph(para, styles["chart_signature"]))
        else:
            story.append(Paragraph(para, styles["body"]))

    return story


# ---------- Main builder ----------

def build_pdf(input_md: Path, output_pdf: Path, title: str, client: str, dob: str,
              day_master: str, *, report_id: str = "", tier: str | None = None):
    text = strip_source_citations(input_md.read_text(encoding="utf-8"))
    text = strip_engine_drafts(text)
    # ReportLab's fonts do not contain color-emoji glyphs; strip element-circle
    # emoji globally before layout so the client PDF never shows tofu boxes.
    text = _strip_element_emoji(text)
    if not report_id:
        report_id = f"CID-{output_pdf.stem}-{date.today().strftime('%Y%m%d')}"

    # First pass: count pages on a throwaway temporary file.
    tmp_path = output_pdf.with_suffix('.tmp.pdf')
    try:
        doc1 = SajuDoc(str(tmp_path), report_id=report_id, client=client)
        doc1.build(_md_to_story(text, title, client, dob, day_master, report_id, tier=tier))
        total_pages = doc1.page
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass

    # Final pass: write the real PDF with "Page X / Y" in the footer.
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc2 = SajuDoc(str(output_pdf), report_id=report_id, client=client, total_pages=total_pages)
    doc2.build(_md_to_story(text, title, client, dob, day_master, report_id, tier=tier))
    return output_pdf


# ---------- Chart → Markdown bridge (Priority 3) ----------

# These translate Korean names from the engine into a presentable markdown
# string that matches the structure of knowledge/10-output-template.md.
# (The PDF builder below then re-translates Korean→English for layout.)

_MONTH_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}


def _format_date_dob(chart) -> str:
    """Format a Chart's birth_date as a presentable '11 December 1993' string."""
    try:
        y, m, d = chart.birth_date.split("-")
        return f"{int(d)} {_MONTH_NAME[int(m)]} {y}"
    except (ValueError, AttributeError):
        return str(chart.birth_date)


def _format_day_master(chart) -> str:
    """Return '丙 (Yang Fire)' style label from a Chart."""
    info = chart.day_master_info
    return f"{chart.day_master} ({info['element']}, {info['polarity']})"


def chart_to_markdown(chart, *, title: str = "Saju Reading") -> str:
    """Render a `Chart` object as a markdown document following
    `knowledge/10-output-template.md`.

    The output is a fully self-contained .md that build_pdf() can consume.
    Placeholders `[INTERPRET...]` are used for the prose sections that
    require human (or LLM) judgment — the engine derives structure, not prose.
    """
    dob = _format_date_dob(chart)
    dm = _format_day_master(chart)
    location = chart.city or "—"

    # Four pillars table
    rows = []
    for p in chart.pillars:
        hidden_str = ", ".join(f"{role}={s}" for role, s in p.hidden_stems) or "—"
        rows.append(f"| {p.position.capitalize()} | {p.combined} | {hidden_str} |")
    pillars_table = (
        "| Pillar | Combined | Hidden Stems |\n"
        "|---|---|---|\n"
        + "\n".join(rows)
    )

    # Ten gods table (visible stems + branch main stems)
    tg_rows = []
    for h in chart.ten_gods:
        tg_rows.append(f"| {h.position} | {h.stem} | {h.tengod} |")
    tengod_table = (
        "| Position | Stem | Ten God |\n"
        "|---|---|---|\n"
        + "\n".join(tg_rows)
    )

    # 12 stages table
    st_rows = [f"| {pos} | {br} | {st} |" for pos, br, st in chart.twelve_stages]
    stages_table = (
        "| Position | Branch | 12 Stage |\n"
        "|---|---|---|\n"
        + "\n".join(st_rows)
    )

    # Major luck table
    dl_rows = [f"| {p.start_age}–{p.end_age} | {p.combined} |" for p in chart.daeun] or ["| — | — |"]
    daeun_table = (
        "| Ages | Pillar |\n"
        "|---|---|\n"
        + "\n".join(dl_rows)
    )

    # Branch relationships
    rel_lines = []
    if chart.combinations_6:
        for a, c, elem, pa, pb in chart.combinations_6:
            rel_lines.append(f"- **{a}+{c}** (six combination) → {elem} ({pa}–{pb})")
    if chart.clashes:
        for a, c in chart.clashes:
            rel_lines.append(f"- **{a}↔{c}** (six clash)")
    if chart.three_harmonies:
        for a, b, c, elem in chart.three_harmonies:
            rel_lines.append(f"- **{a}+{b}+{c}** (three harmony) → {elem}")
    if chart.self_punishments:
        for a, _ in chart.self_punishments:
            rel_lines.append(f"- **{a}{a}** (self-punishment)")
    rel_md = "\n".join(rel_lines) if rel_lines else "_None found in natal._"

    md = f"""# {title}

_Base natal reading — engine-derived (manual prose pending)._

**Name:** {chart.name or '—'}
**Gender:** {chart.gender or '—'}
**Born:** {dob}, {chart.birth_time} ({location})
**Day Master:** {dm}

## Four Pillars (사주, 四柱)

{pillars_table}

## Day Master Strength (일간 강약)

[INTERPRET: argue from seasonal + branch support, per knowledge/09-interpretation-method.md step 2.]

## Ten Gods Distribution (십신, 十神)

The following 십신 are present in the natal chart, derived from the visible stems
and each branch's hidden stems (지장간):

{tengod_table}

[INTERPRET: summarize which classes dominate and what that implies for personality, career, relationships — per knowledge/05-ten-gods.md.]

## Twelve Life Stages (12운성, 十二運星)

{stages_table}

[INTERPRET: highlight the Day Master's stage in the month branch — this is the primary seasonal-strength signal. See knowledge/06-twelve-stages.md.]

## Favorable Element (용신, 用神)

[INTERPRET: derive from Day Master strength + chart balance, per knowledge/09-interpretation-method.md step 2 + knowledge/03-five-elements.md §용신.]

## Branch Relationships (합 · 충 · 형)

{rel_md}

## Major Luck Periods (대운, 大運)

{daeun_table}

[INTERPRET: which 대운 is current, what it activates, what theme it brings. See knowledge/08-luck-pillars.md.]

## Annual Luck (세운) — Current Year

[INTERPRET: 2026 is 丙午 (Yang Fire) per knowledge/08-luck-pillars.md Part 6. Check annual stem/branch against natal pillars for activation.]

## Career & Life Direction

[INTERPRET: derive from 십신 distribution + 용신 + 12 stages, per knowledge/05-ten-gods.md § Ten Gods in Detail and the interpretation procedure in knowledge/09-interpretation-method.md.]

## Relationships & Marriage

[INTERPRET: read 일지 (day branch) as 배우자궁, check 용신 vs 일지, look for 합/충 in spouse palace. Per knowledge/05-ten-gods.md and knowledge/02-branches.md §Branch Six Combinations.]

## Health Tendencies

[INTERPRET: from element balance + Day Master strength + the body-organ correspondences in knowledge/03-five-elements.md. Tendencies only — not medical advice.]

## Closing

[INTERPRET: synthesize the chart. Per CLAUDE.md ground rules: phrase all readings as potentials, not predictions. Use inclusive, respectful language.]
"""
    return md


def _slugify(name: str) -> str:
    """Create a lowercase, hyphenated slug from a full name."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def build_pdf_from_chart(chart, output_pdf: Path, *, title: str = "Saju Reading",
                         client: str = "", dob: str = "", day_master: str = "",
                         overwrite_report: bool = False, tier: Optional[str] = None,
                         report_id: str = ""):
    """Render a Chart object directly to a PDF, without a markdown intermediate.

    Internally calls chart_to_markdown() or generate_premium_report() then
    build_pdf(). The output PDF sits next to the candidate's .md report in the
    same folder.

    By default the auto-generated markdown is written to ``{name}-engine.md``
    so it does not overwrite a hand-written ``{name}-report.md``. Pass
    ``overwrite_report=True`` to write to the report filename instead.

    If ``tier`` is given (sample/essential/deep or spark/reading/fullmap), the
    premium report generator is used instead of the legacy chart_to_markdown()
    template.
    """
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Derive defaults from the chart if the caller didn't pass them
    if not client:
        client = chart.name or ""
    if not dob:
        dob = _format_date_dob(chart)
    if not day_master:
        day_master = _format_day_master(chart)

    # Write the intermediate markdown to a sibling file unless the caller
    # explicitly wants to overwrite the hand-written report.
    if overwrite_report:
        md_path = output_pdf.with_suffix(".md")
    else:
        md_path = output_pdf.with_name(output_pdf.stem.replace("-report", "-engine") + ".md")
        if md_path.name == output_pdf.with_suffix(".md").name:
            # Fallback if the PDF path does not contain '-report'.
            md_path = output_pdf.with_name(output_pdf.stem + "-engine.md")

    if tier:
        md_text = generate_premium_report(chart, tier=tier, generation_date=None)
    else:
        md_text = chart_to_markdown(chart, title=title)
    md_path.write_text(md_text, encoding="utf-8")

    if not report_id:
        slug = _slugify(client or chart.name or output_pdf.stem)
        tier_label = (tier or "").upper()
        report_id = f"CID-{slug}-{date.today().strftime('%Y%m%d')}-{tier_label}"
    # Render
    return build_pdf(md_path, output_pdf, title, client, dob, day_master, report_id=report_id, tier=tier)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, help="Path to the source .md file (mode 1).")
    ap.add_argument("--output", required=True, type=Path, help="Path to write the PDF.")
    ap.add_argument("--title", default="Saju Reading")
    ap.add_argument("--client", default="")
    ap.add_argument("--dob", default="")
    ap.add_argument("--day-master", default="")
    # Chart-input mode (Priority 3): --from-chart with a single date set
    ap.add_argument("--from-chart", action="store_true",
                    help="Build PDF from a Chart computed by the engine (provide --birth-* flags).")
    ap.add_argument("--name", default="")
    ap.add_argument("--gender", choices=["M", "F"], default=None)
    ap.add_argument("--birth-year", type=int)
    ap.add_argument("--birth-month", type=int)
    ap.add_argument("--birth-day", type=int)
    ap.add_argument("--birth-hour", type=int)
    ap.add_argument("--birth-minute", type=int, default=0)
    ap.add_argument("--city", default="")
    ap.add_argument("--longitude", type=float, default=None)
    ap.add_argument("--utc-offset", type=utc_offset_float, default=9.0)
    ap.add_argument("--no-solar-time", dest="use_solar_time", action="store_false", default=True,
                    help="Disable true solar-time correction (enabled by default).")
    ap.add_argument("--convention", choices=["korean", "chinese"], default="korean",
                    help="Korean (야자시, default) or Chinese (조자시) Zi-hour convention.")
    # Legacy aliases kept for backward compatibility.
    ap.add_argument("--korean-yazi", action="store_true", default=None,
                    help="Deprecated alias for --convention korean.")
    ap.add_argument("--no-korean-yazi", dest="korean_yazi", action="store_false")
    ap.add_argument("--overwrite-report", action="store_true",
                    help="When using --from-chart, write the markdown to {name}-report.md instead of {name}-engine.md.")
    ap.add_argument("--tier", choices=["sample", "essential", "deep", "spark", "reading", "fullmap"], default=None,
                    help="Premium report tier. With --from-chart it selects generated sections; "
                         "with an existing .md it only affects cover-page styling and translation.")
    ap.add_argument("--report-id", default="",
                    help="Unique report ID for cover/footer branding (auto-derived if omitted).")
    args = ap.parse_args()

    if args.from_chart:
        # Mode 2: engine → markdown → PDF
        if not all([args.birth_year, args.birth_month, args.birth_day,
                    args.birth_hour is not None]):
            ap.error("--from-chart requires --birth-year, --birth-month, --birth-day, --birth-hour")
        from saju_engine.engine import compute_chart  # local import: keep core script lean
        convention = args.convention
        if args.korean_yazi is not None:
            convention = "korean" if args.korean_yazi else "chinese"
        chart = compute_chart(
            name=args.name or None,
            gender=args.gender,
            year=args.birth_year, month=args.birth_month, day=args.birth_day,
            hour=args.birth_hour, minute=args.birth_minute,
            city=args.city or None, longitude=args.longitude,
            utc_offset=args.utc_offset,
            use_solar_time=args.use_solar_time,
            convention=convention,
        )
        out = build_pdf_from_chart(
            chart, args.output,
            title=args.title, client=args.client, dob=args.dob, day_master=args.day_master,
            overwrite_report=args.overwrite_report, tier=args.tier, report_id=args.report_id,
        )
        print(f"Wrote {out} ({out.stat().st_size} bytes) [from-chart mode]")
    else:
        # Mode 1: existing .md → PDF
        if not args.input:
            ap.error("--input is required (or pass --from-chart with birth data)")
        out = build_pdf(
            args.input, args.output, args.title, args.client, args.dob, args.day_master,
            report_id=args.report_id, tier=args.tier,
        )
        print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
