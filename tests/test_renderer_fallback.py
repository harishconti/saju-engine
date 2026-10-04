"""build_pdf must not silently fall back to reportlab (P5 task 1)."""
import pytest

from saju_html import renderer


def _boom(*a, **k):
    raise RuntimeError("no chromium")


@pytest.fixture
def md(tmp_path):
    p = tmp_path / "r.md"
    p.write_text("# Title\n\nHello.\n", encoding="utf-8")
    return p


def test_missing_backend_raises_loudly(monkeypatch, md, tmp_path):
    monkeypatch.setattr(renderer, "html_to_pdf", _boom)
    monkeypatch.delenv("SAJU_PDF_FALLBACK", raising=False)
    with pytest.raises(RuntimeError, match="HTML/Playwright PDF backend unavailable"):
        renderer.build_pdf(md, tmp_path / "o.pdf", title="T", client="C", dob="D", day_master="DM")


def test_import_error_also_raises(monkeypatch, md, tmp_path):
    def imp(*a, **k):
        raise ImportError("playwright")

    monkeypatch.setattr(renderer, "html_to_pdf", imp)
    monkeypatch.delenv("SAJU_PDF_FALLBACK", raising=False)
    with pytest.raises(RuntimeError, match="playwright install chromium"):
        renderer.build_pdf(md, tmp_path / "o.pdf", title="T", client="C", dob="D", day_master="DM")


def _stub_reportlab(monkeypatch):
    calls = []
    import saju_html.md_to_saju_pdf as m

    monkeypatch.setattr(m, "build_pdf", lambda *a, **k: calls.append(a) or "rl")
    return calls


def test_allow_fallback_keyword(monkeypatch, md, tmp_path):
    monkeypatch.setattr(renderer, "html_to_pdf", _boom)
    monkeypatch.delenv("SAJU_PDF_FALLBACK", raising=False)
    calls = _stub_reportlab(monkeypatch)
    with pytest.warns(UserWarning, match="falling back"):
        out = renderer.build_pdf(md, tmp_path / "o.pdf", title="T", client="C", dob="D", day_master="DM", allow_fallback=True)
    assert out == "rl" and len(calls) == 1


def test_env_var_fallback(monkeypatch, md, tmp_path):
    monkeypatch.setattr(renderer, "html_to_pdf", _boom)
    monkeypatch.setenv("SAJU_PDF_FALLBACK", "reportlab")
    calls = _stub_reportlab(monkeypatch)
    with pytest.warns(UserWarning, match="falling back"):
        renderer.build_pdf(md, tmp_path / "o.pdf", title="T", client="C", dob="D", day_master="DM")
    assert len(calls) == 1
