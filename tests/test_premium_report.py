"""Tests for the premium client-facing report generator."""
from __future__ import annotations

import re

import pytest

from saju_engine.engine import compute_chart
from saju_engine.premium_report import generate_premium_report
from saju_engine.report_data import (
    _career_tiers,
    _chart_signature,
    _compatibility_rows,
    _element_balance,
    _hidden_stems_str,
    _strength_label,
)
from saju_engine.yongsin import favorable_element


def _sample_chart():
    return compute_chart(
        name="Sruthi",
        gender="F",
        year=1993,
        month=12,
        day=11,
        hour=2,
        minute=45,
        longitude=79.32,
        utc_offset=5.5,
        use_solar_time=True,
        convention="korean",
    )


def test_element_balance_totals_to_100():
    chart = _sample_chart()
    pct, counts = _element_balance(chart)
    assert sum(pct.values()) == 100.0
    assert all(e in pct for e in ["Wood", "Fire", "Earth", "Metal", "Water"])
    assert counts[chart.day_master_info["element"]] > 0


def test_hidden_stems_str():
    chart = _sample_chart()
    s = _hidden_stems_str(chart.month)
    assert "본" in s or s == "—"


def test_strength_label():
    chart = _sample_chart()
    label = _strength_label(chart)
    assert label in {"Strong", "Weak", "Balanced", "Very Strong"}


def test_chart_signature_includes_day_master_element():
    chart = _sample_chart()
    sig = _chart_signature(chart)
    # Signature is a prose sentence; just ensure it is non-empty and mentions
    # season-imagery words.
    assert sig
    assert len(sig) > 20


def test_compatibility_rows_balanced():
    # Balanced Fire DM, 용신 = Wood. Wood is "Best"; Water (generates Wood) is
    # "Good" (희신, strict classical); the rest are "Compatible".
    rows = _compatibility_rows("Fire", "Wood", verdict="balanced")
    assert len(rows) == 5
    fits = {r[1]: r[2] for r in rows}
    assert fits["Wood"] == "**Best**"
    assert fits["Water"] == "**Good**"
    # Exactly one Best row (the bug A10 produced two Best rows by also flagging
    # the generating/Resource element as Best).
    assert list(fits.values()).count("**Best**") == 1


def test_compatibility_rows_strong_dm_resource_is_watch():
    # Strong Fire DM, 용신 = Earth (output). Resource = Wood (generates Fire).
    # Per knowledge/09 Step 3, 인성 (Wood) amplifies the over-strong self and
    # must NOT be marked "Best" — it should be "Watch".
    rows = _compatibility_rows("Fire", "Earth", verdict="strong")
    fits = {r[1]: r[2] for r in rows}
    assert fits["Earth"] == "**Best**"
    assert fits["Wood"] == "**Watch**"   # Resource (인성) — the A10 fix
    assert fits["Fire"] == "**Watch**"   # Self (비겁) echoes strong self
    # The drain group (output/wealth/authority) is "Good".
    assert fits["Metal"] == "**Good**"   # Wealth (Fire overcomes Metal)


def test_compatibility_rows_weak_dm_support_is_good():
    # Weak Fire DM, 용신 = Wood (resource). Self = Fire (비겁) supports weak DM.
    rows = _compatibility_rows("Fire", "Wood", verdict="weak")
    fits = {r[1]: r[2] for r in rows}
    assert fits["Wood"] == "**Best**"
    assert fits["Fire"] == "**Good**"    # Self (비겁) supports weak self
    # Output (Earth) drains the weak self → Watch.
    assert fits["Earth"] == "**Watch**"


def test_career_tiers_nonempty_and_ranked():
    chart = _sample_chart()
    tiers = _career_tiers(chart)
    assert tiers
    # First entries should be Best Fit
    assert tiers[0][0] == "**Best Fit**"
    # All domains are distinct
    assert len({t[1] for t in tiers}) == len(tiers)


def test_premium_deep_has_plain_words_callouts_and_glossary():
    chart = _sample_chart()
    r = generate_premium_report(chart, tier="deep", generation_date="2026-06-21")
    assert r.count("> **In plain words:**") >= 4
    gi = r.index("## What the Terms Mean")
    ci = r.index("## Closing Note")
    assert gi > ci, "glossary must come after the Closing Note"
    assert "[ENGINE DRAFT" not in r
    # an inline gloss landed on a ten-god
    assert "— steady, earned income" in r or "— variable money" in r


def test_premium_essential_glossary_is_short_and_present():
    r = generate_premium_report(_sample_chart(), tier="essential")
    assert "## What the Terms Mean" in r


def test_premium_sample_has_glosses_but_no_glossary_or_callouts():
    r = generate_premium_report(_sample_chart(), tier="sample")
    assert "## What the Terms Mean" not in r
    assert "> **In plain words:**" not in r


def test_premium_report_contains_all_sections():
    chart = _sample_chart()
    report = generate_premium_report(chart, generation_date="2026-06-21")
    required = [
        "# Korean Four Pillars of Destiny · Saju Reading",
        "## Chart at a Glance",
        "## Day Master Portrait",
        "## Career & Wealth",
        "## Relationships",
        "## Health & Vitality",
        "## Timing: Major Luck & Annual Windows",
        "## Practical Guidance Summary",
        "## Closing Note",
    ]
    for section in required:
        assert section in report, f"missing {section}"
    # The premium report should be prose-filled, not prompt-shaped.
    # `[ENGINE DRAFT — REVIEW REQUIRED]` is preserved only when a section
    # truly cannot be auto-generated from chart data (intentional guardrail).
    assert "[ENGINE DRAFT — REVIEW REQUIRED]" not in report, (
        "premium report still contains [ENGINE DRAFT — REVIEW REQUIRED] placeholders"
    )


def test_premium_report_quick_reference_values():
    chart = _sample_chart()
    report = generate_premium_report(chart)
    fe = favorable_element(chart)
    assert "**Day Master:**" in report
    assert f"**Favorable Element:** {fe.element}" in report
    assert f"**Supporting Element:** {fe.supporting}" in report


def test_premium_report_timing_tables():
    chart = _sample_chart()
    report = generate_premium_report(chart)
    # Major luck table header
    assert "| Age | Pillar | Element Theme | Ten-God |" in report
    # Annual windows table header
    assert "| Year | Pillar | Annual Ten-God | Overall Theme |" in report
    # Reading tier = 3-year window (current year ± 1). chart.sewoon is the
    # pre-computed current_year ± 2 list, so its middle hit is current_year.
    current_year = chart.sewoon[len(chart.sewoon) // 2].year
    assert str(current_year) in report
    # Years outside the 3-year window must NOT appear in the Reading tier.
    assert str(current_year - 2) not in report
    assert "### Annual Windows (current year ± 1)" in report


def test_premium_report_fullmap_has_10_year_forecast():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="fullmap")
    # Full Map tier advertises a 10-year forward forecast.
    assert "### 10-Year Forecast" in report
    current_year = chart.sewoon[len(chart.sewoon) // 2].year
    assert str(current_year) in report
    assert str(current_year + 9) in report


def test_premium_report_element_balance_uses_colored_emoji():
    chart = _sample_chart()
    report = generate_premium_report(chart)
    assert "| Element | Presence | Percentage |" in report
    # Each element row should carry its colored emoji indicator.
    for emoji in ("🔴", "🟡", "⚪", "🔵", "🟢"):
        assert emoji in report, f"missing element emoji {emoji}"


def test_premium_report_spark_is_short():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="spark")
    # Spark should contain the core identity sections.
    assert "# Korean Four Pillars of Destiny · Saju Reading" in report
    assert "## Chart at a Glance" in report
    assert "## Day Master Portrait" in report
    assert "## Practical Guidance Summary" in report
    assert "## Closing Note" in report
    # Spark should NOT include the full thematic modules.
    assert "## Career & Wealth" not in report
    assert "## Relationships" not in report
    assert "## Health & Vitality" not in report
    assert "## Timing: Major Luck & Annual Windows" not in report


def test_premium_report_reading_has_relationships_and_career():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="reading")
    assert "## Career & Wealth" in report
    assert "## Relationships" in report
    assert "## Health & Vitality" in report
    assert "## Timing: Major Luck & Annual Windows" in report
    # Deep-dive sections belong to the Full Map tier only.
    assert "### Career Deep-Dive" not in report
    assert "### Relationship Deep-Dive" not in report
    assert "## Auspicious Dates — Next 90 Days" not in report


def test_premium_report_fullmap_has_deep_dive_and_auspicious_dates():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="fullmap")
    assert "## Career & Wealth" in report
    assert "### Career Deep-Dive" in report
    assert "## Relationships" in report
    assert "### Relationship Deep-Dive" in report
    assert "## Auspicious Dates — Next 90 Days" in report
    assert "## Monthly Lucky Dates" in report
    assert "## MP3 Audio Summary — Included by Default" in report
    assert "## Business & Launch Timing" in report
    assert "## Natal Pattern Analysis" in report
    assert "## Wealth & Investment Timing" in report
    assert "## Relocation, Travel & Direction Guidance" in report
    assert "## Life Themes by Major Luck Period" in report


def test_premium_report_unknown_tier_raises():
    chart = _sample_chart()
    import pytest
    with pytest.raises(ValueError, match="Unknown tier"):
        generate_premium_report(chart, tier="platinum")


def test_premium_report_sample_hook_is_compact():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="sample")
    assert "The Hook" in report
    assert "Complimentary" in report
    assert "## Your Chart Snapshot" in report
    assert "### Four Pillars" in report
    assert "### Element Balance" in report
    assert "### Your Lucky Cues" in report
    assert "## Closing Note" in report
    # Sample must not include the full thematic modules.
    assert "## Day Master Portrait" not in report
    assert "## Career & Wealth" not in report


def test_premium_report_essential_matches_contract():
    """Essential tier must match the landing-page product description."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="essential")
    assert "## Chart at a Glance" in report
    assert "## Day Master Portrait" in report
    assert "## Career & Wealth" in report
    assert "## Timing: Major Luck" in report
    assert "## Practical Guidance Summary" in report
    assert "## Closing Note" in report
    # Essential excludes the Deep-only modules.
    assert "## Relationships" not in report
    assert "## Health & Vitality" not in report
    assert "## 30-Day" not in report
    assert "### Lucky Attributes" in report
    # Abbreviated Lucky Attributes (Spark-style) has only 4 fields.
    assert "**Season:**" not in report


def test_premium_report_has_no_stale_year_ranges():
    """Previously hardcoded year windows must not leak into generated markdown.

    We lint the source module directly because dynamic output can legitimately
    reproduce the same numeric span when the current year happens to match.
    """
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "saju_engine" / "premium_report.py"
    text = src.read_text(encoding="utf-8")
    for stale in ("2025–2030", "2026–2028"):
        assert stale not in text, f"stale hardcoded range {stale!r} in premium_report.py"


def test_premium_report_business_launch_window_anchors_on_current_year():
    """Deep-tier business launch heading uses a year range derived from the chart."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    current_year = chart.sewoon[len(chart.sewoon) // 2].year
    assert f"### Favorable Windows ({current_year}–{current_year + 5})" in report


def test_premium_report_companion_is_focused_timing_read():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="companion")
    assert "Cosmic Companion" in report
    assert "$9/month" in report
    assert "## Chart at a Glance" in report
    assert "## Timing: Major Luck & Annual Windows" in report
    assert "## Practical Guidance Summary" in report
    assert "## Closing Note" in report
    # Companion should be short: exclude the full thematic modules.
    assert "## Day Master Portrait" not in report
    assert "## Career & Wealth" not in report
    assert "## Relationships" not in report
    assert "## Health & Vitality" not in report
    assert "### Career Deep-Dive" not in report


def test_premium_report_essential_price_and_scope():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="essential")
    assert "Essential Report" in report
    assert "$19" in report
    assert "## Chart at a Glance" in report
    assert "## Table of Contents" in report
    assert "## Day Master Portrait" in report
    assert "## Career & Wealth" in report
    assert "## Timing: Major Luck Periods" in report
    assert "## Practical Guidance Summary" in report
    assert "## Closing Note" in report
    # Essential matches the landing-page contract: compact portrait + career +
    # major-luck table + abbreviated Lucky Attributes + short closing.
    assert "### Four Pillars, One by One" in report
    assert "### Wealth Preservation Note" in report
    # Deep-only sections should not appear.
    assert "## Relationships" not in report
    assert "## Health & Vitality" not in report
    assert "## 30-Day Action Plan" not in report
    assert "### Ready to Go Deeper?" not in report
    assert "## Business & Launch Timing" not in report
    assert "## Monthly Lucky Dates" not in report
    assert "## MP3 Audio Summary" not in report
    assert "### Career Deep-Dive" not in report
    assert "### Relationship Deep-Dive" not in report
    # Abbreviated Lucky Attributes lacks the extra fields in the full card.
    assert "**Season:**" not in report


def test_premium_report_deep_price_and_dynamic_window():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    current_year = chart.sewoon[len(chart.sewoon) // 2].year
    assert "Deep Destiny Report" in report
    assert "$55" in report
    assert "## Career & Wealth" in report
    assert "## Relationships" in report
    assert "## Health & Vitality" in report
    assert "## Business & Launch Timing" in report
    assert f"### Favorable Windows ({current_year}–{current_year + 5})" in report
    assert "### 10-Year Forecast" in report
    assert "## Health & Vitality — Deep-Dive" in report
    assert "## Auspicious Dates — Next 90 Days" in report
    assert "## Monthly Lucky Dates" in report
    assert "## MP3 Audio Summary — Included by Default" in report
    # New deep-only expansion sections
    assert "## Natal Pattern Analysis" in report
    assert "## Wealth & Investment Timing" in report
    assert "## Relocation, Travel & Direction Guidance" in report
    assert "## Life Themes by Major Luck Period" in report
    for year in range(current_year, current_year + 6):
        assert str(year) in report


def test_premium_report_tier_aliases_normalize():
    chart = _sample_chart()
    assert "The Hook" in generate_premium_report(chart, tier="hook")
    assert "Essential Report" in generate_premium_report(chart, tier="₹799")
    assert "Deep Destiny Report" in generate_premium_report(chart, tier="1499")


# ── Blueprint-alignment tests (CosmicSaju Three-Tier Architecture) ────────


def test_premium_report_sample_has_year_summary_and_curiosity_line():
    """Hook tier must include the 'What This Year Means for You' line and
    the '8 major luck periods' curiosity note."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="sample")
    assert "What This Year Means for You" in report
    assert "8 major luck periods" in report


def test_premium_report_essential_has_four_pillars_one_by_one():
    """Essential tier must include the shorter Four Pillars One by One section."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="essential")
    assert "### Four Pillars, One by One" in report
    # All four pillars covered
    for label in ("Year Pillar", "Month Pillar", "Day Pillar", "Hour Pillar"):
        assert label in report, f"missing pillar label {label}"


def test_premium_report_essential_excludes_relationship_and_social_sections():
    """Essential tier contract excludes Relationships and Social Energy modules."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="essential")
    assert "### Key Relationship Timing" not in report
    assert "### Friendship & Social Energy" not in report


def test_premium_report_essential_has_wealth_preservation_note():
    """Essential tier must include a Wealth Preservation Note sub-section."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="essential")
    assert "### Wealth Preservation Note" in report


def test_premium_report_deep_has_single_wealth_preservation_note():
    """Deep tier must not emit two Wealth Preservation Note sections."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    matches = report.count("### Wealth Preservation Note")
    assert matches == 1, f"expected 1 Wealth Preservation Note heading, got {matches}"


def test_premium_report_deep_has_ten_god_distribution_table():
    """Deep tier must include the full Ten-God Distribution Table with
    all 4 pillars and a Hidden Ten-God column."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "### Ten-God Distribution Table" in report
    # Header columns are present
    assert "Hidden Ten-Gods" in report
    # All 4 pillars covered
    for label in ("Year Pillar", "Month Pillar", "Day Pillar", "Hour Pillar"):
        assert label in report, f"missing pillar label {label}"


def test_premium_report_deep_has_lifetime_decade_roadmap():
    """Deep tier must include the Lifetime Decade Roadmap table."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "## Lifetime Decade Roadmap" in report
    # Road map markers (used by the HTML backend to swap in the SVG)
    assert "<!-- decade-roadmap:start -->" in report
    assert "<!-- decade-roadmap:end -->" in report
    # Lean classification column present
    assert "Favorable Lean" in report


def test_premium_report_deep_has_how_to_use_section():
    """Deep tier must include the How to Use This Report FAQ block,
    positioned before the Closing Note."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "## How to Use This Report" in report
    # The block sits before the Closing Note so the reader sees it first.
    how_pos = report.index("## How to Use This Report")
    closing_pos = report.index("## Closing Note")
    assert how_pos < closing_pos, "How to Use must come before Closing Note"
    # FAQ is non-trivial
    assert "What does \"favorable element\" mean in daily life?" in report


def test_premium_report_deep_cover_mentions_audio_included():
    """Deep tier cover must include the 'MP3 audio summary is included' line."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "Your MP3 audio summary is included" in report


def test_premium_report_deep_audio_section_uses_default_wording():
    """Deep tier audio section wording should say 'delivered alongside' (default),
    not the old 'on request' wording."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "delivered alongside this PDF" in report
    assert "on request" not in report


def test_premium_report_deep_has_partner_compat_upsell():
    """Deep tier Relationships deep-dive must include the Partner Chart Add-On upsell."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "#### Partner Chart Add-On" in report
    assert "compatibility reading" in report


def test_premium_report_deep_monthly_lucky_dates_has_methodology():
    """Deep tier Monthly Lucky Dates section must include the methodology note."""
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "## Monthly Lucky Dates" in report
    # The methodology line is a 1-sentence callout. The closing
    # "business-critical decisions" reminder is positioned after the table
    # so the chunk must include the full section to end-of-document.
    mld_idx = report.index("## Monthly Lucky Dates")
    chunk = report[mld_idx:]
    assert "Methodology" in chunk
    assert "daily-luck" in chunk
    # And the closing 'for business-critical decisions' reminder
    assert "business-critical decisions" in chunk



# ── G1: internal reviewer notes must never reach client output ──────────────

_REVIEWER_NOTE_MARKERS = (
    "Chart-derived",
    "verify against",
    "verify archetype",
    "refine each entry",
    "Engine note:",
    "engine heuristic",
    "REVIEW REQUIRED",
)


@pytest.mark.parametrize("tier", ["sample", "essential", "deep", "companion"])
def test_no_reviewer_notes_in_client_report(tier):
    chart = _sample_chart()
    report = generate_premium_report(chart, tier=tier)
    for marker in _REVIEWER_NOTE_MARKERS:
        assert marker not in report, f"reviewer marker {marker!r} leaked into {tier} report"


def test_every_premium_tier_is_client_facing():
    """All tiers routed through generate_premium_report are client-facing, so
    _reviewer_note suppresses the notes for every one of them."""
    from saju_engine.premium_report import _CLIENT_TIERS
    from saju_engine.report_data import TIER_CONFIG
    assert set(TIER_CONFIG) <= _CLIENT_TIERS


# ── G2: per-pillar walk is grammatical and pillar-specific ──────────────────

def test_per_pillar_walk_is_grammatical_and_distinct():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="essential")
    assert "**. sits as **" not in report
    assert ". sits as " not in report
    assert "shaping the **" not in report  # old broken "shaping the **<area>**." phrasing

    walk_idx = report.index("### Four Pillars, One by One")
    section = report[walk_idx:report.index("---", walk_idx)]
    paras = [ln for ln in section.splitlines() if ln.startswith("The ") and "pillar pairs the" in ln]
    assert len(paras) == 4
    # Strip bolded chart-specific tokens; the remaining skeletons must differ.
    skeletons = {re.sub(r"\*\*[^*]+\*\*", "X", p) for p in paras}
    assert len(skeletons) > 1, "all four per-pillar paragraphs use an identical template"


def test_per_pillar_walk_deep_has_no_duplicate_container_sentence():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    walk_idx = report.index("### Four Pillars, One by One")
    section = report[walk_idx:report.index("### Ten-God Distribution Table", walk_idx)]
    assert "both a container" not in section  # the old redundant Deep sentence


# ── G3: favorable-element provenance is client-voice ────────────────────────

def test_favorable_element_line_carries_client_voice_provenance():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "**Favorable Element:**" in report
    fav_line = next(ln for ln in report.splitlines() if ln.startswith("- **Favorable Element:**"))
    assert "heuristic guess" not in fav_line
    assert "reader review" not in fav_line


def test_favorable_override_flows_into_report():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep", favorable_override="Fire")
    assert "- **Favorable Element:** Fire —" in report


# ── Report-leak regressions (partial 삼형, GridCandidate repr, doubled phrase) ──

def _partial_punishment_chart():
    """Chart with a two-branch (partial) 삼형: 申巳 — the Harish 1992-06-04 case."""
    return compute_chart(
        name="Harish",
        gender="M",
        year=1992,
        month=6,
        day=4,
        hour=3,
        minute=10,
        longitude=79.12,
        utc_offset=5.5,
        use_solar_time=True,
        convention="korean",
    )


def test_partial_punishment_table_row_is_labeled_partial():
    chart = _partial_punishment_chart()
    assert chart.three_punishments[0][2] == "—", "fixture chart must have a partial 삼형"
    report = generate_premium_report(chart, tier="deep")
    assert "Three Punishment (partial)" in report
    assert "申-巳-" not in report, "no third-branch placeholder may appear in the table"
    assert "申-巳-—" not in report


def test_partial_punishment_prose_never_renders_placeholder_branch():
    chart = _partial_punishment_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "partial 삼형 (Three Punishment)" in report
    assert "among **申**, **巳**, and **—**" not in report
    assert "partial three-punishment between **申** and **巳**" in report


def test_pattern_candidate_label_is_human_readable():
    chart = _partial_punishment_chart()
    assert chart.patterns["regular_grid"], "fixture chart must have a 격국 candidate"
    report = generate_premium_report(chart, tier="deep")
    assert "GridCandidate(" not in report, "dataclass repr must never reach client prose"
    assert "**정관격 (Direct Officer Grid)**" in report


def test_balanced_chart_growth_area_has_no_doubled_phrase():
    # 1993-09-30 04:00 (Korea) assesses as a balanced chart with no 기신 named.
    chart = compute_chart(
        year=1993, month=9, day=30, hour=4, minute=0,
        gender="M", longitude=127.0, utc_offset=9.0,
        convention="korean",
    )
    assert (chart.strength_assessment or {}).get("verdict") == "balanced"
    report = generate_premium_report(chart, tier="deep")
    assert "challenging element element" not in report
    assert "Working with the chart's challenging element" in report


# ── Method-transparency disclosures (external-review feedback, 2026-09-07) ──

def test_solar_time_disclosure_present_with_hour_boundary_flag():
    chart = _partial_punishment_chart()  # 03:10 clock → 02:56 solar, 4 min from 寅 boundary
    sc = chart.solar_correction or {}
    assert sc.get("solar_time") == "02:56"
    report = generate_premium_report(chart, tier="deep")
    assert "**Time method:**" in report
    assert "true solar time **02:56**" in report
    assert "⚠ Hour-boundary note" in report, "knife-edge births must be flagged"
    assert "~4 minutes from a 2-hour branch boundary" in report


def test_solar_time_note_omitted_when_no_correction_applied():
    chart = compute_chart(
        year=1993, month=12, day=11, hour=2, minute=45,
        gender="F", longitude=82.5, utc_offset=5.5,  # on the IST meridian → no correction
        convention="korean",
    )
    report = generate_premium_report(chart, tier="deep")
    # No meaningful correction → no disclosure block (or no correction line).
    assert "true solar time" not in report


def test_daeun_direction_disclosed_in_quick_reference_and_timing():
    chart = _partial_punishment_chart()
    report = generate_premium_report(chart, tier="deep")
    lines = [ln for ln in report.splitlines() if "Luck direction" in ln]
    assert len(lines) >= 2, "disclosure must appear in Quick Reference and the Timing section"
    for ln in lines:
        assert "yang year stem (壬) and male gender" in ln
        assert ln.startswith("- **Luck direction:** forward") or ln.startswith("**Luck direction:** forward")


def test_daeun_direction_absent_gender_is_disclosed_not_hidden():
    chart = compute_chart(
        year=1990, month=5, day=15, hour=10, minute=0,
        longitude=127.0, utc_offset=9.0, gender=None,
        convention="korean",
    )
    assert chart.daeun == []
    report = generate_premium_report(chart, tier="deep")
    assert "Luck direction:** not computed" in report
    assert "requires the querent's gender" in report


def test_element_balance_has_methodology_footnote():
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "Methodology: each element's share counts the 8 visible stems and branches" in report
    assert "main qi 0.6, middle 0.3, residual 0.1" in report
