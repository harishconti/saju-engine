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
| `tools/audit-ui.py` | **UI/UX audit and CI gate** for the deployed webapp: real Chrome at 390/768/1440 px in both colour schemes, reporting horizontal overflow, axe-core violations, hydration warnings, `<h1>` count, missing shells and sub-44 px controls. `--strict` fails on any of them; wired into CI as the `ui` job. See `docs/webapp/12-testing.md`. |
| `tools/prune_deployments.py` | Prunes old Vercel deployments, because Functions Storage counts every retained function bundle (~157 MB per engine deployment here). Dry-run by default, always passes `--safe` so an aliased deployment cannot be removed, and keeps the newest `--keep` (default 3) for rollback. Runbook: [09-operations.md](../webapp/09-operations.md). |
| `tools/build-web-fonts.py` | Subsets the app's three webfaces (Inter, Cormorant Garamond, IBM Plex Mono) to the glyphs a report sets and writes them as `woff2` into `src/saju_html/fonts/`, with the OFL notices. `--check` verifies coverage and reports glyphs the face itself lacks. Run it when the app's font stack changes. |
| `tools/build-cjk-font-subset.py` | Regenerates the bundled Hangul/Hanja font subset (`src/saju_html/fonts/SajuCJK-*.ttf`) from OFL Noto Sans KR, scanning report-prose sources only; `--check` verifies coverage. Run it after adding Hanja to `knowledge/`. |
| `tools/build-icons.py` | Builds the browser-tab icons (`src/app/favicon.ico`, `icon.png`, `apple-icon.png`) from the brand mark, set in **Cormorant Garamond** — a favicon must not depend on which serif the viewer happens to have, which is why the old `favicon.svg` (Georgia) was not reused. `apple-icon.png` is drawn square because iOS applies its own mask. `--check` asserts the gold glyph actually rendered, since a blank tile is still a valid PNG. |
| `tools/build-cities.py` | Builds `apps/web/public/city-index.json`, the birthplace picker's searchable index (GeoNames `cities5000`, ~70k places, ~0.83 MB gzipped, fetched in the background). It **fails on a dead alias target or a missing required place**, because both failure modes are silent in production: a dead alias tells someone their hometown is not a real place, and a missing place cannot be submitted at all. `--check` verifies coverage. Run it when the picker needs a place it does not have. |
| `tools/build-og-fonts.py` | Derives the **TTFs the Open Graph image needs** (`apps/web/src/lib/og-fonts/`) from the committed woff2 subsets, and instances the variable fonts to a static weight first — Satori (`next/og`) cannot read a variable font, and it rejects woff2 outright. Run it if the web fonts change; `--check` reports glyph coverage. |
| `tools/suggest_letter.py` | **Review-time letter drafter** (suggest-only, never in the delivery path). Builds a *grounding pack* from the computed chart plus `knowledge/` excerpts and asks an API-key provider (Ollama Cloud by default, `deepseek-v4.1-flash`) for the one page a template cannot write. `--dry-run` prints the exact request and sends nothing; no PII is included; unknown citations, invented numbers, wrong length, a missing birth-time caveat or any client-ready gate finding fails the draft. Writes to `--out`/stdout only — it never edits a report. See `src/saju_ai/` and [products/reports.md](../products/reports.md). |
| `tools/smoke_compat_reading.py` | **Live end-to-end smoke** for a compatibility reading: signs its own R2 PUT/GET/DELETE URLs (SigV4, stdlib only), asks the *deployed* engine for a compat reading with `htmlUploadUrl`, then fetches the objects back and checks both artefacts arrived, that the document is the two-chart one, is self-contained and `noindex`, and passes the client-ready gate. Deletes everything it creates. Needs `apps/web/.env` (R2 + engine token) and network, so it is **manual, never CI**. |
| `tools/qa_client_ready.py` | **Client-ready gate**: fails a report carrying internal jargon (`querent`, `the engine`, `Step N`, raw engine keys), template debris, double glosses, a lowercase client name, an `a Earth` article, a repeated word, a sentence repeated more than twice, or a price. Runs on the engine markdown *and* (`--pdf`) on text extracted from the artefact, because only there can a renderer leak show up. Needs `pdftotext` (poppler) for the PDF half — and when it cannot read the artefact it raises `ARTEFACT_NOT_CHECKED` instead of returning clean, which is why `approve` blocks rather than silently approving an unread report. `intake_admin.py approve` runs it and refuses to issue a link unless `--force`. Wired to `tests/test_qa_client_ready.py`. |
| `tools/qa_compliance.py` | Optional compliance QA gate for a report markdown file (ground-rule check on generated prose). Requires `TYPESAFE_API_KEY`. |

## Running the test suite

```bash
pytest
```

The suite currently contains ~1,909 cases (as of 2026-10-11). Core coverage includes:

> **Two suites, not one.** This page covers the **Python engine**. The webapp (`apps/web`) has its own
> Vitest suite (**112 passed / 4 skipped**) plus the UI audit above, and all three run in CI — see
> `docs/webapp/12-testing.md`.

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
- `--web` writes the standalone **web document** instead of a PDF (no browser involved): one self-contained HTML file with heading anchors, a linked contents list, scrollable tables, an optional `--audio-url` player, and `noindex`. See [products/reports.md](../products/reports.md) § The web document. `tools/qa_client_ready.py --html` gates the artefact.
- Use `--compact` for the one-page Hook/sample tier. `src/saju_html/chart_input.py` is the shared chart-to-markdown step for `--from-chart`.
- **No silent fallback:** a missing browser raises. The renderer falls back to ReportLab only with `allow_fallback=True` or env `SAJU_PDF_FALLBACK=reportlab`.
- Korean/Hanja is translated **and kept**: client copy reads `Direct Officer (正官)`, per the owner's convention (2026-10-16). Unmapped CJK is kept and reported, never deleted. The gloss is the `gloss=True` argument of `translate_inline`, which is why the audio script can stay English-only. Phrase-level Korean glosses live in `_PHRASE_RULES` (`src/saju_html/__init__.py`).
- Env `SAJU_PDF_BACKEND=reportlab` makes the self-service job queue (`src/saju_web/jobs.py`) use ReportLab.

### ReportLab backend (legacy, one more release)
- Opt-in with `./tools/build-pdf.sh --reportlab`; writes `{name}-report-reportlab.pdf` / `{name}-combined-reportlab.pdf` so it never overwrites the HTML PDF. `--html` is a no-op alias.
- Uses DejaVu fonts for Latin and a **bundled glyph subset of Noto Sans KR** (`src/saju_html/fonts/SajuCJK-*.ttf`) for the Hangul/Hanja that survives translation — embedded, so CJK renders in Chrome and phone viewers, unlike the Korean CID faces it replaced. A character no Korean face can draw is dropped with a stderr warning rather than printed as a tofu box. Regenerate the subset after adding Hanja to `knowledge/` with `python3 tools/build-cjk-font-subset.py` (`--check` verifies coverage).
- **Two-pass build** producing a linked contents page with page numbers, a PDF outline, and Title/Author/Subject/Creator metadata; markdown blockquote notes render as notes. See `docs/openwiki/products/reports.md` § The PDF artefact.
- Planned for removal after one release. Note that the *webapp* engine service renders with ReportLab (`api/index.py`), where Chromium does not fit in a Vercel function.

### Compat PDF
- Separate tool in `src/saju_html/md_to_saju_compat_pdf.py` (HTML/Chromium default; `--backend reportlab` uses a Korean CID font).
- `--web` writes the compat **reading** — the same self-contained screen document the single-chart tiers get (`markdown_to_html(web=True)`, tier-agnostic apart from the `tier-compat` body class). Give `--output` an `.html` path; the default output becomes `…_compatibility.html` beside the pair. No browser is needed.
- Tier-aware translation skip keeps couple names and verdicts intact.

## Regenerating client reports

`tools/regen_client_reports.sh` rebuilds every engine-generated client artefact from a fixed
reference date (`REF` in `tools/regen/markdown.sh`; edit it for a new date):

1. `tools/regen/markdown.sh` — base reports, engine `career`/`luck-cycle`, tier files.
2. `tools/regen/compat.py` — the compatibility pairs (basic + deep).
3. `src/saju_html/combine_candidate_report.py` — the combined single-chart reports.
4. `tools/regen/pdfs.sh` — the PDF keepsakes (HTML/Chromium backend; also rewrites the public demo PDFs/readings).
5. `tools/regen/html.sh` — the **web documents** (readings), one beside each canonical `.md` (`--web`, no browser needed).

Hand-authored files are excluded deliberately: `harish`/`gurumoorthy`/`mahesh`/`vishnu-priya`
`career.md` (and `vishnu-priya/relationships.md`), the `*-legacy.md` and engine-draft
(`*-engine*.md`) files, and `harish_vinothini` (no birth data on record).

## Continuous development checklist

- Run `pytest` before committing.
- Run `npm test` / `npm run lint` / `npm run build` in `apps/web/` for landing-page or webapp changes.
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
- `tests/test_pdf_navigation.py`
- `tests/test_web_report.py`
- `src/saju_html/theme-web.css`
- `src/saju_html/fonts/` (the embedded webfaces and their licence)
- `tests/test_qa_client_ready.py`
- `tests/test_saju_ai_letter.py`
- `src/saju_ai/pack.py`
- `tests/test_saju_qa.py`
- `tools/qa_compliance.py`
