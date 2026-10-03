# P2 — Report Primitives, Typed Compat Flags, Core-Table Dedup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Source:** audit `/mnt/data2/git_repos/research-engine/output/2026-10-01/saju-engine-audit-2026-10-01.md` §4.2, §7 item 2–3, §9 B4/B6/B8 (S6).

**Goal:** Remove the report-layer duplication that caused the S2/S3 drift (ten-god class tables ×5, favorability ×4, verdict labels ×4, decade helpers ×2, emoji/class/bar/plain copies, sewoon gloss ×3, core lookup tables ×2–3), type the compat flags so classification never parses prose (S6), and give each "in-season" concept one named, documented primitive (B8) — **with zero change to client output** except one intentional label fix.

**Architecture:** A golden-snapshot harness (Task 1) freezes the byte-exact markdown of every report generator for fixed charts. A new `src/saju_engine/report_primitives.py` holds the shared report tables/helpers; consumers are migrated module-by-module while the golden stays byte-identical. Core lookup duplicates move into `lookup.py`. Compat flags become a `str` subclass carrying `kind`/`severity`/`code`, so every existing string use keeps working while classification reads the type.

**Tech Stack:** Python 3.10–3.12, pytest.

## Global Constraints

- Test prefix: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages`
- Baseline: `python3 -m pytest tests/ -q` → **1224 passed, 5 skipped, 9 xfailed**; `python3 tools/run_validation.py` → exit 0 (206 checks, 0 FAIL). Every task ends with zero new failures and validation exit 0.
- **Golden rule:** after Task 1, `tests/golden/` files may change ONLY in Task 2, and ONLY where a strength label `Extreme` becomes `Very Strong`. Any other golden diff is a bug in the refactor — fix the code, never regenerate the golden.
- Do not change `compat.WEIGHT`, any score threshold, band cut-point, or any client-visible string except the one label above.
- Bug-fix/refactor comments use the house style: `# B4 (2026-10-01 audit): ...`.
- Branch: `refactor/p2-report-primitives` off `develop`; one commit per task; commit messages end with a blank line + `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Decisions recorded up front

| Item | Decision |
|---|---|
| `_ELEMENT_ORGANS` (report_data / prose_fillers / prose_scaffold) | **Not merged.** The three copies carry *different client wording* (e.g. "liver/gallbladder (간/담)" vs "liver/gall bladder and nervous system"); merging changes client prose. Out of scope. |
| prose_fillers `_TENGOD_CLASS` (10 variant names) | Not a buggy copy — it is the *short English ten-god name* (Companion/Robber/Eating God…). It becomes `report_primitives.TENGOD_SHORT_EN`, also replacing the 3 inline dicts in `sewoon.py`. |
| Verdict labels | One `verdict_label()` = the `report_data._strength_label` mapping (`extreme`→`Very Strong`, `extreme_weak`→`Very Weak`). The other three copies print `Extreme` for `extreme` — asymmetric with `Very Weak`; this is the one allowed client-visible change. |
| In-season (B8) | They are **two different doctrines**, not one drifted rule: (a) *element rules the month* — `BRANCH_ELEMENT[month] == element` (compat 합화 test, pattern breaker, 육합 합화); (b) *season supports the Day Master* — seasonal branch groups incl. Earth 辰戌丑未 (report_data). Each gets one named primitive; no outputs change. |
| Compat F-verdict wording vs canonical table | Stays derived from the §F weighted measure (scores frozen by user decision 2026-10-02). Out of scope. |

---

### Task 1: Golden-snapshot harness for every report generator

**Files:**
- Create: `tests/golden/__init__.py` (empty), `tests/golden/cases.py`, `tests/test_golden_reports.py`, `tools/regen_golden.py`
- Create (generated): `tests/golden/*.md`

**Interfaces:**
- Produces: `tests/golden/cases.py::golden_outputs() -> Dict[str, str]` (file name → markdown). Later tasks only *run* the test.

- [ ] **Step 1: Write `tests/golden/cases.py`**

```python
"""Fixed inputs for the golden-snapshot report test (P2, 2026-10-02).

Every report generator is rendered for fixed charts with a fixed reference
date so output is deterministic. A refactor that changes any byte of these
files changed client output.
"""
from __future__ import annotations

from typing import Dict

from saju_engine.compat_report import generate_compat_report
from saju_engine.cross_candidate_report import generate_cross_candidate_report
from saju_engine.engine import compute_chart
from saju_engine.premium_report import generate_premium_report

REF = dict(reference_year=2026, reference_month=6, reference_day=1)
GEN_DATE = "2026-06-01"

CHARTS = {
    # Textbook case (tests/test_textbook_cases.py) — Korea, male.
    "park": dict(year=1917, month=11, day=14, hour=10, minute=0, gender="M",
                 utc_offset=9.0, longitude=128.74, name="Park"),
    # Non-KST chart (exercises the S1 offset path) — New York, female.
    "ny": dict(year=1990, month=6, day=15, hour=10, minute=0, gender="F",
               utc_offset=-5.0, longitude=-74.0, name="Nova"),
    # Winter Water-month chart, Korea, female.
    "seoul": dict(year=1985, month=12, day=20, hour=6, minute=30, gender="F",
                  utc_offset=9.0, longitude=126.98, name="Seo"),
}
TIERS = ["sample", "essential", "deep", "career", "luck-cycle"]


def _chart(key: str):
    return compute_chart(**CHARTS[key], **REF)


def golden_outputs() -> Dict[str, str]:
    out: Dict[str, str] = {}
    charts = {k: _chart(k) for k in CHARTS}
    for key, chart in charts.items():
        for tier in TIERS:
            out[f"{key}-{tier}.md"] = generate_premium_report(
                chart, tier=tier, generation_date=GEN_DATE)
    for a, b in (("park", "seoul"), ("ny", "seoul")):
        for tier in ("basic", "deep"):
            out[f"compat-{a}-{b}-{tier}.md"] = generate_compat_report(
                charts[a], charts[b], charts[a].name, charts[b].name,
                generation_date=GEN_DATE, tier=tier)
    out["cross-candidate.md"] = _cross_candidate(charts)
    return out


def _cross_candidate(charts) -> str:
    # Build the smallest valid input per the docstring of
    # generate_cross_candidate_report (cross_candidate_report.py:679):
    # two members (park, seoul) and one relationship between them.
    raise NotImplementedError  # Step 2 replaces this body
```

- [ ] **Step 2: Fill `_cross_candidate`**

Read the docstring of `generate_cross_candidate_report` (`src/saju_engine/cross_candidate_report.py:679-700`) and its existing test (`grep -rn generate_cross_candidate_report tests/`). Replace the `raise` with a call that passes two members (`{"name": "Park", "chart": charts["park"], "override": None}` and the same for `seoul`), one relationship in the shape the existing test uses, and `reference_date="2026-06-01"`. Copy the shape from the existing test exactly.

- [ ] **Step 3: Write the regen tool and the test**

`tools/regen_golden.py`:
```python
"""Regenerate tests/golden/*.md. Only run when a change to client output is
INTENDED and reviewed (see docs/superpowers/plans/2026-10-02-p2-report-primitives.md)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tests.golden.cases import golden_outputs  # noqa: E402

out_dir = ROOT / "tests" / "golden"
for name, text in golden_outputs().items():
    (out_dir / name).write_text(text, encoding="utf-8")
print(f"wrote {len(golden_outputs())} golden files to {out_dir}")
```

`tests/test_golden_reports.py`:
```python
"""Golden snapshot: every report generator's markdown must be byte-identical
to tests/golden/*.md (P2 refactor safety net, 2026-10-02). Regenerate only for
an intended, reviewed output change: `python3 tools/regen_golden.py`."""
from pathlib import Path

import pytest

from tests.golden.cases import golden_outputs

GOLDEN = Path(__file__).resolve().parent / "golden"
OUTPUTS = golden_outputs()


@pytest.mark.parametrize("name", sorted(OUTPUTS))
def test_report_matches_golden(name):
    expected = (GOLDEN / name).read_text(encoding="utf-8")
    assert OUTPUTS[name] == expected, f"{name} drifted from its golden snapshot"


def test_golden_set_is_complete():
    on_disk = {p.name for p in GOLDEN.glob("*.md")}
    assert on_disk == set(OUTPUTS)
```
If `tests/` is not importable as a package (`from tests.golden...` fails), add an empty `tests/__init__.py` only if one doesn't exist AND the full suite still collects; otherwise switch both files to `sys.path`-insert `tests/golden` and `import cases`.

- [ ] **Step 4: Generate and verify determinism**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 tools/regen_golden.py && PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_golden_reports.py -q`
Expected: 20 files written (3 charts × 5 tiers + 2 pairs × 2 tiers + 1 cross-candidate); test PASS (21 tests). Run the test **twice more** to confirm no nondeterminism (dict ordering, `datetime.now()` leaks). If any file differs between runs, find the leak (grep the diff for today's date) and pin it via the inputs — do not mask it.

Also record which golden charts have strength verdict `extreme`/`extreme_weak`: `grep -l "Extreme\|Very Strong\|Very Weak" tests/golden/*.md` → put the result in the report (Task 2 needs it).

- [ ] **Step 5: Full suite, commit**

```bash
git add tests/golden tests/test_golden_reports.py tools/regen_golden.py
git commit -m "test: P2 golden-snapshot harness for all report generators"
```

---

### Task 2: `report_primitives.py` + migrate the report modules

**Files:**
- Create: `src/saju_engine/report_primitives.py`
- Create: `tests/test_report_primitives.py`
- Modify: `career_report.py`, `luck_cycle_report.py`, `cross_candidate_report.py`, `prose_scaffold.py`, `prose_fillers.py`, `compat_report.py`, `sewoon.py`, `report_data.py`, `premium_report.py` (only the import/usage sites named below)

**Interfaces (Produces — exact names later tasks use):**
```python
TENGOD_CLASS: Dict[str, str]          # 비견→Companion … 정인→Resource (five classes)
TENGOD_SHORT_EN: Dict[str, str]       # 비견→Companion, 겁재→Robber, … (ten names)
CLASS_KO: Dict[str, str]              # Companion→"비겁 (比劫)" …
CLASS_ORDER: List[str]                # ["Companion","Output","Wealth","Authority","Resource"]
ELEMENT_EMOJI: Dict[str, str]         # moved from report_data (re-exported there)
ELEMENT_COLORS: Dict[str, str]        # moved from report_data (re-exported there)
def verdict_label(verdict: str) -> str
def favorability(stem_e, branch_e, favorable, supporting, unfavorable) -> str  # "favorable"|"neutral"|"unfavorable"
def plain(text: str) -> str
def bar(pct: float, width: int = 20) -> str
def first_period_start(chart) -> Optional[date]
```

- [ ] **Step 1: Write the failing primitive tests** (`tests/test_report_primitives.py`)

```python
from saju_engine import report_primitives as RP


def test_tengod_tables_cover_all_ten():
    assert set(RP.TENGOD_CLASS) == set(RP.TENGOD_SHORT_EN) == {
        "비견", "겁재", "식신", "상관", "편재", "정재", "편관", "정관", "편인", "정인"}
    assert RP.TENGOD_CLASS["상관"] == "Output"
    assert RP.TENGOD_SHORT_EN["상관"] == "Hurting Officer"
    assert set(RP.TENGOD_CLASS.values()) == set(RP.CLASS_ORDER) == set(RP.CLASS_KO)


def test_verdict_label_is_symmetric():
    assert RP.verdict_label("extreme") == "Very Strong"
    assert RP.verdict_label("extreme_weak") == "Very Weak"
    assert RP.verdict_label("strong") == "Strong"
    assert RP.verdict_label("weak") == "Weak"
    assert RP.verdict_label("balanced") == "Balanced"
    assert RP.verdict_label("") == "Balanced"


def test_favorability_rule():
    f = RP.favorability
    assert f("Metal", "Earth", "Water", "Metal", "Fire") == "favorable"   # 희신 hit
    assert f("Fire", "Earth", "Water", "Metal", "Fire") == "unfavorable"
    assert f("Water", "Fire", "Water", "Metal", "Fire") == "neutral"      # F-7 wash
    assert f("Earth", "Earth", "Water", "—", None) == "neutral"
    assert f("Water", "Earth", "Water", None, "—") == "favorable"        # sentinels ignored


def test_plain_and_bar():
    assert RP.plain("x") == "> **In plain words:** x"
    assert RP.bar(50, 10) == "█████░░░░░"
    assert RP.bar(43.4) == "█" * 9 + "░" * 11
```

Run: `PYTHONPATH=... python3 -m pytest tests/test_report_primitives.py -v` → FAIL (`No module named saju_engine.report_primitives`).

- [ ] **Step 2: Create `src/saju_engine/report_primitives.py`**

```python
"""Shared report-layer primitives (B4, 2026-10-01 audit).

Every report generator (premium, compat, career, luck-cycle, cross-candidate)
used to carry its own copy of these tables/helpers, and the copies drifted
(S2/S3 were live client-visible consequences). Import from here; never
re-declare a copy in a report module.
"""
from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from . import lookup as L
from .daeun import first_period_start_date

# Five broad 십신 classes keyed by the KOREAN ten-god code. Classify by this,
# never by substring of an English gloss (prose_fillers 2026-09-19 bug).
TENGOD_CLASS: Dict[str, str] = {
    "비견": "Companion", "겁재": "Companion",
    "식신": "Output", "상관": "Output",
    "편재": "Wealth", "정재": "Wealth",
    "편관": "Authority", "정관": "Authority",
    "편인": "Resource", "정인": "Resource",
}

# Short English ten-god names (lookup.TENGOD_EN without the Hanja suffix).
TENGOD_SHORT_EN: Dict[str, str] = {
    k: v.split(" (")[0] for k, v in L.TENGOD_EN.items()
}

CLASS_KO: Dict[str, str] = {
    "Companion": "비겁 (比劫)",
    "Output": "식상 (食傷)",
    "Wealth": "재성 (財星)",
    "Authority": "관성 (官星)",
    "Resource": "인성 (印星)",
}

CLASS_ORDER: List[str] = ["Companion", "Output", "Wealth", "Authority", "Resource"]

ELEMENT_COLORS: Dict[str, str] = {
    "Wood": "#27ae60", "Fire": "#e74c3c", "Earth": "#f39c12",
    "Metal": "#7f8c8d", "Water": "#3498db",
}

ELEMENT_EMOJI: Dict[str, str] = {
    "Wood": "🟢", "Fire": "🔴", "Earth": "🟡", "Metal": "⚪", "Water": "🔵",
}

_VERDICT_LABELS: Dict[str, str] = {
    "extreme": "Very Strong", "strong": "Strong", "balanced": "Balanced",
    "weak": "Weak", "extreme_weak": "Very Weak",
}


def verdict_label(verdict: str) -> str:
    """Client-facing label for a strength verdict. B4: replaces four copies,
    three of which printed "Extreme" for `extreme` (asymmetric with "Very Weak")."""
    return _VERDICT_LABELS.get(verdict or "balanced", "Balanced")


def _real(e: Optional[str]) -> Optional[str]:
    return e if e and e != "—" else None


def favorability(stem_e: Optional[str], branch_e: Optional[str],
                 favorable: Optional[str], supporting: Optional[str],
                 unfavorable: Optional[str]) -> str:
    """The single favorable/neutral/unfavorable rule (S3 + F-7): a 용신 or 희신
    hit is favorable, a 기신 hit unfavorable, both at once a wash (neutral).
    "—"/None sentinels never match."""
    hits = {stem_e, branch_e}
    good = {e for e in (_real(favorable), _real(supporting)) if e}
    bad = _real(unfavorable)
    fav_hit = bool(good & hits)
    unfav_hit = bad is not None and bad in hits
    if fav_hit and unfav_hit:
        return "neutral"
    if fav_hit:
        return "favorable"
    if unfav_hit:
        return "unfavorable"
    return "neutral"


def plain(text: str) -> str:
    """Wrap a lay restatement as a single-line 'In plain words' blockquote."""
    return f"> **In plain words:** {text}"


def bar(pct: float, width: int = 20) -> str:
    """ASCII presence bar: round(pct/100*width) filled cells of `width`."""
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def first_period_start(chart) -> Optional[date]:
    """Precise calendar date the first 대운 decade begins (N-4)."""
    try:
        by, bm, bd = (int(x) for x in chart.birth_date.split("-"))
    except (ValueError, AttributeError):
        return None
    bh, bmi = 0, 0
    try:
        bh, bmi = (int(x) for x in (chart.birth_time or "00:00").split(":"))
    except (ValueError, AttributeError):
        pass
    direction = L.daeun_direction(chart.year.stem, chart.gender)
    return first_period_start_date(
        by, bm, bd, direction, hour=bh, minute=bmi,
        utc_offset=getattr(chart, "utc_offset", 9.0) or 9.0,
    )
```
If importing `daeun` here creates a cycle, import `first_period_start_date` inside `first_period_start`.

Run the primitive tests → PASS.

- [ ] **Step 3: Migrate consumers (golden must stay byte-identical except the verdict label)**

| File | Replace | With |
|---|---|---|
| `career_report.py` | `_CLASS_OF`, `_CLASS_KO`, `_first_start`, `_year_status`, `_verdict_label` | `RP.TENGOD_CLASS`, `RP.CLASS_KO`, `RP.first_period_start`, `RP.favorability`, `RP.verdict_label` (keep `_decade_year_range`, now calling `RP.first_period_start`) |
| `luck_cycle_report.py` | `_CLASS_OF`, `_CLASS_KO`, `_CLASS_ORDER`, `_first_start_date`, `year_status` body, `_verdict_label` | RP equivalents; keep the public name `year_status` as a thin wrapper `return RP.favorability(...)` (it is imported elsewhere — grep first) |
| `cross_candidate_report.py` | inline class dict in `_class_counts`, `_CLASS_ORDER`, import of private `_CLASS_KO` from luck_cycle_report | `RP.TENGOD_CLASS`, `RP.CLASS_ORDER`, `RP.CLASS_KO`. Rename `luck_cycle_report._build_blocks` → `build_blocks` (keep `_build_blocks = build_blocks` alias for one release) and import the public name |
| `prose_scaffold.py` | `_TENGOD_CLASS` | `RP.TENGOD_CLASS` |
| `prose_fillers.py` | `_TENGOD_FIVE_CLASS`, `_TENGOD_CLASS`, `_plain`, `_display_verdict`; body of `period_favorable_status` | `RP.TENGOD_CLASS`, `RP.TENGOD_SHORT_EN`, `RP.plain`, `RP.verdict_label`; `period_favorable_status` returns `RP.favorability(period.stem_element, period.branch_element, fav, sup, unfav)` (keep its docstring + dated notes). Keep module aliases `_TENGOD_FIVE_CLASS = RP.TENGOD_CLASS` because `premium_report.py:1454` uses `PF._TENGOD_FIVE_CLASS` — then change that call site to `RP.TENGOD_CLASS` and drop the alias. |
| `compat_report.py` | `_ELEMENT_EMOJI`, `_plain`, `_bar` | `RP.ELEMENT_EMOJI`, `RP.plain`, `RP.bar(pct, 10)` |
| `sewoon.py` | 3 inline ten-god English dicts (~`:325`, `:486`, `:554`) | `RP.TENGOD_SHORT_EN.get(tengod, tengod)` |
| `report_data.py` | `ELEMENT_COLORS`, `ELEMENT_EMOJI` definitions, `_bar`, `_strength_label` body | `from .report_primitives import ELEMENT_COLORS, ELEMENT_EMOJI` (keeps the public names — `saju_html` imports them); `_bar = RP.bar`; `_strength_label` returns `RP.verdict_label(sa.get("verdict", "balanced"))` |

Import style in each module: `from . import report_primitives as RP`. After each file, run `python3 -m pytest tests/test_golden_reports.py -q`.

- [ ] **Step 4: Golden check**

Run: `PYTHONPATH=... python3 -m pytest tests/test_golden_reports.py -q`
- PASS → no client output changed (the golden charts had no `extreme` verdict).
- FAIL → inspect: `python3 - <<'EOF'` script that prints a unified diff of each failing file vs `golden_outputs()`. If and only if every differing line is `Extreme` → `Very Strong`, run `tools/regen_golden.py` and list the changed lines in the report. Anything else: fix the code.

- [ ] **Step 5: No stale copies remain**

Run: `grep -n "\"비견\": \"Companion\"\|_CLASS_KO *=\|_CLASS_ORDER *=\|def _verdict_label\|def _display_verdict\|def _plain\|def _bar\|_ELEMENT_EMOJI *=" src/saju_engine/*.py`
Expected: matches only in `report_primitives.py`.

- [ ] **Step 6: Full suite + validation + commit**

```bash
git add src/saju_engine tests/test_report_primitives.py tests/golden
git commit -m "refactor: B4 extract report_primitives; migrate report modules"
```

---

### Task 3: Core lookup-table dedup (engine)

**Files:**
- Modify: `src/saju_engine/lookup.py`, `strength.py:39`, `yongsin.py:110`, `climate.py:57`, `pillars.py:113, 426-432, 520-523, 150-151`, `sewoon.py:93-105, 459`
- Test: `tests/test_lookup.py` (append)

**Interfaces:** Produces `lookup.GENERATED_BY: Dict[str, str]`, `lookup.FIVE_TIGERS: Dict[str, str]` (public rename of `_OHO_DUN`, keep `_OHO_DUN = FIVE_TIGERS` alias), `lookup.JIAZI_ANCHOR_YEAR: int = 1984`.

- [ ] **Step 1: Failing test (append to `tests/test_lookup.py`)**

```python
def test_core_tables_have_single_home():
    """B4 (2026-10-01 audit): inverse-cycle ×3, 五虎遁 ×2, 1984 anchor ×2 and
    branch order ×2 now live only in lookup.py."""
    from saju_engine import climate, lookup as L, pillars, sewoon, strength, yongsin

    assert L.GENERATED_BY == {v: k for k, v in L.GENERATES.items()}
    assert strength._GENERATED_BY is L.GENERATED_BY
    assert yongsin._GENERATED_BY is L.GENERATED_BY
    assert climate._GENERATED_BY is L.GENERATED_BY
    assert pillars._FIVE_TIGERS is L.FIVE_TIGERS
    assert pillars._BRANCH_ORDER is L.BRANCH_ORDER
    assert pillars._YEAR_CYCLE_ANCHOR == sewoon._ANCHOR_YEAR == L.JIAZI_ANCHOR_YEAR == 1984
```
Run → FAIL (`AttributeError: GENERATED_BY`).

- [ ] **Step 2: Implement**

In `lookup.py` (after `GENERATES` and `_OHO_DUN` are defined):
```python
# B4 (2026-10-01 audit): single home for the inverse generating cycle
# (was re-derived in strength.py, yongsin.py and climate.py).
GENERATED_BY: Dict[str, str] = {v: k for k, v in GENERATES.items()}

# 五虎遁 (오호둔): year stem → 寅-month stem. Public name for _OHO_DUN
# (pillars.py kept a second hand-typed copy, _FIVE_TIGERS).
FIVE_TIGERS: Dict[str, str] = _OHO_DUN

# 甲子 anchor year for the 60-year cycle (pillars.py and sewoon.py each kept one).
JIAZI_ANCHOR_YEAR = 1984
```
Before replacing `pillars._FIVE_TIGERS`, assert equality once: `python3 -c "from saju_engine import lookup as L, pillars as P; assert P._FIVE_TIGERS == L._OHO_DUN"` — if it fails, STOP and report (a real doctrinal divergence).
Then: `strength._GENERATED_BY = L.GENERATED_BY`, same in `yongsin`, `climate`; `pillars._FIVE_TIGERS = L.FIVE_TIGERS`, `pillars._BRANCH_ORDER = L.BRANCH_ORDER`, `pillars._YEAR_CYCLE_ANCHOR = L.JIAZI_ANCHOR_YEAR`, `sewoon._ANCHOR_YEAR = L.JIAZI_ANCHOR_YEAR`, `sewoon.py:459` uses `L.FIVE_TIGERS`. Keep the module-level private names as aliases (tests and fixtures may reference them).

- [ ] **Step 3: Verify** — test PASS; golden PASS (byte-identical); full suite; `tools/run_validation.py` exit 0 with identical counts.

- [ ] **Step 4: Commit** — `refactor(lookup): B4 single home for inverse cycle, 五虎遁, cycle anchor, branch order`

---

### Task 4: B8 — two named in-season primitives

**Files:**
- Modify: `src/saju_engine/lookup.py`, `compat.py:188-197`, `patterns.py:140-160`, `prose_fillers.py:1858-1870`, `report_data.py:384-395`
- Test: `tests/test_lookup.py` (append)

**Interfaces:** Produces
```python
lookup.element_rules_month(element: str, month_branch: str) -> bool
lookup.season_supports(element: str, month_branch: str) -> bool
```

- [ ] **Step 1: Failing tests**

```python
def test_element_rules_month_is_branch_element_equality():
    from saju_engine import lookup as L
    for b, e in L.BRANCH_ELEMENT.items():
        assert L.element_rules_month(e, b)
        assert not L.element_rules_month("Nope", b)
    assert not L.element_rules_month("Earth", "")


def test_season_supports_uses_seasonal_groups():
    """Distinct doctrine from element_rules_month: 辰 (Earth branch) still
    supports Wood (spring), 丑 supports Water (winter), and every 季月
    (辰戌丑未) supports Earth."""
    from saju_engine import lookup as L
    assert L.season_supports("Wood", "辰")
    assert L.season_supports("Water", "丑")
    assert L.season_supports("Metal", "戌")
    assert all(L.season_supports("Earth", b) for b in "辰戌丑未")
    assert not L.season_supports("Fire", "子")
```
Run → FAIL.

- [ ] **Step 2: Implement in `lookup.py`**

```python
# B8 (2026-10-01 audit): "in season" was implemented four times. They are two
# distinct doctrines, each now with one home:
#
# element_rules_month — the element IS the month branch's own element
#   (BRANCH_ELEMENT equality). Used for 합화 season tests (knowledge/11-gunghap.md
#   §A step 3; knowledge/02-branches.md 육합) and pattern-breaker strength
#   (knowledge/07-special-formations.md).
# season_supports — the month falls in the element's SEASON group (spring
#   寅卯辰 Wood, summer 巳午未 Fire, autumn 申酉戌 Metal, winter 亥子丑 Water,
#   季月 辰戌丑未 Earth). Used for Day-Master seasonal support (report_data).
def element_rules_month(element: str, month_branch: str) -> bool:
    return bool(month_branch) and BRANCH_ELEMENT.get(month_branch) == element


_SEASON_GROUPS: Dict[str, str] = {
    "Wood": "寅卯辰", "Fire": "巳午未", "Earth": "辰戌丑未",
    "Metal": "申酉戌", "Water": "亥子丑",
}


def season_supports(element: str, month_branch: str) -> bool:
    return bool(month_branch) and month_branch in _SEASON_GROUPS.get(element, "")
```

- [ ] **Step 3: Rewire call sites (behaviour-preserving)**
- `compat._element_in_season(element, branch)` body → `return L.element_rules_month(element, branch)` (keep docstring).
- `patterns._breaker_is_powerful`: the in-season line → `if breaker_elem and L.element_rules_month(breaker_elem, month_branch): return True`.
- `prose_fillers.six_combination_transforms`: replace the `month_elem` lines with `if not L.element_rules_month(elem, chart.month.branch): return False`. (All `SIX_COMBINATIONS` elements are single words, so the old substring test `month_elem not in elem` was equivalent to inequality — add that sentence to the comment.)
- `report_data._day_master_in_season` body → `return L.season_supports(chart.day_master_info.get("element", ""), chart.month.branch)`.

- [ ] **Step 4: Verify** — tests PASS; golden byte-identical; full suite; validation identical.
- [ ] **Step 5: Commit** — `refactor(lookup): B8 one named primitive per in-season doctrine`

---

### Task 5: S6 — typed compat flags

**Files:**
- Modify: `src/saju_engine/compat.py` (Flag type; all `flags.append(...)` sites — 63 at plan time; `_classify_flag`, `_flag_severity`, the cover aggregation ~`:1501-1512`)
- Modify: `src/saju_engine/compat_report.py` (the `any("육충" in f ...)`-style checks listed by `grep -n '" in f for f in' src/saju_engine/compat_report.py`)
- Test: `tests/test_compat_flags.py` (create)

**Interfaces:** Produces
```python
class Flag(str):
    kind: Optional[str]      # "red" | "yellow" | "favorable" | None
    severity: int            # cover ranking weight (0 if not red)
    code: str                # stable machine code, e.g. "daybranch.clash"
    def __new__(cls, text: str, *, kind: Optional[str], code: str, severity: int = 0) -> "Flag"
```
Because `Flag` subclasses `str`, rendering (`", ".join(...)`, f-strings, PDF translation maps) is unchanged.

- [ ] **Step 1: Write the equivalence test FIRST (pins today's behaviour)**

```python
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


def _all_flags(report):
    for sub in report.sub_systems():
        yield from sub.flags


@pytest.mark.parametrize("i,j", PAIRS)
def test_every_flag_is_typed_and_matches_legacy_classification(i, j):
    report = compat.compat_score(CHARTS[i], CHARTS[j])
    for flag in _all_flags(report):
        assert isinstance(flag, compat.Flag), repr(flag)
        assert flag.kind == compat._legacy_classify_flag(str(flag)), flag
        assert flag.severity == compat._legacy_flag_severity(str(flag)), flag
        assert flag.code
```
(`report.sub_systems()` exists — `compat.py` `CompatReport.sub_systems`; check its exact name with `grep -n "def sub_systems" src/saju_engine/compat.py` and adjust.)

- [ ] **Step 2: Rename the substring classifiers to legacy, run the test → FAIL**

Rename `_classify_flag` → `_legacy_classify_flag` and `_flag_severity` → `_legacy_flag_severity` (bodies unchanged; docstring: "Kept only as the oracle for tests/test_compat_flags.py — production code reads Flag.kind/severity."). Add the `Flag` class (below). Test fails: flags are plain `str`.

```python
class Flag(str):
    """A compat tag with its classification attached (S6, 2026-10-01 audit).

    Subclasses str so every renderer keeps working; consumers must read
    ``kind``/``severity``/``code`` instead of substring-matching the text."""

    kind: Optional[str]
    severity: int
    code: str

    def __new__(cls, text: str, *, kind: Optional[str], code: str,
                severity: int = 0) -> "Flag":
        obj = super().__new__(cls, text)
        obj.kind = kind
        obj.code = code
        obj.severity = severity
        return obj
```

- [ ] **Step 3: Type every emission site**

For each `flags.append(<text>)` in `compat.py`, wrap as `flags.append(Flag(<text>, kind=..., code="<subsystem>.<what>", severity=...))`, choosing `kind`/`severity` to equal what `_legacy_classify_flag`/`_legacy_flag_severity` return for that text (read the legacy token lists; e.g. a `육충` day-branch flag → `kind="red", severity=25, code="daybranch.clash"`). Codes: `<sub-system key from WEIGHT>.<snake_case meaning>`; must be unique per distinct meaning and stable (no numbers/elements inside the code).

Then switch production consumers to the type:
- cover aggregation (~`compat.py:1501-1512`): `bucket = flag.kind`; sort key `(-flag.severity, str(flag))`.
- `compat_report.py`: replace each `any("<token>" in f for f in X.flags)` / `"RED FLAG" in " ".join(...)` with a code check, e.g. `any(f.code == "daybranch.clash" for f in db.flags)`. Use a tiny helper in compat_report: `def _has(flags, *codes): return any(getattr(f, "code", None) in codes for f in flags)`.

Run the equivalence test → PASS for all 28 pairs.

- [ ] **Step 4: No production substring classification remains**

Run: `grep -n '" in f\b\|in " ".join(\|_legacy_classify_flag\|_legacy_flag_severity' src/saju_engine/*.py`
Expected: only the two legacy definitions in `compat.py`.

- [ ] **Step 5: Verify** — golden byte-identical (flags render identically); full suite; validation identical (27 compat fixtures).
- [ ] **Step 6: Commit** — `refactor(compat): S6 typed Flag carries kind/severity/code; no prose parsing`

---

### Task 6: Docs + tracker

**Files:** `docs/issues_bugs.md` (Audit 2026-10-01 table), `docs/MEMORY.md`, `docs/openwiki/architecture/engine.md`

- [ ] **Step 1:** Mark B4, B8, S6 (and B6) FIXED with commit SHAs; note the deliberate exclusions (organs wording, compat F verdict) from "Decisions recorded up front". Note the one client-visible change: strength label `Extreme` → `Very Strong` in career / luck-cycle / prose-filler text.
- [ ] **Step 2:** MEMORY.md "Conventions": add "Report tables/helpers live in `src/saju_engine/report_primitives.py`; never re-declare a copy. Golden snapshots in `tests/golden/` — regenerate with `tools/regen_golden.py` only for a reviewed output change."
- [ ] **Step 3:** engine.md module map: add `report_primitives.py`, `lookup.element_rules_month` / `season_supports`, `compat.Flag`.
- [ ] **Step 4:** Full suite + validation; commit `docs: record P2 report-primitives refactor`.
