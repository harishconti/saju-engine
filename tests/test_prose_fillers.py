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


# ── E-8 — relationship_style ignored gender entirely (found 2026-09-25, ──
# ── external report review) ───────────────────────────────────────────


def test_relationship_style_names_gendered_spouse_star_female(ctx):
    """The sample fixture chart is female; her 부성 (관성, husband star)
    appears at three positions (year branch, month branch, hour stem) —
    confirmed independently against chart.ten_gods."""
    out = PF.relationship_style(ctx)
    assert "부성 (관성, husband star)" in out
    assert "자평진전" in out


def test_relationship_style_names_gendered_spouse_star_male_in_palace():
    """Harish (male) has his 처성 (재성, wife star) at the month stem AND
    inside the spouse palace itself (day branch's middle hidden stem, 甲) —
    the classically stronger placement, which must be named explicitly."""
    chart = compute_chart(
        name="Harish", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5, convention="korean",
    )
    ctx2 = _ReportContext(chart, tier="deep", generation_date="2026-09-25")
    out = PF.relationship_style(ctx2)
    assert "처성 (재성, wife star)" in out
    assert "including the spouse palace itself" in out


def test_relationship_style_gendered_spouse_star_absent_case():
    """A chart with no gender set must not attempt the gendered reading at
    all (the classical mapping only applies once gender is known)."""
    chart = compute_chart(
        name="NoGender",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5, convention="korean",
    )
    ctx2 = _ReportContext(chart, tier="deep", generation_date="2026-09-25")
    assert PF.gendered_spouse_star_note(ctx2) == ""


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


# ── E-6 (2026-09-25 audit) — harmony completions never surfaced in prose ──


def test_annual_activation_note_surfaces_full_samhap_completion():
    """2024's real annual pillar 甲辰 completes 申子辰 (Water) 삼합 against
    natal 申+子 — this 3-branch fact was never checked anywhere before E-6."""
    from saju_engine.sewoon import derive_sewoon
    hit = derive_sewoon("丙", ["申", "子"], 2024)
    note = PF.annual_activation_note(hit)
    assert "completes" in note and "삼합" in note and "Water" in note
    assert "申子" in note or "子申" in note


def test_annual_activation_note_surfaces_half_samhap_completion():
    """Only 申 present -> 반합 (half), worded distinctly from a full completion."""
    from saju_engine.sewoon import derive_sewoon
    hit = derive_sewoon("丙", ["申"], 2024)
    note = PF.annual_activation_note(hit)
    assert "half-completes" in note and "반합" in note


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


def test_regular_grid_narrative_surfaces_pagyeok_caveat_instead_of_vanishing():
    """E-9 (2026-09-25 audit): Harish's real chart is a 정관격 downgraded to
    'possible' by the new 성격/파격 cross-check (상관견관 present). Before this
    fix, regular_grid_narrative gated strictly on confidence == 'likely', so
    the entire grid theme sentence would have silently vanished from his
    report the moment E-9 could produce a 'possible' regular grid at all —
    it must instead surface the 파격 caveat."""
    chart = compute_chart(
        name="harish-e9-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    grid = chart.patterns["regular_grid"][0]
    assert grid.name_ko == "정관격" and grid.confidence == "possible"
    harish_ctx = _ReportContext(chart, tier="deep", generation_date="2026-09-25")
    out = PF.regular_grid_narrative(harish_ctx)
    assert out != ""
    assert "정관격" in out and "파격" in out and "상관견관" in out


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


# ── E-4 — a skewed support/drain sentence must reconcile with a "Balanced" ──
# ── verdict, not read as contradicting it (found 2026-09-25, external ──────
# ── report review) ──────────────────────────────────────────────────────


def test_strength_reasoning_reconciles_skew_with_balanced_verdict():
    """1970-03-15 10:00 (Korea) is a balanced chart whose drain (5.9) is
    well over 1.3x its support (0.6) — exactly the shape that used to read
    as flatly contradicting "Balanced" ("the drain outweighs the support",
    full stop). The sentence must now explicitly say what reconciles the
    two: the month-stage term pulling the total back into the balanced
    range."""
    chart = compute_chart(
        name="skew-test", gender="M",
        year=1970, month=3, day=15, hour=10, minute=0,
        longitude=127.0, utc_offset=9.0, convention="korean",
    )
    sa = chart.strength_assessment
    assert sa["verdict"] == "balanced"
    support = sa["self_score"] + sa["resource_score"]
    assert sa["drain_score"] > support * 1.3
    text = PF.strength_reasoning({"chart": chart})
    assert "the output/wealth/authority drain outweighs the peer and resource support" in text
    assert "pulls the total back into the balanced range despite that skew" in text


def test_strength_reasoning_no_reconciliation_for_strong_weak_charts():
    """A strong/weak verdict's own skew reinforces its label rather than
    contradicting it, so the reconciling clause must not appear there."""
    chart = compute_chart(
        name="strong-or-weak", gender="M",
        year=1980, month=6, day=15, hour=10, minute=0,
        longitude=127.0, utc_offset=9.0, convention="korean",
    )
    sa = chart.strength_assessment
    assert sa["verdict"] in ("strong", "extreme", "weak", "extreme_weak")
    text = PF.strength_reasoning({"chart": chart})
    assert "pulls the total back into the balanced range" not in text


# ── E-6 residuals (2026-09-26) — stem checks, 삼형, per-branch dedup ──


def _harish_hit(year):
    from saju_engine import sewoon as SE
    chart = compute_chart(
        name="harish-e6-residual", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    return SE.build_sewoon_range(
        chart.day_master, chart.branches, year, year, natal_stems=chart.stems
    )[0]


def test_annual_activation_note_surfaces_natal_stem_combo_and_clash():
    note_2027 = PF.annual_activation_note(_harish_hit(2027))
    assert "정임합목" in note_2027 and "natal **壬** stem" in note_2027
    note_2026 = PF.annual_activation_note(_harish_hit(2026))
    assert "natal **壬** in a **천간충**" in note_2026


def test_annual_activation_note_surfaces_sanhyeong_completion():
    note = PF.annual_activation_note(_harish_hit(2034))
    assert "寅巳申 삼형" in note and "갑기합토" in note


def test_annual_activation_note_keeps_same_relation_against_two_branches():
    """Dedup is per (relationship, natal branch), not per relationship: a
    second harm against a different natal branch must still be named."""
    from saju_engine.sewoon import SeWoonHit
    hit = SeWoonHit(year=2034, stem="甲", branch="寅", activated_branches=[
        ("寅", "巳", "harm"), ("寅", "巳", "harm"),   # exact duplicate → once
        ("寅", "未", "harm"),                          # synthetic second target
        ("寅", "巳", "punish"),
    ])
    note = PF.annual_activation_note(hit)
    assert note.count("natal **巳** are in **해 (harm)**") == 1
    assert "natal **未** are in **해 (harm)**" in note
    assert "형 (punishment)" in note


# ── E-12 (2026-09-25 audit) — template / prose defects in Harish's report ──


@pytest.fixture
def harish_ctx() -> _ReportContext:
    chart = compute_chart(
        name="harish-e12", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    return _ReportContext(chart, tier="deep", generation_date="2026-09-26")


def test_companion_decade_undertow_is_not_support_and_study(harish_ctx):
    period = next(p for p in harish_ctx.chart.daeun if p.stem_tengod in ("비견", "겁재"))
    text = PF.major_luck_narrative(period, harish_ctx)
    assert "support and study" not in text
    assert "peer dynamics" in text


def test_year_note_keyed_to_ten_god_not_raw_element(harish_ctx):
    from saju_engine import sewoon as SE
    # 2026 丙 (Fire) is 정관 (Authority) for a 辛 Day Master, and Fire is his 기신.
    hit = SE.build_sewoon_range(harish_ctx.chart.day_master, harish_ctx.chart.branches, 2026, 2026)[0]
    note = PF.year_by_year_note(hit, harish_ctx)
    assert "visibility, speaking" not in note
    assert "responsibility, structure" in note
    assert "challenging element (Fire)" in note
    # 2030 庚 (Metal) is the 희신, not the 용신.
    hit = SE.build_sewoon_range(harish_ctx.chart.day_master, harish_ctx.chart.branches, 2030, 2030)[0]
    assert "supporting-element (Metal) year" in PF.year_by_year_note(hit, harish_ctx)


def test_grouped_dominant_classes_keeps_ties(harish_ctx):
    dominant = PF._grouped_dominant_classes(harish_ctx.chart, 2)
    assert {c for c, _ in dominant} == {"Output", "Companion", "Resource"}


def test_attachment_patterns_names_real_stage_group(harish_ctx):
    text = PF.attachment_patterns(harish_ctx)
    assert "묘/관/충" not in text
    assert "목욕" in text and "supported (strong)" in text


def test_travel_timing_names_supporting_element(harish_ctx):
    text = PF.travel_timing(harish_ctx)
    assert "supporting **Metal**" in text


def test_business_and_health_seasons_agree(harish_ctx):
    assert "winter" in PF.business_seasonal_note(harish_ctx)
    rhythm = PF.seasonal_daily_rhythms(harish_ctx)
    assert "winter" in rhythm and "21:00–01:00" in rhythm and "Twelve Stages" not in rhythm


def test_direct_officer_fit_does_not_claim_a_stem():
    import inspect
    assert "Direct Officer stem" not in inspect.getsource(PF)


# ── E-8 residual (2026-09-26) — marriage timing from spouse star/palace ──


def test_marriage_timing_uses_spouse_star_and_palace_for_harish(harish_ctx):
    text = PF.marriage_timing_windows(harish_ctx)
    assert "재성 (wife star)" in text and "spouse palace **亥**" in text
    # The audit's worked example: 2034 甲寅 = 정재 year + 寅亥合 into the palace.
    assert "**2034 甲寅** (정재 spouse-star year, 寅亥 육합 into the spouse palace" in text
    assert "2030 (겁재 year)" in text


def test_marriage_timing_female_uses_officer_star(ctx):
    text = PF.marriage_timing_windows(ctx)
    assert "관성 (husband star)" in text
    assert "spouse-star stem" in text


def test_marriage_timing_without_gender_falls_back():
    chart = compute_chart(**{**SAMPLE_BIRTH, "gender": None})
    c = _ReportContext(chart, tier="deep", generation_date="2026-09-26")
    assert "No gender is recorded" in PF.marriage_timing_windows(c) or \
        "Major-luck data not available" in PF.marriage_timing_windows(c)


def test_regular_grid_narrative_keeps_non_breaking_caveat():
    """A 'likely' grid can still carry a caveat note (월지 충·형 / 신약, E-9
    residual) — the narrative must not drop it."""
    from types import SimpleNamespace
    from saju_engine.patterns import GridCandidate
    cand = GridCandidate(name_ko="정관격", name_en="Direct Officer Grid", basis="b",
                         confidence="likely", note="The month branch is struck (午子 충).")
    fake = SimpleNamespace(chart=SimpleNamespace(patterns={"regular_grid": [cand]}))
    assert "午子 충" in PF.regular_grid_narrative(fake)


# ── Validation 2026-09-25 (Harish) follow-ups ──


def test_current_decade_names_samhap_and_root(harish_ctx):
    text = PF.current_period_deep_dive(harish_ctx)
    assert "巳酉丑 삼합 (Metal)" in text and "건록" in text


def test_next_decade_names_combo_and_punishment(harish_ctx):
    p = next(x for x in harish_ctx.chart.daeun if x.combined == "庚戌")
    note = PF.decade_structure_note(p, harish_ctx.chart)
    assert "을경합금" in note and "punishes (형) your natal **丑**" in note


def test_annual_lean_reads_branch_too(harish_ctx):
    from saju_engine import sewoon as SE
    h = SE.build_sewoon_range(harish_ctx.chart.day_master, harish_ctx.chart.branches, 2029, 2029)[0]
    assert PF.annual_lean(h, harish_ctx) == ("supporting", "Metal")
    h = SE.build_sewoon_range(harish_ctx.chart.day_master, harish_ctx.chart.branches, 2027, 2027)[0]
    assert PF.annual_lean(h, harish_ctx)[0] == "challenging"


def test_natal_six_combination_binds_without_transforming_for_harish(harish_ctx):
    assert not PF.six_combination_transforms(harish_ctx.chart, "巳", "申", "Water")
    assert "합이불화" in PF.six_combination_phrase(harish_ctx.chart, "巳", "申", "Water")


def test_void_year_flagged_for_harish_2034(harish_ctx):
    from saju_engine import sewoon as SE
    c = harish_ctx.chart
    h = SE.build_sewoon_range(c.day_master, c.branches, 2034, 2034, natal_stems=c.stems)[0]
    assert "공망 year" in PF.year_by_year_note(h, harish_ctx)
    h = SE.build_sewoon_range(c.day_master, c.branches, 2029, 2029, natal_stems=c.stems)[0]
    assert "공망" not in PF.year_by_year_note(h, harish_ctx)


def test_boss_profile_embodies_yongsin_not_its_controller(harish_ctx):
    text = PF.boss_team_dynamics(harish_ctx)
    assert "Water advisor" in text and "Earth anchor" not in text
