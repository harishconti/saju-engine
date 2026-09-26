"""Validation harness shared library (W1–W6 campaign).

Loads cited ground-truth fixtures and checks engine output against them.
Three check statuses per the validation spec:
PASS (engine matches ground truth), INTERPRETATION (engine follows the cited
classical rule; external source differs by school/method — documented, not a
failure), FAIL (engine bug or unsupported rule — logged for later fixing).
See docs/superpowers/specs/2026-09-13-engine-validation-campaign-design.md.
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
    supporting, climate_band, climate_element, climate_agrees, confidence —
    None skips that field) and "strength" (chart.strength_assessment fields
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
    }
    for key, exp in (expected.get("fe") or {}).items():
        if exp is not None and got_fe[key] != exp:
            mismatches[f"fe.{key}"] = {"expected": exp, "got": got_fe[key]}
    exp_strength = expected.get("strength")
    if exp_strength:
        sa = chart.strength_assessment
        got_strength = {"verdict": sa["verdict"],
                        "candidate": sa["candidate_favorable"]}
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
      supporting, climate_band, climate_element, climate_agrees, confidence).
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
                        "candidate": sa["candidate_favorable"]}
        for key, exp in exp_strength.items():
            if exp is not None and got_strength[key] != exp:
                mismatches[f"strength.{key}"] = {
                    "expected": exp, "got": got_strength[key]}

    fe = yongsin.favorable_element(chart)
    got_fe = {
        "element": fe.element, "method": fe.method, "supporting": fe.supporting,
        "climate_band": fe.climate_band, "climate_element": fe.climate_element,
        "climate_agrees": fe.climate_agrees, "confidence": fe.confidence,
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


_SUBSYSTEM_ORDER = ["pillars", "daeun", "sewoon", "lookups", "yongsin",
                    "climate", "compat", "career"]
# Workstream label per subsystem (spec §workstreams). Extended by Plans 4–6.
_WORKSTREAM = {"pillars": "W1", "daeun": "W2", "sewoon": "W2", "lookups": "W3",
               "yongsin": "W4", "climate": "W5", "compat": "W6", "career": "W6"}
_RUNNERS = {"pillars": run_fixture, "daeun": run_daeun_fixture, "sewoon": run_sewoon_fixture,
            "lookups": run_lookups_fixture, "yongsin": run_yongsin_fixture,
            "climate": run_climate_fixture, "compat": run_compat_fixture,
            "career": run_career_fixture}


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
# workstream's certification. Gate dates and at-gate counts are facts that do
# not move; the live totals below are derived from the current run instead.
_GATE_HISTORY = [
    {"workstream": "W1 Pillars", "gate_date": "2026-09-13", "checks": 17, "passed": 17},
    {"workstream": "W2 대운/세운", "gate_date": "2026-09-13", "checks": 19, "passed": 19},
    {"workstream": "W3 십신/12운성/납음/공망", "gate_date": "2026-09-13", "checks": 56, "passed": 56},
    {"workstream": "W4 용신", "gate_date": "2026-09-13", "checks": 13, "passed": 13,
     "note": "10 PASS + 3 documented_interpretation"},
    {"workstream": "W5 Climate (조후)", "gate_date": "2026-09-13", "checks": 30, "passed": 30,
     "note": "30 PASS; 3 rows carry the documented_interpretation guard "
             "(published divergences cross-referenced in source); 16 band "
             "(12 branches + 4 edges) + 14 merge covering all 9 band × verdict "
             "cells; 0 FAIL"},
    {"workstream": "W6 Compat / spouse + career", "gate_date": "2026-09-14",
     "checks": 59, "passed": 59,
     "note": "27 compat (the eleven sub-systems A-K + 10 band cut-point edges + "
             "6 score/anchor rows) + 32 career (30 KB12 domain-map + 2 "
             "need-keyed tier charts); 2 documented_interpretation "
             "(harish × vinothini pillars-only reconstruction; pawan × sruthi "
             "stale ya-ja-si chart); 0 FAIL. Gate-time pin tally, re-measured "
             "2026-09-14: 3 bug-lock families / 6 non-strict xfail markers "
             "(which parametrize to 10 xfailed tests) / 10 guard tests — 육합 "
             "dead code (test_val_compat, 3 locks / 3 fix-immune guards), C9 "
             "삼형 shadowing (test_compat, 1 lock parametrized over 5 pairs / 2 "
             "guards), C8 order-dependence (test_compat, 1 lock / 2 guards). "
             "NOTE: this line previously read '9 non-strict xfail markers'; no "
             "scoping reproduces 9 (W6-scoped is 6, suite-wide is 8), so the "
             "figure is corrected to the measured value rather than carried. "
             "A 4th family pinned at gate time "
             "(report_data stale candidate_favorable, 1 lock + 3 guards) was "
             "FIXED 2026-09-14; its lock XPASSed (delete-the-marker signal), so "
             "the marker is retired and test_report_data now pins the fixed "
             "behaviour positively. The fix also resolved the related "
             "report_data._career_tiers contradiction — the candidate pool is "
             "now keyed on the resolved 용신/희신 families, so both tier "
             "fixtures measure possible_tier_reachable true over 12 rows "
             "(W6 coverage gap 1 closed). C8 was likewise FIXED 2026-09-14 — "
             "compat.py::_canonical_nayin_pair() now resolves the Nayin subject "
             "order from the couple (male-first when both genders are known and "
             "differ, else lower NAYIN_ORDER index) instead of from the caller's "
             "argument order, so one couple has one verdict; see "
             "knowledge/11-gunghap.md §C 'Canonical subject order'. Its lock "
             "XPASSed, the marker is retired, and test_compat now pins "
             "order-independence positively (0 locks / 3 guards). The 육합 "
             "dead-code family was FIXED 2026-09-14 as well — "
             "compat._branch_pair_lookup now matches each relation row on its "
             "branch columns rather than on the whole row, so the 六合 branch is "
             "reachable at all four call sites; the defect record and its three "
             "pins live in tests/validation/test_val_compat.py. Its 3 locks "
             "XPASSed, their markers are retired, and they now stand as positive "
             "behaviour pins (L1 cross-pair helper +4, L2 spouse-palace +20, L3 "
             "띠 +3). L3 additionally had to be REPAIRED rather than merely "
             "un-marked: _pillars_chart hardcoded 甲子 for both charts, so the "
             "띠 sub-system compared 子 with 子 and could never reach a 육합 — "
             "permanently unsatisfiable under any candidate fix, which is why it "
             "never XPASSed; _pillars_chart now takes a year_branch. Its 3 "
             "guards stay, one INVERTED: "
             "test_guard_lookup_is_shape_tolerant_for_six_combinations had "
             "asserted the pre-fix premise (六合 lookup is False for all six "
             "pairs) and failed the moment the helper gained 3-tuple tolerance, "
             "so the shape-tolerance contract is now asserted positively. One "
             "family remains live and fix-immune (C9). Live marker tally, "
             "re-measured 2026-09-14 after all three retirements: 1 W6-scoped "
             "non-strict xfail marker (C9, parametrized over 5 pairs = 5 xfailed "
             "tests); 3 markers suite-wide once the 2 client-visible climate "
             "locks are counted, expanding to 7 xfailed tests — the other 5 "
             "xfailed are documented_interpretation escapes (dynamic "
             "pytest.xfail on fixture mismatch: 3 W4 용신 + 2 W6 compat), not "
             "bug locks. The chain ORDER was deliberately not touched, so the C9 "
             "family is otherwise unchanged: four of its five rows still report "
             "the shadowing relation the lock names, and the fifth (巳申) now "
             "reports 육합 instead of 육파 — a different shadowing kind, still "
             "not 삼형, so the row remains xfailed and the lock's status is "
             "unmoved. The arity fix alone therefore flips 0 of C9's 5 rows. The "
             "premium_report.py instances of that bug class (spec §Known Open "
             "Bugs #1) were FIXED 2026-09-14 -- see the W5 note below."},
]


def render_report(results: dict[str, list[dict]]) -> str:
    lines = [
        "# Engine Validation Report — 2026-09 campaign",
        "",
        "Ground truth: cited fixtures in `tests/validation/fixtures/` "
        "(spec: docs/superpowers/specs/2026-09-13-engine-validation-campaign-design.md).",
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
        if subsystem == "yongsin":
            lines += [
                "",
                "### W4 yongsin — method coverage and documented divergences",
                "",
                "Merge logic validated (read-only engine, yongsin.py:105-206;",
                "knowledge/09-interpretation-method.md Step 3; knowledge/17",
                "§How This Combines With 억부): reader override wins unconditionally,",
                "then climate-balanced (balanced Day Master × non-temperate 조후 band),",
                "then the strong/weak 억부 verdict. All five method labels exercised:",
                "strong-dm-drain, weak-dm-support, balanced-heuristic,",
                "climate-balanced, reader-confirmed.",
                "",
                "Fixture layers: A — synthetic merge-logic charts (weak-cold-*);",
                "B — published client verdicts (rm, gurumoorthy, harish,",
                "vishnu-priya, sruthi, pawan, mahesh); C — both override channels",
                "(explicit `override` argument and",
                "`strength_assessment['reader_override_favorable']`, byte-identical).",
                "",
                "3 documented divergences (INTERPRETATION rows above):",
                "sruthi-published (published Earth vs engine climate-balanced Fire),",
                "pawan-published (published Water vs engine balanced-heuristic Wood),",
                "mahesh-published (published Earth vs engine climate-balanced Fire) —",
                "reader-argued verdicts on borderline balanced charts; the",
                "reader-override fixtures reproduce each published element exactly.",
                "pawan/mahesh verdicts predate the ya-ja-si hour-stem fix (STALE",
                "CHART); reports queued for regeneration at campaign close.",
                "",
                "External cross-check (2026-09-13): 3 rule families × ≥2 sources,",
                "no contradiction — weak DM → 인성/비겁 and strong DM →",
                "식상/재성/관성 drain (두루미사주 억부용신 + 사자사주), extreme",
                "climate ⇒ 조후 priority (두루미사주 conditional + OpenFate",
                "climate-vs-strength-priority). Citations appended to each",
                "fixture's `source` field; full research:",
                "docs/research/2026-09-validation-yongsin.md.",
            ]
        if subsystem == "climate":
            lines += [
                "",
                "### W5 climate — three-band classifier and the 조후 × 억부 merge matrix",
                "",
                "Classifier validated (read-only engine, climate.py:assess_climate;",
                "knowledge/17-climate-method.md §Three Bands + §How This Combines",
                "With 억부): a pure function of the month BRANCH — 巳午未 → hot/Water",
                "(supporting Metal), 亥子丑 → cold/Fire (supporting Wood), all other",
                "branches → temperate with both elements None. All 12 branches are",
                "pinned, plus 4 defensive edges (empty string, a stem, latin input,",
                "a 子時 hour label) that must fall through to temperate rather than",
                "crash or mis-band — the 子時 edge specifically proves an hour label",
                "is never read as the 子 MONTH.",
                "",
                "Merge matrix: 14 corpus charts covering all 9 band × verdict-class",
                "cells (strong / balanced / weak folded over the 5-value strength",
                "enum) with both climate_agrees polarities present for every",
                "non-temperate band. Split by which layer decided the element:",
                "5 rows where 억부 overrides 조후 (gurumoorthy-published,",
                "weak-cold-priority, hot-weak-priority, cold-strong-priority,",
                "cold-strong-scan — the raw candidate is kept and the 조후 element",
                "declined), 4 where 조후 decides (harish, sruthi, mahesh,",
                "vishnu-priya — all climate-balanced), 3 temperate controls where",
                "조후 must not fire at all (rm-published, pawan-published,",
                "weak-temperate), and 2 agreement rows where the raw candidate and",
                "the 조후 element already coincide (weak-cold-agree, hot-weak-agree).",
                "",
                "Engine rule measured: 억부 decides unless the verdict is",
                "`balanced`, in which case 조후 decides for a non-temperate band.",
                "Whether the classical sources rank 조후 above 억부 unconditionally",
                "is examined in docs/research/2026-09-validation-climate.md §5 —",
                "recorded as an engine-behavior finding, not changed in-campaign.",
                "",
                "3 rows carry the documented_interpretation guard — sruthi-published,",
                "pawan-published, mahesh-published (published Earth / Water / Earth",
                "reading vs engine Fire / Wood / Fire) — the same three divergences",
                "W4 documented, here attributed to their band × verdict cause. NOTE",
                "the guard is a safety flag, not a verdict: a guarded row renders",
                "INTERPRETATION only when it ALSO mismatches, and these three assert",
                "engine values the probe reproduces exactly, so they render PASS.",
                "The divergence is against the reader's published reading, which is",
                "what each entry's `source` records. W5 therefore contributes 0",
                "INTERPRETATION rows; the CLI's 3 remain W4's. pawan/mahesh verdicts",
                "predate the ya-ja-si hour-stem fix (STALE CHART); reports queued",
                "for regeneration at campaign close.",
                "",
                "Open coverage gaps (logged, NOT fixed — validation-only campaign):",
                "the 120-cell 궁통보감 per-stem-per-month table is unimplemented",
                "(climate.py self-declares the conservative scope), and climate.py",
                "implements only the 寒暖 (hot/cold) axis of the classical 조후",
                "treatment, whose fuller form is the four-way 寒暖燥濕 reading",
                "(적천수: 天道有寒暖 … 地道有燥湿; knowledge/17-climate-method.md",
                "§The Fuller 寒暖燥濕 Reading). Measured against that reading the",
                "engine agrees on all ten branches where it prescribes an element",
                "at all, and diverges only on 辰 (engine temperate, source 濕→火)",
                "and 戌 (engine temperate, source 燥→水) — and only in whether an",
                "override fires, never in which element: nobody assigns those two",
                "branches a different remedy; the models differ on whether they are",
                "assigned one. 丑 and 未 agree by convergent validity — the engine",
                "cuts by seasonal quartet (丑 with 亥子, 未 with 巳午) and the source",
                "by damp/dry state (辰丑 damp, 戌未 dry), and the two schemes still",
                "land on Fire for 丑 and Water for 未. The divergence is pinned as an",
                "explicit SCOPE LIMIT rather than an open uncertainty, because",
                "widening the model would move the client-facing band value for",
                "every 辰/戌-month chart — so the expansion is a product decision,",
                "recorded in the knowledge file §Why the fuller reading is not",
                "implemented and pinned by band-chen / band-xu. Both gaps are",
                "addressed in docs/research/2026-09-validation-climate.md.",
                "",
                "Known-bug regression lock (spec §Known Open Bugs Tracked #1) --",
                "FIXED 2026-09-14: premium_report.py _right_now_callout (~L181)",
                "and ctx_favorable_phrase (~L1399) used to read the stale raw",
                "strength_assessment['candidate_favorable'] instead of the",
                "resolved favorable_element(). Both now take an `override`",
                "param threaded from _ReportContext.favorable_override and read",
                "the resolved channel, mirroring the report_data.py career-",
                "section fix. The two non-strict pytest xfails in",
                "tests/validation/test_val_climate.py XPASSed and were retired;",
                "the tests now stand as plain regression locks on the fix.",
            ]
        # W6 is the only workstream spanning TWO subsystems (compat + career),
        # so this block is keyed to the LAST of them -- `_SUBSYSTEM_ORDER` puts
        # career after compat -- and therefore renders exactly once, after both
        # W6 detail tables, the way the W4/W5 blocks follow theirs.
        if subsystem == "career":
            lines += [
                "",
                "### W6 compat / spouse + career — composite, weight table, and "
                "pinned defects",
                "",
                "Compat composite validated (read-only engine, compat.py; "
                "knowledge/11-gunghap.md §A-K, weight table :18-40, verdict bands "
                ":959-978). 27 rows: the eleven sub-systems A-K, 10 band "
                "cut-point edges, 6 score/anchor rows.",
                "",
                "Weight table measured: `WEIGHT` has 11 keys summing to 112, and "
                "the scored subset excluding `combined_elements` sums to exactly "
                "100 -- so the affine composite "
                "`round(max(0, min(100, 50 + raw_total)))` is 0-100 normalizable, "
                "and the gap between the two sums is `WEIGHT['combined_elements']` "
                "(12). This is the one structural invariant the whole 0-100 scale "
                "rests on; a twelfth weighted key or a 113 total would silently "
                "break every published number.",
                "",
                "Band cut-points measured (`_band_for`): >=80 Excellent, >=65 "
                "Strong, >=45 Mixed, else Challenging. All 10 edges pinned from "
                "both sides, plus the out-of-range clamps: -1 and 0 Challenging; "
                "44 Mixed / 45 Mixed; 64 Mixed / 65 Strong; 79 Strong / 80 "
                "Excellent; 100 and 101 Excellent.",
                "",
                "Anchor: `compat-harish-manvitha` reproduces the published "
                "70/Strong exactly from FULL/FULL `birth` pipelines with ZERO "
                "reader overrides, and asserts all 11 WEIGHT keys. The override "
                "anchor (partner B favorable forced to Earth) moves to 74/Strong "
                "-- a reader override perturbs yongshin, ilju_pair AND "
                "combined_elements, which is why the anchor's zero-override "
                "provenance is asserted rather than assumed.",
                "",
                "Cross-branch priority measured, strict and first-match-wins "
                "(:310): 육합 -> 육충 -> 육해 -> 육파 -> 형 -> 반합. The 형 step is "
                "reachable for exactly 子卯 and 丑戌 within the 三刑 frames; 寅巳, "
                "巳申, 寅申, 丑未 and 戌未 are shadowed by an earlier step, and the "
                "four self-punishments 辰午酉亥 ride the same step at -2.",
                "",
                "Career validated (read-only engine, report_data.py; "
                "knowledge/12-career-and-vocation.md, industry families :25-49). "
                "32 rows: 30 domain-map + 2 need-keyed tier charts. The 30 "
                "domains are the 5 per-element keyword lists in "
                "`_domain_element`, 6 domains each; 25 agree with the KB12 "
                "family and 5 carry the documented_interpretation guard (2 "
                "coverage gaps that return None, 3 substring/ordering artifacts "
                "where an earlier keyword list claims the domain).",
                "",
                "Tier cut-points measured: `_career_tiers` scores then sorts and "
                "labels `i<4` **Best Fit**, `i<7` **Good Fit**, else "
                "**Possible**. The candidate pool is the resolved 용신's family "
                "followed by the 희신's family -- 12 candidates from 2 families "
                "on both fixture charts -- so all three tiers are live, and both "
                "fixtures pin `possible_tier_reachable` true against the full "
                "ordered 12-row list. That closes the KB12:130-152 contradiction "
                "this campaign recorded: the pool is now keyed on the chart's "
                "*need*, not the Day Master's own element (fixed 2026-09-14, "
                "which also closes W6 coverage gap 1).",
                "",
                "2 documented divergences (INTERPRETATION rows above). "
                "harish × vinothini: the published 57/100 Mixed is a FULL/FULL "
                "measurement -- the report prints both partners' four pillars in "
                "full -- so this entry is a pillars-only reconstruction and the "
                "divergence is a chart-INPUT difference, not a rule conflict. "
                "pawan × sruthi: the published 55/100 Mixed predates the 야자시 "
                "(夜子時) hour-stem fix (STALE CHART), so the engine's current "
                "value is ground truth and the published figure is the outdated "
                "one; both reports are queued for regeneration at campaign close.",
                "",
                "1 pinned bug-lock family / 1 non-strict xfail marker (which "
                "parametrizes to 5 xfailed tests; 3 markers suite-wide once the 2 "
                "client-visible climate locks are counted) / 11 guard-or-pin test "
                "functions (16 test instances, by collection). The single live "
                "family is fix-immune, and the campaign is "
                "validation-only, so it remains unfixed by design. Three of the "
                "four families pinned at gate time have since been FIXED and "
                "their markers retired: the 육합 dead code (3 locks + 3 guards, "
                "2026-09-14); the `report_data` stale `candidate_favorable` "
                "field (1 lock + 3 guards, 2026-09-14), whose lock went XPASS -- "
                "the delete-the-marker signal -- so that file now pins the fixed "
                "behaviour as a positive pin; and C8 order-dependence (1 lock / "
                "2 guards, 2026-09-14), fixed by "
                "`compat.py::_canonical_nayin_pair()`, which resolves the Nayin "
                "subject order from the couple rather than from the caller's "
                "argument order (see knowledge/11-gunghap.md §C \"Canonical "
                "subject order\"), retiring its marker and replacing its two "
                "*defect pins* with three order-independence guards. The "
                "`report_data` fix necessarily resolved the second half of the "
                "`premium_report.py` bug class in `report_data._career_tiers` as "
                "well, because the ranking and the per-row prose had to move to "
                "the display channel together to stay consistent -- the W4 "
                "`premium_report.py` instances above remain the only unfixed "
                "half:",
                "",
                "* 육합 dead code -- FIXED 2026-09-14. "
                "`compat._branch_pair_lookup` matched a 2-tuple against "
                "`lookup.SIX_COMBINATIONS`, which is declared "
                "`List[Tuple[str, str, str]]`, so the 육합 branch was unreachable "
                "at all four call sites (:310 intended +4, :407 the PRIMARY "
                "spouse-palace +20, :1295 띠 +3, :428 a vacuous 반합 "
                "suppression). The helper now matches each relation row on its "
                "branch columns; the defect record and its three pins live in "
                "tests/validation/test_val_compat.py. Its 3 locks XPASSed -- the "
                "delete-the-marker signal -- so the markers are retired and the "
                "locks now stand as positive behaviour pins; its 3 guards remain, "
                "one INVERTED, because the shape-tolerance contract had asserted "
                "the buggy premise (六合 lookup is False for all six pairs) and is "
                "now asserted positively. NOTE: this fix did NOT move the C9 "
                "family -- the fix-order coupling previously asserted here is "
                "refuted below.",
                "* C9 삼형 shadowing -- 1 lock parametrized over 5 pairs / 2 "
                "guards, fix-immune and LEFT UNFIXED BY DESIGN: no `knowledge/` "
                "file sanctions a position for 삼형 in this ladder, so any "
                "re-ordering would invent a priority -- carried as a documented "
                "scope limit, the same shape as the accepted #11 resolution (see "
                "knowledge/11-gunghap.md §B9, and §B4-C9 note for the per-pair "
                "table and the two reachable controls 子卯 / 亥亥). MEASURED, "
                "CORRECTING A CLAIM THIS REPORT USED TO MAKE: the 육합 arity fix "
                "and a C9 fix are NOT coupled. The arity fix alone flips 0 of "
                "these 5 rows -- it moves 巳申 from 육파 to 육합, which is still "
                "not 삼형. The earlier 'a C9 fix alone flips 5/5, C9 + 육합 "
                "together flips only 4/5' figure came from hoisting 삼형 above "
                "육충 in the ladder, which is a different and unsanctioned "
                "change: it would relabel 丑未 and 寅申, costing them the §B4 "
                "육충 label and the −5 weight those rows carry, and displace "
                "육해/육파 without a source. That full-chain reorder is a NO-OP "
                "on all 27 compat fixtures -- no published anchor, no "
                "client-visible value and no fixture expectation moves; only the "
                "relation LABELS and this lock's bookkeeping would change. So the "
                "lock is unmoved by the arity fix, and its 巳申 row is knowingly "
                "stale by design (巳申 is simultaneously 六合 and 六破 and 육합 "
                "is tested first, so it now reports 육합); do not \"fix\" that row.",
                "",
                "External cross-check (2026-09-14): all 59 fixtures carry a "
                "`source['external']` {citation, url} object plus an inline ref "
                "on `url_or_ref`, so every expectation is traceable to a named "
                "Korean source or to the published report it measures. Full "
                "research: docs/research/2026-09-validation-compat-career.md.",
            ]
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
    lines.append(
        "- Gate: Campaign COMPLETE — all six workstreams (W1-W6) certified; "
        "no successor gate."
    )
    return "\n".join(lines) + "\n"