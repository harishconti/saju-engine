"""Engine-driven interpretive prose scaffold.

Produces *draft* paragraphs for each section of `knowledge/10-output-template.md`
from computed chart data. The output is explicitly marked as an engine-aided
first draft that the reader must review and refine.

This module does **not** replace the reader; it removes repetitive setup so the
human/AI interpreter can spend tokens on synthesis and nuance rather than on
deriving obvious sentences from the tables.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Tuple

from .chart import Chart
from . import lookup as L
from . import daeun as DAEUN


from .hanja_glossary import inject_hanja
from .stem_profiles import stem_profile

# Element → organ mapping — source: knowledge/15-health-and-body.md § 오행 → Organ Systems
_ELEMENT_ORGANS: Dict[str, str] = {
    "Wood": "liver/gallbladder (간/담)",
    "Fire": "heart/small intestine (심/소장)",
    "Earth": "spleen/stomach (비/위)",
    "Metal": "lungs/large intestine (폐/대장)",
    "Water": "kidneys/bladder (신/방광)",
}


# Ten-god class names
_TENGOD_CLASS: Dict[str, str] = {
    "비견": "Companion", "겁재": "Companion",
    "식신": "Output", "상관": "Output",
    "편재": "Wealth", "정재": "Wealth",
    "편관": "Authority", "정관": "Authority",
    "편인": "Resource", "정인": "Resource",
}


def _class_counts(chart: Chart) -> Counter:
    """Count ten-god classes across all visible and hidden stems."""
    counts: Counter = Counter()
    for hit in chart.ten_gods:
        cls = _TENGOD_CLASS.get(hit.tengod)
        if cls:
            counts[cls] += 1
    return counts


def _dominant_classes(chart: Chart, n: int = 2) -> List[Tuple[str, int]]:
    """Return the n most common ten-god classes."""
    return _class_counts(chart).most_common(n)


def _element_balance(chart: Chart) -> Counter:
    """Return canonical weighted element counts from the strength helper."""
    from . import strength as S

    return S.element_balance_counts(chart)


def _strength_draft(chart: Chart) -> str:
    """Draft paragraph for Day Master strength reasoning."""
    dm = chart.day_master
    dm_info = chart.day_master_info
    month = chart.month
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    candidate_fav = sa.get("candidate_favorable", "—")
    month_stage = sa.get("month_stage", "—")

    season_map = {
        "寅": "early Wood", "卯": "peak Wood", "辰": "late Wood/Earth",
        "巳": "early Fire", "午": "peak Fire", "未": "late Fire/Earth",
        "申": "early Metal", "酉": "peak Metal", "戌": "late Metal/Earth",
        "亥": "early Water", "子": "peak Water", "丑": "late Water/Earth",
    }
    season = season_map.get(month.branch, "transitional")

    element = dm_info.get("element", "")
    dm_season = {
        "Wood": "Spring", "Fire": "Summer", "Earth": "Late summer",
        "Metal": "Autumn", "Water": "Winter",
    }.get(element, "—")
    in_season = (
        (element == "Wood" and month.branch in "寅卯辰")
        or (element == "Fire" and month.branch in "巳午未")
        or (element == "Earth" and month.branch in "辰戌丑未")
        or (element == "Metal" and month.branch in "申酉戌")
        or (element == "Water" and month.branch in "亥子丑")
    )

    parts = [
        f"Day Master **{dm}** is {dm_info.get('polarity')} {element}.",
        f"Born in the **{month.branch}** month ({season}), the Day Master's 12운성 stage there is **{month_stage}**.",
    ]
    if in_season:
        parts.append(f"The month branch is in the Day Master's season of peak ({dm_season}), which generally supports the self.")
    else:
        parts.append(f"The month branch is outside the Day Master's season of peak ({dm_season}), so seasonal support is muted.")

    parts.append(
        f"The engine's heuristic places the chart toward **{verdict}**, with a candidate 용신 of **{candidate_fav}**. "
        "The final ruling must still consider hidden-stem support, 합/충, and any special-grid candidate."
    )
    return " ".join(parts)


def _yongsin_draft(chart: Chart) -> str:
    """Draft paragraph for 용신/희신 reasoning."""
    sa = chart.strength_assessment or {}
    fav = sa.get("candidate_favorable", "—")
    sup = sa.get("candidate_supporting", "—")
    unfav = sa.get("candidate_unfavorable") or "—"
    verdict = sa.get("verdict", "balanced")

    if verdict in ("strong", "extreme"):
        logic = (
            f"Because the Day Master reads as {verdict}, the chart has surplus self-energy. "
            f"The most useful element is one that drains or structures that energy: **{fav}** (용신), "
            f"with **{sup}** as 희신. **{unfav}** is the element most likely to amplify the imbalance."
        )
    elif verdict == "weak":
        logic = (
            f"Because the Day Master reads as {verdict}, the chart needs support. "
            f"**{fav}** (용신) strengthens or feeds the self, while **{sup}** (희신) reinforces it. "
            f"**{unfav}** is the element most likely to further deplete the self."
        )
    else:
        logic = (
            f"The heuristic reads the chart as {verdict}. "
            f"The engine suggests cultivating **{fav}** (용신) because it is the most under-represented element, "
            f"with **{sup}** as 희신; this should be argued from the full chart context rather than accepted blindly."
        )
    # E-3/E-5 (2026-09-26): the paragraph above narrates the raw 억부
    # heuristic. When the single resolution (climate/reader-aware) lands on a
    # different set, say so, so the draft never contradicts the report.
    from .yongsin import favorable_element
    fe = favorable_element(chart)
    if (fe.element, fe.supporting, fe.unfavorable) != (fav, sup, sa.get("candidate_unfavorable")):
        logic += (
            f" After the climate (조후) and reader-override resolution the chart's working set is "
            f"용신 **{fe.element}**, 희신 **{fe.supporting}**, 기신 **{fe.unfavorable or '—'}** — "
            f"use these in the reading."
        )
    return logic


def _personality_draft(chart: Chart) -> str:
    """Draft paragraph for personality."""
    dm = chart.day_master
    profile = stem_profile(dm)
    dominant = _dominant_classes(chart, 2)
    dom_names = [f"{cls} ({count})" for cls, count in dominant]

    base = (
        f"With **{dm}** ({chart.day_master_info.get('element')}, {chart.day_master_info.get('polarity')}) as the Day Master, "
        f"the self carries the image of the **{profile.get('image', 'stem')}**: "
        f"{profile.get('strengths', 'strengths')} are natural strengths, while "
        f"{profile.get('weaknesses', 'weaknesses')} may need attention."
    )
    if dom_names:
        base += (
            f" The chart's dominant ten-god classes are **{dom_names[0]}** and **{dom_names[1] if len(dom_names) > 1 else '—'}**, "
            "shaping how this self expresses in relationships, work, and stress."
        )
    return base


def _career_draft(chart: Chart) -> str:
    """Draft paragraph for career / wealth tendencies."""
    cls_counts = _class_counts(chart)
    authority = cls_counts.get("Authority", 0)
    wealth = cls_counts.get("Wealth", 0)
    output = cls_counts.get("Output", 0)
    from .yongsin import favorable_element
    fav = favorable_element(chart).element

    parts = [
        f"The ten-god mix shows {authority} Authority (관성), {wealth} Wealth (재성), and {output} Output (식상) occurrences."
    ]
    if authority >= 2:
        parts.append("A noticeable 관성 presence points toward structure, status, and conventional accomplishment.")
    if wealth >= 2:
        parts.append("Multiple Wealth stars suggest money and resources are a central life theme.")
    if output >= 2:
        parts.append("Strong Output favors creative, expressive, or teaching paths where the self produces something visible.")
    parts.append(
        f"Fields aligned with the favorable element **{fav}** and the Day Master's {chart.day_master_info.get('element')} nature are generally supportive. "
        "The reader should weigh whether the Day Master is strong enough to hold wealth and authority, or whether it needs resource/peer support first."
    )
    return " ".join(parts)


def _relationships_draft(chart: Chart) -> str:
    """Draft paragraph for relationships."""
    spouse_branch = chart.day.branch
    spouse_tengods = [hit.tengod for hit in chart.ten_gods if hit.position == "day_branch_main"]
    spouse_tg = spouse_tengods[0] if spouse_tengods else "—"
    peach = chart.stars.get("peach_blossom", [])

    base = (
        f"The spouse palace is the day branch **{spouse_branch}**, whose main hidden stem relates to the Day Master as **{spouse_tg}**. "
    )
    if peach:
        base += f"**도화 (Peach Blossom)** is present at **{', '.join(peach)}**, adding charm and relational magnetism. "
    else:
        base += "No **도화** star is natally active; relationship style is more shaped by the spouse palace and ten-god mix than by overt magnetism. "

    if chart.combinations_6 or chart.three_harmonies:
        base += "Natal branch combinations suggest an attraction to harmony and partnership. "
    if chart.clashes:
        base += "Natal clashes indicate that relationships may also bring sudden change or tension. "
    return base


def _health_draft(chart: Chart) -> str:
    """Draft paragraph for health tendencies (non-diagnostic)."""
    counts = _element_balance(chart)
    if not counts:
        return "Element balance could not be determined."
    most = counts.most_common(1)[0]
    least = counts.most_common()[-1]
    parts = [
        "This is a classical tendency reading, not a medical diagnosis.",
        f"The chart's weighted element counts show **{most[0]}** as the most present element and **{least[0]}** as the least present.",
        f"Excess **{most[0]}** may stress the {_ELEMENT_ORGANS.get(most[0], 'associated')} system; deficiency of **{least[0]}** may leave the {_ELEMENT_ORGANS.get(least[0], 'associated')} system under-supported.",
        "For any health concern, consult a licensed medical professional."
    ]
    return " ".join(parts)


def _current_time_draft(chart: Chart) -> str:
    """Draft paragraph for current time-based themes."""
    ref = chart.reference_date_obj()
    ref_year = ref.year if ref else None
    ref_month = ref.month if ref else None
    current_sewoon = next((h for h in chart.sewoon if h.year == ref_year), None) if ref_year else None
    current_woon = next(
        (h for h in chart.woon if ref and h.year == ref.year * 100 + ref.month), None
    )

    parts = []
    if ref_year:
        parts.append(
            f"As of {ref_year}, the annual pillar is **{current_sewoon.combined if current_sewoon else '—'}** "
            f"({current_sewoon.stem_tengod if current_sewoon else '—'} ten-god)."
        )
    if current_sewoon and current_sewoon.relationship_types:
        parts.append(
            f"It activates the natal chart through: {', '.join(current_sewoon.relationship_types)}."
        )
    if current_woon:
        parts.append(
            f"The current monthly pillar is **{current_woon.combined}** ({current_woon.stem_tengod}), "
            f"with activations: {', '.join(current_woon.relationship_types) or 'none'}."
        )

    # Use the chart-level current major-luck period (already computed by
    # `engine.compute_chart` from the querier's reference date).
    current_daeun = chart.current_daeun
    if current_daeun:
        parts.append(
            f"The current major-luck period (ages {current_daeun.start_age}-{current_daeun.end_age}) is **{current_daeun.combined}** "
            f"({current_daeun.stem_tengod}), favorability **{current_daeun.favorable_status or '—'}**."
        )

    return " ".join(parts) if parts else "No reference date available; add a reference date to enable current timing themes."


def generate_prose_scaffold(chart: Chart) -> Dict[str, str]:
    """Return a dictionary of draft paragraphs for each template section.

    Each value is a single-paragraph draft. The caller is expected to review,
    refine, and cite the appropriate knowledge files; these are not final
    readings. Korean technical terms are annotated with Hanja on first use
    per CLAUDE.md.
    """
    drafts = {
        "day_master_strength": _strength_draft(chart),
        "yongsin": _yongsin_draft(chart),
        "personality": _personality_draft(chart),
        "career_wealth": _career_draft(chart),
        "relationships": _relationships_draft(chart),
        "health": _health_draft(chart),
        "current_time_themes": _current_time_draft(chart),
    }
    used: set = set()
    return {k: inject_hanja(v, used) for k, v in drafts.items()}


_VERDICT_PLAIN_LABEL = {
    "strong": "strong",
    "extreme_strong": "very strong",
    "weak": "on the weaker side",
    "extreme_weak": "quite weak",
    "balanced": "balanced",
}


def generate_plain_words(chart: Chart) -> Dict[str, str]:
    """Return one-line 'In plain words' callouts for the scaffold sections.

    Keys: personality, career_wealth, relationships, health,
    current_time_themes. Each value is a ``"> **In plain words:** …"`` line or
    ``""``. Mirrors ``premium_report``'s plain-language layer so the skeleton
    and the client report read the same way.
    """
    from . import prose_fillers as PF

    from .yongsin import favorable_element

    sa = chart.strength_assessment or {}
    fe = favorable_element(chart)
    ctx = {
        "chart": chart,
        "dm_element": chart.day_master_info.get("element", ""),
        "favorable": fe.element,
        "supporting": fe.supporting,
        "unfavorable": fe.unfavorable or "",
        "strength_label": _VERDICT_PLAIN_LABEL.get(sa.get("verdict", ""), ""),
        "current_daeun": chart.current_daeun,
        "pattern_name": "",
    }
    return {
        "personality": PF.plain_words_day_master(ctx),
        "career_wealth": PF.plain_words_career(ctx),
        "relationships": PF.plain_words_relationships(ctx),
        "health": PF.plain_words_health(ctx),
        "current_time_themes": PF.plain_words_timing(ctx),
    }
