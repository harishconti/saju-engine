# 07 · Special Formations (격국 · 신살 · 합 · 충 · 형 · 파 · 해)

This file covers the **structural and overlay** patterns that classical 명리 uses to read a chart in addition to the standard ten-god analysis.

## Part 1: 격국 (格局) — Chart Structures (Grids)

The 격국 is the **dominant pattern** of the chart. The classical 자평진전 (子平眞詮) / 연해자평 (淵海子平) / 명리정종 (命理正宗) method is:

1. Look at the **월지 (month branch) hidden stems** in priority order: 본기 (本氣, main) → 중기 (中氣, middle) → 여기 (餘氣, residual).
2. The first hidden stem that **투출 (透出)** — i.e. transparently appears on a 천간 (heavenly stem) of **any** pillar — determines the 격국. Its ten-god relation to the Day Master names the grid (e.g. 정관격, 식신격).
3. If **multiple** hidden stems 투출, 본기 takes precedence.
4. If **none** 투출, fall back to the 월지 본기 hidden stem.

> **School note.** A minority Korean school reads the visible 월간 directly (without 투출). The engine in `src/saju_engine/patterns.py` follows the **classical 투출 method** (본기 → 중기 → 여기, first 투출 wins, 본기 fallback) per Ground Rule 7 (prefer classical). When the visible 월간 itself is a 투출 of a 월지 hidden stem, both methods agree.

### A. Regular Grids (정격, 正格)

> **Trigger column reads per the classical 투출 method above** (month-branch hidden stem 투출 onto a visible stem = X of the Day Master), matching what `src/saju_engine/patterns.py` implements — not the minority 월간 (visible month stem) school also mentioned above. *(Corrected 2026-09-20 — external report review, 4th pass: this table previously said "Month stem = X," which is the minority school's rule, contradicting Part 1's own declared classical method and the glossary's "most powerful stem in the month branch" phrasing. When the visible 월간 is itself a 투출 of the month branch's hidden stem, both readings agree.)*

| Grid | Korean | Trigger | Day Master tendency | Career / Life tendency |
|---|---|---|---|---|
| 비견격 / 겁재격 | 比肩格 / 劫財格 | 월지 hidden stem 투출 = 비견 or 겁재 of Day Master | Day Master strengthened by month | Self-reliance, peer competition, may be stubbornly independent |
| 식신격 | 食神格 | 월지 hidden stem 투출 = 식신 of Day Master | Day Master strong, channeled through output | Steady, productive, nourishment-oriented, often good in food / care / service |
| 상관격 | 傷官格 | 월지 hidden stem 투출 = 상관 of Day Master | Day Master strong, output is sharp | Creative, rebellious, sharp in speech, often artistic but may clash with authority |
| 편재격 | 偏財格 | 월지 hidden stem 투출 = 편재 of Day Master | Day Master strong, wealth is variable | Entrepreneurial, speculative, large income swings, social/visible |
| 정재격 | 正財格 | 월지 hidden stem 투출 = 정재 of Day Master | Day Master strong, wealth is stable | Conservative finance, steady earning, careful saving, traditional |
| 편관격 | 偏官格 | 월지 hidden stem 투출 = 편관 (칠살) of Day Master | Day Master strong, authority is forceful | Competitive, high-pressure careers, military/political, sometimes risk of accidents |
| 정관격 | 正官格 | 월지 hidden stem 투출 = 정관 of Day Master | Day Master strong, authority is conventional | Government, large companies, exams, conventional respectability |
| 편인격 | 偏印格 | 월지 hidden stem 투출 = 편인 of Day Master | Day Master strong, support is unconventional | Specialized knowledge, solitary scholarship, sometimes strangeness |
| 정인격 | 正印格 | 월지 hidden stem 투출 = 정인 of Day Master | Day Master strong, support is maternal | Education, certificates, real estate, mother's influence, gradual advancement |

### B. Special Grids (특수격, 特殊格)

These grids apply when the Day Master is **either very weak or very strong** in unusual ways. They are read only when their specific conditions are met.

#### 1. 종격 (從格, Following Grid) — Day Master is too weak to stand

The Day Master is **overwhelmed** by the chart. The querent's "self" is not the dominant force — the chart's environment is. The querent is "carried" by a single dominant force.

Conditions:
- Day Master has **no support** (no 인성, no 비겁, and **no** seasonal support).
- The month stem is **powerful** in the dominant element of the chart.
- 한 (the Day Master) is "in" the chart but has no ally.

Subtypes:
- **종재 (從財):** The chart is dominated by wealth. The querent lives for / is defined by money or possessions.
- **종관 (從官):** The chart is dominated by authority. The querent lives for / is defined by discipline, career, or institutional life.
- **종식상 (從食傷):** The chart is dominated by output. The querent lives for / is defined by expression, creativity, or children.
- **종인 (從印):** Rare. The chart is dominated by resource. The querent lives for / is defined by support, learning, mother figures.
- **종자 (從子):** Rare. The chart is dominated by child / output but read through the "child" lens.

In 종격, the **favorable element (용신) is the dominant element itself** — the querent should align with the chart, not fight it. Choosing a path that "follows" the dominant element is more successful than fighting it.

#### 2. 화격 (化格, Transformation Grid) — Day Master is "transformed"

The month stem is a **변 (變, transforming) stem** that combines with another stem in the chart to **transform into a different element**. The new element is the Day Master's "adopted element" — it represents the querent's deep nature.

Conditions for a true 화격:
- The month stem must be the **합 partner** of either the Day Master's element or the year stem, and the two must **fully combine** (no breaking stem present).
- The combined element must be **in season** at the month branch.
- The Day Master must be **isolated** — not strongly supported by allies.

If all conditions are met, the new element is treated as the Day Master's effective identity. 용신 is then derived from the new element, not the original.

> Example: 甲 day master + 己 in month branch + no 乙/庚 breaking force + month branch is Earth season → 甲己合化土, the querent is "earth-toned" — practical, grounded, deliberate.

**Breaker stems (간섭, 干涉).** Classical texts name the following stems as disruptive to the five 천간합 pairs:

| Combination | Combined Element | Breaking Stems | Reason |
|---|---|---|---|
| 甲己合 | Earth | 乙, 庚 | 乙 competes with 甲 for 己; 庚 clashes with 甲 |
| 乙庚合 | Metal | 甲, 辛 | 甲 competes with 乙 for 庚; 辛 competes with 庚 for 乙 |
| 丙辛合 | Water | 丁, 壬 | 丁 competes with 丙 for 辛; 壬 clashes with 丙 |
| 丁壬合 | Wood | 丙, 癸 | 丙 competes with 丁 for 壬; 癸 competes with 壬 for 丁 |
| 戊癸合 | Fire | 己, 甲 | 己 competes with 戊 for 癸; 甲 clashes with 戊 |

A breaker is considered **effective** only when it is powerful — i.e. rooted in a natal branch (visible or hidden) **or** its element is in season at the month branch. A floating breaker with no root or seasonal support is too weak to dissolve the combination; it may create friction but not cancel the 합.

#### 3. 양인격 (羊刃格, Blade of the Sheep) — Day Master is in its 제왕 branch

A specific 격국 where the Day Master is in its peak branch (제왕 in the 12운성 cycle) and that branch appears in the **year, day, or hour pillar**.

- 甲 day master in 卯 (제왕) → 양인
- 丙 day master in 午 → 양인
- 戊 day master in 午 → 양인 (since Earth follows Fire's cycle)
- 庚 day master in 酉 → 양인
- 壬 day master in 子 → 양인

양인격 is read as a **double-edged sword**: the querent has great personal power, decisiveness, and capacity, but also the tendency to act recklessly, be isolated, or attract conflict.

#### 4. 건록격 (建祿格) — Day Master is in its 건록 branch

A sub-pattern where the Day Master is in its 건록 (earning / strong) branch:
- 甲 in 寅 (건록)
- 丙 in 巳
- 戊 in 巳
- 庚 in 申
- 壬 in 亥

건록격 is favorable — the querent has natural self-sufficiency and earning capacity. Often a person with steady income and quiet confidence.

#### 5. 병월 (病月) / 고월 (庫月) variations — minor patterns

Some 명리 schools distinguish minor variations in the month branch's hidden-stems arrangement, but these are not as widely agreed upon as the above. Reference only with care.

## Part 2: 신살 (神殺) — Star Formations

신살 are **named stars** that overlay on top of the basic chart. They come from the **day branch** (some schools use year branch or year stem).

> The classical school of **명리정종** and the Korean traditional reading tend to use 신살 **lightly** — they describe tendencies, not fixed traits. The classical **적천수** and **연해자평** treat them as descriptive overlays.

### Common 신살

#### 도화살 (桃花殺) — Peach Blossom Star

**Day-branch-based** (most common):
- Born in 寅 / 午 / 戌 → 도화 at 卯
- Born in 巳 / 酉 / 丑 → 도화 at 午
- Born in 申 / 子 / 辰 → 도화 at 酉
- Born in 亥 / 卯 / 未 → 도화 at 子

**Year-branch-based** (alternative school):
- Born in 寅 / 午 / 戌 → 도화 at 卯
- Born in 巳 / 酉 / 丑 → 도화 at 午
- Born in 申 / 子 / 辰 → 도화 at 酉
- Born in 亥 / 卯 / 未 → 도화 at 子

> Same pattern for both, in classical Korean 명리. The 도화 is the branch where 도화 resides. *(Corrected 2026-09-20 — external report review, 4th pass: a mixed Hangul/Hanja artifact, "도桃花," previously stood in for "도화.")*

**Meaning:** Charm, attractiveness, romantic magnetism, artistic sensibility, sensitivity to beauty. Excessive 도화 can indicate romantic complications or vanity. 도화 in the spouse palace (day branch) → very magnetic in relationships.

#### 역마살 (驛馬殺) — Post Horse Star

**Day-branch-based**:
- 寅 / 午 / 戌 → 역마 at 申
- 巳 / 酉 / 丑 → 역마 at 亥
- 申 / 子 / 辰 → 역마 at 寅
- 亥 / 卯 / 未 → 역마 at 巳

**Meaning:** Movement, travel, relocation, change of environment. Strong in those whose careers or lives involve movement. Excessive 역마 → "always moving, never arriving." 역마 in spouse palace → partner from a distance or one who moves a lot.

#### 화개살 (華蓋殺) — Canopy Star

**Day-branch-based**:
- 寅 / 午 / 戌 → 화개 at 戌
- 巳 / 酉 / 丑 → 화개 at 丑
- 申 / 子 / 辰 → 화개 at 辰
- 亥 / 卯 / 未 → 화개 at 未

**Meaning:** Solitary star. Often found in those drawn to religion, scholarship, art, philosophy, or a hermetic life. 화개 + 도화 → "religious-romantic" pattern (often monastics, artists, contemplatives). 화개 + 역마 → "wandering scholar."

#### 귀문관살 (鬼門關殺) — Ghost Gate Star

Less common in modern Korean readings. **See the "More classical 신살" section below for the actual branch-pair table this star is checked against** — the rule is a full six-pair lookup (子酉, 丑午, 寅未, 卯申, 辰亥, 巳戌), matching `src/saju_engine/stars.py::_GHOST_GATE_PAIRS`, not a vague "born in 子 or 午" rule.

**Meaning (classical):** Sensitivity to the unseen, sometimes psychic tendencies, sometimes "curse" patterns. **Use with care** — some schools treat this as a serious omen, others as a descriptive overlay only.

*(Corrected 2026-09-20 — external report review, 4th pass: this section previously stated an unimplemented, vague rule ("born in 子 or 午 → concern in opposing branches") that duplicated and contradicted the fuller, engine-matching pair-table definition later in this same file, with no reconciliation note. The vague rule is removed; this entry now points to the authoritative table.)*

#### 천을귀인 (天乙貴人) — Heavenly Noble / Helper Star

**Day-stem-based** (a benign star):
- 甲 day master → 丑 or 未
- 乙 → 子 or 申
- 丙 → 亥 or 酉
- 丁 → 亥 or 酉
- 戊 → 丑 or 未
- 己 → 子 or 申
- 庚 → 丑 or 未
- 辛 → 寅 or 午
- 壬 → 卯 or 巳
- 癸 → 卯 or 巳

**Meaning:** A "helper" star — indicates that at critical moments, a noble person will appear to assist. Not a fixed protection; a tendency toward receiving help at key turning points.

#### 문창귀인 (文昌貴人) — Literary Star

**Day-stem-based**:
- 甲 → 亥
- 乙 → 午
- 丙 → 申
- 丁 → 酉
- 戊 → 申
- 己 → 酉
- 庚 → 亥
- 辛 → 子
- 壬 → 寅
- 癸 → 卯

**Meaning:** Favorable for academic and literary work, exams, written expression. Indicates native facility with words and ideas.

### More classical 신살 (star overlays)

The engine also recognizes the following additional classical stars. They are treated as **descriptive overlays**, not deterministic predictions.

#### 십이신살 (十二神殺) — Twelve Stars

Derived from the **day branch's three-harmony triplet**. The table below gives the star position for each of the four triplets.

> **School note — anchor branch (added 2026-09-26, E-7).** Traditional Korean practice anchors the
> 12신살 primarily on the **year branch (년지)**; many modern readers use the **day branch (일지)**, and
> many check both. Both use the same triplet table — only the anchor changes, so a chart's stars can
> differ completely between the two bases. This engine defaults to the day branch (consistent with its
> 도화/역마/화개 default) and supports year-branch anchoring via `anchor="year"`. Readers should state
> which basis they are using. Sources: 두루미사주 12신살 사전 ("년지를 기준으로 삼합 그룹에 따라"),
> 류동학, 대구신문 「12신살의 이론과 적용」; see `docs/audits/2026-09-25-engine-audit-verification.md`.

| Day-branch triplet | 겁살 (劫煞) | 재살 (災煞) | 천살 (天煞) | 지살 (地煞) | 연살 (年煞) | 월살 (月煞) | 망신 (亡神) | 장성 (將星) | 반안 (攀鞍) | 역마 (驛馬) | 육해 (六害) | 화개 (華蓋) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 寅午戌 | 亥 | 子 | 丑 | 寅 | 卯 | 辰 | 巳 | 午 | 未 | 申 | 酉 | 戌 |
| 申子辰 | 巳 | 午 | 未 | 申 | 酉 | 戌 | 亥 | 子 | 丑 | 寅 | 卯 | 辰 |
| 巳酉丑 | 寅 | 卯 | 辰 | 巳 | 午 | 未 | 申 | 酉 | 戌 | 亥 | 子 | 丑 |
| 亥卯未 | 申 | 酉 | 戌 | 亥 | 子 | 丑 | 寅 | 卯 | 辰 | 巳 | 午 | 未 |

> **Note:** 도화 (桃花), 역마 (驛馬), and 화개 (華蓋) already have dedicated sections above and are not duplicated here.

**Meanings (classical descriptive):**
- **겁살 (劫煞):** Sudden loss, theft, unexpected competition; can also mark decisive action.
- **재살 (災煞):** Mishaps, illness, obstacles; often softened by a strong 용신.
- **천살 (天煞):** External pressures, authority conflicts, "heaven-sent" trials.
- **지살 (地煞):** The movement/departure star — relocation, travel, job or residence changes; the milder, more passive sibling of 역마 (역마 is active, 지살 is change that arrives). *(Corrected 2026-09-26, E-7: previously mis-described as "hindrances, delays".)*
- **연살 (年煞):** In the 12신살 sequence 연살 falls on the same branch as 도화 (桃花) and is read the same way — charm, attraction, social visibility (see §도화 above). *(Corrected 2026-09-26, E-7.)*
- **월살 (月煞):** Also called 고초살 (枯焦殺) / 고갈살 (枯渴殺) — the drying-up/stagnation star: slow development, effort that does not yet bear fruit, a need for patience and replenishment. *(Corrected 2026-09-26, E-7: previously mis-described as "romantic turbulence".)*
- **망신 (亡神):** Mental dispersion, forgetfulness, scattered energy; can indicate hidden schemes.
- **장성 (將星):** Leadership, command, organizational ability.
- **반안 (攀鞍):** Advancement, promotion, riding a rising wave.
- **육해 (六害):** Covert harm from the six-harm branch direction.

#### 원진살 (怨嗔煞) — Deep Grudge Star

A **branch-pair** star. If two of the following pairs appear in the natal chart (in any pillars), the pair is flagged.

| Branch pair | |
|---|---|
| 子 | 未 |
| 丑 | 午 |
| 寅 | 酉 |
| 卯 | 申 |
| 辰 | 亥 |
| 巳 | 戌 |

**Meaning:** Lingering resentment, unfinished conflict, difficulty letting go of grievances. In relationships it can point to recurring arguments that never fully resolve.

#### 귀문관살 (鬼門關煞) — Ghost Gate Star

A **branch-pair** star. When the day branch (or another natal branch) meets its paired branch elsewhere in the four pillars, the star is considered active.

| Branch | Ghost-gate pair |
|---|---|
| 子 | 酉 |
| 丑 | 午 |
| 寅 | 未 |
| 卯 | 申 |
| 辰 | 亥 |
| 巳 | 戌 |

**Meaning:** Sensitivity to hidden matters, the unseen, or unusual life-turning events. Some schools treat it as a serious caution; the classical Korean reading treats it as a **descriptive sensitivity marker** only.

> **Note on overlap with 원진살.** This pair list shares 4 of its 6 pairs with 원진살's list above (丑午, 卯申, 辰亥, 巳戌); only 子/丑↔酉/未 differ (원진: 子未, 寅酉; 귀문관: 子酉, 寅未). Both are genuine, separately-named classical stars — the overlap is a known feature of how these two star systems were historically derived, not a duplication error — but a chart matching one pair often also matches (or nearly matches) the other, so expect the two readings to co-occur. *(Added 2026-09-20 — external report review, 4th pass.)*

#### 괴강살 (魁罡煞) — Sky Hero Star

Based on the **day pillar (일주, 日柱)**. The four classical 괴강 pillars are:

- **壬辰**, **庚辰**, **庚戌**, **戊戌**

**Meaning:** Strong will, charisma, leadership, decisiveness; also a tendency toward extremity and conflict if the chart is not balanced.

#### 백호대살 (白虎大煞) — White Tiger Star

Based on the **day pillar (일주, 日柱)**. The commonly cited seven 백호대살 day pillars are:

- **甲辰**, **乙未**, **丙戌**, **丁丑**, **戊辰**, **壬戌**, **癸丑**

**Meaning:** Intensity, sudden force, surgical or martial precision; can bring accidents or conflicts if unchecked, but also the capacity for decisive action.

#### 천덕귀인 (天德貴人) — Heavenly Virtue Noble

Derived from the **month branch (월지, 月支)**. The target stem is looked for among the four natal 천간.

| 월지 | 천덕귀인 |
|---|---|
| 寅 | 丁 |
| 卯 | 申 |
| 辰 | 壬 |
| 巳 | 辛 |
| 午 | 亥 |
| 未 | 甲 |
| 申 | 癸 |
| 酉 | 寅 |
| 戌 | 丙 |
| 亥 | 乙 |
| 子 | 巳 |
| 丑 | 庚 |

**Meaning:** Virtue, protection, honorable character, and help arriving in times of need. Often regarded as one of the most favorable stars.

#### 월덕귀인 (月德貴人) — Monthly Virtue Noble

Derived from the **month branch (월지, 月支)** via its three-harmony element direction. The target stem is looked for among the four natal 천간.

| 월지 | 월덕귀인 |
|---|---|
| 寅 | 丙 |
| 卯 | 甲 |
| 辰 | 壬 |
| 巳 | 庚 |
| 午 | 丙 |
| 未 | 甲 |
| 申 | 壬 |
| 酉 | 庚 |
| 戌 | 丙 |
| 亥 | 甲 |
| 子 | 壬 |
| 丑 | 庚 |

**Meaning:** Monthly/quarterly support, popularity, and smooth assistance from people around the querent. 천덕 + 월덕 together is called 천월이덕 (天月二德) and is considered especially auspicious.

#### Terms intentionally not implemented

The following terms appear in some specialized texts but lack a single standardized lookup table across the major Korean classical schools, so the engine does not compute them:
- **혈각 (血角)**, **관부 (關符)**, **폐문 (閉門)**, **고각 (孤角)**, **사의 (死意)**, **양록 (陽祿)**, **음록 (陰祿)**, **학당 (學堂)**, **문곡 (文曲)**.
If a reading references any of these, state the school/source explicitly and mark the interpretation `[UNCERTAIN]`.

## Part 3: 합 / 충 / 형 / 파 / 해 (Branch Relationships)

These were covered in `02-branches.md`; summarized here for quick lookup with respect to special formations.

| Relationship | Korean | Hanja | Pairs (six each) | Tone |
|---|---|---|---|---|
| Combination | 합 | 合 | 육합 (6 pairs) + 삼합 (4 triples) | Binding, attractive, stabilizing |
| Clash | 충 | 沖 | 子午, 丑未, 寅申, 卯酉, 辰戌, 巳亥 | Disruptive, activating, sudden |
| Punishment | 형 | 刑 | 삼형 (2 triples + 子卯) + 자형 (4 self-pairs) — see `02-branches.md` | Legal trouble, injury, conflict with authority |
| Self-punishment | 자형 | 自刑 | 辰辰, 午午, 酉酉, 亥亥 | Inner torment, self-destructive |
| Harm | 해 | 害 | 6 pairs (see 02) | Covert friction |
| Break | 파 | 破 | 6 pairs (see 02) | Erosion, lost trust |

> *(Added 2026-09-20 — external report review, 4th pass: this table's title has always included 형, but the row itself was missing — see `02-branches.md`'s "Branch Three Punishments (삼형)" section for the full 寅巳申/丑戌未/子卯 tables.)*

### When a Relationship "Activates" an Event

- A natal relationship between two branches becomes a "live event" when:
  1. A **major luck pillar (대운)** brings one of the two branches.
  2. An **annual pillar (세운)** brings one of the two branches.
  3. The Day Master's current running element is the same as the activating branch.

> Example: 丑未 충 in natal chart. 대운 brings 丑 → the chart's 未 branch is "activated" by clash → events in the domains of 未 (e.g., 未 = Earth, also spouse-related) come to the fore.

## How to Use This File

- To identify a chart's 격국 → use the Regular Grids / Special Grids tables.
- To identify a 신살 → use the relevant star's lookup table, keyed off the day branch (or year branch / day stem as the school dictates).
- To identify structural relationships → use the 합/충/형/파/해 table.
- To interpret when a relationship "activates" → use the activation rule.
- For non-classical 신살 (e.g., 역마-based schools), state the school being used to avoid confusion.
