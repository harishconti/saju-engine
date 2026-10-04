"""Backend-neutral chart -> tier-markdown step shared by both PDF backends.

Both ``md_to_saju_pdf.build_pdf_from_chart`` (ReportLab) and
``md_to_saju_html_pdf`` (HTML/Chromium) turn a computed ``Chart`` into the
same intermediate markdown, then render it. Keeping that step here (no
reportlab import at module level) means the HTML backend does not depend on
ReportLab when a ``tier`` is given; only the tier-less legacy path lazily
imports it.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Optional

from saju_engine.cli_validators import utc_offset_float

_MONTH_NAME = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December",
}

TIER_CHOICES = ["sample", "essential", "deep", "spark", "reading", "fullmap", "career", "luck-cycle"]


def _format_date_dob(chart) -> str:
    """Format a Chart's birth_date as a presentable '11 December 1993' string."""
    try:
        y, m, d = chart.birth_date.split("-")
        return f"{int(d)} {_MONTH_NAME[int(m)]} {y}"
    except (ValueError, AttributeError):
        return str(chart.birth_date)


def _format_day_master(chart) -> str:
    """Return '丙 (Yang Fire)' style label from a Chart."""
    info = chart.day_master_info
    return f"{chart.day_master} ({info['element']}, {info['polarity']})"


def _slugify(name: str) -> str:
    """Create a lowercase, hyphenated slug from a full name."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def chart_markdown(chart, tier: Optional[str] = None, *, title: str = "Saju Reading") -> str:
    """Markdown for ``chart``: the premium generator when ``tier`` is given,
    else the legacy ``chart_to_markdown`` template."""
    if tier:
        from saju_engine.premium_report import generate_premium_report
        return generate_premium_report(chart, tier=tier, generation_date=None)
    from saju_html.md_to_saju_pdf import chart_to_markdown  # lazy: this tier-less legacy path imports reportlab
    return chart_to_markdown(chart, title=title)


def prepare_chart_render(chart, output_pdf: Path, *, title: str = "Saju Reading",
                         client: str = "", dob: str = "", day_master: str = "",
                         overwrite_report: bool = False, tier: Optional[str] = None,
                         report_id: str = "") -> dict:
    """Write the intermediate markdown next to ``output_pdf`` and return the
    kwargs (``input_md``, ``client``, ``dob``, ``day_master``, ``report_id``)
    a backend needs to render it.

    By default the markdown goes to ``{name}-engine.md`` so a hand-written
    ``{name}-report.md`` is never overwritten; ``overwrite_report=True``
    writes ``{pdf stem}.md`` instead.
    """
    output_pdf = Path(output_pdf)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    client = client or chart.name or ""
    dob = dob or _format_date_dob(chart)
    day_master = day_master or _format_day_master(chart)

    if overwrite_report:
        md_path = output_pdf.with_suffix(".md")
    else:
        md_path = output_pdf.with_name(output_pdf.stem.replace("-report", "-engine", 1) + ".md")
        if md_path.name == output_pdf.with_suffix(".md").name:
            md_path = output_pdf.with_name(output_pdf.stem + "-engine.md")
    md_path.write_text(chart_markdown(chart, tier, title=title), encoding="utf-8")

    if not report_id:
        slug = _slugify(client or chart.name or output_pdf.stem)
        report_id = f"CID-{slug}-{date.today().strftime('%Y%m%d')}-{(tier or '').upper()}"
    return {"input_md": md_path, "client": client, "dob": dob,
            "day_master": day_master, "report_id": report_id}


def add_chart_args(ap) -> None:
    """Register the ``--from-chart`` birth-data flags on an argparse parser."""
    ap.add_argument("--from-chart", action="store_true",
                    help="Build PDF from a Chart computed by the engine (provide --birth-* flags).")
    ap.add_argument("--name", default="")
    ap.add_argument("--gender", choices=["M", "F"], default=None)
    ap.add_argument("--birth-year", type=int)
    ap.add_argument("--birth-month", type=int)
    ap.add_argument("--birth-day", type=int)
    ap.add_argument("--birth-hour", type=int)
    ap.add_argument("--birth-minute", type=int, default=0)
    ap.add_argument("--city", default="")
    ap.add_argument("--longitude", type=float, default=None)
    ap.add_argument("--utc-offset", type=utc_offset_float, default=9.0)
    ap.add_argument("--no-solar-time", dest="use_solar_time", action="store_false", default=True,
                    help="Disable true solar-time correction (enabled by default).")
    ap.add_argument("--convention", choices=["korean", "chinese"], default="korean",
                    help="Korean (야자시, default) or Chinese (조자시) Zi-hour convention.")
    # Legacy aliases kept for backward compatibility.
    ap.add_argument("--korean-yazi", action="store_true", default=None,
                    help="Deprecated alias for --convention korean.")
    ap.add_argument("--no-korean-yazi", dest="korean_yazi", action="store_false")
    ap.add_argument("--overwrite-report", action="store_true",
                    help="When using --from-chart, write the markdown to {name}-report.md instead of {name}-engine.md.")


def chart_from_args(ap, args):
    """Compute the Chart described by the ``add_chart_args`` flags."""
    if not all([args.birth_year, args.birth_month, args.birth_day, args.birth_hour is not None]):
        ap.error("--from-chart requires --birth-year, --birth-month, --birth-day, --birth-hour")
    from saju_engine.engine import compute_chart
    convention = args.convention
    if args.korean_yazi is not None:
        convention = "korean" if args.korean_yazi else "chinese"
    return compute_chart(
        name=args.name or None, gender=args.gender,
        year=args.birth_year, month=args.birth_month, day=args.birth_day,
        hour=args.birth_hour, minute=args.birth_minute,
        city=args.city or None, longitude=args.longitude,
        utc_offset=args.utc_offset, use_solar_time=args.use_solar_time,
        convention=convention,
    )
