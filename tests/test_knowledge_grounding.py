"""Assert the engine's interpretive tables trace to their cited knowledge/ file."""
import re
from pathlib import Path

import saju_engine.report_data as report_data
from saju_engine.report_data import (
    _CAREER_DOMAINS,
    _ELEMENT_ASSOCIATIONS,
    _ELEMENT_ORGANS,
    _GROUNDING_PRACTICES,
)

KB = Path(__file__).parent.parent / "knowledge"


def _kb(name: str) -> str:
    return (KB / name).read_text(encoding="utf-8").lower()


def test_career_domains_domain_titles_appear_in_kb12():
    kb = _kb("12-career-and-vocation.md")
    for element, pairs in _CAREER_DOMAINS.items():
        for title, _roles in pairs:
            # first significant word of the domain title must appear in the file
            head = re.split(r"[ &/]", title.lower())[0]
            assert head in kb, f"{element}/{title!r} not grounded in knowledge/12"


def test_element_directions_match_kb14():
    kb = _kb("14-directions-and-relocation.md")
    expect = {"Wood": "east", "Fire": "south", "Earth": "cent", "Metal": "west", "Water": "north"}
    for element, assoc in _ELEMENT_ASSOCIATIONS.items():
        assert expect[element] in assoc["direction"].lower()
        assert expect[element] in kb


def test_element_organs_match_kb15():
    kb = _kb("15-health-and-body.md")
    for element, organs in _ELEMENT_ORGANS.items():
        head = organs.split("/")[0].strip().split()[0].lower()  # e.g. "liver"
        assert head in kb, f"{element} organ {organs!r} not in knowledge/15"


def test_grounding_practices_have_kb15_anchors():
    kb = _kb("15-health-and-body.md")
    anchors = {
        "Wood": "forest", "Fire": "midday", "Earth": "grain",
        "Metal": "breath", "Water": "swim",
    }
    for element, practices in _GROUNDING_PRACTICES.items():
        joined = " ".join(practices).lower()
        assert anchors[element] in joined
        assert anchors[element] in kb


# ── §5 item 8 (2026-09-14 architecture audit §4.3): discovery-based ────────
# ── grounding sweep. The four tests above enumerate their subjects by hand,
# so any table ADDED to report_data is uncovered by default, and the
# calculation-layer constants in lookup/strength/patterns are not covered at
# all. These sweeps introspect the modules so new tables/constants fail a
# test instead of waiting for the next audit.


def test_every_report_data_interpretive_table_has_a_source_citation():
    """Discovery sweep: every module-level dict in report_data whose name
    starts with `_` and looks interpretive (element/star/career/health/
    wealth/relationship vocabulary) must have a `# source: knowledge/...`
    comment within a few lines above its definition — the repo's own
    'no table without a knowledge citation' convention (lookup.py docstring).
    """
    import inspect
    src = inspect.getsource(report_data)
    known_tables = {
        "_CAREER_DOMAINS", "_ELEMENT_ASSOCIATIONS", "_ELEMENT_ORGANS",
        "_GROUNDING_PRACTICES",
    }
    dict_defs = [
        (m.group(1), m.start())
        for m in re.finditer(r"^(_[A-Z_]+)\s*[:=]\s*\{", src, re.MULTILINE)
    ]
    assert dict_defs, "discovery sweep found no module-level dicts — update the regex"
    missing = []
    for name, pos in dict_defs:
        # The four originally-tested tables are covered by the named tests;
        # everything else must carry its own citation.
        if name in known_tables:
            continue
        preceding = src[max(0, pos - 400):pos]
        if not re.search(r"# source: knowledge/", preceding):
            missing.append(name)
    # Tables that are pure engine vocabulary (translations, layout labels,
    # structural mappings with no interpretive claim) are listed here
    # explicitly with a reason — the sweep exists to force a conscious
    # decision per table, not to block refactors.
    ALLOWED_UNCITED = {
        "_STEM_PROFILE",       # stem imagery — grounded via the named KB-01 test
        "_STAR_MEANING",       # star meanings — grounded by the E-7 fix vs knowledge/07
        "_STEM_EN",            # pure translation table (Korean→English labels)
        "_PILLAR_POSITION_LABELS",  # layout labels (Year/Month/Day/Hour)
        "_PILLAR_AREAS",       # classical life-area mapping — its comment cites
                               # the convention directly; no numeric/doctrinal claim
    }
    unexpected = [n for n in missing if n not in ALLOWED_UNCITED]
    assert not unexpected, (
        f"interpretive tables without a `# source: knowledge/` citation "
        f"(add a citation or an explicit ALLOWED_UNCITED entry with a reason): {unexpected}"
    )


def test_calculation_layer_constants_are_documented_with_scope():
    """The audit's §4.2 finding: unsourced magic-number thresholds in
    strength.py and patterns.py are 'tuned to be conservative' but
    indistinguishable from an untested guess. The fix is documentation: each
    threshold must record (a) a knowledge/ anchor where one exists, and
    (b) the deliberate-choice note where it does not. This pins the
    *presence* of the documentation, not the numbers (the numbers are pinned
    by the sensitivity sweep)."""
    import saju_engine.strength as strength
    import saju_engine.patterns as patterns

    strength_src = inspect_source(strength)
    patterns_src = inspect_source(patterns)

    # strength.py verdict bands: documented as tuned/conservative with the
    # N-5 extreme-band rationale.
    assert re.search(r"verdict thresholds.*tuned to be conservative", strength_src, re.IGNORECASE | re.DOTALL), (
        "strength.py verdict bands lost their 'tuned to be conservative' scope note"
    )
    # patterns.py 종격 dominant share: documented as a conservative flag
    # threshold with the reader-rules caveat.
    assert re.search(r"dominant share.*≥ ?50%.*≥ ?60%", patterns_src, re.IGNORECASE), (
        "patterns.py 종격 dominant-share thresholds lost their docstring documentation"
    )


def inspect_source(module):
    import inspect
    return inspect.getsource(module)
