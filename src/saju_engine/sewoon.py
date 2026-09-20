"""Annual-luck (세운, 歲運) and monthly-luck (월운) overlays.

Rules from knowledge/08-luck-pillars.md:
  - The annual pillar is the 60-cycle pillar of the calendar year.
  - The Saju new year starts at 입춘 (Lichun), around Feb 4, not at Lunar New Year.
  - The annual pillar changes at 입춘.

This module computes the annual pillar for a requested year and pre-computes
its relationship to the natal chart:
  - annual stem ten-god relative to the Day Master
  - annual branch vs. natal branches (clash, combine, harm, break, punish)
  - annual stem vs. natal stems (no classical relation except via ten-god)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from functools import lru_cache

from . import lookup as L


@dataclass
class SeWoonHit:
    """One annual-luck overlay result."""
    year: int
    stem: str
    branch: str
    combined: str = ""
    # Relationship to natal chart
    stem_tengod: str = ""          # 십신 of annual stem relative to Day Master
    stem_tengod_en: str = ""
    activated_branches: List[Tuple[str, str, str]] = field(default_factory=list)
    # Each tuple: (annual_branch, natal_branch, relationship_type)
    relationship_types: List[str] = field(default_factory=list)
    # deduplicated list of relationship types for quick filtering
    stem_combinations: List[Tuple[str, str, str, str]] = field(default_factory=list)
    # Each tuple: (stem_a, stem_b, combined_element, korean_name), (stem_a,
    # stem_b) in the table's own canonical order (matching korean_name's
    # reading order, e.g. "병신합수" reads 丙 before 辛) —
    # 천간합 between the annual stem and a natal stem (knowledge/08 Part 2
    # step 3: "Annual stem vs. natal stems → 합?"). Bug found 2026-09-20
    # (external report review, 3rd pass): this check was never implemented
    # at all — e.g. 2026's 丙 combining with Harish's 辛 Day Master (丙辛합수)
    # was silently absent from every report despite being, per the
    # reviewer, "a major 2026 reading element."

    def __post_init__(self):
        self.combined = f"{self.stem}{self.branch}"


# Cached 60-cycle index for year-pillar lookup (approximate).
# 1984 is 甲子 (Jia-Zi) per classical tables.
# We use the simple mapping: (year + 56) % 60 for the 60-cycle index,
# because 1984 is index 0, and 1984 + 56 = 2040 gives index 56, etc.
# More robustly, we derive from a known anchor.
_ANCHOR_YEAR = 1984
_ANCHOR_INDEX = 0


def _annual_pillar(year: int) -> Tuple[str, str]:
    """Return the 60-cycle pillar for a Saju year.

    Note: Saju years change at 입춈 (Lichun), roughly Feb 4. For a birth before
    Lichun in year Y, the annual pillar still belongs to Y-1's cycle year in
    classical convention. This function returns the pillar for the Saju year
    whose Lichun is within the Gregorian year Y.
    """
    idx = (_ANCHOR_INDEX + (year - _ANCHOR_YEAR)) % 60
    return L.JIAZI_CYCLE[idx]


def _daily_pillar(year: int, month: int, day: int) -> Tuple[str, str]:
    """Return the 60-cycle pillar for a calendar day.

    Anchor: 1900-01-01 = 甲戌 (index 10), verified against sajupy.
    """
    from datetime import date
    anchor = date(1900, 1, 1)
    target = date(year, month, day)
    delta = (target - anchor).days
    idx = (10 + delta) % 60
    return L.JIAZI_CYCLE[idx]


# ── Solar-term-aware year/month pillar lookup ────────────────────────────────
# Classical Saju years begin at 立春 (Lichun, ~Feb 4) and months begin at each
# 節氣. The math-only functions above treat the Gregorian calendar as if Lichun
# always falls on Feb 1, which is wrong for late-January / early-February dates.
# We therefore consult sajupy's calendar_data.csv, which lists the exact
# year_pillar and month_pillar for every day 1900–2100.


@lru_cache(maxsize=1)
def _load_sajupy_calendar() -> Dict[Tuple[int, int, int], Tuple[str, str]]:
    """Load a {(year, month, day): (year_pillar, month_pillar)} map from sajupy."""
    import sajupy
    calc = sajupy.get_saju_calculator()
    df = calc.data
    years = df["year"].astype(int).tolist()
    months = df["month"].astype(int).tolist()
    days = df["day"].astype(int).tolist()
    yps = df["year_pillar"].tolist()
    mps = df["month_pillar"].tolist()
    return {
        (y, m, d): (yp, mp)
        for y, m, d, yp, mp in zip(years, months, days, yps, mps)
    }


def _annual_pillar_for_date(year: int, month: int, day: int) -> Tuple[str, str]:
    """Return the 60-cycle annual pillar for the given Gregorian date.

    Before Lichun (~Feb 4) the pillar belongs to the previous Saju year.
    """
    lookup = _load_sajupy_calendar()
    key = (year, month, day)
    if key in lookup:
        year_pillar = lookup[key][0]
        return year_pillar[0], year_pillar[1]
    # Outside the ephemeris range, fall back to the raw Saju-year math.
    return _annual_pillar(year)


def _monthly_pillar_for_date(year: int, month: int, day: int) -> Tuple[str, str]:
    """Return the 60-cycle monthly pillar for the given Gregorian date."""
    lookup = _load_sajupy_calendar()
    key = (year, month, day)
    if key in lookup:
        month_pillar = lookup[key][1]
        return month_pillar[0], month_pillar[1]
    # Outside the ephemeris range, fall back to the raw month math.
    return _monthly_pillar(year, month)


def _detect_branch_relationship(a: str, b: str) -> Optional[str]:
    """Return the relationship type between two branches, or None."""
    pair_set = {a, b}
    for x, y in L.SIX_CLASHES:
        if pair_set == {x, y}:
            return "clash"
    for x, y, _ in L.SIX_COMBINATIONS:
        if pair_set == {x, y}:
            return "combine"
    for x, y in L.SIX_HARMS:
        if pair_set == {x, y}:
            return "harm"
    for x, y in L.SIX_BREAKS:
        if pair_set == {x, y}:
            return "break"
    if a == b and a in L.SELF_PUNISHMENTS:
        return "self_punish"
    return None


def derive_sewoon(
    day_master: str,
    natal_branches: List[str],
    year: int,
    month: int = 7,
    day: int = 1,
) -> SeWoonHit:
    """Compute the annual-luck overlay for the given Gregorian date.

    Saju years change at 立春 (Lichun, ~Feb 4). For dates before Lichun the
    annual pillar belongs to the previous cycle year. Defaults to mid-year so
    that a plain year query returns the post-Lichun pillar.
    """
    stem, branch = _annual_pillar_for_date(year, month, day)
    tengod = L.ten_god(day_master, stem)
    tengod_en = {
        "비견": "Companion", "겁재": "Robber", "식신": "Eating God",
        "상관": "Hurting Officer", "편재": "Indirect Wealth",
        "정재": "Direct Wealth", "편관": "Seven Killings",
        "정관": "Direct Officer", "편인": "Indirect Resource", "정인": "Direct Resource",
    }.get(tengod, tengod)

    activated: List[Tuple[str, str, str]] = []
    types: set[str] = set()
    for nb in natal_branches:
        rel = _detect_branch_relationship(branch, nb)
        if rel:
            activated.append((branch, nb, rel))
            types.add(rel)

    combos: List[Tuple[str, str, str, str]] = []
    dm_combo = L.stem_combination(day_master, stem)
    if dm_combo:
        combo_elem, combo_ko, _ = dm_combo
        # `korean_name` (e.g. "병신합수") reads the pair in the table's own
        # canonical order, not necessarily (day_master, stem) argument
        # order — find that order so the Hanja built from it in
        # `annual_activation_note` matches (avoids a "辛丙合水" for a
        # "병신합수" label, which reads 丙 first).
        stem_a, stem_b = day_master, stem
        for sa, sb, _elem, _ko in L.TEN_STEM_COMBINATIONS:
            if {sa, sb} == {day_master, stem}:
                stem_a, stem_b = sa, sb
                break
        combos.append((stem_a, stem_b, combo_elem, combo_ko))

    return SeWoonHit(
        year=year,
        stem=stem,
        branch=branch,
        stem_tengod=tengod,
        stem_tengod_en=tengod_en,
        activated_branches=activated,
        relationship_types=sorted(types),
        stem_combinations=combos,
    )


def build_sewoon_range(
    day_master: str,
    natal_branches: List[str],
    start_year: int,
    end_year: int,
    month: int = 7,
    day: int = 1,
) -> List[SeWoonHit]:
    """Return annual-luck overlays for [start_year, end_year] inclusive."""
    return [
        derive_sewoon(day_master, natal_branches, y, month, day)
        for y in range(start_year, end_year + 1)
    ]


def current_sewoon(
    day_master: str,
    natal_branches: List[str],
    reference_year: int,
    reference_month: int = 7,
    reference_day: int = 1,
    window: int = 3,
) -> List[SeWoonHit]:
    """Return a window of annual luck around the reference date.

    Default window is reference_year-1, reference_year, reference_year+1,
    each evaluated at the same month/day as the reference date.
    """
    return build_sewoon_range(day_master, natal_branches,
                              reference_year - window, reference_year + window,
                              reference_month, reference_day)


# ── Monthly luck (월운) ──────────────────────────────────────────────────────
# The monthly pillar follows the same 60-cycle logic as the annual pillar,
# anchored on the first Saju month (寅 month, around Lichun). Saju months are
# numbered 1–12 starting from the month whose branch is 寅.
#
# For a given Gregorian year and month, we map the month to the Saju month
# index (1 = 寅, 2 = 卯, ..., 12 = 丑) and step from the year's 寅 month pillar.

_MONTH_BRANCHES: List[str] = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]


def _saju_month_index(gregorian_month: int, lichun_month: int = 2) -> int:
    """Map a Gregorian month to a Saju month index 1–12.

    The Saju year starts at 立春, roughly Gregorian Feb (month 2). So:
      - Gregorian Feb → Saju month 1 (寅)
      - Gregorian Mar → Saju month 2 (卯)
      - ...
      - Gregorian Jan → Saju month 12 (丑)

    `lichun_month` defaults to 2 (February). Adjust if a different convention is used.
    """
    idx = (gregorian_month - lichun_month) % 12
    return idx + 1  # 1-based


def _monthly_pillar(year: int, month: int) -> Tuple[str, str]:
    """Return the 60-cycle pillar for a Saju month.

    The Saju year begins at 立春 (≈ Gregorian Feb). Therefore:
      - Gregorian Jan belongs to the previous Saju year.
      - Gregorian Feb is the first Saju month (寅月).

    The first-month stem is derived from the year stem via 五虎遁 (Oho-dun).
    See `lookup._OHO_DUN`.
    """
    # Determine which Saju year this Gregorian month belongs to.
    if month < 2:  # January only
        sajuyear = year - 1
    else:
        sajuyear = year

    year_stem, _ = _annual_pillar(sajuyear)
    first_month_stem = L._OHO_DUN[year_stem]
    sm_index = _saju_month_index(month)
    branch = _MONTH_BRANCHES[sm_index - 1]
    # Step the stem from the first-month stem by (sm_index - 1).
    stem = L.STEM_ORDER[(L.STEM_INDEX[first_month_stem] + sm_index - 1) % 10]
    return stem, branch


def derive_woon(
    day_master: str,
    natal_branches: List[str],
    year: int,
    month: int,
    day: int = 15,
) -> SeWoonHit:
    """Compute the monthly-luck overlay for a Gregorian year/month/day.

    The day is needed because Saju months begin at 節氣, not at Gregorian
    month boundaries. Defaults to mid-month.

    Returns a SeWoonHit whose `year` field is overloaded to hold a synthetic
    `YYYYMM` integer for identification, since the dataclass was designed for
    annual luck. This is a pragmatic reuse; callers should document the meaning.
    """
    stem, branch = _monthly_pillar_for_date(year, month, day)
    tengod = L.ten_god(day_master, stem)
    tengod_en = {
        "비견": "Companion", "겁재": "Robber", "식신": "Eating God",
        "상관": "Hurting Officer", "편재": "Indirect Wealth",
        "정재": "Direct Wealth", "편관": "Seven Killings",
        "정관": "Direct Officer", "편인": "Indirect Resource", "정인": "Direct Resource",
    }.get(tengod, tengod)

    activated: List[Tuple[str, str, str]] = []
    types: set[str] = set()
    for nb in natal_branches:
        rel = _detect_branch_relationship(branch, nb)
        if rel:
            activated.append((branch, nb, rel))
            types.add(rel)

    return SeWoonHit(
        year=year * 100 + month,
        stem=stem,
        branch=branch,
        stem_tengod=tengod,
        stem_tengod_en=tengod_en,
        activated_branches=activated,
        relationship_types=sorted(types),
    )


def _add_months(year: int, month: int, delta: int) -> Tuple[int, int]:
    """Return the (year, month) that is `delta` calendar months from the base."""
    total = year * 12 + (month - 1) + delta
    return (total // 12), (total % 12) + 1


def current_woon_window(
    day_master: str,
    natal_branches: List[str],
    reference_year: int,
    reference_month: int,
    reference_day: int = 15,
    window: int = 2,
) -> List[SeWoonHit]:
    """Return monthly-luck overlays for +/- `window` months around the reference.

    Steps by calendar months (not fixed 30-day offsets) so the window follows
    real Saju month boundaries as returned by `_monthly_pillar_for_date`.
    """
    results: List[SeWoonHit] = []
    for delta in range(-window, window + 1):
        y, m = _add_months(reference_year, reference_month, delta)
        results.append(derive_woon(day_master, natal_branches, y, m, reference_day))
    return results


# ── Daily luck (일운) ─────────────────────────────────────────────────────────
# The daily pillar follows the same 60-cycle day math as the natal day pillar,
# anchored at 1900-01-01 = 甲戌. For a reference date, derive the day pillar and
# compute activations against natal branches.


def derive_ilwoon(
    day_master: str,
    natal_branches: List[str],
    year: int,
    month: int,
    day: int,
) -> SeWoonHit:
    """Compute the daily-luck overlay for a Gregorian calendar date."""
    stem, branch = _daily_pillar(year, month, day)
    tengod = L.ten_god(day_master, stem)
    tengod_en = {
        "비견": "Companion", "겁재": "Robber", "식신": "Eating God",
        "상관": "Hurting Officer", "편재": "Indirect Wealth",
        "정재": "Direct Wealth", "편관": "Seven Killings",
        "정관": "Direct Officer", "편인": "Indirect Resource", "정인": "Direct Resource",
    }.get(tengod, tengod)

    activated: List[Tuple[str, str, str]] = []
    types: set[str] = set()
    for nb in natal_branches:
        rel = _detect_branch_relationship(branch, nb)
        if rel:
            activated.append((branch, nb, rel))
            types.add(rel)

    return SeWoonHit(
        year=year * 10000 + month * 100 + day,  # YYYYMMDD
        stem=stem,
        branch=branch,
        stem_tengod=tengod,
        stem_tengod_en=tengod_en,
        activated_branches=activated,
        relationship_types=sorted(types),
    )


def current_ilwoon_window(
    day_master: str,
    natal_branches: List[str],
    reference_year: int,
    reference_month: int,
    reference_day: int,
    window: int = 2,
) -> List[SeWoonHit]:
    """Return daily-luck overlays for +/- `window` days around the reference."""
    from datetime import date, timedelta
    results: List[SeWoonHit] = []
    base = date(reference_year, reference_month, reference_day)
    for delta in range(-window, window + 1):
        d = base + timedelta(days=delta)
        results.append(derive_ilwoon(day_master, natal_branches, d.year, d.month, d.day))
    return results
