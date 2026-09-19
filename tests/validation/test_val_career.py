"""Plan 6 (W6 career) validation-harness tests.

Fixtures: tests/validation/fixtures/career.json — 32 entries. Two probe kinds:

* ``domain_map`` (30 rows, chart-free) — pins ``report_data._domain_element(domain)``,
  the element → industry-family mapping against knowledge/12-career-and-vocation.md
  "Element to Industry Families". 25 rows are ``expect_match`` (engine element == the
  KB12 family the domain belongs to); 5 are ``documented_interpretation`` where the
  engine's keyword router mis-maps the domain (expected carries the *engine's* value
  plus a root-cause note — a keyword-coverage gap, never a doctrine conflict).
* ``tiers`` (2 rows, chart-based) — pins ``report_data._career_tiers(chart)`` as an
  ordered (tier, domain) list for harish and manvitha, plus whether the
  ``**Possible**`` tier is reachable. Both measure a pool keyed on the chart's *need*
  — the resolved 용신's family followed by the 희신's family, 12 candidates from 2
  families on each chart — which is what KB12:130-152 requires (align work with the
  chart's 용신, not the Day Master's own element). Until 2026-09-14 the pool was keyed
  on the Day Master's own family instead, which contradicted that priority and left
  the ``i < 7`` **Possible** band code-reachable but output-unreachable (W6 coverage
  gap 1); the fixtures documented the contradiction in their notes rather than
  asserting the doctrine, and they now assert it as fixed.

Expected values are grounded in knowledge/12-career-and-vocation.md with every value
probe-verified 2026-09-14 (harish 1992-06-04 03:10 lon 79.42; manvitha 1996-12-03
21:15 lon 78.8242). The five mis-map rows carry an external citation (the KB12 family
list) in addition to the engine's own output.
"""
import pytest

from saju_engine.validation import (
    _ALLOWED_INPUT,
    _CAREER_ALLOWED_PROBE,
    _CAREER_MAP_INPUT,
    _CAREER_TIER_INPUT,
    load_fixtures,
)

ENTRIES = load_fixtures("career")

# The five domains a keyword-coverage router mis-maps: engine value vs KB12 family.
# These are the *names* -- the fixture rows pin the engine's value under
# documented_interpretation so a future router fix turns them into a FAIL the moment
# the engine's output moves off the pinned value.
KNOWN_MIS_MAPS = {
    "People Development & Culture": ("Wood", None, "keyword-coverage gap"),
    "Public Affairs & Advocacy": ("Fire", None, "keyword-coverage gap"),
    "Mediation & Counselling": ("Earth", "Fire", "substring 'media' wins before earth"),
    "Finance & Investment": ("Metal", "Earth", "earth 'finance' checked before metal 'investment'"),
    "Psychology & Counseling": ("Water", "Earth", "earth 'counseling' (US) wins before water"),
}


def _domain_map_entries():
    return [e for e in ENTRIES if e["input"]["probe"] == "domain_map"]


def _tiers_entries():
    return [e for e in ENTRIES if e["input"]["probe"] == "tiers"]


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_career_fixture(entry):
    """Each career fixture must match engine output.

    Same contract as test_val_compat: a documented_interpretation entry that does NOT
    match marks itself xfail (renders INTERPRETATION in the CLI report) instead of
    failing the suite.
    """
    from saju_engine.validation import run_career_fixture

    result = run_career_fixture(entry)
    if result["status"] != "PASS" and entry["status"] == "documented_interpretation":
        pytest.xfail(f"documented interpretation — {result['detail']}")
    assert result["status"] == "PASS", result["detail"]


# ---------------------------------------------------------------------------
# Corpus structure -- the fixture set must be exhaustive, not incidental.
# ---------------------------------------------------------------------------

def test_career_corpus_exercises_both_probe_kinds():
    """Both probe kinds must appear, and nothing else.

    A corpus of only domain-map rows would leave the chart-based tier pipeline (pool
    selection, scoring, tier cutoffs) entirely unpinned; a corpus of only tiers rows
    would leave the element→domain router unpinned. Either omission would be a silent
    coverage regression.
    """
    probes = {e["input"]["probe"] for e in ENTRIES}
    assert probes == {"domain_map", "tiers"}, probes


def test_domain_map_covers_exactly_all_30_kb12_domains():
    """Every one of the 30 domains in the engine's pools is pinned, no extras.

    The domain set must be EXACTLY the 30 domains the engine selects from. Pinning
    fewer would leave a domain's mapping unobserved; pinning a domain the engine does
    not serve would be dead weight that can only rot.
    """
    got = {e["input"]["domain"] for e in _domain_map_entries()}
    assert len(got) == 30, f"expected 30 distinct domains, got {len(got)}"
    assert len(_domain_map_entries()) == 30, "domain_map rows must be one per domain, no dupes"
    assert got == {d for groups in _domain_pools().values() for d, _ in groups}, (
        "domain_map domains must equal the engine's served pool domain set, exactly"
    )


def _domain_pools():
    from saju_engine import report_data

    return report_data._CAREER_DOMAINS


def test_pool_structure_invariant():
    """The reference table is 5 elements × exactly 6 domains.

    ``_CAREER_DOMAINS`` is the element→industry-family reference that KB12:25-49
    names as the lookup the 용신 should be mapped through, so its 5×6 shape is an
    invariant in its own right: 30 domains, one per KB12 family slot, with no
    element short a family. What it is *not* is the size of the candidate pool
    ``_career_tiers`` ranks -- since 2026-09-14 that pool is the union of the
    resolved 용신 family and the 희신 family (up to 12 candidates), so the ``i < 7``
    **Possible** band is live and both tiers fixtures pin it as reached. This test
    keeps the reference table honest; the tiers fixtures keep the ranking honest.
    """
    pools = _domain_pools()
    assert set(pools) == {"Wood", "Fire", "Earth", "Metal", "Water"}, pools
    for element, pool in pools.items():
        assert len(pool) == 6, f"{element} pool has {len(pool)} domains, expected 6: {pool}"


def test_documented_interpretation_rows_are_exactly_the_known_mis_maps():
    """The 5 documented_interpretation rows are exactly the known mis-map set.

    Asserting exactly five (one per engine-vs-KB12 divergence) prevents two failure
    modes: a fourth/fifth/sixth divergence silently added as a pass-through row, or a
    mis-map "fixed" in the engine while its divergent fixture row is deleted rather
    than promoted to expect_match. Each named domain + its expected engine value is
    pinned against KNOWN_MIS_MAPS so the fixture and this test cannot drift apart.
    """
    di = {e["input"]["domain"]: e for e in _domain_map_entries()
          if e["status"] == "documented_interpretation"}
    assert set(di) == set(KNOWN_MIS_MAPS), (
        f"missing: {sorted(set(KNOWN_MIS_MAPS) - set(di))}; "
        f"unexpected: {sorted(set(di) - set(KNOWN_MIS_MAPS))}"
    )
    for domain, e in di.items():
        _, engine_value, _ = KNOWN_MIS_MAPS[domain]
        assert e["expected"]["element"] == engine_value, (
            f"{domain}: fixture pins engine value {e['expected']['element']!r} but the "
            f"known mis-map says {engine_value!r}"
        )


def test_documented_interpretation_rows_declare_root_cause_in_notes():
    """Every mis-map row must carry a root-cause note, and name the KB12 family.

    The notes are the reader's only way to tell "engine diverges from doctrine" from
    "test author does not know the doctrine". A blank note would make the row
    indistinguishable from an expect_match with the engine value hand-copied in.
    """
    for e in _domain_map_entries():
        if e["status"] != "documented_interpretation":
            continue
        assert "KB12" in e.get("notes", ""), f"{e['id']}: notes must name KB12"
        assert "root cause" in e["notes"].lower() or "mis-map" in e["notes"].lower(), (
            f"{e['id']}: notes must declare the root cause"
        )


def test_tiers_entries_pin_possible_reachable_on_both_charts():
    """Both tiers fixtures assert possible_tier_reachable True, explicitly, and pin 12 rows.

    This is a *positive* pin and deliberately so. Before the 2026-09-14 need-keyed
    pool fix the candidate list was one family of 6, so ``i >= 7`` could never fire
    and the **Possible** tier existed in the code but in no output -- the campaign
    recorded that as W6 coverage gap 1 ("no fixture can exercise a chart that reaches
    it, so if the pool ever widens nothing would notice"). Both charts now serve 12
    candidates from 2 families and reach the band. A True value is only a real
    assertion because the checker tests ``if exp_possible is not None``; pinning 12
    rows rather than 6 is what would catch a pool that silently narrowed back to a
    single family (the row count would drop while a truthy flag still passed).
    """
    tiers = _tiers_entries()
    assert len(tiers) == 2, f"expected exactly 2 tiers entries, got {len(tiers)}"
    for e in tiers:
        assert e["expected"]["possible_tier_reachable"] is True, e["id"]
        assert len(e["expected"]["tiers"]) == 12, (
            f"{e['id']} must pin all 12 candidate rows (a partial list could pass "
            f"while a tier silently drops)"
        )
        assert any(t["tier"] == "**Possible**" for t in e["expected"]["tiers"]), (
            f"{e['id']} claims possible_tier_reachable but pins no Possible row"
        )


# ---------------------------------------------------------------------------
# Input guards -- the probe contract, mirrored from the checker's own guards.
# ---------------------------------------------------------------------------

def test_career_probe_input_guarded():
    """The career probe input sets must be well-formed and correctly nested."""
    assert _CAREER_ALLOWED_PROBE == {"domain_map", "tiers"}
    # domain_map is chart-free -- an exact-key set; any extra key is a hard error.
    assert _CAREER_MAP_INPUT == {"probe", "domain"}
    # tiers is chart-based -- input keys a SUBSET of what compute_chart accepts, plus
    # the probe discriminator. A domain_map row can never satisfy this (its "domain"
    # key is not in _ALLOWED_INPUT), so the two channels are unambiguous.
    assert _CAREER_TIER_INPUT == _ALLOWED_INPUT | {"probe"}
    assert _CAREER_MAP_INPUT & _CAREER_TIER_INPUT == {"probe"}, (
        "domain_map and tiers must share only the probe discriminator"
    )
