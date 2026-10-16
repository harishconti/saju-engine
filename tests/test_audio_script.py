#!/usr/bin/env python3
"""Tests for the spoken-word audio script (`src/saju_html/audio_script.py`).

The audio is generated **after** the human approves the PDF, so its only defence is that
it is a *deterministic derivation* of the approved text. These tests hold that line:
same input → same output, nothing outside the reviewed sections, no markup or glyphs,
and — the regression that motivated the whole design — **no clause mangled by stripping
Hanja**.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from saju_html.audio_script import (
    DEFAULT_MAX_CHARS,
    SPOKEN_SECTIONS,
    build_audio_script,
    chunk_for_tts,
    script_stats,
)

GOLDEN = Path(__file__).resolve().parent / "golden" / "kiran-deep.md"

pytestmark = pytest.mark.skipif(not GOLDEN.exists(), reason="golden deep report fixture missing")

CJK = re.compile(r"[\u4e00-\u9fff\uac00-\ud7a3]")


@pytest.fixture(scope="module")
def script() -> str:
    return build_audio_script(GOLDEN.read_text(encoding="utf-8"))


# ─────────────────────────── determinism ───────────────────────────


def test_same_report_yields_the_same_script():
    """Two calls must agree: the audio is a derivation, not a fresh composition."""
    md = GOLDEN.read_text(encoding="utf-8")
    assert build_audio_script(md) == build_audio_script(md)


def test_script_is_reproducible_across_a_fresh_read(script):
    assert build_audio_script(GOLDEN.read_text(encoding="utf-8")) == script


# ─────────────────────────── the mangled-clause regression ───────────────────────────


def test_hanja_is_translated_not_deleted():
    """The defect that shaped this module.

    The report writes ``shaped by **丙午** (편재)``. Deleting the glyphs instead of
    translating them left the husk "shaped by." — a broken sentence in the narration.

    Tested on a controlled input rather than the full report, because in the real script
    this clause may legitimately fall outside its section's budget.
    """
    md = (
        "## Chart at a Glance\n\n"
        "Right now, in June 2026, you are moving through a year whose energy is shaped by "
        "**丙午** (편재). This sits inside your broader **戊申** major luck period (ages 39-48), "
        "whose theme is 편관.\n"
    )
    script = build_audio_script(md)
    assert "shaped by Bing O" in script          # 丙午, not deleted
    assert "Indirect Wealth" in script           # 편재, not deleted
    assert "Mu Shin" in script                   # 戊申
    assert "shaped by." not in script            # the husk that started all this
    assert "whose theme is." not in script


def test_the_real_script_contains_no_grammatical_husks(script):
    """The same class of defect, checked on real output."""
    for husk in ["shaped by.", "theme is.", "is shaped by ,", "()", "(, )"]:
        assert husk not in script


def test_no_cjk_glyphs_survive(script):
    assert not CJK.search(script), CJK.search(script).group(0)


# ─────────────────────────── only what was promised ───────────────────────────


def _as_spoken(heading: str) -> str:
    """Headings are spoken, so `&` becomes "and" — the one documented substitution."""
    return re.sub(r"\s{2,}", " ", heading.replace("&", " and ")).strip()


@pytest.mark.parametrize("heading", SPOKEN_SECTIONS)
def test_each_promised_section_is_narrated(script, heading):
    """Every topic the report promises the audio covers must actually be in it.

    An earlier single-budget implementation let the opening sections consume the whole
    allowance and silently dropped the timing windows and the recommendations — the two
    things the audio is *sold* on.
    """
    assert _as_spoken(heading) in script


@pytest.mark.parametrize(
    "excluded",
    ["Table of Contents", "How to Use This Report", "Auspicious Dates",
     "Monthly Lucky Dates", "What the Terms Mean", "Sources & Limits",
     "MP3 Audio Summary"],
)
def test_reference_material_is_never_narrated(script, excluded):
    assert excluded not in script


def test_sections_outside_the_promise_are_dropped(script):
    """Career & Wealth, Relationships and the date tables are in the PDF but not the audio."""
    for absent in ["Career & Wealth", "Natal Pattern Analysis", "Lifetime Decade Roadmap"]:
        assert absent not in script


# ─────────────────────────── it must be speakable ───────────────────────────


@pytest.mark.parametrize("marker", ["|", "**", "###", ">", "knowledge/", "[UNCERTAIN]", "⚠"])
def test_markup_and_citations_are_stripped(script, marker):
    assert marker not in script


def test_no_empty_parentheses_from_dropped_glosses(script):
    assert "()" not in script
    assert "(, )" not in script


def test_length_targets_a_ten_minute_listen(script):
    stats = script_stats(script)
    # ~150 words/minute, so 8-11 minutes is the target band.
    assert 8 * 60 <= stats["estimatedSeconds"] <= 11 * 60
    assert len(script) <= DEFAULT_MAX_CHARS


def test_it_does_not_read_the_whole_report(script):
    """A read-through of 76k characters would be over an hour of audio."""
    assert len(script) < 15_000


# ─────────────────────────── trimming and chunking ───────────────────────────


def test_max_chars_is_respected_and_cut_on_a_sentence():
    trimmed = build_audio_script(GOLDEN.read_text(encoding="utf-8"), max_chars=2_000)
    assert len(trimmed) <= 2_000
    assert trimmed.endswith((".", "!", "?"))


def test_trimming_never_returns_nothing():
    assert build_audio_script(GOLDEN.read_text(encoding="utf-8"), max_chars=50).strip()


def test_chunks_respect_the_limit_and_lose_nothing(script):
    chunks = chunk_for_tts(script, max_chars=2_000)
    assert len(chunks) > 1
    assert all(len(c) <= 2_000 for c in chunks)
    # No text is dropped, only whitespace normalised at the joins.
    rejoined = " ".join(chunks).split()
    assert rejoined == script.split()


def test_a_single_overlong_sentence_is_split_not_dropped():
    monster = ("word " * 500).strip() + "."
    chunks = chunk_for_tts(monster, max_chars=200)
    assert all(len(c) <= 200 for c in chunks)
    assert "".join(chunks).count("word") == 500


def test_chunking_rejects_a_nonsense_limit(script):
    with pytest.raises(ValueError):
        chunk_for_tts(script, max_chars=0)


# ─────────────────────────── degenerate input ───────────────────────────


def test_a_report_with_none_of_the_sections_yields_an_empty_script():
    """No crash, no fallback content — an empty script is the honest answer."""
    assert build_audio_script("## Something Else Entirely\n\nBody text.\n") == ""


def test_empty_input_is_handled():
    assert build_audio_script("") == ""


def test_stats_are_sane(script):
    stats = script_stats(script)
    assert stats["chars"] == len(script)
    assert stats["words"] > 500
    assert stats["estimatedSeconds"] > 0
