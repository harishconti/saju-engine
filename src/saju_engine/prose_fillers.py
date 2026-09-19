"""Chart-derived prose fillers for the premium report placeholders.

Each filler takes a `Chart` plus a context dictionary (the `_ReportContext`
fields used by `premium_report.py`) and returns a `str` of prose grounded in
real chart data: Day Master element, ten-god counts, element balance, 대운
favorability, branch relationships, classical stars, etc.

These fillers replace the previous `[ENGINE DRAFT — REVIEW REQUIRED]`
*prompts*. The output is still marked for human review (the marker is preserved
in the engine markdown but stripped at the PDF layer by `strip_engine_drafts`).

All prose is **deterministic** (same chart → same prose) and avoids templated
language. The fillers are intentionally conservative: each sentence is
defensible from chart data and references the specific chart feature it
speaks to.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .report_data import _PILLAR_AREAS


# ── Ten-god class names (English) ────────────────────────────────────────
_TENGOD_CLASS: Dict[str, str] = {
    "비견": "Companion", "겁재": "Robber",
    "식신": "Output", "상관": "Output",
    "편재": "Indirect Wealth", "정재": "Direct Wealth",
    "편관": "Seven Killings", "정관": "Direct Officer",
    "편인": "Indirect Resource", "정인": "Direct Resource",
}

# The five broad 십신 classes (비겁/식상/재성/관성/인성), keyed by the KOREAN
# ten-god code — not the English gloss. Use this, never a substring check on
# an English label, to classify a ten-god by class.
#
# Bug found 2026-09-19 (external report review): major_luck_theme_row and
# annual_window_row used to branch on substrings of the English gloss (e.g.
# `"Officer" in tg`), which silently misclassified 3 of the 10 ten-gods
# because their English names don't reliably contain their class name:
# 상관 ("Hurting Officer") wrongly matched the Authority branch via the word
# "Officer" even though 상관 is 식상 (Output); 식신 ("Eating God") and 편관
# ("Seven Killings") matched no keyword at all and silently fell through to
# the Companion/peer branch even though they are Output and Authority
# respectively. Confirmed live in Harish's report: 2027 (丁未, Seven Killings)
# and the 10-19 major-luck decade both showed "peer-driven" text instead of
# authority-pressure text; 2032 (壬子, Hurting Officer) and the 60-69 decade
# both showed "structured career moves" (Authority text) instead of
# Output-class text.
_TENGOD_FIVE_CLASS: Dict[str, str] = {
    "비견": "Companion", "겁재": "Companion",
    "식신": "Output", "상관": "Output",
    "편재": "Wealth", "정재": "Wealth",
    "편관": "Authority", "정관": "Authority",
    "편인": "Resource", "정인": "Resource",
}

# Element → organ mapping (used by health fillers)
# source: knowledge/15-health-and-body.md § 오행 → Organ Systems
_ELEMENT_ORGANS: Dict[str, str] = {
    "Wood": "liver/gall bladder and nervous system",
    "Fire": "heart/small intestine and circulation",
    "Metal": "lung/large intestine and respiratory/immune boundaries",
    "Water": "kidney/bladder and hormonal/endocrine reserves",
    "Earth": "spleen/stomach and digestive metabolism",
}


def _ctx_get(ctx: Any, key: str, default: Any = None) -> Any:
    """Read a field from either a `_ReportContext` object or a plain dict."""
    if isinstance(ctx, dict):
        return ctx.get(key, default)
    return getattr(ctx, key, default)


def _plain(text: str) -> str:
    """Wrap a lay restatement as a single-line 'In plain words' blockquote."""
    return f"> **In plain words:** {text}"


def period_favorable_status(period: Any, ctx: Any) -> str:
    """Return a 대운 period's favorable/neutral/unfavorable lean vs. THIS
    report's final resolved favorable element (``ctx.favorable`` — which
    already accounts for a reader override), rather than trusting
    ``period.favorable_status`` directly.

    ``period.favorable_status`` is baked into the chart once, at
    compute_chart time (see ``daeun_overlay.py``), before any report-level
    ``favorable_override`` is known — so for an overridden chart (Gurumoorthy,
    Sruthi, Pawan) it can silently disagree with what the report's Quick
    Reference / Chart-at-a-Glance actually shows. Found 2026-09-19 alongside
    the climate-resolution fix in ``daeun_overlay.py`` (which fixed the
    non-override baseline but, without this render-time recomputation, would
    have newly exposed the override mismatch here). Every prose filler that
    narrates 대운/timing favorability should call this instead of reading
    ``period.favorable_status`` directly.
    """
    hits = {getattr(period, "stem_element", None), getattr(period, "branch_element", None)}
    favorable = _ctx_get(ctx, "favorable")
    unfavorable = _ctx_get(ctx, "unfavorable")
    if favorable in hits:
        return "favorable"
    if unfavorable and unfavorable in hits:
        return "unfavorable"
    return "neutral"


def _display_verdict(verdict: str) -> str:
    """Return a client-facing label for the strength verdict."""
    if verdict == "extreme_weak":
        return "Very Weak"
    return verdict.title()


def _class_counts(chart) -> Counter:
    """Count ten-god classes across all visible and hidden stems."""
    counts: Counter = Counter()
    for hit in chart.ten_gods:
        cls = _TENGOD_CLASS.get(hit.tengod)
        if cls:
            counts[cls] += 1
    return counts


def _dominant_classes(chart, n: int = 2) -> List[Tuple[str, int]]:
    return _class_counts(chart).most_common(n)


def _element_balance(chart) -> Counter:
    """Weighted element counts. Delegates to the canonical strength helper."""
    from . import strength as S

    return S.element_balance_counts(chart)


def _element_pct(chart) -> Dict[str, float]:
    """Return element percentage breakdown (sums to 100)."""
    from . import strength as S

    return S.element_balance_pct(chart)


# ── Day Master portrait enhancer ───────────────────────────────────────────

# 12운성 tendency labels (source: knowledge/06-twelve-stages.md)
_STAGE_TENDENCY: Dict[str, Tuple[str, str]] = {
    "장생": ("early momentum", "the chart tends to begin things with fresh, supported energy"),
    "목욕": ("exposed emergence", "early life may feel vivid and visible, with lessons learned through contact with others"),
    "관대": ("coming-of-age energy", "the querent grows into form gradually; adolescence and early adulthood often bring ambition"),
    "건록": ("steady prime", "the Day Master is already strong in the month branch, so competence arrives without much fanfare"),
    "제왕": ("peak self-presence", "the Day Master reaches maximum presence early; the challenge is not starting but learning to modulate intensity"),
    "쇠": ("post-peak adjustment", "the chart's first major chapter may ask for rest and recalibration before the next rise"),
    "병": ("recessive start", "early momentum is depleted; the querent often builds strength through recovery and patience"),
    "사": ("phase-ending start", "one cycle is completing as the querent enters the world, so early identity may feel transitional"),
    "묘": ("contained start", "energy is stored in the month branch; the chart ripens slowly and reveals depth over time"),
    "절": ("severed start", "the lowest point of the cycle touches the month branch — a clean-slate tendency rather than a deficit"),
    "태": ("gestational start", "new potential is forming; early life may feel preparatory rather than openly productive"),
    "양": ("nurtured start", "the chart is being held in incubation; support from others often matters more than self-propulsion"),
}


def dm_arrival_narrative(ctx) -> str:
    """2–3 sentences about how the Day Master 'arrives' in the month branch.

    Uses the Day Master's 12운성 stage in `chart.month_branch` plus a simple
    seasonal strength signal (see knowledge/06-twelve-stages.md). No fatalism:
    all phrasing is about tendency and rhythm.
    """
    chart = _ctx_get(ctx, "chart")
    from . import lookup as L
    stage = "—"
    try:
        stage = L.twelve_stage(chart.day_master, chart.month.branch)
    except Exception:
        pass
    label, description = _STAGE_TENDENCY.get(stage, ("mixed arrival", "the month branch gives a mixed first impression"))

    sa = chart.strength_assessment or {}
    month_stage = sa.get("month_stage", stage)
    # Use the engine's month-stage score as a second signal, if present.
    month_stage_score = sa.get("month_stage_score", 0.0)
    if month_stage_score >= 0.5:
        season_signal = "seasonally supported"
    elif month_stage_score <= -0.5:
        season_signal = "seasonally depleted"
    else:
        season_signal = "mixed seasonal support"

    return (
        f"Your Day Master **{chart.day_master}** meets the month branch **{chart.month.branch}** "
        f"at the **{stage} ({label})** twelve-stage — {description}. "
        f"This is read as a {season_signal} arrival: a tendency in how the querent's core energy "
        f"first enters the world, not a fixed early-life outcome."
    )


# ── Wealth & Career fillers ──────────────────────────────────────────────

def wealth_pattern(ctx) -> str:
    """Wealth Pattern paragraph (Essential/Deep)."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    sup = _ctx_get(ctx, "supporting", "—")
    unfav = _ctx_get(ctx, "unfavorable") or "the challenging element"
    cls = _class_counts(chart)
    wealth_n = cls.get("Direct Wealth", 0) + cls.get("Indirect Wealth", 0)
    if wealth_n >= 1:
        wealth_label = "재성 (Wealth) ten-gods are visible in the natal pillars, so earning capacity is rooted in the chart"
    else:
        wealth_label = (
            "no direct 재성 (Wealth) stem is visible, so wealth is more likely to flow "
            "through resource, output, or authority channels rather than a direct wealth stem"
        )
    return (
        f"Wealth timing is read from where 재성 (Wealth) ten-gods appear and are supported. "
        f"Your favorable element **{fav}** and supporting element **{sup}** describe the broader "
        f"climate that helps those wealth channels function; they are not the wealth channel itself. "
        f"{wealth_label}. Use the 대운 and 세운 tables to see when income and value-creation themes "
        f"surface most clearly. Periods dominated by **{unfav}** call for conservation rather than expansion."
    )


def wealth_preservation_short(ctx) -> str:
    """3-sentence Wealth Preservation Note for Essential tier."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    verdict_label = _display_verdict(verdict)
    return (
        f"For a **{dm_elem}** Day Master with a **{verdict_label}** reading, wealth preservation starts with "
        f"diversification — never concentrate more than your chart can comfortably hold. "
        f"Liquidity buffers aligned with the **{fav}** element (its colors, foods, and rhythms) help the "
        f"querent stay flexible across unfavorable 대운 periods. "
        f"Lean on **{fav}**-aligned custodians and instruments rather than chasing growth alone."
    )


def employment_vs_entrepreneurship(ctx) -> str:
    """Direct recommendation on solo vs structured work."""
    chart = _ctx_get(ctx, "chart")
    cls = _class_counts(chart)
    authority = cls.get("Direct Officer", 0) + cls.get("Seven Killings", 0)
    wealth = cls.get("Direct Wealth", 0) + cls.get("Indirect Wealth", 0)
    output = cls.get("Output", 0)
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    parts: List[str] = []
    if verdict in ("strong", "extreme") and (wealth >= 1 or output >= 1):
        parts.append(
            "The Day Master reads as **strong** with visible Output or Wealth stems, which favours "
            "independent paths once the querent has built enough foundation to hold the variability."
        )
    elif verdict in ("weak", "extreme_weak") and authority >= 2:
        parts.append(
            "The Day Master reads as **weaker** with a strong Authority presence, which favours "
            "structured employment early on — a clear hierarchy and a defined mentor accelerate growth."
        )
    elif authority >= 2 and wealth >= 1:
        parts.append(
            "A double pull between Authority and Wealth suggests a hybrid path: a credible institutional "
            "platform in the early career years, then a measured move toward independent ventures once "
            "credibility and capital are in place."
        )
    else:
        parts.append(
            "The Authority and Wealth pulls are present but balanced, so either path is workable — "
            "the deciding factor will be which environment the querent can sustain emotionally for a decade."
        )
    parts.append(
        "Treat this as a tendency reading, not a verdict; the 대운 and annual luck tables below show when "
        "each path is more likely to land cleanly."
    )
    return " ".join(parts)


def income_rhythm(ctx) -> str:
    """Sketch of whether income arrives steadily or in bursts."""
    chart = _ctx_get(ctx, "chart")
    cls = _class_counts(chart)
    direct_wealth = cls.get("Direct Wealth", 0)
    indirect_wealth = cls.get("Indirect Wealth", 0)
    direct = direct_wealth >= 1
    indirect = indirect_wealth >= 1 and direct_wealth == 0
    from . import lookup as L
    wealth_rooted = False
    for p in chart.pillars:
        if not p.hidden_stems:
            continue
        for role, stem in p.hidden_stems:
            if role in ("main", "middle"):
                try:
                    tg = L.ten_god(chart.day_master, stem)
                except Exception:
                    continue
                # NOT a substring check: "재" also occurs inside 겁재 (Robber,
                # a 비겁-class ten-god, not Wealth) — a substring match here
                # would wrongly treat a hidden 겁재 as wealth-rooting. Found
                # 2026-09-19 alongside the English-gloss substring bug in
                # major_luck_theme_row / annual_window_row.
                if tg in ("정재", "편재"):
                    wealth_rooted = True
                    break
        if wealth_rooted:
            break
    if direct and wealth_rooted:
        return (
            "Income tends to arrive in **steady increments** — a salaried baseline, retainer work, or "
            "recurring contracts. The Direct Wealth stem is rooted in a branch, so the source is durable "
            "and the rhythm is rarely interrupted by surprise windfalls."
        )
    if indirect:
        return (
            "Income arrives in **project-based bursts** — commissions, deals, or ventures that close in "
            "lumps rather than steady drip. Build cash reserves between projects so the slower months "
            "do not force reactive decisions."
        )
    return (
        "There is no direct wealth ten-god on a visible stem, so income may arrive through resource, "
        "output, or authority channels rather than a clean wealth stream — the reader should trace the "
        "money path through the hidden stems and the timing tables."
    )


def skill_levers(ctx) -> str:
    """2–3 skills to cultivate based on dominant ten-god class + favorable element."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    cls = _class_counts(chart)
    dominant = _dominant_classes(chart, 1)
    dom_class = dominant[0][0] if dominant else "Companion"
    skill_pool = {
        "Companion": ["peer collaboration", "team facilitation", "honest self-assessment"],
        "Robber": ["competitive positioning", "negotiation", "boundary-setting"],
        "Output": ["written or verbal communication", "creative production", "presentation craft"],
        "Direct Wealth": ["financial modelling", "value-pricing", "asset stewardship"],
        "Indirect Wealth": ["deal-sourcing", "investment evaluation", "opportunity spotting"],
        "Direct Officer": ["structured planning", "policy literacy", "conflict mediation"],
        "Seven Killings": ["decisive action under pressure", "rapid prioritization", "turnaround leadership"],
        "Direct Resource": ["deep expertise in one domain", "patient study", "documentation"],
        "Indirect Resource": ["intuition-driven research", "pattern recognition", "cross-domain synthesis"],
    }
    skills = skill_pool.get(dom_class, ["structured planning", "clear communication", "patient execution"])[:3]
    fav_note = {
        "Water": "Cultivate **listening and reflective writing** to strengthen Water's receptive quality.",
        "Wood": "Cultivate **growth-oriented learning** — books, mentors, or courses — to feed Wood's upward motion.",
        "Fire": "Cultivate **public visibility** — speaking, publishing, or teaching — to light Fire's radiance.",
        "Earth": "Cultivate **slow, steady routines** — daily practice, steady journaling, long-cycle planning.",
        "Metal": "Cultivate **refinement and discipline** — editing, design, or craft that rewards precision.",
    }.get(fav, "")
    parts = [f"**{dom_class}-dominant** charts tend to grow fastest through {skills[0]}, {skills[1]}, and {skills[2]}."]
    if fav_note:
        parts.append(fav_note)
    return " ".join(parts)


def wealth_preservation_long(ctx) -> str:
    """Long Wealth Preservation Note for Deep tier."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    verdict_label = _display_verdict(verdict)
    return (
        f"For a **{dm_elem}** Day Master with a **{verdict_label}** reading, wealth preservation starts with "
        f"diversification — never concentrate more than your chart can comfortably hold. "
        f"Liquidity buffers aligned with the **{fav}** element (its colors, foods, and rhythms) help the "
        f"querent stay flexible across unfavorable 대운 periods. "
        f"Partnerships and joint ventures work well when the partner's element supports {fav}; avoid "
        f"partners whose chart emphasizes the unfavorable element, since their decisions tend to amplify "
        f"the chart's existing pressure. "
        f"Across a full lifetime, the disciplined saver with {fav}-aligned custodians outperforms the "
        f"aggressive investor whose chart cannot hold the volatility."
    )


def company_type_fit(ctx) -> str:
    """Best-fit organisation style."""
    chart = _ctx_get(ctx, "chart")
    cls = _class_counts(chart)
    direct_officer = cls.get("Direct Officer", 0)
    seven_killings = cls.get("Seven Killings", 0)
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    if verdict in ("strong", "extreme") and seven_killings >= 1 and direct_officer == 0:
        return (
            "A **boutique firm or solo practice** is the most likely fit. The Seven Killings presence without "
            "Direct Officer prefers competitive, high-velocity environments over bureaucratic ones, and the "
            "strong Day Master can absorb the volatility."
        )
    if direct_officer >= 1 and seven_killings == 0:
        return (
            "**Large institutions and mid-size specialists** are the most likely fit. The Direct Officer stem "
            "values hierarchy, credential, and a clear chain of accountability — the querent is most "
            "productive when the structure around them is unambiguous."
        )
    if direct_officer >= 1 and seven_killings >= 1:
        return (
            "A **mid-size specialist firm with strong leadership visibility** is the most likely fit. Both "
            "Direct Officer and Seven Killings are present, so the querent needs a credible structure but "
            "also room to push back when needed."
        )
    return (
        "Neither Authority nor Wealth is dominant, so **a small team with clear values** is likely the best "
        "fit — a culture defined by mutual trust rather than hierarchy or chaos."
    )


def boss_team_dynamics(ctx) -> str:
    """Ideal manager profile + warning signs."""
    chart = _ctx_get(ctx, "chart")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    fav = _ctx_get(ctx, "favorable", "—")
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    complement = {
        "Wood": "steady Earth mentor",
        "Fire": "patient Water advisor",
        "Earth": "visionary Wood leader",
        "Metal": "warm Fire motivator",
        "Water": "structured Earth anchor",
    }.get(fav, "complementary-element mentor")
    warning = {
        "Wood": "constant crisis mode that fragments Wood's growth",
        "Fire": "cold isolation that starves Fire's warmth",
        "Earth": "rapid change that erodes Earth's stability",
        "Metal": "vague goals that blunt Metal's precision",
        "Water": "rigid rules that dam Water's flow",
    }.get(dm_elem, "environments that ignore the Day Master's nature")
    return (
        f"The ideal manager profile is a **{complement}** — someone whose element complements rather than "
        f"competes with your Day Master. Watch for {warning}; this is the most common way the querent's "
        f"energy gets drained in a team setting."
    )


def red_flag_environments(ctx) -> str:
    """2–3 workplace drainers."""
    chart = _ctx_get(ctx, "chart")
    unfav = _ctx_get(ctx, "unfavorable") or "the challenging element"
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    items = []
    if verdict in ("weak", "extreme_weak"):
        items.append("environments with unclear accountability — the querent absorbs other people's work")
        items.append("constant crisis mode with no recovery windows")
        items.append("isolated creative demands with no peer feedback")
    elif verdict in ("strong", "extreme"):
        items.append("slow bureaucratic processes that the querent's energy quickly overruns")
        items.append("unclear decision rights — strong Day Masters struggle without ownership")
        items.append("teams that refuse to challenge the querent's ideas")
    else:
        items.append(f"long stretches of {unfav}-heavy work that drain the Day Master")
        items.append("either-or framing that forces a single dominant choice")
        items.append("environments that ignore the favorable element's rhythm")
    return "Look out for: " + "; ".join(items[:3]) + "."


def decade_career_strategy(ctx, p) -> str:
    """One paragraph per 대운 connecting ten-god + favorable_status to career phase."""
    tg = p.stem_tengod_en or p.stem_tengod or "—"
    status = period_favorable_status(p, ctx)
    branch_elem = p.branch_element or "—"
    stem_elem = p.stem_element or "—"
    fav = _ctx_get(ctx, "favorable", "—")
    if "favor" in status:
        phase = "build and rise"
        guidance = "Plant several seeds at once — the chart can carry more than one initiative in this window."
    elif "challeng" in status or "difficult" in status:
        phase = "conserve and consolidate"
        guidance = "Protect what already works; defer large bets and focus on craft and relationships."
    else:
        phase = "transition and adapt"
        guidance = "Use the mixed energy to refine skills and reposition rather than to launch new ventures."
    return (
        f"With a **{tg}** ten-god over a **{branch_elem}** branch (stem element {stem_elem}), this is a "
        f"{phase} decade. {guidance} Years where the stem element matches the favorable **{fav}** energy "
        f"are the most reliable for visible wins; the others are best used for quiet preparation."
    )


# ── Relationship fillers ────────────────────────────────────────────────

def relationship_style(ctx) -> str:
    """Relationship Style paragraph: spouse palace + hidden stem ten-god + implication."""
    chart = _ctx_get(ctx, "chart")
    spouse_branch = chart.day.branch
    spouse_tg = "—"
    spouse_tg_ko = ""
    for hit in chart.ten_gods:
        if hit.position == "day_branch_main":
            spouse_tg = hit.tengod_en or hit.tengod
            spouse_tg_ko = hit.tengod
            break
    peach = chart.stars.get("peach_blossom", []) if chart.stars else []
    from . import lookup as L
    try:
        stage = L.twelve_stage(chart.day_master, spouse_branch)
    except Exception:
        stage = "—"
    # Look up by the simplified class key derived from the KOREAN ten-god
    # code (via _TENGOD_CLASS), not by `spouse_tg` (the full English gloss,
    # e.g. "Hurting Officer (傷官)") — the dict below is keyed by the class
    # name ("Output", "Companion", etc.), which the full gloss never matches.
    # Bug found 2026-09-19 (external report review): this lookup always
    # missed and fell through to the generic fallback sentence below,
    # regardless of the actual spouse-palace ten-god — confirmed identical
    # fallback text ("you bring the querent's full nature into the
    # partnership") in every candidate report's Relationship Style
    # paragraph, across at least 4 different actual ten-gods (Robber,
    # Indirect Resource, Direct Resource, Hurting Officer).
    implication = {
        "Companion": "you want a partner who feels like an equal — neither admiring nor competing, just present.",
        "Robber": "you are drawn to partners who challenge you, which can be exhilarating or exhausting.",
        "Output": "you express affection through doing — cooking, building, fixing — not always through words.",
        "Direct Wealth": "you find steadiness attractive; partners who can hold resources well feel safe.",
        "Indirect Wealth": "you are attracted to variety and the unexpected, which keeps long-term partnerships fresh.",
        "Direct Officer": "you value reliability and a partner who respects clear roles in the relationship.",
        "Seven Killings": "you want a partner who is strong and direct; passivity is more uncomfortable than conflict.",
        "Direct Resource": "you are drawn to partners who feel grounding, patient, and protective of your inner life.",
        "Indirect Resource": "you are drawn to partners who spark your curiosity and bring unexpected insights.",
    }.get(_TENGOD_CLASS.get(spouse_tg_ko, ""), "you bring your full nature into the partnership.")
    base = (
        f"The spouse palace is **{spouse_branch}** (12-stage: {stage}), whose main hidden stem relates to "
        f"your Day Master as **{spouse_tg}**. In practice, {implication}"
    )
    if peach:
        base += f" **도화 (Peach Blossom)** is present at **{', '.join(peach)}**, adding warmth and relational magnetism."
    else:
        base += " No **도화** star is natally active, so relationship style is more shaped by the spouse palace and ten-god mix than by overt magnetism."
    return base


def spouse_palace_tengod(ctx) -> str:
    """Partner-domain tendency from the ten-god of the day-branch main hidden stem.

    Reads the spouse palace (배우자궁, 夫妻宮) as a domain rather than a personality
    trait — what kind of relational atmosphere the chart tends to create.
    Source: knowledge/05-ten-gods.md and knowledge/07-special-formations.md §spouse palace.
    """
    chart = _ctx_get(ctx, "chart")
    spouse_branch = chart.day.branch
    spouse_tg_ko = "—"
    spouse_tg_en = "—"
    for hit in chart.ten_gods:
        if hit.position == "day_branch_main":
            spouse_tg_ko = hit.tengod
            spouse_tg_en = _TENGOD_CLASS.get(hit.tengod, hit.tengod_en or hit.tengod)
            break
    from . import lookup as L
    try:
        stage = L.twelve_stage(chart.day_master, spouse_branch)
    except Exception:
        stage = "—"
    domain = {
        "Companion": "a peer-like partnership where independence and togetherness stay in balance",
        "Robber": "a lively, sometimes competitive partnership that keeps the querent sharp",
        "Output": "a creative, doing-oriented partnership; shared projects and conversation matter more than convention",
        "Direct Wealth": "a stable, materially grounded partnership where practical care reads as love",
        "Indirect Wealth": "a varied, opportunity-rich partnership that resists rigid routine",
        "Direct Officer": "a structured, respectful partnership with clear roles and reliability",
        "Seven Killings": "an intense, direct partnership; the spouse palace can attract strong, forceful figures",
        "Direct Resource": "a protective, grounding partnership that offers rest and steady support",
        "Indirect Resource": "an unusual or insight-driven partnership — the spouse domain teaches the querent things",
    }.get(spouse_tg_en, "a partnership shaped by the chart's full ten-god mix")
    return (
        f"The spouse palace **{spouse_branch}** (12-stage: {stage}) carries a main hidden stem that "
        f"relates to your Day Master as **{spouse_tg_en} ({spouse_tg_ko})**. In the partner domain "
        f"this points toward {domain}. Read this as an atmospheric tendency, not a prediction about "
        f"a specific person."
    )


def three_mindful_notes(ctx) -> List[str]:
    """3 short bullets for the 'Three Things to Be Mindful Of' section."""
    chart = _ctx_get(ctx, "chart")
    notes: List[str] = []
    # (1) 도화 presence/absence
    peach = chart.stars.get("peach_blossom", []) if chart.stars else []
    if peach:
        notes.append(
            f"**도화 (Peach Blossom)** is active at **{', '.join(peach)}** — relational magnetism is high; "
            f"be deliberate about which invitations you accept."
        )
    else:
        notes.append(
            "**도화 (Peach Blossom)** is not natally active, so your social style leans toward depth rather "
            "than breadth — protect your close-circle time."
        )
    # (2) spouse palace clash or combination
    if chart.clashes:
        involved_in_spouse = any(c[0] == chart.day.branch or c[1] == chart.day.branch for c in chart.clashes)
        if involved_in_spouse:
            notes.append(
                f"The day branch **{chart.day.branch}** is involved in a natal clash, so partnerships tend "
                f"to surface change or tension — frame this as information, not a verdict."
            )
        else:
            for a, c in chart.clashes:
                notes.append(
                    f"A natal clash between **{a}** and **{c}** brings recurring pressure between two life palaces; "
                    f"in relationships, this often shows up as competing priorities."
                )
                break
    elif chart.combinations_6:
        a, c, elem, pa, pb = chart.combinations_6[0]
        notes.append(
            f"A natal six-combination between **{a}** and **{c}** draws the partner into a transformation "
            f"toward **{elem}** energy — expect the relationship to ask for adaptation."
        )
    else:
        notes.append(
            "No major natal clashes touch the spouse palace, so relationship friction is more likely to "
            "come from timing (대운/세운 activations) than from the natal structure."
        )
    # (3) current/upcoming 대운 relationship theme
    current = _ctx_get(ctx, "current_daeun")
    if current:
        tg = current.stem_tengod_en or current.stem_tengod or "—"
        notes.append(
            f"The current major-luck period (**{current.combined}**, {tg}) carries "
            f"{'favorable' if period_favorable_status(current, ctx) == 'favorable' else 'mixed'} "
            f"energy for relationships — the next few years are about consolidation rather than reinvention."
        )
    else:
        notes.append(
            "The current 대운 is in a stable phase, so relationships benefit from sustained attention "
            "rather than dramatic gestures."
        )
    return notes[:3]


def relationship_timing_row(year: int, pillar: str, tengod: str) -> str:
    """1-line theme for a relationship-timing year (2026–2031)."""
    from . import lookup as L
    # Look up the year's stem element from the pillar's first char (stem).
    stem = pillar[:1] if pillar else "—"
    elem = L.STEM_INFO.get(stem, {}).get("element", "—")
    class_theme = {
        "Direct Officer": "structure and visible milestones (engagement, marriage, formal commitment)",
        "Seven Killings": "intensity and transformation — expect a relationship to demand change",
        "Direct Wealth": "stability and value-sharing — good for settling into a long-term rhythm",
        "Indirect Wealth": "variety and social expansion — meeting new people, diversifying the social circle",
        "Output": "creative expression together — projects, conversations, or artistic collaboration",
        "Direct Resource": "support and study — a partner who mentors or grounds you",
        "Indirect Resource": "intuition and surprise — a relationship that teaches you something unexpected",
        "Companion": "peer energy — friendships and partnerships strengthen",
        "Robber": "competition or boundary-setting — be clear about what you will and will not negotiate",
    }
    theme = class_theme.get(tengod, "a year that asks the relationship to evolve quietly")
    return f"**{elem}** energy + {tengod}: {theme}."


def friendship_social_energy(ctx) -> str:
    """3–4 sentences on friendship energy."""
    chart = _ctx_get(ctx, "chart")
    cls = _class_counts(chart)
    fav = _ctx_get(ctx, "favorable", "—")
    unfav = _ctx_get(ctx, "unfavorable") or "the challenging element"
    dominant = _dominant_classes(chart, 2)
    dom_classes = ", ".join(f"{c} ({n})" for c, n in dominant) or "Companion"
    attracts = {
        "Wood": "people who are curious, learning, and growing",
        "Fire": "people who are visible, expressive, and energetic",
        "Earth": "people who are grounded, practical, and steady",
        "Metal": "people who are precise, principled, and disciplined",
        "Water": "people who are reflective, listening, and emotionally present",
    }.get(fav, "people whose element resonates with the querent's growth edge")
    drains = {
        "Wood": "people who refuse to grow or change",
        "Fire": "people who demand constant attention without reciprocity",
        "Earth": "people who are chaotic and directionless",
        "Metal": "people who are harsh, critical, or cold",
        "Water": "people who are stagnant or emotionally unavailable",
    }.get(unfav, "people who drain rather than nourish")
    return (
        f"Friend and social energy is shaped by the chart's dominant classes — **{dom_classes}** — so the "
        f"querent tends to give and receive in those modes. The querent is naturally drawn to {attracts}, "
        f"and tends to feel drained by {drains}. Social settings where the favorable **{fav}** element is "
        f"present (a community garden for Wood, a quiet studio for Water, a workshop for Metal) tend to "
        f"feel more nourishing than large unstructured gatherings."
    )


def attachment_patterns(ctx) -> str:
    """Deep-only: attachment from spouse palace hidden stems + day branch stage."""
    chart = _ctx_get(ctx, "chart")
    spouse_branch = chart.day.branch
    from . import lookup as L
    try:
        stage = L.twelve_stage(chart.day_master, spouse_branch)
    except Exception:
        stage = "—"
    hidden_tgs = []
    for role, stem in chart.day.hidden_stems:
        try:
            hidden_tgs.append(L.ten_god(chart.day_master, stem))
        except Exception:
            hidden_tgs.append("—")
    hidden_summary = ", ".join(hidden_tgs) if hidden_tgs else "—"
    return (
        f"With the spouse palace **{spouse_branch}** sitting in the **{stage}** 12-stage and carrying "
        f"hidden-stem ten-gods of **{hidden_summary}**, the querent bonds through a mix of presence "
        f"and discernment. The day branch's stage matters: a **절/병/사** stage asks for openness and "
        f"vitality, while a **묘/관/충** stage leans toward reserve and selectivity. The hidden-stem "
        f"ten-gods colour the undercurrent — Resource leans into safety, Output into creative play, "
        f"Wealth into stability. Read this as the emotional baseline; the 대운/세운 overlays show when "
        f"the querent's bond patterns shift most."
    )


def marriage_timing_windows(ctx) -> str:
    """Deep-only: 2–3 strongest commitment years in current + next 대운."""
    chart = _ctx_get(ctx, "chart")
    current = _ctx_get(ctx, "current_daeun")
    daeun = chart.daeun
    if not daeun:
        return "Major-luck data not available; defer to the annual timing tables."
    try:
        cur_idx = next(i for i, p in enumerate(daeun) if current and p.combined == current.combined)
    except StopIteration:
        cur_idx = 0
    spans = daeun[cur_idx:cur_idx + 2] if cur_idx + 2 <= len(daeun) else daeun[cur_idx:]
    current_age = getattr(chart, "current_age", None)
    candidates = []
    for p in spans:
        if current_age is not None and not (p.start_age <= current_age <= p.end_age):
            continue
        if period_favorable_status(p, ctx) == "favorable":
            candidates.append(f"**{p.combined}** (ages {p.start_age}-{p.end_age}, {period_favorable_status(p, ctx)})")
    if not candidates and spans:
        candidates.append(
            f"**{spans[0].combined}** (ages {spans[0].start_age}-{spans[0].end_age}) — "
            f"favorable-element years within this window are the strongest commitment windows"
        )
    if not candidates:
        return "Timing data incomplete; defer to the annual windows and 세운 overlays."
    body = "; ".join(candidates[:3])
    return (
        f"The strongest windows for commitment decisions in the current and next major-luck periods: {body}. "
        f"Within those windows, the annual pillars whose stem element matches the favorable element are "
        f"the cleanest moments to formalize; clash years are better for deepening privately."
    )


def family_dynamics(ctx) -> str:
    """Deep-only: parent/child themes from year/month pillars and any activated stars."""
    chart = _ctx_get(ctx, "chart")
    year_branch = chart.year.branch
    month_branch = chart.month.branch
    hour_branch = chart.hour.branch
    peach = chart.stars.get("peach_blossom", []) if chart.stars else []
    travel = chart.stars.get("travelling_star", []) if chart.stars else []
    parts = [
        f"The year pillar **{year_branch}** carries ancestral and parental themes; its main hidden stem "
        f"shapes how the querent absorbs (or pushes back on) family-of-origin patterns.",
        f"The month pillar **{month_branch}** is the career and sibling palace — its dynamics surface in "
        f"how the querent shows up among peers and early mentors.",
    ]
    if hour_branch:
        parts.append(
            f"The hour pillar **{hour_branch}** speaks to children and later life — its hidden stems "
            f"indicate what the querent is likely to pass on, and what they will need to consciously teach."
        )
    stars: List[str] = []
    if peach:
        stars.append(f"**도화** at **{', '.join(peach)}** (romantic and creative magnetism)")
    if travel:
        stars.append(f"**역마** at **{', '.join(travel)}** (frequent movement; family may be geographically dispersed)")
    if stars:
        parts.append("Activated classical stars: " + "; ".join(stars) + ".")
    return " ".join(parts)


# ── Health fillers ───────────────────────────────────────────────────────

def overdrive_warning(ctx) -> str:
    """How a <strength_label> <dm_element> Day Master may overdrive."""
    chart = _ctx_get(ctx, "chart")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    verdict = _ctx_get(ctx, "strength_label", "Balanced")
    organs = _ELEMENT_ORGANS.get(dm_elem, "associated organ systems")
    fav = _ctx_get(ctx, "favorable", "—")
    overdrive = {
        "Wood": "burning out through over-effort, irritability, or muscular tension",
        "Fire": "burning out through over-visibility, agitation, or cardiac strain",
        "Earth": "burning out through worry, over-nurturing, or digestive sluggishness",
        "Metal": "burning out through perfectionism, grief, or respiratory tightness",
        "Water": "burning out through over-work, isolation, or depletion of deep reserves",
    }.get(dm_elem, "burning out through excess expression of the Day Master's element")
    warning = {
        "Strong": f"A **Strong** {dm_elem} Day Master has surplus self-energy and may push past the body without noticing. Watch for {overdrive}, especially during demanding seasons or under high-output projects.",
        "Very Strong": f"A **Very Strong** {dm_elem} Day Master has the most self-energy to spare but also the most to lose when output exceeds input. Watch for {overdrive}.",
        "Balanced": f"A **Balanced** {dm_elem} Day Master has reasonable reserves but still needs conscious rhythm. Watch for {overdrive} when output stays high without recovery windows.",
        "Weak": f"A **Weak** {dm_elem} Day Master has limited reserves and overdrives quickly when asked to perform at full stretch. Watch for {overdrive} — recovery matters more than another push.",
        "Very Weak": f"A **Very Weak** {dm_elem} Day Master has very limited reserves and can be overwhelmed by ordinary demands. Watch for {overdrive} and protect sleep, meals, and quiet time.",
        "Slightly Weak": f"A **Slightly Weak** {dm_elem} Day Master is one stretch past their natural capacity from being overwhelmed. Watch for {overdrive} and protect sleep, meals, and quiet time.",
    }.get(verdict, f"A {dm_elem} Day Master may overdrive; watch for {overdrive}.")
    return (
        warning
        + f" In classical Five-Element reading, the **{organs}** are a common watchpoint when "
        + f"energy is overstretched; the **{fav}** element's practices "
        + f"(its seasons, foods, and rhythms) are the simplest countermeasure."
    )


def depleted_element_health(ctx) -> str:
    """Tentative health watch area based on the most depleted weighted element.

    Uses `_element_pct` to find the element with the smallest share and pairs
    it with the organ mapping in `_ELEMENT_ORGANS`. This is a preventive,
    non-diagnostic cue from Five-Element balance
    (knowledge/03-five-elements.md; organ correspondence per
    knowledge/15-health-and-body.md § 오행 → Organ Systems).
    """
    chart = _ctx_get(ctx, "chart")
    pct = _element_pct(chart)
    if not pct:
        return "Element-balance data is unavailable; defer to the primary watchpoints."
    depleted = min(pct.items(), key=lambda kv: kv[1])
    elem, value = depleted
    organs = _ELEMENT_ORGANS.get(elem, f"the {elem.lower()}-associated organ systems")
    return (
        f"The chart's lightest weighted element is **{elem} ({value}%)**, which in classical "
        f"Five-Element mapping is paired with the **{organs}**. This is not a diagnosis; it is "
        f"the least natally emphasized system, making it the natural place to begin gentle, "
        f"preventive support through {elem.lower()}-aligned foods, seasons, and rhythms."
    )


def seasonal_daily_rhythms(ctx) -> str:
    """Best season/time-of-day for the chart."""
    chart = _ctx_get(ctx, "chart")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    fav = _ctx_get(ctx, "favorable", "—")
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    dm_season = {
        "Wood": "spring", "Fire": "summer", "Earth": "late summer / transitions",
        "Metal": "autumn", "Water": "winter",
    }.get(dm_elem, "the querent's own season")
    fav_season = {
        "Wood": "spring (the rising Wood energy)", "Fire": "summer (the peak Fire energy)",
        "Earth": "the transitions between seasons", "Metal": "autumn (the harvest, the refinement)",
        "Water": "winter (the deep, still Water energy)",
    }.get(fav, "the favorable element's natural season")
    return (
        f"The **{dm_elem}** Day Master is most at home in **{dm_season}**; that is when the chart's "
        f"natural energy peaks. "
        f"Conversely, the chart is most depleted in the season of the unfavorable element — protect "
        f"rest and reduce commitments during those months. "
        f"The favorable **{fav}** element's season (**{fav_season}**) is the cleanest window for new "
        f"beginnings and visible projects; use it deliberately. "
        f"In the daily cycle, the {fav} hours of the day (per the Twelve Stages) are the most aligned — "
        f"mornings for Wood, midday for Fire, transitions for Earth, afternoons for Metal, evenings for Water."
    )


def element_story(ctx) -> str:
    """Element Story paragraph for Deep health deep-dive."""
    chart = _ctx_get(ctx, "chart")
    pct = _element_pct(chart)
    sorted_elems = sorted(pct.items(), key=lambda kv: -kv[1])
    excess = sorted_elems[0]
    deficient = sorted_elems[-1]
    return (
        f"This chart's element balance shows **{excess[0]} ({excess[1]}%)** as the most present element "
        f"and **{deficient[0]} ({deficient[1]}%)** as the least. "
        f"Energy tends to **{'accumulate and congest' if excess[1] > 35 else 'flow in cycles'}** in the "
        f"{excess[0]} domain; a balanced day feels like quiet movement between input, processing, and "
        f"release. The {deficient[0]} system is the most likely leak point — under-supported and easy to "
        f"neglect — and the easiest place to begin rebuilding through the favorable element's practices."
    )


def stress_signature(ctx) -> str:
    """3 physical/emotional out-of-balance signals from a fixed pool."""
    chart = _ctx_get(ctx, "chart")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    unfav = _ctx_get(ctx, "unfavorable") or "the challenging element"
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    signals = {
        "Wood": ["irritability or quick frustration", "neck/shoulder tension", "indecision or feeling stuck"],
        "Fire": ["agitation or racing thoughts", "chest tightness or palpitations", "difficulty sleeping"],
        "Earth": ["worry that loops without resolution", "digestive sluggishness", "feeling over-responsible for others"],
        "Metal": ["grief that surfaces unbidden", "skin or respiratory sensitivity", "rigid perfectionism"],
        "Water": ["deep fatigue or depletion", "lower-back or kidney-area tension", "withdrawal and isolation"],
    }.get(dm_elem, ["sleep disruption", "irritability", "digestive shifts"])
    base = (
        f"When this chart goes out of balance, the most common early signals are: "
        f"{signals[0]}, {signals[1]}, and {signals[2]}. "
    )
    if verdict in ("weak", "extreme_weak"):
        base += (
            f"The pattern usually appears first as physical depletion — the {dm_elem} system runs hot to "
            f"compensate, then crashes. Recovery comes from actively cultivating the favorable element before "
            f"the crash, not after."
        )
    else:
        verdict_label = _display_verdict(verdict)
        base += (
            f"With a {verdict_label} reading, the early signs are more emotional than physical — irritability, "
            f"detachment, or perfectionism show up before the body signals."
        )
    return base


def recovery_toolkit(ctx) -> str:
    """4 recovery practices for Deep health deep-dive."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    base = {
        "Water": ["evening walks near water", "soup or broth as a regular meal", "20 minutes of stillness before sleep", "reading fiction that lets the mind drift"],
        "Wood": ["morning walks among trees", "leafy-green meals 4–5 times a week", "stretching or tai chi", "creative writing before noon"],
        "Fire": ["midday sunlight exposure (10–15 minutes)", "a creative project with a visible output each week", "a shared meal with company", "a daily moment of celebration or laughter"],
        "Earth": ["a fixed wake-time and sleep-time", "warm cooked meals at regular hours", "light journaling at season transitions", "gardening or grounding physical work"],
        "Metal": ["a quiet hour of focused craft (drawing, editing, instrument practice)", "white or silver objects near the workspace", "breathwork in cool air", "a weekly review and tidy"],
    }.get(fav, ["daily rhythm", "weekly review", "seasonal reset", "a quiet anchor practice"])
    dm_practice = {
        "Water": "Rest before you feel you need to — Water's recovery is preventive, not reactive.",
        "Wood": "Learn in public — teach, write, or share. Wood feeds on growth that has an audience.",
        "Fire": "Make something visible every week. Fire without output burns itself out.",
        "Earth": "Slow down on purpose — Earth recovers by staying still, not by pushing harder.",
        "Metal": "Refine what is already there. Metal recovers through editing, polishing, and small precision.",
    }.get(dm_elem, "Anchor recovery in small, repeatable rituals.")
    parts = [f"**Favorable-element practices ({fav}):**"]
    for p in base:
        parts.append(f"- {p}")
    parts.append(f"**Day-Master practice ({dm_elem}):** {dm_practice}")
    return "\n".join(parts)


def long_term_vitality_strategy(ctx) -> str:
    """Sustainable habits across the coming 대운 periods."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    supportive_periods = []
    conserving_periods = []
    for p in chart.daeun:
        status = period_favorable_status(p, ctx)
        if "favor" in status:
            supportive_periods.append(f"ages {p.start_age}-{p.end_age} ({p.combined})")
        elif "challeng" in status or "difficult" in status:
            conserving_periods.append(f"ages {p.start_age}-{p.end_age} ({p.combined})")
    parts = []
    if supportive_periods:
        parts.append(
            f"**Renewal windows** — the chart's energy supports new health practices and increased "
            f"capacity during: {', '.join(supportive_periods[:3])}. Use these decades to build resilience."
        )
    if conserving_periods:
        parts.append(
            f"**Conservation windows** — the chart asks for gentler practice during: "
            f"{', '.join(conserving_periods[:3])}. Reduce load, deepen recovery, and avoid starting "
            f"ambitious new regimens in these years."
        )
    parts.append(
        f"Across all periods, the **{fav}** element's daily practices (its season, foods, colors, and "
        f"rhythms) are the simplest and most reliable countermeasure — small daily inputs compound more "
        f"than occasional heroic efforts."
    )
    return "\n\n".join(parts)


# ── Timing fillers ───────────────────────────────────────────────────────

def major_luck_theme_row(p, ctx) -> Tuple[str, str]:
    """(career_theme, relationship_theme) for one 대운 row."""
    status = period_favorable_status(p, ctx)
    favorable = "favor" in status
    cls = _TENGOD_FIVE_CLASS.get(p.stem_tengod, "")
    if cls == "Authority":
        career = "structured career moves; credentials matter"
        relationship = "commitment or formalization themes"
    elif cls == "Wealth":
        career = "income, assets, or value-creation themes"
        relationship = "shared resources or lifestyle alignment"
    elif cls == "Output":
        career = "creative output, voice, or visible production"
        relationship = "creative partnership or playful dynamic"
    elif cls == "Resource":
        career = "study, mentorship, or skill-building"
        relationship = "nurturing, support, or healing connection"
    else:
        career = "peer-driven or self-defined work"
        relationship = "friendship-based or peer dynamic"
    if not favorable:
        career = career + " (mixed — protect, don't overcommit)"
    return career, relationship


def major_luck_narrative(p, ctx) -> str:
    """Full 1-paragraph interpretation per 대운."""
    tg = p.stem_tengod_en or p.stem_tengod or "—"
    status = period_favorable_status(p, ctx)
    branch_elem = p.branch_element or "—"
    stem_elem = p.stem_element or "—"
    fav = _ctx_get(ctx, "favorable", "—")
    cls = _TENGOD_FIVE_CLASS.get(p.stem_tengod, "")
    undertow = (
        "commitment and visibility" if cls in ("Authority", "Wealth")
        else "creative exploration" if cls == "Output"
        else "support and study"
    )
    return decade_career_strategy(ctx, p) + (
        f" Relationships in this window carry the same **{tg}** undertow — themes of "
        f"{undertow} "
        f"are likely. The favorable **{fav}** element shows up most clearly in years and months whose "
        f"stem matches it — these are the periods to lean in."
    )


def current_period_deep_dive(ctx) -> str:
    """2 paragraphs: what this decade is for + specific opportunity window."""
    chart = _ctx_get(ctx, "chart")
    current = _ctx_get(ctx, "current_daeun")
    fav = _ctx_get(ctx, "favorable", "—")
    if not current:
        return "Current major-luck period is outside the chart's documented 대운 range."
    tg = current.stem_tengod_en or current.stem_tengod or "—"
    status = period_favorable_status(current, ctx)
    branch_elem = current.branch_element or "—"
    favorable = "favor" in status
    do = "push visible projects, plant seeds, and request what is owed" if favorable else "conserve, refine, and protect the foundation"
    avoid = "long commitments whose payoff is years away" if not favorable else "starting too many things at once"
    return (
        f"This decade carries a **{tg}** ten-god over a **{branch_elem}** branch — "
        f"{'a clearly favorable window for visible wins.' if favorable else 'a mixed window that asks for measured moves rather than bold ones.'} "
        f"The stem ten-god is the *outer theme* — what the world sees and asks of the querent — "
        f"while the branch element is the *underlying terrain* — the quieter emotional and circumstantial backdrop. "
        f"Read them together rather than separately; mismatches between outer theme and inner terrain are where "
        f"this decade is most likely to surprise.\n\n"
        f"Specifically: **do** {do}; **avoid** {avoid}. "
        f"Within this decade, years and months whose stem element matches the favorable **{fav}** energy are "
        f"the cleanest moments for major commitments; the annual windows table below shows them. "
        f"Years dominated by the unfavorable element are best used for rest, review, and quiet preparation."
    )


def annual_window_row(h, ctx) -> Tuple[str, str, str]:
    """(overall_theme, best_uses, watch_out_for) for one annual hit."""
    from . import lookup as L
    stem = h.stem
    elem = L.STEM_INFO.get(stem, {}).get("element", "—")
    tg = h.stem_tengod_en or h.stem_tengod or "—"
    fav = _ctx_get(ctx, "favorable", "—")
    sup = _ctx_get(ctx, "supporting", "—")
    favorable = elem in {fav, sup}
    theme = f"{elem} energy + {tg} — a {'favorable-element' if favorable else 'mixed'} year."
    cls = _TENGOD_FIVE_CLASS.get(h.stem_tengod, "")
    if cls == "Authority":
        best = "career moves, credentials, formal commitments"
        watch = "stubborn authority clashes; avoid ego fights"
    elif cls == "Wealth":
        best = "income launches, negotiations, value-pricing"
        watch = "over-leveraging or risky investments"
    elif cls == "Output":
        best = "creative production, writing, speaking, teaching"
        watch = "speaking before thinking; reputation risk"
    elif cls == "Resource":
        best = "study, mentorship, rest, skill-building"
        watch = "over-isolation or missed opportunities"
    else:
        best = "peer projects, friendships, self-definition"
        watch = "comparison and competition with peers"
    if not favorable:
        watch = f"{watch}; the {elem} element drains rather than feeds — slow down"
    return theme, best, watch


def year_by_year_note(h, ctx) -> str:
    """2 sentences per year: best focus + one caution."""
    from . import lookup as L
    stem = h.stem
    elem = L.STEM_INFO.get(stem, {}).get("element", "—")
    tg = h.stem_tengod_en or h.stem_tengod or "—"
    fav = _ctx_get(ctx, "favorable", "—")
    favorable = elem in {fav, _ctx_get(ctx, "supporting", "")}
    focus = {
        "Wood": "growth, learning, and creative expansion",
        "Fire": "visibility, speaking, and visible output",
        "Earth": "grounding, routines, and supporting others",
        "Metal": "refinement, precision, and clear boundaries",
        "Water": "reflection, listening, and quiet study",
    }.get(elem, "the chart's natural rhythm")
    caution = {
        "Wood": "watch for over-effort and stiffness",
        "Fire": "watch for burnout from over-visibility",
        "Earth": "watch for over-responsibility and worry",
        "Metal": "watch for rigidity and harsh self-judgment",
        "Water": "watch for isolation and depletion",
    }.get(elem, "watch for the chart's natural pressure point")
    year_kind = "**favorable-element year**" if favorable else "an annual energy to navigate consciously"
    return (
        f"This is {year_kind} — best focused on {focus}. "
        f"Caution: {caution}; pace yourself rather than pushing through."
    )


# ── Pattern / Closing fillers ───────────────────────────────────────────

def _pattern_candidate_label(kind: str, val) -> str:
    """Human-readable label for a `chart.patterns` entry.

    Pattern values vary by kind — a list of GridCandidate dataclasses
    (regular_grid), dicts (transformation_grid / special_forms), or plain
    strings. Interpolating the raw value into an f-string would leak a
    dataclass repr into client-facing prose; this formats it properly.
    """
    def _from_mapping(m: dict) -> str:
        ko = m.get("name_ko") or kind
        en = m.get("name_en") or ""
        return f"{ko} ({en})" if en else ko

    if isinstance(val, list) and val:
        first = val[0]
        if hasattr(first, "name_ko"):
            en = getattr(first, "name_en", "")
            return f"{first.name_ko} ({en})" if en else first.name_ko
        if isinstance(first, dict):
            return _from_mapping(first)
        return kind
    if isinstance(val, dict):
        return _from_mapping(val)
    if isinstance(val, str):
        return f"{kind} — {val}"
    return kind


def pattern_story(ctx) -> str:
    """3–5 sentences summarizing the dominant pattern candidate."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    parts = []
    if chart.patterns:
        top_kind, top_val = next(iter(chart.patterns.items()))
        top_label = _pattern_candidate_label(top_kind, top_val)
        if top_label:
            parts.append(
                f"The chart's dominant pattern candidate is **{top_label}**."
            )
    if chart.combinations_6:
        a, c, elem, pa, pb = chart.combinations_6[0]
        parts.append(
            f"A six-combination between **{a}** and **{c}** transforms toward **{elem}** energy, "
            f"linking the {pa} and {pb} palaces."
        )
    if chart.three_harmonies:
        a, b, c, elem = chart.three_harmonies[0]
        parts.append(
            f"A three-harmony cluster among **{a}**, **{b}**, **{c}** strengthens **{elem}** energy through three life palaces."
        )
    if chart.clashes:
        a, c = chart.clashes[0]
        parts.append(
            f"A natal clash between **{a}** and **{c}** brings recurring pressure and asks the querent "
            f"to make conscious choices between the two palaces involved."
        )
    if chart.three_punishments:
        a, b, c, _ = chart.three_punishments[0]
        if c == "—":
            # Partial punishment: two branches of a 삼형 frame, third absent
            # (matches skeleton.py's rendering convention).
            parts.append(
                f"A partial three-punishment between **{a}** and **{b}** — two branches of a punishment "
                f"frame without the third — is a recurring structural pressure; "
                f"these themes mature slowly and call for patience."
            )
        else:
            parts.append(
                f"A three-punishment among **{a}**, **{b}**, **{c}** is a heavier structural pressure; "
                f"these themes mature slowly and call for patience."
            )
    if not parts:
        parts.append(
            "No major branch patterns were flagged in this chart; the reading rests more heavily on "
            "stem ten-god distribution and element balance."
        )
    parts.append(
        f"Together, these patterns point to a recurring life theme rather than a single event. "
        f"The favorable **{fav}** element is the querent's lever for working with — rather than against — "
        f"the chart's structure."
    )
    return " ".join(parts)


# ── Pattern deep-dive fillers ─────────────────────────────────────────────

# Source: knowledge/07-special-formations.md §A. Regular Grids
_REGULAR_GRID_THEME: Dict[str, str] = {
    "비견격": "self-reliance and peer dynamics — the chart learns most through equal relationships and independent effort",
    "겁재격": "competition and shared resources — success tends to come through teamwork, negotiation, and knowing when to cooperate or compete",
    "식신격": "steady, nourishing output — productive creativity, care, and craft carried forward patiently",
    "상관격": "sharp, individual voice — creative expression that can outpace convention and may push back against authority",
    "편재격": "entrepreneurial, variable wealth — larger swings in income and a sociable, opportunity-driven path",
    "정재격": "conservative, stable wealth — careful earning, traditional structure, and methodical accumulation",
    "편관격": "high-pressure authority and decisive action — careers or life phases that demand courage under constraint",
    "정관격": "conventional respectability and structure — credentials, large institutions, examinations, and public trust",
    "편인격": "specialized or unconventional knowledge — solitary study, unusual expertise, and insight that does not fit the mainstream",
    "정인격": "education, protection, and gradual advancement — certificates, mentors, real estate, and maternal support",
}


def regular_grid_narrative(ctx) -> str:
    """2-sentence life-theme sketch if a regular grid is likely.

    Uses the `chart.patterns.regular_grid` candidate from the engine and a small
    lookup grounded in knowledge/07-special-formations.md §A. Returns an empty
    string when no likely regular grid is present.
    """
    chart = _ctx_get(ctx, "chart")
    regular = chart.patterns.get("regular_grid") if chart.patterns else None
    if not regular:
        return ""
    candidate = regular[0]
    if candidate.confidence != "likely":
        return ""
    theme = _REGULAR_GRID_THEME.get(candidate.name_ko, "a life theme read from the dominant month-branch ten-god")
    return (
        f"The engine flags a likely **{candidate.name_ko} ({candidate.name_en})** as the regular grid. "
        f"This points toward a life theme shaped by {theme}. "
        f"It is a structural tendency, not a career verdict; the ten-god distribution and timing tables refine how it expresses."
    )


def special_grid_note(ctx) -> str:
    """Cautious paragraph if a transformation (화격) or follower (종격) grid is flagged.

    Surfaces only candidates the engine already marked as likely/possible.
    The output is explicitly marked [UNCERTAIN] because special-grid rulings are
    strict and require reader verification (knowledge/07-special-formations.md §B).
    """
    chart = _ctx_get(ctx, "chart")
    candidates: List[str] = []
    transformation = chart.patterns.get("transformation_grid") if chart.patterns else None
    if transformation and transformation.get("confidence") in ("likely", "possible"):
        name_ko = transformation.get("name_ko", "화격")
        name_en = transformation.get("name_en", "Transformation Grid")
        basis = transformation.get("basis", "")
        candidates.append(f"**{name_ko} ({name_en})** — {basis}")
    for form in chart.patterns.get("special_forms") or []:
        if form.get("confidence") in ("likely", "possible"):
            name_ko = form.get("name_ko", "종격")
            name_en = form.get("name_en", "Follower Grid")
            basis = form.get("basis", "")
            candidates.append(f"**{name_ko} ({name_en})** — {basis}")
    if not candidates:
        return ""
    body = "; ".join(candidates)
    return (
        f"[UNCERTAIN] The engine flags a special-grid candidate: {body}. "
        "Special-grid rulings are strict; the final verdict requires a reader to verify that all classical preconditions "
        "(Day Master isolation, 득령/in-season support, and absence of breaking stems) are truly met. "
        "If confirmed, the Day Master may behave more like the transformed or followed element, and the favorable element could shift accordingly."
    )


def branch_relationship_snapshot(ctx) -> str:
    """Summarize the most prominent natal branch relationship and the palaces it touches.

    Ranks heavier structural pressures higher (three punishment > clash > self punishment
    > harm/break > combination/harmony). Uses `_PILLAR_AREAS` for domain language.
    Returns an empty string if no branch relationship is present.
    """
    chart = _ctx_get(ctx, "chart")

    def _positions_for(branches: List[str]) -> List[str]:
        """Map each branch to the first matching pillar position/domain."""
        positions = ["year", "month", "day", "hour"]
        result = []
        seen_pos = set()
        for br in branches:
            for pos, natal in zip(positions, chart.branches):
                if natal == br and pos not in seen_pos:
                    seen_pos.add(pos)
                    result.append(_PILLAR_AREAS.get(pos, pos))
                    break
        return result

    if chart.three_punishments:
        a, b, c, label = chart.three_punishments[0]
        domains = _positions_for([a, b, c])
        domains_str = " and ".join(domains) if domains else "multiple life palaces"
        if c == "—":
            # Partial punishment: two branches of a 삼형 frame, third absent
            # (matches skeleton.py's rendering convention).
            return (
                f"The most prominent natal branch signal is a **partial 삼형 (Three Punishment)** between "
                f"**{a}** and **{b}** ({label}), touching the {domains_str}. Two branches of a punishment "
                f"frame are present without the third — a lighter but recurring structural pressure; "
                f"its themes mature slowly and tend to recur until they are consciously recognized."
            )
        return (
            f"The most prominent natal branch signal is a **삼형 (Three Punishment)** among **{a}**, **{b}**, "
            f"and **{c}** ({label}), touching the {domains_str}. This is a heavier structural pressure; "
            f"its themes mature slowly and tend to recur until they are consciously recognized."
        )
    if chart.clashes:
        a, c = chart.clashes[0]
        domains = _positions_for([a, c])
        domains_str = " and ".join(domains) if len(domains) == 2 else (domains[0] if domains else "two life palaces")
        return (
            f"The most prominent natal branch signal is a **육충 (Six Clash)** between **{a}** and **{c}**, "
            f"linking the {domains_str}. This brings recurring tension that asks the querent to adjust, "
            f"release, or choose between the two areas rather than hold both in full force."
        )
    if chart.self_punishments:
        b, _ = chart.self_punishments[0]
        domains = _positions_for([b])
        domain = domains[0] if domains else "a life palace"
        return (
            f"The most prominent natal branch signal is a **자형 (Self-Punishment)** of **{b}**, "
            f"appearing more than once in the {domain}. This points to an inner pattern that repeats "
            f"until self-awareness reframes it; it is structural, not a character flaw."
        )
    if chart.six_harms:
        a, c = chart.six_harms[0]
        domains = _positions_for([a, c])
        domains_str = " and ".join(domains) if len(domains) == 2 else (domains[0] if domains else "two life palaces")
        return (
            f"The most prominent natal branch signal is a **육해 (Six Harm)** between **{a}** and **{c}**, "
            f"linking the {domains_str}. This is a quieter friction that can drain energy if the connection is ignored."
        )
    if chart.six_breaks:
        a, c = chart.six_breaks[0]
        domains = _positions_for([a, c])
        domains_str = " and ".join(domains) if len(domains) == 2 else (domains[0] if domains else "two life palaces")
        return (
            f"The most prominent natal branch signal is a **육파 (Six Break)** between **{a}** and **{c}**, "
            f"linking the {domains_str}. This tends to show up as disrupted plans or external adjustments "
            f"between the two palaces involved."
        )
    if chart.combinations_6:
        a, c, elem, pa, pb = chart.combinations_6[0]
        domain_a = _PILLAR_AREAS.get(pa, pa)
        domain_b = _PILLAR_AREAS.get(pb, pb)
        return (
            f"The most prominent natal branch signal is a **육합 (Six Combination)** between **{a}** "
            f"({pa}) and **{c}** ({pb}), transforming toward **{elem}** energy. This links the "
            f"{domain_a} with the {domain_b} — a recurring theme of alliance or mutual shaping that tends "
            f"to reassert itself whenever either palace activates."
        )
    if chart.three_harmonies:
        a, b, c, elem = chart.three_harmonies[0]
        domains = _positions_for([a, b, c])
        domains_str = ", ".join(domains) if domains else "three life palaces"
        return (
            f"The most prominent natal branch signal is a **삼합 (Three Harmony)** among **{a}**, **{b}**, "
            f"and **{c}**, strengthening **{elem}** energy through the {domains_str}. This gathers momentum "
            f"in one element across multiple life areas."
        )
    return ""


def closing_note_short(ctx) -> str:
    """2–3 sentences for Hook/Short closing."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    dm_en = _ctx_get(ctx, "dm_en", "Day Master")
    cls = _dominant_classes(chart, 1)
    gift = f"a strong {cls[0][0].lower()} presence that gives the querent real follow-through" if cls else "a clear and workable Day Master foundation"
    return (
        f"This chart's gift is {gift}; the challenge is staying aware of the chart's pressure points "
        f"rather than letting them run in the background. "
        f"The single most useful next step is to weave the favorable **{fav}** element into daily rhythm — "
        f"through color, direction, season, or practice — so the chart has somewhere to land. "
        f"Treat the rest of this report as a starting place; the best readings come from revisiting the "
        f"same chart across different life phases."
    )


def closing_note_long(ctx) -> str:
    """5–7 sentences referencing 2–3 specific chart features by name."""
    chart = _ctx_get(ctx, "chart")
    dm = _ctx_get(ctx, "dm", "—")
    dm_en = _ctx_get(ctx, "dm_en", "Day Master")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    fav = _ctx_get(ctx, "favorable", "—")
    sup = _ctx_get(ctx, "supporting", "—")
    spouse_branch = chart.day.branch
    cls = _class_counts(chart)
    dominant = _dominant_classes(chart, 2)
    dom_summary = ", ".join(f"{c} ({n})" for c, n in dominant) or "Companion"
    parts = [
        f"**{dm} ({dm_en})** sits at the centre of this chart, with the chart's element balance leaning "
        f"toward **{dm_elem}** and a ten-god distribution dominated by **{dom_summary}**.",
        f"The favorable **{fav}** element (with **{sup}** as the quiet secondary) is the querent's main "
        f"lever — not as a rule to follow, but as a rhythm to listen to.",
        f"The spouse palace **{spouse_branch}** and the chart's relationship dynamics reward the "
        f"querent for showing up consistently rather than performing.",
    ]
    if chart.clashes:
        a, c = chart.clashes[0]
        parts.append(
            f"The natal clash between **{a}** and **{c}** is a recurring pressure; the chart's gift is that "
            f"the querent has already learned how to navigate it — and the favorable element makes the navigation gentler."
        )
    if chart.combinations_6:
        a, c, elem, pa, pb = chart.combinations_6[0]
        parts.append(
            f"The six-combination between **{a}** and **{c}** is a quiet asset — partnerships or projects "
            f"that bring two palaces into harmony, with the querent's role often as the connector."
        )
    parts.append(
        f"Across a full lifetime, this chart rewards the querent who studies their own patterns and "
        f"acts with the favorable element rather than against it. The work is not to fix the chart; "
        f"it is to use what is already there well."
    )
    return " ".join(parts)


# ── Practical-guidance fillers ──────────────────────────────────────────

def top_strengths(ctx) -> List[str]:
    """5 short strength statements."""
    chart = _ctx_get(ctx, "chart")
    dm = _ctx_get(ctx, "dm", "—")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    profile = {
        "甲": "visionary leadership and the ability to set long-term direction",
        "乙": "adaptive persuasion and the ability to bring people along",
        "丙": "radiant presence and the ability to light up a room",
        "丁": "focused warmth and the ability to sustain attention on what matters",
        "戊": "grounding stability and the ability to hold weight without bending",
        "己": "nurturing patience and the ability to make others feel held",
        "庚": "decisive clarity and the ability to cut through confusion",
        "辛": "refined discernment and the ability to notice quality others miss",
        "壬": "broad strategic thinking and the ability to hold complex systems",
        "癸": "quiet persistence and the ability to nourish what others start",
    }.get(dm, "the Day Master's natural strengths")
    cls = _class_counts(chart)
    dominant = _dominant_classes(chart, 3)
    dom_strengths = {
        "Companion": "the ability to collaborate as an equal without losing self",
        "Output": "the ability to create and produce visible work",
        "Direct Wealth": "the ability to hold and grow resources with discipline",
        "Indirect Wealth": "the ability to spot opportunity and move on it",
        "Direct Officer": "the ability to lead through structure and accountability",
        "Seven Killings": "the ability to act decisively under pressure",
        "Direct Resource": "the ability to study deeply and bring expertise",
        "Indirect Resource": "the ability to synthesize across domains and see patterns",
    }
    strengths = [f"**{dm_elem} Day Master strength** — {profile}."]
    for c, _ in dominant[:3]:
        if c in dom_strengths:
            strengths.append(f"**{c}-dominant** — {dom_strengths[c]}.")
    fav = _ctx_get(ctx, "favorable", "—")
    strengths.append(f"**Favorable {fav} responsiveness** — the chart has a clear lever for growth, which not every chart does.")
    if chart.stars and chart.stars.get("noble"):
        strengths.append("**Noble helper presence** — supportive people tend to appear at the right time in this chart.")
    # Pad to 5 with sensible defaults if short
    while len(strengths) < 5:
        strengths.append(f"**Steady practice** — the chart rewards consistent effort over heroic bursts.")
    return strengths[:5]


def top_growth_areas(ctx) -> List[str]:
    """5 growth areas."""
    chart = _ctx_get(ctx, "chart")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    unfav = _ctx_get(ctx, "unfavorable") or "the challenging element"
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    growth = []
    if verdict in ("strong", "extreme"):
        growth.append("**Receive without deflecting** — strong Day Masters often turn help away; practicing receiving builds reserves.")
        growth.append("**Rest as discipline** — output without recovery is the most common failure mode for this chart.")
    elif verdict in ("weak", "extreme_weak"):
        growth.append("**Build slowly** — the chart rewards accumulation over speed; trust the long arc.")
        growth.append("**Protect sleep and meals** — the Day Master's recovery runs through these anchors.")
    else:
        growth.append("**Consistency over intensity** — the chart works best with steady rhythm, not bursts.")
        growth.append("**Rest before the body demands it** — balanced charts deplete quietly; preventive rest is the antidote.")
    growth.append(f"**Boundary-setting** — learning to say no without guilt protects the {dm_elem} Day Master's energy.")
    if _ctx_get(ctx, "unfavorable"):
        growth.append(f"**Working with the unfavorable {unfav} element** — denial amplifies it; conscious engagement contains it.")
    else:
        # Balanced chart: no 기신 named — keep the phrasing, drop the doubled placeholder.
        growth.append("**Working with the chart's challenging element** — denial amplifies it; conscious engagement contains it.")
    growth.append(f"**Asking for help early** — {dm_elem} Day Masters often wait too long before reaching out.")
    return growth[:5]


def practical_recommendations(ctx) -> List[str]:
    """5 concrete recommendations."""
    fav = _ctx_get(ctx, "favorable", "—")
    dm_elem = _ctx_get(ctx, "dm_element", "")
    rec_pool = {
        "Water": [
            "Add a 20-minute evening walk near water 4× a week",
            "Replace one caffeinated drink with a warm herbal tea",
            "Read fiction for 30 minutes before bed — let the mind drift",
            "Keep a quiet hour after work with no screens",
            "Schedule one restorative weekend per quarter",
        ],
        "Wood": [
            "Add a morning walk among trees or in a green space",
            "Plan one learning project (course, book, mentorship) per quarter",
            "Eat leafy greens at 4–5 meals a week",
            "Stretch or practice tai chi three times a week",
            "Journal on growth intentions every Sunday",
        ],
        "Fire": [
            "Take a 15-minute midday sunlight break daily",
            "Schedule one visible creative project each month",
            "Share a meal with company once a week",
            "Practice a daily moment of celebration or laughter",
            "Speak in public or present at least once a quarter",
        ],
        "Earth": [
            "Keep a fixed wake-time and sleep-time, including weekends",
            "Eat warm cooked meals at regular hours",
            "Light journal at every season transition",
            "Spend 30 minutes a week in physical grounding work (gardening, walking, cleaning)",
            "Limit commitments to what can be sustained for a year",
        ],
        "Metal": [
            "Reserve one quiet hour weekly for focused craft (editing, drawing, instrument)",
            "Keep white or silver objects near the workspace",
            "Practice breathwork outdoors in cool air",
            "Run a weekly review and tidy of your most-used space",
            "Declutter one drawer or shelf every Sunday",
        ],
    }
    recs = rec_pool.get(fav, [
        "Anchor a daily rhythm that does not depend on motivation",
        "Protect one quiet hour weekly for reflection",
        "Choose one anchor practice and stay with it for 90 days",
        "Build a weekly review into the calendar",
        "Reach out to one supportive person each week",
    ])
    # Pad/trim to 5
    return recs[:5]


# ── Business launch fillers ─────────────────────────────────────────────

def business_launch_format(ctx) -> str:
    """Best launch format based on Day Master strength + dominant ten-god class."""
    chart = _ctx_get(ctx, "chart")
    cls = _class_counts(chart)
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    if verdict in ("strong", "extreme") and cls.get("Output", 0) >= 1:
        return (
            "**A public campaign with a clear voice** is the most likely fit. Strong Day Masters with "
            "visible Output stems can carry the visibility, and a public launch reads as confidence "
            "rather than risk. Pair it with a small but engaged audience rather than a mass-broadcast feel."
        )
    if verdict in ("weak", "extreme_weak") and cls.get("Output", 0) == 0:
        return (
            "**A quiet beta with a small reference audience** is the safest fit. The Day Master needs "
            "time to learn what the work wants to be before the visibility of a public launch. Treat "
            "the first 60–90 days as a calibration period rather than a sales period."
        )
    if cls.get("Direct Officer", 0) >= 1 or cls.get("Seven Killings", 0) >= 1:
        return (
            "**A partnership or co-launch with one credible counterparty** is the most likely fit. "
            "The Authority ten-god gives the launch a stamp of legitimacy, and a partner carries the "
            "parts the querent's chart cannot carry alone."
        )
    if cls.get("Output", 0) >= 1:
        return (
            "**An evergreen product that lives on its own voice** is the most likely fit. Output-dominant "
            "charts can sustain a long-running artifact (writing, course, content) more easily than "
            "a one-shot campaign."
        )
    return (
        "**A small, values-led launch** is the most likely fit. The chart supports building slowly and "
        "audience-by-audience more than chasing a single big moment."
    )


def business_seasonal_note(ctx) -> str:
    """Which season/quarter favors this Day Master's launches."""
    dm_elem = _ctx_get(ctx, "dm_element", "")
    season = {
        "Wood": "spring (rising Wood energy is when new growth takes root)",
        "Fire": "summer (peak Fire energy supports visible launches)",
        "Earth": "late summer / transitions (Earth stabilizes what is being built)",
        "Metal": "autumn (the harvest, the refinement)",
        "Water": "winter (deep, still Water — best for quiet launches, beta, and writing)",
    }.get(dm_elem, "the Day Master's natural season")
    return (
        f"For a **{dm_elem}** Day Master, the most aligned launch window is **{season}**. "
        f"Outside that window, plan a quieter cadence — audits, refinements, and behind-the-scenes "
        f"infrastructure work — rather than big public pushes. Pushing against the seasonal rhythm "
        f"rarely accelerates the result; it just adds friction."
    )


def business_watch_items(ctx) -> List[str]:
    """5 launch-watch items."""
    chart = _ctx_get(ctx, "chart")
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    items = [
        f"**Annual branches that clash your natal day branch {chart.day.branch}** — these tend to "
        f"bring unexpected pivots; launch a soft beta, not a public campaign.",
        "**Annual pillars dominated by the unfavorable element** — favour audits, refinements, and "
        "quiet product work over big announcements.",
        "**A major-luck shift into a heavier stem (strong 정관 / 편관)** — use the first 1–2 years "
        "to set up systems rather than scale headcount.",
        "**Activated chart-punishment or self-punishment patterns during the launch year** — keep "
        "partnerships small and written, not verbal.",
        "**Conjunction of new-moon or full-moon eclipses falling on spouse-palace or wealth-stem "
        "branches** — defer the launch by 30–45 days if it lands on the public date.",
    ]
    if verdict in ("strong", "extreme"):
        items.append(
            "**Over-confidence from a strong Day Master** — pause to get one external review before "
            "committing dates, since a strong chart can talk itself into commitments too quickly."
        )
    return items[:5]


# ── Travel / Relocation filler ──────────────────────────────────────────

def travel_timing(ctx) -> str:
    """When travel is most aligned with the chart."""
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "—")
    favorable_periods = [
        f"ages {p.start_age}-{p.end_age} ({p.combined})"
        for p in chart.daeun
        if period_favorable_status(p, ctx) == "favorable"
    ]
    if favorable_periods:
        return (
            f"Travel and relocation are most likely to feel aligned during the favorable **{fav}**-element "
            f"years and months, and especially during major-luck periods: {', '.join(favorable_periods[:3])}. "
            f"Relocations outside those windows may bring temporary benefit but require more adjustment; "
            f"plan for a longer settling-in period rather than expecting instant payoff."
        )
    return (
        f"Travel is most aligned during years and months whose stem element matches the favorable "
        f"**{fav}** element. Outside those windows, travel brings useful perspective but rarely the "
        f"lasting lift the favorable element would offer."
    )


# ── "In plain words" section callouts (Track A plain-language layer) ──────
# Each returns a single-line blockquote `"> **In plain words:** …"` derived from
# the same chart facts the surrounding section uses, or `""` when the needed
# fact is absent. Citations are deliberately omitted — these are the lay
# restatement, and the section itself carries the knowledge/ references.

_CAREER_DRIVERS: Dict[str, str] = {
    "Wealth": "earning by owning and growing resources — business, sales, deals",
    "Output": "earning by making and expressing — creating, teaching, building",
    "Authority": "earning inside structure — institutions, management, licensed roles",
    "Resource": "earning through knowledge — research, advice, credentialed practice",
    "Companion": "earning alongside peers — teams, partnerships, independent practice",
}

# fine-grained _class_counts label -> coarse driver
_CLASS_TO_DRIVER: Dict[str, str] = {
    "Direct Wealth": "Wealth", "Indirect Wealth": "Wealth",
    "Output": "Output",
    "Direct Officer": "Authority", "Seven Killings": "Authority",
    "Direct Resource": "Resource", "Indirect Resource": "Resource",
    "Companion": "Companion", "Robber": "Companion",
}

_TEN_GOD_PLAIN: Dict[str, str] = {
    "Wealth": "money, assets, and the practical world",
    "Output": "what you make, say, and put out",
    "Authority": "rules, status, and the structures you work inside",
    "Resource": "learning, support, and what refills you",
    "Companion": "peers, rivals, and how you hold your own",
}

_SPOUSE_PLAIN: Dict[str, str] = {
    "Companion": "a partner who feels like an equal — independence and closeness held in balance",
    "Robber": "a lively, sometimes competitive partner who keeps you on your toes",
    "Output": "a partner you do and make things with — shared projects over convention",
    "Direct Wealth": "a steady, practical partner where everyday care reads as love",
    "Indirect Wealth": "a varied, opportunity-minded partner who resists rigid routine",
    "Direct Officer": "a reliable partner with clear roles and mutual respect",
    "Seven Killings": "an intense, direct partner; strong personalities show up here",
    "Direct Resource": "a protective, grounding partner who offers rest",
    "Indirect Resource": "an unusual, insight-driven partner who teaches you things",
}


def _spouse_driver(chart) -> str:
    for hit in chart.ten_gods:
        if hit.position == "day_branch_main":
            return _TENGOD_CLASS.get(hit.tengod, "")
    return ""


def plain_words_day_master(ctx) -> str:
    dm_el = _ctx_get(ctx, "dm_element", "")
    strength = (_ctx_get(ctx, "strength_label", "") or "").lower()
    fav = _ctx_get(ctx, "favorable", "")
    image = {
        "Wood": "a growing tree — you push upward and branch out",
        "Fire": "a flame — you light things up and move fast",
        "Earth": "steady ground — you hold, stabilise, and mediate",
        "Metal": "a refined blade — you cut to the point and value quality",
        "Water": "moving water — you adapt, connect, and go deep",
    }.get(dm_el)
    if not image:
        return ""
    return _plain(
        f"At your core you are {image}. Your chart reads as {strength or 'balanced'}, so the rest of "
        f"this report is about where that helps and where leaning toward "
        f"{fav or 'your favourable element'} keeps you in balance."
    )


def plain_words_career(ctx) -> str:
    chart = _ctx_get(ctx, "chart")
    fav = _ctx_get(ctx, "favorable", "")
    drivers: Counter = Counter()
    if chart is not None:
        for cls, n in _class_counts(chart).items():
            drv = _CLASS_TO_DRIVER.get(cls)
            if drv:
                drivers[drv] += n
    top = max(_CAREER_DRIVERS, key=lambda k: drivers.get(k, 0)) if drivers else "Output"
    return _plain(
        f"Your chart leans toward {_CAREER_DRIVERS[top]}. Fields and decades that carry "
        f"{fav or 'your favourable element'} give the cleanest results; the timing tables show when."
    )


def plain_words_relationships(ctx) -> str:
    chart = _ctx_get(ctx, "chart")
    if chart is None:
        return ""
    driver = _spouse_driver(chart)
    picture = _SPOUSE_PLAIN.get(driver)
    if not picture:
        return ""
    return _plain(
        f"Your partnership area points toward {picture}. Treat this as the weather it tends to "
        f"create, not a description of one person."
    )


def plain_words_health(ctx) -> str:
    chart = _ctx_get(ctx, "chart")
    if chart is None:
        return ""
    pct = _element_pct(chart)
    if not pct:
        return ""
    lightest = min(pct.items(), key=lambda kv: kv[1])[0]
    organs = _ELEMENT_ORGANS.get(lightest, f"the {lightest.lower()}-associated systems")
    return _plain(
        f"Your lightest element is {lightest}, so the {organs} are the natural place to start gentle, "
        f"preventive care — through {lightest.lower()}-aligned food, rest, and seasons. This is a "
        f"balance cue, not a diagnosis."
    )


def plain_words_timing(ctx) -> str:
    current = _ctx_get(ctx, "current_daeun")
    fav = _ctx_get(ctx, "favorable", "your favourable element")
    if current is None:
        return _plain(
            f"Timing works in layers — a roughly ten-year chapter, then the year, then the month. "
            f"Windows that carry {fav} are the ones to act in."
        )
    status = period_favorable_status(current, ctx)
    if "unfavor" in status or "challeng" in status:
        weather = "a headwind decade — steady effort beats big bets right now"
    elif "favor" in status:
        weather = "a tailwind decade — a good stretch to push on the things that matter"
    else:
        weather = "a mixed decade — pick your moments using the year and month tables"
    return _plain(
        f"You are currently in {weather}. Zoom in with the year and month windows that carry {fav}."
    )


def plain_words_pattern(ctx) -> str:
    name = _ctx_get(ctx, "pattern_name", "") or ""
    if not name or name == "Standard chart":
        return ""
    if name.startswith("종격"):
        return _plain(
            "Your chart may be a 'follower' type — it works best by going fully with its strongest "
            "element rather than fighting it. This is a candidate reading, not a settled one."
        )
    if name.startswith("화격"):
        return _plain(
            "Your chart may be a 'transformation' type — two parts combine and shift its centre of "
            "gravity. This is a candidate reading, not a settled one."
        )
    ko = name.split(" / ")[0].strip()
    theme = _REGULAR_GRID_THEME.get(ko)
    if not theme:
        return ""
    return _plain(f"The chart's organising theme is {theme}.")


def plain_words_ten_gods(ctx) -> str:
    chart = _ctx_get(ctx, "chart")
    if chart is None:
        return ""
    drivers: Counter = Counter()
    for cls, n in _class_counts(chart).items():
        drv = _CLASS_TO_DRIVER.get(cls)
        if drv:
            drivers[drv] += n
    if not drivers:
        return ""
    ranked = [d for d, _ in drivers.most_common()]
    top = ranked[0]
    thin = [d for d in _TEN_GOD_PLAIN if drivers.get(d, 0) == 0]
    tail = ""
    if thin:
        tail = f" Light on {_TEN_GOD_PLAIN[thin[0]]} — that area asks for more deliberate attention."
    return _plain(
        f"Where your chart puts its weight: most of all on {_TEN_GOD_PLAIN[top]}.{tail}"
    )


