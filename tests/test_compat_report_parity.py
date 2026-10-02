"""Cross-report parity: compat must render the same numbers/labels as the
natal products for the same chart (audit 2026-10-01 S2/S3)."""
from types import SimpleNamespace

from saju_engine.compat_report import _period_status, generate_compat_report
from saju_engine.engine import compute_chart
from saju_engine.strength import element_balance_pct
from saju_engine.yongsin import FavorableElement

FE = FavorableElement(element="Water", method="weak-dm-support",
                      confidence="heuristic", note="", supporting="Metal",
                      unfavorable="Fire")


def _p(stem_e, branch_e):
    return SimpleNamespace(stem_element=stem_e, branch_element=branch_e)


def test_supporting_element_decade_is_favorable():
    assert _period_status(_p("Metal", "Earth"), FE) == "favorable"


def test_unfavorable_element_decade_is_unfavorable():
    assert _period_status(_p("Fire", "Earth"), FE) == "unfavorable"


def test_mixed_decade_is_neutral():
    assert _period_status(_p("Water", "Fire"), FE) == "neutral"


def test_compat_element_table_matches_natal_element_balance():
    a = compute_chart(year=1990, month=6, day=15, hour=10, minute=0,
                      gender="M", utc_offset=9.0, longitude=127.0)
    b = compute_chart(year=1992, month=3, day=20, hour=14, minute=0,
                      gender="F", utc_offset=9.0, longitude=127.0)
    md = generate_compat_report(a, b, "Alpha", "Beta", tier="deep")
    for name, chart in (("Alpha", a), ("Beta", b)):
        section = md.split(f"#### Element Balance — {name}", 1)[1].split("####", 1)[0]
        for elem, pct in element_balance_pct(chart).items():
            assert f"{elem} |" in section
            assert f"| {pct:.1f}% |" in section, (name, elem, pct)
