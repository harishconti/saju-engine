"""Top-level Saju chart derivation.

Call `compute_chart(...)` to get a fully populated `Chart` object with:
  - The four pillars (sourced from sajupy)
  - Hidden stems per branch
  - 십신 for every visible stem and every hidden stem
  - 12운성 for the Day Master in each branch
  - The major-luck (대운) sequence
  - Branch-relationship flags (합 / 충 / 형)
  - Classical stars (신살)
  - Day-Master strength heuristic
  - Grid / pattern candidates (격국)
  - Annual-luck (세운) window

All interpretation rules come from `knowledge/`.
"""
from __future__ import annotations

from typing import Optional

from datetime import date

from . import pillars as P
from . import lookup as L
from . import daeun as D
from . import stars as S
from . import strength as STR
from . import patterns as PAT
from . import sewoon as SE
from . import daeun_overlay as DO
from . import yongsin as YS
from .chart import Chart, Pillar, TenGodHit, DaeunPeriod
from .lookup import TENGOD_EN as _TENGOD_EN


def _build_pillars(raw: dict) -> list[Pillar]:
    pillars = []
    for pos in ("year", "month", "day", "hour"):
        stem = raw[f"{pos}_stem"]
        branch = raw[f"{pos}_branch"]
        hidden = []
        for role in ("main", "middle", "residual"):
            s = L.HIDDEN_STEMS.get(branch, {}).get(role)
            if s:
                hidden.append((role, s))
        pillars.append(Pillar(position=pos, stem=stem, branch=branch, hidden_stems=hidden))
    return pillars


def _derive_ten_gods(chart: Chart) -> list[TenGodHit]:
    """Compute 십신 for every visible stem and every hidden stem in the chart."""
    day_master = chart.day_master
    hits: list[TenGodHit] = []

    for p in chart.pillars:
        # visible stem
        tg = L.ten_god(day_master, p.stem)
        hits.append(TenGodHit(position=f"{p.position}_stem", stem=p.stem,
                              tengod=tg, tengod_en=_TENGOD_EN[tg]))
        # hidden stems
        for role, stem in p.hidden_stems:
            tg = L.ten_god(day_master, stem)
            hits.append(TenGodHit(position=f"{p.position}_branch_{role}", stem=stem,
                                  tengod=tg, tengod_en=_TENGOD_EN[tg]))
    return hits


def _derive_twelve_stages(chart: Chart) -> list[tuple[str, str, str]]:
    """12운성 of the Day Master in each of the four branches."""
    out = []
    for p in chart.pillars:
        stage = L.twelve_stage(chart.day_master, p.branch)
        out.append((p.position, p.branch, stage))
    return out


def _derive_branch_relationships(chart: Chart):
    """Find 합 / 충 / 형 / 파 / 해 / 삼형 in the natal chart."""
    for i, p1 in enumerate(chart.pillars):
        for p2 in chart.pillars[i + 1:]:
            b1, b2 = p1.branch, p2.branch
            pair_set = {b1, b2}
            # 6 combinations
            for a, c, elem in L.SIX_COMBINATIONS:
                if pair_set == {a, c}:
                    chart.combinations_6.append((a, c, elem, p1.position, p2.position))
            # 6 clashes
            for a, c in L.SIX_CLASHES:
                if pair_set == {a, c}:
                    chart.clashes.append((a, c))
            # 6 harms
            for a, c in L.SIX_HARMS:
                if pair_set == {a, c}:
                    chart.six_harms.append((a, c))
            # 6 breaks
            for a, c in L.SIX_BREAKS:
                if pair_set == {a, c}:
                    chart.six_breaks.append((a, c))
            # self-punishment (only same-branch pairs)
            if b1 == b2 and b1 in L.SELF_PUNISHMENTS:
                chart.self_punishments.append((b1, b1))
    # 3-harmonies: any 3 of the 4 branches that match a group
    branches = set(chart.branches)
    for a, b, c, elem in L.THREE_HARMONIES:
        if {a, b, c}.issubset(branches):
            chart.three_harmonies.append((a, b, c, elem))
    # Directional harmonies (방합): any 3 of the 4 branches match a cardinal frame.
    for a, b, c, label in L.DIRECTIONAL_HARMONIES:
        if {a, b, c}.issubset(branches):
            chart.directional_harmonies.append((a, b, c, label))
    # Half-harmonies (반합): two-of-three in a 삼합 frame when the third is absent.
    seen_half = set()
    for i, p1 in enumerate(chart.pillars):
        for p2 in chart.pillars[i + 1:]:
            b1, b2 = p1.branch, p2.branch
            if b1 == b2:
                continue
            for a, b, c, elem in L.THREE_HARMONIES:
                frame = {a, b, c}
                if b1 in frame and b2 in frame and not frame.issubset(branches):
                    key = tuple(sorted((b1, b2), key=lambda x: L.BRANCH_INDEX[x]))
                    if key not in seen_half:
                        seen_half.add(key)
                        chart.half_harmonies.append((b1, b2, f"{a}{b}{c}", elem))
    # 3-punishments: any 3 of the 4 branches that match a group
    for a, b, c, label in L.THREE_PUNISHMENTS:
        if c != "—" and {a, b, c}.issubset(branches):
            chart.three_punishments.append((a, b, c, label))
    # Pairwise 3-punishments: two-of-three in a 삼형 frame when the third is absent.
    for i, p1 in enumerate(chart.pillars):
        for p2 in chart.pillars[i + 1:]:
            b1, b2 = p1.branch, p2.branch
            if b1 == b2:
                continue
            for a, b, c, label in L.THREE_PUNISHMENTS:
                if c == "—":
                    continue
                frame = {a, b, c}
                if b1 in frame and b2 in frame and not frame.issubset(branches):
                    chart.three_punishments.append((b1, b2, "—", f"삼형 {b1}{b2} ({label})"))
    # 子卯 is a two-member punishment; detect it separately.
    if "子" in branches and "卯" in branches:
        chart.three_punishments.append(("子", "卯", "—", "Water-Wood punishment (子卯刑)"))


def _build_daeun(chart: Chart, n_periods: int = 8, utc_offset: float = 9.0) -> list[DaeunPeriod]:
    if not chart.gender:
        return []
    # N-2 (2026-09-26 audit): a 절기 is an absolute instant, and the calendar's
    # term times (once converted to this timezone) are civil-clock instants —
    # so the starting-age count must compare the birth's civil date/time
    # against them, not the solar-corrected effective_date/solar_time (which
    # differ by the longitude correction + equation of time). Using solar
    # time here used to flip which side of a 절기 boundary a birth counted
    # from, shifting the 대운 starting age.
    date_to_use = chart.birth_date
    time_to_use = chart.birth_time or "00:00"
    try:
        hh, mm = (int(x) for x in time_to_use.split(":"))
    except (ValueError, AttributeError):
        hh, mm = 0, 0
    return D.compute_daeun(
        year_stem=chart.year.stem,
        month_stem=chart.month.stem,
        month_branch=chart.month.branch,
        year=int(date_to_use[:4]),
        month=int(date_to_use[5:7]),
        day=int(date_to_use[8:10]),
        gender=chart.gender,
        n_periods=n_periods,
        hour=hh,
        minute=mm,
        utc_offset=utc_offset,
    )


def _validate_input(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    gender: Optional[str],
    longitude: Optional[float],
    convention: str,
    star_anchor: str = "day",
) -> None:
    """Raise ValueError for inputs outside sane ranges."""
    if not (1900 <= year <= 2100):
        raise ValueError(f"year {year} is outside the 1900–2100 ephemeris range")
    if not (1 <= month <= 12):
        raise ValueError(f"month must be 1–12, got {month}")
    if not (1 <= day <= 31):
        raise ValueError(f"day must be 1–31, got {day}")
    if not (0 <= hour <= 23):
        raise ValueError(f"hour must be 0–23, got {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"minute must be 0–59, got {minute}")
    if gender is not None and gender not in ("M", "F"):
        raise ValueError(f"gender must be 'M', 'F', or None, got {gender!r}")
    if longitude is not None and not (-180 <= longitude <= 180):
        raise ValueError(f"longitude must be -180 to 180, got {longitude}")
    if convention.lower() not in ("korean", "chinese"):
        raise ValueError(f"convention must be 'korean' or 'chinese', got {convention!r}")
    if star_anchor not in ("day", "year"):
        raise ValueError(f"star_anchor must be 'day' or 'year', got {star_anchor!r}")


def compute_chart(
    *,
    name: Optional[str] = None,
    gender: Optional[str] = None,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int = 0,
    city: Optional[str] = None,
    longitude: Optional[float] = None,
    utc_offset: float = 9.0,
    use_solar_time: bool = True,
    convention: str = "korean",
    early_zi_time: Optional[bool] = None,
    korean_yazi: Optional[bool] = None,
    n_periods: int = 8,
    reference_year: Optional[int] = None,
    reference_month: Optional[int] = None,
    reference_day: Optional[int] = None,
    star_anchor: str = "day",
) -> Chart:
    """Top-level: compute a fully-derived Saju chart.

    `star_anchor` selects the branch the 12신살 (and 도화/역마/화개) are
    counted from: ``"day"`` (default, common modern practice) or ``"year"``
    (traditional Korean basis) — knowledge/07-special-formations.md
    §십이신살 school note.

    `gender` must be 'M' or 'F' (or None to skip 대운 computation).
    `utc_offset` defaults to 9.0 (Korea). Pass 5.5 for India.
    `convention` defaults to ``"korean"`` — Korean 명리 야자시 semantics where
    23:00–00:59 belongs to the *current* day's 자 hour. Use ``"chinese"`` for
    mainland BaZi-style 조자시 semantics. ``korean_yazi`` and ``early_zi_time``
    are kept for backward compatibility.
    `n_periods` controls how many major-luck (대운) periods are generated.
    `reference_year/month/day` set the querier-relative "now" for current
    major-luck, annual-luck, monthly-luck, and daily-luck overlays. They default
    to the day `compute_chart` is called.
    """
    _validate_input(year, month, day, hour, minute, gender, longitude, convention, star_anchor)
    today = date.today()
    ref_year = reference_year or today.year
    ref_month = reference_month or today.month
    ref_day = reference_day or today.day
    ref_date = date(ref_year, ref_month, ref_day)
    raw = P.compute_pillars(
        year=year, month=month, day=day, hour=hour, minute=minute,
        city=city, longitude=longitude,
        utc_offset=utc_offset,
        use_solar_time=use_solar_time,
        convention=convention,
        early_zi_time=early_zi_time,
        korean_yazi=korean_yazi,
    )

    # If city was geocoded, use the returned longitude for the chart record.
    effective_longitude = longitude
    if city and raw.get("solar_correction"):
        effective_longitude = raw["solar_correction"].get("longitude", longitude)

    adjusted = raw.get("adjusted_date", (year, month, day))
    effective_date = f"{adjusted[0]:04d}-{adjusted[1]:02d}-{adjusted[2]:02d}"

    chart = Chart(
        name=name, gender=gender,
        birth_date=raw.get("birth_date", f"{year:04d}-{month:02d}-{day:02d}"),
        effective_date=effective_date,
        birth_time=raw.get("birth_time", f"{hour:02d}:{minute:02d}"),
        city=city, longitude=effective_longitude,
        utc_offset=utc_offset,
        solar_correction=raw.get("solar_correction"),
        year_month_correction=raw.get("year_month_correction"),
        zi_time_type=raw.get("zi_time_type"),
        convention=raw.get("convention", convention),
        reference_date=f"{ref_year:04d}-{ref_month:02d}-{ref_day:02d}",
        star_anchor=star_anchor,
    )
    chart.year, chart.month, chart.day, chart.hour = _build_pillars(raw)
    chart.day_master = chart.day.stem
    chart.day_master_info = L.STEM_INFO[chart.day_master]

    # 사주 세수 on the querier's reference date; used by all report layers.
    chart.current_age = D.saju_age(chart.effective_date, ref_date)

    chart.ten_gods = _derive_ten_gods(chart)
    chart.twelve_stages = _derive_twelve_stages(chart)
    _derive_branch_relationships(chart)
    chart.daeun = _build_daeun(chart, n_periods=n_periods, utc_offset=utc_offset)

    # Optional overlays
    all_hidden = [
        (role, stem)
        for p in chart.pillars
        for role, stem in p.hidden_stems
    ]
    chart.stars = S.derive_stars(
        day_stem=chart.day_master,
        day_branch=chart.day.branch,
        branches=chart.branches,
        month_branch=chart.month.branch,
        stems=chart.stems,
        day_pillar=(chart.day.stem, chart.day.branch),
        anchor=star_anchor,
        year_branch=chart.year.branch,
    )
    chart.strength_assessment = STR.assess_strength(
        day_master=chart.day_master,
        month_branch=chart.month.branch,
        stems=chart.stems,
        hidden_stems=all_hidden,
    )

    # Structural / grid pattern candidates (non-interpretive flags)
    chart.patterns = PAT.detect_patterns(
        day_master=chart.day_master,
        month_stem=chart.month.stem,
        month_branch=chart.month.branch,
        branches=chart.branches,
        stems=chart.stems,
        hidden_stems=all_hidden,
        strength_verdict=chart.strength_assessment.get("verdict", "") if chart.strength_assessment else "",
    )

    # Major-luck (대운) activation overlay. Uses the climate-resolved 용신
    # (not the raw strength-heuristic candidate) for the favorable/neutral/
    # unfavorable lean per period — see daeun_overlay.py's docstring.
    _resolved_fe = YS.favorable_element(chart)
    chart.daeun = DO.build_daeun_overlays(
        day_master=chart.day_master,
        natal_branches=chart.branches,
        natal_stems=chart.stems,
        strength_assessment=chart.strength_assessment,
        periods=chart.daeun,
        resolved_favorable=_resolved_fe.element,
        resolved_unfavorable=_resolved_fe.unfavorable,
    )

    # Current major-luck period on the querier's reference date.
    # N-4 (2026-09-26 audit): comparing `current_age` (세수) against the
    # daeun periods' `start_age`/`end_age` (floored elapsed-year labels)
    # mixed two different age conventions and picked the next decade
    # 1.3-2.4 years early. Compare the reference date directly against each
    # period's precise start date instead.
    if chart.gender in ("M", "F") and chart.daeun:
        bh, bm_ = (int(x) for x in (chart.birth_time or "00:00").split(":"))
        by_, bmo_, bd_ = (int(x) for x in chart.birth_date.split("-"))
        direction = L.daeun_direction(chart.year.stem, chart.gender)
        first_start = D.first_period_start_date(
            by_, bmo_, bd_, direction, hour=bh, minute=bm_, utc_offset=utc_offset,
        )
        if first_start is not None and ref_date >= first_start:
            def _period_start(k: int) -> date:
                try:
                    return first_start.replace(year=first_start.year + 10 * k)
                except ValueError:
                    # 29 Feb in a decade whose target year isn't a leap year.
                    return first_start.replace(year=first_start.year + 10 * k, day=28)

            for idx, p in enumerate(chart.daeun):
                period_start = _period_start(idx)
                next_start = _period_start(idx + 1) if idx + 1 < len(chart.daeun) else None
                if ref_date >= period_start and (next_start is None or ref_date < next_start):
                    chart.current_daeun = p
                    break

    # Annual-luck window around the reference date
    chart.sewoon = SE.current_sewoon(
        day_master=chart.day_master,
        natal_branches=chart.branches,
        reference_year=ref_date.year,
        reference_month=ref_date.month,
        reference_day=ref_date.day,
        window=2,
        natal_stems=chart.stems,
    )

    # Monthly-luck window around the reference date
    chart.woon = SE.current_woon_window(
        day_master=chart.day_master,
        natal_branches=chart.branches,
        reference_year=ref_date.year,
        reference_month=ref_date.month,
        reference_day=ref_date.day,
        window=2,
    )

    # Daily-luck window around the reference date
    chart.ilwoon = SE.current_ilwoon_window(
        day_master=chart.day_master,
        natal_branches=chart.branches,
        reference_year=ref_date.year,
        reference_month=ref_date.month,
        reference_day=ref_date.day,
        window=2,
    )

    return chart
