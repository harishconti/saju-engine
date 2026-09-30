# Research — 조후 Gate: Chart-Extremeness Threshold (N-6)

**Workstream:** deep-audit N-6 · **Date:** 2026-09-26 · **Subsystem:** `src/saju_engine/climate.py` + `src/saju_engine/yongsin.py`
**Rule base:** `knowledge/17-climate-method.md`, `knowledge/09-interpretation-method.md` Step 3
**Question:** the 조후 override currently keys on the **month branch alone**. The sourced doctrine
conditions it on the whole chart being climate-extreme ("사주가 너무 차거나 너무 더우면"). No
threshold was available, so N-6 was parked pending research. This document reports the research.

---

## 1. What the audit found

`climate.assess_climate(month_branch)` takes only the month branch, so the override fires for
every chart born in a non-temperate month (8 of 12 branches) regardless of whether the *chart* is
actually climate-extreme. Across 1,500 random charts: 66% are climate-governed; in **9% of all
charts** the prescribed remedy element is already the chart's **most abundant** element.

**Audit's two cited examples** (reproduced here, 2026-09-26):

| Chart | Pillars | Month band | Chart state |
|---|---|---|---|
| 1963-10-24 11:00 | 癸壬庚辛 / 卯戌子巳 | 戌 → dry → Water | 36% Water already (壬, 癸, 子) — Water is the most-abundant element |
| 2010-12-06 01:00 | (weak 庚 DM) | 亥 → cold → Fire | Fire 35% already; Fire is this chart's 관살 = its 기신 |

---

## 2. What the primary classical text actually says

The doctrinal basis is 적천수 (滴天髓), chapters **二十九 寒暖** and **三十 燥濕**, with 任鐵樵's
(임철초) commentary (滴天髓闡微). Transcribed from 維基文庫 / ctext.org (directly reviewed
2026-09-26):

> 天道有寒暖，发育万物，人道行之，**不可过也**。 — §29 寒暖, original text
>
> 地道有燥湿，生成品泯，人道得之，**不可偏也**。 — §30 燥濕, original text

The commentary is explicit that the disease is **excess / one-sidedness of the whole chart**, not
merely the birth month:

> ...本文末句"不可过也"，适中而已矣。**寒虽甚，要暖有气；暖虽至，要寒有根**，则能生成万物。若寒甚而暖无气；过于暖者，反以无寒为宜也。
> — 任氏曰, §29

> ...**过于湿者，滞而无成；过于燥者，烈而有祸** ... 皆偏枯也。
> — 原注, §30

and, decisively for the gate, §29's own commentary adds that when the excess is absolute, the
remedy is **withheld** rather than applied:

> 若原局全是极寒、极湿、极暖、极燥之气，反不宜调候，应该顺其势。

**Conclusion §2:** the classical text confirms the *principle* (a chart must be **extreme**
before 조후 governs — "不可過/不可偏/過於") but states it qualitatively. **It gives no numeric
threshold.** So a threshold cannot be transcribed from the classics; it has to be sourced from
practitioner commentary that operationalises the classical "不可過" test, or left unimplemented.

---

## 3. Practitioner sources that DO give a concrete criterion

Two independent Korean practitioner sources state a numeric whole-chart test. A third
commercial engine documents the same scoring *method* without publishing its cutoff.

### 3a. 사주플러스 / 현산玹山 — 「격국용신(8)-한난조습에 따른 조후용신 취용법」

> 1).목화가 용신인 경우: 월지가 해,자,축월이면서 **월지 포함 4개 이상의 글자가 추운 글자**인 경우
> 2).금수가 용신인 경우: 월지가 사,오,미월이면서 **월지 포함 더운 글자가 4개 이상**인 경우
> 3).조습은 실무에서는 많이 적용하지 않습니다.

— <https://sajuplus.tistory.com/2775> (scraped 2026-09-26)

Character lists given there: 추운 글자 (cold) = 천간 壬癸庚辛己 · 지지 酉戌亥子丑寅;
더운 글자 (hot) = 천간 丙丁甲乙戊 · 지지 巳午未申卯辰. The criterion is **≥ 4 of the 8 characters
(month included)** in the season's temperature class. It also notes 燥濕 is rarely applied in
practice — matching the engine's conservative 辰/戌 handling.

### 3b. 네이버 / 촌노 — 「조후용신(調候用神)」

> (5) 구체적인 판단방법 — 조후를 판단할 때 **지지를 위주로** 판단하는 것이 중요하다.
> ① 亥子丑寅월이고 **지지 3개 또는 4개가 추운 글자**이면 木火용신이다.
> ② 巳午未申월이고 **지지 3개 또는 4개가 더운 글자**이면 金水용신이다.
> ③ 丑辰월이고 지지 3개 또는 4개가 습한 글자이면 火, 燥土가 필요하다.
> ④ 戌未월이고 지지 3개 또는 4개가 마른 글자이면 水, 濕土가 필요하다.
> 위 경우에 해당하지 않을 경우, ... ① 지지에 추운 글자가 3개이상(>=3)이고 천간지지에 추운
> 글자가 **5개이상이면 火용신** / ② 지지에 더운 글자가 3개이상(>=3)이고 천간지지에 더운 글자가
> **5개이상이면 水용신**

— <https://m.blog.naver.com/hs72hs72/60214125204> (scraped 2026-09-26)

This version is **branch-weighted** — a majority of the **four branches** (≥3 of 4) is the
primary test, with a whole-chart fallback (branch ≥3 **and** total ≥5 of 8). It gives the fuller
cold/hot character lists including the secondary "차가운/따뜻한" (cool/warm) tier.

### 3c. 정해 만세력 (8-codes) — documents the same method, no cutoff

> 천간, 지지의 각 글자마다 각각 한난, 조습에 해당하는 점수를 부여하고 이를 조합하여 사주의
> 온도와 습도를 구합니다. 이때, **월지와 시지에 더 큰 가산점**을 주어 구합니다.
> ... 조후가 중화되어 있을수록 조후 용신의 중요성은 떨어지고, 지나치게 춥거나 더운 경우
> 조후 용신의 중요성이 커집니다.

— <https://doc.8-codes.com/docs/origin/yongsin/> (scraped 2026-09-26)

This independently corroborates the *shape* of the fix (a whole-chart temperature score, with
month/hour branches weighted higher) but does not publish its threshold — so it is method
corroboration, not a second threshold.

### 3d. 「调候用神一定有用吗？什么情况不适合用调候？」 (算准网) — when NOT to apply

> 1. 适用条件 ... 命局五行之气基本畅通，仅仅是整体格局偏寒或者偏燥 ...
> 2. 不宜使用的情况 ... **正格用神已经十分明确** ... **命局大运流年五行已经达到平衡** ...

— <https://www.suanzhun.net/article/2783.html>

Supports the gate direction: 조후 is a *temporary* remedy ("临时用神") that should not displace a
clear 정격/억부 answer, and should not fire when the chart is already balanced.

---

## 4. Convergent criterion and measured impact

Both numeric sources agree on the same test in structure:

- **Month must be in the season:** cold 亥子丑 (naver adds 寅), hot 巳午未 (naver adds 申).
- **The chart must be dominated by that temperature:** sajuplus = ≥4 of 8 characters;
  naver = ≥3 of 4 **branches** (with a ≥5-of-8 whole-chart fallback).
- **If not dominated → no 조후 override** (억부 governs), and for absolute excess the remedy is
  withheld entirely (적천수 §29).

A candidate gate implementing naver's primary branch test — the chart must be extreme **in the
same direction as its month band** (hot/dry month → ≥3 of 4 branches hot; cold/damp month → ≥3 of
4 branches cold) — was measured against the live engine, 2026-09-26. (Note: the gate must be
direction-consistent; early drafts checked only "≥3 hot OR ≥3 cold" and wrongly fired a hot month
on a cold-dominated chart.)

| Metric (4,000 random charts) | Current (month-only) | With whole-chart gate |
|---|---|---|
| Charts where 조후 fires | 2,600 (~66%) | 1,323 (**suppresses 49%** of current overrides) |
| Remedy already the chart's **most-abundant** element | 14.7% of fired | 4.8% of fired |

**The gate does materially fix the audit's complaint** (the "remedy already dominant" rate drops
from 14.7% to 4.8%) while keeping Fire-for-cold / Water-for-hot for genuinely extreme charts.

### Effect on the audit's two examples

| Chart | Month band | Current | Gate result |
|---|---|---|---|
| 1963-10-24 11:00 (36% Water) | 戌 dry | Water override | **fires** (3 hot/dry branches) → Water stays; the fix here is *not* the gate |
| 2010-12-06 01:00 (Fire = 기신) | 亥 cold | Fire override | **suppressed** (2 cold branches) ✓ |

**Correction from an earlier draft of this doc:** the gate corrects the second audit example
(2010) but **not the first** (1963-10-24) — that chart has 3 hot/dry branches (卯戌巳), so a
branch-count gate lets the Water override through. The 1963 case is exactly the "remedy already
dominant" failure that option **C** (suppress when the remedy is already dominant) targets. The
branch-count gate and the remedy-dominance guard are therefore **complementary**, not
alternatives — see §5.

### Effect on published candidates (measured, not assumed)

| Candidate | Month | Current band | Gate fires? | Current 용신 | If gated |
|---|---|---|---|---|---|
| harish | 巳 | hot | no (1 hot branch) | Water | **Wood** ← changes |
| mahesh | 丑 | cold | no (2 cold branches) | Fire | **Water** ← changes |
| vishnu-priya | 午 | hot | no (2 hot branches) | Water | Water (억부 candidate is also Water) — no change |
| sruthi | 子 | cold | yes (3 cold branches) | Earth *(override)* | Earth — unchanged (override) |
| gurumoorthy | 未 | hot | no (2 hot branches) | Metal *(override)* | Metal — unchanged (override) |
| manvitha | 亥 | cold | yes (3 cold branches) | Fire | Fire — unchanged |
| rm / pawan | 酉 | temperate | no | Water / Wood | unchanged |

So the gate would change the resolved 용신 for **Harish** (Water → Wood) and **Mahesh**
(Fire → Water) — both client-visible. Vishnu Priya is unchanged despite her override being
suppressed because her 억부 candidate is the same element. Harish and Mahesh are both canonical
demo/candidate charts, and Harish's Water-용신 was the headline result of the 2026-09-13 climate
work — so this needs explicit approval, not a unilateral fix.

---

## 5. Decision — the industry-standard whole-chart temperature gate. IMPLEMENTED.

The user asked for the **industry standard**. Research into the major Korean engines settled it:
both **정해 만세력 (8-codes)** and **사주플러스** judge 한난 (temperature) from the **whole chart**,
not the month alone — 8-codes as a weighted per-character temperature score with month/hour
weighted higher, 사주플러스 with a published per-character 한난 table and "월지 중심" reading. So
the audit's N-6 recommendation (weigh Fire/Water across stems and hidden stems, gate on that) *is*
the industry standard. It is implemented as two gates; the element stays month/stem-derived.

### What was implemented

`climate.climate_temperature(pillars)` — the weighted whole-chart 한난 score (positive = warm/木火,
negative = cool/金水), using the 사주플러스 per-character assignment (stems 한 甲辛壬癸 / 난 乙丙丁庚,
neutral 戊己; branches 한 寅酉戌亥子丑 / 난 卯辰巳午未申) and the 8-codes position weighting (month
×2, hour ×1.5; hidden stems at a fraction). Two threshold-free gates then decide priority:

1. **Direction gate (寒暖 axis)** — `is_climate_extreme()`. For a hot (巳午未) or cold (亥子丑)
   month, if the whole chart clearly leans *opposite* its month (a hot month whose chart reads
   cool, or vice versa, beyond `_NEUTRAL_TEMPERATURE_MARGIN`), the "사주가 너무 차거나 너무
   더우면" condition is not met and the override is withheld. (辰戌 are the 燥濕/humidity axis,
   which this *temperature* score cannot judge, so they are not gated on it.)
2. **Remedy-dominance guard** — `is_remedy_dominant()`. If the prescribed remedy is already the
   chart's most-abundant element, adding more cannot balance the chart. Covers 辰戌 and any other
   oversaturation.

**Why the element stays month-derived.** Both the branch-count gates (A/B) *and* a naive
whole-chart-temperature element derivation would **contradict 궁통보감's unconditional per-stem
rule** — 四月辛金 (Harish's exact chart) prescribes 壬水 regardless of the rest of the chart:

> 四月辛金，必喜庚壬为用 … 忌丙火之燥烈，喜壬水之洗淘 … 如壬癸水俱无，但见烈烈火攻，金被火鎔
> — 窮通寶鑑 (四月辛金), transcribed via <https://www.dajiazhao.com/sm/qtbj/6178.html>

Harish's chart scores ≈0.0 on the temperature scale (genuinely neutral), so an element-from-
temperature rule would flip his validated Water → an unsourced element. Ground Rule 1 (classical
wins) therefore forbids deriving the *element* from the chart-wide score; only the *priority* is
gated. This also matches 사주플러스's "한난은 월지 중심" and the classical stem×month structure.

**Measured impact** (4,000 random climate-governed charts): the direction gate withholds the
clearly-contradicted ~9%, the dominance guard ~14%, together ~21% — and **every published
deliverable is unchanged** (Harish Water, Mahesh Fire, Vishnu Priya Water, Manvitha Fire, RM
Water; Gurumoorthy/Sruthi/Pawan are reader-overrides). Both audit examples are corrected:
1963-10-24 (dry/Water, remedy already dominant) and 2010-12-06 (cold/Fire, remedy already
dominant) now resolve via 억부.

### Remaining [UNCERTAIN]

`_NEUTRAL_TEMPERATURE_MARGIN = 1.0` is an **operational choice** — the engines publish no cutoff —
and is flagged `[UNCERTAIN]` in knowledge/17. It is deliberately conservative (withholds only the
clearly-contradicted case), so a future source giving a precise extremeness threshold could widen
it without changing any current output. An element-from-temperature derivation (the more literal
8-codes reading) is **not adopted** because it contradicts 궁통보감.

---

## 6. Sources

Directly reviewed (scraped 2026-09-26):

1. 滴天髓闡微 — 維基文庫, chapters §29 寒暖 / §30 燥濕 (原注 + 任鐵樵 註) —
   <https://zh.wikisource.org/wiki/滴天髓闡微> (also ctext.org chapter 126492)
2. 사주플러스 / 현산玹山 — 격국용신(8): 한난조습에 따른 조후용신 취용법 —
   <https://sajuplus.tistory.com/2775>
3. 네이버 블로그 / 촌노 — 조후용신(調候用神) —
   <https://m.blog.naver.com/hs72hs72/60214125204>
4. 정해 만세력 (8-codes) — 용신 (조후용신) —
   <https://doc.8-codes.com/docs/origin/yongsin/>
5. 算准网 — 调候用神一定有用吗？什么情况不适合用调候？ —
   <https://www.suanzhun.net/article/2783.html>
6. 算准网 — 旺衰和调候用神不一样、冲突的底层逻辑与取舍原则 —
   <https://www.suanzhun.net/article/3011.html>
7. 凤凰网 / 命理何锋 — “调候”命格的判断标准与取用原则 —
   <https://i.ifeng.com/c/85FVTpgnUih>
8. 算准网 — 如何来确定八字的寒暖燥湿状况 —
   <https://www.suanzhun.net/article/2113.html>
9. 太极书馆 — 《四柱预测学入门》 补偏之三·用神调候 —
   <https://www.8bei8.com/book/sizhuyucexuerumen_30.html>

**Industry engines (the standard this implementation follows), directly reviewed 2026-09-26:**

10. 정해 만세력 / 8-codes — 용신과 용신격 (조후용신 method: per-character 한난 score, month &
    hour weighted higher; 조후 importance falls as the chart approaches neutral) —
    <https://guide.8-codes.com/guide/origin/yongsin.html>
11. 사주플러스 (플러스만세력) — 명리학 조견표 · 천간 지지의 한난조습 (published per-character
    한난 table; "한난은 월지 중심으로 판단") —
    <http://mase.sajuplus.net/?mnuid=1&idcnt=2&curjong=manse003006&cstyle=D&drlink=habchsch2&etcval=hanan1>
12. 窮通寶鑑 — 四月辛金 條 (unconditional 壬水; the per-stem rule that fixes the *element* even
    when the whole-chart temperature is neutral) —
    <https://www.dajiazhao.com/sm/qtbj/6178.html>

**Ground-rule note.** The *principle* (chart must be extreme) is classical and transcribed. The
industry *method* (whole-chart weighted temperature score) is documented by 정해 만세력 and
사주플러스. The one numeric constant (`_NEUTRAL_TEMPERATURE_MARGIN`) is an operational choice, not
published by any source, and is flagged `[UNCERTAIN]`. The *element* is taken from 궁통보감's
stem×month rule, not derived from the temperature score, per Ground Rule 1.
