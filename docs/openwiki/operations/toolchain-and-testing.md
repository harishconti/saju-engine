# Toolchain and Testing

## Toolchain overview

The project has three complementary layers:

1. **Calculation engine** — `src/saju_engine/`, wraps `sajupy` and adds Korean Saju lookups.
2. **Interpretive layer** — markdown reports generated from the engine or hand-written by the reader.
3. **Presentation layer** — PDF renderers and shell wrappers.

Key scripts:

| Script | Purpose |
|---|---|
| `src/saju_engine/__main__.py` | CLI entry point for chart calculation and report generation. |
| `src/saju_engine/premium_report.py` | Single-chart premium markdown generator. |
| `src/saju_engine/compat_report.py` | Two-chart compatibility (궁합) markdown generator. |
| `src/saju_html/md_to_saju_pdf.py` | Legacy ReportLab two-pass PDF renderer (`--reportlab`). |
| `src/saju_html/md_to_saju_html_pdf.py` | HTML/CSS + Playwright renderer (default); supports `--from-chart` / `--tier`. |
| `src/saju_html/md_to_saju_compat_pdf.py` | Compat (궁합) PDF tool: HTML/Chromium by default, `--backend reportlab` for the legacy renderer. |
| `tools/build-pdf.sh` | Wrapper that sets `PYTHONPATH`, site-packages, and dispatches to the chosen backend (HTML default; `--reportlab` legacy). |
| `src/saju_html/combine_candidate_report.py` | Merges base report + topic follow-ups into a single client deliverable. |
| `tools/client_intake_app.html` + `tools/client_intake_app.py` | Self-service FastAPI app: `/` single-chart, `/compat` two-chart; sample tier returns a PDF instantly; paid tiers are stored in an encrypted SQLite queue (`src/saju_web/store.py`, `SAJU_INTAKE_KEY`), drafted in the background and approved by the owner. |
| `tools/intake_admin.py` | Owner CLI: `genkey`, `list [--status]`, `show <id>`, `approve <id> --base-url`, `regenerate <id>`, `purge --days 180`. `approve` prints the private `/report/{token}` link to email. |
| `tools/qa_compliance.py` | Optional compliance QA gate for a report markdown file (ground-rule check on generated prose). Requires `TYPESAFE_API_KEY`. |

## Running the test suite

```bash
pytest
```

The suite currently contains ~1,846 cases (as of 2026-10-11). Core coverage includes:

- Foundation tables (HIDDEN_STEMS, STEM_INFO, BRANCH_INFO, SIX_*, THREE_*).
- Stem/branch operations, 12운성, ten-god lookups, hidden stems, Nayin.
- Chart calculation including solar-time correction and 夜子시 (late-night child-hour) handling.
- Major, annual, monthly, and daily luck overlays.
- Classical star lookups.
- Korean textbook 만세력 cases: 박정희, 노무현, 김대중, 김영삼.
- PDF Hanja-pair regression and citation stripping.

Run a subset:

```bash
pytest tests/test_textbook_cases.py
pytest tests/test_nayin.py
pytest tests/test_pdf.py
```

## Validation fixtures

`python3 tools/run_validation.py` runs cited JSON fixtures in `tests/validation/fixtures/`
(314 checks, 10 subsystems): `pillars.json`, `daeun.json`, `sewoon.json`, `lookups.json`,
`yongsin.json`, `climate.json`, `compat.json`, `career.json`, plus the P3 additions
`stars.json` (W7 신살, 57 fixtures; harness `tests/validation/test_val_stars.py`) and
`patterns.json` (W8 격국, 51 fixtures; harness `tests/validation/test_val_patterns.py`). Gate
history: `docs/validation/gate-history.md`.

## Engine validation priorities

- **Priority A — Foundation tables.** Verifiable against standard Korean almanac tables.
- **Priority B — Korean textbook cases.** Presidential birth charts from publicly available articles; used for end-to-end date→pillar validation.
- **Priority C — Classical star corpus.** Implemented from `knowledge/07-stars.md` with documented ambiguity rules.
- **Priority D — PDF rendering.** Visual regression via the Hanja-pair test and manual spot checks.
- **Priority E — Compatibility engine.** Score distribution checked against known demo pairs.

## Compliance QA gate (optional)

The engine derives structure deterministically, but report prose is written for human
review. `src/saju_qa/` is an optional, self-contained classifier package that checks a
generated report's prose blocks against the ground rules: (a) outcome-as-certain
(predictive) language, (b) master/guarantee claims, (c) specific medical/legal/financial
advice, and (d) missing hedging. It produces flags + scores and **never writes chart facts
or edits the report**.

```bash
# Gate a report (exit 0 clean, 1 flagged, 2 classifier unavailable)
python3 tools/qa_compliance.py candidates_horoscope/reports/rm/rm_deep.md
python3 tools/qa_compliance.py --json report.md        # machine-readable
python3 tools/qa_compliance.py --warn-only report.md   # never exit non-zero
```

- Uses the standard library only (no new runtime dependency) and is gated behind
  `TYPESAFE_API_KEY`; the model name is overridable via `SAJU_CLASSIFY_MODEL`
  (default `jev-latest`). Without a key the gate skips and returns exit code 2.
- `src/saju_qa/client.py` is a minimal TypeSafe/Jev `/v1/systemone` client;
  `src/saju_qa/compliance.py::scan_report()` splits the report into prose paragraphs
  (dropping headings, tables, code and short fragments) and batches all block×check
  pairs into one classifier call per batch.
- Standalone by design: it is **not** wired into the report/web pipeline — it is a manual
  pre-delivery gate, run alongside (not instead of) the reader review. Tests:
  `tests/test_saju_qa.py` (no network; uses a fake client).

## Adding a new textbook case

1. Collect multiple independent Korean sources confirming the year/month/day/hour pillars.
2. Add the case to `tests/test_textbook_cases.py`:
   ```python
   ("Case Name", (YYYY, MM, DD, HH, MM), ("Year Stem", "Year Branch", ...), "source URL"),
   ```
3. Run `pytest tests/test_textbook_cases.py -v` and confirm the engine matches.
4. If there is any discrepancy, leave the case as `pytest.mark.xfail` and document the divergence in the test docstring.
5. Update `docs/MEMORY.md` with the new case and test count.

## Adding a new classical star

1. Confirm the rule is documented in `knowledge/07-stars.md` or another accepted classical source.
2. Add the lookup to `src/saju_engine/stars.py`.
3. Add a unit test in `tests/test_stars.py`.
4. If the classical term is ambiguous (e.g., multiple schools define it differently), add an `[UNCERTAIN]` note in the report output instead of silently choosing one branch.

## Nayin (납음, 納音) 30×30 table

The table lives in `src/saju_engine/nayin.py`. It is currently populated from a documented 5-element fallback and tagged with source provenance.

**Current state of source research:**
- No open, published 30×30 *named* Nayin pair table was found in Korean or Chinese open literature, Saju blogs, academic databases (RISS/KCI/DBpia), or library catalogs.
- The title **“서전구미록”** (in either Hanja form used in the project) could not be verified as a citable published book; it appears to be an internal/lineage label rather than a cataloged text.
- The only concrete bibliographic record claiming a Nayin compatibility table is **Kim Man-tae (김만태), *『한국 사주명리의 활용양상과 인식체계』*, Andong University Ph.D. dissertation, 2010**, tables on pp. 214–215. The dissertation (and the 2011/2022 book 『한국사주명리연구』 from 민속원) is paywalled; the 900 cell values cannot be read without purchase or library request.
- All open sources reproduce either the 30 individual Nayin names or the 5×5 element-level marriage grid. The current fallback grammar (same element → 상대 +1; generating → 상합 +3 / 상구 +2; overcoming → 상충 −5 / 상해 −3) is the standard element-reduction rule found across those sources.

**Consequence:** The engine keeps the data-ready `NAYIN_PAIR_TABLE` populated from the 5-element fallback with the `"element-grammar-fallback"` source tag. If Kim Man-tae’s dissertation pages are ever obtained, individual cells can be overridden and re-tagged without changing the API.

To validate an entry:

```python
from tools.saju_engine.nayin import JIAZI_TO_NAYIN
assert JIAZI_TO_NAYIN[("甲", "子")] == "海中金"  # Gold in the sea
```

## PDF backends

### HTML/Playwright backend (default)
- Default since 2026-10-04 for `tools/build-pdf.sh`, the compat PDF tool (`--backend html|reportlab`) and the self-service app.
- Requires Playwright and its bundled Chromium: `pip install -e .[html]` then `python -m playwright install chromium`. If the bundled Chromium is missing, a system Google Chrome is used with a warning; set `SAJU_ALLOW_SYSTEM_CHROME=0` to require the bundled Chromium (identical output on every machine). A missing browser raises `PdfBackendUnavailable`; the self-service app records that class name as the failure reason.
- Renders Quick Reference as a card, current-year paragraph as a callout, Lucky Attributes as a grid, and adds an SVG element-balance chart.
- Use `--compact` for the one-page Hook/sample tier. `src/saju_html/chart_input.py` is the shared chart-to-markdown step for `--from-chart`.
- **No silent fallback:** a missing browser raises. The renderer falls back to ReportLab only with `allow_fallback=True` or env `SAJU_PDF_FALLBACK=reportlab`.
- Unmapped Hanja/Korean is kept in the HTML and reported (not deleted). Phrase-level Korean glosses live in `_PHRASE_RULES` (`src/saju_html/__init__.py`).
- Env `SAJU_PDF_BACKEND=reportlab` makes the self-service job queue (`src/saju_web/jobs.py`) use ReportLab.

### ReportLab backend (legacy, one more release)
- Opt-in with `./tools/build-pdf.sh --reportlab`; writes `{name}-report-reportlab.pdf` / `{name}-combined-reportlab.pdf` so it never overwrites the HTML PDF. `--html` is a no-op alias.
- Uses DejaVu fonts for Unicode; two-pass build; branded footer and report ID. Warns on unmapped CJK. Planned for removal after one release.

### Compat PDF
- Separate tool in `src/saju_html/md_to_saju_compat_pdf.py` (HTML/Chromium default; `--backend reportlab` uses a Korean CID font).
- Tier-aware translation skip keeps couple names and verdicts intact.

## Continuous development checklist

- Run `pytest` before committing.
- Run `npm test` / `npm run lint` / `npm run build` for landing-page changes.
- Keep citations in `.md` files; client PDFs strip them automatically (leak-checked via pdftotext in tests).
- Rendered-HTML snapshots: `tests/golden_html/` (46 files), regenerate with `python tools/regen_golden.py --html`. Snapshots embed the full CSS, so any CSS change rewrites them all; regenerate deliberately.
- Store every candidate report in `candidates_horoscope/reports/{slug}/`.
- Store every compatibility report in `candidates_horoscope/marriage_compatibility/{name_a}_{name_b}/`.
- Update indexes (`candidates_horoscope/README.md`, `docs/MEMORY.md`, `MEMORY.md`) when adding reports or cases.

## Useful commands

```bash
# Calculate a chart
PYTHONPATH=src python3 -m saju_engine --date 1990-05-15 --time 14:30 --city Seoul --gender F

# Generate a premium report
PYTHONPATH=src python3 -m saju_engine \
  --date 1990-05-15 --time 14:30 --city Seoul --gender F \
  --format premium --tier deep --output-file report.md

# Render to PDF (HTML/Playwright default)
./tools/build-pdf.sh jane "Title" "Client" "15 May 1990, 14:30" "Day Master" \
    --from-chart --tier deep --gender F --birth-year 1990 --birth-month 5 --birth-day 15 \
    --birth-hour 14 --birth-minute 30 --city Seoul --utc-offset 9

# Legacy ReportLab PDF (writes *-reportlab.pdf); --reportlab may appear anywhere
./tools/build-pdf.sh --reportlab jane "Title" "Client" "15 May 1990, 14:30" "Day Master" \
    --from-chart --tier deep --gender F --birth-year 1990 --birth-month 5 --birth-day 15 \
    --birth-hour 14 --birth-minute 30 --city Seoul --utc-offset 9

# Run tests
pytest

# Optional compliance QA gate on a generated report (needs TYPESAFE_API_KEY)
python3 tools/qa_compliance.py candidates_horoscope/reports/rm/rm_deep.md

# Run a single test verbosely
pytest tests/test_textbook_cases.py::test_park_chung_hee -v
```

## Source anchors

- `tools/build-pdf.sh`
- `src/saju_html/md_to_saju_pdf.py`
- `src/saju_html/md_to_saju_html_pdf.py`
- `src/saju_html/md_to_saju_compat_pdf.py`
- `src/saju_engine/nayin.py`
- `tests/test_textbook_cases.py`
- `tests/test_nayin.py`
- `tests/test_pdf.py`
- `tests/test_saju_qa.py`
- `tools/qa_compliance.py`
