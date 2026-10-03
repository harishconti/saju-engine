"""Validation harness shared library (W1–W6 campaign).

Loads cited ground-truth fixtures and checks engine output against them.
Three check statuses per the validation spec:
PASS (engine matches ground truth), INTERPRETATION (engine follows the cited
classical rule; external source differs by school/method — documented, not a
failure), FAIL (engine bug or unsupported rule — logged for later fixing).
See the 2026-09 validation campaign design (removed 2026-10-01).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_FIXTURES_DIR = _REPO_ROOT / "tests" / "validation" / "fixtures"
_VALID_ENTRY_STATUS = {"expect_match", "documented_interpretation"}


def load_fixtures(subsystem: str, fixtures_dir: Optional[Path] = None) -> list[dict]:
    """Load and schema-check fixtures for one subsystem.

    Returns the list of fixture entries. Raises FileNotFoundError when the
    subsystem file does not exist and ValueError on schema violations.
    """
    path = (fixtures_dir or _DEFAULT_FIXTURES_DIR) / f"{subsystem}.json"
    if not path.is_file():
        raise FileNotFoundError(f"unknown validation subsystem: {path}")
    entries = json.loads(path.read_text(encoding="utf-8"))
    for entry in entries:
        missing = {"id", "subsystem", "input", "source", "expected", "status"} - set(entry)
        if missing:
            raise ValueError(f"{subsystem}: entry missing keys {sorted(missing)}")
        if entry["status"] not in _VALID_ENTRY_STATUS:
            raise ValueError(f"{subsystem}/{entry['id']}: invalid status {entry['status']!r}")
    return entries


from saju_engine.engine import compute_chart  # noqa: E402  (after loader defs; lazy use)
from saju_engine import climate, compat, lookup as L, nayin, report_data, stars, yongsin  # noqa: E402
from saju_engine.chart import Chart, Pillar  # noqa: E402  (pillars-only compat pairs)

_PILLAR_POSITIONS = ("year", "month", "day", "hour")
# compute_chart kwargs allowed in fixture "input"; anything else is a fixture bug.
_ALLOWED_INPUT = {
    "name", "year", "month", "day", "hour", "minute",
    "longitude", "utc_offset", "gender", "convention", "use_solar_time",
    "city", "early_zi_time", "korean_yazi", "n_periods",
    "reference_year", "reference_month", "reference_day",
}


def check_pillars(chart: Any, entry: dict) -> dict:
    """Check a computed Chart against a pillars fixture entry.

    Returns {"id", "status", "mismatches", "detail"} where status is
    PASS / INTERPRETATION / FAIL per the campaign spec. An expected field
    that is None (JSON null — ground truth not published) is skipped: not
    compared and never recorded as a mismatch.
    """
    expected = entry.get("expected", {}).get("pillars", {})
    got = {pos: getattr(chart, pos).combined for pos in expected}
    mismatches = {pos: {"expected": exp, "got": got[pos]}
                  for pos, exp in expected.items()
                  if exp is not None and got[pos] != exp}
    exp_corr = entry.get("expected", {}).get("solar_correction_minutes")
    if exp_corr is not None:
        actual = (chart.solar_correction or {}).get("correction_minutes", 0)
        if actual != exp_corr:
            mismatches["solar_correction_minutes"] = {"expected": exp_corr, "got": actual}
    exp_zi = entry.get("expected", {}).get("zi_time_type")
    if exp_zi is not None and chart.zi_time_type != exp_zi:
        mismatches["zi_time_type"] = {"expected": exp_zi, "got": chart.zi_time_type}
    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{pos}: expected {m['expected']}, got {m['got']}"
                       for pos, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def run_fixture(entry: dict) -> dict:
    """Compute the chart described by a fixture entry and check it.

    An input key that compute_chart does not accept is a fixture bug
    (e.g. a typo'd key would otherwise be silently ignored), so it raises.
    """
    unknown = set(entry["input"]) - _ALLOWED_INPUT
    if unknown:
        raise ValueError(
            f"{entry['subsystem']}/{entry['id']}: unknown input key(s) "
            f"{sorted(unknown)} — not accepted by compute_chart"
        )
    kwargs = {k: v for k, v in entry["input"].items() if k in _ALLOWED_INPUT}
    kwargs.setdefault("name", entry["id"])
    kwargs.setdefault("gender", None)
    chart = compute_chart(**kwargs)
    return check_pillars(chart, entry)


def _result(entry: dict, mismatches: dict) -> dict:
    """Turn a mismatches dict into the standard PASS/INTERPRETATION/FAIL result."""
    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def check_daeun(chart: Any, entry: dict) -> dict:
    """Check a computed Chart's major-luck (대운) table against a daeun fixture.

    Compares the first `len(expected.periods)` period pillars (the direction
    and sequence are encoded in the pillar order) and the starting age.
    `expected.start_age` (exact) and `expected.start_age_accept` (list of
    tolerated values, for Korean-vs-Western counting differences) are
    mutually exclusive; null/None means "not checked".
    """
    expected = entry.get("expected", {})
    exp_periods = expected.get("periods") or []
    mismatches: dict = {}

    got_periods = [f"{p.stem}{p.branch}" for p in chart.daeun]
    if len(got_periods) < len(exp_periods):
        mismatches["periods"] = {
            "expected": f">= {len(exp_periods)} periods",
            "got": f"{len(got_periods)} periods {got_periods}",
        }
    elif got_periods[: len(exp_periods)] != exp_periods:
        mismatches["periods"] = {"expected": exp_periods,
                                 "got": got_periods[: len(exp_periods)]}

    if chart.daeun:
        got_start = chart.daeun[0].start_age
    else:
        got_start = None
        if exp_periods:
            mismatches["daeun"] = {"expected": "non-empty daeun table", "got": "[]"}
    exp_start = expected.get("start_age")
    exp_accept = expected.get("start_age_accept")
    if exp_start is not None and got_start != exp_start:
        mismatches["start_age"] = {"expected": exp_start, "got": got_start}
    elif exp_accept is not None and got_start not in exp_accept:
        mismatches["start_age"] = {"expected": f"in {exp_accept}", "got": got_start}

    return _result(entry, mismatches)


def run_daeun_fixture(entry: dict) -> dict:
    """Compute the chart described by a daeun fixture entry and check its 대운 table.

    Same unknown-input-key guard as run_fixture. `gender` is REQUIRED in the
    input: the engine returns an empty daeun table without it, so an entry
    without gender is a fixture bug and raises.
    """
    unknown = set(entry["input"]) - _ALLOWED_INPUT
    if unknown:
        raise ValueError(
            f"{entry['subsystem']}/{entry['id']}: unknown input key(s) "
            f"{sorted(unknown)} — not accepted by compute_chart"
        )
    if "gender" not in entry["input"] or not entry["input"]["gender"]:
        raise ValueError(
            f"{entry['subsystem']}/{entry['id']}: daeun fixtures require a gender input "
            "(the engine returns an empty 대운 table without one)"
        )
    kwargs = {k: v for k, v in entry["input"].items() if k in _ALLOWED_INPUT}
    kwargs.setdefault("name", entry["id"])
    chart = compute_chart(**kwargs)
    return check_daeun(chart, entry)


def check_sewoon(chart: Any, entry: dict) -> dict:
    """Check a computed Chart's 세운/월운 window + current 대운 against a sewoon fixture.

    expected.annual:  {"year": Y, "pillar": "XX"} — the SeWoonHit for year Y in
                      chart.sewoon must have that combined pillar.
    expected.monthly: {"ym": YYYYMM, "pillar": "XX"} — the hit for synthetic YYYYMM
                      in chart.woon.
    expected.current_daeun: {"pillar": "XX"} — chart.current_daeun.combined.
    All three keys optional (null = not checked).
    """
    expected = entry.get("expected", {})
    mismatches: dict = {}

    exp_annual = expected.get("annual")
    if exp_annual:
        hit = next((h for h in chart.sewoon if h.year == exp_annual["year"]), None)
        got = hit.combined if hit else None
        if got != exp_annual["pillar"]:
            mismatches["annual"] = {"expected": exp_annual["pillar"], "got": got}

    exp_monthly = expected.get("monthly")
    if exp_monthly:
        hit = next((h for h in chart.woon if h.year == exp_monthly["ym"]), None)
        got = hit.combined if hit else None
        if got != exp_monthly["pillar"]:
            mismatches["monthly"] = {"expected": exp_monthly["pillar"], "got": got}

    exp_cur = expected.get("current_daeun")
    if exp_cur:
        got = chart.current_daeun.combined if chart.current_daeun else None
        if got != exp_cur["pillar"]:
            mismatches["current_daeun"] = {"expected": exp_cur["pillar"], "got": got}

    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def run_sewoon_fixture(entry: dict) -> dict:
    """Compute the chart with its reference-date windows and check 세운/월운/대운 window.

    Same unknown-input-key guard as run_fixture. At least one of
    expected.annual / expected.monthly / expected.current_daeun must be set —
    an entry expecting nothing is a fixture bug and raises.
    """
    unknown = set(entry["input"]) - _ALLOWED_INPUT
    if unknown:
        raise ValueError(
            f"{entry['subsystem']}/{entry['id']}: unknown input key(s) "
            f"{sorted(unknown)} — not accepted by compute_chart"
        )
    expected = entry.get("expected", {})
    if not any(expected.get(k) for k in ("annual", "monthly", "current_daeun")):
        raise ValueError(
            f"{entry['subsystem']}/{entry['id']}: sewoon fixtures must expect "
            "at least one of annual / monthly / current_daeun"
        )
    kwargs = {k: v for k, v in entry["input"].items() if k in _ALLOWED_INPUT}
    kwargs.setdefault("name", entry["id"])
    chart = compute_chart(**kwargs)
    return check_sewoon(chart, entry)


# Per lookup kind, the exact input-key set an entry must carry (fixture bug
# otherwise — the lookups subsystem never builds a chart, so there is no
# compute_chart-kwargs guard here, just a strict shape check).
_LOOKUPS_ALLOWED_INPUT = {
    "ten_god": {"lookup", "day_master"},
    "twelve_stage": {"lookup", "day_master"},
    "nayin": {"lookup", "nayin"},
    "xunkong": {"lookup", "xun_start"},
    "hidden_stems": {"lookup"},
}


def check_lookups(entry: dict) -> dict:
    """Check one lookup-table fixture entry against the engine's lookup API.

    Dispatches on entry["input"]["lookup"] (no compute_chart call):
      ten_god      → expected.gods: {stem: god} for ALL 10 stems of one Day Master
      twelve_stage → expected.stages: {branch: stage} for ALL 12 branches of one DM
      nayin        → expected.jiazi (the ONLY 2 jiazi mapping to this nayin)
                     + expected.element (nayin_element_of)
      xunkong      → expected.absent: the 2 void branches of one 旬 block,
                     checked against ALL 10 day pillars of that block
      hidden_stems → expected.stems: {branch: {"main": .., "middle": .. (opt),
                     "residual": .. (opt)}} for ALL 12 branches in one entry
                     (F-12, 2026-09-26 audit: no check kind existed for
                     L.HIDDEN_STEMS at all, so a repeat of E-2's 중기/여기
                     swap on the four storage/tomb branches would have been
                     invisible to this gate)

    stars._xun_kong is a private module function; the validation harness is the
    one documented consumer (no public 공망 surface exists yet — W3 validates
    the table directly rather than adding engine API).
    """
    kind = entry["input"]["lookup"]
    expected = entry.get("expected", {})
    mismatches: dict = {}

    if kind == "ten_god":
        dm = entry["input"]["day_master"]
        for stem, exp_god in expected["gods"].items():
            got = L.ten_god(dm, stem)
            if got != exp_god:
                mismatches[f"ten_god({dm},{stem})"] = {"expected": exp_god, "got": got}
    elif kind == "twelve_stage":
        dm = entry["input"]["day_master"]
        for branch, exp_stage in expected["stages"].items():
            got = L.twelve_stage(dm, branch)
            if got != exp_stage:
                mismatches[f"twelve_stage({dm},{branch})"] = {
                    "expected": exp_stage, "got": got}
    elif kind == "nayin":
        name = entry["input"]["nayin"]
        exp_pairs = sorted(tuple(p) for p in expected["jiazi"])
        got_pairs = sorted(k for k, v in nayin.JIAZI_TO_NAYIN.items() if v == name)
        if got_pairs != exp_pairs:
            mismatches["jiazi"] = {"expected": [list(p) for p in exp_pairs],
                                   "got": [list(p) for p in got_pairs]}
        exp_elem = expected["element"]
        got_elem = nayin.nayin_element_of(name)
        if got_elem != exp_elem:
            mismatches["element"] = {"expected": exp_elem, "got": got_elem}
    elif kind == "xunkong":
        start = entry["input"]["xun_start"]
        idx = L.JIAZI_CYCLE.index((start[0], start[1]))
        absent = expected["absent"]
        for p in L.JIAZI_CYCLE[idx: idx + 10]:
            got = stars._xun_kong(p[0], p[1])
            if got != absent:
                mismatches[f"xun_kong({p[0]}{p[1]})"] = {"expected": absent, "got": got}
    elif kind == "hidden_stems":
        for branch, exp_roles in expected["stems"].items():
            got_roles = L.HIDDEN_STEMS.get(branch, {})
            if got_roles != exp_roles:
                mismatches[f"hidden_stems({branch})"] = {"expected": exp_roles, "got": got_roles}
    else:
        raise ValueError(f"lookups/{entry['id']}: unknown lookup kind {kind!r}")

    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def run_lookups_fixture(entry: dict) -> dict:
    """Validate one lookup fixture entry's input shape, then check it.

    The input key set must EXACTLY match the kind's allowed keys — an extra
    or missing key is a fixture bug and raises (mirrors the unknown-input-key
    guards of run_fixture/run_daeun_fixture/run_sewoon_fixture).
    """
    kind = entry["input"].get("lookup")
    if kind not in _LOOKUPS_ALLOWED_INPUT:
        raise ValueError(f"lookups/{entry['id']}: unknown lookup kind {kind!r}")
    keys = set(entry["input"])
    if keys != _LOOKUPS_ALLOWED_INPUT[kind]:
        raise ValueError(
            f"lookups/{entry['id']}: input keys {sorted(keys)} must be exactly "
            f"{sorted(_LOOKUPS_ALLOWED_INPUT[kind])} for lookup kind {kind!r}"
        )
    return check_lookups(entry)


# compute_chart kwargs allowed in a yongsin fixture "input", plus the two
# reader-override channels the yongsin merge supports (yongsin.py): an explicit
# override= argument, and chart.strength_assessment["reader_override_favorable"]
# — the wiring compat.py:1344-1355 uses for reader-argued 용신.
_YONGSIN_EXTRA_INPUT = {"override", "reader_override_favorable"}

# climate fixture input guards, dispatched by entry["input"]["probe"].
# band:  chart-free — exactly these keys (mirrors _LOOKUPS_ALLOWED_INPUT).
# merge: chart-based — any compute_chart kwarg (mirrors run_yongsin_fixture).
_CLIMATE_BAND_INPUT = {"probe", "month_branch"}
_CLIMATE_MERGE_INPUT = _ALLOWED_INPUT | {"probe"}
_CLIMATE_ALLOWED_INPUT = {"band", "merge"}

# compat fixture input guards, dispatched by entry["input"]["probe"].
#
# A compat fixture describes a PAIR, so the birth-data keys are namespaced
# a_/b_ (partner A first, matching the client-facing convention). Two ways to
# build the pair:
#   charts="birth"   — a_/b_ compute_chart kwargs; the pair is computed.
#   charts="pillars" — pre-supplied pillars_a/dm_a/pillars_b/dm_b; no compute.
# The pillars form exists because only 7 of the 11 sub-systems are
# reproducible from pillars alone (see W6 fixture notes): it pins a sub-system
# whose rule reads nothing but the four pillars.
_COMPAT_A_KEYS = {"a_name", "a_year", "a_month", "a_day", "a_hour", "a_minute",
                  "a_longitude", "a_utc_offset", "a_gender", "a_use_solar_time",
                  "a_early_zi_time", "a_korean_yazi"}
_COMPAT_B_KEYS = {k.replace("a_", "b_", 1) for k in _COMPAT_A_KEYS}
_COMPAT_PILLAR_KEYS = {"pillars_a", "dm_a", "pillars_b", "dm_b"}
_COMPAT_CHART_INPUT = _COMPAT_A_KEYS | _COMPAT_B_KEYS | _COMPAT_PILLAR_KEYS | {"charts"}
# band is chart-free — exactly these keys (mirrors _CLIMATE_BAND_INPUT).
_COMPAT_BAND_INPUT = {"probe", "score"}
_COMPAT_SUBSYSTEM_INPUT = _COMPAT_CHART_INPUT | {"probe", "subsystem"}
_COMPAT_SCORE_INPUT = _COMPAT_CHART_INPUT | {"probe", "favorable_element_a",
                                             "favorable_element_b"}
_COMPAT_ALLOWED_PROBE = {"band", "subsystem", "score"}

# career fixture input guards, dispatched by entry["input"]["probe"] (Plan 6
# T3). Two probe kinds:
#   domain_map — chart-free, input keys EXACTLY _CAREER_MAP_INPUT. Pins
#                report_data._domain_element(domain) — the element -> industry
#                family mapping grounded in knowledge/12-career-and-vocation.md.
#   tiers      — chart-based, input keys a SUBSET of _CAREER_TIER_INPUT. Pins
#                report_data._career_tiers(chart): the IN-ORDER (tier, domain)
#                list and whether the "**Possible**" tier is reachable.
_CAREER_MAP_INPUT = {"probe", "domain"}
_CAREER_TIER_INPUT = _ALLOWED_INPUT | {"probe"}
_CAREER_ALLOWED_PROBE = {"domain_map", "tiers"}


def _compat_pair(entry: dict):
    """Build (chart_a, chart_b) from a compat fixture entry's chart source.

    charts="birth"   -> compute_chart(**a_*) / compute_chart(**b_*), the
                        a_/b_ prefix stripped. compute_chart is called with
                        exactly the namespaced keys the guard admitted, so a
                        fixture cannot smuggle an unvalidated kwarg through.
    charts="pillars" -> a Chart hand-built from pillars_{tag}/dm_{tag}: no
                        birth data, no solar-time correction, no strength
                        assessment. Used to pin sub-systems that read only the
                        four pillars.
    Anything else raises — a typo must not silently pick a chart source.
    """
    inp = entry["input"]
    kind = inp.get("charts")

    if kind == "pillars":
        def mk(tag: str) -> Chart:
            c = Chart()
            for pos in _PILLAR_POSITIONS:
                two = inp[f"pillars_{tag}"][pos]
                setattr(c, pos, Pillar(position=pos, stem=two[0], branch=two[1]))
            c.day_master = inp[f"dm_{tag}"]
            c.day_master_info = {}
            return c
        return mk("a"), mk("b")

    if kind == "birth":
        def mk(tag: str) -> Chart:
            kw = {k[len("a_"):]: v for k, v in inp.items()
                  if k.startswith(tag + "_")}
            kw.setdefault("name", f"{entry['id']}-{tag}")
            kw.setdefault("use_solar_time", True)
            return compute_chart(**kw)
        return mk("a"), mk("b")

    raise ValueError(f"compat/{entry['id']}: unknown charts source {kind!r}")


def _compat_outcome(entry: dict, mismatches: dict) -> dict:
    """PASS / INTERPRETATION / FAIL epilogue shared by the compat checkers.

    Status semantics identical to check_pillars: a mismatch on a
    documented_interpretation entry renders INTERPRETATION (a documented
    school divergence), not FAIL.
    """
    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def check_compat(entry: dict) -> dict:
    """Check compat._band_for() against a chart-free compat fixture entry.

    Expected key: "band". Pins the composite 0–100 band thresholds
    (knowledge/11-gunghap.md:959-978), including the two defensive edges
    outside the nominal range.
    """
    expected = entry.get("expected", {})
    got = compat._band_for(entry["input"]["score"])
    mismatches = {}
    if "band" in expected and got != expected["band"]:
        mismatches["band"] = {"expected": expected["band"], "got": got}
    return _compat_outcome(entry, mismatches)


def check_compat_subsystem(a: Chart, b: Chart, entry: dict) -> dict:
    """Check ONE sub-system's score for a pair.

    Expected key: "score" — the named sub-system's CompatSubResult.score.
    "label" is optional and pins the display label too. Deliberately narrow:
    a sub-system fixture should fail for exactly one reason.
    """
    name = entry["input"]["subsystem"]
    expected = entry.get("expected", {})
    sub = getattr(compat.compat_score(a, b), name)
    mismatches = {}
    if "score" in expected and sub.score != expected["score"]:
        mismatches[f"{name}.score"] = {"expected": expected["score"], "got": sub.score}
    if "label" in expected and sub.label != expected["label"]:
        mismatches[f"{name}.label"] = {"expected": expected["label"], "got": sub.label}
    return _compat_outcome(entry, mismatches)


def check_compat_score(a: Chart, b: Chart, entry: dict) -> dict:
    """Check the composite compat score, band, and any per-sub-system map.

    Expected keys: "score" (composite 0–100), "band", and "subsystems" — an
    optional {sub_system: score} map. The composite is an affine shift of the
    weighted sub-system total (50 + sum), not a weighted mean, so a
    sub-system map is what makes a composite mismatch diagnosable.

    The two ``favorable_element_*`` reader overrides are optional input keys
    (see ``_COMPAT_SCORE_INPUT``) and are forwarded verbatim. They are NOT
    re-guarded here: ``compat.compat_score`` already gates each on
    ``if favorable_element_a and a.strength_assessment:``, and a pillars-only
    chart has ``strength_assessment is None`` — so the override is silently
    dropped for that chart source (A7). Duplicating that rule here would
    create a second copy free to drift out of sync with the engine's.
    """
    expected = entry.get("expected", {})
    inp = entry.get("input", {})
    report = compat.compat_score(
        a, b,
        favorable_element_a=inp.get("favorable_element_a"),
        favorable_element_b=inp.get("favorable_element_b"),
    )
    mismatches = {}
    if "score" in expected and report.score != expected["score"]:
        mismatches["score"] = {"expected": expected["score"], "got": report.score}
    if "band" in expected and report.band != expected["band"]:
        mismatches["band"] = {"expected": expected["band"], "got": report.band}
    for name, exp in (expected.get("subsystems") or {}).items():
        got = getattr(report, name).score
        if got != exp:
            mismatches[f"subsystems.{name}"] = {"expected": exp, "got": got}
    return _compat_outcome(entry, mismatches)


def run_compat_fixture(entry: dict) -> dict:
    """Dispatch a compat fixture entry by its "probe" kind and check it.

    probe="band":      chart-free. Input keys must be EXACTLY
                       _COMPAT_BAND_INPUT.
    probe="subsystem": chart-based. Keys must be a SUBSET of
                       _COMPAT_SUBSYSTEM_INPUT (charts="birth" needs every
                       a_/b_ key; charts="pillars" needs every pillar key).
    probe="score":     chart-based. Keys must be a SUBSET of
                       _COMPAT_SCORE_INPUT; the two favorable_element_*
                       overrides are optional.
    An unrecognised (or missing) probe raises rather than silently
    defaulting — a typo must not degrade to a vacuous PASS.
    """
    inp = entry["input"]
    probe = inp.get("probe")
    if probe not in _COMPAT_ALLOWED_PROBE:
        raise ValueError(
            f"compat/{entry['id']}: unknown probe kind {probe!r} — "
            f"expected one of {sorted(_COMPAT_ALLOWED_PROBE)}"
        )
    if probe == "band":
        keys = set(inp)
        if keys != _COMPAT_BAND_INPUT:
            raise ValueError(
                f"compat/{entry['id']}: input keys {sorted(keys)} must be exactly "
                f"{sorted(_COMPAT_BAND_INPUT)} for probe kind 'band'"
            )
        return check_compat(entry)

    allowed = (_COMPAT_SUBSYSTEM_INPUT if probe == "subsystem"
               else _COMPAT_SCORE_INPUT)
    unknown = set(inp) - allowed
    if unknown:
        raise ValueError(
            f"compat/{entry['id']}: unknown input key(s) {sorted(unknown)} — "
            f"not accepted for probe kind {probe!r}"
        )
    if probe == "subsystem":
        name = inp["subsystem"]
        if name not in compat.WEIGHT:
            raise ValueError(
                f"compat/{entry['id']}: unknown sub-system {name!r} — "
                f"expected one of {sorted(compat.WEIGHT)}"
            )

    kind = inp.get("charts")
    if kind == "birth":
        missing = (_COMPAT_A_KEYS | _COMPAT_B_KEYS) - set(inp)
    elif kind == "pillars":
        missing = _COMPAT_PILLAR_KEYS - set(inp)
    else:
        raise ValueError(
            f"compat/{entry['id']}: unknown charts source {kind!r} — "
            f"expected 'birth' or 'pillars'"
        )
    if missing:
        raise ValueError(
            f"compat/{entry['id']}: charts={kind!r} requires {sorted(missing)}, "
            f"which the entry does not supply"
        )

    a, b = _compat_pair(entry)
    if probe == "subsystem":
        return check_compat_subsystem(a, b, entry)
    return check_compat_score(a, b, entry)


def _career_outcome(entry: dict, mismatches: dict) -> dict:
    """PASS / INTERPRETATION / FAIL epilogue shared by the career checkers.

    Mirrors _compat_outcome: a mismatch on a documented_interpretation entry
    renders INTERPRETATION (a documented school divergence), not FAIL.
    """
    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def check_career(entry: dict) -> dict:
    """Check report_data._domain_element() against a chart-free career fixture.

    Expected key: "element" — the element _domain_element resolves for the
    named domain (knowledge/12-career-and-vocation.md element -> industry
    families). The registry entry for the career subsystem, like check_compat
    is the registry entry for compat: the chart-free checker with the
    chart-based one kept separate, since the two probe kinds do not share a
    signature.

    MEMBERSHIP semantics, not null-skip: ``if "element" in expected``, so an
    expected value that IS null (None — a domain the keyword lists cannot
    classify) is compared rather than skipped. Two of the five KB12
    contradiction rows carry element=null on purpose; null-skip would let
    those rows pass vacuously forever.
    """
    expected = entry.get("expected", {})
    got = report_data._domain_element(entry["input"]["domain"])
    mismatches: dict = {}
    if "element" in expected and got != expected["element"]:
        mismatches["element"] = {"expected": expected["element"], "got": got}
    return _career_outcome(entry, mismatches)


def check_career_tiers(chart: Any, entry: dict) -> dict:
    """Check report_data._career_tiers() for one computed chart.

    Expected keys:
      "tiers"                  — list of {"tier", "domain"} pairs, compared IN
                                 ORDER against _career_tiers(chart). Pinning
                                 the order is the point: the pool is selected
                                 by Day Master element, not the resolved 용신,
                                 so a wrong pool shows up as a wrong ordering.
      "possible_tier_reachable" — optional boolean; true iff any row's tier is
                                 "**Possible**". Asserted with ``is not None``
                                 so a False value stays a real assertion.
    """
    expected = entry.get("expected", {})
    got = report_data._career_tiers(chart)
    got_pairs = [{"tier": t, "domain": d} for t, d, _, _ in got]
    mismatches: dict = {}
    exp_tiers = expected.get("tiers")
    if exp_tiers is not None and got_pairs != exp_tiers:
        mismatches["tiers"] = {"expected": exp_tiers, "got": got_pairs}
    exp_possible = expected.get("possible_tier_reachable")
    if exp_possible is not None:
        got_possible = any(t == "**Possible**" for t, _, _, _ in got)
        if got_possible != exp_possible:
            mismatches["possible_tier_reachable"] = {
                "expected": exp_possible, "got": got_possible}
    return _career_outcome(entry, mismatches)


def run_career_fixture(entry: dict) -> dict:
    """Dispatch a career fixture entry by its "probe" kind and check it.

    probe="domain_map": chart-free. Input keys must be EXACTLY
                        _CAREER_MAP_INPUT (mirrors the compat "band" probe).
    probe="tiers":      chart-based. Unknown input keys beyond
                        _CAREER_TIER_INPUT raise (mirrors run_yongsin_fixture).
    An unrecognised (or missing) probe raises rather than silently
    defaulting — a typo must not degrade to a vacuous PASS.
    """
    probe = entry["input"].get("probe")
    if probe not in _CAREER_ALLOWED_PROBE:
        raise ValueError(
            f"career/{entry['id']}: unknown probe kind {probe!r} — "
            f"expected one of {sorted(_CAREER_ALLOWED_PROBE)}"
        )
    if probe == "domain_map":
        keys = set(entry["input"])
        if keys != _CAREER_MAP_INPUT:
            raise ValueError(
                f"career/{entry['id']}: input keys {sorted(keys)} must be exactly "
                f"{sorted(_CAREER_MAP_INPUT)} for probe kind 'domain_map'"
            )
        return check_career(entry)
    unknown = set(entry["input"]) - _CAREER_TIER_INPUT
    if unknown:
        raise ValueError(
            f"career/{entry['id']}: unknown input key(s) {sorted(unknown)} — "
            f"not accepted by compute_chart"
        )
    kwargs = {k: v for k, v in entry["input"].items() if k in _ALLOWED_INPUT}
    kwargs.setdefault("name", entry["id"])
    chart = compute_chart(**kwargs)
    return check_career_tiers(chart, entry)


def check_yongsin(chart: Any, entry: dict) -> dict:
    """Check yongsin.favorable_element() against a yongsin fixture entry.

    Expected keys: "fe" (fields of FavorableElement: element, method,
    supporting, climate_band, climate_element, climate_agrees, confidence,
    remedy_dominant — None skips that field) and "strength" (chart.strength_assessment fields
    verdict / candidate_favorable, None skips). Status semantics identical
    to check_pillars: PASS / INTERPRETATION / FAIL.
    """
    expected = entry.get("expected", {})
    fe = yongsin.favorable_element(
        chart, override=entry["input"].get("override"))
    mismatches: dict = {}
    got_fe = {
        "element": fe.element, "method": fe.method, "supporting": fe.supporting,
        "climate_band": fe.climate_band, "climate_element": fe.climate_element,
        "climate_agrees": fe.climate_agrees, "confidence": fe.confidence,
        "remedy_dominant": fe.remedy_dominant, "climate_extreme": fe.climate_extreme,
    }
    for key, exp in (expected.get("fe") or {}).items():
        if exp is not None and got_fe[key] != exp:
            mismatches[f"fe.{key}"] = {"expected": exp, "got": got_fe[key]}
    exp_strength = expected.get("strength")
    if exp_strength:
        sa = chart.strength_assessment
        got_strength = {"verdict": sa["verdict"],
                        "candidate": sa["_raw_unresolved_favorable"]}
        for key, exp in exp_strength.items():
            if exp is not None and got_strength[key] != exp:
                mismatches[f"strength.{key}"] = {
                    "expected": exp, "got": got_strength[key]}
    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def run_yongsin_fixture(entry: dict) -> dict:
    """Compute the chart, apply the reader-override channel if present, check.

    override= is passed straight to yongsin.favorable_element;
    reader_override_favorable is injected into
    chart.strength_assessment before checking (compat.py wiring).
    Unknown input keys (beyond _ALLOWED_INPUT + _YONGSIN_EXTRA_INPUT) raise
    like the other runners.
    """
    unknown = set(entry["input"]) - (_ALLOWED_INPUT | _YONGSIN_EXTRA_INPUT)
    if unknown:
        raise ValueError(
            f"{entry['subsystem']}/{entry['id']}: unknown input key(s) "
            f"{sorted(unknown)} — not accepted by compute_chart or yongsin"
        )
    kwargs = {k: v for k, v in entry["input"].items() if k in _ALLOWED_INPUT}
    kwargs.setdefault("name", entry["id"])
    chart = compute_chart(**kwargs)
    rof = entry["input"].get("reader_override_favorable")
    if rof:
        chart.strength_assessment["reader_override_favorable"] = rof
    return check_yongsin(chart, entry)


def check_climate(entry: dict) -> dict:
    """Check climate.assess_climate() against a chart-free climate fixture entry.

    Expected key: "climate" — fields band / climate_favorable /
    climate_supporting, None skips that field (null-skip semantics, same as
    check_pillars). Only probe="band" entries reach here; probe="merge"
    entries are checked by check_climate_merge. Status semantics identical
    to check_pillars: PASS / INTERPRETATION / FAIL.
    """
    expected = entry.get("expected", {})
    got = climate.assess_climate(entry["input"]["month_branch"])
    mismatches: dict = {}
    for key, exp in (expected.get("climate") or {}).items():
        if exp is not None and got[key] != exp:
            mismatches[f"climate.{key}"] = {"expected": exp, "got": got[key]}
    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def check_climate_merge(chart: Any, entry: dict) -> dict:
    """Check the climate cross-check's effect on the resolved 용신 for one chart.

    Three expected blocks, all None-skipping:
    - "climate": the classifier re-run on chart.month.branch — proves the
      merge consumed the same band the classifier produces.
    - "strength": chart.strength_assessment verdict / candidate_favorable —
      the raw pre-merge candidate, so a resolved-element change is
      attributable to the climate merge rather than to a moved candidate.
    - "fe": the resolved FavorableElement fields (element, method,
      supporting, climate_band, climate_element, climate_agrees, confidence,
      remedy_dominant).
    Status semantics identical to check_pillars: PASS / INTERPRETATION / FAIL.
    """
    expected = entry.get("expected", {})
    mismatches: dict = {}

    got_climate = climate.assess_climate(chart.month.branch)
    for key, exp in (expected.get("climate") or {}).items():
        if exp is not None and got_climate[key] != exp:
            mismatches[f"climate.{key}"] = {"expected": exp, "got": got_climate[key]}

    exp_strength = expected.get("strength")
    if exp_strength:
        sa = chart.strength_assessment
        got_strength = {"verdict": sa["verdict"],
                        "candidate": sa["_raw_unresolved_favorable"]}
        for key, exp in exp_strength.items():
            if exp is not None and got_strength[key] != exp:
                mismatches[f"strength.{key}"] = {
                    "expected": exp, "got": got_strength[key]}

    fe = yongsin.favorable_element(chart)
    got_fe = {
        "element": fe.element, "method": fe.method, "supporting": fe.supporting,
        "climate_band": fe.climate_band, "climate_element": fe.climate_element,
        "climate_agrees": fe.climate_agrees, "confidence": fe.confidence,
        "remedy_dominant": fe.remedy_dominant, "climate_extreme": fe.climate_extreme,
    }
    for key, exp in (expected.get("fe") or {}).items():
        if exp is not None and got_fe[key] != exp:
            mismatches[f"fe.{key}"] = {"expected": exp, "got": got_fe[key]}

    if not mismatches:
        status = "PASS"
    elif entry.get("status") == "documented_interpretation":
        status = "INTERPRETATION"
    else:
        status = "FAIL"
    detail = "; ".join(f"{k}: expected {m['expected']}, got {m['got']}"
                       for k, m in mismatches.items()) or "all checks matched"
    return {"id": entry["id"], "status": status,
            "mismatches": mismatches, "detail": detail}


def run_climate_fixture(entry: dict) -> dict:
    """Dispatch a climate fixture entry by its "probe" kind and check it.

    probe="band":  chart-free. Input keys must be EXACTLY
                   _CLIMATE_BAND_INPUT (mirrors run_lookups_fixture).
    probe="merge": chart-based. Unknown input keys beyond
                   _CLIMATE_MERGE_INPUT raise (mirrors run_yongsin_fixture).
    An unrecognised (or missing) probe raises rather than silently
    defaulting — a typo must not degrade to a vacuous PASS.
    """
    probe = entry["input"].get("probe")
    if probe not in _CLIMATE_ALLOWED_INPUT:
        raise ValueError(
            f"climate/{entry['id']}: unknown probe kind {probe!r} — "
            f"expected one of {sorted(_CLIMATE_ALLOWED_INPUT)}"
        )
    if probe == "band":
        keys = set(entry["input"])
        if keys != _CLIMATE_BAND_INPUT:
            raise ValueError(
                f"climate/{entry['id']}: input keys {sorted(keys)} must be exactly "
                f"{sorted(_CLIMATE_BAND_INPUT)} for probe kind 'band'"
            )
        return check_climate(entry)
    unknown = set(entry["input"]) - _CLIMATE_MERGE_INPUT
    if unknown:
        raise ValueError(
            f"{entry['subsystem']}/{entry['id']}: unknown input key(s) "
            f"{sorted(unknown)} — not accepted by compute_chart or climate"
        )
    kwargs = {k: v for k, v in entry["input"].items() if k in _ALLOWED_INPUT}
    kwargs.setdefault("name", entry["id"])
    chart = compute_chart(**kwargs)
    return check_climate_merge(chart, entry)


_STARS_ALLOWED_INPUT = _ALLOWED_INPUT | {"star_anchor"}


def check_stars(chart: Any, entry: dict) -> dict:
    """Check a declared subset of chart.stars against a stars fixture.

    expected.stars: {star_key: [branches/stems/pillars]} — each listed key must
    equal chart.stars[key] (order-insensitive); an empty list asserts the star
    is not activated. Unlisted keys are not checked. Unknown keys raise.
    """
    exp = entry.get("expected", {}).get("stars") or {}
    unknown = set(exp) - set(chart.stars)
    if unknown:
        raise ValueError(f"stars/{entry['id']}: unknown star key(s) {sorted(unknown)}")
    mismatches = {
        k: {"expected": sorted(v), "got": sorted(chart.stars.get(k, []))}
        for k, v in exp.items() if sorted(v) != sorted(chart.stars.get(k, []))
    }
    return _result(entry, mismatches)


def run_stars_fixture(entry: dict) -> dict:
    """Compute the chart for a stars fixture entry and check its 신살 subset."""
    unknown = set(entry["input"]) - _STARS_ALLOWED_INPUT
    if unknown:
        raise ValueError(f"stars/{entry['id']}: unknown input key(s) {sorted(unknown)}")
    anchor = entry["input"].get("star_anchor")
    if anchor is not None and anchor not in ("day", "year"):
        raise ValueError(
            f"stars/{entry['id']}: star_anchor must be 'day' or 'year', got {anchor!r}"
        )
    kwargs = dict(entry["input"])
    kwargs.setdefault("name", entry["id"])
    return check_stars(compute_chart(**kwargs), entry)


def _patterns_extract(pat: dict) -> dict:
    """Extractors over the JSON shape of ``Chart._patterns_dict`` (regular_grid
    already converted to dicts), one per supported ``expected.patterns`` key."""
    grid = pat.get("regular_grid") or []
    tg = pat.get("transformation_grid")
    return {
        "regular_grid_name": grid[0]["name_ko"] if grid else None,
        "yangin": bool(pat["yangin"]["present"]),
        "yangin_grid": bool(pat["yangin_grid"]["present"]),
        "jianlu": bool(pat["jianlu"]["present"]),
        "jianlu_grid": bool(pat["jianlu_grid"]["present"]),
        "transformation_grid": tg["name_ko"] if tg else None,
        "special_forms_names": sorted(f["name_ko"] for f in pat.get("special_forms") or []),
        "special_forms_confidence": {f["name_ko"]: f["confidence"] for f in pat.get("special_forms") or []},
        "structural_notes_kinds": sorted(n["name_ko"] for n in pat.get("structural_notes") or []),
        "tengod_conflicts_names": sorted(c["name_ko"] for c in pat.get("tengod_conflicts") or []),
    }


def check_patterns(chart: Any, entry: dict) -> dict:
    """Check a declared subset of chart.patterns (격국) against a fixture.

    expected.patterns keys (each optional): regular_grid_name, yangin (blade
    present at any position), yangin_grid (month-branch 양인격), jianlu,
    jianlu_grid (month-branch 건록격), transformation_grid (name or null),
    special_forms_names, special_forms_confidence (dict name_ko -> confidence),
    structural_notes_kinds, tengod_conflicts_names (sorted lists). Unknown keys raise.
    """
    exp = entry.get("expected", {}).get("patterns") or {}
    got = _patterns_extract(chart._patterns_dict(chart.patterns))
    unknown = set(exp) - set(got)
    if unknown:
        raise ValueError(f"patterns/{entry['id']}: unknown expected key(s) {sorted(unknown)}")
    mismatches = {}
    for k, v in exp.items():
        want = sorted(v) if isinstance(v, list) else v
        if want != got[k]:
            mismatches[k] = {"expected": want, "got": got[k]}
    return _result(entry, mismatches)


def run_patterns_fixture(entry: dict) -> dict:
    """Compute the chart for a patterns fixture entry and check its 격국 subset."""
    unknown = set(entry["input"]) - _ALLOWED_INPUT
    if unknown:
        raise ValueError(f"patterns/{entry['id']}: unknown input key(s) {sorted(unknown)}")
    kwargs = dict(entry["input"])
    kwargs.setdefault("name", entry["id"])
    return check_patterns(compute_chart(**kwargs), entry)


_SUBSYSTEM_ORDER = ["pillars", "daeun", "sewoon", "lookups", "yongsin",
                    "climate", "compat", "career", "stars", "patterns"]
# Workstream label per subsystem (spec §workstreams). Extended by Plans 4–6.
_WORKSTREAM = {"pillars": "W1", "daeun": "W2", "sewoon": "W2", "lookups": "W3",
               "yongsin": "W4", "climate": "W5", "compat": "W6", "career": "W6", "stars": "W7",
               "patterns": "W8"}
_RUNNERS = {"pillars": run_fixture, "daeun": run_daeun_fixture, "sewoon": run_sewoon_fixture,
            "lookups": run_lookups_fixture, "yongsin": run_yongsin_fixture,
            "climate": run_climate_fixture, "compat": run_compat_fixture,
            "career": run_career_fixture, "stars": run_stars_fixture,
            "patterns": run_patterns_fixture}


def collect_results(fixtures_dir: Optional[Path] = None) -> dict[str, list[dict]]:
    """Run every registered subsystem's fixtures through its check runner."""
    results: dict[str, list[dict]] = {}
    for subsystem in _SUBSYSTEM_ORDER:
        runner = _RUNNERS[subsystem]
        results[subsystem] = [runner(e) for e in load_fixtures(subsystem, fixtures_dir)]
    return results


def _esc(cell: Any) -> str:
    return str(cell).replace("|", "\\|")


# Historical gate record: one entry per certified workstream, appended at that
# workstream's certification. Narrative lives in
# docs/validation/gate-history.md. Gate dates and at-gate counts are facts that
# do not move; the live totals below are derived from the current run instead.
_GATE_HISTORY = [
    {"workstream": "W1 Pillars", "gate_date": "2026-09-13", "checks": 17, "passed": 17},
    {"workstream": "W2 대운/세운", "gate_date": "2026-09-13", "checks": 19, "passed": 19},
    {"workstream": "W3 십신/12운성/납음/공망", "gate_date": "2026-09-13", "checks": 56, "passed": 56},
    {"workstream": "W4 용신", "gate_date": "2026-09-13", "checks": 13, "passed": 13,
     "note": "10 PASS + 3 documented_interpretation"},
    {"workstream": "W5 Climate (조후)", "gate_date": "2026-09-13", "checks": 30, "passed": 30,
     "note": "30 PASS; 3 documented_interpretation guard rows; 0 FAIL"},
    {"workstream": "W6 Compat / spouse + career", "gate_date": "2026-09-14",
     "checks": 59, "passed": 59,
     "note": "27 compat + 32 career; 2 documented_interpretation; 0 FAIL"},
    {"workstream": "W7 Stars (신살)", "gate_date": "2026-10-03", "checks": 57, "passed": 57,
     "note": "54 PASS + 3 documented_interpretation"},
    {"workstream": "W8 Patterns (격국)", "gate_date": "2026-10-03", "checks": 48, "passed": 48,
     "note": "46 PASS + 2 documented_interpretation"},
]


def render_report(results: dict[str, list[dict]]) -> str:
    lines = [
        "# Engine Validation Report — 2026-09 campaign",
        "",
        "Ground truth: cited fixtures in `tests/validation/fixtures/` "
        "(spec: the 2026-09 validation campaign design (removed 2026-10-01)).",
        "",
        "## Scorecard",
        "",
        "| subsystem | charts | PASS | INTERPRETATION | FAIL |",
        "|---|---|---|---|---|",
    ]
    for subsystem, rows in results.items():
        counts = {"PASS": 0, "INTERPRETATION": 0, "FAIL": 0}
        for r in rows:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
        lines.append(
            f"| {_esc(subsystem)} | {len(rows)} | {counts['PASS']} "
            f"| {counts['INTERPRETATION']} | {counts['FAIL']} |"
        )
    for subsystem, rows in results.items():
        lines += [
            "",
            f"## {_WORKSTREAM.get(subsystem, '?')} — {subsystem}",
            "",
            "| id | status | detail |",
            "|---|---|---|",
        ]
        for r in rows:
            lines.append(f"| {_esc(r['id'])} | {r['status']} | {_esc(r['detail'])} |")
    # Certification epilogue (brief-authorized placement: the CLI rewrites the
    # report file on every run, so hand-edits get clobbered; emitting it here
    # keeps it idempotent). _GATE_HISTORY carries frozen per-gate facts; the
    # current-status line is derived from `results` so it stays truthful as
    # later plans add checks.
    total_checks = sum(len(rows) for rows in results.values())
    total_pass = sum(1 for rows in results.values() for r in rows if r["status"] == "PASS")
    lines += [
        "",
        "### Certification",
        "",
    ]
    for g in _GATE_HISTORY:
        note = f" ({g['note']})" if g.get("note") else ""
        lines.append(
            f"- {g['workstream']}: CERTIFIED (gate date {g['gate_date']}). "
            f"Checks at gate: {g['passed']}/{g['checks']} PASS{note}."
        )
    lines.append(
        f"- Current validation checks: {total_pass}/{total_checks} PASS "
        f"across {len(results)} subsystems."
    )
    lines += ["", "Full certification history: docs/validation/gate-history.md"]
    return "\n".join(lines) + "\n"