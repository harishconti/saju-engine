"""Tests for `saju_engine.hanja_glossary.inject_hanja`."""
from __future__ import annotations

import inspect

from saju_engine import hanja_glossary
from saju_engine.hanja_glossary import inject_hanja


def test_glossary_source_has_no_duplicate_keys():
    """F-15 (2026-09-26 audit): "육해", "일주", "월지" were each defined twice
    in HANJA_GLOSSARY with identical values (harmless, redundant)."""
    src = inspect.getsource(hanja_glossary)
    dict_src = src[src.index("HANJA_GLOSSARY"):src.index("\n}\n") + 2]
    import re
    keys = re.findall(r'^\s*"([^"]+)":', dict_src, re.MULTILINE)
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, f"duplicate glossary keys: {dupes}"


def test_prefix_term_does_not_split_an_already_annotated_longer_term():
    """Regression for the 2026-09-20 bug (external report review): "천덕" is a
    prefix of the longer glossary term "천덕귀인". Text that already spells
    out "천덕귀인 (天德貴人)" (e.g. hand-authored, or from a different code
    path) must NOT get a second, word-splitting annotation inserted in the
    middle of the longer term — the old check only looked immediately after
    the SHORT term's own end (finding "귀인", not "("), so it missed that a
    LONGER term at the same position already had its Hanja written a few
    characters later, producing "천덕 (天德)귀인 (天德貴人)".
    """
    text = "**천덕귀인 (天德貴人)** (at 辛): virtue, protection, honorable character."
    result = inject_hanja(text, set())
    assert result == text, f"text must be unchanged (already annotated): {result!r}"
    assert "천덕 (" not in result, f"the longer term must not be split: {result!r}"


def test_shorter_prefix_term_still_gets_annotated_when_standalone():
    """The fix must not suppress legitimate annotation of a short term when
    it appears on its own, unrelated to any longer term."""
    result = inject_hanja("천덕 is not itself a ten-god or star name here.", set())
    assert "천덕 (天德)" in result


def test_prefix_term_does_not_split_a_compound_not_itself_in_the_glossary():
    """Regression for the SAME 2026-09-20 bug, the harder variant: "역마" is a
    prefix of "역마살", but "역마살" is NOT itself a HANJA_GLOSSARY key (only
    the base "역마" is). Hand-authored text that already spells out
    "역마살 (驛馬殺, Post Horse Star)" must not get a second annotation
    inserted after "역마", splitting it into "역마 (驛馬)살 (驛馬殺, ...)" —
    confirmed live in Harish's regenerated report before this fix.
    """
    text = "**역마살 (驛馬殺, Post Horse Star)** is natally active at 巳."
    result = inject_hanja(text, set())
    assert result == text, f"text must be unchanged (already annotated): {result!r}"
    assert "역마 (" not in result, f"the compound must not be split: {result!r}"


def test_longest_term_wins_when_both_are_bare():
    """Both "천덕귀인" and "천덕" are unannotated in the input; the longer
    term must be the one that gets glossed (existing longest-first
    behaviour), not the shorter prefix."""
    result = inject_hanja("천덕귀인 is a star.", set())
    assert "천덕귀인 (天德貴人)" in result
    assert "천덕 (天德)귀인" not in result


def test_pre_annotated_compound_is_not_further_split():
    """Regression for the 2026-09-20 bug (own find, while implementing R12's
    annual-activation note): "합" (a bare 1-character glossary key) sits
    embedded inside "병신합수" — a freshly-built 천간합 label that is NOT
    itself a glossary key, and even "병" (a real glossary term, 病, that
    happens to collide with the Stem 丙's transliteration) sits at its
    start. `annual_activation_note` defends against this by pre-annotating
    the whole compound with its own Hanja ("병신합수 (丙辛合水)") before the
    text ever reaches `inject_hanja` — this must survive a subsequent
    `inject_hanja` pass completely unchanged (the right-side "already
    annotated" lookahead must recognize the whole compound as done),
    not get a second annotation spliced into "병" or "합" mid-word.
    """
    text = "the annual stem forms 병신합수 (丙辛合水) with your Day Master"
    result = inject_hanja(text, set())
    assert result == text, f"pre-annotated compound must not be re-split: {result!r}"


def test_single_char_term_embedded_at_start_of_unlisted_compound_is_a_known_limit():
    """Documents a known, narrower limit of `inject_hanja` alone (not fixed
    here — the real defense is `annual_activation_note`'s pre-annotation,
    see the test above): a single-character glossary term with no Hangul
    character before it (e.g. "병" at the very start of "병신합수") has no
    left neighbour to check, so the left-boundary guard cannot catch it by
    itself. Raw, un-pre-annotated compounds fed straight to `inject_hanja`
    can still mis-annotate in this specific position; callers that build
    ad-hoc compound labels must pre-annotate them, as `annual_activation_note`
    now does, rather than rely on `inject_hanja` to infer word boundaries
    from a single-character match with nothing on either side.
    """
    text = "the annual stem forms 병신합수 with your Day Master"
    result = inject_hanja(text, set())
    assert "병 (病)신합수" in result  # known limitation, not asserted as correct


def test_single_char_term_still_annotated_when_standalone():
    """The same term ("합") must still be annotated normally when it truly
    stands alone (not embedded in a longer unlisted compound)."""
    result = inject_hanja("the 합 is important here.", set())
    assert "합 (合)" in result


def test_term_already_inside_a_bare_parenthetical_is_not_double_parenthesized():
    """F-4 (2026-09-26 audit): "(대운)" written in ordinary prose (the term
    already sitting inside an open parenthetical, with no Hanja) became
    "(대운 (大運))" in every generated report — `inject_hanja` only ever
    checked for an existing annotation immediately AFTER the term, never
    checked whether the term was already sitting inside an open paren.
    """
    text = "The current major luck period (대운) shapes this decade."
    result = inject_hanja(text, set())
    assert "(大運)" not in result, f"must not inject inside an existing paren: {result!r}"
    assert "((" not in result and "))" not in result, f"no nested parens: {result!r}"
