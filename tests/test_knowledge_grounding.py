"""Assert the engine's interpretive tables trace to their cited knowledge/ file."""
import re
from pathlib import Path

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
