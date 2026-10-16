"""The grounding pack: everything a drafting request is allowed to know.

A pack is built deterministically from a computed chart plus the report markdown the
engine just produced, so the same chart always yields the same pack — which is what
makes the drafting step auditable and the tests meaningful.

Three parts, and the separation is deliberate:

* ``facts`` — the chart, from a fixed whitelist of fields. The model may not state a
  number or a relationship that is not here.
* ``excerpts`` — the doctrine, pulled from ``knowledge/`` by heading keyword match.
  Every interpretive claim the draft makes must cite one of these, by id.
* ``constraints`` — the writing rules, the output schema, and the client-ready gate's
  own bans, so the model is told the same thing the validator enforces.

No personally identifying data is ever included; see the module docstring on
``saju_ai``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

KNOWLEDGE_ROOT = Path(__file__).resolve().parents[2] / "knowledge"

# How much doctrine to send. Six to eight short excerpts is enough for a one-page
# letter and keeps the request cheap (a few thousand tokens) and reviewable by eye.
MAX_EXCERPTS = 8
MAX_EXCERPT_WORDS = 120

LETTER_MIN_WORDS = 140
LETTER_MAX_WORDS = 280


@dataclass(frozen=True)
class Excerpt:
    """One cited slice of a `knowledge/` file."""

    file: str
    section: str
    text: str
    words: int

    @property
    def id(self) -> str:
        return f"{self.file}#{self.section}"


@dataclass
class GroundingPack:
    """Everything a drafting request may use, and nothing else."""

    section: str
    facts: Dict[str, Any]
    excerpts: Tuple[Excerpt, ...]
    constraints: Tuple[str, ...]
    report_sections: Tuple[str, ...]
    pii_terms: Tuple[str, ...] = field(default=())

    def excerpt_ids(self) -> set:
        return {e.id for e in self.excerpts}

    def render(self) -> str:
        """The pack as text — for `--dry-run`, for review, and for the PII check."""
        lines = [f"## SECTION: {self.section}", "", "## FACTS (the only facts allowed)"]
        lines += _render_facts(self.facts)
        lines += ["", "## EXCERPTS (the only doctrine allowed; cite by id)"]
        for excerpt in self.excerpts:
            lines += [f"### {excerpt.id}", excerpt.text, ""]
        lines += ["## CONSTRAINTS"]
        lines += [f"- {c}" for c in self.constraints]
        lines += ["", "## REPORT OUTLINE (what the client will read)"]
        lines += [f"- {s}" for s in self.report_sections]
        return "\n".join(lines)

    def contains_pii(self) -> List[str]:
        """Any supplied PII term that leaked into the pack (should always be empty)."""
        haystack = self.render().casefold()
        return [t for t in self.pii_terms if t and t.casefold() in haystack]


# ── facts ────────────────────────────────────────────────────────────────────────

def _facts(chart, report_md: str) -> Dict[str, Any]:
    """The chart, from a fixed whitelist.

    Whitelist rather than blacklist on purpose: a new chart field is not sent to a
    third party until someone adds it here deliberately.
    """
    from saju_engine.report_primitives import TENGOD_CLASS
    from saju_engine.yongsin import favorable_element

    fe = favorable_element(chart)
    strength = dict(getattr(chart, "strength_assessment", None) or {})
    info = dict(getattr(chart, "day_master_info", None) or {})

    facts: Dict[str, Any] = {
        "day_master": {
            "hanja": getattr(chart, "day_master", ""),
            "romanised": _romanise(getattr(chart, "day_master", "")),
            "element": info.get("element", ""),
            "polarity": info.get("polarity", ""),
        },
        "pillars": [_pillar_facts(p) for p in getattr(chart, "pillars", [])],
        "strength": {
            "verdict": strength.get("verdict", ""),
            "score": strength.get("score"),
        },
        "favorable_element": {
            "element": fe.element,
            "supporting": fe.supporting,
            "method": fe.method,
            "confidence": fe.confidence,
            "note": fe.note,
            "climate_band": fe.climate_band,
            "climate_agrees": fe.climate_agrees,
        },
        "dominant_ten_god_classes": _dominant_classes(chart, TENGOD_CLASS),
        "stars_present": _stars(chart),
        "daeun": [
            {
                "ages": f"{p.start_age}-{p.end_age}",
                "combined": p.combined,
                "ten_god": p.stem_tengod_en or p.stem_tengod or "",
            }
            for p in (getattr(chart, "daeun", None) or [])
        ],
        "chart_signature": _chart_signature(report_md),
        "hour_uncertainty": _hour_uncertainty(chart),
    }
    current_year = _current_sewoon(chart)
    if current_year:
        facts["current_year"] = current_year
    return facts


def _romanise(hanja: str) -> str:
    """The report's own English name for a stem or branch.

    Reusing `saju_html.translate_inline` rather than a second table on purpose: this
    is the same mapping the client sees in the report, so the letter cannot disagree
    with the page it introduces. Imported lazily to keep this package light.
    """
    if not hanja:
        return ""
    try:
        from saju_html import translate_inline

        return translate_inline(hanja).strip()
    except Exception:  # pragma: no cover - only if the translation tables are missing
        return hanja


def _pillar_facts(pillar) -> Dict[str, Any]:
    """One pillar, with the names and elements the report uses."""
    from saju_engine.lookup import BRANCH_INFO, STEM_INFO

    stem_info = STEM_INFO.get(pillar.stem, {})
    branch_info = BRANCH_INFO.get(pillar.branch, {})
    return {
        "position": pillar.position,
        "hanja": pillar.combined,
        "romanised": f"{_romanise(pillar.stem)} {_romanise(pillar.branch)}".strip(),
        "stem_element": stem_info.get("element", ""),
        "branch_element": branch_info.get("element", ""),
        "animal": branch_info.get("animal", ""),
        "hidden_stems": [
            f"{stem} ({_romanise(stem)}, {role})" for role, stem in pillar.hidden_stems
        ],
    }


def _dominant_classes(chart, tengod_class: Dict[str, str]) -> List[Dict[str, Any]]:
    """The ten-god classes this chart actually leans on, most first, with counts.

    Counts, not just names: the audit caught a report claiming three "dominant"
    classes while its own table showed one class appearing five times and another
    twice. A model handed bare names makes the same mistake.
    """
    from collections import Counter

    counts: Counter = Counter()
    for hit in (getattr(chart, "ten_gods", None) or []):
        cls = tengod_class.get(getattr(hit, "tengod", ""), "")
        if cls:
            counts[cls] += 1
    return [{"class": cls, "count": count} for cls, count in counts.most_common(3)]


def _stars(chart) -> List[str]:
    """Present stars, in the report's own English-plus-Hanja form."""
    from saju_engine.stars import STAR_LABELS

    hits = getattr(chart, "stars", None) or {}
    out = []
    for name in sorted(hits):
        if not hits[name]:
            continue
        label = STAR_LABELS.get(name)
        out.append(_romanise(label) if label else name.replace("_", " ").title())
    return out


def _current_sewoon(chart) -> Optional[Dict[str, Any]]:
    """The annual overlay for the year the report was generated for."""
    sewoon = list(getattr(chart, "sewoon", None) or [])
    if not sewoon:
        return None
    hit = sewoon[len(sewoon) // 2]
    return {
        "year": hit.year,
        "combined": hit.combined,
        "ten_god": getattr(hit, "stem_tengod_en", "") or getattr(hit, "stem_tengod", ""),
        "relationships": sorted(set(getattr(hit, "relationship_types", None) or [])),
    }


_SIGNATURE_RE = re.compile(r"Chart signature:\s*(.+)", re.IGNORECASE)


def _chart_signature(report_md: str) -> str:
    """The engine's one good sentence — the natural spine of the letter."""
    match = _SIGNATURE_RE.search(report_md or "")
    return match.group(1).strip().strip("*_ ") if match else ""


_UNCERTAINTY_KEYS = ("primary_hour_pillar", "alternative_hour_pillar", "corrected_time")


def _hour_uncertainty(chart) -> Optional[Dict[str, Any]]:
    """Birth-time ambiguity, if the chart is a knife-edge case.

    The audit's own design for this page says the letter must carry "any caveat
    about birth-time accuracy". The engine already computes the margin; the letter
    just has to say it out loud.
    """
    boundary = ((getattr(chart, "solar_correction", None) or {}).get("hour_boundary")) or None
    if not boundary:
        return None
    out: Dict[str, Any] = {k: boundary.get(k) for k in _UNCERTAINTY_KEYS
                           if boundary.get(k) is not None}
    # One precise margin, not two conflicting ones. Sending both `distance_minutes: 1`
    # and `distance_seconds: 41` invited the model to merge them into "a minute and a
    # half" — a rounded minute and 41 seconds are not the same claim, and this is the one
    # page where that costs the most. `distance_seconds` is the true margin; the minutes
    # figure is only its whole-minute rounding.
    seconds = boundary.get("distance_seconds")
    if seconds is not None:
        out["margin_seconds"] = round(float(seconds))
        out["margin_text"] = f"{out['margin_seconds']} seconds"
    elif boundary.get("distance_minutes") is not None:
        out["margin_minutes"] = boundary["distance_minutes"]
        out["margin_is_rounded"] = True
    return out


def _render_facts(facts: Dict[str, Any]) -> List[str]:
    lines: List[str] = []

    def walk(value: Any, indent: str = "  ") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}{key}:")
                    walk(item, indent + "  ")
                else:
                    lines.append(f"{indent}{key}: {_fmt(item)}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}-")
                    walk(item, indent + "  ")
                else:
                    lines.append(f"{indent}- {_fmt(item)}")
        else:
            lines.append(f"{indent}{_fmt(value)}")

    walk(facts)
    return lines


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


# ── doctrine excerpts ─────────────────────────────────────────────────────────────

# Which sections of which knowledge files ground which part of a letter. Keyword
# match on the heading, in a fixed order, so the selection is reproducible.
_SOURCES: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("09-interpretation-method.md", (
        "Step 1 · ", "Step 2 · ", "Step 3 · Determine the Favorable Element",
    )),
    ("17-climate-method.md", ("The Four Climate Bands", "How This Combines With")),
    ("03-five-elements.md", (
        "When Each Element Is Strong", "When Each Element Is Weak",
        "용신 (Favorable Element) — High-Level Logic", "희신 / 기신",
    )),
    ("05-ten-gods.md", (
        "1. 비겁", "2. 식상", "3. 재성", "4. 관성", "5. 인성",
    )),
    ("02-branches.md", (
        "Branch Six Combinations", "Branch Clashes", "Branch Three Punishments",
    )),
)


def _sections(path: Path) -> List[Tuple[str, str]]:
    """(heading, body) for every `##`/`###` heading in a knowledge file."""
    if not path.exists():
        return []
    out: List[Tuple[str, str]] = []
    heading = ""
    body: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") or line.startswith("### "):
            if heading:
                out.append((heading, "\n".join(body).strip()))
            heading = line.lstrip("# ").strip()
            body = []
        elif heading:
            body.append(line)
    if heading:
        out.append((heading, "\n".join(body).strip()))
    return out


def _trim(text: str, max_words: int = MAX_EXCERPT_WORDS) -> str:
    """First paragraph(s) up to ``max_words``, so an excerpt stays readable inline."""
    words: List[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        candidate = paragraph.strip()
        if not candidate or candidate.startswith("|") or candidate.startswith("#"):
            continue
        words.extend(candidate.split())
        if len(words) >= max_words:
            break
    return " ".join(words[:max_words])


MAX_EXCERPT_WORDS_TOTAL = 750


def _select_excerpts(facts: Dict[str, Any], knowledge_root: Path) -> Tuple[Excerpt, ...]:
    """Deterministic section selection: chart-derived picks first, then the file list.

    Order is fixed and the match is a plain substring test on the heading, so the same
    chart always produces the same pack — which is what the tests assert and what makes
    a drafted letter auditable after the fact.
    """
    excerpts: List[Excerpt] = []
    seen: set = set()

    def add(filename: str, matcher) -> None:
        if len(excerpts) >= MAX_EXCERPTS:
            return
        if sum(e.words for e in excerpts) >= MAX_EXCERPT_WORDS_TOTAL:
            return
        for heading, body in _sections(knowledge_root / filename):
            if (filename, heading) in seen or not matcher(heading):
                continue
            text = _trim(body)
            if not text:
                continue
            seen.add((filename, heading))
            excerpts.append(Excerpt(file=filename, section=heading, text=text,
                                    words=len(text.split())))
            return

    favorable = facts.get("favorable_element") or {}
    band = favorable.get("climate_band") or ""
    if band and band != "temperate":
        # The climate method is what explains the favourable element in most charts.
        add("17-climate-method.md", lambda h: "The Four Climate Bands" in h)
    for cls in (facts.get("dominant_ten_god_classes") or [])[:3]:
        add("05-ten-gods.md", lambda h, c=cls: f"({c})" in h)

    for filename, keywords in _SOURCES:
        for keyword in keywords:
            add(filename, lambda h, k=keyword: k in h)
    return tuple(excerpts)


# ── constraints ──────────────────────────────────────────────────────────────────

_CONSTRAINTS = (
    f"Length: {LETTER_MIN_WORDS}–{LETTER_MAX_WORDS} words. One page.",
    "Second person, present tense, addressed to the client as \"you\". No name, no "
    "greeting, no signature — the reader adds those.",
    "Name the two or three chart features that drive the whole reading, and say why "
    "they matter. Use only the FACTS.",
    "Warm and plain. No fortune-telling absolutes: no \"will definitely\", no "
    "\"guaranteed\", no medical, legal or financial certainty.",
    "If HOUR_UNCERTAINTY is present, spend one sentence on it: what it would change "
    "if the recorded birth time is a few minutes out, and what would settle it.",
    "Never mention the engine, the pipeline, a step number, a file path, a price, or "
    "\"the querent\". Write as a person, not as software.",
    "Every interpretive claim must rest on one of the EXCERPTS. Cite them by their "
    "exact ids; do not cite anything else and do not invent doctrine.",
    "Prefer the concrete over the general: two Horses at noon is worth more than "
    "\"strong Earth energy\".",
)


def _constraints_for(section: str) -> Tuple[str, ...]:
    if section != "letter":
        raise ValueError(f"unsupported section: {section!r}")
    return _CONSTRAINTS


def _report_sections(report_md: str, pii_terms: Sequence[str]) -> Tuple[str, ...]:
    """The report's own section headings — what the letter may point forward to."""
    out: List[str] = []
    for line in (report_md or "").splitlines():
        if not line.startswith("## "):
            continue
        heading = line[3:].strip()
        if not heading:
            continue
        lowered = heading.casefold()
        if any(term and term.casefold() in lowered for term in pii_terms):
            continue
        out.append(heading)
    # The first heading is the report title ("Name — Tier"); it carries the client's
    # name and is not a section the letter should reference.
    return tuple(out[1:]) if out else ()


def build_pack(
    chart,
    report_md: str,
    *,
    section: str = "letter",
    knowledge_root: Optional[Path] = None,
    pii_terms: Iterable[str] = (),
) -> GroundingPack:
    """Build the pack for one section from a computed chart and its report markdown.

    ``pii_terms`` are values that must not appear anywhere in the pack (the client's
    name, date of birth, place). They are used twice: to drop any report heading that
    contains one, and — via ``GroundingPack.contains_pii`` — to prove none was sent.
    """
    terms = tuple(t.strip() for t in pii_terms if t and t.strip())
    facts = _facts(chart, report_md)
    return GroundingPack(
        section=section,
        facts=facts,
        excerpts=_select_excerpts(facts, knowledge_root or KNOWLEDGE_ROOT),
        constraints=_constraints_for(section),
        report_sections=_report_sections(report_md, terms),
        pii_terms=terms,
    )
