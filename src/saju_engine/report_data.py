"""Data tables and pure helpers used by `premium_report.py`.

This module is the single source of truth for:
  - Tier metadata (`TIER_CONFIG`) and tier-key normalization (`normalize_tier`).
  - Static lookup tables: English stem labels, stem profiles, element organ
    maps, classical element associations, career domain pools, grounding
    practices, chart signature templates, and pillar position labels.
  - Chart-derived helpers that read `chart` fields and return data structures
    without writing prose: `_element_balance`, `_chart_signature`,
    `_career_tiers`, `_compatibility_rows`, `_hidden_stems_str`, etc.

Everything in this module is pure (no I/O, no rendering) so it can be reused
by callers that need chart-derived data without the full report. Section
builders that produce prose stay in `premium_report.py`.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import lookup as L
from .chart import Chart, Pillar
from .yongsin import favorable_element


# ── Five-element presentation helpers (engine-neutral, used by both backends) ─
ELEMENT_COLORS = {
    "Wood": "#27ae60",
    "Fire": "#e74c3c",
    "Earth": "#f39c12",
    "Metal": "#7f8c8d",
    "Water": "#3498db",
}

ELEMENT_EMOJI = {
    "Wood": "🟢",
    "Fire": "🔴",
    "Earth": "🟡",
    "Metal": "⚪",
    "Water": "🔵",
}


# ── Tier metadata ──────────────────────────────────────────────────────────
TIER_CONFIG: Dict[str, Dict[str, str]] = {
    "sample": {
        "name": "The Hook",
        "price": "Complimentary",
        "pages": "1",
        "tagline": "A one-page taste of your Saju chart — your elemental blueprint, no predictions",
    },
    "essential": {
        "name": "Essential Report",
        "price": "$19",
        "pages": "6–7",
        "tagline": "Your natal chart, career arc, decade cycles, and lucky-element guide",
    },
    "deep": {
        "name": "Deep Destiny Report",
        "price": "$55",
        "pages": "10–12",
        "tagline": "Full natal reading + ten-year year-by-year timing + relationship and business-launch guidance",
    },
    "spark": {
        "name": "The Spark",
        "price": "$9",
        "pages": "4–5",
        "tagline": "Your Saju chart decoded in 5 minutes",
    },
    "reading": {
        "name": "The Reading",
        "price": "$55",
        "pages": "10–12",
        "tagline": "Your complete Saju reading — personality, career, relationships, health, and the next 3 years",
    },
    "fullmap": {
        "name": "The Full Map",
        "price": "$129",
        "pages": "18–22",
        "tagline": "Your life's complete map — natal reading + deep-dive modules + 10-year forecast",
    },
    "companion": {
        "name": "Cosmic Companion",
        "price": "$9/month",
        "pages": "3–4",
        "tagline": "Ongoing monthly timing guidance, annual outlook refresh, and priority email support",
    },
}


# ── English stem labels (no single global lookup, so we keep a local table) ─
_STEM_EN = {
    "甲": "Gap (Yang Wood, 甲木)",
    "乙": "Eul (Yin Wood, 乙木)",
    "丙": "Bing (Yang Fire, 丙火)",
    "丁": "Jeong (Yin Fire, 丁火)",
    "戊": "Mu (Yang Earth, 戊土)",
    "己": "Gi (Yin Earth, 己土)",
    "庚": "Gyeong (Yang Metal, 庚金)",
    "辛": "Sin (Yin Metal, 辛金)",
    "壬": "Im (Yang Water, 壬水)",
    "癸": "Gye (Yin Water, 癸水)",
}


# ── Stem imagery profile (used in the Day Master Portrait section) ────────
from .stem_profiles import _STEM_PROFILE

# ── Five Element organ / system mapping (classical, not medical advice) ──────
# source: knowledge/15-health-and-body.md § 오행 → Organ Systems
_ELEMENT_ORGANS: Dict[str, str] = {
    "Wood": "liver/gall bladder and nervous system",
    "Fire": "heart/small intestine and circulation",
    "Earth": "spleen/stomach and digestive metabolism",
    "Metal": "lung/large intestine and respiratory/immune boundaries",
    "Water": "kidney/bladder and hormonal/endocrine reserves",
}


# ── Classical Five Element associations for lucky attributes ────────────────
# source: knowledge/14-directions-and-relocation.md (direction/colours/numbers/materials);
#         knowledge/15-health-and-body.md (foods). Gemstone lists are modern
#         convention — see knowledge/14 § Classical vs. Modern.
_ELEMENT_ASSOCIATIONS: Dict[str, Dict[str, str]] = {
    "Wood": {
        "colors": "green, teal, jade",
        "direction": "east",
        "numbers": "3, 8",
        "season": "spring",
        "gemstones": "jade, aventurine, green tourmaline, emerald",
        "foods": "leafy greens, sprouts, sour foods in moderation, fresh herbs",
        "best_times": "dawn to mid-morning (Wood hours, 3–7 am)",
        "avoid": "excessive white/grey, autumn dryness, and Metal-heavy west orientation",
    },
    "Fire": {
        "colors": "red, orange, crimson",
        "direction": "south",
        "numbers": "2, 7",
        "season": "summer",
        "gemstones": "ruby, garnet, carnelian, red jasper",
        "foods": "bitter greens, red-colored vegetables, warm foods, light spices",
        "best_times": "late morning through early afternoon (Fire hours, 9 am–1 pm) for visibility and momentum",
        "avoid": "excessive black/navy, winter cold, and Water-heavy north orientation",
    },
    "Earth": {
        "colors": "yellow, ochre, warm brown",
        "direction": "center",
        "numbers": "0, 5",
        "season": "transitions between seasons",
        "gemstones": "citrine, tiger's eye, yellow jasper, amber",
        "foods": "whole grains, yellow and orange root vegetables, mildly sweet foods",
        "best_times": "stable routines at season transitions and late afternoon (1–3 pm)",
        "avoid": "excessive green, early-spring wind, and Wood-heavy east orientation",
    },
    "Metal": {
        "colors": "white, silver, metallic grey",
        "direction": "west",
        "numbers": "4, 9",
        "season": "autumn",
        "gemstones": "clear quartz, hematite, silver, white moonstone",
        "foods": "white-colored foods (radish, pear, rice), pungent spices in moderation",
        "best_times": "late afternoon to early evening (Metal hours, 3–7 pm) for focus",
        "avoid": "excessive red/orange, summer heat, and Fire-heavy south orientation",
    },
    "Water": {
        "colors": "black, navy, deep blue",
        "direction": "north",
        "numbers": "1, 6",
        "season": "winter",
        "gemstones": "black tourmaline, obsidian, lapis lazuli, aquamarine",
        "foods": "black beans, seaweed, salty foods in moderation, soups and broths",
        "best_times": "evening through midnight (Water hours, 9 pm–1 am) for restoration",
        "avoid": "excessive yellow/ochre, damp stagnation, and Earth-heavy center orientation",
    },
}


# ── Career domain pools by element ────────────────────────────────────────
# source: knowledge/12-career-and-vocation.md § Element → Industry Families
#         (element nature from knowledge/03-five-elements.md; the occupation
#         extension is modern 명리 convention — see knowledge/12 § Scope & Limits)
_CAREER_DOMAINS: Dict[str, List[Tuple[str, str]]] = {
    "Wood": [
        ("Education & Training", "teaching, curriculum design, academic research"),
        ("Healthcare & Wellness", "nursing, therapy, fitness, holistic health"),
        ("Design & Publishing", "graphic design, writing, editing, publishing"),
        ("Social & Environmental Work", "social work, NGOs, environmental advocacy"),
        ("People Development & Culture", "coaching, talent development, organizational culture"),
        ("Creative Direction", "art direction, brand storytelling, content strategy"),
    ],
    "Fire": [
        ("Leadership & Executive Roles", "CEO, director, team lead, public office"),
        ("Media & Performing Arts", "broadcasting, acting, music, public speaking"),
        ("Marketing & Public Relations", "brand management, PR, advertising, influencer strategy"),
        ("Teaching & Coaching", "seminars, motivational speaking, personal coaching"),
        ("Entrepreneurship", "startups, venture building, product evangelism"),
        ("Public Affairs & Advocacy", "campaigns, policy, community organizing"),
    ],
    "Earth": [
        ("Real Estate & Property", "development, brokerage, property management"),
        ("Hospitality & Food", "restaurants, hotels, catering, event planning"),
        ("Finance & Accounting", "accounting, bookkeeping, wealth management"),
        ("Mediation & Counselling", "psychotherapy, life coaching, pastoral care"),
        ("Project Management", "operations, program management, logistics coordination"),
        ("Agriculture & Land", "farming, landscaping, environmental restoration"),
    ],
    "Metal": [
        ("Law & Governance", "attorney, judge, compliance, policy"),
        ("Engineering & Technology", "software, hardware, civil, mechanical engineering"),
        ("Medicine & Surgery", "surgery, diagnostics, medical research"),
        ("Finance & Investment", "investment banking, trading, risk management"),
        ("Quality & Audit", "auditing, QA, forensic analysis, due diligence"),
        ("Security & Military", "defense, intelligence, security consulting"),
    ],
    "Water": [
        ("Strategy & Consulting", "management consulting, advisory, research"),
        ("Diplomacy & International Business", "diplomacy, import/export, global trade"),
        ("Psychology & Counseling", "clinical psychology, counseling, hypnotherapy"),
        ("Arts & Curation", "curation, art dealing, museum work, creative research"),
        ("Journalism & Investigation", "reporting, investigative journalism, publishing"),
        ("Logistics & Shipping", "supply chain, maritime, travel industry"),
    ],
}
# Reviewed 2026-09-20 (external report review): knowledge/12's Water family
# prose also names "data, networks & platforms" as a 7th item, which this
# 6-slot table does not carry. NOT changed here — `_CAREER_DOMAINS` is a
# validated invariant (tests/validation/test_val_career.py::test_pool_structure_invariant,
# test_domain_map_covers_exactly_all_30_kb12_domains: exactly 5 x 6 = 30
# domains, one curated representative per KB12 family slot, deliberately not
# a verbatim 1:1 copy of KB12's prose lists). Swapping in a 7th domain, or
# swapping out an existing one for it, changes what a real delivered report
# shows and is a product decision, not a bug fix — flagged for the user
# rather than decided unilaterally.


# ── Grounding practices by favorable element ──────────────────────────────
# source: knowledge/15-health-and-body.md § Foods, Lifestyle & Rhythm by Favourable Element
_GROUNDING_PRACTICES: Dict[str, List[str]] = {
    "Wood": [
        "Walking in forests or tree-lined paths",
        "Eating leafy greens, sprouts, and sour foods in moderation",
        "Waking early (dawn, the Wood hour)",
        "Creative writing or planning sessions in the morning",
        "Stretching or tai chi to unblock stagnant Wood qi",
    ],
    "Fire": [
        "Short midday walks in sunlight",
        "Eating bitter greens, red-colored vegetables, and warm foods",
        "Speaking or performing in well-lit south-facing spaces",
        "Taking brief social breaks to rekindle enthusiasm",
        "Journaling by candlelight to focus scattered Fire",
    ],
    "Earth": [
        "Gardening, pottery, or cooking with whole grains",
        "Eating yellow/orange root vegetables and mildly sweet foods",
        "Grounding walks on soil or grass with bare feet",
        "Keeping a steady meal and sleep schedule",
        "Working from a stable, centered location rather than constantly moving",
    ],
    "Metal": [
        "Breathwork and pranayama in cool, dry air",
        "Eating white-colored foods (radish, pear, rice) and pungent spices",
        "Organizing and decluttering physical and digital spaces",
        "Autumn retreats or west-facing quiet rooms",
        "Precision hobbies: calligraphy, instrument practice, martial forms",
    ],
    "Water": [
        "Swimming, baths, or walking near rivers/lakes/ocean",
        "Eating black beans, seaweed, and salty foods in moderation",
        "Meditation or stillness practice in the evening",
        "North-facing study or rest spaces",
        "Reading, research, or journaling to settle a restless mind",
    ],
}


# ── Chart signature templates ──────────────────────────────────────────────
# source: knowledge/03-five-elements.md (element nature) + knowledge/01-stems.md (stem imagery)
_SIGNATURES: Dict[str, Dict[str, str]] = {
    "Wood": {
        "in_season": "A forest in full spring — rising, branching, and built to grow upward.",
        "off_season": "A deep-rooted tree in unlikely soil — resilient, patient, and quietly tenacious.",
    },
    "Fire": {
        "in_season": "A noon sun in full summer — radiant, relentless, and built to illuminate.",
        "off_season": "A steady lamp in a cool room — warm, focused, and sustaining against the dark.",
    },
    "Earth": {
        "in_season": "A broad plateau at harvest — steady, sustaining, and made to bear weight.",
        "off_season": "A garden plot waiting for rain — fertile, patient, and needing the right season.",
    },
    "Metal": {
        "in_season": "A honed blade in autumn air — sharp, decisive, and made to cut through clutter.",
        "off_season": "A jewel kept in velvet — refined, reserved, and requiring the right setting.",
    },
    "Water": {
        "in_season": "A river in flood — vast, intelligent, and carrying everything before it.",
        "off_season": "An underground spring — quiet, persistent, and finding paths others miss.",
    },
}


# ── Pillar position labels and classical life-area mapping ─────────────────
_PILLAR_POSITION_LABELS = {
    "year": "Year Pillar",
    "month": "Month Pillar",
    "day": "Day Pillar",
    "hour": "Hour Pillar",
}

# Classical life-area mapping per pillar position.
_PILLAR_AREAS = {
    "year": "ancestral and social-root energy — the wider world you were born into",
    "month": "career and immediate environment — how you show up at work and in daily life",
    "day": "spouse palace and the inner self — the partner you choose and the self behind the choices",
    "hour": "later life and children — what you build toward and what you pass on",
}


# ── Pure helpers ───────────────────────────────────────────────────────────
def normalize_tier(tier: str) -> str:
    """Return a canonical tier key from user input.

    Supports the landing-page client tiers (sample/hook, essential, deep)
    and the legacy internal tiers (spark, reading, fullmap). The legacy tiers
    remain distinct content products for backward compatibility.
    """
    mapping = {
        # Landing-page tiers
        "sample": "sample", "hook": "sample", "thehook": "sample",
        "taste": "sample", "type1": "sample", "1": "sample",
        "essential": "essential", "theessential": "essential",
        "799": "essential", "type2": "essential", "2": "essential",
        "deep": "deep", "thedeep": "deep", "deepdestiny": "deep",
        "destiny": "deep", "1499": "deep", "type3": "deep", "3": "deep",
        # Legacy internal tiers (distinct products, kept for backward compatibility)
        "spark": "spark", "thespark": "spark",
        "reading": "reading", "thereading": "reading",
        "fullmap": "fullmap", "thefullmap": "fullmap", "full": "fullmap",
        # Subscription tier
        "companion": "companion", "cosmiccompanion": "companion",
    }
    key = tier.lower().replace(" ", "").replace("-", "").replace("_", "").replace("₹", "").replace("/month", "")
    if key not in mapping:
        raise ValueError(
            f"Unknown tier {tier!r}. Choose one of: sample, essential, deep, spark, reading, fullmap, companion."
        )
    return mapping[key]


def _day_master_in_season(chart: Chart) -> bool:
    """Return True if the month branch supports the Day Master's element."""
    element = chart.day_master_info.get("element", "")
    month_branch = chart.month.branch
    return (
        (element == "Wood" and month_branch in "寅卯辰")
        or (element == "Fire" and month_branch in "巳午未")
        or (element == "Earth" and month_branch in "辰戌丑未")
        or (element == "Metal" and month_branch in "申酉戌")
        or (element == "Water" and month_branch in "亥子丑")
    )


def _chart_signature(chart: Chart) -> str:
    """Generate a unique chart signature sentence."""
    element = chart.day_master_info.get("element", "Earth")
    in_season = "in_season" if _day_master_in_season(chart) else "off_season"
    return _SIGNATURES.get(element, {}).get(in_season, "A chart of quiet, persistent potential.")


def _element_balance(chart: Chart) -> Tuple[Dict[str, float], Counter]:
    """Return (percentage_dict, weighted_counts).

    Uses the canonical element-balance helper in ``strength.py`` so that
    Chart at a Glance, Health, and every other consumer read the same numbers.
    """
    from . import strength as S

    counts = S.element_balance_counts(chart)
    pct = S.element_balance_pct(chart)
    return pct, counts


def _bar(pct: float, width: int = 20) -> str:
    """Return an ASCII bar for the element balance display."""
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _element_balance_table(chart: Chart) -> List[str]:
    """Return element balance as a Markdown table with colored emoji indicators."""
    pct, _ = _element_balance(chart)
    lines = [
        "| Element | Presence | Percentage |",
        "|---|---|---|",
    ]
    for element in ["Fire", "Earth", "Metal", "Water", "Wood"]:
        value = pct.get(element, 0.0)
        emoji = ELEMENT_EMOJI.get(element, "")
        lines.append(f"| {emoji} {element} | {_bar(value)} | {value}% |")
    return lines


def _strength_label(chart: Chart) -> str:
    sa = chart.strength_assessment or {}
    verdict = sa.get("verdict", "balanced")
    if verdict == "extreme":
        return "Very Strong"
    if verdict == "strong":
        return "Strong"
    if verdict == "extreme_weak":
        return "Very Weak"
    if verdict == "weak":
        return "Weak"
    return "Balanced"


def _domain_element(domain: str) -> Optional[str]:
    """Map a career domain to its dominant element for scoring."""
    domain_lower = domain.lower()
    wood_keys = ["wood", "education", "healthcare", "design", "publishing", "social", "environmental", "hr development", "creative direction"]
    fire_keys = ["fire", "leadership", "media", "marketing", "teaching", "entrepreneurship", "politics", "coaching", "public relations"]
    earth_keys = ["earth", "real estate", "hospitality", "finance", "accounting", "counseling", "project management", "agriculture", "human resources"]
    metal_keys = ["metal", "law", "engineering", "medicine", "surgery", "investment", "technology", "audit", "quality", "security"]
    water_keys = ["water", "strategy", "diplomacy", "psychology", "arts", "journalism", "logistics", "shipping", "research", "investigation", "international"]
    if any(k in domain_lower for k in wood_keys):
        return "Wood"
    if any(k in domain_lower for k in fire_keys):
        return "Fire"
    if any(k in domain_lower for k in earth_keys):
        return "Earth"
    if any(k in domain_lower for k in metal_keys):
        return "Metal"
    if any(k in domain_lower for k in water_keys):
        return "Water"
    return None


def _top_tengod(chart: Chart) -> str:
    """Return the most frequently appearing 십신 (Ten God) in the natal chart."""
    from collections import Counter

    counts = Counter(h.tengod_en for h in chart.ten_gods if h.tengod_en)
    if not counts:
        return ""
    return counts.most_common(1)[0][0]


def _resolved_favorable(chart: Chart, override: Optional[str] = None) -> str:
    """The 용신 the engine actually resolved, as an element name.

    Single read point for the career subsystem's display channel. Returns ""
    when the resolver cannot name an element, so callers compare falsy rather
    than matching the sentinel "—" against a real element name.

    ``override`` is the reader-argued element carried by the report generator
    (``_ReportContext.favorable_override``) and must be passed explicitly.
    ``yongsin.favorable_element`` also honours a *chart-level*
    ``strength_assessment["reader_override_favorable"]``, but the CLI sets only
    the argument and never that field (measured: ``None`` for every CLI-built
    chart), so a bare ``favorable_element(chart)`` resolves the **engine**
    element and silently drops the reader's reading — leaving the career table
    naming an element that contradicts the report's own Quick Reference.
    """
    element = favorable_element(chart, override).element
    return element if element and element != "—" else ""


def _career_why(chart: Chart, domain: str, override: Optional[str] = None) -> str:
    # Display channel, not the raw 억부 candidate: ``favorable_element()``
    # applies the 조후 merge and any reader override, so the prose names the
    # element the engine actually resolved. Reading
    # ``strength_assessment["candidate_favorable"]`` here named an element the
    # engine did not resolve for climate-tie-broken / overridden charts.
    dm_element = chart.day_master_info.get("element", "")
    favorable = _resolved_favorable(chart, override)
    domain_elem = _domain_element(domain)
    if domain_elem == favorable:
        return f"Aligns with your favorable element {favorable}, reducing friction."
    if domain_elem == dm_element:
        return f"Lets your native {dm_element} energy express directly."
    if domain_elem:
        return f"Uses {domain_elem} energy in a supportive role to your {dm_element} Day Master."
    top = _top_tengod(chart)
    if top:
        return f"Lets you express your strongest visible ten-god, {top}, in a structured setting."
    return "Uses skills that fit your overall stem-branch composition."



def _career_tiers(
    chart: Chart, override: Optional[str] = None
) -> List[Tuple[str, str, str, str]]:
    """Return ranked (tier, domain, why, examples) rows.

    Candidate families are keyed on the chart's *need*, not its Day Master.
    Per knowledge/12-career-and-vocation.md §"용신 vs. Day Master for Career
    Choice", the classical priority is to "align work with what the chart
    *needs* (용신 / 희신, 喜神), not merely with the Day Master's own element",
    because "choosing a field that reinforces an already-dominant element
    pushes the chart further out of balance"; that section's closing procedure
    is to "identify the 용신 element from Step 3, map it through the
    **Element → Industry Families** list above". So the pool is the resolved
    용신's family, then the 희신's family as secondary breadth.

    The Day Master's own family is no longer served on its own account — it
    enters only when it *is* the 용신 or 희신 family for this chart, which is
    the common case for a 신강 / balanced chart: there the 용신 is the draining
    element and its generator (the 희신) is the Day Master's own element.

    The resolved element comes from the display channel
    (``_resolved_favorable`` → ``yongsin.favorable_element``), which applies
    the 조후 merge and any reader override — not the raw 억부
    ``strength_assessment["candidate_favorable"]``, which diverges from it on
    climate-tie-broken and reader-overridden charts.

    ``override`` is the reader-argued element from the report generator. Both
    the 용신 and the 희신 resolve through it together, so a reader-overridden
    chart ranks its *reader's* families and never a half-swapped mix of the
    reader's 용신 and the engine's 희신.

    Falls back to the Day Master's own family only when the resolver names no
    element at all, so the table is never empty.

    One asymmetry is deliberate. The *penalty* branch still reads the raw
    ``candidate_unfavorable``, because ``FavorableElement`` (yongsin.py:75-102)
    publishes no display-channel unfavorable element at all — it carries only
    ``element`` and ``supporting``. There is no resolver to read, and inventing
    one would mean asserting a rule the knowledge files do not state, so the raw
    field stays until ``yongsin.py`` grows that channel. It is latent today: the
    raw unfavorable is ``None`` for harish and ``"Wood"`` for manvitha, and no
    Wood-family domain reaches her pool, so the −2 branch never fires on either
    tier fixture.
    """
    dm_element = chart.day_master_info.get("element", "")
    favorable = _resolved_favorable(chart, override)
    supporting = favorable_element(chart, override).supporting
    if supporting == "—":
        supporting = ""
    unfavorable = (chart.strength_assessment or {}).get("candidate_unfavorable")

    family_order = [e for e in (favorable, supporting) if e in _CAREER_DOMAINS]
    if not family_order and dm_element in _CAREER_DOMAINS:
        family_order = [dm_element]

    domains: List[Tuple[str, str]] = []
    seen: set = set()
    for element in family_order:
        for domain, examples in _CAREER_DOMAINS[element]:
            if domain not in seen:
                seen.add(domain)
                domains.append((domain, examples))

    scored = []
    for domain, examples in domains:
        score = 0
        domain_elem = _domain_element(domain)
        if domain_elem and domain_elem == favorable:
            score += 2
        if domain_elem == dm_element:
            score += 1
        if domain_elem and domain_elem == unfavorable:
            score -= 2
        scored.append((score, domain, examples))

    # Stable sort: within a score tie the family order above is preserved
    # (용신 family before 희신 family, each in table-declaration order), so the
    # tier ladder never depends on dict iteration order.
    scored.sort(reverse=True, key=lambda x: x[0])

    tiers = []
    for i, (score, domain, examples) in enumerate(scored):
        if i < 4:
            tier = "**Best Fit**"
        elif i < 7:
            tier = "**Good Fit**"
        else:
            tier = "**Possible**"
        why = _career_why(chart, domain, override)
        tiers.append((tier, domain, why, examples))
    return tiers


def _compatibility_rows(
    dm_element: str,
    favorable_element: Optional[str],
    verdict: str = "balanced",
) -> List[Tuple[str, str, str, str]]:
    """Return (archetype, element, fit, reason) rows.

    Doctrinally grounded in knowledge/09-interpretation-method.md Step 3 and
    knowledge/03-five-elements.md: the fit of each element as a *partner element*
    depends on Day-Master strength, not on a fixed "generating == best" rule.
      - Strong DM (신강): 용신 = 식상/재성/관성 (drain/control). Resource (인성)
        and Self (비겁) amplify the imbalance → "Watch".
      - Weak DM (신약): 용신 = 인성/비겁 (support). Output/Wealth/Authority drain
        or press the weak self → "Watch".
      - Balanced: favorable element is "Best"; its generator (희신, strict
        classical) is "Good"; the rest are "Compatible".
    The favorable_element (용신) is always the single "Best" row.
    """
    # 인성 (Resource) — generates DM.
    generating = {
        "Wood": "Water", "Fire": "Wood", "Earth": "Fire",
        "Metal": "Earth", "Water": "Metal",
    }
    # 식상 (Output) — DM generates.
    generated = {
        "Wood": "Fire", "Fire": "Earth", "Earth": "Metal",
        "Metal": "Water", "Water": "Wood",
    }
    # 관성 (Authority) — controls DM.
    controlling = {
        "Wood": "Metal", "Fire": "Water", "Earth": "Wood",
        "Metal": "Fire", "Water": "Earth",
    }
    # 재성 (Wealth) — DM overcomes.
    wealth = {
        "Wood": "Earth", "Fire": "Metal", "Earth": "Water",
        "Metal": "Wood", "Water": "Fire",
    }

    archetypes = {
        "Wood": "Growth-oriented, idealistic, and principled",
        "Fire": "Radiant, expressive, and momentum-driven",
        "Earth": "Grounded, nurturing, and reliability-focused",
        "Metal": "Disciplined, precise, and structure-oriented",
        "Water": "Adaptive, perceptive, and depth-seeking",
    }

    resource = generating.get(dm_element)
    output = generated.get(dm_element)
    authority = controlling.get(dm_element)
    wealth_elem = wealth.get(dm_element)

    strong = verdict in ("strong", "extreme")
    weak = verdict == "weak"

    def fit_for(elem: str) -> Tuple[str, str]:
        if elem == favorable_element:
            return "**Best**", f"{elem} is your 용신 (favorable element) — the core balance your chart seeks."
        if strong:
            # Drain/control group (식상/재성/관성) = secondary favorable.
            if elem in (output, wealth_elem, authority):
                return "**Good**", f"{elem} helps drain or channel your strong Day Master — a complementary force."
            if elem == resource:
                return "**Watch**", f"{elem} (인성) feeds your already-strong self and can amplify imbalance."
            if elem == dm_element:
                return "**Watch**", "Same-element (비겁) peers echo your strength — support turns into competition."
        elif weak:
            # Support group (인성/비겁) = secondary favorable.
            if elem in (resource, dm_element):
                return "**Good**", f"{elem} supports and nourishes your weak Day Master."
            # Output/Wealth/Authority drain or press the weak self.
            if elem in (output, wealth_elem, authority):
                return "**Watch**", f"{elem} drains or pressures your weak Day Master — handle with care."
        else:
            # Balanced: 희신 = generator of 용신 (strict classical, knowledge/03).
            if favorable_element and elem == generating.get(favorable_element):
                return "**Good**", f"{elem} generates your 용신 ({favorable_element}) — secondary support (희신)."
        return "**Compatible**", "Neutral energetic exchange."

    rows: List[Tuple[str, str, str, str]] = []
    for elem in ["Wood", "Fire", "Earth", "Metal", "Water"]:
        fit, reason = fit_for(elem)
        rows.append((archetypes[elem], elem, fit, reason))
    return rows


def _hidden_stems_str(p: Pillar) -> str:
    """Return a concise hidden-stem string for the four-pillar table."""
    parts = []
    for role, s in p.hidden_stems:
        label = {"main": "본", "middle": "중", "residual": "여"}.get(role, role)
        parts.append(f"{s} ({label})")
    return ", ".join(parts) if parts else "—"


# ── One-line classical meanings for the 신살 (stars) `stars.py` computes ────
# source: knowledge/07-special-formations.md's own "Meaning:" lines for each
# star (§Common 신살, §More classical 신살). 도화 (peach_blossom) and 역마
# (post_horse) are intentionally excluded here — they already have their own
# dedicated sections elsewhere in the report (Relationship Style / Relocation
# & Travel) and would be redundant if repeated in a generic star list. 홍염
# and 양인 are also excluded: this project has no natal-context "Meaning:"
# line for them (they are documented only for the compatibility/궁합 product,
# knowledge/11-gunghap.md), and Ground Rule 1 forbids inventing one.
#
# Added 2026-09-20 (external report review): stars.py already computes all
# of these correctly, but no report section ever surfaced them — confirmed
# missing for Harish, whose chart carries 겁살 (year branch 申), 지살 (day
# branch 亥), 월살 (hour branch 丑), and 천덕귀인 (day stem 辛), none of which
# appeared anywhere in his delivered report.
_STAR_MEANING: Dict[str, str] = {
    "kong_mang": "the branches here are read as symbolically \"void\" — their themes feel deferred or less solid, not absent.",
    "canopy": "a scholarly / solitary / artistic marker — often found in those drawn to religion, scholarship, art, or a hermetic path.",
    "heavenly_noble": "a \"helper\" star — a tendency toward receiving support from an unexpected, noble source at key turning points.",
    "literary_star": "favorable for academic and literary work, exams, and written expression — a native facility with words and ideas.",
    "robbery_star": "sudden loss, theft, or unexpected competition — can also mark a capacity for decisive action.",
    "disaster_star": "mishaps, illness, or obstacles as a recurring theme — classically read as softened by a strong 용신.",
    "heaven_bane": "external pressures or authority conflicts — \"heaven-sent\" trials.",
    "earth_bane": "earthly hindrances, delays, or bureaucratic friction.",
    "annual_bane": "yearly/annual-style friction — a lighter, less emphasized marker in modern Korean readings.",
    "monthly_bane": "monthly-style friction; some schools also read it for romantic turbulence.",
    "lost_spirit": "mental dispersion, forgetfulness, or scattered energy; can also indicate hidden schemes.",
    "general_star": "leadership, command, and organizational ability.",
    "saddle_star": "advancement, promotion — riding a rising wave.",
    "six_harm_bane": "covert harm or friction from the six-harm branch direction.",
    "deep_grudge": "lingering resentment or unfinished conflict — in relationships, recurring arguments that never fully resolve.",
    "ghost_gate": "sensitivity to hidden matters or the unseen; read here as a descriptive sensitivity marker, not an omen.",
    "white_tiger": "intensity and sudden force — surgical or martial precision; can bring accidents or conflict if unchecked, alongside a real capacity for decisive action.",
    "sky_hero": "strong will, charisma, and leadership — with a tendency toward extremity or conflict if the chart is not balanced.",
    "heavenly_virtue": "virtue, protection, and honorable character — help arriving in times of need; often read as one of the most favorable stars.",
    "monthly_virtue": "monthly/quarterly support, popularity, and smooth assistance from people around the querent.",
}
