"""Plan 6 (W6 compat) validation-harness tests.

Fixtures: tests/validation/fixtures/compat.json — 27 entries (17 layer-A at
Task 1, +10 layer-B at Task 2). Layer A: 10 ``band`` probes (the 4-band ladder
with all three boundaries straddled plus 2 out-of-range defensive edges) and 7
``subsystem`` probes on a ``charts="pillars"`` pair built from the *published*
harish x manvitha pillars, asserting the 7 sub-systems that A6 measured as
pillars-only reproducible. Layer B adds 6 ``score`` probes (including the
zero-override B2 anchor, a reversal, and an override-bearing case) plus 4
``charts="birth"`` ``subsystem`` probes, exercising all 11 ``WEIGHT`` keys
across the two chart sources.

Expected values are grounded in knowledge/11-gunghap.md (11 sub-systems A–K,
composite bands, the WEIGHT table) with every value probe-verified 2026-09-14.
The sub-system values carry an external citation: the published deep compat
report, not the engine's own output.

Three assertions in Plan 6 T1 Step 5 cannot be fixtures and live here as direct
module assertions instead, because they are not keys of ``compat.WEIGHT`` and so
are not reachable through the ``subsystem`` probe (whose dispatcher raises on an
unknown name by design):

* the 삼형 / 자형 reachability contract (:func:`test_punishment_pairs_reach_their_step`),
* the WEIGHT reconciliation -- 112 total vs 100 scored (:func:`test_weight_reconciliation`),
* the 육합 regression lock (see the block comment at the foot of this file).
"""
import pytest

from saju_engine.validation import (
    _COMPAT_ALLOWED_PROBE,
    _COMPAT_A_KEYS,
    _COMPAT_BAND_INPUT,
    _COMPAT_B_KEYS,
    _COMPAT_CHART_INPUT,
    _COMPAT_PILLAR_KEYS,
    load_fixtures,
)

ENTRIES = load_fixtures("compat")

# A6's measured set: the sub-systems a pillars-only Chart reproduces to the
# published value. The other four (yongshin, ilju_pair, combined_elements,
# daeun_sync) need the full pipeline or the override channel.
PILLARS_ONLY_REPRODUCIBLE = {
    "daystem_combo", "daybranch", "nayin", "tengod_cross",
    "compat_stars", "yin_yang", "year_branch",
}
PILLARS_ONLY_OUT_OF_SCOPE = {
    "yongshin", "ilju_pair", "combined_elements", "daeun_sync",
}

# (band, the score that must produce it) — the measured ladder.
BAND_LADDER = [("Challenging", 44), ("Mixed", 45), ("Mixed", 64),
               ("Strong", 65), ("Strong", 79), ("Excellent", 80)]


def _band_entries():
    return [e for e in ENTRIES if e["input"]["probe"] == "band"]


def _subsystem_entries():
    return [e for e in ENTRIES if e["input"]["probe"] == "subsystem"]


def _pillars_only_subsystem_entries():
    """The ``subsystem`` probes that read a *pillars-only* chart.

    Scoped by chart source, not merely by probe kind. T1's set is the seven
    sub-systems a pillars-only Chart reproduces (A6); T2 adds four
    ``charts="birth"`` subsystem probes for the complementary four. An
    unfiltered ``probe == "subsystem"`` set would therefore mix two different
    claims -- "what a pillars-only chart reproduces" and "what has been
    pinned" -- and neither assertion would mean what it says.
    """
    return [e for e in _subsystem_entries()
            if e["input"].get("charts") == "pillars"]


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_compat_fixture(entry):
    """Each compat fixture must match engine output.

    Same contract as test_val_climate / test_val_yongsin: a
    documented_interpretation entry that does NOT match marks itself xfail
    (renders INTERPRETATION in the CLI report) instead of failing the suite.
    """
    from saju_engine.validation import run_compat_fixture

    result = run_compat_fixture(entry)
    if result["status"] != "PASS" and entry["status"] == "documented_interpretation":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]


def test_band_coverage_straddles_every_boundary():
    """All four bands must appear, and every ladder boundary must be straddled.

    A fixture set that samples only mid-band scores would pass while never
    proving the >= boundaries are at 45/65/80 rather than, say, 44/64/79 --
    which is the actual content of the band rule.
    """
    band = _band_entries()
    labels = {e["expected"]["band"] for e in band}
    assert labels == {"Excellent", "Strong", "Mixed", "Challenging"}, labels

    scored = {(e["input"]["score"], e["expected"]["band"]) for e in band}
    for label, score in BAND_LADDER:
        assert (score, label) in scored, f"ladder rung {score} -> {label} missing"

    edges = [e for e in band if not 0 <= e["input"]["score"] <= 100]
    assert len(edges) >= 2, f"expected >=2 out-of-range defensive probes, got {edges}"


def test_subsystem_fixtures_cover_exactly_the_pillars_only_set():
    """The subsystem probes must be exactly A6's pillars-only reproducible set.

    Asserting more than seven would mean asserting a sub-system that reads the
    full pipeline from a pillars-only chart -- a fixture that could only pass by
    accident. Asserting fewer would leave a reproducible sub-system unpinned.
    """
    got = {e["input"]["subsystem"] for e in _pillars_only_subsystem_entries()}
    assert got == PILLARS_ONLY_REPRODUCIBLE, (
        f"missing: {sorted(PILLARS_ONLY_REPRODUCIBLE - got)}; "
        f"unexpected: {sorted(got - PILLARS_ONLY_REPRODUCIBLE)}"
    )


def test_subsystem_fixtures_declare_their_out_of_scope_set():
    """Every pillars-only fixture must name the four sub-systems it cannot assert.

    This is the A6/A7 disclosure requirement: without it a reader cannot tell
    whether a 7-of-11 fixture set means "these seven are equivalent" or "the
    other four measured differently".
    """
    for e in _pillars_only_subsystem_entries():
        notes = e.get("notes", "")
        for name in PILLARS_ONLY_OUT_OF_SCOPE:
            assert name in notes, f"{e['id']}: notes must declare {name!r} out of scope"


def test_compat_probe_input_guarded():
    """The compat probe input sets must be well-formed and correctly nested."""
    assert _COMPAT_ALLOWED_PROBE == {"band", "subsystem", "score"}
    # The band probe is chart-free -- that is what lets it run without a Chart.
    assert _COMPAT_BAND_INPUT == {"probe", "score"}
    assert not (_COMPAT_BAND_INPUT & _COMPAT_CHART_INPUT), (
        "band must stay chart-free, or its exact-key guard is unreachable"
    )
    # Pillars keys are a strict subset of the chart input, and never collide
    # with the birth keys (a collision would make the two channels ambiguous).
    assert _COMPAT_PILLAR_KEYS < _COMPAT_CHART_INPUT
    assert not (_COMPAT_PILLAR_KEYS & (_COMPAT_A_KEYS | _COMPAT_B_KEYS))


# ---------------------------------------------------------------------------
# Module invariants -- reachable only directly, not through a `subsystem` probe.
# ---------------------------------------------------------------------------

def test_weight_reconciliation():
    """WEIGHT sums to 112, but the scored subset sums to exactly 100.

    combined_elements is carried in the table for reporting yet excluded from
    the composite sum, so the 112/100 gap is a documented reconciliation and
    not a defect. Pinning both numbers means a future weight edit cannot
    silently break the 0-100 composite scale.
    """
    from saju_engine import compat

    total = sum(compat.WEIGHT.values())
    scored = sum(v for k, v in compat.WEIGHT.items() if k != "combined_elements")
    assert total == 112, f"WEIGHT total moved: {total}"
    assert scored == 100, f"scored subset must stay 0-100 normalizable, got {scored}"
    assert total - scored == compat.WEIGHT["combined_elements"]


def test_punishment_pairs_reach_their_step():
    """Only pairs that survive the earlier relation steps may reach 형.

    ``_cross_branch_score`` checks 육합 -> 육충 -> 육해 -> 육파 -> 형 -> 반합, so
    the 형 step is reachable for a pair only when no earlier step claims it.
    Within the 三刑 frames that leaves exactly 子卯 and 丑戌; the rest of the
    寅巳申 and 丑戌未 frames are shadowed by 합/해/파/충. The 四自刑 branches are
    carried by the same step. Pinning the reachable set keeps a future
    reordering of that chain from silently re-scoring the family.

    The 巳申 row is the load-bearing one: it is simultaneously a 六合 pair and a
    六破 pair, so which step claims it is a direct read-out of the chain order
    and not of the relation tables. Since the 육합 arity repair (2026-09-14) it
    reports 육합, because 육합 is checked first (:310) and the chain was left
    untouched. If a future change reorders the chain, this row moves before
    anything else does.
    """
    from saju_engine import compat

    # 三刑 frames minus the pairs an earlier step claims.
    assert compat._cross_branch_score("子", "卯") == (-2, "삼형 子卯")
    assert compat._cross_branch_score("丑", "戌") == (-2, "삼형 丑戌")
    # Shadowed members of the frames -- each claimed by an earlier step.
    assert compat._cross_branch_score("寅", "巳")[1].startswith("육해")
    assert compat._cross_branch_score("巳", "申")[1].startswith("육합")
    assert compat._cross_branch_score("寅", "申")[1].startswith("육충")
    assert compat._cross_branch_score("丑", "未")[1].startswith("육충")
    assert compat._cross_branch_score("戌", "未")[1].startswith("육파")
    # 自刑 is carried by the 형 step, at the same -2.
    for branch in ("辰", "午", "酉", "亥"):
        assert compat._cross_branch_score(branch, branch) == (-2, f"자형 {branch}{branch}")


# ---------------------------------------------------------------------------
# T2 -- the `score` probe kind, and corpus-wide structural coverage.
# ---------------------------------------------------------------------------

B2_ANCHOR_ID = "compat-harish-manvitha"


def test_compat_score_full_pair_reproduces_published_exactly():
    """B2 -- the certification centrepiece: all 11 sub-systems byte-identical.

    Asserted against the corpus entry rather than the plan's Step 1 literal.
    That literal carries 21 of the 24 ``a_*``/``b_*`` keys, so
    ``run_compat_fixture``'s missing-key guard raises on it; the corpus entry is
    the same claim stated in the shape the harness accepts.

    Three properties are pinned beyond what the parametrized runner proves:

    * the probe kind -- without this the anchor could be satisfied by a
      ``subsystem`` probe and the composite/band comparison would go untested;
    * FULL/FULL provenance -- both charts born, not reconstructed, so the
      published 70/Strong is being reproduced and not merely re-derived;
    * zero reader overrides. An override is not cosmetic: it moves
      ``yongshin``, ``ilju_pair`` *and* ``combined_elements`` (measured
      H x M: Earth 9 -> 11, Fire 9 -> 7), so a 70/Strong carrying all eleven
      published rows is only meaningful as a no-override measurement. The
      override channel has its own fixture.
    """
    from saju_engine import compat

    entry = next(e for e in ENTRIES if e["id"] == B2_ANCHOR_ID)
    assert entry["input"]["probe"] == "score"
    assert entry["input"]["charts"] == "birth", "the anchor must be FULL/FULL"
    assert not ({"favorable_element_a", "favorable_element_b"} & set(entry["input"])), (
        "the B2 anchor must be a zero-override measurement"
    )
    assert set(entry["expected"]["subsystems"]) == set(compat.WEIGHT), (
        "the anchor must assert every WEIGHT key -- a partial map could pass "
        "while a sub-system silently drifts"
    )

    from saju_engine.validation import run_compat_fixture

    result = run_compat_fixture(entry)
    assert result["status"] == "PASS", result["detail"]


def test_compat_coverage_pins_all_probe_kinds_and_all_11_subsystems():
    """The corpus must exercise every probe kind and every sub-system.

    Three separate coverage claims, none implied by the others:

    * all three probe kinds appear -- a corpus of only ``band`` probes would
      leave the composite and the sub-system dispatch entirely unpinned;
    * all eleven ``WEIGHT`` keys are covered by ``subsystem`` probes. They are
      covered across *two* chart sources (seven pillars-only, four birth),
      because four of the eleven are not pillars-only reproducible;
    * both chart sources are actually exercised, so neither channel can rot
      unnoticed while the other keeps the suite green.
    """
    from saju_engine import compat

    entries = load_fixtures("compat")
    probes = {e["input"].get("probe") for e in entries}
    assert probes == {"band", "subsystem", "score"}, probes

    covered = {e["input"]["subsystem"] for e in entries
               if e["input"].get("probe") == "subsystem"}
    assert covered == set(compat.WEIGHT), (
        f"missing: {sorted(set(compat.WEIGHT) - covered)}; "
        f"unexpected: {sorted(covered - set(compat.WEIGHT))}"
    )

    charts = {e["input"].get("charts") for e in entries if "charts" in e["input"]}
    assert charts == {"birth", "pillars"}, charts


# ---------------------------------------------------------------------------
# Known-bug regression lock (Plan 6 T1) -- FIXED 2026-09-14.
#
# The finding (not in the spec's Known Open Bugs list, which carries exactly 3
# items): `lookup.SIX_COMBINATIONS` is declared `List[Tuple[str, str, str]]` --
# each row carries the resulting element, e.g. ('子', '丑', 'Earth'). The helper
# `compat._branch_pair_lookup` tested 2-tuple membership:
#
#     return (b1, b2) in table or (b2, b1) in table
#
# so `(b1, b2) in SIX_COMBINATIONS` was False for EVERY pair and the 육합 branch
# was unreachable dead code at all four call sites:
#
#   compat.py:310  _cross_branch_score   -- 육합 intended +4, never fired.
#                                         Four of six 六合 pairs scored 0
#                                         ("no relation"); 寅亥 and 巳申 fell
#                                         through to 육파 -1.
#   compat.py:407  compat_daybranch      -- the PRIMARY spouse-palace 육합
#                                         intended +20 and the engine's own
#                                         narrative calls it "the strongest
#                                         favorable indicator in classical
#                                         궁합"; instead the pair was reported as
#                                         having "no direct 합/충", which is a
#                                         false statement in a paid deliverable.
#   compat.py:1343 compat_year_branch    -- 띠 육합 intended +3, never fired.
#
#   compat.py:428  compat_daybranch 반합 suppression -- `not _branch_pair_lookup(..)`
#                                         was always True, so the guard was
#                                         vacuous. LATENT ONLY: no 六合 pair
#                                         shares a 삼합 frame, so it can never
#                                         change a result even now that the root
#                                         cause is fixed. Still true post-fix.
#
# The other three relation tables (SIX_CLASHES / SIX_HARMS / SIX_BREAKS) are
# 2-tuples and work correctly, so the defect was specific to the 3-tuple table
# and the fix is one bounded line inside `_branch_pair_lookup`: match the first
# two columns of each row instead of the whole row.
#
# LANDED: the fix is in `compat._branch_pair_lookup` (table re-typed
# `Sequence[Tuple[str, ...]]`, body `any(tuple(row[:2]) in ((b1,b2),(b2,b1)) ...)`).
# The chain ORDER was deliberately NOT touched -- see the C9 note in
# knowledge/11-gunghap.md §B4 and `test_three_punishment_shadowed_by_priority`
# in tests/test_compat.py, which is carried as C-none.
#
# The three locks below XPASSed on the fix -- the delete-the-marker signal the
# campaign specified -- so their xfail markers are retired and they now stand as
# positive behaviour guards. L3 additionally had to be REPAIRED rather than
# merely un-marked: `_pillars_chart` used to hardcode the year pillar as 甲子
# for BOTH charts, so the 띠 sub-system compared 子 with 子 and could never reach
# a 육합. It was permanently unsatisfiable, which is why it never XPASSed under
# any candidate fix. `_pillars_chart` now takes a `year_branch`.
# ---------------------------------------------------------------------------


def _pillars_chart(day_stem, day_branch, name, year_branch="子"):
    """A pillars-only chart -- enough to drive the day-branch and year sub-systems.

    `year_branch` defaults to 子 so the day-branch callers are unaffected; the
    띠/육합 guard needs the two charts' YEAR branches to differ, which the
    previously-hardcoded 甲子 pillar made impossible.
    """
    from saju_engine.chart import Chart, Pillar

    c = Chart()
    for pos, stem, branch in [("year", "甲", year_branch), ("month", "乙", "丑"),
                             ("day", day_stem, day_branch), ("hour", "丙", "寅")]:
        setattr(c, pos, Pillar(position=pos, stem=stem, branch=branch))
    c.day_master = day_stem
    c.day_master_info = {}
    c.name = name
    return c


# ── Guards: PASS today, and stay passing after a sanctioned fix ──────────────

def test_guard_other_relation_tables_are_two_tuples():
    """Guard 1 -- the defect was specific to the 3-tuple table.

    SIX_COMBINATIONS is the only relation table carrying an element, which is
    why the original defect was bounded to 육합 and the fix could be one line
    inside the helper instead of new logic at four call sites. The shape
    asymmetry is the fact this guard protects: if a future edit flattens the
    tables to a uniform arity, the 육합 element column has been dropped and the
    六合 label loses the element it reports.
    """
    from saju_engine import lookup as L

    arities = {len(row) for row in L.SIX_COMBINATIONS}
    assert arities == {3}, f"SIX_COMBINATIONS shape moved: arities={arities}"
    for name in ("SIX_CLASHES", "SIX_HARMS", "SIX_BREAKS"):
        table = getattr(L, name)
        assert {len(row) for row in table} == {2}, f"{name} shape moved"


def test_guard_two_tuple_tables_do_fire():
    """Guard 2 -- 충/해/파 are reachable, and were even while 합 was dead.

    These three pairs are not 六合, so the arity repair could not touch them.
    That is what made the original diagnosis locatable: the defect was in the
    helper's shape assumption, not in the relation tables, and three of the
    four tables worked the whole time. Kept as the standing proof that the
    tables themselves are intact, so a future 육합 regression cannot be
    mistaken for table damage.
    """
    from saju_engine import compat

    assert compat._cross_branch_score("子", "午") == (-5, "육충 子午")
    assert compat._cross_branch_score("子", "未") == (-1, "육해 子未")
    assert compat._cross_branch_score("子", "酉") == (-1, "육파 子酉")


def test_guard_lookup_is_shape_tolerant_for_six_combinations():
    """Guard 3 -- the shape-tolerance contract, asserted directly.

    Before the 2026-09-14 fix this guard asserted the *inverse* premise: that
    `_branch_pair_lookup` was False for all six 六合 pairs. It failed the moment
    the helper gained 3-tuple tolerance, exactly as its own message predicted
    ("delete the xfail markers below"), and the locks below XPASSed.

    It is INVERTED rather than deleted, so the contract stays asserted rather
    than merely inferred from the locks: matching the branch columns is what
    makes the helper work across tables of different arity, and if someone
    later "simplifies" it back to whole-row membership this guard fails here
    first, pointing at the cause instead of at four downstream symptoms.

    The helper is called with the table explicitly, so this asserts the helper
    itself and not the four call sites.
    """
    from saju_engine import compat, lookup as L

    for pair in L.SIX_COMBINATIONS:
        b1, b2 = pair[0], pair[1]
        assert compat._branch_pair_lookup(b1, b2, L.SIX_COMBINATIONS) is True, (
            f"({b1},{b2}) failed to match -- _branch_pair_lookup lost its "
            "shape tolerance and the 육합 branch is dead again"
        )
        # Reversed order too: the helper is documented as order-insensitive.
        assert compat._branch_pair_lookup(b2, b1, L.SIX_COMBINATIONS) is True


# ── Behaviour guards: the 육합 locks retired to positive assertions ──────────

def test_cross_branch_score_recognizes_six_combinations():
    """L1 -- every 六合 pair scores +4 through the cross-pair helper."""
    from saju_engine import compat, lookup as L

    for b1, b2, element in L.SIX_COMBINATIONS:
        got = compat._cross_branch_score(b1, b2)
        assert got == (4, f"육합 {b1}{b2}"), (
            f"{b1}{b2} ({element}) is a 六合 pair but scored {got!r}"
        )


def test_daybranch_primary_recognizes_spouse_palace_six_combination():
    """L2 -- 子丑 spouse palaces must take the +20 primary 육합 path.

    The narrative is asserted too: before the fix the engine stated these two
    palaces "have no direct 합/충", which is false and reached the client.
    """
    from saju_engine import compat

    a = _pillars_chart("甲", "子", "a")
    b = _pillars_chart("乙", "丑", "b")
    result = compat.compat_daybranch(a, b)
    assert result.score == 20, f"子丑 육합 spouse palaces scored {result.score}, not +20"
    assert any("육합" in f for f in result.flags), result.flags
    assert "no direct" not in result.narrative, result.narrative[-160:]


def test_year_branch_recognizes_zodiac_six_combination():
    """L3 -- 子丑 year branches must take the capped +3 띠 육합 path.

    `_pillars_chart` is called with the two charts' YEAR branches differing
    (子 vs 丑). It used to hardcode 甲子 for both, so this lock compared 子
    with 子 and was permanently unsatisfiable -- it did not XPASS under the
    fix either, and had to be repaired rather than merely un-marked.
    """
    from saju_engine import compat

    a = _pillars_chart("甲", "子", "a", year_branch="子")
    b = _pillars_chart("乙", "丑", "b", year_branch="丑")
    result = compat.compat_year_branch(a, b)
    assert result.score == 3, f"子丑 띠 육합 scored {result.score}, not +3"
    assert any("육합" in f for f in result.flags), result.flags
