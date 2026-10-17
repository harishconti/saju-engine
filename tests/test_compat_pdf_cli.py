"""Regression test for md_to_saju_compat_pdf.py's default output-path bug.

Bug (found 2026-09-19): the default-output branch computed
``repo_root = Path(__file__).resolve().parent.parent``, which — after the
project's src/ layout migration — resolves to ``src/`` instead of the actual
repo root. Every compat PDF built without an explicit --output silently
landed under ``src/candidates_horoscope/...`` instead of
``candidates_horoscope/...``. Confirmed live: rebuilding the pawan_sruthi
compat PDF wrote to ``src/candidates_horoscope/marriage_compatibility/...``
before the fix (repo_root needs one more ``.parent``, matching the pattern
already used by ``combine_candidate_report.PROJECT_ROOT``).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.test_html_pdf import requires_browser

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# A5 (2026-10-01 audit): this hard-coded /home/harish/.local/... and so only
# ran on one machine. Inherit the caller's PYTHONPATH (CI installs deps
# normally; locally build-pdf.sh / $SAJU_SITE provide it) and prepend src/.
ENV = {
    **os.environ,
    "PYTHONPATH": os.pathsep.join(
        p for p in (str(PROJECT_ROOT / "src"), os.environ.get("PYTHONPATH", "")) if p
    ),
}

MINIMAL_COMPAT_MD = """\
# Test Pair A x Test Pair B — 궁합 (合婚 / Compatibility Reading)

**Composite Score (종합 점수):** **50 / 100**
**Verdict Band (평가):** **Mixed**

| Partner | Day Master | Day Branch | Day Pillar | Favorable Element |
|---|---|---|---|---|
| **Test Pair A** | 丙 | 午 | 丙午 | Water |
| **Test Pair B** | 丙 | 寅 | 丙寅 | Earth |

## Closing Note

Placeholder closing note for the regression fixture.
"""


@pytest.mark.parametrize("backend", [
    pytest.param("html", marks=requires_browser),
    "reportlab",
])
def test_compat_pdf_default_output_lands_under_repo_root_not_src(tmp_path, backend):
    if backend == "reportlab":
        pytest.importorskip("reportlab")
    input_md = tmp_path / "test-pair-a_test-pair-b_compatibility.md"
    input_md.write_text(MINIMAL_COMPAT_MD, encoding="utf-8")

    pair_dir = (
        PROJECT_ROOT
        / "candidates_horoscope"
        / "marriage_compatibility"
        / "test-pair-a_test-pair-b"
    )
    stray_dir = PROJECT_ROOT / "src" / "candidates_horoscope"
    assert not pair_dir.exists(), f"test fixture dir already exists: {pair_dir}"
    assert not stray_dir.exists(), f"leftover stray dir from a prior failure: {stray_dir}"

    try:
        result = subprocess.run(
            [
                "python3",
                str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_compat_pdf.py"),
                str(input_md),
                "--name-a", "Test Pair A",
                "--name-b", "Test Pair B",
                "--dob-a", "1 January 1990",
                "--dob-b", "1 January 1990",
                "--day-master-a", "丙",
                "--day-master-b", "丙",
                "--tier", "basic",
                "--backend", backend,
            ],
            cwd=PROJECT_ROOT,
            env=ENV,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

        expected_pdf = pair_dir / "test-pair-a_test-pair-b_compatibility.pdf"
        assert expected_pdf.exists(), (
            f"expected PDF under repo-root candidates_horoscope/, got: {result.stdout}"
        )
        assert not stray_dir.exists(), (
            "default output path regressed: wrote under src/candidates_horoscope/ again"
        )
    finally:
        shutil.rmtree(pair_dir, ignore_errors=True)
        shutil.rmtree(stray_dir, ignore_errors=True)


def _run_compat_cli(input_md: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "python3",
            str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_compat_pdf.py"),
            str(input_md),
            "--name-a", "Test Pair A",
            "--name-b", "Test Pair B",
            "--dob-a", "1 January 1990",
            "--dob-b", "1 January 1990",
            "--day-master-a", "丙",
            "--day-master-b", "丙",
            "--tier", "basic",
            *extra,
        ],
        cwd=PROJECT_ROOT,
        env=ENV,
        capture_output=True,
        text=True,
    )


def test_compat_web_document_is_a_self_contained_reading(tmp_path):
    """`--web` renders the compat *reading* — the screen artefact, not a PDF.

    Regression (2026-10-17): the compat tool had no web mode, so the two compatibility demos
    on the marketing page were PDF-only while every single-chart tier offered a reading — a
    withheld capability that never errored. The reading must be the same self-contained
    artefact the single-chart tiers get: the compat body class, no leaked ``knowledge/``
    citations, and no external request beyond the inline SVG XML namespace.
    """
    input_md = tmp_path / "pawan_sruthi_compatibility.md"
    input_md.write_text(MINIMAL_COMPAT_MD, encoding="utf-8")
    out_html = tmp_path / "demo-compat-basic.html"

    result = _run_compat_cli(input_md, "--web", "--output", str(out_html))
    assert result.returncode == 0, result.stderr
    assert out_html.exists(), result.stdout

    doc = out_html.read_text(encoding="utf-8")
    assert '<body class="tier-compat web-mode">' in doc
    assert "knowledge/" not in doc, "the reading must not leak knowledge/ citations"
    external = {
        url
        for url in re.findall(r"https?://[^\s\"')<>]+", doc)
        if not url.startswith("http://www.w3.org/")
    }
    assert external == set(), f"reading must make no external requests, found: {external}"


def test_compat_web_default_output_is_html_not_pdf(tmp_path):
    """`--web` with no --output writes an .html beside the pair, never a .pdf."""
    input_md = tmp_path / "test-pair-a_test-pair-b_compatibility.md"
    input_md.write_text(MINIMAL_COMPAT_MD, encoding="utf-8")
    pair_dir = (
        PROJECT_ROOT
        / "candidates_horoscope"
        / "marriage_compatibility"
        / "test-pair-a_test-pair-b"
    )
    assert not pair_dir.exists(), f"test fixture dir already exists: {pair_dir}"
    try:
        result = _run_compat_cli(input_md, "--web")
        assert result.returncode == 0, result.stderr
        assert (pair_dir / "test-pair-a_test-pair-b_compatibility.html").exists(), result.stdout
        assert not (pair_dir / "test-pair-a_test-pair-b_compatibility.pdf").exists()
    finally:
        shutil.rmtree(pair_dir, ignore_errors=True)


def test_compat_web_rejects_a_pdf_output_path(tmp_path):
    """`--web --output x.pdf` fails loudly rather than silently writing HTML to a .pdf."""
    input_md = tmp_path / "pawan_sruthi_compatibility.md"
    input_md.write_text(MINIMAL_COMPAT_MD, encoding="utf-8")
    not_a_pdf = tmp_path / "oops.pdf"

    result = _run_compat_cli(input_md, "--web", "--output", str(not_a_pdf))
    assert result.returncode == 2
    assert "give --output an .html path" in result.stderr
    assert not not_a_pdf.exists()
