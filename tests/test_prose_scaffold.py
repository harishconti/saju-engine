"""Tests for the engine-driven interpretive prose scaffold."""
from __future__ import annotations

from saju_engine.engine import compute_chart
from saju_engine.prose_scaffold import _current_time_draft, generate_prose_scaffold


def test_scaffold_has_all_sections():
    c = compute_chart(
        name="Tester", gender="F",
        year=1993, month=12, day=11, hour=10, minute=0,
        city="Seoul", utc_offset=9, use_solar_time=True,
    )
    scaffold = generate_prose_scaffold(c)
    expected_keys = {
        "day_master_strength", "yongsin", "personality",
        "career_wealth", "relationships", "health", "current_time_themes",
    }
    assert set(scaffold.keys()) == expected_keys
    for v in scaffold.values():
        assert isinstance(v, str) and v.strip()


def test_generate_plain_words_keys_and_format():
    from saju_engine.prose_scaffold import generate_plain_words
    c = compute_chart(
        name="T", gender="M", year=1991, month=10, day=3,
        hour=23, minute=45, longitude=79.19, utc_offset=5.5,
        use_solar_time=True, convention="korean",
    )
    pw = generate_plain_words(c)
    assert set(pw) == {"personality", "career_wealth", "relationships", "health", "current_time_themes"}
    for v in pw.values():
        assert v == "" or v.startswith("> **In plain words:** ")


def test_scaffold_mentions_day_master_and_yongsin():
    c = compute_chart(
        name="Tester", gender="M",
        year=1991, month=10, day=3, hour=23, minute=45,
        longitude=79.19, utc_offset=5.5, use_solar_time=True,
    )
    scaffold = generate_prose_scaffold(c)
    assert c.day_master in scaffold["day_master_strength"]
    assert "용신" in scaffold["yongsin"]
    # Health disclaimer must be present
    assert "not a medical diagnosis" in scaffold["health"]


def test_scaffold_relationships_mentions_spouse_palace():
    c = compute_chart(
        name="Tester", gender="F",
        year=2002, month=6, day=7, hour=16, minute=45,
        city="Mysore", utc_offset=5.5, use_solar_time=True,
    )
    scaffold = generate_prose_scaffold(c)
    assert "spouse palace" in scaffold["relationships"]
    assert c.day.branch in scaffold["relationships"]


def test_skeleton_includes_scaffold_by_default():
    from saju_engine.skeleton import generate_skeleton
    c = compute_chart(
        name="Tester", gender="F",
        year=1993, month=12, day=11, hour=10, minute=0,
        city="Seoul", utc_offset=9, use_solar_time=True,
    )
    s = generate_skeleton(c)
    assert "engine-drafted scaffolds" in s
    assert "Day Master Strength Reasoning (draft)" in s
    assert "Favorable Element (용신) & Reasoning (draft)" in s


def test_skeleton_can_disable_scaffold():
    from saju_engine.skeleton import generate_skeleton
    c = compute_chart(
        name="Tester", gender="F",
        year=1993, month=12, day=11, hour=10, minute=0,
        city="Seoul", utc_offset=9, use_solar_time=True,
    )
    s = generate_skeleton(c, include_prose_scaffold=False)
    assert "engine-drafted scaffolds" not in s
    assert "Day Master Strength Reasoning (draft)" not in s
    assert "_(argue from season" in s


def test_current_time_draft_labels_the_saju_year_not_gregorian():
    """N-11 (2026-09-26 audit): "As of {year}..." used the raw Gregorian
    reference year. For a reference date between Jan 1 and 입춀 (~Feb 4),
    the active 세운 is still the PRIOR year's — the pillar shown was already
    correct (chart.sewoon's window keys off the same Gregorian year), but
    the label said e.g. "As of 2024" over a pillar that is actually 2023's,
    contradicting the chart's own 입춀-based age/대운 timing."""
    c = compute_chart(
        name="Tester", gender="F",
        year=1993, month=12, day=11, hour=10, minute=0,
        city="Seoul", utc_offset=9, use_solar_time=True,
        reference_year=2024, reference_month=1, reference_day=15,
    )
    draft = _current_time_draft(c)
    assert "As of 2023," in draft
    assert "As of 2024," not in draft
