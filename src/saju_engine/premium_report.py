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
    _STAR_MEANING,
    _strength_label,
    normalize_tier,
)
from .stars import STAR_LABELS


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
    eot = sc.get("equation_of_time_minutes")
    lon = sc.get("longitude")
    std = sc.get("standard_longitude")
    where = ""
    if lon is not None and std is not None:
        where = f" (birthplace {lon}°E vs the {std}°E zone meridian)"
    eot_clause = f" (longitude {corr - eot:+g} min + equation of time {eot:+g} min)" if eot is not None and corr is not None else ""

    lines = [
        f"**Time method:** recorded birth time {original} (local clock) corrected to true solar time **{solar}**"
        f"{where}{', ' + f'{corr:+g} min' if corr is not None else ''}{eot_clause}. "
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
        unit = "minute" if dist_to_boundary == 1 else "minutes"
        lines.append(
            f"> **⚠ Hour-boundary note:** the corrected time is only ~{dist_to_boundary} {unit} from a "
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


def _daeun_starting_age_note(chart) -> str:
    """State the precise 대운수 (major-luck starting age), not just the
    rounded decade label.

    Bug found 2026-09-20 (external report review, 3rd pass, R19): knowledge/08's
    rule is "3 days = 1 year," so an integer starting age of 0 really means
    "somewhere in [0, 3) years" — a chart starting at ~4 months reads
    identically to one starting at 2.9 years under the bare integer.
    Confirmed live: Harish's own days-to-절기 count is ~1 day, i.e. a
    starting age of ~0.3 years (~4 months after birth), not a clean "age 0."
    """
    gender = getattr(chart, "gender", None)
    if gender not in ("M", "F") or not getattr(chart, "daeun", []):
        return ""
    from .lookup import daeun_direction
    from .daeun import starting_age_days

    direction = daeun_direction(chart.year.stem, gender)
    date_to_use = chart.effective_date or chart.birth_date
    time_to_use = "00:00"
    if chart.solar_correction and chart.solar_correction.get("solar_time"):
        time_to_use = chart.solar_correction["solar_time"]
    elif chart.birth_time:
        time_to_use = chart.birth_time
    try:
        hh, mm = (int(x) for x in time_to_use.split(":"))
    except (ValueError, AttributeError):
        hh, mm = 0, 0
    try:
        days = starting_age_days(
            int(date_to_use[:4]), int(date_to_use[5:7]), int(date_to_use[8:10]),
            direction, hour=hh, minute=mm,
        )
    except Exception:
        return ""
    if days is None:
        return ""
    precise_age = round(days / 3, 1)
    months = round(days * 4 / 3)
    start_age = chart.daeun[0].start_age if chart.daeun else int(precise_age)
    day_word = "day" if days == 1 else "days"
    month_word = "month" if months == 1 else "months"
    return (
        f"**대운수 (starting age):** ~{precise_age} (~{days} {day_word} to the qualifying 節氣 ÷ 3, "
        f"per knowledge/08's \"3 days = 1 year\" rule) — the first major-luck period begins "
        f"roughly {months} {month_word} after birth, inside the **{start_age}-{start_age + 9}** decade "
        f"label shown below, not precisely at its first birthday."
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


def _avoid_watch_text(ctx: _ReportContext) -> str:
    """Text for the Quick Reference 'Avoid / Watch' (기신/구신/한신) field.

    Bug found 2026-09-20 (external report review, 3rd pass): `strength.py`'s
    balanced-DM branch leaves `candidate_unfavorable` as `None` (the
    strong/weak branches compute a DM-relative 기신, but the classical
    "generates/overcomes 용신" formula the balanced branch actually needs is
    a 용신-relative one — see knowledge/03-five-elements.md's own worked
    example: 용신=Water -> 기신=Fire, 구신=Earth, 한신=Wood), so for every
    balanced/climate-gated chart (e.g. Harish's) this field rendered as a
    bare "—" with no guidance at all.

    Rather than patch `strength.py`'s raw heuristic dict (which would risk
    a raw-vs-resolved mismatch: `ctx.favorable` is the climate-resolved
    용신 from `yongsin.py`, which can differ from the heuristic's own
    `candidate_favorable` — the exact class of bug fixed elsewhere this
    session), this derives 기신/구신/한신 directly from `ctx.favorable`
    (the value the rest of the report already shows) using the same
    overcoming/generating cycles knowledge/03 defines. This mirrors the
    already-correct strong/weak branches, which keep their existing
    DM-relative 기신 text unchanged.
    """
    if ctx.unfavorable and ctx.unfavorable != "—":
        return ctx.unfavorable
    fav = ctx.favorable
    gisin = L.OVERCOMES.get(fav)  # 기신: the element 용신 overcomes
    gusin = next((k for k, v in L.OVERCOMES.items() if v == fav), None)  # 구신: restrains 용신
    hansin = L.GENERATES.get(fav)  # 한신: drains 용신 (용신 generates this)
    if not (gisin or gusin or hansin):
        return "—"
    parts = []
    if gisin:
        parts.append(f"{gisin} (기신, watch)")
    if gusin:
        parts.append(f"{gusin} (구신, restrains {fav})")
    if hansin:
        parts.append(f"{hansin} (한신, drains {fav})")
    return " · ".join(parts)


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
        "> _Methodology: each element's share counts the 4 visible stems (year/month/day/hour) at weight "
        "1.0, plus every branch's hidden stems (藏干) at reduced weights (main qi 0.6, middle 0.3, "
        "residual 0.1) — a branch's own elemental weight is carried entirely through its hidden stems "
        "(its main-qi hidden stem is usually the branch's nominal element), not counted a second time as "
        "a separate 1.0 entry, since that would double-count it; the counts are then normalized to 100%._",
    ]
    lines += ["", "### Quick Reference", ""]
    lines += [
        f"- **Day Master:** {ctx.dm_en}",
        f"- **Strength:** {ctx.strength_label} — {PF.strength_reasoning(ctx)}",
        f"- **Favorable Element:** {ctx.favorable} — {ctx.favorable_note}",
        f"- **Supporting Element:** {ctx.supporting}",
        f"- **Avoid / Watch:** {_avoid_watch_text(ctx)}",
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
            note = PF.relationship_timing_row(h.year, h.combined, tg, gender=ctx.chart.gender)
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
    excess_line = f"- **Element excess:** {excess} — pay attention to the {_ELEMENT_ORGANS.get(excess, 'associated')} system."
    if excess == ctx.favorable:
        # Bug found 2026-09-19 (external report review, 2nd pass): the raw
        # numeric-abundance "excess" read (knowledge/15-health-and-body.md
        # §Excess vs. Deficiency) and the climate/억부-resolved 용신
        # (knowledge/17-climate-method.md) can name the SAME element — here
        # Water is both Harish's most numerically-present element (27.8%)
        # AND his resolved 용신. Presenting both independently produced a
        # direct contradiction: "watch for Water excess" next to Grounding
        # Practices that recommend MORE Water-element activity. Neither
        # knowledge file states how to reconcile this collision (Ground
        # Rule 1/2: not inventing a resolution), so this surfaces the
        # tension explicitly instead of silently presenting both as if
        # unrelated.
        excess_line += (
            f" This is also your favorable element (용신) — classical 조후/억부 "
            f"resolution reads a chart's own 용신 as the element it structurally "
            f"needs, not a harmful surplus, even when it is also the most "
            f"numerically prominent one. The caution here is about extreme, "
            f"further concentration (e.g. through diet, environment, or timing "
            f"choices layered on top of an already-abundant element), not about "
            f"the element itself — which the Grounding Practices below still "
            f"recommend leaning into."
        )
    lines += [
        "### Primary Watchpoints",
        "",
        excess_line,
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
    tengod_conflicts = (ctx.chart.patterns or {}).get("tengod_conflicts", [])
    for c in tengod_conflicts:
        rels.append((f"{c['name_ko']} ({c['name_en']})", "상관 + 정관", c["note"]))

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

    # Other active 신살 — engine-computed but, before this fix, never
    # surfaced anywhere in the report. See _STAR_MEANING's docstring
    # (report_data.py) for what's deliberately excluded (도화/역마, already
    # covered elsewhere; 홍염/양인, no natal-context source).
    active_stars = [
        (key, positions) for key, positions in (ctx.chart.stars or {}).items()
        if positions and key in _STAR_MEANING
    ]
    if active_stars:
        lines += ["", "### Other Active 신살", ""]
        for key, positions in active_stars:
            label = STAR_LABELS.get(key, key)
            where = ", ".join(positions)
            lines.append(f"- **{label}** (at {where}): {_STAR_MEANING[key]}")
        lines.append("")

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
            f"- **Favorable lean:** {PF.period_favorable_status(p, ctx)}",
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
        status = PF.period_favorable_status(p, ctx).lower()
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
            tg_label = p.stem_tengod_en or p.stem_tengod
            cls = PF._TENGOD_FIVE_CLASS.get(p.stem_tengod, "")
            if cls == "Wealth":
                note = "a window where income, asset, or value-creation themes are more likely to surface."
            elif cls == "Companion":
                # Bug found 2026-09-19 (external report review, 2nd pass,
                # independently corroborated by a 3rd review): 겁재/비견
                # decades were listed here with the SAME wealth-opportunity
                # note as genuine 재성 decades, purely because the stem
                # ELEMENT happened to match 용신/희신 — but 비겁-class
                # ten-gods are classically read as wealth COMPETITORS
                # (겁재奪財, knowledge/13-wealth-and-business.md), the
                # opposite framing. This decade is included because its
                # element supports overall balance, not because it
                # specifically brings wealth.
                note = (
                    "your favorable element is active here, supporting overall stability — but its ten-god "
                    "is a peer/rival type (겁재奪財), classically read as wealth *competition* rather than "
                    "opportunity; keep shared-money agreements explicit here rather than expecting income "
                    "growth from it directly."
                )
            else:
                note = (
                    "your favorable element is active here, supporting overall balance rather than "
                    "specifically signaling a wealth-influx window."
                )
            lines.append(f"- Ages {p.start_age}–{p.end_age} ({p.combined}, {tg_label}) — {note}")
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
    ]
    # 역마살 (Post Horse Star) — bug found 2026-09-20 (external report
    # review): the engine already computes this correctly (`stars.py`'s
    # `post_horse`), but no report section ever surfaced it, even though it
    # is the one classical star most directly relevant to a Travel &
    # Relocation section. Confirmed missing for Harish, whose natal month
    # branch 巳 IS his 역마 branch (亥卯未 day-branch triplet -> 역마 at 巳).
    post_horse = (ctx.chart.stars or {}).get("post_horse", []) if ctx.chart.stars else []
    if post_horse:
        branches_str = ", ".join(post_horse)
        lines += [
            f"**역마살 (驛馬殺, Post Horse Star) is natally active at {branches_str}** — this classical "
            "star indicates a tendency toward movement: travel, relocation, or change of environment "
            "as a recurring life theme rather than a one-time event *(see knowledge/07-special-formations.md)*. "
            "Years or major-luck periods that activate this branch again tend to bring relocation or "
            "travel decisions to the foreground.",
            "",
        ]
    lines += ["---", ""]
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
    ]
    age_note = _daeun_starting_age_note(ctx.chart)
    if age_note:
        lines += ["", age_note]
    lines += [
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
            f"- **Gemstones (modern, optional):** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('gemstones', '—')}",
            f"- **Foods:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('foods', '—')}",
            f"- **Best Times:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('best_times', '—')}",
            f"- **Avoid:** {_ELEMENT_ASSOCIATIONS.get(ctx.favorable, {}).get('avoid', '—')}",
            f"- **Business Lucky Numbers:** {_business_numbers(ctx)}",
            "",
            # Bug found 2026-09-20 (external report review): knowledge/14
            # requires gemstone lists to be presented as "an optional,
            # clearly-labelled extra — never as derived doctrine," but the
            # card previously listed them as a plain fact alongside classical
            # doctrine (direction/colour/season/number). The inline label
            # above plus this footnote satisfy that requirement.
            "> _Direction, colours, season, and numbers above are classical "
            "오행 방위 doctrine (`knowledge/03-five-elements.md`). Gemstones are a "
            "modern popular-astrology convention, not classical 명리 (命理) — "
            "optional, not analytically load-bearing._",
        ]
    lines += ["", "---", ""]
    return lines


def _section_auspicious_dates(ctx: _ReportContext, window_days: int = 90) -> List[str]:
    """Scan the next `window_days` for real favorable-element, non-conflicting days.

    2026-09-19 fix (external report review): this used to pick 5 FIXED offsets
    (7/21/42/63/84 days out) regardless of what those dates' actual day-pillars
    were, then attached a generic templated sentence via
    ``PF.auspicious_date_note`` that named the favorable element without ever
    checking whether that specific date's stem matched it or whether its
    branch clashed the natal day branch. Confirmed live: 2026-10-10 (丁巳) was
    listed as "supported by Water" despite its branch 巳 directly clashing
    Harish's natal day branch 亥 (巳亥沖) — exactly the clash this section's own
    docstring claimed to filter for. Rewritten to reuse the same real
    day-pillar computation and clash filter as `_section_monthly_lucky_dates`
    (already validated correct), so a listed date is one whose day-stem
    element actually matches 용신/희신 and whose day-branch does not clash the
    natal day branch.

    2026-09-20 fix (external report review, 3rd pass, R7): (a) the table
    silently truncated to 5 dates regardless of how many actually qualified
    in the 90-day window — knowledge/16 gives no basis for that cap, so this
    now lists every qualifying day; (b) the filter checked only 충 (clash)
    against the day branch — knowledge/16 also requires avoiding 해 (harm)
    and 파 (break) against the day OR hour branch "when a cleaner day
    exists," so a day like 寅 (파 against a natal 亥 day branch) or 申 (해
    against 亥) is now excluded too, via `_candidate_day_conflicts`. A day
    that is simultaneously a natal 육합 partner and a 충/해/파 partner (the
    dual-status pairs knowledge/02 lists, e.g. 寅亥) is conservatively
    excluded here rather than shown as ambiguous — the caveat below tells
    the reader why the list may look short.
    """
    ref = ctx.chart.reference_date_obj() or datetime.now().date()
    fav_elems = {ctx.favorable}
    if ctx.supporting and ctx.supporting != ctx.favorable:
        fav_elems.add(ctx.supporting)
    day_branch = ctx.chart.day.branch
    hour_branch = ctx.chart.hour.branch if ctx.chart.hour else None
    watch_branches = [b for b in (day_branch, hour_branch) if b]
    natal_branches = list(ctx.chart.branches)

    selected: List[Tuple[date, str, str, str]] = []
    for offset in range(1, window_days + 1):
        d = ref + timedelta(days=offset)
        try:
            hit = SE.derive_ilwoon(ctx.chart.day_master, natal_branches, d.year, d.month, d.day)
        except Exception:
            continue
        stem_elem = L.STEM_INFO.get(hit.stem, {}).get("element", "")
        if stem_elem not in fav_elems:
            continue
        if _candidate_day_conflicts(hit.branch, watch_branches):
            continue
        tengod_note = hit.stem_tengod_en or hit.stem_tengod
        selected.append((d, hit.combined, tengod_note, stem_elem))

    lines = [
        "## Auspicious Dates — Next 90 Days",
        "",
        f"> The next {window_days}-day window from {ref.strftime('%B %Y')} includes the following candidate dates — each one's day-stem element matches your favorable ({ctx.favorable}) or supporting ({ctx.supporting}) element, and its day-branch does not clash, harm, or break your natal day branch ({day_branch})"
        + (f" or hour branch ({hour_branch})" if hour_branch else "")
        + ". A qualified reader should still cross-check each date against the querent's specific question and local calendar before recommending it.",
        "",
        "> **Almanac caveat:** this is a chart-relative shortlist, not a finished 택일 (auspicious-date selection) — a full 택일 also weighs the day's own 건제십이신/28수 almanac assignment, the specific event type, and local custom, none of which this engine computes *(see knowledge/16-date-selection.md)*.",
        "",
        "| Date | Day Pillar | Suggested Use / Reader Note |",
        "|---|---|---|",
    ]
    if selected:
        for d, combo, tg, stem_elem in selected:
            role = "favorable" if stem_elem == ctx.favorable else "supporting"
            lines.append(
                f"| {d.strftime('%Y-%m-%d (%A)')} | {combo} ({tg}) | "
                f"A reasonable candidate — the day-stem carries your {role} element ({stem_elem}) and its "
                f"branch does not clash, harm, or break your natal day/hour branch; confirm against the "
                f"querent's specific question before booking. |"
            )
    else:
        lines.append(
            f"| — | — | No day in this {window_days}-day window has a favorable-element, "
            "non-conflicting day-stem; widen the window or use the Monthly Lucky Dates table instead. |"
        )
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


def _candidate_day_conflicts(candidate_branch: str, watch_branches: List[str]) -> List[str]:
    """Return relation labels ("충"/"해"/"파") the candidate day's branch has
    against any of `watch_branches` (the natal day AND hour branches).

    Bug found 2026-09-20 (external report review, 3rd pass, R7): the
    auspicious/lucky-date filters only ever checked 충 (clash) against the
    natal DAY branch. knowledge/16-date-selection also requires avoiding
    days that repeat 해 (harm) or 파 (break) against the day *or hour*
    branch "when a cleaner day exists" — confirmed live: candidate days
    whose branch is 寅 (파 against Harish's natal 亥 day branch) or 申 (해
    against 亥) were passing the old clash-only filter untouched.
    """
    hits: List[str] = []
    for wb in watch_branches:
        pair = {candidate_branch, wb}
        if any(pair == {a, c} for a, c in L.SIX_CLASHES):
            hits.append("충")
        if any(pair == {a, c} for a, c in L.SIX_HARMS):
            hits.append("해")
        if any(pair == {a, c} for a, c in L.SIX_BREAKS):
            hits.append("파")
    return hits


def _section_monthly_lucky_dates(ctx: _ReportContext, months_ahead: int = 3, max_per_month: Optional[int] = None) -> List[str]:
    """Generate Monthly Lucky Dates for the Deep tier using daily-luck overlays.

    2026-09-20 fix (external report review, 3rd pass, R7): this used to
    silently cap each month at 5 dates and only check 충 (clash) against the
    day branch. knowledge/16 gives no basis for the cap (typical qualifying
    counts run ~10-12/month) and also requires checking 해/파 against the
    day OR hour branch — both fixed the same way as `_section_auspicious_dates`.
    """
    ref = ctx.chart.reference_date_obj() or datetime.now().date()
    lines = [
        "## Monthly Lucky Dates",
        "",
        f"The next **{months_ahead} months** of favorable days, selected when the daily stem element matches your **{ctx.favorable}** or **{ctx.supporting}** element and the day branch does not clash, harm, or break your natal day or hour branch.",
        "",
        "> _Methodology: each row filters the daily-luck (일운) stems to those whose element matches your favorable or supporting element, then drops any day whose branch clashes, harms, or breaks against your natal day or hour branch._",
        "",
        "> **Almanac caveat:** this is a chart-relative shortlist, not a finished 택일 — a full 택일 also weighs the day's own almanac assignment, the specific event type, and local custom *(see knowledge/16-date-selection.md)*.",
        "",
        "| Month | Favorable Dates | Energy Note |",
        "|---|---|---|",
    ]

    fav_elems = {ctx.favorable}
    if ctx.supporting and ctx.supporting != ctx.favorable:
        fav_elems.add(ctx.supporting)
    day_branch = ctx.chart.day.branch
    hour_branch = ctx.chart.hour.branch if ctx.chart.hour else None
    watch_branches = [b for b in (day_branch, hour_branch) if b]
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
        # Walk through each day of the month. For the CURRENT month
        # (month_offset == 0), start at ref.day + 1, not day 1 — a date
        # already in the past when the report was generated is not a usable
        # suggestion. Bug found 2026-09-19 (external report review, 2nd
        # pass): this used to always start at day 1, so a report generated
        # mid-month listed already-elapsed dates for its own current month
        # (confirmed live: a report generated Sept 19/20 listing "3, 5, 6,
        # 13, 14" for September).
        _, last_day = calendar.monthrange(year, month)
        first_day = ref.day + 1 if month_offset == 0 else 1
        selected: List[Tuple[int, str, str]] = []
        for day in range(first_day, last_day + 1):
            try:
                hit = SE.derive_ilwoon(ctx.chart.day_master, natal_branches, year, month, day)
            except Exception:
                continue
            stem_elem = L.STEM_INFO.get(hit.stem, {}).get("element", "")
            if stem_elem not in fav_elems:
                continue
            if _candidate_day_conflicts(hit.branch, watch_branches):
                continue
            tengod_note = hit.stem_tengod_en or hit.stem_tengod
            selected.append((day, hit.combined, tengod_note))
            if max_per_month is not None and len(selected) >= max_per_month:
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
