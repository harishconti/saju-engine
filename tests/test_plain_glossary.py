from pathlib import Path

from saju_engine import plain_glossary as PG

KB = Path(__file__).parent.parent / "knowledge"


def test_every_source_file_exists():
    for d in set(PG.PLAIN_GLOSSARY.values()):
        assert (KB / Path(d.source).name).exists(), d.source


def test_gloss_first_use_only_glosses_first_occurrence():
    used = set()
    out = PG.gloss_first_use("Direct Wealth here, and Direct Wealth again.", used)
    assert out.count("steady") == 1  # gloss text appears once
    assert out.index("steady") < out.index("again")


def test_gloss_longest_match_first():
    used = set()
    out = PG.gloss_first_use("천을귀인 appears", used)
    # must gloss the star, not partially match 천간
    assert "천을귀인" in out and "노블" not in out
    assert PG.PLAIN_GLOSSARY["천을귀인"].display in used


def test_gloss_skips_already_used():
    used = set()
    out1 = PG.gloss_first_use("대운 shapes a decade of life.", used)
    assert "ten-year" in out1  # first use is glossed
    out2 = PG.gloss_first_use("another 대운 shapes the next span.", used)
    assert "—" not in out2.split("대운")[1][:5]  # not re-glossed


def test_gloss_does_not_corrupt_markup_or_split_phrases():
    """Regression: gloss injection must never land in structured markup or split
    a noun phrase / list / emphasis span (surfaced regenerating a real report)."""
    cases = [
        "## Table of Contents\n\n- Monthly Lucky Dates\n- Day Master Portrait\n",  # TOC + substring
        "the Direct Officer (正官) stem values hierarchy",                        # attributive noun
        "a **절 (絶)/병 (病)/사 (死)** stage asks for openness",                    # slash list in bold
        "The Authority and Wealth pulls are present but balanced",               # compound subject
        "*정관격 / Direct Officer Grid*",                                          # italic label span
        "the querent goes into creative play, Output into creative play",        # elided-verb parallel
    ]
    for text in cases:
        out = PG.gloss_first_use(text, set())
        assert out == text, f"gloss corrupted: {out!r}"
    # a plain-prose first use still gets glossed
    got = PG.gloss_first_use("Your 대운 opens a fresh chapter every decade.", set())
    assert "ten-year" in got


def test_render_terms_section_tiering():
    used = ["Direct Wealth (正財)", "Major Luck (大運)"]
    assert PG.render_terms_section(used, "sample") == ""
    ess = PG.render_terms_section(used, "essential")
    deep = PG.render_terms_section(used, "deep")
    assert "## What the Terms Mean" in ess
    assert "Direct Wealth" in ess and "Major Luck" in ess
    assert len(deep) >= len(ess)  # deep carries the fuller note


def test_render_terms_section_only_used_terms():
    out = PG.render_terms_section(["Major Luck (大運)"], "deep")
    assert "Major Luck" in out
    assert "Peach Blossom" not in out
