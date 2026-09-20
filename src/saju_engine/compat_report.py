"""Standalone 궁합 (合婚) report generator.

Produces a single Markdown document from two `Chart` objects. The cover shows
both names, DOBs, Day Masters, and the composite score + band; the body has
all 11 sub-system sections in classical order, followed by a Practical
Guidance summary and Closing Note.

Citation stripping is handled by the PDF backend — inline
`*(see knowledge/11-gunghap.md §X)*` references stay in the markdown and are
removed at render time, consistent with the rest of the engine.

Wording rules (per CLAUDE.md Ground Rules):
  - Never claim a perfect or failing marriage.
  - Use "tendency / pattern / resonance / friction" language.
  - Always include Korean (한글) and Hanja (한자) for technical terms on
    first use, then Korean only thereafter.
"""
from __future__ import annotations

from typing import List, Optional

from .chart import Chart
from .compat import WEIGHT, CompatReport, CompatSubResult, _element_strength, compat_score
from .yongsin import favorable_element

from datetime import date


# ── Element-color emoji table (matches saju_html / engine convention) ───────

_ELEMENT_EMOJI = {
    "Wood": "🟢", "Fire": "🔴", "Earth": "🟡", "Metal": "⚪", "Water": "🔵",
}


def _plain(text: str) -> str:
    """Wrap a lay restatement as a single-line 'In plain words' blockquote."""
    return f"> **In plain words:** {text}"


def _plain_words_verdict(report: CompatReport) -> str:
    picture = {
        "Excellent": "a strongly supportive match — the fundamentals line up",
        "Strong": "a solid match — more working with each other than against",
        "Mixed": "a workable match with real friction points to manage deliberately",
        "Challenging": "a match that asks for steady, conscious effort to hold together",
    }.get(report.band, "a match to read section by section")
    return _plain(
        f"Overall this reads as {picture} ({report.score}/100). "
        f"Treat the number as a weather report, not a verdict."
    )


def _plain_words_daymaster_cross(report: CompatReport) -> str:
    db = report.daybranch.band
    if db == "Yellow Flag":
        core = ("your day-to-day rhythms rub against each other — the friction sits in ordinary "
                "life, so it helps to name it early")
    elif db in ("Strong", "Moderate"):
        core = ("your day-to-day rhythms fit naturally — the everyday texture of living together "
                "is a strength")
    else:
        core = "your day-to-day rhythms are neutral — neither a lift nor a drag on their own"
    return _plain(f"At the centre of the match, {core}.")


def _plain_words_timing(report: CompatReport) -> str:
    band = report.daeun_sync.band
    if band in ("Strong", "Moderate"):
        t = "your big life-chapters tend to turn at similar times — you are likely to move in step"
    elif band == "Soft":
        t = ("your life-chapters turn on loosely related clocks — mostly fine, with occasional "
             "mismatched timing")
    else:
        t = ("your life-chapters turn on different clocks — plan for stretches where one of you is "
             "rising while the other is steadying")
    return _plain(f"On timing, {t}.")


def _emoji(elem: str) -> str:
    return _ELEMENT_EMOJI.get(elem, "·")


# ── Deep-tier helpers (added for the deep compatibility product) ────────────


def _bar(pct: float) -> str:
    filled = int(round(pct / 10))
    return "█" * filled + "░" * (10 - filled)


def _element_balance_lines(chart: Chart, name: str) -> List[str]:
    """Colored-emoji element balance table for one partner."""
    dist = _element_strength(chart)
    lines: List[str] = []
    lines.append(f"#### Element Balance — {name}")
    lines.append("")
    lines.append("| Element | Presence | Percentage |")
    lines.append("|---|---|---|")
    for elem in ["Fire", "Wood", "Earth", "Metal", "Water"]:
        pct = dist.get(elem, 0.0)
        lines.append(f"| {_emoji(elem)} {elem} | {_bar(pct)} | {pct:.1f}% |")
    lines.append("")
    return lines


def _day_master_snapshot(chart: Chart, name: str) -> List[str]:
    """Concise Day Master strength / favorable-element snapshot."""
    dm = chart.day_master_info or {}
    sa = chart.strength_assessment or {}
    lines: List[str] = []
    lines.append(f"#### Day Master Snapshot — {name}")
    lines.append("")
    lines.append(
        f"- **Day Master:** {chart.day.stem} "
        f"({dm.get('korean', '')} / {dm.get('hanja', '')}) — "
        f"{dm.get('element', '')} ({dm.get('polarity', '')})"
    )
    fe = favorable_element(chart)
    lines.append(f"- **Seasonal strength verdict:** {sa.get('verdict', '—')}")
    lines.append(f"- **Favorable element (용신):** {fe.element}")
    lines.append(f"- **Supporting element (희신):** {fe.supporting}")
    lines.append(f"- **Unfavorable / watch element:** {sa.get('candidate_unfavorable', '—')}")
    if fe.note:
        lines.append(f"- *How this was derived:* {fe.note}")
    lines.append("")
    return lines


def _period_status(period, fe) -> str:
    """Favorable/neutral/unfavorable lean vs. the FINAL resolved element
    ``fe`` (which already reflects a reader override, if one was applied via
    ``compat_score``'s ``favorable_element_a``/``_b`` — see the docstring on
    ``_daeun_lines`` for why this must not read ``period.favorable_status``
    directly)."""
    hits = {period.stem_element, period.branch_element}
    if fe.element in hits:
        return "favorable"
    return "neutral"


def _daeun_lines(chart: Chart, name: str) -> List[str]:
    """Current major-luck period + next two upcoming periods for one partner.

    Recomputes each period's favorable/neutral lean against
    ``favorable_element(chart)`` rather than trusting the chart-baked
    ``period.favorable_status``. That field is set once at compute_chart
    time, before any reader override is known; ``compat_score`` (called
    earlier in ``generate_compat_report``) mutates ``chart.strength_assessment``
    in place with ``reader_override_favorable`` when a favorable_element_a/_b
    override was passed, so calling ``favorable_element(chart)`` here (no
    explicit override arg needed) picks that up automatically. Found
    2026-09-19 alongside the same bug in daeun_overlay.py / prose_fillers.py.
    """
    lines: List[str] = []
    cur = getattr(chart, "current_daeun", None)
    if cur is None:
        return lines

    fe = favorable_element(chart)
    lines.append(f"#### Major Luck Timeline — {name}")
    lines.append("")
    lines.append(
        f"**Current period (ages {cur.start_age}–{cur.end_age}):** "
        f"**{cur.combined}** — {cur.stem_tengod_en or cur.stem_tengod} "
        f"· Favorable status: *{_period_status(cur, fe)}*"
    )
    if cur.activated_branches:
        rels = ", ".join(sorted(set(cur.relationship_types or [])))
        lines.append(f"- Activated branch patterns: {rels or 'none'}")
    lines.append("")
    lines.append("| Ages | Pillar | Stem Ten-God | Favorable Status |")
    lines.append("|---|---|---|---|")
    seen = {(cur.start_age, cur.end_age)}
    for per in chart.daeun:
        if (per.start_age, per.end_age) in seen:
            continue
        if per.start_age < cur.start_age:
            continue
        lines.append(
            f"| {per.start_age}–{per.end_age} | {per.combined} | "
            f"{per.stem_tengod_en or per.stem_tengod} | {_period_status(per, fe)} |"
        )
        seen.add((per.start_age, per.end_age))
        if len(seen) >= 4:
            break
    lines.append("")
    return lines


def _annual_overlay(chart_a: Chart, chart_b: Chart, name_a: str, name_b: str) -> List[str]:
    """Side-by-side annual luck table for the next several years."""
    years: dict = {}
    for hit in chart_a.sewoon:
        years.setdefault(hit.year, {})["a"] = hit
    for hit in chart_b.sewoon:
        years.setdefault(hit.year, {})["b"] = hit

    # Bug found 2026-09-20 (external code-quality review): `date.today().year`
    # made the visible year range silently shift on every real-world day the
    # report is generated, with no way to pin it for a reproducible test or
    # a "report as of" regeneration. `Chart.reference_date_obj()` is the
    # established mechanism the rest of the engine (`premium_report.py`)
    # already uses for exactly this purpose — it defaults to "now" when the
    # chart carries no explicit `reference_date`, so behaviour is unchanged
    # for ordinary callers.
    current_year = (chart_a.reference_date_obj() or date.today()).year
    lines: List[str] = []
    lines.append("#### Annual Couple Timing Overlay")
    lines.append("")
    lines.append(f"| Year | {name_a} | {name_b} | Joint Note |")
    lines.append("|---|---|---|---|")
    for yr in sorted(years.keys()):
        if yr < current_year - 1:
            continue
        ha = years[yr].get("a")
        hb = years[yr].get("b")
        a_txt = f"{ha.combined} ({ha.stem_tengod_en or ha.stem_tengod})" if ha else "—"
        b_txt = f"{hb.combined} ({hb.stem_tengod_en or hb.stem_tengod})" if hb else "—"
        note_parts: List[str] = []
        if ha and hb:
            if ha.combined == hb.combined:
                note_parts.append("same annual pillar — shared theme")
            else:
                a_rels = ha.relationship_types or []
                b_rels = hb.relationship_types or []
                if not a_rels and not b_rels:
                    note_parts.append("quiet year for both")
                else:
                    if a_rels:
                        note_parts.append(f"{name_a}: {', '.join(a_rels)}")
                    if b_rels:
                        note_parts.append(f"{name_b}: {', '.join(b_rels)}")
        note = "; ".join(note_parts) if note_parts else "—"
        lines.append(f"| {yr} | {a_txt} | {b_txt} | {note} |")
    lines.append("")
    return lines


def _deep_sections(report: CompatReport, name_a: str, name_b: str) -> List[str]:
    """Extra content for the deep compatibility tier."""
    a, b = report.chart_a, report.chart_b
    lines: List[str] = []
    lines.append("## Deep Compatibility Layer")
    lines.append("")
    lines.append(
        "The basic reading above evaluates the natal composite across the classical "
        "eleven sub-systems. This deep layer adds each partner's individual element "
        "balance, Day Master strength, current major-luck (대운) direction, and a "
        "year-by-year couple timing overlay so you can see *when* the natal pattern is "
        "likely to be activated."
    )
    lines.append("")

    lines.append("### Individual Chart Snapshots")
    lines.append("")
    lines.extend(_element_balance_lines(a, name_a))
    lines.extend(_day_master_snapshot(a, name_a))
    lines.extend(_element_balance_lines(b, name_b))
    lines.extend(_day_master_snapshot(b, name_b))

    lines.append("### Timing & Movement")
    lines.append("")
    lines.extend(_daeun_lines(a, name_a))
    lines.extend(_daeun_lines(b, name_b))
    lines.extend(_annual_overlay(a, b, name_a, name_b))

    lines.append(
        "*All timing notes are tendencies, not date-specific predictions. Use them "
        "as a lens for joint planning rather than as fixed forecasts.*"
    )
    lines.append("")
    return lines


# ── Section helpers ─────────────────────────────────────────────────────────

def _cover(report: CompatReport, name_a: str, name_b: str) -> List[str]:
    """Cover: both names, DOBs, Day Masters, score, band."""
    lines: List[str] = []
    a, b = report.chart_a, report.chart_b
    a_dm_elem = _ELEMENT_EMOJI.get(a.day_master_info.get("element", "·"), "·") if a.day_master_info else "·"
    b_dm_elem = _ELEMENT_EMOJI.get(b.day_master_info.get("element", "·"), "·") if b.day_master_info else "·"
    lines.append(f"# {name_a} × {name_b} — 궁합 (合婚 / Compatibility Reading)")
    lines.append("")
    lines.append(f"**Composite Score (종합 점수):** **{report.score} / 100**  ")
    lines.append(f"**Verdict Band (평가):** **{report.band}**  *(see knowledge/11-gunghap.md §Composite Weight)*")
    lines.append("")
    lines.append("| Partner | Day Master | Day Branch | Day Pillar | Favorable Element |")
    lines.append("|---|---|---|---|---|")
    a_fav = favorable_element(a).element
    b_fav = favorable_element(b).element
    lines.append(
        f"| **{name_a}** | {a.day.stem} {a_dm_elem} | {a.day.branch} | "
        f"{a.day.combined} | {a_fav} |"
    )
    lines.append(
        f"| **{name_b}** | {b.day.stem} {b_dm_elem} | {b.day.branch} | "
        f"{b.day.combined} | {b_fav} |"
    )
    lines.append("")
    return lines


def _glance_table(chart: Chart, name: str) -> List[str]:
    """Compact 4-pillar + element balance table for one chart."""
    lines: List[str] = []
    lines.append(f"### {name} — Four Pillars (사주 팔자 / 四柱八字)")
    lines.append("")
    lines.append("| Pillar | Stem | Branch | Combined |")
    lines.append("|---|---|---|---|")
    for label, p in [("Year (년주)", chart.year), ("Month (월주)", chart.month),
                     ("Day (일주)", chart.day), ("Hour (시주)", chart.hour)]:
        lines.append(f"| {label} | {p.stem} | {p.branch} | {p.combined} |")
    lines.append("")
    return lines


def _verdict_block(report: CompatReport) -> List[str]:
    """Composite breakdown table + top red flags + top favorable points."""
    lines: List[str] = []
    lines.append("## The Verdict (심정)")
    lines.append("")
    lines.append("| Sub-System | Korean | Score | Max | Verdict |")
    lines.append("|---|---|---|---|---|")
    for sub in report.sub_systems():
        lines.append(
            f"| {sub.label} | {sub.label_kr} | {sub.score:+d} | {sub.max} | {sub.band} |"
        )
    lines.append("")
    lines.append(f"**Composite Score (종합 점수):** {report.score}/100 → **{report.band}**")
    lines.append("")
    if report.red_flags:
        lines.append("### Top Red Flags (주의 사항)")
        lines.append("")
        for f in report.red_flags:
            lines.append(f"- ⚠️ {f}")
        lines.append("")
    if report.yellow_flags:
        lines.append("### Yellow Flags (관찰 사항)")
        lines.append("")
        for f in report.yellow_flags[:5]:
            lines.append(f"- 🟡 {f}")
        lines.append("")
    if report.favorable_points:
        lines.append("### Favorable Points (긍정적 요소)")
        lines.append("")
        for f in report.favorable_points:
            lines.append(f"- ✅ {f}")
        lines.append("")
    return lines


def _sub_system_block(label_en: str, label_kr: str, sub: CompatSubResult,
                       citation: str, extra: Optional[List[str]] = None,
                       compact: bool = False) -> List[str]:
    """Render one sub-system as a section."""
    lines: List[str] = []
    if compact:
        lines.append(f"### {label_en}")
        lines.append(f"**{sub.score:+d} / {sub.max}** — {sub.band}  ")
        lines.append(sub.narrative)
        lines.append("")
        if sub.flags:
            lines.append("Tags: " + ", ".join(f"`{f}`" for f in sub.flags))
            lines.append("")
        if extra:
            lines.extend(extra)
        return lines

    lines.append(f"## {label_en} — {label_kr}")
    lines.append("")
    lines.append(f"**Score:** {sub.score:+d} / {sub.max}  ({sub.band})")
    lines.append("")
    lines.append(sub.narrative)
    lines.append("")
    if sub.flags:
        lines.append("**Tags:** " + ", ".join(f"`{f}`" for f in sub.flags))
        lines.append("")
    if extra:
        lines.extend(extra)
    lines.append(f"*{citation}*")
    lines.append("")
    return lines


def _practical_guidance(report: CompatReport, name_a: str, name_b: str) -> List[str]:
    """Actionable summary, derived deterministically from sub-system flags.

    Grounded in `knowledge/11-gunghap.md` (§A–§K). Each bullet is conditioned on
    a real flag/score the engine emits, so the set scales to 6–8 actionable
    notes for most charts rather than collapsing to one or two.
    """
    lines: List[str] = []
    lines.append("## Practical Guidance (실천 지침)")
    lines.append("")
    bullets: List[str] = []
    a, b = report.chart_a, report.chart_b
    fav_a = favorable_element(a).element
    fav_b = favorable_element(b).element

    # Cross-용신 availability (lucky-element guidance).
    yongshin = report.yongshin
    if yongshin.score >= 6:
        bullets.append(
            f"**Lean on your shared lucky element.** Cross-용신 supply is strong "
            f"(sub-system D: {yongshin.score}/12) — each of you brings what the "
            f"other's chart needs. Consciously build environments, seasons, and "
            f"activities that activate the favorable element ({fav_a}"
            f"{f' / {fav_b}' if fav_a != fav_b else ''}); both Day Masters "
            "benefit at once. *(see knowledge/11-gunghap.md §D)*"
        )

    # Day-stem combination (일간합) — full / half-binding / absent.
    dsc = report.daystem_combo
    if dsc.score == WEIGHT["daystem_combo"]:
        bullets.append(
            f"**Day-stem combination (일간합) is fully present** between {name_a} and "
            f"{name_b} — a strong magnetic layer without breaking interference. "
            "Use it as the 'ease' axis: not every interaction has to be effortful. "
            "*(see knowledge/11-gunghap.md §A)*"
        )
    elif dsc.score == int(WEIGHT["daystem_combo"] * 0.5):
        bullets.append(
            f"**Day-stem combination (일간합) is a half-binding (간섭).** "
            f"{name_a} and {name_b} share a natural 천간합, but a breaking stem "
            "in one of the charts partially dissolves it — attraction is present "
            "but moderated. Let the day-branch and shared activities carry more "
            "weight. *(see knowledge/11-gunghap.md §A)*"
        )
    elif dsc.score == 0:
        bullets.append(
            "**Day-stem combination (일간합) is absent.** Attraction must build "
            "through shared activities, not first-meeting chemistry — the "
            "day-branch layer (below) is your primary anchor. *(see "
            "knowledge/11-gunghap.md §A)*"
        )

    # Same Day Master (비견/비견 mirror dynamic) — fires for both-丙, both-甲, etc.
    if a.day.stem == b.day.stem:
        bullets.append(
            f"**You share the same Day Master ({a.day.stem}) — a 비견 (比肩) "
            "mirror dynamic.** You are peers rather than complements: easy and "
            "familiar, but it can drift toward a sibling/friendship tone or "
            "mild competition when both want the same role. Counter it with "
            "deliberate asymmetry — take turns leading and following, and "
            "protect romantic differentiation so the bond doesn't flatten. "
            "*(see knowledge/11-gunghap.md §G)*"
        )

    # Day-branch (spouse palace) — mutually exclusive: clash / 육합 / 반합 / neutral.
    db = report.daybranch
    db_flags = " ".join(db.flags)
    if "RED FLAG" in db_flags or any("육충" in f for f in db.flags):
        bullets.append(
            "**Day-branch clash (일지 육충) is present** — a classical hard "
            "indicator. Workable, but the relationship benefits from explicit "
            "communication rhythms: a weekly 'check-in' beats ad-hoc resolution. "
            "*(see knowledge/11-gunghap.md §B4)*"
        )
    elif any("육합" in f for f in db.flags):
        bullets.append(
            "**Day-branch combination (일지 육합) is present** — the strongest "
            "classical favorable. Maintain shared rituals (meals, weekly date, "
            "annual trip) that reinforce this anchor. *(see "
            "knowledge/11-gunghap.md §B1)*"
        )
    elif any("반합" in f for f in db.flags):
        bullets.append(
            "**Day-branch partial harmony (일지 반합) is present** — two-of-three "
            "in a 삼합 frame. A real but incomplete anchor: nurture the shared "
            "element (e.g. Fire for 寅午戌) through joint activities, and be "
            "aware the third branch is 'missing' — the bond wants a deliberate "
            "third point of connection (a shared project, place, or person) to "
            "complete the frame. *(see knowledge/11-gunghap.md §B2)*"
        )

    # Nayin clash — practical caution for the 납음 상충 case.
    if report.nayin.score < 0 or any("상충" in f for f in report.nayin.flags):
        bullets.append(
            "**Nayin (납음) clash is present** — a soft, disputed indicator. "
            "Don't overweight it on its own; treat it as a reminder to align "
            "emotional climate (조후: cold/hot, dry/wet) rather than as a "
            "blocking verdict. *(see knowledge/11-gunghap.md §C)*"
        )

    # Ten-god cross — classical caution (negative score only).
    if report.tengod_cross.score < 0:
        bullets.append(
            "**Ten-god cross-pattern is a classical caution.** Both partners "
            "tend to apply the same relational pattern (e.g. both authoritative, "
            "both critical). Conscious asymmetry helps: take turns leading and "
            "following. *(see knowledge/11-gunghap.md §G)*"
        )

    # Compatibility stars.
    if any("쌍화개" in f for f in report.compat_stars.flags):
        bullets.append(
            "**쌍화개 (both have 화개):** both partners carry a Canopy overlay — "
            "spiritual / aesthetic affinity is high, but emotional distance can "
            "creep in. Schedule deliberate emotional connection time. *(see "
            "knowledge/11-gunghap.md §I)*"
        )

    # Yin-Yang polarity — mutually exclusive: complementary / same.
    yy = report.yin_yang
    if yy.score >= 2:
        bullets.append(
            "**Yin-Yang polarity is complementary** — opposite Day-Master "
            "polarity, a classic complementary dynamic. Honor the differences "
            "rather than trying to smooth them out. *(see "
            "knowledge/11-gunghap.md §J)*"
        )
    elif any("음양 동일" in f for f in yy.flags) or yy.score < 0:
        bullets.append(
            "**Identical Yin-Yang polarity (same wavelength).** Easy resonance, "
            "but the 권인성 school warns it can go 편의-stale — protect "
            "differentiation and avoid drifting into parallel rather than "
            "intertwined lives. *(see knowledge/11-gunghap.md §J)*"
        )

    # Combined elements — only when genuinely uneven (negative).
    if report.combined_elements.score < 0:
        bullets.append(
            "**Combined element balance is uneven.** One element dominates the "
            "union. Conscious counter-balance (the favored partner occasionally "
            "yielding, or jointly cultivating the under-represented element) "
            "keeps the relationship from locking into a single rhythm. *(see "
            "knowledge/11-gunghap.md §F)*"
        )

    # Daeun direction divergence + 'when to be more deliberate' timing note.
    ds = report.daeun_sync
    if any("방향 상이" in f for f in ds.flags):
        bullets.append(
            "**Your major-luck (대운) directions diverge** — life's large phases "
            "arrive on different timing tracks for the two of you. Be more "
            "deliberate about timing joint decisions: for any wedding year, "
            "relocation, or major purchase, overlay both partners' 세운 (annual "
            "luck) and pick a window that is favorable for both, not just one. "
            "*(see knowledge/11-gunghap.md §H)*"
        )

    if not bullets:
        bullets.append(
            "**No strong red flags surfaced.** The relationship shows a workable "
            "default — use the natural ease to invest in the long-term "
            "structural factors (family, finances, mutual support)."
        )

    for b in bullets:
        lines.append(f"- {b}")
    lines.append("")
    return lines


def _verdict_narrative(report: CompatReport) -> List[str]:
    """Plain-English explanation of what the composite score / band means."""
    para = (
        f"**What {report.score}/100 ({report.band}) means:** "
        "The composite is anchored so that a perfectly neutral chart "
        "(all sub-systems scoring 0) lands at 50/100 in the Mixed band; "
        "positive classical signals lift it, and negative signals lower it. "
    )
    if report.band == "Excellent":
        para += (
            "an unusually strong classical alignment across most sub-systems — "
            "the charts reinforce each other rather than strain. This is a "
            "favorable tendency, not a guarantee; the relationship still lives "
            "on conscious effort."
        )
    elif report.band == "Strong":
        para += (
            "a solid classical alignment with a few sub-systems needing "
            "attention. The favorable layers outweigh the friction points — a "
            "workable, durable tendency with known soft spots to mind."
        )
    elif report.band == "Mixed":
        para += (
            "a workable union in which specific sub-systems ask for deliberate "
            "attention. Mixed is not a failure — many long, happy marriages sit "
            "in this band; the chart simply flags which dimensions want "
            "conscious effort rather than riding on natural ease."
        )
    else:  # Challenging
        para += (
            "a union where several classical sub-systems pull against each "
            "other. Challenging is not a verdict of impossibility — it means "
            "the relationship will ask for more deliberate communication and "
            "structure than average. Many couples in this band build lasting "
            "marriages by treating the friction points as explicit work."
        )
    return [
        para,
        "",
        "*see knowledge/11-gunghap.md §Composite Weight*",
        "",
    ]


def _couple_narrative(report: CompatReport, name_a: str, name_b: str) -> List[str]:
    """2–3 sentence 'Who are you together?' synthesizing daybranch + ten-god cross + 용신 supply."""
    a, b = report.chart_a, report.chart_b
    parts: List[str] = []

    # Day-branch (spouse palace) layer.
    db = report.daybranch
    if any("육합" in f for f in db.flags):
        parts.append("your spouse palaces (일지) combine")
    elif any("반합" in f for f in db.flags):
        parts.append("your spouse palaces (일지) sit in a partial harmony (반합)")
    elif "RED FLAG" in " ".join(db.flags) or any("육충" in f for f in db.flags):
        parts.append("your spouse palaces (일지) carry a classical clash")
    else:
        parts.append("your spouse palaces (일지) hold a neutral, uncombined relation")

    # Ten-god cross layer.
    tg = report.tengod_cross
    if a.day.stem == b.day.stem:
        parts.append(f"you share the Day Master {a.day.stem} — a peer/mirror dynamic (비견) rather than a complement")
    elif tg.score > 0:
        parts.append("your ten-god cross leans complementary")
    elif tg.score < 0:
        parts.append("your ten-god cross leans cautionary")
    else:
        parts.append("your ten-god cross is neutral")

    # 용신 supply layer.
    ys = report.yongshin
    if ys.score >= 6:
        parts.append("your charts feed each other's favorable element (용신) — each brings what the other needs")
    elif ys.score <= 0:
        parts.append("your favorable elements (용신) do not strongly cross-supply")

    sentence = "Together, " + ", ".join(parts) + "."
    sentence2 = (
        "This composite is a tendency, not a destiny — the daily relationship "
        "is shaped by the choices both of you make over years."
    )
    return [
        "## Who You Are Together (두 사람의 관계 성향)",
        "",
        f"{sentence} {sentence2}",
        "",
        "*see knowledge/11-gunghap.md §B, §G, §D*",
        "",
    ]


def _daeun_callout(report: CompatReport) -> List[str]:
    """Top-line 'Watch out for' callout when 대운 directions diverge. Empty if no divergence."""
    if not any("방향 상이" in f for f in report.daeun_sync.flags):
        return []
    return [
        "> **⚠️ Watch out for — 대운 방향 상이 (diverging major-luck directions):** "
        "the two of you enter life's large phases on different timing tracks. "
        "Years that feel expansive for one can coincide with a contraction "
        "phase for the other. For any time-bound decision (wedding year, "
        "relocation, major purchase), overlay both partners' 세운 (annual "
        "luck) rather than reading either chart alone.",
        "",
        "*see knowledge/11-gunghap.md §H*",
        "",
    ]


def _next_steps(name_a: str, name_b: str, compact: bool = False) -> List[str]:
    """Closing CTA — upgrade options beyond the static compat reading."""
    if compact:
        return [
            "## Next Steps",
            "",
            "This is a snapshot of your natal composite. For the full "
            "eleven-sub-system analysis, major-luck timelines, and a year-by-year "
            "couple overlay, ask for the Deep Compatibility Reading.",
            "",
        ]
    return [
        "## Next Steps (다음 단계)",
        "",
        "This 두 분 궁합 reading is a static, whole-life composite. To go deeper:",
        "",
        f"- **Individual deep-dive reading** for {name_a} and for {name_b} — "
        "the full natal portrait (Day Master strength, 용신, 대운 timeline, "
        "and career / relationship / health tendencies) that this compat "
        "reading draws on.",
        "- **Year-ahead couple overlay** — a 세운 (annual luck) overlay for "
        "both partners across the next 12 months, flagging synchronized "
        "favorable and cautionary windows for joint decisions.",
        "- **MP3 audio summary** — this compatibility reading narrated for the "
        "two of you to listen to together.",
        "",
        "Ask for any of these as a follow-up.",
        "",
    ]


def _closing_note(report: CompatReport, name_a: str, name_b: str) -> List[str]:
    """Closing note synthesizing 2–3 specific chart features."""
    lines: List[str] = []
    lines.append("## Closing Note (맺음말)")
    lines.append("")
    lines.append(
        f"This reading reflects the classical 권인성·곽임성·정봉재·송기영 Korean "
        f"Myeongri consensus on {name_a} × {name_b}'s natal compatibility, "
        f"across all eleven sub-systems documented in "
        f"`knowledge/11-gunghap.md`. The composite score of **{report.score}/100 "
        f"({report.band})** is a tendency indicator, not a destiny. No "
        f"compatibility reading can account for conscious effort, life "
        f"circumstances, or the choices both partners make over years. "
        f"Classical 명리 text guides tendencies; the relationship itself is "
        f"lived."
    )
    lines.append("")
    if report.band in {"Mixed", "Challenging"}:
        lines.append(
            "**A note on challenging and mixed verdicts:** these do not mean "
            "incompatibility. They mean the chart surfaces patterns that need "
            "deliberate, conscious attention — which is a different problem from "
            "having no resonance at all. Many long, happy marriages have charts "
            "with 'Challenging' compat scores; many short, painful ones have "
            "'Excellent'."
        )
    lines.append("")
    return lines

# ── Top-level entry point ───────────────────────────────────────────────────

def generate_compat_report(
    chart_a: Chart,
    chart_b: Chart,
    name_a: str = "Partner A",
    name_b: str = "Partner B",
    generation_date: str = "",
    tier: str = "basic",
    favorable_element_a: Optional[str] = None,
    favorable_element_b: Optional[str] = None,
) -> str:
    """Generate the 두 분 궁합 (Compatibility Reading) markdown report.

    Tiers:
      - ``basic`` (default) — compact ~4-page snapshot: cover, quick verdict,
        the four most decisive sub-systems, a condensed practical guidance
        summary, closing note, and a short next-steps prompt.
      - ``deep`` — basic + full eleven-sub-system breakdown, individual chart
        snapshots, major-luck timelines, and a year-by-year couple overlay
        (~9–10 pages).

    There is no ``sample`` tier; the old sample logic is now the basic tier.

    ``favorable_element_a`` / ``favorable_element_b`` override the engine's
    heuristic 용신 when a qualified reader has already argued a specific
    favorable element for a partner.
    """
    report = compat_score(
        chart_a, chart_b,
        favorable_element_a=favorable_element_a,
        favorable_element_b=favorable_element_b,
    )

    if tier == "deep":
        lines: List[str] = _deep_report_lines(report, chart_a, chart_b, name_a, name_b)
    else:
        # basic (and any unrecognized tier falls back to basic)
        lines = _basic_report_lines(report, chart_a, chart_b, name_a, name_b)

    if generation_date:
        lines.append(f"\n*Generated on {generation_date}.*")

    md = "\n".join(lines).rstrip() + "\n"

    # Plain-language layer: gloss jargon on first prose use, then a tier-scaled
    # "What the Terms Mean" section after the Closing Note.
    from .plain_glossary import collect_used_terms, gloss_first_use, render_terms_section

    md = gloss_first_use(md, set())
    terms = render_terms_section(
        collect_used_terms(md), "compat_deep" if tier == "deep" else "compat"
    )
    if terms:
        md = md.rstrip() + "\n\n" + terms + "\n"
    return md


def _basic_report_lines(
    report: CompatReport,
    chart_a: Chart,
    chart_b: Chart,
    name_a: str,
    name_b: str,
) -> List[str]:
    """Compact ~4-page compatibility snapshot (the basic product)."""
    lines: List[str] = []
    lines.extend(_cover(report, name_a, name_b))

    lines.append("## Compatibility at a Glance")
    lines.append("")
    lines.append(f"| Pillar | {name_a} | {name_b} |")
    lines.append("|---|---|---|")
    for label, pa, pb in [
        ("Year", chart_a.year, chart_b.year),
        ("Month", chart_a.month, chart_b.month),
        ("Day", chart_a.day, chart_b.day),
        ("Hour", chart_a.hour, chart_b.hour),
    ]:
        lines.append(f"| {label} | {pa.combined} | {pb.combined} |")
    lines.append("")

    lines.extend(_verdict_block(report))
    lines.extend(_verdict_narrative(report))
    lines.extend(_couple_narrative(report, name_a, name_b))
    lines.append("")
    lines.append(_plain_words_verdict(report))
    lines.append("")

    lines.append("## Key Sub-Systems")
    lines.append("")
    lines.append(
        "The verdict table above lists all eleven sub-systems. The four below "
        "are the ones that most strongly shape day-to-day married life."
    )
    lines.append("")

    lines.extend(_sub_system_block(
        "Day-Branch Interaction (the heart of compatibility)", "일지 합충형파해",
        report.daybranch,
        "see knowledge/11-gunghap.md §B",
        compact=True,
    ))
    lines.extend(_sub_system_block(
        "Day-Stem Combination", "일간합 (天干合)",
        report.daystem_combo,
        "see knowledge/11-gunghap.md §A",
        compact=True,
    ))
    lines.extend(_sub_system_block(
        "Favorable Element Cross-Supply", "용신 궁합 (用神 宮合)",
        report.yongshin,
        "see knowledge/11-gunghap.md §D",
        compact=True,
    ))
    lines.extend(_sub_system_block(
        "Yin-Yang Polarity", "음양 조화 (陰陽 調和)",
        report.yin_yang,
        "see knowledge/11-gunghap.md §J",
        compact=True,
    ))
    lines.append("")
    lines.append(_plain_words_daymaster_cross(report))
    lines.append("")

    lines.extend(_daeun_callout(report))

    lines.append("## Practical Guidance")
    lines.append("")
    bullets: List[str] = _compact_guidance_bullets(report, name_a, name_b)
    for b in bullets[:4]:
        lines.append(f"- {b}")
    lines.append("")

    lines.extend(_closing_note(report, name_a, name_b))
    lines.extend(_next_steps(name_a, name_b, compact=True))
    return lines


def _deep_report_lines(
    report: CompatReport,
    chart_a: Chart,
    chart_b: Chart,
    name_a: str,
    name_b: str,
) -> List[str]:
    """Full compatibility report with all eleven sub-systems and timing overlay."""
    lines: List[str] = []
    lines.extend(_cover(report, name_a, name_b))

    lines.append("## Compatibility at a Glance (한눈에 보기)")
    lines.append("")
    lines.extend(_glance_table(chart_a, name_a))
    lines.extend(_glance_table(chart_b, name_b))

    lines.extend(_verdict_block(report))
    lines.extend(_verdict_narrative(report))
    lines.extend(_couple_narrative(report, name_a, name_b))
    lines.append("")
    lines.append(_plain_words_verdict(report))
    lines.append("")

    # Sub-systems in classical order A→K.
    lines.extend(_sub_system_block(
        "Day-Stem Combination", "일간합 (天干合)",
        report.daystem_combo,
        "see knowledge/11-gunghap.md §A",
    ))
    lines.extend(_sub_system_block(
        "Day-Branch Interaction (the heart of 궁합)", "일지 합충형파해",
        report.daybranch,
        "see knowledge/11-gunghap.md §B",
    ))
    lines.append("")
    lines.append(_plain_words_daymaster_cross(report))
    lines.append("")
    lines.extend(_sub_system_block(
        "Nayin Harmony", "납음오행 (納音五行)",
        report.nayin,
        "see knowledge/11-gunghap.md §C",
    ))
    lines.extend(_sub_system_block(
        "Favorable Element Cross-Supply", "용신 궁합 (用神 宮合)",
        report.yongshin,
        "see knowledge/11-gunghap.md §D",
    ))
    lines.extend(_sub_system_block(
        "Day-Pillar Pair Classification", "일주 궁합 (日柱 宮合)",
        report.ilju_pair,
        "see knowledge/11-gunghap.md §E",
    ))
    lines.extend(_sub_system_block(
        "Combined Element Balance", "결합 오행 (結合 五行)",
        report.combined_elements,
        "see knowledge/11-gunghap.md §F",
    ))
    lines.extend(_sub_system_block(
        "Ten-God Cross-Relationship", "십신 교차 (十神 交叉)",
        report.tengod_cross,
        "see knowledge/11-gunghap.md §G",
    ))
    # Daeun callout leads into §H so the divergence is surfaced up front.
    lines.extend(_daeun_callout(report))
    lines.extend(_sub_system_block(
        "Major Luck Synchrony", "대운·세운 동기 (大運·歲運 同期)",
        report.daeun_sync,
        "see knowledge/11-gunghap.md §H",
    ))
    lines.extend(_sub_system_block(
        "Compatibility Star Overlays", "신살 궁합 (神殺 宮合)",
        report.compat_stars,
        "see knowledge/11-gunghap.md §I",
    ))
    lines.extend(_sub_system_block(
        "Yin-Yang Polarity", "음양 조화 (陰陽 調和)",
        report.yin_yang,
        "see knowledge/11-gunghap.md §J",
    ))
    lines.extend(_sub_system_block(
        "Year-Branch Zodiac Pair (띠)", "띠 궁합 (支 宮合)",
        report.year_branch,
        "see knowledge/11-gunghap.md §K",
    ))

    lines.extend(_deep_sections(report, name_a, name_b))
    lines.append("")
    lines.append(_plain_words_timing(report))
    lines.append("")
    lines.extend(_practical_guidance(report, name_a, name_b))
    lines.extend(_closing_note(report, name_a, name_b))
    lines.extend(_next_steps(name_a, name_b))
    return lines


def _compact_guidance_bullets(report: CompatReport, name_a: str, name_b: str) -> List[str]:
    """Condensed practical guidance for the basic tier."""
    bullets: List[str] = []
    a, b = report.chart_a, report.chart_b
    if report.yongshin.score >= 6:
        bullets.append(
            f"**Shared lucky element.** {name_a} and {name_b}'s charts strongly "
            "cross-supply the favorable element — build environments and seasons "
            "that activate it for both of you at once."
        )
    if a.day.stem == b.day.stem:
        bullets.append(
            f"**Peer dynamic.** You share the same Day Master — easy and familiar, "
            "but guard against sibling-style competition. Take turns leading."
        )
    db_flags = " ".join(report.daybranch.flags)
    if "RED FLAG" in db_flags or any("육충" in f for f in report.daybranch.flags):
        bullets.append(
            "**Day-branch clash is present.** Use explicit communication rhythms — "
            "a regular check-in works better than ad-hoc conflict resolution."
        )
    elif any("육합" in f for f in report.daybranch.flags):
        bullets.append(
            "**Day-branch combination is present.** Reinforce it with shared rituals "
            "(meals, weekly time together, annual traditions)."
        )
    if any("방향 상이" in f for f in report.daeun_sync.flags):
        bullets.append(
            "**Timing divergence.** Your major-luck phases run on different tracks — "
            "overlay both annual-luck charts before big joint decisions."
        )
    if not bullets:
        bullets.append(
            "No strong red flags surfaced. Use the natural ease to invest in "
            "long-term structure: finances, family, and mutual support."
        )
    return bullets


__all__ = ["generate_compat_report"]
