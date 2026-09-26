"""용신 (favorable element) single-source-of-truth + cross-product consistency.

Regression guard for issue G3 / A1 (see improvements_issues.md): the favorable
element shown in a person's natal report must equal the one shown in any
compatibility report they appear in, and both must equal the resolver value.
"""
from __future__ import annotations

import pytest

from saju_engine.engine import compute_chart
from saju_engine.yongsin import FavorableElement, favorable_element
from saju_engine.premium_report import generate_premium_report
from saju_engine.compat_report import generate_compat_report
from saju_engine.climate import assess_climate


def _chart(year, month, day, hour, minute, longitude, gender, name="X"):
    return compute_chart(
        name=name, gender=gender, year=year, month=month, day=day,
        hour=hour, minute=minute, longitude=longitude, utc_offset=5.5,
        use_solar_time=True,
    )


CANDIDATES = [
    _chart(1993, 12, 11, 2, 45, 79.32, "F", "Sruthi"),
    _chart(1995, 1, 19, 23, 50, 78.713454, "M", "Mahesh"),
    _chart(2001, 6, 7, 16, 45, 76.65, "F", "Vishnu Priya"),
]

_ALLOWED_METHODS = {
    "strong-dm-drain", "weak-dm-support", "balanced-heuristic",
    "climate-balanced", "reader-confirmed",
}


@pytest.mark.parametrize("chart", CANDIDATES, ids=lambda c: c.name)
def test_resolver_shape(chart):
    fe = favorable_element(chart)
    assert isinstance(fe, FavorableElement)
    assert fe.element in {"Wood", "Fire", "Earth", "Metal", "Water"}
    assert fe.method in _ALLOWED_METHODS
    assert fe.confidence == "heuristic"
    assert fe.note and fe.note[0].isupper()


# Expected (element, supporting, climate_agrees) after the 조후 cross-check.
# Sruthi (子, cold) and Mahesh (丑, cold) both get a climate override to Fire;
# Vishnu Priya (午, hot) already agreed with Water, so she is unchanged —
# this is the regression case proving the merge is a no-op on agreement.
EXPECTED_WITH_CLIMATE = {
    "Sruthi": ("Fire", "Wood", False),
    "Mahesh": ("Fire", "Wood", False),
    "Vishnu Priya": ("Water", "Metal", True),
}


@pytest.mark.parametrize("chart", CANDIDATES, ids=lambda c: c.name)
def test_resolver_applies_climate_cross_check(chart):
    """Balanced-verdict charts route the headline element through 조후 (climate)."""
    expected_element, expected_supporting, expected_agrees = EXPECTED_WITH_CLIMATE[chart.name]
    fe = favorable_element(chart)
    assert fe.element == expected_element
    assert fe.supporting == expected_supporting
    assert fe.climate_agrees is expected_agrees
    assert fe.method == "climate-balanced"


@pytest.mark.parametrize("chart", CANDIDATES, ids=lambda c: c.name)
def test_natal_report_shows_resolver_value(chart):
    fe = favorable_element(chart).element
    md = generate_premium_report(chart, tier="deep")
    assert f"**Favorable Element:** {fe}" in md


@pytest.mark.parametrize("chart", CANDIDATES, ids=lambda c: c.name)
def test_compat_report_agrees_with_natal(chart):
    other = CANDIDATES[0] if chart is not CANDIDATES[0] else CANDIDATES[1]
    fe = favorable_element(chart).element

    # chart as Partner A — cover table row + Day Master snapshot
    md_a = generate_compat_report(chart, other, chart.name, other.name, tier="deep")
    assert f"{chart.day.combined} | {fe} |" in md_a
    assert f"#### Day Master Snapshot — {chart.name}" in md_a
    snap_a = md_a.split(f"#### Day Master Snapshot — {chart.name}", 1)[1]
    assert f"**Favorable element (용신):** {fe}" in snap_a

    # chart as Partner B
    md_b = generate_compat_report(other, chart, other.name, chart.name, tier="deep")
    assert f"{chart.day.combined} | {fe} |" in md_b


def test_compat_report_note_is_client_voice_not_engine_leak(chart=CANDIDATES[0]):
    other = CANDIDATES[1]
    md = generate_compat_report(chart, other, chart.name, other.name, tier="deep")
    assert "*Engine note:*" not in md
    assert "Heuristic only; final 용신 must be argued" not in md


def test_override_flips_confidence_and_wins():
    chart = CANDIDATES[0]
    fe = favorable_element(chart, override="Fire")
    assert fe.element == "Fire"
    assert fe.method == "reader-confirmed"
    assert fe.confidence == "reader-confirmed"


def test_override_flows_into_compat_display():
    a, b = CANDIDATES[0], CANDIDATES[1]  # a = Sruthi, climate-based favorable = Fire
    assert favorable_element(a).element != "Earth"  # guard: override is a real change
    md = generate_compat_report(a, b, a.name, b.name, tier="deep", favorable_element_a="Earth")
    # Partner A's cover cell and Day Master snapshot must both show the override.
    assert f"{a.day.combined} | Earth |" in md
    snap_a = md.split(f"#### Day Master Snapshot — {a.name}", 1)[1]
    assert "**Favorable element (용신):** Earth" in snap_a


from types import SimpleNamespace


def _fake_chart(verdict, month_branch, candidate_favorable, candidate_supporting):
    return SimpleNamespace(strength_assessment={
        "verdict": verdict,
        "month_branch": month_branch,
        "candidate_favorable": candidate_favorable,
        "candidate_supporting": candidate_supporting,
    })


def test_climate_no_override_for_temperate_balanced_chart():
    """A balanced chart born in a temperate month keeps the least-represented pick."""
    chart = _fake_chart("balanced", "卯", "Water", "Metal")
    fe = favorable_element(chart)
    assert fe.element == "Water"
    assert fe.supporting == "Metal"
    assert fe.method == "balanced-heuristic"
    assert fe.climate_band == "temperate"
    assert fe.climate_element is None
    assert fe.climate_agrees is None
    assert "no 조후 override applies" in fe.note


def test_climate_governs_for_strong_verdict_when_it_agrees():
    """2026-09-19: 조후 governs the headline for a strong DM in a hot/cold month
    even when it happens to agree with 억부 (docs/research/2026-09-validation-climate.md §5).
    """
    chart = _fake_chart("strong", "巳", "Water", "Metal")  # hot month wants Water too
    fe = favorable_element(chart)
    assert fe.element == "Water"
    assert fe.supporting == "Metal"
    assert fe.method == "climate-balanced"
    assert fe.climate_band == "hot"
    assert fe.climate_element == "Water"
    assert fe.climate_agrees is True
    assert "matches the chart's own least-represented element" in fe.note


def test_climate_governs_over_weak_verdict_when_it_disagrees():
    """2026-09-19: 조후 governs the headline for a weak DM in a hot/cold month
    even when 억부 would have picked a different element (docs/research/2026-09-validation-climate.md §5).
    """
    chart = _fake_chart("weak", "亥", "Earth", "Fire")  # cold month wants Fire
    fe = favorable_element(chart)
    assert fe.element == "Fire"           # 조후 now overrides the weak-DM 억부 pick
    assert fe.supporting == "Wood"        # climate_supporting, not the 억부 convention
    assert fe.method == "climate-balanced"
    assert fe.climate_band == "cold"
    assert fe.climate_element == "Fire"
    assert fe.climate_agrees is False
    assert "climate-balance) check takes priority ahead of 억부" in fe.note


def test_supporting_matches_generator_of_headline_when_climate_wins():
    """Harish-shaped case: supporting element must track the NEW headline, not the old one."""
    chart = _fake_chart("balanced", "巳", "Fire", "Wood")  # old 억부 pick was Fire/Wood
    fe = favorable_element(chart)
    assert fe.element == "Water"
    assert fe.supporting == "Metal"  # Metal generates Water, not Wood (the stale pick)
    assert fe.climate_agrees is False


def test_override_still_reports_a_supporting_element():
    """A reader override must not blank out the Supporting Element line."""
    chart = _fake_chart("balanced", "巳", "Fire", "Wood")
    fe = favorable_element(chart, override="Wood")
    assert fe.element == "Wood"
    assert fe.method == "reader-confirmed"
    assert fe.supporting == "Water"  # Water generates Wood — strict classical default


def test_harish_regression_climate_override_to_water():
    """Named regression closing the loop on the 2026-09-13 investigation.

    Harish's chart (辛 Day Master, born 巳월) reads as balanced under 억부
    (-0.43), so before this change the engine picked Fire (least-represented).
    적천수's 辛金 stanza and 궁통보감's 조후 principle both call for Water in a
    summer-born chart; the climate cross-check must now win the headline.
    """
    chart = compute_chart(
        name="Harish", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
        city="Pallipattu, Tamil Nadu", utc_offset=5.5, use_solar_time=True,
        convention="korean",
    )
    assert chart.strength_assessment["verdict"] == "balanced"
    assert chart.strength_assessment["month_branch"] == "巳"
    fe = favorable_element(chart)
    assert fe.element == "Water"
    assert fe.supporting == "Metal"
    assert fe.method == "climate-balanced"
    assert fe.climate_agrees is False


# ── E-3/E-5 single resolution (2026-09-26) ───────────────────────────────


def _c(y, m):
    from saju_engine.engine import compute_chart
    return compute_chart(name="x", gender="M", year=y, month=m, day=15, hour=12, minute=0,
                         longitude=127.0, utc_offset=9)


def test_full_role_set_resolved_once_for_every_method():
    from saju_engine.yongsin import favorable_element
    cases = {
        "balanced-heuristic": (1980, 3),
        "climate-balanced": (1980, 4),
        "strong-dm-drain": (1980, 9),
        "weak-dm-support": (1983, 3),
    }
    for method, (y, m) in cases.items():
        fe = favorable_element(_c(y, m))
        assert fe.method == method
        assert fe.unfavorable and fe.unfavorable not in (fe.element, fe.supporting)
        assert fe.requires_reader is (method == "balanced-heuristic")
        expected_src = "dm-relative" if method in ("strong-dm-drain", "weak-dm-support") else "derived-from-yongsin"
        assert fe.unfavorable_method == expected_src


def test_harish_gisin_is_fire_and_compat_reads_the_same_value():
    from saju_engine.engine import compute_chart
    from saju_engine.yongsin import favorable_element
    from saju_engine import compat
    chart = compute_chart(name="h", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
                          longitude=79.4408, utc_offset=5.5)
    fe = favorable_element(chart)
    assert (fe.element, fe.unfavorable, fe.gusin, fe.hansin) == ("Water", "Fire", "Earth", "Wood")
    assert compat._resolved_unfavorable(chart) == "Fire"
    # The raw strength field stays None for a balanced chart — nothing reads it now.
    assert chart.strength_assessment.get("candidate_unfavorable") is None


def test_reader_override_rederives_gisin_from_override():
    from saju_engine.yongsin import favorable_element
    fe = favorable_element(_c(1980, 9), override="Fire")
    assert fe.method == "reader-confirmed"
    assert fe.unfavorable == "Metal" and fe.unfavorable_method == "derived-from-yongsin"


def test_balanced_temperate_report_marks_yongsin_provisional():
    from saju_engine.premium_report import generate_premium_report
    report = generate_premium_report(_c(1980, 3), tier="deep")
    line = next(l for l in report.splitlines() if l.startswith("- **Favorable Element:**"))
    assert "provisional — requires reader confirmation" in line
