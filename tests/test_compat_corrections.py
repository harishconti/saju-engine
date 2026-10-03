"""P2 Task 7 (user decision 2026-10-03): four client-visible compat corrections.

Pairs are pinned by birth inputs (found by scanning); see the report in
.superpowers/sdd/p2/task-7-report.md."""
import itertools

import pytest

from saju_engine import compat
from saju_engine.compat_report import generate_compat_report
from saju_engine.engine import compute_chart

REF = dict(reference_year=2026, reference_month=6, reference_day=1)
BIRTHS = [
    (1917, 11, 14, 10, "M", 9.0, 128.74), (1946, 9, 1, 8, "M", 9.0, 128.74),
    (1990, 6, 15, 10, "F", -5.0, -74.0), (1985, 12, 20, 6, "F", 9.0, 126.98),
    (1992, 3, 20, 14, "F", 9.0, 127.0), (1978, 4, 2, 23, "M", 9.0, 127.0),
    (2001, 8, 8, 8, "F", 5.5, 77.2), (1965, 1, 30, 4, "M", 9.0, 129.0),
]


def _c(idx):
    y, m, d, h, g, o, lon = BIRTHS[idx]
    return compute_chart(year=y, month=m, day=d, hour=h, minute=0, gender=g,
                         utc_offset=o, longitude=lon, name=f"P{idx}", **REF)


CHARTS = [_c(i) for i in range(len(BIRTHS))]
PAIRS = list(itertools.combinations(range(len(CHARTS)), 2))


def _rep(i, j):
    return compat.compat_score(CHARTS[i], CHARTS[j])


def _md(i, j, tier="deep"):
    return generate_compat_report(CHARTS[i], CHARTS[j], CHARTS[i].name, CHARTS[j].name,
                                  generation_date="2026-06-01", tier=tier)


def _flags(rep):
    for sub in rep.sub_systems():
        yield from sub.flags


CLASH_GUIDE = "Day-branch clash"


def test_cross_clash_does_not_trigger_daybranch_clash_guidance():
    # (0,3): primary 육합 + a cross-branch 육충.
    rep = _rep(0, 3)
    codes = [f.code for f in rep.daybranch.flags]
    assert "daybranch.combine" in codes and "daybranch.cross_clash" in codes
    for tier in ("basic", "deep"):
        md = _md(0, 3, tier)
        assert "spouse palaces (일지) combine" in md
        assert CLASH_GUIDE not in md
    assert "Day-branch clash (일지 육충) is present" not in _md(0, 3)


def test_cross_clash_only_pair_is_not_called_a_palace_clash():
    # (4,7): only a cross 육충, primary is neutral.
    codes = [f.code for f in _rep(4, 7).daybranch.flags]
    assert codes == ["daybranch.cross_clash"]
    md = _md(4, 7)
    assert CLASH_GUIDE not in md
    assert "spouse palaces (일지) carry a classical clash" not in md


def test_real_primary_clash_still_gets_clash_guidance():
    # (0,1): primary 육충.
    assert "daybranch.clash" in [f.code for f in _rep(0, 1).daybranch.flags]
    assert "Day-branch clash (일지 육충) is present" in _md(0, 1)
    assert "Day-branch clash" in _md(0, 1, "basic")


@pytest.mark.parametrize("i,j", PAIRS)
def test_clash_severity_is_score_delta(i, j):
    rep = _rep(i, j)
    for f in _flags(rep):
        if f.code == "daybranch.cross_clash":
            assert f.severity == 5, f
        elif f.code == "year_branch.clash":
            assert f.severity == 3, f
        elif f.code == "daybranch.clash":
            assert f.severity == 25, f
        elif f.code == "daybranch.cross_self_punish":
            assert f.severity == 2, f


def test_clash_severity_pairs_exist_in_scan():
    codes = {f.code for i, j in PAIRS for f in _flags(_rep(i, j))}
    assert {"daybranch.cross_clash", "year_branch.clash", "daybranch.clash"} <= codes


def _F(text, code, kind, sev=0):
    return compat.Flag(text, kind=kind, code=code, severity=sev)


def test_cover_ranks_cross_clash_below_primary_and_ilju_red_flags():
    flags = [
        _F("a: cross 육충", "daybranch.cross_clash", "red", 5),
        _F("b: 일지 자형", "daybranch.self_punish", "red", 8),
        _F("c: ilju RED FLAG", "ilju_pair.red", "red", 12),
    ]
    top = compat._top_red(flags)
    assert [f.severity for f in top] == [12, 8, 5]
    assert top[-1].code == "daybranch.cross_clash"


def test_top_yellow_keeps_primary_harm_break_despite_cap():
    # Hangul "일" sorts after "육"/"가": without the key, 일지 해 is truncated off.
    others = [_F(f"가{n}: caution", f"x.{n}", "yellow") for n in range(7)]
    harm = _F("일지 해 (육해)", "daybranch.harm", "yellow")
    brk = _F("일지 파 (육파)", "daybranch.break", "yellow")
    top = compat._top_yellow(others + [harm, brk])
    assert len(top) == 5
    assert top[:2] == sorted([harm, brk], key=str)
    assert harm in top and brk in top


@pytest.mark.parametrize("pair,code", [((0, 2), "daybranch.harm"), ((5, 6), "daybranch.break")])
def test_primary_harm_and_break_are_yellow(pair, code):
    rep = _rep(*pair)
    flags = [f for f in rep.daybranch.flags if f.code == code]
    assert flags and all(f.kind == "yellow" for f in flags)
    token = "일지 해" if code == "daybranch.harm" else "일지 파"
    assert any(token in y for y in rep.yellow_flags), rep.yellow_flags


def test_direction_differs_is_not_favorable():
    seen = 0
    for i, j in PAIRS:
        for f in _rep(i, j).daeun_sync.flags:
            if f.code == "daeun_sync.direction_differs":
                seen += 1
                assert f.kind is None
    assert seen


def test_deep_snapshot_uses_verdict_label():
    from tests.golden.cases import _chart
    a, b = _chart("lux"), _chart("kiran")
    md = generate_compat_report(a, b, a.name, b.name, generation_date="2026-06-01", tier="deep")
    assert "Seasonal strength verdict:** Very Strong" in md
    assert "Seasonal strength verdict:** extreme" not in md
