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
| `src/saju_html/md_to_saju_pdf.py` | ReportLab two-pass PDF renderer. |
| `src/saju_html/md_to_saju_html_pdf.py` | HTML/CSS + Playwright rich renderer. |
| `src/saju_html/md_to_saju_compat_pdf.py` | Compat-specific PDF renderer with Korean CID font. |
| `tools/build-pdf.sh` | Wrapper that sets `PYTHONPATH`, site-packages, and dispatches to the chosen backend. |
| `src/saju_html/combine_candidate_report.py` | Merges base report + topic follow-ups into a single client deliverable. |
| `tools/client_intake_form.html` + `client_intake_server.py` | JSON-only intake form. |
| `tools/client_intake_app.html` + `tools/client_intake_app.py` | Self-service FastAPI tiered calculator. |

## Running the test suite

```bash
pytest
```

The suite currently contains ~548 cases (as of 2026-07-12). Core coverage includes:

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

## Engine validation priorities

- **Priority A — Foundation tables.** Verifiable against standard Korean almanac tables.
- **Priority B — Korean textbook cases.** Presidential birth charts from publicly available articles; used for end-to-end date→pillar validation.
- **Priority C — Classical star corpus.** Implemented from `knowledge/07-stars.md` with documented ambiguity rules.
- **Priority D — PDF rendering.** Visual regression via the Hanja-pair test and manual spot checks.
- **Priority E — Compatibility engine.** Score distribution checked against known demo pairs.

## Adding a new textbook case

1. Collect multiple independent Korean sources confirming the year/month/day/hour pillars.
2. Add the case to `tests/test_textbook_cases.py`:
   ```python
   ("Case Name", (YYYY, MM, DD, HH, MM), ("Year Stem", "Year Branch", ...), "source URL"),
   ```
3. Run `pytest tests/test_textbook_cases.py -v` and confirm the engine matches.
4. If there is any discrepancy, leave the case as `pytest.mark.xfail` and document the divergence in the test docstring.
5. Update `docs/MEMORY.md`, `MEMORY.md`, and `tasks.md` with the new case and test count.

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

### ReportLab backend
- Default, no browser required.
- Uses DejaVu fonts for Unicode.
- Two-pass build: first pass measures content, second pass lays out pages.
- Adds branded footer and report ID.

### HTML/Playwright backend
- Requires Playwright and a browser install.
- Renders Quick Reference as a card, current-year paragraph as a callout, Lucky Attributes as a grid, and adds an SVG element-balance chart.
- Use `--compact` for the one-page Hook/sample tier.

### Compat PDF
- Separate renderer in `src/saju_html/md_to_saju_compat_pdf.py`.
- Uses a Korean CID font for CJK characters.
- Tier-aware translation skip keeps couple names and verdicts intact.

## Continuous development checklist

- Run `pytest` before committing.
- Run `npm test` / `npm run lint` / `npm run build` for landing-page changes.
- Keep citations in `.md` files; client PDFs strip them automatically.
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

# Render to PDF
./tools/build-pdf.sh --from-chart report.md "Title" "Client" "1990-05-15" "Day Master"

# Render HTML/Playwright PDF
./tools/build-pdf.sh --html --from-chart report.md "Title" "Client" "1990-05-15" "Day Master"

# Run tests
pytest

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
- `tasks.md`
