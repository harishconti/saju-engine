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
class HarmonyCompletion:
    """A 삼합/방합 triad that the incoming (annual/decade/monthly/daily)
    branch completes or half-completes with the natal chart.

    Source: knowledge/02-branches.md §Branch Three Harmonies / §Directional
    Harmonies — "When all three appear... highly empowered. When two appear,
    it is a partial empowerment (반합)." Applied here to a transiting branch
    arriving against the natal branches, which `_detect_branch_relationship`
    (pairwise only) can never surface since a triad completion is a 3-branch
    fact, not a 2-branch one. (E-6, 2026-09-25 audit: "no 3-branch completion
    check exists at all.")
    """
    kind: str                    # "삼합" | "방합"
    triad: Tuple[str, str, str]
    element: str
    status: str                  # "full" | "half"
    matched_natal: Tuple[str, ...]


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
    harmony_completions: List[HarmonyCompletion] = field(default_factory=list)
    # 삼합/방합 triads the incoming branch completes/half-completes; see
    # HarmonyCompletion above.
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

    natal_stem_combinations: List[Tuple[str, str, str, str, str]] = field(default_factory=list)
    # 천간합 between the annual stem and a natal stem OTHER than the Day
    # Master: (stem_a, stem_b, combined_element, korean_name, natal_stem),
    # (stem_a, stem_b) in canonical table order like `stem_combinations`.
    # Only populated when the caller passes `natal_stems`. E-6 (2026-09-25
    # audit): knowledge/08 Part 2 step 3 asks for "annual stem vs. natal
    # stems", not only vs. the Day Master (e.g. 2027 丁 + natal 壬 → 丁壬合).
    stem_clashes: List[Tuple[str, str]] = field(default_factory=list)
    # 천간충 (annual_stem, natal_stem) against any natal stem incl. the Day
    # Master — knowledge/01-stems.md §Stem Clashes. Only populated when the
    # caller passes `natal_stems` (the Day Master alone is checked otherwise).

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


def _detect_branch_relationship(a: str, b: str) -> List[str]:
    """Return every relationship type between two branches (may be more than
    one — knowledge/02-branches.md documents 寅亥 and 巳申 as "dual-status
    pairs" that are simultaneously a 합 (combine) and a 파 (break), not an
    either/or. Fixed 2026-09-25 (E-6 audit): this used to return on the
    first match in a fixed clash→combine→harm→break→self-punish priority
    order, so a dual-status pair's second relationship was silently
    discarded — e.g. 2026's 丙午 sewoon branch 午 combining with a natal 未
    also never surfaced any simultaneous break/harm it might carry.
    """
    pair_set = {a, b}
    rels: List[str] = []
    for x, y in L.SIX_CLASHES:
        if pair_set == {x, y}:
            rels.append("clash")
    for x, y, _ in L.SIX_COMBINATIONS:
        if pair_set == {x, y}:
            rels.append("combine")
    for x, y in L.SIX_HARMS:
        if pair_set == {x, y}:
            rels.append("harm")
    for x, y in L.SIX_BREAKS:
        if pair_set == {x, y}:
            rels.append("break")
    if a == b and a in L.SELF_PUNISHMENTS:
        rels.append("self_punish")
    if a != b and _is_pairwise_punishment(a, b):
        rels.append("punish")
    return rels


def _is_pairwise_punishment(a: str, b: str) -> bool:
    """True when two distinct branches belong to the same 삼형 triad, or are
    the 2-member 子卯 punishment (knowledge/02-branches.md / 07-special-
    formations.md; L.THREE_PUNISHMENTS). E-6 (2026-09-25 audit): only 자형
    was detected in annual/decade overlays, so e.g. 寅巳, 丑戌 and 子卯 were
    never flagged even though this module's docstring promised "punish".
    Same rule as premium_report._candidate_day_conflicts's 형 check.
    """
    for b1, b2, b3, _label in L.THREE_PUNISHMENTS:
        members = {m for m in (b1, b2, b3) if m != "—"}
        if a in members and b in members:
            return True
    return False


def _stem_overlay(
    day_master: str,
    stem: str,
    natal_stems: Optional[List[str]],
) -> Tuple[List[Tuple[str, str, str, str, str]], List[Tuple[str, str]]]:
    """Stem-level activations of an incoming stem against the natal stems
    other than the Day Master (천간합) and against all natal stems (천간충).
    The Day-Master 천간합 stays in `stem_combinations` (unchanged contract).
    """
    others: List[Tuple[str, str, str, str, str]] = []
    clashes: List[Tuple[str, str]] = []
    targets = list(natal_stems) if natal_stems else [day_master]
    seen_combo: set = set()
    seen_clash: set = set()
    for ns in targets:
        if L.stem_clash(stem, ns) and ns not in seen_clash:
            seen_clash.add(ns)
            clashes.append((stem, ns))
        if ns == day_master or ns in seen_combo:
            continue
        combo = L.stem_combination(stem, ns)
        if combo:
            seen_combo.add(ns)
            elem, ko, _ = combo
            sa, sb = stem, ns
            for ta, tb, _e, _k in L.TEN_STEM_COMBINATIONS:
                if {ta, tb} == {stem, ns}:
                    sa, sb = ta, tb
                    break
            others.append((sa, sb, elem, ko, ns))
    return others, clashes


# 삼형 triads that a transiting branch can complete (3-member only — the 子卯
# pair is fully covered by the pairwise "punish" relationship).
_PUNISHMENT_TRIADS: List[Tuple[str, str, str, str]] = [
    t for t in L.THREE_PUNISHMENTS if "—" not in t[:3]
]


def _detect_harmony_completions(branch: str, natal_branches: List[str]) -> List[HarmonyCompletion]:
    """Detect whether `branch` completes or half-completes a 삼합/방합 triad
    against the natal branches. See HarmonyCompletion for the doctrine cite.
    """
    hits: List[HarmonyCompletion] = []
    for table, kind in ((L.THREE_HARMONIES, "삼합"), (L.DIRECTIONAL_HARMONIES, "방합")):
        for a, b, c, label in table:
            triad = (a, b, c)
            if branch not in triad:
                continue
            others = [m for m in triad if m != branch]
            matched = tuple(m for m in others if m in natal_branches)
            if len(matched) == 2:
                hits.append(HarmonyCompletion(kind, triad, label, "full", matched))
            elif len(matched) == 1:
                hits.append(HarmonyCompletion(kind, triad, label, "half", matched))
    # 삼형 completion (E-6, 2026-09-25 audit: e.g. 2034 甲寅 completing
    # 寅巳申 against a natal 巳+申). Only the full triad is reported here —
    # a two-member 형 is already surfaced pairwise as "punish".
    for a, b, c, label in _PUNISHMENT_TRIADS:
        triad = (a, b, c)
        if branch not in triad:
            continue
        others = [m for m in triad if m != branch]
        matched = tuple(m for m in others if m in natal_branches)
        if len(matched) == 2:
            hits.append(HarmonyCompletion("삼형", triad, label, "full", matched))
    return hits


def derive_sewoon(
    day_master: str,
    natal_branches: List[str],
    year: int,
    month: int = 7,
    day: int = 1,
    natal_stems: Optional[List[str]] = None,
) -> SeWoonHit:
    """Compute the annual-luck overlay for the given Gregorian date.

    ``natal_stems`` (the four natal stems) enables the stem checks against
    every natal stem — 천간합 with non-Day-Master stems and 천간충 (E-6).

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
        for rel in _detect_branch_relationship(branch, nb):
            activated.append((branch, nb, rel))
            types.add(rel)
    harmony_completions = _detect_harmony_completions(branch, natal_branches)

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
    natal_combos, clashes = _stem_overlay(day_master, stem, natal_stems)

    return SeWoonHit(
        year=year,
        stem=stem,
        branch=branch,
        stem_tengod=tengod,
        stem_tengod_en=tengod_en,
        activated_branches=activated,
        relationship_types=sorted(types),
        harmony_completions=harmony_completions,
        stem_combinations=combos,
        natal_stem_combinations=natal_combos,
        stem_clashes=clashes,
    )


def build_sewoon_range(
    day_master: str,
    natal_branches: List[str],
    start_year: int,
    end_year: int,
    month: int = 7,
    day: int = 1,
    natal_stems: Optional[List[str]] = None,
) -> List[SeWoonHit]:
    """Return annual-luck overlays for [start_year, end_year] inclusive."""
    return [
        derive_sewoon(day_master, natal_branches, y, month, day, natal_stems=natal_stems)
        for y in range(start_year, end_year + 1)
    ]


def current_sewoon(
    day_master: str,
    natal_branches: List[str],
    reference_year: int,
    reference_month: int = 7,
    reference_day: int = 1,
    window: int = 3,
    natal_stems: Optional[List[str]] = None,
) -> List[SeWoonHit]:
    """Return a window of annual luck around the reference date.

    Default window is reference_year-1, reference_year, reference_year+1,
    each evaluated at the same month/day as the reference date.
    """
    return build_sewoon_range(day_master, natal_branches,
                              reference_year - window, reference_year + window,
                              reference_month, reference_day,
                              natal_stems=natal_stems)


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
        for rel in _detect_branch_relationship(branch, nb):
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
        harmony_completions=_detect_harmony_completions(branch, natal_branches),
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
        for rel in _detect_branch_relationship(branch, nb):
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
        harmony_completions=_detect_harmony_completions(branch, natal_branches),
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
