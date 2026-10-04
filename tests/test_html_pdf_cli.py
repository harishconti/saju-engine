"""md_to_saju_html_pdf CLI: backend banner, failed-render cleanup, --tier choices."""
import sys
from pathlib import Path

import pytest

import saju_html.md_to_saju_html_pdf as cli
import saju_html.renderer as renderer

CHART = ["--from-chart", "--tier", "essential", "--gender", "F", "--birth-year", "1993",
         "--birth-month", "12", "--birth-day", "11", "--birth-hour", "2", "--birth-minute", "45",
         "--longitude", "79.42", "--utc-offset", "5.5"]


def _stub_ok(html_doc, output_pdf, **kw):
    Path(output_pdf).write_bytes(b"%PDF-stub")
    return Path(output_pdf)


def _boom(*a, **k):
    raise RuntimeError("no browser")


def _run(monkeypatch, argv):
    monkeypatch.setattr(sys, "argv", ["prog", *argv])
    cli.main()


def test_reports_html_mode(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(renderer, "html_to_pdf", _stub_ok)
    _run(monkeypatch, ["--output", str(tmp_path / "a-report.pdf"), *CHART])
    assert "[html-playwright mode]" in capsys.readouterr().out


def test_reports_reportlab_fallback_mode(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(renderer, "html_to_pdf", _boom)
    monkeypatch.setenv("SAJU_PDF_FALLBACK", "reportlab")
    _run(monkeypatch, ["--output", str(tmp_path / "a-report.pdf"), *CHART])
    out = capsys.readouterr().out
    assert "[reportlab fallback mode]" in out and "[html-playwright mode]" not in out


def test_failed_render_removes_intermediate_md_it_created(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(renderer, "html_to_pdf", _boom)
    monkeypatch.delenv("SAJU_PDF_FALLBACK", raising=False)
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, ["--output", str(tmp_path / "a-report.pdf"), *CHART])
    assert e.value.code == 1
    assert not (tmp_path / "a-engine.md").exists()
    assert not (tmp_path / "a-report.pdf").exists()


def test_failed_render_keeps_preexisting_md(monkeypatch, tmp_path):
    monkeypatch.setattr(renderer, "html_to_pdf", _boom)
    monkeypatch.delenv("SAJU_PDF_FALLBACK", raising=False)
    pre = tmp_path / "a-engine.md"
    pre.write_text("mine", encoding="utf-8")
    with pytest.raises(SystemExit):
        _run(monkeypatch, ["--output", str(tmp_path / "a-report.pdf"), *CHART])
    assert pre.read_text(encoding="utf-8") != "" and pre.exists()


def test_tier_choices_enforced(monkeypatch, tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, ["--input", str(tmp_path / "x.md"), "--output", str(tmp_path / "o.pdf"), "--tier", "bogus"])
    assert e.value.code == 2
    assert "invalid choice" in capsys.readouterr().err
