"""Career, business and wealth deep-dive report.

A standalone, engine-generated deep-dive (`--format career`) that grounds
every claim in `knowledge/12-career-and-vocation.md` (career mode, earning
vehicle) and `knowledge/13-wealth-and-business.md` (income style, carrying
capacity, 겁재奪財, 재고, preservation), with timing read from
`knowledge/08-luck-pillars.md` (대운/세운).

The ranked-domain table reuses the engine's single career subsystem
(`report_data._career_tiers`), so this report can never disagree with the
Career & Wealth section of the natal report for the same chart. Everything
else here — role ladders, entity fit, investment behaviour, decade timing —
is assembled from the resolved five roles plus the concrete annual pillars.

Citations stay in the `.md` source and are stripped from client PDFs.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Tuple

from . import lookup as L
from .daeun import first_period_start_date
from .report_data import _career_tiers
from .sewoon import derive_sewoon
from .yongsin import favorable_element

_CLASS_OF: Dict[str, str] = {
    "비견": "Companion", "겁재": "Companion",
    "식신": "Output", "상관": "Output",
    "편재": "Wealth", "정재": "Wealth",
    "편관": "Authority", "정관": "Authority",
    "편인": "Resource", "정인": "Resource",
}
_CLASS_KO = {
    "Companion": "비겁 (比劫)", "Output": "식상 (食傷)", "Wealth": "재성 (財星)",
    "Authority": "관성 (官星)", "Resource": "인성 (印星)",
}

# Concrete role ladders per domain (modern 명리 convention, knowledge/12).
_ROLES: Dict[str, str] = {
    "Education & Training": "teacher, lecturer, curriculum lead, L&D manager",
    "Healthcare & Wellness": "practitioner, therapist, clinic lead, wellness director",
    "Design & Publishing": "designer, editor, author, creative lead",
    "Social & Environmental Work": "program officer, advocate, NGO lead, sustainability lead",
    "People Development & Culture": "HR business partner, coach, talent lead, culture head",
    "Creative Direction": "art director, brand storyteller, content strategist",
    "Leadership & Executive Roles": "team lead, director, general manager, founder-CEO",
    "Media & Performing Arts": "broadcaster, performer, host, producer",
    "Marketing & Public Relations": "marketer, PR lead, brand manager, growth lead",
    "Teaching & Coaching": "trainer, speaker, coach, program facilitator",
    "Entrepreneurship": "founder, product owner, venture operator",
    "Public Affairs & Advocacy": "campaigner, policy analyst, public advocate",
    "Real Estate & Property": "agent, developer, property manager, investor-operator",
    "Hospitality & Food": "operator, chef-owner, hotel/events manager",
    "Finance & Accounting": "accountant, controller, wealth manager, CFO-track",
    "Mediation & Counselling": "mediator, counsellor, life coach, pastoral lead",
    "Project Management": "project manager, operations lead, program director",
    "Agriculture & Land": "farm operator, agribusiness manager, land steward",
    "Law & Governance": "lawyer, compliance officer, policy lead, judge-track",
    "Engineering & Technology": "engineer, architect, tech lead, CTO-track",
    "Medicine & Surgery": "physician, surgeon, diagnostics lead, researcher",
    "Finance & Investment": "analyst, trader, risk manager, portfolio lead",
    "Quality & Audit": "auditor, QA lead, forensic analyst, due-diligence lead",
    "Security & Military": "security lead, intelligence analyst, defence consultant",
    "Strategy & Consulting": "consultant, strategist, advisor, research lead",
    "Diplomacy & International Business": "diplomat, trade lead, global BD manager",
    "Psychology & Counseling": "clinical psychologist, counsellor, therapist",
    "Arts & Curation": "curator, art dealer, creative researcher, museum lead",
    "Journalism & Investigation": "reporter, investigative journalist, editor",
    "Logistics & Shipping": "supply-chain lead, freight manager, mobility operator",
}

# Company/entity type by the favorable element's working character.
_ENTITY_BY_ELEMENT = {
    "Wood": ("growth-stage organisations that develop people or ideas",
             "structured but expanding — education, health, design, mission-led firms"),
    "Fire": ("visible, fast, audience-facing organisations",
             "founder-led or brand-led teams where recognition compounds"),
    "Earth": ("stable, asset-holding, mediating organisations",
             "established firms, property/finance/operations, long-horizon institutions"),
    "Metal": ("precise, standards-driven, accountable organisations",
             "regulated or engineering/law/finance firms with clear lines of authority"),
    "Water": ("fluid, information-moving organisations",
             "consulting, research, logistics/data or international networks"),
}


# ── helpers ─────────────────────────────────────────────────────────────────

def _first_start(chart) -> Optional[object]:
    try:
        by, bm, bd = (int(x) for x in chart.birth_date.split("-"))
    except (ValueError, AttributeError):
        return None
    bh, bmi = 0, 0
    try:
        bh, bmi = (int(x) for x in (chart.birth_time or "00:00").split(":"))
    except (ValueError, AttributeError):
        pass
    direction = L.daeun_direction(chart.year.stem, chart.gender)
    return first_period_start_date(
        by, bm, bd, direction, hour=bh, minute=bmi,
        utc_offset=getattr(chart, "utc_offset", 9.0) or 9.0,
    )


def _decade_year_range(chart, idx: int) -> Tuple[int, int]:
    first = _first_start(chart)
    if first is None:
        return (0, 0)
    s = first.replace(year=first.year + 10 * idx)
    e = first.replace(year=first.year + 10 * (idx + 1))
    return s.year + 1, e.year


def _year_status(stem_e: str, branch_e: str, fav: str, sup: str,
                 unfav: Optional[str]) -> str:
    favsup = {e for e in (fav, sup) if e and e != "—"}
    fav_hit = (stem_e in favsup) or (branch_e in favsup)
    unfav_hit = bool(unfav) and unfav != "—" and (stem_e == unfav or branch_e == unfav)
    if fav_hit and unfav_hit:
        return "neutral"
    if fav_hit:
        return "favorable"
    if unfav_hit:
        return "unfavorable"
    return "neutral"


def _class_counts(chart) -> Counter:
    c: Counter = Counter()
    for h in chart.ten_gods:
        cls = _CLASS_OF.get(h.tengod)
        if cls:
            c[cls] += 1
    return c


def _top_classes(chart) -> List[str]:
    counts = _class_counts(chart)
    if not counts:
        return []
    top = max(counts.values())
    return [c for c in ("Companion", "Output", "Wealth", "Authority", "Resource")
            if counts.get(c, 0) == top]


# ── sections ────────────────────────────────────────────────────────────────

def _tiers_section(chart, override) -> List[str]:
    rows = _career_tiers(chart, override)
    lines = [
        "## Career Archetypes — Ranked Domains",
        "",
        "Your career archetypes are the fields the chart can carry, ranked by "
        "what it *needs* (용신 / 희신) rather than by the Day Master's own "
        "element — the classical priority in "
        "`knowledge/12-career-and-vocation.md` §용신 vs. Day Master for Career "
        "Choice is to \"align work with what the chart needs\", because work that "
        "reinforces an already-dominant element pushes the chart further out of "
        "balance. **Best Fit** = directly aligned; **Good Fit** = supportive "
        "breadth; **Possible** = workable but not strongly resourced by the "
        "chart.",
        "",
        "| Tier | Domain | Why It Fits | Example Roles |",
        "|---|---|---|---|",
    ]
    for tier, domain, why, examples in rows:
        lines.append(f"| {tier} | {domain} | {why} | {examples} |")
    lines += [
        "",
        "## Concrete Role Ladders",
        "",
        "Same domains, expanded into representative roles to aim for or hire into "
        "(modern 명리 extension of the element families — "
        "`knowledge/12-career-and-vocation.md` §Element → Industry Families).",
        "",
        "| Domain | Roles to Target |",
        "|---|---|",
    ]
    seen = set()
    for _tier, domain, _why, _ex in rows:
        if domain in seen:
            continue
        seen.add(domain)
        lines.append(f"| {domain} | {_ROLES.get(domain, '—')} |")
    lines.append("")
    lines += _domain_detail_section(chart, override, rows)
    return lines


# Element → the character of work it produces (knowledge/12 §Element → Industry
# Families; knowledge/03-five-elements.md for the nature).
_DOMAIN_ELEMENT_NOTE = {
    "Wood": ("grows something over time — it develops people, ideas or structures and keeps extending",
             "nourished into being and then feeding the next stage"),
    "Fire": ("is public-facing and expressive — it makes things seen and energises an audience",
             "maximum outward radiance that cannot act in private"),
    "Earth": ("holds, stores and mediates — it stabilises assets and provides the base others rely on",
             "the element that contains and stands between"),
    "Metal": ("demands precision, standards and clean boundaries — it refines raw material into a finished thing",
             "the element that cuts, separates and finishes"),
    "Water": ("moves information, goods or people — it connects separated things and runs below the surface",
             "the element that flows around obstacles and connects"),
}


def _domain_detail_section(chart, override, rows) -> List[str]:
    """A paragraph per ranked domain: what it is, why it fits THIS chart, how to
    use it, and how it relates to the chart's favorable/structural roles."""
    from .report_data import _domain_element

    fe = favorable_element(chart, override)
    fav, sup, unfav = fe.element, fe.supporting, fe.unfavorable
    dm_elem = chart.day_master_info.get("element", "")
    lines = [
        "## Domain Deep-Dive — Why Each Archetype Fits",
        "",
        "Each ranked archetype below is read for *this* chart: what the element "
        "family is, why the chart fits it, the practical way to use it, and the "
        "honest caveat where the fit is weaker "
        "*(see knowledge/12-career-and-vocation.md §Element → Industry Families; "
        "knowledge/03-five-elements.md)*.",
        "",
    ]
    # de-dupe domains, keeping the best (first-seen) tier label
    seen: Dict[str, str] = {}
    for tier, domain, _why, _ex in rows:
        seen.setdefault(domain, tier)
    for domain, tier in seen.items():
        elem = _domain_element(domain)
        nature, image = _DOMAIN_ELEMENT_NOTE.get(elem, ("has its own character", "its elemental nature"))
        role = _ROLES.get(domain, "—")
        # Why the chart fits — the element relation (the engine's actual reason).
        if elem == fav:
            why_elem = (f"the family runs on **{fav}**, your favorable element, so the "
                        "work moves *with* the chart's grain instead of against it")
        elif elem == sup:
            why_elem = (f"the family runs on **{sup}**, your 희신, which strengthens the "
                        "chart's balance rather than draining or feeding the Day Master")
        elif elem == dm_elem:
            why_elem = (f"the family shares your Day Master's element (**{dm_elem}**), so "
                        "it lets your native energy express directly")
        elif elem and elem == unfav:
            why_elem = (f"the family runs on **{unfav}**, your unfavorable element, which the "
                        "chart reads as pressure rather than nourishment")
        else:
            why_elem = (f"the family runs on **{elem}**, a neutral element for this chart — "
                        "neither favorable nor unfavorable on its own")

        # The practical tone is keyed on the ACTUAL ranked tier, so the prose can
        # never contradict the table above (the tier is score-based; element
        # equality alone does not determine it).
        if "Best" in tier:
            fit = f"This is a **Best Fit**: {why_elem}."
            use = ("Lean into it deliberately — this is where effort compounds fastest "
                   "and friction is lowest.")
            caveat = ("Even a favorable element can be overrun if pursued to excess; keep "
                      "other tracks alive so the chart stays balanced.")
        elif "Good" in tier:
            fit = (f"A **Good Fit**: {why_elem}. It is well resourced by the chart, just "
                   "not at the very top of the ranking.")
            use = "Treat it as a lead second track, or a strong complement to your Best-Fit work."
            caveat = ("Strong but not primary — pick it deliberately rather than by default, "
                      "and keep the favorable element in play alongside it.")
        else:
            fit = f"A **Possible** fit: {why_elem}."
            use = ("Use it only inside a supporting structure, with the favorable element "
                   "present to offset it; do not make it the core identity of the work.")
            caveat = ("The chart is not strongly resourced for this family — do not "
                      "over-invest career capital here without a reader's check.")
        lines += [
            f"### {domain} ({tier})",
            "",
            f"- **Element family:** {elem} — this family {nature} "
            f"(*{elem} {image}*, knowledge/12 §Element → Industry Families).",
            f"- **Why it fits your chart:** {fit}",
            f"- **How to use it:** {use}",
            f"- **Caveat:** {caveat}",
            f"- **Roles:** {role}",
            "",
        ]
    return lines


def _mode_section(chart, fav: str, sup: str, unfav: Optional[str], verdict: str,
                  favorable_override=None) -> List[str]:
    tops = _top_classes(chart)
    top_ko = " · ".join(_CLASS_KO.get(c, c) for c in tops) if tops else "—"
    mode_blurb = {
        "Wealth": "Business, sales, owning and growing resources — turning effort into held assets.",
        "Authority": "Institutions, licensed authority, management — operating inside accountable rank.",
        "Output": "Creating, expressing, teaching, making — producing something that goes out into the world.",
        "Resource": "Research, advisory, credentialed practice — working from accumulated learning.",
        "Companion": "Peer/team or independent operator — working alongside or against equals on one's own terms.",
    }
    blurb = " / ".join(mode_blurb.get(c, "") for c in tops) or "—"

    # Employment vs. entrepreneurship (knowledge/12).
    if verdict in ("strong", "extreme") and tops and ("Output" in tops or "Wealth" in tops):
        ent = ("Your chart leans toward the **independent / founder track**: a strong "
               "Day Master with visible Output/Wealth energy has the surplus self-energy "
               "and the produce→earn path the classics read as independent-work fit.")
    elif verdict in ("weak", "extreme_weak") or (tops and tops[0] == "Authority"):
        ent = ("Your chart leans toward **institutional employment first**: a weak or "
               "관성-led chart benefits from the structure and rank it does not generate "
               "internally. Independence can become viable later if a 대운 strengthens the self.")
    else:
        ent = ("A **hybrid** reading: the chart supports either a structured role with "
               "side output, or an independent practice with an anchor client/employer. "
               "Keep a stable base while the independent side is proven.")

    entity, env = _ENTITY_BY_ELEMENT.get(fav, ("—", "—"))
    return [
        "## Ten-God → Career Mode",
        "",
        f"Your dominant ten-god class is **{top_ko}** — {blurb} "
        "*(see knowledge/12-career-and-vocation.md §Ten-God → Career Mode)*.",
        "",
        "## Employment vs. Entrepreneurship",
        "",
        ent,
        "",
        "**Company / entity fit:** " + entity + " — " + env + " "
        "*(see knowledge/12-career-and-vocation.md §Element → Industry Families)*.",
        "",
        *_archetype_deep_dive(chart, favorable_override),
    ]


def _archetype_deep_dive(chart, override) -> List[str]:
    """The premium report's archetype deep-dive prose, reuse-assembled.

    These helpers live on a `_ReportContext`; we pass a minimal dict with the
    same keys (`chart`, `favorable`, `supporting`, `unfavorable`, `dm_element`)
    so the standalone career report carries the SAME grounded archetype detail
    the Deep tier's Career & Wealth section shows — one source of truth.

    ``override`` MUST be threaded through: without it `favorable_element()`
    resolves the engine's raw pick and the deep-dive would name a different
    element than this report's own header (the E-3 channel-split bug).
    """
    from . import prose_fillers as PF
    from .yongsin import favorable_element

    fe = favorable_element(chart, override)
    ctx = {
        "chart": chart,
        "favorable": fe.element,
        "supporting": fe.supporting,
        "unfavorable": fe.unfavorable or "the challenging element",
        "dm_element": chart.day_master_info.get("element", ""),
        "tier": "deep",
    }
    return [
        "## Archetype Deep-Dive",
        "",
        "### Wealth Pattern",
        "",
        PF.wealth_pattern(ctx),
        "",
        "### Income Rhythm",
        "",
        PF.income_rhythm(ctx),
        "",
        "### Skill-Levers to Develop",
        "",
        PF.skill_levers(ctx),
        "",
        "### Company-Type Fit",
        "",
        PF.company_type_fit(ctx),
        "",
        "### Boss / Team Dynamics",
        "",
        PF.boss_team_dynamics(ctx),
        "",
        "### Red-Flag Environments",
        "",
        PF.red_flag_environments(ctx),
        "",
    ]


def _wealth_section(chart, fav: str, sup: str, unfav: Optional[str], override) -> List[str]:
    kinds = {h.tengod for h in chart.ten_gods}
    has_direct, has_indirect = "정재" in kinds, "편재" in kinds
    if has_direct and has_indirect:
        style = ("**Mixed 재성 (재성 혼잡)** — income comes from a base plus variable "
                 "upside; stabilising if the Day Master can carry it, scattering if not.")
    elif has_indirect:
        style = ("**편재-weighted** — deal-making, commissions, trading and several "
                 "streams suit you better than one fixed source; higher variance, "
                 "comfortable with opportunity capture.")
    elif has_direct:
        style = ("**정재-weighted** — salary, steady cash flow, savings and disciplined "
                 "revenue; low variance, natural concentration in one reliable source.")
    else:
        style = ("**No visible 재성 on a stem** — wealth routes through the output / "
                 "resource channels rather than a direct wealth stem; trace the money "
                 "path through hidden stems and timing.")

    # Carrying capacity (knowledge/13 §Can the Day Master Hold Wealth).
    verdict = (chart.strength_assessment or {}).get("verdict", "balanced")
    if verdict in ("weak", "extreme_weak"):
        carry = ("Weak Day Master — the classics read heavy 재성 as a burden "
                 "(재다신약): money flows in but is hard to retain. **Strengthen the "
                 "self first** (인성/비겁: study, credentials, trusted peers) before "
                 "carrying a heavy wealth load.")
    elif verdict in ("strong", "extreme"):
        carry = ("Strong Day Master — you can carry 재성 and 관성 directly; wealth that "
                 "comes in can be held. The caution is not to hold *beyond* what the "
                 "chart supports — diversify so no single loss is structural.")
    else:
        carry = ("Balanced Day Master — carrying capacity is adequate but not unlimited; "
                 "favour custodianship aligned with your favorable element over "
                 "concentrated bets.")

    # Partnership risk: any Companion in the natal visible/hidden stems.
    comp = _class_counts(chart).get("Companion", 0)
    partnership = (
        f"Your chart carries **{comp} 비겁 (Companion)** stems — the 겁재奪財 pattern "
        "reads shared and loosely-defined money as contested. Put ownership "
        "percentages in writing, keep separate accounts, and prefer sole operation or "
        "hard-boundary partnerships *(see knowledge/13-wealth-and-business.md "
        "§겁재奪財)*."
        if comp else
        "Little natal 비겁, so the 겁재奪財 partnership risk is not natal — it still "
        "arrives with any 비겁 대운/세운, where shared-money agreements should be made "
        "explicit *(see knowledge/13-wealth-and-business.md §겁재奪財)*."
    )

    return [
        "## Income Style & Carrying Capacity",
        "",
        f"**Income style:** {style} "
        "*(see knowledge/13-wealth-and-business.md §정재 vs. 편재)*",
        "",
        f"**Carrying capacity:** {carry} "
        "*(see knowledge/13-wealth-and-business.md §Can the Day Master Hold Wealth)*",
        "",
        f"**Partnership & shared-money risk:** {partnership}",
        "",
        "## Investment Behaviour",
        "",
        _investment_behaviour(fav, sup, unfav, carry),
        "",
        "## Wealth Preservation",
        "",
        _preservation(verdict, fav),
        "",
    ]


def _investment_behaviour(fav: str, sup: str, unfav: Optional[str], carry: str) -> str:
    return (
        f"Plan and negotiate in periods running **{fav}** / **{sup}**; treat years "
        f"dominated by **{unfav}** as conservation, review and patience rather than "
        "expansion. Large, long-term commitments (property, deeds, contracts) key to "
        "**인성 (Resource)** in the classics — prefer placing them where 인성 is active "
        "*and* the year runs the favorable element, not in a bare 재성 year. "
        "Storehouse (재고) charts accumulate quietly and release in bursts: be ready "
        "for the release windows rather than expecting steady flow. This describes "
        "stewardship *tendencies*, not investment instructions "
        "*(see knowledge/13-wealth-and-business.md §Investment / §재고)*."
    )


def _preservation(verdict: str, fav: str) -> str:
    if verdict in ("weak", "extreme_weak"):
        return ("Prioritise **retention over acquisition** — fewer, simpler holdings; "
                "strengthen the self (study, credentials, trusted peers) before taking "
                "on more *(see knowledge/13-wealth-and-business.md §Wealth Preservation)*.")
    return ("Favour custodianship aligned with your favorable element and diversify "
            "enough that no single loss is structural; in 비겁/기신 periods, **defend "
            "rather than expand** *(see knowledge/13-wealth-and-business.md §Wealth Preservation)*.")


def _timing_section(chart, fav: str, sup: str, unfav: Optional[str],
                    override) -> List[str]:
    lines = [
        "## Career Transition Timing — Decade by Decade",
        "",
        "Each 10-year major-luck period (대운) is read from its own ten-god theme plus "
        "the favorable balance of the annual pillars inside it "
        "*(see knowledge/08-luck-pillars.md)*.",
        "",
        "| Calendar years | Ages | Decade | Ten-God | Favorable years | Read |",
        "|---|---|---|---|---|---|",
    ]
    rows = []
    for i, p in enumerate(chart.daeun):
        ys, ye = _decade_year_range(chart, i)
        years = list(range(ys, ye))
        fav_n = unfav_n = 0
        for y in years:
            hit = derive_sewoon(chart.day_master, chart.branches, y, 7, 1,
                                natal_stems=chart.stems)
            se = L.STEM_INFO.get(hit.stem, {}).get("element", "")
            be = L.BRANCH_ELEMENT.get(hit.branch, "")
            st = _year_status(se, be, fav, sup, unfav)
            fav_n += st == "favorable"
            unfav_n += st == "unfavorable"
        # Ten years per decade, so a real majority (not a 2-vs-0 margin)
        # decides the read.
        if fav_n >= 6 and fav_n > unfav_n:
            read = "expansion window"
        elif unfav_n >= 6 and unfav_n > fav_n:
            read = "consolidation / defend"
        else:
            read = "steady build"
        tg = p.stem_tengod_en or p.stem_tengod
        lines.append(
            f"| {ys}–{ye} | {p.start_age}–{p.end_age} | {p.combined} | {tg} "
            f"| {fav_n}/10 | {read} |"
        )
        rows.append((p, ys, ye, tg, fav_n, unfav_n, read))

    lines += ["", "### Period Notes", ""]
    for p, ys, ye, tg, fav_n, unfav_n, read in rows:
        cls = _CLASS_OF.get(p.stem_tengod, "")
        if cls == "Resource":
            note = ("a learning, credential or advisory decade — build depth and "
                    "authority before converting it into output.")
        elif cls == "Output":
            note = ("an output decade — craft, expression and production lead; the "
                    "식상생재 path (produce → earn) is most available here.")
        elif cls == "Wealth":
            note = ("a wealth-activity decade — earning, spending and money decisions "
                    "rise; whether it is net favourable depends on Day-Master strength.")
        elif cls == "Authority":
            note = ("an authority decade — institution, rank, licensing or management; "
                    "structure and pressure arrive together.")
        elif cls == "Companion":
            note = ("a peer/competition decade — work alongside equals; keep ownership "
                    "boundaries explicit (겁재奪財 risk on shared money).")
        else:
            note = "read from the annual pillars above."
        lines.append(
            f"- **Ages {p.start_age}–{p.end_age} ({ys}–{ye}) — {p.combined} "
            f"({tg}):** {note} Favorable years **{fav_n}/10**."
        )
    lines += ["", "---", ""]
    return lines


# ── top-level ───────────────────────────────────────────────────────────────

def generate_career_report(chart, *, favorable_override: Optional[str] = None) -> str:
    """Render the career / business / wealth deep-dive as markdown."""
    fe = favorable_element(chart, favorable_override)
    fav, sup, unfav = fe.element, fe.supporting, fe.unfavorable
    verdict = (chart.strength_assessment or {}).get("verdict", "balanced")
    name = chart.name or "Client"

    lines: List[str] = [
        f"# {name} — Career, Business & Wealth Deep-Dive",
        "",
        f"**Born:** {chart.birth_date} · {chart.birth_time} · {chart.city or '—'}  ",
        f"**Day Master:** {chart.day_master}  ",
        f"**Strength:** {_verdict_label(verdict)}  ",
        f"**Favorable (용신):** {fav} · **Supporting (희신):** {sup}"
        + (f" · **Unfavorable (기신):** {unfav}" if unfav else ""),
        "",
        "A full career, business and wealth deep-dive: ranked domains and role "
        "ladders, working mode, income style, carrying capacity, investment "
        "behaviour, and a decade-by-decade transition timeline. Read the "
        "rankings as *fits and tendencies*, not destiny "
        "*(see knowledge/12-career-and-vocation.md §Scope & Limits)*.",
        "",
        "---",
        "",
    ]
    lines += _tiers_section(chart, favorable_override)
    lines += [
        "---",
        "",
    ]
    lines += _mode_section(chart, fav, sup, unfav, verdict, favorable_override)
    lines += [
        "---",
        "",
    ]
    lines += _wealth_section(chart, fav, sup, unfav, favorable_override)
    lines += [
        "---",
        "",
    ]
    lines += _timing_section(chart, fav, sup, unfav, favorable_override)
    lines += [
        "## Sources & Limits",
        "",
        "- Method: `knowledge/12-career-and-vocation.md` (career mode, earning "
        "vehicle, employment vs. entrepreneurship), "
        "`knowledge/13-wealth-and-business.md` (income style, carrying capacity, "
        "겁재奪財, 재고, preservation), `knowledge/08-luck-pillars.md` (대운/세운 "
        "timing).",
        "- This reading describes tendencies, not fixed outcomes; it is for "
        "reflection and entertainment — not career, financial, investment or "
        "business advice.",
        "- Domain ranking follows the classical 용신/희신 priority; the role "
        "ladders and entity fit are modern 명리 extensions of the element "
        "families, illustrative rather than exhaustive.",
    ]
    return "\n".join(lines) + "\n"


def _verdict_label(verdict: str) -> str:
    return {"extreme_weak": "Very Weak"}.get(verdict, verdict.title())
