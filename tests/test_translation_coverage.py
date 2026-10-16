"""No golden report may contain CJK that the translation maps cannot handle."""
import logging
from pathlib import Path

import pytest

from saju_html import strip_engine_drafts, strip_source_citations, translate_inline
from saju_html import renderer

GOLDEN = sorted(Path(__file__).parent.joinpath("golden").glob("*.md"))


@pytest.mark.parametrize("path", GOLDEN, ids=lambda p: p.name)
def test_golden_has_no_unmapped_cjk(path):
    text = strip_engine_drafts(strip_source_citations(path.read_text(encoding="utf-8")))
    unmapped: set = set()
    translate_inline(text, unmapped=unmapped)
    assert unmapped == set(), f"{path.name}: unmapped CJK {sorted(unmapped)}"


def test_keep_unmapped_keeps_and_reports():
    seen: set = set()
    out = translate_inline("Hello 龍 world", unmapped=seen)
    assert "龍" in out and seen == {"龍"}


def test_drop_mode_drops_and_still_reports():
    seen: set = set()
    out = translate_inline("Hello 龍 world", keep_unmapped=False, unmapped=seen)
    assert "龍" not in out and seen == {"龍"}


def test_html_renderer_logs_unmapped(caplog):
    with caplog.at_level(logging.WARNING, logger="saju_html.renderer"):
        html = renderer._render_markdown("Para 龍 here.\n")
    assert "龍" in html
    assert any("龍" in r.getMessage() for r in caplog.records)


def test_reportlab_path_keeps_cjk_in_the_bundled_face():
    """CJK the translation maps cannot reach is drawn, not dropped.

    The ReportLab backend used to erase surviving CJK because DejaVu has no
    Hangul or Hanja. It now routes those runs to a bundled subset of Noto Sans KR
    (see tools/build-cjk-font-subset.py), so a client sees the character.
    """
    from saju_html.md_to_saju_pdf import _CJK_FONT, md_inline_to_html

    out = md_inline_to_html("Hello 龍")
    assert "龍" in out
    assert f"face='{_CJK_FONT}'" in out


def test_reportlab_path_drops_only_characters_no_face_can_draw(capsys):
    """A character outside the bundled face is omitted, never a tofu box.

    A box is indistinguishable from a typo in a paid report, so the renderer
    prefers to drop the character and say so on stderr. U+9F98 龘 is outside Noto
    Sans KR, which is why it stands in here.
    """
    import saju_html.md_to_saju_pdf as pdfmod

    pdfmod._CJK_DROP_WARNED.clear()
    out = pdfmod.md_inline_to_html("Hello 龘")
    assert "龘" not in out
    assert "U+9F98" in capsys.readouterr().err


def test_theme_css_has_cjk_fallback():
    css = (Path(renderer.__file__).parent / "theme.css").read_text(encoding="utf-8")
    assert "Noto Serif CJK KR" in css and "Noto Sans CJK KR" in css
