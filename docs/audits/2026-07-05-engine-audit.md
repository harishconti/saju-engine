# Saju Engine — Complete Audit (2026-07-05)

> **ARCHIVED / HISTORICAL** — point-in-time record. See `README.md` in this folder and the live
> trackers (`../issues_bugs.md`, `../../improvements_issues.md`). Paths/line-numbers may be stale.

**Scope:** `tools/saju_engine/` (22 modules, ~9,500 LOC) + `tests/` + `knowledge/` doctrine files.
**Method:** 7 parallel audit agents (foundation tables, strength/patterns/stars, daeun/sewoon, compat, report/prose/nayin, engine/cli/validate, web doctrine research) + direct verification of every BUG-level finding against source.
**Baseline:** 441/441 pytest pass; `tools/cross_validate.py` 12/12 pass; test coverage 82% overall.

**Headline:** The **foundation/lookup layer is doctrinally sound** — all 10 stems, 12 branches, HIDDEN_STEMS, 십신 (full 10×10), 12운성 (full 10×12 incl. tricky yin-stem backward cases), 五虎遁/五鼠遁, 천간합, 육합/삼합/충/형/파/해, JIAZI_CYCLE, solar-term month boundaries, and the Korean-야자시 vs Chinese-조자시 자시 handling are all verified correct. The defects concentrate in the **interpretation layer** (격국/용신/희신 logic), the **CLI/orchestration glue**, and a handful of **doctrinal-vs-knowledge inconsistencies**.

**Counts (after cross-cutting dedup):** ~21 BUGs, ~39 GAPs, ~33 IMPROVEMENTs.

---

## A. High-severity BUGs (verified)

### A1. 정격 (Regular Grid) is taken from 월간, not 월지 투출 — `patterns.py:300`
```python
month_tengod = L.ten_god(day_master, month_stem)   # uses visible month STEM
```
Classical 자평진전/연해자평/명리정종 (confirmed by web research, point G): 격국 is the 월지 hidden stem (본기→중기→여기) that **투출** (transparently appears) on a 천간 of any pillar; if none 투출, fall back to 본기. The engine uses the visible 월간 directly, ignoring 월지's hidden stems. This **mislabels the 격국 for a large fraction of charts** — e.g. a 甲 DM with 午 month (본기 丁-상관) but a 庚 월간 is labeled 편관격 instead of 상관격. *Note: a minority Korean school does use 월간 directly; the fix is to either implement 투출 or document the school choice in `knowledge/07` (which is currently ambiguously worded on line 7).*

### A2. 희신 (Huisin) definition contradicts the project's own `knowledge/03` — `strength.py:159-167`
`knowledge/03-five-elements.md:99` explicitly defines: **희신 = the element that generates 용신** (용신 Water → 희신 Metal, because Metal generates Water).

The engine returns the **opposite** in both branches:
- Strong DM: `favorable=output`, `supporting=wealth`. But wealth does **not** generate output — **self (비겁)** generates output. Per knowledge/03, 희신 should be `dm_element`.
- Weak DM: `favorable=resource`, `supporting=dm_element`. But self does **not** generate resource — **wealth (재성)** generates resource. Per knowledge/03, 희신 should be `wealth_element`.

The engine follows a *modern redefinition* of 희신 as "secondary favorable element," but that directly contradicts the strict classical definition in `knowledge/03`. Two tests encode the current (wrong-vs-knowledge) behavior and would need updating. Fix: either align code to knowledge/03, or document both schools in `knowledge/03` and add a school flag.

### A3. 대운 starting_age wrong for births *after* the 절기 moment on a 절기 date — `daeun.py:148-151`
The same-date shortcut discards the term's sub-day time:
```python
if term_dt.date() == birth:
    return (birth_dt, birth_dt)   # ignores term_time
```
Reproduced: `starting_age(2024, 2, 4, "forward", 23, 59)` → returns `0`; doctrine says ~`9` (next 절기 경칩 2024-03-05, ~30 days → ~10 years ÷ 3 ≈ 9). The boundary is the term **moment**, not the calendar date. The existing test only exercises the before-term-time case.

### A4. Birth hour/minute (and solar-corrected time) dropped before reaching `starting_age()` — `engine.py:116-129` → `daeun.py:239-266`
`compute_daeun` only takes `year, month, day`; `starting_age()` accepts `hour, minute` for sub-day precision but the plumbing never passes them. For births within a few hours of a 절기, the day-count can be off by 1 (~4 months in starting age; usually not enough to flip the integer, but it can near boundaries).

### A5. "Current 대운" selection mixes 만 나이 (western) with 세수 (Korean counting) — `premium_report.py:128`
```python
current_age = current_year - by - ((current_month, now.day) < (bm, bd))   # 만 나이
current_daeun = next(p for p in chart.daeun if p.start_age <= current_age <= p.end_age)
```
`DaeunPeriod.start_age` is `days // 3` from the classical 3-day=1-year rule, which yields **세수** (Korean counting age: birth=1, +1 at each 입춘). `current_age` here is **만 나이**. The comparison mixes conventions; depending on birth date vs 입춘, the offset is 1–2 years and **can select the wrong 10-year period**. Web research (point A) confirms this is the single biggest reason 만세력 apps disagree. Fix: pick one convention (recommend 세수 throughout 대운), document it (`knowledge/08`), and add a regression test where 만 나이 and 세수 diverge enough to flip the selected period.

### A6. sajupy warning printed to **stdout** corrupts `--format json` output — `pillars.py:255`
Confirmed by direct run: `python3 -m saju_engine --date 1993-12-11 --time 02:45 --utc-offset 5.5 --gender F --format json` emits `Warning: Could not get longitude information, using standard time.\n{...}`. `json.loads(stdout)` raises `JSONDecodeError`. The existing JSON test passes `--longitude` (suppressing the warning) and only substring-checks. Fix: `contextlib.redirect_stdout(io.StringIO())` around `calculate_saju`, re-emit captured warnings to stderr.

### A7. Uncaught `ValueError` from `_validate_input` dumps a traceback — `cli.py:127`
`--date 2200-01-01 ...` → full Python traceback on stderr, exit 1. Argparse-level errors are clean (exit 2) via `_HelpfulParser`, but engine-level validation bypasses it. Fix: wrap `compute_chart` in `try/except ValueError as e: ap.error(str(e))`.

### A8. 3 invented `_WEAK_SPOUSE_PALACE` entries not in `knowledge/11` — `compat.py:506-515`
`knowledge/11-gunghap.md §E3` lists 5 classical "약 일주" (甲申, 丙午, 庚子, 壬寅, 戊戌). The engine adds **庚戌, 甲午, 壬子** — invented, violating CLAUDE.md Ground Rule 1 (every analytical claim must derive from `knowledge/`). Fix: remove the three, or cite a source in `knowledge/11` first.

### A9. Same-Nayin mapped to 상형 (相刑, −4) is invented — `nayin.py:211-212`
`knowledge/11 §C` defines the six relationships for **different** Nayins; same-element → 상대 (+1) per the engine's own element-grammar reduction. The special-case `if nayin_a == nayin_b: return "상형", -4` is invented and penalizes same-Nayin couples by 5 points. Fix: remove the branch; let same-Nayin fall through to 상대 (+1).

### A10. `_compatibility_rows` doctrinal error — generating element marked "Best" for strong charts — `report_data.py:529`
The "Best" branch fires when `elem == favorable OR elem == generating.get(dm_element)`. `generating.get(dm_element)` is the **Resource (인성)** element. For a **strong** DM, 인성 amplifies the imbalance (feeds the already-strong self) and is doctrinally wrong as a partner — yet the code marks it "Best" with reason "supports and nourishes your core energy." Per `knowledge/09` Step 3, 신강 용신 is 식상/재성/관성, never 인성. Also produces two "Best" rows when `favorable != generating`. Fix: split the conditions; read `chart.strength_assessment` rather than assuming generating == favorable.

### A11. Wrong CTA price — `premium_report.py:623`
`"Add a compatibility reading for ₹499"` — but CLAUDE.md and `report_data.TIER_CONFIG` set Compat at **₹1,499**. The ₹499 is the legacy Spark tier (a different product). Misprices the upsell by ₹1,000. Fix: `₹499` → `₹1,499`.

### A12. 釵釧금 transliteration wrong (project-wide) — `nayin.py:139` + `knowledge/11-gunghap.md:307`
Both render 釵釧金 as `최천금`. The standard Sino-Korean reading is **채천금** (釵 = 채, 釧 = 천); `최` is not a valid reading of 釵. Error propagated everywhere Nayin #24 appears. (All other 29 Korean names are correct; 路傍土→노방토 is correct under 두음법칙.) Fix: replace in both files.

### A13. `combinations_6` type annotation arity mismatch — `chart.py:101`
Annotation `List[Tuple[str, str, str, str]]` (4-tuple) but `engine.py:86` appends 5-tuples `(a, c, elem, p1.position, p2.position)` and all consumers unpack 5. `from __future__ import annotations` masks it at runtime, but `typing.get_type_hints(Chart)` raises `NameError` (also `Dict`/`Any` not imported — see D2). Fix: 5-tuple annotation + comment.

### A14. 홍염살 (Red Flame Star) drops one of two valid alternates for 6 stems — `stars.py:181-192`
`knowledge/11-gunghap.md:792-798` lists two valid positions for 丙/丁, 庚/辛, 壬/癸. The engine's `_hongyeom` only matches the single primary, so a 丁 DM with day branch 寅, or a 辛 DM with day branch 戌, register no 홍염. Fix: `HONGYEOM_BRANCHES: Dict[str, List[str]]` with both alternates.

### A15. 종격 (從格) detection missing two preconditions — `patterns.py:206, 209-273`
- **B4a:** Does **not** verify the dominant element is 득령 (in season at 월지). A 60% Earth mass in a Wood month would be flagged 종재, but classical doctrine rejects it (Earth not in season). Add `dominant == BRANCH_ELEMENT[month_branch]` (or generated by it) as a precondition, or downgrade to "possible."
- **B4b:** Accepts `"balanced"` strength verdict; 종격 requires **extreme** weakness. Drop `"balanced"` from the gate (or add an "extreme weak" verdict ≤ −5.0 and require it).

### A16. Broken markdown bold nesting — `prose_fillers.py:1044, 1071`
`f"**Favorable **{fav}** responsiveness** — ..."` → `**Favorable **X** responsiveness**` parses as bold-`Favorable ` + plain `X` + bold-` responsiveness` (split emphasis). Same at line 1071. Fix: `**Favorable {fav} responsiveness**`.

### A17. Inconsistent ten-god language in Business & Launch Timing table — `premium_report.py:1258`
Uses `h.stem_tengod` (Korean, e.g. `편관`) while `theme`/`best` in the same row are English; every other timing table uses `h.stem_tengod_en or h.stem_tengod or "—"` (English-preferred). Fix: align to the English-preferred pattern.

---

## B. Doctrine GAPs (rules in `knowledge/` not implemented, or recognized doctrines missing)

### B1. 반합 (2-of-3 삼합) not detected in natal chart — `engine.py:103-106`
Only full 3-member 삼합 flagged. `knowledge/02-branches.md:66,75` explicitly recognizes 반합 ("partial empowerment"). **Inconsistent**: `compat.py:277` *does* detect 반합 via `_three_harmony_match`. Add `half_harmonies` to `Chart`.

### B2. 방합 (directional harmonies) not detected — `lookup.py`/`engine.py`
`knowledge/02-branches.md:77-79` recognizes 방합 (寅卯辰=Wood, 巳午未=Fire, 申酉戌=Metal, 亥子丑=Water). No table, no detection. (Knowledge file hedges "sometimes counted" — soft GAP.)

### B3. Pairwise 삼형 (punishments) within 寅巳申 / 丑戌未 groups missed — `engine.py:108-113`
Only full 3-member groups + 子卯 detected. A chart with 寅+巳 (no 申) produces `three_punishments: []`. Korean 명리 recognizes the 6 pair punishments (寅巳刑, 巳申刑, 申寅刑, 丑戌刑, 戌未刑, 未丑刑) even without the third member.

### B4. 월운 (monthly luck) uses approximate Gregorian-month boundary, not real 절기 — `sewoon.py:236-270`
`(month - 2) % 12` instead of actual 절기 dates. The code comment acknowledges this. Early-February (pre-입춘) queries can be off by one Saju month. The natal month pillar (from sajupy) is correct; only the monthly-luck overlay is approximate. Fix: reuse `daeun._parse_calendar()` solar-term data.

### B5. No 삼합국 / 삼회국 / 전국 / 편국 / 암합격 / 무칙지 detection in `detect_patterns` — `patterns.py`
`knowledge/02` and `knowledge/03` document 삼합 "highly empowers" an element (directly relevant to 격국/strength). 전국 (all four branches same) and 편국 (three-of-four same) are recognized formations. `Chart.three_harmonies` exists but `detect_patterns` doesn't consume it. 암합격/무칙지 need a knowledge entry first (Ground Rule 1).

### B6. 종자 (從子) subtype missing — `patterns.py:241-249`
Only 종재/종관/종식상/종인 implemented. `knowledge/07-special-formations.md:41` lists 종자 as a rare fifth subtype (or fold into 종식상 — reconcile the knowledge file).

### B7. 화격 (Transformation Grid) doesn't enforce Day Master isolation — `patterns.py:105-156`
Docstring claims "we conservatively require a weak/balanced strength verdict from the caller," but the function **never checks `strength_verdict`**. `knowledge/07:50-53`: 화격 requires the DM to be isolated (not strongly supported). Pass `strength_verdict` in and require `weak`.

### B8. 합화 conditions incomplete — `patterns.py:64-102`
`knowledge/01-stems.md:34-38` lists four conditions; engine omits (a) "weaker stem of the pair should be drained or absent," and (b) breaker-strength check — a breaker only breaks if it's powerful (in season / rooted). `_COMBO_BREAKERS` (line 55-61) is also uncited in `knowledge/`.

### B9. ✅ 신살 coverage limited by `knowledge/` gaps — `stars.py` (DONE)
Engine implements: 도화, 역마, 화개, 천을귀인, 문창귀인, 홍염, 양인, 공망, plus the additional classical stars documented in `knowledge/07-special-formations.md`: 겁살, 재살, 천살, 지살, 연살, 월살, 망신, 장성, 반안, 육해 (the remaining 십이신살), 원진, 귀문관, 백호대살, 괴강, 천덕귀인, 월덕귀인. Terms without a standardized cross-school table (혈각, 관부, 폐문, 고각, 사의, 양록, 음록, 삼기귀인, 학당, 문곡) remain unimplemented per Ground Rule 1.

### B10. 도화/역마/화개 only expose day-branch anchoring; no year-branch alternative — `stars.py:257-264`
`knowledge/07:95-107` documents **both** day-branch (common) and year-branch (alternative school) anchoring. Engine offers no way to select. Add `anchor="day"|"year"` + `year_branch` param. (Web research point H: Korean convention commonly uses 일지, but 연지 is the 고법 — offer both.)

### B11. 양인격 (grid) vs 양인 (star) conflation — `patterns.py:310-313`
Flags `yangin["present"]` if the blade branch appears in **any** of the four branches, conflating the star (anywhere) with the grid (month branch per strict classical; year/day/hour per the looser `knowledge/07:58-60`). Distinguish `yangin_star` from `yangin_grid`.

### B12. 일간합 half-binding ignores month-branch 80% rule — `compat.py:148-200`
`knowledge/11 §A` step 4: if the 간섭 (breaking stem) is in the **month branch** of either partner → "broken," reduce 80%; elsewhere → 50% half-binding. Engine applies a flat 50% regardless of breaker position and never distinguishes "broken" from "half-binding."

### B13. 일간합 합화 in-season (월령/통근) check not computed — `compat.py:148-200`
`knowledge/11 §A` step 3 says to check whether the combined element is in season at either partner's month branch. Engine only mentions it in an [UNCERTAIN] narrative string; never computes it. Emit a flag so the reader can apply their school rule.

### B14. Cross-chart secondary analysis skips 파/형/삼합 — `compat.py:300-331`
Only checks 육합/충/해. `knowledge/11 §B7` requires 합/충/형/파/해 — all five. Add SIX_BREAKS, self/삼형, and THREE_HARMONIES two-of-three.

### B15. 십신 pair table order-sensitive; no canonical-order enforcement — `compat.py:710-721, 747`
`pair = (a_to_b, b_to_a)`; only one direction listed for each good/bad pattern. Swapping A/B (e.g. female as Partner A) makes `(정관, 정인)` → `(정인, 정관)` fall through. CLAUDE.md says A=male for heterosexual pairs but the engine doesn't enforce it, and same-sex pairs have no canonical order. Fix: check `pair in table or pair[::-1] in table`, or enforce canonical order.

### B16. No same-sex / non-hetero handling; no gendered spouse-star mapping — `compat.py` overall
`knowledge/11 §G` Ground Rule 5 specifies gendered mapping (male → 재성 as wife indicator, female → 관성 as husband indicator, per 자평진전). Engine uses the gender-agnostic 적천수/용신 path only. Add `gender_a`/`gender_b` params, apply 자평진전 mapping as secondary check, and annotate same-sex pairs ("동성 커플 — 자평진전 성별 매핑 미적용").

### B17. 궁합 sub-systems missing 진신/용신 호환성 + 시주/월주 비교 — `compat.py` overall
Web research (point I): the 11-item set is a reasonable modern synthesis, not a fixed classical canon. For completeness consider adding **진신/용신 호환성** (sajuclass's #1 item) and explicit **시주/월주 comparison** (4-pillar whole-chart comparison with 월주/시주 weights). Add a `격국 compatibility` sub-system too (not in the 11; user's checklist asks).

### B18. Full Nayin 30×30 relation table not implemented — `nayin.py:159-217`
Module header implies 서전구미록 grounding, but `nayin_relation` reduces all 900 pairs to 5-element grammar. The 60-jiazi→Nayin and 30-Nayin→element tables are complete and correct; the pair-specific 900-cell table is not. Either implement it (data-gathering) or rewrite the docstring to say "element-grammar reduction."

### B19. Skeleton missing Summary (종합) draft — `skeleton.py:299-338`
`knowledge/10-output-template.md:113` requires `## Summary (종합)`. Skeleton has 7 drafts + Sources & Limits but no Summary. (Premium pipeline uses Closing Note instead — document the deliberate omission.)

### B20. auspicious_dates doesn't filter by favorable element as claimed — `premium_report.py:1092-1121`
Docstring says "biased toward the favorable element and away from day-branch clashes," but implementation uses fixed offsets `[7, 21, 42, 63, 84]` with no element lookup, no clash filter, and a single generic note. Comment "roughly every ~18 days" is also wrong (gaps are 14/21/21/21). Implement the filter or rewrite the docstring.

### B21. `--tier` default is legacy `reading`; `compat` rejected — `cli.py:66`
Landing-page tiers per CLAUDE.md are `sample/essential/deep/compat`. CLI default is `reading` (legacy internal) and `--tier compat` is rejected by argparse. CLAUDE.md's tier table is misleading. New clients get the legacy `reading` product by default. Fix: default to `essential` or `deep`; add `compat` to choices (routing to `generate_compat_report`) or document it as API-only.

### B22. `--gender` optional → premium/skeleton silently render empty 대운 table — `cli.py:51` + `engine.py:_build_daeun`
`--format premium` without `--gender` produces the "Major Luck Periods" markdown with header-only and zero rows, no warning. Warn or error when format needs 대운 and gender is omitted.

### B23. Engine luck windows use `datetime.now()`, ignoring CLI `--year/--month/--day` — `engine.py:266,277,287` + `premium_report.py:1198`
"Curren" 세운/월운/일운 and "What This Year Means for You" are pinned to the server clock, not user input. A user running for a past/future reference year gets the wrong window. Thread `reference_year/month/day` through `compute_chart` (default `now()`); have CLI pass them.

### B24. No `is_current` / active flag on `DaeunPeriod` — `daeun_overlay.py`, `chart.py:42-65`
`build_daeun_overlays` populates per-period data but never marks the active period. Only `premium_report.py` derives it (with the A5 age-convention bug). Any other consumer must re-derive. Set `is_current` in `engine.compute_chart` using a correctly-converted reference age.

### B25. Missing birth time crashes with `TypeError` instead of clear `ValueError` — `engine.py:149`, `pillars.py:215`
`hour=None` → `TypeError: '<=' not supported between int and NoneType` rather than a descriptive error. Validate explicitly.

---

## C. CLI / input-validation bugs (silent garbage on bad input)

- **C1. `--utc-offset` not range-validated** — `cli.py:57` / `engine._validate_input`. `--utc-offset 25` is accepted; sajupy applies `25*15=375°` standard longitude (nonsense). Add `if not (-12 <= utc_offset <= 14): raise ValueError`.
- **C2. `--daeun-periods -1` accepted silently** → empty 대운 list, exit 0. Add a positive-int checker.
- **C3. `--month`/`--day` skeleton reference not range-validated** — `--month 13` accepted. Add `choices=range(1,13)` / `1..31`.
- **C4. `--city` geocoding unreliable; no suspicious-longitude warning** — `--city Pallipat` geocodes to 76.33°E (real ~79.32°E, ~3° off → ~12-min solar-time error). `cross_validate.py` bypasses with `--longitude`. Warn if `abs(geocoded_lon - utc_offset*15) > 5°`.
- **C5. `--skeleton-file` deprecated alias silently collides with `--output-file`** — both map to `dest="output_file"`; last wins, no warning. Remove or warn.
- **C6. `engine.py:201-203` silent fallback when city geocoding returns no longitude** — falls back to user `longitude` (may be `None`); `Chart.longitude` ends up `None` silently.

---

## D. Doctrine/heuristic weaknesses (IMPROVEMENTs worth fixing)

- **D1. Seasonal strength double-counted** — `strength.py:135-141`. ✅ Fixed: `month_season_score` removed from `total_score`; `month_stage_score` alone carries the 월령 signal. Thresholds retuned (`strong ≥1.5`, `extreme ≥4.0`). Regression test adjusted.
- **D2. `_MONTH_BRANCH_SEASON` omits 중기/여기 for 巳 and 申** — `strength.py:27-40`. ✅ Fixed: 巳 now includes Metal 0.5 (庚 장생); 申 now includes Earth 0.5 (戊 여기).
- **D3. Asymmetric verdict thresholds (strong ≥2.5, weak ≤−1.5), no "extreme weak"** — `strength.py:144-151`. ✅ Fixed: thresholds symmetrized (`strong ≥1.5`, `weak ≤−1.5`); added `extreme_weak` verdict (`≤−4.0`). `patterns.py` now requires `extreme_weak` for "likely" 종격; `weak` charts surface only as "possible".
- **D4. Balanced 용신 picks "least-present element" — folk heuristic, no doctrinal basis** — `strength.py:168-177`. ✅ Fixed: comment explicitly labels it a folk heuristic; Quick Reference in `premium_report.py` adds a parenthetical note for balanced charts.
- **D5. `drain_score` weighting (authority 1.2 > wealth 1.0 > output 0.8) undocumented** — `strength.py:129-133`. ✅ Fixed: flattened to uniform 1.0 weights; removes undocumented bias.
- **D6. `_STAGE_WEIGHT` sets 묘 (tomb) to 0.0, same as 사/절** — `strength.py:44-57`. ✅ Fixed: 묘 set to 0.3 (stored/hidden qi, weak but non-zero).
- **D7. `_element_strength` hidden-stem weights (2/2/1) ≠ doctrine (1/0.5/0.3)** — `compat.py:391-406`. Align to `knowledge/11 §F:572-573`.
- **D8. `쌍역마` fixed +1 vs doctrine conditional ±2** — `compat.py:921-922`. `knowledge/11 §I:781`: +2 if 양 partner's career benefits, −2 otherwise.
- **D9. "Total weighted score" label misleading** — `compat.py:1090-1094` + `compat_report.py:92`. Composite is `50 + raw_sum` (shifted), not a weighted sum. Rename to "Composite Score (normalized)" to match the cover, or compute a true weighted sum.
- **D10. 4-band + sub-system band thresholds not in doctrine** — `compat.py:126-133, 57-67`. Document in `knowledge/11` or mark [UNCERTAIN] in the report.
- **D11. `_triplet_target` substring matching** — `stars.py:139-144`. Works only because each branch is a unique single Hanja; fragile. Use a tuple/set.
- **D12. `wealth_pattern` borderline doctrinal claim** — `prose_fillers.py:88-103`. "Wealth arrives through channels that activate your favorable element" conflates wealth channel with favorable element; for a weak chart favorable=인성, so "wealth via Resource" is a modern gloss not in `knowledge/05/09`. Reword to reference 재성 ten-gods' rootedness + cite.
- **D13. Medical-leaning "usually the first physical signal"** — `prose_fillers.py:624-626`. "Usually" is stronger than tendency language and pairs a named organ system with probability — edges toward diagnosis (Ground Rule 5). Reword to "a watchpoint in classical Five-Element reading."
- **D14. Missing Hanja on first technical-term use (systematic)** — `prose_fillers.py`, `prose_scaffold.py`, `skeleton.py`. ✅ Fixed: added `hanja_glossary.py` with Korean→Hanja map; `generate_prose_scaffold` and `generate_premium_report` now annotate first occurrence of each technical term across the generated report.
- **D15. Dead `slightly_weak` branches** — `prose_fillers.py:137,322,693,1064,1142`. `strength.py` never emits `slightly_weak`; five fillers check for it; the gentler "Slightly Weak" wording never renders. Either add the verdict band or remove the dead branches.
- **D16. TIER_CONFIG page counts contradict CLAUDE.md** — `report_data.py:38,44` (essential="10–12", deep="20–22"; should be 6–7 and 10–12). Currently unread by renderers but stale; `premium_report.py:708` repeats the wrong "20–22" in a comment.
- **D17. Dead `"compact"` mode in career/relationships builders** — `premium_report.py:446-453, 529-540`. Documented as Essential-tier mode but no tier calls it (essential uses `"essential"`). Wire or delete.
- **D18. `monthly_lucky_dates` approximates months as 30 days** — `premium_report.py:1438`. ✅ Fixed: iterates `(year, month)` tuples so Jan 31 → Feb (not Mar 2) and no drift accumulates.
- **D19. Audio summary section order differs between deep and fullmap** — `premium_report.py:1554 vs 1585`. ✅ Fixed: both `deep` and `fullmap` now place Practical Guidance before the MP3 note, then Closing.
- **D20. `pattern_name` priority unclear when multiple pattern types coexist** — `premium_report.py:197-206`. ✅ Fixed: explicit `elif` chain (special_forms > transformation_grid > regular_grid) in P0.
- **D21. `compat_score` mutates shared `Chart` state for overrides** — `compat.py:1067-1075`. ✅ Fixed: `compat_score` now operates on shallow copies with deep-copied `strength_assessment`; input charts are never mutated. Regression test added.
- **D22. `_classify_flag` token `"해"` too short** — `compat.py:233`. ✅ Fixed: yellow bucket uses `"육해"` only; regression test locks out `해결/해당/해석` misclassification.
- **D23. Two separate `_STEM_PROFILE` dicts drift** — `report_data.py:84` and `prose_scaffold.py:21`. ✅ Fixed: canonical portraits moved to `stem_profiles.py`; both modules import from it.
- **D24. `_career_why` generic fallback vague** — `report_data.py:466`. ✅ Fixed: fallback now references the chart's strongest visible 십신 (Ten God); if none, a generic but non-misleading composition line.
- **D25. `render()` dispatcher unused** — `prose_fillers.py:1236-1284`. ✅ Fixed: removed unused dispatcher and its test.
- **D26. `_COMBO_BREAKERS` uncited + no breaker-strength check** — `patterns.py:55-61`. ✅ Fixed: breaker-stem table documented in `knowledge/07-special-formations.md`; `_breaker_is_powerful()` gates breakers on season/root; signatures threaded through `detect_stem_combinations` and `detect_transformation_grid`.
- **D27. Server-clock `datetime.now()` for "current" luck (cross-cutting)** — unifies A23 / daeun IMP7 / report I4. ✅ Fixed in P4: `reference_date` threaded through all report and engine layers.

---

## E. Test / CI / packaging gaps

- **E1. `validate.py` 0% coverage, no test** — 145 stmts, 0 covered; not collected by pytest (`testpaths=["tests"]`). 11 scenario tests pass manually but drift undetected.
- **E2. `cross_validate.py` (12 known-good cases: 6 candidates + 6 edge cases) not in CI** — no `.github/workflows/`. It's the only curated known-good reference for real candidates. Move cases into `tests/` as parametrized tests, or add a CI workflow/Makefile target.
- **E3. Coverage holes** (pytest-cov): `validate.py` 0%, `__main__.py` 0% (trivial shim), `nayin.py` 74%, `pillars.py` 77%, `compat.py` 80%, `daeun.py` 81%. (Note: `cli.py` shows 0% but is actually exercised — `test_cli.py` uses `subprocess.run`, which pytest-cov can't trace. Measurement artifact, not a real gap.)
- **E4. Missing regression tests for verified BUGs** — recommended new tests:
  1. Birth **after** the term time on a 절기 date — forward + backward `starting_age` (catches A3).
  2. Birth within ±2 hours of a 절기 moment, with solar correction (catches A4).
  3. 만 나이 vs 세수 divergent enough to flip "current 대운" (catches A5).
  4. `--format json` with no `--longitude` → assert `json.loads` succeeds (catches A6).
  5. `--date` far-future / `--utc-offset 25` / `--daeun-periods -1` → assert clean error, not traceback (catches A7, C1, C2).
  6. Same-Nayin pair → assert 상대 (+1), not 상형 (−4) (catches A9).
  7. 甲 DM with 午 month + 庚 월간 → assert 상관격 (from 월지 본기), not 편관격 (catches A1).
- **E5. No `__version__` attribute on the package** — `import saju_engine; saju_engine.__version__` → `AttributeError`. Add `__version__` (or read via `importlib.metadata.version`).
- **E6. `chart.py` missing `Dict`/`Any` imports** — `from __future__ import annotations` masks it at runtime, but `typing.get_type_hints(Chart.to_dict)` raises `NameError`. Add to `from typing import …`.

---

## F. What's verified correct (do not "fix")

- All 10 stems (element + 음양), 12 branches (element + 음양 + animal + month + hour).
- HIDDEN_STEMS for all 12 branches (본기/중기/여기 designations, incl. single-stem 子/卯/酉).
- 십신 full 10×10 천간 table + 10×12 지지 table — 0 mismatches vs `knowledge/05`.
- 12운성 full 10×12 table — 0 mismatches vs `knowledge/06`, incl. non-intuitive yin-stem backward cases (乙@午, 丁@酉, 己@酉, 辛@子, 癸@卯).
- 천간합 (5 pairs + 화기 elements), 육합, 육충, 삼합, 자형, 육해, 육파 — all correct + bidirectional.
- THREE_PUNISHMENTS groups (寅巳申, 丑戌未, 子卯) — group membership correct (pairwise detection is the gap, B3).
- JIAZI_CYCLE (60-cycle) construction; 五虎遁 (10 stems); 五鼠遁 (10 stems); `_LONG_LIFE_START` (12운성 장생 starts + direction).
- `daeun_direction` (양년+남 / 음년+여 → forward; else backward) — matches `knowledge/08`.
- 대운 천간/지지 derivation via 60-cycle from 월주 (canonical Korean method; NOT 五虎遁, which is for 월주-from-연주 only) — correct.
- 세운 입춘 cutoff (via sajupy `year_pillar` lookup) — correct, not Jan 1 / lunar new year.
- 월운 primary path (sajupy `month_pillar` with 절기-day cutoff); 일운 60-cycle anchored at 1900-01-01 = 甲戌 (index 10) — verified.
- Solar-time / longitude correction for natal pillars; solar-rollback re-applies the 자시 convention correctly.
- 23:00 자시 convention handling — Korean 야자시 (current-day 일주) and Chinese 조자시 (next-day) both correct, including hour-stem via 五鼠遁. `zi_time_type` label set correctly.
- 납음 60-jiazi → 30 Nayin pairs → elements: complete and correct for all 30 pairs (modulo the 釵釧금 romanization A12).
- Compat: 5 천간합 pairs, 5 간섭 pairs, 6 육합/충/해/파, 4 삼합, day-branch primary scoring, spouse-virtue (용신+3/희신+2/기신−3), 4 good + 3 bad 십신 pair pairs, star overlays (쌍도화/도화스쳐/귀인배우/쌍화개/쌍양인/쌍홍염/홍양교차), 음양 polarity — all match `knowledge/11`. Demo Pawan×Sruthi still yields 64/100 Mixed.
- Tier gating in `premium_report.py` correctly includes/excludes sections per CLAUDE.md for sample/essential/deep/spark/reading/fullmap + aliases.
- No fatalistic language in prose — consistent tendency framing ("tends to", "may", "likely").
- No bare `except:`/`except Exception: pass` silent-failure patterns in engine/cli/validate.
- Orchestration order in `engine.py` is correct: validate → pillars → chart → ten_gods → twelve_stages → branch_relationships → daeun → stars → strength → patterns → daeun_overlay → sewoon/woon/ilwoon.

---

## G. Prioritized fix roadmap

> **Progress (updated 2026-07-05):** ✅ P0 fully done. ✅ P1 fully done. ✅ P2 fully done. ✅ P3 fully done. ✅ P4 fully done. ✅ P5 fully done. Suite: 502 passed.

**P0 — client-facing correctness / crashes (do first):** ✅ DONE
1. ✅ A6 (JSON stdout corruption) — `contextlib.redirect_stdout` around `calculate_saju` in `pillars.py`; warning re-emitted to stderr.
2. ✅ A11 (price ₹499 → ₹1,499 in `premium_report.py:623`) + ✅ A12 (채천금 in `nayin.py:139` + `knowledge/11:307`) + ✅ A16 (markdown bold in `prose_fillers.py:1044,1071`) + ✅ A17 (ten-god language in `premium_report.py:1258`).
3. ✅ A7 (ValueError → `ap.error` in `cli.py`) + ✅ C1–C3 (utc-offset / daun-periods / month-day range checks via `_utc_offset_float` / `_positive_int` / `_month_int` / `_day_int` in `cli.py`).
4. ✅ A5 (만 나이 vs 세수) — added `daeun.saju_age()` (입춘-based 세수); wired into `premium_report.py` (2 sites) + `prose_scaffold.py`; regression tests added. (Moved from P1; done here.)

Also done in P0: A13 (`combinations_6` 5-tuple annotation in `chart.py`), B21 (`--tier` default `essential` in `cli.py`), B22 (`--gender` required for premium/skeleton), E5 (`__version__` in `__init__.py`), E6 (`Any, Dict` imports in `chart.py`), D16 (TIER_CONFIG page counts `essential 6–7` / `deep 10–12` in `report_data.py` + `premium_report.py:708`).

**P1 — doctrinal correctness (affects every reading):** ✅ DONE
5. ✅ A1 (정격 from 월지 투출) — added `_grid_stem_by_tuochul()` in `patterns.py` (본기→중기→여기, first 투출 wins, 본기 fallback); `knowledge/07 §Part 1` reworded to document the classical 투출 method + minority 월간 school; 3 tests in `test_patterns.py`.
6. ✅ A2 (희신 vs `knowledge/03`) — documented BOTH schools in `knowledge/03` (strict classical "generates 용신" vs modern Korean "secondary favorable"); `strength.py` annotated with the convention (modern for strong/weak, strict classical for balanced); 2 test comments updated. Did NOT blindly swap (strict classical yields the 기신 element for strong/weak — paradox; see knowledge/03 note).
7. ✅ A10 (`_compatibility_rows` in `report_data.py`) — rewrote verdict-aware: favorable=single "Best"; strong DM → Resource/Self="Watch", drain group="Good"; weak DM → Resource/Self="Good", drain group="Watch"; balanced → 희신 (generates 용신)="Good". Added `wealth` (재성) relation. `_ReportContext.verdict` added; 3 tests in `test_premium_report.py`.
8. ✅ A15 (종격 득령 + extreme-weak) — `detect_special_forms` in `patterns.py`: gate drops "balanced" from "likely" (balanced only surfaces as "possible" at ≥60% share); added `month_branch` param + 득령 check (dominant == month-branch element or generated by it, else "possible"); 2 regression tests.
9. ✅ A3 + A4 (대운 sub-day precision) — `_term_boundary_datetimes` + `starting_age` now moment-level (prev = last 절기 ≤ birth moment, next = first 절기 ≥ birth moment); `compute_daeun` takes `hour, minute`; `_build_daeun` in `engine.py` plumbs solar-corrected time (`chart.solar_correction['solar_time']`) or `birth_time`. Audit repro `starting_age(2024,2,4,'forward',23,59)` now returns 9 (was 0). `test_daeun.py` term tests updated + exact-moment test added.

**P2 — compat engine doctrine gaps:** ✅ DONE
10. ✅ A8 + A9 (invented `_WEAK_SPOUSE_PALACE` entries 庚戌/甲午/壬子在 `compat.py:506-515` + same-Nayin 상형 in `nayin.py:211-212`) — removed invented rules per Ground Rule 1.
11. ✅ B12 + B13 + B14 (일간합 month-branch 80% / 합화 in-season / cross-chart 파·형·삼합 in `compat.py`).
12. ✅ B15 + B16 (십신 pair symmetry + same-sex / gendered mapping).
13. ✅ A14 (홍염 alternates in `stars.py:181-192` — `HONGYEOM_BRANCHES: Dict[str, List[str]]` with both alternates per `knowledge/11:792-798`).

P2 added regression tests in `tests/test_compat.py`, `tests/test_nayin.py`, and `tests/test_stars.py`; suite rose from 448 to 458 passing.

**P3 — missing doctrines (knowledge-first per Ground Rule 1):** ✅ DONE
14. ✅ B1–B3 (반합 / 방합 / pairwise 삼형) — natal detection in `engine.py` via new `half_harmonies`, `directional_harmonies`, and pairwise `three_punishments` entries.
15. ✅ B4 (월운 절기 boundary) — `current_woon_window` now steps by calendar months and delegates to `_monthly_pillar_for_date`, which uses the real solar-term lookup.
16. ✅ B5–B8 (삼합국/전국/편국, 종자, 화격 isolation, 합화 conditions) — `detect_structural_notes` added 전국/편국/삼합국; `종자` alias added for output-following forms; `detect_transformation_grid` now requires a weak Day Master when `strength_verdict` is supplied.
17. ⏳ B9–B11 (신살 knowledge entries + anchoring + 양인격 vs 양인) — B10 (year-branch anchor for 도화/역마/화개) ✅ and B11 (양인_star vs 양인_grid split) ✅. **B9 (additional classical 신살 entries) remains open because `knowledge/07` only documents the 8 already-implemented stars plus a vague 귀문관살 entry — Ground Rule 1 blocks adding new tables until knowledge entries are authored first.**

**P4 — CLI/UX + CI:** ✅ DONE
18. ✅ B23 + B24 (reference date threading + active major-luck flag) — `compute_chart` now accepts `reference_year/month/day` (defaults to today), stores `chart.reference_date`, `current_age`, and `current_daeun`; all `datetime.now()` calls in `premium_report.py`, `prose_scaffold.py`, `prose_fillers.py`, `skeleton.py`, and `cli.py` use the chart's reference date; CLI `--year/--month/--day` are passed into `compute_chart` for consistent skeleton/premium output. Regression tests in `tests/test_engine.py`.
19. ✅ C4–C6 (city geocoding warning, alias collision, silent longitude fallback in `pillars.py`) — `_warn_if_suspicious_longitude()` warns when geocoded longitude differs >5° from standard meridian or user longitude; `--skeleton-file` emits a deprecation warning; fallback longitude is patched into `solar_correction` when geocoding returns none.
20. ✅ E1 + E2 (`cross_validate.py` scenarios migrated to `tests/test_cross_validate.py`; `.github/workflows/ci.yml` runs pytest on Python 3.10/3.11/3.12).
21. ✅ E4 (regression tests for reference-date threading, geocoding warnings, and CLI hardening added to `tests/test_engine.py` and `tests/test_cli.py`).

**P5 — polish (D1–D27, E5–E6):** ✅ DONE (E5/E6 done in P0)
22. ✅ Strength heuristic tightening (D1–D6), compat weights/labels (D7–D10), prose Hanja + dead-branch cleanup (D14–D17), thread-safety (D21), `__version__` (E5), type imports (E6).
23. ✅ Remaining D18–D20, D22–D27 completed. All open D1–D27 items resolved.

---

*Audit conducted 2026-07-05 by 7 parallel agents + direct source verification. Every BUG-level finding above was re-checked against the source before inclusion. Roadmap progress markers and the ✅/⏳ status above were added during the fix pass (2026-07-05). Resume at P2.*