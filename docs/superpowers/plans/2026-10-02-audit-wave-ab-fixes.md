# Audit 2026-10-01 — Wave A + B Correctness Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Source:** `/mnt/data2/git_repos/research-engine/output/2026-10-01/saju-engine-audit-2026-10-01.md` (§3 S1–S8, §9 Waves A/B).

**Goal:** Fix the audit's verified client-visible correctness bugs (S1 대운/세수 timezone, S2 compat element-balance drift, S3 compat favorability gap, S7 ₹ prices, S8b/c compat endpoint) and the cheap Wave-A hygiene items (S5 dead stdlib servers, machine-coupled test, dead code, stale docs).

**Architecture:** Every fix is local and test-first. No new modules. Compat display is re-pointed at the canonical natal functions (`strength.element_balance_pct`, `prose_fillers.period_favorable_status`) so natal and compat products cannot disagree; the compat *scoring* math (knowledge/11-gunghap.md §F weights) is left untouched so no published composite score moves.

**Tech Stack:** Python 3.10–3.12, pytest, FastAPI (tools/client_intake_app.py), sajupy 0.2.0.

## Global Constraints

- Test command prefix (until Task 7 lands, some tests need it): `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages`
- Baseline before starting: `python3 -m pytest tests/ -q` → **1206 passed, 5 skipped, 9 xfailed**. Every task must end with zero new failures.
- Validation gate must stay green: `python3 tools/run_validation.py` exits 0.
- Every bug-fix code comment carries a dated audit citation in the house style: `# S1 (2026-10-01 audit): ...`.
- USD prices (CLAUDE.md "Tiered Client Products", verbatim): Essential **$19** (intro $9), Deep **$55**, Compat Snapshot **$24**, Compat Deep **$45**.
- Do not change `compat.WEIGHT` or any compat scoring threshold — published scores must not move.
- Branch: work on `fix/audit-2026-10-01-wave-ab` off `develop`; one commit per task.

## Verified status vs. the audit (checked 2026-10-02)

| Audit item | Status |
|---|---|
| S1 대운 age TZ | **Reproduced**: NY birth 2024-02-04 10:00 (UTC−5) → year pillar 甲辰 but `current_age`=4 at 2026-06-01 (correct: 3). → Task 1 |
| S2 dual element balance | Confirmed (`compat_report.py:94` uses `compat._element_strength`). → Task 3 |
| S3 compat favorability | Confirmed (`compat_report.py:130-139` checks `fe.element` only). → Task 2 |
| S5 stdlib servers | Confirmed. → Task 6 |
| S7 ₹ prices | Confirmed in 3 forms, 7 occurrences. → Task 4 |
| S8b/S8c compat endpoint | Confirmed (`client_intake_app.py:267,273` `Form(5.5)`; save at `:305` before validation at `:319`). → Task 5 |
| A5 machine PYTHONPATH | Confirmed (`tests/test_compat_pdf_cli.py:23`). → Task 7 |
| A6 stale CLAUDE.md | Confirmed (`CLAUDE.md:94-96`). → Task 9 |
| A7 dead code | Confirmed, **except** `nayin_relation` — it is exported public API with tests (`tests/test_nayin.py`); keep it. → Task 8 |
| **B5 weight invariant** | **Already done** — `tests/validation/test_val_compat.py:169` pins total 112 / scored 100. (The audit's "88" figure is wrong.) No task. |
| A1 landing-page `src/` | **Blocked — not on this machine.** Needs the user to locate the working copy. Not in this plan. |

---

### Task 1: S1 — timezone-aware 사주 year / 세수 (대운 age boundary)

**Files:**
- Modify: `src/saju_engine/daeun.py:39-103` (`saju_year`, `saju_age`)
- Modify: `src/saju_engine/engine.py:303`
- Modify: `src/saju_engine/luck_cycle_report.py:117-130` (`_saju_year_of_birth`)
- Modify: `src/saju_engine/premium_report.py:1897`, `src/saju_engine/prose_scaffold.py:252`
- Test: `tests/test_daeun_timezone.py` (create)

**Interfaces:**
- Produces: `saju_year(d: date | datetime, utc_offset: float = 9.0) -> int`; `saju_age(birth_date_str, today=None, birth_time_str=None, utc_offset: float = 9.0) -> Optional[int]`. Default 9.0 keeps every existing caller's behaviour.

- [ ] **Step 1: Write the failing test**

```python
"""S1 (2026-10-01 audit): the 세수/age path compared a naive LOCAL birth
datetime against the KST-wall-clock 입춘 instant, while the pillar path
shifts terms by (utc_offset - 9). 2024 立春 = 2024-02-04 17:27 KST = 03:27 EST,
so a New York birth on Feb 4 between 03:27 and 17:26 local got the 2024 (甲辰)
year pillar but was aged as a 2023 (癸卯) birth."""
from datetime import date, datetime

from saju_engine.daeun import saju_age, saju_year
from saju_engine.engine import compute_chart


def test_saju_year_shifts_ipchun_into_local_time():
    # 10:00 EST = 00:00 KST Feb 5 -> after 立春 in absolute time.
    assert saju_year(datetime(2024, 2, 4, 10, 0), utc_offset=-5.0) == 2024
    # 03:00 EST = 17:00 KST -> still before 立春 (17:27 KST).
    assert saju_year(datetime(2024, 2, 4, 3, 0), utc_offset=-5.0) == 2023


def test_saju_year_default_is_kst_unchanged():
    assert saju_year(datetime(2024, 2, 4, 10, 0)) == 2023
    assert saju_year(datetime(2024, 2, 4, 17, 30)) == 2024
    assert saju_year(date(2024, 2, 5)) == 2024


def test_saju_age_threads_offset():
    ref = date(2026, 6, 1)
    assert saju_age("2024-02-04", ref, "10:00", utc_offset=-5.0) == 3
    assert saju_age("2024-02-04", ref, "10:00") == 4  # KST birth: before 立春


def test_chart_age_agrees_with_year_pillar_for_new_york_birth():
    kw = dict(year=2024, month=2, day=4, minute=0, gender="F",
              utc_offset=-5.0, longitude=-74.0,
              reference_year=2026, reference_month=6, reference_day=1)
    after = compute_chart(hour=10, **kw)
    assert after.year.stem + after.year.branch == "甲辰"
    assert after.current_age == 3
    before = compute_chart(hour=3, **kw)
    assert before.year.stem + before.year.branch == "癸卯"
    assert before.current_age == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_daeun_timezone.py -v`
Expected: FAIL — `TypeError: saju_year() got an unexpected keyword argument 'utc_offset'`; `test_chart_age_agrees...` fails with `assert 4 == 3`.

- [ ] **Step 3: Implement in `daeun.py`**

Replace the body/signature of `saju_year` (keep the existing N-18/N-11 docstring paragraphs, fix the `입춀` typos to `입춘` while there, and append the S1 paragraph):

```python
def saju_year(d: Union[date, datetime], utc_offset: float = 9.0) -> int:
    """...existing docstring...

    S1 (2026-10-01 audit): the 입춘 instant is stored in KST wall clock, but
    `d` is the querent's LOCAL wall clock. The pillar path already shifts
    terms by (utc_offset - 9) (pillars.py `_independent_year_month_pillar`);
    this path compared them naively, so for any non-KST chart the 세수 /
    current-대운 boundary sat up to ~14 h away from the year-pillar boundary.
    `utc_offset` defaults to KST (9.0 == KST_OFFSET_HOURS) so existing
    callers are unchanged.
    """
    ipchun = _ipchun_date(d.year)
    if ipchun is None:
        return d.year
    ipchun = ipchun + timedelta(hours=utc_offset - 9.0)
    if isinstance(d, datetime):
        return d.year - 1 if d < ipchun else d.year
    return d.year - 1 if d < ipchun.date() else d.year
```

(The default is the literal `9.0` because `KST_OFFSET_HOURS` is defined further down the module, after this function.)

In `saju_age`, add the parameter and pass it to both calls:

```python
def saju_age(
    birth_date_str: str,
    today: Optional[date] = None,
    birth_time_str: Optional[str] = None,
    utc_offset: float = 9.0,
) -> Optional[int]:
    ...
    return saju_year(today, utc_offset) - saju_year(birth, utc_offset) + 1
```

- [ ] **Step 4: Thread the offset through the callers**

`engine.py:303`:
```python
    # S1 (2026-10-01 audit): pass the birth offset so the 입춘 boundary is
    # compared in the querent's local clock, matching the year pillar.
    chart.current_age = D.saju_age(chart.effective_date, ref_date, chart.birth_time, chart.utc_offset)
```
`luck_cycle_report.py:130`:
```python
    return saju_year(datetime(by, bm, bd, bh, bmi), chart.utc_offset)
```
`premium_report.py:1897`: `f"{saju_year(ref, chart.utc_offset)} is a **..."`
`prose_scaffold.py:252`: `f"As of {saju_year(ref, chart.utc_offset)}, the annual pillar ..."`

- [ ] **Step 5: Run the new test and the full suite + validation gate**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/ -q && python3 tools/run_validation.py`
Expected: new tests PASS; totals = baseline + 4 passed; validation exits 0. If any existing fixture changes, it is a non-KST birth inside the window — inspect it, don't loosen the test.

- [ ] **Step 6: Commit**

```bash
git add src/saju_engine/daeun.py src/saju_engine/engine.py src/saju_engine/luck_cycle_report.py src/saju_engine/premium_report.py src/saju_engine/prose_scaffold.py tests/test_daeun_timezone.py
git commit -m "fix(daeun): S1 compare 입춘 in local time for 세수/current 대운"
```

---

### Task 2: S3 — compat favorability uses the shared rule (희신 + 기신)

**Files:**
- Modify: `src/saju_engine/compat_report.py:130-139` (`_period_status`)
- Test: `tests/test_compat_report_parity.py` (create; Task 3 appends to it)

**Interfaces:**
- Consumes: `prose_fillers.period_favorable_status(period, ctx)` — `ctx` may be a dict with keys `favorable`, `supporting`, `unfavorable`.
- Produces: `_period_status(period, fe: FavorableElement) -> str` (signature unchanged).

- [ ] **Step 1: Write the failing test**

```python
"""Cross-report parity: compat must render the same numbers/labels as the
natal products for the same chart (audit 2026-10-01 S2/S3)."""
from types import SimpleNamespace

from saju_engine.compat_report import _period_status
from saju_engine.yongsin import FavorableElement

FE = FavorableElement(element="Water", method="weak-dm-support",
                      confidence="heuristic", note="", supporting="Metal",
                      unfavorable="Fire")


def _p(stem_e, branch_e):
    return SimpleNamespace(stem_element=stem_e, branch_element=branch_e)


def test_supporting_element_decade_is_favorable():
    assert _period_status(_p("Metal", "Earth"), FE) == "favorable"


def test_unfavorable_element_decade_is_unfavorable():
    assert _period_status(_p("Fire", "Earth"), FE) == "unfavorable"


def test_mixed_decade_is_neutral():
    assert _period_status(_p("Water", "Fire"), FE) == "neutral"
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_compat_report_parity.py -v`
Expected: `test_supporting...` FAIL (`'neutral' == 'favorable'`), `test_unfavorable...` FAIL, `test_mixed...` FAIL (returns `favorable`).

- [ ] **Step 3: Implement**

Add the import near the top of `compat_report.py`:
```python
from .prose_fillers import period_favorable_status
```
Replace `_period_status`:
```python
def _period_status(period, fe) -> str:
    """Favorable/neutral/unfavorable lean vs. the FINAL resolved element
    set ``fe`` (already reflecting any reader override from ``compat_score``).

    S3 (2026-10-01 audit): this used to check ``fe.element`` only, dropping
    the 희신 and 기신 checks every other product applies — a 희신 decade read
    "favorable" in the natal report but "neutral" here. It now delegates to
    the single shared rule in ``prose_fillers.period_favorable_status``.
    """
    return period_favorable_status(period, {
        "favorable": fe.element if fe.element and fe.element != "—" else None,
        "supporting": fe.supporting if fe.supporting and fe.supporting != "—" else None,
        "unfavorable": fe.unfavorable,
    })
```

- [ ] **Step 4: Run tests**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_compat_report_parity.py tests/ -q`
Expected: all PASS. If an import cycle appears (`prose_fillers` ↔ `compat_report`), move the import inside `_period_status`.

- [ ] **Step 5: Commit**

```bash
git add src/saju_engine/compat_report.py tests/test_compat_report_parity.py
git commit -m "fix(compat): S3 major-luck favorability uses shared 용신/희신/기신 rule"
```

---

### Task 3: S2 — compat element-balance display uses the canonical natal numbers

**Decision (recommended, applied here):** the client-visible table switches to `strength.element_balance_pct` (same numbers as the natal report). The compat *scoring* helper keeps knowledge/11-gunghap.md §F weights, renamed to `_weighted_presence_pct` so nobody reuses it for display again. No composite score changes.

**Files:**
- Modify: `src/saju_engine/compat_report.py:23, 92-104`
- Modify: `src/saju_engine/compat.py:675` (rename + docstring) and its 6 call sites (`:712, 713, 731, 732, 926, 927`)
- Test: `tests/test_compat_report_parity.py` (append)

**Interfaces:**
- Consumes: `strength.element_balance_pct(chart) -> Dict[str, float]` (sums to exactly 100.0).
- Produces: `compat._weighted_presence_pct(chart) -> Dict[str, float]` (renamed from `_element_strength`, same math).

- [ ] **Step 1: Append the failing test**

```python
from saju_engine.compat_report import generate_compat_report
from saju_engine.engine import compute_chart
from saju_engine.strength import element_balance_pct


def test_compat_element_table_matches_natal_element_balance():
    a = compute_chart(year=1990, month=6, day=15, hour=10, minute=0,
                      gender="M", utc_offset=9.0, longitude=127.0)
    b = compute_chart(year=1992, month=3, day=20, hour=14, minute=0,
                      gender="F", utc_offset=9.0, longitude=127.0)
    md = generate_compat_report(a, b, "Alpha", "Beta", tier="deep")
    for name, chart in (("Alpha", a), ("Beta", b)):
        section = md.split(f"#### Element Balance — {name}", 1)[1].split("####", 1)[0]
        for elem, pct in element_balance_pct(chart).items():
            assert f"{elem} |" in section
            assert f"| {pct:.1f}% |" in section, (name, elem, pct)
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_compat_report_parity.py::test_compat_element_table_matches_natal_element_balance -v`
Expected: FAIL on the first element whose weighted-presence % differs from the canonical %.

- [ ] **Step 3: Implement**

`compat.py` — rename the function and rewrite its docstring:
```python
def _weighted_presence_pct(chart: Chart) -> Dict[str, float]:
    """Compat SCORING input only — knowledge/11-gunghap.md §F weighted
    presence (visible stems = 1; hidden main=1, middle=0.5, residual=0.3).

    S2 (2026-10-01 audit): this was also used to DISPLAY each partner's
    element balance, which then disagreed with the natal report's
    `strength.element_balance_pct` for the same person (measured: Water
    14.4% vs 43.4%). Display now uses the canonical function; this stays
    for the 용신 cross-supply / combined-element thresholds so published
    composite scores do not move. Never render these numbers to a client.
    """
```
Then update every call site: `sed -i 's/_element_strength(/_weighted_presence_pct(/g' src/saju_engine/compat.py`.

`compat_report.py` — fix the import line and the display helper:
```python
from .compat import WEIGHT, CompatReport, CompatSubResult, compat_score
from .strength import element_balance_pct
...
def _element_balance_lines(chart: Chart, name: str) -> List[str]:
    """Colored-emoji element balance table for one partner — the SAME
    numbers as the natal report (S2, 2026-10-01 audit)."""
    dist = element_balance_pct(chart)
```

- [ ] **Step 4: Verify combined-elements narrative doesn't print percentages to clients**

Run: `grep -n "dist_a\|dist_b" src/saju_engine/compat.py | sed -n 1,20p`
If the `combined_elements` narrative (around `compat.py:926-990`) formats `dist_a/dist_b` values into client text, switch only those *formatted* numbers to `element_balance_pct` and leave the threshold comparisons on `_weighted_presence_pct`.

- [ ] **Step 5: Run full suite + validation**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/ -q && python3 tools/run_validation.py`
Expected: all PASS; compat fixtures unchanged (scoring untouched).

- [ ] **Step 6: Commit**

```bash
git add src/saju_engine/compat.py src/saju_engine/compat_report.py tests/test_compat_report_parity.py
git commit -m "fix(compat): S2 element-balance table uses canonical natal percentages"
```

---

### Task 4: S7 — USD prices in client-facing forms

**Files:**
- Modify: `tools/client_intake_app.html:356, 371`
- Modify: `tools/client_compat_intake_form.html:163, 288, 289`
- (`tools/client_intake_form.html` is deleted in Task 6 — skip it here.)
- Test: `tests/test_client_intake_app.py` (append)

- [ ] **Step 1: Append the failing test**

```python
def test_client_forms_show_usd_not_rupee_prices():
    """S7 (2026-10-01 audit): forms still showed ₹799/₹1,499 after the
    2026-09-07 USD pivot."""
    for html_path in sorted((PROJECT_ROOT / "tools").glob("*.html")):
        assert "₹" not in html_path.read_text(encoding="utf-8"), html_path.name
    app_html = (PROJECT_ROOT / "tools" / "client_intake_app.html").read_text()
    assert "$19" in app_html and "$55" in app_html
    compat_html = (PROJECT_ROOT / "tools" / "client_compat_intake_form.html").read_text()
    assert "$24" in compat_html and "$45" in compat_html
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_client_intake_app.py::test_client_forms_show_usd_not_rupee_prices -v`
Expected: FAIL on `client_compat_intake_form.html` (or the first html with `₹`).

- [ ] **Step 3: Replace the strings**

`client_intake_app.html`:
- `:356` `<div class="tier-price">₹799 <small>6–7 pages</small></div>` → `<div class="tier-price">$19 <small>6–7 pages</small></div>`
- `:371` `<div class="tier-price">₹1,499 <small>10–12 pages</small></div>` → `<div class="tier-price">$55 <small>10–12 pages</small></div>`

`client_compat_intake_form.html`:
- `:163` `Basic ₹799 / Deep ₹1,499` → `Snapshot $24 / Deep $45`
- `:288` `(₹799)` → `($24)`
- `:289` `(₹1,499)` → `($45)`

- [ ] **Step 4: Run test** — Expected: PASS (it will still fail on `client_intake_form.html` until Task 6; if executing out of order, do Task 6 first or also patch that file's `:324,:339` the same way).

- [ ] **Step 5: Commit**

```bash
git add tools/client_intake_app.html tools/client_compat_intake_form.html tests/test_client_intake_app.py
git commit -m "fix(forms): S7 show USD tier prices in intake forms"
```

---

### Task 5: S8b + S8c — `/compat/generate` requires offsets and validates before persisting

**Files:**
- Modify: `tools/client_intake_app.py:261-328` (`compat_generate`)
- Test: `tests/test_client_intake_app.py` (append)

- [ ] **Step 1: Append the failing tests**

```python
def test_compat_generate_requires_explicit_utc_offsets():
    """S8b (2026-10-01 audit): /compat/generate still defaulted both offsets
    to Form(5.5) (India) after N-13 removed it from /generate."""
    import inspect

    params = inspect.signature(_load_app_module().compat_generate).parameters
    for name in ("utc_offset_a", "utc_offset_b"):
        assert params[name].default.is_required(), name


def test_compat_generate_validates_before_writing_intake(monkeypatch, tmp_path):
    """S8c (2026-10-01 audit): the intake JSON was written BEFORE gender/date
    validation, so rejected (possibly hostile) payloads accumulated as PII."""
    import asyncio

    import pytest
    from fastapi import HTTPException

    module = _load_app_module()
    monkeypatch.setattr(module, "INTAKE_DIR", tmp_path)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(module.compat_generate(
            name_a="A", dob_a="1990-06-15", birth_time_a="10:00",
            location_a="Seoul", utc_offset_a=9.0, gender_a="X",
            name_b="B", dob_b="1992-03-20", birth_time_b="14:00",
            location_b="Seoul", utc_offset_b=9.0, gender_b="F",
            email="t@example.com", main_concern="", favorable_element_a="",
            favorable_element_b="", timezone_a="", timezone_b="", tier="basic",
        ))
    assert exc.value.status_code == 400
    assert not list(tmp_path.rglob("*.json"))
```

- [ ] **Step 2: Run to verify failure**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_client_intake_app.py -k "offsets or validates_before" -v`
Expected: both FAIL (`is_required()` False; a `.json` file exists in tmp_path).

- [ ] **Step 3: Implement**

In the signature: `utc_offset_a: float = Form(...)` and `utc_offset_b: float = Form(...)`.

Move the two validation blocks (gender loop + `_parse_dob_time` try/except, currently `:318-328`) to directly after the `payload = {...}` dict and before `# Save raw intake.`, and annotate:
```python
    # S8c (2026-10-01 audit): validate BEFORE persisting — rejected payloads
    # must never be written to INTAKE_DIR as PII.
```

- [ ] **Step 4: Run the intake test file**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_client_intake_app.py -v`
Expected: all PASS (the N-14 test still passes offsets explicitly).

- [ ] **Step 5: Commit**

```bash
git add tools/client_intake_app.py tests/test_client_intake_app.py
git commit -m "fix(intake): S8b/S8c require compat offsets; validate before saving intake"
```

---

### Task 6: S5 — delete the stdlib intake servers and the orphaned JSON-only form

The FastAPI app (`tools/client_intake_app.py`) serves both flows (`/` and `/compat`) and already saves every intake as JSON. The compat stdlib server 404s every submission (form posts to `/compat/generate`, server only has `/submit`); the single server double-decodes JSON.

**Files:**
- Delete: `tools/client_intake_server.py`, `tools/client_compat_intake_server.py`, `tools/client_intake_form.html`, `tests/test_client_intake_server.py`
- Modify docs: `CLAUDE.md:183-188` ("Client Intake"), `README.md:89-94, 146-150`, `docs/openwiki/operations/toolchain-and-testing.md:23`, `docs/MEMORY.md:83`, `candidates_horoscope/README.md:62-67`

- [ ] **Step 1: Delete**

```bash
git rm tools/client_intake_server.py tools/client_compat_intake_server.py tools/client_intake_form.html tests/test_client_intake_server.py
```

- [ ] **Step 2: Confirm nothing else references them**

Run: `grep -rn "client_intake_server\|client_compat_intake_server\|client_intake_form.html" --include=*.py --include=*.sh --include=*.md --include=*.html . | grep -v "^./docs/superpowers\|^./candidates_horoscope/intake"`
Expected: only the doc lines listed above.

- [ ] **Step 3: Update docs**

Replace CLAUDE.md "Client Intake" items 1–2 with:
```markdown
**Self-service app** — `tools/client_intake_app.html` + `tools/client_compat_intake_form.html`, served by `tools/client_intake_app.py` (FastAPI; `/` single-chart, `/compat` two-chart). Every validated submission is saved as JSON in `candidates_horoscope/intake/` and a tiered PDF is returned. Requires the `web` optional dependencies (`pip install -e ".[web]"`). (The stdlib JSON-only servers were removed 2026-10-02 — audit S5.)
```
In the other four docs, delete the server/form rows and point to `tools/client_intake_app.py`.

- [ ] **Step 4: Run suite** — `PYTHONPATH=... python3 -m pytest tests/ -q` → baseline minus the deleted server tests, no failures.

- [ ] **Step 5: Commit**

```bash
git add -A tools tests CLAUDE.md README.md docs candidates_horoscope/README.md
git commit -m "chore(intake): S5 remove broken stdlib intake servers; FastAPI serves both flows"
```

---

### Task 7: A5 — remove the machine-coupled PYTHONPATH from the compat PDF CLI test

**Files:**
- Modify: `tests/test_compat_pdf_cli.py:20-24`

- [ ] **Step 1: Replace the ENV block**

```python
# A5 (2026-10-01 audit): this hard-coded /home/harish/.local/... and so only
# ran on one machine. Inherit the caller's PYTHONPATH (CI installs deps
# normally; locally build-pdf.sh / $SAJU_SITE provide it) and prepend src/.
ENV = {
    **os.environ,
    "PYTHONPATH": os.pathsep.join(
        p for p in (str(PROJECT_ROOT / "src"), os.environ.get("PYTHONPATH", "")) if p
    ),
}
```
Then add `pytest.importorskip("reportlab")` at the top of each test function that shells out to the renderer (add `import pytest` to the imports).

- [ ] **Step 2: Verify both ways**

Run: `PYTHONPATH=/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/test_compat_pdf_cli.py -v` → PASS.
Run: `grep -rn "/home/harish" tests/` → no output.

- [ ] **Step 3: Commit**

```bash
git add tests/test_compat_pdf_cli.py
git commit -m "test: A5 drop machine-specific PYTHONPATH from compat PDF CLI test"
```

---

### Task 8: A7 — delete dead code and dead statements

**Files / exact edits:**
- `src/saju_engine/stars.py:534-575` — delete `derive_star_positions` (zero callers).
- `src/saju_engine/pillars.py:756-765` — delete the `# Light validation...` comment and `pretty()`.
- `src/saju_engine/chart.py:332-337` — delete `pillar_table_rows`.
- `src/saju_engine/compat.py:1199-1200` — docstring: delete the sentence "For time-bound queries use the separate `compat_daeun_sync_at_year()` API (planned for v2)."
- `src/saju_engine/compat.py:1230-1231` — `a.daeun[0].stem if hasattr(a.daeun[0], "stem") else None` → `a.daeun[0].stem` (same for `b`); keep the `if start_a and start_b:` guard.
- `src/saju_engine/patterns.py:520` — delete the bare `set(branches)` line.
- `src/saju_engine/patterns.py:619` — delete the bare `L.STEM_INFO[day_master]["element"]` line.
- `src/saju_engine/patterns.py:11, 603` — import `Any`; `-> Dict[str, any]` → `-> Dict[str, Any]`.
- `src/saju_engine/lookup.py:70-75` — replace with:
  ```python
  JIAZI_CYCLE: List[Tuple[str, str]] = [
      (STEM_ORDER[i % 10], BRANCH_ORDER[i % 12]) for i in range(60)
  ]
  ```
- `src/saju_html/md_to_saju_pdf.py:151-155` — delete `_wrap_cjk_in_cid_font`.
- `src/saju_html/md_to_saju_pdf.py:321-335` — delete `_replace_element_emoji_with_bullet`; change the comment above `_strip_element_emoji` to `# Element emoji are stripped before reportlab layout (no colour-emoji font support).`
- `src/saju_html/md_to_saju_pdf.py:165` — `.replace("-Bold", "-Bold").replace("-Oblique", "-Oblique")` → delete both no-op calls: `return name.replace("DejaVuSans", "Helvetica")`.
- `src/saju_html/svg_charts.py:301` — delete the bare `seg_width * len(rows) + ...` expression line.
- **Keep** `nayin.nayin_relation` (public export, tested).

- [ ] **Step 1: Confirm zero callers before deleting**

Run: `grep -rn "derive_star_positions\|pillar_table_rows\|_wrap_cjk_in_cid_font\|_replace_element_emoji_with_bullet\|\bpretty(" src tests tools`
Expected: only the definitions.

- [ ] **Step 2: Apply the edits above.**

- [ ] **Step 3: Lint + full suite + validation**

Run: `ruff check --select F src tests tools && PYTHONPATH=... python3 -m pytest tests/ -q && python3 tools/run_validation.py`
Expected: clean; no new failures. (If ruff flags `_CJK_RE`/`_ELEMENT_EMOJI_TO_ELEMENT` as now-unused imports, remove them.)

- [ ] **Step 4: Commit**

```bash
git add -A src
git commit -m "chore: A7 remove dead functions and no-op statements found in audit"
```

---

### Task 9: A6 + tracker — docs reflect reality

**Files:**
- Modify: `CLAUDE.md:94-96`
- Modify: `docs/issues_bugs.md` (append an "Audit 2026-10-01" section)
- Modify: `docs/MEMORY.md` (Recent Changes + Open Items)

- [ ] **Step 1: CLAUDE.md**

Line 94: `(translation maps live in src/saju_html/md_to_saju_pdf.py)` → `(translation maps live in src/saju_html/__init__.py)`.
Line 95: replace `and the hardcoded \`_SITE\` in the engine` with `; the engine honours \`$SAJU_SITE\` as an override (src/saju_engine/pillars.py)`.
Line 96: `in \`src/saju_html/md_to_saju_pdf.py\`` → `in \`src/saju_html/__init__.py\``.

- [ ] **Step 2: issues_bugs.md** — append a table with one row per audit ID: S1, S2, S3, S5, S7, S8b, S8c, A5, A6, A7 → FIXED (2026-10-02, commit sha); B5 → ALREADY DONE (test_val_compat.py:169); S4/A1, S6, S8a/d/e/f, B4, B6–B8 → OPEN (see follow-up plans). Also correct M8 (`:363-370`) to say the compat skip-translation branch was superseded by `renderer.py:214-217`.

- [ ] **Step 3: MEMORY.md** — add a dated Recent Changes bullet summarising Tasks 1–8; under Open Items add "A1: recover `apps/landing-page/src/` from the machine that built it (not in this repo)".

- [ ] **Step 4: Final verification**

Run: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages python3 -m pytest tests/ -q && python3 tools/run_validation.py && ruff check --select F src tests tools`
Expected: passed = 1206 + new tests − deleted stdlib-server tests; 0 failed; validation exit 0.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md docs/issues_bugs.md docs/MEMORY.md
git commit -m "docs: record audit 2026-10-01 Wave A/B fixes; fix stale CLAUDE.md paths"
```

---

## Follow-up plans (not in this plan — each gets its own plan file when started)

| Next plan | Audit IDs | Why separate |
|---|---|---|
| **P2 — `report_primitives` extraction** | B4, B8, S6 (typed compat flags) | Large cross-module refactor (10 duplicated primitives, 4 in-season variants); needs its own fixture-first design. Tasks 2–3 here are its first two consumers. |
| **P3 — validation coverage** | B7 (stars + patterns fixture subsystems), §4.4 stale certification prose in `validation.py` | Fixture authoring needs sourced textbook cases. |
| **P4 — web hardening** | S8a (sewoon on own ephemeris), S8d (background PDF jobs), S8e (CORS), S8f (review gate), SQLite intake (C3) | Touches data model + deployment. |
| **P5 — HTML-first reports** | C1, C2, C5 | Multi-week; flips the default PDF backend. |
| **P6 — landing page** | S4/A1, C6, D1–D4 | Blocked until `apps/landing-page/src/` is recovered. |
