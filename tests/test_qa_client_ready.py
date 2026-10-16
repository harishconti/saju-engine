"""Tests for the client-ready gate (`tools/qa_client_ready.py`).

Every case here is a string from the external audit of the delivered Deep report
(`docs/analysis/2026-10-16-deep-report-audit.md` §2). The gate exists so those
defects cannot reach a client again, so the tests are written against the audit's
own wording rather than invented examples.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "qa_client_ready.py"


def _gate():
    spec = importlib.util.spec_from_file_location("qa_client_ready", GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _gate()


def codes(text: str, **kwargs) -> set:
    return {f.code for f in gate.scan(text, **kwargs)}


def artefact(text: str, **kwargs) -> set:
    """Codes raised for text as a *client artefact* (the rendered page).

    Some rules are artefact-only by design: the engine markdown legitimately
    carries "a Earth" (the renderer corrects the article), a pure-CJK gloss and a
    live `knowledge/` citation.
    """
    return codes(text, rendered=True, **kwargs)


# ── the audit's defect strings ───────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    # §2.1 #2 — the client's name, lowercase input straight from the form.
    ("## prakash — Deep Destiny Report\n\nBody.\n", "LOWERCASE_NAME"),
    # §2.1 #3 — double glosses from word-by-word substitution.
    ("Day Master: Gi (Yin Earth, Gi Earth) sits at the centre.", "DOUBLE_GLOSS"),
    ("(binding without transforming, binding without transforming) is the reading.", "DOUBLE_GLOSS"),
    # §2.1 #4 — internal machinery.
    ("the querent should confirm this with the querent's own records.", "INTERNAL_JARGON"),
    ("The engine has weighed both.", "INTERNAL_JARGON"),
    ("derived from the month pillar, per Step 2.", "INTERNAL_JARGON"),
    ("The engine flags a likely Companion Grid.", "INTERNAL_JARGON"),
    ("year_stem and year_branch_middle feed the table.", "INTERNAL_JARGON"),
    # §2.3 — grammar.
])
def test_audit_defects_are_caught(text, expected):
    """Rules that read the engine markdown OR the artefact."""
    assert expected in codes(text), f"{expected} not raised for {text!r}"


@pytest.mark.parametrize("text,expected", [
    # §2.1 #3 — gloss shapes: an artefact concern (see `artefact()`).
    ("A Jeong-Im Wood combination (Jeong Im combination Wood) is present.", "DOUBLE_GLOSS"),
    ("Myeongri (Korean Saju tradition) (destiny principles) shaped this.", "DOUBLE_GLOSS"),
    ("Bathing (bathe bath) describes the phase.", "WEAK_GLOSS"),
    ("Nurturing (nurture) follows.", "DOUBLE_GLOSS"),
    ("per 's '3 days = 1 year' rule, the count differs.", "ERASED_SOURCE"),
    # A citation the renderer half-removed. Every report carried "(per)" on its first
    # screen until 2026-10-16; the engine now cites in the form the stripper removes whole.
    ("supported by element relation (per); its stage follows.", "DANGLING_CITATION"),
    ("see the method (see) for the argument.", "DANGLING_CITATION"),
    # §2.3 — grammar is corrected at the render layer, so it is checked there.
    ("Born in a Earth chart with the engine reading as strong.", "GRAMMAR_ARTICLE"),
    ("This is a Indirect Resource year.", "GRAMMAR_ARTICLE"),
    ("The nervous system system needs care.", "REPEATED_WORD"),
])
def test_gloss_and_grammar_defects_are_caught_in_the_artefact(text, expected):
    assert expected in artefact(text), f"{expected} not raised for {text!r}"


@pytest.mark.parametrize("text", [
    # The intended notation: English then the Hanja. Not a defect.
    "Direct Officer (正官) governs the year.",
    "The Day Master is Gi (Yin Earth, soft field soil).",
    "Gyeong (庚) (main) is the hidden stem.",
    "Hidden stems: Yang Water, Yang Metal appear.",
    "A Hurting Officer window opens; an honest reading follows.",
    "The ten-year year-by-year timing is in the table.",
    "How is Saju different from Western astrology?",
])
def test_intended_output_is_not_flagged(text):
    assert codes(text) == set(), f"false positive on {text!r}"


# ── markdown vs artefact ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("> In plain words: a note.", "TEMPLATE_DEBRIS"),
    ("<!-- decade-roadmap:start -->", "TEMPLATE_DEBRIS"),
    ("*Engine-generated premium report draft. Interpretive prose must be reviewed.*",
     "TEMPLATE_DEBRIS"),
    ("see knowledge/17-climate-method.md for the argument", "TEMPLATE_DEBRIS"),
])
def test_render_time_stripped_things_only_fail_in_the_artefact(text, expected):
    """These are legitimate in the engine markdown and stripped on render.

    A `>` blockquote, the roadmap's HTML comment, the reviewer's note, and a
    `knowledge/` citation are all *expected* in the markdown — the defect is only
    their survival into what the client opens.
    """
    assert codes(text) == set(), "flagged in markdown, where it is legitimate"
    assert expected in codes(text, rendered=True), "not caught in the artefact"


def test_repeated_sentence_is_flagged_beyond_the_limit():
    sentence = ("A sentence long enough to count as prose rather than a fragment arrives here.")
    text = "\n".join([sentence] * 3)
    assert "REPEATED_SENTENCE" in codes(text)
    # Two occurrences are allowed: a report has eight decades and two sections.
    assert "REPEATED_SENTENCE" not in codes("\n".join([sentence] * 2))


def test_price_is_allowed_only_in_the_free_sample():
    text = "The Deep Destiny Report ($55) adds year-by-year timing."
    assert "PRICE_IN_COPY" in codes(text, tier="deep")
    assert "PRICE_IN_COPY" not in codes(text, tier="sample")


# ── the CLI, on real report output ───────────────────────────────────────────────

def test_cli_flags_a_real_report_and_clears_a_clean_one(tmp_path):
    clean = tmp_path / "clean.md"
    clean.write_text(
        "## Alice Smith — Deep Destiny Report\n\n"
        "You were born on a Gyeong (庚) day, with Water (水) as your favourable element.\n",
        encoding="utf-8",
    )
    ok = subprocess.run([sys.executable, str(GATE), str(clean), "--name", "Alice"],
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "CLEAN" in ok.stdout

    dirty = tmp_path / "dirty.md"
    dirty.write_text("## alice smith — Deep Destiny Report\n\nthe querent should check per Step 2.\n",
                     encoding="utf-8")
    bad = subprocess.run([sys.executable, str(GATE), str(dirty), "--json"],
                         capture_output=True, text=True)
    assert bad.returncode == 1
    assert "LOWERCASE_NAME" in bad.stdout and "INTERNAL_JARGON" in bad.stdout
    # --warn-only is the reviewer's deliberate override at the CLI level.
    warn = subprocess.run([sys.executable, str(GATE), str(dirty), "--warn-only"],
                          capture_output=True, text=True)
    assert warn.returncode == 0


def test_every_golden_report_passes_the_gate():
    """The committed report snapshots must be deliverable.

    When the gate was written, the golden deep report raised 45 findings — "the
    querent" ×30, "the engine", raw keys, double glosses. The jargon pass closed
    them, so the goldens are now the standing proof that the gate is satisfied by
    real output rather than only by its own fixtures. A regression anywhere in the
    report generators shows up here, on every tier, for every chart.
    """
    failures = {}
    for md in sorted((REPO_ROOT / "tests" / "golden").glob("*.md")):
        tier = "sample" if md.stem.endswith("sample") else "deep"
        result = subprocess.run(
            [sys.executable, str(GATE), str(md), "--tier", tier, "--json"],
            capture_output=True, text=True)
        if result.returncode != 0:
            failures[md.name] = result.stdout.strip()[:400]
    assert not failures, failures
