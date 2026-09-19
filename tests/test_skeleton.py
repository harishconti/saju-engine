"""Tests for the engine-driven markdown skeleton generator."""
from __future__ import annotations

from saju_engine.engine import compute_chart
from saju_engine.skeleton import generate_skeleton


def test_skeleton_has_glossary_and_glosses():
    c = compute_chart(
        name="T", gender="M", year=1991, month=10, day=3,
        hour=23, minute=45, longitude=79.19, utc_offset=5.5,
        use_solar_time=True, convention="korean",
    )
    s = generate_skeleton(c, reference_year=2026)
    assert "## What the Terms Mean" in s
    assert "> **In plain words:**" in s


def test_skeleton_contains_key_sections():
    c = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
    )
    s = generate_skeleton(c, focus="career", reference_year=2026)
    assert "# Saju Reading Skeleton" in s
    assert "Four Pillars" in s
    assert "Day Master (일간): 丙" in s
    assert "Strength heuristic" in s
    assert "Ten-God Distribution" in s
    assert "Major Luck Periods" in s
    assert "Annual-Luck Window" in s
    assert "Monthly-Luck Window" in s
    assert "Focus Requested by Querent: career" in s


def test_skeleton_annual_window_populated():
    c = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
    )
    s = generate_skeleton(c, reference_year=2026)
    assert "| 2026 | 丙午" in s
    assert "| 2027 | 丁未" in s


def test_skeleton_monthly_window_populated():
    c = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
    )
    s = generate_skeleton(c, reference_year=2026, reference_month=6)
    assert "Monthly-Luck Window" in s
    # Center month should be present as YYYY-MM.
    assert "2026-06" in s


def test_skeleton_branch_relationships_rendered():
    c = compute_chart(
        name="Sruthi", gender="F",
        year=1993, month=12, day=11, hour=2, minute=45,
        longitude=79.32, utc_offset=5.5, use_solar_time=True,
    )
    s = generate_skeleton(c)
    assert "六合" in s or "三合" in s or "六沖" in s
