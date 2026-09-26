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
# Bug found 2026-09-20 (external report review, 3rd pass): 식신/상관 used to
# both map to a single merged "Output" key here, while every other class
# stayed split by yin/yang variant (Companion/Robber, Direct/Indirect Wealth,
# Direct Officer/Seven Killings, Direct/Indirect Resource) — an inconsistent
# grouping level that both inflated "Output"'s count in variant-level
# comparisons (`_dominant_classes`) and silently mismatched every dict here
# keyed by the class name, since `sewoon.py`/`daeun_overlay.py` already use
# "Eating God"/"Hurting Officer" as the canonical English names (so any
# tengod string sourced from those modules, e.g. `stem_tengod_en` in a 세운
# table, never matched a dict entry keyed "Output"). Split them to match the
# existing convention and the other four classes' split-by-variant shape.
_TENGOD_CLASS: Dict[str, str] = {
    "비견": "Companion", "겁재": "Robber",
    "식신": "Eating God", "상관": "Hurting Officer",
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
    supporting = _ctx_get(ctx, "supporting")
    unfavorable = _ctx_get(ctx, "unfavorable")
    # Bug found 2026-09-20 (external report review, 3rd pass): this used to
    # check only `favorable`, not `supporting`, while the sibling annual-year
    # check (`annual_window_row`) checks `elem in {fav, sup}` — a genuine
    # inconsistency between this function (introduced 2026-09-19) and the
    # pre-existing annual logic. Confirmed live: Harish's 40-49 decade
    # (庚戌, stem Metal = 희신) was labelled "neutral" by this function while
    # the 2030 (庚戌) YEAR inside that same decade, sharing the identical
    # qualifying element, was labelled a "favorable-element year" by the
    # annual check — a direct, client-visible contradiction between two
    # tables describing the same period.
    fav_hit = (favorable is not None and favorable in hits) or (supporting and supporting in hits)
    unfav_hit = bool(unfavorable) and unfavorable in hits
    # F-7 (2026-09-26 audit): a period whose stem matches the favorable
    # element but whose branch matches the unfavorable one (or vice versa)
    # used to report flatly "favorable" (checked first, unconditionally),
    # discarding the conflicting signal. Both hitting at once is a wash.
    if fav_hit and unfav_hit:
        return "neutral"
    if fav_hit:
        return "favorable"
    if unfav_hit:
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


def _grouped_dominant_classes(chart, n: int = 2) -> List[Tuple[str, int]]:
    """Dominant 십신 classes at the proper 5-group level (비겁/식상/재성/관성/인성).

    Bug found 2026-09-20 (external report review): `_class_counts` /
    `_dominant_classes` mix grouping levels — 식상 is pre-merged into one
    "Output" key, but 비겁/재성/관성/인성 are each kept split by yin/yang
    variant (Companion/Robber, Direct/Indirect Wealth, Direct Officer/Seven
    Killings, Direct/Indirect Resource). Calling `.most_common()` on that mix
    compares a class-level count against variant-level counts and can name a
    tied or even non-leading variant as "dominant." Confirmed live: Harish's
    real class distribution is 비겁 4, 식상 4, 인성 4 (a three-way tie), 재성 2,
    관성 1 — but `_dominant_classes` reported "Output (4), Robber (2)" (dropping
    two of the three tied leaders and surfacing a class that isn't even in
    the true top tier), while a SEPARATE function elsewhere concluded
    "Direct Resource-dominant" from the same chart — two different,
    inconsistent claims about what dominates the same ten-god profile.

    This reuses the existing `_CLASS_TO_DRIVER` re-grouping (already used
    correctly elsewhere in this file, e.g. `skill_levers`'s sibling driver
    tally) rather than inventing a new grouping scheme.

    E-12 (2026-09-25 audit): a plain ``most_common(n)`` still truncated
    ties — Harish's three-way 4/4/4 tie surfaced as "Output (4), Companion
    (4)", hiding Resource (4) while career.md called it a three-way tie. Any
    class tied with the n-th entry is now included, so the result may be
    longer than ``n``.
    """
    grouped: Counter = Counter()
    for cls, n_hits in _class_counts(chart).items():
        driver = _CLASS_TO_DRIVER.get(cls, cls)
        grouped[driver] += n_hits
    ranked = grouped.most_common()
    if len(ranked) <= n or n <= 0:
        return ranked[:max(n, 0)] if n <= 0 else ranked
    cutoff = ranked[n - 1][1]
    return [(c, k) for c, k in ranked if k >= cutoff]


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


def _season_signal(month_stage_score: float) -> str:
    """Classify a 12운성 month-stage score as supported / depleted / mixed.

    Bug found 2026-09-20 (own find, while implementing R17's strength
    reasoning): `strength.py::_STAGE_WEIGHT` scores range 0.0-2.0 and are
    NEVER negative (see its own comment: "제왕/건록/관대/장생 are supportive,
    사/묘/절 are depleted" — the depleted stages score exactly 0.0, not a
    negative number). The threshold `<= -0.5` used here and in
    `dm_arrival_narrative` could therefore never fire, so a Day Master at
    사/절/병 (score 0.0-0.2) was always mis-bucketed as "mixed seasonal
    support" instead of depleted — confirmed live: Harish's 辛 at 사 (0.0)
    in 巳 read as "mixed" when knowledge/06 calls 사 an ending/depleted stage.
    """
    if month_stage_score >= 1.2:
        return "supported"
    if month_stage_score <= 0.3:
        return "depleted"
    return "mixed"


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
    sa.get("month_stage", stage)
    # Use the engine's month-stage score as a second signal, if present.
    month_stage_score = sa.get("month_stage_score", 0.0)
    season_signal = {
        "supported": "seasonally supported", "depleted": "seasonally depleted",
        "mixed": "mixed seasonal support",
    }[_season_signal(month_stage_score)]

    return (
        f"Your Day Master **{chart.day_master}** meets the month branch **{chart.month.branch}** "
        f"at the **{stage} ({label})** twelve-stage — {description}. "
        f"This is read as a {season_signal} arrival: a tendency in how the querent's core energy "
        f"first enters the world, not a fixed early-life outcome."
    )


def strength_reasoning(ctx) -> str:
    """One-sentence argument for the strength verdict (season, hidden-stem
    support, drain) — the reasoning block knowledge/10-output-template
    requires alongside the bare verdict label.

    Bug found 2026-09-20 (external report review, 3rd pass): the Quick
    Reference used to state only the verdict ("Balanced — a
    seasonal-strength reading") with no argument for it, even though
    `strength_assessment` already carries every input the argument needs —
    confirmed live: Harish's 辛 sits at 사 (death/depleted, per
    knowledge/06-twelve-stages.md) in the 巳 month, a seasonally weak
    baseline, which the chart's Earth/Metal (resource + peer) support then
    offsets back to balanced; the report never stated this mechanism.
    """
    chart = _ctx_get(ctx, "chart")
    sa = chart.strength_assessment or {}
    stage = sa.get("month_stage", "—")
    _, description = _STAGE_TENDENCY.get(stage, ("mixed", "the month branch gives a mixed signal"))
    month_stage_score = sa.get("month_stage_score", 0.0)
    season_note = {
        "supported": "a seasonally supported baseline", "depleted": "a seasonally weak baseline",
        "mixed": "a mixed seasonal baseline",
    }[_season_signal(month_stage_score)]
    self_score = sa.get("self_score", 0.0)
    resource_score = sa.get("resource_score", 0.0)
    drain_score = sa.get("drain_score", 0.0)
    support = self_score + resource_score
    skewed = False
    if support > drain_score * 1.3:
        offset_note = "peer and resource support (visible and hidden stems) outweighs the output/wealth/authority drain"
        skewed = True
    elif drain_score > support * 1.3:
        offset_note = "the output/wealth/authority drain outweighs the peer and resource support"
        skewed = True
    else:
        offset_note = "peer/resource support and the output/wealth/authority drain sit close to even"
    # Bug found 2026-09-25 (external report review, E-4): for a chart whose
    # overall verdict is "Balanced," a bare, unqualified skew statement here
    # ("the drain outweighs the support") reads as flatly contradicting the
    # verdict label a few words earlier — confirmed live: Harish's support
    # (2.8) and drain (4.1) are genuinely ~46% apart, but total_score also
    # includes the month-stage term (weight 1.5), which is what actually
    # pulls the total back into the balanced band despite that skew. Say so
    # explicitly rather than leaving the reader to reconcile "Balanced" with
    # a sentence that, read alone, sounds unbalanced. Strong/weak charts are
    # unaffected — there, a skew in the verdict's own direction reinforces
    # rather than contradicts the label, so no reconciling clause is needed.
    reconcile = ""
    if skewed and sa.get("verdict") == "balanced":
        reconcile = (
            " — the month-branch stage above (weighted more heavily in the overall formula) "
            "is what pulls the total back into the balanced range despite that skew"
        )
    return (
        f"the Day Master's stage in the month branch **{chart.month.branch}** is **{stage}** "
        f"({season_note}, per knowledge/06-twelve-stages.md) — {description} — and {offset_note}{reconcile}."
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
    output = cls.get("Eating God", 0) + cls.get("Hurting Officer", 0)
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
    # Whether 정재 (Direct Wealth) specifically appears on a VISIBLE stem —
    # "rooted" classically describes a visible stem reinforced by a matching
    # hidden stem in a branch, so this check is a precondition for that
    # claim, not the hidden-only case handled separately below.
    direct_wealth_visible = any(
        L.ten_god(chart.day_master, s) == "정재" for s in chart.stems
    )
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
    if direct and direct_wealth_visible and wealth_rooted:
        return (
            "Income tends to arrive in **steady increments** — a salaried baseline, retainer work, or "
            "recurring contracts. The Direct Wealth stem is rooted in a branch, so the source is durable "
            "and the rhythm is rarely interrupted by surprise windfalls."
        )
    if direct and direct_wealth_visible:
        return (
            "Income tends to arrive in **steady increments** — a salaried baseline, retainer work, or "
            "recurring contracts. The Direct Wealth stem is visible but not echoed in a branch, so the "
            "source is real but may need more conscious maintenance to stay durable."
        )
    if direct:
        # Bug found 2026-09-19 (external report review, 2nd pass): this
        # branch used to be unreachable in practice — `direct` alone (no
        # visibility check) fell straight into the "steady increments...
        # rooted in a branch" text above even when the only 정재 in the
        # chart was a HIDDEN stem with no visible counterpart at all (e.g.
        # Harish: hidden 甲 in 亥, no visible 정재 anywhere) — a specific,
        # false "rooted" claim about a stem that doesn't visibly exist.
        return (
            "The chart carries **Direct Wealth only as a hidden stem** — real, but latent rather than "
            "actively expressed. Income from a steady, earned source is structurally present but may "
            "need a deliberate channel (a role, a contract, a platform) to become visible and regular."
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
    _class_counts(chart)
    dominant = _dominant_classes(chart, 1)
    dom_class = dominant[0][0] if dominant else "Companion"
    skill_pool = {
        "Companion": ["peer collaboration", "team facilitation", "honest self-assessment"],
        "Robber": ["competitive positioning", "negotiation", "boundary-setting"],
        "Eating God": ["craft refinement", "creative production", "steady output routines"],
        "Hurting Officer": ["written or verbal communication", "sharp critique", "presentation craft"],
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
            "**Large institutions and mid-size specialists** are the most likely fit. The Direct Officer influence "
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
    sa.get("verdict", "balanced")
    # Keyed to the manager who embodies the chart's 용신 itself. Validation
    # 2026-09-25 #5: this used to map each 용신 to the element that CONTROLS
    # it (Water → "Earth anchor", Fire → "Water advisor", …) — i.e. the 구신
    # — contradicting the same report's Avoid/Watch line.
    complement = {
        "Wood": "visionary Wood leader",
        "Fire": "warm Fire motivator",
        "Earth": "steady Earth mentor",
        "Metal": "structured, precise Metal manager",
        "Water": "patient, perceptive Water advisor",
    }.get(fav, "complementary-element mentor")
    warning = {
        "Wood": "constant crisis mode that fragments Wood's growth",
        "Fire": "cold isolation that starves Fire's warmth",
        "Earth": "rapid change that erodes Earth's stability",
        "Metal": "vague goals that blunt Metal's precision",
        "Water": "rigid rules that dam Water's flow",
    }.get(dm_elem, "environments that ignore the Day Master's nature")
    return (
        f"The ideal manager profile is a **{complement}** — someone who carries your favorable **{fav}** "
        f"element, supplying what the chart needs rather than competing with your Day Master. Watch for {warning}; this is the most common way the querent's "
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
    # Bug found 2026-09-25 (external report review, E-3 follow-up): a naive
    # `"favor" in status` substring check matches "unfavorable" too (it
    # contains "favor"), so a genuinely unfavorable decade was silently
    # mislabeled "build and rise". Unreachable before the E-3 fix
    # (period_favorable_status could never actually return "unfavorable"
    # for a balanced/climate-gated chart), and confirmed to fire the moment
    # it could — exact-match against the function's only 3 return values
    # instead of substring-matching.
    if status == "favorable":
        phase = "build and rise"
        guidance = "Plant several seeds at once — the chart can carry more than one initiative in this window."
    elif status == "unfavorable":
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
        "Eating God": "you express affection through doing — cooking, building, fixing — not always through words.",
        "Hurting Officer": "you express affection candidly, sometimes bluntly, and want a partner who can take direct feedback.",
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
    base += " " + gendered_spouse_star_note(ctx)
    return base


# Bug found 2026-09-25 (external report review, E-8): this section read only
# the spouse palace's main hidden stem, ignoring gender entirely — per
# 자평진전's gendered spouse-star mapping (knowledge/11-gunghap.md §G,
# already applied for compatibility readings via
# compat.py::_gendered_spouse_star_note), a male chart's actual spouse
# indicator is 재성 (wealth star) wherever it appears, and a female chart's
# is 관성 (officer star) — not exclusively the day branch's main hidden
# stem. This is the single-chart counterpart of that compat.py function.
def gendered_spouse_star_note(ctx) -> str:
    """Name where the querent's classical gendered spouse-star sits, if present."""
    chart = _ctx_get(ctx, "chart")
    gender = chart.gender
    if gender not in ("M", "F"):
        return ""
    from .compat import _HUSBAND_STARS, _WIFE_STARS
    target = _WIFE_STARS if gender == "M" else _HUSBAND_STARS
    star_label = "처성 (재성, wife star)" if gender == "M" else "부성 (관성, husband star)"
    hits = [hit for hit in chart.ten_gods if hit.tengod in target]
    if not hits:
        return (
            f"No **{star_label}** appears anywhere in the natal chart (visible or hidden) — the classical "
            "gendered spouse-star indicator is simply absent here, not a negative signal on its own; the "
            "spouse-palace reading above still applies *(see knowledge/11-gunghap.md §G)*."
        )
    positions = ", ".join(f"**{hit.stem}** ({hit.position.replace('_', ' ')})" for hit in hits)
    in_palace = any(hit.position.startswith("day_branch") for hit in hits)
    palace_note = " — including the spouse palace itself, a classically stronger placement" if in_palace else ""
    return (
        f"By 자평진전's gendered spouse-star convention, your **{star_label}** appears at {positions}{palace_note} "
        "*(see knowledge/11-gunghap.md §G)*."
    )


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
        "Eating God": "a creative, doing-oriented partnership; shared projects and quiet craft matter more than convention",
        "Hurting Officer": "a candid, expressive partnership; direct conversation and shared creative output matter more than convention",
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


_RELATIONSHIP_THEME_NEUTRAL: Dict[str, str] = {
    "Direct Officer": "structure and accountability in relationships and partnerships",
    "Seven Killings": "intensity and transformation — expect a relationship to demand change",
    "Direct Wealth": "stability and value-sharing — good for settling into a long-term rhythm",
    "Indirect Wealth": "variety and social expansion — meeting new people, diversifying the social circle",
    "Eating God": "creative expression together — shared projects, craft, or quiet collaboration",
    "Hurting Officer": "candid expression together — direct conversation, art, or public collaboration",
    "Direct Resource": "support and study — a partner who mentors or grounds you",
    "Indirect Resource": "intuition and surprise — a relationship that teaches you something unexpected",
    "Companion": "peer energy — friendships and partnerships strengthen",
    "Robber": "competition or boundary-setting — be clear about what you will and will not negotiate",
}


def relationship_timing_row(year: int, pillar: str, tengod: str, gender: Optional[str] = None) -> str:
    """1-line theme for a relationship-timing year (2026–2031).

    The marriage/commitment-coded ten-god is GENDER-DEPENDENT per the
    classical 자평진전 spouse-star convention already used elsewhere in this
    project (see `compat.py::_gendered_spouse_star_note`, sourced from
    `knowledge/11-gunghap.md` §G): for a male Day Master the spouse
    (wife) indicator is 재성 (Wealth — 정재/편재), not 관성; for a female
    Day Master it is 관성 (Officer — 정관 positive, 편관 read with caution),
    matching 명리정종's "남성에게는 정재·편재 모두 긍정, 여성에게는 정관 긍정
    / 편관 부정."

    Bug found 2026-09-19 (external report review, 2nd pass): this function
    used to hard-code "Direct Officer -> engagement, marriage, formal
    commitment" for every chart regardless of gender — a template built for
    a female querent, applied unchanged to a male one (confirmed live in
    Harish's report). When gender is unknown, the gendered read is declined
    (matching the compat.py convention) and a neutral theme is used instead.
    """
    from . import lookup as L
    # Look up the year's stem element from the pillar's first char (stem).
    stem = pillar[:1] if pillar else "—"
    elem = L.STEM_INFO.get(stem, {}).get("element", "—")
    class_theme = dict(_RELATIONSHIP_THEME_NEUTRAL)
    if gender == "M":
        class_theme["Direct Wealth"] = "structure and visible milestones (engagement, marriage, formal commitment)"
        class_theme["Indirect Wealth"] = "a relationship-opportunity year — meeting a partner through new circles, or a lower-commitment variety phase"
    elif gender == "F":
        class_theme["Direct Officer"] = "structure and visible milestones (engagement, marriage, formal commitment)"
        class_theme["Seven Killings"] = "intensity or pressure in a relationship — per 명리정종, 편관 years read with more caution than 정관 for a female Day Master; not automatically a commitment year"
    theme = class_theme.get(tengod, "a year that asks the relationship to evolve quietly")
    return f"**{elem}** energy + {tengod}: {theme}."


def friendship_social_energy(ctx) -> str:
    """3–4 sentences on friendship energy."""
    chart = _ctx_get(ctx, "chart")
    _class_counts(chart)
    fav = _ctx_get(ctx, "favorable", "—")
    unfav = _ctx_get(ctx, "unfavorable") or "the challenging element"
    dominant = _grouped_dominant_classes(chart, 2)
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


def _spouse_stage_clause(stage: str) -> str:
    """Name the spouse-palace stage's own group (knowledge/06-twelve-stages.md
    §strongest/weakest stages). E-12 (2026-09-25 audit): this used to be a
    fixed sentence contrasting "절/병/사" with "묘/관/충" — 충 is not one of
    the twelve stages, and 절/병/사 are weak stages, not "vitality" ones.
    """
    strong = {"장생", "목욕", "관대", "건록", "제왕"}
    weak = {"쇠", "병", "사", "묘", "절"}
    if stage in strong:
        return (f"The **{stage}** stage is one of the supported (strong) stages, so the querent tends to "
                f"bring energy and presence into the bond.")
    if stage in weak:
        return (f"The **{stage}** stage is one of the unsupported (weak) stages, so the querent tends to "
                f"lean toward reserve and selectivity in the bond.")
    if stage in {"태", "양"}:
        return (f"The **{stage}** stage is a transitional (mixed) stage — neither peak nor decline — so the "
                f"bond's energy reads as still forming rather than fixed.")
    return ""


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
        f"and discernment. {_spouse_stage_clause(stage)} The hidden-stem "
        f"ten-gods colour the undercurrent — Resource leans into safety, Output into creative play, "
        f"Wealth into stability. Read this as the emotional baseline; the 대운/세운 overlays show when "
        f"the querent's bond patterns shift most."
    )


def _marriage_year_signals(
    h, day_branch: str, gender: str, void: Tuple[str, ...] = ()
) -> Tuple[int, List[str], List[str]]:
    """Score one 세운 for commitment timing per knowledge/08-luck-pillars.md
    Part 5b: spouse star in the annual stem, 육합/삼합 into the spouse palace,
    minus 충/형/파 on the palace and the gendered obstruction (상관 for F,
    겁재 for M). Returns (score, positives, negatives)."""
    spouse_class = "Wealth" if gender == "M" else "Authority"
    obstruction = "겁재" if gender == "M" else "상관"
    pos: List[str] = []
    neg: List[str] = []
    score = 0
    if _TENGOD_FIVE_CLASS.get(h.stem_tengod) == spouse_class:
        score += 2
        pos.append(f"{h.stem_tengod} spouse-star year")
    rels = {rel for _a, nb, rel in (h.activated_branches or []) if nb == day_branch}
    if "combine" in rels:
        score += 2
        pos.append(f"{h.branch}{day_branch} 육합 into the spouse palace")
    for hc in getattr(h, "harmony_completions", []) or []:
        if hc.kind == "삼합" and day_branch in hc.matched_natal:
            score += 1
            pos.append(f"{''.join(hc.triad)} 삼합 through the spouse palace")
            break
    bad = rels & {"clash", "punish", "break", "self_punish"}
    if bad:
        score -= 2
        neg.append(f"{h.branch}{day_branch} " + "/".join(
            {"clash": "충", "punish": "형", "break": "파", "self_punish": "자형"}[r] for r in sorted(bad)
        ) + " on the spouse palace")
    if h.stem_tengod == obstruction:
        score -= 1
        neg.append(f"{obstruction} year")
    if h.branch in void:
        # 공망 dampens rather than blocks (knowledge/08 §공망 years): noted,
        # not scored, so it never hides an otherwise-converging year.
        neg.append("a void (empty) year, so gains may feel less solid")
    return score, pos, neg


def marriage_timing_windows(ctx) -> str:
    """Deep-only: commitment windows from the spouse star and spouse palace.

    E-8 (2026-09-25 audit): this used to key marriage timing to 용신-element
    decades/years only. It now follows knowledge/08-luck-pillars.md Part 5b:
    the gendered spouse star (재성 for men, 관성 for women) in the 대운 opens
    a window and in the 세운 selects the year; a 육합/삼합 into the day
    branch (spouse palace) strengthens it; 충/형/파 on the palace and the
    classical obstruction (상관 / 겁재) weaken it. Without a recorded gender
    the spouse star is undefined, so it falls back to the 용신-decade reading.
    """
    chart = _ctx_get(ctx, "chart")
    current = _ctx_get(ctx, "current_daeun")
    daeun = chart.daeun
    if not daeun:
        return "Major-luck data not available; defer to the annual timing tables."
    gender = getattr(chart, "gender", None)
    if gender not in ("M", "F"):
        return _marriage_timing_fallback(ctx)

    from . import sewoon as SE
    from datetime import datetime
    ref = chart.reference_date_obj() if hasattr(chart, "reference_date_obj") else None
    start_year = (ref or datetime.now().date()).year
    day_branch = chart.day.branch
    spouse_class = "Wealth" if gender == "M" else "Authority"
    star_label = "재성 (wife star)" if gender == "M" else "관성 (husband star)"

    # Decade windows: current + next 대운 whose stem carries the spouse star
    # or whose branch binds the spouse palace.
    try:
        cur_idx = next(i for i, p in enumerate(daeun) if current and p.combined == current.combined)
    except StopIteration:
        cur_idx = 0
    decade_notes = []
    for p in daeun[cur_idx:cur_idx + 2]:
        why = []
        if _TENGOD_FIVE_CLASS.get(p.stem_tengod) == spouse_class:
            why.append(f"{p.stem_tengod} spouse-star stem")
        if any(nb == day_branch and rel == "combine" for _a, nb, rel in (p.activated_branches or [])):
            why.append(f"{p.branch}{day_branch} 육합 into the spouse palace")
        if why:
            decade_notes.append(f"**{p.combined}** (ages {p.start_age}-{p.end_age}: {', '.join(why)})")

    hits = SE.build_sewoon_range(
        chart.day_master, chart.branches, start_year, start_year + 9, natal_stems=chart.stems
    )
    scored = []
    cautions = []
    for h in hits:
        score, pos, neg = _marriage_year_signals(h, day_branch, gender, tuple(_void_branches(chart)))
        if score >= 2 and pos:
            detail = ", ".join(pos) + (f"; offset by {', '.join(neg)}" if neg else "")
            scored.append((score, h.year, f"**{h.year} {h.combined}** ({detail})"))
        elif neg and not pos:
            cautions.append(f"{h.year} ({', '.join(neg)})")
    scored.sort(key=lambda t: (-t[0], t[1]))
    top = [t[2] for t in scored[:3]]

    parts = [
        f"Commitment timing is read from your **{star_label}** and your spouse palace **{day_branch}** "
        f"(the day branch) *(see knowledge/08-luck-pillars.md Part 5b)*."
    ]
    if decade_notes:
        parts.append("Major-luck windows that open the theme: " + "; ".join(decade_notes) + ".")
    else:
        parts.append(
            "Neither the current nor the next major-luck period carries the spouse star or binds the "
            "spouse palace, so the annual years below carry more of the weight."
        )
    if top:
        parts.append("The years where the most signals converge: " + "; ".join(top) + ".")
    else:
        parts.append("No year in the next decade combines the spouse star with a spouse-palace bond.")
    if cautions:
        parts.append(
            "Years better suited to deepening privately than to formalising: " + "; ".join(cautions[:3]) + "."
        )
    parts.append(
        "These are tendencies for when the theme is most active — not predictions of an event."
    )
    return " ".join(parts)


def _marriage_timing_fallback(ctx) -> str:
    """Pre-E-8 reading, kept for charts with no recorded gender: 용신 decades."""
    chart = _ctx_get(ctx, "chart")
    current = _ctx_get(ctx, "current_daeun")
    daeun = chart.daeun
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
        f"the cleanest moments to formalize; clash years are better for deepening privately. (No gender "
        f"is recorded for this chart, so the classical spouse-star reading cannot be applied.)"
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
    _ctx_get(ctx, "chart")
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
        + "(its seasons, foods, and rhythms) are the simplest countermeasure."
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
    sa.get("verdict", "balanced")
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
        f"In the daily cycle, the {fav} hours (by the twelve branch hours) are the most aligned — "
        f"{_ELEMENT_HOURS.get(fav, 'the favorable element’s branch hours')}."
    )


# Element → its branch double-hours (시진). Earth owns the four transition
# branches 辰戌丑未. Replaces a loose "mornings/evenings" gloss that
# contradicted the Lucky Card's exact 21:00–01:00 Water window (E-12,
# 2026-09-25 audit) and wrongly attributed the hours to the Twelve Stages.
_ELEMENT_HOURS: Dict[str, str] = {
    "Wood": "寅卯 hours, 03:00–07:00",
    "Fire": "巳午 hours, 09:00–13:00",
    "Earth": "the transition hours 辰戌丑未 (07–09, 13–15, 19–21, 01–03)",
    "Metal": "申酉 hours, 15:00–19:00",
    "Water": "亥子 hours, 21:00–01:00",
}


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
    _ctx_get(ctx, "unfavorable") or "the challenging element"
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
    _ctx_get(ctx, "chart")
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
        # Exact match, not substring — see decade_career_strategy's E-3
        # follow-up note; "favor" in status also matches "unfavorable".
        if status == "favorable":
            supportive_periods.append(f"ages {p.start_age}-{p.end_age} ({p.combined})")
        elif status == "unfavorable":
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
    # Exact match — see decade_career_strategy's E-3 follow-up note.
    favorable = status == "favorable"
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
    period_favorable_status(p, ctx)
    fav = _ctx_get(ctx, "favorable", "—")
    cls = _TENGOD_FIVE_CLASS.get(p.stem_tengod, "")
    # E-12 (2026-09-25 audit): every non-Authority/Wealth/Output decade used
    # to fall through to "support and study" — including 비견/겁재 decades.
    # Keyed to the same five classes as major_luck_theme_row's relationship
    # column so the two never disagree.
    undertow = {
        "Authority": "commitment and visibility",
        "Wealth": "commitment and visibility",
        "Output": "creative exploration",
        "Resource": "support and study",
        "Companion": "peer dynamics, independence, and friendship-based bonds",
    }.get(cls, "shifting priorities")
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
    # Exact match — see decade_career_strategy's E-3 follow-up note.
    favorable = status == "favorable"
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
        + decade_structure_note(current, chart)
    )


def decade_structure_note(p, chart) -> str:
    """Structural drivers of a 대운 against the natal chart: 삼합/방합/삼형
    completions, the Day Master's 12운성 on the decade branch when it is a
    root (건록/제왕), and 천간합/천간충 with natal stems. Validation
    2026-09-25 §2.7: Harish's 己酉 decade completes 巳酉丑 金局 with natal
    巳+丑 and puts 辛 at 건록 — the real reason the decade is supportive —
    but the deep-dive never mentioned it. Returns "" when nothing applies.
    """
    from . import lookup as L
    notes: List[str] = []
    for hc in getattr(p, "harmony_completions", []) or []:
        if hc.status != "full":
            continue
        triad = "".join(hc.triad)
        if hc.kind == "삼형":
            notes.append(f"its **{p.branch}** completes the **{triad} 삼형** with your natal "
                         f"**{''.join(hc.matched_natal)}**, a decade-long friction to manage carefully")
        else:
            notes.append(f"its **{p.branch}** completes the **{triad} {hc.kind} ({hc.element})** with your "
                         f"natal **{''.join(hc.matched_natal)}**, concentrating that element for the whole decade")
    try:
        stage = L.twelve_stage(chart.day_master, p.branch)
    except Exception:
        stage = ""
    if stage in ("건록", "제왕"):
        notes.append(f"your Day Master sits at **{stage}** on **{p.branch}** — a strong root for the self")
    seen_pairs = set()
    for _a, nb, rel in getattr(p, "activated_branches", []) or []:
        if rel in ("clash", "punish") and (nb, rel) not in seen_pairs:
            seen_pairs.add((nb, rel))
            label = "clashes (충) with" if rel == "clash" else "punishes (형)"
            notes.append(f"its **{p.branch}** {label} your natal **{nb}**")
    for c in getattr(p, "stem_combinations", []) or []:
        notes.append(f"its stem **{c['stem_a']}** combines with your natal **{c['stem_b']}** ({c['korean_name']}), "
                     f"tying up what that stem represents")
    for c in getattr(p, "stem_clashes", []) or []:
        notes.append(f"its stem **{c['stem_a']}** clashes with your natal **{c['stem_b']}** (천간충)")
    if not notes:
        return ""
    return "\n\nStructurally, " + "; ".join(notes) + "."


def _void_branches(chart) -> List[str]:
    """The day pillar's 공망 branches (stars._xun_kong), [] if unavailable."""
    try:
        from .stars import _xun_kong
        return list(_xun_kong(chart.day_master, chart.day.branch))
    except Exception:
        return []


def void_year_note(h, chart) -> str:
    """One clause when the 세운 branch is a day-pillar 공망 branch
    (knowledge/08-luck-pillars.md §공망 years)."""
    if chart is None or getattr(h, "branch", "") not in _void_branches(chart):
        return ""
    # "공망 —" (em-dash right after the term) keeps plain_glossary's
    # first-use pass from splicing its gloss mid-phrase.
    return (f"{h.year} falls in your chart's 공망 — a void year ({h.branch} is empty for your day pillar): "
            f"what it brings may feel less solid, so confirm and document gains rather than assuming they will hold.")


def annual_lean(h, ctx) -> Tuple[str, str]:
    """(lean, element) for one 세운, reading both the stem and the branch.

    lean is "favorable" | "supporting" | "challenging" | "neutral". The
    annual stem (the year's outer theme) is checked against the 기신 first,
    then either pillar half against the 용신 / 희신, then the branch against
    the 기신. Validation 2026-09-25 §2.8: keying on the stem alone read
    2029 己酉 (酉 = the Day Master's 건록 Metal) as a plain "mixed" year.
    """
    from . import lookup as L
    stem_el = L.STEM_INFO.get(h.stem, {}).get("element", "")
    branch_el = L.BRANCH_ELEMENT.get(getattr(h, "branch", ""), "")
    fav = _ctx_get(ctx, "favorable", "")
    sup = _ctx_get(ctx, "supporting", "")
    unfav = _ctx_get(ctx, "unfavorable", "")
    if unfav and stem_el == unfav:
        return "challenging", stem_el
    if fav and fav in (stem_el, branch_el):
        return "favorable", fav
    if sup and sup in (stem_el, branch_el):
        return "supporting", sup
    if unfav and branch_el == unfav:
        return "challenging", branch_el
    return "neutral", stem_el


def annual_window_row(h, ctx) -> Tuple[str, str, str]:
    """(overall_theme, best_uses, watch_out_for) for one annual hit."""
    from . import lookup as L
    stem = h.stem
    elem = L.STEM_INFO.get(stem, {}).get("element", "—")
    tg = h.stem_tengod_en or h.stem_tengod or "—"
    lean, lean_elem = annual_lean(h, ctx)
    favorable = lean in ("favorable", "supporting")
    branch_elem = L.BRANCH_ELEMENT.get(getattr(h, "branch", ""), "")
    elem_label = elem if branch_elem in ("", elem) else f"{elem}/{branch_elem}"
    lean_label = {
        "favorable": "favorable-element", "supporting": "supporting-element",
        "challenging": "challenging-element", "neutral": "mixed",
    }[lean]
    theme = f"{elem_label} energy + {tg} — a {lean_label} year."
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
        # Only assert the stronger "drains" language when this year's element
        # matches a chart's specifically-declared 기신 (unfavorable element).
        # Bug found 2026-09-19 (external report review, 2nd pass): this used
        # to fire for ANY non-favorable/supporting year, even for a
        # climate-balanced chart with NO declared 기신 (Quick Reference shows
        # "Avoid / Watch: —") — asserting a specific harm ("drains rather
        # than feeds") the chart never actually claims is a direct
        # contradiction with the empty Avoid/Watch field two sections
        # earlier. A year that is merely neutral (한신, neither favorable nor
        # specifically unfavorable) gets softer language instead.
        if lean == "challenging":
            watch = f"{watch}; the {lean_elem} element drains rather than feeds — slow down"
        else:
            watch = f"{watch}; a neutral year for this chart — steady maintenance over big pushes"
    return theme, best, watch


def year_by_year_note(h, ctx) -> str:
    """2 sentences per year: best focus + one caution.

    E-12 (2026-09-25 audit): focus/caution used to be keyed to the annual
    stem's raw *element* ("Fire → visibility, speaking"), which misreads the
    year for most Day Masters — Fire is 관성 (authority/pressure) for a Metal
    Day Master, not output. They are now keyed to the stem's ten-god class
    relative to the Day Master (knowledge/05-ten-gods.md §five classes), and
    the favorability label separates 용신, 희신 and 기신 years instead of
    calling every 희신 year a "favorable-element year".
    """
    cls = _TENGOD_FIVE_CLASS.get(h.stem_tengod, "")
    focus = {
        "Companion": "independent initiative, peers, and collaboration on equal terms",
        "Output": "expression, creative work, and putting your skills on show",
        "Wealth": "income, practical projects, and managing resources",
        "Authority": "responsibility, structure, and recognition within institutions",
        "Resource": "learning, credentials, and support from mentors",
    }.get(cls, "the chart's natural rhythm")
    caution = {
        "Companion": "watch for competition and friction over shared money",
        "Output": "watch for over-extending yourself or clashing with authority",
        "Wealth": "watch for overreaching or spreading resources too thin",
        "Authority": "watch for pressure, scrutiny, and stress from obligations",
        "Resource": "watch for passivity or leaning too heavily on others",
    }.get(cls, "watch for the chart's natural pressure point")
    lean, lean_elem = annual_lean(h, ctx)
    year_kind = {
        "favorable": f"a **favorable-element ({lean_elem}) year**",
        "supporting": f"a **supporting-element ({lean_elem}) year**",
        "challenging": f"a year of your **challenging element ({lean_elem})** — navigate it consciously",
        "neutral": "an annual energy to navigate consciously",
    }[lean]
    base = (
        f"This is {year_kind} — best focused on {focus}. "
        f"Caution: {caution}; pace yourself rather than pushing through."
    )
    activation = annual_activation_note(h)
    void = void_year_note(h, _ctx_get(ctx, "chart"))
    return " ".join(x for x in (base, activation, void) if x)


_RELATIONSHIP_LABEL: Dict[str, str] = {
    "clash": "충 (clash)", "combine": "합 (combination)",
    "harm": "해 (harm)", "break": "파 (break)", "self_punish": "자형 (self-punishment)",
    "punish": "형 (punishment)",
}


_ELEMENT_HANJA: Dict[str, str] = {"Wood": "木", "Fire": "火", "Earth": "土", "Metal": "金", "Water": "水"}


def annual_activation_note(h) -> str:
    """One clause naming this year's natal-chart activations: a 천간합
    between the annual stem and the Day Master, and/or a branch
    clash/combine/harm/break against a natal branch (knowledge/08 Part 2
    step 3: "Annual stem vs. natal stems -> 합?" / "Annual branch vs. natal
    branches -> 충, 형, 파, 해?").

    Bug found 2026-09-20 (external report review, 3rd pass): the engine
    already computed `SeWoonHit.activated_branches` / `relationship_types`
    for every year but no report prose ever read them, so a genuine
    activation — e.g. 2026's 丙辛합 with the Day Master, or its 丑午 해
    against a natal 丑 hour branch — was silently absent from every report.
    Returns "" when the year carries no activation, so callers can append
    it conditionally without an empty trailing clause.
    """
    notes: List[str] = []
    for stem_a, stem_b, combo_elem, combo_ko in getattr(h, "stem_combinations", []) or []:
        # The combo label (e.g. "병신합수") is annotated with its own Hanja
        # inline here, not left for the general `inject_hanja` pass. Bug
        # found 2026-09-20 (own find, while implementing this function):
        # the label's individual syllables (합=合, and even 병=病 — the
        # Stem "丙" transliteration collides with the unrelated 12운성 term
        # 병=病) are each independently registered in `HANJA_GLOSSARY`, so
        # glossing this string character-by-character mis-annotated it
        # mid-word (e.g. "병 (病)신합수"). Supplying the correct compound
        # Hanja directly makes the text already-annotated, so the general
        # pass's own "already annotated" lookahead correctly skips it.
        combo_hanja = f"{stem_a}{stem_b}合{_ELEMENT_HANJA.get(combo_elem, '')}"
        notes.append(
            f"the annual stem **{h.stem}** forms **{combo_ko} ({combo_hanja})** with your Day Master, "
            f"activating {combo_elem}"
        )
    for stem_a, stem_b, combo_elem, combo_ko, natal_s in getattr(h, "natal_stem_combinations", []) or []:
        # E-6 (2026-09-25 audit): 천간합 with natal stems other than the DM.
        combo_hanja = f"{stem_a}{stem_b}合{_ELEMENT_HANJA.get(combo_elem, '')}"
        notes.append(
            f"the annual stem **{h.stem}** forms **{combo_ko} ({combo_hanja})** with your natal "
            f"**{natal_s}** stem, drawing it toward {combo_elem}"
        )
    for annual_s, natal_s in getattr(h, "stem_clashes", []) or []:
        # knowledge/01-stems.md §Stem Clashes — tension/pressure, not doom.
        notes.append(
            f"the annual stem **{annual_s}** clashes with your natal **{natal_s}** "
            f"in a **천간충** (stem clash) — pressure or abrupt change in what that stem represents"
        )
    # De-duplicate by (relationship, natal branch), not by relationship
    # alone — E-6 (2026-09-25 audit): a second harm/clash against a
    # different natal branch in the same year was silently dropped.
    seen_pairs: set = set()
    for annual_b, natal_b, rel in getattr(h, "activated_branches", []) or []:
        if (rel, natal_b) in seen_pairs:
            continue
        seen_pairs.add((rel, natal_b))
        label = _RELATIONSHIP_LABEL.get(rel, rel)
        notes.append(f"the annual branch **{annual_b}** and natal **{natal_b}** are in **{label}**")
    for hc in getattr(h, "harmony_completions", []) or []:
        # E-6 (2026-09-25 audit): the engine never checked whether the
        # annual/decade branch completes a 삼합/방합 triad with the natal
        # chart at all — knowledge/02-branches.md: "When all three appear...
        # highly empowered. When two appear... partial empowerment (반합)."
        triad_label = "".join(hc.triad)
        others = "".join(hc.matched_natal)
        if hc.kind == "삼형":
            notes.append(
                f"the annual branch **{h.branch}** completes the **{triad_label} 삼형 "
                f"(three-way punishment)** with your natal **{others}** — classically read as friction "
                f"with rules or authority, injury risk, or self-inflicted setbacks, so a year to move carefully"
            )
        elif hc.status == "full":
            notes.append(
                f"the annual branch **{h.branch}** completes the "
                f"**{triad_label} {hc.kind} ({hc.element})** with your natal **{others}**"
            )
        else:
            # No trailing "(반합)" gloss here — 반합 is in HANJA_GLOSSARY, so
            # the general first-use pass appends its own Hanja; wrapping it
            # in our own parens too would double them ("(반합 (半合))").
            notes.append(
                f"the annual branch **{h.branch}** half-completes the **{triad_label} {hc.kind} "
                f"({hc.element})** with your natal **{others}** — 반합"
            )
    if not notes:
        return ""
    return "Also active this year: " + "; ".join(notes) + "."


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
            f"A six-combination between **{a}** and **{c}** {six_combination_phrase(chart, a, c, elem)}, "
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


def six_combination_transforms(chart, a: str, c: str, elem: str) -> bool:
    """True when a natal 육합 actually transforms (합화) per
    knowledge/02-branches.md: the combined element must be in season at the
    month branch and neither member may be struck by a natal 충. Otherwise
    the pair only binds (합이불화, 合而不化). Validation 2026-09-25 #7: 巳申 was
    reported as "transforming toward Water" in a 巳 (Fire) month with 巳亥沖.
    """
    from . import lookup as L
    month_elem = L.BRANCH_ELEMENT.get(chart.month.branch, "")
    if not month_elem or month_elem not in elem:
        return False
    struck = {x for pair in (chart.clashes or []) for x in pair}
    return not ({a, c} & struck)


def six_combination_phrase(chart, a: str, c: str, elem: str) -> str:
    """Client phrase for a natal 육합 — transforms vs. binds without transforming."""
    if six_combination_transforms(chart, a, c, elem):
        return f"transforms toward **{elem}** energy"
    return (f"binds the two branches without transforming (합이불화, 合而不化) — {elem} is not in season at "
            f"the month branch or a member is struck by a clash, so read it as a tie, not a new {elem} force")


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
    if candidate.confidence not in ("likely", "possible"):
        return ""
    theme = _REGULAR_GRID_THEME.get(candidate.name_ko, "a life theme read from the dominant month-branch ten-god")
    if candidate.confidence == "possible":
        # E-9 (2026-09-25 audit): a regular grid only ever reaches "possible"
        # via patterns.py's 성격/파격 cross-check, which always sets `note`.
        # Surface that caveat instead of silently dropping the whole theme
        # sentence — gating strictly on "likely" (the old behavior) made the
        # grid narrative vanish with no explanation once this could fire.
        return (
            f"The engine flags **{candidate.name_ko} ({candidate.name_en})** as the regular grid, but with "
            f"a caveat: {candidate.note} When intact, this grid points toward a life theme shaped by {theme}."
        )
    return (
        f"The engine flags a likely **{candidate.name_ko} ({candidate.name_en})** as the regular grid. "
        f"This points toward a life theme shaped by {theme}. "
        + (f"{candidate.note} " if candidate.note else "")
        + "It is a structural tendency, not a career verdict; the ten-god distribution and timing tables refine how it expresses."
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
    _ctx_get(ctx, "dm_en", "Day Master")
    cls = _grouped_dominant_classes(chart, 1)
    if cls:
        names = [c.lower() for c, _ in cls]
        joined = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        gift = f"a strong {joined} presence that gives the querent real follow-through"
    else:
        gift = "a clear and workable Day Master foundation"
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
    fav = _ctx_get(ctx, "favorable", "—")
    sup = _ctx_get(ctx, "supporting", "—")
    spouse_branch = chart.day.branch
    _class_counts(chart)
    dominant = _grouped_dominant_classes(chart, 2)
    dom_summary = ", ".join(f"{c} ({n})" for c, n in dominant) or "Companion"
    # The chart's actual weighted-balance dominant element (chart.patterns
    # already computes this via the same _element_counts weighting shown in
    # the Element Balance table) — NOT the Day Master's own native element
    # (ctx.dm_element), which can differ (e.g. Harish: DM is Metal, but the
    # chart's weighted balance leans Water). Bug found 2026-09-19 (external
    # report review, 2nd pass): this sentence used to substitute
    # ctx.dm_element here, producing "the chart's element balance leaning
    # toward Metal" for a chart whose actual balance leans Water (27.8% vs
    # 25.3%) — a direct, client-visible internal contradiction against the
    # Element Balance table two sections earlier in the same report.
    balance_elem = (chart.patterns or {}).get("dominant_element") or _ctx_get(ctx, "dm_element", "")
    parts = [
        f"**{dm} ({dm_en})** sits at the centre of this chart, with the chart's element balance leaning "
        f"toward **{balance_elem}** and a ten-god distribution dominated by **{dom_summary}**.",
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
        "Across a full lifetime, this chart rewards the querent who studies their own patterns and "
        "acts with the favorable element rather than against it. The work is not to fix the chart; "
        "it is to use what is already there well."
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
    _class_counts(chart)
    dominant = _dominant_classes(chart, 3)
    dom_strengths = {
        "Companion": "the ability to collaborate as an equal without losing self",
        "Eating God": "the ability to create and produce visible work at a steady, sustainable pace",
        "Hurting Officer": "the ability to express sharply and produce work that cuts through noise",
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
        strengths.append("**Steady practice** — the chart rewards consistent effort over heroic bursts.")
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
    _ctx_get(ctx, "dm_element", "")
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
    output = cls.get("Eating God", 0) + cls.get("Hurting Officer", 0)
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    if verdict in ("strong", "extreme") and output >= 1:
        return (
            "**A public campaign with a clear voice** is the most likely fit. Strong Day Masters with "
            "visible Output stems can carry the visibility, and a public launch reads as confidence "
            "rather than risk. Pair it with a small but engaged audience rather than a mass-broadcast feel."
        )
    if verdict in ("weak", "extreme_weak") and output == 0:
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
    if output >= 1:
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
    """Which season favors this chart's launches.

    E-12 (2026-09-25 audit): this used to key the launch window to the Day
    Master's own season, while seasonal_rhythm_note (Health) called the 용신
    season "the cleanest window for new beginnings" — two rules in one
    report. Unified on the 용신 season, which is what
    knowledge/16-date-selection.md §Business opening asks for ("ideally in
    a favourable-element month").
    """
    fav = _ctx_get(ctx, "favorable", "")
    season = {
        "Wood": "spring (rising Wood energy is when new growth takes root)",
        "Fire": "summer (peak Fire energy supports visible launches)",
        "Earth": "the seasonal transitions (Earth stabilizes what is being built)",
        "Metal": "autumn (the harvest, the refinement)",
        "Water": "winter (deep, still Water — best for quiet launches, beta, and writing)",
    }.get(fav, "the favorable element's natural season")
    return (
        f"With **{fav}** as the favorable element, the most aligned launch window is **{season}**, "
        f"the favorable element's own season. "
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
        # E-12 (2026-09-25 audit): the listed decades qualify through the
        # 용신 OR the 희신 (period_favorable_status), so calling them all
        # "favorable {fav}-element periods" misdescribed 희신-only decades
        # (e.g. three Metal decades listed as "Water" periods).
        sup = _ctx_get(ctx, "supporting", "")
        elems = f"**{fav}**" + (f" (and supporting **{sup}**)" if sup and sup != fav else "")
        return (
            f"Travel and relocation are most likely to feel aligned during {elems}-element years and "
            f"months, and especially during these supportive major-luck periods: "
            f"{', '.join(favorable_periods[:3])}. "
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
    "Eating God": "Output", "Hurting Officer": "Output",
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
    "Eating God": "a partner you do and make things with — shared projects over convention",
    "Hurting Officer": "a partner you speak plainly with — candid exchange over convention",
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


