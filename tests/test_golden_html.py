"""Rendered-HTML golden snapshots (P5 Task 3, 2026-10-04).

``tests/golden_html/<name>.html`` is the exact HTML ``renderer.markdown_to_html``
produces (the string ``html_to_pdf`` prints) for each committed
``tests/golden/<name>.md``, with fixed metadata. Regenerate only for an
intended, reviewed rendering change: ``python3 tools/regen_golden.py --html``
(the markdown goldens are never touched by that).
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.golden.cases import HTML_REPORT_ID_PREFIX, render_golden_html
from tests.test_html_pdf import requires_browser
from tests.test_pdf import requires_pdftotext

ROOT = Path(__file__).resolve().parent
GOLDEN_MD = ROOT / "golden"
GOLDEN_HTML = ROOT / "golden_html"
NAMES = sorted(p.stem for p in GOLDEN_MD.glob("*.md"))

_BALANCE_HEADER = re.compile(r"^\|(?=.*Element)(?=.*Presence)(?=.*Percentage).*$", re.M)


def _md(name: str) -> str:
    return (GOLDEN_MD / f"{name}.md").read_text(encoding="utf-8")


def _render(name: str) -> str:
    return render_golden_html(f"{name}.md", _md(name))


def test_html_golden_set_is_complete():
    on_disk = {p.stem for p in GOLDEN_HTML.glob("*.html")}
    assert on_disk == set(NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_html_matches_golden(name, caplog):
    with caplog.at_level(logging.WARNING, logger="saju_html"):
        html = _render(name)
    expected = (GOLDEN_HTML / f"{name}.html").read_text(encoding="utf-8")
    assert html == expected, f"{name}.html drifted from its golden snapshot"

    # Structural invariants (independent of byte-exactness).
    assert html.lstrip().lower().startswith("<!doctype html")
    if _BALANCE_HEADER.search(_md(name)):
        assert 'class="element-balance-chart' in html and "<svg" in html
    assert "(see knowledge/" not in html and "see knowledge/" not in html
    assert "knowledge/" not in html
    assert "ENGINE DRAFT" not in html
    assert f"{HTML_REPORT_ID_PREFIX}{name}" in html
    unmapped = [r.getMessage() for r in caplog.records if "Unmapped CJK" in r.getMessage()]
    assert not unmapped, unmapped


def test_html_render_is_deterministic():
    assert _render("park-deep") == _render("park-deep")


def test_chart_structural_check_is_not_vacuous():
    with_table = [n for n in NAMES if _BALANCE_HEADER.search(_md(n))]
    assert len(with_table) >= 10
    assert all('class="element-balance-chart' in (GOLDEN_HTML / f"{n}.html").read_text(encoding="utf-8")
               for n in with_table)


@requires_browser
@requires_pdftotext
def test_browser_smoke_golden_html_prints_to_pdf(tmp_path):
    from saju_html.renderer import html_to_pdf

    name = "park-essential"
    html = (GOLDEN_HTML / f"{name}.html").read_text(encoding="utf-8")
    pdf = html_to_pdf(html, tmp_path / "smoke.pdf", report_id=f"{HTML_REPORT_ID_PREFIX}{name}")
    assert pdf.exists() and pdf.stat().st_size > 1024
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                          text=True, check=True).stdout
    pages = text.count("\f")
    assert pages >= 1
    assert re.search(r"Page\s+1\s*/\s*\d+", text), "footer page numbering missing"
    if shutil.which("pdfinfo") is None:
        return
    info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    assert int(re.search(r"Pages:\s+(\d+)", info).group(1)) >= 1
    assert "knowledge/" not in text and "ENGINE DRAFT" not in text


_COVER_RE = re.compile(r'<div class="cover">\n.*?\n</div>\n', re.S)
_CJK_CHARS = re.compile(r"[가-힣一-鿿]")
# A parenthesised Hanja/Korean gloss — "Direct Officer (正官)", "Gyeong (庚)".
_GLOSS = re.compile(r"\([^()]*[가-힣一-鿿][^()]*\)")


def _unexplained_cjk(text: str) -> str:
    """CJK that is NOT inside a parenthetical gloss — empty when the text is fine.

    The delivered artefact's convention (owner decision, 2026-10-16) is English
    with the Hanja the reading is about beside it, so CJK is expected on the page
    — but only as a gloss in parentheses, never as untranslated prose.
    """
    return "".join(_CJK_CHARS.findall(_GLOSS.sub("", text)))
_WATERMARK = re.compile(r'<div class="watermark">[^<]*</div>')


@pytest.mark.parametrize("name", NAMES)
def test_golden_cover_cjk_is_only_a_gloss(name):
    """The cover is English; the only CJK it may carry is a parenthetical gloss.

    It used to assert no CJK at all, because the cover font could not draw any.
    It now shows "Gyeong (庚)" — the Hanja beside its romanisation, the owner's
    convention — so the invariant is "translated, with the term kept".
    """
    html = (GOLDEN_HTML / f"{name}.html").read_text(encoding="utf-8")
    m = _COVER_RE.search(html)
    assert m, "cover block not found"
    cover = _WATERMARK.sub("", m.group(0))  # the decorative 命 watermark is intentional
    assert not _unexplained_cjk(cover), cover


def test_cover_meta_rows_are_translated():
    from saju_html.renderer import markdown_to_html

    for compact in (False, True):
        html = markdown_to_html(
            "# T\n\nbody\n",
            title="Compatibility Reading — A × B",
            client="Alice (庚) · Bob (辛) · McKay",
            dob="1990 · 1991",
            day_master="庚/辛",
            generation_date="January 1, 2026",
            report_id="X-1",
            compact=compact,
        )
        cover = _WATERMARK.sub("", _COVER_RE.search(html).group(0) if not compact else
                               re.search(r'<div class="compact-cover">.*?\n</div>\n', html, re.S).group(0))
        assert not _unexplained_cjk(cover), cover
        assert "Gyeong (庚)/Sin (辛)" in cover
        assert "Alice (Gyeong (庚))" in cover
        assert "McKay" in cover  # Latin names are never rewritten
