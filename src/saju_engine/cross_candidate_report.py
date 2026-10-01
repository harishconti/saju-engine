"""Cross-candidate business / partnership analysis.

Produces a client-facing markdown deep-dive for a small group of people who
are considering a joint business. It is NOT a natal reading and NOT a marriage
궁합 — it reads the group through three lenses that already exist in the
engine:

1. **Pairwise 궁합** (`compat.compat_score`) — the 11 sub-systems, used here for
   partnership-style interaction (trust, friction, spouse-palace and luck-pillars
   synchrony), not for marriage.
2. **Career domain fit** (`report_data._career_tiers`) — each person's ranked
   domains from their own 용신/희신.
3. **Five-year luck blocks** (`luck_cycle_report._build_blocks`) — the concrete
   세운 inside each 대운, so the report can say *when* the group's cycles align.

It also states the group's **coverage gap** honestly: which classical function
(목/화/토/금/수 → planner / face / operator / quality / audience) no member
supplies, and the shared-money risk (겁재奪財, knowledge/13) that a
비겁-heavy group carries.

Every interpretive claim cites a file under `knowledge/`; citations stay in the
`.md` and are stripped from client PDFs by `saju_html`.

This is decision support, not advice. The module is generic over the member
list and relationship labels; the canonical trio + relationships live in the
`tools/gen_cross_candidate_report.py` driver.
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Sequence, Tuple

from .compat import compat_score
from .luck_cycle_report import _build_blocks, _CLASS_KO
from .report_data import _career_tiers
from .yongsin import favorable_element

_RELATION_LABEL = {
    "siblings": "siblings",
    "spouses": "husband & wife",
    "co-founders": "co-founders",
    "mentor-mentee": "mentor & mentee",
}

# Element → the functional role it plays inside a small team
# (knowledge/05-ten-gods.md §The Five Classes; knowledge/12 §Ten-God → Career Mode).
_ELEMENT_ROLE = {
    "Wood": "Planner / brand-story / learning — long-horizon growth and design",
    "Fire": "Leader / public face / brand charisma — the visible, energising front",
    "Earth": "Operator / producer / asset-holder — the tangible base and delivery",
    "Metal": "Quality / finance / structure / compliance — the refining discipline",
    "Water": "Audience / communication / regulation / flow — the information and market layer",
}
# Which ten-god class each element is to a typical Day Master is chart-specific,
# so the *class* role map below is keyed on the member's dominant class instead.
_CLASS_ROLE = {
    "Wealth": "commercial lead — pricing, deals, resource stewardship",
    "Authority": "institution / structure lead — process, rank, accountability",
    "Output": "product / craft lead — what the venture makes and says",
    "Resource": "research / advisory lead — depth, credentials, the knowledge base",
    "Companion": "network / team lead — relationships, peers, coalition-building",
}
_CLASS_ORDER = ["Companion", "Output", "Wealth", "Authority", "Resource"]


# ── small helpers ───────────────────────────────────────────────────────────

def _class_counts(chart) -> Counter:
    counts: Counter = Counter()
    for h in chart.ten_gods:
        cls = {
            "비견": "Companion", "겁재": "Companion",
            "식신": "Output", "상관": "Output",
            "편재": "Wealth", "정재": "Wealth",
            "편관": "Authority", "정관": "Authority",
            "편인": "Resource", "정인": "Resource",
        }.get(h.tengod)
        if cls:
            counts[cls] += 1
    return counts


def _best_fit(chart, override) -> List[str]:
    return [d for t, d, _w, _e in _career_tiers(chart, override) if "Best" in t]


def _good_fit(chart, override) -> List[str]:
    return [d for t, d, _w, _e in _career_tiers(chart, override)
            if "Best" in t or "Good" in t]


def _lean_of(block) -> str:
    if block.fav_years - block.unfav_years >= 2:
        return "favorable"
    if block.unfav_years - block.fav_years >= 2:
        return "challenging"
    return "mixed"


def _blocks(chart, override) -> List:
    fe = favorable_element(chart, override)
    return _build_blocks(chart, fe.element, fe.supporting, fe.unfavorable)


def _blocks_by_year(blocks) -> Dict[int, str]:
    out: Dict[int, str] = {}
    for b in blocks:
        for y in b.years:
            out[y] = _lean_of(b)
    return out


_LEAN_RANK = {"favorable": 2, "mixed": 1, "challenging": 0}


# ── sections ────────────────────────────────────────────────────────────────

def _header(members, relationships, reference_date: str) -> List[str]:
    names = [m["name"] for m in members]
    rel_txt = "; ".join(
        f"{r['a']} & {r['b']} are {_RELATION_LABEL.get(r['kind'], r['kind'])}"
        for r in relationships
    )
    return [
        f"# Cross-Candidate Business Analysis — {', '.join(names)}",
        "",
        f"**Reference date:** {reference_date}  ",
        f"**Group:** {', '.join(names)}  ",
        f"**Relationships:** {rel_txt}  ",
        "**Status:** Observational decision-support. Not a binding recommendation "
        "or financial/legal advice. Elemental-affinity based; skills, capital, "
        "health and life circumstances are not factors.",
        "",
        "This report asks one question: **are these people a good business "
        "group, and if so for what, in what roles, and when?** It reads the "
        "group through three engine layers — pairwise 궁합 "
        "(`knowledge/11-gunghap.md`, used for partnership interaction, not "
        "marriage), each person's career-domain fit (`knowledge/12-career-and-"
        "vocation.md`) and their five-year luck blocks "
        "(`knowledge/08-luck-pillars.md`). Negatives are stated as plainly as "
        "positives.",
        "",
        "---",
        "",
    ]


def _charts_at_a_glance(members) -> List[str]:
    lines = [
        "## 1. The Charts at a Glance",
        "",
        "| Member | Day Master | Four Pillars | Strength | 용신 | 희신 | 기신 | Dominant class |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for m in members:
        c, ov = m["chart"], m["override"]
        fe = favorable_element(c, ov)
        tops = _dominant_classes_for(c)
        top_ko = " / ".join(_CLASS_KO.get(t, t) for t in tops) or "—"
        verdict = (c.strength_assessment or {}).get("verdict", "balanced")
        lines.append(
            f"| {m['name']} | {c.day_master} | {c.year.combined}·{c.month.combined}·"
            f"{c.day.combined}·{c.hour.combined} | {verdict.title()} | {fe.element} "
            f"| {fe.supporting} | {fe.unfavorable or '—'} | {top_ko} |"
        )
    lines += [
        "",
        "The Day Master is the reference point; the 용신 (favorable element) is "
        "what each chart *needs*, and the dominant ten-god class is how each "
        "person naturally works *(see knowledge/05-ten-gods.md)*.",
        "",
        "---",
        "",
    ]
    return lines


def _dominant_classes_for(c) -> List[str]:
    counts = _class_counts(c)
    if not counts:
        return []
    top = max(counts.values())
    return [k for k in _CLASS_ORDER if counts.get(k, 0) == top]


def _pairwise(members, names) -> List[str]:
    lines = ["## 2. Pairwise Partnership Compatibility", ""]
    lines += [
        "Each pair is scored by the engine's 11 궁합 sub-systems "
        "*(see knowledge/11-gunghap.md §Composite Weight)*. This is the engine's "
        "own compatibility engine; a high score means the two charts interact "
        "smoothly, **not** that they should marry or partner — trust and friction "
        "are read from the day-branch (spouse/palace) and the luck-pillar "
        "synchrony in particular. **In every pair, A = the first name in the "
        "heading (the reference chart) and B = the second.**",
        "",
    ]
    by_name = {m["name"]: m for m in members}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = by_name[names[i]], by_name[names[j]]
            r = compat_score(a["chart"], b["chart"],
                             favorable_element_a=a["override"],
                             favorable_element_b=b["override"])
            lines += [
                f"### 2.{i + j}. {names[i]} × {names[j]} — {r.score}/100 ({r.band})",
                "",
                "| Sub-system | Score | Band |",
                "|---|---|---|",
            ]
            for s in r.sub_systems():
                lines.append(f"| {s.label} | {s.score} / {s.max} | {s.band} |")
            lines.append("")
            if r.red_flags:
                lines.append("**Red flags (structural tensions):**")
                lines += [f"- {f}" for f in r.red_flags]
                lines.append("")
            if r.yellow_flags:
                lines.append("**Yellow flags (watch):**")
                lines += [f"- {f}" for f in r.yellow_flags]
                lines.append("")
            if r.favorable_points:
                lines.append("**Positives:**")
                lines += [f"- {f}" for f in r.favorable_points]
                lines.append("")
    lines += ["---", ""]
    return lines


def _role_coverage(members) -> List[str]:
    lines = [
        "## 3. Element & Role Coverage — Who Supplies What",
        "",
        "A small founding team needs five functions: a **planner** (Wood), a "
        "**public face** (Fire), an **operator/asset-holder** (Earth), a "
        "**quality/finance anchor** (Metal) and an **audience/communication/"
        "regulatory** function (Water) *(see knowledge/05-ten-gods.md §The Five "
        "Classes; knowledge/12-career-and-vocation.md §Ten-God → Career Mode)*. "
        "The table below maps each member to the functions their chart naturally "
        "supplies, from their 용신/희신 and dominant class.",
        "",
        "| Member | Supplies (favorable function) | Works as (dominant-class role) |",
        "|---|---|---|",
    ]
    supplied_elements: set = set()
    for m in members:
        c, ov = m["chart"], m["override"]
        fe = favorable_element(c, ov)
        funcs = []
        for e in (fe.element, fe.supporting):
            if e and e != "—":
                supplied_elements.add(e)
                funcs.append(f"**{e}** — {_ELEMENT_ROLE.get(e, '')}")
        tops = _dominant_classes_for(c)
        roles = "; ".join(
            f"{_CLASS_KO.get(t, t)}: {_CLASS_ROLE.get(t, '')}" for t in tops
        ) or "—"
        lines.append(f"| {m['name']} | " + " · ".join(funcs) + f" | {roles} |")
    lines.append("")

    all_elements = set(_ELEMENT_ROLE)
    missing = sorted(all_elements - supplied_elements)
    lines += [
        "### The Coverage Gap",
        "",
    ]
    if missing:
        for e in missing:
            lines.append(
                f"- **{e} is not supplied by any member's 용신/희신** — "
                f"{_ELEMENT_ROLE.get(e, '')}"
            )
        lines.append("")
    covered = sorted(supplied_elements)
    lines += [
        f"**Covered by the group:** {', '.join(covered) if covered else '—'}.  ",
        f"**Missing:** {', '.join(missing) if missing else 'nothing — full coverage'}.  ",
        "",
        "A missing function is not fatal — it is a **hiring brief**. The "
        "classical caution is to *staff*, not to force, the gap "
        "*(see knowledge/12-career-and-vocation.md §Element → Industry Families)*.",
        "",
        "---",
        "",
    ]
    return lines


def _domain_fit(members) -> List[str]:
    lines = [
        "## 4. Domain Fit — Where the Group Can Actually Operate",
        "",
        "Each member's ranked career domains come from their own 용신/희신 "
        "*(see knowledge/12-career-and-vocation.md §용신 vs. Day Master for "
        "Career Choice)*. **Best Fit** = directly aligned; **Good Fit** = "
        "supportive breadth.",
        "",
        "| Member | Best-Fit domains | Good-Fit domains (incl. Best) |",
        "|---|---|---|",
    ]
    per = {}
    for m in members:
        c, ov = m["chart"], m["override"]
        best = _best_fit(c, ov)
        good = _good_fit(c, ov)
        per[m["name"]] = set(good)
        lines.append(
            f"| {m['name']} | {', '.join(best) or '—'} | {', '.join(good) or '—'} |"
        )
    lines.append("")

    names = [m["name"] for m in members]
    inter_all = set.intersection(*per.values()) if per else set()
    lines += [
        "### Overlap Analysis",
        "",
    ]
    if inter_all:
        lines.append(
            f"**Domains that are a Good-or-better fit for all members:** "
            f"{', '.join(sorted(inter_all))}."
        )
    else:
        lines.append(
            "**No domain is a Good-or-better fit for every member at once.** "
            "This is the central structural fact of the group: the members' "
            "favorable families do not overlap completely, so a venture cannot "
            "be 'one person's top domain' and expect the others to be equally "
            "aligned — each member contributes a *function*, not a shared "
            "domain label."
        )
    lines.append("")
    pairs = [(names[i], names[j]) for i in range(len(names))
             for j in range(i + 1, len(names))]
    shared_by_pair = {p: sorted(per[p[0]] & per[p[1]]) for p in pairs}
    best_pair = max(pairs, key=lambda p: len(shared_by_pair[p])) if pairs else None
    for (a, b) in pairs:
        shared = shared_by_pair[(a, b)]
        if shared:
            tag = " *(the pairing that shares the most domain-fit)*" if (a, b) == best_pair else ""
            lines.append(f"- **{a} ∩ {b}:** {', '.join(shared)}{tag}")
        else:
            lines.append(
                f"- **{a} ∩ {b}:** no shared Good-fit domain — they complement "
                "through *roles*, not a common domain."
            )
    lines += ["", "---", ""]
    return lines


def _venture_options(members) -> List[str]:
    """Derive a small set of element-coherent venture shapes from the roles."""
    name_by_elem: Dict[str, List[str]] = {}
    for m in members:
        fe = favorable_element(m["chart"], m["override"])
        for e in (fe.element, fe.supporting):
            if e and e != "—":
                name_by_elem.setdefault(e, []).append(m["name"])
    earth = name_by_elem.get("Earth", [])
    metal = name_by_elem.get("Metal", [])
    water = name_by_elem.get("Water", [])
    fire = name_by_elem.get("Fire", [])

    lines = [
        "## 5. Venture Shapes That Fit the Group",
        "",
        "Because no single domain fits all members, the viable ventures are "
        "**element blends** — each member supplies the function their chart "
        "naturally carries. Two shapes survive scrutiny from the data above:",
        "",
        "### Venture A — Asset-backed operations (Earth base + Metal finance + Fire face)",
        "",
        f"- **Earth base (operator / asset-holder):** "
        f"{', '.join(earth) if earth else 'no member supplies Earth as a favorable function — this is a gap'} "
        "— real assets, hospitality, property, agri-land, delivery operations.",
        f"- **Metal finance / quality anchor:** {', '.join(metal) if metal else '—'} "
        "— unit economics, compliance, contracts, audit.",
        f"- **Fire face / leadership:** {', '.join(fire) if fire else '—'} "
        "— the public face, deal-closing, brand energy, leadership.",
        "",
        "This is the shape the group's elements most naturally support: a "
        "tangible, income-generating base run with disciplined finance and a "
        "visible front *(see knowledge/13-wealth-and-business.md §Wealth "
        "Preservation; knowledge/12-career-and-vocation.md §Employment vs. "
        "Entrepreneurship)*.",
        "",
        "### Venture B — Advisory / strategy / logistics (Water + Metal, audience-facing)",
        "",
        f"- **Water strategy / communication:** {', '.join(water) if water else '—'} "
        "— consulting, research, information, trade, logistics, media.",
        f"- **Metal structure:** {', '.join(metal) if metal else '—'} "
        "— methodology, quality, finance.",
        "This shape leans on the members whose favorable families are "
        "Water/Metal; a member whose favorable family is Earth/Fire is the "
        "**audience/leadership** contributor here, not the technical lead.",
        "",
        "**Honest limitation:** neither shape is a natural top-fit for every "
        "member. Whichever is chosen, at least one founder is operating outside "
        "their Best-Fit domain and must accept a functional (not equal-fit) role "
        "— see §6.",
        "",
        "---",
        "",
    ]
    return lines


# Seats keyed on the member's DOMINANT ten-god class (how they work), which is
# what differentiates members who share the same favorable element. Preference
# order per class; allocation is greedy so seats stay distinct.
_SEAT_BY_CLASS = {
    "Companion": ("Business development / partnerships / network lead",
                  "spreads thin across too many relationships — pick a lane"),
    "Output": ("Product / craft / marketing lead",
               "produces without pricing — pair with the finance seat"),
    "Wealth": ("Commercial / pricing / resource lead",
               "chases activity; keep the unit economics the gate"),
    "Authority": ("Operations / process / compliance lead",
                  "over-formalises; keep the process proportionate"),
    "Resource": ("Research / advisory / quality lead",
                 "studies past the ship date — pair with the product seat"),
}
_SEAT_FALLBACK = {
    "Earth": ("Operations / asset & property lead",
              "avoid over-concentration in slow, illiquid assets"),
    "Metal": ("CFO / quality, compliance & contracts",
              "can over-audit; keep the standard proportionate"),
    "Water": ("Strategy / business development / communications",
              "spreads thin across too many streams — pick a lane"),
    "Fire": ("CEO / public face / brand & partnerships",
             "impulse to over-expose; pair with the finance seat"),
    "Wood": ("Planning / product & brand-story / training",
             "plans without shipping — pair with the operator seat"),
}


def _role_matrix(members) -> List[str]:
    lines = [
        "## 6. Role Assignment",
        "",
        "Roles follow each member's **dominant class** (how they work) and "
        "**favorable element** (what they supply), not seniority. Seats are "
        "allocated distinctly — two members who both run on Water/Metal are "
        "differentiated by their dominant class, not given the same chair.",
        "",
        "| Member | Dominant class | Favorable function | Recommended seat | Watch-out |",
        "|---|---|---|---|---|",
    ]
    # Allocation: (1) the seat matching the member's favorable element — what
    # they naturally supply; (2) if taken, the seat matching their dominant
    # class — how they work; (3) the supporting-element seat. Distinct seats.
    seats: Dict[str, Tuple[str, str]] = {}
    used: set = set()
    for m in members:
        c, ov = m["chart"], m["override"]
        fe = favorable_element(c, ov)
        tops = _dominant_classes_for(c)
        candidates = []
        if fe.element in _SEAT_FALLBACK:
            candidates.append(_SEAT_FALLBACK[fe.element])
        for cls in tops:
            if cls in _SEAT_BY_CLASS:
                candidates.append(_SEAT_BY_CLASS[cls])
        if fe.supporting in _SEAT_FALLBACK:
            candidates.append(_SEAT_FALLBACK[fe.supporting])
        candidates.append(("Generalist — assign by task", "—"))
        seat, watch = next(
            (s for s in candidates if s[0] not in used), candidates[-1]
        )
        used.add(seat)
        seats[m["name"]] = (seat, watch)

    for m in members:
        c, ov = m["chart"], m["override"]
        fe = favorable_element(c, ov)
        tops = _dominant_classes_for(c)
        top_ko = " / ".join(_CLASS_KO.get(t, t) for t in tops) if tops else "—"
        seat, watch = seats[m["name"]]
        lines.append(
            f"| {m['name']} | {top_ko} | {fe.element}/{fe.supporting} | {seat} | {watch} |"
        )
    lines += ["", "---", ""]
    return lines


def _luck_section(members, reference_date: str) -> List[str]:
    names = [m["name"] for m in members]
    by_year: Dict[str, Dict[int, str]] = {}
    for m in members:
        by_year[m["name"]] = _blocks_by_year(_blocks(m["chart"], m["override"]))

    years = sorted({y for d in by_year.values() for y in d})
    years = [y for y in years if y >= int(reference_date[:4])][:35]

    lines = [
        "## 7. Five-Year Luck-Cycle Effect on the Venture",
        "",
        "Each member's five-year block lean (from the concrete annual pillars in "
        "their 대운) is shown below *(see knowledge/08-luck-pillars.md Part 5 — "
        "'a trigger is most powerful when all three layers point in the same "
        "direction')*. **F** = favorable, **M** = mixed, **C** = challenging.",
        "",
        "| Year | " + " | ".join(names) + " | Group |",
        "|---|" + "---|" * (len(names) + 1),
    ]
    window_scores = []
    for y in years:
        cells = [by_year[n].get(y, "—") for n in names]
        ranks = [_LEAN_RANK.get(c, 1) for c in cells]
        total = sum(ranks)
        if all(r == 2 for r in ranks):
            group = "**full alignment**"
        elif all(r >= 1 for r in ranks):
            group = "workable"
        elif sum(1 for r in ranks if r == 0) >= 2:
            group = "stalled"
        else:
            group = "partial"
        window_scores.append((y, total, group))
        lines.append(f"| {y} | " + " | ".join(c[:1].upper() if c != '—' else '—' for c in cells)
                     + f" | {group} |")
    lines += [""]

    full = [y for y, _t, g in window_scores if g == "**full alignment**"]
    workable = [y for y, _t, g in window_scores if g == "workable"]
    stalled = [y for y, _t, g in window_scores if g == "stalled"]
    best = sorted(workable + full)[:6]

    lines += ["### Reading the Windows", ""]
    if full:
        lines.append(
            f"- **Full three-way alignment:** {full[0]}–{full[-1] if len(full) > 1 else full[0]} "
            "— every member's cycle is favorable. This is the strongest strategic "
            "window in the horizon; plan major commitments around it."
        )
    else:
        lines.append(
            "- **No year in the horizon has all members favorable at once** — "
            "there is no 'everyone is strong' window, so the group must decide "
            "with someone always in a mixed or challenging phase."
        )
    if workable:
        lines.append(
            f"- **Workable years (nobody challenged):** {', '.join(str(y) for y in workable)}."
        )
    if stalled:
        lines.append(
            f"- **Stalled years (two or more members challenged):** "
            f"{', '.join(str(y) for y in stalled)} — avoid capital deployment, "
            "major hiring or new-market pushes here."
        )
    if best:
        lines.append(
            f"- **Recommended action windows:** {', '.join(str(y) for y in best)} — "
            "sequence launches, fundraising and expansion into these."
        )
    lines += [
        "",
        "The per-member five-year detail (the five annual pillars, wealth/business/"
        "family/investment notes in each block) is in each member's own "
        "luck-cycle report.",
        "",
        "---",
        "",
    ]
    return lines


def _missing_section(members) -> List[str]:
    supplied: Dict[str, List[str]] = {}
    for m in members:
        fe = favorable_element(m["chart"], m["override"])
        for e in (fe.element, fe.supporting):
            if e and e != "—":
                supplied.setdefault(e, []).append(m["name"])
    missing = sorted(set(_ELEMENT_ROLE) - set(supplied))

    # 겁재奪財 exposure: count Companion-class members.
    comp_members = [m["name"] for m in members
                    if _class_counts(m["chart"]).get("Companion", 0) >= 3]

    lines = [
        "## 8. What Is Missing",
        "",
        "Stated plainly — these are the group's structural gaps, not cosmetic "
        "observations.",
        "",
    ]
    if missing:
        for e in missing:
            lines.append(f"- **{e} function absent** ({_ELEMENT_ROLE.get(e, '')}): "
                         "hire or partner this in; do not improvise it.")
    else:
        lines.append("- **No element function is wholly absent** — all five "
                     "are carried by at least one member's favorable set.")
    lines += [
        "",
        f"- **Shared-money risk (겁재奪財) is the top internal hazard.** "
        f"{len(comp_members)} of {len(members)} members "
        f"({', '.join(comp_members) if comp_members else 'none'}) carry three or "
        "more 비겁 (Companion) stems. The classical reading is that the Companion "
        "class competes for the same 재성 — **financial loss and partnership "
        "breakdown, especially where money is shared**: family businesses, pooled "
        "investments, informal lending among peers "
        "*(see knowledge/13-wealth-and-business.md §겁재奪財)*.",
        "- **Capital depth.** No member is 재성 (Wealth)-*dominant* — the "
        "funding call is a business problem, not a chart strength. The "
        "Companion-heavy charts also raise the cost of *shared* capital.",
        "- **A single decisive leader.** All members read balanced rather than "
        "strong; the Fire/public-face seat is the closest to a natural leader, "
        "but decision-rights must be written, not assumed.",
        "- **Conflict management.** The red flags in §2 (day-branch 충/해 and one "
        "broken day-stem combination) are the specific fault lines; name them in "
        "the operating agreement before money moves.",
        "",
        "### Structural Mitigations (knowledge/13 §겁재奪財)",
        "",
        "- Put **roles and ownership percentages in writing** before any money "
        "moves; the sibling and spouse pairings make informal assumptions likely.",
        "- Keep **separate accounts**; never commingle personal, family and "
        "venture funds.",
        "- Earn through a **structured product or service with clear pricing**, "
        "not informal arrangements.",
        "- Prefer **hard-boundary roles** over loosely-shared P&L; the group can "
        "collaborate without a shared wallet.",
        "- Treat any **비겁/기신 decade** (see each member's luck-cycle report) as "
        "a period to **defend rather than expand** shared commitments.",
        "",
        "---",
        "",
    ]
    return lines


def _verdict(members, names) -> List[str]:
    # Recompute pairwise quickly for a summary line.
    by = {m["name"]: m for m in members}
    scores = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            r = compat_score(by[names[i]]["chart"], by[names[j]]["chart"],
                             favorable_element_a=by[names[i]]["override"],
                             favorable_element_b=by[names[j]]["override"])
            scores[(names[i], names[j])] = (r.score, r.band)
    lines = [
        "## 9. Verdict",
        "",
        "| Pair | Score | Band |",
        "|---|---|---|",
    ]
    for (a, b), (s, band) in scores.items():
        lines.append(f"| {a} × {b} | {s}/100 | {band} |")
    lines += [
        "",
        "**Are they a good business group?** The pairwise data says: the bond is "
        "real and the elements are complementary, **but it is a group that must "
        "be structured, not a group that can be left informal.** Every pair shows "
        "a hard red flag in the palace/branch layer while the *combined element "
        "balance* is strong in all three pairs — the charts want to work together "
        "and will also rub where it matters most (money and authority).",
        "",
        "- **Strengths:** complementary element roles; strong combined-element "
        "balance in every pairing; at least one clear alignment window "
        "(see §7).",
        "- **Weaknesses:** a shared-money red flag from the Companion-heavy "
        "charts; no shared Best-Fit domain; no all-favorable year in the near "
        "horizon; specific branch clash/harm fault lines between each pair.",
        "- **The single most actionable insight:** decide the venture's **one "
        "shared domain and one person's decisive seat** in writing *before* "
        "capital moves — the charts support the work, and the risk is entirely in "
        "the shared-money governance.",
        "",
        "---",
        "",
    ]
    return lines


def generate_cross_candidate_report(
    members: Sequence[Dict],
    relationships: Sequence[Dict],
    *,
    reference_date: str = "2026-09-26",
) -> str:
    """Render the cross-candidate business analysis as markdown.

    ``members``: list of dicts with keys ``name``, ``chart``, ``override``
    (element or None). ``relationships``: list of dicts with ``a``, ``b``,
    ``kind`` ∈ {siblings, spouses, co-founders, mentor-mentee}.
    """
    names = [m["name"] for m in members]
    lines: List[str] = []
    lines += _header(members, relationships, reference_date)
    lines += _charts_at_a_glance(members)
    lines += _pairwise(members, names)
    lines += _role_coverage(members)
    lines += _domain_fit(members)
    lines += _venture_options(members)
    lines += _role_matrix(members)
    lines += _luck_section(members, reference_date)
    lines += _missing_section(members)
    lines += _verdict(members, names)
    lines += [
        "## Sources & Limits",
        "",
        "- Method: `knowledge/11-gunghap.md` (pairwise sub-systems, used here for "
        "partnership interaction), `knowledge/12-career-and-vocation.md` (career "
        "mode, earning vehicle, employment vs. entrepreneurship), "
        "`knowledge/13-wealth-and-business.md` (income style, carrying capacity, "
        "겁재奪財, 재고, preservation), `knowledge/08-luck-pillars.md` (대운/세운 "
        "timing), `knowledge/05-ten-gods.md` (the five classes and their "
        "functional roles).",
        "- This is **decision support, not advice** — not financial, investment, "
        "legal, tax or business advice. It describes elemental tendencies; real "
        "outcomes depend on skills, capital, markets, effort and choice.",
        "- Pairwise 궁합 scores were built for relationship compatibility; they "
        "are reused here as one signal for partnership *interaction style*, not "
        "as a business-success prediction.",
        "- All statements are tendencies and potentials, not predictions of "
        "events or results.",
    ]
    return "\n".join(lines) + "\n"
