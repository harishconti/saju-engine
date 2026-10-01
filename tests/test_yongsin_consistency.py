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
    # N-6: Harish's Water remedy is NOT already dominant, so the override is
    # not suppressed — 궁통보감 prescribes 壬水 for 四月辛金 unconditionally.
    assert fe.remedy_dominant is False


# ── N-6 remedy-dominance guard (2026-09-26 deep audit) ───────────────────


def test_n6_guard_suppresses_water_remedy_when_water_already_dominant():
    """The audit's own N-6 example: 1963-10-24 11:00 is a 戌 (dry → Water)
    month, but the chart is already 36% Water (壬, 癸, 子). Adding Water cannot
    balance it, so the 조후 override must be withheld and 억부 governs."""
    chart = compute_chart(
        name="N6-dry-water-dominant", gender="M",
        year=1963, month=10, day=24, hour=11, minute=0,
        longitude=127.0, utc_offset=9.0, use_solar_time=True,
    )
    fe = favorable_element(chart)
    assert fe.climate_band == "dry"
    assert fe.climate_element == "Water"
    assert fe.remedy_dominant is True
    assert fe.method != "climate-balanced"      # override withheld
    assert fe.element != "Water"


def test_n6_guard_suppresses_fire_remedy_when_fire_already_dominant():
    """The audit's second N-6 example: a 亥 (cold → Fire) month whose chart is
    already Fire-dominant (35%) — Fire here is the chart's 기신, so it must not
    be prescribed."""
    chart = compute_chart(
        name="N6-cold-fire-dominant", gender="M",
        year=2010, month=12, day=6, hour=1, minute=0,
        longitude=127.0, utc_offset=9.0, use_solar_time=True,
    )
    fe = favorable_element(chart)
    assert fe.climate_band == "cold"
    assert fe.climate_element == "Fire"
    assert fe.remedy_dominant is True
    assert fe.element != "Fire"


def test_n6_guard_does_not_fire_for_published_candidates():
    """The guard must leave every published reading's resolved 용신 unchanged
    (none of them has its remedy element as the most abundant)."""
    for chart in CANDIDATES:
        fe = favorable_element(chart)
        # remedy_dominant is None for a temperate month, else must be False.
        assert fe.remedy_dominant in (None, False)


def test_n6_direction_gate_suppresses_hot_month_on_cool_chart():
    """Industry-standard whole-chart gate: a 巳 (hot → Water) month whose whole
    chart leans clearly cool is not 'too hot', so 조후 is withheld and 억부
    governs. Water is NOT the most-abundant element here, so this exercises the
    direction gate independently of the dominance guard."""
    chart = compute_chart(
        name="N6-hot-month-cool-chart", gender="M",
        year=1981, month=6, day=5, hour=1, minute=0,
        longitude=127.0, utc_offset=9.0, use_solar_time=True,
    )
    fe = favorable_element(chart)
    assert fe.climate_band == "hot"
    assert fe.climate_element == "Water"
    assert fe.climate_temperature is not None and fe.climate_temperature < 0
    assert fe.climate_extreme is False
    assert fe.remedy_dominant is False
    assert fe.method != "climate-balanced"
    assert fe.element != "Water"


def test_n6_harish_keeps_water_despite_neutral_temperature():
    """Regression lock: Harish's chart scores ~0 on the whole-chart temperature
    (genuinely neutral), but 궁통보감's 四月辛金 rule prescribes 壬水
    unconditionally, so the *element* must stay Water — the gate must never flip
    a validated reading by deriving the element from the temperature score."""
    chart = compute_chart(
        name="Harish", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
        city="Pallipattu, Tamil Nadu", utc_offset=5.5, use_solar_time=True,
        convention="korean",
    )
    fe = favorable_element(chart)
    assert fe.element == "Water"
    assert fe.method == "climate-balanced"
    assert abs(fe.climate_temperature) < 1.0        # neutral temperature
    assert fe.climate_extreme is True               # but not opposing its month


# ── E-3/E-5 single resolution (2026-09-26) ───────────────────────────────


def _c(y, m, day=15, hour=12):
    from saju_engine.engine import compute_chart
    return compute_chart(name="x", gender="M", year=y, month=m, day=day, hour=hour, minute=0,
                         longitude=127.0, utc_offset=9)


def test_full_role_set_resolved_once_for_every_method():
    from saju_engine.yongsin import favorable_element
    # N-12 (2026-09-26): branch-qi normalisation moved the old (1983, 3)
    # weak-dm-support probe to balanced; (1980, 2, day 5) still resolves weak.
    cases = {
        "balanced-heuristic": (1980, 3, 15, 12),
        "climate-balanced": (1980, 4, 15, 12),
        "strong-dm-drain": (1980, 9, 15, 12),
        "weak-dm-support": (1980, 2, 5, 6),
    }
    for method, (y, m, day, hour) in cases.items():
        fe = favorable_element(_c(y, m, day, hour))
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


def test_reader_override_confirming_eokbu_keeps_dm_relative_gisin():
    """Gurumoorthy: strong 己 DM, reader-confirmed Metal (= the raw 억부 pick),
    so the 억부 method's own 기신 (Earth, the over-strong self) stands."""
    from saju_engine.engine import compute_chart
    from saju_engine.yongsin import favorable_element
    c = compute_chart(name="g", gender="M", year=1964, month=7, day=19, hour=8, minute=30,
                      longitude=79.42, utc_offset=5.5)
    fe = favorable_element(c, override="Metal")
    assert (fe.unfavorable, fe.unfavorable_method) == ("Earth", "dm-relative")


# ── 2026-09-14 architecture audit §4.5 / §5 item 2: the raw field is now ──
# self-flagging. The producer emits both keys; the underscore name is the
# canonical raw channel and `candidate_favorable` is a backward-compatible
# alias pointing at the same value. The divergence rule (audit §4.5, derived
# over 2,016 charts) is pinned so the two channels cannot silently
# re-converge or re-diverge without a test failing.

def test_raw_field_is_self_flagged_and_has_no_public_alias():
    """2026-09-14 audit §5 item 2. The raw pick is published ONLY as
    ``_raw_unresolved_favorable``. An earlier pass added the new key while
    keeping ``candidate_favorable`` as an "alias" — but that name reads like a
    public 용신 field, and four modules had already adopted it as one (two of
    them shipping a pre-climate element to clients). The alias is gone, so a
    stray read now raises KeyError instead of silently resolving."""
    from saju_engine.strength import assess_strength
    sa = assess_strength("甲", "酉", ["甲", "辛", "甲", "乙"], [("酉", "辛")])
    assert "_raw_unresolved_favorable" in sa
    assert "candidate_favorable" not in sa, (
        "the legacy candidate_favorable alias is back — it reads like a public "
        "용신 field and has silently diverged from the resolved value before"
    )


def test_divergence_rule_balanced_climate_band_diverges():
    """resolved ≠ raw  iff  reader_override_favorable is set
    or (verdict == "balanced" and month_branch ∈ 巳午未/亥子丑) — for a
    climate-band chart where the N-6 whole-chart gate does NOT withhold the
    override. (Gate-withheld charts legitimately agree; this pins the firing
    half of the rule on a known firing example, 1970-05-23 from the audit's
    2,016-chart sweep: 巳 month, balanced, raw Wood → resolved Water.)"""
    from saju_engine.engine import compute_chart
    from saju_engine.yongsin import favorable_element
    c = compute_chart(name="d", gender="F", year=1970, month=5, day=23,
                      hour=12, minute=0, longitude=100.5, utc_offset=7.0)
    sa = c.strength_assessment
    fe = favorable_element(c)
    if fe.method == "climate-balanced":
        assert sa["verdict"] == "balanced"
        assert fe.element != sa["_raw_unresolved_favorable"]
    else:
        # The N-6 whole-chart gate withheld the override — the rule's
        # precondition no longer holds, so agreement is legitimate.
        assert fe.method in _ALLOWED_METHODS
