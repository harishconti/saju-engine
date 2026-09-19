# Saju — Four Pillars of Destiny Reading

This project is a **Claude Code skill + knowledge base + calculation engine** for performing Korean Saju (사주) readings grounded in classical principles (오행, 음양, 십신, 격국, 12운성, 대운/세운), plus a client-report pipeline and landing page. The client-facing product targets an **English-speaking global** audience (K-culture fans, diaspora) priced in USD — see `improvements_issues.md` for the go-to-market and `docs/market-research-2026-09.md` for the research.

For the **current state of work** (what's built, what's deferred, the change log) see `tasks.md`. For persistent project memory (conventions, decisions, quick commands) see `docs/MEMORY.md`. For the engine issue tracker, see `docs/issues_bugs.md`. For the **go-to-market strategy, product/landing issues, and the prioritised backlog**, see `improvements_issues.md` (with sourced research in `docs/market-research-2026-09.md`).

> **Project health (2026-09-07):** The engine suite is green (**590 passed**); the three client-launch blockers (G1–G3) and the ₹→USD / English-global pivot are done. Remaining P0/P1 work (real testimonials, checkout, deployment) is tracked in `improvements_issues.md` §12. The engine, PDF toolchain, and HTML/Playwright backend live under `src/`.

## What this gives you

When you invoke `/saju` inside this project, Claude:

1. Loads the persona and ground rules from `CLAUDE.md`.
2. Loads terminology from `knowledge/00-glossary.md`.
3. Loads only the topic knowledge files relevant to your question.
4. Applies the interpretation procedure in `knowledge/09-interpretation-method.md`.
5. Renders the reading using the structure in `knowledge/10-output-template.md`.

The knowledge is **encyclopedic** — stems, branches, ten gods, 12 stages, special formations, luck pillars, and the interpretation method are all documented in depth under `knowledge/`.

## Directory map

```
saju/
├── CLAUDE.md                          # Persona + ground rules
├── README.md                          # This file
├── tasks.md                           # Prioritized project to-do list
├── improvements_issues.md             # Master go-to-market + issues doc (see also docs/market-research-2026-09.md)
├── docs/
│   ├── MEMORY.md                      # Persistent project memory (state, conventions, quick commands)
│   ├── issues_bugs.md                 # Engine issue tracker / decision log (with fix history)
│   ├── market-research-2026-09.md     # Sourced market research (confidence-flagged)
│   ├── audits/                        # Historical engine/architecture audit reports + index
│   ├── openwiki/                      # Reference docs: quickstart, architecture, domain, products, operations
│   ├── superpowers/                   # Design specs + implementation plans
│   └── codex/instructions.md          # Codex project-level instructions
├── pyproject.toml                     # Packaging + dependencies
├── requirements.txt                   # Runtime dependencies
├── requirements-dev.txt               # Development dependencies (pytest, ruff)
├── .claude/
│   ├── settings.local.json
│   └── commands/
│       ├── saju.md                    # /saju slash command
│       └── saju-client.md             # /saju-client order-fulfillment command
├── knowledge/
│   ├── 00-glossary.md                 # Korean / Hanja glossary
│   ├── 01-stems.md                    # 10 Heavenly Stems (천간)
│   ├── 02-branches.md                 # 12 Earthly Branches (지지)
│   ├── 03-five-elements.md            # 오행 theory + interactions
│   ├── 04-yin-yang.md                 # 음양 theory
│   ├── 05-ten-gods.md                 # 십신 (ten gods)
│   ├── 06-twelve-stages.md            # 12운성 (life stages)
│   ├── 07-special-formations.md       # 격국, 신살, 합, 충, 형, 파, 해
│   ├── 08-luck-pillars.md             # 대운 / 세운
│   ├── 09-interpretation-method.md    # Step-by-step reading procedure
│   ├── 10-output-template.md          # Reading output structure + tables
│   └── 11-gunghap.md                  # Compatibility (궁합) — 11 sub-systems, weights, verdict bands
├── src/
│   ├── saju_engine/                   # Calculation engine (sajupy + our lookups)
│   │   ├── engine.py                  # Top-level: compute_chart()
│   │   ├── pillars.py                 # Four-pillar derivation, solar time, Korean/Chinese Zi convention
│   │   ├── lookup.py                  # 십신 / 12운성 / hidden stems / branch relations / 60-cycle helpers
│   │   ├── chart.py                   # Pillar / Chart / DaeunPeriod dataclasses + exporters
│   │   ├── daeun.py                   # Major-luck sequence + starting age
│   │   ├── stars.py                   # Classical 신살 overlays
│   │   ├── strength.py                # Day-Master strength heuristic + 용신/희신 candidate
│   │   ├── yongsin.py                 # Single source of truth for the favorable element (용신) + provenance
│   │   ├── patterns.py                # 천간합 / 화격 / 종격 grid candidates
│   │   ├── daeun_overlay.py           # Major-luck activation overlay
│   │   ├── sewoon.py                  # Annual/monthly/daily luck (세운/월운/일운) windows
│   │   ├── prose_scaffold.py          # Engine-drafted interpretive paragraphs
│   │   ├── prose_fillers.py           # Engine-drafted paragraph fillers (used by premium_report)
│   │   ├── skeleton.py                # Engine-driven markdown scaffold for readers
│   │   ├── premium_report.py          # 9-section tiered client-facing report generator
│   │   ├── report_data.py             # Data tables + pure helpers for premium_report
│   │   ├── stem_profiles.py           # Per-stem imagery/strengths profile table
│   │   ├── hanja_glossary.py          # Hanja term glossary + inline injection
│   │   ├── cli.py                     # Console entry point: saju-engine
│   │   ├── __main__.py                # python -m saju_engine
│   │   ├── compat.py                  # Two-chart 궁합 engine — 11 sub-systems + composite 0–100
│   │   ├── compat_report.py           # generate_compat_report() — standalone 두 분 궁합 product
│   │   └── nayin.py                   # 60 jiazi → 30 Nayin (납음오행) + 서전구미록 6-relationship
│   └── saju_html/                     # PDF rendering package
│       ├── __init__.py                # Shared Korean/Hanja translation maps
│       ├── md_to_saju_pdf.py          # ReportLab two-pass PDF renderer
│       ├── md_to_saju_compat_pdf.py   # Compat PDF renderer (wraps md_to_saju_pdf.build_pdf)
│       ├── md_to_saju_html_pdf.py     # HTML/CSS + Playwright PDF generator CLI
│       ├── renderer.py                # Markdown → HTML + Playwright PDF orchestrator
│       ├── sections.py                # Section card / callout wrappers
│       ├── svg_charts.py              # SVG element-balance + decade-roadmap builders
│       ├── combine_candidate_report.py # Merge base report + follow-up topic files
│       └── theme.css                  # Default premium theme
├── tools/
│   ├── build-pdf.sh                   # Wrapper script (sets up PYTHONPATH, forwards flags)
│   ├── client_intake_form.html        # JSON-only client intake + tier selection form
│   ├── client_intake_server.py        # Tiny server that saves intake submissions as JSON
│   ├── client_intake_app.html         # Self-service form variant with PDF download
│   ├── client_intake_app.py           # FastAPI self-service app that returns tiered PDFs
│   ├── client_compat_intake_form.html # Two-chart compat intake form (Partner A × Partner B)
│   ├── client_compat_intake_server.py # Stdlib HTTP server for compat intake
│   └── build_market_research_html.py  # Renders misc/market_research/*.md → misc/market_research_html/
├── apps/landing-page/                 # Next.js marketing site (own git repo; USD/English-global positioning)
├── tests/                             # pytest suite (590 tests)
├── misc/market_research/              # ⚠️ SUPERSEDED June-2026 India research — see docs/market-research-2026-09.md
└── candidates_horoscope/
    ├── README.md                      # Per-candidate folder conventions + index
    ├── intake/                        # Client intake records (gitignored — may hold PII)
    ├── marriage_compatibility/        # Two-chart 궁합 readings — one subfolder per pair
    │   ├── pawan_sruthi/              # Demo pair: Pawan × Sruthi
    │   └── harish_vinothini/
    └── reports/
        ├── cross-candidate-business-analysis.{md,pdf}
        ├── {slug}/                    # One subfolder per candidate: {slug}-report.{md,pdf} + topic files
        └── rm/                        # Landing-page demo (RM / Kim Nam-joon): sample / essential / report(=deep)
```

## How to use

### Invoke the skill
```
/saju
```

For client order fulfillment (name + birth data + chosen tier → deliverable PDF), use:

```
/saju-client
```

### Ask a reading
Provide the four pillars (or the birth date + time + place) and the focus of the question. Example:

> `/saju — please read my chart.`
> Birth: 1988-08-15, 14:20, Seoul.
> Focus: career and 2026 outlook.

### Example outputs
See `candidates_horoscope/reports/` for worked readings per candidate (e.g. `sruthi/`, `pawan/`).

## Toolchain

Beyond the knowledge base, the project ships two execution paths:

### Calculation engine — `src/saju_engine/`
- **What:** Python module that takes a Gregorian birth date/time/location and returns a fully-derived Saju chart (four pillars + hidden stems + 십신 + 12운성 + major-luck sequence + Day Master + branch relationships + classical stars + Day-Master strength heuristic + special-grid candidates + annual/monthly/daily luck windows).
- **Built on:** `sajupy` (for solar-term month boundaries + base 60-cycle day math) plus our own Korean-명리 lookup tables.
- **Validation:** 520 pytest cases under `tests/`. Run with `python3 -m pytest tests/ -v` from the project root.
- **Solar-time correction:** Enabled by default for non-standard longitudes. Indian births east or west of the IST meridian (82.5°E) are corrected to true solar time before the hour branch and day pillar are derived.
- **Korean `야자시` vs Chinese `조자시`:** defaults to `convention="korean"` (23:00 belongs to the *current* day's 子 hour). Use `--convention=chinese` for the Chinese early-Zi rule.
- **CLI formats:** `table` (default), `json`, `skeleton`, and `premium`. Premium supports `--tier {sample,essential,deep,spark,reading,fullmap}` — the first three are the landing-page products (Hook / Essential Report / Deep Destiny Report), the last three are legacy internal aliases kept for backward compatibility. Skeleton supports `--year`, `--month`, `--day`, `--focus`, and `--no-prose-scaffold`. `--convention` and `--overwrite-report` are available on the PDF wrapper.
- **Dependencies:** declared in `pyproject.toml`. For a fresh machine: `pip install --user --break-system-packages sajupy reportlab pytest`.

### Client intake form — `tools/client_intake_form.html`
- A self-contained, mobile-friendly intake form that asks for name, DOB, birth time, location, email, gender, marriage status, and tier selection.
- The "main concern" textarea is enabled only when **The Deep Destiny Report ($55)** is selected, matching the Mahesh combined-report deep-dive format.
- Run `python3 tools/client_intake_server.py 8080` and open `http://localhost:8080`. Submissions are saved as JSON in `candidates_horoscope/intake/`.

### Self-service calculator — `tools/client_intake_app.py`
- FastAPI web app that extends the intake form: the client fills the same form and receives a tiered PDF immediately.
- Computes the chart with `src/saju_engine/`, generates the premium markdown for the chosen tier, and renders it to PDF via the reportlab backend.
- Saves the intake JSON and the generated PDF (plus its engine markdown) in `candidates_horoscope/intake/`.
- Run `python3 tools/client_intake_app.py 8080` and open `http://localhost:8080`. Requires the `web` optional dependencies: `pip install --user --break-system-packages -e ".[web]"`.
- **Note:** The generated PDF is an engine draft marked `[ENGINE DRAFT — REVIEW REQUIRED]` for Essential and Deep Destiny reports. Use it as a first-pass deliverable only after review, or restrict self-service to **The Hook** (sample tier) for fully automated delivery.
- **Privacy / deployment:** This is a demo deployment pattern. Intake records are stored as unencrypted local JSON and PDF generation is synchronous in the HTTP worker. For production, move to encrypted storage, a background task queue, and email delivery.

### PDF toolchain — `tools/build-pdf.sh` + `src/saju_html/md_to_saju_pdf.py`
- **Two modes:**
  - **From markdown** (default): `./tools/build-pdf.sh sruthi` reads `candidates_horoscope/reports/sruthi/sruthi-report.md` and renders it to PDF.
  - **From chart** (Priority 3 path): `./tools/build-pdf.sh sruthi "Title" "Client" "DOB" "DayMaster" --from-chart --gender F --birth-year 1993 ...` calls the engine and renders the chart directly — no intermediate `.md` needed.
- **Flags:** `--convention korean|chinese` controls the 23:00–00:59 day handling; `--overwrite-report` lets an engine run overwrite an existing `{name}-engine.md`. Use `--tier {sample,essential,deep,spark,reading,fullmap}` with `--from-chart` for tiered engine reports.
- **Style:** English-primary, Korean/Hanja translated inline (translation maps live in `src/saju_html/md_to_saju_pdf.py`). Cover page with title, candidate info, Day Master, generation date. Body has clean headings, alternating-row tables, footer with page numbers.
- **Dependencies:** `reportlab` is declared in `pyproject.toml`; the wrapper script sets up `PYTHONPATH` automatically.

### HTML/Playwright PDF backend — `src/saju_html/md_to_saju_html_pdf.py`
- **Opt-in:** `./tools/build-pdf.sh --html sruthi` routes to the new renderer; default remains reportlab.
- **Technology:** markdown → `markdown-it-py` → styled HTML → Playwright/Chromium → A4 PDF.
- **Why use it:** better table typography, easier theming via CSS, and native `@page` print controls.
- **Shared translation maps:** `src/saju_html/__init__.py` keeps both backends in sync.
- **Dependencies:** `playwright` (runtime); `markdown-it-py` (already present).

### Two-chart compatibility pipeline — `src/saju_engine/compat.py` + `src/saju_html/md_to_saju_compat_pdf.py`
- **Engine:** `compat_score(chart_a, chart_b)` in `src/saju_engine/compat.py` runs all 11 sub-systems (일간합 → 띠 궁합), weights them per `knowledge/11-gunghap.md`, and returns a `CompatReport` with composite 0–100 score + 4-band verdict.
- **Standalone report:** `generate_compat_report(chart_a, chart_b, name_a, name_b, tier="basic"|"deep")` in `src/saju_engine/compat_report.py` produces a tiered markdown report. `basic` is the ~4-page compact snapshot; `deep` is the full 11-sub-system report plus individual chart snapshots + timing overlay.
- **Intake form:** `tools/client_compat_intake_form.html` is a two-chart variant — symmetric Partner A | Partner B layout, single email + main-concern field. Stdlib server at `tools/client_compat_intake_server.py` saves submissions as JSON to `candidates_horoscope/intake/`.
- **Self-service route:** `python3 tools/client_intake_app.py 8080` then visit `/compat` for an immediate basic-tier PDF; the FastAPI app computes both charts, runs `compat_score`, and renders the compat PDF on the fly.
- **Standalone renderer:** `python3 src/saju_html/md_to_saju_compat_pdf.py <compat.md> --name-a ... --name-b ... --tier basic|deep` produces a premium-styled PDF with both partners on the cover, composite score as a header block, and the sub-system cards selected by tier.
- **Demo pair:** Pawan × Sruthi in `candidates_horoscope/marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility.{md,pdf}` (basic) and `pawan_sruthi/pawan_sruthi_compatibility_deep.{md,pdf}` (deep).
- **Knowledge reference:** `knowledge/11-gunghap.md` (1002 lines) — the classical Korean Myeongri reference grounding every sub-system.

## Developer quick commands

```bash
# Run the pytest suite (includes the cross-validation cases in tests/test_cross_validate.py)
python3 -m pytest tests/ -v

# Compute a chart from the CLI
saju-engine --date 1993-12-11 --time 02:45 --city "Pallipat" --gender F --format table

# Build a PDF from an existing markdown report
./tools/build-pdf.sh sruthi
```

## Writing your own reading

1. Create a new candidate subfolder under `candidates_horoscope/reports/` (see `candidates_horoscope/README.md` for naming).
2. Fill in the four pillars.
3. Follow the procedure in `knowledge/09-interpretation-method.md`.
4. Render using `knowledge/10-output-template.md`.

## Client products

Report tiers implemented in the engine and exposed to clients via the intake forms. Prices are USD
launch prices; the target market is **English-speaking global** (see `improvements_issues.md` for the
strategy and `docs/market-research-2026-09.md` for the research behind it).

| Tier | Name | Price | Length | Core Contents |
|---|---|---|---|---|
| 1 | **The Hook** ✦ | Free | 1 page | Compact cover + four pillars + element balance + Day Master + lucky colors/directions/numbers + invitation to upgrade |
| 2 | **The Essential Report** ✦✦ | $9 intro → $19 | 6–7 pages | Cover + four pillars + element balance + quick reference + short Day Master portrait + Career & Wealth overview + Major Luck (대운) table + abbreviated Lucky Attributes + short Closing Note |
| 3 | **The Deep Destiny Report** ✦✦✦ | $55 | 10–12 pages | Everything in Essential + full Day Master portrait + Relationships + Health & Vitality + Business & Launch Timing + year-by-year windows + full Practical Guidance + full Closing Note. (The MP3 audio summary is produced separately.) |
| 4 | **Compatibility Snapshot (두 분 궁합)** ✦✦✦ | $24 | ~4 pages | Two-chart snapshot: composite 0–100 + 4-band verdict on cover; four-pillar glance; the four most decisive sub-systems; condensed Practical Guidance; Closing Note. |
| 5 | **Deep Compatibility (두 분 궁합)** ✦✦✦✦ | $45 | 9–10 pages | Basic + all 11 sub-system cards (일간합, 일지 합충, Nayin, 용신, 일주, 결합 오행, 십신 교차, 대운 동기, 신살, 음양, 띠); individual element balance / Day Master snapshots; major-luck timelines for both partners; year-by-year couple timing overlay; full Practical Guidance; Closing Note. |
| — | **Cosmic Companion** (subscription) | $9/mo or $79/yr | 3–4 pages | Monthly timing read; manual billing; off the primary pricing grid. |

Engine usage: `python -m saju_engine --format premium --tier {sample,essential,deep} ...` for single-chart. For Compat (두 분 궁합): `generate_compat_report(chart_a, chart_b, name_a, name_b)` from `src/saju_engine/compat_report.py`, then render via `python3 src/saju_html/md_to_saju_compat_pdf.py <md-path> --name-a ... --name-b ...`.

The legacy internal tiers (`spark` $9, `reading` $55, `fullmap` $129) remain engine-supported for backward compatibility, but new client orders should use `sample`, `essential`, `deep`, or the compatibility (`compat`) products (`basic`/`deep`).

## Limitations

- The **slash command** (`/saju`) does not auto-calculate the four pillars from a date. It asks the user to supply them (or a chart from a trusted source). Saju software disagrees on the precise solar-term cutoff, the time-zone interpretation for places outside Korea, and the handling of "double-pillar" months. The skill defaults to user-supplied charts rather than guess.
- The **calculation engine** at `src/saju_engine/` can derive pillars from a date/time/location programmatically. It's used for cross-verification, the `--from-chart` PDF path, the self-service app, and the validation test suite — but it is not wired into the `/saju` slash command yet.
- The **self-service calculator** can fully automate **The Hook**. Essential/Deep Destiny PDFs are engine drafts marked `[ENGINE DRAFT — REVIEW REQUIRED]` and require human review before client delivery.
- The skill covers the Korean 명리 (Myeongri) tradition. Other East-Asian systems (BaZi mainland style, Zi Wei Dou Shu, QMDJ) are out of scope.
- Readings describe tendencies and timing, not fixed outcomes.

## License of materials

The reference files in `knowledge/` are written for this skill and are not copied from any single copyrighted text. Classical terms and standard interpretations are used; they are part of the public traditional corpus of 명리학.
