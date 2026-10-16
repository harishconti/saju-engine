"""Deterministic validation of a drafting result. This is the safety layer.

The model is not trusted to police itself: every rule in the prompt is re-checked here,
so "the model was told" never has to be the argument. A draft either passes or it is
returned to the reviewer with the specific reasons it failed.

The structured checks are local (shape, length, citations, numbers, caveats, ground
rules). The repo's client-ready gate is run on top by the CLI, because that gate lives
in `tools/` and this package stays importable on its own.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .pack import GroundingPack, LETTER_MAX_WORDS, LETTER_MIN_WORDS

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_SECOND_PERSON_RE = re.compile(r"\b(you|your|you're|yours)\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\b\d{4}\b|\b\d{1,3}(?:\.\d+)?%")
# A favourable-element claim, and the element it claims. Deliberately narrow: a marker
# word, then an element name within a short window.
_FAVOURABLE_CLAIM_RE = re.compile(
    r"(favou?rable|favou?red|remedy|beneficial|best element)[^.]{0,50}?"
    r"\b(Wood|Fire|Earth|Metal|Water)\b", re.IGNORECASE)
_NEGATION = ("not ", "n't", "rather than", "instead of", "other than", "neither")
# "climate takes priority over the strength reading" — a claim about *which method
# governs*, which the chart states as a structured fact.
_METHOD_CLAIM_RE = re.compile(
    r"climate[^.]{0,80}?(takes priority|takes precedence|comes first|governs|wins)",
    re.IGNORECASE)
# A stated duration: seconds/minutes/hours should be traceable to the facts. The facts
# carry the knife-edge margin in minutes and seconds, which is exactly where a model
# rounds "41 seconds" into "a minute and a half".
# A *measurement* of time, in either word order: "41 seconds", "a minute and a half".
# Hours are excluded on purpose: "the next hour pillar" is a term of art on this page, and
# "one hour" would have matched a bare-count rule. The number token has to be adjacent to
# its unit, so "one in your month pillar ... hour" no longer fires.
_MEASURE_RE = re.compile(
    r"\b(\d+(?:\.\d+)?|half|quarter)\s*(seconds?|minutes?)\b"
    r"|\b(seconds?|minutes?)\s+(?:and\s+)?(?:a\s+)?(\d+(?:\.\d+)?|half|quarter)\b"
    r"|\bhalf an hour\b",
    re.IGNORECASE)
_VAGUE_QUANTITY = ("few", "some", "several", "couple")

_BIRTH_TIME_RE = re.compile(
    r"birth[\s-]?time|recorded time|birth[\s-]?hour|minutes? (?:off|out|either side)|"
    r"hour pillar|civil record|hospital|clock",
    re.IGNORECASE,
)

# Ground rules (CLAUDE.md): no medical, legal or financial certainty, ever.
_BANNED_PHRASES = (
    "guaranteed", "guarantee", "will definitely", "definitely will", "100%",
    "diagnos", "cure", "treat your", "medical advice", "financial advice",
    "investment advice", "legal advice", "you will get", "cannot fail",
)

# Machinery and trade jargon — the same classes the client-ready gate fails, kept here
# too so a draft is never even shown with them in it.
_MACHINERY = (
    "querent", "the engine", "this engine", "step 1", "step 2", "step 3",
    "knowledge/", "engine-generated", "candidate", "draft",
)


@dataclass(frozen=True)
class Problem:
    code: str
    detail: str


def _words(text: str) -> int:
    return len(_WORD_RE.findall(text or ""))


def _citation_ids(payload: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for item in payload.get("citations") or []:
        if isinstance(item, dict):
            out.append(f"{item.get('file', '')}#{item.get('section', '')}")
        else:
            out.append(str(item))
    return out


def validate(
    payload: Dict[str, Any],
    pack: GroundingPack,
    *,
    min_words: int = LETTER_MIN_WORDS,
    max_words: int = LETTER_MAX_WORDS,
    require_birth_time_note: bool = True,
) -> List[Problem]:
    """Every reason this draft must not be shown to a reviewer as finished."""
    problems: List[Problem] = []
    letter = payload.get("letter")
    if not isinstance(letter, str) or not letter.strip():
        return [Problem("SHAPE", "no letter text")]

    features = payload.get("features")
    if not isinstance(features, list) or not all(isinstance(f, str) and f.strip() for f in features):
        problems.append(Problem("SHAPE", "`features` must be a list of 2-3 short strings"))
    elif not 2 <= len(features) <= 3:
        problems.append(Problem("FEATURE_COUNT", f"{len(features)} features; the page needs 2-3"))

    citations = _citation_ids(payload)
    if not citations:
        problems.append(Problem("CITATION_MISSING", "no citations"))
    known = pack.excerpt_ids()
    for cid in citations:
        if cid not in known:
            problems.append(Problem("CITATION_UNKNOWN", f"{cid!r} is not one of the excerpts"))

    count = _words(letter)
    if not min_words <= count <= max_words:
        problems.append(Problem("LENGTH", f"{count} words; expected {min_words}-{max_words}"))

    if not _SECOND_PERSON_RE.search(letter):
        problems.append(Problem("NOT_SECOND_PERSON", "the letter never addresses the client as 'you'"))

    if (require_birth_time_note and pack.facts.get("hour_uncertainty")
            and not _BIRTH_TIME_RE.search(letter)):
        problems.append(Problem(
            "MISSING_BIRTH_TIME_NOTE",
            "the chart is a knife-edge birth time and the letter does not mention it"))

    lowered = letter.casefold()
    for phrase in _BANNED_PHRASES:
        if phrase in lowered:
            problems.append(Problem("GROUND_RULE", f"absolute claim: {phrase!r}"))
    for phrase in _MACHINERY:
        if phrase in lowered:
            problems.append(Problem("MACHINERY", f"machinery or jargon: {phrase!r}"))

    # Numbers must come from the facts: an invented year or percentage is the clearest
    # sign the model is not reading the pack.
    facts_text = _facts_text(pack)
    for number in _NUMBER_RE.findall(letter):
        if number not in facts_text:
            problems.append(Problem("INVENTED_NUMBER", f"{number!r} is not in the facts"))

    favourable = pack.facts.get("favorable_element") or {}
    allowed = {str(favourable.get(field, "")).casefold()
               for field in ("element", "supporting")} - {""}
    if allowed:
        for match in _FAVOURABLE_CLAIM_RE.finditer(letter):
            claimed = match.group(2)
            between = match.group(0)[: match.start(2) - match.start(0)].casefold()
            if any(neg in between for neg in _NEGATION):
                continue
            if claimed.casefold() not in allowed:
                problems.append(Problem(
                    "ELEMENT_MISMATCH",
                    f"the letter calls {claimed} favourable; this chart's favourable element "
                    f"is {favourable.get('element')} (supporting {favourable.get('supporting')})"))

    method = str(favourable.get("method", ""))
    if _METHOD_CLAIM_RE.search(letter) and "climate" not in method:
        problems.append(Problem(
            "METHOD_MISMATCH",
            f"the letter says the climate reading governs; this chart's method is {method!r}"))

    # Time measurements, specifically. The facts carry the knife-edge margin in seconds;
    # a letter that rounds it into "a minute and a half" is stating a number the chart did
    # not give — on the one page where that costs the most.
    for match in _MEASURE_RE.finditer(letter):
        number = match.group(1) or match.group(4) or ""
        if not number:
            # The "half an hour" form: a measurement with no digit at all.
            problems.append(Problem(
                "UNSUPPORTED_DURATION",
                f"a time measurement the facts do not give: {match.group(0).strip()!r}"))
            continue
        if number.casefold() in ("half", "quarter"):
            problems.append(Problem(
                "UNSUPPORTED_DURATION",
                f"a time measurement the facts do not give: {match.group(0).strip()!r}"))
        elif number not in facts_text:
            problems.append(Problem(
                "UNSUPPORTED_DURATION",
                f"{match.group(0).strip()!r} is not in the facts"))

    return problems


def _facts_text(pack: GroundingPack) -> str:
    """The pack's facts as flat text, for the number check."""
    def flat(value: Any) -> List[str]:
        if isinstance(value, dict):
            out: List[str] = []
            for item in value.values():
                out.extend(flat(item))
            return out
        if isinstance(value, list):
            out = []
            for item in value:
                out.extend(flat(item))
            return out
        return [str(value)]

    return " ".join(flat(pack.facts)) + " " + " ".join(
        f"{e.file} {e.section}" for e in pack.excerpts)


def summarise(problems: Sequence[Problem]) -> str:
    """One line per problem, for the CLI."""
    return "\n".join(f"  [{p.code}] {p.detail}" for p in problems)
