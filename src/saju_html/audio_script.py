#!/usr/bin/env python3
"""Turn an approved report into a spoken-word script for the MP3 audio summary.

**Deterministic on purpose.** The audio is a *derivation* of text a human already
approved, so it must add no claim of its own: no model is called, and the same markdown
always yields the same script. That is what allows the MP3 to be produced *after*
approval without a second review pass — it says nothing the approved PDF does not say.

It lives in ``saju_html`` because it is a *rendering* of the report, next to the PDF and
HTML renderers, and because it must run the same text pipeline they do:
``strip_source_citations`` → ``strip_engine_drafts`` → ``translate_inline``.

That pipeline step is not cosmetic. The raw markdown writes Hanja with a Romanised gloss
("Day Master: Sin (Yin Metal, 辛金)"); deleting the glyphs instead of translating them
leaves grammatical husks — "energy is shaped by." , "its theme is." Reusing the
translation keeps every clause whole and identical to what the PDF says.

Two jobs:

    build_audio_script(markdown)   the whole narration, ~9,000 characters (~9 min)
    chunk_for_tts(script)          split on sentence boundaries for the TTS API
"""
from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

from saju_html import strip_engine_drafts, strip_source_citations, translate_inline

# What the report *promises* the audio contains. Keeping this list next to that promise
# is deliberate: if the copy changes, this must change with it.
SPOKEN_SECTIONS: Tuple[str, ...] = (
    "Chart at a Glance",
    "Day Master Portrait",
    "Timing: Major Luck & Annual Windows",
    "Practical Guidance Summary",
    "Closing Note",
)

# Never spoken, even if a heading would otherwise match: reference material, lists of
# dates, and the audio note itself (that one is meta-instruction, not content).
EXCLUDED_SECTIONS: Tuple[str, ...] = (
    "Table of Contents",
    "How to Use This Report",
    "Auspicious Dates",
    "Monthly Lucky Dates",
    "What the Terms Mean",
    "Sources & Limits",
    "MP3 Audio Summary",
)

DEFAULT_MAX_CHARS = 9_000
DEFAULT_CHUNK_CHARS = 2_000

# Latin-1 plus the punctuation the reports use. Anything outside this is a leftover
# glyph (an unmapped Hanja, an emoji) that an English voice would spell out or skip.
_NON_SPEECH = re.compile(r"[^\x20-\x7E\u2018\u2019\u201C\u201D\u2013\u2014\u2026]")

_SPOKEN_SUBSTITUTIONS: Sequence[Tuple[str, str]] = (
    ("&", " and "),
    ("—", ", "),
    ("–", ", "),
    ("→", " to "),
    ("·", ", "),
    ("~", " approximately "),
    (" e.g. ", " for example "),
    (" i.e. ", " that is "),
    (" vs. ", " versus "),
    (" vs ", " versus "),
    ("%", " percent"),
)

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_SLASH_SEPARATED = re.compile(r"\s*/\s*")


def _prepare(markdown: str) -> str:
    """The same text pipeline the PDF renderer runs, so the script matches the PDF."""
    text = strip_source_citations(markdown)
    text = strip_engine_drafts(text)
    # `keep_unmapped=False` drops any glyph the translator does not know, which is what
    # the ReportLab path does (its fonts have no CJK coverage).
    return translate_inline(text, keep_unmapped=False)


def _split_sections(markdown: str) -> List[Tuple[str, List[str]]]:
    """[(heading, body_lines)] for every level-2 heading, in document order."""
    sections: List[Tuple[str, List[str]]] = []
    heading: Optional[str] = None
    body: List[str] = []
    for line in markdown.splitlines():
        if line.startswith("## "):
            if heading is not None:
                sections.append((heading, body))
            heading, body = line[3:].strip(), []
        elif heading is not None:
            body.append(line)
    if heading is not None:
        sections.append((heading, body))
    return sections


def _wanted(heading: str) -> bool:
    if any(excluded in heading for excluded in EXCLUDED_SECTIONS):
        return False
    return any(heading.startswith(wanted) for wanted in SPOKEN_SECTIONS)


def _clean_prose(text: str) -> str:
    """One line of report prose -> speakable text, or '' when it is not prose."""
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped.startswith(("|", ">", "---", "```", "<")):
        return ""  # table, callout, rule, fence, html
    if stripped.startswith(("- [", "* [")):
        return ""
    if "knowledge/" in stripped:
        return ""  # citations are for the reader, not the listener

    line = stripped
    line = re.sub(r"^#{3,6}\s*", "", line)          # heading marker
    line = re.sub(r"^[-*+]\s+", "", line)          # bullet
    line = re.sub(r"^\d+[.)]\s+", "", line)        # numbered
    line = line.replace("**", "").replace("`", "")
    line = re.sub(r"(?<!\w)\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
    line = line.replace("[UNCERTAIN]", "")
    line = re.sub(r"\(Audio summary included\)\s*", "", line)
    line = line.replace("⚠", "")
    # "From Structure / Companion Grid" reads badly aloud; a comma flows.
    line = _SLASH_SEPARATED.sub(", ", line)

    line = _NON_SPEECH.sub(" ", line)            # safety net for leftovers
    line = re.sub(r"\(\s*[,;]?\s*\)", "", line)   # empty parens from a dropped gloss
    line = re.sub(r",\s*\)", ")", line)

    for old, new in _SPOKEN_SUBSTITUTIONS:
        line = line.replace(old, new)

    line = re.sub(r"[ \t]{2,}", " ", line)
    line = re.sub(r"\s+([,.;:])", r"\1", line)
    return line.strip(" -–—,;:")


# Per-section share of the character budget. A single global trim let the opening
# sections consume everything, which silently dropped the timing windows and the
# recommendations — i.e. it would have shipped an audio summary that did not cover what
# the report promises it covers. Allocating per section guarantees every promised topic
# is present. Values sum to 1.0.
SECTION_BUDGETS: dict = {
    "Chart at a Glance": 0.14,
    "Day Master Portrait": 0.26,
    "Timing: Major Luck & Annual Windows": 0.30,
    "Practical Guidance Summary": 0.25,
    "Closing Note": 0.05,
}
_DEFAULT_SHARE = 0.05


def _spoken_sentences(heading: str, body: List[str]) -> List[str]:
    """The speakable sentences of one section, chapter heading first."""
    out: List[str] = []
    spoken_heading = _clean_prose(heading)
    if spoken_heading:
        out.append(f"{spoken_heading.rstrip('.')}.")

    guidance = heading.startswith("Practical Guidance")
    for raw in body:
        # Sub-headings carry the recommendation text in the guidance list, but elsewhere
        # they would pepper the narration with bare labels.
        if raw.strip().startswith("###") and not guidance:
            continue
        line = _clean_prose(raw)
        if not line:
            continue
        for sentence in _SENTENCE_END.split(line):
            piece = sentence.strip()
            if piece:
                out.append(piece if piece.endswith((".", "!", "?")) else f"{piece}.")

    return out


def _take(sentences: List[str], budget: int) -> Tuple[List[str], int]:
    """As many whole sentences as fit in ``budget``; never zero if there is content.

    Returning at least one sentence is what makes "every promised section is narrated"
    hold even when a section's opening sentence is longer than its allocation.
    """
    taken: List[str] = []
    size = 0
    for sentence in sentences:
        if taken and size + len(sentence) + 1 > budget:
            break
        taken.append(sentence)
        size += len(sentence) + 1
    return taken, size


def build_audio_script(
    markdown: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    sections: Sequence[str] = SPOKEN_SECTIONS,
) -> str:
    """A spoken script derived only from ``markdown``.

    Deterministic: no model, no randomness, no clock. Every promised section is
    represented, and the total stays within ``max_chars``.
    """
    prepared = _prepare(markdown)

    parts: List[Tuple[str, List[str]]] = []
    for heading, body in _split_sections(prepared):
        if not (_wanted(heading) and any(heading.startswith(s) for s in sections)):
            continue
        sentences = _spoken_sentences(heading, body)
        if sentences:
            parts.append((heading, sentences))

    if not parts:
        return ""

    def share(heading: str) -> float:
        return SECTION_BUDGETS.get(heading, _DEFAULT_SHARE)

    taken = [(h, *_take(s, max(1, int(max_chars * share(h))))) for h, s in parts]

    # Redistribute whatever the short sections left over, in proportion to how much
    # unused content each truncated section still has. Keeps the script near the target
    # rather than under-filling it.
    leftover = max_chars - sum(size for _, _, size in taken)
    if leftover > 0:
        spare = [max(0, len(s) - len(kept)) for (_, s), (_, kept, _) in zip(parts, taken)]
        total_spare = sum(spare)
        if total_spare:
            taken = [
                (h, *_take(s, max(1, int(max_chars * share(h)) + int(leftover * left / total_spare))))
                for (h, s), (_, _, _), left in zip(parts, taken, spare)
            ]

    script = re.sub(r"\s{2,}", " ", " ".join(" ".join(kept) for _, kept, _ in taken)).strip()
    if len(script) <= max_chars:
        return script

    # Safety net: a section's guaranteed first sentence may have pushed us over.
    kept_all: List[str] = []
    total = 0
    for sentence in _SENTENCE_END.split(script):
        piece = sentence if sentence.endswith((".", "!", "?")) else f"{sentence}."
        if total + len(piece) + 1 > max_chars:
            break
        kept_all.append(piece)
        total += len(piece) + 1
    return (" ".join(kept_all) if kept_all else script[:max_chars]).strip()


def chunk_for_tts(script: str, *, max_chars: int = DEFAULT_CHUNK_CHARS) -> List[str]:
    """Split on sentence boundaries so each chunk fits a single TTS request.

    ElevenLabs allows 40,000 characters per request on a paid plan, 5,000 on
    ``eleven_v3`` and only 2,500 on a free one — so a conservative default works on any
    plan, and raising ``max_chars`` simply reduces the number of joins. A sentence longer
    than the budget is hard-split rather than dropped.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    chunks: List[str] = []
    current: List[str] = []
    size = 0

    for sentence in _SENTENCE_END.split(script.strip()):
        piece = sentence.strip()
        if not piece:
            continue
        if len(piece) > max_chars:
            if current:
                chunks.append(" ".join(current))
                current, size = [], 0
            # Raw slices, deliberately not stripped: each chunk is sent to the TTS API
            # independently, and stripping a boundary space would merge two words if the
            # chunks were ever concatenated. A leading/trailing space is harmless there.
            while len(piece) > max_chars:
                chunks.append(piece[:max_chars])
                piece = piece[max_chars:]
            if piece:
                current, size = [piece], len(piece)
            continue
        if size + len(piece) + 1 > max_chars:
            chunks.append(" ".join(current))
            current, size = [], 0
        current.append(piece)
        size += len(piece) + 1

    if current:
        chunks.append(" ".join(current))
    return chunks


def script_stats(script: str) -> dict:
    """Figures recorded alongside the audio, for cost and audit."""
    words = len(script.split())
    # ~150 words per minute is the ratio TTS vendors price and quote against.
    return {
        "chars": len(script),
        "words": words,
        "estimatedSeconds": round(words / 150 * 60),
    }
