"""Luck-cycle and lifetime decade-roadmap report.

Produces a client-facing markdown report that walks the whole life in
**five-year blocks**: each 10-year 대운 (major-luck period) is split into two
five-year phases, and each phase is read from the five concrete 세운 (annual
pillars) that fall inside it, together with the decade's own stem/branch.

The block model is deliberately built from the *annual pillars* rather than
from an invented stem/branch half-rule: `knowledge/08-luck-pillars.md` defines
the 10-year 대운 and the annual 세운 but does NOT define a stem-governs-first-
five-years convention, so the report reads each block from the yearly luck the
chart actually brings (Part 1 + Part 2 + Part 5 of that file — "a trigger is
most powerful when all three layers point in the same direction").

Every interpretive claim cites a file under `knowledge/`; the citations stay
in the `.md` source and are stripped from client PDFs by `saju_html`.

Output structure
----------------
- Chart-at-a-glance (Day Master, strength, five-role elements, career mode).
- Lifetime timeline (16 five-year blocks) as a table between chart markers.
- Favorable-cycle, ten-god-class and element-rhythm tables (chart markers).
- One section per five-year block with a summary plus Wealth / Business /
  Family / Investment notes.
- Sources & Limits (stripped from the PDF).
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Dict, List, Optional, Tuple

from . import lookup as L
from .daeun import first_period_start_date, saju_year
from .sewoon import SeWoonHit, derive_sewoon
from .yongsin import favorable_element

# ── Ten-god classes (five-group level) ──────────────────────────────────────

_CLASS_OF: Dict[str, str] = {
    "비견": "Companion", "겁재": "Companion",
    "식신": "Output", "상관": "Output",
    "편재": "Wealth", "정재": "Wealth",
    "편관": "Authority", "정관": "Authority",
    "편인": "Resource", "정인": "Resource",
}

_CLASS_KO: Dict[str, str] = {
    "Companion": "비겁 (比劫)",
    "Output": "식상 (食傷)",
    "Wealth": "재성 (財星)",
    "Authority": "관성 (官星)",
    "Resource": "인성 (印星)",
}

_CLASS_ORDER = ["Companion", "Output", "Wealth", "Authority", "Resource"]

# Storehouse branches (사고, 四庫) — knowledge/02-branches.md §Special Branches.
_STOREHOUSE = {"辰", "戌", "丑", "未"}


def year_status(stem_e: str, branch_e: str, fav: str, sup: str,
                unfav: Optional[str]) -> str:
    """Classify one year's favorable lean with the SAME rule the engine's
    `prose_fillers.period_favorable_status` uses (F-7): a year whose stem hits
    the favorable element but whose branch hits the unfavorable one is a wash
    (neutral), not both. This keeps the luck-cycle blocks consistent with the
    premium report's own favorable/unfavorable labels and makes the counts
    non-overlapping (favorable + unfavorable + neutral == 5)."""
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


# ── Small data container ────────────────────────────────────────────────────

class _Block:
    """One five-year phase of a decade."""

    __slots__ = (
        "decade", "half", "age_start", "age_end", "year_start", "year_end",
        "years", "annual", "classes", "fav_years", "unfav_years",
        "wealth_years", "output_years", "authority_years", "resource_years",
        "companion_years", "spouse_palace_events", "storehouse_events",
        "is_current", "_day_branch",
    )

    def __init__(self, decade, half: int, ages: Tuple[int, int], years: List[int]):
        self.decade = decade
        self.half = half
        self.age_start, self.age_end = ages
        self.years = years
        self.year_start, self.year_end = years[0], years[-1]
        self.annual: List[SeWoonHit] = []
        self.classes: Counter = Counter()
        self.fav_years = 0
        self.unfav_years = 0
        self.wealth_years = 0
        self.output_years = 0
        self.authority_years = 0
        self.resource_years = 0
        self.companion_years = 0
        self.spouse_palace_events: List[Tuple[int, str]] = []
        self.storehouse_events: List[Tuple[int, str]] = []
        self.is_current = False


# ── Phase construction ──────────────────────────────────────────────────────

def _saju_year_of_birth(chart) -> int:
    """The birth's Saju year (입춘-reckoned), so age↔calendar mapping is right
    even for a January/early-February birth."""
    try:
        by, bm, bd = (int(x) for x in chart.birth_date.split("-"))
    except (ValueError, AttributeError):
        return int(chart.birth_date[:4])
    bh, bmi = 0, 0
    try:
        bh, bmi = (int(x) for x in (chart.birth_time or "00:00").split(":"))
    except (ValueError, AttributeError):
        pass
    from datetime import datetime
    return saju_year(datetime(by, bm, bd, bh, bmi))


def _first_start_date(chart) -> Optional[date]:
    """The precise calendar date the first decade begins (N-4)."""
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


def _decade_bounds(chart, idx: int) -> Tuple[date, date]:
    """(start, end) dates of decade `idx`. The engine starts the first decade
    at a precise December date (N-4), so a 10-year label like "0–9" actually
    spans e.g. Dec 1992–Dec 2002 — the calendar-year ranges below honour that
    rather than assuming a January boundary."""
    first = _first_start_date(chart)
    if first is None:
        syb = _saju_year_of_birth(chart)
        period = chart.daeun[idx]
        return (date(period.start_age + syb - 1, 1, 1),
                date(period.start_age + syb + 9, 1, 1))
    start = first.replace(year=first.year + 10 * idx)
    end = first.replace(year=first.year + 10 * (idx + 1))
    return start, end


def _annual_year_for_block(start: date, half: int) -> List[int]:
    """The five Gregorian years whose 입춘-based annual pillar sits inside this
    half-decade. Since halves begin in December, the years fully inside
    [start, start+5y) are start.year+1 .. start.year+5 for the first half and
    +6..+10 for the second."""
    base = start.year + 1 + half * 5
    return list(range(base, base + 5))


def _build_blocks(chart, fav: str, sup: str, unfav: Optional[str]) -> List[_Block]:
    ref = chart.reference_date_obj()
    blocks: List[_Block] = []
    for i, period in enumerate(chart.daeun):
        start, _end = _decade_bounds(chart, i)
        for half in (0, 1):
            chunk = _annual_year_for_block(start, half)
            ages = (period.start_age + half * 5, period.start_age + half * 5 + 4)
            blk = _Block(period, half, ages, chunk)
            for y in chunk:
                hit = derive_sewoon(
                    chart.day_master, chart.branches, y, 7, 1,
                    natal_stems=chart.stems,
                )
                blk.annual.append(hit)
                cls = _CLASS_OF.get(hit.stem_tengod, "")
                if cls:
                    blk.classes[cls] += 1
                    if cls == "Wealth":
                        blk.wealth_years += 1
                    elif cls == "Output":
                        blk.output_years += 1
                    elif cls == "Authority":
                        blk.authority_years += 1
                    elif cls == "Resource":
                        blk.resource_years += 1
                    elif cls == "Companion":
                        blk.companion_years += 1
                stem_e = L.STEM_INFO.get(hit.stem, {}).get("element", "")
                branch_e = L.BRANCH_ELEMENT.get(hit.branch, "")
                status = year_status(stem_e, branch_e, fav, sup, unfav)
                if status == "favorable":
                    blk.fav_years += 1
                elif status == "unfavorable":
                    blk.unfav_years += 1
                # Spouse-palace (day branch) relationships.
                for _ab, natal_b, rel in hit.activated_branches:
                    if natal_b == chart.day.branch:
                        blk.spouse_palace_events.append((y, rel))
                # Storehouse triggers: the annual branch clashes/punishes a
                # natal 사고 branch (knowledge/13 §재고).
                for _ab, natal_b, rel in hit.activated_branches:
                    if natal_b in _STOREHOUSE and rel in ("clash", "punish"):
                        blk.storehouse_events.append((y, rel))
                if ref and ref.year in chunk:
                    blk.is_current = True
            # Weight the decade's own stem class once, as the decade backdrop.
            d_cls = _CLASS_OF.get(period.stem_tengod, "")
            if d_cls:
                blk.classes[d_cls] += 1
            blocks.append(blk)
    return blocks


def _dominant_classes(blk: _Block) -> List[str]:
    """All classes tied at the block's top count (canonical order, decade stem
    class first when it is itself tied). Honest about genuine ties rather than
    naming one arbitrarily."""
    if not blk.classes:
        return []
    top = max(blk.classes.values())
    tied = [c for c in _CLASS_ORDER if blk.classes.get(c, 0) == top]
    d_cls = _CLASS_OF.get(blk.decade.stem_tengod, "")
    if d_cls in tied and d_cls != tied[0]:
        tied = [d_cls] + [c for c in tied if c != d_cls]
    return tied


def _dominant_class(blk: _Block) -> str:
    doms = _dominant_classes(blk)
    return doms[0] if doms else "—"


def _dominant_label(blk: _Block) -> str:
    return " · ".join(_CLASS_KO.get(c, c) for c in _dominant_classes(blk))


def _lean(fav_years: int, unfav_years: int) -> str:
    if fav_years - unfav_years >= 2:
        return "favorable"
    if unfav_years - fav_years >= 2:
        return "challenging"
    return "mixed"


# ── Prose (grounded, deterministic) ─────────────────────────────────────────

_WEALTH_STYLE = {
    "Wealth": "재성-led",
    "Output": "식상생재",
    "Companion": "비겁-contested",
    "Resource": "인성-backed",
    "Authority": "관성-led",
}

_FIELD_BY_ELEMENT = {
    "Wood": "education, design/publishing, people development, healthcare & wellness",
    "Fire": "public-facing work, media & marketing, teaching/coaching, entrepreneurship",
    "Earth": "real estate & property, finance/accounting, operations & logistics, mediation",
    "Metal": "law & governance, engineering & technology, finance & investment, audit/quality",
    "Water": "strategy & consulting, research, psychology/counselling, logistics & data platforms",
}


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"



def _is(n: int) -> str:
    return "is" if n == 1 else "are"


def _block_summary(blk: _Block, fav: str, sup: str, unfav: Optional[str]) -> str:
    d = blk.decade
    lean = _lean(blk.fav_years, blk.unfav_years)
    fav_txt = _plural(blk.fav_years, "year")
    parts = [
        f"The decade backdrop is **{d.combined}** ({d.stem_tengod_en or d.stem_tengod}, "
        f"{_CLASS_KO.get(_CLASS_OF.get(d.stem_tengod, ''), '—')}), with the "
        f"{'opening' if blk.half == 0 else 'closing'} five years led by "
        f"**{_dominant_label(blk)}** annual energy.",
    ]
    if blk.fav_years:
        verb = "carries" if blk.fav_years == 1 else "carry"
        sentence = (
            f"{fav_txt} of 5 {verb} your favorable element (**{fav}** / **{sup}**)"
        )
    else:
        sentence = "None of the 5 years carries your favorable element"
    if blk.unfav_years:
        verb = "carries" if blk.unfav_years == 1 else "carry"
        sentence += (
            f", and {_plural(blk.unfav_years, 'year')} {verb} the unfavorable "
            f"element (**{unfav}**)"
        )
    parts.append(sentence + f" — an overall **{lean}** phase.")
    if blk.spouse_palace_events:
        evs = ", ".join(f"{y} {_rel_ko(r)}" for y, r in blk.spouse_palace_events)
        parts.append(
            f"The spouse palace (day branch **{getattr(blk, '_day_branch', '')}**) "
            f"is activated in {evs} — relationship, home, or partnership themes are "
            "more likely to surface."
        )
    return " ".join(parts)


def _rel_ko(rel: str) -> str:
    return {
        "combine": "육합 (binding)", "clash": "충 (clash)",
        "harm": "해 (harm)", "break": "파 (break)",
        "punish": "형 (punishment)", "self_punish": "자형 (self-punishment)",
    }.get(rel, rel)


def _block_wealth(blk: _Block) -> str:
    if blk.wealth_years:
        return (
            f"**{blk.wealth_years} of 5** annual stems are 재성 (Wealth) — money, "
            "pricing and asset decisions are foregrounded. Treat this as a window "
            "to *earn and negotiate*, and to put agreements in writing "
            "*(see knowledge/13-wealth-and-business.md §Wealth Timing)*."
        )
    if blk.companion_years:
        return (
            f"No direct 재성 stem, but **{blk.companion_years} of 5** are 비겁 "
            "(Companion). The 겁재奪財 pattern reads shared and loosely-defined money "
            "as contested here — defend rather than expand shared commitments "
            "*(see knowledge/13-wealth-and-business.md §겁재奪財)*."
        )
    return (
        "Wealth activity is quiet in this phase; income themes run through the "
        "decade backdrop rather than a direct 재성 year. Favor steady, low-drama "
        "stewardship *(see knowledge/13-wealth-and-business.md §Wealth Preservation)*."
    )


def _block_business(blk: _Block, fav: str) -> str:
    dom = _dominant_class(blk)
    if blk.output_years and fav == "Water":
        return (
            f"**{blk.output_years} of 5** years {_is(blk.output_years)} 식상 (Output), and Output is your "
            "favorable element — the 식상생재 chain (produce → earn) is strongest here. "
            "Independent, craft- or product-led work suits this phase; the classical "
            "caution is to sustain the output without draining the self "
            "*(see knowledge/12-career-and-vocation.md §Employment vs. Entrepreneurship)*."
        )
    if blk.authority_years:
        return (
            f"**{blk.authority_years} of 5** years {_is(blk.authority_years)} 관성 (Authority) — an "
            "institution, rank or licensed role comes to the fore. Since 관성 is your "
            "unfavorable element, read this as added structure and pressure rather than "
            "a natural fit; use it to build standing, not to over-commit "
            "*(see knowledge/12-career-and-vocation.md §용신 vs. Day Master for Career Choice)*."
        )
    if blk.resource_years:
        return (
            f"**{blk.resource_years} of 5** years {_is(blk.resource_years)} 인성 (Resource) — study, "
            "credentials, advisors and accumulated depth lead the phase. Useful for "
            "building the base that later phases convert into output "
            "*(see knowledge/12-career-and-vocation.md §Ten-God → Career Mode)*."
        )
    if dom == "Companion":
        return (
            "Peer and partnership energy leads this phase — work alongside equals, but "
            "keep ownership boundaries explicit given the 겁재 signal in this chart "
            "*(see knowledge/12-career-and-vocation.md §Employment vs. Entrepreneurship)*."
        )
    return (
        "Business energy is diffuse in this phase; let the decade backdrop and the "
        "concrete annual pillars above guide the read "
        "*(see knowledge/12-career-and-vocation.md §Ten-God → Career Mode)*."
    )


def _block_family(blk: _Block) -> str:
    if blk.spouse_palace_events:
        evs = ", ".join(f"{y} {_rel_ko(r)}" for y, r in blk.spouse_palace_events)
        binds = [r for _y, r in blk.spouse_palace_events if r == "combine"]
        unsettled = [r for _y, r in blk.spouse_palace_events
                     if r in ("clash", "harm", "break", "punish", "self_punish")]
        if binds and unsettled:
            return (
                f"The spouse palace is both **bound and unsettled** ({evs}) — a "
                "phase where a bond can deepen or formalise, but with friction or "
                "change around it; read it as a window, not a guarantee "
                "*(see knowledge/08-luck-pillars.md Part 5b)*."
            )
        if binds:
            return (
                f"The spouse palace is **bound** ({evs}) — meetings and formal "
                "commitments cluster here; read it as a window for deepening or "
                "formalising a bond *(see knowledge/08-luck-pillars.md Part 5b)*."
            )
        return (
            f"The spouse palace is struck or unsettled ({evs}) — better for "
            "deepening privately than for formalising commitments this phase "
            "*(see knowledge/08-luck-pillars.md Part 5b)*."
        )
    if blk.resource_years or blk.companion_years:
        return (
            "Family and support themes are steady: 인성 years point to parental/mentor "
            "backing and 비겁 years to siblings and peers "
            "*(see knowledge/05-ten-gods.md §인성생신)*."
        )
    return (
        "No strong spouse-palace activation in this phase; family life is more shaped "
        "by the decade backdrop than by a specific trigger year "
        "*(see knowledge/08-luck-pillars.md Part 5b)*."
    )


def _block_investment(blk: _Block, fav: str, sup: str, unfav: Optional[str], verdict: str) -> str:
    lean = _lean(blk.fav_years, blk.unfav_years)
    bits: List[str] = []
    if lean == "favorable":
        bits.append(
            f"A favorable-element phase ({blk.fav_years}/5) — the chart is in better "
            "balance, which supports planning and negotiation"
        )
    elif lean == "challenging":
        bits.append(
            f"An unfavorable-leaning phase ({blk.unfav_years}/5) — conserve, review "
            "and postpone large speculative commitments"
        )
    else:
        bits.append("A mixed phase — keep positions simple and liquidity available")
    if blk.storehouse_events:
        evs = ", ".join(f"{y} {_rel_ko(r)}" for y, r in blk.storehouse_events)
        bits.append(
            f"a natal storehouse (사고) is clashed/punished in {evs}, the classical "
            "재고 'storehouse opens' timing — the classics do not settle release vs. "
            "scatter, so treat it as a watch, not a signal "
            "*(see knowledge/13-wealth-and-business.md §재고)*"
        )
    if blk.companion_years:
        bits.append(
            "the 비겁 presence argues for sole holdings or partnerships with hard "
            "boundaries *(see knowledge/13-wealth-and-business.md §겁재奪財)*"
        )
    return "; ".join(bits) + "."


# ── Charts (marker-wrapped tables; the HTML backend replaces them with SVG) ──

def _timeline_markdown(blocks: List[_Block]) -> List[str]:
    lines = [
        "<!-- luck-timeline:start -->",
        "",
        "| Years | Ages | Decade | Ten-God | Favorable | Lean |",
        "|---|---|---|---|---|---|",
    ]
    for b in blocks:
        lean = _lean(b.fav_years, b.unfav_years)
        mark = " ⟵ you are here" if b.is_current else ""
        lines.append(
            f"| {b.year_start}–{b.year_end} | {b.age_start}–{b.age_end} "
            f"| {b.decade.combined} | {b.decade.stem_tengod_en or b.decade.stem_tengod} "
            f"| {b.fav_years}/5 | {lean}{mark} |"
        )
    lines += ["", "<!-- luck-timeline:end -->", ""]
    return lines


def _favorable_markdown(blocks: List[_Block]) -> List[str]:
    lines = [
        "<!-- luck-favorable:start -->",
        "",
        "| Years | Favorable | Neutral | Unfavorable |",
        "|---|---|---|---|",
    ]
    for b in blocks:
        neutral = 5 - b.fav_years - b.unfav_years
        lines.append(
            f"| {b.year_start}–{b.year_end} | {b.fav_years} | {neutral} | {b.unfav_years} |"
        )
    lines += ["", "<!-- luck-favorable:end -->", ""]
    return lines


def _classes_markdown(blocks: List[_Block]) -> List[str]:
    lines = [
        "<!-- luck-classes:start -->",
        "",
        "| Years | Companion | Output | Wealth | Authority | Resource |",
        "|---|---|---|---|---|---|",
    ]
    for b in blocks:
        lines.append(
            f"| {b.year_start}–{b.year_end} "
            f"| {b.classes.get('Companion', 0)} | {b.classes.get('Output', 0)} "
            f"| {b.classes.get('Wealth', 0)} | {b.classes.get('Authority', 0)} "
            f"| {b.classes.get('Resource', 0)} |"
        )
    lines += ["", "<!-- luck-classes:end -->", ""]
    return lines


def _elements_markdown(blocks: List[_Block], fav: str, sup: str, unfav: Optional[str]) -> List[str]:
    lines = [
        "| Years | Stem elements | Branch elements |",
        "|---|---|---|",
    ]
    for b in blocks:
        stems = Counter(L.STEM_INFO.get(h.stem, {}).get("element", "") for h in b.annual)
        branches = Counter(L.BRANCH_ELEMENT.get(h.branch, "") for h in b.annual)
        s_txt = " ".join(f"{e}:{n}" for e, n in stems.most_common() if e)
        br_txt = " ".join(f"{e}:{n}" for e, n in branches.most_common() if e)
        lines.append(f"| {b.year_start}–{b.year_end} | {s_txt} | {br_txt} |")
    lines += [""]
    return lines


# ── Top-level generator ─────────────────────────────────────────────────────

def generate_luck_cycle_report(chart, *, favorable_override: Optional[str] = None) -> str:
    """Render the luck-cycle / lifetime-roadmap report as markdown."""
    fe = favorable_element(chart, favorable_override)
    fav, sup = fe.element, fe.supporting
    unfav = fe.unfavorable
    verdict = (chart.strength_assessment or {}).get("verdict", "balanced")
    blocks = _build_blocks(chart, fav, sup, unfav)
    # attach the day branch for the summary's spouse-palace wording
    for _b in blocks:
        setattr(_b, "_day_branch", chart.day.branch)

    name = chart.name or "Client"
    lines: List[str] = []
    lines += [
        f"# {name} — Luck Cycle & Lifetime Decade Roadmap",
        "",
        f"**Born:** {chart.birth_date} · {chart.birth_time} · {chart.city or '—'}  ",
        f"**Day Master:** {chart.day_master}  ",
        f"**Strength:** {_verdict_label(verdict)}  ",
        f"**Favorable (용신):** {fav} · **Supporting (희신):** {sup}"
        + (f" · **Unfavorable (기신):** {unfav}" if unfav else ""),
        "",
        "This report walks your whole life in **five-year blocks**. Each 10-year "
        "major-luck period (대운) is split into two five-year phases, and each phase "
        "is read from the five concrete annual pillars (세운) that fall inside it, "
        "together with the decade's own stem and branch. Sections cover wealth, "
        "business, family and investment patterns in each block. Read the blocks as "
        "*rhythms and tendencies*, not fixed events "
        "*(see knowledge/08-luck-pillars.md Part 5)*.",
        "",
        "---",
        "",
        "## Chart at a Glance",
        "",
        f"- **Four Pillars:** {chart.year.combined} · {chart.month.combined} · "
        f"{chart.day.combined} · {chart.hour.combined}",
        f"- **Career mode (dominant ten-god):** {_career_mode(chart)} "
        "*(see knowledge/12-career-and-vocation.md §Ten-God → Career Mode)*",
        f"- **Flavour of work (favorable element):** {_FIELD_BY_ELEMENT.get(fav, '—')} "
        "*(see knowledge/12-career-and-vocation.md §Element → Industry Families)*",
        f"- **Spouse palace (day branch):** {chart.day.branch} "
        "*(see knowledge/11-gunghap.md)*",
        f"- **Income style:** {_income_style(chart)} "
        "*(see knowledge/13-wealth-and-business.md §정재 vs. 편재)*",
        "",
        "---",
        "",
        "## Lifetime Timeline",
        "",
        "Every five-year block, colour-coded by **net** favorable lean (favorable "
        "years minus unfavorable years): green where the favorable element leads by "
        "2+ years, red where the unfavorable leads by 2+, amber otherwise. A block "
        "showing fewer favorable years can still read green if it has no "
        "unfavorable years — the net, not the raw count, sets the colour.",
        "",
    ]
    lines += _timeline_markdown(blocks)
    lines += [
        "## Favorable-Cycle Chart",
        "",
        "How many of each block's five years carry your favorable element.",
        "",
    ]
    lines += _favorable_markdown(blocks)
    lines += [
        "## Ten-God Class Rhythm",
        "",
        "The five-group ten-god mix each block brings (annual stems, plus the "
        "decade's own stem once).",
        "",
    ]
    lines += _classes_markdown(blocks)
    lines += [
        "## Element Rhythm",
        "",
        "Which elements dominate the annual stems and branches of each block.",
        "",
    ]
    lines += _elements_markdown(blocks, fav, sup, unfav)
    lines += ["---", "", "## The Five-Year Blocks", ""]

    for i, b in enumerate(blocks, 1):
        here = " · **current**" if b.is_current else ""
        lines += [
            f"### {i}. {b.year_start}–{b.year_end} "
            f"(Ages {b.age_start}–{b.age_end}) — {b.decade.combined}{here}",
            "",
            _block_summary(b, fav, sup, unfav),
            "",
            "| Year | Pillar | Ten-God | Class | Favorable? |",
            "|---|---|---|---|---|",
        ]
        for h in b.annual:
            stem_e = L.STEM_INFO.get(h.stem, {}).get("element", "")
            branch_e = L.BRANCH_ELEMENT.get(h.branch, "")
            mark = {"favorable": "✅", "unfavorable": "⚠️", "neutral": "—"}[
                year_status(stem_e, branch_e, fav, sup, unfav)
            ]
            lines.append(
                f"| {h.year} | {h.combined} | {h.stem_tengod_en or h.stem_tengod} "
                f"| {_CLASS_KO.get(_CLASS_OF.get(h.stem_tengod, ''), '—')} "
                f"| {mark} |"
            )
        lines += [
            "",
            f"- **Wealth:** {_block_wealth(b)}",
            f"- **Business:** {_block_business(b, fav)}",
            f"- **Family:** {_block_family(b)}",
            f"- **Investment pattern:** {_block_investment(b, fav, sup, unfav, verdict)}",
            "",
            "---",
            "",
        ]

    lines += [
        "## Sources & Limits",
        "",
        "- Method: `knowledge/08-luck-pillars.md` (대운/세운 layers, Part 5b "
        "relationship timing), `knowledge/13-wealth-and-business.md` (wealth "
        "timing, 겁재奪財, 재고), `knowledge/12-career-and-vocation.md` (career "
        "mode and earning vehicle).",
        "- This reading describes tendencies, not fixed outcomes; it is for "
        "reflection and entertainment — not financial, investment, legal or "
        "business advice.",
        "- The engine's heuristic verdicts (strength, 용신) are provisional where "
        "the classical sources disagree; a qualified reader confirms the final "
        "reading.",
    ]
    return "\n".join(lines) + "\n"


def _verdict_label(verdict: str) -> str:
    return {"extreme_weak": "Very Weak"}.get(verdict, verdict.title())


def _career_mode(chart) -> str:
    counts: Counter = Counter()
    for hit in chart.ten_gods:
        cls = _CLASS_OF.get(hit.tengod)
        if cls:
            counts[cls] += 1
    if not counts:
        return "—"
    top = max(counts.values())
    tied = [c for c in _CLASS_ORDER if counts.get(c, 0) == top]
    modes = {
        "Wealth": "Business, sales, owning and growing resources",
        "Authority": "Institutions, licensed authority, management",
        "Output": "Creating, expressing, teaching, making",
        "Resource": "Research, advisory, credentialed practice",
        "Companion": "Peer/team or independent operator",
    }
    return f"{' / '.join(tied)} — {modes.get(tied[0], '—')}"


def _income_style(chart) -> str:
    kinds = {h.tengod for h in chart.ten_gods}
    has_direct = "정재" in kinds
    has_indirect = "편재" in kinds
    if has_direct and has_indirect:
        return "mixed sources (재성 혼잡) — a base plus variable upside"
    if has_indirect:
        return "편재-weighted — deal-making, commissions, several streams"
    if has_direct:
        return "정재-weighted — salary, steady cash flow, disciplined revenue"
    return "no visible 재성 on a stem — wealth routes through output/resource channels"
