# Saju Engine — Architecture Audit & Improvement Report

> **ARCHIVED / HISTORICAL** — point-in-time record. See `README.md` in this folder and the live
> trackers (`../issues_bugs.md`, `../../improvements_issues.md`). Paths/line-numbers may be stale.

**Date:** 2026-08-10  
**Scope:** Full codebase review including `tools/saju_engine/`, `tools/`, `tests/`, `knowledge/`, `docs/`, and `candidates_horoscope/`

---

## Executive Summary

The Saju project is a **mature, well-tested Korean Saju (Four Pillars of Destiny) engine** with:
- **553/557 passing pytest tests** (4 failures: Playwright Chromium not installed)
- **12/12 cross-validation cases** passing
- Complete calculation engine wrapping `sajupy` with Korean Myeongri overlays
- Dual PDF backends (ReportLab + HTML/Playwright)
- Tiered client products (sample/essential/deep + compatibility basic/deep)
- Self-service FastAPI calculator + landing page integration
- Comprehensive documentation in `docs/openwiki/`

**Current state:** Feature-complete for the defined product scope. All critical/high-severity bugs from the 2026-07-05 audit have been **fixed** (P0–P5 roadmap complete). Remaining work is **optional polish** and **architectural modernization**.

**Correction note (2026-08-10):** My original audit report contained ~50% stale claims in the "Remaining Technical Debt" table — most items were already fixed in the codebase. This version corrects those inaccuracies.

---

## 1. Architecture Assessment

### 1.1 Strengths

| Area | Assessment |
|------|------------|
| **Calculation correctness** | Foundation tables (stems, branches, hidden stems, 10×10 ten-god, 10×12 twelve-stage, 60-cycle, 五虎遁/五鼠遁, solar-term boundaries, Zi-hour conventions) are **doctrinally verified** against classical sources and `knowledge/` files. |
| **Test coverage** | 557 tests covering edge cases: solar-term boundaries, high-longitude day rollover, leap months, full year-stem×gender 대운 matrix, textbook 만세력 cases (10 Korean presidential/business figures), PDF rendering regressions. |
| **Modular design** | Clean separation: `pillars.py` (sajupy wrapper), `lookup.py` (Korean Myeongri tables), `engine.py` (orchestrator), `chart.py` (dataclasses), overlay modules (`daeun_overlay.py`, `sewoon.py`, `patterns.py`, `stars.py`, `strength.py`). |
| **Deterministic & auditable** | Every computed value traces to either `sajupy` (solar/60-cycle math) or `knowledge/` (interpretive rules). Engine prose marked `[ENGINE DRAFT — REVIEW REQUIRED]`. |
| **Convention-aware** | First-class support for Korean `야자시` vs Chinese `조자시`, solar-time correction, and reference-date threading for luck windows. |
| **Client pipeline** | Tiered reports (sample/essential/deep/companion), compatibility engine (11 sub-systems), combined report pipeline, citation stripping in PDFs. |

### 1.2 Architectural Concerns

| Concern | Impact | Location |
|---------|--------|----------|
| **Package layout** | `tools/saju_engine/` as package root (not `src/`) — non-standard, breaks tooling expectations | `pyproject.toml: where = ["tools"]` |
| **Hardcoded paths** | ~~Removed in audit~~ — now uses `site.getusersitepackages()` and `$SAJU_SITE` | Fixed in P0/P1 |
| **Single `Chart` god object** | `Chart` dataclass accumulates 37 fields; becoming a "god object" | `chart.py` |
| **Import graph** | Clean DAG — no circular imports. Only `cli.py` + `__init__.py` import `engine` | Verified 2026-08-10 |
| **Public API boundary** | Curated `__all__` with 14 names in `__init__.py` | `__init__.py` |
| **Mixed concerns in `engine.py`** | 363-line orchestrator doing validation, computation, overlay wiring, date handling | `engine.py` |

---

## 2. Code Quality & Technical Debt

### 2.1 Fixed in Audit (P0–P5) — **All Complete**

| ID | Issue | Fix |
|----|-------|-----|
| A1 | 정격 from 월간 not 월지 투출 | `_grid_stem_by_tuochul()` in `patterns.py` |
| A2 | 희신 contradicts `knowledge/03` | Documented both schools; annotated convention |
| A3 | 대운 starting_age ignores term moment | `_term_boundary_datetimes()` + moment-level precision |
| A4 | Birth time dropped before `starting_age` | Plumbed `hour/minute` through `compute_daeun` |
| A5 | 만 나이 vs 세수 mix in current 대운 | `daeun.saju_age()` (입춘-based 세수) wired throughout |
| A6 | sajupy warning corrupts JSON output | `contextlib.redirect_stdout` in `pillars.py` |
| A7 | ValueError traceback in CLI | `try/except` → `ap.error()` in `cli.py` |
| A8 | Invented `_WEAK_SPOUSE_PALACE` entries | Removed 3 invented entries |
| A9 | Same-Nayin → 상형 (−4) invented | Removed special case; falls to 상대 (+1) |
| A10 | Compatibility rows wrong for strong DM | Rewrote verdict-aware logic in `report_data.py` |
| A11 | Wrong CTA price (₹499→₹1,499) | Fixed in `premium_report.py` |
| A12 | 釵釧금 = 채천금 not 최천금 | Fixed in `nayin.py` + `knowledge/11` |
| A13 | `combinations_6` type arity mismatch | 5-tuple annotation in `chart.py` |
| A14 | 홍염 missing alternates | `HONGYEOM_BRANCHES: Dict[str, List[str]]` |
| A15 | 종격 missing 득령/extreme-weak | Added preconditions in `detect_special_forms` |
| A16 | Broken markdown bold nesting | Fixed in `prose_fillers.py` |
| A17 | Inconsistent ten-god language | Aligned to English-preferred pattern |

### 2.2 Actually Remaining Technical Debt (Verified 2026-08-10)

| Priority | Issue | Location | Effort |
|----------|-------|----------|--------|
| **High** | `Chart` god object — 37 fields, no clear boundaries | `chart.py` | Medium |
| **High** | `engine.py` 363 lines, does too much (imports 8 sibling modules) | `engine.py` | Medium |
| **Medium** | `validate.py` 0% test coverage, not in pytest | `validate.py` / `tests/` | Low |
| **Medium** | Coverage holes: `pillars.py` ~77%, `compat.py` ~80%, `daeun.py` ~81% | `tests/` | Medium |
| **Medium** | No CI workflow (`.github/workflows/ci.yml` missing) | Repo root | Low |
| **Low** | `_triplet_target` substring matching in `stars.py` (fragile) | `stars.py:176-182` | Trivial |
| **Low** | Module size concentration: `compat.py` 1326, `premium_report.py` 1641, `prose_fillers.py` 1527 lines | Various | Medium |

**Stale claims removed (verified fixed):**
- ❌ `detect_grid_candidates` dead code — **doesn't exist** in codebase
- ❌ Duplicate `_element_counts` — **shared** via `from .strength import _element_counts` (patterns.py:14)
- ❌ Hand-maintained 空亡 typo risk — **guarded** by algorithmic cross-check at import (stars.py:148-151)
- ❌ `Chart.to_json` uses `default=str` — **strict** `json.dumps()` since audit (chart.py:305-312)
- ❌ No public API boundary — **curated** `__all__` with 14 names (`__init__.py`)
- ❌ `_OHO_DUN` not tested — **classical verse test** exists (test_lookup.py:99-100)
- ❌ `ten_god` only 11/100 pairs — **exhaustive** 100-pair test (test_lookup.py:75-78)
- ❌ Circular-ish imports — **clean DAG**, only `cli.py` + `__init__.py` import `engine`
- ❌ `nayin.py` 74% coverage — **improved to 81%** per pytest-cov

---

## 3. Modularization Recommendations

### 3.1 Proposed Package Structure

```
tools/
├── saju_engine/                 # Public API package
│   ├── __init__.py             # Exports ONLY public API
│   ├── _version.py             # __version__ from pyproject.toml
│   ├── api.py                  # Public entry points: compute_chart, generate_premium_report, compat_score
│   │
│   ├── core/                   # Core calculation (no interpretive logic)
│   │   ├── __init__.py
│   │   ├── pillars.py          # sajupy wrapper + solar/zi correction
│   │   ├── calendar.py         # Solar terms, 60-cycle, 五虎遁/五鼠遁
│   │   ├── chart.py            # Dataclasses only (Pillar, Chart, DaeunPeriod, etc.)
│   │   └── lookup.py           # Pure lookup tables (STEM_INFO, BRANCH_INFO, HIDDEN_STEMS, etc.)
│   │
│   ├── overlays/               # Deterministic overlays
│   │   ├── __init__.py
│   │   ├── ten_gods.py         # 십신 derivation
│   │   ├── twelve_stages.py    # 12운성 derivation
│   │   ├── branch_relations.py # 합/충/형/파/해/삼합/반합/방합
│   │   ├── daeun.py            # 대운 sequence + starting age
│   │   ├── daeun_overlay.py    # 대운 activation metadata
│   │   ├── sewoon.py           # 세운/월운/일운 windows
│   │   ├── stars.py            # Classical 신살
│   │   ├── nayin.py            # Nayin lookup + pair table
│   │   └── strength.py         # Day Master strength heuristic
│   │
│   ├── patterns/               # Pattern/grid detection
│   │   ├── __init__.py
│   │   ├── regular_grid.py     # 정격 (투출 method)
│   │   ├── transformation.py   # 화격
│   │   ├── follower.py         # 종격/종자
│   │   ├── structural.py       # 전국/편국/삼합국
│   │   └── combinations.py     # 천간합 + 화격 conditions
│   │
│   ├── compat/                 # Compatibility engine
│   │   ├── __init__.py
│   │   ├── core.py             # compat_score + 11 sub-systems
│   │   ├── report.py           # generate_compat_report
│   │   └── data.py             # Weight tables, verdict bands
│   │
│   ├── reporting/              # Report generation
│   │   ├── __init__.py
│   │   ├── premium.py          # generate_premium_report
│   │   ├── skeleton.py         # Markdown skeleton
│   │   ├── prose.py            # prose_scaffold + prose_fillers
│   │   └── combine.py          # combine_candidate_report
│   │
│   └── cli/                    # CLI entry point
│       ├── __init__.py
│       ├── main.py             # saju-engine command
│       └── args.py             # Argument parsing + validation
│
├── pdf/                        # PDF rendering (separate package)
│   ├── __init__.py
│   ├── reportlab_backend.py
│   ├── html_backend.py
│   ├── compat_backend.py
│   └── build.py                # build-pdf.sh logic in Python
│
├── intake/                     # Client intake
│   ├── __init__.py
│   ├── server.py               # JSON intake server
│   ├── app.py                  # FastAPI self-service
│   └── forms/                  # HTML forms
│
└── utils/                      # Shared utilities
    ├── __init__.py
    ├── dates.py                # Date/time helpers
    ├── io.py                   # File I/O helpers
    └── validation.py           # Input validation
```

### 3.2 Key Architectural Changes

| Change | Rationale |
|--------|-----------|
| **Move to `src/` layout** | Standard Python packaging; enables `pip install -e .`, works with all tooling |
| **Public API in `api.py`** | Clear boundary: `compute_chart`, `generate_premium_report`, `compat_score` only |
| **Core vs Overlays vs Patterns** | Separates deterministic calculation from interpretive detection |
| **Compat as subpackage** | Isolates complex 11-sub-system logic |
| **Reporting separate from engine** | Engine produces `Chart`; reporting consumes it |
| **CLI as thin wrapper** | Delegates to `api.py`; no business logic |
| **PDF as separate package** | Decouples rendering from calculation |

### 3.3 Actual Architecture (Verified 2026-08-10)

**Import graph:** Clean DAG — no circular imports. Only `cli.py` and `__init__.py` import from `engine`. The `engine.py` imports 8 sibling modules (pillars, lookup, daeun, stars, strength, patterns, sewoon, daeun_overlay) but **no module imports back from engine**.

**Real modularization problem:** Module size concentration, not layering:
- `compat.py` 1326 lines (scoring + 11 sub-systems)
- `premium_report.py` 1641 lines (9-section report generation)
- `prose_fillers.py` 1527 lines (engine-drafted prose fragments)
- vs `engine.py` only 363 lines

**Highest-value splits (smaller than full re-layout):**
1. Split `Chart` (37 fields) into natal vs luck-window vs derived sub-clusters or computed properties
2. Split `compat.py` scoring from `compat_report.py` presentation
3. Make CLI unit-testable: `main(argv)` instead of `subprocess` in tests
4. Remove redundant `sys.path.insert($SAJU_SITE)` bootstrap (now 4 files) — `sajupy` is on PyPI, declare as normal dependency

### 3.4 Migration Path

1. **Phase 1** (Non-breaking): Create new structure alongside old; add `__init__.py` re-exports for backward compatibility
2. **Phase 2**: Move modules one by one, updating imports; run full test suite after each move
3. **Phase 3**: Switch `pyproject.toml` to `src/` layout; update `PYTHONPATH` references
4. **Phase 4**: Remove compatibility shims; clean up `tools/saju_engine/` old structure

---

## 4. Testing & CI Improvements

### 4.1 Current Test Status (2026-08-10)

| Metric | Value |
|--------|-------|
| **Total tests** | 557 collected |
| **Passing** | 553 |
| **Failing** | 4 (all in `tests/test_html_pdf.py`) |
| **Failure cause** | Playwright Chromium not installed (`playwright install chromium` never run) |
| **Cross-validation** | 12/12 parametrized cases in `tests/test_cross_validate.py` ✅ |

### 4.2 Missing Test Coverage

| Module | Coverage | Target | Priority |
|--------|----------|--------|----------|
| `validate.py` | 0% | 80%+ | High |
| `pillars.py` | ~77% | 90%+ | Medium |
| `compat.py` | ~80% | 90%+ | Medium |
| `daeun.py` | ~81% | 90%+ | Medium |
| `cli.py` | 0% (subprocess-based) | 80%+ | Low |

### 4.3 CI Pipeline (Missing)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install sajupy
        run: pip install --user --break-system-packages sajupy
      - name: Install deps
        run: pip install -e ".[dev,web]" pytest-cov
      - name: Install Playwright browsers
        run: playwright install chromium
      - name: Run tests
        run: pytest --cov=tools.saju_engine --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

**Critical fix:** Add `playwright install chromium` step and/or skip guard in `test_html_pdf.py`:
```python
pytest.importorskip("playwright")
# or
@pytest.mark.skipif(not shutil.which("playwright"), reason="Playwright not installed")
```

### 4.4 Cross-Validation in CI

Already done: `tools/cross_validate.py` cases migrated to `tests/test_cross_validate.py` as parametrized tests (per audit P4).

---

## 5. Documentation Gaps

| Gap | Location | Action |
|-----|----------|--------|
| **API reference** | Missing | Generate from docstrings (Sphinx/pdoc) |
| **Architecture decision records** | `docs/engine_audit_2026-07-05.md` only | Add ADR folder for future decisions |
| **Contribution guide** | Missing | `CONTRIBUTING.md` |
| **Release process** | Missing | Document versioning + release steps |
| **Compatibility engine internals** | `knowledge/11-gunghap.md` only | Add technical docs for 11 sub-systems |
| **PDF backend architecture** | `toolchain-and-testing.md` only | Document theme system, font handling |

---

## 6. Product & Feature Observations

### 6.1 Current Product Completeness

| Product | Status | Gaps |
|---------|--------|------|
| **The Hook (sample)** | ✅ Complete | None |
| **Essential Report** | ✅ Complete | Minor prose polish |
| **Deep Destiny Report** | ✅ Complete | MP3 audio summary (separate pipeline) |
| **Cosmic Companion** | ✅ Email-intake only | Payment gateway, automated billing |
| **Compatibility Basic** | ✅ Complete | None |
| **Compatibility Deep** | ✅ Complete | None |
| **Landing Page** | ✅ Wired to calculator | Production deployment hardening |

### 6.2 Suggested Enhancements (Optional)

| Enhancement | Value | Effort |
|-------------|-------|--------|
| **Payment gateway integration** (Stripe/Razorpay) | Enables automated paid delivery | Medium |
| **Background job queue** (Celery/RQ) for PDF generation | Removes sync blocking in API | Medium |
| **Encrypted PII storage** | Production readiness | Medium |
| **Webhook notifications** for intake submissions | Operational visibility | Low |
| **Admin dashboard** for report management | Operational efficiency | Medium |
| **Multi-language PDF output** (Korean/English) | Market expansion | High |
| **API rate limiting / auth** | Production security | Medium |

---

## 7. Knowledge Base Alignment

### 7.1 Current State

The `knowledge/` directory is **the canonical interpretive reference**. Engine code must not invent rules. Audit confirmed:
- ✅ All implemented rules trace to `knowledge/` files
- ✅ `knowledge/03-five-elements.md` documents both 희신 schools (classical + modern)
- ✅ `knowledge/07-special-formations.md` documents breaker stems, 종격 preconditions
- ✅ `knowledge/11-gunghap.md` documents all 11 compat sub-systems with classical sources

### 7.2 Gaps in `knowledge/`

| Topic | Status | Needed |
|-------|--------|--------|
| **암합격 / 무칙지** | Not documented | Add to `07-special-formations.md` before implementing |
| **Year-branch anchoring for 도화/역마/화개** | Documented as alternative | Already implemented with `anchor` param |
| **Same-sex / non-hetero 궁합** | Not addressed | Add to `11-gunghap.md` |
| **진신/용신 호환성 sub-system** | Not in 11 sub-systems | Document if adding |

---

## 8. Priority Roadmap (Updated 2026-08-10)

### Immediate (Week 1)
- [ ] **Fix playwright tests**: Add `playwright install chromium` to CI + skip guard in `test_html_pdf.py`
- [ ] **Add CI workflow**: `.github/workflows/ci.yml` with Playwright install step
- [ ] Fix `Chart.to_json` — already strict, verify no regression
- [ ] Remove redundant `sys.path.insert($SAJU_SITE)` bootstrap (4 files) — `sajupy` on PyPI

### Short-term (Month 1)
- [ ] Add missing regression tests for audit-fixed bugs (validate.py coverage)
- [ ] Split `compat.py` scoring from `compat_report.py` presentation
- [ ] Make CLI unit-testable: `main(argv)` instead of `subprocess` in tests
- [ ] Add exhaustive tests for `validate.py` (currently 0% coverage)

### Medium-term (Month 2–3)
- [ ] Refactor to `src/` layout with public API boundary
- [ ] Split `Chart` (37 fields) into natal/luck/derived sub-clusters
- [ ] Payment gateway integration for Cosmic Companion + paid tiers
- [ ] Background job queue for PDF generation
- [ ] Encrypted PII storage + audit logging

### Long-term (Quarter+)
- [ ] Multi-language PDF support (Korean primary)
- [ ] Public API with rate limiting, auth, webhooks
- [ ] Mobile app / PWA for self-service
- [ ] Advanced timing features (시운/시진, more granular daily luck)
- [ ] AI-assisted interpretation (grounded in `knowledge/` citations)

---

## 9. Risk Register (Updated 2026-08-10)

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Playwright tests fail in CI (browser not installed) | **High** | Medium | Add `playwright install chromium` to CI workflow |
| `sajupy` unmaintained / breaks | Low | High | Pin version; test against known cases; consider fork |
| Knowledge/source disagreement | Medium | Medium | Document both schools; mark `[UNCERTAIN]` in output |
| PDF backend dependency drift | Medium | Medium | Pin `playwright`/`reportlab`; visual regression tests |
| PII leak in intake JSON | Low | Critical | Encrypt at rest; add purge policy |
| Engine provenance unclear to clients | Medium | Medium | Maintain `[ENGINE DRAFT]` markers; citation stripping |

---

## 10. Conclusion

The Saju engine is **production-ready for its defined scope**. The 2026-07-05 audit resolved all critical and high-severity issues. The codebase is well-tested (553/557 passing, 4 playwright-only failures), doctrinally grounded, and has a clear product pipeline.

**Corrected assessment:** My original audit report contained ~50% stale claims in the "Remaining Technical Debt" table — most items were already fixed. The actual remaining work is smaller and more focused.

**Recommended next steps:**
1. **Stabilize**: Fix playwright CI, add CI workflow, remove redundant bootstrap code
2. **Modularize incrementally**: Split `compat.py`/`compat_report.py`, make CLI unit-testable, split `Chart` god object
3. **Productionize**: Payment gateway, background jobs, encrypted storage for paid products
4. **Extend**: Multi-language, advanced timing, AI-assisted interpretation (all optional)

The architecture supports all of the above incrementally — no rewrites needed.

---

*Report generated from comprehensive review of: `CLAUDE.md`, `docs/MEMORY.md`, `tasks.md`, `docs/issues_bugs.md`, `docs/engine_audit_2026-07-05.md`, `docs/PLAN.md`, `docs/openwiki/`, `tools/saju_engine/`, `tests/`, `knowledge/`, and `candidates_horoscope/` conventions.*