"""Engine-driven markdown skeleton for a Saju reading.

Produces a structured report shell that a human or AI can complete with
interpretive prose. The skeleton removes repetitive transcription work:
four-pillar table, ten-god distribution, branch relationships, stars,
strength heuristic, grid candidates, current major-luck / annual-luck /
monthly-luck windows.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

from .chart import Chart, Pillar
from .plain_glossary import collect_used_terms, gloss_first_use, render_terms_section
from .prose_scaffold import generate_plain_words, generate_prose_scaffold
from .stars import star_label


_POSITION_LABEL = {
    "year": "Year (년주)",
    "month": "Month (월주)",
    "day": "Day (일주)",
    "hour": "Hour (시주)",
}


def _hidden_str(p: Pillar) -> str:
    parts = [f"{role} {stem}" for role, stem in p.hidden_stems]
    return ", ".join(parts) if parts else "—"


def _ten_god_grouped(chart: Chart) -> str:
    """Return a Ten-God distribution table."""
    groups = {}
    for hit in chart.ten_gods:
        groups.setdefault(hit.tengod, []).append(hit.position)
    lines = ["| Class | Positions |", "|-------|-----------|"]
    for tg in ["비견", "겁재", "식신", "상관", "편재", "정재", "편관", "정관", "편인", "정인"]:
        if tg in groups:
            lines.append(f"| {tg} | {', '.join(groups[tg])} |")
    return "\n".join(lines)


def _stars_str(chart: Chart) -> str:
    lines = []
    for k, v in chart.stars.items():
        if v:
            lines.append(f"- **{star_label(k)}**: {', '.join(v)}")
    return "\n".join(lines) if lines else "_No classical stars matched. Signatures may still be present via branch relationships._"


def _daeun_str(chart: Chart) -> str:
    lines = [
        "| Age | Pillar | Ten-God | Activations | Favorability |",
        "|-----|--------|---------|-------------|--------------|",
    ]
    for p in chart.daeun:
        # Deduplicate branch activations by relationship type, showing count.
        branch_counts = Counter((a, n, r) for a, n, r in p.activated_branches)
        act_parts = []
        for (a, n, r), count in branch_counts.items():
            part = f"{a}{n} ({r})"
            if count > 1:
                part += f" ×{count}"
            act_parts.append(part)
        acts = ", ".join(act_parts) or "—"

        # Deduplicate stem combinations by element and target stem.
        combo_counts = Counter(
            (c["stem_a"], c["stem_b"], c["combined_element"]) for c in p.stem_combinations
        )
        if combo_counts:
            combo_parts = []
            for (sa, sb, elem), count in combo_counts.items():
                part = f"{sa}{sb}→{elem}"
                if count > 1:
                    part += f" ×{count}"
                combo_parts.append(part)
            combos = ", ".join(combo_parts)
            acts = f"{acts}; 천간합: {combos}" if acts != "—" else f"천간합: {combos}"

        fav = p.favorable_status or "—"
        lines.append(
            f"| {p.start_age}-{p.end_age} | {p.combined} | {p.stem_tengod} | {acts} | {fav} |"
        )
    return "\n".join(lines)


def _patterns_str(chart: Chart) -> str:
    p = chart.patterns or {}
    parts = []

    regular = p.get("regular_grid", [])
    if regular:
        parts.append("**Regular grids (정격)**:")
        for g in regular:
            parts.append(f"- {g.name_ko} / {g.name_en} — {g.basis} ({g.confidence})")

    if p.get("yangin", {}).get("present"):
        parts.append(f"**양인 (Blade Star)**: {p['yangin']['blade_branch']} at positions {p['yangin']['positions']} — {p['yangin']['note']}")
    if p.get("yangin_grid", {}).get("present"):
        parts.append(f"**양인격 (Blade Grid)**: {p['yangin_grid']['blade_branch']} month branch — {p['yangin_grid']['note']}")
    if p.get("yangin_non_month", {}).get("present"):
        parts.append(
            f"**Non-month 양인 (Blade outside the month)**: {p['yangin_non_month']['blade_branch']} at positions "
            f"{p['yangin_non_month']['positions']} — {p['yangin_non_month']['note']}"
        )

    if p.get("jianlu", {}).get("present"):
        parts.append(f"**건록격 (Established Salary Grid)**: {p['jianlu']['jianlu_branch']} month branch — {p['jianlu']['note']}")
    if p.get("jianlu_non_month", {}).get("present"):
        parts.append(
            f"**Non-month 건록 (Salary branch outside the month)**: {p['jianlu_non_month']['jianlu_branch']} at positions "
            f"{p['jianlu_non_month']['positions']} — {p['jianlu_non_month']['note']}"
        )

    combos = p.get("stem_combinations", [])
    if combos:
        parts.append("**천간합 (Ten-Stem Combinations)**:")
        for c in combos:
            season = "in season" if c["in_season"] else "not in season"
            broken = "breaker present" if c["breaker_present"] else "no breaker"
            parts.append(
                f"- {c['stem_a']}{c['stem_b']} → {c['korean_name']} ({c['combined_element']}, "
                f"{season}, {broken}, {c['confidence']})"
            )

    trans = p.get("transformation_grid")
    if trans:
        parts.append(
            f"**화격 (Transformation Grid) candidate**: {trans['basis']} → "
            f"{trans['combined_element']} ({trans['confidence']}) — {trans['note']}"
        )

    special = p.get("special_forms", [])
    if special:
        parts.append("**종격 (Follower-Grid) candidates**:")
        for s in special:
            parts.append(f"- {s['name_ko']} / {s['name_en']} — {s['basis']} ({s['confidence']})")
            parts.append(f"  - {s['note']}")

    return "\n\n".join(parts) if parts else "_No structural grid candidates flagged by the engine._"


def _sewoon_str(hits: List) -> str:
    lines = ["| Year | Pillar | Annual Ten-God | Activations |", "|------|--------|----------------|-------------|"]
    for h in hits:
        acts = ", ".join(f"{a}{n} ({r})" for a, n, r in h.activated_branches) or "—"
        lines.append(f"| {h.year} | {h.combined} | {h.stem_tengod} | {acts} |")
    return "\n".join(lines)


def _woon_str(hits: List) -> str:
    lines = ["| Month | Pillar | Monthly Ten-God | Activations |", "|-------|--------|-----------------|-------------|"]
    for h in hits:
        yyyymm = h.year  # overloaded to YYYYMM
        acts = ", ".join(f"{a}{n} ({r})" for a, n, r in h.activated_branches) or "—"
        lines.append(f"| {yyyymm//100}-{yyyymm%100:02d} | {h.combined} | {h.stem_tengod} | {acts} |")
    return "\n".join(lines)


def _ilwoon_str(hits: List) -> str:
    lines = ["| Date | Pillar | Daily Ten-God | Activations |", "|------|--------|---------------|-------------|"]
    for h in hits:
        yyyymmdd = h.year  # overloaded to YYYYMMDD
        acts = ", ".join(f"{a}{n} ({r})" for a, n, r in h.activated_branches) or "—"
        lines.append(
            f"| {yyyymmdd//10000}-{(yyyymmdd//100)%100:02d}-{yyyymmdd%100:02d} | "
            f"{h.combined} | {h.stem_tengod} | {acts} |"
        )
    return "\n".join(lines)


def _branch_rels_str(chart: Chart) -> str:
    parts = []
    if chart.combinations_6:
        parts.append("**六合 / 三合**: " + ", ".join(f"{a}{b}({elem})" for a, b, elem, _, _ in chart.combinations_6))
    if chart.clashes:
        parts.append("**六沖**: " + ", ".join(f"{a}{b}" for a, b in chart.clashes))
    if chart.six_harms:
        parts.append("**六害**: " + ", ".join(f"{a}{b}" for a, b in chart.six_harms))
    if chart.six_breaks:
        parts.append("**六破**: " + ", ".join(f"{a}{b}" for a, b in chart.six_breaks))
    if chart.self_punishments:
        parts.append("**自刑**: " + ", ".join(f"{a}{b}" for a, b in chart.self_punishments))
    if chart.three_harmonies:
        parts.append("**三合**: " + ", ".join(f"{a}{b}{c}({elem})" for a, b, c, elem in chart.three_harmonies))
    if chart.three_punishments:
        parts.append("**三刑**: " + ", ".join(f"{a}{b}{c}" if c != "—" else f"{a}{b}" for a, b, c, _ in chart.three_punishments))
    return "\n\n".join(parts) if parts else "_No natal branch relationships detected._"


def generate_skeleton(
    chart: Chart,
    focus: Optional[str] = None,
    reference_year: Optional[int] = None,
    reference_month: Optional[int] = None,
    reference_day: Optional[int] = None,
    include_prose_scaffold: bool = True,
) -> str:
    """Return a markdown skeleton for the chart.

    If `reference_year` is provided, the skeleton includes a 5-year annual-luck
    window centered on that year. Otherwise it uses the current Gregorian year.
    If `reference_month` is provided, a monthly-luck window centered on that
    month is also rendered. If `reference_day` is provided, a daily-luck
    window centered on that day is also rendered.

    When `include_prose_scaffold=True` (default), the skeleton includes
    engine-drafted paragraphs for each interpretive section. These are marked
    as drafts and must be reviewed by the reader.
    """
    # Ensure the chart has the latest overlays; if called on a fresh chart they
    # are already populated by compute_chart(). Prefer the chart's own reference
    # date; fall back to today only when called outside the normal pipeline.
    ref = chart.reference_date_obj() or datetime.now().date()
    if reference_year is None:
        reference_year = ref.year
    if reference_month is None:
        reference_month = ref.month
    if reference_day is None:
        reference_day = ref.day

    lines = [
        "# Saju Reading Skeleton (사주 감정 골격)",
        "",
        "> ⚠️ This file is an **engine-generated skeleton**. Interpretive prose must be",
        "> added by a qualified reader following `knowledge/09-interpretation-method.md`.",
        "",
        "## Birth Information",
        "",
        f"- **Name**: {chart.name or '—'}",
        f"- **Gender**: {chart.gender or '—'}",
        f"- **Birth date/time**: {chart.birth_date} {chart.birth_time}",
        f"- **Location**: {chart.city or '—'} (lon={chart.longitude or '—'})",
        f"- **Zi-hour convention**: {chart.convention}",
        "",
        "## Four Pillars",
        "",
        "| Pillar | Stem | Branch | Hidden Stems | 12운성 |",
        "|--------|------|--------|--------------|--------|",
    ]

    stage_map = {pos: stage for pos, _, stage in chart.twelve_stages}
    for p in chart.pillars:
        lines.append(
            f"| {_POSITION_LABEL[p.position]} | {p.stem} | {p.branch} | {_hidden_str(p)} | {stage_map.get(p.position, '—')} |"
        )

    lines += [
        "",
        f"## Day Master (일간): {chart.day_master}",
        "",
        f"Element: {chart.day_master_info.get('element')} ({chart.day_master_info.get('polarity')})",
        "",
        "### Strength heuristic",
        "",
    ]

    if chart.strength_assessment:
        sa = chart.strength_assessment
        rounded_counts = {k: round(v, 1) for k, v in sa["element_counts"].items()}
        lines += [
            f"- **Verdict**: {sa['verdict']}",
            f"- **Candidate 용신**: {sa['candidate_favorable']}",
            f"- **Candidate 희신**: {sa['candidate_supporting']}",
            f"- **Candidate 기신**: {sa.get('candidate_unfavorable') or '—'}",
            f"- **Total score**: {round(sa['total_score'], 2)}",
            f"- **Element counts**: {rounded_counts}",
            f"- **Note**: {sa['note']}",
        ]
    else:
        lines.append("_Strength assessment not available._")

    lines += [
        "",
        "### Ten-God Distribution",
        "",
        _ten_god_grouped(chart),
        "",
        "## Branch Relationships",
        "",
        _branch_rels_str(chart),
        "",
        "## Grid / Pattern Candidates (격국 후보)",
        "",
        _patterns_str(chart),
        "",
        "## Stars",
        "",
        _stars_str(chart),
        "",
        "## Major Luck Periods (대운)",
        "",
        _daeun_str(chart),
        "",
        f"## Annual-Luck Window ({reference_year-2}–{reference_year+2})",
        "",
        _sewoon_str(chart.sewoon),
        "",
        f"### Focus year: {reference_year}",
        "",
        "_(interpret the annual pillar and its natal activations here)_",
        "<!-- Use `sewoon.derive_sewoon()` or the `--year` CLI flag to populate. -->",
        "",
        f"## Monthly-Luck Window ({reference_year}-{reference_month:02d} ± 2 months)",
        "",
        _woon_str(chart.woon),
        "",
        f"## Daily-Luck Window ({reference_year}-{reference_month:02d}-{reference_day:02d} ± 2 days)",
        "",
        _ilwoon_str(chart.ilwoon),
        "",
        "## Interpretive Sections",
        "",
    ]

    if include_prose_scaffold:
        lines += [
            "> ⚠️ The paragraphs below are **engine-drafted scaffolds**. They pull facts from the computed chart but are **not a finished reading**. The reader must verify, refine, and add the classical reasoning and citations from `knowledge/`.",
            "",
        ]
        scaffold: Dict[str, str] = generate_prose_scaffold(chart)
        pw: Dict[str, str] = generate_plain_words(chart)

        def _sec(title: str, body: str, plain_key: str = "") -> List[str]:
            block = [title, "", body, ""]
            if plain_key and pw.get(plain_key):
                block += [pw[plain_key], ""]
            return block

        lines += _sec("### 1. Day Master Strength Reasoning (draft)", scaffold["day_master_strength"])
        lines += _sec("### 2. Favorable Element (용신) & Reasoning (draft)", scaffold["yongsin"])
        lines += _sec("### 3. Personality (draft)", scaffold["personality"], "personality")
        lines += _sec("### 4. Career / Wealth (draft)", scaffold["career_wealth"], "career_wealth")
        lines += _sec("### 5. Relationships (draft)", scaffold["relationships"], "relationships")
        lines += _sec("### 6. Health Tendencies (draft)", scaffold["health"], "health")
        lines += _sec("### 7. Current Time-Based Themes (draft)", scaffold["current_time_themes"], "current_time_themes")
    else:
        lines += [
            "### 1. Day Master Strength Reasoning",
            "",
            "_(argue from season, hidden stems, 인성/비겁/관재/식상 balance)_",
            "",
            "### 2. Favorable Element (용신) & Reasoning",
            "",
            "_(state 용신 and 희신; explain why it balances the chart)_",
            "",
            "### 3. Personality",
            "",
            "_(2–4 sentences based on Day Master + dominant ten-god classes)_",
            "",
            "### 4. Career / Wealth",
            "",
            "_(관성/식상/재성 balance; best fields by Day Master element and 용신)_",
            "",
            "### 5. Relationships",
            "",
            "_(spouse palace analysis; 도화살; compatibility pattern)_",
            "",
            "### 6. Health Tendencies",
            "",
            "_(not a diagnosis; element balance / organ mapping)_",
            "",
            "### 7. Current Time-Based Themes",
            "",
            "_(current 대운 + annual 세운; natal activations)_",
            "",
        ]

    lines += [
        "## Sources & Limits",
        "",
        "- Engine output from `tools/saju_engine/`.",
        "- Interpretive framework from `knowledge/09-interpretation-method.md`.",
        "- This reading describes tendencies, not fixed outcomes.",
    ]

    if focus:
        lines += [
            "",
            f"## Focus Requested by Querent: {focus}",
            "",
            "_(answer the specific question here, integrating the data above)_",
        ]

    doc = "\n".join(lines)
    # Plain-language layer: gloss jargon on first prose use, then a full glossary.
    doc = gloss_first_use(doc, set())
    terms = render_terms_section(collect_used_terms(doc), "skeleton")
    if terms:
        doc = doc.rstrip() + "\n\n" + terms
    return doc
