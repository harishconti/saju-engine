"""Translation quality: phrase-level glosses, no bare-particle substitution."""
from pathlib import Path

import pytest

from saju_html import strip_engine_drafts, strip_source_citations, translate_inline

GOLDEN = sorted(Path(__file__).parent.joinpath("golden").glob("*.md"))

BAD = [
    "’s Mi",
    "storehouse 가",
    "people 석",
    "Kuigang (Commanding Star) (",
    "% Nurturing",
    "A to B",
    "B to A",
    "(Wealth mixed)",
    "(at a glance overview)",
]

GOOD = [
    "excess of B’s Unfavorable Element",
    "in A",
    "B’s Day Master element",
    "A’s Day Master element",
    "A (Sin) is B (Im)’s",
    "Couple Compatibility",
    "% Yang)",
    "Kuigang Star",
    "Mixed Wealth",
    "Compatibility at a Glance",
]


def _translate(path: Path) -> str:
    text = strip_engine_drafts(strip_source_citations(path.read_text(encoding="utf-8")))
    return translate_inline(text)


@pytest.fixture(scope="module")
def translated() -> dict:
    return {p.name: _translate(p) for p in GOLDEN}


@pytest.mark.parametrize("bad", BAD)
def test_no_garbled_phrases(translated, bad):
    hits = [n for n, t in translated.items() if bad in t]
    assert not hits, f"{bad!r} found in {hits}"


@pytest.mark.parametrize("good", GOOD)
def test_corrected_phrases_present(translated, good):
    assert any(good in t for t in translated.values()), good


def test_kuigang_source_line_renders_once(translated):
    for name, t in translated.items():
        for line in t.splitlines():
            if "Kuigang" in line and "charisma" in line:
                assert line.count("Kuigang") == 1, line


def test_cross_supply_meaning():
    out = translate_inline("A에 B의 기신 Metal 과다")
    assert out == "excess of B’s Unfavorable Element Metal in A"


def test_yin_yang_percent():
    assert "(38% Yang)" in translate_inline("결합 음양 불균형 (38% 양)")
    assert "(40% Yin)" in translate_inline("결합 음양 불균형 (40% 음)")


def test_tengod_tag():
    out = translate_inline("A (辛)는 B (壬)의 정인")
    assert out.startswith("A (Sin) is B (Im)’s")


def test_no_particle_injection():
    seen: set = set()
    out = translate_inline("의미 있는 분석", unmapped=seen)
    for injected in ("\u2019s", "people", "storehouse", " is ", " to "):
        assert injected not in out, out
    for kept in ("의", "있", "는", "분", "석"):
        assert kept in out, out
    assert {"의", "는", "분"} <= seen


def test_sagoga_not_garbled():
    out = translate_inline("사고가 있다")
    assert out.startswith("storehouse") and "가" in out
