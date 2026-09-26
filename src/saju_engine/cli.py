"""Command-line interface for the Saju engine.

Examples:
    python -m saju_engine --date 1993-12-11 --time 02:45 --city Pallipat --gender F
    python -m saju_engine --date 1991-10-03 --time 23:45 --longitude 79.19 --utc-offset 5.5 --gender M --format json
    python -m saju_engine --date 1993-12-11 --time 02:45 --longitude 79.32 --gender F --format skeleton --year 2026 --focus "career"
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

from .cli_validators import utc_offset_float
from .engine import compute_chart
from .premium_report import generate_premium_report
from .skeleton import generate_skeleton


class _HelpfulParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"error: {message}\n\n")
        self.print_help()
        sys.exit(2)


def _parse_date(s: str) -> tuple[int, int, int]:
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.year, dt.month, dt.day
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"date must be YYYY-MM-DD, got {s!r}") from exc


def _parse_time(s: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(s, "%H:%M")
        return dt.hour, dt.minute
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"time must be HH:MM, got {s!r}") from exc


def _positive_int(s: str) -> int:
    try:
        v = int(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {s!r}") from exc
    if v <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {v}")
    return v


def _month_int(s: str) -> int:
    try:
        v = int(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"month must be 1-12, got {s!r}") from exc
    if not 1 <= v <= 12:
        raise argparse.ArgumentTypeError(f"month must be 1-12, got {v}")
    return v


def _day_int(s: str) -> int:
    try:
        v = int(s)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"day must be 1-31, got {s!r}") from exc
    if not 1 <= v <= 31:
        raise argparse.ArgumentTypeError(f"day must be 1-31, got {v}")
    return v


def _build_parser() -> argparse.ArgumentParser:
    ap = _HelpfulParser(
        prog="saju-engine",
        description="Compute a Korean Saju (Four Pillars of Destiny) chart.",
    )
    ap.add_argument("--date", required=True, type=_parse_date,
                    help="Birth date as YYYY-MM-DD.")
    ap.add_argument("--time", required=True, type=_parse_time,
                    help="Birth time as HH:MM (24-hour clock).")
    ap.add_argument("--gender", choices=["M", "F"], default=None,
                    help="Gender (M/F). Needed for major-luck (대운) direction.")
    ap.add_argument("--city", default=None,
                    help="Birth city for longitude geocoding (e.g., 'Pallipat').")
    ap.add_argument("--longitude", type=float, default=None,
                    help="Birth longitude in decimal degrees (east positive). Overrides city.")
    ap.add_argument("--utc-offset", type=utc_offset_float, default=None,
                    help="UTC offset in hours (required; e.g. 5.5 for India, 9 for Korea). Range [-12, 14].")
    ap.add_argument("--no-solar-time", dest="use_solar_time", action="store_false",
                    default=True, help="Disable true solar-time correction.")
    ap.add_argument("--convention", choices=["korean", "chinese"], default="korean",
                    help="Zi-hour convention: korean (야자시, default) or chinese (조자시).")
    ap.add_argument("--star-anchor", choices=["day", "year"], default="day",
                    help="Branch the 12신살 (and 도화/역마/화개) are counted from: day (default, common "
                         "modern practice) or year (traditional Korean basis).")
    ap.add_argument("--name", default=None, help="Candidate name (optional).")
    ap.add_argument("--format", choices=["json", "table", "skeleton", "premium"], default="table",
                    help="Output format (default table; skeleton/premium = engine-driven markdown).")
    ap.add_argument("--tier", choices=["sample", "essential", "deep", "companion", "spark", "reading", "fullmap"], default="essential",
                    help="Premium report tier (default essential; used only with --format premium). Compat tier is API-only — use generate_compat_report.")
    ap.add_argument("--favorable-override", default=None,
                    choices=["Wood", "Fire", "Earth", "Metal", "Water"],
                    help="Override the engine's heuristic 용신 with a reader-argued favorable element "
                         "(used only with --format premium; keeps the report consistent with a "
                         "hand-crafted natal reading).")
    ap.add_argument("--year", type=int, default=None,
                    help="Reference year for the annual-luck window in skeleton output.")
    ap.add_argument("--month", type=_month_int, default=None,
                    help="Reference month for the monthly-luck window in skeleton output (1-12).")
    ap.add_argument("--day", type=_day_int, default=None,
                    help="Reference day for the daily-luck window in skeleton output (1-31).")
    ap.add_argument("--daeun-periods", type=_positive_int, default=8,
                    help="Number of major-luck (대운) periods to generate (default 8; must be positive).")
    ap.add_argument("--focus", default=None,
                    help="Focus of the question (used only in skeleton output).")
    ap.add_argument("--no-prose-scaffold", dest="include_prose_scaffold",
                    action="store_false", default=True,
                    help="Disable the engine-drafted interpretive prose scaffold in skeleton output.")
    ap.add_argument("--output-file", default=None,
                    help="If given with --format skeleton/premium, write output to this file instead of stdout.")
    ap.add_argument("--skeleton-file", default=None, dest="output_file",
                    help="Deprecated alias for --output-file. Emits a warning to stderr.")
    return ap


def _deprecated_skeleton_file_used(argv: list[str] | None) -> bool:
    """Return True if the deprecated --skeleton-file flag appears in argv."""
    if argv is None:
        argv = sys.argv[1:]
    return any(a == "--skeleton-file" for a in argv)


def _table(chart) -> str:
    lines = [
        f"Name:        {chart.name or '-'}",
        f"Gender:      {chart.gender or '-'}",
        f"Born:        {chart.birth_date} {chart.birth_time}",
    ]
    if chart.effective_date and chart.effective_date != chart.birth_date:
        lines.append(f"Effective:   {chart.effective_date}  (day-pillar date after solar/zi adjustment)")
    lines.extend([
        f"Location:    {chart.city or '-'}  lon={chart.longitude or '-'}  convention={chart.convention}",
        "",
        "Four Pillars:",
        "  Year   Month   Day     Hour",
        f"  {chart.year.combined:<6}  {chart.month.combined:<6}  {chart.day.combined:<6}  {chart.hour.combined:<6}",
        "",
        f"Day Master:  {chart.day_master} ({chart.day_master_info.get('element')} {chart.day_master_info.get('polarity')})",
        "",
        "Major Luck Periods (대운):",
    ])
    for p in chart.daeun:
        lines.append(f"  Ages {p.start_age:2d}-{p.end_age:2d}: {p.combined}")
    lines.append("")
    lines.append("Strength heuristic:")
    if chart.strength_assessment:
        lines.append(f"  Verdict: {chart.strength_assessment['verdict']}")
        lines.append(f"  Favorable candidate: {chart.strength_assessment['candidate_favorable']}")
    return "\n".join(lines)


def _run(args, stdout, stderr, *, deprecated_alias_used: bool = False) -> int:
    """Execute the requested command; write output to the provided streams."""
    if args.utc_offset is None:
        raise SystemExit("--utc-offset is required (e.g. 5.5 for India, 9 for Korea)")

    year, month, day = args.date
    hour, minute = args.time

    if args.format in ("premium", "skeleton") and args.gender is None:
        raise SystemExit(
            f"--gender is required for --format {args.format} (대운 direction depends on gender)"
        )

    try:
        chart = compute_chart(
            name=args.name,
            gender=args.gender,
            year=year, month=month, day=day,
            hour=hour, minute=minute,
            city=args.city,
            longitude=args.longitude,
            utc_offset=args.utc_offset,
            use_solar_time=args.use_solar_time,
            convention=args.convention,
            n_periods=args.daeun_periods,
            reference_year=args.year,
            reference_month=args.month,
            reference_day=args.day,
            star_anchor=args.star_anchor,
        )
    except ValueError as exc:
        raise SystemExit(str(exc))

    if deprecated_alias_used:
        stderr.write(
            "Warning: --skeleton-file is deprecated; use --output-file instead.\n"
        )

    if args.format == "json":
        stdout.write(chart.to_json() + "\n")
    elif args.format == "skeleton":
        ref = chart.reference_date_obj() or datetime.now().date()
        ref_year = args.year or ref.year
        ref_month = args.month or ref.month
        ref_day = args.day or ref.day
        skeleton = generate_skeleton(
            chart, focus=args.focus,
            reference_year=ref_year, reference_month=ref_month, reference_day=ref_day,
            include_prose_scaffold=args.include_prose_scaffold,
        )
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(skeleton)
            stdout.write(f"Skeleton written to {args.output_file}\n")
        else:
            stdout.write(skeleton + "\n")
    elif args.format == "premium":
        premium = generate_premium_report(
            chart, tier=args.tier, favorable_override=args.favorable_override
        )
        if args.output_file:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(premium)
            stdout.write(f"Premium report written to {args.output_file}\n")
        else:
            stdout.write(premium + "\n")
    else:
        stdout.write(_table(chart) + "\n")
    return 0


def main(argv: list[str] | None = None, *, stdout=None, stderr=None) -> int:
    """Parse arguments and run the requested command.

    Returns an integer exit code. Does not call ``sys.exit()`` itself, so
    callers can unit-test by passing ``io.StringIO`` streams and inspecting
    the return value.
    """
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr

    ap = _build_parser()
    args = ap.parse_args(argv)

    try:
        return _run(
            args, stdout, stderr,
            deprecated_alias_used=_deprecated_skeleton_file_used(argv),
        )
    except SystemExit as exc:
        if isinstance(exc.code, str) and exc.code:
            stderr.write(f"error: {exc.code}\n")
            ap.print_help(stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive
        stderr.write(f"unexpected error: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
