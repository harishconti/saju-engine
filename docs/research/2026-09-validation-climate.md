# Validation Research — W5 Climate (조후, 調候)

**Workstream:** W5 · **Date:** 2026-09-13 · **Subsystem:** `src/saju_engine/climate.py`
**Rule base:** `knowledge/17-climate-method.md`, `knowledge/09-interpretation-method.md` Step 3
**Fixture set:** `tests/validation/fixtures/climate.json` (30 checks — 16 band + 14 merge)

---

## 1. What the engine implements, exactly

`assess_climate(month_branch)` is a pure function of the month **branch** (12
lines of classifier, `src/saju_engine/climate.py`):

| Band | Month branches | `climate_favorable` | `climate_supporting` |
|---|---|---|---|
| hot | 巳 午 未 | Water | Metal |
| cold | 亥 子 丑 | Fire | Wood |
| temperate | everything else | `None` | `None` |

This mirrors `knowledge/17-climate-method.md:43-47` line for line, including the
희신 column (supporting element = the element that generates the climate
element, `_GENERATED_BY` being the inverse of the generating cycle).

Two properties matter for everything below:

- **It is branch-only.** The Day-Master stem is never an input. There is no
  per-stem × per-month table — the file's own Scope Note
  (`knowledge/17-climate-method.md:20-39`) records that no 궁통보감 source text
  was available to build one, so the engine implements the *quartet-level*
  seasonal rule only.
- **It is a cross-check, not a decider.** `climate.py` returns a band and two
  elements; the merge in `src/saju_engine/yongsin.py` decides whether that
  output actually overrides 억부. §5 measures that merge.

---

## 2. The classical organizing principle (sourced)

### The seasonal-want rule

The climate principle is stated as a general law before it is stated as a table:
*"추우면 덥게 하고, 더우면 식혀준다 (寒者熱之，熱者寒之)"*
([cantian.ai 한난조습 해설](https://www.cantian.ai/wiki/ko/other_words_explanations/tiaohou/)).
Classically this is grounded in the 적천수 (滴天髓) couplet — *"天道有寒暖，
发育万物 … 地道有燥湿"* — which the same page quotes as the doctrinal basis for
reading climate at all.

The two summer/winter poles are the engine's two bands, and the sources give
them without qualification:

> 北方阴极而生寒，寒生水。南方阳极而生热，热生火。
> — 窮通寶鑑, quoted at [cantian.ai](https://www.cantian.ai/wiki/ko/other_words_explanations/tiaohou/)

so 亥子丑 (winter, 寒) want **Fire** and 巳午未 (summer, 熱) want **Water**.
This is exactly the engine's `_COLD_BRANCHES` / `_HOT_BRANCHES` split and its
`Fire` / `Water` prescriptions. Also quoted there: a secondary 窮通寶鑑 line,
*"寒金不生水，寒水不生木"* — cold metal cannot generate water, cold water
cannot generate wood — i.e. in a cold chart the *generating chain itself stalls*
until Fire is supplied. That is the mechanism behind the 희신 column: Metal
accompanies the Water prescription in hot months, Wood accompanies Fire in cold
months, because the remedy has to be *fed*.

### The 궁통보감 structure — and what "120-cell" actually names

The classical text keys its prescriptions jointly to the **천간 (Day-Master stem)
and the 절기월 (solar-term month)**, not to a three- or two-band reduction. The
[OpenFate Wiki 궁통보감 entry](https://wiki.openfate.ai/ko/bazi/classics-schools-cases/qiong-tong-bao-jian)
(편집 검토 2026-07-23) describes it as a work organizing
*"일간과 절기월을 기준으로 한랭·온열·건조·습윤과 후보 조후 기능"*, and its source
note calls the tradition *"천간과 출생월을 기준으로 구성되어"* (Chinese-language
note: *"天干按月分論"*) — organized stem-by-month.

**Honest limit on this citation:** that page does **not** print a grid, never
says "120 cells," and gives no 10 × 12 count. The 120-cell figure is a *derived*
description (10 천간 × 12 지지) of a stem-by-month organization, not a number any
source I reached states. §4 treats the gap accordingly.

The same page supplies the second half of the organizing principle, and it is
the half the engine does **not** implement:

- **월령 is the primary basis.** The page's summary box lists
  *"핵심 입력: 일간과 정확한 절기월"*, and requires the month be fixed
  reproducibly — *"재현 가능한 절기 경계로 월령을 정하고 음력월이나 대략적
  계절로 대신하지 않습니다"* — an explicit warning against the approximate
  season-reading the engine's three-band model performs.
- **The text is a starting point, not a verdict.** *"해당 조문은 시작점이며 전체
  뿌리, 투간, 제어와 흐름을 추가로 봅니다."* The candidate element must be
  validated against the whole chart — and, pointedly for a client product,
  *"조후에서 필요한 오행은 곧바로 격국·억부 용신이나 건강·음식·거주 처방이 아닙니다"*
  (the element climate wants is not automatically a 용신, nor a health, diet, or
  residence prescription).

The genealogy is also worth recording because it fixes what "궁통보감" denotes:
compiled by 余春台 from the earlier 《欄江網》, later annotated by 徐樂吾 through
《造化元钥》 (per [cantian.ai](https://www.cantian.ai/wiki/ko/other_words_explanations/tiaohou/)).
The OpenFate page cites only 《窮通寶鑑》 and 《滴天髓》 and gives **no** 欄江網 /
徐樂吾 / 余春台 genealogy — a source disagreement about the text's lineage, not
about its content, noted here so a later reader does not treat either account as
settled.

---

## 3. Resolution of the 辰戌丑未 `[UNCERTAIN]` flag

`knowledge/17-climate-method.md:49-54` flags the four earth-storage months as a
simplification, with a parenthetical illustration, and marks the finer
distinction `[UNCERTAIN]` "pending a fuller source."

**The flag is resolved: the classical treatment is the 寒暖燥濕 (hán-nuǎn-zào-shī)
four-way reading, and it is a genuinely finer distinction than the three bands.**
The table below is from
[cantian.ai](https://www.cantian.ai/wiki/ko/other_words_explanations/tiaohou/)
(directly reviewed, 2026-09-13):

| Climate state | Month branches | Remedy |
|---|---|---|
| 寒 (cold) | 亥 子 | 火, esp. 丙 |
| 暖/熱 (hot) | 巳 午 | 水, esp. 壬 |
| **燥 (dry)** | **戌 未** | 水, esp. 癸 |
| **濕 (damp)** | **辰 丑** | 火, 丙 or 丁 |

OpenFate's [사계절 토와 월령](https://wiki.openfate.ai/ko/bazi/five-elements/seasonal-earth-and-the-month-command)
(편집 검토 2026-07-22) independently corroborates that the four are *not* one
class — *"네 지지는 모두 토로 분류되지만 습도, 온도, 장간, 계절 위치와 생극
기능이 다릅니다"* — and its section 진·미·술·축을 개별 월로 읽는다 refuses to lump
them (*"토를 하나로 묶지 않고 각 월의 계절 전환, 장간, 한열조습, 통근을 판독하는
기준을 설명합니다"*). It frames the split as 寒濕 (辰·丑) vs 溫燥 (未·戌), matching
cantian, but gives **no** element prescriptions and does **not** group them by
seasonal quartet. A 庚金-specific classical line, *"丑辰 습토에 왕생, 戌未 조토에는
부스러짐"*, is surfaced by search via
[SajuGallery](https://www.sajugallery.com/p/blog-page_01.html) as a further
corroboration of the damp/dry pairing — **provenance caveat: that page was not
directly reviewed**; the pairing itself rests on the two directly-reviewed
sources above.

### What this means for the engine — branch by branch

Comparing the source table against the engine's bands:

| Branch | Engine | Source (寒暖燥濕) | Agree? |
|---|---|---|---|
| 亥 | cold → Fire | 寒 → 火 | ✅ |
| 子 | cold → Fire | 寒 → 火 | ✅ |
| 丑 | cold → Fire | 濕 → 火 | ✅ |
| 巳 | hot → Water | 熱 → 水 | ✅ |
| 午 | hot → Water | 熱 → 水 | ✅ |
| 未 | hot → Water | 燥 → 水 | ✅ |
| 寅 卯 申 酉 | temperate → None | (not in the four states) | ✅ |
| **辰** | **temperate → None** | **濕 → 火** | ❌ |
| **戌** | **temperate → None** | **燥 → 水** | ❌ |

**The simplification is material for 2 of 12 branches — 辰 and 戌 — not for 丑 and
未.** This *reverses* the conclusion the plan template reached, and the reason is
worth stating: the plan inferred the divergent set from the knowledge file's own
parenthetical aside, which pairs 辰戌 / 丑未. The classical table pairs
**辰丑 / 戌未** instead. Because the engine bands 丑 with 亥子 (→Fire) and 未 with
巳午 (→Water), it *coincidentally lands on the source's element* for both — so 丑
and 未 agree despite being grouped differently.

Note the **direction** of the divergence precisely: it is confined to *whether an
override fires at all* for 辰 and 戌, never to *which* element. Where the engine
does prescribe, it prescribes what the source prescribes, everywhere, for all
ten branches covered. There is no element-level disagreement in the subsystem.

**Convergent validity.** The convergence on 丑 and 未 is worth more than a match
would be: the source groups 丑 with 辰 (both 濕) while the engine groups 丑 with
亥子 (both cold); the source groups 未 with 戌 (both 燥) while the engine groups
未 with 巳午 (both hot). Two independent groupings, same prescription — evidence
the Fire-for-丑 / Water-for-未 reading is robust to how the earth branches are
sliced, rather than an artifact of one grouping.

### A documentation imprecision, separate from the engine

`knowledge/17-climate-method.md:51-52` illustrates the nuance as *"辰戌 carry more
dryness, 丑未 carry more dampness."* Measured against the source table above,
that illustration is correct for 戌 (dry) and 丑 (damp) and **inverted for 辰
(dry vs. the source's damp) and 未 (damp vs. the source's dry)**. This is a
*wording* defect in a parenthetical aside, not engine behaviour — the engine
reads the band table at lines 43-47 and never consults the aside. Logged here as
a knowledge-file imprecision, not fixed (validation-only campaign).

### Disposition

**INTERPRETATION (documented), not FAIL.** The engine faithfully implements the
rule `knowledge/17-climate-method.md` states, and the file itself already flags
the rule as a simplification. The finding concerns the rule's *fidelity to the
fuller classical treatment*, not the engine's adherence to its own stated rule —
which is the distinction the campaign's three-status scheme is built to make.
Coverage gap re-logged in §4; not fixed in a validation-only campaign.

---

## 4. The 120-cell table gap (Plan 4 T3 handoff)

`docs/research/2026-09-validation-yongsin.md` §5 logged the missing full 궁통보감
table. Restated here with both halves of the gap, because §2 above split it:

1. **The stem dimension is entirely absent.** The engine's climate input is the
   month branch alone; the classical text is organized stem-by-month (§2), so
   two charts sharing a month branch but differing in Day-Master stem receive
   identical climate treatment from the engine and *not* identical treatment in
   the classical text.
2. **The "120-cell" figure is a derived description, not a sourced one.** No
   source reached in this workstream states a cell count (§2); it names a
   stem-by-month organization. Any future estimate of "how much of the table is
   covered" must not quote 120 as if a source said it.

**Disposition: unimplemented, logged, not fixed.** Same as W4. Building it would
require source text the project does not have (`knowledge/17-climate-method.md`
Scope Note), and this campaign is validation-only.

---

## 5. 조후 vs 억부 priority — a live engine-behavior finding

### The engine's rule, as documented

`knowledge/17-climate-method.md:56-70` ("How This Combines With 억부"): when the
verdict is `balanced`, 조후 is the classical tie-breaker; when the verdict is
strong or weak, **억부 stays authoritative and 조후 is only a cross-check**; a
reader override wins outright. So 조후 decides the headline element only behind a
`balanced` verdict.

### What the sources actually say

The plan's premise was that classical sources rank 조후 *above* 억부
unconditionally, which would make the engine's ordering a deviation. **That
premise is not supported.** The sourced position is that there is no fixed order:

> 조후와 부억에는 명식을 떠난 고정 순서가 없습니다.
> — [OpenFate, 조후와 부억 중 무엇을 우선할까](https://wiki.openfate.ai/ko/bazi/useful-gods-climate/climate-vs-strength-priority)

The same page conditions the choice on whether the climate is *blocking*:

> 극단적 기후가 다른 기능을 막으면 조후가 전제가 되고, 기후가 이미 운용 가능하면
> 부억이 먼저일 수 있습니다.
> — [ibid.](https://wiki.openfate.ai/ko/bazi/useful-gods-climate/climate-vs-strength-priority)

and 두루미사주 states the same conditional as the common view:

> 일반적으로 사주가 너무 차거나 너무 더우면 조후를 우선하고, 그렇지 않으면 억부를
> 우선하는 견해가 많습니다.
> — [두루미사주, 억부용신](https://www.durumisaju.com/dict/yongshin/eokbu)

This corroborates W4's independent finding in
`docs/research/2026-09-validation-yongsin.md` §3 rather than contradicting it:
the "조후 always outranks 억부" claim is a **popular simplification**, not the
sourced doctrine. (A search-surfaced 삼명통회 line to the same effect —
*"沒有固定永遠先調候或先扶抑的單一規則"* — was **not directly reviewed** and is
recorded as secondary only.)

### The precise finding

The sources condition priority on **climate extremeness** ("너무 차거나 너무
더우면", "극단적 기후가 … 막으면"). The engine conditions it on the **strength
verdict** (`balanced`). These are different tests, and the engine's is the
*narrower* gate: a chart in an extreme 巳午未 or 亥子丑 month whose Day Master is
decisively strong or weak will have 조후 suppressed by the engine in a case where
the majority sourced position would let it govern.

### Disposition — recorded, engine unchanged

**No engine change.** The 억부-authoritative position is itself defensible, is
what `knowledge/17-climate-method.md` documents, and this campaign is
validation-only. Flagged as a **campaign-close product decision**: whether to
widen the 조후 gate from verdict-conditioned to climate-extremeness-conditioned.
Any such change would move published client outputs (the 8 `climate_agrees:
false` rows below are exactly the affected population) and must not be made
inside a validation pass.

### The measured matrix (from `climate.json`, T2)

Five rows show 억부 deciding the headline against a genuinely differing 조후
candidate:

| fixture | band | verdict | 억부 resolution | 조후 wanted |
|---|---|---|---|---|
| `gurumoorthy-published` | hot | strong | Metal (strong-dm-drain) | Water |
| `weak-cold-priority` | cold | weak | Metal (weak-dm-support) | Fire |
| `hot-weak-priority` | hot | weak | Metal (weak-dm-support) | Water |
| `cold-strong-priority` | cold | strong | Water (strong-dm-drain) | Fire |
| `cold-strong-scan` | cold | strong | Wood (strong-dm-drain) | Fire |

Four rows show 조후 deciding the headline — every one of them behind a `balanced`
verdict, which is the engine's documented gate:

| fixture | band | verdict | resolution |
|---|---|---|---|
| `harish-published` | hot | balanced | Water (climate-balanced); raw candidate differed |
| `vishnu-priya-published` | hot | balanced | Water (climate-balanced); raw candidate agreed |
| `sruthi-published` | cold | balanced | Fire (climate-balanced); raw candidate differed |
| `mahesh-published` | cold | balanced | Fire (climate-balanced); raw candidate differed |

`pawan-published` is the **temperate control**: `balanced` verdict, but band
`temperate`, so 조후 contributes nothing and the `balanced-heuristic` path
resolves Wood. It is the fixture that proves 조후 does not over-fire on temperate
months — the one case where a balanced verdict plus a non-firing band must not
invent an override.

**`climate_agrees` semantics, stated precisely** (it is easy to misread): the flag
compares the *raw 억부 candidate* to the climate element — it does **not** report
who won. `False` therefore arises from two opposite situations: (a) 억부 won the
headline and 조후 disagreed (`gurumoorthy-published`, `weak-cold-priority`,
`hot-weak-priority`, `cold-strong-priority`, `cold-strong-scan`), and (b) 조후 won
the headline *by correcting* a disagreeing raw candidate (`harish-published`,
`sruthi-published`, `mahesh-published`). Only
`vishnu-priya-published` (조후 won, raw candidate already agreed) and the two
`*-agree` synthetics sit on the `True` side.

---

## 6. Fixture coverage and divergences

**30 checks — 30 PASS, 0 INTERPRETATION, 0 FAIL.** Measured 2026-09-13.

| Layer | Count | Composition |
|---|---|---|
| band (`probe="band"`) | 16 | all 12 month branches + 4 defensive edges |
| merge (`probe="merge"`) | 14 | all 9 band × verdict-class cells |

The 4 defensive edges are `""`, `"甲"`, `"Z"`, `"子時"` — all fall through to
temperate/`None`. The pointed one is `"子時"`: a 子 *hour label* supplied where a
子 *month branch* is expected must not fire the cold override. These pin
defensive behaviour, not doctrine.

The merge corpus fills every cell of {hot, cold, temperate} × {strong, weak,
balanced}, and non-temperate rows cover both `climate_agrees` polarities
(True: `vishnu-priya-published`, `weak-cold-agree`, `hot-weak-agree`; False: 8
rows). `_VERDICT_CLASS` folds all **five** engine verdicts (`strength.py`
emits `strong`/`extreme`/`weak`/`extreme_weak`/`balanced`), so a future chart
landing on `extreme` classifies instead of erroring — and
`test_verdict_enum_is_fully_mapped` fails loudly if `strength.py` grows a sixth.

### The 3 guarded rows PASS, and the plan could not have both

Three rows carry the `documented_interpretation` guard — `sruthi-published`,
`pawan-published`, `mahesh-published`, the W4 published divergences, here
attributed to their band/verdict cause. The plan predicted these would render
`INTERPRETATION`; they render `PASS`.

**Root cause, settled from source:** in the checker,
`INTERPRETATION` is reachable *only on a mismatch* —
`documented_interpretation` is a **guard** ("if this diverges, don't fail the
suite"), not a verdict ("this must diverge"). The three rows assert the
**engine's** values (Fire / Wood / Fire), and the T2 re-probe reproduced those
exactly, so they match and PASS. The published divergences are recorded in each
row's `source` prose. W5 therefore contributes **0** INTERPRETATION rows; the
CLI's 3 INTERPRETATION remain W4's. No fixture content was changed — Step 1's
verified re-probe outranks Step 5's prediction, and two of the three
(`pawan-published`, `mahesh-published`) are marked "STALE CHART pre-ya-ja-si
fix" in their own source strings, so asserting their published values would
enshrine a comparison the campaign already knows is obsolete.

The divergence record stays machine-checked where it belongs, in
`tests/validation/fixtures/yongsin.json`.

### Null-skip blind spot

Temperate rows carry `climate_favorable: null`, and a null `expected` sub-field
means *skip* — so the fixture **cannot** prove a temperate band yields no climate
element. That property is asserted directly against `climate.assess_climate()` by
`test_temperate_rows_have_no_climate_element`, the only place it is testable.

---

## 7. Sources

Directly reviewed (fetched 2026-09-13/14):

1. Cantian AI — 사주 조후 이론 완전 해설 (한난조습 표; 滴天髓 · 窮通寶鑑 quotes;
   欄江網 / 徐樂吾 / 余春台 genealogy) —
   <https://www.cantian.ai/wiki/ko/other_words_explanations/tiaohou/>
2. OpenFate Wiki — 궁통보감(窮通寶鑑): 일간·월령·조후 안내 (편집 검토 2026-07-23) —
   <https://wiki.openfate.ai/ko/bazi/classics-schools-cases/qiong-tong-bao-jian>
3. OpenFate Wiki — 사계절 토와 월령 (편집 검토 2026-07-22) —
   <https://wiki.openfate.ai/ko/bazi/five-elements/seasonal-earth-and-the-month-command>
4. OpenFate Wiki — 조후와 부억 중 무엇을 우선할까 —
   <https://wiki.openfate.ai/ko/bazi/useful-gods-climate/climate-vs-strength-priority>

Carried forward from W4 (`docs/research/2026-09-validation-yongsin.md`, quoted
verbatim there):

5. 두루미사주 — 억부용신(抑扶用神)이란? — <https://www.durumisaju.com/dict/yongshin/eokbu>
6. 사자사주 — 용신이란? 억부용신부터 조후용신까지 — <https://www.sazasaju.com/blog/yongsin-guide>
7. 현인사주 — 용신 찾는 법 — <https://www.hyuninsaju.com/blog/basics/yongsin-finding>
8. 진영아·최정준 (2022), DBpia 학술논문 — <https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11275955>

Surfaced by search, **not directly reviewed** (recorded as secondary
corroboration only; no load-bearing claim rests on these):

9. SajuGallery — 궁통보감 (10-stem month-by-month 용신 표) —
   <https://www.sajugallery.com/p/blog-page_01.html>
10. OpenFate Wiki — 조후 용신 뜻과 보는 법: 한난조습·판단 순서 —
    <https://wiki.openfate.ai/ko/bazi/useful-gods-climate/climate-regulating-useful-god>

**Ground-rule note.** Where the classical position is genuinely contested or
unreached, this document says so rather than asserting it — specifically: the
120-cell count (§2, §4), the 조후/억부 priority ordering (§5), and the
辰/未 damp-dry attribution in `knowledge/17-climate-method.md:51-52` (§3) all
carry an explicit provenance or disagreement note. No claim in §2–§5 is stated
as established doctrine beyond what its cited source supports.
