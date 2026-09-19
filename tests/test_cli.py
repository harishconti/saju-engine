"""Smoke tests for the command-line interface."""
from __future__ import annotations

import io
import json
import os
import subprocess

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}


def test_cli_table_output():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "table",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "癸酉" in result.stdout
    assert "丙寅" in result.stdout


def test_cli_json_output():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1991-10-03",
            "--time", "23:45",
            "--longitude", "79.19",
            "--utc-offset", "5.5",
            "--gender", "M",
            "--format", "json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert '"day"' in result.stdout
    assert "丙午" in result.stdout


def test_cli_invalid_date():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1899-01-01",
            "--time", "12:00",
            "--gender", "M",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode != 0


def test_cli_skeleton_with_year_and_month():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "skeleton",
            "--year", "2026",
            "--month", "6",
            "--focus", "career",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "Annual-Luck Window" in result.stdout
    assert "Monthly-Luck Window" in result.stdout
    assert "2026-06" in result.stdout
    assert "Focus Requested by Querent: career" in result.stdout


def test_cli_skeleton_with_year_month_and_day():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "skeleton",
            "--year", "2026",
            "--month", "6",
            "--day", "21",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "Daily-Luck Window" in result.stdout
    assert "2026-06-21" in result.stdout


def test_cli_premium_output():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "premium",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "# Korean Four Pillars of Destiny · Saju Reading" in result.stdout
    assert "## Career & Wealth" in result.stdout
    assert "[ENGINE DRAFT — REVIEW REQUIRED]" not in result.stdout, (
        "CLI premium output still contains [ENGINE DRAFT] placeholders"
    )


def test_cli_premium_output_file(tmp_path):
    out = tmp_path / "premium.md"
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "premium",
            "--output-file", str(out),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert f"Premium report written to {out}" in result.stdout
    text = out.read_text(encoding="utf-8")
    assert "## Chart at a Glance" in text
    assert "## Practical Guidance Summary" in text


def test_cli_requires_utc_offset():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--gender", "F",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode != 0
    assert "--utc-offset" in result.stderr


def test_cli_custom_daeun_periods():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "json",
            "--daeun-periods", "10",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    import json
    data = json.loads(result.stdout)
    assert len(data["daeun"]) == 10


def test_cli_suspicious_city_longitude_warning():
    # Pallipat geocodes to ~76.33°E, which is >5° from the standard 82.5°E meridian.
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--city", "Pallipat",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "Warning:" in result.stderr
    assert "Pallipat" in result.stderr


def test_cli_deprecated_skeleton_file_warning(tmp_path):
    out = tmp_path / "skeleton.md"
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "skeleton",
            "--skeleton-file", str(out),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "--skeleton-file is deprecated" in result.stderr
    assert out.exists()


def test_cli_reference_date_flows_to_premium_output():
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "premium",
            "--year", "2030",
            "--month", "6",
            "--day", "15",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "2030" in result.stdout
    # The "What This Year Means for You" paragraph should mention the reference year.
    assert "in June 2030" in result.stdout or "2030 is a" in result.stdout


# ── E4: regression tests for prior P0–P4 fixes ─────────────────────────────


def test_cli_json_output_has_no_sajupy_stdout_warning():
    """P0 A6: sajupy warning must go to stderr, not stdout, so JSON stays valid."""
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--city", "Pallipat",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "json",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    # stdout must be valid JSON starting with '{'
    assert result.stdout.strip().startswith("{"), (
        f"stdout does not start with '{{': {result.stdout[:200]!r}"
    )
    import json
    data = json.loads(result.stdout)
    assert data["day_master"]


def test_cli_default_tier_is_essential():
    """P0: --tier default must be essential (not legacy reading)."""
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "premium",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode == 0, result.stderr
    assert "Essential Report" in result.stdout


def test_cli_premium_requires_gender():
    """P0 B22: --format premium without --gender must error cleanly."""
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--format", "premium",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode != 0
    assert "--gender is required" in result.stderr


@pytest.mark.parametrize("bad_offset", ["25", "-15"])
def test_cli_rejects_out_of_range_utc_offset(bad_offset):
    """P0 C1: utc_offset must be in [-12, 14]."""
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--gender", "F",
            "--utc-offset", bad_offset,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode != 0


def test_cli_rejects_non_positive_daeun_periods():
    """P0 C2: --daeun-periods must be positive."""
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--daeun-periods", "0",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode != 0


@pytest.mark.parametrize("bad_month,bad_day", [("13", "1"), ("6", "32")])
def test_cli_rejects_invalid_reference_month_day(bad_month, bad_day):
    """P0 C3: --month/--day skeleton reference values must be in range."""
    result = subprocess.run(
        [
            "python3", "-m", "saju_engine",
            "--date", "1993-12-11",
            "--time", "02:45",
            "--longitude", "79.32",
            "--utc-offset", "5.5",
            "--gender", "F",
            "--format", "skeleton",
            "--month", bad_month,
            "--day", bad_day,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=ENV,
    )
    assert result.returncode != 0


# ── Phase 2: direct unit tests for main() without subprocess ─────────────────


def test_main_table_output_directly():
    from saju_engine.cli import main

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(
        ["--date", "1993-12-11", "--time", "02:45", "--longitude", "79.32",
         "--utc-offset", "5.5", "--gender", "F", "--format", "table"],
        stdout=stdout,
        stderr=stderr,
    )
    assert code == 0
    out = stdout.getvalue()
    assert "癸酉" in out
    assert "丙寅" in out


def test_main_json_output_directly():
    from saju_engine.cli import main

    stdout = io.StringIO()
    code = main(
        ["--date", "1991-10-03", "--time", "23:45", "--longitude", "79.19",
         "--utc-offset", "5.5", "--gender", "M", "--format", "json"],
        stdout=stdout,
        stderr=io.StringIO(),
    )
    assert code == 0
    data = json.loads(stdout.getvalue())
    assert data["day_master"]
    day_pillar = next(p for p in data["pillars"] if p["position"] == "day")
    assert "丙午" in day_pillar["combined"]


def test_main_requires_utc_offset_directly():
    from saju_engine.cli import main

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = main(
        ["--date", "1993-12-11", "--time", "02:45", "--gender", "F"],
        stdout=stdout,
        stderr=stderr,
    )
    assert code == 2
    assert "--utc-offset" in stderr.getvalue()


def test_main_premium_requires_gender_directly():
    from saju_engine.cli import main

    stderr = io.StringIO()
    code = main(
        ["--date", "1993-12-11", "--time", "02:45", "--longitude", "79.32",
         "--utc-offset", "5.5", "--format", "premium"],
        stdout=io.StringIO(),
        stderr=stderr,
    )
    assert code == 2
    assert "--gender is required" in stderr.getvalue()
