"""Cross-report parity: compat must render the same numbers/labels as the
natal products for the same chart (audit 2026-10-01 S2/S3)."""
from types import SimpleNamespace

from saju_engine.compat_report import _period_status
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
