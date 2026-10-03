"""P3 Task 7 (user decision 2026-10-03): a "likely" 종격 takes the dominant
element as its 용신 (knowledge/07-special-formations.md:73); "possible" keeps
the 억부/조후 resolution; a reader override still wins."""
from types import SimpleNamespace

from saju_engine import compute_chart
from saju_engine import lookup as L
from saju_engine import yongsin as Y

_LIKELY = dict(year=1948, month=9, day=9, hour=1, minute=47,
               utc_offset=9.0, longitude=127.0, gender="M", name="jong-likely")


def _likely_chart():
    return compute_chart(**_LIKELY)


def test_likely_jonggyeok_follows_dominant_element():
    chart = _likely_chart()
    forms = chart.patterns["special_forms"]
    assert forms and forms[0]["confidence"] == "likely"
    assert forms[0]["name_ko"] == "종재"
    dominant = forms[0]["dominant_element"]
    assert dominant == "Metal"  # 丁 DM: Metal = 재 (wealth)
    fe = Y.favorable_element(chart)
    assert fe.element == dominant
    assert fe.method == "jonggyeok-follow"
    assert fe.confidence == "heuristic"
    assert fe.supporting == L.GENERATED_BY[dominant]  # Earth generates Metal
    assert fe.unfavorable == L.OVERCOMES[dominant]    # knowledge/03 cycle used by _derive_from_yongsin
    assert "종재" in fe.note and "Metal" in fe.note
    assert fe.unfavorable_method == "derived-from-yongsin"


def test_dominant_element_on_every_special_form_incl_alias():
    import json, pathlib
    fx = json.loads((pathlib.Path(__file__).parent / "validation/fixtures/patterns.json").read_text())
    inp = next(e for e in fx if e["id"] == "jong-종식상-1998")["input"]
    forms = compute_chart(**inp, name="alias").patterns["special_forms"]
    assert {f["name_ko"] for f in forms} == {"종식상", "종자"}
    for form in forms:
        assert form["dominant_element"] in {"Wood", "Fire", "Earth", "Metal", "Water"}


def test_possible_jonggyeok_keeps_eokbu_resolution():
    # the pinned chart comes from the patterns fixture, not guessed dates
    import json, pathlib
    fx = json.loads((pathlib.Path(__file__).parent / "validation/fixtures/patterns.json").read_text())
    inp = next(e for e in fx if e["id"] == "jong-visible-bigyeop-possible-종관-1938")["input"]
    chart = compute_chart(**inp, name="possible")
    forms = chart.patterns["special_forms"]
    assert forms and all(f["confidence"] == "possible" for f in forms)
    fe = Y.favorable_element(chart)
    assert fe.method != "jonggyeok-follow"
    assert (fe.element, fe.method) == ("Fire", "climate-balanced")


def test_override_wins_on_likely_chart():
    fe = Y.favorable_element(_likely_chart(), override="Water")
    assert (fe.element, fe.method) == ("Water", "reader-confirmed")


def test_chart_level_reader_override_wins_on_likely_chart():
    chart = _likely_chart()
    chart.strength_assessment["reader_override_favorable"] = "Fire"
    fe = Y.favorable_element(chart)
    assert (fe.element, fe.method) == ("Fire", "reader-confirmed")


def test_chart_without_patterns_still_resolves():
    sa = {"verdict": "weak", "candidate_favorable": "Wood",
          "candidate_supporting": "Fire", "month_branch": "子", "element_counts": {}}
    chart = SimpleNamespace(strength_assessment=sa, pillars=[])
    fe = Y.favorable_element(chart)
    assert fe.method != "jonggyeok-follow"
    assert fe.element in {"Wood", "Fire", "Earth", "Metal", "Water"}


def _fixture_chart(fixture_id):
    import json, pathlib
    fx = json.loads((pathlib.Path(__file__).parent / "validation/fixtures/patterns.json").read_text())
    return compute_chart(**next(e for e in fx if e["id"] == fixture_id)["input"], name=fixture_id)


def test_likely_jonggyeok_governs_ahead_of_climate():
    """1983 (癸亥 甲子 戊子 癸亥): the 조후 check would pick Fire for a cold
    winter chart, but a "likely" 종재 follows the dominant Water."""
    fe = Y.favorable_element(_fixture_chart("jong-likely-종재-1983"))
    assert (fe.element, fe.method) == ("Water", "jonggyeok-follow")
    assert fe.climate_element == "Fire"  # 조후 remedy differs from the followed element


def test_premium_report_explains_follow_without_claiming_reader_review():
    from saju_engine.premium_report import generate_premium_report
    md = generate_premium_report(_fixture_chart("jong-likely-종재-1983"), tier="deep",
                                 generation_date="2026-10-03")
    why = next(l for l in md.splitlines() if l.startswith("- **Why this element:**"))
    assert "following grid (종격)" in why
    assert "does not govern a following grid" in why
    assert "reader has weighed" not in why
