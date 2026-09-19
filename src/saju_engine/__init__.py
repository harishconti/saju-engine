"""Saju calculation engine.

A Python module that takes a Gregorian birth date/time/location and returns
a fully-derived Saju chart (four pillars + 십신 + 12운성 + 대운 sequence +
Day Master strength + 용신).

Modules:
    pillars  — four-pillar computation (wraps sajupy)
    lookup   — 십신 / 12운성 / hidden stems / branch relationships
    chart    — dataclasses for the chart
    daeun    — major-luck sequence computation
    engine   — top-level orchestrator
    validate — test suite (run as a script)

Plus:
    compat         — two-chart compatibility (궁합) engine
    compat_report  — standalone 궁합 markdown report generator
    nayin          — Nayin (납음오행) 60-jiazi → 30-pair table
"""
from .engine import compute_chart
from .chart import Chart, Pillar, TenGodHit, DaeunPeriod
from .premium_report import generate_premium_report, normalize_tier
from .compat import compat_score, CompatReport, CompatSubResult
from .compat_report import generate_compat_report
from .nayin import nayin_of, nayin_relation, nayin_element_of

try:
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
    try:
        __version__ = _pkg_version("saju-engine")
    except PackageNotFoundError:
        __version__ = "0.0.0+unknown"
except ImportError:  # pragma: no cover - py<3.8
    __version__ = "0.0.0+unknown"

__all__ = [
    "compute_chart",
    "Chart",
    "Pillar",
    "TenGodHit",
    "DaeunPeriod",
    "generate_premium_report",
    "normalize_tier",
    "compat_score",
    "CompatReport",
    "CompatSubResult",
    "generate_compat_report",
    "nayin_of",
    "nayin_relation",
    "nayin_element_of",
    "__version__",
]