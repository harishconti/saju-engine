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


# ── S2 follow-up: compat labels must not print mismatched percentages ──────
import re

import pytest

from saju_engine.compat import compat_combined_elements, compat_yongshin

_PAIRS = [
    ((1990, 6, 15, 10, "M"), (1992, 3, 20, 14, "F")),
    ((1985, 11, 2, 6, "M"), (1988, 8, 8, 20, "F")),
    ((1978, 1, 25, 23, "M"), (1981, 9, 30, 3, "F")),
    ((2000, 2, 29, 12, "F"), (1996, 12, 1, 18, "M")),
    ((1969, 7, 7, 8, "M"), (1974, 4, 14, 16, "F")),
]


def _chart(t):
    y, m, d, h, g = t
    return compute_chart(year=y, month=m, day=d, hour=h, minute=0,
                         gender=g, utc_offset=9.0, longitude=127.0)


@pytest.mark.parametrize("pa,pb", _PAIRS)
def test_compat_d_and_f_labels_print_no_percentages(pa, pb):
    a, b = _chart(pa), _chart(pb)
    d = compat_yongshin(a, b)
    f = compat_combined_elements(a, b)
    for flag in d.flags + f.flags:
        assert "%" not in flag, flag
    assert not re.search(r"=\s*\d+(\.\d+)?%", f.narrative), f.narrative


# ── Hour-boundary disclosure (2026-10-22) ───────────────────────────────────
def test_compat_report_discloses_a_knife_edge_hour_pillar():
    """Harish × Prethivika (2026-10-22): Prethivika's corrected solar time sits 3
    minutes from the 寅 boundary, and Harish's own chart is knife-edge too — the
    natal products warn about this, but the compat report silently presented the
    hour pillar as certain. It now carries the same disclosure per partner."""
    harish = compute_chart(name="Harish", gender="M", year=1992, month=6, day=4,
                           hour=3, minute=10, longitude=79.4408, utc_offset=5.5,
                           reference_year=2026, reference_month=10, reference_day=22)
    prethivika = compute_chart(name="Prethivika", gender="F", year=1993, month=3, day=19,
                               hour=3, minute=17, longitude=79.8083, utc_offset=5.5,
                               reference_year=2026, reference_month=10, reference_day=22)
    md = generate_compat_report(harish, prethivika, "Harish", "Prethivika", tier="basic")
    assert "⚠ Hour-boundary note (Prethivika)" in md
    assert "丙寅" in md  # the alternate hour pillar the reader should weigh
    assert "乙丑" in md  # the primary hour pillar actually used
    # ...and a chart with no boundary note stays clean.
    quiet = compute_chart(gender="F", year=1990, month=6, day=15, hour=10, minute=0,
                          utc_offset=9.0, longitude=127.0)
    quiet_md = generate_compat_report(quiet, prethivika, "Quiet", "Prethivika", tier="basic")
    assert "Hour-boundary note (Quiet)" not in quiet_md
