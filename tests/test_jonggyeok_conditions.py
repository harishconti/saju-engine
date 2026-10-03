"""P2-W Option C (user decision 2026-10-03): 종격 confidence is decided from the
knowledge/07-special-formations.md:57-65 conditions, not a strength-score band.
See docs/analysis/2026-10-03-extreme-weak-verdict.md."""
from __future__ import annotations

import datetime
import random

from saju_engine import patterns as PAT
from saju_engine.engine import compute_chart
from saju_engine.prose_scaffold import _VERDICT_PLAIN_LABEL, generate_plain_words

KW = dict(utc_offset=9.0, longitude=127.0, gender="M")

# Pinned by a 120k-chart scan: weak verdict, dominant >= 50 %, in season at the
# month branch, no 비겁/인성 in any branch, hidden stem or visible stem.
LIKELY = {
    "1948-09-09 01:47": (dict(year=1948, month=9, day=9, hour=1, minute=47), "종재"),
    "1983-12-26 22:03": (dict(year=1983, month=12, day=26, hour=22, minute=3), "종재"),
}
# Same conditions but a visible 비겁 stem (unrooted in branches/hidden stems).
VISIBLE_ONLY = {
    "1938-01-05 23:56": (dict(year=1938, month=1, day=5, hour=23, minute=56), "종관"),
    "1943-03-26 05:13": (dict(year=1943, month=3, day=26, hour=5, minute=13), "종식상"),
}
# Rooted in a branch / hidden stem (in season, dominant >= 50 %).
ROOTED = {
    "1978-07-19 17:58": (dict(year=1978, month=7, day=19, hour=17, minute=58), "종관"),
}


def _conf(birth, name):
    c = compute_chart(**birth, **KW)
    forms = {f["name_ko"]: f["confidence"] for f in c.patterns["special_forms"]}
    return c, forms[name]


def test_has_rooting_visible_stem_counts():
    # DM 丁 (Fire); resource Wood. Branches/hidden stems carry neither.
    base = dict(day_master="丁", branches=["子", "子", "酉", "子"],
                hidden_stems=[("main", "癸"), ("main", "辛")])
    assert PAT._has_rooting(**base, visible_stems=["壬", "壬", "壬"]) is False
    assert PAT._has_rooting(**base, visible_stems=["丁", "壬", "壬"]) is True   # 비겁
    assert PAT._has_rooting(**base, visible_stems=["壬", "乙", "壬"]) is True   # 인성
    assert PAT._has_rooting(**base, visible_stems=[]) is False


def test_likely_charts():
    for key, (birth, name) in LIKELY.items():
        c, conf = _conf(birth, name)
        assert c.strength_assessment["verdict"] == "weak", key
        assert conf == "likely", key
        note = next(f["note"] for f in c.patterns["special_forms"] if f["name_ko"] == name)
        assert "extreme" not in note


def test_visible_bigyeop_or_inseong_stem_downgrades():
    for key, (birth, name) in VISIBLE_ONLY.items():
        c, conf = _conf(birth, name)
        assert conf == "possible", key
        f = next(f for f in c.patterns["special_forms"] if f["name_ko"] == name)
        assert "통근" in f["note"] or "rooting" in f["note"]


def test_rooted_chart_is_possible():
    for key, (birth, name) in ROOTED.items():
        assert _conf(birth, name)[1] == "possible", key


def test_balanced_and_strong_return_nothing():
    args = dict(day_master="甲", stems=["戊", "己", "甲", "戊"],
                branches=["辰", "戌", "丑", "未"],
                hidden_stems=[("main", "戊"), ("main", "己")] * 2,
                month_branch="辰")
    counts = PAT._element_counts(args["stems"], args["hidden_stems"])
    for v in ("balanced", "strong", "extreme"):
        assert PAT.detect_special_forms(element_counts=counts, strength_verdict=v, **args) == []
    out = PAT.detect_special_forms(element_counts=counts, strength_verdict="weak", **args)
    assert out and out[0]["confidence"] == "likely"
    # extreme_weak is no longer a recognised verdict
    assert PAT.detect_special_forms(element_counts=counts, strength_verdict="extreme_weak", **args) == []


def test_extreme_weak_never_emitted_sample():
    rnd = random.Random(7)
    s = datetime.date(1930, 1, 1).toordinal()
    e = datetime.date(2030, 12, 31).toordinal()
    seen = set()
    for _ in range(2000):
        d = datetime.date.fromordinal(rnd.randint(s, e))
        c = compute_chart(year=d.year, month=d.month, day=d.day, hour=rnd.randint(0, 23),
                          minute=rnd.randint(0, 59), **KW)
        seen.add(c.strength_assessment["verdict"])
    assert seen <= {"extreme", "strong", "balanced", "weak"}


def test_plain_label_for_extreme():
    assert _VERDICT_PLAIN_LABEL["extreme"] == "very strong"
    assert "extreme_strong" not in _VERDICT_PLAIN_LABEL
    from tests.golden.cases import CHARTS, REF
    c = compute_chart(**CHARTS["lux"], **REF)
    assert c.strength_assessment["verdict"] == "extreme"
    assert "reads as very strong" in generate_plain_words(c)["personality"]


def test_missing_month_branch_downgrades_to_possible():
    # Unrooted weak chart, Metal dominant (종재 for 丁). With the month branch
    # known and in season it is "likely"; with it unknown 득령 cannot be
    # confirmed, so it must be "possible" with an explanatory note.
    args = dict(day_master="丁", stems=["戊", "辛", "丁", "辛"],
                branches=["子", "酉", "酉", "子"],
                hidden_stems=[("main", "癸"), ("main", "辛"), ("main", "辛"), ("main", "癸")],
                strength_verdict="weak")
    counts = PAT._element_counts(args["stems"], args["hidden_stems"])
    known = PAT.detect_special_forms(element_counts=counts, month_branch="酉", **args)
    assert known and known[0]["confidence"] == "likely"
    for mb in ("", ):
        out = PAT.detect_special_forms(element_counts=counts, month_branch=mb, **args)
        assert out and out[0]["confidence"] == "possible"
        assert "month branch unknown" in out[0]["note"]
