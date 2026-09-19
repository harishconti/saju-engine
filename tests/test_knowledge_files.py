"""Structural checks on the knowledge/ files (content is reviewed by a human)."""
from pathlib import Path

KB = Path(__file__).parent.parent / "knowledge"


def _read(name: str) -> str:
    return (KB / name).read_text(encoding="utf-8")


def test_12_career_has_required_sections():
    t = _read("12-career-and-vocation.md")
    for heading in [
        "# 12 · Career",
        "## Element → Industry Families",
        "## Ten-God → Career Mode",
        "## 용신 vs. Day Master for Career Choice",
        "## Employment vs. Entrepreneurship",
        "## Skill-Levers by Dominant Ten-God",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    for element in ["Wood", "Fire", "Earth", "Metal", "Water"]:
        assert f"### {element}" in t
    # every element family cites the five-elements or ten-gods file
    assert t.count("knowledge/03-five-elements.md") >= 1
    assert t.count("knowledge/05-ten-gods.md") >= 1


def test_13_wealth_has_required_sections():
    t = _read("13-wealth-and-business.md")
    for heading in [
        "# 13 · Wealth",
        "## 정재 vs. 편재 — Two Income Styles",
        "## Wealth-Producing Chains",
        "## Can the Day Master Hold Wealth?",
        "## 겁재奪財 — Partnership & Shared-Money Risk",
        "## Wealth Timing",
        "## Wealth Preservation",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    assert "식상생재" in t and "재생관" in t and "재고" in t
    assert "재다신약" in t
    assert "knowledge/05-ten-gods.md" in t


def test_14_directions_has_required_sections_and_scope_block():
    t = _read("14-directions-and-relocation.md")
    for heading in [
        "# 14 · Directions",
        "## Element → Direction",
        "## 용신 → Favourable Personal Direction",
        "## Relocation & Move Timing",
        "## Colours, Numbers, Seasons & Materials by Element",
        "## Classical vs. Modern",
        "## Scope Boundary — This Is Not 풍수 (Fengshui)",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    # scope block must name the excluded systems
    for excluded in ["풍수", "양택", "팔택", "flying star", "Kua"]:
        assert excluded in t
    # direction table must contain all five pairings
    for pair in ["East", "South", "West", "North", "Centre"]:
        assert pair in t


def test_15_health_has_required_sections_and_disclaimer():
    t = _read("15-health-and-body.md")
    for heading in [
        "# 15 · Health",
        "## 오행 → Organ Systems",
        "## Excess vs. Deficiency Tendencies",
        "## Controlling-Cycle Cascade",
        "## Foods, Lifestyle & Rhythm by Favourable Element",
        "## Health-Watch Timing",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    assert "not a diagnosis" in t.lower()
    assert "licensed medical" in t.lower()
    for organ in ["liver", "heart", "spleen", "lung", "kidney"]:
        assert organ in t.lower()


def test_16_date_selection_has_required_sections_and_scope():
    t = _read("16-date-selection.md")
    for heading in [
        "# 16 · Date Selection",
        "## Chart-Relative Principles",
        "## By Event Type",
        "## Two-Person Events",
        "## Scope Boundary — The Almanac Layer",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    assert "황도길일" in t and "손없는날" in t
    assert "이사" in t and "개업" in t


def test_new_knowledge_files_are_referenced():
    method = _read("09-interpretation-method.md")
    for n in ["12-career", "13-wealth", "14-directions", "15-health", "16-date-selection"]:
        assert n in method, f"09-interpretation-method.md does not reference {n}"
    glossary = _read("00-glossary.md")
    for term in ["재고", "재다신약", "택일", "양택"]:
        assert term in glossary
