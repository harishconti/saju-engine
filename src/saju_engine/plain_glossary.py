"""Plain-language glosses for Saju jargon in engine reports.

Mirrors `hanja_glossary.py`: a dict plus a first-use annotator. Every `plain`
string is curated from and faithful to the cited `knowledge/` file. The
inline `*(see …)*` citation is stripped at the PDF layer; the gloss text stays.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PlainDef:
    plain: str          # <= ~14 words, lay phrasing
    display: str        # canonical rendering, e.g. "Direct Wealth (正財)"
    source: str         # e.g. "knowledge/05-ten-gods.md"
    note: str = ""      # one extra clarifying sentence, used in deep/skeleton glossary


def _d(plain, display, source, note=""):
    return PlainDef(plain=plain, display=display, source=source, note=note)


# Canonical PlainDefs, then a trigger->PlainDef expansion below.
_TEN_GODS = {
    "비견": _d("a peer or equal — support, solidarity, and rivalry in equal measure",
              "Companion (比肩)", "knowledge/05-ten-gods.md"),
    "겁재": _d("a rival for the same resources — competition in money or love",
              "Robber (劫財)", "knowledge/05-ten-gods.md"),
    "식신": _d("gentle output — talent, making, teaching, slow enjoyable accumulation",
              "Eating God (食神)", "knowledge/05-ten-gods.md"),
    "상관": _d("sharp output — bold expression, creativity, friction with rules and authority",
              "Hurting Officer (傷官)", "knowledge/05-ten-gods.md"),
    "편재": _d("variable money — deals, commissions, windfalls, higher risk and reward",
              "Indirect Wealth (偏財)", "knowledge/05-ten-gods.md"),
    "정재": _d("steady, earned income and everyday resources — salary and savings",
              "Direct Wealth (正財)", "knowledge/05-ten-gods.md"),
    "편관": _d("pressure and demand — deadlines, tough oversight, decisive action under stress",
              "Seven Killings (偏官)", "knowledge/05-ten-gods.md"),
    "정관": _d("conventional authority — career structure, rules, status, institutions",
              "Direct Officer (正官)", "knowledge/05-ten-gods.md"),
    "편인": _d("unconventional learning — intuition, solitary study, restless over-thinking",
              "Indirect Resource (偏印)", "knowledge/05-ten-gods.md"),
    "정인": _d("support and knowledge — education, mentors, care, property, credentials",
              "Direct Resource (正印)", "knowledge/05-ten-gods.md"),
}

_CLASS_TERMS = {
    "비겁": _d("the peers-and-rivals group — how you meet equals and competitors",
              "Companion class (比劫)", "knowledge/05-ten-gods.md"),
    "식상": _d("the output group — how you create, express, and produce",
              "Output class (食傷)", "knowledge/05-ten-gods.md"),
    "재성": _d("the wealth group — how money and resources come and are held",
              "Wealth class (財星)", "knowledge/05-ten-gods.md"),
    "관성": _d("the authority group — how you meet rules, status, and institutions",
              "Authority class (官星)", "knowledge/05-ten-gods.md"),
    "인성": _d("the resource group — support, learning, and what sustains you",
              "Resource class (印星)", "knowledge/05-ten-gods.md"),
}

_YONGSIN = {
    "용신": _d("the element your chart most needs for balance — lean toward it",
              "Favourable Element (用神)", "knowledge/03-five-elements.md",
              "It is the working target for choices about work, place, colour, and timing."),
    "희신": _d("the element that supports the favourable one — a helpful secondary",
              "Supporting Element (喜神)", "knowledge/03-five-elements.md"),
    "기신": _d("the element that unbalances your chart — minimise its influence",
              "Unfavourable Element (忌神)", "knowledge/03-five-elements.md"),
    "한신": _d("a neutral element that mostly drains the favourable one",
              "Draining Element (閒神)", "knowledge/00-glossary.md"),
    "구신": _d("an element that restrains the favourable one",
              "Restricting Element (仇神)", "knowledge/00-glossary.md"),
}

_LUCK = {
    "대운": _d("roughly ten-year life chapters that colour a whole span",
              "Major Luck (大運)", "knowledge/08-luck-pillars.md"),
    "세운": _d("the theme of a single year",
              "Annual Luck (歲運)", "knowledge/08-luck-pillars.md"),
    "월운": _d("the theme of a single month",
              "Monthly Luck (月運)", "knowledge/08-luck-pillars.md"),
    "일운": _d("the theme of a single day",
              "Daily Luck (日運)", "knowledge/08-luck-pillars.md"),
}

# 12운성 stages — plain one-liners from knowledge/06-twelve-stages.md
_STAGES = {
    "장생": _d("a fresh start — early, hopeful, growing", "Birth stage (長生)", "knowledge/06-twelve-stages.md"),
    "목욕": _d("an unsettled, exposed phase — learning through mistakes", "Bath stage (沐浴)", "knowledge/06-twelve-stages.md"),
    "관대": _d("coming into form — gaining competence and standing", "Cap stage (冠帶)", "knowledge/06-twelve-stages.md"),
    "건록": _d("established and productive — steady working strength", "Office stage (建祿)", "knowledge/06-twelve-stages.md"),
    "제왕": _d("peak strength — full power, with the risk of over-reach", "Peak stage (帝旺)", "knowledge/06-twelve-stages.md"),
    "쇠": _d("just past the peak — a gentle decline, wiser and slower", "Decline stage (衰)", "knowledge/06-twelve-stages.md"),
    "병": _d("a low-energy phase — rest and repair matter more", "Illness stage (病)", "knowledge/06-twelve-stages.md"),
    "사": _d("a dormant, minimal phase — little outward force", "Death stage (死)", "knowledge/06-twelve-stages.md"),
    "묘": _d("stored away — kept in reserve, opens when triggered", "Storehouse stage (墓)", "knowledge/06-twelve-stages.md"),
    "절": _d("cut off and empty — a clean break before renewal", "Severance stage (絶)", "knowledge/06-twelve-stages.md"),
    "태": _d("conceived but unseen — potential forming", "Conception stage (胎)", "knowledge/06-twelve-stages.md"),
    "양": _d("nurtured and preparing — sheltered growth before emergence", "Nourish stage (養)", "knowledge/06-twelve-stages.md"),
}

# 신살 stars — from knowledge/07-special-formations.md
_STARS = {
    "도화": _d("charm and magnetism — attractiveness, and sometimes distraction or scandal",
              "Peach Blossom (桃花)", "knowledge/07-special-formations.md"),
    "역마": _d("movement — travel, relocation, changing scenes, a mobile life",
              "Travelling Horse (驛馬)", "knowledge/07-special-formations.md"),
    "화개": _d("solitude and depth — art, scholarship, spirituality, time alone",
              "Canopy (華蓋)", "knowledge/07-special-formations.md"),
    "천을귀인": _d("a protective helper star — timely aid from others in hard moments",
                 "Nobleman (天乙貴人)", "knowledge/07-special-formations.md"),
    "문창귀인": _d("a study-and-writing star — academic and literary aptitude",
                 "Academic Star (文昌貴人)", "knowledge/07-special-formations.md"),
    "양인": _d("a sharp, forceful star — drive and edge, and a risk of excess",
              "Blade (羊刃)", "knowledge/07-special-formations.md"),
    "공망": _d("an 'empty' position — its themes feel deferred or less solid",
              "Void (空亡)", "knowledge/07-special-formations.md"),
    "천덕귀인": _d("a virtue-and-protection star — help arrives through good conduct",
                 "Heavenly Virtue (天德貴人)", "knowledge/07-special-formations.md"),
    "월덕귀인": _d("a monthly virtue-and-protection star",
                 "Monthly Virtue (月德貴人)", "knowledge/07-special-formations.md"),
    "백호": _d("a sudden-event star — accidents or shocks; handle risk deliberately",
              "White Tiger (白虎)", "knowledge/07-special-formations.md"),
    "괴강": _d("an intense all-or-nothing star — strong character, dramatic swings",
              "Kuigang (魁罡)", "knowledge/07-special-formations.md"),
    "원진": _d("a friction star between two branches — quiet resentment, hard-to-name irritation",
              "Resentment (怨嗔)", "knowledge/07-special-formations.md"),
    "귀문관": _d("an over-sensitivity star — vivid inner world, anxiety, acute intuition",
               "Ghost Gate (鬼門關)", "knowledge/07-special-formations.md"),
    "겁살": _d("a loss-and-seizure star — guard against sudden loss",
              "Robbery Star (劫煞)", "knowledge/07-special-formations.md"),
    "재살": _d("a confinement-and-conflict star — legal or bounded-situation risk",
              "Calamity Star (災煞)", "knowledge/07-special-formations.md"),
    "천살": _d("a 'forces beyond control' star — weather, authority, big systems",
              "Heaven Star (天煞)", "knowledge/07-special-formations.md"),
    "지살": _d("a movement-and-relocation star, milder than 역마",
              "Ground Star (地煞)", "knowledge/07-special-formations.md"),
    "월살": _d("a depletion star — dryness, stalling, thin returns for a while",
              "Moon Star (月煞)", "knowledge/07-special-formations.md"),
    "망신": _d("an exposure star — private matters becoming public, embarrassment",
              "Loss-of-Face (亡神)", "knowledge/07-special-formations.md"),
    "장성": _d("a leadership star — command, responsibility, being looked to",
              "General Star (將星)", "knowledge/07-special-formations.md"),
    "반안": _d("a promotion-and-comfort star — steady advancement, saddle secured",
              "Saddle Star (攀鞍)", "knowledge/07-special-formations.md"),
}

_STRUCTURAL = {
    "일간": _d("you — the reference point the whole chart is read against",
              "Day Master (日干)", "knowledge/09-interpretation-method.md"),
    "일주": _d("your day pillar — the self and the marriage/partner area",
              "Day Pillar (日柱)", "knowledge/00-glossary.md"),
    "격국": _d("the chart's overall shape — its dominant organising pattern",
              "Chart Structure (格局)", "knowledge/00-glossary.md"),
    "지장간": _d("the hidden stems inside a branch — the undercurrent of that area",
               "Hidden Stems (地藏干)", "knowledge/02-branches.md"),
    "본기": _d("the main hidden stem of a branch — its dominant inner force",
              "Primary hidden stem (本氣)", "knowledge/02-branches.md"),
    "중기": _d("the middle hidden stem of a branch — a secondary inner theme",
              "Middle hidden stem (中氣)", "knowledge/02-branches.md"),
    "여기": _d("the residual hidden stem of a branch — a faint lingering theme",
              "Residual hidden stem (餘氣)", "knowledge/02-branches.md"),
}

_CANON: Dict[str, PlainDef] = {
    **_TEN_GODS, **_CLASS_TERMS, **_YONGSIN, **_LUCK,
    **_STAGES, **_STARS, **_STRUCTURAL,
}

# English display names + "English (漢字)" forms + grid names all resolve to the
# same PlainDef as the Korean key.
_ENGLISH_ALIASES: Dict[str, str] = {
    "Companion": "비견", "Robber": "겁재",
    "Eating God": "식신", "Hurting Officer": "상관", "Output": "식상",
    "Indirect Wealth": "편재", "Direct Wealth": "정재", "Wealth": "재성",
    "Seven Killings": "편관", "Direct Officer": "정관", "Authority": "관성",
    "Indirect Resource": "편인", "Direct Resource": "정인", "Resource": "인성",
    "Favourable Element": "용신", "Favorable Element": "용신",
    "Supporting Element": "희신", "Unfavourable Element": "기신", "Unfavorable Element": "기신",
    "Major Luck": "대운", "Annual Luck": "세운", "Monthly Luck": "월운", "Daily Luck": "일운",
    "Peach Blossom": "도화", "Travelling Horse": "역마", "Nobleman": "천을귀인",
    "Day Master": "일간",
    "Peak": "제왕", "Death": "사", "Bath": "목욕", "Nourish": "양",
    # grid names
    "비견격": "비견", "겁재격": "겁재", "식신격": "식신", "상관격": "상관",
    "편재격": "편재", "정재격": "정재", "편관격": "편관", "정관격": "정관",
    "편인격": "편인", "정인격": "정인",
    "Companion Grid": "비견", "Direct Officer Grid": "정관", "Eating God Grid": "식신",
    "Direct Wealth Grid": "정재",
}

PLAIN_GLOSSARY: Dict[str, PlainDef] = dict(_CANON)
for alias, key in _ENGLISH_ALIASES.items():
    PLAIN_GLOSSARY[alias] = _CANON[key]
# also register the "English (漢字)" display strings as triggers
for pd in set(_CANON.values()):
    PLAIN_GLOSSARY.setdefault(pd.display, pd)


_TRIGGERS = sorted(PLAIN_GLOSSARY, key=len, reverse=True)


def _line_bounds(text: str, idx: int) -> str:
    """Return the line of `text` that position `idx` falls on."""
    start = text.rfind("\n", 0, idx) + 1
    end = text.find("\n", idx)
    return text[start:] if end == -1 else text[start:end]


def _is_word_char(ch: str) -> bool:
    """A-Z / a-z / 0-9 / Hangul / CJK ideograph — anything that continues a term."""
    if not ch:
        return False
    if ch.isalnum():
        return True
    return "가" <= ch <= "힣" or "一" <= ch <= "鿿"


def _nearest_heading(text: str, idx: int) -> str:
    """Return the text of the closest markdown heading at or before `idx`."""
    heading = ""
    for m in re.finditer(r"(?m)^#{1,6}[ \t]+(.+?)[ \t]*$", text[:idx]):
        heading = m.group(1)
    return heading


def _is_structured_slot(text: str, idx: int, after: int) -> bool:
    """True if the trigger sits somewhere a gloss clause would read badly or
    corrupt markup: a heading, a table row, a table-of-contents entry, an
    italic blockquote note, a parenthetical label, or a ``**bold label:**``."""
    before = text[idx - 1] if idx > 0 else ""
    nxt1 = text[after:after + 1]
    # word-boundary: never fire mid-word (e.g. "Monthly Luck" inside "Monthly Lucky")
    if _is_word_char(before) or _is_word_char(nxt1):
        return True
    stripped = _line_bounds(text, idx).lstrip()
    if stripped.startswith("#") or "|" in stripped:
        return True
    if stripped.startswith("> _") or stripped.startswith(">_"):
        return True  # engine's italic methodology / reviewer notes
    if stripped.startswith(("- **", "* **")):
        return True  # bold-label definition bullets (Quick Reference, guidance lists)
    # inside a table-of-contents / navigation list
    if "contents" in _nearest_heading(text, idx).lower():
        return True
    # parenthetical label: `(상관)` / `Output (傷官)`
    if before == "(" or nxt1 == ")":
        return True
    # slash-delimited list: `절 (絶)/병 (病)/사 (死)`
    if before == "/" or nxt1 == "/":
        return True
    # inside a `**bold**` or `*italic*` span — an enumeration or inline emphasis
    # where a gloss clause would break the markup
    line_start = text.rfind("\n", 0, idx) + 1
    dbl = text.count("**", line_start, idx)
    if dbl % 2 == 1:
        return True
    if (text.count("*", line_start, idx) - 2 * dbl) % 2 == 1:
        return True
    tail = text[after:]
    # trigger ends its line (TOC entry, heading, bare label) — not mid-sentence
    if tail[:1] in ("", "\n") or tail.lstrip(" \t")[:1] == "\n":
        return True
    nxt = tail[:2]
    if nxt.startswith(":") or nxt.startswith("*"):
        return True  # `**Favorable Element:**` / `**Major Luck**`
    if before == "*":  # trigger opens right after `**`
        return True
    # trigger used attributively (modifying the next noun) — a gloss clause would
    # split the noun phrase ("Major Luck Periods", "Direct Wealth stem",
    # "Authority ten-god", "세운 tables"). Look past an immediate `(漢字)` group.
    _MODIFIED_NOUNS = {
        "and", "or", "but", "nor", "into", "for", "as",
        "stem", "stems", "star", "stars", "ten-god", "ten-gods", "class",
        "period", "periods", "table", "tables", "pillar", "pillars", "cycle",
        "energy", "element", "elements", "branch", "branches", "grid", "phase",
        "windows", "window", "years", "months", "timing", "theme", "themes",
        "reading", "verdict", "candidate", "pull", "pulls", "presence",
        "influence", "load", "count", "mix",
    }
    look = tail.lstrip(" \t")
    if look.startswith("("):
        cl = look.find(")")
        if 0 <= cl < 12:
            look = look[cl + 1:].lstrip(" \t")
    follow_word = look.split(" ", 1)[0].rstrip(".,;:)*_").lower()
    if follow_word in _MODIFIED_NOUNS:
        return True
    # trigger is the second half of a compound ("... and Wealth pulls") or the
    # object of a preposition that starts a noun phrase ("... without Direct Officer")
    prev_word = text[:idx].rstrip(" \t").rsplit(" ", 1)[-1].lower()
    if prev_word in {"and", "or", "without", "with"}:
        return True
    return False


def gloss_first_use(text: str, already_used: set) -> str:
    """Append ' — {plain} *(see {source})*' after the first plain-prose use of each term.

    Occurrences inside headings, table rows, or bold labels (``**Term:**``) are
    skipped so the markup is never corrupted; the term is still picked up by
    ``collect_used_terms`` for the glossary section.
    """
    for trigger in _TRIGGERS:
        pd = PLAIN_GLOSSARY[trigger]
        if pd.display in already_used:
            continue
        search_from = 0
        while True:
            idx = text.find(trigger, search_from)
            if idx == -1:
                break
            after = idx + len(trigger)
            if _is_structured_slot(text, idx, after):
                search_from = after
                continue
            # skip if an em-dash gloss or a parenthetical already follows
            tail = text[after:after + 3].lstrip()
            if tail.startswith("—") or tail.startswith("("):
                # a parenthetical (漢字) may still precede the gloss slot
                close = text.find(")", after)
                if 0 <= close < after + 12:
                    after = close + 1
                    tail = text[after:after + 3].lstrip()
                if tail.startswith("—"):
                    already_used.add(pd.display)
                    break
            insertion = f" — {pd.plain} *(see {pd.source})*"
            text = text[:after] + insertion + text[after:]
            already_used.add(pd.display)
            break
    return text


def _first_real_use(text: str, trigger: str) -> int:
    """Index of the first occurrence of `trigger` that reads as a real term use
    (would accept an inline gloss). -1 if none."""
    start = 0
    while True:
        i = text.find(trigger, start)
        if i == -1:
            return -1
        after = i + len(trigger)
        if not _is_structured_slot(text, i, after):
            return i
        start = after


def collect_used_terms(text: str) -> List[str]:
    """Display names of glossary terms that appear as real term uses in `text`,
    in first-appearance order, deduped by PlainDef identity."""
    best: Dict[int, int] = {}
    defs: Dict[int, PlainDef] = {}
    for trigger, pd in PLAIN_GLOSSARY.items():
        i = _first_real_use(text, trigger)
        if i == -1:
            continue
        if id(pd) not in best or i < best[id(pd)]:
            best[id(pd)] = i
            defs[id(pd)] = pd
    return [defs[k].display for k in sorted(best, key=best.get)]


_SHORT_TIERS = {"essential", "companion", "spark", "compat", "basic"}
_FULL_TIERS = {"deep", "reading", "fullmap", "skeleton", "compat_deep"}


def render_terms_section(used: List[str], tier: str) -> str:
    if tier == "sample" or not used:
        return ""
    full = tier not in _SHORT_TIERS
    lines = ["## What the Terms Mean", ""]
    by_display = {pd.display: pd for pd in PLAIN_GLOSSARY.values()}
    for display in used:
        pd = by_display.get(display)
        if not pd:
            continue
        entry = f"- **{pd.display}:** {pd.plain}"
        if full and pd.note:
            sep = "" if pd.plain.rstrip().endswith((".", "!", "?")) else "."
            entry += f"{sep} {pd.note}"
        lines.append(entry)
    lines.append("")
    return "\n".join(lines)
