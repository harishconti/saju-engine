"""Tests for the engine-driven interpretive prose scaffold."""
from __future__ import annotations

from saju_engine.engine import compute_chart
from saju_engine.prose_scaffold import generate_prose_scaffold


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
