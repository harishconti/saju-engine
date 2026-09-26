# Saju Project Memory

> **Context file:** `CLAUDE.md` (primary agent persona + ground rules)  
> **Task tracker:** `tasks.md`  
> **Project overview:** `README.md`  
> This file tracks persistent facts, decisions, and conventions that should be remembered across sessions when working on the saju repo.

## Project Identity

- **Name:** Saju Engine (PyPI-style package name `saju-engine`, version `0.2.0`)
- **What it is:** Korean Saju (Four Pillars of Destiny / 사주, 四柱) calculation engine, PDF toolchain, and Claude Code skill.
- **Author:** Harish Gurumoorthy
- **License:** MIT
- **Stack:** Python 3.10+, `sajupy==0.2.0` (pinned 2026-09-26 — see N-17 below; was `>=0.2.0`), `reportlab>=4.1`, optional `playwright`, optional `fastapi`/`uvicorn`.

## Current State (last updated 2026-09-26)

- **Two 2026-09-26 audit passes closed 22 + 16 findings, 26 of 38 fixed.** See "Recent Changes"
  below and `docs/audits/2026-09-26-deep-engine-audit-verification.md` for the live tracker of the
  second pass. **Suite: 1094 passed / 9 xfailed / 0 failed.** Validation gate:
  `python3 tools/run_validation.py` → `204 (PASS 200, INTERPRETATION 4, FAIL 0)`. `ruff check
  --select F src tools tests` is now clean and enforced in CI (was not run in CI before this pass).
  **Three doctrinal items are decided but not yet implemented** — N-5 (yin DM strength should read
  season/element relation, not 12운성 stage), N-9 (양인격/건록격 should also recognize a
  month-branch/월령 case, kept distinct from the existing year/day/hour case), and N-6 (조후 gate
  needs more research before a chart-extremeness threshold is picked). Do not assume these are done
  — check the tracker doc before relying on strength/조후/grid output for a yin-DM or hot/cold-month
  chart.

- Engine is feature-complete for the current product scope, now including a 조후 (climate-balance)
  cross-check on top of the existing 억부 (strength-balance) 용신 heuristic — see the 2026-09-13
  entry below and `knowledge/17-climate-method.md`.
- **885 pytest tests pass / 10 xfailed / 0 failed** (`python3 -m pytest` from the repo root; verified
  2026-09-14 late evening, after the item-1 fix below). The 10 xfails are `xfail(strict=False)`
  markers asserting the *correct* behaviour that a still-unfixed defect blocks — "still xfailed"
  means *still defective*; the marker turning XPASS is the delete-the-marker signal. Cross-validation
  cases are in `tests/test_cross_validate.py` (the standalone harness was folded in and deleted).
- **Validation campaign closed 2026-09-14:** all six workstreams certified — 194 checks / 189 PASS /
  5 INTERPRETATION / 0 FAIL across 8 subsystems (W1 pillars 17, W2 대운·세운 19, W3 lookups 56,
  W4 용신 13, W5 조후 30, W6 compat+career 59). Gate commands and expected output:
  `python3 tools/run_validation.py` → `194 (PASS 189, INTERPRETATION 5, FAIL 0)`, exit 0, stdout md5
  `9626959ad9b18f658fa49adb1b3ebeee`. The rendered report
  `docs/audits/2026-09-engine-validation-report.md` is **produced by that tool — never hand-edit it**;
  current render md5 `c697db8f529cb992f07de623598869b4`.
- **Post-campaign fix wave landed (2026-09-14) — tree is CLEAN, not dirty.** The user directed work on
  the 13 loose ends the campaign pinned but didn't fix (see `memory/saju-open-defects-triage.md` in
  Claude's own memory for the full record). **Nine are now fixed:** #5 (nayin order-dependence), #6
  (career tier-pool Day-Master→용신/희신 rekey, which also fixed client-visible item 2), #8
  (`md_to_saju_compat_pdf.py --output` path bug), #9 (Harish longitude 76.33→79.42), #11 (辰/戌 climate
  divergence, resolved as documentation+scope not a model change), #12 (unsourced dry/damp claim
  removed), #13 (dead `_CHECKERS` registry pruned), and **#4 + client-visible item 3 together**,
  landed as **"(A) + C-none"**: the 육합 (six-combination) dead-code arity fix in
  `compat.py::_branch_pair_lookup` (moved exactly one fixture, `compat-mahesh-vp` 64/Mixed→68/Strong),
  plus documenting the 삼형 (branch-punishment) chain position as an unsourced scope limit — C9 stays
  pinned by design, not a bug. `src/saju_engine/compat.py` current md5 `9de82a5548caaf22828a2298a591966e`
  — this is the **sanctioned final state**, not the mid-experiment variant. (An earlier same-day
  session note about a "dirty tree at variant A-high" describes a since-resolved intermediate state;
  do not act on it.)
- **Client-visible item 1 — FIXED 2026-09-14 late evening.** `premium_report.py`'s
  `_right_now_callout()` and `ctx_favorable_phrase()` now read the resolved `favorable_element()`
  value (with `ctx.favorable_override` threaded through) instead of the raw candidate field. This
  closes the entire two-channel bug class found by the campaign. Harish's `harish-report.md` was
  regenerated from scratch the same session and now shows Water natively (previously a hand-patch).
  **#7** (regenerating client reports affected by the 야자시 hour-stem fix, plus Harish's stale
  follow-ups) is still in progress, not complete — see "Active Wishes / Open Items" below. Two
  **product decisions** (not defects) remain surfaced but undecided: #10 (조후-vs-억부 gate width)
  and whether `climate.py` should expand to the full 寒暖燥濕 four-way 궁통보감 reading.
- **Products implemented** (USD, after the 2026-09-07 pivot — see `improvements_issues.md`):
  - **The Hook** (`sample`) — free 1-page report.
  - **The Essential Report** (`essential`) — $9 intro → $19, 6–7 pages.
  - **The Deep Destiny Report** (`deep`) — $55, 10–12 pages.
  - **Cosmic Companion** (`companion`) — $9/month or $79/year, 3–4 pages; manual-billing subscription (off the primary pricing grid).
  - **두 분 궁합 / Compatibility** (`compat`) — Snapshot ($24) and Deep ($45) tiers, 11 sub-systems, composite 0–100 score. Deep is the hero product.
- **Intake paths:** JSON-only form (`tools/client_intake_form.html` + server), self-service FastAPI calculator (`tools/client_intake_app.py`), two-chart compat intake form + server, and landing-page Next.js app (`apps/landing-page`) wired to the calculator for the free sample tier.
- **PDF backends:** reportlab (default) and HTML/Playwright (`--html`).
- **Major recent additions (2026-06-21 through 2026-07-12):** daily-luck (일운) overlay, engine-driven prose scaffold, premium report generator, landing-page tiered products, major-luck activation overlay, marriage-compatibility engine + report + PDF renderer, 30×30 Nayin pair table, Korean textbook 만세력 validation cases, repo-root documentation consolidation into `docs/`, Cosmic Companion subscription tier, deeper special-formations validation tests, richer engine-drafted prose fillers, landing-page/free-sample integration, complete `docs/openwiki/` reference site (README + quickstart + architecture + domain + products + operations), and landing-page demo reports generated from RM (Kim Nam-joon, BTS) birth data for all three single-chart tiers.

## Strategy (2026-09-07 pivot)

Triggered by the deep-dive research report `research-engine/output/2026-09-07/report-saju.html`.
The product moved from an **India / ₹ / Vedic-adjacent NRI** framing to an **English-speaking-global
/ USD** one. India is now a Phase-2 PPP experiment only. Positioning: *"an accurate engine and an
honest interpreter — not a Korean master."* Lowest-CAC channel is organic short-form video; the
compatibility (궁합) product is the marketing hero. Realistic revenue ceiling with manual
fulfilment: ~$1–3K/month; most likely 12-month outcome is a kill/skip.

- **Master execution doc:** `improvements_issues.md` (root) — issues, backlog (P0–P3), pricing, plan.
- **Sourced research:** `docs/market-research-2026-09.md` — every market number with a confidence flag.
- **Design spec:** `docs/superpowers/specs/2026-09-07-saju-business-refinement-design.md`.
- **P0 blockers fixed 2026-09-07:** G1 (reviewer-note leak into client PDFs), G2 (per-pillar template
  grammar), G3 (용신 single source of truth via `src/saju_engine/yongsin.py` + provenance), G6 (₹→USD
  in engine text). Suite 568 → 590.

## Decisions to Remember

1. **Package layout:** The Python packages live under `src/`: `src/saju_engine/` and `src/saju_html/`. `pyproject.toml` declares `where = ["src"]` and `pytest` adds `src` to `pythonpath`. Direct-run scripts under `src/saju_html/` and `src/saju_engine/` insert `src/` into `sys.path` so they still work when invoked directly.
2. **Calculation backend:** Use `sajupy` for solar-term and 60-cycle math; all Korean / Myeongri (명리) lookups and overlays are our own.
3. **Zi-hour convention:** Default is `korean` (야자시, 23:00–00:59 belongs to the *current* day's 子 hour). Use `chinese` for the early-Zi / 조子시 rule if requested.
4. **Solar-time correction:** Enabled by default for non-standard longitudes. Indian births are corrected from the IST meridian (82.5°E) before deriving hour branch and day pillar.
5. **Engine output is a draft:** Premium reports are explicitly marked `[ENGINE DRAFT — REVIEW REQUIRED]`. Human review is required before delivering paid tiers to clients.
6. **No custom ephemeris:** `sajupy` is sufficient for the target accuracy; a from-scratch ephemeris is explicitly out of scope.
7. **No public web app in repo:** The FastAPI self-service app exists for local use; deployment to a public endpoint is a separate, deliberate decision.
8. **Language:** Primary output language is English; technical terms include Korean (한글) and Hanja (한자) on first use.
9. **용신 resolution order (as of 2026-09-13):** `yongsin.favorable_element(chart, override=None)` checks, in order: (1) an explicit `override=` argument, (2) `chart.strength_assessment["reader_override_favorable"]` (set by `compat.py::compat_score`'s `favorable_element_a`/`_b` params — this is what lets a compat report's reader override survive the climate merge), (3) for a **balanced** verdict born in a **hot** (巳午未) or **cold** (亥子丑) month, the 조후 climate element wins the headline (`method="climate-balanced"`) over the old "least-represented element" fallback, (4) otherwise the existing 억부 strong/weak-drain/support logic (unchanged) — see `src/saju_engine/climate.py` + `knowledge/17-climate-method.md`. `compat.py`'s 4 scoring functions (`compat_yongshin`, `_spouse_palace_virtue`, `compat_combined_elements`, `compat_tengod_cross`) all route through `favorable_element()` now too (via `_resolved_favorable`/`_resolved_supporting` helpers), not the raw `strength_assessment` fields directly — this keeps compat *scoring* and *display* from disagreeing.

## File Map

| Need | File |
|---|---|
| Agent persona / ground rules | `CLAUDE.md` |
| Project overview & quickstart | `README.md` |
| Prioritized task list & changelog | `tasks.md` |
| This memory file | `docs/MEMORY.md` |
| Engine issue tracker + fix history | `docs/issues_bugs.md` |
| Go-to-market strategy, product/landing issues, backlog | `improvements_issues.md` (root) |
| Sourced market research | `docs/market-research-2026-09.md` |
| Historical engine/architecture audits | `docs/audits/` |
| Design specs + implementation plans | `docs/superpowers/` |
| Reference doc site | `docs/openwiki/` |
| Knowledge base (interpretive reference) | `knowledge/00-glossary.md` through `knowledge/17-climate-method.md` |
| Calculation engine | `src/saju_engine/` |
| HTML/PDF shared helpers | `src/saju_html/` |
| PDF builders | `src/saju_html/md_to_saju_pdf.py`, `src/saju_html/md_to_saju_html_pdf.py`, `src/saju_html/md_to_saju_compat_pdf.py`, `tools/build-pdf.sh` |
| Report combiner | `src/saju_html/combine_candidate_report.py` |
| Tests (includes cross-validation cases) | `tests/` |
| Per-candidate readings | `candidates_horoscope/reports/{slug}/` |
| Client intake records (gitignored — may hold PII) | `candidates_horoscope/intake/` |
| Slash commands | `.claude/commands/saju.md`, `.claude/commands/saju-client.md` |
| Codex project instructions | `docs/codex/instructions.md` |
| Codex skills (user-level) | `~/.codex/skills/saju-reading/`, `~/.codex/skills/saju-client-order/` |

## Conventions

### Candidate folders
- One subfolder per candidate: `candidates_horoscope/reports/{name-slug}/`
- Slug style: lowercase, hyphenated.
- Base natal reading: `{slug}-report.md`
- Topic follow-ups: `career.md`, `relationships.md`, `health.md`, `2027-outlook.md`, etc.
- Overlapping follow-ups append to the existing file under a dated heading: `## YYYY-MM-DD — summary`.
- Consolidated client PDF: `{slug}-combined.{md,pdf}` generated via `src/saju_html/combine_candidate_report.py {slug}`.

### Compatibility reports
- All compat reports live under `candidates_horoscope/marriage_compatibility/{name_a_slug}_{name_b_slug}/` (one subfolder per pair).
- Basic tier: `{name_a_slug}_{name_b_slug}_compatibility.{md,pdf}`.
- Deep tier: `{name_a_slug}_{name_b_slug}_compatibility_deep.{md,pdf}`.
- Partner A is listed first; for heterosexual pairs Partner A is the male.
- Update the **Compatibility (궁합) readings** table at the bottom of `candidates_horoscope/README.md`.

### Client products (USD — 2026-09-07 pivot)
| Client-facing name | Engine tier | Price | Page target | Notes |
|---|---|---|---|---|
| The Hook | `sample` | Free | ~1 page | Fully automatable. |
| The Essential Report | `essential` | $9 intro → $19 | 6–7 pages | Engine draft → review required. |
| The Deep Destiny Report | `deep` | $55 | 10–12 pages | Includes year-by-year windows; MP3 audio summary wording included by default. |
| Compatibility Snapshot (두 분 궁합) | `compat_report(..., tier="basic")` | $24 | ~4 pages | Two-chart snapshot: composite 0–100 score + 4-band verdict, four-pillar glance, four decisive sub-systems, condensed Practical Guidance, Closing Note. |
| Deep Compatibility (두 분 궁합) — hero | `compat_report(..., tier="deep")` | $45 | 9–10 pages | Basic + all 11 sub-system cards, per-partner element balance / Day Master snapshots, major-luck timelines, year-by-year couple timing overlay, full Practical Guidance, Closing Note. |
| Cosmic Companion | `companion` | $9/mo or $79/yr | 3–4 pages | Manual-billing subscription; off the primary pricing grid. |

`generate_compat_report` accepts `favorable_element_a` / `favorable_element_b` — pass the reader-argued 용신 so the natal and compat products agree (see `src/saju_engine/yongsin.py`).

Legacy tiers `spark`, `reading`, and `fullmap` are still accepted by the engine but map to `essential`/`deep`/`deep` and should not be sold to new clients.

### Engine-first rule
When a user supplies a Gregorian birth date, time, and place, run the engine first to get a structured skeleton. When the user supplies the four pillars directly (년주/월주/일주/시주), accept them and proceed without the engine.

## Quick Commands

```bash
# Run the full pytest suite (includes cross-validation cases)
python3 -m pytest tests/ -v

# Generate an engine skeleton for interpretive work
PYTHONPATH=src python3 -m saju_engine \
  --date YYYY-MM-DD --time HH:MM --gender M --city "City" \
  --format skeleton --output-file /tmp/skeleton.md

# Generate a premium client-facing draft
PYTHONPATH=src python3 -m saju_engine \
  --date YYYY-MM-DD --time HH:MM --gender M --city "City" \
  --name "Client" --format premium --tier essential \
  --output-file /tmp/premium.md

# Build PDF from an existing markdown report
./tools/build-pdf.sh sruthi

# Build a consolidated client PDF (base report + topic follow-ups)
./tools/build-pdf.sh --combined --html sruthi "Title" "Client" "DOB" "Day Master"

# Build a compatibility PDF
python3 src/saju_html/md_to_saju_compat_pdf.py <compat.md> --name-a ... --name-b ...
```

## Active Wishes / Open Items

See `improvements_issues.md` §12 for the prioritised P0–P3 backlog and `tasks.md` for the engine
history. As of 2026-09-07 the engine P0 blockers (G1–G3, G6) are fixed. Open P1 items:
- **Merchant-of-Record checkout** (Lemon Squeezy / Paddle) for paid tiers and the Companion subscription — nothing is charged today.
- **Real testimonials** on the landing page — the current ones are flagged illustrative and must be replaced or removed before launch (FTC risk).
- Self-service app hardening: encrypt PII, background queue, auth (`tools/client_intake_app.py`).
- Deployment hardening for the landing-page Next.js app and FastAPI calculator.
- Populate the 30×30 Nayin pair table from a published source (currently on the 5-element fallback).
- Optional additional Korean textbook 만세력 cases if more independent sources are found.
- **`premium_report.py` "What This Year Means for You" bug — FIXED 2026-09-14.**
  `_right_now_callout()` (line 181) and `ctx_favorable_phrase()` (line 1399, called from
  `_year_one_liner`) now take an `override: Optional[str] = None` param, read
  `favorable_element(chart, override).element` instead of the raw
  `strength_assessment["candidate_favorable"]`, and both call sites (`_section_chart_glance`'s
  "What This Year Means" block, `_year_one_liner`'s Hook-tier one-liner) thread
  `ctx.favorable_override` through. This was the last surface in the two-channel bug class (the
  matching `report_data.py` career-section bug was fixed earlier the same day). The 2
  `xfail(strict=False)` markers in `tests/validation/test_val_climate.py:234`/`:255` XPASSed and
  were retired — the tests now stand as plain regression locks. Suite 883/12 → **885 passed / 10
  xfailed / 0 failed**; validation CLI gate unchanged at `194 (PASS 189, INTERPRETATION 5, FAIL 0)`
  (these 2 tests were never part of the CLI's own check count). **Note for future regens:** this
  fix changes the "What This Year Means for You" / Hook-tier one-liner text for any *already
  generated* report whose raw candidate element differs from its resolved element (climate-merged
  or reader-overridden charts) — worth checking before treating an old PDF as current.
- **Harish's candidate folder — base report regenerated from scratch 2026-09-14, follow-ups still
  pending.** All 8 original files were deleted 2026-09-14 (md5-verified backup at
  `/tmp/harish-backup-2026-09-14`, not in the repo). `harish-report.md` + `harish-report.pdf` are
  now regenerated cleanly (`--tier deep`, `--longitude 79.4408 --city "Pallipattu, Tamil Nadu"`, no
  override; pillars 壬申/乙巳/辛亥/己丑 confirmed; PDF audited clean — 0 draft markers, 0 citation
  leaks) — and now that the bug above is fixed, the "What This Year Means for You" line shows
  Water natively with no hand-patching. **Not yet recreated:** `career.md`,
  `land-workshop-business.md`, `luck-timeline.md` (+ their PDFs). Mechanical mapping for the
  re-authoring: 용신=Water, 희신=Metal, 기신=Earth (controls Water), secondary avoid=Fire (controls
  Metal); branch-activation bonuses (합/충/해/파/삼형) are unaffected. This is real classical
  interpretive writing (the deleted originals were ~30KB each), not a mechanical regen — treat as a
  separate task.
- **#7 — regen for the 야자시 hour-stem fix, in progress:** Pawan's `pawan-report.md` + `career.md` +
  PDF are regenerated and promoted (hour 戊子→庚子). **Still pending:** Mahesh's client report +
  the `pawan_sruthi` compat pair PDF rebuild (the `.md` was hand-edited — hour cells 戊子→庚子,
  score re-measured 55/Mixed — but the PDF rebuild was user-rejected, so `.md`/`.pdf` are currently
  out of sync), plus the `yongsin.json`/`climate.json` fixture cascade noted in the plan.
- **`md_to_saju_compat_pdf.py` default `--output` path bug — FIXED 2026-09-14** (carried defect #8):
  `output_pdf.parent.mkdir(parents=True, exist_ok=True)` added before write. `--output` no longer
  needs to be passed explicitly, though doing so is still fine.

## Recent Changes to Remember

- **2026-09-26 (second deep engine audit, 11 of 22 fixed + 3 doctrinal decisions recorded, Suite →
  1094)** — A separate session ran a fresh from-scratch audit
  (`docs/audits/2026-09-26-deep-engine-audit.md`, N-1..N-22) against the same baseline the
  F-1..F-16 pass below started from (so it did not know about those fixes), merged via PR #4.
  Cross-referenced against F-1..F-16 first (N-1/N-9-partial/N-16-partial were already fixed),
  then fixed the rest of the audit's recommended order: **N-2** (절기 override compared solar time
  against civil term instants), **N-4** (current 대운 selected 1.3-2.4y early — 세수 vs.
  floored-elapsed-year mismatch; first fix attempt used the wrong unit conversion, caught by the
  Kim-Dae-jung validation fixture, not the unit test), **N-7** (web compat mislabeled a raw 억부
  pick as reader-confirmed), **N-8** (HTML injection into the Playwright PDF backend via
  `<script>`/`<iframe>` in a client name — `html: False` + JS-disabled Playwright context),
  **N-10** (compat's top red flags were alphabetical, not by severity), **N-11** ("this year" prose
  stated the Gregorian year instead of 사주 year — new `daeun.saju_year()` helper), **N-14** (web
  app overwrote curated client PDFs + blocked the event loop + leaked exceptions), **N-15**
  (partial: 子-hour boundary now disclosed), **N-16** (remaining lint debt + `ruff` added to CI),
  **N-17** (pinned `sajupy==0.2.0` + CSV hash test), **N-20** (duplicate pairwise 삼형), **N-22**
  (tests were overwriting `sruthi-report.pdf` on every run — `build-pdf.sh` gained `SAJU_OUT_DIR`).
  **Three items are marked doctrinal** (need a sourced decision, not a unilateral fix, per Ground
  Rule 1) — investigated each against the actual knowledge files (not the audit's word alone) and
  found genuine internal conflicts, then asked the user: **N-5** (yin DM strength — knowledge/06's
  12운성-stage cheat sheet vs. knowledge/09 Step 2's season/element criterion, which disagree for
  yin stems specifically) → decided: switch to season/element, not yet implemented. **N-6** (조후
  gate — knowledge/17's own cited source says the CHART must be extreme, not just the birth month,
  but no source gives a numeric threshold) → user asked for more research before deciding, open.
  **N-9's 양인격/건록격** month-branch question (자평진전's 월령-based grids vs. the current
  year/day/hour-only rule, uncitable independently) → decided: support both, labeled differently,
  not yet implemented. Full tracker with fix-log commit hashes:
  `docs/audits/2026-09-26-deep-engine-audit-verification.md`. **Still open, not started:** N-3
  (ephemeris-accurate 절기 table — the largest remaining item), N-12 (hidden-stem qi weights), N-13
  (IANA timezone/DST redesign), N-15's remainder (절기-proximity disclosure), N-18/N-19 (range-edge
  crashes, dead `month_season_score`). N-21 (landing-page source) is not fixable from this repo —
  the source simply is not here. Gates: suite **1094 passed / 9 xfailed / 0 failed**; validation
  `204 (PASS 200, INTERPRETATION 4, FAIL 0)`; `ruff check --select F src tools tests` clean and now
  in CI.
- **2026-09-26 (first deep engine audit, 16 of 16 fixed, F-1..F-16)** — Fixed all 16 findings from
  a from-scratch audit pasted directly into the session (not a repo file): F-1 (P0, EoT-only
  midnight day-pillar crossing never recomputed the day pillar), F-2 (천덕귀인 branch-target months
  could never fire), F-3 (`client_intake_app.py` crashed on import, undefined `TOOLS_DIR` — this is
  N-1 above), F-4 (already-parenthesized terms got double-annotated), F-5 (day-branch 육합+육파
  double-dipped), F-6 (compat basic tier leaked deep-tier verdict detail), F-7 (conflicting
  stem/branch daeun-favorability signal defaulted to "favorable" instead of "neutral" — also fixed
  the same bug duplicated in `prose_fillers.period_favorable_status`), F-8 (annual/monthly pillar
  out-of-range fallback ignored 입춀), F-9 (도화스쳐 flag never bucketed into red/yellow), F-10
  (intake forms defaulted UTC offset to India's 5.5), F-11 (`star_anchor` unvalidated by the direct
  API), F-12 (added a `hidden_stems` validation-lookup kind + a cross-timezone daeun fixture), F-13
  (essential tier's stale `$19` price), F-14 (`Chart.to_dict()` duplicate `reference_date` key),
  F-15 (3 duplicate `HANJA_GLOSSARY` keys), F-16 (F821 `Dict`/`List` in `daeun.py`/`sewoon.py`,
  scoped to only the two files the finding named — the wider repo-scale ruff UP006/UP045 sweep was
  judged disproportionate for a P3 item). Suite 1034 → 1068 passed / 9 xfailed. Committed and
  pushed as `3fc4d1f`.
- **2026-09-14 (full-engine architecture audit, documentation-only)** — Wrote
  `docs/audits/2026-09-14-full-architecture-audit.md`: a design/robustness review of every
  calculation subsystem (distinct from the validation campaign's classical-source-correctness
  check). Full reads of `engine.py`, `daeun.py`, `pillars.py`, `sewoon.py`, `lookup.py`,
  `strength.py`, `chart.py`; targeted reads of `patterns.py`/`stars.py`; compared against two
  external open-source BaZi engines (bazi-analyzer, viet-bazi-engine) found via web search, plus
  Chinese-language sourcing on 대운 starting-age remainder handling. **Key findings:** the engine's
  `starting_age()` floors the day-count remainder to whole years instead of the classical
  months-conversion (undocumented simplification, not a bug); `strength.py`'s `month_season_score`
  is computed but never consumed anywhere (dead field); 13 bare `except Exception:` blocks in the
  presentation layer (`prose_fillers.py` ×6, `compat.py` ×3, `premium_report.py` ×3) swallow errors
  with no logging — the top robustness risk found, since a real bug there would silently degrade
  to a plausible-looking sentence in a paid PDF rather than crash a test; the raw-vs-resolved
  favorable-element two-channel bug (fixed 3× independently this project) is a design smell, not
  three coincidences — recommends renaming the raw field to self-flag direct reads. No code
  changes made; see the audit's §5 priority list for the follow-up work.
- **2026-09-14 (client-visible item 1 fixed + Harish base report regenerated, Suite 883 → 885)** —
  Fixed the last surface of the raw-vs-resolved favorable-element bug class:
  `premium_report.py::_right_now_callout()` and `ctx_favorable_phrase()` (called from
  `_year_one_liner`) now accept an `override` param and read `favorable_element(chart, override)`
  instead of `strength_assessment["candidate_favorable"]`; both call sites thread
  `ctx.favorable_override`. Retired the 2 `xfail(strict=False)` markers in
  `tests/validation/test_val_climate.py` that pinned the bug (they XPASSed). Regenerated
  `candidates_horoscope/reports/harish/harish-report.md` + `.pdf` from scratch (his folder had been
  cleared 2026-09-14 for a from-scratch rebuild) — the "What This Year Means for You" line now
  shows Water natively with no hand patch. PDF audited clean (0 draft markers, 0 citation leaks).
  Harish's `career.md`/`land-workshop-business.md`/`luck-timeline.md` (+ PDFs) are still not
  recreated — flagged as a separate re-authoring task. Gates: suite **885 passed / 10 xfailed / 0
  failed**; validation CLI unchanged `194 (PASS 189, INTERPRETATION 5, FAIL 0)`.
- **2026-09-13 → 2026-09-14 (Engine Validation Campaign — COMPLETE, Suite 649 → 883)** — Independent
  validation of the whole engine against classical sources, run as spec + Plans 1–6
  (`docs/superpowers/specs/2026-09-13-engine-validation-campaign-design.md`,
  `docs/superpowers/plans/2026-09-13-engine-validation-plan-{1-foundation-pillars,2-daeun-sewoon,
  3-lookups,4-yongsin,5-climate,6-compat-career}.md` — all six now **deleted**, superseded by this
  entry + `docs/research/2026-09-validation-*.md` + the rendered report). Built a permanent
  validation harness: `src/saju_engine/validation.py` + `tools/run_validation.py` (`python3
  tools/run_validation.py` → renders `docs/audits/2026-09-engine-validation-report.md`, **never
  hand-edit it**) + `tests/validation/` fixtures. **Certified 194 checks / 189 PASS / 5
  INTERPRETATION / 0 FAIL across 8 subsystems**: W1 pillars 17, W2 대운·세운 19, W3
  십신/12운성/납음/공망 56, W4 용신 13, W5 조후 30, W6 compat+career 59. Each workstream is backed by
  a research doc citing ≥2 independent Korean sources per rule family
  (`docs/research/2026-09-validation-{yongsin,climate,compat-career}.md`). Validation-only by
  design — defects found were **pinned as tests asserting the current wrong behaviour**, not fixed
  in-campaign (sole exception: the user-ordered 야자시 hour-stem fix in `pillars.py`, part of W1).
  Found **13 loose ends**: 3 client-visible (`premium_report.py` + `report_data.py` reading the raw
  un-resolved 용신 field instead of the display value; 육합 dead code in `compat.py`) and 10 others
  (C9 삼형 chain position, C8 nayin order-dependence, KB12 career tier-pool contradiction, Harish's
  longitude inconsistency, a compat PDF output-path bug, a 辰/戌 climate-model divergence, an
  unsourced climate wording claim, a dead test registry, and two Pawan/Mahesh client reports needing
  regen for the 야자시 fix).
- **2026-09-14 (post-campaign fix wave — user-directed on items 4–13, Suite → 883/12 xfailed)** —
  Nine of the thirteen loose ends are now fixed, each independently re-measured, not transcribed:
  **#5** nayin order-dependence (`compat.py::_canonical_nayin_pair`, male-first canonicalization);
  **#6** career tier pool re-keyed from the Day Master's element family onto the resolved
  용신+희신 families per `knowledge/12-career-and-vocation.md:130-152` (new `_resolved_favorable()`
  helper in `report_data.py`) — **this also fixed client-visible item 2** (career sections were
  reading the raw, un-resolved favorable element); **#8** `md_to_saju_compat_pdf.py --output` path
  bug (missing `mkdir(parents=True)`); **#9** Harish's longitude reconciled to `79.42` at 3 data
  sites (pillar-neutral); **#11** the 辰/戌 climate-model divergence resolved as a **documentation +
  scope** fix (not a model change — see the reusable precedent in Claude's own memory,
  `saju-open-defects-triage.md`); **#12** an unsourced dry/damp climate claim removed from
  `knowledge/17-climate-method.md`; **#13** the dead `_CHECKERS` test registry pruned; and **#4 +
  client-visible item 3 together**, landed as **"(A) + C-none"** on the user's approval — the 육합
  (six-combination) dead-code arity fix in `compat.py::_branch_pair_lookup` (the table is 3-tuples,
  the lookup was testing 2-tuple membership, so 육합 never fired at 4 call sites including the
  spouse-palace bonus), plus documenting the 삼형 branch-punishment chain position as an unsourced
  scope limit rather than reordering it (C9 stays intentionally pinned — branch 삼형 has zero
  citations anywhere in `knowledge/`). Net measured effect: one fixture moved,
  `compat-mahesh-vp` 64/Mixed → 68/Strong; the two published compat anchors (70/Strong, 74/Strong)
  did not move. **Still open:** client-visible **item 1** (`premium_report.py`'s "What This Year
  Means for You" callout, still reading the raw favorable element — see "Active Wishes" below);
  **#7** (regenerating the Pawan/Mahesh/Harish client deliverables affected by the 야자시 fix and
  the 조후 fix — Pawan done, Mahesh and the fixture cascade pending, Harish's base report
  regenerated but its three follow-up files not yet re-authored); and two **product decisions**
  surfaced but not decided — #10 (whether 조후 should outrank 억부 more broadly) and whether
  `climate.py` should expand from its conservative 3-band model to the full 寒暖燥濕 four-way
  궁통보감 reading. Final verified gates: suite **883 passed / 12 xfailed / 0 failed**; CLI
  `194 (PASS 189, INTERPRETATION 5, FAIL 0)` exit 0.
- **2026-09-13 (조후 climate-balance engine fix — plan complete, Suite 627 → 649)** — Triggered by
  the user noticing Harish's 용신 (Fire, from the old "least-represented element" balanced-verdict
  fallback) disagreed with an independent reading (Water). Investigation confirmed the four-pillar
  engine was already correct (verified against `tests/test_textbook_cases.py`'s 9 independently
  published charts); the real gap was that 용신 determination only implemented 抑扶
  (strength-balance) — missing 조후 (climate-balance, 궁통보감/적천수), both cited in CLAUDE.md's
  persona but never wired into `knowledge/09-interpretation-method.md` Step 3 or the code. Full
  design in `docs/superpowers/specs/2026-09-13-climate-favorable-element-design.md`, plan in
  `docs/superpowers/plans/2026-09-13-climate-favorable-element.md`, executed via
  subagent-driven-development (adapted for no-git: no commits/worktrees, reviewers read files
  directly — ledger `.superpowers/sdd/progress.md`). **What shipped:**
  - New `src/saju_engine/climate.py` (`assess_climate(month_branch)`): a conservative, general
    season-based model — 巳午未 (hot) → Water, 亥子丑 (cold) → Fire, everything else → no override.
    Deliberately NOT a fabricated per-stem-per-month 궁통보감 table (no source text was available).
  - `src/saju_engine/yongsin.py` rewritten to merge climate into `favorable_element()` — see the new
    "Decisions to Remember" #9 above for the exact resolution order.
  - **Mid-implementation discovery (real bug, not in the original plan):** `compat.py` had 4 scoring
    functions reading `strength_assessment["candidate_favorable"]` directly, and its reader-override
    mechanism mutated that same field — both silently broken by the climate merge for any
    balanced+hot/cold chart (Mahesh, this project's own canonical demo compat partner, is one).
    User decided to fix in scope: `compat.py` now routes through `favorable_element()`, and its
    override sets a new `reader_override_favorable` field that `yongsin.py` checks with the same
    outright-wins precedence as an explicit override.
  - `premium_report.py`/`compat_report.py`'s "Supporting Element" display fixed to read the resolved
    `.supporting` value (was reading the stale raw field, would have silently gone out of sync).
  - New `knowledge/17-climate-method.md` + `knowledge/09-interpretation-method.md` Step 3 updated.
  - **Content regenerated:** `harish-report.md`+PDF (Fire/Wood → Water/Metal, fully internally
    consistent), Vishnu Priya's reports (note text only, element already agreed), the Pawan×Sruthi
    compat report (picked up an unrelated latent display-bug fix in the same pass). **Confirmed
    correctly left untouched:** Sruthi/Pawan/Gurumoorthy (reader-argued `--favorable-override`,
    documented `(reader-argued)` in `candidates_horoscope/README.md`, bypasses climate by design),
    Mahesh (fully hand-crafted Weak-DM analysis overriding the engine's own balanced auto-verdict),
    RM (strong verdict + temperate month → climate never even consulted, byte-identical). This
    4-of-6-unaffected finding corrected an earlier over-broad assumption in the plan — always check
    the actual delivered file for a documented override before assuming the raw engine table
    applies.
  - **harish_vinothini compat pair:** its Harish-side favorable element was a stale "Earth" (matched
    neither the old nor new engine value, no documented override anywhere) — corrected to Water.
    Vinothini's real birth data isn't recoverable from the repo, so her side was reconstructed
    pillars-only from her own already-published numbers (verified against a published cross-supply
    percentage before use) to recompute just the 2 favorable-element-dependent sub-systems; composite
    score unchanged. User confirmed (2026-09-13) this reconstruction stands as final — no further
    action pending on this pair.
  - **Follow-up fix applied same day (user-approved):** the pawan_sruthi regen exposed a real
    contradiction — its corrected Supporting Element display (Pawan→Metal, Sruthi→Fire, the
    classically-correct generator) disagreed with Pawan's and Sruthi's own *individual* reports
    (which duplicated favorable==supporting: Water/Water, Earth/Earth). Fixed the individual reports
    to match (5 lines each: Quick Reference, Wealth Pattern, Investment Style Cue, Relocation table
    + orientation line), rebuilt both PDFs.
  - **3 items explicitly flagged, not fixed** (see "Active Wishes / Open Items" above for full
    detail): `premium_report.py`'s "What This Year Means" line reads the wrong raw field;
    Harish's `career.md`/`land-workshop-business.md`/`luck-timeline.md` still argue stale Fire/Wood;
    `md_to_saju_compat_pdf.py`'s default `--output` path bug (workaround: pass `--output` explicitly).
  - **Same-day follow-on:** created a new compat pair, `harish_manvitha` (both tiers, both PDFs;
    added to `candidates_horoscope/README.md`'s index) — Harish × Manvitha (1996-12-03, 21:15,
    Kadapa, Andhra Pradesh), composite 70/100 "Strong". Manvitha's chart (甲, strong, 亥월) is a
    clean fresh validation of the new engine with no overrides on either side.
- **2026-09-08 (candidate regen, starting Harish — DONE)** — Re-validating each candidate's
  pillars against external sources and regenerating reports. **Harish complete:** pillars
  壬申/乙巳/辛亥/己丑 validated (year/month/day confirmed via web + the engine's verified 노무현
  anchor; hour 己丑 correct for 03:10 but solar time 02:57 is ~3–5 min from the 丑→寅 boundary —
  lower-confidence). Longitude corrected 79.32→**79.45°E** (Wikipedia 13.33°N,79.45°E); pillars
  unchanged. Regenerated: `harish-report.md`+PDF (engine deep + plain-language layer); `career.md`
  and `land-workshop-business.md` **re-grounded in `knowledge/12-16`** — the old "not in the
  knowledge base / [UNCERTAIN — extrapolation]" disclaimers on industries and directions replaced
  with real citations + each file's modern-convention caveat. All 4 PDFs clean (no leaks / drafts
  / residual CJK). The regen surfaced & fixed clusters of bugs in `plain_glossary.gloss_first_use`
  (TOC corruption, noun-phrase splits, "Monthly Luck" ⊂ "Monthly Lucky"), `strip_source_citations`
  (line-wrapped `*(see …)*`, short `knowledge/13` form, orphan `§Section`), and the PDF translation
  maps (+20 compound terms). `collect_used_terms` now filters like the glossers. Suite **626**.
  RM demos rebuilt. **Sruthi / Pawan / Gurumoorthy also done** (2026-09-08): pillars
  re-validated (Sruthi 癸酉/甲子/丙寅/己丑, Pawan 辛未/丁酉/丙午/戊子, Gurumoorthy 甲辰/辛未/己巳/戊辰
  — all confirmed via the 노무현 anchor + engine solar-term checks; no hour knife-edge). Base
  reports regenerated as engine `--tier deep` via a new **`--favorable-override`** CLI flag set
  to each reader-argued 용신 (Earth / Water / Metal); hand-written bases kept as
  `{name}-report-legacy.md`. Each `career.md` re-grounded in `knowledge/12-16`. Fixed
  `combine_candidate_report.PROJECT_ROOT` (broke after the src/ migration). Two PDF-render fixes
  landed too: `premium_report` practical-guidance lists now emit `-` bullets (were rendering
  `1. 1. 1.`), and the reportlab inline renderer now handles `_underscore italic_`. Suite **627**.
- **2026-09-08 (Better Reports — plan complete)** — Executed
  `docs/superpowers/plans/2026-09-07-better-reports.md` Tasks 1–16 inline. **Track B:**
  `knowledge/12`–`16` (career / wealth / directions / health / date-selection) now exist,
  are Hanja-compliant, wired into the method / glossary / `CLAUDE.md` / `.claude/commands/saju.md`
  / openwiki, and back the engine's interpretive tables (`report_data.py` `# source:` comments +
  `tests/test_knowledge_grounding.py`). **Track A:** new `src/saju_engine/plain_glossary.py`
  adds a plain-language layer — inline first-use glosses (`Direct Wealth (正財) — steady, earned
  income …`), `> **In plain words:**` section callouts (`prose_fillers.plain_words_*` +
  `prose_scaffold.generate_plain_words`), and a tier-scaled `## What the Terms Mean` appendix
  after the Closing Note — wired into `premium_report.py`, `skeleton.py`, `compat_report.py`.
  `strip_source_citations` eats the leading space; `combine_candidate_report.py` keeps the
  glossary last. RM demo set regenerated leak-free. Suite 594 → **625**; PDF backends + compat
  renderer + landing `npm run build` green. Resume ledger: `.superpowers/sdd/progress.md`.
- **2026-09-07 (landing redesign — shipped)** — Full `apps/landing-page` restructure:
  ~15 sections → ~9, proof-first arc, new Saju visual system (`src/components/viz/`), premium-editorial
  aesthetic, elemental palette tokens, `四柱` watermark. Deletes `WhatIsSaju` / `WhatYouReceive` /
  `TrustClarity` / `ImportantDetails` / `ComparisonTable`. Spec + plan in `docs/superpowers/`;
  tracker `improvements_issues.md` §5a (LP13).
- **2026-09-07 (repo housekeeping)** — Deleted cruft (`!`, `.coverage`, `.pytest_cache/`,
  `.playwright-mcp/`, stray root PNGs, `rm-deep.md` dup, 12 intake test files). Archived the 3
  audit reports → `docs/audits/` (+ index README). Deleted 4 completed plan docs (`docs/PLAN.md`,
  `docs/plans/*`, `.claude/plan.md`). `misc/market_research/` kept with a SUPERSEDED banner.
  `.gitignore` extended (node_modules, .next, intake/, .remember/, settings.local.json).
  `.claude/settings.local.json` trimmed from ~250 stale allowlist entries to a compact set.
  `docs/issues_bugs.md` paths `tools/ → src/`. New file map in README + `docs/MEMORY.md`.
- **2026-09-07** — Go-to-market pivot to English-speaking-global / USD (see `improvements_issues.md`,
  `docs/market-research-2026-09.md`). Fixed 3 client-facing engine defects: G1 reviewer-note leak
  (`premium_report._reviewer_note`, `strip_source_citations`), G2 per-pillar template grammar, G3
  용신 single source of truth (`src/saju_engine/yongsin.py` — `favorable_element()` +
  `FavorableElement` provenance; `generate_premium_report`/`generate_compat_report` consume it, with
  `favorable_override` / `favorable_element_a`/`_b` for reader-argued values). Engine + docs + all
  candidate/landing prices ₹→USD. Landing page (`apps/landing-page`) repositioned; testimonials
  flagged illustrative. Suite 568 → 590; landing build + 107 vitest green. RM + pawan_sruthi demo
  reports/PDFs regenerated leak-free.
- **2026-06-28** — Added Codex support: `docs/codex/instructions.md` plus `saju-reading` and `saju-client-order` skills in `~/.codex/skills/`.
- **2026-06-28** — Marriage-compatibility engine (`compat.py`), 16-section report generator (`compat_report.py`), Nayin lookup (`nayin.py`), two-chart intake form + server, standalone compat PDF renderer, and `knowledge/11-gunghap.md` reference completed.
- **2026-06-28** — Repo cleanup: deleted old `docs/`, `ENGINE_SPEC.md`, `ENGINE_RESEARCH.md`. Documentation surface then lived in `README.md`, `CLAUDE.md`, `tasks.md`, `candidates_horoscope/README.md`, and this `MEMORY.md`.
- **2026-07-06** — Repo-root reorganization: created `docs/` and consolidated project memory, issue tracker, engine audit, plan artifacts, OpenWiki stubs, and Codex instructions there. Deleted stray files/dirs (`:`, `=0.2.0`, `=4.1`, `EOF`, `.coverage`, `.pytest_cache/`) and added coverage/cache artifacts to `.gitignore`.
- **2026-06-27** — Added landing-page tiers (`sample`/`essential`/`deep`) and `/saju-client` slash command.
- **2026-06-22** — Self-service FastAPI calculator, tiered intake form, combined-report combiner, colored Element Balance rendering, citation stripping in PDFs.
- **2026-06-21** — Daily-luck overlay, prose scaffold, premium report generator, major-luck activation overlay, grid/pattern candidates, HTML/Playwright PDF backend.

## Codex-Specific Notes

- Project-level Codex instructions live in `docs/codex/instructions.md`.
- Two user-level skills are installed in `~/.codex/skills/` for auto-discovery:
  - `saju-reading` — single-chart reading workflow.
  - `saju-client-order` — client order fulfillment workflow.
- The skills reference the same `docs/MEMORY.md`, `CLAUDE.md`, and `knowledge/` files that the Claude slash commands use.

## How to Use This Memory

At the start of a new session working on this repo, read:
1. `MEMORY.md` (this file) for state, conventions, and quick commands.
2. `CLAUDE.md` for persona, ground rules, and interpretive workflow.
3. `tasks.md` for the prioritized work list and change log.
