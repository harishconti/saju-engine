"""Premium client-facing report generator.

Produces a polished, tiered markdown report from a fully-derived `Chart`
following the 9-section structure in `knowledge/10-output-template.md`
(Cover, Chart at a Glance, Day Master Portrait, Career & Wealth, Relationships,
Health & Vitality, Timing, Practical Guidance Summary, Closing Note).

Seven tier values are accepted; the first three are the one-time landing-page
products, `companion` is the monthly subscription product, and the last three
are legacy internal tiers kept for backward compatibility:

  * sample   — The Hook (complimentary, 1 page): compact cover + four pillars +
               element balance + Day Master + lucky cues + upgrade invitation.
  * essential — The Essential Report ($19, 6–7 pages): everything in The Hook
                plus Chart at a Glance, short Day Master portrait, Career &
                Wealth overview, Major Luck table, abbreviated Lucky Attributes,
                short Closing Note.
  * deep     — The Deep Destiny Report ($55, 10–12 pages): everything in
               Essential plus full Day Master Portrait, Relationships, Health &
               Vitality, Business & Launch Timing, six-year year-by-year
               windows, full Practical Guidance, full Closing Note. An MP3
               audio summary is delivered alongside the PDF by default.
  * companion — Cosmic Companion ($9/month, 3–4 pages): focused monthly/
                annual timing read with Chart at a Glance, Current Major Luck
                snapshot, Next 12-month window, Practical Guidance Summary, and
                short Closing Note.
  * spark    — Legacy short tier: compact Day Master portrait + Practical
               Guidance + short Closing Note (no career/relationships/health/timing).
  * reading  — Legacy full-tier: Day Master portrait + Career & Wealth +
               Relationships + Health & Vitality + Timing + full Practical
               Guidance + Closing Note (no deep-dive add-ons).
  * fullmap  — Legacy ultra-deep tier: everything in `deep` plus Natal Pattern
               Analysis, Wealth & Investment Timing, Relocation/Travel Guidance,
               Life Themes by Major Luck Period, Monthly Lucky Dates.

See `CLAUDE.md` (Tiered Client Products) and `README.md` (Client products)
for the canonical tier mapping.

The engine fills all deterministic content (tables, element balance, timing
windows, lucky attributes) and drafts interpretive prose sections marked for
human/AI review.

This module does NOT replace the reader. It is a token-reduction aid: the AI
interpreter receives a structured premium draft and only needs to refine,
personalize, and remove the `[ENGINE DRAFT — REVIEW REQUIRED]` markers before
the report goes to a client.
"""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from . import lookup as L
from . import sewoon as SE
from .chart import Chart, DaeunPeriod, Pillar
from . import prose_fillers as PF
from .hanja_glossary import inject_hanja
from .plain_glossary import collect_used_terms, gloss_first_use, render_terms_section
from .yongsin import favorable_element
from .report_data import (
    ELEMENT_EMOJI,
    TIER_CONFIG,
    _career_tiers,
    _career_why,
    _chart_signature,
    _compatibility_rows,
    _day_master_in_season,
    _domain_element,
    _element_balance,
    _element_balance_table,
    _hidden_stems_str,
    _STEM_EN,
    _STEM_PROFILE,
    _ELEMENT_ORGANS,
    _ELEMENT_ASSOCIATIONS,
    _CAREER_DOMAINS,
    _GROUNDING_PRACTICES,
    _SIGNATURES,
    _PILLAR_POSITION_LABELS,
    _PILLAR_AREAS,
    _strength_label,
    normalize_tier,
)


# Re-exported from `report_data` so callers that imported them from
# `premium_report` keep working. The canonical definitions live in
# `report_data.py`; do not edit them here.
__all__ = [
    "TIER_CONFIG",
    "_STEM_EN",
    "_STEM_PROFILE",
    "_ELEMENT_ORGANS",
    "_ELEMENT_ASSOCIATIONS",
    "_CAREER_DOMAINS",
    "_GROUNDING_PRACTICES",
    "_SIGNATURES",
    "_PILLAR_POSITION_LABELS",
    "_PILLAR_AREAS",
    "_career_tiers",
    "_career_why",
    "_chart_signature",
    "_compatibility_rows",
    "_day_master_in_season",
    "_domain_element",
    "_element_balance",
    "_element_balance_table",
    "_hidden_stems_str",
    "_strength_label",
    "normalize_tier",
    "generate_premium_report",
    "_ReportContext",
]


# ── Internal helpers (data tables and chart-derived helpers live in report_data) ──

# Tiers that produce a document handed straight to a paying client. Internal
# reviewer notes ("verify against the knowledge files", "engine heuristic only")
# must never appear in these — see _reviewer_note. Non-client callers (e.g. an
# internal draft) get the notes.
_CLIENT_TIERS = {"sample", "essential", "deep", "spark", "reading", "fullmap", "companion"}


def _reviewer_note(ctx: "_ReportContext", text: str) -> List[str]:
    """Return a blockquote reviewer note, or nothing for client-facing tiers.

    `text` is the note body without the leading `>` or surrounding `*`.
    """
    if getattr(ctx, "tier", None) in _CLIENT_TIERS:
        return []
    return [f">*{text}*", ""]


def _append_callout(lines: List[str], text: str, ctx: "_ReportContext") -> None:
    """Append an 'In plain words' blockquote to a section, unless tier is sample."""
    if getattr(ctx, "tier", None) == "sample" or not text:
        return
    if lines and lines[-1] != "":
        lines.append("")
    lines.append(text)
    lines.append("")


def _right_now_callout(chart: Chart, override: Optional[str] = None) -> str:
    """Return a short, personalized paragraph about the reference year and period.

    Uses the chart's reference date to find the matching annual luck (세운) and
    the active major luck (대운) window. This keeps the report stable for
    past/future queries and reproducible in tests.

    ``override`` is the reader-argued element carried by the report generator
    (``_ReportContext.favorable_override``). Reading the raw
    ``strength_assessment["candidate_favorable"]`` here named an element the
    engine did not actually resolve for climate-tie-broken or overridden
    charts — the same two-channel bug already fixed in ``report_data.py``'s
    career sections; see ``_resolved_favorable`` there.
    """
    ref = chart.reference_date_obj()
    current_year = ref.year if ref else None
    current_age = chart.current_age
    current_daeun = chart.current_daeun

    current_sewoon = next((h for h in chart.sewoon if h.year == current_year), None) if current_year else None

    parts: List[str] = []
    if ref:
        parts.append(
            f"Right now, in {ref.strftime('%B %Y')}, you are moving through a year whose energy is "
            f"shaped by **{current_sewoon.combined if current_sewoon else 'the current annual luck'}** "
            f"({current_sewoon.stem_tengod if current_sewoon else 'annual ten-god'})."
        )
    else:
        parts.append(
            "No reference date is set, so the current annual-luck window cannot be pinned to a specific year."
        )

    if current_daeun:
        parts.append(
            f"This sits inside your broader **{current_daeun.combined}** major luck period "
            f"(ages {current_daeun.start_age}–{current_daeun.end_age}), whose theme is "
            f"{current_daeun.stem_tengod or 'major-luck ten-god'}."
        )

    # Tie to favorable element — resolved channel (조후 merge + reader override),
    # not the raw 억부 candidate; see the docstring above.
    fe = favorable_element(chart, override).element
    favorable = fe if fe and fe != "—" else ""
    if favorable:
        parts.append(
            f"For your chart, the most useful energy to lean into this year is **{favorable}**: "
            f"look for decisions, environments, and relationships that bring {favorable.lower()} qualities forward."
        )

    return " ".join(parts)


# ── Tier-aware section builders ────────────────────────────────────────────

class _ReportContext:
    """Shared values used by every section builder."""

    def __init__(
        self,
        chart: Chart,
        tier: str,
        generation_date: str,
        favorable_override: Optional[str] = None,
    ):
        self.chart = chart
        self.tier = tier
        self.config = TIER_CONFIG[tier]
        self.generation_date = generation_date
        # Kept so section builders that resolve an element *independently* of
        # self.favorable / self.supporting (the career subsystem) can honour the
        # same reader override instead of silently resolving the engine value.
        self.favorable_override = favorable_override

        dm = chart.day_master
        dm_info = chart.day_master_info
        self.dm = dm
        self.dm_info = dm_info
        self.dm_element = dm_info.get("element", "")
        self.dm_en = _STEM_EN.get(dm, dm)

        sa = chart.strength_assessment or {}
        # 용신 resolved through the single source of truth (see yongsin.py) so the
        # value + provenance match the compatibility report for the same person.
        fe = favorable_element(chart, favorable_override)
        self.favorable = fe.element
        self.favorable_note = fe.note
        self.favorable_method = fe.method
        self.supporting = fe.supporting
        self.unfavorable = sa.get("candidate_unfavorable", "—")
        self.verdict = sa.get("verdict", "balanced")
        self.strength_label = _strength_label(chart)

        # Querier-relative current major-luck period (computed once by the engine).
        self.current_daeun: Optional[DaeunPeriod] = chart.current_daeun

        # Priority: special follower grids > transformation grids > regular grids.
        # This matches the classical order of rarity / interpretive weight.
        pattern_name = "Standard chart"
        if chart.patterns:
            if chart.patterns.get("special_forms"):
                pattern_name = "종격 (Follower Grid) candidate"
            elif chart.patterns.get("transformation_grid"):
                pattern_name = "화격 (Transformation Grid) candidate"
            elif chart.patterns.get("regular_grid"):
                regular = chart.patterns["regular_grid"]
                if regular:
                    pattern_name = f"{regular[0].name_ko} / {regular[0].name_en}"
        self.pattern_name = pattern_name

        # Stable report ID for cover/footer branding.
        slug = re.sub(r"[^a-z0-9]+", "-", (chart.name or "client").lower()).strip("-")
        self.report_id = f"CID-{slug}-{generation_date.replace('-', '')}-{tier.upper()}"


# ── Method-transparency disclosures ──────────────────────────────────────────
# Hour-branch windows are 2-hour solar windows starting on odd hours (子 23:00,
# 丑 01:00, 寅 03:00, …). A corrected solar time within this many minutes of a
# window boundary is a "knife-edge" birth: the neighboring hour pillar is a
# plausible alternative and the hour pillar should carry lower confidence.
HOUR_BOUNDARY_MARGIN_MIN = 10


def _solar_time_note(chart) -> List[str]:
    """True-solar-time disclosure, including a knife-edge hour-boundary flag.

    The engine silently applies a solar-time correction when a longitude is
    given; reports must surface it so the reader can audit which hour pillar
    the chart used (external-review feedback, 2026-09-07).
    """
    sc = getattr(chart, "solar_correction", None) or {}
    original = sc.get("original_time")
    solar = sc.get("solar_time")
    if not (original and solar) or original == solar:
        return []

    corr = sc.get("correction_minutes")
    lon = sc.get("longitude")
    std = sc.get("standard_longitude")
    where = ""
    if lon is not None and std is not None:
        where = f" (birthplace {lon}°E vs the {std}°E zone meridian)"

    lines = [
        f"**Time method:** recorded birth time {original} (local clock) corrected to true solar time **{solar}**"
        f"{where}{', ' + f'{corr:+g} min' if corr is not None else ''}. "
        "Hour branches follow 2-hour solar windows, so the pillars above use the corrected time.",
    ]

    # Knife-edge flag: distance from the nearest odd-hour boundary
    # (branch windows start on odd hours: 子 23:00, 丑 01:00, 寅 03:00, …).
    try:
        hh, mm = (int(x) for x in solar.split(":"))
    except (ValueError, AttributeError):
        return lines
    minutes = hh * 60 + mm
    raw = (minutes - 60) % 120  # 0 at odd-hour marks
    dist_to_boundary = min(raw, 120 - raw)
    if dist_to_boundary <= HOUR_BOUNDARY_MARGIN_MIN:
        lines.append(
            f"> **⚠ Hour-boundary note:** the corrected time is only ~{dist_to_boundary} minutes from a "
            "2-hour branch boundary. If the recorded clock time carries even a few minutes of error, the "
            "neighboring hour pillar is a plausible alternative — treat the hour pillar (and its palace "
            "themes) as lower-confidence in this reading."
        )
    return lines


def _daeun_direction_note(chart) -> str:
    """Disclose the major-luck (대운) direction and its gender input.

    대운 direction is derived from the year-stem polarity and the querent's
    gender; the calculation is correct but was previously invisible in the
    report (external-review feedback, 2026-09-07).
    """
    gender = getattr(chart, "gender", None)
    if gender not in ("M", "F") or not getattr(chart, "daeun", []):
        return "**Luck direction:** not computed — major-luck (대운) direction requires the querent's gender; provide it to complete the timing tables."
    from .lookup import daeun_direction, STEM_INFO

    direction = daeun_direction(chart.year.stem, gender)
    polarity = STEM_INFO[chart.year.stem]["polarity"]
    gender_en = "male" if gender == "M" else "female"
    arrow = "advancing from the month pillar" if direction == "forward" else "retracing from the month pillar"
    return (
        f"**Luck direction:** {direction}, {arrow} — derived from a {polarity.lower()} year stem "
        f"({chart.year.stem}) and {gender_en} gender, per the classical rule (yang year + male, "
        "or yin year + female → forward; otherwise backward)."
    )


def _section_cover(ctx: _ReportContext, compact: bool = False) -> List[str]:
    tier = ctx.config
    lines = [
        "# Korean Four Pillars of Destiny · Saju Reading",
        "",
        f"## {ctx.chart.name or 'Client'} — {tier['name']} · {tier['price']}",
        "",
        f"*{tier['tagline']}*",
        "",
        f"**Born:** {ctx.chart.birth_date} · {ctx.chart.birth_time} · {ctx.chart.city or '—'}",
        "",
        *_solar_time_note(ctx.chart),
        "",
        f"**Day Master:** {ctx.dm_en}",
        "",
        f"**Report generated:** {ctx.generation_date} · **Report ID:** {ctx.report_id}",
        "",
        "*Delivered by CosmicSaju · cosmicsaju.com*",
        "",
    ]
    if not compact:
        lines.append(f"**Chart signature:** *{_chart_signature(ctx.chart)}*")
        lines.append("")
    # Deep Destiny cover: confirm the MP3 audio is included by default.
    if ctx.tier == "deep":
        lines += [
            "**(Audio summary included)** Your MP3 audio summary is included — delivered with this report.",
            "",
        ]
    lines += [
        "---",
        "",
    ]
    return lines


def _section_chart_at_a_glance(ctx: _ReportContext) -> List[str]:
    lines = [
        "## Chart at a Glance",
        "",
        "### Four Pillars",
        "",
        "| | Year | Month | Day | Hour |",
        "|---|---|---|---|---|",
    ]
    stem_row = "| Stem | " + " | ".join(p.stem for p in ctx.chart.pillars) + " |"
    branch_row = "| Branch | " + " | ".join(p.branch for p in ctx.chart.pillars) + " |"
    hidden_row = "| Hidden Stems | " + " | ".join(_hidden_stems_str(p) for p in ctx.chart.pillars) + " |"
    lines += [stem_row, branch_row, hidden_row, ""]

    lines += ["### Element Balance", ""]
    lines += _element_balance_table(ctx.chart)
    lines += [
        "",
        "> _Methodology: each element's share counts the 8 visible stems and branches at weight 1.0 plus "
        "hidden stems at reduced weights (main qi 0.6, middle 0.3, residual 0.1) because hidden stems are "
        "submerged qi; the counts are then normalized to 100%._",
    ]
    lines += ["", "### Quick Reference", ""]
    lines += [
        f"- **Day Master:** {ctx.dm_en}",
        f"- **Strength:** {ctx.strength_label} — a seasonal-strength reading; a full classical analysis may refine it.",
        f"- **Favorable Element:** {ctx.favorable} — {ctx.favorable_note}",
        f"- **Supporting Element:** {ctx.supporting}",
        f"- **Avoid / Watch:** {ctx.unfavorable or '—'}",
    ]
    if ctx.current_daeun:
        lines.append(
            f"- **Current Major Luck:** {ctx.current_daeun.combined} (ages {ctx.current_daeun.start_age}-{ctx.current_daeun.end_age})"
        )
    lines.append(f"- {_daeun_direction_note(ctx.chart)}")
    lines.append(f"- **Pattern / Formation:** {ctx.pattern_name}")
    lines += [
        "",
        "### What This Year Means for You",
        "",
        f"{_right_now_callout(ctx.chart, ctx.favorable_override)}",
        "",
        "---",
        "",
    ]
    return lines


def _section_day_master_portrait(ctx: _ReportContext, short: bool = False) -> List[str]:
    profile = _STEM_PROFILE.get(ctx.dm, {})
    lines = [
        "## Day Master Portrait",
        "",
    ]
    if not short:
        lines += _reviewer_note(
            ctx, "Chart-derived first draft — verify against the relevant knowledge files before client delivery."
        )

    lines += [
        f"With **{ctx.dm}** ({ctx.dm_en}) as your Day Master, your core self carries the image of the **{profile.get('image', ctx.dm_element)}**. "
        f"Your natural strengths run toward **{profile.get('strengths', 'strength')}**, while the shadow side can show as **{profile.get('weaknesses', 'weakness')}**.",
        "",
    ]

    if not short:
        lines += [
            f"Born in a **{ctx.dm_element}** chart with the engine reading as **{ctx.strength_label.lower()}**, the way you meet the world is shaped by how much {ctx.dm_element} energy is available. "
            f"When balanced, you express the best of {ctx.dm_element}; when stressed, the unintegrated side may dominate.",
            "",
            f"Your growth edge is to consciously cultivate **{ctx.favorable}** energy — the favorable element — so that your {ctx.dm_element} nature has the right container and outlet.",
            "",
            PF.dm_arrival_narrative(ctx),
            "",
        ]

    # Essential and Deep tiers include a per-pillar walk (shorter in Essential,
    # 4–5 sentences per pillar in Deep). Tier-gated below.
    if ctx.tier == "essential":
        lines += _four_pillars_one_by_one(ctx, sentences=2)
    elif ctx.tier == "deep":
        lines += _four_pillars_one_by_one(ctx, sentences=4)
        # Deep tier adds the full Ten-God distribution table right after the
        # per-pillar walk so the reader has a single pillar-by-pillar reference.
        lines += _section_ten_god_distribution_table(ctx)
        _append_callout(lines, PF.plain_words_ten_gods(ctx), ctx)

    _append_callout(lines, PF.plain_words_day_master(ctx), ctx)
    lines += ["---", ""]
    return lines


def _four_pillars_one_by_one(ctx: _ReportContext, sentences: int = 2) -> List[str]:
    """Return a Four Pillars One by One sub-section for Essential/Deep tiers.

    Each pillar gets a short paragraph of `sentences` prose sentences. The
    shorter form (2 sentences) belongs to the Essential tier; the longer form
    (4–5 sentences) to the Deep tier.

    All prose is engine-drafted and marked for review.
    """
    lines = ["### Four Pillars, One by One", ""]
    lines += _reviewer_note(
        ctx,
        "Chart-derived per-pillar walk — refine each entry by reading the relevant "
        "`knowledge/01-stems.md` and `knowledge/02-branches.md`.",
    )
    for p in ctx.chart.pillars:
        label = _PILLAR_POSITION_LABELS.get(p.position, p.position.capitalize())
        area = _PILLAR_AREAS.get(p.position, "the corresponding life area")
        stem_en = _STEM_EN.get(p.stem, p.stem)
        branch_elem = L.BRANCH_ELEMENT.get(p.branch, "")
        # Look up stem ten-god from chart.ten_gods if available.
        tengod = ""
        for hit in ctx.chart.ten_gods:
            if hit.position == f"{p.position}_stem":
                tengod = hit.tengod_en or hit.tengod
                break
        stem_elem = L.STEM_INFO.get(p.stem, {}).get("element", "")
        lines.append(f"#### {label} — {p.combined} ({stem_en})")
        lines.append("")
        if sentences >= 2:
            first = (
                f"The {p.combined} pillar pairs the **{p.stem}** stem ({stem_en}) with the "
                f"**{p.branch}** branch, together shaping **{area}**."
            )
            if tengod:
                first += (
                    f" Its stem reads as **{tengod}** relative to your Day Master, so "
                    f"this area of life tends to carry that dynamic."
                )
            lines.append(first)
            lines.append("")
            lines.append(
                f"The **{branch_elem}** branch is the container for this area and the "
                f"**{stem_elem}** stem is its driver — read the two together when weighing "
                f"how {p.position}-pillar matters unfold."
            )
            lines.append("")
        if sentences >= 4:
            lines.append(
                f"Because the stem belongs to the **{stem_elem}** element, it tends to bring {stem_elem.lower()}-flavoured themes "
                f"into this life area — qualities of motion, structure, or feeling that quietly shape how the querent relates to {p.position}-pillar matters."
            )
            lines.append(
                f"Hidden stems within the {p.branch} branch add layers: any mid- or residual-stem ten-god the querent carries here will surface as a recurring sub-theme when this life area activates."
            )
            lines.append(
                f"When the annual or major luck touches the {p.branch} branch or the {p.stem} stem, "
                f"expect {p.position}-pillar themes to move to the foreground for that window."
            )
            lines.append("")
    return lines


def _section_ten_god_distribution_table(ctx: _ReportContext) -> List[str]:
    """Deep-exclusive ten-god distribution table.

    Shows one row per pillar with:
      - Pillar position and combined stem-branch
      - The pillar's stem ten-god (relative to the Day Master)
      - The branch's hidden stems as a short list
      - Each hidden stem's ten-god (relative to the Day Master)
      - A one-line reading of the pillar's overall feel

    All cells are filled deterministically; the "Reading" column is a
    short auto-generated summary that the reader must refine.
    """
    lines = [
        "### Ten-God Distribution Table",
        "",
        "A pillar-by-pillar view of the ten-god (십신) picture — including the hidden stems inside each branch, which most of the time shape the chart's deeper themes more than the visible stems alone.",
        "",
        "| Pillar | Stem | Ten-God (Stem) | Branch Hidden Stems | Hidden Ten-Gods | Reading |",
        "|---|---|---|---|---|---|",
    ]

    for p in ctx.chart.pillars:
        # Stem ten-god (from chart.ten_gods, position == "<pos>_stem").
        stem_tg = ""
        for hit in ctx.chart.ten_gods:
            if hit.position == f"{p.position}_stem":
                stem_tg = hit.tengod_en or hit.tengod
                break
        # Branch hidden stems with their ten-god names.
        hidden_strs: List[str] = []
        hidden_tg_strs: List[str] = []
        for role, stem in p.hidden_stems:
            label = {"main": "본", "middle": "중", "residual": "여"}.get(role, role)
            try:
                tg = L.ten_god(ctx.chart.day_master, stem)
            except Exception:
                tg = "—"
            hidden_strs.append(f"{stem} ({label})")
            hidden_tg_strs.append(tg)
        hidden_cell = ", ".join(hidden_strs) if hidden_strs else "—"
        hidden_tg_cell = ", ".join(hidden_tg_strs) if hidden_tg_strs else "—"
        # Short auto-reading: name the dominant hidden-stem ten-god if any.
        dominant_tg = hidden_tg_strs[0] if hidden_tg_strs else stem_tg or "—"
        reading = f"Outer layer: {stem_tg or '—'}; inner driver through the branch: {dominant_tg}."
        lines.append(
            f"| {_PILLAR_POSITION_LABELS.get(p.position, p.position)} — {p.combined} "
            f"| {p.stem} | {stem_tg or '—'} "
            f"| {hidden_cell} | {hidden_tg_cell} | {reading} |"
        )

    lines += [
        "",
        "Use this table as a quick reference when you are unsure which ten-god a particular pillar carries. The visible stem is the persona; the hidden stems are the undertow.",
        "",
        "---",
        "",
    ]
    return lines


def _section_career_wealth(ctx: _ReportContext, mode: str = "standard") -> List[str]:
    """Career & Wealth section.

    Modes:
      - "essential": Essential tier — keeps the archetype table and core themes,
                     plus the short "Wealth Preservation Note".
      - "standard" : Reading tier and Deep non-deep portion — full subsections.
      - "deep"     : Deep tier — full subsections plus the exclusive deep-dive.
    """
    lines = ["## Career & Wealth", ""]
    lines += _reviewer_note(
        ctx,
        "Chart-derived first draft — verify archetype table against "
        "`knowledge/03-five-elements.md` and `knowledge/05-ten-gods.md`.",
    )
    lines += [
        "### Career Archetypes",
        "",
        "| Tier | Domain | Why It Fits | Example Roles |",
        "|---|---|---|---|",
    ]
    for tier, domain, why, examples in _career_tiers(
        ctx.chart, ctx.favorable_override
    ):
        lines.append(f"| {tier} | {domain} | {why} | {examples} |")

    lines += [
        "",
        "### Wealth Pattern",
        "",
        PF.wealth_pattern(ctx),
        "",
    ]

    if mode in ("essential", "standard"):
        lines += [
            "### Wealth Preservation Note",
            "",
            PF.wealth_preservation_short(ctx),
            "",
        ]

    if mode in ("standard", "deep"):
        lines += [
            "### Employment vs. Entrepreneurship",
            "",
            PF.employment_vs_entrepreneurship(ctx),
            "",
            "### Income Rhythm",
            "",
            PF.income_rhythm(ctx),
            "",
            "### Skill-Levers to Develop",
            "",
            PF.skill_levers(ctx),
            "",
        ]

    if mode == "deep":
        lines += [
            "### Wealth Preservation Note",
            "",
            PF.wealth_preservation_long(ctx),
            "",
            "### Career Deep-Dive",
            "",
            "#### Company-Type Fit",
            PF.company_type_fit(ctx),
            "",
            "#### Boss / Team Dynamics",
            PF.boss_team_dynamics(ctx),
            "",
            "#### Red-Flag Environments",
            PF.red_flag_environments(ctx),
            "",
            "#### Decade-by-Decade Career Strategy",
        ]
        for p in ctx.chart.daeun:
            lines.append("")
            lines.append(f"**Ages {p.start_age}-{p.end_age} — {p.combined}**")
            lines.append("")
            lines.append(PF.decade_career_strategy(ctx, p))
        lines.append("")

    _append_callout(lines, PF.plain_words_career(ctx), ctx)
    lines += ["---", ""]
    return lines


def _section_relationships(ctx: _ReportContext, mode: str = "standard") -> List[str]:
    """Relationships section.

    Modes:
      - "essential": Essential tier — relationship style + compatibility table
                     + mindfulness notes, plus "Key Relationship Timing" and
                     "Friendship & Social Energy".
      - "standard" : Reading tier — adds timing and friendship notes.
      - "deep"     : Deep tier — everything plus exclusive deep-dive modules.
    """
    lines = ["## Relationships", ""]
    lines += _reviewer_note(
        ctx,
        "Chart-derived first draft — review against `knowledge/07-special-formations.md` "
        "(도화살, 배우자궁) and `knowledge/05-ten-gods.md`.",
    )
    lines += [
        "### Relationship Style",
        "",
        PF.relationship_style(ctx),
        "",
        "### Spouse Palace Ten-God",
        "",
        PF.spouse_palace_tengod(ctx),
        "",
        "### Partner Compatibility",
        "",
        "| Partner Type | Element | Fit Level | Why |",
        "|---|---|---|---|",
    ]
    for archetype, elem, fit, reason in _compatibility_rows(ctx.dm_element, ctx.favorable, ctx.verdict):
        lines.append(f"| {archetype} | {elem} | {fit} | {reason} |")

    lines += [
        "",
        "### Three Things to Be Mindful Of",
        "",
    ]
    for note in PF.three_mindful_notes(ctx):
        lines.append(f"- {note}")
    lines.append("")

    if mode in ("essential", "standard", "deep"):
        lines += [
            "### Key Relationship Timing",
            "",
            ">*Relationship theme per year for the next six years — read alongside the annual windows table.*",
            "",
            "| Year | Pillar | Note |",
            "|---|---|---|",
        ]
        current_year = (ctx.chart.reference_date_obj() or datetime.now().date()).year
        try:
            annual_hits = SE.build_sewoon_range(
                ctx.chart.day_master, ctx.chart.branches, current_year, current_year + 5
            )
        except Exception:
            annual_hits = []
        for h in annual_hits:
            tg = h.stem_tengod_en or h.stem_tengod or "—"
            note = PF.relationship_timing_row(h.year, h.combined, tg)
            lines.append(
                f"| {h.year} | {h.combined} ({tg}) | {note} |"
            )
        lines.append("")

        lines += [
            "### Friendship & Social Energy",
            "",
            PF.friendship_social_energy(ctx),
            "",
        ]

    if mode == "deep":
        lines += [
            "### Relationship Deep-Dive",
            "",
            "#### Attachment Patterns from Chart Structure",
            PF.attachment_patterns(ctx),
            "",
            "#### Marriage Timing Windows",
            PF.marriage_timing_windows(ctx),
            "",
            "#### Family Dynamics",
            PF.family_dynamics(ctx),
            "",
        ]

        # Partner Compatibility Snapshot — only rendered when ctx.partner_chart
        # is supplied. Designed to be human-driven (the reader supplies a
        # partner's chart from a separate code path).
        partner_chart = getattr(ctx, "partner_chart", None)
        if partner_chart is not None:
            lines += _render_compat_snapshot(ctx, partner_chart)
            lines.append("")

        lines += [
            "#### Partner Chart Add-On",
            "",
            "*Curious about a specific person? Add a compatibility reading — the Deep Compatibility report ($45) — by replying with their birth details.*",
            "",
        ]

    _append_callout(lines, PF.plain_words_relationships(ctx), ctx)
    lines += ["---", ""]
    return lines


def _render_compat_snapshot(ctx, partner_chart) -> List[str]:
    """Render a Partner Compatibility Snapshot inside the deep-tier Relationships
    section when a `partner_chart` is attached to the report context.

    This is intentionally lightweight — it shows the composite score, band, and
    the top red / favorable flags from the compat engine, without re-emitting
    the full 11 sub-system breakdown (which lives in the standalone Compat
    product). See `tools/saju_engine/compat.py` and `knowledge/11-gunghap.md`.
    """
    # Local import to avoid circular import at module-load time.
    from .compat import compat_score
    report = compat_score(ctx.chart, partner_chart)
    lines: List[str] = []
    lines.append("#### Partner Compatibility Snapshot (궁합 스냅샷)")
    lines.append("")
    lines.append(
        f"**Composite Score (with attached partner chart):** "
        f"{report.score}/100 → **{report.band}**  "
        "*(see knowledge/11-gunghap.md §Composite Weight)*"
    )
    lines.append("")
    if report.red_flags:
        lines.append("- ⚠️ **Top red flags:**")
        for f in report.red_flags:
            lines.append(f"  - {f}")
    if report.favorable_points:
        lines.append("- ✅ **Top favorable points:**")
        for f in report.favorable_points:
            lines.append(f"  - {f}")
    if not (report.red_flags or report.favorable_points):
        lines.append(
            "- _No specific flags surfaced — the relationship profile is neutral; "
            "see the standalone 두 분 궁합 product for the full 11-sub-system "
            "breakdown._"
        )
    lines.append("")
    return lines


def _section_health_vitality(ctx: _ReportContext) -> List[str]:
    pct, _ = _element_balance(ctx.chart)
    excess = max(pct, key=pct.get)
    deficient = min(pct, key=pct.get)
    lines = ["## Health & Vitality", ""]
    lines += _reviewer_note(
        ctx,
        "Chart-derived first draft — review against `knowledge/03-five-elements.md` "
        "organ mapping. Not a medical diagnosis.",
    )
    lines += [
        "### Primary Watchpoints",
        "",
        f"- **Element excess:** {excess} — pay attention to the {_ELEMENT_ORGANS.get(excess, 'associated')} system.",
        f"- **Element deficiency:** {deficient} — the {_ELEMENT_ORGANS.get(deficient, 'associated')} system may need gentle support.",
        f"- {PF.depleted_element_health(ctx)}",
        "",
        "### Grounding Practices",
        "",
    ]
    for practice in _GROUNDING_PRACTICES.get(ctx.favorable, ["Meditation", "Balanced meals", "Regular sleep"]):
        lines.append(f"- {practice}")
    lines += [
        "",
        "### The Overdrive Warning",
        "",
        PF.overdrive_warning(ctx),
        "",
        "### Seasonal & Daily Rhythms",
        "",
        PF.seasonal_daily_rhythms(ctx),
        "",
        "> *This section reflects classical Five Element organ mapping and is not a medical diagnosis. Consult a licensed healthcare provider for any health concerns.*",
        "",
    ]
    _append_callout(lines, PF.plain_words_health(ctx), ctx)
    lines += ["---", ""]
    return lines


def _health_deep_dive(ctx: _ReportContext) -> List[str]:
    """Extra health module used by the Deep tier to reach 10–12 pages."""
    pct, _ = _element_balance(ctx.chart)
    excess = max(pct, key=pct.get)
    deficient = min(pct, key=pct.get)
    lines = ["## Health & Vitality — Deep-Dive", ""]
    lines += _reviewer_note(
        ctx,
        "Chart-derived deep-dive — review against `knowledge/03-five-elements.md` "
        "and `knowledge/06-twelve-stages.md`. Not a medical diagnosis.",
    )
    lines += [
        "### Element Story",
        "",
        PF.element_story(ctx),
        "",
        "### Body-System Map",
        "",
        f"- **Excess system ({excess}):** {_ELEMENT_ORGANS.get(excess, 'associated')} — watch for signs of over-activity or congestion.\n"
        f"- **Deficient system ({deficient}):** {_ELEMENT_ORGANS.get(deficient, 'associated')} — gentle rebuilding over time is usually better than forceful stimulation.",
        "",
        "### Stress Signature",
        "",
        PF.stress_signature(ctx),
        "",
        "### Recovery Toolkit",
        "",
        PF.recovery_toolkit(ctx),
        "",
        "### Long-Term Vitality Strategy",
        "",
        PF.long_term_vitality_strategy(ctx),
        "",
        "---",
        "",
    ]
    return lines


def _section_natal_patterns(ctx: _ReportContext) -> List[str]:
    """Surface the chart's structural branch relationships and dominant grid pattern."""
    lines = [
        "## Natal Pattern Analysis",
        "",
        "This section gathers the visible structural signals in your natal chart — combinations, clashes, harmonies, and self-punishments — so the reader can see which branches are speaking to one another. These patterns do not dictate events; they describe recurring themes and pressures that tend to appear across life areas.",
        "",
    ]

    # Dominant pattern candidate (engine aid, not classical ruling)
    if ctx.chart.patterns:
        lines.append(f"**Dominant pattern candidate:** *{ctx.pattern_name}*")
        lines.append("")

    rels = []
    if ctx.chart.combinations_6:
        for a, c, elem, pa, pb in ctx.chart.combinations_6:
            rels.append(("Six Combination", f"{a}+{c}", f"transforms toward {elem} energy between the {pa} and {pb} palaces"))
    if ctx.chart.three_harmonies:
        for a, b, c, elem in ctx.chart.three_harmonies:
            rels.append(("Three Harmony", f"{a}+{b}+{c}", f"strengthens {elem} energy through the {a}, {b}, and {c} branches"))
    if ctx.chart.clashes:
        for a, c in ctx.chart.clashes:
            rels.append(("Six Clash", f"{a}↔{c}", "a tension or activation between two life palaces; often a call to adjust, release, or decide"))
    if ctx.chart.self_punishments:
        for a, _ in ctx.chart.self_punishments:
            rels.append(("Self-Punishment", f"{a}{a}", f"the {a} branch appears twice; a recurring inner pattern that asks for self-awareness"))
    if ctx.chart.three_punishments:
        for a, b, c, _ in ctx.chart.three_punishments:
            if c == "—":
                # Partial punishment: only two branches of the 삼형 frame are present.
                rels.append(("Three Punishment (partial)", f"{a}-{b}", "two branches of a punishment frame without the third; a lighter but recurring structural pressure that matures slowly"))
            else:
                rels.append(("Three Punishment", f"{a}-{b}-{c}", "a heavier structural pressure involving three branches; usually points to a life theme that matures slowly"))
    if ctx.chart.six_harms:
        for a, b in ctx.chart.six_harms:
            rels.append(("Six Harm", f"{a}-{b}", "a quiet friction that can drain energy if ignored"))
    if ctx.chart.six_breaks:
        for a, b in ctx.chart.six_breaks:
            rels.append(("Six Break", f"{a}-{b}", "a disruption of an expected harmony; often appears as a changed plan or external adjustment"))

    if rels:
        lines += ["| Pattern | Branches | Classical Note |", "|---|---|---|"]
        for kind, branches, note in rels:
            lines.append(f"| {kind} | {branches} | {note} |")
        lines.append("")
    else:
        lines.append("_No major branch patterns were flagged in this chart. The reading therefore rests more heavily on stem ten-god distribution and element balance._")
        lines.append("")

    lines += [
        "### Pattern Narratives",
        "",
    ]
    grid_note = PF.regular_grid_narrative(ctx)
    if grid_note:
        lines.append(grid_note)
        lines.append("")
    special_note = PF.special_grid_note(ctx)
    if special_note:
        lines.append(special_note)
        lines.append("")
    branch_snapshot = PF.branch_relationship_snapshot(ctx)
    if branch_snapshot:
        lines.append(branch_snapshot)
        lines.append("")
    if not (grid_note or special_note or branch_snapshot):
        lines.append(
            "No strong pattern narrative is auto-drafted for this chart; the structural table above and the "
            "ten-god distribution carry the reading."
        )
        lines.append("")

    lines += [
        "### What This Means in Plain Language",
        "",
        PF.pattern_story(ctx),
        "",
    ]
    _append_callout(lines, PF.plain_words_pattern(ctx), ctx)
    lines += ["---", ""]
    return lines


def _section_major_luck_narrative(ctx: _ReportContext) -> List[str]:
    """Narrate each 10-year major-luck period to add depth for the Deep tier."""
    lines = [
        "## Life Themes by Major Luck Period",
        "",
        "Each 10-year major-luck (대운) period brings a new stem and branch into prominence. The stem shows the outer theme through its 십신 relationship to your Day Master; the branch shows the stage of life and the underlying terrain. Read these as tendencies, not fixed events.",
        "",
    ]
    for p in ctx.chart.daeun:
        stage = L.twelve_stage(ctx.chart.day_master, p.branch)
        branch_elem = L.BRANCH_ELEMENT.get(p.branch, "")
        tg = p.stem_tengod_en or p.stem_tengod or "—"
        lines += [
            f"### Ages {p.start_age}–{p.end_age}: {p.combined}",
            "",
            f"- **Ten-God theme:** {tg}",
            f"- **Branch element & 12-stage:** {branch_elem} · {stage}",
            f"- **Favorable lean:** {p.favorable_status or 'neutral'}",
            "",
            PF.major_luck_narrative(p, ctx),
            "",
        ]
    lines += ["---", ""]
    return lines


def _section_lifetime_decade_roadmap(ctx: _ReportContext) -> List[str]:
    """Deep-exclusive visual lifetime roadmap of all major-luck periods.

    Renders a markdown table summarising the favorable lean of each
    10-year major-luck period. The HTML/Playwright PDF backend picks up
    the `data-favorable` cell values and replaces this table with an
    SVG horizontal timeline. The reportlab backend prints the table
    unchanged.
    """
    lines = [
        "## Lifetime Decade Roadmap",
        "",
        "A single-glance view of all 8 major-luck periods in your life and the favorable lean of each. Green segments are clearly favorable, amber are mixed, red lean toward challenge. Treat this as a rhythm, not a verdict — the supporting-element periods are often where the most important growth quietly happens.",
        "",
        "<!-- decade-roadmap:start -->",
        "",
        "| Ages | Pillar | Ten-God | Favorable Lean |",
        "|---|---|---|---|",
    ]
    for p in ctx.chart.daeun:
        status = (p.favorable_status or "neutral").lower()
        if "favor" in status or status in {"strong", "supporting", "helpful"}:
            lean = "favorable"
        elif "challeng" in status or "difficult" in status or "weak" in status:
            lean = "challenging"
        else:
            lean = "neutral"
        tg = p.stem_tengod_en or p.stem_tengod or "—"
        lines.append(
            f"| {p.start_age}–{p.end_age} "
            f"| {p.combined} "
            f"| {tg} "
            f"| {lean} |"
        )
    lines += [
        "",
        "<!-- decade-roadmap:end -->",
        "",
        "---",
        "",
    ]
    return lines


def _section_wealth_timing(ctx: _ReportContext) -> List[str]:
    """Grounded wealth-timing notes based on wealth ten-gods and major-luck periods."""
    wealth_hits = [h for h in ctx.chart.ten_gods if h.tengod_en and "Wealth" in h.tengod_en]
    lines = [
        "## Wealth & Investment Timing",
        "",
        "This section identifies where wealth ten-gods appear in the natal chart and which major-luck and annual windows tend to activate the wealth story. It is not investment advice; it is a Saju lens on when the chart's energy favors planning, negotiation, or conservation.",
        "",
    ]
    if wealth_hits:
        lines += ["| Position | Stem | Ten-God | Note |", "|---|---|---|---|"]
        for h in wealth_hits:
            lines.append(f"| {h.position} | {h.stem} | {h.tengod_en} | Natal wealth signal visible here. |")
        lines.append("")
    else:
        lines.append("_No direct wealth ten-god appears on a visible stem in this chart. Wealth may arrive through resource, output, or authority channels instead — the reader should trace the money path through the hidden stems and the timing tables._")
        lines.append("")

    # Major-luck periods that carry wealth ten-god or favorable element
    wealth_periods = [
        p for p in ctx.chart.daeun
        if (p.stem_tengod_en and "Wealth" in p.stem_tengod_en)
        or (p.stem_element == ctx.favorable or p.stem_element == ctx.supporting)
    ]
    if wealth_periods:
        lines.append("**Major-luck periods that carry wealth or favorable-element energy:**")
        lines.append("")
        for p in wealth_periods[:4]:
            lines.append(f"- Ages {p.start_age}–{p.end_age} ({p.combined}, {p.stem_tengod_en or p.stem_tengod}) — a window where income, asset, or value-creation themes are more likely to surface.")
        lines.append("")

    lines += [
        "### Investment Style Cue",
        "",
        f"Because your favorable element is **{ctx.favorable}** and your supporting element is **{ctx.supporting}**, years and months that bring these elements into the annual or monthly pillar are generally more supportive for financial planning and negotiation. Years dominated by your unfavorable element call for conservation, review, and patience rather than expansion.",
        "",
        "---",
        "",
    ]
    return lines


def _section_relocation_directions(ctx: _ReportContext) -> List[str]:
    """Practical direction guidance drawn from the favorable element."""
    fav_assoc = _ELEMENT_ASSOCIATIONS.get(ctx.favorable, {})
    sup_assoc = _ELEMENT_ASSOCIATIONS.get(ctx.supporting or "", {})
    lines = [
        "## Relocation, Travel & Direction Guidance",
        "",
        "Classical Saju associates each element with a direction and a quality of space. These notes are directional tendencies, not guarantees about a specific city or property.",
        "",
        "| Element | Direction | Best For | Use With Care |",
        "|---|---|---|---|",
        f"| {ctx.favorable} (favorable) | {fav_assoc.get('direction', '—')} | Restoration, big decisions, starting new rhythms | Years when this element is weak in the annual luck |",
        f"| {ctx.supporting or '—'} (supporting) | {sup_assoc.get('direction', '—')} | Building momentum, collaboration, steady growth | Periods of heavy clash or punishment in the natal branches |",
        "",
        f"- **Favorable orientation:** Facing or sleeping with head toward **{fav_assoc.get('direction', 'your favorable direction')}** is traditionally considered supportive for your chart.",
        f"- **Supporting orientation:** Use **{sup_assoc.get('direction', 'your supporting direction')}** when you need steady, collaborative energy.",
        "",
        "### Travel & Move Timing",
        "",
        PF.travel_timing(ctx),
        "",
        "---",
        "",
    ]
    return lines


def _section_timing(
    ctx: _ReportContext,
    full_forecast: bool = False,
    annual_range: Optional[Tuple[int, int]] = None,
    include_annual: bool = True,
) -> List[str]:
    heading = "## Timing: Major Luck & Annual Windows" if include_annual else "## Timing: Major Luck Periods"
    lines = [
        heading,
        "",
        f"{_daeun_direction_note(ctx.chart)}",
        "",
        "### Major Luck Periods",
        "",
        "| Age | Pillar | Element Theme | Ten-God | Career Theme | Relationship Theme |",
        "|---|---|---|---|---|---|",
    ]
    for p in ctx.chart.daeun:
        elem_theme = L.BRANCH_ELEMENT.get(p.branch, "")
        tg = p.stem_tengod_en or p.stem_tengod or "—"
        career_t, rel_t = PF.major_luck_theme_row(p, ctx)
        lines.append(
            f"| {p.start_age}-{p.end_age} | {p.combined} | {elem_theme} | {tg} | {career_t} | {rel_t} |"
        )

    lines += [
        "",
        "### Current Period Deep-Dive",
        "",
        PF.current_period_deep_dive(ctx),
        "",
    ]

    if include_annual:
        current_year = (ctx.chart.reference_date_obj() or datetime.now().date()).year
        if full_forecast:
            # 10-year forward forecast (current year + next 9).
            annual_hits = SE.build_sewoon_range(
                ctx.chart.day_master,
                ctx.chart.branches,
                current_year,
                current_year + 9,
            )
            lines += [
                "### 10-Year Forecast",
                "",
                "| Year | Pillar | Annual Ten-God | Overall Theme | Best Uses | Watch Out For |",
                "|---|---|---|---|---|---|",
            ]
        elif annual_range:
            annual_hits = SE.build_sewoon_range(
                ctx.chart.day_master,
                ctx.chart.branches,
                annual_range[0],
                annual_range[1],
            )
            lines += [
                f"### Annual Windows ({annual_range[0]}–{annual_range[1]})",
                "",
                "| Year | Pillar | Annual Ten-God | Overall Theme | Best Uses | Watch Out For |",
                "|---|---|---|---|---|---|",
            ]
        else:
            # Reading tier: 3-year window (current year ± 1).
            annual_hits = [
                h for h in ctx.chart.sewoon
                if current_year - 1 <= h.year <= current_year + 1
            ]
            lines += [
                "### Annual Windows (current year ± 1)",
                "",
                "| Year | Pillar | Annual Ten-God | Overall Theme | Best Uses | Watch Out For |",
                "|---|---|---|---|---|---|",
            ]

        for h in annual_hits:
            tg = h.stem_tengod_en or h.stem_tengod or "—"
            theme, best, watch = PF.annual_window_row(h, ctx)
            lines.append(
                f"| {h.year} | {h.combined} | {tg} | {theme} | {best} | {watch} |"
            )

        # Deep-tier year-by-year notes
        if full_forecast or annual_range:
            lines += [
                "",
                "### Year-by-Year Notes",
                "",
                "A quick reading of each year's energy relative to your Day Master and favorable element. Treat these as timing cues, not predictions.",
                "",
            ]
            for h in annual_hits:
                lines.append(f"- **{h.year} · {h.combined} ({h.stem_tengod_en or h.stem_tengod or '—'}):** {PF.year_by_year_note(h, ctx)}")
            lines.append("")

    _append_callout(lines, PF.plain_words_timing(ctx), ctx)
    lines += ["", "---", ""]
    return lines


def _section_practical_guidance(ctx: _ReportContext, full: bool = False) -> List[str]:
    lines = [
        "## Practical Guidance Summary",
        "",
    ]
    if full:
        lines += [
            "### Top 5 Strengths",
            "",
        ]
        for s in PF.top_strengths(ctx):
            lines.append(f"- {s}")
        lines += [
            "",
            "### Top 5 Growth Areas",
            "",
        ]
        for s in PF.top_growth_areas(ctx):
            lines.append(f"- {s}")
        lines += [
            "",
            "### 5 Practical Recommendations",
            "",
        ]
        for s in PF.practical_recommendations(ctx):
            lines.append(f"- {s}")
        lines.append("")

    lines += ["### Lucky Attributes — Your Favorable Element Reference Card", ""]
    if not full:
        # Spark tier: abbreviated list
        lines += [
            f"- **Element:** {ctx.favorable}",
            f"- **Colors:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('colors', '—')}",
            f"- **Direction:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('direction', '—')}",
            f"- **Numbers:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('numbers', '—')}",
        ]
    else:
        lines += [
            f"- **Element:** {ctx.favorable}",
            f"- **Colors:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('colors', '—')}",
            f"- **Direction:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('direction', '—')}",
            f"- **Numbers:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('numbers', '—')}",
            f"- **Season:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('season', '—')}",
            f"- **Gemstones:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('gemstones', '—')}",
            f"- **Foods:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('foods', '—')}",
            f"- **Best Times:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('best_times', '—')}",
            f"- **Avoid:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('avoid', '—')}",
            f"- **Business Lucky Numbers:** {_business_numbers(ctx)}",
        ]
    lines += ["", "---", ""]
    return lines


def _section_auspicious_dates(ctx: _ReportContext) -> List[str]:
    """Draft a 90-day auspicious-dates window for the Full Map tier.

    The engine currently marks these as reader-drafted placeholders because
    precise date selection depends on the querent's specific question and
    local calendar conventions. The list provides 3–5 candidate windows
    biased toward the favorable element and away from clashes on the day branch.
    """
    ref = ctx.chart.reference_date_obj() or datetime.now().date()
    dates: List[Tuple[str, str]] = []
    # Pick roughly every ~18 days within the next 90 days, landing on days
    # whose stem/branch element leans toward the favorable element.
    candidate_offsets = [7, 21, 42, 63, 84]
    for offset in candidate_offsets:
        d = ref + timedelta(days=offset)
        dates.append((d.strftime("%Y-%m-%d (%A)"), PF.auspicious_date_note(d.strftime("%Y-%m-%d"), ctx)))

    lines = [
        "## Auspicious Dates — Next 90 Days",
        "",
        f"> The next 90-day window from {ref.strftime('%B %Y')} includes the following candidate dates. "
        "A qualified reader should cross-check each date against the querent's specific natal activations and local calendar before recommending it.",
        "",
        "| Date | Suggested Use / Reader Note |",
        "|---|---|",
    ]
    for d, note in dates:
        lines.append(f"| {d} | {note} |")
    lines += ["", "---", ""]
    return lines


def _section_closing_note(ctx: _ReportContext, short: bool = False) -> List[str]:
    if short:
        return [
            "## Closing Note",
            "",
            PF.closing_note_short(ctx),
            "",
            "---",
            "",
        ]
    return [
        "## Closing Note",
        "",
        PF.closing_note_long(ctx),
        "",
        "---",
        "",
    ]


def _section_sample_hook(ctx: _ReportContext) -> List[str]:
    """Compact one-page snapshot used by the free Hook tier."""
    pct, _ = _element_balance(ctx.chart)
    assoc = _ELEMENT_ASSOCIATIONS.get(ctx.favorable, {})
    lines = [
        "## Your Chart Snapshot",
        "",
        "### Four Pillars",
        "",
        "| Year | Month | Day | Hour |",
        "|---|---|---|---|",
        "| " + " | ".join(p.combined for p in ctx.chart.pillars) + " |",
        "",
        "### Element Balance",
        "",
    ]
    for element in ["Fire", "Earth", "Metal", "Water", "Wood"]:
        value = pct.get(element, 0.0)
        emoji = ELEMENT_EMOJI.get(element, "")
        lines.append(f"- {emoji} **{element}:** {value}%")
    lines += [
        "",
        "### Quick Read",
        "",
        f"- **Day Master:** {ctx.dm_en}",
        f"- **Strength:** {ctx.strength_label}",
        f"- **Favorable Element:** {ctx.favorable}",
        "",
        "### What This Year Means for You",
        "",
        f"{_year_one_liner(ctx.chart, ctx.favorable_override)}",
        "",
        "_Your full chart contains 8 major luck periods spanning your lifetime — this snapshot shows only the surface._",
        "",
        "### Your Lucky Cues",
        "",
        f"- **Colors:** {assoc.get('colors', '—')}",
        f"- **Direction:** {assoc.get('direction', '—')}",
        f"- **Numbers:** {assoc.get('numbers', '—')}",
        "",
        "This is just a snapshot. The full Essential or Deep Destiny report opens the story behind these numbers — your strengths, relationships, career arcs, and the timing that matters most.",
        "",
        "---",
        "",
    ]
    return lines


def _year_one_liner(chart: Chart, override: Optional[str] = None) -> str:
    """Return a single-sentence summary of the reference year's energy.

    Used by the Hook tier where space is tight. Falls back to a generic
    sentence if the reference year's 세운 cannot be derived.
    """
    ref = chart.reference_date_obj()
    current_year = ref.year if ref else None
    if current_year is None:
        return (
            f"This year carries {ctx_favorable_phrase(chart, override)} — a useful window to "
            f"bring {chart.day_master_info.get('element', '')} energy into clearer focus."
        )
    sewoon = next((h for h in chart.sewoon if h.year == current_year), None)
    if sewoon is None:
        return (
            f"This year carries {ctx_favorable_phrase(chart, override)} — a useful window to "
            f"bring {chart.day_master_info.get('element', '')} energy into clearer focus."
        )
    tengod = sewoon.stem_tengod_en or sewoon.stem_tengod or "annual energy"
    return (
        f"{current_year} is a **{sewoon.combined} ({tengod})** year — "
        f"an invitation to lean into {ctx_favorable_phrase(chart, override)}."
    )


def ctx_favorable_phrase(chart: Chart, override: Optional[str] = None) -> str:
    """Return a short favorable-element phrase for narrative sentences.

    Reads the resolved channel (``yongsin.favorable_element``, which applies
    the 조후 merge and any reader override), not the raw 억부 candidate — see
    ``_right_now_callout`` above for the same two-channel fix.
    """
    fe = favorable_element(chart, override).element
    favorable = fe if fe and fe != "—" else ""
    if not favorable:
        return "your favorable element"
    return f"{favorable.lower()} energy"


def _section_business_launch(ctx: _ReportContext) -> List[str]:
    """Business-launch timing module used by the Deep Destiny tier.

    Fills a six-year window anchored on the chart reference date with annual
    pillars plus business-specific lucky cues. Interpretive prose is left as a
    reader draft because a real launch recommendation depends on the specific
    business, partners, and natal activations.
    """
    current_year = (ctx.chart.reference_date_obj() or datetime.now().date()).year
    lines = ["## Business & Launch Timing", ""]
    lines += _reviewer_note(
        ctx,
        "Chart-derived first draft — review against `knowledge/08-luck-pillars.md` "
        "and the annual table below.",
    )
    lines += [
        f"For a {ctx.dm_element} Day Master, the most supportive launch windows tend to come when the annual pillar carries **{ctx.favorable}** or **{ctx.supporting}** energy and does not clash the natal day branch.",
        "",
        f"### Your Business Lucky Numbers",
        "",
        f"Use **{_business_numbers(ctx)}** in pricing, launch dates, seat numbers, and branding choices where practical. These numbers carry the frequency of your favorable element.",
        "",
        "### Best Launch Types for This Chart",
        "",
        PF.business_launch_format(ctx),
        "",
        f"### Favorable Windows ({current_year}–{current_year + 5})",
        "",
        "| Year | Pillar | Why It Matters | Suggested Use |",
        "|---|---|---|---|",
    ]
    annual_hits = SE.build_sewoon_range(
        ctx.chart.day_master, ctx.chart.branches, current_year, current_year + 5
    )
    for h in annual_hits:
        theme, best, _watch = PF.annual_window_row(h, ctx)
        lines.append(
            f"| {h.year} | {h.combined} | {h.stem_tengod_en or h.stem_tengod or '—'} ({theme}) | {best} |"
        )
    lines += [
        "",
        "### Quarterly / Seasonal Reminders",
        "",
        PF.business_seasonal_note(ctx),
        "",
        "### Things to Watch",
        "",
    ]
    for i, item in enumerate(PF.business_watch_items(ctx), 1):
        lines.append(f"{i}. {item}")
    lines += [
        "",
        "---",
        "",
    ]
    return lines


def _business_numbers(ctx: _ReportContext) -> str:
    """Return a business-focused lucky-number string from favorable + supporting elements."""
    fav_nums = _ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get("numbers", "—")
    if ctx.supporting and ctx.supporting != ctx.favorable and ctx.supporting in _ELEMENT_ASSOCIATIONS:
        sup_nums = _ELEMENT_ASSOCIATIONS[ctx.supporting].get("numbers", "—")
        return f"{fav_nums} (favorable {ctx.favorable}) and {sup_nums} (supporting {ctx.supporting})"
    return f"{fav_nums} (favorable {ctx.favorable})"


def _section_toc(ctx: _ReportContext) -> List[str]:
    """Table of Contents for multi-page paid tiers."""
    if ctx.tier == "essential":
        items = [
            "Chart at a Glance",
            "Day Master Portrait — Short Portrait incl. Four Pillars One by One",
            "Career & Wealth — incl. Wealth Preservation Note",
            "Timing: Major Luck Periods",
            "Practical Guidance Summary",
            "Closing Note",
        ]
    elif ctx.tier in ("deep", "fullmap"):
        items = [
            "Chart at a Glance",
            "How to Use This Report",
            "Day Master Portrait — incl. Four Pillars One by One & Ten-God Distribution",
            "Career & Wealth",
            "Relationships — incl. Relationship Deep-Dive & Partner Add-On",
            "Health & Vitality",
            "Natal Pattern Analysis",
            "Wealth & Investment Timing",
            "Relocation, Travel & Direction Guidance",
            "Business & Launch Timing",
            "Timing: Major Luck & Annual Windows",
            "Life Themes by Major Luck Period — incl. Lifetime Decade Roadmap",
            "Auspicious Dates — Next 90 Days",
            "Health & Vitality — Deep-Dive",
            "Monthly Lucky Dates",
            "Practical Guidance Summary",
            "MP3 Audio Summary",
            "Closing Note",
        ]
    else:
        return []
    lines = ["## Table of Contents", ""]
    for item in items:
        lines.append(f"- {item}")
    lines += ["", "---", ""]
    return lines


def _section_how_to_use(ctx: _ReportContext) -> List[str]:
    """Brief 'How to Use This Report' guide (Deep tier, FAQ-style).

    Lives right after the Table of Contents so the client reads it before
    diving into the technical sections. Pure prose, no chart data — answers
    the most common reader questions about Saju, favorable elements, and how
    to return to the document over time.
    """
    return [
        "## How to Use This Report",
        "",
        "This document is a structured, multi-section reading. It is meant to be returned to, not read once and shelved. A few notes that make it easier to use:",
        "",
        "1. **What does \"favorable element\" mean in daily life?** It is the element (Wood, Fire, Earth, Metal, or Water) that tends to balance your chart. Bringing it into your environment, schedule, and decisions reduces friction and supports steadier growth.",
        f"2. **Should I move north or only wear {ctx.favorable.lower()}?** No. The favorable element is a tendency, not a rule. Wear the colors that feel right, work in the direction that suits you, but do not rearrange your life around a single element. The goal is balance, not obsession.",
        "3. **Can Saju tell me what illness I might get?** No. Classical Saju maps tendencies in the body's elemental systems (e.g. *excess Wood* may show up in the liver channel), but it does not diagnose. Always consult a licensed healthcare provider for any health concern.",
        "4. **How often should I get a reading?** Most readers find that a full re-reading every 2–3 years is enough, with a brief check-in at each major annual or lunar-new-year transition. Use the Annual Windows table in this report to track the larger currents yourself.",
        "5. **What is a major luck period?** A 10-year stretch of life shaped by a new stem and branch (대운) that overlays your natal chart. The Major Luck Periods table summarises all of yours. Plan long-term decisions with the table in hand.",
        "6. **How is Saju different from Western astrology?** Saju is solar-lunar calendar-based and built on the Five Elements and Yin-Yang, not the tropical zodiac. There is no equivalent of \"rising sign\" or \"house system\"; the four pillars and the timing overlays are the entire frame.",
        "7. **Should I read this report chronologically?** No. The Chart at a Glance, Quick Reference, and Closing Note are the entry points. Use the timing tables (Annual Windows, Monthly Lucky Dates) as a navigation layer, not as a linear story.",
        "",
        "Return to the Practical Guidance Summary whenever you need a reminder. Return to the Major Luck Periods table at every life transition. Return to the Closing Note when you want a single, well-formed paragraph to sit with.",
        "",
        "---",
        "",
    ]


def _section_upsell(ctx: _ReportContext) -> List[str]:
    """Upsell/CTA box for the Hook tier."""
    if ctx.tier == "sample":
        current_year = (ctx.chart.reference_date_obj() or datetime.now().date()).year
        return [
            "### Want the Full Story?",
            "",
            f"This snapshot is just the doorway. The **Essential Report** ($19) explains your career arc, major luck periods, and lucky-element guide; the **Deep Destiny Report** ($55) adds year-by-year {current_year}–{current_year + 5} timing, relationship and business-launch guidance, monthly lucky dates, and an included MP3 audio summary.",
            "",
        ]
    if ctx.tier == "essential":
        return [
            "### Ready to Go Deeper?",
            "",
            "The **Deep Destiny Report** ($55) builds on this Essential reading with a full decade forecast, monthly lucky dates, expanded business & launch timing, relationship deep-dives, and an **MP3 audio summary included by default** — so you can carry the guidance with you.",
            "",
        ]
    return []


def _section_30_day_plan(ctx: _ReportContext) -> List[str]:
    """A four-week action plan aligned with the favorable element (Essential tier)."""
    fav = ctx.favorable
    assoc = _ELEMENT_ASSOCIATIONS.get(fav, {})
    color = assoc.get("colors", "").split(",")[0] if assoc.get("colors") else fav
    direction = assoc.get("direction", "your favorable direction")
    foods = assoc.get("foods", "favorable-element foods")
    lines = [
        "## 30-Day Action Plan",
        "",
        f"A short, focused cycle designed to bring more **{fav}** energy into your daily rhythm. These steps are tendencies and invitations, not prescriptions — adapt them to your schedule and comfort.",
        "",
        "| Week | Focus | Suggested Action |",
        "|---|---|---|",
        f"| Week 1 | Tune the environment | Add {color} accents, face {direction} when working, and clear one space that feels stagnant.",
        f"| Week 2 | Feed the element | Bring {foods} into two meals a day and notice which foods leave you feeling steady.",
        f"| Week 3 | Move with the energy | Take one daily walk or practice session at the time of day that carries {fav.lower()} qi for you.",
        "| Week 4 | Make one aligned decision | Choose one small career, relationship, or health choice that leans into your favorable element and notice the result.",
        "",
        "> *Carry the chart’s strength into action gradually. Big changes built on small, consistent moves tend to outlast dramatic swings.*",
        "",
        "---",
        "",
    ]
    return lines


def _branch_clashes(day_branch: str, natal_branches: List[str]) -> List[str]:
    """Return natal branches that clash with the given day branch."""
    clashing = []
    for a, c in L.SIX_CLASHES:
        if day_branch == a:
            clashing.append(c)
        elif day_branch == c:
            clashing.append(a)
    return clashing


def _section_monthly_lucky_dates(ctx: _ReportContext, months_ahead: int = 3, max_per_month: int = 5) -> List[str]:
    """Generate Monthly Lucky Dates for the Deep tier using daily-luck overlays."""
    ref = ctx.chart.reference_date_obj() or datetime.now().date()
    lines = [
        "## Monthly Lucky Dates",
        "",
        f"The next **{months_ahead} months** of favorable days, selected when the daily stem element matches your **{ctx.favorable}** or **{ctx.supporting}** element and the day branch does not clash your natal day branch.",
        "",
        "> _Methodology: each row filters the daily-luck (일운) stems to those whose element matches your favorable or supporting element, then drops any day whose branch clashes your natal day branch._",
        "",
        "| Month | Favorable Dates | Energy Note |",
        "|---|---|---|",
    ]

    fav_elems = {ctx.favorable}
    if ctx.supporting and ctx.supporting != ctx.favorable:
        fav_elems.add(ctx.supporting)
    day_branch = ctx.chart.day.branch
    natal_branches = list(ctx.chart.branches)

    # Advance by calendar months (year, month) rather than fixed 30-day chunks,
    # so January 31 → February 1 does not drift across the year.
    year, month = ref.year, ref.month
    for month_offset in range(months_ahead):
        if month_offset:
            month += 1
            if month > 12:
                month = 1
                year += 1
        # Walk through each day of the month.
        _, last_day = calendar.monthrange(year, month)
        selected: List[Tuple[int, str, str]] = []
        for day in range(1, last_day + 1):
            try:
                hit = SE.derive_ilwoon(ctx.chart.day_master, natal_branches, year, month, day)
            except Exception:
                continue
            stem_elem = L.STEM_INFO.get(hit.stem, {}).get("element", "")
            if stem_elem not in fav_elems:
                continue
            if hit.branch in _branch_clashes(day_branch, natal_branches):
                continue
            tengod_note = hit.stem_tengod_en or hit.stem_tengod
            selected.append((day, hit.combined, tengod_note))
            if len(selected) >= max_per_month:
                break

        month_label = date(year, month, min(ref.day, last_day)).strftime("%B %Y")
        if selected:
            date_str = ", ".join(str(d) for d, _, _ in selected)
            notes = " / ".join(f"{combo} ({tg})" for _, combo, tg in selected[:3])
        else:
            date_str = "—"
            notes = "No strongly favorable dates this month; use grounding routines instead."
        lines.append(f"| {month_label} | {date_str} | {notes} |")

    lines += [
        "",
        "> _For business-critical decisions, confirm the chosen date against the specific action type and consult a qualified reader._",
        "",
        "---",
        "",
    ]
    return lines


def _section_audio_summary_note(ctx: _ReportContext) -> List[str]:
    """Deep-tier note that the MP3 audio summary is included by default."""
    current_year = (ctx.chart.reference_date_obj() or datetime.now().date()).year
    return [
        "## MP3 Audio Summary — Included by Default",
        "",
        f"🎧 **Audio Summary:** Your MP3 companion to this report will be delivered alongside this PDF. It covers your Day Master portrait, current major-luck period, key timing windows for {current_year}–{current_year + 2}, and the top 5 practical recommendations in approximately 8–10 minutes.",
        "",
        "Listen once in full, then return to the chapters that match the season you are in.",
        "",
        "---",
        "",
    ]


# ── Main report generator ──────────────────────────────────────────────────
def generate_premium_report(
    chart: Chart,
    *,
    tier: str = "reading",
    generation_date: Optional[str] = None,
    favorable_override: Optional[str] = None,
) -> str:
    """Return a tiered premium client-facing markdown report from `chart`.

    Parameters
    ----------
    tier : str
        One of the landing-page tiers ("sample", "essential", "deep"), the
        monthly subscription tier ("companion"), or the legacy internal tiers
        ("spark", "reading" (default), "fullmap").
    generation_date : str | None
        Optional generation date string. Defaults to today.

    Returns
    -------
    str
        Markdown report. Interpretive prose is marked as an engine draft;
        the reader must review, refine, and remove the
        `[ENGINE DRAFT — REVIEW REQUIRED]` markers before client delivery.
    """
    tier = normalize_tier(tier)
    if generation_date is None:
        generation_date = (chart.reference_date_obj() or datetime.now().date()).strftime("%Y-%m-%d")

    ctx = _ReportContext(chart, tier, generation_date, favorable_override=favorable_override)

    sections: List[List[str]] = []
    sections.append(_section_cover(ctx, compact=(tier == "sample")))
    if tier != "sample":
        sections.append(_section_chart_at_a_glance(ctx))

    if tier == "sample":
        sections.append(_section_sample_hook(ctx))
        sections.append(_section_upsell(ctx))
        sections.append(_section_closing_note(ctx, short=True))
    elif tier == "essential":
        sections.append(_section_toc(ctx))
        sections.append(_section_day_master_portrait(ctx, short=True))
        sections.append(_section_career_wealth(ctx, mode="essential"))
        sections.append(_section_timing(ctx, include_annual=False))
        sections.append(_section_practical_guidance(ctx, full=False))
        sections.append(_section_closing_note(ctx, short=True))
    elif tier == "deep":
        sections.append(_section_toc(ctx))
        sections.append(_section_how_to_use(ctx))
        sections.append(_section_day_master_portrait(ctx, short=False))
        sections.append(_section_career_wealth(ctx, mode="deep"))
        sections.append(_section_relationships(ctx, mode="deep"))
        sections.append(_section_health_vitality(ctx))
        sections.append(_section_natal_patterns(ctx))
        sections.append(_section_wealth_timing(ctx))
        sections.append(_section_relocation_directions(ctx))
        sections.append(_section_business_launch(ctx))
        sections.append(_section_timing(ctx, full_forecast=True))
        sections.append(_section_major_luck_narrative(ctx))
        sections.append(_section_lifetime_decade_roadmap(ctx))
        sections.append(_section_auspicious_dates(ctx))
        sections.append(_health_deep_dive(ctx))
        sections.append(_section_monthly_lucky_dates(ctx, months_ahead=12))
        sections.append(_section_practical_guidance(ctx, full=True))
        sections.append(_section_audio_summary_note(ctx))
        sections.append(_section_closing_note(ctx, short=False))
    elif tier == "companion":
        # Focused monthly/annual timing read: chart snapshot + major-luck
        # snapshot + next 12-month window + practical guidance + short closing.
        current_year = (ctx.chart.reference_date_obj() or datetime.now().date()).year
        sections.append(_section_timing(ctx, annual_range=(current_year, current_year + 1)))
        sections.append(_section_practical_guidance(ctx, full=True))
        sections.append(_section_closing_note(ctx, short=True))
    elif tier == "spark":
        sections.append(_section_day_master_portrait(ctx, short=True))
        sections.append(_section_practical_guidance(ctx, full=False))
        sections.append(_section_closing_note(ctx, short=True))
    elif tier == "reading":
        sections.append(_section_day_master_portrait(ctx, short=False))
        sections.append(_section_career_wealth(ctx, mode="standard"))
        sections.append(_section_relationships(ctx, mode="standard"))
        sections.append(_section_health_vitality(ctx))
        sections.append(_section_timing(ctx, full_forecast=False))
        sections.append(_section_practical_guidance(ctx, full=True))
        sections.append(_section_closing_note(ctx, short=False))
    else:  # fullmap
        sections.append(_section_toc(ctx))
        sections.append(_section_how_to_use(ctx))
        sections.append(_section_day_master_portrait(ctx, short=False))
        sections.append(_section_career_wealth(ctx, mode="deep"))
        sections.append(_section_relationships(ctx, mode="deep"))
        sections.append(_section_health_vitality(ctx))
        sections.append(_section_natal_patterns(ctx))
        sections.append(_section_wealth_timing(ctx))
        sections.append(_section_relocation_directions(ctx))
        sections.append(_section_business_launch(ctx))
        sections.append(_section_timing(ctx, full_forecast=True))
        sections.append(_section_major_luck_narrative(ctx))
        sections.append(_section_lifetime_decade_roadmap(ctx))
        sections.append(_section_auspicious_dates(ctx))
        sections.append(_health_deep_dive(ctx))
        sections.append(_section_monthly_lucky_dates(ctx, months_ahead=12))
        sections.append(_section_practical_guidance(ctx, full=True))
        sections.append(_section_audio_summary_note(ctx))
        sections.append(_section_closing_note(ctx, short=False))

    sections.append([
        "*Engine-generated premium report draft. Interpretive prose must be reviewed and finalized by a qualified reader before client delivery.*",
    ])

    # Annotate Korean technical terms with Hanja on first use across the report.
    used: set = set()
    annotated = [inject_hanja("\n".join(s), used) for s in sections]
    doc = "\n".join(annotated)

    # Plain-language layer: gloss each jargon term on first use, then append a
    # tier-scaled "What the Terms Mean" section after the Closing Note.
    doc = gloss_first_use(doc, set())
    terms = render_terms_section(collect_used_terms(doc), tier)
    if terms:
        doc = doc.rstrip() + "\n\n" + terms
    return doc
