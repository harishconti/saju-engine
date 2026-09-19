# 11 · Compatibility (궁합, 宮合 / 合婚)

This file is the classical Korean 명리 reference for **marriage compatibility** (궁합, 宮合) between two four-pillar charts. It is grounded in the **Korean traditional 명리 school** — 적천수 (滴天髓, 任鐵樵 주석), 연해자평 (淵海子平), 궁통보감 (窮通寶鑑), 명리정종 (命理正宗), 자평진전 (子平眞詮) — and the modern Korean Myeongri (명리) reading tradition. It **excludes** mainland Chinese BaZi folk-algorithm layers, Zi Wei Dou Shu, Western astrology, and the pop "12-animal-zodiac" Korean 점괘 style.

## Ground Rules for Compatibility Readings

1. **No single factor decides 궁합.** Classical texts weight day-branch interaction above all else, but every other layer is checked. A perfect 일지 육합 with catastrophic 십신 cross can still fail.
2. **궁 is greater than 성.** *(see `07-special-formations.md`, Part 2)* Following the academic survey of divorce cases in Korea (남기동·김만태 2018, KCI ART002338687), the **spouse palace (궁, the day branch)** outweighs the **spouse star (성, the 십신 of the spouse)** in determining stability.
3. **간여지동 (干與支同) is the strongest single red flag** — when the day branch shares the same element as the day master, classical 명리 flags the conjugal bond as **the most unstable** configuration.
4. **Birth-time accuracy is mandatory.** Wrong hour → wrong day pillar → every 결론 below invalid. Confirm both charts before reading.
5. **Day Master gender convention for spouse-star mapping:**
   - **Male querent (남성)**: 재성 (wealth star) = wife indicator (편재 = secondary / later partner, 정재 = primary / first partner in traditional reading).
   - **Female querent (여성)**: 관성 (officer star) = husband indicator (정관 = primary husband, 편관 = 칠살 = second / non-conventional partner).
   - Modern Korean Myeongri also accepts **부성용신론 (夫星用神論)** — 임철초's position that the husband is not only 관성 but also the woman's 용신 in her chart (김우정 2025, J Korean Hist of Han Thought, p.305). For our engine, the spouse is **primarily 관성/재성**, with the 용신 map as a secondary cross-check.
6. **모든 분석은 양 사주 전체의 합 (combined chart) + 개별 사주의 통합으로 봅니다.** Never read only day pillars in isolation.
7. **Mark [UNCERTAIN] where schools disagree** — the engine output must keep the uncertainty tag visible to the client.

## Composite Weight (총점 100 — classical Korean Myeongri balance)

The following weighting reflects the **consensus of the Korean classical lineage** (권인성·곽임성·정봉재·송기영 schools), tempered by the academic empirical studies of divorce correlation (KCI 2018, 2023). Individual schools may weight differently; the engine should expose the breakdown so the client sees the composite.

| Sub-system | Classical label | Default weight | Red flag? | Notes |
|---|---|---|---|---|
| **B** Day-branch 합·충·형·파·해 (spouse palace interaction) | 일지 합충 | **30** | Yes — 일지 육충 is a hard red flag | Highest classical priority |
| **C** Nayin (납음) compatibility | 납음 궁합 | **5** | No | Soft indicator, often disputed |
| **A** Day-stem 천간합 (일간합) | 일간합 | **12** | Soft | Attraction, but secondary |
| **E** Day-pillar (일주) classification | 일주 궁합 | **15** | Yes — 배우자궁 약 일주는 soft flag | Medium-strong |
| **F** Combined element balance (용신 alignment) | 오행 보완 / 용신 궁합 | **12** | Soft | "They bring what I lack" |
| **D** 용신 호환 (cross-용신) | 용신 궁합 | included in F | Soft | See D |
| **G** 십신 cross-relationship | 십신 교차 | **10** | Soft | Important but interpretive |
| **H** 대운·세운 synchrony | 운세 호환 | **5** | Soft | Time-bound only |
| **I** Compatibility star overlays | 신살 궁합 | **5** | Yes — 홍염 + 양인 cross is a yellow flag | Bounded by chart balance |
| **J** Yin-Yang polarity balance | 음양 조화 | **3** | No | Adjuster only |
| **K** Year-branch (띠) zodiac pair | 띠 궁합 | **3** | No | Folk layer; intuition hook |
| **Total** | | **100** | | |

> Each sub-system section below gives the classical rule, Hanja/Korean label, programmatic contract, classical weighting, and any inter-school disagreement.

---

## A · Day-stem Combination (일간합 / 천간합)

### Rule

The two Day Masters either **combine (합)** or they do not. There are exactly **5 stem-combination pairs**, and in a 궁합 context the most important is whether the **two Day Masters** themselves form a pair:

| Pair | Combined element | Korean / Hanja | Classical reading in 궁합 |
|---|---|---|---|
| 甲 + 己 | Earth (토) | 갑기합토 (甲己合土) | Most famous "natural pair." 1순위 궁합 partner; mutual attraction & complementarity |
| 乙 + 庚 | Metal (금) | 을경합금 (乙庚合金) | Attraction through contrast (Wood-Me); can be intense, sometimes conflict-laden |
| 丙 + 辛 | Water (수) | 병신합수 (丙辛合水) | Mutual transformation; traditionally a strong "spouse" reading because 丙辛 is the canonical husband-wife axis in 적천수 commentary |
| 丁 + 壬 | Wood (목) | 정임합목 (丁壬合木) | Growing, generative pairing |
| 戊 + 癸 | Fire (화) | 무계합화 (戊癸合火) | Warm, romantic; "fire produced from earth-water meeting" |

### 합화 (transformation) vs 반합 (half-binding)

In 궁합 context, classical schools **rarely require 합화** for the Day Masters — 합화 requires the combined element to be **in season** at the month branch of the *couple's combined chart*, which is ambiguous because each partner has a different month branch. Most Korean 명리 scholars treat 일간합 as a **binding (합)** that signals strong attraction, **not** a full 화격 transformation. [UNCERTAIN: 명리정종 and 일부 classical commentators require 합화 for "true" marriage indication; modern Korean schools treat any 합 as attraction.]

### Breaking stems (합 방해)

A **breaking stem** (간섭, 干泄) appears in either chart and disrupts the 합. The classical breaking stems:

| Pair | Breaking stems (간섭) | Korean | Why |
|---|---|---|---|
| 甲己 | 乙, 庚 | 을·경 | Same element (乙=Wood competing) or controlling (庚=Metal chopping) |
| 乙庚 | 甲, 辛 | 갑·신 | Strong Wood beats; 辛 competes |
| 丙辛 | 丁, 壬 | 정·임 | 丁 = same-element; 壬 = authority competing |
| 丁壬 | 丙, 癸 | 병·계 | 丙 = same-element rival; 癸 = authority |
| 戊癸 | 己, 甲 | 기·갑 | 己 = same-element; 甲 = controlling |

A breaking stem **in the same chart** as one of the pair generally dissolves the 합 — especially if the breaking stem is in the **month branch** (most powerful position). A breaking stem in the **other partner's chart** has weaker effect, but if it appears in *both* charts, the 합 is severely weakened.

### Classical reading in 궁합

- **Both Day Masters combine** → traditional reading: "자연 부부 (natural couple)," strong magnetic attraction, often described as 천생연분 (heaven-made bond). 적천수 (임철초 주석) lists this as a **primary spouse indicator**.
- **No day-master combination** → no special attraction layer; relationship must rely on day-branch, 십신 cross, and element balance.
- **Breaking stem present** → the natural attraction weakens. If the breaking stem is the partner's own Day Master or another prominent stem in the partner's chart, the dissolving effect is strongest.

### How to compute programmatically

**Inputs needed:** chart A's day_stem, chart B's day_stem, all four stems of each chart, each chart's month branch (for 합화 in-season check), and any visible stems in *both* charts to test for breaking.

**Procedure:**

1. Look up `(chart_a.day_stem, chart_b.day_stem)` in `lookup.TEN_STEM_COMBINATIONS`.
2. If no combination → return `"no_combo"`, weight 0.
3. If combination → return the 합 result and check whether the **combined element** is "in season" at the month branch of either partner (for the partial 합화 check). Most Korean 명리 scholars use **either** partner's month branch as the in-season indicator.
4. Scan **all 8 visible stems** (4 per chart) for any breaking stem. If found → mark the 합 as `"half_binding"` and reduce weight by 50%. If the breaking stem is in the month branch of either chart → mark as `"broken"` and reduce weight by 80%.
5. The transformed element (합화 → 토/금/수/목/화) is the **element the relationship "becomes"**. Use this as an overlay in the reading.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| day_stem | The combination check itself |
| month_stem + month_branch | 합화 in-season test |
| All 4 stems (especially month_stem) | Breaking-stem detection |
| Year stem (less often) | Sometimes used as a secondary 합 partner |

### Whether it requires a new engine module

**Reuses existing chart data.** The 합 detection already exists in `lookup.stem_combination()`. A new function `compat_daystem_combo(chart_a, chart_b) -> {pair, broken, transformed_element, score}` can be added that calls `lookup.stem_combination()` and applies the breaking-stem check.

### Classical weight

12 / 100 (medium-strong attraction layer).

### School disagreements

- **명리정종** strict view: only 합화 (with in-season proof) counts as a true spouse indicator.
- **Modern Korean 명리** (권인성·송기영 traditions): any 합 is meaningful, regardless of season.
- **Tag:** [UNCERTAIN] in client report.

---

## B · Day-branch Interaction (일지 합·충·형·파·해)

**This is the most important single sub-system in classical Korean 궁합.**

### Rule

Both partners' **day branches** are "spouse palaces" (배우자궁). They interact through the standard 12-branch relationship grammar. *(see `02-branches.md` for full tables.)*

### B1 · 육합 (六合一 — Six Combinations) — strongest favorable

| Pair | Combined element | Korean | Classical weight |
|---|---|---|---|
| 子丑 (자축) | Earth (토) | 자축합토 | ++ very favorable |
| 寅亥 (인해) | Wood (목) | 인해합목 | ++ very favorable |
| 卯戌 (묘술) | Fire (화) | 묘술합화 | ++ very favorable |
| 辰酉 (진유) | Metal (금) | 진유합금 | ++ very favorable |
| 巳申 (사신) | Water (수) | 사신합수 | + favorable but often "turbulent" |
| 午未 (오미) | Earth (화토) | 오미합 (화토) | ++ very favorable |

**Classical reading:** *"배우자궁이 서로 합이 되면, 부부궁이 하나로 묶인다"* — when the two day branches form 육합, the two spouse palaces are bound into one. This is the **single strongest favorable indicator** in 궁합.

**Caveat — 해 (harm) cross-check:** 자축합 is sometimes disturbed by 자미해; 인신형 etc. Modern Korean 명리 treats pure 육합 as ~+20 weight, but if 해 or 형 also exists in the cross, weight is halved.

> **⚠ Unsourced — NOT implemented by the engine.** The halving clause above rests on no classical text consulted, and the engine implements no such discount. Read carefully, its own worked examples are **cross-level co-occurrences**, not a same-pair condition: 자축합 (one pair) disturbed by 자미해 (a *different* pair in the same cross), and 인신형 likewise — so the sentence does not state "a pair that is simultaneously 육합 and 해/형 is halved." It is also internally inconsistent with this file: `:137` names 寅申 `인신형`, while **§B4 (`:166`) tabulates the same pair as `인신충`** (육충). Implementing the clause would require converting the strict first-match ladder into an **inventory scan** — a behaviour change, not a bug fix. Deliberately **not** taken. See **§B9**.

### B2 · 삼합 (三合一 — Three Harmonies) into one of 5 element frames

If either partner's day branch + the other's day branch are **two of three** in a 삼합 frame, this is a **반합 (half-harmony)**:

| Group | Element | Two-of-three detection |
|---|---|---|
| 申子辰 (신자진) | Water | If both day branches contain any two of {申, 子, 辰} → half-Water harmony |
| 亥卯未 (해묘미) | Wood | any two of {亥, 卯, 未} |
| 寅午戌 (인오술) | Fire | any two of {寅, 午, 戌} |
| 巳酉丑 (사유축) | Metal | any two of {巳, 酉, 丑} |

**Two-of-three (반합)** = +8 to +10 classical weight. **Three-of-three (full 삼합 across both charts)** is extremely rare in 궁합 context (would require one partner's day branch to be in both the other's chart AND in their own chart, which doesn't happen day-branch-to-day-branch alone — but possible if month/day/hour branches across both charts collectively form the triple). Most commonly relevant: **the day branch + the other partner's month/year/hour branch** forms a 반합 or full triple. We compute this with the **expanded "cross-chart" version** below.

**Caveat:** 삼합 between two charts is **secondary** to 육합 between day branches. 권인성·곽임성 schools: 삼합 counts as ~half the weight of 육합.

### B3 · 방합 (方合一 — Directional Combination, 4 branches)

The four branches of one cardinal direction: 寅卯辰 (East/Wood), 巳午未 (South/Fire), 申酉戌 (West/Metal), 亥子丑 (North/Water). Less concentrated than 삼합. In 궁합 context: when **both partners' branches collectively** cover ≥3 of one directional group, this is a 방합 hint.

**Weight:** ~half of 삼합 (i.e. +4). Modern Korean 명리 treats it as informational.

### B4 · 육충 (六沖 — Six Clashes) — strongest RED FLAG

| Pair | Element opposition | Korean | Classical weight |
|---|---|---|---|
| 子午 (자오) | Water ↔ Fire | 자오충 | **Red flag** — 水火 direct opposition |
| 丑未 (축미) | Earth ↔ Earth | 축미충 | **Red flag** — both Earth branches; "earth vs earth" friction |
| 寅申 (인신) | Wood ↔ Metal | 인신충 | **Red flag** — Wood chopped by Metal |
| 卯酉 (묘유) | Wood ↔ Metal | 묘유충 | **Red flag** — same as above |
| 辰戌 (진술) | Earth ↔ Earth | 진술충 | **Red flag** — earth storehouse clash |
| 巳亥 (사해) | Fire ↔ Water | 사해충 | **Red flag** — water-fire direct opposition |

**Classical reading:** *"배우자궁이 서로 충이면 부딪힘"* — when the two spouse palaces clash, the marriage is **disrupted, activating, and prone to sudden events**. The two partners weaken each other. This is the **single strongest RED FLAG** in 궁합.

**Modern Korean nuance:** 명리정종 and 적천수 treat 일지 육충 as a **structural weakness that needs compensating features** (e.g., 양 partner has strong 재성 to "anchor" the relationship, or the Day Masters form a 천간합 that overrides the branch clash). 학업적 divorce study (KCI 2018) confirms 일지 육충 as one of the top correlates of divorce.

**Caveat — 격/용신에서 충이 풀리는 경우:** if the 충 occurs **inside the chart** (e.g., year-day branches clash in the SAME chart), classical texts say the day-branch-to-day-branch clash in 궁합 may be **softened** by internal structure. But if both partners' day branches clash with **no internal compensation**, it remains a hard flag.

**§B4-C9 note — 삼형 is never reached for a pair that is also 충·해·파.** The engine resolves a day-branch pair through a **strict first-match ladder** (`compat.py::_cross_branch_score`):

> 육합 → 육충 → 육해 → 육파 → 삼형 → 반합

The *first* relation kind that matches the pair wins and no later kind is consulted. So **삼형 is unreachable for any pair that also forms a higher-priority relation** — measured, exactly five unordered pairs:

| Pair | Engine reports | 삼형 shadowed by |
|---|---|---|
| 丑未 (축미) | `육충 丑未` (−5) | 육충 (§B4) |
| 寅巳 (인사) | `육해 寅巳` (−1) | 육해 (§B6) |
| 寅申 (인신) | `육충 寅申` (−5) | 육충 (§B4) |
| 巳申 (사신) | `육합 巳申` (+4) | 육합 (§B1) — 巳申 is simultaneously 六合 and 六破 |
| 未戌 (미술) | `육파 未戌` (−1) | 육파 (§B6) |

Two 삼형 cases *are* reachable and are asserted correct: `子卯` → `(−2, 삼형 子卯)`, and the self-punishment `亥亥` → `(−2, 자형 亥亥)`.

This is **C9**. It is **not fixed**: no `knowledge/` file sanctions any position for 삼형 in this ladder, so re-ordering it would invent a priority. The divergence is carried as a `documented_interpretation` scope limit — the same shape as the accepted 辰/戌 climate resolution. Full argument and evidence: **§B9** below.

### B5 · 자형 (自刑 — Self-Punishment) — two-of-four cross-check

If both day branches are in `{辰, 午, 酉, 亥}`, this is a 자형 cross:
- 辰辰 (진진) — Dragon/Dragon
- 午午 (오오) — Horse/Horse
- 酉酉 (유유) — Rooster/Rooster
- 亥亥 (해해) — Pig/Pig

**Classical reading:** Inner torment, self-destructive tendencies, "two people who amplify each other's worst patterns." Reading: each partner brings the same self-punishment branch → "double-down" effect.

**Weight:** Soft red flag (~-8). Classical texts do NOT treat this as decisive; modern Korean Myeongri reads it as "challenging but workable."

### B6 · 해 (害 — Harm) and 파 (破 — Break)

These are **subtler** than 충. Korean classical schools (especially 궁통보감 tradition) treat them with more weight than mainland BaZi.

**Standard tables** *(see `02-branches.md` Part on Harm/Break):*

| 해 (害) | 파 (破) |
|---|---|
| 子未 (자미) | 子酉 (자유) |
| 丑午 (축오) | 午卯 (오묘) |
| 寅巳 (인사) | 辰丑 (진축) |
| 卯辰 (묘진) | 未戌 (미술) |
| 申亥 (신해) | 申巳 (신사) |
| 酉戌 (유술) | 寅亥 (인해) |

**Classical reading:** *"은근한 마찰 / 신뢰의 침식"* — covert friction, erosion of trust. Often paired with 충: if a chart has 충, check whether 해 also exists, indicating layered friction. 권인성·송기영 schools: each 해/파 cross is a **soft yellow flag** (-3 to -5).

### B7 · Cross-chart expanded branch analysis (확장 일지 분석)

Classical Korean 궁합 goes **beyond** day-branch to day-branch. It checks whether the **other partner's branches** form relationships with the **first partner's day branch** specifically (since the day branch is the spouse palace). Specifically:

- Partner A's day_branch vs Partner B's year/month/day/hour branch
- For each cross: check 합/충/형/파/해

This is the "이궁합 (二宮合 / cross-palace)" tradition in Korean Myeongri.

**Example:** Partner A = 甲子 day pillar; Partner B = 己巳 year pillar.
- A's day_branch = 子, B's year_branch = 巳
- 子 + 巳 = ?  子 is one half of 자축합; 巳 is one half of 사신합. **No direct 합/충.**
- However 子 + 巳亥 = 사해충 (one half). **Soft red flag** from A's day_branch perspective.

**Weight:** Treat each cross-chart branch relationship at **half** the weight of a day-to-day relationship, summed up to a max cap (don't double-count). Modern Korean schools use this as supporting evidence; classical 적천수 treats it lightly.

### B8 · Korean school disagreements on 일지 weight

| School | Treatment of 일지 |
|---|---|
| **적천수 (임철초)** | 일지 육합 is "very favorable"; 일지 육충 is the **hardest** red flag |
| **연해자평** | 일지 관계s are the **first** thing to check in 궁합 |
| **궁통보감** | 일지 relationship, but the **용신 alignment** is the deciding factor — "even perfect 일지 합 can fail if 용신 is opposed" |
| **권인성·곽임성 (modern Korean)** | 일지 육합 = 25 weight, 일지 육충 = -25 weight; other relationships ~half |
| **정봉재·송기영** | Same as 권인성 but **삼합 (반합) counts more** (15 weight) |
| **KCI empirical 2018** | Data: 일지 육충 has highest correlation with divorce (top-3 factor) |

**Tag:** [UNCERTAIN] for exact weight percentages; **consensus**: 일지 육합 = strongest favorable, 일지 육충 = strongest unfavorable.

### B9 · 삼형 (三刑) — carried as a documented scope limit

**Status: the engine computes 삼형, but nothing in `knowledge/` sanctions its use, its weight, or its position in the priority ladder. Carried as a `documented_interpretation` scope limit — not fixed, and not removed.**

**What the engine does.** `lookup.py` holds a `THREE_PUNISHMENTS` table of 4-tuples `(a, b, c, label)` (with a `—` placeholder where a classical triple names only two members), and `compat.py::_pairwise_three_punishment` returns `삼형 {b1}{b2}` for any two members of a triple at **−2** — half the day-to-day weight, per this file's §B7 halving convention. `L.SELF_PUNISHMENTS` handles 자형 separately (`자형 亥亥`). The detection table itself is **not** in question; the engine's 삼형 matching is correct.

**What `knowledge/` does *not* say.** A repository-wide search for `삼형`, `三刑`, `寅巳申` and `丑戌未` across `knowledge/` returns **zero hits**. The gap is *not* blanket silence about 형 — this file references 형 as a *category* five times — but **no file ever defines 삼형, tables its triples, weights it, or ranks it** against the other relations:

| Where | What it says | Why it does not settle the question |
|---|---|---|
| `11-gunghap.md:24` | weight-table row label `일지 합·충·형·파·해` | names the category; assigns no 형 weight |
| `11-gunghap.md:116` | §B heading — the same five-way label | heading only |
| `11-gunghap.md:137` | names one instance, `인신형` | see (2) below — this file contradicts itself on that pair |
| `11-gunghap.md:211` | §B7 instruction: "check 합/충/형/파/해" | an instruction to look, not a rule |
| `11-gunghap.md:1039` | see-also pointer to `02-branches.md` | **dead pointer** — see (1) below |
| `11-gunghap.md:323` | `\| 상형 (相刑) \| mutually punishing \| **-4** \|` | **this is the Nayin (납음) table in §C**, not branch 삼형 |
| `11-gunghap.md:1052` | 연해자평 — *"婚姻宜避刑沖"* | names 형 and 충 **together, without ranking them** |

Two findings sharpen this beyond a simple absence:

1. **The delegated source has no 형 table at all.** §B's opening (`:122`) and the see-also at `:1039` both send the reader to `02-branches.md` "for full tables." That file contains exactly **one** 형 line — `02-branches.md:96`, the **자형** section — and **no 삼형 section and no 삼형 table**. `07-special-formations.md`'s Part 3 relation table (`:318-322`) likewise lists 합 · 충 · **자형** · 해 · 파 and **omits 삼형 as a row**, despite its section title (`:312`) containing 형. The cross-reference therefore dangles in two files at once.
2. **One named instance is self-contradicting.** `:137` calls 寅申 `인신형`; `:166` tabulates the identical pair as `인신충` (육충, §B4). Whatever 인신형 denotes here, the file never says.

The gap is specific to **삼형**, not to 형 in general: **자형 *is* fully documented** — `02-branches.md:96`, `07-special-formations.md:320`, `00-glossary.md:79,189`.

**Why C-none, and not a re-order.** Every candidate ladder position for 삼형 encodes a *priority* that would have to be invented:

- **Hoisting 삼형 above 육충** makes 丑未 and 寅申 lose their §B4 label ("육충 — strongest RED FLAG") and drop −5 → −2, directly contradicting §B4 and §B8's consensus that 일지 육충 is the strongest unfavorable sign. That is not merely unsourced — it **contradicts this file**.
- **Placing it between 육충 and 육해** preserves 육충's documented primacy but displaces 해/파, whose relative ranking against 형 no consulted source states.

So the engine keeps the existing order, and the divergence is pinned as a scope limit — the **same shape as the accepted 辰/戌 resolution** (`17-climate-method.md`, §"The Fuller 寒暖燥濕 Reading — Sourced, Not Implemented"): name the scope, pin it, do not silently widen.

**Measured consequence — the question is far smaller than it looks.** Re-ordering the ladder was measured across all **27** compatibility fixtures: it is a **no-op on every one** — no published anchor, no client-visible value, and no fixture expectation moves. Its only observable effects are the label reported for the five pairs above, and pytest xfail-marker bookkeeping. Under the shipped engine:

| Pair | Engine reports | 삼형 shadowed by | Note |
|---|---|---|---|
| 丑未 | `육충 丑未` (−5) | 육충 (§B4) | |
| 寅巳 | `육해 寅巳` (−1) | 육해 (§B6) | |
| 寅申 | `육충 寅申` (−5) | 육충 (§B4) | the pair §B1 calls `인신형` |
| 巳申 | `육합 巳申` (+4) | 육합 (§B1) | simultaneously 六合 and 六破; 육합 is tested first |
| 未戌 | `육파 未戌` (−1) | 육파 (§B6) | |

`子卯` → `(−2, 삼형 子卯)` and `亥亥` → `(−2, 자형 亥亥)` remain reachable and correct.

**Tag:** [UNCERTAIN] — the priority of 삼형 relative to 충·해·파 is not established by any consulted source. The engine's ordering is a declared implementation choice, **not** a recovered classical rule.

### How to compute programmatically

**Inputs needed from each chart:** day_branch, year_branch, month_branch, hour_branch (for cross-chart analysis).

**Procedure:**

1. **Primary (day-to-day):** lookup `(chart_a.day_branch, chart_b.day_branch)` in:
   - `lookup.SIX_COMBINATIONS` → if match, weight = +20
   - `lookup.SIX_CLASHES` → if match, weight = -25 (RED FLAG)
   - `lookup.SIX_HARMS` → if match, weight = -5
   - `lookup.SIX_BREAKS` → if match, weight = -3
   - `lookup.SELF_PUNISHMENTS` (both branches ∈ {辰,午,酉,亥}) → if match, weight = -8
   - For 삼합: check if branches are in same `THREE_HARMONIES` group → +10
2. **Secondary (cross-chart):** for each combination of `chart_a.day_branch × chart_b.{year,month,hour}_branch` and `chart_b.day_branch × chart_a.{year,month,hour}_branch`, apply the same checks at **half** weight. Sum and cap.
3. **Composite score** for sub-system B = primary + secondary (capped at ±30 to prevent runaway from over-counting).

### Inputs needed from each chart

| Input | Used for |
|---|---|
| day_branch | Primary day-to-day interaction |
| year_branch, month_branch, hour_branch | Cross-chart secondary analysis |

### Whether it requires a new engine module

**New module: `src/saju_engine/compat.py`** with function `compat_daybranch(chart_a, chart_b) -> {primary, secondary, score, flags}`. Uses existing `lookup.SIX_COMBINATIONS`, `SIX_CLASHES`, `THREE_HARMONIES`, `SIX_HARMS`, `SIX_BREAKS`, `SELF_PUNISHMENTS`.

### Classical weight

**30 / 100** (highest single factor).

---

## C · Nayin Five Elements (납음오행, 納音五行)

### Rule

Each of the **60 jiazi pairs** (the complete stem-branch cycle) is assigned a **Nayin element** based on the Heavenly Stem + Earthly Branch pair. This element is fixed for each pair and is the "deep tone" of that day pillar. The Nayin classification groups the 60 jiazi into **6 groups of 10** by element, then subdivides into the famous 30 nayin pairs.

| Group | Nayin element | 10 jiazi pairs | Korean |
|---|---|---|---|
| 甲乙 | Wood | 甲子, 乙丑 (海中金's 1st pair) → see table | (wood subset of nayin) |

**The classical 30 nayin pairings** (the standard list used in Korean 궁합): See table below.

### The 30 nayin pairs (table)

| # | Jiazi | Nayin element | Korean / Hanja |
|---|---|---|---|
| 1 | 甲子, 乙丑 |海中金 (해중금, Gold in the Sea) | Gold hidden in deep water; surface calm, deep value |
| 2 | 丙寅, 丁卯 | 爐中火 (노중화, Fire in the Furnace) | Concentrated, refining fire |
| 3 | 戊辰, 己巳 | 大林木 (대림목, Forest Wood) | Tall-tree wood, expansive |
| 4 | 庚午, 辛未 | 路傍土 (노방토, Roadside Earth) | Earth by the path; cultivated, ordinary, accessible |
| 5 | 壬申, 癸酉 | 劍鋒金 (검봉금, Sword-Edge Metal) | Sharp, refined metal |
| 6 | 甲戌, 乙亥 | 山頭火 (산두화, Mountain-Top Fire) | Bright, exposed fire |
| 7 | 丙子, 丁丑 | 澗下水 (간하수, Water Under the Stream) | Quiet, nourishing water |
| 8 | 戊寅, 己卯 | 城頭土 (성두토, City-Wall Earth) | Earth on the wall; defensive, structural |
| 9 | 庚辰, 辛巳 | 白蠟金 (백랍금, White Wax Metal) | Polished, refined metal |
| 10 | 壬午, 癸未 | 楊柳木 (양류목, Willow Wood) | Flexible, pliant wood |
| 11 | 甲申, 乙酉 | 泉中水 (천중수, Spring Water) | Flowing, clear water |
| 12 | 丙戌, 丁亥 | 屋上土 (옥상토, Rooftop Earth) | Earth on the roof; isolated, elevated |
| 13 | 戊子, 己丑 | 霹靂火 (벽력화, Thunder Fire) | Sudden, shocking fire |
| 14 | 庚寅, 辛卯 | 松柏木 (송백목, Pine-Cypress Wood) | Evergreen, enduring wood |
| 15 | 壬辰, 癸巳 | 長流水 (장류수, Long-Flowing Water) | Enduring, far-flowing water |
| 16 | 甲午, 乙未 | 沙中金 (사중금, Sand Gold) | Gold hidden in sand; needs digging |
| 17 | 丙申, 丁酉 | 山下火 (산하화, Mountain-Foot Fire) | Quiet fire at the base |
| 18 | 戊戌, 己亥 | 平地木 (평지목, Flatland Wood) | Ordinary, accessible wood |
| 19 | 庚子, 辛丑 | 壁上土 (벽상토, Wall Earth) | Earth on the wall; supporting |
| 20 | 壬寅, 癸卯 | 金箔金 (금박금, Gold-Leaf Metal) | Surface-bright metal; decorative |
| 21 | 甲辰, 乙巳 | 覆燈火 (복등화, Lamp Fire) | Sheltered, gentle fire |
| 22 | 丙午, 丁未 | 天河水 (천하수, Milky-Way Water) | Heavenly, vast water |
| 23 | 戊申, 己酉 | 大驛土 (대역토, Post-Horse Earth) | Earth of the road; travelers' earth |
| 24 | 庚戌, 辛亥 | 釵釧金 (채천금, Hairpin-Bracket Metal) | Jewelry metal; refined, ornamental |
| 25 | 壬子, 癸丑 | 桑柘木 (상저목, Mulberry Wood) | Useful, pliant wood |
| 26 | 甲寅, 乙卯 | 大溪水 (대계수, Great Stream Water) | Strong, flowing water |
| 27 | 丙辰, 丁巳 | 沙中土 (사중토, Sand Earth) | Earth in sand; needs structure |
| 28 | 戊午, 己未 | 天上火 (천상화, Heavenly Fire) | Bright, exposed fire |
| 29 | 庚申, 辛酉 | 石榴木 (석류목, Pomegranate Wood) | Fruitful, vibrant wood |
| 30 | 壬戌, 癸亥 | 大海水 (대해수, Great Sea Water) | Vast, deep water |

### Use in 궁합

The classical Korean view (especially 궁통보감 and **서전구미록 書傳九微錄** commentary) is that the **two partners' Nayin elements should be compatible**. The six standard relationships (서전구미록):

| Nayin relationship | Korean | Effect |
|---|---|---|
| 상합 (相合) | mutually harmonious | **+3** (very soft) |
| 상충 (相沖) | mutually clashing | **-5** (soft flag) |
| 상형 (相刑) | mutually punishing | **-4** |
| 상해 (相害) | mutually harming | **-3** |
| 상구 (相求) | mutually seeking | **+2** (one reinforces the other) |
| 상대 (相代) | mutually substituting | **+1** (similar tones) |

### School disagreements — Nayin in 궁합

| School | Treatment of Nayin |
|---|---|
| **적천수 / 자평진전** (classical Chinese) | Nayin is "tone" but **not** a primary factor in 궁합 |
| **궁통보감 tradition** (Korean) | Nayin is a **secondary, descriptive** factor — used for "overall harmony" but not for red flags |
| **Modern Korean 점술** (folk) | Nayin is often inflated to **primary** factor — this is the **modern folk over-weighting**, not classical |
| **권인성·송기영** | Treat Nayin as **5 weight**, descriptive only |
| **서전구미록 commentary** | Most systematic Korean use of Nayin for 궁합; referenced as the "standard" |

**Tag:** [UNCERTAIN] for exact weight. **Consensus**: Nayin is a **soft indicator (~5 weight)** and is **never** a red flag by itself.

### How to compute programmatically

**Inputs needed:** day_pillar of each chart (stem + branch → unique jiazi pair).

**Procedure:**

1. Build a lookup table `JIAZI_TO_NAYIN` mapping the 60 jiazi pairs to one of 30 nayin names (each nayin covers 2 jiazi).
2. Look up `nayin_a = JIAZI_TO_NAYIN[(chart_a.day_stem, chart_a.day_branch)]` and same for chart B.
3. Build a `NAYIN_PAIR_TABLE` for the 30 × 30 = 900 ordered pairs. Each cell stores one of the six relationship types above and a source tag.
4. Until the full published **서전구미록** 30×30 table is sourced, the table is seeded with the documented 5-element grammar reduction (same element → 상대; generation → 상합; reverse generation → 상구; overcoming → 상충; reverse overcoming → 상해). This is a deterministic fallback, not a pair-specific reading.
5. Return `{nayin_a, nayin_b, relation, weight, source_tag}`.

### Canonical subject order (engine convention)

Step 3 specifies an **ordered** table, and the six relationship labels are
themselves direction-bearing — 상합 and 상구 both mean "generation", but name
opposite directions of it, as do 상충 and 상해 for overcoming. So the relation
is only well-defined once the *order of the two tones* is fixed, and the order
must therefore come from the **couple**, not from whichever argument a caller
happens to pass first.

The engine fixes it by one convention, applied in
`compat.py::_canonical_nayin_pair()`:

- **When both genders are known and differ** — the male partner's Nayin is
  subject, matching the product's canonical partner order for a heterosexual
  pair ("Partner A first; for heterosexual pairs Partner A is the male").
- **Otherwise** (same gender, or either gender unknown) — the tone that appears
  earlier in the 30-name display order above is subject.

The index tiebreak is a **stability rule, not a classical claim**: no sourced
text consulted for this file defines an order rule for the 30×30 table at all
(see the data-gathering note below), so a deterministic tiebreak is needed to
make the sub-system a function of the couple rather than of the call. Both
branches are a **NO-OP for every already-canonical (male-first) pair**, so no
published verdict moves; they only stop a reversed call from silently producing
a subject-swapped — and, in some pairs, band-flipping — verdict for the same
couple. This gender-keying mirrors the §G spouse-star mapping
(`_gendered_spouse_star_note()`), which likewise declines the gendered read
when gender is unknown.

### Data-gathering note

A true **pair-specific 서전구미록 30×30 table** (not the 5-element reduction) has not yet been located in an accessible published source. Korean web sources (e.g., sajplus.tistory.com/2017) provide only a 5×5 gender-aware element grid. The engine therefore flags each Nayin verdict with its source tag:

- `"element-grammar-fallback"` — derived from the 5-element grammar documented above.
- `"sourced"` — reserved for future entries taken directly from a published 30×30 서전구미록 table with citation.

**[DATA GATHERING]** Needed: a published Korean almanac, book, or academic source that lists the 30×30 ordered relationship table keyed by the 30 Nayin categories above. Once sourced, cells can be overridden individually without changing the API or tests.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| day_stem + day_branch | Jiazi pair → Nayin lookup |

### Whether it requires a new engine module

**New module: `src/saju_engine/nayin.py`** with the `JIAZI_TO_NAYIN` table, the 30×30 `NAYIN_PAIR_TABLE`, and `nayin_relation_detail(nayin_a, nayin_b)` function. Self-contained; doesn't depend on existing charts.

### Classical weight

**5 / 100** (soft indicator).

---

## D · Favorable Element Compatibility (용신 궁합 / 교차 용신)

### Rule

Two questions are answered separately:

1. **Cross-용신 (교차 용신):** Does Partner A's chart carry the element that Partner B needs (as 용신)? And vice versa?
2. **Same-용신 (동일 용신):** Are both partners' 용신 the same element? (Can be harmonious — both oriented toward the same goal — or strained — both "lean" on the same missing element.)

### Classical reading

- **Cross-용신 "feeding":** A's chart has strong Water (B's 용신 is Water) and B's chart has strong Metal (A's 용신 is Metal). Mutual fulfillment, "서로 용신이 되는" reading. **Strong favorable** (정통 궁합의 핵심).
- **Cross-용신 "draining":** A's chart is dominated by the element that B needs to *avoid* (기신). E.g., A is heavy Fire (B's 기신 is Fire). **불리**.
- **Same 용신:** Both partners' charts need Water → both are "thirsty for Water" → they can either align (grow in same direction) or compete (struggle for the same resource).
- **No overlap:** Neither partner has what the other needs → "운명적 동지 (fated companions)" reading; relationship must rely on other factors.

### 궁통보감 emphasis

궁통보감 treats **용신 alignment as the deciding factor** in 궁합. From the **KCI 2023 paper** (ART002969199): 궁합을 자연의 **조후 (寒暖燥濕 climate balance)** 관점에서 해석 — a person's chart needs 조후 (寒暖·燥濕 balance) and the partner's chart should supply it. **이수동 2023 정량 모델**: 인월생자에게 오월생(97점), 술월생(88점), 사월생(85점)이 가장 좋고, 자월생(30점)은 피해야. (Higher score = better 용신 alignment.)

### School disagreements

| School | Treatment |
|---|---|
| **궁통보감** | 용신 alignment is **THE deciding factor** — if 용신 matches, ignore other minor red flags |
| **적천수** | 용신 is critical but 일지 궁 interaction is **equally important** |
| **명리정종** | Balanced approach: 일지 25%, 용신 25%, 십신 cross 25%, other 25% |
| **Modern Korean 명리** | 용신 alignment: ~12 weight (sub-factor, but important) |

**Tag:** [UNCERTAIN] on exact weight, but **consensus**: 용신 alignment is the **single most important non-day-branch** factor.

### How to compute programmatically

**Inputs needed from each chart:**
- 용신 (already computed by `engine.py` or `premium_report.py`)
- 기신 (already computed)
- Element distribution (already computed)
- Day Master strength

**Procedure:**

1. Get `yongshin_a`, `yongshin_b` (and `gishin_a`, `gishin_b`).
2. Compute the **"cross-need"** score: how strongly does B's chart contain A's 용신? How strongly does A's chart contain B's 용신?
3. Compute the **"mutual gishin"** penalty: how strongly does B's chart contain A's 기신? And vice versa.
4. Sum and normalize. Apply classical weight ~12.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| yongshin, gishin (from existing engine) | Cross-need and mutual-gishin test |
| Element distribution | Strength of cross-supply |
| 희신 (supporting element) | Secondary check |

### Whether it requires a new engine module

**New function in `compat.py`:** `compat_yongshin(chart_a, chart_b) -> {cross_need_score, mutual_gishin_penalty, total, narrative}`. Reuses existing `engine.yongshin` / `engine.gishin`.

### Classical weight

**12 / 100** (medium-strong; higher in 궁통보감 school, lower in 적천수 school).

---

## E · Day Pillar Pair Classification (일주 궁합 / 60 갑자 일주 궁합)

### Rule

Each person's **day pillar** is one of the 60 jiazi pairs. The classical Korean tradition (권인성·곽임성, 정봉재 schools; based on 궁통보감 and 자평진전 commentary) classifies day pillars by **spouse-palace strength** and assigns **pairwise compatibility** between common pillars.

### E1 · 배우자궁 강 / 약 (Spouse Palace Strong / Weak)

A spouse palace (day branch) is **strong** when:
- It is the Day Master's **건록** or **제왕** branch (peak strength) — see `01-stems.md` 12 stages
- It contains the Day Master's element in its 본기
- It is a "storehouse" (사고, 辰戌丑未) with the Day Master's element in hidden stems
- It is the Day Master's **장생** branch (life-beginning)

A spouse palace is **weak** when:
- It is the Day Master's **사** (death) or **묘** (tomb) branch
- It contains only the **controlling** element in 본기 (e.g., 甲 day master with 酉 day branch = Metal chopping)
- It is **공망** (empty) for the day pillar's 旬

### E2 · 배우자궁 강 일주 (Strong spouse palace) — classical favorites

| Day pillar | Day Master | Spouse palace | Korean reading |
|---|---|---|---|
| 甲子 (갑자) | 甲 Wood | 子 Water | "Yang wood rooted in deep water" — 영리한 배우자, 사회성 강함 |
| 丙寅 (병인) | 丙 Fire | 寅 Wood | "Sun rising in spring" — 따뜻하고 활동적인 배우자 |
| 戊辰 (무진) | 戊 Earth | 辰 Earth | "Mountain earth" — 안정적이고 신중한 배우자 |
| 庚午 (경오) | 庚 Metal | 午 Fire | "Sword in refining fire" — 단련된 강인한 배우자 |
| 壬申 (임신) | 壬 Water | 申 Metal | "Great river in metal source" — 지적이고 체계적인 배우자 |
| 丁卯 (정묘) | 丁 Fire | 卯 Wood | "Candle with wood" — 부드러운 성장 동반자 |
| 己未 (기미) | 己 Earth | 未 Earth | "Garden earth" — 다산의 배우자 |
| 辛酉 (신유) | 辛 Metal | 酉 Metal | "Jewel in jewel" — 정교하고 예리한 배우자 |
| 癸亥 (계해) | 癸 Water | 亥 Water | "Dew in deep water" — 깊고 사려 깊은 배우자 |

### E3 · 배우자궁 약 일주 (Weak spouse palace) — classical cautions

| Day pillar | Day Master | Spouse palace | Korean reading |
|---|---|---|---|
| 甲申 (갑신) | 甲 Wood | 申 Metal | "Wood in metal" — 배우자에게 상처 받기 쉬움 |
| 丙午 (병오) | 丙 Fire | 午 Fire | "Sun at peak" — 배우자가 너무 강해 갈등 |
| 庚子 (경자) | 庚 Metal | 子 Water | "Metal in water" — 배우자에게 침식당함 |
| 壬寅 (임인) | 壬 Water | 寅 Wood | "Water in wood" — 흡수당함 |
| 戊戌 (무술) | 戊 Earth | 戌 Earth | "Mountain earth vs mountain" — 갈등·정체 |

### E4 · 궁합이 좋은 일주 pairings (Good day-pillar pairs)

Classical Korean sources (권인성·곽임성 tradition; based on 일간 합 + 일지 합 cross-checks) commonly list these high-affinity day-pillar pairs:

| Pair | 합 reasons | Classical reading |
|---|---|---|
| 甲子 + 己丑 | 천간 甲己合, 일지 자축합 | 1순위 — 천생 부부 |
| 乙亥 + 甲午 | 천간 甲乙合 + 해자합 | 따뜻한 결합 |
| 丙寅 + 辛酉 | 천간 丙辛合, 일지 인유 관계 | 정열적 결합 |
| 丁卯 + 壬寅 | 천간 丁壬合, 일지 묘인 관계 | 성장 결합 |
| 戊辰 + 癸未 | 천간 戊癸合, 일지 진미 관계 | 안정적 결합 |
| 己巳 + 甲戌 | 천간 甲己合, 일지 사유 관계 | 균형 잡힌 결합 |
| 庚午 + 乙丑 | 천간 乙庚合, 일지 축오 관계 | 정밀한 결합 |
| 辛未 + 丙子 | 천간 丙辛합, 일지 미자 관계 | 따뜻한 결합 |
| 壬申 + 丁巳 | 천간 丁壬합, 일지 신사 육합 | "용과 봉황" 결합 |
| 癸酉 + 戊寅 | 천간 戊癸합, 일지 유묘 관계 | 잠재력 결합 |

### E5 · 궁합이 어려운 일주 pairings (Challenging day-pillar pairs)

| Pair | 충 reasons | Classical reading |
|---|---|---|
| 甲子 + 庚午 | 일지 子午충 | RED FLAG — 배우자궁 정면충돌 |
| 乙丑 + 辛未 | 일지 丑未충 | RED FLAG — 토끼-양 갈등 |
| 丙寅 + 壬申 | 일지 寅申충 | RED FLAG — 호랑이-원숭이 갈등 |
| 丁卯 + 癸酉 | 일지 卯酉충 | RED FLAG — 토끼-닭 갈등 |
| 戊辰 + 甲戌 | 일지 辰戌충 | RED FLAG — 용-개 갈등 |
| 己巳 + 乙亥 | 일지 巳亥충 | RED FLAG — 뱀-돼지 갈등 |
| 경자 + 신자 | 일지 子子 (자형 자형) | Inner torment pattern |
| 경인 + 신인 | 일지 寅寅 | Inner torment |
| 병오 + 정오 | 일지 午午 | Inner torment — "두 태양" |
| 무술 + 기술 | 일지 戌戌 | Inner torment |

### E6 · 배우자 복덕 (Spouse Virtue) — day-branch hidden stem quality

Classical Korean 명리 judges the **spouse's virtue** by the **hidden stem (지장간)** in the day branch:

| Day-branch hidden stem (본기) as 십신 of Day Master | Reading | Spouse virtue |
|---|---|---|
| 정재 (Direct Wealth) | 배우자가 재물을 안정시킴 | **가장 좋은 배우자 복덕** (일지 정재 = 부덕이 있는 배우자) |
| 정관 (Direct Officer) | 배우자가 권위·질서를 가져다줌 | 좋은 배우자 — 사회적으로 안정 |
| 식신 (Eating God) | 배우자가 표현·자녀 복을 가져다줌 | 좋은 배우자 — 자녀 복 |
| 정인 (Direct Resource) | 배우자가 보호·학업 복을 가져다줌 | 좋은 배우자 — 정신적 지지 |
| 편재 (Indirect Wealth) | 배우자가 다양한 재물 기회 | 좋으나 변동성 있음 |
| 편관 (Seven Killings) | 배우자가 압박·긴장 | 주의 — 권위 다툼 가능 |
| 상관 (Hurting Officer) | 배우자가 표현·갈등 | 주의 — 언쟁 잦음 |
| 편인 (Indirect Resource) | 배우자가 비정통적 지원 | 독특한 배우자; 호불호 |
| 비견 / 겁재 (Companion class) | 배우자가 동등·경쟁 | 평이함; 때로 경쟁 관계 |

### School disagreements

- **권인성·곽임성 (modern Korean)**: 위 표와 같이 정재·정관·식신·정인이 "좋은 배우자 복덕"으로 분류.
- **명리정종 (classical Korean)**: 배우자 복덕은 **일간 성별**에 따라 다름 — 남성에게는 정재·편재 모두 긍정, 여성에게는 정관 긍정 / 편관 부정.
- **적천수 (Chinese classical)**: 배우자 복덕은 **용신의 길흉**으로 판단 — 일지의 십신이 용신이면 무조건 좋음, 기신이면 무조건 나쁨. (성별 무관.)

**Tag:** [UNCERTAIN] on which framework; **consensus**: 일지의 십신이 **용신이면 좋음, 기신이면 나쁨** (적천수 원칙)이 가장 견고함.

### How to compute programmatically

**Inputs needed from each chart:** day_stem, day_branch, day_pillar (combined), yongshin, gishin (for 적천수 원칙 application).

**Procedure:**

1. **Spouse-palace strength check:** Look up `day_branch` in 건록/제왕/장생 tables for `day_master`. Flag strong/weak.
2. **Spouse virtue:** Identify the day-branch's 본기 hidden stem, look up its 십신 relationship to `day_master`, then check if that 십신 is yongshin/gishin/heeshin. Score:
   - 십신 = yongshin → +3
   - 십신 = heeshin → +2
   - 십신 = 중립 (비겁) → 0
   - 십신 = gishin → -3
3. **Pair-pair check:** Look up `(chart_a.day_pillar, chart_b.day_pillar)` in the 일주 궁합 table (E4, E5). Apply weight from the table.
4. Return combined score.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| day_stem, day_branch | Day-pillar identification, spouse-palace strength |
| yongshin, gishin | Spouse-virtue 적천수 원칙 check |

### Whether it requires a new engine module

**New module: `src/saju_engine/compat_pillars.py`** with `ILJU_GUNGHAP_TABLE` (60×60 lookup of pair classifications) and `spouse_virtue(chart)` function. Reuses `lookup.twelve_stage`, `lookup.HIDDEN_STEMS`, `lookup.ten_god`.

### Classical weight

**15 / 100** (medium-strong).

---

## F · Combined Element Balance (오행 보완 / 결합 오행 분포)

### Rule

The **union of two charts** has its own element distribution (sum of all 8 stems + all 8 branches with weighted hidden stems). The classical question: **is the union balanced?** or **does the union have a missing element (결핍 오행)?** or **does the union have a disastrous excess?**

### Computation

For each of the 5 elements, count:
- Number of visible stems equal to that element
- Sum of weighted hidden stems (main=1, middle=0.5, residual=0.3) equal to that element
- Total per element

Compare to the **ideal** distribution: each element between 15-25% of total weight.

### Interpretation

- **Balanced union** (all elements 15-25%): "두 사람이 함께 일정한 삶" — neutral-to-positive reading.
- **One element missing (0%)**: classical Korean Myeongri reads as **결합의 결핍** — the union lacks a quality (e.g., no Metal → missing "justice/structure"; no Water → missing "communication/flow").
- **One element >40%**: union is **skewed**; the over-dominant element "rules" the relationship.
- **용신 union check:** does each partner's 용신 appear in the union? If both partners' 용신 appear → "서로 용신 보완" — strongest favorable.

### 궁통보감 "조후" perspective

The KCI 2023 paper (ART002969199) frames this as **조후 (寒暖燥濕 climate balance)**:
- One partner is "寒 (cold)" → needs warm partner
- One partner is "熱 (hot)" → needs cool partner
- One partner is "燥 (dry)" → needs moist partner
- One partner is "濕 (wet)" → needs dry partner

If both partners are "寒" → double-cold; one will catch the other's cold → **불리**.
If one is "寒" and one is "熱" → complementary climate → **유리**.

### How to compute programmatically

**Inputs needed:** all stems and branches of both charts.

**Procedure:**

1. Compute element counts for chart A (using existing `engine.count_elements()` or similar).
2. Compute element counts for chart B.
3. Sum the two distributions → union distribution.
4. Compute balance score: deviation from 20%-per-element ideal.
5. Compute "양 partner's 용신 in union" check.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| All 4 stems | Element count |
| All 4 branches + hidden stems | Element count (weighted) |
| yongshin (both) | 용신 union check |

### Whether it requires a new engine module

**New function in `compat.py`:** `compat_combined_elements(chart_a, chart_b) -> {union_dist, balance_score, missing_element, yongshin_union, score}`. Reuses existing element-counting logic.

### Classical weight

**12 / 100** (medium-strong; subsumed partially by D for the 용신-alignment piece).

---

## G · Ten-God Cross-Relationship (십신 교차)

### Rule

In 궁합, each partner can be classified as **a specific 십신 of the other partner's Day Master**. This is computed by treating each partner's day pillar (stem + branch hidden stems) as "input" to the other partner's chart.

### The four primary cross-relationships

1. **내 일간 → 상대 일간:** Partner A's Day Master is what 십신 to Partner B's Day Master?
   - E.g., A = 甲, B = 己 → 甲 is 偏財 (편재) to 己
2. **내 일간 → 상대 일지 (배우자궁):** Partner A's Day Master lands on Partner B's spouse palace — what 십신 to B?
3. **상대 일간 → 내 일지:** Partner B's Day Master lands on A's spouse palace — what 십신 to A?
4. **상대 일간 → 내 (년/월/시)지:** Cross-palace analysis.

### 십신 reading in 궁합

| 십신 | Classical reading in 궁합 context |
|---|---|
| **정관** (Direct Officer) | 배우자·상대가 **나에게 규율·질서·안정**을 가져다줌. 아버지 같은 존재. *편관보다 부드러운 권위.* |
| **편관 (칠살)** (Seven Killings) | 배우자·상대가 **강한 압박·긴장·통제**을 가져다줌. 때로 강렬한 끌림, 때로 갈등. |
| **정재** (Direct Wealth) | 배우자·상대가 **안정된 재물·현실적 도움**을 가져다줌. 가장 따뜻한 배우자 복덕. |
| **편재** (Indirect Wealth) | 배우자·상대가 **변동성 있는 재물·큰 기회**을 가져다줌. 시빨간 부자 또는 불안정한 재물. |
| **식신** (Eating God) | 배우자·상대가 **표현·여유·자녀 복**을 가져다줌. 부드러운 관계. |
| **상관** (Hurting Officer) | 배우자·상대가 **날카로운 표현·갈등·통찰**을 가져다줌. 강렬하지만 불안정. |
| **정인** (Direct Resource) | 배우자·상대가 **보호·학업·정서적 지지**을 가져다줌. 어머니 같은 존재. |
| **편인** (Indirect Resource) | 배우자·상대가 **독특한 지원·비정통적 보호**을 가져다줌. |
| **비견** (Companion) | 배우자·상대가 **동등한 관계·동료**을 가져다줌. |
| **겁재** (Robber) | 배우자·상대가 **경쟁·갈취·소모**을 가져다줌. 주의. |

### Specific patterns

| Pattern | Korean | Reading |
|---|---|---|
| 배우자 (상대) 일간 = 내 정관 | 정관배우 | 안정적 결혼 — 가장 권장되는 패턴 (남성→여성 / 여성→남성 모두) |
| 배우자 일간 = 내 편관 | 편관배우 | 강렬한 관계; 권위 다툼 위험 |
| 배우자 일간 = 내 식신 | 식신배우 | 부드러운 관계; 표현·자녀 복 |
| 배우자 일간 = 내 상관 | 상관배우 | 갈등·언쟁 잦음; 주의 |
| 배우자 일간 = 내 정재 | 정재배우 | 재물·현실적 도움 (남성의 경우 전통적 "정처" reading) |
| 배우자 일간 = 내 편재 | 편재배우 | 큰 재물 기회; 변동성 |
| 배우자 일간 = 내 정인 | 정인배우 | 정신적·정서적 지지 |
| 배우자 일간 = 내 편인 | 편인배우 | 독특한 지원 |
| 배우자 일간 = 내 비견 | 비견배우 | 동등한 관계; 때로 경쟁 |
| 배우자 일간 = 내 겁재 | 겁재배우 | 재물·관계 갈등; 주의 |

### Combined 십신 cross-readings (classical 권인성 tradition)

| A → B | B → A | Combined reading |
|---|---|---|
| 정관 | 정인 | **가장 좋은 궁합** — 서로 신뢰·안정 (A는 B에게 규율, B는 A에게 지지) |
| 정재 | 정관 | 따뜻한 부부 — 재물·안정·질서의 결합 |
| 식신 | 정인 | 부드러운 부부 — 표현·보호 |
| 정관 | 정재 | 사회적 부부 — 권위·안정의 결합 |
| 편관 | 편관 | 강렬한 부부 — 둘 다 압박적 |
| 상관 | 상관 | 갈등 부부 — 둘 다 날카로움 |
| 겁재 | 겁재 | 갈등 부부 — 둘 다 갈등 |

### School disagreements

- **권인성·송기영 (modern Korean)**: 위 표를 표준으로 사용.
- **적천수 (임철초 주석)**: 용신 여부로 판단 — 십신이 용신이면 좋음, 기신이면 나쁨 (십신 종류 무관).
- **자평진전**: 성별에 따른 배우자-십신 매핑 사용 (남성=재성, 여성=관성).

**Tag:** [UNCERTAIN] on which 십신이 "good" — depends on (a) gender, (b) yongshin/gishin, (c) school. **Consensus rule**: 십신 + 용신 여부 + 성별 = combined verdict.

### How to compute programmatically

**Inputs needed from each chart:** day_stem, day_branch, hidden stems of day branch.

**Procedure:**

1. For each partner, classify the other's day_stem as 십신 of self: `ten_god(self.day_stem, other.day_stem)` — already exists in `lookup.py`.
2. Classify the other's day_stem as 십신 landing on self's day_branch (via hidden stems).
3. Build the cross-table.
4. Apply classical readings (above).
5. Apply 용신 modifier (적천수 원칙).

### Inputs needed from each chart

| Input | Used for |
|---|---|
| day_stem | 십신 classification of partner |
| day_branch + hidden stems | 십신 landing on spouse palace |
| yongshin, gishin | Modifier check |

### Whether it requires a new engine module

**New function in `compat.py`:** `compat_ten_god_cross(chart_a, chart_b, gender_a, gender_b) -> {a_to_b, b_to_a, pattern, score, narrative}`. Reuses `lookup.ten_god`.

### Classical weight

**10 / 100** (medium-soft; interpretive).

---

## H · Major Luck / Annual Luck Synchrony (대운·세운 호환)

### Rule

For each year or decade, both partners' 대운 + 세운 should be checked together. Classical Korean Myeongri (especially 권인성·송기영 schools) does **not** compute synchrony as a "static" score — it's a **time-bound overlay**.

### Patterns of synchrony

| Pattern | Korean | Reading |
|---|---|---|
| **Parallel 대운** (both enter new 대운 in same year or close) | 평행대운 | 인생의 큰 변화가 동시에 일어남; 함께 성장 |
| **Mirrored 대운** (one enters new 대운 as the other enters their last year of current) | 거울대운 | Life events echo; can be supportive |
| **Opposite 대운** (one enters 대운 X as the other enters 대운 X's opposite-element 대운) | 반대대운 | Tension — one rises as the other falls |
| **Synchronized difficult 대운** (both enter difficult 대운 simultaneously) | 동시고난 | Togetherness in adversity |
| **Synchronized good 대운** (both enter favorable 대운 simultaneously) | 동시호운 | Golden years together |

### For the compatibility score (static)

The **static 궁합 score** is **time-invariant**. The synchrony overlay only applies when answering a **time-bound question** ("how is our marriage in 2027?"). For static, this sub-system contributes a small **structural** weight based on whether the 두 대운 sequences broadly align (e.g., both forward or both backward; same starting-element).

### How to compute programmatically

**Inputs needed from each chart:** year_stem (for 대운 direction), gender (for 대운 direction), 대운 list.

**Procedure:**

1. Compute each partner's 대운 list (already in `engine.py` via `daeun.compute_daeun()`).
2. Compute a **direction-similarity** score: same direction = +1, opposite = 0.
3. Compute a **starting-element similarity** score.
4. Apply soft weight ~5.
5. For **time-bound** questions (specific year), compute 세운 overlay for each partner in that year, then check for synchrony/dissonance.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| year_stem, gender | 대운 direction |
| 대운 list | Sequence comparison |
| Current date | Time-bound 세운 overlay |

### Whether it requires a new engine module

**Reuses existing `daeun.py` and `sewoon.py`.** New function in `compat.py`: `compat_daeun_sync(chart_a, chart_b, target_year?) -> {direction_sim, start_elem_sim, time_overlay?, score}`. Apply only for time-bound queries.

### Classical weight

**5 / 100** (soft; time-bound overlay).

---

## I · Compatibility Star Overlays (신살 궁합)

### Rule

Each chart has stars (도화, 역마, 화개, 천을귀인, 홍염, 양인, etc.). In 궁합, classical Korean Myeongri checks **whether both charts share or activate each other's stars**.

### Key cross-star patterns

| Pattern | Korean | Classical reading | Weight |
|---|---|---|---|
| Both have 도화 in spouse palace | 쌍도화 | Strong magnetic attraction; can be romantic or unstable; **황색 flag** if 도화 is overly strong in both | -3 |
| One's 도화 = other's spouse palace | 도화스쳐 | 배타적 매력; **외도 위험** (불륜의 위험) | -5 |
| Both have 역마 in spouse palace | 쌍역마 | Both travel a lot; can mean parallel lives or "always gone" | +2 (if 양 partner's career benefits) / -2 (otherwise) |
| One's 천을귀인 = other's day branch | 귀인배우 | "배우자가 나에게 귀인의 역할" — **매우 favorable** | +5 |
| Both have 화개 in spouse palace | 쌍화개 | Solitary pattern amplified; risk of growing apart emotionally | -2 |
| Both have 양인 in chart | 쌍양인 | Strong impulse + impulse; 충동적 결혼·갈등 | -3 |
| Both have 홍염 in chart | 쌍홍염 | Very magnetic; **외도 위험 if one or both has 과한 도화** | -3 |
| 홍염 + 양인 cross | 홍양교차 | classical **"이혼 위험" 신살** (주의; 사용 자제) | -5 |

### Specific 신살 details

**홍염살 (紅艶殺)** — defined by day stem → day branch:

| Day stem | 홍염 position |
|---|---|
| 甲, 乙 | 午 |
| 丙, 丁 | 寅 or 未 |
| 戊, 己 | 辰 |
| 庚, 辛 | 戌 or 酉 |
| 壬, 癸 | 子 or 申 |

일지에 홍염 → strongest effect (배우자가 본인의 가장 큰 매력 포인트).

**양인살 (羊刃殺)** — defined by Day Master:

| Day Master | 양인 branch |
|---|---|
| 甲 | 卯 |
| 丙 | 午 |
| 戊 | 午 |
| 庚 | 酉 |
| 壬 | 子 |

### School disagreements

- **명리정종 / 적천수 (classical)**: 신살은 **descriptive overlay** — use lightly. 과도한 강조는 비고전.
- **Modern Korean 명리 (folk-influenced)**: 신살 비중이 큼 — **non-classical over-weighting**.
- **KCI empirical 2018**: 신살은 divorce study에서 **약한 correlation** (유의미하지만 결정적이지 않음).

**Tag:** [UNCERTAIN] on whether to include 신살. **Consensus**: 신살은 5/100 weight, descriptive only.

### How to compute programmatically

**Inputs needed from each chart:** day_stem, day_branch, all 4 stems, all 4 branches (for star detection).

**Procedure:**

1. Compute each partner's star list (already exists in `stars.derive_stars()` for 도화·역마·화개·천을귀인·문창·공망).
2. Add 홍염, 양인 overlays (new tables needed).
3. Check cross-star patterns from the table above.
4. Apply weights.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| day_stem, day_branch | 천을귀인·문창·홍염·양인 |
| All branches | 도화·역마·화개·공망 |

### Whether it requires a new engine module

**Extend existing `stars.py`** with 홍염 + 양인 overlays. **New function in `compat.py`:** `compat_stars(chart_a, chart_b) -> {cross_patterns, score, narrative}`.

### Classical weight

**5 / 100** (soft; descriptive overlay).

---

## J · Yin-Yang Balance (음양 조화)

### Rule

Classical Korean Myeongri checks whether the **two Day Masters** are opposite or same polarity:
- **Same polarity (both Yang or both Yin):** "similar wavelength," can be harmonious but also competitive; 권인성 school reads as **편의 (편한) but stale**.
- **Opposite polarity (one Yang, one Yin):** "complementary dynamic," traditional reading is more attractive.
- **Both Day Branches opposite polarity to each Day Master** (간여지동) is a separate (RED) flag.

### Polarity count in union

Sum the polarities of all 8 stems + 8 branches (or weighted). Healthy union: ~50/50.

### School disagreements

| School | Reading |
|---|---|
| **적천수 (임철초)** | 음양 균형은 **전체 8 글자**로 판단; 일간 일간만 보지 않음 |
| **Modern Korean** | 일간 일간 음양을 강조 — 양+음 = best |
| **자평진전** | 일간 음양보다 **오행 균형**을 우선 |
| **KCI 2018** | 음양 단독으로는 divorce correlation 약함 |

**Tag:** [UNCERTAIN] on weight. **Consensus**: 음양은 **3/100 weight** (adjuster only).

### How to compute programmatically

**Inputs needed from each chart:** all 8 stems + all 8 branches (polarity from `lookup.STEM_INFO`, `lookup.BRANCH_INFO`).

**Procedure:**

1. Compute polarity of each Day Master.
2. Compute union polarity count.
3. Score: opposite polarity Day Masters = +3, same polarity = -1.
4. Adjust by union polarity balance (50/50 ideal).

### Inputs needed from each chart

| Input | Used for |
|---|---|
| day_stem | Day Master polarity |
| All stems, branches | Union polarity balance |

### Whether it requires a new engine module

**Reuses existing `lookup.STEM_INFO`, `lookup.BRANCH_INFO`.** New function in `compat.py`: `compat_yin_yang(chart_a, chart_b) -> {dm_polarity_match, union_polarity_balance, score}`.

### Classical weight

**3 / 100** (adjuster only).

---

## K · Year-Branch Zodiac Pair (띠 궁합 / 연지 궁합)

### Rule

The two partners' **year branches** (띠, 12 animal signs) form one of several standard relationships:
- **삼합** (three-harmony): 인오술 / 사유축 / 신자진 / 해묘미 → very favorable (strong 방합 effect)
- **육합** (six-combination): the standard 6 pairs → favorable
- **상충** (clash): 자오 / 축미 / 인신 / 묘유 / 진술 / 사해 → red flag (lesser than 일지 육충)
- **방합** (directional 4): same as 삼합 but 4 branches
- **No relationship**: neutral

### Classical reading

This is the **folk layer** of 궁합 — recognizable to laypeople, intuitive, but not the deep analysis. Modern Korean 명리 treats it as a "starter hook" for client conversation.

### School disagreements

- **All classical schools**: 띠 궁합은 **most superficial** layer.
- **Modern Korean 점술** (folk-influenced): often over-weighted.
- **권인성·송기영**: 띠 궁합 = **3 weight** — useful for the opening, but not for the verdict.

**Tag:** [UNCERTAIN] on weight. **Consensus**: 3/100 (lowest weight; folk layer).

### How to compute programmatically

**Inputs needed from each chart:** year_branch.

**Procedure:**

1. Look up `(chart_a.year_branch, chart_b.year_branch)` in same branch-relationship tables as Section B (삼합/육합/방합/육충/해/파).
2. Apply weights at **half** of Section B weights.
3. Cap at 3 / 100 in composite.

### Inputs needed from each chart

| Input | Used for |
|---|---|
| year_branch | 띠 pair relationship |

### Whether it requires a new engine module

**Reuses existing `lookup.SIX_COMBINATIONS`, etc.** New function in `compat.py`: `compat_year_branch(chart_a, chart_b) -> {relation, score}`. Cap at 3 weight.

### Classical weight

**3 / 100** (lowest; folk layer; intuition hook only).

---

## Scoring Normalization and Verdict Bands

> **Engine convention, not a fixed classical canon.** The 11 sub-systems above each return a weighted contribution (positive or negative). The raw total is then mapped to a 0–100 client-facing score and one of four bands. This is a modern synthesis used to give clients a quick orientation; the breakdown of the 11 sub-systems is always more important than the single number.

**Sub-system verdict bands** (ratio = sub-system score ÷ its maximum positive score):
- **Strong** — ratio ≥ 0.65
- **Moderate** — ratio ≥ 0.30
- **Mixed / Neutral** — ratio ≥ 0.0
- **Challenging** — ratio < 0.0

**Composite bands** (after normalizing raw total to a 0–100 scale):
- **Excellent** — ≥ 80
- **Strong** — 65–79
- **Mixed** — 45–64
- **Challenging** — < 45

A score near 50 means the positive and challenging factors roughly balance; it is not a "failing" marriage, only a relationship where conscious effort matters more.

---

## How to Use This File

1. **To compute a compatibility score:** follow all 11 sub-system procedures (A–K), sum the weighted scores, and present the breakdown to the client.
2. **To interpret a specific aspect (e.g., "is the spouse palace good?"):** jump to sub-system B (일지) first, then E (일주) for the spouse-palace structural reading.
3. **To check 용신 alignment:** use sub-system D directly — it often overrides sub-system B in 궁통보감 school.
4. **To explain a specific red flag:** cite the sub-system (B, E, I) and the rule.
5. **To write the client report:** use the **Premium Client Report Pipeline** (`candidates_horoscope/README.md`) — base report + topic deep-dive + combiner + PDF. The compat section typically goes under `## Relationships` in the base report, with deep-dives in `relationships.md` and `compat-with-{name}.md`.

## Quality Checklist (run before sending a compatibility reading)

- [ ] Both charts confirmed by client (4 pillars each, including hour pillar if known).
- [ ] Day Master of each partner identified, plus Day Master strength and 용신 derived for **both** charts.
- [ ] Sub-system B (일지) checked first — note any RED FLAG 육충.
- [ ] Sub-system A (일간합) checked — note any 합 or breaking stems.
- [ ] Sub-system C (Nayin) computed.
- [ ] Sub-system D (용신 호환) computed.
- [ ] Sub-system E (일주 pair) looked up.
- [ ] Sub-system F (combined elements) computed.
- [ ] Sub-system G (십신 cross) computed.
- [ ] Sub-system I (compat star overlays) checked for cross-flag patterns.
- [ ] Sub-system H (대운 synchrony) addressed if time-bound question.
- [ ] Sub-system J (음양) sanity check.
- [ ] Sub-system K (띠) included as opener, not as verdict.
- [ ] Composite score = sum of all sub-system weights, capped at 100.
- [ ] [UNCERTAIN] tags applied where schools disagree.
- [ ] No claim is made beyond what this file supports.
- [ ] Final reading uses inclusive, non-fatalistic language — tendencies, not destinies.

## See Also

- `knowledge/01-stems.md` — Heavenly Stems
- `knowledge/02-branches.md` — Earthly Branches, 육합·충·형·파·해
- `knowledge/03-five-elements.md` — Five Elements generating/overcoming
- `knowledge/04-yin-yang.md` — Yin-Yang polarity
- `knowledge/05-ten-gods.md` — Ten Gods (십신)
- `knowledge/06-twelve-stages.md` — 12 Stages (장생~양)
- `knowledge/07-special-formations.md` — 격국 + 신살 tables (천을귀인, 도화, 역마, 화개)
- `knowledge/08-luck-pillars.md` — Major Luck (대운)
- `knowledge/09-interpretation-method.md` — Step-by-step reading procedure
- `knowledge/10-output-template.md` — Output template

## Sources & Classical References

- 적천수천미 (滴天髓闡微), 임철초 (任鐵樵) 주석 — primary classical source for 궁합 principle "夫婦以生化爲最貴"
- 연해자평 (淵海子平) — "婚姻宜避刑沖"
- 자평진전 (子平眞詮) — "以日干爲我" — 일간 중심 분석
- 궁통보감 (窮通寶鑑) — 60 갑자 용신·조후의 결정 텍스트
- 삼명통회 (三命通會), 만민영 (萬民英) — Ming dynasty 명리 종합서, 합혼법
- 명리탐원 (命理探原), 원수산 (袁樹珊) — spouse palace 분석
- 서전구미록 (書傳九微錄) — 납음 궁합의 가장 체계적 정리
- 명리정종 (命理正宗) — Korean classical 종합서
- 권인성·곽임성·정봉재·송기영 — modern Korean 명리 schools (cited per sub-system)
- KCI ART002338687 (남기동·김만태 2018) — "한국사회 이혼현상에 따른 부부궁합의 명리학적 고찰"
- KCI ART002969199 (이수동 2023) — "조후(調候) 관점의 궁합이론 연구"
- DBpia 김우정 2025 — "적천수천미 여명장의 현대적 고찰: 부성용신론"