"""Shared report-layer primitives (B4, 2026-10-01 audit).

Every report generator (premium, compat, career, luck-cycle, cross-candidate)
used to carry its own copy of these tables/helpers, and the copies drifted
(S2/S3 were live client-visible consequences). Import from here; never
re-declare a copy in a report module.
"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from . import lookup as L
from .daeun import first_period_start_date

# Five broad 십신 classes keyed by the KOREAN ten-god code. Classify by this,
# never by substring of an English gloss (prose_fillers 2026-09-19 bug).
TENGOD_CLASS: Dict[str, str] = {
    "비견": "Companion", "겁재": "Companion",
    "식신": "Output", "상관": "Output",
    "편재": "Wealth", "정재": "Wealth",
    "편관": "Authority", "정관": "Authority",
    "편인": "Resource", "정인": "Resource",
}

# Short English ten-god names (lookup.TENGOD_EN without the Hanja suffix).
TENGOD_SHORT_EN: Dict[str, str] = {
    k: v.split(" (")[0] for k, v in L.TENGOD_EN.items()
}

CLASS_KO: Dict[str, str] = {
    "Companion": "비겁 (比劫)",
    "Output": "식상 (食傷)",
    "Wealth": "재성 (財星)",
    "Authority": "관성 (官星)",
    "Resource": "인성 (印星)",
}

CLASS_ORDER: List[str] = ["Companion", "Output", "Wealth", "Authority", "Resource"]

ELEMENT_COLORS: Dict[str, str] = {
    "Wood": "#27ae60", "Fire": "#e74c3c", "Earth": "#f39c12",
    "Metal": "#7f8c8d", "Water": "#3498db",
}

ELEMENT_EMOJI: Dict[str, str] = {
    "Wood": "🟢", "Fire": "🔴", "Earth": "🟡", "Metal": "⚪", "Water": "🔵",
}

_VERDICT_LABELS: Dict[str, str] = {
    "extreme": "Very Strong", "strong": "Strong", "balanced": "Balanced",
    "weak": "Weak", "extreme_weak": "Very Weak",
}


def verdict_label(verdict: str) -> str:
    """Client-facing label for a strength verdict. B4: replaces four copies,
    three of which printed "Extreme" for `extreme` (asymmetric with "Very Weak")."""
    return _VERDICT_LABELS.get(verdict or "balanced", "Balanced")


def _real(e: Optional[str]) -> Optional[str]:
    return e if e and e != "—" else None


def favorability(stem_e: Optional[str], branch_e: Optional[str],
                 favorable: Optional[str], supporting: Optional[str],
                 unfavorable: Optional[str]) -> str:
    """The single favorable/neutral/unfavorable rule (S3 + F-7): a 용신 or 희신
    hit is favorable, a 기신 hit unfavorable, both at once a wash (neutral).
    "—"/None sentinels never match."""
    hits = {stem_e, branch_e}
    good = {e for e in (_real(favorable), _real(supporting)) if e}
    bad = _real(unfavorable)
    fav_hit = bool(good & hits)
    unfav_hit = bad is not None and bad in hits
    if fav_hit and unfav_hit:
        return "neutral"
    if fav_hit:
        return "favorable"
    if unfav_hit:
        return "unfavorable"
    return "neutral"


def plain(text: str) -> str:
    """Wrap a lay restatement as a single-line 'In plain words' blockquote."""
    return f"> **In plain words:** {text}"


def bar(pct: float, width: int = 20) -> str:
    """ASCII presence bar: round(pct/100*width) filled cells of `width`."""
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def first_period_start(chart) -> Optional[date]:
    """Precise calendar date the first 대운 decade begins (N-4)."""
    try:
        by, bm, bd = (int(x) for x in chart.birth_date.split("-"))
    except (ValueError, AttributeError):
        return None
    bh, bmi = 0, 0
    try:
        bh, bmi = (int(x) for x in (chart.birth_time or "00:00").split(":"))
    except (ValueError, AttributeError):
        pass
    direction = L.daeun_direction(chart.year.stem, chart.gender)
    return first_period_start_date(
        by, bm, bd, direction, hour=bh, minute=bmi,
        utc_offset=getattr(chart, "utc_offset", 9.0) or 9.0,
    )
