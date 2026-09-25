# Candidates Horoscope — Reports

This directory holds individual Saju readings for each candidate. Each candidate has **their own subfolder** under `reports/`. The base natal reading lives in that subfolder, and any follow-up queries or topic-specific files also live there.

## Folder Structure

```
candidates_horoscope/
├── README.md                 # this file (pattern + index)
└── reports/
    ├── cross-candidate-business-analysis.{md,pdf}  # cross-candidate synthesis (sibling to per-candidate folders); regen 2026-06-03
    ├── sruthi/               # one subfolder per candidate
    │   ├── sruthi-report.{md,pdf}  # base natal reading
    │   ├── sruthi-combined.{md,pdf}  # optional: base + all topic files concatenated for the consolidated PDF
    │   ├── career.md         # follow-up queries / suggestions
    │   ├── relationships.md  # another follow-up
    │   └── 2027-outlook.md   # year-specific query
    └── {next-candidate}/
        └── {name}-report.{md,pdf}
```

## File Conventions

### Base natal reading
- Path: `reports/{name}/{name}-report.md`
- Always present once per candidate.
- Follows the premium 9-section scaffold (cover / chart-at-a-glance with Element Balance + Quick Reference + "What This Year Means for You", Day Master Portrait, Career & Wealth, Relationships, Health & Vitality, Timing, Practical Guidance Summary with Lucky Attributes reference card, Closing Note). Derived from `knowledge/10-output-template.md`.

### Optional consolidated file
- Path: `reports/{name}/{name}-combined.{md,pdf}` (and `{name}-combined-html.pdf` for the Playwright backend)
- The base reading merged with all topic files in this folder, used for shipping a single multi-section PDF to the client. Generated with `src/saju_html/combine_candidate_report.py {name}`, which moves the Closing Note to the final page, dedupes the base career table when a `career.md` deep-dive exists, and strips Sources sections from follow-ups. PDFs are built with `./tools/build-pdf.sh --combined {name} ...`; add `--html` for the richer Playwright backend.

### Follow-up queries / topic files
- Path: `reports/{name}/{topic}.md` (kebab-case, descriptive name)
- Naming should reflect the **type of query**:
  - `career.md` — career, business, domains, do's & don'ts
  - `relationships.md` — marriage, compatibility, partner analysis
  - `health.md` — health, wellness, prevention
  - `2027-outlook.md` or `2026-yearly.md` — year-specific
  - `current-daeun.md` — current major luck period deep-dive
  - `parenting.md` — children / parenting analysis
  - `finance.md` — money, investments, financial cycles
  - `relocation.md` — geography, environment
  - `compatibility-with-john.md` — paired compatibility (note: the standalone 두 분 궁합 product uses a different convention — see "Compatibility (궁합) readings" below)

### Merge rule for overlapping queries
- If a follow-up query **overlaps an existing file's topic**, **append to that file** rather than creating a new one. Use clear dated subheadings (e.g., `## 2026-06-02 — business domains deep-dive`) within the file to keep history traceable.
- Examples:
  - "What about marketing as a domain?" → goes into `career.md` (or the most-specific existing file).
  - "Should I do business now or wait?" → if no `business-timing.md` exists, create it; if `career.md` already covers general career, append with a dated heading.
  - "Tell me about my marriage timing in 2027" → if `relationships.md` exists, append with a dated heading; otherwise create it.

## Naming Convention (folder + base file)
- Use the candidate's full name (lowercase, hyphenated) for stability.
- Examples:
  - `reports/sruthi/sruthi-report.md`
  - `reports/john-doe/john-doe-report.md`
  - `reports/candidate-001/candidate-001-report.md`

## Client Intake Form

A self-contained HTML intake form lives at `tools/client_intake_form.html`. It collects name, DOB, birth time, birth location, email, gender, marriage/relationship status, and tier selection. The "main concern" textarea is enabled only when **The Deep Destiny Report** is selected.

Run the tiny server to collect submissions as JSON:

```bash
python3 tools/client_intake_server.py 8080
# open http://localhost:8080
```

Submissions are saved to `candidates_horoscope/intake/YYYYMMDD-HHMMSS-{name-slug}.json`.

## Self-Service Calculator

`tools/client_intake_app.py` is a FastAPI app that serves the same form and immediately returns a tiered PDF. It computes the chart with `src/saju_engine/`, generates the premium markdown for the selected tier, and renders it via the reportlab backend.

```bash
pip install --user --break-system-packages -e ".[web]"
python3 tools/client_intake_app.py 8080
# open http://localhost:8080
```

The generated PDF and engine markdown are saved alongside the intake JSON in `candidates_horoscope/intake/`. The PDF is an engine draft for paid tiers; review before final delivery or restrict self-service to **The Hook**.

## Workflow for a New Candidate

1. **Gather data** via the intake form or manually: full name, Gregorian DOB, exact birth time, birthplace (lat/long for time-zone), gender, calendar system, and marriage/relationship status.
2. **Ask for the tier** before generating the report. Landing-page options:
   - **The Hook** (complimentary, 1 page) — a free sample with four pillars, element balance, and lucky cues
   - **The Essential Report** ($9 intro → $19, 6–7 pages) — natal chart + career arc + relationships + health + major luck + annual windows + lucky-element guide
   - **The Deep Destiny Report** ($55, 10–12 pages) — full natal reading + career deep-dive + relationship deep-dive + health deep-dive + year-by-year timing + business-launch guidance + auspicious dates + lucky-element guide
   
   Engine tier flags are `sample`, `essential`, `deep`. Legacy flags `spark/reading/fullmap` still work for older templates.
3. **Create folder**: `candidates_horoscope/reports/{name}/`
4. **Compute the four pillars** using the procedure in `knowledge/09-interpretation-method.md` Step 0, cross-verifying with a trusted online 만세력 calculator if needed. Or generate via the engine: `python -m saju_engine --format premium --tier {sample,essential,deep} --output-file {name}/{name}-report.md ...`
5. **Walk the nine-step procedure** in `knowledge/09-interpretation-method.md`.
6. **Save base reading** as `{name}/{name}-report.md` using `knowledge/10-output-template.md`.
7. **Add a one-line entry** to the **Index** table at the bottom of this file.

## Workflow for a Follow-up Query

1. **Read the base reading** for the candidate first to ground the answer.
2. **Check existing files** in `reports/{name}/` — does an `career.md` / `relationships.md` / etc. already exist that fits this query?
3. **If yes** → append to that file with a dated subheading (`## YYYY-MM-DD — short query summary`).
4. **If no** → create a new file `reports/{name}/{topic}.md` with a short heading, the query, and the answer.

## Index

> **Maintenance note (2026-07-01):** Every item in `docs/issues_bugs.md` is now closed. Legacy base reports (Sruthi, Pawan, Gurumoorthy) are tagged with an explicit *legacy-format* banner; they remain accurate but do not yet follow the premium 9-section scaffold used for Vishnu Priya and later candidates. Inline citations were standardized to the `*(see knowledge/...)*` format across all base reports.

| Name | Birth Date | Day Master | Favorable Element | Base Report |
|---|---|---|---|---|
| Sruthi | 1993-12-11, 02:45 IST, Pallipattu (Tiruvallur), Tamil Nadu — 13.33°N, 79.45°E | 丙 병 (Yang Fire) | Earth (土) *(reader-argued)* | [sruthi/sruthi-report.md](reports/sruthi/sruthi-report.md) — **regenerated 2026-09-08** as an engine `--tier deep` report with `--favorable-override Earth` (plain-language layer); pillars **re-validated** (癸酉/甲子/丙寅/己丑 — all confirmed; hour 己丑 stable). The hand-written 궁통보감 base is kept as [sruthi-report-legacy.md](reports/sruthi/sruthi-report-legacy.md). + [career.md](reports/sruthi/career.md) — **re-grounded** in `knowledge/12-16` (10-domain table + business fit). **2026-09-19:** the shipped base report was found stale — it predated the 2026-09-14 raw-vs-resolved favorable-element fix entirely, so it still said "lean into Metal" and ranked Fire-native domains (Leadership/Media/Marketing) as Best Fit instead of her actual Earth-favorable ones (Real Estate/Hospitality/Finance/Project Management). Regenerated from scratch; `career.md` was already correct (hand-authored separately) and needed no change. |
| Pawan | 1991-10-03, 11:45 PM IST, Vellore, Tamil Nadu — ~13.02°N, 79.19°E | 丙 병 (Yang Fire) | Water (水) *(reader-argued)* | [pawan/pawan-report.md](reports/pawan/pawan-report.md) — **regenerated 2026-09-08** as engine `--tier deep` with `--favorable-override Water`; pillars **re-validated** (辛未/丁酉/丙午/戊子 — all confirmed; 야자시 hour 戊子). Legacy base: [pawan-report-legacy.md](reports/pawan/pawan-report-legacy.md). + [career.md](reports/pawan/career.md) — **re-grounded** in `knowledge/12-16`. **2026-09-19:** regenerated again — the shipped report's "What This Year Means for You" line still said Wood instead of his actual Water override, and the Lifetime Decade Roadmap used the pre-fix `daeun_overlay.py` favorability logic. `career.md` was already correct and needed no change. |
| Harish | 1992-06-04, 03:10 AM IST, Pallipattu (Tiruvallur), Tamil Nadu — 13.33°N, 79.45°E | 辛 신 (Yin Metal) | Water (水) *(engine heuristic, 조후 climate-check applied)* | [harish/harish-report.md](reports/harish/harish-report.md) + [career.md](reports/harish/career.md) — PDFs: [base](reports/harish/harish-report.pdf) · [combined](reports/harish/harish-combined.pdf) · [career](reports/harish/career.pdf). Deep Destiny (engine `--tier deep`, `--longitude 79.4408 --city "Pallipattu, Tamil Nadu"`, no override). **2026-09-25:** entire candidate folder deleted and rebuilt from scratch again per user request (same birth data; same-chart determinism confirmed — identical pillars/ten-god counts to the 2026-09-19 build). Pillars: 壬申/乙巳/辛亥/己丑, Balanced DM, 용신 Water/희신 Metal, 정관격. The base report now carries a new "⚠ Hour-boundary note" (added by this session's I7 engine fix, 2026-09-20): the corrected solar time is only ~1 minute from the 丑/寅 boundary, flagging **庚寅** as a plausible alternate hour pillar alongside the primary **己丑** — `career.md`'s Ten-God Profile now discloses how that would shift the Resource/Wealth/Authority balance. The Lifetime Decade Roadmap's favorable-lean labels for the 20s/30s/40s decades now read **favorable** (were **neutral** in the 2026-09-19 build) — almost certainly the effect of engine fixes landed in the intervening commits; `career.md`'s Career Transition Timing section was rewritten to match. `career.md` rewritten fresh at full standalone deep-dive depth (ranked career domains, concrete job roles, business-domain fit, investment/wealth behavior, decade-by-decade + annual career-transition timing) — content re-derived from the regenerated chart, not copied from the prior version, though conclusions are materially the same since the underlying chart is identical. Also fixed a latent citation-stripping cosmetic bug found while combining (`*Sources: ...*` inline-italic footers left literal `Sources:,,,,,.` comma-litter in the client PDF after `knowledge/` paths were stripped — Mahesh's `career.md` uses the same inline format and likely has the same defect, not yet checked); worked around for Harish by switching to the `## Sources & Limits` heading convention used by most other candidates, which strips cleanly — the underlying `strip_source_citations` regex itself was not patched. **2026-09-25 (same day, external audit against the just-regenerated `harish-combined.md`):** an independent reviewer recalculated the report by hand and found 4 real defects, all confirmed and fixed: (1) **engine bug** — `daeun.py::starting_age_days` truncated the days-to-절기 count to a whole day *before* the ÷3 conversion, understating Harish's true 대운수 offset (~1.68 days) as "~0.3 years / 1 month" instead of the correct "~0.6 years / 7 months"; (2) **engine bug** — `premium_report.py::_daeun_starting_age_note`'s months conversion divided by 3 an extra time (`days*4/3` instead of `days*4`, since 3 days = 1 year = 12 months ⇒ 1 day = 4 months); both fixed with regression tests (`tests/test_daeun.py`, `tests/test_premium_report.py`), base report regenerated with the corrected "~0.6 (~1.7 days ... roughly 7 months)" text. Both bugs affect every candidate's report, not just Harish's — no other candidate reports were regenerated this pass. (3) **`career.md` content bug** — the Ten-God Profile table undercounted 식상 (Output) at 3 by missing the hidden 壬 in 申's middle position; the true count is a three-way tie at 4 among 인성/식상/비겁 (cross-checked against the engine's own `_grouped_dominant_classes`), not a clean "Resource-dominant" reading — table and prose corrected. (4) **`career.md` content bug** — the storehouse-check footnote wrongly claimed 정재 becomes "visible directly in the hour stem" under the alternate hour 庚寅; the hour stem 庚 is actually 겁재 (Companion), and 정재 (甲) remains hidden, just promoted from 亥's middle position to 寅's main position — corrected. The reviewer's separately-flagged "2030–2033, ages roughly 36–39" text (from the *original*, pre-audit `career.md`) was also independently caught and fixed in this pass to the correct 37–41 before the audit report was seen. Reviewed-but-not-changed: the reviewer's element-percentage recalculation confirmed the engine's own weighting is applied correctly (no bug); the health-section "Water as both favorable and excess" framing already carries an explicit caveat resolving that tension; the MP3 "included" language is pre-existing shared boilerplate describing a real manual fulfillment step (per this file's own Premium Client Report Pipeline docs), not a per-report defect. |
| Gurumoorthy | 1964-07-19, 08:30 AM IST, Tirupati AP | 己 기 (Yin Earth) | Metal (金) *(reader-argued)* | [gurumoorthy/gurumoorthy-report.md](reports/gurumoorthy/gurumoorthy-report.md) — **regenerated 2026-09-08** as engine `--tier deep` with `--favorable-override Metal`; pillars **re-validated** (甲辰/辛未/己巳/戊辰 — all confirmed). Legacy base: [gurumoorthy-report-legacy.md](reports/gurumoorthy/gurumoorthy-report-legacy.md). + [career.md](reports/gurumoorthy/career.md) — **re-grounded** in `knowledge/12-16` + [gurumoorthy-combined.md](reports/gurumoorthy/gurumoorthy-combined.md) ([PDF](reports/gurumoorthy/gurumoorthy-combined.pdf)) |
| Mahesh | 1995-01-19, 11:50 PM IST, Ambur TN | 庚 경 (Yang Metal) | Fire (火) *(조후 climate-check; corrected 2026-09-19, was Earth)* | [mahesh/mahesh-report.md](reports/mahesh/mahesh-report.md) + [career.md](reports/mahesh/career.md) + [relationships.md](reports/mahesh/relationships.md) — PDFs: [base](reports/mahesh/mahesh-report.pdf) · [combined](reports/mahesh/mahesh-combined.pdf) · [combined-html](reports/mahesh/mahesh-combined-html.pdf). **2026-09-19:** full regen — the hour pillar had never been updated after the 2026-09-13 야자시 hour-stem engine fix (was 丙子, corrected to 戊子). This flipped Day Master strength from 신약 to Balanced and 용신 from Earth to Fire (희신 Metal→Wood), and removed a spurious 정편관혼잡 pattern (only one clean 정관 remains). Base report, `career.md`, and `relationships.md` fully re-derived; the old versions had been recommending Earth/Metal partners and industries and flagging 2026 as an avoid-marriage year when it is now favorable. **Regenerated again same day** after the `daeun_overlay.py` favorable-status fix (see engine-level note below) corrected his Lifetime Decade Roadmap's favorable-decade labels. |
| Vishnu Priya | 2001-06-07, 04:45 PM IST, Mysore KA | 辛 신 (Yin Metal) | Water (水) | Base: [vishnu-priya-report.md](reports/vishnu-priya/vishnu-priya-report.md) · Tiered: [sample.md](reports/vishnu-priya/vishnu-priya-sample.md) / [essential.md](reports/vishnu-priya/vishnu-priya-essential.md) / [deep.md](reports/vishnu-priya/vishnu-priya-deep.md) — Follow-ups: [career.md](reports/vishnu-priya/career.md) + [relationships.md](reports/vishnu-priya/relationships.md) — PDFs: [base](reports/vishnu-priya/vishnu-priya-report.pdf) · [sample](reports/vishnu-priya/vishnu-priya-sample.pdf) · [essential](reports/vishnu-priya/vishnu-priya-essential.pdf) · [deep](reports/vishnu-priya/vishnu-priya-deep.pdf) · [combined](reports/vishnu-priya/vishnu-priya-combined.pdf) · [combined-html](reports/vishnu-priya/vishnu-priya-combined-html.pdf) |
| RM (Kim Nam-joon) | 1994-09-12, 13:28 KST, Seoul | 辛 신 (Yin Metal) | Water (水) | Demo reports for landing page. Tiered: [sample.md](reports/rm/rm-sample.md) / [essential.md](reports/rm/rm-essential.md) / [deep.md](reports/rm/rm-report.md) — PDFs: [sample](reports/rm/rm-sample-report.pdf) · [essential](reports/rm/rm-essential-report.pdf) · [deep](reports/rm/rm-report.pdf) · Landing-page demos: [sample](../../apps/landing-page/public/demo-rm-sample.pdf) / [essential](../../apps/landing-page/public/demo-rm-essential.pdf) / [deep](../../apps/landing-page/public/demo-rm-deep.pdf) |

## Compatibility (궁합) readings

Two-chart readings live under `candidates_horoscope/marriage_compatibility/` in **one subfolder per pair**, named with the partners' actual slugified names: `{name_a_slug}_{name_b_slug}/`. Inside that subfolder, the files use the same slug as the folder name. (Partner A first, Partner B second; for heterosexual pairs Partner A is the male). Each pair has two tiers:

- **Basic** — `{name_a_slug}_{name_b_slug}/{name_a_slug}_{name_b_slug}_compatibility.{md,pdf}` (~4-page compact snapshot: cover, glance, verdict, 4 key sub-systems, practical guidance, closing note)
- **Deep** — `{name_a_slug}_{name_b_slug}/{name_a_slug}_{name_b_slug}_compatibility_deep.{md,pdf}` (full 11-sub-system report + individual element balance, Day Master snapshots, major-luck timelines, and a year-by-year couple timing overlay, ~9–10 pages)

| Pair | Basic | Deep | Score | Band |
|---|---|---|---|---|
| Pawan × Sruthi (demo) | [MD](marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility.md) · [PDF](marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility.pdf) | [MD](marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility_deep.md) · [PDF](marriage_compatibility/pawan_sruthi/pawan_sruthi_compatibility_deep.pdf) | 55/100 | Mixed |
| Harish × Manvitha | [MD](marriage_compatibility/harish_manvitha/harish_manvitha_compatibility.md) · [PDF](marriage_compatibility/harish_manvitha/harish_manvitha_compatibility.pdf) | [MD](marriage_compatibility/harish_manvitha/harish_manvitha_compatibility_deep.md) · [PDF](marriage_compatibility/harish_manvitha/harish_manvitha_compatibility_deep.pdf) | 68/100 *(was 70, corrected 2026-09-19)* | Strong |

The compat engine lives at `src/saju_engine/compat.py` (see `knowledge/11-gunghap.md` for the classical reference).

## Cross-candidate analyses

| Topic | File | Notes |
|---|---|---|
| Joint-venture analysis (Sruthi + Pawan + Harish) | [cross-candidate-business-analysis.md](reports/cross-candidate-business-analysis.md) | 5 business ideas, role assignments, luck-cycle timing, recommended top pick (Idea #4: Real-Estate-Backed F&B). Created 2026-06-02. **Regen 2026-06-03** to reflect corrected Harish chart (壬申/乙巳/辛亥/己丑, 己酉 current major luck, 寅巳申 三刑 removed). |
| SaaS / software business fit | [cross-candidate-business-analysis.md#9-saas--software-business--why-it-doesnt-fit-and-2-exceptions](reports/cross-candidate-business-analysis.md) | **Verdict: generic SaaS is a poor cross-candidate fit (pure Water+Wood, opposite of trio's Earth+Metal+Fire profile).** Two exceptions work as secondary plays: Vertical SaaS for F&B/Real Estate/Hospitality (#6) and EdTech for Hospitality Training (#7). Added 2026-06-02. Verdict unchanged in 2026-06-03 regen. |
