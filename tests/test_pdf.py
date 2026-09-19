"""Smoke tests for the PDF toolchain."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from saju_html import translate_inline

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}


def test_build_pdf_from_markdown():
    result = subprocess.run(
        ["bash", str(PROJECT_ROOT / "tools" / "build-pdf.sh"), "sruthi"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    pdf_path = PROJECT_ROOT / "candidates_horoscope" / "reports" / "sruthi" / "sruthi-report.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


def test_build_pdf_from_premium_markdown(tmp_path):
    # Generate premium markdown via the engine
    md_path = tmp_path / "sruthi-premium.md"
    pdf_path = tmp_path / "sruthi-premium.pdf"
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--name", "Sruthi",
            "--format", "premium",
            "--output-file", str(md_path),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr

    # Convert the premium markdown to PDF
    result = subprocess.run(
        [
            "python3", str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_pdf.py"),
            "--input", str(md_path),
            "--output", str(pdf_path),
            "--title", "Sruthi — Premium Saju Reading",
            "--client", "Sruthi",
            "--dob", "11 December 1993",
            "--day-master", "Gye Water",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


def test_build_pdf_strips_source_citations(tmp_path):
    md_path = tmp_path / "citations.md"
    pdf_path = tmp_path / "citations.pdf"
    md_path.write_text(
        "# Test\n\n"
        "Yin Metal is the image of the polished jewel. "
        "*(see knowledge/01-stems.md)*.\n\n"
        "| Element | Presence | Percentage |\n"
        "|---|---|---|\n"
        "| 🔴 Fire | ████████░░░░░░░░░░░░ | 40% |\n"
        "| 🟢 Wood | ████░░░░░░░░░░░░░░░░ | 20% |\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "python3", str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_pdf.py"),
            "--input", str(md_path),
            "--output", str(pdf_path),
            "--title", "Citation Test",
            "--client", "Candidate",
            "--dob", "1 January 2000",
            "--day-master", "Sin Metal",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert pdf_path.exists()

    text_result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        text=True,
    )
    pdf_text = text_result.stdout
    assert "see knowledge" not in pdf_text
    assert "knowledge/01-stems.md" not in pdf_text
    # Element names should appear without emoji artifacts and, for Fire, color markup.
    assert "Fire" in pdf_text
    assert "Wood" in pdf_text


def test_element_balance_emoji_replaced_with_colored_bullet(tmp_path):
    md_path = tmp_path / "elements.md"
    pdf_path = tmp_path / "elements.pdf"
    md_path.write_text(
        "# Test\n\n"
        "| Element | Presence | Percentage |\n"
        "|---|---|---|\n"
        "| 🔴 Fire | ████████░░░░░░░░░░░░ | 40% |\n"
        "| 🟢 Wood | ████░░░░░░░░░░░░░░░░ | 20% |\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "python3", str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_pdf.py"),
            "--input", str(md_path),
            "--output", str(pdf_path),
            "--title", "Element Emoji Test",
            "--client", "Candidate",
            "--dob", "1 January 2000",
            "--day-master", "Sin Metal",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert pdf_path.exists()

    text_result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        text=True,
    )
    pdf_text = text_result.stdout
    # The colored bullet should survive layout and the element names must be intact.
    assert "●" in pdf_text or "Fire" in pdf_text
    assert "Fire" in pdf_text
    assert "Wood" in pdf_text


def test_translate_inline_separates_adjacent_hanja_pairs():
    # Old behaviour collapsed adjacent translations: 丙午 -> "BingO".
    assert "BingO" not in translate_inline("丙午")
    assert "Bing" in translate_inline("丙午")
    assert "O" in translate_inline("丙午")


def test_translate_inline_drops_parenthetical_duplicates():
    # Markdown often supplies CJK followed by its English expansion.
    # The translator should not emit "Direct Officer (Direct Officer)".
    assert translate_inline("正官 (Direct Officer)") == "Direct Officer"
    assert translate_inline("세운 (Annual Luck)") == "Annual Luck"


def test_translate_inline_protects_arbitrary_parenthetical_english():
    # Generic English in parentheses must survive untouched.
    assert translate_inline("Some notes (do not translate this)") == "Some notes (do not translate this)"


def test_translate_inline_drops_unmapped_cjk():
    assert "龍" not in translate_inline("Hello 龍 world")


def test_md_to_pdf_honors_tier_in_md_mode(tmp_path):
    """--tier is forwarded to build_pdf() even in existing-markdown (mode 1) path."""
    md_path = tmp_path / "tier.md"
    pdf_path = tmp_path / "tier-deep.pdf"
    md_path.write_text("# Test\n\nBody content.\n", encoding="utf-8")

    result = subprocess.run(
        [
            "python3", str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_pdf.py"),
            "--input", str(md_path),
            "--output", str(pdf_path),
            "--title", "Tier Test",
            "--client", "Candidate",
            "--dob", "1 January 2000",
            "--day-master", "Gap (Yang Wood)",
            "--tier", "deep",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert pdf_path.exists()

    text_result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        text=True,
    )
    pdf_text = text_result.stdout
    # Deep tier cover note.
    assert "MP3 audio summary" in pdf_text


def test_md_to_pdf_sample_tier_omits_deep_cover_note(tmp_path):
    """Sample tier should not show the deep-tier MP3 cover note."""
    md_path = tmp_path / "tier.md"
    pdf_path = tmp_path / "tier-sample.pdf"
    md_path.write_text("# Test\n\nBody content.\n", encoding="utf-8")

    result = subprocess.run(
        [
            "python3", str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_pdf.py"),
            "--input", str(md_path),
            "--output", str(pdf_path),
            "--title", "Tier Test",
            "--client", "Candidate",
            "--dob", "1 January 2000",
            "--day-master", "Gap (Yang Wood)",
            "--tier", "sample",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert pdf_path.exists()

    text_result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        text=True,
    )
    pdf_text = text_result.stdout
    assert "MP3 audio summary" not in pdf_text


def test_pdf_no_camelcase_hanja_pair_transliteration(tmp_path):
    """Regression: adjacent Hanja pairs (e.g. 丙寅, 辛未, 甲子) must not be
    transliterated to camelCase tokens in the rendered PDF.

    Background: `translate_inline()` in `src/saju_html/__init__.py` uses
    longest-match tokenization and joins tokens with spaces. A previous
    version joined without a separator, producing "BingIn" / "SinMi" /
    "GapJa" in legacy PDFs. This test ensures the rendered output of a
    fresh PDF build never contains those tokens.

    Pre-2026-07-02: legacy PDFs had "BingIn" / "SinMi" / "GapJa" tokens.
    The defect was a stale-PDF artifact; the underlying code was already
    fixed. This test guards against the defect recurring in fresh builds.
    """
    md_path = tmp_path / "hanja-pairs.md"
    pdf_path = tmp_path / "hanja-pairs.pdf"
    # Body that mentions every Hanja pair known to trigger the defect,
    # both inline and in a table cell (different rendering paths).
    md_path.write_text(
        "# Test\n\n"
        "Day pillar is 丙寅. Hour pillar is 辛未. Year pillar is 甲子. "
        "Month pillar is 壬子.\n\n"
        "| Year | 丙寅 |\n"
        "|---|---|\n"
        "| Day | 辛未 |\n"
        "| Hour | 甲子 |\n\n"
        "Bing-day rule: 丙辛之日起戊子. Compatibility: 甲己合土, 乙庚合金, 丙辛合水.\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            "python3", str(PROJECT_ROOT / "src" / "saju_html" / "md_to_saju_pdf.py"),
            "--input", str(md_path),
            "--output", str(pdf_path),
            "--title", "Hanja Pair Test",
            "--client", "Candidate",
            "--dob", "1 January 2000",
            "--day-master", "Bing (Yang Fire)",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert pdf_path.exists()

    text_result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        capture_output=True,
        text=True,
    )
    pdf_text = text_result.stdout

    # CamelCase tokens that the defect produced. None of these should
    # appear in a fresh PDF build.
    forbidden_camelcase = [
        "BingIn", "BingO", "SinMi", "SinMu", "GapJa", "GapIn", "EulMi",
        "ImJa", "GyeMi",
    ]
    for tok in forbidden_camelcase:
        assert tok not in pdf_text, (
            f"PDF contains camelCase transliteration {tok!r} — "
            f"`translate_inline()` join is broken. Full PDF text:\n{pdf_text}"
        )

    # Sanity check: the transliterated English parts DO appear, with spaces.
    assert "Bing" in pdf_text
    assert "In" in pdf_text  # 寅 → In
    assert "Sin" in pdf_text  # 辛 → Sin
    assert "Mi" in pdf_text   # 未 → Mi
    assert "Gap" in pdf_text  # 甲 → Gap
