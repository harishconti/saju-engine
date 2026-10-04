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


def test_reportlab_path_warns_on_dropped():
    from saju_html.md_to_saju_pdf import md_inline_to_html

    with pytest.warns(UserWarning, match="龍"):
        out = md_inline_to_html("Hello 龍")
    assert "龍" not in out


def test_theme_css_has_cjk_fallback():
    css = (Path(renderer.__file__).parent / "theme.css").read_text(encoding="utf-8")
    assert "Noto Serif CJK KR" in css and "Noto Sans CJK KR" in css
