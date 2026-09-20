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


def test_relationship_style_uses_real_tengod_implication_not_generic_fallback(ctx):
    """Regression for the 2026-09-19 bug: the personalized implication dict
    in relationship_style() was keyed by simplified class names ("Output",
    "Companion", ...) but looked up using the full English gloss
    ("Hurting Officer (傷官)"), which never matches any key — every chart
    fell through to the same generic "you bring the querent's full nature
    into the partnership" sentence regardless of its actual spouse-palace
    ten-god. Confirmed identical fallback text across every real candidate
    report (4+ different actual ten-gods, same sentence every time) before
    this fix. The sample fixture chart's spouse palace is 편인 (Indirect
    Resource), which should now produce its specific implication sentence.
    """
    out = PF.relationship_style(ctx)
    assert "bring the querent's full nature" not in out, (
        f"relationship_style regressed to the generic fallback: {out!r}"
    )
    assert "spark your curiosity and bring unexpected insights" in out, (
        f"sample chart's spouse-palace ten-god is 편인 (Indirect Resource); "
        f"expected its specific implication text, got: {out!r}"
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


def test_year_by_year_note_includes_year_or_caution(ctx):
    """The year_by_year_note should be a sentence-shaped string."""
    chart = compute_chart(**SAMPLE_BIRTH)
    hits = chart.sewoon
    assert hits, "expected sewoon hits for the sample chart"
    note = PF.year_by_year_note(hits[0], ctx)
    assert isinstance(note, str) and note.strip()


# ── R12 — annual activation layer (천간합 / 충/합/형/파/해) never surfaced ──
# ── (found 2026-09-20, external report review, 3rd pass) ─────────────────


def test_annual_activation_note_surfaces_2026_activations_for_harish():
    """Confirmed live: Harish's 2026 (丙午) forms 병신합수 with his 辛 Day
    Master, and 午 harms his natal 丑 hour branch — knowledge/08 Part 2 step
    3 requires checking both, but the engine computed them and no report
    prose ever read the result."""
    from saju_engine import sewoon as SE
    chart = compute_chart(
        name="harish-r12-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    hit = SE.build_sewoon_range(chart.day_master, chart.branches, 2026, 2026)[0]
    note = PF.annual_activation_note(hit)
    assert "병신합수" in note
    assert "해 (harm)" in note


def test_annual_activation_note_empty_when_nothing_activates():
    from saju_engine.sewoon import derive_sewoon
    hit = derive_sewoon("甲", ["寅", "卯"], 2099)  # unlikely to activate anything
    if not hit.stem_combinations and not hit.activated_branches:
        assert PF.annual_activation_note(hit) == ""


def test_year_by_year_note_appends_activation_when_present(ctx):
    from saju_engine import sewoon as SE
    chart = compute_chart(
        name="harish-r12-year-note-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    from saju_engine.premium_report import _ReportContext
    harish_ctx = _ReportContext(chart, tier="deep", generation_date="2026-09-20")
    hit = SE.build_sewoon_range(chart.day_master, chart.branches, 2026, 2026)[0]
    note = PF.year_by_year_note(hit, harish_ctx)
    assert "Also active this year" in note
    assert "병신합수" in note


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


# ── Regression: ten-god class must come from the Korean code, not an ─────
# ── English-gloss substring match (found 2026-09-19, external review)  ───

class _FakePeriod:
    """Minimal stand-in for a DaeunPeriod, just the fields these fillers read."""
    def __init__(self, stem_tengod, stem_tengod_en, start_age=30, end_age=39,
                 combined="辛亥", branch_element="Water", stem_element="Water",
                 favorable_status=None):
        self.stem_tengod = stem_tengod
        self.stem_tengod_en = stem_tengod_en
        self.start_age = start_age
        self.end_age = end_age
        self.combined = combined
        self.branch_element = branch_element
        self.stem_element = stem_element
        self.favorable_status = favorable_status  # deliberately unused by the fix


@pytest.mark.parametrize("ko,en,expected_career_substring", [
    ("편관", "Seven Killings (偏官)", "structured career moves"),  # Authority
    ("정관", "Direct Officer (正官)", "structured career moves"),  # Authority
    ("식신", "Eating God (食神)", "creative output"),              # Output
    ("상관", "Hurting Officer (傷官)", "creative output"),          # Output
    ("비견", "Companion (比肩)", "peer-driven"),                   # Companion
    ("겁재", "Robber (劫財)", "peer-driven"),                       # Companion
])
def test_major_luck_theme_row_classifies_by_korean_code_not_english_substring(ko, en, expected_career_substring):
    """Regression for the 2026-09-19 bug: 편관 ('Seven Killings') and 식신
    ('Eating God') contain no keyword the old code matched on and silently
    fell through to the Companion/peer branch; 상관 ('Hurting Officer')
    wrongly matched the Authority branch via the substring 'Officer' even
    though 상관 is 식상 (Output), not 관성 (Authority). Confirmed live in
    Harish's shipped report (10-19 and 2027 both 편관; 60-69 and 2032/2033
    both 상관/식신) before this fix.
    """
    p = _FakePeriod(stem_tengod=ko, stem_tengod_en=en)
    ctx = {"favorable": "Water", "supporting": "Metal"}
    career, _relationship = PF.major_luck_theme_row(p, ctx)
    assert expected_career_substring in career, (
        f"{ko} ({en}) should classify as giving {expected_career_substring!r}, got {career!r}"
    )


@pytest.mark.parametrize("ko,en,expected_best_substring", [
    ("편관", "Seven Killings (偏官)", "career moves, credentials"),
    ("식신", "Eating God (食神)", "creative production"),
    ("상관", "Hurting Officer (傷官)", "creative production"),
])
def test_annual_window_row_classifies_by_korean_code_not_english_substring(ko, en, expected_best_substring):
    """Same regression as above, for the annual-window "Best Uses" column."""
    h = _FakePeriod(stem_tengod=ko, stem_tengod_en=en)
    h.stem = "辛"
    h.year = 2030
    ctx = {"favorable": "Water", "supporting": "Metal"}
    _theme, best, _watch = PF.annual_window_row(h, ctx)
    assert expected_best_substring in best, (
        f"{ko} ({en}) should classify as giving {expected_best_substring!r}, got {best!r}"
    )


def test_income_rhythm_does_not_treat_hidden_robber_as_wealth_rooted():
    """Regression for the 2026-09-19 bug: `if "재" in tg` also matches 겁재
    (Robber, a 비겁-class ten-god), which contains the character "재" but is
    not 재성 (Wealth) at all.

    Constructs a chart with a VISIBLE 정재 (so `direct` is legitimately True)
    but only a hidden main-position 겁재 (no real hidden 정재/편재 at all) — a
    case where the pre-fix code would wrongly set `wealth_rooted = True` from
    the 겁재 and claim "The Direct Wealth stem is rooted in a branch," which
    is false for this chart.
    """
    import types
    from saju_engine import lookup as L

    day_master = "庚"  # Yang Metal
    assert L.ten_god(day_master, "乙") == "정재"  # visible wealth stem
    assert L.ten_god(day_master, "辛") == "겁재"  # the hidden stem that used to false-trigger
    assert "재" in "겁재"  # the substring collision the old code depended on

    fake_pillar_hour = types.SimpleNamespace(hidden_stems=[("main", "辛")])  # 겁재 only
    fake_pillar_other = types.SimpleNamespace(hidden_stems=[])
    fake_chart = types.SimpleNamespace(
        day_master=day_master,
        stems=["乙", "庚", "庚", "庚"],  # the visible 정재 (乙) plus 3 filler self-stems
        pillars=[fake_pillar_other, fake_pillar_other, fake_pillar_other, fake_pillar_hour],
        ten_gods=[types.SimpleNamespace(tengod="정재")],  # the one visible wealth stem
    )
    ctx = {"chart": fake_chart}
    out = PF.income_rhythm(ctx)
    assert "rooted in a branch" not in out, (
        f"income_rhythm should not claim wealth is rooted when only a hidden "
        f"겁재 (not a real 정재/편재) was found: {out!r}"
    )


def test_income_rhythm_does_not_claim_rooted_for_hidden_only_direct_wealth():
    """Regression for the 2026-09-19 bug (external report review, 2nd pass):
    income_rhythm used to claim "The Direct Wealth stem is rooted in a
    branch" whenever ANY 정재 was found via `_class_counts` (which counts
    visible AND hidden stems), even when the ONLY 정재 in the whole chart is
    itself a hidden stem with no visible counterpart at all — "rooted"
    specifically means a visible stem echoed by a hidden one, which cannot
    be true if there is no visible stem to begin with.

    Harish's real chart is exactly this case: his only 정재 is 甲, hidden as
    the middle qi of the day branch 亥; no stem in his four visible pillars
    (壬乙辛己) is 정재.
    """
    from saju_engine import lookup as L

    chart = compute_chart(
        name="harish-income-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    assert not any(L.ten_god(chart.day_master, s) == "정재" for s in chart.stems), (
        "test premise: Harish must have no VISIBLE 정재 stem"
    )
    out = PF.income_rhythm({"chart": chart})
    assert "rooted in a branch" not in out, (
        f"must not claim a hidden-only Direct Wealth stem is 'rooted': {out!r}"
    )
    assert "hidden stem" in out, f"should name the actual (hidden-only) situation: {out!r}"




# ── relationship_timing_row gender adaptation — added 2026-09-19, external ──
# ── report review, 2nd pass ──────────────────────────────────────────────


def test_relationship_timing_row_male_marriage_code_is_wealth_not_officer():
    """For a male Day Master, 재성 (Wealth) is the classical spouse indicator
    (자평진전, per knowledge/11-gunghap.md §G / compat.py::_gendered_spouse_star_note),
    not 관성. Direct Wealth years should carry the marriage-coded theme;
    Direct Officer must NOT (that was the bug — a female-chart template
    applied unconditionally)."""
    male_wealth_note = PF.relationship_timing_row(2026, "甲子", "Direct Wealth", gender="M")
    assert "marriage" in male_wealth_note
    male_officer_note = PF.relationship_timing_row(2026, "甲子", "Direct Officer", gender="M")
    assert "marriage" not in male_officer_note


def test_relationship_timing_row_female_marriage_code_is_officer():
    """For a female Day Master, 정관 (Direct Officer) remains the classical
    spouse indicator — this is the one case the old code got right, and
    must not regress."""
    female_officer_note = PF.relationship_timing_row(2026, "甲子", "Direct Officer", gender="F")
    assert "marriage" in female_officer_note
    female_wealth_note = PF.relationship_timing_row(2026, "甲子", "Direct Wealth", gender="F")
    assert "marriage" not in female_wealth_note


def test_relationship_timing_row_declines_gendered_read_when_gender_unknown():
    """No gender supplied -> neutral theme, not a silently-defaulted guess."""
    note = PF.relationship_timing_row(2026, "甲子", "Direct Officer", gender=None)
    assert "marriage" not in note


# ── R10 — dominant ten-god class must not mix grouping levels ────────────
# ── (found 2026-09-20, external report review, 3rd pass) ─────────────────


@pytest.fixture
def harish_chart():
    return compute_chart(
        name="harish-r10-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )


def test_class_counts_no_longer_merges_eating_god_and_hurting_officer(harish_chart):
    """`_TENGOD_CLASS` used to map both 식신 and 상관 to one merged "Output"
    key while every other class stayed split by yin/yang variant — an
    inconsistent grouping level that inflated Output's count relative to
    the (correctly split) other classes, and silently mismatched every
    dict keyed by class name against tengod strings from `sewoon.py` /
    `daeun_overlay.py` (which already use "Eating God" / "Hurting Officer").
    """
    counts = PF._class_counts(harish_chart)
    assert "Output" not in counts
    assert counts["Hurting Officer"] == 3
    assert counts["Eating God"] == 1


def test_variant_level_dominant_class_is_the_true_leader_not_a_merged_tie(harish_chart):
    """Confirmed live: `_dominant_classes` used to report "Output (4)" as the
    top variant, produced only by merging 식신(1) and 상관(3) — hiding that
    상관 (Hurting Officer) alone is the true, uniquely-dominant variant (3),
    ahead of every other variant (all <= 2)."""
    dominant = PF._dominant_classes(harish_chart, 1)
    assert dominant[0] == ("Hurting Officer", 3)


def test_grouped_dominant_classes_surfaces_full_three_way_tie(harish_chart):
    """Confirmed live: Harish's true 5-class distribution is a three-way tie
    at 4 (비겁/식상/인성), with 재성=2 and 관성=1 trailing — but the old
    `_dominant_classes(chart, 2)` reported "Output (4), Robber (2)",
    dropping two of the three tied leaders and surfacing a class (재성)
    that isn't even in the true top tier. `_grouped_dominant_classes` must
    report all three tied leaders at the correct count."""
    top3 = dict(PF._grouped_dominant_classes(harish_chart, 3))
    assert top3 == {"Output": 4, "Companion": 4, "Resource": 4}


def test_closing_note_long_and_friendship_agree_with_top_strengths_leader(harish_chart):
    """The reviewer's exact complaint: `closing_note_long` claimed
    "Output (4), Robber (2)" while `top_strengths` (a separate function,
    same chart) concluded "Direct Resource-dominant" — two different,
    inconsistent claims about what dominates the same ten-god profile.
    After the fix, the class-level narrative (closing_note_long,
    friendship_social_energy) must draw from the same properly-grouped
    counts, and the variant-level narrative (top_strengths) must name the
    true leading variant (Hurting Officer) rather than a tied non-leader."""
    ctx = _ReportContext(harish_chart, tier="deep", generation_date="2026-09-20")
    closing = PF.closing_note_long(ctx)
    friendship = PF.friendship_social_energy(ctx)
    for out in (closing, friendship):
        assert "Output (4)" in out and "Companion (4)" in out, (
            f"expected the true tied class-level leaders (Output/Companion at 4 each): {out!r}"
        )
    strengths = PF.top_strengths(ctx)
    assert any("Hurting Officer-dominant" in s for s in strengths), (
        f"top_strengths should name the true, uniquely-leading variant (Hurting Officer, 3) "
        f"as its first dominant-class pick, not a merged or tied-non-leader name: {strengths!r}"
    )
