# Saju Engine Audit — 2026-09-25

**Scope:** `src/saju_engine/` (calculation + premium-report prose), `knowledge/` (the rule base the
engine and readings cite), and the test suite. Triggered by the Harish combined Deep Destiny report
(`candidates_horoscope/reports/harish/harish-combined.md`), which the attached copy matches byte for
byte. The chart-level validation of that report is in
[`candidates_horoscope/reports/harish/validation-2026-09-25.md`](../../candidates_horoscope/reports/harish/validation-2026-09-25.md).

**Method.**
1. Recomputed Harish's chart **independently of sajupy and the engine**: solar terms from the
   `ephem` ephemeris (apparent solar longitude, bisection), day pillar from the Julian Day Number
   (anchored on 2000-01-01 = 戊午), and true solar time from the actual hour angle, which includes the
   equation of time.
2. Read the code paths behind every wrong or contradictory statement in the report and traced each
   one to a root cause.
3. Ran the test suite: `python3 -m pytest` gives **947 passed, 5 failed, 4 skipped, 10 xfailed**. All 5
   failures are environmental (see E-10).

Severity scale: **P0** gives wrong pillars or wrong data for some clients. **P1** gives a wrong or
self-contradictory interpretation in client-facing text. **P2** is misleading or incomplete.
**P3** is polish.

---

## Summary

| # | Sev | Area | Issue |
|---|---|---|---|
| E-1 | **P0** | Pillars (month/year) | Solar-term moments are stored in **KST** but compared with the birth's **local** time, so births near a 절기 in any non-KST time zone can get the wrong month pillar. Year and month can also come out inconsistent with each other. |
| E-2 | **P0** | Hidden stems (지장간) | For all four storage branches **辰, 戌, 丑, 未**, the middle (중기) and residual (여기) stems are **swapped**. This skews element percentages, the 고(庫) readings and the Water/Metal ranking. |
| E-3 | **P1** | 용신 plumbing | The 기신/구신/한신 derived for balanced and climate-gated charts exist **only in the Quick Reference text**. Every other consumer (decade lean, annual forecast, business windows, partner table) sees `None`, so Fire years get labelled "neutral" or even "favorable windows". |
| E-4 | **P1** | Strength | A chart whose drain (4.1) exceeds support (2.8) by 46% is labelled **Balanced**, while the same sentence says "the drain outweighs the support". The verdict thresholds and the prose disagree. |
| E-5 | **P1** | 용신 heuristic | The balanced branch picks the **least-represented element** as 용신. For Harish that is **Fire**, the chart's actual 기신. The 조후 gate rescued this chart, but any balanced chart the gate does not cover still gets a folk heuristic. |
| E-6 | **P1** | Annual/decade interactions | The detector returns **only the first relation per branch pair** (巳申 shows 합 but never 형/파) and never checks **3-branch completions** (巳酉丑 삼합, 亥子丑 방합, 寅巳申 삼형) or stem-vs-natal-stem interactions (乙庚합, 甲己합, 丙壬/乙辛). |
| E-7 | **P1** | Knowledge base | `07-special-formations.md` gives **wrong meanings for 지살 and 월살**, and the report printed them. `01-stems.md` says stems "do not clash", but `08-luck-pillars.md` tells the reader to check 천간충. |
| E-8 | **P1** | Relationship section | Gender is ignored. For a male chart the spouse star (재성: 乙 편재 and 甲 정재 inside the spouse palace 亥, per `11-gunghap.md` §5) is never read, and the section runs only on the palace main-qi ten-god. |
| E-9 | **P2** | 격국 | 정관격 is named with no 성격/파격 check, even though the report itself lists 상관견관 and the month branch is clashed (巳亥沖). |
| E-10 | **P2** | Tests | 5 PDF tests hard-fail when `pdftotext` is missing instead of skipping. |
| E-11 | P2 | Date filters | The auspicious-day filter ignores 형 (丑戌), 자형 (亥亥) and 원진, so it lets through 庚戌 and 壬戌 days that 형 the hour branch 丑, and 亥 days that self-punish the day branch. |
| E-12 | P2 | Template prose | Several copy-paste and template defects reach client text (listed in §E-12). |
| E-13 | P3 | Daeun display | Decade labels (0-9, 10-19…) ignore the real start (~0.5 y). Korean apps show 대운수 1 (1, 11, 21…), so clients comparing against an app will see a mismatch. |

---

## E-1 · P0 · Solar-term time-zone mismatch (month/year pillar)

**Where:** `sajupy/core.py::_check_term_time` / `_get_month_pillar_considering_term` (upstream), and
`src/saju_engine/daeun.py:174-221` (`_term_boundary_datetimes`, `_parse_term_time`).

sajupy's `calendar_data.csv` stores `term_time` in **Korea Standard Time**. For 1992 芒種 it holds
`199206051923`, which is 10:23 UTC. The ephemeris confirms 10:21 UTC. Both sajupy and the engine
compare that value against the querent's **local / solar-corrected** clock time, which is a naive
datetime in a different zone.

**Reproduction (New York, just after 立春 2024):**

```
python3 -m saju_engine --date 2024-02-04 --time 10:00 --gender M --longitude -74.0 --utc-offset -5 --format table
→ Year 甲辰  Month 乙丑  …  Daeun 0-9: 丙寅
```

立春 2024 fell at 08:27 UTC, and 10:00 EST is 15:00 UTC, so this birth is **after** 立春. The correct
month pillar is **丙寅**. The engine outputs **乙丑**, which is the 12th month of the previous year
(癸卯), sitting under a 甲辰 year pillar. The year and month pillars are mutually impossible, and the
대운 sequence starts from the wrong month.

**Exposure:** any birth whose UTC offset differs from +9 and that falls within
|offset − 9| hours of a 절기. For the US East Coast that window is **14 hours around each of the 12
절기 per year**, roughly 2% of all US births. The US is the primary market (CLAUDE.md, "Market &
Positioning").

**Harish:** not affected. His birth is 1.53 days before 芒種. The same bug does shift his 대운수:
the engine uses 1.68 days where the true figure is **1.53 days**, so 0.56 y becomes a true **0.51 y**.
The decade labels are unchanged.

**Fix:** convert the birth moment to KST (or both sides to UTC) before any 절기 comparison. Pass
`birth_local − utc_offset + 9h` into the term check, while keeping solar time for the hour branch
only. Add regression cases for the US, UK and IN zones on a 절기 date.

## E-2 · P0 · 辰戌丑未 hidden-stem order swapped

**Where:** `src/saju_engine/lookup.py:155-168`, sourced from `knowledge/02-branches.md` (the hidden-stem
table near line 35).

| Branch | Engine (middle / residual) | Standard 지장간 (중기 / 여기) |
|---|---|---|
| 丑 | 癸 / 辛 | **辛 / 癸** (癸 9d → 辛 3d → 己 18d) |
| 辰 | 乙 / 癸 | **癸 / 乙** (乙 9d → 癸 3d → 戊 18d) |
| 未 | 丁 / 乙 | **乙 / 丁** (丁 9d → 乙 3d → 己 18d) |
| 戌 | 辛 / 丁 | **丁 / 辛** (辛 9d → 丁 3d → 戊 18d) |

For each storage branch the **중기 is the element it stores**: 辰 stores Water, 戌 Fire, 丑 Metal and
未 Wood (the 묘고/庫 concept). The four 사생 branches (寅巳申亥) are already in correct order, so the
table is internally inconsistent.

**Effects:**
- Element balance weights (0.6/0.3/0.1) put the wrong stem at 0.3. For Harish, Water and Metal
  **swap places**: the report's "Water 27.8% (most present) / Metal 25.3%" should read **Metal 27.8% /
  Water 25.3%**. The "Water excess" health watchpoint is built on that swap.
- `career.md`'s 재고 paragraph and every 庫-based reading depend on which stem is the 중기.
- Minor, related: 子/卯/午/酉/亥 omit their 여기 (壬, 甲, 丙, 庚, 戊) and 午 omits 丙. That is a
  valid simplified-table choice, but it contradicts including 戊 in 寅/巳/申. Pick one convention and
  document it in `02-branches.md`.

## E-3 · P1 · Derived 기신 not propagated (two-channel bug, second instance)

**Where:**
- `premium_report.py:238`: `self.unfavorable = sa.get("candidate_unfavorable")`, which is **None** for balanced charts
- `premium_report.py:426-460`: `_avoid_watch_text` derives 기신 = Fire, 구신 = Earth, 한신 = Wood **locally, for display only**
- `prose_fillers.py:1245-1249`: year forecast checks `ctx.unfavorable`, gets None, and prints "a neutral year for this chart"
- `daeun_overlay.py:86-95`: decade `favorable_status` uses the raw `candidate_unfavorable`, so 丙午 and 丁未 come out "neutral"
- `report_data.py:640-661`: partner table marks Fire as "**Compatible** — Neutral energetic exchange"

**Client-visible result in Harish's report.** The Quick Reference says *"Avoid / Watch: Fire (기신)"*.
The rest of the report contradicts it:
- Fire decades 丙午/丁未 are shown as "neutral".
- 2026 丙午 and 2027 丁未 appear in **"Favorable Windows (2026–2031)"** with *"career moves, credentials, formal commitments"*.
- The partner table rates Fire as "Compatible".
- The Earth-stem decades 戊申/己酉 are called "favorable" even though Earth is listed as 구신.

This is the same bug class that MEMORY.md records as fixed for `favorable`. The fix is the same
pattern: resolve 기신/구신/한신 once in `yongsin.py`, store them on the context, and make every
consumer read the resolved value.

## E-4 · P1 · Strength verdict contradicts its own argument

**Where:** `strength.py:147-155` (verdict thresholds on `total_score`) and `prose_fillers.py:289-298`
(the offset sentence, which uses a separate 1.3× ratio test).

For Harish: `self 1.0 + resource 1.8 = 2.8` against `drain 4.1`, which gives `total_score = −0.43`
and a verdict of **balanced**. The ratio test in the prose sees 4.1 > 1.3 × 2.8 and prints *"the
output/wealth/authority drain then outweighs the peer and resource support."* The Quick Reference
therefore reads "Balanced — … the drain outweighs the support". A reader sees a weak argument under a
balanced label.

Separately, the month-command factor looks under-weighted. `month_season_score = 0.5` for Metal in a
巳 month, while `06-twelve-stages.md` puts 辛 at **사** in 巳, and summer Metal is the weakest seasonal
state. Recommend one scoring model feeding both the verdict and the prose, plus a
"borderline / 중화에 가까운 신약" band that the prose can state honestly.

## E-5 · P1 · Balanced-chart 용신 = least-present element

**Where:** `strength.py:177-186`.

The code comment already calls this "a folk heuristic, not a classical ruling". For Harish it selected
**Fire**, the element both the 억부 and 조후 methods treat as harmful here. `yongsin.py` overrode it
with Water only because the 巳-month climate gate fired. For balanced charts born in 寅卯申酉
(Temperate, no gate), the engine still ships the folk pick as 용신. Recommendation: for balanced charts
with no climate gate, return **"용신 requires reader argument"** (the report already carries a
reviewer note) instead of the least-element pick. At minimum, never pick an element that controls the
Day Master when the month is its own season.

## E-6 · P1 · Interaction detection incomplete (annual, decade, daily)

**Where:** `sewoon.py:137-154` (`_detect_branch_relationship`) and `sewoon.py:157-212` (`derive_sewoon`).
The same helper serves `derive_woon` and `derive_ilwoon`.

1. **First-match-wins.** The function returns a single relation, so 巳+申 is always "combine" and
   never 형 or 파, and 寅+亥 never shows its 파. `knowledge/02-branches.md` (Dual-status pairs note)
   explicitly requires both to be reported.
2. **No pairwise 형.** Only self-punishment (자형) is detected. 寅巳, 巳申, 丑戌, 戌未, 丑未 (as 형)
   and 子卯 are never flagged in annual or decade overlays, even though the module docstring (line 11)
   says "punish".
3. **No 3-branch completion** (natal + annual, or natal + 대운). For Harish this misses:
   - **巳酉丑 金局** completed by the current 대운 **己酉** (whole decade) and by **2029 己酉**
   - **亥子丑 水方** completed by **2032 壬子**
   - **寅巳申 삼형** completed by **2034 甲寅**
   - **丑戌 형** (partial 丑戌未) in **2030 庚戌**
4. **Stems.** Only an annual stem combining with the Day Master is checked. Missing: combinations with
   other natal stems (**2027 丁 + 壬 → 丁壬合**, **2030 庚 + 乙 → 乙庚合**, **2034 甲 + 己 → 甲己合**) and the clash-type
   oppositions (**2026 丙 vs 壬**, **2031 辛 vs 乙**). `08-luck-pillars.md:88` asks for "Annual stem vs.
   natal stems → 합? 천간충?".
5. `prose_fillers.py:1325-1329` (`annual_activation_note`) de-duplicates **by relation type**, so a
   second harm or clash against a different natal branch in the same year is silently dropped.

## E-7 · P1 · Knowledge-base defects surfaced in client text

- `knowledge/07-special-formations.md:213`: **지살** is described as *"earthly hindrances, delays,
  bureaucratic friction."* In the 12신살 system 지살 is the **movement/departure** star, the milder
  sibling of 역마. The engine's own `plain_glossary.py:138` already says so, which means the KB and the
  engine disagree.
- `knowledge/07-special-formations.md:215`: **월살** is described as *"monthly-style friction; romantic
  turbulence."* 월살 (고초살) is a **drying-up/stagnation** star; `plain_glossary.py:140` is correct.
- `knowledge/01-stems.md:44-49` says *"stems technically do not clash"*, while `08-luck-pillars.md:88`
  says to check 천간충. The four standard 천간충 pairs (甲庚, 乙辛, 丙壬, 丁癸) belong in `01-stems.md`
  with their source.
- `knowledge/02-branches.md`: the hidden-stem order for 辰戌丑未 (see E-2).
- 12신살 basis: `07-special-formations.md:190` uses the **day branch**. Traditional Korean practice
  mainly uses the **year branch** (many readers use both). Harish's stars change entirely by basis:
  year-based gives 巳 = 겁살, 申 = 지살, 亥 = 망신, 丑 = 반안. Document the choice as a school note.

## E-8 · P1 · Relationship analysis ignores gender / spouse star

`knowledge/11-gunghap.md` §5 states: male querent, **재성 = wife indicator**. Harish's chart has
**정재 甲 hidden inside the spouse palace 亥**, which classically is a notable spouse-star-in-spouse-palace
signal. It also has **편재 乙** on the month stem, which the Day Master **辛 controls directly** (乙辛).
The natal Relationships section never mentions either. It reads the partner only as "Hurting Officer,
candid", and marriage timing is keyed to 용신-element years instead of spouse-star and spouse-palace
activations (for example, 2034 甲寅: 정재 year + 寅亥合 into the spouse palace). The `gender` field
reaches the chart but not `prose_fillers` relationship functions.

## E-9 · P2 · 격국 without 성격/파격

`patterns.py` names 정관격 through the 본기 fallback (correct per `07-special-formations.md` §Part 1, step 4:
no 巳 hidden stem is 투출). The narrative then says *"conventional respectability, credentials, large
institutions"*, while the same report lists **상관견관** (year-stem 壬 상관 against the 정관 丙 in 巳) and
**巳亥沖** hitting the month branch. Both are classic damage to a 정관격. The KB's own 정관격 row assumes
"Day Master strong", which this Day Master is not. Add a 파격 flag (상관견관, 월지충, weak DM for an
officer grid) and soften the narrative when it fires.

## E-10 · P2 · Test suite environment coupling

`tests/test_pdf.py` (5 tests) calls `pdftotext` through `subprocess` and raises `FileNotFoundError` when
poppler-utils is absent. Use `pytest.importorskip` or `shutil.which("pdftotext")` with a skip. The core
suite is otherwise green (947 passed).

## E-11 · P2 · Date-selection filters

`Auspicious Dates` and `Monthly Lucky Dates` drop only 충/해/파 against the natal day and hour branches.
Harish's list includes 2026-10-03 **庚戌** and 2026-10-15 **壬戌** (丑戌 형 on the hour branch), and
2026-10-04 **辛亥** / 2026-10-16 **癸亥** (亥亥 자형 on the day branch). The 巳申-style dual-status
rule from `02-branches.md` is not applied either. Also check against the **annual** pillar: 2026 is
丙午, so 子 days clash the year branch.

## E-12 · P2 · Template / prose defects visible in the Harish report

| Location | Defect |
|---|---|
| `prose_fillers.py:1168-1172` | Every non-Authority, non-Wealth, non-Output decade gets "themes of **support and study**", including **Robber (庚戌) and Companion (辛亥)** decades. |
| `premium_report.py:1236-1245` | The 비견 decade (辛亥) is described as "**겁재**奪財", which is the wrong ten-god name. |
| `prose_fillers.py:871` | "a 묘/관/**충** stage": 충 is not one of the twelve stages. |
| `prose_fillers.py:530` | "The **Direct Officer stem** values hierarchy…", but 정관 is only hidden in this chart. There is no 정관 stem. |
| `premium_report.py:1327` | "Element Theme" column shows the **branch** element (丁未 → Earth) without saying so. |
| `year_by_year_note` (`prose_fillers.py:1253+`) | Focus and caution text is keyed to the year's **element**, not its **ten-god relation**. Fire is labelled "visibility, speaking, visible output" even though Fire is 관성 (authority/pressure) for a Metal Day Master. The favorability flag lumps 희신 in with 용신 ("favorable-element year" for 庚戌). |
| Friendship / Closing Note | "dominated by Output (4), Companion (4)". **Resource is also 4**, and `career.md` itself calls it a three-way tie. The top-N truncation hides the tie. |
| Health vs Business | Health says the 용신 season (**winter**) is "the cleanest window for new beginnings". Business says the DM season (**autumn**) is "the most aligned launch window". Pick one rule. |
| Health "Seasonal & Daily Rhythms" | "the Water hours of the day (per the **Twelve Stages**)": hours come from the 12 branches, not the 12 stages. "evenings for Water" conflicts with the Lucky Card's 21:00–01:00. |
| Travel & Move Timing | Says "favorable **Water**-element … periods: ages 20-29 (戊申), 30-39 (己酉), 40-49 (庚戌)". None of those decades contains Water. |
| Business "Favorable Windows" | The table lists all six years, including two 기신 years, under a "Favorable" heading (see E-3). |
| Health watchpoints | "Deficient: Fire → support the heart" for a chart born in the **peak-Fire month** whose 조후 remedy is to **cool** Fire. The raw-percentage view contradicts the climate view the report itself uses for 용신. |

## E-13 · P3 · 대운 labelling

The engine labels decades 0–9, 10–19 and so on. The true start is 0.51 y (E-1), so the periods run from
roughly Dec 1992 to Dec 2002, Dec 2002 to Dec 2012, and so on. The current 己酉 period runs **~Dec 2022 → ~Dec 2032**,
and 庚戌 starts around **Dec 2032** rather than at the June 2032 birthday. Korean 만세력 apps round 1.5
days / 3 to **대운수 1** and list 1, 11, 21, 31…, often in Korean age. Show "starts ≈ age 0.5 (Dec 1992)"
next to the table so client cross-checks don't look like errors.

---

## What is verified correct

Checked independently: the four pillars (壬申 乙巳 辛亥 己丑), including the day pillar by JDN; 芒種
1992 = 06-05 10:21 UTC (so the month is 巳, correct); true solar time **02:59:32** (the engine's 02:59
and the boundary warning are right); equation of time +1.77 min (the engine uses +1.7); every
visible-stem and hidden-stem ten-god; the 12운성 of 辛 on every natal and 대운 branch; the 대운
direction (yang year, male, forward) and sequence 丙午…癸丑; the 세운 pillars 2026–2035; all 20
auspicious-date day pillars I sampled; 천덕귀인 (巳 month → 辛) on the Day Master; the absence of
natal 도화; 역마 at 巳 (day-branch basis); 河圖 numbers (Water 1·6, Metal 4·9); and the natal
합/충/형/해/파 list (except that it omits 巳丑 반합 and 乙辛, see the validation file).

## Recommended fix order

1. **E-1** (wrong pillars for US clients), then **E-2** (wrong data table). Add regression tests for both.
2. **E-3** + **E-5** in one pass through `yongsin.py`: resolve 용신/희신/기신/구신/한신 once, with
   provenance, and make every consumer read it.
3. **E-6** (interaction detector: return all relations per pair, add 3-branch completion against natal
   ∪ 대운 and stem-stem checks) and **E-11** (the filters reuse the detector).
4. **E-4**, **E-7**, **E-8**, **E-9** (interpretation layer and KB).
5. **E-10**, **E-12**, **E-13** (polish).
6. Regenerate every client report in `candidates_horoscope/reports/` after 1–3. E-2 alone changes the
   element percentages of every chart that has a 辰, 戌, 丑 or 未.
