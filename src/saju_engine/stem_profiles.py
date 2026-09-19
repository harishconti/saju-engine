"""Canonical Day Master stem imagery shared across report builders.

Consolidates the previously divergent `_STEM_PROFILE` tables in
`report_data.py` and `prose_scaffold.py` so all prose uses the same
stem portrait language.
"""
from typing import Dict

_STEM_PROFILE: Dict[str, Dict[str, str]] = {
    "甲": {
        "image": "tall oak rising toward light",
        "strengths": "vision, initiative, and the ability to break new ground",
        "weaknesses": "stubbornness or impatience when growth is blocked",
    },
    "乙": {
        "image": "flexible vine finding its way around obstacles",
        "strengths": "adaptability, charm, and refined persuasion",
        "weaknesses": "indecision or over-dependence on external support",
    },
    "丙": {
        "image": "sun illuminating a wide horizon",
        "strengths": "warmth, generosity, and the power to inspire others",
        "weaknesses": "pride, burnout, or scattered attention when overextended",
    },
    "丁": {
        "image": "steady flame of a lamp or candle",
        "strengths": "concentration, care, and an eye for what others need",
        "weaknesses": "moodiness or self-criticism when feeling unappreciated",
    },
    "戊": {
        "image": "solid mountain holding the landscape together",
        "strengths": "reliability, endurance, and practical judgment",
        "weaknesses": "rigidity or resistance to quick change",
    },
    "己": {
        "image": "rich garden soil nurturing many seeds",
        "strengths": "patience, service, and quiet organizational skill",
        "weaknesses": "over-giving, worry, or losing boundaries",
    },
    "庚": {
        "image": "tempered metal blade or strong framework",
        "strengths": "decisiveness, discipline, and the courage to cut through confusion",
        "weaknesses": "harshness, inflexibility, or impulsive confrontation",
    },
    "辛": {
        "image": "polished jewel or fine instrument",
        "strengths": "precision, refinement, and a gift for detail and quality",
        "weaknesses": "perfectionism, detachment, or being easily bruised by criticism",
    },
    "壬": {
        "image": "deep river carrying intelligence and connection",
        "strengths": "curiosity, resourcefulness, and broad strategic sight",
        "weaknesses": "restlessness, inconsistency, or emotional overflow",
    },
    "癸": {
        "image": "quiet spring or morning mist",
        "strengths": "intuition, subtle influence, and creative depth",
        "weaknesses": "isolation, secrecy, or being overwhelmed by too many inputs",
    },
}


def stem_profile(stem: str) -> Dict[str, str]:
    """Return the canonical portrait for a Day Master stem, or empty dict."""
    return _STEM_PROFILE.get(stem, {})
