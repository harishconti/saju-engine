"""Seeded random coverage: nothing the engine can emit may reach the client PDF
as unmapped (garbled / untranslated) CJK.

Runs the exact HTML-path pipeline (strip citations + engine drafts, then the
renderer's translation with keep_unmapped=True) over random charts and pairs.
"""
import random
import re

import pytest

from saju_engine.compat_report import generate_compat_report
from saju_engine.engine import compute_chart
from saju_engine.premium_report import generate_premium_report
from saju_html import strip_engine_drafts, strip_source_citations, translate_inline

# Documented, intentionally unmapped strings (none at present).
KNOWN_GAPS: set = set()

_ZONES = [(9.0, 127.0), (5.5, 77.2), (-5.0, -74.0), (-8.0, -118.2), (0.0, 0.0)]
_CJK = re.compile(r"[가-힣一-鿿]+")


def _chart(rng, gender):
    utc, lon = rng.choice(_ZONES)
    return compute_chart(
        name="X", gender=gender, year=rng.randint(1940, 2010),
        month=rng.randint(1, 12), day=rng.randint(1, 28),
        hour=rng.randint(0, 23), minute=rng.randint(0, 59),
        city=None, longitude=lon, utc_offset=utc,
        use_solar_time=rng.random() < 0.7, convention="korean",
    )


def _residuals(md: str) -> set:
    md = strip_engine_drafts(strip_source_citations(md))
    unmapped: set = set()
    out = translate_inline(md, keep_unmapped=True, unmapped=unmapped)
    runs = set()
    if unmapped:
        runs = {r for r in _CJK.findall(out)}
    return runs - KNOWN_GAPS


def test_random_compat_has_no_unmapped_cjk():
    rng = random.Random(20261004)
    bad: dict = {}
    for _ in range(40):
        a, b = _chart(rng, "M"), _chart(rng, "F")
        for tier in ("deep", "basic"):
            for r in _residuals(generate_compat_report(a, b, "A", "B", tier=tier)):
                bad.setdefault(r, tier)
    assert not bad, f"unmapped CJK in compat reports: {sorted(bad)}"


@pytest.mark.parametrize("tier", ["sample", "essential", "deep", "career", "luck-cycle"])
def test_random_premium_has_no_unmapped_cjk(tier):
    rng = random.Random(77)
    bad: set = set()
    for _ in range(8):
        chart = _chart(rng, rng.choice("MF"))
        bad |= _residuals(generate_premium_report(chart, tier=tier, generation_date=None))
    assert not bad, f"unmapped CJK in {tier} reports: {sorted(bad)}"
