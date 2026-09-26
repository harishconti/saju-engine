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
    assert "| Age | Pillar | Elements (Stem / Branch) | Ten-God |" in report
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
    assert f"### Year-by-Year Launch Timing ({current_year}–{current_year + 5})" in report


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
    # F-13 (2026-09-26 audit): TIER_CONFIG must match CLAUDE.md's documented
    # launch price ("$9 intro → $19"), not the bare regular price alone.
    assert "$9 intro → $19" in report
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
    assert f"### Year-by-Year Launch Timing ({current_year}–{current_year + 5})" in report
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


def test_wealth_timing_major_luck_periods_flags_companion_class_as_competition():
    """Regression for the 2026-09-19 bug (external report review, 2nd + 3rd
    pass): 겁재/비견 (비겁-class) 대운 decades were listed under 'Major-luck
    periods that carry wealth or favorable-element energy' with the SAME
    "income, asset, or value-creation" note as genuine 재성 decades, purely
    because the decade's stem ELEMENT matched 용신/희신 — but 비겁-class
    ten-gods are classically read as wealth competitors (겁재奪財,
    knowledge/13-wealth-and-business.md), not wealth opportunities. Harish's
    real chart has exactly this: ages 40-49 (庚戌, Robber) and 50-59 (辛亥,
    Companion) both carry his 희신/용신 element with a 비겁-class ten-god.
    """
    chart = compute_chart(
        name="harish-wealth-periods-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    report = generate_premium_report(chart, tier="deep")
    idx = report.find("Major-luck periods that carry wealth")
    assert idx != -1
    section = report[idx:idx + 2000]
    assert "40–49" in section and "50–59" in section
    assert "wealth *competition*" in section, (
        f"비겁-class decades must be flagged as wealth competition, not opportunity: {section!r}"
    )
    assert section.count("income, asset, or value-creation themes are more likely to surface") == 0, (
        "the genuine-wealth-note text must not be applied to 비겁-class decades"
    )


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


def test_lifetime_decade_roadmap_honours_override_not_chart_baked_status():
    """Regression for the 2026-09-19 override/roadmap mismatch.

    ``chart.daeun[i].favorable_status`` is baked in at compute_chart time
    (bare-resolved, no override — see daeun_overlay.py). The rendered
    "Lifetime Decade Roadmap" must instead reflect THIS report's actual
    favorable_override, or an overridden report (Gurumoorthy, Sruthi, Pawan
    in production) would show a roadmap that contradicts its own Quick
    Reference favorable element.

    Harish's chart resolves to Water bare (조후 climate-balanced, hot 巳
    month), with Metal as the supporting (희신) element — so both Water AND
    Metal decades count as "favorable" (`period_favorable_status` checks
    both, per the 2026-09-20 fix; see that function's docstring). Overriding
    to Metal here must move the roadmap's favorable rows to the Metal-and-
    Earth decades (Earth generates Metal, so it becomes the new supporting
    element) — a pure-Water decade (60-69, 壬子) is favorable bare but
    neutral overridden.

    The pure-Fire decade (0-9, 丙午) reads differently under each: Fire is
    Water's actual 기신 (기신 = the element 용신 overcomes; Water overcomes
    Fire), so it is genuinely **challenging** under the bare (Water)
    reading (E-3 fix, 2026-09-25 — before that fix, `ctx.unfavorable` could
    never be populated for a balanced/climate-gated chart, so this always
    silently read "neutral" instead). Under the Metal override, Metal's
    기신 is Wood, not Fire, so 0-9 stays neutral there.
    """
    chart = compute_chart(
        name="Harish-override-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    bare_report = generate_premium_report(chart, tier="deep")
    override_report = generate_premium_report(chart, tier="deep", favorable_override="Metal")

    def _roadmap_row(report: str, ages: str) -> str:
        for line in report.splitlines():
            if line.startswith(f"| {ages} |"):
                return line
        raise AssertionError(f"no roadmap row found for ages {ages}")

    # Bare (Water-resolved, Metal-supported): 60-69 (pure Water) favorable;
    # 0-9 (pure Fire, Water's actual 기신) challenging.
    assert _roadmap_row(bare_report, "60–69").endswith("| favorable |")
    assert _roadmap_row(bare_report, "0–9").endswith("| challenging |")

    # Overridden to Metal (Earth becomes the new supporting element): the
    # favorable rows must move accordingly, not stay pinned to the
    # bare-resolved Water/Metal rows.
    assert _roadmap_row(override_report, "20–29").endswith("| favorable |")
    assert _roadmap_row(override_report, "30–39").endswith("| favorable |")
    assert _roadmap_row(override_report, "60–69").endswith("| neutral |")
    assert _roadmap_row(override_report, "0–9").endswith("| neutral |")


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
    # 1993-09-30 04:00 (Korea) assesses as a balanced chart.
    #
    # Updated 2026-09-25 (external report review, E-3): every chart now has
    # a real, named unfavorable element (this one resolves to Water) — see
    # _ReportContext.__init__'s E-3 fix — so growth_areas' generic "the
    # chart's challenging element" fallback (prose_fillers.py, for when no
    # 기신 could be named) is unreachable code for every chart, not just
    # this one, and the report correctly names the element instead.
    chart = compute_chart(
        year=1993, month=9, day=30, hour=4, minute=0,
        gender="M", longitude=127.0, utc_offset=9.0,
        convention="korean",
    )
    assert (chart.strength_assessment or {}).get("verdict") == "balanced"
    report = generate_premium_report(chart, tier="deep")
    assert "challenging element element" not in report
    assert "Working with the unfavorable Water element" in report


# ── Method-transparency disclosures (external-review feedback, 2026-09-07) ──

def test_solar_time_disclosure_present_with_hour_boundary_flag():
    # 03:10 clock -> 02:58 solar (longitude -13.5 min + equation of time +1.7
    # min, added 2026-09-19 per the external report review — see
    # pillars.py::_equation_of_time_minutes), 2 min from the 寅 boundary.
    chart = _partial_punishment_chart()
    sc = chart.solar_correction or {}
    assert sc.get("solar_time") == "02:58"
    report = generate_premium_report(chart, tier="deep")
    assert "**Time method:**" in report
    assert "true solar time **02:58**" in report
    assert "equation of time" in report, "the EoT breakdown must be disclosed, not silently folded in"
    assert "⚠ Hour-boundary note" in report, "knife-edge births must be flagged"
    assert "~2 minutes from a 2-hour branch boundary" in report


def test_solar_time_disclosure_flags_zi_hour_edge_without_a_false_alternate():
    """N-15 (2026-09-26 audit): the 子 (23:00/01:00) hour edge used to get no
    boundary disclosure at all (see pillars.py::_hour_boundary_info) — the
    single costliest edge in the chart, since it can also flip which
    calendar day's stem drives the hour pillar. The report must now warn
    the reader, without claiming a specific (unresolved) alternate pillar.
    """
    chart = compute_chart(
        name="ZiEdge", gender="M",
        year=2000, month=1, day=1, hour=23, minute=30,
        longitude=127.0, utc_offset=9.0, use_solar_time=True,
        convention="korean",
    )
    report = generate_premium_report(chart, tier="deep")
    assert "⚠ Hour-boundary note" in report
    assert "子" in report
    assert "possibly the day pillar" in report


def test_solar_time_note_omitted_when_no_correction_applied():
    # 2000-06-13 is the date the equation of time is nearest zero (see
    # pillars.py::_equation_of_time_minutes); combined with longitude on the
    # exact IST meridian (82.5°E, zero longitude term), total correction
    # rounds to 0 min and no disclosure should render. A date/longitude
    # combo that zeroes only the longitude term (e.g. the old 1993-12-11) no
    # longer suffices on its own now that EoT is applied (added 2026-09-19).
    chart = compute_chart(
        year=2000, month=6, day=13, hour=2, minute=45,
        gender="F", longitude=82.5, utc_offset=5.5,
        convention="korean",
    )
    report = generate_premium_report(chart, tier="deep")
    # No meaningful correction → no disclosure block (or no correction line).
    assert "true solar time" not in report


# ── E-1 — sajupy's month-pillar term-time comparison ignored the birth's ──
# ── timezone (found 2026-09-25, external report review) ───────────────────


def test_year_month_correction_note_for_far_from_kst_birth():
    """A birth far from KST (New York, UTC-5) whose month pillar sajupy
    gets wrong (乙丑, which doesn't fit its own year pillar 甲辰 under 오호둔)
    must surface the correction disclosure, and the corrected pillar (丙寅)
    must be the one the rest of the report actually uses."""
    chart = compute_chart(
        name="NY-disclosure", gender="M",
        year=2024, month=2, day=4, hour=10, minute=0,
        utc_offset=-5, longitude=-74.0, use_solar_time=True, convention="korean",
    )
    assert chart.month.combined == "丙寅"
    assert chart.year_month_correction is not None
    report = generate_premium_report(chart, tier="deep")
    assert "Year/month correction note" in report
    assert "丙" in report and "寅" in report


def test_year_month_correction_note_omitted_for_kst_adjacent_birth():
    """Korea/India-timezone births (0-3.5h from KST) essentially never
    trigger the correction — no disclosure should render for Harish's own
    chart."""
    chart = compute_chart(
        name="Harish-no-correction", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5, convention="korean",
    )
    assert chart.year_month_correction is None
    report = generate_premium_report(chart, tier="deep")
    assert "Year/month correction note" not in report


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
    """The footnote must accurately describe the counting method, not claim a
    branch's own element is counted separately from its hidden stems (it
    isn't — see strength.py::_element_counts, which weights only the 4
    visible stems at 1.0 plus every hidden stem at 0.6/0.3/0.1). The old
    wording ("8 visible stems and branches") was found 2026-09-19 (external
    report review) to describe a DIFFERENT method than the code implements,
    which led an outside reviewer to (incorrectly) conclude the Fire
    percentage was miscomputed — it wasn't; the prose was just misleading.
    """
    chart = _sample_chart()
    report = generate_premium_report(chart, tier="deep")
    assert "counts the 4 visible stems" in report
    assert "8 visible stems and branches" not in report
    assert "main qi 0.6, middle 0.3, residual 0.1" in report


def test_decade_and_annual_favorable_lean_agree_on_shared_element():
    """Regression for R2 (external report review, 3rd pass): the decade-level
    `period_favorable_status` used to check only `favorable`, while the
    annual-level `annual_window_row` checked `elem in {favorable,
    supporting}` — a genuine inconsistency. Confirmed live: Harish's 40-49
    decade (庚戌, stem Metal = his 희신) was "neutral" while 2030 (also 庚戌)
    inside that exact decade was a "favorable-element year" in the Annual
    Windows / 10-Year Forecast table — a direct contradiction between two
    tables describing the same period.
    """
    chart = compute_chart(
        name="Harish-decade-annual-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    report = generate_premium_report(chart, tier="deep")

    def _row(prefix: str) -> str:
        for line in report.splitlines():
            if line.startswith(prefix):
                return line
        raise AssertionError(f"no row found for {prefix!r}")

    decade_row = _row("| 40–49 |")
    # Several tables have a "2030" row (relationship timing, life-themes,
    # 10-Year Forecast); the 10-Year Forecast row is the 6-column one with a
    # bare "Robber" ten-god column.
    year_row = _row("| 2030 | 庚戌 | Robber | ")
    assert decade_row.endswith("| favorable |"), decade_row
    # 2026-09-26: annual rows now distinguish a 희신 ("supporting-element")
    # year from a 용신 year (E-12 / validation §2.8); both are the favorable
    # side, so they still agree with the decade's "favorable".
    assert "supporting-element year" in year_row, year_row


# ── R5 — Avoid/Watch (기신/구신/한신) blank for balanced/climate charts ────
# ── (found 2026-09-20, external report review, 3rd pass) ─────────────────


def test_avoid_watch_field_is_populated_for_a_balanced_chart():
    """`strength.py`'s balanced-verdict branch leaves `candidate_unfavorable`
    as `None`, so the Quick Reference "Avoid / Watch" field used to render as
    a bare "—" for every balanced/climate-gated chart (e.g. Harish's,
    favorable=Water). knowledge/03-five-elements.md's own worked example for
    a Water 용신 gives 기신=Fire, 구신=Earth, 한신=Wood — the field must name
    all three, derived from the report's actual resolved favorable element."""
    chart = compute_chart(
        name="Harish-avoidwatch-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    assert chart.strength_assessment["verdict"] == "balanced"
    report = generate_premium_report(chart, tier="deep")
    line = next(l for l in report.splitlines() if l.startswith("- **Avoid / Watch:**"))
    assert line != "- **Avoid / Watch:** —"
    assert "Fire" in line and "Earth" in line and "Wood" in line


# ── R17 — strength verdict has no reasoning block ─────────────────────────
# ── (found 2026-09-20, external report review, 3rd pass) ─────────────────


def test_strength_line_states_a_reasoning_not_just_the_verdict():
    """knowledge/10-output-template requires verdict + reasoning (season,
    hidden stems, stem support). The Quick Reference used to say only
    "Balanced — a seasonal-strength reading" with no argument — confirmed
    live: it never mentioned that Harish's 辛 sits at 사 (a seasonally weak
    12운성 stage per knowledge/06) in the 巳 month, which the chart's
    Earth/Metal support then offsets back to balanced."""
    chart = compute_chart(
        name="Harish-strength-reasoning-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    report = generate_premium_report(chart, tier="deep")
    line = next(l for l in report.splitlines() if l.startswith("- **Strength:**"))
    assert "seasonal-strength reading; a full classical analysis" not in line
    assert "사" in line and "seasonally weak baseline" in line
    assert "peer" in line or "resource" in line or "drain" in line


def test_daeun_starting_age_note_states_precise_age_not_just_decade():
    """R19: the precise 대운수 must be stated (e.g. "~0.5") alongside the
    rounded "0-9" decade label, not silently collapsed into it.

    Value corrected twice (external report review):
    - 2026-09-20 (4th pass): the R19 fix itself truncated the day count to a
      whole day before dividing by 3 (1.68 days floored to 1 -> "~0.3"/"~1
      month"), and a second, independent bug divided the months conversion
      by 3 twice ("~1 month" instead of ~7). Fixed to "~0.6"/"~7 months".
    - 2026-09-25 (E-1): that "~0.6"/1.68-day figure was itself still wrong —
      `_term_boundary_datetimes` compared the CSV's KST-stored term time
      directly against IST birth time with no conversion. Fixed in
      `_term_boundary_datetimes` (now takes a required `utc_offset`). The
      true value, 1.5375 days -> 0.5125 years -> 6.15 months, independently
      matches two external reviewers who used different methods (a
      Beijing-time-based estimate landing at ~0.51y/6.1mo, and an ephemeris
      based one landing at ~1.53 days) almost exactly.
    """
    chart = compute_chart(
        name="Harish-r19-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    report = generate_premium_report(chart, tier="deep")
    assert "대운수" in report
    assert "~0.5" in report
    assert "roughly 6 months" in report


def test_year_one_liner_labels_the_saju_year_not_gregorian():
    """N-11 (2026-09-26 audit): "{year} is a **{pillar}** year" stated the
    raw Gregorian reference year. For a reference date between Jan 1 and
    입춀 (~Feb 4), the active 세운 is still the PRIOR year's — the pillar was
    already correct (chart.sewoon's window keys off the same Gregorian
    year), but the label said e.g. "2024 is a ... year" over a pillar that
    is actually 2023's."""
    from saju_engine.premium_report import _year_one_liner

    chart = compute_chart(
        name="Tester", gender="F",
        year=1993, month=12, day=11, hour=10, minute=0,
        city="Seoul", utc_offset=9, use_solar_time=True,
        reference_year=2024, reference_month=1, reference_day=15,
    )
    line = _year_one_liner(chart)
    assert "2023 is a" in line
    assert "2024 is a" not in line


def test_daeun_starting_age_note_is_independent_of_use_solar_time():
    """N-2 (2026-09-26 audit): a 절기 is an absolute instant, and the CSV's
    term times (converted to the birth's timezone) are civil-clock instants
    — so the starting-age day count must compare the CIVIL birth time
    against them. `_build_daeun` used to feed the SOLAR-corrected time in
    instead, so the same birth produced a different (wrong) precise starting
    age depending only on whether `use_solar_time` was True or False. Fixed:
    the note is now identical either way, for a birth minutes from a 절기
    where the solar correction (~-32 min in Seoul) is large enough to matter.
    """
    notes = []
    for use_solar_time in (True, False):
        chart = compute_chart(
            name="N2-daeun-regression", gender="M",
            year=2024, month=2, day=4, hour=17, minute=20,
            longitude=127.0, utc_offset=9.0, use_solar_time=use_solar_time,
        )
        report = generate_premium_report(chart, tier="deep")
        notes.append(next(l for l in report.splitlines() if "대운수" in l))
    assert notes[0] == notes[1]


# ── R7 — date-selection filter defects ────────────────────────────────────
# ── (found 2026-09-20, external report review, 3rd pass) ─────────────────


def _harish_chart_for_dates():
    return compute_chart(
        name="Harish-r7-regression", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )


def test_auspicious_dates_not_truncated_to_five():
    """The 90-day table used to silently cap at 5 dates regardless of how
    many actually qualified; knowledge/16 gives no basis for that cap."""
    from saju_engine.premium_report import _ReportContext, _section_auspicious_dates
    ctx = _ReportContext(_harish_chart_for_dates(), tier="deep", generation_date="2026-09-20")
    lines = _section_auspicious_dates(ctx)
    data_rows = [l for l in lines if l.startswith("| 20")]
    assert len(data_rows) > 5, f"expected more than the old 5-date cap: {len(data_rows)} rows"


def test_auspicious_dates_exclude_harm_and_break_not_just_clash():
    """Confirmed live: candidate days whose branch is 寅 (파 against Harish's
    natal 亥 day branch) or 申 (해 against 亥) passed the old clash-only
    filter untouched. Neither may appear as a candidate day-branch now."""
    from saju_engine.premium_report import _ReportContext, _section_auspicious_dates
    ctx = _ReportContext(_harish_chart_for_dates(), tier="deep", generation_date="2026-09-20")
    lines = _section_auspicious_dates(ctx)
    data_rows = [l for l in lines if l.startswith("| 20")]
    for row in data_rows:
        pillar = row.split("|")[2].strip()  # e.g. "庚子 (Robber)"
        branch = pillar[1]
        assert branch not in ("寅", "申"), f"寅/申 must be filtered (파/해 vs natal 亥): {row!r}"


# ── E-11 — date filter checked 충/해/파 but not 형/자형 (found 2026-09-25, ──
# ── external report review) ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "candidate,watch,expected",
    [
        # 戌 vs natal 丑: both members of the 丑戌未 punishment triad.
        ("戌", ["亥", "丑"], ["형"]),
        # 亥 repeating natal 亥: self-punishment (亥 is a SELF_PUNISHMENTS branch).
        ("亥", ["亥", "丑"], ["자형"]),
        # 子 vs 卯: the documented 2-member special-case punishment.
        ("子", ["卯"], ["형"]),
        # 卯 vs 子 (same pair, reversed roles).
        ("卯", ["子"], ["형"]),
        # Equal branches that are NOT self-punishing must not falsely flag 형
        # (e.g. 寅 repeating a natal 寅 — 寅 is a member of the 寅巳申 triad
        # but is not itself a SELF_PUNISHMENTS branch).
        ("寅", ["寅"], []),
        # No relation at all.
        ("酉", ["亥", "丑"], []),
        # 未 vs natal 丑: both in the 丑戌未 triad AND a 충 (clash) pair —
        # both labels must appear.
        ("未", ["丑"], ["충", "형"]),
    ],
)
def test_candidate_day_conflicts_detects_punishment(candidate, watch, expected):
    from saju_engine.premium_report import _candidate_day_conflicts
    assert _candidate_day_conflicts(candidate, watch) == expected


def test_auspicious_dates_section_has_almanac_caveat():
    from saju_engine.premium_report import _ReportContext, _section_auspicious_dates
    ctx = _ReportContext(_harish_chart_for_dates(), tier="deep", generation_date="2026-09-20")
    lines = "\n".join(_section_auspicious_dates(ctx))
    assert "Almanac caveat" in lines
    assert "not a finished 택일" in lines


def test_monthly_lucky_dates_not_capped_at_five_and_has_caveat():
    """Regression for the original R7 cap-at-5 bug (2026-09-20): there must
    be no artificial truncation. Updated 2026-09-25 (E-11): adding 형/자형
    to the branch-conflict filter legitimately lowers Harish's real monthly
    count from ~10-12 (충/해/파 alone) to 4 (his 亥 day branch self-punishes
    and his 丑 hour branch sits in the 丑戌未 triad) — manually verified
    against every October 2026 favorable-element day (5, 6, 14, 26 pass;
    3/15 excluded for 형, 4/16 for 자형, 13/25 for 해, 23 for 해, 24 for
    충+형). The test now asserts the exact, doctrine-complete count instead
    of a threshold that assumed the pre-E-11 filter.
    """
    from saju_engine.premium_report import _ReportContext, _section_monthly_lucky_dates
    ctx = _ReportContext(_harish_chart_for_dates(), tier="deep", generation_date="2026-09-20")
    lines = "\n".join(_section_monthly_lucky_dates(ctx, months_ahead=1))
    assert "Almanac caveat" in lines
    lines2 = _section_monthly_lucky_dates(ctx, months_ahead=2)
    oct_row = next(l for l in lines2 if l.startswith("| October"))
    dates_cell = oct_row.split("|")[2]
    dates = [d.strip() for d in dates_cell.split(",")]
    assert dates == ["5", "6", "14", "26"], f"unexpected dates: {oct_row!r}"


def test_season_signal_correctly_buckets_depleted_month_stages():
    """Own find while implementing R17: `_STAGE_WEIGHT` scores range 0.0-2.0
    and are NEVER negative, so the old `<= -0.5` "depleted" threshold could
    never fire — a Day Master at 사/절 (score 0.0) or 병 (0.2) was always
    mis-bucketed as "mixed" instead of depleted."""
    from saju_engine.prose_fillers import _season_signal
    assert _season_signal(0.0) == "depleted"  # 사, 절
    assert _season_signal(0.2) == "depleted"  # 병
    assert _season_signal(2.0) == "supported"  # 제왕
    assert _season_signal(0.7) == "mixed"  # 양


# ── E-12 (2026-09-25 audit) ──────────────────────────────────────────────


def _harish_deep_report():
    from saju_engine.engine import compute_chart
    from saju_engine.premium_report import generate_premium_report
    chart = compute_chart(
        name="harish-e12", gender="M",
        year=1992, month=6, day=4, hour=3, minute=10,
        longitude=79.4408, utc_offset=5.5,
    )
    return generate_premium_report(chart, tier="deep")


def test_e12_deficient_gisin_is_reconciled_and_companion_decade_named():
    report = _harish_deep_report()
    # Fire is both the least-present element and the climate-resolved 기신.
    assert "Fire is also this chart's challenging element (기신)" in report
    # 辛亥 is a 비견 decade — it must not be labelled as if it were 겁재.
    line = next(l for l in report.splitlines() if "(辛亥" in l and "peer/rival" in l)
    assert "**비견**" in line
    # Major-luck table shows stem AND branch element (丁未 → Fire / Earth).
    assert "| 丁未 | Fire / Earth |" in report


def test_e13_daeun_start_note_gives_calendar_month_and_app_convention():
    report = _harish_deep_report()
    line = next(l for l in report.splitlines() if "대운수 (starting age)" in l)
    assert "≈ Dec 1992" in line
    assert "대운수 1" in line and "1, 11, 21" in line


def test_e7_star_basis_is_labelled_and_year_anchor_selectable():
    from saju_engine.engine import compute_chart
    from saju_engine.premium_report import generate_premium_report
    kw = dict(name="h", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
              longitude=79.4408, utc_offset=5.5)
    day_report = generate_premium_report(compute_chart(**kw), tier="deep")
    assert "Counted from your day branch **亥**" in day_report
    year_chart = compute_chart(**kw, star_anchor="year")
    assert year_chart.stars["earth_bane"] == ["申"]
    assert year_chart.to_dict()["star_anchor"] == "year"
    year_report = generate_premium_report(year_chart, tier="deep")
    assert "Counted from your year branch **申** (traditional Korean basis)" in year_report


def test_validation_harish_partner_table_and_natal_rows():
    report = _harish_deep_report()
    assert "| Radiant, expressive, and momentum-driven | Fire | **Watch** |" in report
    assert "| Half Harmony | 巳+丑 |" in report
    assert "乙↔辛" in report
    assert "numeric least-represented-element pick" not in report
