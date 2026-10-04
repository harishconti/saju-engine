"""HTML/Chromium is the default PDF backend; reportlab is opt-in (--reportlab)."""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from tests.test_html_pdf import requires_browser  # noqa: F401  (skips without Chromium)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": os.pathsep.join(
    p for p in (str(PROJECT_ROOT / "src"), os.environ.get("PYTHONPATH", "")) if p)}

CHART_ARGS = [
    "sruthi", "Sruthi — Saju", "Sruthi", "11 December 1993", "Bing Fire",
    "--from-chart", "--tier", "essential", "--name", "Sruthi", "--gender", "F",
    "--birth-year", "1993", "--birth-month", "12", "--birth-day", "11",
    "--birth-hour", "2", "--birth-minute", "45", "--city", "Pallipat", "--utc-offset", "5.5",
]


def _run(tmp_path, *extra):
    return subprocess.run(
        ["bash", str(PROJECT_ROOT / "tools" / "build-pdf.sh"), *extra, *CHART_ARGS],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
        env={**ENV, "SAJU_OUT_DIR": str(tmp_path)},
    )


def _producer(pdf: Path) -> str:
    data = pdf.read_bytes()
    return " ".join(m.decode("latin-1") for m in re.findall(rb"/(?:Producer|Creator)\s*\(([^)]*)\)", data))


def test_wrapper_script_defaults_to_html():
    sh = (PROJECT_ROOT / "tools" / "build-pdf.sh").read_text(encoding="utf-8")
    assert "USE_HTML=1" in sh.split("NEW_ARGS=()")[0]
    assert "--reportlab" in sh
    assert "-report-reportlab.pdf" in sh and "-combined-reportlab.pdf" in sh


def test_html_cli_accepts_from_chart_flags():
    r = subprocess.run(
        ["python3", str(PROJECT_ROOT / "src/saju_html/md_to_saju_html_pdf.py"), "--help"],
        capture_output=True, text=True, env=ENV)
    assert r.returncode == 0
    for flag in ("--from-chart", "--birth-year", "--tier", "--utc-offset", "--overwrite-report"):
        assert flag in r.stdout


def test_compat_cli_has_backend_flag_default_html():
    r = subprocess.run(
        ["python3", str(PROJECT_ROOT / "src/saju_html/md_to_saju_compat_pdf.py"), "--help"],
        capture_output=True, text=True, env=ENV)
    assert "--backend" in r.stdout and "html,reportlab" in r.stdout.replace(" ", "")


def test_chart_markdown_helper_shared_by_both_backends():
    from saju_html import md_to_saju_pdf as rl
    from saju_html import chart_input
    assert rl.prepare_chart_render is chart_input.prepare_chart_render


@requires_browser
def test_default_build_is_chromium_and_canonical_name(tmp_path):
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    pdf = tmp_path / "sruthi-report.pdf"
    assert pdf.exists() and pdf.stat().st_size > 1024
    assert re.search(r"Skia|Chrom", _producer(pdf)), _producer(pdf)
    assert not (tmp_path / "sruthi-report-reportlab.pdf").exists()


@requires_browser
def test_html_flag_is_noop_alias(tmp_path):
    r = _run(tmp_path, "--html")
    assert r.returncode == 0, r.stderr
    assert re.search(r"Skia|Chrom", _producer(tmp_path / "sruthi-report.pdf"))


def test_reportlab_flag_produces_reportlab_pdf_with_distinct_name(tmp_path):
    pytest.importorskip("reportlab")
    r = _run(tmp_path, "--reportlab")
    assert r.returncode == 0, r.stderr
    pdf = tmp_path / "sruthi-report-reportlab.pdf"
    assert pdf.exists()
    assert "ReportLab" in _producer(pdf)
    assert not (tmp_path / "sruthi-report.pdf").exists()


@requires_browser
def test_default_pdf_text_has_no_citations(tmp_path):
    pypdf = pytest.importorskip("pypdf")
    assert _run(tmp_path).returncode == 0
    text = "\n".join(p.extract_text() for p in pypdf.PdfReader(tmp_path / "sruthi-report.pdf").pages)
    assert "knowledge/" not in text and "ENGINE DRAFT" not in text


@requires_browser
def test_compat_cli_html_backend_default(tmp_path):
    md = tmp_path / "a_b_compatibility.md"
    md.write_text("# A x B — 궁합\n\n**Composite Score:** **50 / 100**\n\n## Closing Note\n\nHi.\n", encoding="utf-8")
    out = tmp_path / "out" / "c.pdf"
    r = subprocess.run(
        ["python3", str(PROJECT_ROOT / "src/saju_html/md_to_saju_compat_pdf.py"), str(md),
         "--name-a", "A", "--name-b", "B", "--dob-a", "1 Jan 1990", "--dob-b", "1 Jan 1990",
         "--day-master-a", "丙", "--day-master-b", "丙", "--output", str(out)],
        capture_output=True, text=True, env=ENV)
    assert r.returncode == 0, r.stderr
    assert re.search(r"Skia|Chrom", _producer(out))


def test_jobs_backend_env_switch(monkeypatch):
    from saju_web import jobs
    monkeypatch.delenv("SAJU_PDF_BACKEND", raising=False)
    assert jobs._pdf_backend() == "html"
    monkeypatch.setenv("SAJU_PDF_BACKEND", "reportlab")
    assert jobs._pdf_backend() == "reportlab"
