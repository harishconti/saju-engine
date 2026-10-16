"""Regression tests for the report PDF's navigation and CJK handling.

The ReportLab backend gained four things in one pass, each of which was a defect
in the delivered artefact before it:

1. **A real contents page.** It printed a bare bullet list with no page numbers,
   no links, and no outline, so a 28-page reading could not be navigated.
2. **PDF metadata.** Every delivered report reported itself as `Title:
   (anonymous)` in the reader's window and tab.
3. **Markdown blockquotes.** The 16 reader notes in the Deep tier ("In plain
   words:", "Almanac caveat:") printed their `>` marker literally.
4. **Hangul/Hanja.** Surviving CJK was erased because DejaVu has no CJK coverage;
   it is now drawn with a bundled subset of Noto Sans KR, and a character no
   bundled face can draw is dropped rather than shown as a tofu box.

These read the produced PDF rather than the story, because that is what the
client receives.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from saju_html.md_to_saju_pdf import build_pdf

REPO_ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = REPO_ROOT / "src" / "saju_html" / "fonts"

MD = """# Korean Four Pillars of Destiny · Saju Reading

## A Client — Essential Report

*Subtitle line*

## Table of Contents

- Chart at a Glance
- Longer Section — incl. A Subsection

---

## Chart at a Glance

> In plain words: the marker must not survive into the PDF.

Filler paragraph so the page has some height.

## Longer Section

More filler, long enough that the section is genuinely later in the document.

### A Subsection

A subsection the contents entry refers to.
"""


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("nav") / "report.pdf"
    build_pdf(
        _write_md(tmp_path_factory.mktemp("md") / "report.md"),
        out,
        "Saju Reading — Essential",
        "A Client",
        "1 January 2000",
        "Gap (Yang Wood)",
        report_id="CID-NAV",
        tier="essential",
    )
    return out


def _write_md(path: Path) -> Path:
    path.write_text(MD, encoding="utf-8")
    return path


def _page_text(pdf: Path, page: int) -> str:
    return subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],
        capture_output=True, text=True, check=True,
    ).stdout


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext not installed")
def test_contents_prints_the_page_each_section_is_on(built):
    """Each contents number must name the page the heading really starts on.

    The numbers come from a first measuring pass, so this asserts the two passes
    agree — the failure mode is a contents page that is confidently wrong.
    """
    raw = subprocess.run(["pdftotext", "-layout", str(built), "-"],
                         capture_output=True, text=True, check=True).stdout
    contents_page = next(i for i, page in enumerate(raw.split("\f"), start=1)
                         if "Table of Contents" in page)
    entries = re.findall(r"•\s+(.+?)\s{2,}(\d+)\s*$",
                         raw.split("\f")[contents_page - 1], re.M)
    assert entries, "no numbered contents entries found"

    def plain(text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^0-9A-Za-z& ]", " ", text)).casefold()

    for title, page in entries:
        # `Longer Section — incl. A Subsection` names the heading `Longer Section`;
        # the composite tail is a contents label, not part of the heading.
        heading = re.split(r"\s+\u2014\s+", title)[0]
        first_words = plain(heading).split()[:2]
        page_text = plain(_page_text(built, int(page)))
        assert all(word in page_text for word in first_words), (
            f"contents says {heading!r} is on page {page}, but it is not"
        )


@pytest.mark.skipif(shutil.which("pdfinfo") is None, reason="pdfinfo not installed")
def test_pdf_is_outlined_linked_and_titled(built):
    """Outline, clickable contents links, and real document metadata.

    Asserted through `pdfinfo` rather than the raw bytes: reportlab writes the
    info dictionary in PDFDocEncoding/UTF-16, so the title is not searchable as
    UTF-8 text.
    """
    raw = built.read_bytes()
    assert b"/Outlines" in raw, "no PDF outline: the reader gets no section panel"
    assert b"/Subtype /Link" in raw, "contents entries are not clickable"
    info = subprocess.run(["pdfinfo", str(built)], capture_output=True,
                          text=True, check=True).stdout
    assert "Saju Reading \u2014 Essential" in info, info
    assert re.search(r"^Author:\s+CosmicSaju", info, re.M), info
    assert "(anonymous)" not in info


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext not installed")
def test_blockquote_marker_is_not_printed(built):
    """A `>` note reads as a note, not as a literal angle bracket."""
    text = subprocess.run(["pdftotext", str(built), "-"],
                          capture_output=True, text=True, check=True).stdout
    assert "In plain words: the marker must not survive" in text
    assert "> In plain words" not in text
    assert not re.search(r"^\s*>", text, re.M), "a blockquote marker leaked into the PDF"


def test_cjk_is_routed_to_the_bundled_face():
    """CJK that survives translation is drawn, not erased."""
    from saju_html.md_to_saju_pdf import _CJK_FONT, _wrap_cjk_font

    marked = _wrap_cjk_font("the year 龍 pillar")
    assert "龍" in marked and f"face='{_CJK_FONT}'" in marked


def test_cjk_font_covers_repo_cjk():
    """Every CJK character a report can contain is in the bundled subset.

    The subset is deliberately not the whole font (see
    `tools/build-cjk-font-subset.py`), so adding a Hanja to `knowledge/` without
    regenerating it would quietly drop a character from a client PDF. This is the
    check that makes that impossible.
    """
    pytest.importorskip("fontTools")
    import sys
    from importlib import import_module
    from fontTools.ttLib import TTFont

    sys.path.insert(0, str(REPO_ROOT / "tools"))
    builder = import_module("build-cjk-font-subset")
    wanted = builder.collect_codepoints()

    # Compare against the source face, so the check only fails on a genuine
    # subsetting gap: Noto Sans KR is a Korean face and cannot draw every
    # ideograph in the repo, and those are dropped at render time by design.
    # Reuse the maintenance cache when it is there (fast), otherwise download to a
    # temp dir so the check still runs on a clean CI checkout.
    cache = Path("/tmp/opencode")
    if not cache.is_dir():
        cache = Path(tempfile.mkdtemp(prefix="saju-cjk-"))
    try:
        source = builder.download(builder.SOURCE_URL, cache / "NotoSansKR-VF.ttf")
        source_cmap = set(TTFont(str(source)).getBestCmap())
    except Exception as exc:  # pragma: no cover - network-dependent
        pytest.skip(f"source font unavailable ({exc}); cannot attribute the gap")
    for weight_file in ("SajuCJK-Regular.ttf", "SajuCJK-Bold.ttf"):
        cmap = set(TTFont(str(FONT_DIR / weight_file)).getBestCmap())
        gap = sorted(c for c in wanted if c in source_cmap and c not in cmap)
        assert not gap, (
            f"{weight_file} is missing {len(gap)} characters the repo uses: "
            f"{''.join(chr(c) for c in gap[:12])} — "
            "rebuild with `python3 tools/build-cjk-font-subset.py`"
        )


def test_undrawable_cjk_is_dropped_not_printed_as_a_box(capsys):
    """A glyph no bundled face can draw is omitted, and reported.

    U+9F98 龘 is outside Noto Sans KR. A tofu box is indistinguishable from a
    typo in a paid report, so dropping the character is the lesser defect — but
    it must be visible in the server log, not silent.
    """
    import saju_html.md_to_saju_pdf as pdfmod

    pdfmod._CJK_DROP_WARNED.clear()
    out = pdfmod.md_inline_to_html("a 龘 glyph")
    assert "龘" not in out
    assert "U+9F98" in capsys.readouterr().err
