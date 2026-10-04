# P5 — HTML-First Reports (flip default backend, loud fallback, no silent text loss) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Source:** audit `/mnt/data2/git_repos/research-engine/output/2026-10-01/saju-engine-audit-2026-10-01.md` §5.1–5.2, §7, §9 C1/C5.

**User decision (2026-10-04):** "Flip default, keep reportlab." The HTML → Playwright (Chromium) renderer becomes the default PDF path for `tools/build-pdf.sh`, the compat PDF tool and the self-service app; reportlab stays available behind an explicit flag for one release. A missing browser fails loudly (no silent backend switch). Unmapped Hanja/Korean text is no longer silently deleted from PDFs. Rendered-HTML snapshot tests are added. (Full Jinja2 template rewrite and reportlab removal are NOT in scope.)

**Goal:** One canonical, styled client PDF per report, produced the same way on every machine, with no content silently dropped.

**Architecture:** `saju_html.renderer.build_pdf` (markdown → HTML → Playwright PDF; page X/Y via the browser footer) is the default everywhere. reportlab (`saju_html.md_to_saju_pdf`) remains as `--reportlab` / `backend="reportlab"`. Translation keeps unmapped CJK in HTML output (Noto CJK fonts are present and in the CSS font stack) and reports them; maps are extended so golden reports have zero unmapped terms.

**Tech Stack:** Python, Playwright (Chromium), markdown-it-py, reportlab (legacy flag), pytest.

## Global Constraints

- Test prefix: `PYTHONPATH=src:/home/harish/.local/lib/python3.12/site-packages`
- Baseline: 1581 passed, 6 skipped, 14 xfailed (develop after P4 + geocoder test fix); validation 315 checks (PASS 306, INTERPRETATION 9, FAIL 0); markdown golden snapshots (tests/golden/) must stay byte-identical — this plan changes rendering, not report text.
- Playwright + Chromium work on this machine (`saju_html.renderer.html_to_pdf` renders). Tests that need a browser must `pytest.skip` cleanly when it is unavailable (CI may lack it); tests that check HTML do not need a browser.
- Client PDFs must never contain internal citations (`*(see knowledge/...)*`) or engine-draft markers — the existing strip functions in `saju_html/__init__.py` must still run on the HTML path (verify, don't assume).
- Branch: `feat/p5-html-first` off `develop`; one commit per task; messages end with a blank line + `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_01Xj4iEWtNZjKhVw3kAhU33R`.
- Don't touch `candidates_horoscope/` (user's uncommitted work) — write any test PDFs under tmp.

---

### Task 1: Loud renderer + no silent CJK deletion

**Files:** `src/saju_html/renderer.py` (~:473-497 fallback), `src/saju_html/__init__.py` (`translate_inline` ~:395-404 and final `_CJK_RE` pass ~:487), translation maps in `src/saju_html/__init__.py`, tests `tests/test_renderer_fallback.py` (new), `tests/test_translation_coverage.py` (new).

- [ ] **Step 1 (fallback):** `renderer.build_pdf` must NOT silently fall back to reportlab. New behaviour: on `ImportError`/`RuntimeError` from `html_to_pdf`, raise `RuntimeError("HTML/Playwright PDF backend unavailable: <exc>. Install with `pip install playwright && python -m playwright install chromium`, or pass backend='reportlab' / --reportlab explicitly.")` — unless the caller passed `allow_fallback=True` (new keyword, default False) or the env var `SAJU_PDF_FALLBACK=reportlab` is set, in which case keep the current warning + reportlab call. Test with monkeypatched `html_to_pdf` raising.
- [ ] **Step 2 (CJK):** Replace silent deletion with *keep + report*: `translate_inline(text, *, keep_unmapped: bool = True, unmapped: Optional[set] = None)` — when `keep_unmapped` is True, unmapped CJK characters stay in the output (HTML path renders them via the Noto CJK font stack — check `theme.css` `--font-serif/--font-sans` include a CJK fallback such as "Noto Serif CJK KR"/"Noto Sans CJK KR"; add it if missing) and are added to the `unmapped` set if provided. The reportlab path calls it with `keep_unmapped=False` (its fonts can't draw CJK) but must `warnings.warn` listing the dropped characters (never silent). Find every caller (`grep -rn "translate_inline\|_CJK_RE" src/`) and route the flag correctly; the HTML renderer collects `unmapped` and logs one warning per render if non-empty.
- [ ] **Step 3 (coverage):** `tests/test_translation_coverage.py`: for every `tests/golden/*.md`, run the same translation the HTML renderer applies and assert the `unmapped` set is empty. Extend the maps (`STEM_MAP`, `BRANCH_MAP`, `TENGOD_MAP`, `KOR_REPL`, `HANJA_MAP`) with every term the test reports — each new entry gets a correct English gloss consistent with `knowledge/00-glossary.md` (cite the glossary line in a comment for non-obvious terms). Do not change markdown generation.
- [ ] **Step 4:** Verify (suite, golden markdown unchanged, ruff F). Commit `fix(pdf): no silent backend fallback; keep and report unmapped CJK; complete translation maps`.

### Task 2: HTML is the default backend everywhere

**Files:** `tools/build-pdf.sh`, `src/saju_html/md_to_saju_html_pdf.py` (add `--from-chart` + tier, mirroring `md_to_saju_pdf.py`'s flags), `src/saju_html/md_to_saju_compat_pdf.py` (`--backend html|reportlab`, default html), `src/saju_web/jobs.py` (use `saju_html.renderer.build_pdf` / an HTML from-chart helper), `src/saju_html/combine_candidate_report.py` if it shells to a backend, tests.

- [ ] **Step 1:** `md_to_saju_html_pdf.py`: add the `--from-chart` birth-data flags and `--tier` exactly as `md_to_saju_pdf.py` exposes them (read its argparse), implemented by computing the chart, generating the tier markdown (same function the reportlab path uses: `build_pdf_from_chart`'s markdown step — factor a shared `chart_markdown(chart, tier, ...)` helper in `md_to_saju_pdf.py` or a new module rather than duplicating), then `renderer.build_pdf`.
- [ ] **Step 2:** `tools/build-pdf.sh`: default `USE_HTML=1`; new `--reportlab` flag selects the legacy tool; `--html` stays accepted as a no-op alias. Output naming: the default (HTML) writes the canonical names (`{name}-report.pdf`, `{name}-combined.pdf`); `--reportlab` writes `{name}-report-reportlab.pdf` / `{name}-combined-reportlab.pdf` so the two never overwrite each other silently. Update the script's header comment.
- [ ] **Step 3:** `md_to_saju_compat_pdf.py`: `--backend` (default `html`) routing to `renderer.build_pdf(..., tier="compat")` (check the renderer supports the compat tier/translation path; `renderer.py:~214-217` handles compat translation) or reportlab.
- [ ] **Step 4:** `saju_web/jobs.py`: render single-chart and compat drafts via the HTML path (respecting `SAJU_MAX_RENDERS`), backend overridable by env `SAJU_PDF_BACKEND=reportlab`. App/jobs tests must keep passing; tests that render PDFs skip if no browser.
- [ ] **Step 5:** Tests: `tests/test_build_pdf_default.py` — run `tools/build-pdf.sh --from-chart ...` into tmp (skip without browser) and assert the PDF was produced by Chromium (PDF `/Producer` or `/Creator` contains "Skia"/"Chrome") and that the reportlab flag produces a reportlab PDF (`/Producer` contains "ReportLab"). Verify no knowledge/ citation text appears in the extracted PDF text (use `pypdf` if installed, else skip that assertion and note it).
- [ ] **Step 6:** Verify; commit `feat(pdf): HTML/Playwright is the default backend; reportlab behind --reportlab`.

### Task 3: Rendered-HTML snapshot tests

**Files:** `tests/golden_html/` (generated), `tools/regen_golden.py` (extend with `--html`), `tests/test_golden_html.py` (new).

- [ ] **Step 1:** For each `tests/golden/*.md`, render the HTML string the renderer would print (the function that builds the full HTML before `html_to_pdf` — find it in renderer.py) with fixed metadata (`generation_date="2026-06-01"`, fixed `report_id`), normalise volatile bits (none expected — verify determinism by rendering twice), and snapshot to `tests/golden_html/<name>.html`. `tools/regen_golden.py --html` regenerates them.
- [ ] **Step 2:** `tests/test_golden_html.py`: byte-compare; plus structural assertions on each: contains the SVG element-balance chart where the md has an Element Balance table; contains no `*(see knowledge/` text; contains no `ENGINE DRAFT` marker; no unmapped-CJK warning was emitted.
- [ ] **Step 3:** One browser smoke test (skip without browser): render one golden HTML to PDF, assert ≥1 page and footer page numbering text present in extracted text if `pypdf` is available.
- [ ] **Step 4:** Verify; commit `test(pdf): rendered-HTML golden snapshots`.

### Task 4: Docs + tracker

- [ ] `CLAUDE.md`: "Shareable PDF Generation" and "Premium Client Report Pipeline" step 4 — HTML is the default, `--reportlab` for legacy, browser install note, loud failure; remove "Default reportlab backend" wording. "Adding new translation terms" now mentions `tests/test_translation_coverage.py`.
- [ ] `README.md`, `docs/openwiki/operations/toolchain-and-testing.md`, `docs/openwiki/products/reports.md`, `.claude/commands/saju-client.md` (if it names a backend).
- [ ] `docs/issues_bugs.md`: C1 (default flip; template rewrite remains OPEN as "C1-templates"), C5 (silent CJK drop) FIXED with SHAs; note reportlab removal planned after one release.
- [ ] `docs/MEMORY.md` Recent Changes.
- [ ] Full suite + validation; commit `docs: record P5 HTML-first reports`.
