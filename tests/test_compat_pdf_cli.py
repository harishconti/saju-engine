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
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV = {
    **os.environ,
    "PYTHONPATH": f"{PROJECT_ROOT / 'src'}:/home/harish/.local/lib/python3.12/site-packages",
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


def test_compat_pdf_default_output_lands_under_repo_root_not_src(tmp_path):
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
