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
import hashlib
import os
import re
import sys
from datetime import date
from html import unescape as _unescape_html
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
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
except ImportError:
    _USER_LIB = os.environ.get("SAJU_SITE")
    if _USER_LIB and os.path.isdir(_USER_LIB) and _USER_LIB not in sys.path:
        sys.path.insert(0, _USER_LIB)
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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

from saju_engine.report_data import AUDIO_COVER_CALLOUT  # noqa: E402
from saju_html.chart_input import (  # noqa: E402,F401
    TIER_CHOICES,
    _format_date_dob,
    _format_day_master,
    _slugify,
    add_chart_args,
    chart_from_args,
    prepare_chart_render,
)
from saju_html import (  # noqa: E402
    ELEMENT_COLORS,
    ELEMENT_EMOJI,
    strip_engine_drafts,
    strip_source_citations,
    translate_inline,
)


# ---------- Font registration ----------
# Helvetica lacks the Indian Rupee sign (₹) and many Unicode glyphs. We use
# DejaVu Sans as the primary typeface because it covers Latin, Greek, Cyrillic,
# the rupee symbol, and the block characters we need for the visual elements.
# E1: the engine must render inside a serverless function, where
# /usr/share/fonts does not exist. Resolution order:
#   1. $SAJU_FONT_DIR                     — explicit; used by the report-engine service
#   2. <this package>/fonts/              — faces bundled with the repository
#   3. /usr/share/fonts/truetype/dejavu   — the system copy on a normal Linux box
_DEJAVU_FACE_FILES = [
    ("DejaVuSans", "DejaVuSans.ttf"),
    ("DejaVuSans-Bold", "DejaVuSans-Bold.ttf"),
    ("DejaVuSans-Oblique", "DejaVuSans-Oblique.ttf"),
    ("DejaVuSans-BoldOblique", "DejaVuSans-BoldOblique.ttf"),
    ("DejaVuSansMono", "DejaVuSansMono.ttf"),
]

_DEJAVU_CANDIDATES = [
    Path(os.environ["SAJU_FONT_DIR"]) if os.environ.get("SAJU_FONT_DIR") else None,
    Path(__file__).resolve().parent / "fonts",
    Path("/usr/share/fonts/truetype/dejavu"),
]


def _resolve_dejavu_dir() -> Optional[Path]:
    """First candidate directory that actually holds the DejaVu Sans face."""
    for candidate in _DEJAVU_CANDIDATES:
        if candidate and (candidate / "DejaVuSans.ttf").exists():
            return candidate
    return None


_DEJAVU_DIR = _resolve_dejavu_dir()


def _register_dejavu_fonts() -> None:
    """Register DejaVu Sans faces with reportlab if they are present.

    A missing directory is a warning rather than an error: reportlab then falls back to
    its built-in fonts, which still render Latin text. The warning names every location
    that was searched, so a serverless log makes the cause obvious instead of showing a
    bare "font file not found".
    """
    if _DEJAVU_DIR is None:
        searched = ", ".join(str(c) for c in _DEJAVU_CANDIDATES if c)
        print(
            f"Warning: DejaVu fonts not found in any of: {searched}. "
            "Falling back to reportlab's built-in fonts. Set SAJU_FONT_DIR to override.",
            file=sys.stderr,
        )
        return
    for name, filename in _DEJAVU_FACE_FILES:
        path = _DEJAVU_DIR / filename
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(path)))
            except Exception as exc:
                print(f"Warning: could not register font {name}: {exc}", file=sys.stderr)
        else:
            print(f"Warning: font file not found: {path}", file=sys.stderr)


_register_dejavu_fonts()


# ---------- CJK font (Hangul + Hanja) ----------
# DejaVu has no Hangul/Hanja coverage, so CJK that survives translation (pillar
# Hanja, star names, glossary terms the maps do not cover) used to be dropped
# from the client PDF entirely. We now keep it and draw it with a *bundled*
# face: a glyph-subset of Noto Sans KR (OFL — see fonts/LICENSE-NotoSansKR.txt)
# trimmed to the codepoints the reports actually use, ~195 KB per face instead
# of the 10 MB original. It is embedded, so Hangul/Hanja render in every reader,
# Chrome's PDF viewer and phone viewers included. reportlab's built-in Korean
# CID faces are *not* embedded — their glyphs come from the reader's
# Adobe-Korea1 CMaps, which browsers do not ship — so they are only a
# last-resort fallback when the bundled file is missing (a stripped install).
_CJK_SANS = "SajuCJK"             # sans, matches the DejaVu sans body
_CJK_SANS_BOLD = "SajuCJK-Bold"
_CJK_SERIF = "HYSMyeongJo-Medium"  # legacy CID serif; fallback only
_CJK_FONT = _CJK_SANS
_CJK_FACE_FILES = ((_CJK_SANS, "SajuCJK-Regular.ttf"),
                   (_CJK_SANS_BOLD, "SajuCJK-Bold.ttf"))
# Codepoints the bundled face can actually draw, filled in at registration. Used
# to drop the few characters no Korean face covers rather than print a tofu box.
_CJK_COVERED: set = set()
_CJK_DROP_WARNED: set = set()


def _register_cjk_fonts() -> None:
    """Register the bundled Hangul/Hanja faces; fall back to CID fonts if absent."""
    global _CJK_COVERED
    registered = False
    for name, filename in _CJK_FACE_FILES:
        for candidate in _DEJAVU_CANDIDATES:
            path = candidate / filename if candidate else None
            if path and path.exists():
                try:
                    pdfmetrics.registerFont(TTFont(name, str(path)))
                    registered = True
                    if name == _CJK_SANS:
                        _CJK_COVERED = set(pdfmetrics.getFont(name).face.charToGlyph)
                except Exception as exc:  # pragma: no cover - environment-dependent
                    print(f"Warning: could not register CJK font {name}: {exc}", file=sys.stderr)
                break
    if registered:
        # A family lets <b> inside a CJK run pick the bold face rather than
        # synthesising one, so Hanja inside **bold** keeps its weight.
        try:
            pdfmetrics.registerFontFamily(
                _CJK_SANS, normal=_CJK_SANS, bold=_CJK_SANS_BOLD,
                italic=_CJK_SANS, boldItalic=_CJK_SANS_BOLD,
            )
        except Exception:  # pragma: no cover - environment-dependent
            pass
        return
    for name in (_CJK_SANS, _CJK_SERIF):
        try:
            pdfmetrics.registerFont(UnicodeCIDFont(name))
        except Exception as exc:  # pragma: no cover - environment-dependent
            print(f"Warning: could not register CID font {name}: {exc}", file=sys.stderr)


_register_cjk_fonts()


# CJK runs (Hangul syllables, compat jamo, Hanja ideographs). `_CJK_RE` routes
# surviving CJK to the bundled face here; the HTML backend uses it for
# translation. Kept identical to the pattern in `saju_html/__init__`.
_CJK_RE = re.compile(
    r"[㄰-㆏㐀-䶿一-鿿豈-﫿가-힯]+"
)


# If DejaVu registration failed for any face, fall back to the built-in names.
def _font(name: str) -> str:
    """Return the registered font name, or a built-in fallback if unavailable."""
    try:
        pdfmetrics.getFont(name)
        return name
    except Exception:
        return name.replace("DejaVuSans", "Helvetica")



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
# Markdown blockquote. The reports use `>` for reader notes ("Almanac caveat:",
# "In plain words:") — 16 of them in the Deep tier. Without this the marker was
# printed literally, so the client saw "> Methodology: ..." in the PDF body.
BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")
TOC_HEADING_RE = re.compile(r"^table of contents$", re.IGNORECASE)


def _toc_key(text: str) -> str:
    """Lookup key for a heading or TOC entry: markup- and whitespace-insensitive.

    The two sides of a TOC link are written differently in the source (a heading
    line vs. a bullet), so compare them on the plain text only.
    """
    plain = re.sub(r"[*`_#]", "", text or "")
    return re.sub(r"\s+", " ", plain).strip().casefold()


def _anchor_key(text: str) -> str:
    """Deterministic PDF anchor for a heading, stable across both build passes.

    Deriving it from the title text (not a counter) means the contents page built
    in pass 2 can name a destination that pass 1 already wrote, without either
    pass having to know the other's flowable order. Tags are stripped and
    entities unescaped first, because the two callers see the same title in
    different shapes: reportlab gives the drawn heading's plain text, while the
    contents entries are still inline-markdown-converted HTML.
    """
    plain = _unescape_html(re.sub(r"<[^>]+>", "", text or ""))
    return "saju-" + hashlib.md5(_toc_key(plain).encode("utf-8")).hexdigest()[:12]


# Client-marker emojis that DejaVu cannot render and that should not reach PDF text.
_CLIENT_EMOJI_MARKERS = {"⚠️", "🟡", "✅", "🎧"}


def _strip_client_emojis(text: str) -> str:
    """Remove warning/favorable/headphone emojis that reportlab fonts lack."""
    for emoji in _CLIENT_EMOJI_MARKERS:
        text = text.replace(emoji, "")
    return text


def _cjk_span(match, face: str) -> str:
    """Wrap one CJK run in a <font> tag, dropping characters the face cannot draw.

    A missing glyph is printed by reportlab as a tofu box, which is worse in a
    paid report than an omitted character: the reader cannot tell a box from a
    typo. The bundled Korean face has no simplified-Chinese forms, and the CJK
    routing patterns themselves contain range-boundary ideographs, so this is a
    real case. Each drop is reported once on stderr so it is diagnosable.
    """
    run = match.group(0)
    if _CJK_COVERED:
        kept = "".join(ch for ch in run if ord(ch) in _CJK_COVERED)
        dropped = {ch for ch in run if ch not in kept}
        if dropped:
            new = dropped - _CJK_DROP_WARNED
            if new:
                _CJK_DROP_WARNED.update(new)
                print(
                    "Warning: bundled CJK font cannot draw "
                    + " ".join(f"U+{ord(ch):04X}" for ch in sorted(new))
                    + "; dropped rather than shown as a tofu box.",
                    file=sys.stderr,
                )
        run = kept
    return f"<font face='{face}'>{run}</font>" if run else ""


def _wrap_cjk_font(text: str) -> str:
    """Route CJK runs in already-converted inline HTML to the bundled CJK face.

    Called *after* translation: whatever CJK is left is text the maps could not
    translate and that must still be drawn (pillar and star Hanja, glossary
    terms, Korean a reviewer typed into the review console). Latin around it stays
    in DejaVu, so the existing design — and the golden HTML rendered by the other
    backend — is unchanged. Runs inside a bold span are wrapped in the bold face
    first; the pass after that nests a regular tag around them, and reportlab lets
    the inner tag win, so bold stays bold.
    """
    if not text or not _CJK_RE.search(text):
        return text
    text = re.sub(
        r"<b>(.*?)</b>",
        lambda m: "<b>" + _CJK_RE.sub(
            lambda mm: _cjk_span(mm, _CJK_SANS_BOLD), m.group(1)) + "</b>",
        text,
        flags=re.S,
    )
    return _CJK_RE.sub(lambda m: _cjk_span(m, _CJK_SANS), text)


def md_inline_to_html(text: str, tier: str | None = None) -> str:
    """Convert inline markdown to minimal HTML for reportlab Paragraph."""
    # Escape HTML
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # All client-facing PDFs are English-primary, but CJK the translation maps
    # cannot reach is *kept*, never dropped: the bundled Noto Sans KR subset
    # renders it (see the CJK block above), and the Hanja of pillar and star
    # names is part of the reading, not noise.
    unmapped: set = set()
    # `gloss=True`: the owner's convention for client PDFs is English with the
    # Hanja beside it ("Direct Officer (正官)"), so the term the reading is about
    # stays visible. The bundled CJK font draws it.
    text = translate_inline(text, keep_unmapped=True, unmapped=unmapped, gloss=True)
    # DejaVu/Helvetica do not contain warning/favorable/headphone emojis.
    text = _strip_client_emojis(text)
    # Bold, italic, code
    text = BOLD_RE.sub(r"<b>\1</b>", text)
    text = ITALIC_RE.sub(r"<i>\1</i>", text)
    text = UNDERSCORE_ITALIC_RE.sub(r"<i>\1</i>", text)
    text = CODE_RE.sub(r"<font face='DejaVuSansMono'>\1</font>", text)
    # Finally, point the surviving CJK at the bundled Hangul/Hanja face.
    text = _wrap_cjk_font(text)
    # A gloss whose characters the face cannot draw leaves an empty "()" behind
    # (the pair is kept verbatim by the translator, then emptied here). Drop it so
    # the reader never sees "Seven Killings ()".
    return re.sub(r"\(\s*\)", "", text)


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
    # Contents list: the page number sits in its own narrow right-aligned column
    # so the row height cannot change between the pass that measures and the pass
    # that prints, which is what keeps the printed numbers exact.
    styles["toc_entry"] = ParagraphStyle(
        "toc_entry", parent=styles["body"],
        fontSize=10, leading=14, spaceAfter=0, spaceBefore=0,
    )
    styles["toc_page"] = ParagraphStyle(
        "toc_page", parent=styles["body"],
        fontSize=9, leading=14, alignment=TA_RIGHT,
        textColor=colors.HexColor("#555555"), spaceAfter=0, spaceBefore=0,
    )
    return styles


# ---------- Element-balance colorization for reportlab ----------

_ELEMENT_EMOJI_TO_ELEMENT = {v: k for k, v in ELEMENT_EMOJI.items()}
_ELEMENT_EMOJI_SET = set(ELEMENT_EMOJI.values())


# Element emoji are stripped before reportlab layout (no colour-emoji font support).
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
                 brand: str = "CosmicSaju · cosmicsaju.com", total_pages: int = 0,
                 doc_title: str = "", doc_author: str = "", **kw):
        BaseDocTemplate.__init__(self, filename, pagesize=A4,
                                 leftMargin=18 * mm, rightMargin=18 * mm,
                                 topMargin=18 * mm, bottomMargin=18 * mm,
                                 **kw)
        self.report_id = report_id
        self.client = client
        self.brand = brand
        self.total_pages = total_pages
        self.doc_title = doc_title or "Saju Reading"
        self.doc_author = doc_author or brand
        # Heading title -> page number of its first occurrence, and the anchors
        # already written, so the outline and the TOC agree between passes.
        self.heading_pages: dict = {}
        self._bookmarked: set = set()
        self._heading_count = 0
        frame = Frame(self.leftMargin, self.bottomMargin,
                      self.width, self.height, id="normal")
        self.addPageTemplates([
            PageTemplate(id="cover", frames=[frame], onPage=self.draw_cover_chrome),
            PageTemplate(id="normal", frames=[frame], onPage=self.draw_chrome),
        ])

    def handle_documentBegin(self):
        # Document properties: without these a premium PDF reports itself as
        # anonymous ("Title: (anonymous)") in every reader's window and tab.
        try:
            self.canv.setTitle(self.doc_title)
            self.canv.setAuthor(self.doc_author)
            self.canv.setSubject("Korean Four Pillars (Saju) reading")
            self.canv.setCreator("CosmicSaju report engine · cosmicsaju.com")
        except Exception:  # pragma: no cover - canvas metadata is best-effort
            pass
        BaseDocTemplate.handle_documentBegin(self)

    def afterFlowable(self, flowable):
        """Bookmark each heading, build the outline, and record its page.

        reportlab calls this right after a flowable is drawn, which is the only
        point where the current page number and canvas are both known. The page
        recorded here is what the contents page prints.
        """
        if not isinstance(flowable, Paragraph):
            return
        style_name = getattr(getattr(flowable, "style", None), "name", "") or ""
        m = re.fullmatch(r"h([1-6])", style_name)
        if not m:
            return
        title = flowable.getPlainText().strip()
        if not title:
            return
        self._heading_count += 1
        base_key = _anchor_key(title)
        key = base_key
        if key in self._bookmarked:
            # A repeated title (e.g. a section reopened later) gets its own
            # destination, but the contents entry keeps pointing at the first.
            key = f"{base_key}-{self._heading_count}"
        else:
            self._bookmarked.add(key)
            self.heading_pages.setdefault(_toc_key(title), self.page)
        self.canv.bookmarkPage(key)
        level = {1: 0, 2: 0, 3: 1}.get(int(m.group(1)), 2)
        try:
            self.canv.addOutlineEntry(title, key, level=level, closed=False)
        except Exception:  # pragma: no cover - outline is best-effort
            pass

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
        # The cover is deliberately chrome-free: brand, date and report ID are
        # already part of the cover layout, so a running footer there only
        # repeats them. Page numbering starts on the contents page.
        pass


# ---------- Markdown -> story conversion ----------

def _heading_anchor_map(lines, tier) -> dict:
    """Map every heading anchor to its lookup key, for the contents page.

    Scanned from the same source the story is built from, using the same
    conversion as the drawn heading, so the anchors here are exactly the ones
    ``SajuDoc.afterFlowable`` will write.
    """
    keys: dict = {}
    skipped_title = False
    for line in lines:
        m = HEADING_RE.match(line.strip())
        if not m:
            continue
        if len(m.group(1)) == 1 and not skipped_title:
            skipped_title = True
            continue
        plain = _unescape_html(re.sub(r"<[^>]+>", "", md_inline_to_html(m.group(2), tier)))
        keys[_anchor_key(plain)] = _toc_key(plain)
    return keys


def _resolve_toc_anchor(entry_key: str, heading_keys: dict) -> Optional[str]:
    """Find the heading a contents entry points at, by its lookup key.

    Contents labels are not always literal headings: the engine writes composite
    ones ("Life Themes by Major Luck Period — incl. Lifetime Decade Roadmap" for
    the heading "Life Themes by Major Luck Period") and sometimes the heading
    carries extra words ("MP3 Audio Summary — Included by Default"). So beyond an
    exact match, accept the closest prefix in either direction and otherwise
    return None, which leaves the entry as plain text. A contents page must never
    ship a link to nowhere.
    """
    if not entry_key:
        return None
    lookup_keys = {anchor: key for anchor, key in heading_keys.items()}
    for anchor, key in lookup_keys.items():
        if key == entry_key:
            return anchor
    best = None
    for anchor, key in lookup_keys.items():
        if key.startswith(entry_key) or entry_key.startswith(key):
            distance = abs(len(key) - len(entry_key))
            if best is None or distance < best[0]:
                best = (distance, anchor)
    return best[1] if best else None


def _toc_flowables(entries, toc_pages, styles, tier, content_width, heading_keys=None) -> list:
    """Render the markdown contents list as a linked table of titles + pages.

    Two columns rather than a run of bullets: the page number needs its own cell
    so the row height is the same whether or not a number has been measured yet.
    That is what lets pass 1 (measuring) and pass 2 (printing) lay the pages out
    identically, and therefore what makes the printed numbers exact.
    """
    heading_keys = heading_keys or {}
    rows = []
    for entry in entries:
        label = md_inline_to_html(entry, tier)
        plain = _unescape_html(re.sub(r"<[^>]+>", "", label))
        anchor = _resolve_toc_anchor(_toc_key(plain), heading_keys)
        if anchor:
            page = toc_pages.get(heading_keys.get(anchor, ""), "")
            title_cell = f"&bull;&nbsp; <a href='#{anchor}' color='#2a4d6e'>{label}</a>"
        else:
            page = ""
            title_cell = f"&bull;&nbsp; {label}"
        rows.append([
            Paragraph(title_cell, styles["toc_entry"]),
            Paragraph(str(page), styles["toc_page"]),
        ])
    if not rows:
        return []
    table = Table(rows, colWidths=[content_width - 14 * mm, 14 * mm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2),
    ]))
    return [table, Spacer(1, 4 * mm)]


def _md_to_story(text: str, title: str, client: str, dob: str, day_master: str,
                 report_id: str, tier: str | None = None,
                 toc_pages: dict | None = None) -> list:
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
            f"(Audio summary included) {AUDIO_COVER_CALLOUT}",
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
    # Contents state: entries are collected while inside the "Table of Contents"
    # section and flushed as a linked table when the next heading arrives.
    toc_entries: list = []
    in_contents = False
    content_width = A4[0] - 36 * mm
    heading_keys = _heading_anchor_map(lines, tier)

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
            raw_title = m.group(2)
            if in_contents:
                story.extend(_toc_flowables(toc_entries, toc_pages or {},
                                            styles, tier, content_width, heading_keys))
                toc_entries, in_contents = [], False
            if level == 1 and not skipped_title:
                skipped_title = True
                i += 1
                continue
            content = md_inline_to_html(raw_title, tier)
            style = styles.get(f"h{level}", styles["h4"])
            story.append(Paragraph(content, style))
            if level <= 2 and TOC_HEADING_RE.match(re.sub(r"[*`_]", "", raw_title).strip()):
                in_contents = True
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

        m = BLOCKQUOTE_RE.match(stripped)
        if m:
            # A note block: drop the marker, gather consecutive `>` lines into one
            # paragraph, and set it as a note (italic, indented, grey).
            quote_lines = [m.group(1).strip()]
            i += 1
            while i < len(lines):
                nxt = BLOCKQUOTE_RE.match(lines[i].strip())
                if not nxt:
                    break
                quote_lines.append(nxt.group(1).strip())
                i += 1
            story.append(Paragraph(
                md_inline_to_html(" ".join(q for q in quote_lines if q), tier),
                styles["note"],
            ))
            continue

        m = LIST_RE.match(line)
        if m:
            if in_contents:
                toc_entries.append(m.group(1).strip())
            else:
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
                BLOCKQUOTE_RE.match(nxt) or
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

    if in_contents:
        story.extend(_toc_flowables(toc_entries, toc_pages or {}, styles, tier,
                                    content_width, heading_keys))
    return story


# ---------- Main builder ----------

def build_pdf(input_md: Path, output_pdf: Path, title: str, client: str, dob: str,
              day_master: str, *, report_id: str = "", tier: str | None = None,
              pages_out: list | None = None):
    text = strip_source_citations(input_md.read_text(encoding="utf-8"))
    text = strip_engine_drafts(text)
    # ReportLab's fonts do not contain color-emoji glyphs; strip element-circle
    # emoji globally before layout so the client PDF never shows tofu boxes.
    text = _strip_element_emoji(text)
    if not report_id:
        report_id = f"CID-{output_pdf.stem}-{date.today().strftime('%Y%m%d')}"

    # First pass: count pages on a throwaway temporary file.
    # `pages_out`, when given, receives that count. The two-pass build is already why the footer can
    # print "Page N / total", so the number is free — the service reports it so the review console can
    # show a real page count instead of an em dash. (The HTML/Playwright backend never populates it;
    # production renders with ReportLab.)
    # The same pass also records the page each heading landed on, which is what the
    # contents page prints and what its links jump to. Both passes lay the document
    # out identically — the only difference is the page numbers in the contents
    # table's fixed-width right column — so what is printed is what was measured.
    doc_title = title or "Saju Reading"
    doc_author = "CosmicSaju"
    tmp_path = output_pdf.with_suffix('.tmp.pdf')
    try:
        doc1 = SajuDoc(str(tmp_path), report_id=report_id, client=client,
                       doc_title=doc_title, doc_author=doc_author)
        doc1.build(_md_to_story(text, title, client, dob, day_master, report_id,
                                tier=tier, toc_pages={}))
        total_pages = doc1.page
        heading_pages = dict(doc1.heading_pages)
        if pages_out is not None:
            pages_out.append(total_pages)
    finally:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass

    # Final pass: write the real PDF with "Page X / Y" in the footer and the
    # contents page numbered.
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc2 = SajuDoc(str(output_pdf), report_id=report_id, client=client,
                   total_pages=total_pages, doc_title=doc_title, doc_author=doc_author)
    doc2.build(_md_to_story(text, title, client, dob, day_master, report_id,
                            tier=tier, toc_pages=heading_pages))
    return output_pdf


# ---------- Chart → Markdown bridge (Priority 3) ----------

# These translate Korean names from the engine into a presentable markdown
# string that matches the structure of knowledge/10-output-template.md.
# (The PDF builder below then re-translates Korean→English for layout.)

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


def build_pdf_from_chart(chart, output_pdf: Path, *, title: str = "Saju Reading",
                         client: str = "", dob: str = "", day_master: str = "",
                         overwrite_report: bool = False, tier: Optional[str] = None,
                         report_id: str = "",
                         favorable_override: Optional[str] = None):
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
    kw = prepare_chart_render(
        chart, output_pdf, title=title, client=client, dob=dob, day_master=day_master,
        overwrite_report=overwrite_report, tier=tier, report_id=report_id,
        favorable_override=favorable_override)
    return build_pdf(kw["input_md"], Path(output_pdf), title, kw["client"], kw["dob"],
                     kw["day_master"], report_id=kw["report_id"], tier=tier)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, help="Path to the source .md file (mode 1).")
    ap.add_argument("--output", required=True, type=Path, help="Path to write the PDF.")
    ap.add_argument("--title", default="Saju Reading")
    ap.add_argument("--client", default="")
    ap.add_argument("--dob", default="")
    ap.add_argument("--day-master", default="")
    add_chart_args(ap)
    ap.add_argument("--tier", choices=TIER_CHOICES, default=None,
                    help="Report tier. With --from-chart it selects generated sections; "
                         "with an existing .md it only affects cover-page styling and translation.")
    ap.add_argument("--report-id", default="",
                    help="Unique report ID for cover/footer branding (auto-derived if omitted).")
    args = ap.parse_args()

    if args.from_chart:
        # Mode 2: engine → markdown → PDF
        chart = chart_from_args(ap, args)
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
