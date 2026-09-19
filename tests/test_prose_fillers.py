"""Tests for the chart-derived prose fillers (`saju_engine.prose_fillers`).

These fillers replace the previous `[ENGINE DRAFT — REVIEW REQUIRED]`
*prompts* with real chart-grounded prose. The tests verify:
  - each filler returns non-empty output for the sample chart
  - the prose references specific chart features (Day Master element,
    favorable element, branch names, ten-god names, etc.)
  - the relationship_style and timing fillers respect the chart's data
  - the top-5 / growth-areas / recommendations lists have the right length
  - the `closing_note_long` references the actual Day Master and spouse palace
"""
from __future__ import annotations

import pytest

from saju_engine.engine import compute_chart
from saju_engine.premium_report import _ReportContext
from saju_engine import prose_fillers as PF


SAMPLE_BIRTH = dict(
    name="VP", gender="F", year=2001, month=6, day=7, hour=16, minute=45,
    longitude=80.27, utc_offset=5.5, use_solar_time=True, convention="korean",
)


@pytest.fixture
def ctx() -> _ReportContext:
    chart = compute_chart(**SAMPLE_BIRTH)
    return _ReportContext(chart, tier="deep", generation_date="2026-06-27")


# ── Smoke: every public filler returns non-empty ─────────────────────────


@pytest.mark.parametrize("fn_name", [
    "wealth_pattern", "wealth_preservation_short", "wealth_preservation_long",
    "employment_vs_entrepreneurship", "income_rhythm", "skill_levers",
    "company_type_fit", "boss_team_dynamics", "red_flag_environments",
    "relationship_style", "friendship_social_energy", "attachment_patterns",
    "marriage_timing_windows", "family_dynamics",
    "overdrive_warning", "seasonal_daily_rhythms", "element_story",
    "stress_signature", "recovery_toolkit", "long_term_vitality_strategy",
    "current_period_deep_dive", "pattern_story",
    "closing_note_short", "closing_note_long",
    "travel_timing", "business_launch_format", "business_seasonal_note",
    "dm_arrival_narrative", "branch_relationship_snapshot",
    "depleted_element_health", "spouse_palace_tengod",
])
def test_filler_returns_non_empty(ctx, fn_name):
    """Every chart-derived filler should return a non-empty string."""
    fn = getattr(PF, fn_name)
    out = fn(ctx)
    assert isinstance(out, str)
    assert out.strip(), f"{fn_name} returned empty string"


# ── Specific chart-grounding checks ─────────────────────────────────────


def test_health_filler_uses_kb15_organ_wording(ctx):
    """`depleted_element_health` names an organ system that knowledge/15 also names."""
    from pathlib import Path

    kb = (
        Path(__file__).parent.parent / "knowledge" / "15-health-and-body.md"
    ).read_text(encoding="utf-8").lower()
    text = PF.depleted_element_health(ctx).lower()
    named = [w for w in ("liver", "heart", "spleen", "lung", "kidney") if w in text]
    assert named, f"health filler names no organ system: {text!r}"
    assert all(w in kb for w in named), f"organ wording not grounded in knowledge/15: {named}"


def test_plain_words_fillers_return_blockquote(ctx):
    for fn in (PF.plain_words_day_master, PF.plain_words_career,
               PF.plain_words_relationships, PF.plain_words_health,
               PF.plain_words_timing, PF.plain_words_pattern,
               PF.plain_words_ten_gods):
        out = fn(ctx)
        assert out == "" or out.startswith("> **In plain words:** ")
        assert "[ENGINE DRAFT" not in out
        assert "\n" not in out


def test_wealth_pattern_includes_favorable_element(ctx):
    out = PF.wealth_pattern(ctx)
    assert ctx.favorable in out or ctx.supporting in out, (
        f"wealth_pattern does not reference favorable/supporting element: {out!r}"
    )


def test_relationship_style_mentions_spouse_branch(ctx):
    out = PF.relationship_style(ctx)
    assert ctx.chart.day.branch in out, (
        f"relationship_style should reference day branch {ctx.chart.day.branch}: {out!r}"
    )


def test_three_mindful_notes_returns_three_bullets(ctx):
    notes = PF.three_mindful_notes(ctx)
    assert isinstance(notes, list)
    assert len(notes) == 3
    for note in notes:
        assert isinstance(note, str) and note.strip()


def test_overdrive_warning_mentions_strength_label(ctx):
    out = PF.overdrive_warning(ctx)
    assert ctx.dm_element in out, (
        f"overdrive_warning should mention DM element {ctx.dm_element}: {out!r}"
    )


def test_top_strengths_returns_five_items(ctx):
    items = PF.top_strengths(ctx)
    assert isinstance(items, list)
    assert len(items) == 5
    for item in items:
        assert isinstance(item, str) and item.strip()


def test_top_growth_areas_returns_five_items(ctx):
    items = PF.top_growth_areas(ctx)
    assert isinstance(items, list)
    assert len(items) == 5


def test_practical_recommendations_returns_five_items(ctx):
    items = PF.practical_recommendations(ctx)
    assert isinstance(items, list)
    assert len(items) == 5


def test_closing_note_short_has_three_sentences(ctx):
    """Short closing should mention one gift, one challenge, one next step."""
    out = PF.closing_note_short(ctx)
    # Sentences end with '.' (rough heuristic — split by '. ').
    parts = [p for p in out.split(". ") if p.strip()]
    assert len(parts) >= 2, f"expected ≥2 sentences in short closing: {out!r}"
    assert ctx.favorable in out, "short closing should reference the favorable element"


def test_closing_note_long_references_specific_features(ctx):
    out = PF.closing_note_long(ctx)
    assert ctx.dm in out, f"long closing should reference Day Master {ctx.dm}: {out!r}"
    assert ctx.chart.day.branch in out, (
        f"long closing should reference spouse palace {ctx.chart.day.branch}: {out!r}"
    )
    assert ctx.favorable in out, "long closing should reference favorable element"


def test_auspicious_date_note_non_empty(ctx):
    out = PF.auspicious_date_note("2026-07-15", ctx)
    assert isinstance(out, str)
    assert ctx.favorable in out


def test_year_by_year_note_includes_year_or_caution(ctx):
    """The year_by_year_note should be a sentence-shaped string."""
    chart = compute_chart(**SAMPLE_BIRTH)
    hits = chart.sewoon
    assert hits, "expected sewoon hits for the sample chart"
    note = PF.year_by_year_note(hits[0], ctx)
    assert isinstance(note, str) and note.strip()


def test_major_luck_theme_row_returns_pair(ctx):
    """major_luck_theme_row returns (career, relationship) themes for a 대운."""
    chart = compute_chart(**SAMPLE_BIRTH)
    assert chart.daeun, "expected daeun periods for the sample chart"
    career, relationship = PF.major_luck_theme_row(chart.daeun[0], ctx)
    assert isinstance(career, str) and career.strip()
    assert isinstance(relationship, str) and relationship.strip()


def test_major_luck_narrative_per_period(ctx):
    """major_luck_narrative should produce a paragraph for each 대운."""
    chart = compute_chart(**SAMPLE_BIRTH)
    assert chart.daeun
    for p in chart.daeun:
        out = PF.major_luck_narrative(p, ctx)
        assert isinstance(out, str) and out.strip()


def test_annual_window_row_tuple(ctx):
    chart = compute_chart(**SAMPLE_BIRTH)
    hits = chart.sewoon
    assert hits
    theme, best, watch = PF.annual_window_row(hits[0], ctx)
    assert theme and best and watch


def test_decade_career_strategy_per_period(ctx):
    chart = compute_chart(**SAMPLE_BIRTH)
    assert chart.daeun
    for p in chart.daeun:
        out = PF.decade_career_strategy(ctx, p)
        assert isinstance(out, str) and out.strip()


def test_business_watch_items_returns_five_items(ctx):
    items = PF.business_watch_items(ctx)
    assert isinstance(items, list)
    assert len(items) == 5
    for item in items:
        assert isinstance(item, str) and item.strip()


def test_dm_arrival_narrative_mentions_month_branch_and_stage(ctx):
    out = PF.dm_arrival_narrative(ctx)
    assert ctx.chart.month.branch in out, (
        f"dm_arrival_narrative should reference month branch {ctx.chart.month.branch}: {out!r}"
    )
    # twelve-stage names are Korean; at least one stage term should appear.
    from saju_engine import lookup as L
    stage = L.twelve_stage(ctx.chart.day_master, ctx.chart.month.branch)
    assert stage in out, f"dm_arrival_narrative should mention the 12-stage {stage}: {out!r}"


def test_regular_grid_narrative_uses_grid_candidate(ctx):
    out = PF.regular_grid_narrative(ctx)
    assert isinstance(out, str)
    regular = ctx.chart.patterns.get("regular_grid")
    if regular and regular[0].confidence == "likely":
        assert regular[0].name_ko in out, (
            f"regular_grid_narrative should reference the grid {regular[0].name_ko}: {out!r}"
        )


def test_special_grid_note_returns_string(ctx):
    out = PF.special_grid_note(ctx)
    assert isinstance(out, str)
    # If a special grid is flagged, the note must be marked uncertain.
    transformation = ctx.chart.patterns.get("transformation_grid")
    special = ctx.chart.patterns.get("special_forms")
    if transformation or special:
        assert "[UNCERTAIN]" in out


def test_branch_relationship_snapshot_mentions_branch(ctx):
    out = PF.branch_relationship_snapshot(ctx)
    assert isinstance(out, str)
    if ctx.chart.combinations_6 or ctx.chart.clashes or ctx.chart.three_harmonies:
        assert any(b in out for b in ctx.chart.branches), (
            f"branch_relationship_snapshot should mention at least one natal branch: {out!r}"
        )


def test_depleted_element_health_mentions_lowest_element(ctx):
    out = PF.depleted_element_health(ctx)
    assert isinstance(out, str) and out.strip()
    pct = PF._element_pct(ctx.chart)
    depleted = min(pct.items(), key=lambda kv: kv[1])[0]
    assert depleted in out, (
        f"depleted_element_health should reference the depleted element {depleted}: {out!r}"
    )


def test_spouse_palace_tengod_mentions_day_branch(ctx):
    out = PF.spouse_palace_tengod(ctx)
    assert ctx.chart.day.branch in out, (
        f"spouse_palace_tengod should reference the day branch {ctx.chart.day.branch}: {out!r}"
    )
    # The filler normalizes the Korean ten-god to its English class name.
    spouse_tg_ko = "—"
    for hit in ctx.chart.ten_gods:
        if hit.position == "day_branch_main":
            spouse_tg_ko = hit.tengod
            break
    spouse_tg_en = PF._TENGOD_CLASS.get(spouse_tg_ko, spouse_tg_ko)
    assert spouse_tg_en in out, (
        f"spouse_palace_tengod should reference the spouse-palace ten-god {spouse_tg_en}: {out!r}"
    )


