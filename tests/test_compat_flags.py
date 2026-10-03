"""S6 (2026-10-01 audit): compat flags were classified by substring-matching
their prose. They now carry their classification as data. This test pins that
the typed classification equals the legacy substring classification for every
flag the engine emits on a spread of real chart pairs, and that no consumer
needs the substring path any more."""
import itertools

import pytest

from saju_engine import compat
from saju_engine.engine import compute_chart

BIRTHS = [
    (1917, 11, 14, 10, "M", 9.0, 128.74), (1946, 9, 1, 8, "M", 9.0, 128.74),
    (1990, 6, 15, 10, "F", -5.0, -74.0), (1985, 12, 20, 6, "F", 9.0, 126.98),
    (1992, 3, 20, 14, "F", 9.0, 127.0), (1978, 4, 2, 23, "M", 9.0, 127.0),
    (2001, 8, 8, 8, "F", 5.5, 77.2), (1965, 1, 30, 4, "M", 9.0, 129.0),
]
CHARTS = [compute_chart(year=y, month=m, day=d, hour=h, minute=0, gender=g,
                        utc_offset=o, longitude=lon, reference_year=2026,
                        reference_month=6, reference_day=1)
          for y, m, d, h, g, o, lon in BIRTHS]
PAIRS = list(itertools.combinations(range(len(CHARTS)), 2))


# P2 Task 7 (user decision 2026-10-03): the ONLY codes whose typed
# (kind, severity) deliberately differ from the legacy substring oracle.
#   cross/year 육충 and cross 자형: severity = the flag's actual score delta
#   (-5 / -3 / -2) instead of the substring token's 25 / 25 / 8.
#   primary 육해/육파: now on the cover's yellow (caution) list.
#   direction_differs: no longer a "favorable" highlight.
DEVIATIONS = {
    "daybranch.cross_clash": ("red", 5),
    "year_branch.clash": ("red", 3),
    "daybranch.cross_self_punish": ("red", 2),
    "daybranch.harm": ("yellow", 0),
    "daybranch.break": ("yellow", 0),
    "daeun_sync.direction_differs": (None, 0),
}


def _all_flags(report):
    for sub in report.sub_systems():
        yield from sub.flags


@pytest.mark.parametrize("i,j", PAIRS)
def test_every_flag_is_typed_and_matches_legacy_classification(i, j):
    report = compat.compat_score(CHARTS[i], CHARTS[j])
    for flag in _all_flags(report):
        assert isinstance(flag, compat.Flag), repr(flag)
        if flag.code in DEVIATIONS:
            assert (flag.kind, flag.severity) == DEVIATIONS[flag.code], flag
            continue
        assert flag.kind == compat._legacy_classify_flag(str(flag)), flag
        assert flag.severity == compat._legacy_flag_severity(str(flag)), flag
        assert flag.code


def _report(i=0, j=2):
    return compat.compat_score(CHARTS[i], CHARTS[j])


def test_flag_survives_pickle_copy_asdict():
    import copy
    import dataclasses
    import pickle
    report = _report()
    flags = list(_all_flags(report))
    assert flags
    for f in flags:
        g = pickle.loads(pickle.dumps(f))
        assert isinstance(g, compat.Flag)
        assert (str(g), g.kind, g.code, g.severity) == (str(f), f.kind, f.code, f.severity)
    clone = copy.deepcopy(report)
    assert [(str(f), f.kind, f.code, f.severity) for f in _all_flags(clone)] == \
        [(str(f), f.kind, f.code, f.severity) for f in flags]
    assert all(isinstance(f, compat.Flag) for f in _all_flags(clone))
    assert dataclasses.asdict(report.daybranch)["flags"] is not None
