"""Tests for ``saju_engine.report_data`` — career domain / tier builders.

Created by Plan 6 (W6 career) Task 3, Step 6 of the 2026-09 engine-validation
campaign as the **stale-field bug-lock** for ``report_data._career_why`` and
``report_data._career_tiers``. The lock has since been RETIRED — the defect is
fixed (2026-09-14) and this file now pins the fixed behaviour instead.

THE DEFECT (spec §Known Open Bug 1, second live instance)
---------------------------------------------------------
``premium_report.py`` was the first instance: it reads the RAW
``strength_assessment["candidate_favorable"]`` instead of the element that
``yongsin.favorable_element()`` actually resolves for the chart.
``report_data.py`` repeats the same read at two call sites::

    _career_why:    favorable = (chart.strength_assessment or {}).get("candidate_favorable")
    _career_tiers:  favorable   = (chart.strength_assessment or {}).get("candidate_favorable")
                    unfavorable = (chart.strength_assessment or {}).get("candidate_unfavorable")

Both values are used for *display* — the "why this fits" line on every career
row — so the client-facing career prose can name an element the engine does not
actually resolve. Measured live, 2026-09-14
(probe transcript: /tmp/sdd-val6/probe-3.out.txt):

    harish — raw ``candidate_favorable == "Fire"``, resolved == **Water**
    (``method="climate-balanced"``, no reader override).

``_career_why(harish, "Strategy & Consulting")`` therefore takes the
*supportive-role* branch and emits:

    "Uses Water energy in a supportive role to your Metal Day Master."

where the resolved element would take the *aligned* branch:

    "Aligns with your favorable element Water, reducing friction."

FIXED, 2026-09-14 (the lock's delete-the-marker signal fired)
------------------------------------------------------------
The engine change is confined to ``report_data.py``: a new
``_resolved_favorable(chart)`` helper reads ``yongsin.favorable_element()`` and
returns the element name (empty string when the resolver cannot name one), and
both call sites now read it instead of the raw field. ``_career_tiers`` also
changed *what it ranks*: the candidate pool is now the resolved 용신's family
followed by the 희신's family (``_CAREER_DOMAINS`` itself is unchanged — it is
the reference table KB12:25-49 names as the lookup, and
``test_knowledge_grounding`` plus ``test_domain_map_covers_exactly_all_30_kb12_domains``
both pin its 30 domains). That second change is what the KB12:130-152 priority
actually requires, and it is why the tier side of the defect is pinned at
fixture level (tests/validation/fixtures/career.json, probe ``tiers``) rather
than locked a second time here — the fixture pins the whole ordered 12-row list,
a strictly stronger statement than any field-level assertion.

One asymmetry is deliberate and worth recording: ``favorable`` now comes from
the resolve channel, but ``unfavorable`` must stay on the raw
``candidate_unfavorable`` channel, because ``FavorableElement`` publishes no
unfavorable element at all. It is latent for both tier fixtures (harish's raw
unfavorable is ``None``; manvitha's is ``"Wood"``, and no Wood-family domain is
in her candidate pool), so nothing is measured wrong by it today — but a
display-channel unfavorable resolver would have to be added to ``yongsin.py``
before that branch could be called consistent.

NOTE ON THE SECOND CHART (measured pre-fix, deliberately NOT locked)
--------------------------------------------------------------------
The same ``report_data`` defect reproduced on sruthi (1993-12-11 02:45, lon
79.42) through the chart-level override channel that ``compat.py:1344-1355``
uses — pre-fix measurement::

    c.strength_assessment["reader_override_favorable"] = "Earth"
      -> favorable_element(c) == Earth (method "reader-confirmed")
      -> _career_why(c, "Real Estate & Property")
         == "Uses Earth energy in a supportive role to your Fire Day Master."

The wrong *branch* again; ``_resolved_favorable`` fixes it by the same
mechanism as harish ("Aligns with your favorable element Earth, reducing
friction.").

It is not locked here because it requires an override-applied chart and one
chart is enough to pin the behaviour. Two corrections to the plan's B4 note,
taken from measurement (/tmp/sdd-val6/probe-3c.out.txt) rather than recall:

* sruthi's raw ``candidate_favorable`` is **Metal**, not the Wood B4 records —
  so a *default-path* sruthi assertion would also have been a genuine
  divergence (raw Metal vs resolved Fire), and B4's stated reason for rejecting
  it (raw Wood == resolved Wood) is refuted by measurement.
* sruthi's resolved element is **Fire** (``method="climate-balanced"``) on the
  default path, and **Earth** only once the reader override is applied.
"""
from __future__ import annotations

from saju_engine.engine import compute_chart
from saju_engine.report_data import _career_why
from saju_engine.yongsin import favorable_element


# ── Anchor chart ────────────────────────────────────────────────────────────

# Birth data verified 2026-09-14 against the repo record, NOT recalled: this is
# the same input as the "harish-published" entry in
# tests/validation/fixtures/{yongsin,climate}.json (1992-06-04 03:10, lon 79.42,
# utc+5.5), and it is the W6 compat anchor in tests/test_compat.py.
HARISH = compute_chart(
    name="Harish", gender="M", year=1992, month=6, day=4,
    hour=3, minute=10, longitude=79.42, utc_offset=5.5, use_solar_time=True,
)


# ── The fixed behaviour (was the lock) + its premise guards ─────────────────

# Retired lock: this was `xfail(strict=False, reason="report_data stale
# candidate_favorable vs resolved (Plan 6 T3 lock)")` until the fix landed
# 2026-09-14; it went XPASS, which is the delete-the-marker signal. It now
# asserts the same thing as a positive pin — the career prose reads the
# resolved element, and the raw field is a *different* element on this chart,
# so the assertion still discriminates.
def test_career_why_uses_resolved_favorable_element():
    # harish diverges with NO override: candidate=Fire, resolved=Water (climate-balanced)
    assert (HARISH.strength_assessment or {}).get("candidate_favorable") == "Fire"
    assert favorable_element(HARISH).element == "Water"
    phrase = _career_why(HARISH, "Strategy & Consulting")   # _domain_element -> Water
    assert "favorable element Water" in phrase


# Guard 1 (passing): reproduces the byte-exact FIXED output, so the pin cannot
# go vacuous and the exact served string is recorded. Pre-fix this asserted
# "Uses Water energy in a supportive role to your Metal Day Master." — the
# branch the raw Fire field selected.
def test_career_why_fixed_output_is_byte_exact():
    assert _career_why(HARISH, "Strategy & Consulting") == \
        "Aligns with your favorable element Water, reducing friction."


# Guard 2 (passing): proves the divergence needs no override for harish — the
# resolved element really is Water by the climate-balanced path.
def test_harish_resolved_element_is_climate_balanced_water():
    fe = favorable_element(HARISH)
    assert (fe.element, fe.method) == ("Water", "climate-balanced")


# ── Premise guard that keeps Guard 1 honest ─────────────────────────────────

def test_stale_branch_is_reachable_for_a_domain_the_resolver_maps_to_water():
    """Keeps Guard 1 discriminating: the raw field must still disagree with the resolver.

    Post-fix both channels name Water on this domain, so Guard 1's string would
    be produced by the *aligned* branch in either reading — which is exactly why
    the raw field must stay pinned as a different element here. If a future
    change made ``candidate_favorable`` agree with ``favorable_element()`` for
    harish, Guard 1 would keep passing while silently ceasing to discriminate
    between the resolved and the raw read. This asserts the divergence instead.

    "Strategy & Consulting" routes to Water via ``report_data._domain_element``
    (water_keys contains "strategy") — that routing is what makes the *aligned*
    branch reachable here at all, so it is pinned too, and a future change to
    the keyword table shows up here rather than weakening Guard 1.
    """
    from saju_engine.report_data import _domain_element

    assert _domain_element("Strategy & Consulting") == "Water"
    # ...while the raw (stale) field is a different element — the divergence.
    assert (HARISH.strength_assessment or {}).get("candidate_favorable") == "Fire"
