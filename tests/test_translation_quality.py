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


def test_ordinary_sago_words_are_not_glossed_storehouse():
    # 사고 is only the 四庫 "storehouse" in the engine's "(사고)" contexts; an
    # ordinary word such as 사고방식 must stay ONE unmapped word, never
    # "storehouse 방식"-style fragments.
    seen: set = set()
    out = translate_inline("사고방식이 다르다", unmapped=seen)
    assert "storehouse" not in out
    assert "사고방식이" in out
    assert set("사고방식이") <= seen


def test_storehouse_sense_is_translated():
    assert translate_inline("a natal storehouse (사고) is clashed") == "a natal storehouse is clashed"
    assert "storehouse branch" in translate_inline("사고 지지 충")


def test_phrase_rules_are_anchored():
    # 두 분 must not eat the front of 두 분석; 한눈에 보기 / 재성 혼잡 likewise.
    assert "the couple" not in translate_inline("두 분석")
    assert translate_inline("두 분은 잘 맞습니다").startswith("the couple")
    assert "At a Glance" not in translate_inline("한눈에 보기좋은")
    assert "Mixed Wealth" not in translate_inline("재성 혼잡함")


def test_unmapped_run_stays_one_word():
    out = translate_inline("결핍과 갈등")
    assert "결 핍" not in out and "갈 등" not in out
    out2 = translate_inline("갈등")
    assert out2 == "갈등"


def test_generic_words_do_not_fire_inside_other_words():
    for word in ("일부러", "불일치", "교차점", "원소리"):
        out = translate_inline(word)
        assert out == word, (word, out)
    assert "partial" in translate_inline("A → B 용신 Fire 일부 공급")
    assert "cross" in translate_inline("십신 교차")


def test_unknown_hangul_word_with_mapped_syllables_stays_whole():
    # 귀인배우 contains the branch/stem syllable 인; it must not become "귀 In (Tiger) 배 우".
    assert translate_inline("학파") == "학파"


def test_bigyeon_glossed_as_companion():
    for src in ("비견", "比肩", "비견 (比肩)"):
        out = translate_inline(src)
        assert "Pillar" not in out, (src, out)
        assert out.replace("(", "").replace(")", "").split() == ["Companion"], (src, out)


def test_ipha_solar_term_is_lixia():
    out = translate_inline("입하 (立夏)")
    assert "Lihai" not in out
    assert "Lixia" in out and "Start of Summer" in out
    assert "Lihai" not in translate_inline("입하")
