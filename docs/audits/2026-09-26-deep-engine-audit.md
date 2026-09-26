# Deep Engine Audit — 2026-09-26

**Scope:** `src/saju_engine/` (calculation, strength, 용신, stars, patterns, luck overlays,
compat), `src/saju_html/` (PDF/HTML rendering), `tools/` intake servers, CI, and the
`knowledge/` tables the engine implements.

**Baseline:** branch `claude/practical-babbage-7jo9xx` at `6255f0b`. That is after every
E-1…E-13 fix and the "next set" in `2026-09-25-engine-audit-verification.md` closed.

**Method:** a fresh audit, not a re-verification. Every finding below was reproduced against
live code with a script or a direct computation. Doctrinal findings are marked
**[doctrinal]** and need a sourced decision per CLAUDE.md Ground Rule 1 before the knowledge
file changes. The 절기 (solar term) timing check used an independent ephemeris; the script is
in `docs/audits/scripts/check_solar_terms.py`. Findings already closed in earlier audits are
not repeated here.

---

## 0. Health snapshot

| Check | Result |
|---|---|
| `pytest` (fresh container, `pip install -e ".[dev,web]"`) | **1034 passed, 9 skipped, 9 xfailed, 0 failed** (33 s). Skips are `pdftotext`/Playwright tests. |
| `ruff check src tools tests` (default rules) | **96 errors**, including **7 F821 undefined names** and **13 F601 duplicate dict keys**. CI does not run ruff. |
| Core lookup tables (stems, branches, 10-god, 12운성, 합/충/형/파/해, 삼합/방합, 60-cycle, 오호둔/오서둔, 천을귀인, 월덕, 원진, 귀문관, 12신살, 공망) | Correct, re-derived by hand. The exceptions are in N-9. |
| Self-service FastAPI app (`tools/client_intake_app.py`) | **Does not start** (N-1). |

## 1. Summary of findings

| # | Sev | Area | Finding |
|---|---|---|---|
| N-1 | **P0** | Web app | `client_intake_app.py` raises `NameError: TOOLS_DIR` on import, so the self-service calculator and `/compat` route have never been runnable from this repo. |
| N-2 | **P1** | Pillars / 대운 | The E-1 override compares **true-solar** birth time against **civil-clock** 절기 instants, which **flips correct year/month pillars** for births up to ~45 min after a 절기 (Seoul) or ~40 min (Mumbai). |
| N-3 | **P1** | Data | sajupy's `calendar_data.csv` 절기 times are wrong by a **median of 22 min and up to 114 min**; 39% of terms are off by more than 30 min. Combined with N-2, this gives a wrong month pillar in ~15–37 min of every term window. |
| N-4 | **P1** | 대운 | The "current major luck" switches **1.3–2.4 years before** the engine's own precise 대운 start date, because a floored elapsed-year `start_age` is compared to 세수. |
| N-5 | **P1** [doctrinal] | Strength | Using 음생양사 12운성 as the 월령 signal **inverts yin Day Masters**: 乙 born in 午 scores as supported and 乙 in 亥 as unsupported. Yin DMs born in their draining season are rated "strong" 37% of the time (yang: 10%). |
| N-6 | **P1** [doctrinal] | 용신 | 조후 sets the headline 용신 from the **month branch alone** for 66% of charts. In **9% of all charts** the prescribed 용신 is already the chart's **most abundant** element. |
| N-7 | **P1** | Web compat | When the form's 용신 fields are blank, `/compat/generate` injects the raw pre-climate 억부 pick as a **"reader-confirmed" override**. This changes the composite score in **77% of pairs**. |
| N-8 | **P1** | Security | The HTML/Playwright backend renders report markdown with `html=True`. A client name containing `<script>`/`<iframe>` reaches Chromium unescaped. |
| N-9 | P2 [doctrinal] | Stars / grids | 문창귀인 甲→亥 (classical: 巳). 천덕귀인 can never fire in 卯/午/酉/子 months. 양인격 excludes the **month** branch, which is the classical grid position. 건록격 is flagged at any position. |
| N-10 | P2 | Compat report | The cover's "top 3 red flags" are chosen **alphabetically by sub-system label**, not by severity. |
| N-11 | P2 | Annual luck | "What This Year Means" uses the Gregorian year. Reports generated Jan 1 – Feb 3 describe the **next** 세운 while age and 대운 use 입춘. |
| N-12 | P2 | Strength / balance | Hidden-stem weights give branches unequal total qi: 子/卯/酉 = 0.6, 午/亥 = 0.9, three-stem branches = 1.0. The pure 왕지 are underweighted by 40%. |
| N-13 | P2 | Input / timezones | No DST or historical-offset handling in the CLI or manual flow. The intake default offset is **+5.5 (India)** despite the US-first pivot. The JSON intake form collects no offset or timezone. The single-chart form cannot enter .25/.75 offsets. |
| N-14 | P2 | Web app ops | Public endpoint writes into curated `marriage_compatibility/{a}_{b}/` and **overwrites** same-name client deliverables. `compute_chart` runs on the event loop. No size/rate limits. Exception text is returned to clients. |
| N-15 | P2 | Boundary disclosure | There is no knife-edge warning for 子-hour edges (23:00/01:00) or for births near a 절기, the two boundaries that change the most pillars. |
| N-16 | P3 | Code quality | 7 F821 (typing names), 13 F601 (duplicate translation keys, some with **conflicting** values), 23 unused variables, 18 unused imports. Ruff is not in CI. |
| N-17 | P3 | Dependency | `sajupy>=0.2.0` is unpinned, yet the engine reads its private CSV and compensates for its internal KST behaviour. |
| N-18 | P3 | Range edges | 1900-01-01 early births west of the meridian crash. Late-2100 forward 대운 silently returns start age 0. `saju_age` compares against 입춘 by **date**, not instant. |
| N-19 | P3 | Strength | `month_season_score` is computed and exported but unused in the verdict. Ties in the balanced least-present pick always resolve to Wood. |
| N-20 | P3 | Natal relations | Pairwise 삼형 entries are duplicated when a branch repeats (e.g. `丑寅丑未` lists 丑未 twice). No positions are recorded. |
| N-21 | P3 | Repo | `apps/landing-page` has config and built PDFs but **no source** (`src/`, incl. the `src/proxy.ts` that `DEPLOY.md` describes). It cannot be audited or rebuilt. |
| N-22 | P3 | Tests | `tests/test_pdf.py:31-37` runs `build-pdf.sh sruthi`, which **overwrites the tracked client deliverable** `candidates_horoscope/reports/sruthi/sruthi-report.pdf` on every test run. |

---

## 2. Findings in detail

### N-1 (P0) — Self-service FastAPI app crashes on import

`tools/client_intake_app.py:76-77` uses `TOOLS_DIR`, but no line in the file's history has
ever defined it (`git log -S TOOLS_DIR` shows only the introducing commit `d46b8dd`).

```
$ python3 -c "import sys; sys.path.insert(0,'tools'); import client_intake_app"
NameError: name 'TOOLS_DIR' is not defined
```

No test imports any `tools/*.py` module, and CI runs no linter, so nothing caught it. CLAUDE.md
lists the app as ✅ Priority 5, which is not true of this repo.

**Fix:** add `TOOLS_DIR = PROJECT_ROOT / "tools"`. Add a smoke test that imports the app and
calls `GET /` and `POST /generate` with FastAPI's `TestClient`. Add `ruff check --select F`
to CI.

### N-2 (P1) — Solar time is compared against civil-time 절기 instants

A 절기 is an absolute instant. `pillars.py::_independent_year_month_pillar` and
`daeun.py::_term_boundary_datetimes` convert the KST term time to the birth's **civil** offset
(`KST + (utc_offset − 9)`). They then compare it with the **true-solar** birth time
(`eff_hour/eff_minute`, and `solar_time` in `engine._build_daeun`). The two clocks differ by
the longitude correction plus the equation of time: −32 min in Seoul, −38 min in Mumbai, and
more than 2 h in western China or Spain.

Because the E-1 fix *overrides* sajupy whenever the two disagree, the mismatch now actively
rewrites pillars. Reproduction for Seoul, 2024-02-04 (CSV 立春 = 17:00 KST):

| Civil birth (KST) | Solar time | Engine year/month | `year_month_correction` |
|---|---|---|---|
| 17:20 | 16:33 | 癸卯 / 乙丑 | overrode sajupy's 甲辰 |
| 17:40 | 16:53 | 癸卯 / 乙丑 | overrode sajupy's 甲辰 / 丙寅 |
| 17:55 | 17:08 | 甲辰 / 丙寅 | — |

Using the CSV's own term time, every birth from 17:00 to ~17:47 KST is pushed back into the
previous year and month. (N-3 shows the CSV is itself 27 min early here, so the actual wrong
window is different, but the clock mismatch is a bug either way.)

**Fix:** in both functions, compare the **civil** birth datetime (the raw input
`year…minute`) with `term + tz_shift`. Keep solar time only for the hour branch. The
`compute_daeun` docstring currently instructs callers to pass solar time; that guidance is
wrong. Add regression tests at ±5 min around a 절기 for Seoul (+9, lon 127) and Mumbai
(+5.5, lon 72.9).

### N-3 (P1) — sajupy's 절기 table is not accurate enough for pillar boundaries

`docs/audits/scripts/check_solar_terms.py` recomputes all 2,413 month-opener terms
(1900–2100) from an ephemeris. It is calibrated to the published 2024 values within about
5 s: 立春 08:26:53 UTC, 芒種 04:09:56, 立冬 22:19:46.

| Era | Median CSV error | Range | Terms off by >15 min |
|---|---|---|---|
| 1900–1919 | −24.1 min | −111 … +64 | 205/240 |
| 1940–1959 | −15.6 | −70 … +33 | 170/240 |
| 1960–1979 | −9.7 | −46 … +26 | 100/240 |
| 1980–1999 | −4.7 | −32 … +9 | 42/240 |
| 2000–2019 | −4.3 | −23 … +29 | 52/240 |
| 2020–2039 | +2.6 | −38 … +47 | 152/240 |
| 2040–2059 | +7.6 | −49 … +66 | 184/240 |
| **All** | **median \|err\| 22.2 min** | **max 113.6 min** | **1529/2413 (935 > 30 min)** |

The CSV lists 2024 立春 as 17:00 KST; the true instant is 17:27. The seasonal error pattern
and secular drift point to a low-precision generator, not a timezone issue. The CSV is in a
fixed UTC+9 throughout, including 1954–61 when Korea used +8:30, so E-1's fixed 9.0
conversion is correct.

**Measured impact (N-2 + N-3 together).** 60 random terms from 1950–2030, births swept ±150 min
in 10-min steps, engine month branch compared with the ephemeris truth:

| City | Engine wrong-month minutes per term | Share of all births |
|---|---|---|
| Seoul | 32 | 0.074% |
| Mumbai | 38 | 0.086% |
| New York / London / LA | 16–17 (CSV error only; these cities sit near their meridian) | ~0.036% |

That is about 1 birth in 1,100–2,700. For the affected births the whole chart is wrong:
month pillar, 격국, strength, 용신 and the full 대운 sequence. Older and future charts
(pre-1960, post-2030) are hit 2–4× harder.

**Fix:** ship an accurate term table as package data, computed once from an ephemeris
(DE440 via Skyfield) or taken from KASI. Use it in `_parse_calendar` in place of sajupy's
CSV. Keep sajupy only for the day pillar and lunar data. Add a disclosure note (the
`hour_boundary` pattern) for births within ~30 min of a 절기.

### N-4 (P1) — Current 대운 is selected 1.3–2.4 years early

`starting_age()` returns `days // 3`, which is floored **elapsed** years. `saju_age()` returns
**세수**: birth year = 1, +1 at every 입춘, so it runs 1–2 above elapsed years. `engine.py:348`
compares the two directly (`start_age <= current_age <= end_age`). The report's own E-13
prose meanwhile states the precise start month (birth + days × 4 months).

The date on which the engine switches to the 2nd decade, against the engine's own precise start:

| Birth (Seoul) | 대운수 label | Days | Precise 2nd-decade start | Engine switches | Early by |
|---|---|---|---|---|---|
| 1990-06-15 10:00 M | 7 | 22.33 | 2007-11-24 | 2006-02-07 | 1.8 y |
| 1985-03-20 14:00 F | 5 | 15.63 | 2000-06-04 | 1999-02-07 | 1.3 y |
| 1992-06-04 03:00 M | 0 | 1.68 | 2002-12-26 | 2001-02-07 | 1.9 y |
| 2000-01-10 12:00 F | 8 | 25.39 | 2018-06-27 | 2016-02-09 | 2.4 y |
| 1975-11-02 08:00 M | 8 | 24.04 | 1993-11-06 | 1992-02-07 | 1.7 y |

For roughly 15–25% of any decade, the report's "Current Major Luck" headline, Quick
Reference, "What This Year Means", and the compat timelines name the **next** 대운 while the
prose says it hasn't started. This is the A5 fix's convention mix in reverse.

**Fix:** choose one convention.
- **(a) Recommended:** select `current_daeun` from the precise start instant
  (`birth + days/3 years`, already computed for the note) and keep the displayed labels.
- **(b)** Define labels in 세수 with the Korean rounding (remainder ≥ 1.5 days rounds up,
  label = 대운수) and state it.

Either way, pin it with tests at the transition date.

### N-5 (P1, doctrinal) — Yin Day Master strength is inverted

`strength.py` weighs `month_stage_score = _STAGE_WEIGHT[twelve_stage(DM, month_branch)] × 1.5`.
For yin stems, `twelve_stage` runs the backward (음생양사) cycle, so 乙 in 午 is 장생 (+2.25)
and 乙 in 亥 is 사 (0). Mean month-stage points by the month element's relation to the DM
(non-earth months):

| | same | resource | output (drains) | wealth | authority |
|---|---|---|---|---|---|
| Yang DM | 2.62 | 1.95 | 0.15 | 0.32 | 1.05 |
| **Yin DM** | 2.62 | **0.77** | **1.73** | 0.71 | 0.26 |

Verdicts over 6,000 random charts:

| | output month: strong | resource month: strong |
|---|---|---|
| Yang DM | 10% | 62% |
| **Yin DM** | **37%** | **37%** |

The knowledge base disagrees with itself here. `knowledge/06` §Cheat Sheet ties strength to the
DM's stage. `knowledge/09` Step 2 defines 신강 from "the month branch's hidden stems + 1
supporting ally", which is element-based and gives the expected ordering. The 적천수 commentary
line (임철초) is explicitly critical of using 음장생 for strength.

**Fix (needs a reader decision):** derive 득령 from the month branch's element relation or
hidden stems (knowledge/09), or apply 12운성 to yin stems via their yang partner
(음양동생동사) for strength only. Keep 음생양사 for the descriptive 12운성 table.

### N-6 (P1, doctrinal) — 조후 overrides 용신 from the month branch alone

`climate.assess_climate()` takes only the month branch. `yongsin.favorable_element()` then
lets the climate element win whenever the band is not temperate: 8 of 12 branches
(巳午未亥子丑辰戌). The chart's actual temperature is never checked. Across 1,500 random
charts:

- 987 (66%) are climate-governed. 237 fall to the balanced folk heuristic, 205 to strong-DM
  drain and 71 to weak-DM support.
- In 249 climate-governed charts the prescribed 용신 is already ≥25% of the chart. In 140
  (**9% of all charts**) it is the chart's **most abundant** element.

Examples:
- 1963-10-24 11:00, 癸壬庚辛 / 卯戌子巳: 戌 month → "dry" → Water, while the chart is 36%
  Water with 壬, 癸 and 子.
- 2010-12-06 01:00, weak 庚 DM with 丙/丁 at 35% Fire: 亥 month → Fire. Under 억부, Fire is
  this chart's 관살, i.e. its 기신.

knowledge/09 and the 2026-09-19 research note gate 조후 on "극단적 기후가 다른 기능을 막으면"
(when an extreme climate blocks the chart). The chart has to *be* extreme, not merely be born
in that season.

**Fix:**
1. Gate the climate override on a chart-level temperature measure: Fire/Water weight across
   stems and hidden stems, including 조열 and 한습 earth.
2. When the remedy element is already dominant, fall back to 억부 or set
   `requires_reader=True`.

Re-run the climate validation matrix afterwards.

### N-7 (P1) — Web compat path mislabels the raw 억부 pick as reader-confirmed

`tools/client_intake_app.py::_render` (≈ line 352):

```python
fe_a = favorable_element_a or chart_a.strength_assessment.get("candidate_favorable")
```

This value is passed to `generate_compat_report(favorable_element_a=…)`, which treats any
non-empty value as a **reader override**. The result bypasses the climate merge and the E-3/E-5
single resolution, and is shown to the client as "confirmed by the reader". Over 300 random
M/F pairs, it changed the composite score in **231 (77%)**; partner A's resolved 용신 differed
from the raw pick in 153.

**Fix:** pass `favorable_element_a or None` and let `favorable_element()` resolve it.

### N-8 (P1) — HTML injection into the Playwright renderer

`saju_html/renderer.py:83` builds `MarkdownIt("commonmark", {"html": True})`. Cover fields are
`html.escape`d, but the report body is not. `generate_premium_report` interpolates
`chart.name` verbatim:

```
name = '<iframe src="file:///etc/passwd"></iframe><script>x=1</script>'
→ both tags survive into the HTML passed to page.set_content()
```

Today the HTML backend is reader-driven. Intake-supplied names still reach it, and the
landing page plans to route submissions here. Script execution in Chromium means it can make
outbound requests (SSRF) and rewrite the PDF.

**Fix:**
- Set `html=False`; the generators emit only markdown.
- Otherwise escape `name`, `city` and `main_concern` at the generator boundary.
- Launch Playwright with `java_script_enabled=False`.
- Abort all non-`data:` requests via `page.route`.

### N-9 (P2, doctrinal) — Star and grid table errors (engine matches the KB, the KB is wrong)

- **문창귀인 甲 → 亥** (`stars.py:347`, `knowledge/07` L200). The classical mnemonic
  「甲乙巳午報君知, 丙戊申宮丁己雞, 庚猪辛鼠壬逢虎, 癸人見兔」 gives **甲 → 巳**. 亥 is 甲's 장생
  (학당귀인), probably conflated. The other nine entries match.
- **천덕귀인.** The table's targets for 卯/午/酉/子 months are the **branches** 申/亥/寅/巳.
  `derive_stars` searches only the four stems (`[s for s in stems if s == hv]`), so the star
  can never fire in those four months (1/3 of charts). The KB text says the same
  ("looked for among the four natal 천간"), so the KB contradicts its own table. Check the
  branches too.
- **양인격 / 건록격.** `knowledge/07` L102 and `patterns.py:622` read 양인격 when the blade
  branch is in the year, day or hour pillar, and **exclude the month**. In 자평진전 the grids
  are defined by 월령: 月令 양인 → 양인격, 月令 건록 → 건록격. Other positions give 일인, 귀록 and
  so on. The engine's `jianlu` block labels any position "건禄格". Meanwhile `regular_grid`
  names a month 비겁 as 비견격/겁재격, labels most Korean texts call 건록격/월겁격 (양인격).

Correct the knowledge file first, with a sourced citation, then the code (Ground Rule 1).

### N-10 (P2) — Compat "top red flags" are alphabetical

`compat.py:1462`: `red_flags = sorted(set(red_flags))[:3]`. Entries are
`"{sub.label}: {flag}"`, so the cover shows flags from whichever sub-systems sort first
("Combined…", "Day-branch…"). A −10 day-branch 충 can lose its place to a −1 folk item.

**Fix:** carry each flag's score contribution and sort by it.

### N-11 (P2) — "This year" is the Gregorian year

`premium_report.py:164` and 8 other sites use `reference_date.year` to pick the current 세운.
For a reference date of Jan 1 – Feb 3, the saju year is still the previous one.
`chart.current_age` (입춘-based) and every decade calculation already know this, so a January
report's "What This Year Means" contradicts its own age line.

**Fix:** add a `saju_year(ref_date)` helper and use it at all nine sites.

### N-12 (P2) — Branch qi is unequal in element balance and strength

Weights are main 0.6, middle 0.3, residual 0.1 per hidden stem. Each branch's total therefore
depends on how many hidden stems the table lists:

| Branches | Total qi |
|---|---|
| 子, 卯, 酉 | 0.6 |
| 午, 亥 | 0.9 |
| 寅, 巳, 申, 辰, 戌, 丑, 未 | 1.0 |

The 왕지 (子午卯酉), the purest single-element branches, are underweighted by 10–40%. This
feeds the client-facing Element Balance percentages, the strength verdict, `dominant_element`,
the 종격 thresholds, and compat's element strength.

**Fix:** normalise each branch to 1.0, or use 월률분야 day shares (e.g. 寅 = 戊7/丙7/甲16),
then re-baseline the validation fixtures.

### N-13 (P2) — Timezone and DST handling for the stated market

- The CLI takes only a numeric `--utc-offset`. There is no IANA option and no DST warning.
  Nothing in `.claude/commands/`, CLAUDE.md or `knowledge/09` tells the reader that:
  - US/UK/EU summer births need the DST offset (New York in July is −4, not −5);
  - Korea used +8:30 in 1954–61 and DST in 1948–60 and 1987–88.

  A one-hour error moves the hour pillar for about half of births. It moves the solar-time
  correction by 60 min.
- `client_intake_app.html` defaults `utc_offset=5.5` and the server defaults `Form(5.5)`.
  A US client who leaves it untouched gets an IST chart. The 2026-09-07 pivot made the US the
  primary market.
- `client_intake_form.html` (JSON path) collects **no** offset or timezone, contrary to the
  CLAUDE.md "Client Intake" section.
- The single-chart form has `step="0.5"`, which blocks +5.75 (Nepal), +8.75 and +12.75. The
  compat form uses `0.25`.

**Fix:** make IANA timezone + city the primary input everywhere, resolved with `zoneinfo`
as `_derive_utc_offset` already does in the web app. Add `--timezone` to the CLI. Make the
numeric offset a fallback with no default.

### N-14 (P2) — Web app operational and security gaps (once N-1 is fixed)

- `/compat/generate` writes to `candidates_horoscope/marriage_compatibility/{slug_a}_{slug_b}/`,
  the curated deliverable folder. A public request for "Pawan" × "Sruthi" **overwrites the
  real client's `pawan_sruthi_compatibility.{md,pdf}`**. Concurrent requests for the same
  names race on the same file. Write to a per-request temp directory instead.
- Both `compute_chart` calls in `compat_generate` run on the event loop, blocking all
  requests. A `ValueError` from them (bad timezone, out-of-range year) becomes a 500 whose
  body echoes the exception text.
- No limits on field length, request size or rate, and every request leaves an intake JSON
  and a PDF on disk. Disk-fill is trivial.
- `allow_credentials=True` combined with an env-configurable origin list; binds `0.0.0.0`.
- `client_intake_server.py` decodes form bodies with `unquote`, not `unquote_plus`, so
  "John Doe" is stored as `John+Doe`. There is no `Content-Length` cap.

### N-15 (P2) — Boundary disclosures miss the two costliest edges

`_hour_boundary_info` returns `None` whenever the neighbouring branch is 子, so births near
23:00 and 01:00 get no warning. Those are the edges where the day pillar (chinese convention)
or the hour-stem source day (korean 야자시) also flips. There is also no warning for births
within minutes of a 절기, where the month pillar, possibly the year pillar, and the 대운 flip
(N-2/N-3).

**Fix:** emit the note with an explanation of the compound change, even if the alternate
pillar isn't re-derived.

### N-16 (P3) — Lint debt that hides real bugs

- **F821 (7).** `Dict` in `daeun.py` (3) and `sewoon.py` (1), `List` in `saju_html/__init__.py`
  (3). These are harmless at runtime under `from __future__ import annotations`, but
  `typing.get_type_hints()` raises on them. The two `TOOLS_DIR` hits are N-1.
- **F601 (13).** Duplicate keys in the translation maps, some with **conflicting** values:
  - `육합`: "six-combination" vs "Six Harmony"
  - `상생`: "generating cycle" vs "mutual generation"
  - `명리정종`: with vs without "(Korean school)"
  - `사람의`: "people's" vs "of the people"

  The later value silently wins, so PDF terminology is inconsistent with the engine's.
  `chart.py:410` repeats `reference_date` (same value, harmless).
- **Other.** 23 unused variables and 18 unused imports.

**Fix:** add `ruff check --select F,B` to `.github/workflows/ci.yml`.

### N-17 (P3) — Unpinned private dependency

The engine reads sajupy's private `calendar_data.csv` and works around its internal KST
comparison (E-1), yet `pyproject.toml` allows `sajupy>=0.2.0`. A future sajupy release could
change the CSV schema, fix or alter the timezone behaviour, or move the file, and the double
correction would silently break.

**Fix:** pin `sajupy==0.2.0` and add a test asserting the CSV's SHA-256. This becomes moot if
N-3 replaces the CSV.

### N-18 (P3) — Range edges

- `compute_chart(year=1900, month=1, day=1, hour=0, longitude=127)` raises
  `ValueError: Could not find data for the given date: 1899-12-31`. The solar rollback leaves
  the table.
- For late-2100 forward births, the next term is missing, so `starting_age()` returns **0**
  silently (`# ... just return 0 and let the caller flag it`). No caller flags it.
- `saju_age()` compares `birth < ipchun.date()`. A birth on 입춘 day but before the term
  instant is counted in the new saju year, which puts 세수 (and the 대운 selection) off by one.

### N-19 (P3) — Strength heuristic hygiene

- `_MONTH_BRANCH_SEASON` / `month_season_score` has been computed and exported in
  `strength_assessment` since the D1 fix, but it no longer affects the verdict. Readers of the
  JSON will assume it does.
- In the balanced fallback, `min()` over a fixed list resolves ties to the first entry
  (Wood). Surface ties instead.

### N-20 (P3) — Duplicate pairwise 삼형

`engine._derive_branch_relationships` appends pairwise 삼형 once per pillar pair. For
`丑寅丑未` the list contains `('丑','未','—','삼형 丑未 …')` twice. The entries carry no
positions, so the duplication is visible in prose counts. Deduplicate them, or record
positions as `combinations_6` does.

### N-21 (P3) — Landing-page source not in the repo

`git ls-files apps/landing-page` shows configs, lighthouse reports and PDFs, but no `src/` or
`app/`. `DEPLOY.md` documents a `src/proxy.ts` security proxy that can't be reviewed.


### N-22 (P3) — Test suite overwrites a client deliverable

`tests/test_pdf.py:31-37` shells out to `tools/build-pdf.sh sruthi` and asserts on the real
output path. Every `pytest` run rewrites the tracked `sruthi-report.pdf` with a PDF built
from the current code and timestamp. That dirties the working tree, and a careless
`git add -A` would commit an unreviewed client file. (It happened during this audit and was
reverted.)

**Fix:** have `build-pdf.sh` accept an output path (or `$SAJU_OUT_DIR`), and point the test at
`tmp_path`.

---

## 3. What is solid

- **Lookup tables.** Stem/branch data, the ten-god derivation, 12운성 starts and directions,
  六合/六冲/六害/六破/三合/方合/三刑, 오호둔/오서둔, the 60-cycle anchor, 공망, 천을귀인,
  월덕귀인, 원진, 귀문관, 백호, 괴강 and the 12신살 table all check out by hand.
- **E-1 timezone conversion** (fixed UTC+9 CSV) is confirmed correct by the ephemeris
  analysis. Only the solar/civil mix (N-2) is wrong.
- **Day pillar** (JDN anchor) and **hour stem** (오서둔, including 야자시 from the next day's
  stem) are correct.
- **Equation of time and sub-minute hour-boundary reporting** work as documented.
- **The test suite is broad** (1034 passing) and fast (33 s). The gaps are coverage of
  `tools/`, boundary sweeps around 절기, and yin-DM strength fixtures.

## 4. Recommended fix order

1. **N-1 + N-16 CI lint.** Minutes of work, and it unblocks the whole web path.
2. **N-2.** Compare civil against civil. A small, contained change that stops the E-1
   override from corrupting pillars.
3. **N-7, N-8, N-14 (overwrite).** Required before any public deployment.
4. **N-4.** Pick one 대운 convention; it affects every report's headline.
5. **N-3.** Ship an accurate term table and a 절기 knife-edge disclosure (N-15).
6. **N-5, N-6, N-9, N-12.** These need sourced knowledge-file decisions first (Ground
   Rule 1), then engine changes and a re-baseline of the validation fixtures. Regenerate
   client reports afterwards (`tools/regen_client_reports.sh`).
7. **N-10, N-11, N-13.** Client-facing correctness and intake UX.
8. **P3 items.**

**Client-report exposure:** N-4, N-5, N-6 and N-12 can change existing deliverables.
After fixing, re-run `tools/regen_client_reports.sh` and diff the Quick Reference blocks
(Current Major Luck, strength verdict, 용신) for each candidate before re-sending anything.

## 5. Reproduction notes

- **Ephemeris check:** `pip install ephem && python3 docs/audits/scripts/check_solar_terms.py`
  (about 1 min).
- **N-2, N-4, N-5, N-6, N-7:** the numbers above come from ad-hoc scripts that sample
  `compute_chart` / `compute_pillars` with fixed seeds (Seoul `utc_offset=9, longitude=127`
  unless stated). The core call for each is quoted in its section and can be rerun
  directly.
