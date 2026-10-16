#!/usr/bin/env python3
"""Client-ready gate for a generated Saju report.

Everything this checks was found in a delivered report by the external audit of
2026-10-16 (`docs/analysis/2026-10-16-deep-report-audit.md`); the audit's own
recommendation was to turn it into a permanent check so the same defects cannot
sail again. It never edits the report.

    python3 tools/qa_client_ready.py report.md
    python3 tools/qa_client_ready.py report.md --pdf report.pdf   # also check the artefact
    python3 tools/qa_client_ready.py report.md --name "Prakash S." --tier deep
    python3 tools/qa_client_ready.py report.md --json
    python3 tools/qa_client_ready.py report.md --warn-only        # never exit non-zero

Exit codes: 0 clean, 1 flagged, 2 usage error.

Two sources, because they catch different things. The **markdown** is the engine's
output and is always available; the **PDF** is what the client actually opens, and
only there can a renderer leak show up (a literal `>` blockquote marker, a template
comment, the reviewer's own note). `intake_admin.py approve` runs both.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, NamedTuple

# ── Rules ────────────────────────────────────────────────────────────────────────

# Internal machinery that must never reach client copy (audit §2.1 #4). `Step \d`
# is the pipeline's own step numbering ("per Step 2"); `candidate` is the engine's
# hedge ("a dominant pattern candidate"); `you` is the voice, so `the querent` —
# tarot-trade jargon a client never uses — reads as machine output.
_JARGON = [
    (r"\bquerent\b", "the querent -> you"),
    (r"\bthe engine\b", "internal: 'the engine'"),
    (r"\bthis engine\b", "internal: 'this engine'"),
    (r"\bengine has\b", "internal: 'the engine has'"),
    (r"\bengine flags\b", "internal: 'the engine flags'"),
    (r"\bengine reads\b", "internal: 'the engine reads'"),
    (r"\bStep \d+\b", "internal step reference"),
    # "candidate dates" is ordinary English; the hedging is what reads as
    # machinery ("a pattern candidate", "a candidate reading").
    (r"\b(?:pattern|grid|formation|structure) candidate\b", "engine hedging: 'pattern candidate'"),
    (r"\bcandidate reading\b", "engine hedging: 'candidate reading'"),
    (r"\b[a-z]+_(?:stem|branch|middle|element|tengod|class)\b", "raw engine key"),
]

# Template debris (audit §2.1 #6, #9). The rendered-only ones are legitimate in
# the markdown — a `>` line is a blockquote note — and are defects only if they
# survive into the artefact.
_DEBRIS = [
    # Stripped at render time (`strip_engine_drafts`, and the ReportLab renderer
    # drops comments), so only a survivor in the artefact is a defect.
    (r"<!--", "raw HTML comment", True),
    (r"\bENGINE DRAFT\b", "engine-draft marker", False),
    (r"\[INTERPRET", "unfilled placeholder", False),
    (r"\bTODO\b|\bFIXME\b|\bXXX\b", "authoring placeholder", False),
    (r"^\s*>\s", "blockquote marker leaked into the rendered text", True),
    # The markdown legitimately carries `*(see knowledge/…)*` citations, which the
    # renderer strips; only a surviving path in the artefact is a defect.
    (r"knowledge/", "internal repo path", True),
    # The review note: a paying buyer must not be told nobody read their report
    # (audit §2.1 #1). `strip_engine_drafts` removes it from client renders.
    (r"Engine-generated premium report draft", "reviewer note in client copy", True),
    (r"qualified reader before client delivery", "reviewer note in client copy", True),
]

# A term glossed twice by word-by-word substitution (audit §2.1 #3):
# "Gi (Yin Earth, Gi Earth)", "(binding without transforming, binding without
# transforming)", "Myeongri (Korean Saju tradition) (destiny principles)".
_DOUBLE_GLOSS = [
    (re.compile(r"\b(\w+) \(([^()]*), \1\b"), "term repeated inside its own gloss"),
    (re.compile(r"\(([^(),]{4,}?), \1\)"), "same phrase twice in one gloss"),
    (re.compile(r"\(([^()]{3,})\) \(\1\)"), "duplicate parenthetical"),
]

# The engine's *intended* notation is "Direct Officer (正官)" — English, then the
# Hanja. A parenthetical that only repeats the English already written
# ("a Jeong-Im Wood combination (Jeong Im combination Wood)") is the slop the
# owner's convention is not asking for, and it is distinguishable by the gloss
# carrying no CJK. Compared on word *sets*, so word order does not hide it.
_CJK = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uac00-\ud7af\uff00-\uffef]")
_PAREN = re.compile(r"\(([^()]{6,})\)")
# Two parentheticals in a row: fine when the first is the Hanja gloss ("Gyeong
# (庚) (main)"), a gloss-of-a-gloss otherwise ("(Korean Saju tradition) (destiny
# principles)") — audit §2.1 #3.
_ADJACENT_PARENS = re.compile(r"\(([^()]{3,})\) \(([^()]{3,})\)")

# A gloss whose two words share a stem adds nothing: "Bathing (bathe bath)",
# "Nurturing (nurture)". Element and polarity words legitimately repeat inside a
# list ("Yang Water, Yang Metal"), so they are allowed to.
_WEAK_GLOSS = re.compile(r"\(([A-Za-z]{3,})e? ([A-Za-z]{3,})\)")
_WEAK_GLOSS_OK = {"yang", "yin", "wood", "fire", "earth", "metal", "water",
                  "direct", "indirect", "officer", "wealth", "resource", "god"}

# "per 's '3 days = 1 year' rule" — the quoted source's name was erased, leaving a
# stranded possessive (audit §2.1 #3).
_STRANDED_POSSESSIVE = re.compile(r"\bper 's\b|\bby 's\b")

# A price belongs on the order, not in the reading (audit §2.1 #8). The free
# sample tier is the one place it is copy by design: that report's job is to
# offer the paid tiers.
_PRICE = re.compile(r"\$\d")
_PRICE_EXEMPT_TIERS = {"sample"}

# "a Earth", "a Indirect", "a Hurting Officer ten-god" (audit §2.3, grammar row).
_A_AN = re.compile(r"\b([Aa]n?)\s+(\w+)")
# The article exceptions come from the fixer itself, so this gate can never
# disagree with the correction the renderers apply.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from saju_html import _A_EXCEPTIONS, _AN_EXCEPTIONS  # noqa: E402

# "nervous system system" (audit §2.3). Legitimate doubles are allowed through.
# Hyphen-aware: "ten-year year-by-year" is not a repeated word.
_REPEATED_WORD = re.compile(r"(?<![\w-])(\w{3,})\s+\1(?![\w-])", re.IGNORECASE)
_DOUBLE_WORD_OK = {"had", "that", "very", "no", "so", "bye", "well", "she", "he", "the"}

# Split on sentence-ending punctuation followed by something that can start a
# sentence. The lookahead matters: "release vs. scatter" is one sentence, and
# splitting at the abbreviation produced a phantom sentence made of a
# paragraph's constant tail — reported as repeated eight times.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\u2018\u201c])")
_TITLE_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)

MIN_SENTENCE_CHARS = 40
DEFAULT_MAX_SENTENCE_REPEATS = 2


class Finding(NamedTuple):
    code: str
    source: str        # "markdown" or "pdf"
    line: int
    excerpt: str
    note: str


def _lines(text: str) -> Iterable[tuple[int, str]]:
    for n, line in enumerate(text.splitlines(), start=1):
        yield n, line


def _is_table_row(line: str) -> bool:
    return line.lstrip().startswith("|")


def _sentence_repeats(text: str, max_repeats: int) -> list[Finding]:
    """Sentences appearing more than ``max_repeats`` times, verbatim.

    The audit measured that what readers notice is the same *skeleton* with the
    nouns swapped (27% of prose words) and that is a writing problem a regex
    cannot see. An exact repeat, however, is always a template artefact — the
    decade paragraph used to be one sentence printed sixteen times — so that is
    what is checked, and it is cheap to keep clean.
    """
    body = "\n".join(line for line in text.splitlines() if not _is_table_row(line))
    counts: dict[str, int] = {}
    sample: dict[str, str] = {}
    for raw in _SENTENCE_SPLIT.split(body):
        sentence = re.sub(r"\s+", " ", raw).strip()
        if len(sentence) < MIN_SENTENCE_CHARS:
            continue
        key = sentence.casefold()
        counts[key] = counts.get(key, 0) + 1
        sample.setdefault(key, sentence)
    findings = []
    for key, n in counts.items():
        if n > max_repeats:
            findings.append(Finding(
                "REPEATED_SENTENCE", "", 0, sample[key][:110],
                f"appears {n} times (limit {max_repeats})"))
    return findings


def scan(
    text: str,
    *,
    source: str = "markdown",
    rendered: bool = False,
    name: str | None = None,
    tier: str | None = None,
    max_sentence_repeats: int = DEFAULT_MAX_SENTENCE_REPEATS,
) -> list[Finding]:
    """Check one text (engine markdown, or text extracted from the PDF)."""
    findings: list[Finding] = []

    for n, line in _lines(text):
        for pattern, note in _JARGON:
            m = re.search(pattern, line, re.IGNORECASE)
            if m:
                findings.append(Finding("INTERNAL_JARGON", source, n,
                                        line.strip()[:110], f"{note} ({m.group(0)!r})"))
        for pattern, note, rendered_only in _DEBRIS:
            if rendered_only and not rendered:
                continue
            m = re.search(pattern, line, re.IGNORECASE if pattern.startswith("\\b") else 0)
            if m:
                findings.append(Finding("TEMPLATE_DEBRIS", source, n,
                                        line.strip()[:110], f"{note} ({m.group(0)!r})"))
        for regex, note in _DOUBLE_GLOSS:
            m = regex.search(line)
            if m:
                findings.append(Finding("DOUBLE_GLOSS", source, n,
                                        m.group(0)[:110], note))
        for m in _REPEATED_WORD.finditer(line):
            if m.group(1).casefold() not in _DOUBLE_WORD_OK:
                findings.append(Finding("REPEATED_WORD", source, n,
                                        m.group(0), "word repeated"))
        if tier not in _PRICE_EXEMPT_TIERS and _PRICE.search(line):
            findings.append(Finding("PRICE_IN_COPY", source, n,
                                    line.strip()[:110], "a price in the reading"))

        # The gloss-*shape* checks and the stranded possessive run on the artefact
        # only. In the engine markdown "재성 (Wealth)" is the author's own notation
        # and "per knowledge/08's …" is a live citation — the renderer decides what
        # survives — so a redundancy is a defect only once it is on the page. The
        # exact-repeat check above is different: "X (Y, X)" can only come from the
        # translator, so it fails in both.
        if rendered:
            for m in _ADJACENT_PARENS.finditer(line):
                first, second = m.group(1), m.group(2)
                if _CJK.search(first) and not re.search(r"[A-Za-z]", first):
                    continue  # "Gyeong (庚) (main)": English, Hanja, then a Korean gloss
                findings.append(Finding("DOUBLE_GLOSS", source, n, m.group(0)[:110],
                                        "a gloss of a gloss"))
            for m in _PAREN.finditer(line):
                gloss = m.group(1)
                if _CJK.search(gloss):
                    continue  # English + Hanja: the intended notation
                # Hyphens split too, so "Jeong-Im ... (Jeong Im ...)" is seen as the
                # repetition it is.
                before = {w.casefold().strip(",.") for w in
                          line[:m.start()].replace("-", " ").split()}
                words = [w.casefold().strip(",.") for w in gloss.replace("-", " ").split()]

                def _already_written(word: str) -> bool:
                    # Prefix-matched, so "Nurturing (nurture)" is caught as well as an
                    # exact repeat; five characters is enough to mean the same term.
                    return any(word == b or (len(word) >= 5 and b.startswith(word[:5]))
                               for b in before)

                if len(words) >= 1 and len(gloss) >= 5 and all(_already_written(w) for w in words):
                    findings.append(Finding("DOUBLE_GLOSS", source, n, m.group(0)[:110],
                                            "gloss only repeats the English before it"))
            for m in _WEAK_GLOSS.finditer(line):
                first, second = m.group(1).casefold(), m.group(2).casefold()
                if first in _WEAK_GLOSS_OK or second in _WEAK_GLOSS_OK:
                    continue
                if second.startswith(first[:4]) and first != second:
                    findings.append(Finding("WEAK_GLOSS", source, n, m.group(0),
                                            "a gloss that adds no information"))
            for m in _STRANDED_POSSESSIVE.finditer(line):
                findings.append(Finding("ERASED_SOURCE", source, n, m.group(0),
                                        "a quoted source's name was erased"))
            for m in _A_AN.finditer(line):
                article, word = m.group(1), m.group(2)
                stem = word.casefold()
                if (article.casefold() == "a" and stem[:1] in "aeiou"
                        and stem not in _A_EXCEPTIONS
                        and stem.split("-")[0] not in _A_EXCEPTIONS):
                    findings.append(Finding("GRAMMAR_ARTICLE", source, n,
                                            m.group(0), f"'a' before a vowel -> 'an {word}'"))
                if (article.casefold() == "an" and stem[:1] not in "aeiou"
                        and stem not in _AN_EXCEPTIONS):
                    findings.append(Finding("GRAMMAR_ARTICLE", source, n,
                                            m.group(0), f"'an' before a consonant -> 'a {word}'"))
    # The client's name is the first thing on the cover; it must not be raw input.
    m = _TITLE_RE.search(text)
    if m:
        given = name.split()[0] if name else m.group(1).split("—")[0].strip().split()[0] \
            if m.group(1).split("—")[0].strip() else ""
        if given and given[:1].islower():
            findings.append(Finding("LOWERCASE_NAME", source, 0, m.group(0)[:110],
                                    f"client name {given!r} is not title-cased"))

    findings.extend(Finding(f.code, source, f.line, f.excerpt, f.note)
                    for f in _sentence_repeats(text, max_sentence_repeats))
    return findings


# ── CLI ──────────────────────────────────────────────────────────────────────────

_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.DOTALL | re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


def _html_text(document: str) -> str:
    """Visible text of an HTML report, for the artefact checks.

    Script and style bodies are dropped so a CSS value or a JS string can never be
    mistaken for client copy, and the remaining tags are stripped to leave block
    boundaries as newlines — the same shape `pdftotext` gives the PDF path.
    """
    import html as _html

    stripped = _SCRIPT_STYLE_RE.sub("\n", document)
    stripped = re.sub(r"</(p|li|h[1-6]|tr|div|blockquote|nav)>", "\n", stripped,
                      flags=re.IGNORECASE)
    stripped = re.sub(r"<br\s*/?>", "\n", stripped, flags=re.IGNORECASE)
    return _html.unescape(_TAG_RE.sub("", stripped))


def _pdf_text(pdf: Path) -> str | None:
    if shutil.which("pdftotext") is None:
        print("pdftotext not installed — artefact not checked (`poppler-utils`).",
              file=sys.stderr)
        return None
    result = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"pdftotext failed on {pdf}: {result.stderr.strip()}", file=sys.stderr)
        return None
    return result.stdout


def main() -> int:
    ap = argparse.ArgumentParser(description="Client-ready gate for a Saju report.")
    ap.add_argument("report", type=Path, help="report markdown")
    ap.add_argument("--pdf", type=Path, default=None,
                    help="also check the rendered PDF (catches renderer leaks)")
    ap.add_argument("--html", type=Path, default=None,
                    help="also check the web document (the HTML the client opens)")
    ap.add_argument("--name", default=None, help="client name, to check its casing")
    ap.add_argument("--tier", default=None,
                    help="tier, so the free sample's price copy is allowed")
    ap.add_argument("--max-sentence-repeats", type=int, default=DEFAULT_MAX_SENTENCE_REPEATS,
                    help=f"fail when a sentence appears more than this (default "
                         f"{DEFAULT_MAX_SENTENCE_REPEATS})")
    ap.add_argument("--json", action="store_true", help="print JSON")
    ap.add_argument("--warn-only", action="store_true", help="never exit non-zero on findings")
    args = ap.parse_args()

    if not args.report.exists():
        print(f"no such report: {args.report}", file=sys.stderr)
        return 2

    findings = scan(args.report.read_text(encoding="utf-8"),
                    source="markdown", name=args.name, tier=args.tier,
                    max_sentence_repeats=args.max_sentence_repeats)
    if args.pdf is not None:
        if not args.pdf.exists():
            print(f"no such pdf: {args.pdf}", file=sys.stderr)
            return 2
        text = _pdf_text(args.pdf)
        if text is not None:
            findings.extend(scan(text, source="pdf", rendered=True, name=args.name,
                                 tier=args.tier,
                                 max_sentence_repeats=args.max_sentence_repeats))
    if args.html is not None:
        if not args.html.exists():
            print(f"no such html: {args.html}", file=sys.stderr)
            return 2
        findings.extend(scan(_html_text(args.html.read_text(encoding="utf-8")),
                              source="html", rendered=True, name=args.name,
                              tier=args.tier,
                              max_sentence_repeats=args.max_sentence_repeats))

    findings.sort(key=lambda f: (f.source, f.line, f.code))
    if args.json:
        print(json.dumps([f._asdict() for f in findings], indent=2))
    else:
        status = "CLEAN" if not findings else "FLAGGED"
        parts = ["markdown"]
        if args.pdf is not None:
            parts.append("pdf")
        if args.html is not None:
            parts.append("html")
        sources = " + ".join(parts)
        print(f"{status}: {args.report.name} ({sources}) — {len(findings)} finding(s)")
        for f in findings:
            where = f"{f.source}:{f.line}" if f.line else f.source
            print(f"  [{f.code}] {where}: {f.note}")
            if f.excerpt:
                print(f"      {f.excerpt}")

    if findings and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
