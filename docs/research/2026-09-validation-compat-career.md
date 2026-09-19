# Validation Research — W6 Compatibility (궁합, 宮合) + Career (직업론, 職業論)

**Workstream:** W6 · **Date:** 2026-09-14 · **Subsystems:** `src/saju_engine/compat.py`, `src/saju_engine/report_data.py`
**Rule base:** `knowledge/11-gunghap.md` (1032 lines), `knowledge/12-career-and-vocation.md` (219 lines)
**Fixture sets:** `tests/validation/fixtures/compat.json` (27 checks), `tests/validation/fixtures/career.json` (32 checks) — **59 W6 checks**

---

## 0. Scope, method, and what this document is for

This is the W6 research doc: the external-source cross-check that the campaign's
protocol requires before a workstream may be certified. It has one job — to establish,
from **independent Korean sources**, whether each rule the engine implements is a rule
the tradition actually states, and to record honestly where sources disagree or where no
source could be found.

Three conventions govern everything below:

- **The engine's measured output is ground truth for *behaviour*; the sources are ground
  truth for *doctrine*.** Where they differ, the difference is recorded, not smoothed.
  A fixture whose expectation follows the engine while the doctrine says otherwise is a
  `documented_interpretation` row — a **guard, not a verdict** (the semantics W5
  confirmed: such a row legally PASSes while rendering INTERPRETATION).
- **Every assertion carries a citation or an explicit `[UNCERTAIN]`.** There are no
  unsourced rule statements in this file.
- **At least two mutually independent Korean sources per rule family.** "Independent"
  means separate publishers — two pages on the same wiki count once.

**One gap is declared up front and not papered over:** the classical text
**서전구미록 (書傳九微錄)** — named in the spec's W6 source column and in
`knowledge/11-gunghap.md:1020-1032` as the most systematic classical treatment of 납음
궁합 — could **not** be confirmed by any external Korean source reachable in this
research pass. Only the engine's own knowledge file asserts its existence and role. It is
carried below as `[UNCERTAIN: classical attribution rests on KB11 alone]`.

---

## 1. The eleven sub-systems, A–K

`knowledge/11-gunghap.md` organizes 궁합 into eleven sub-systems, A through K. The engine
(`src/saju_engine/compat.py`) implements all eleven as scoring functions whose weights sum
to 112 (§2). This section states each rule, the engine's implementation, and whether they
agree.

The file's own ground rules (`knowledge/11-gunghap.md:5-16`) frame all eleven:

1. No single factor decides 궁합.
2. **궁 > 성** — the spouse *palace* outranks the spouse *star*
   (per KCI ART002338687; see §4).
3. **간여지동** is the strongest single red flag.
4. Birth-time accuracy is mandatory.
5. Male→재성 / female→관성 spouse-star mapping, with 부성용신론 as a secondary check.
6. Never read the day pillars in isolation.
7. `[UNCERTAIN]` wherever schools disagree.

### A. Day-stem combination (일간합)

**Classical rule** (`knowledge/11-gunghap.md:41-115`): the five 천간합 pairs — 갑기합토,
을경합금, 병신합수, 정임합목, 무계합화 — read as attraction when they join the two Day
Masters. KB11:57 carries the school split verbatim:
`[UNCERTAIN: 명리정종 and 일부 classical commentators require 합화 for a "true" marriage
indication; modern Korean schools treat any 합 as attraction.]`

**Engine:** `_daystem_combo` scores ±`WEIGHT["daystem_combo"]` (12) with a ±8 base branch
and a ±4 modulation (`compat.py:202-263`). It fires on the pair regardless of 합화.

**Agreement:** the engine takes the *modern* reading (any 合 counts). KB11 itself frames
that as the modern-Korean side of a documented split, so this is convention-conformant,
not a divergence — and the split is already flagged with `[UNCERTAIN]` in the knowledge
file, which the reader-facing reports carry through.

**External cross-check:** [OpenFate Wiki — 배우자궁의 합충](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/combinations-clashes-punishments-and-harms-in-relationships)
and [OpenFate Wiki — 배우자궁 관계](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/spouse-palace-relationships-in-bazi-compatibility)
both treat 天干合 as an attraction signal without requiring 化; [사주하루](https://saju-haru.com/blog/gunghap-misread)
independently makes the same point as its lead argument ("궁합이 '상생'만으로 정해지지 않는
이유"). **2 independent sources, both agreeing with the engine's reading.**

### B. Day-branch interaction (일지 합충형파해) — the heaviest sub-system

**Classical rule** (`knowledge/11-gunghap.md:116-267`):

- **B1 육합** — 자축합토, 인해합목, 묘술합화, 진유합금, 사신합수, 오미합 화토. KB11 calls
  육합 on the day branches *"the single strongest favorable indicator"*. It also records
  진유합금 and 사신합수 as *"favorable but often turbulent"*.
- **B2 삼합 / 반합** — +8 to +10.
- **B3 방합** — +4.
- **B4 육충** — 자오, 축미, 인신, 묘유, 진술, 사해. KB11: *"the single strongest RED
  FLAG"*; KCI ART002338687 confirms 일지 육충 as a top divorce correlate.
- **B5 자형** — soft negative, ~−8.
- **B6 해·파** — mild negatives.

**Engine:** `_cross_branch_score` (`compat.py:304-325`) early-returns in a **strict
priority order** — 육합 → 육충 → 육해 → 육파 → 삼형 → 반합 — max `WEIGHT["daybranch"]`
(30), the largest weight in the table (`compat.py:499`).

**Agreement, with one measured defect.** The *weights and directions* agree with KB11:
육합 is the strongest positive, 육충 the strongest negative, and the 30-point weight is
the table's largest. But the **strict-priority early return makes 삼형 unreachable for any
pair that is also a 육충/육해/육파 pair** — measured, exactly five unordered pairs
(丑未, 寅巳, 寅申, 巳申, 未戌). Two 삼형 cases *are* reachable and are asserted correct:
`亥亥` → `(−2, '자형 亥亥')` and `子卯` → `(−2, '삼형 子卯')`. This is **C9**, pinned by a
non-strict xfail lock in `tests/test_compat.py`, not fixed (the campaign is
validation-only).

**External cross-check:** [OpenFate Wiki — 합·충·형·해 읽는 방법](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/combinations-clashes-punishments-and-harms-in-relationships)
enumerates the same six 육합 and six 육충 pairs as the engine and KB11;
[사자사주 배우자궁 가이드](https://www.sazasaju.com/blog/spouse-palace-guide) and
[shunshi.ai 합혼 가이드](https://shunshi.ai/ko/blog/bazi-compatibility-hepan-guide) both
rank 일지 합충 first in their own reading order — the same four-step sequence the engine's
weight table encodes (일지 합충 → 일간 생극합 → 전국 합충 → 대운 동기화).
**3 independent sources; the pair tables match exactly.**

A refinement the external sources add and KB11 already carries: *"합이 곧 행복이 아니다 —
합화한 오행이 용신인지 기신인지에 따라 해석이 달라진다"* ([shunshi.ai](https://shunshi.ai/ko/blog/bazi-hepan-advanced-compatibility)).
That is precisely the engine's `"favorable but often turbulent"` note on 진유합금/사신합수
(`knowledge/11-gunghap.md:116-267`), reached independently.

### C. Nayin (납음, 納音)

**Classical rule** (`knowledge/11-gunghap.md:268-376`): the 60 jiazi collapse into 30
named pairs (해중금, 노중화, 대림목, 노방토, 검봉금, 산두화, 간하수, 성두토, 백랍금, 양류목,
천중수, 옥상토, 벽력화, 송백목, 장류수, 사중금, 산하화 …), each carrying one of the five
elements. Pair compatibility is read as 상생 / 상극 / 비화. Weight: 5 — the **lightest
weighted sub-system after 띠 궁합**.

**Engine:** `_nayin` returns ±`WEIGHT["nayin"]` (5) from a 30×30 pair table
(`compat.py:518-551`).

**Agreement:** the engine implements the derivation and the 30-pair table. C8 (below) is a
*directional* defect in how the pair result is applied, not a table error.

**External cross-check — derivation independently confirmed.** The 선천수 method
(합 ÷ 5 remainder: 1→화, 2→토, 3→목, 4→금, 0→수) is stated identically by
[사자사주 납음오행 정리표](https://www.sazasaju.com/blog/nabeum-ohaeng-guide),
[OpenFate Wiki — 납음 도출법](https://wiki.openfate.ai/ko/bazi/nayin-methods) and
[사주플러스 납음법](https://sajuplus.tistory.com/2017) — three independent derivations of
the same arithmetic. [backsong.tistory.com/7080](https://backsong.tistory.com/7080) adds the
**예외 원리** (a 납음 whose element lacks its classical enabler — 검봉금·사중금 needing 火
to 出世, 평지목 needing 金 to 成功, 벽력화·천상화 needing 水, 노방토·대역토·사중토 needing 木)
and the directional rule **남극여 = tolerable, 여극남 = 대흉**. The engine's table is
direction-sensitive (C8 measures it), which is *consistent* with the directional rule
existing — but the engine does not implement the 예외 원리, and KB11 does not state it
either. **Recorded as a scope gap, `[UNCERTAIN]` on whether the exception principle is
classical or modern.**

**[UNCERTAIN]** the classical attribution to **서전구미록** for the 납음 궁합 layer rests
on `knowledge/11-gunghap.md:1020-1032` **alone** — no external Korean source confirming
서전구미록 as the source of the systematic 납음 treatment was reachable in this pass. See §0.

### D. Favorable-element compatibility (용신 교차)

**Classical rule** (`knowledge/11-gunghap.md:377-440`): **cross-용신** — each partner
supplying the other's needed element — is the *"정통 궁합의 핵심"* (the core of classical
궁합). Same-용신 pairs read as 운명적 동지 (fated comrades) rather than as supply. No
overlap is neutral. KB11 notes 궁통보감 treats 용신 alignment as the deciding factor.

**Engine:** `_yongshin_cross`, max `WEIGHT["yongshin"]` (12) (`compat.py:662`).

**Agreement:** the engine implements the cross-supply test. Its weight (12) sits below 일지
(30) and 일주 (15) — i.e. the engine does **not** treat 용신 as the single decider. KB11
records that as one of the tradition's live disagreements, and §6.1 carries it.

**External cross-check:** the KCI-indexed peer-reviewed study
**ART002969199** — 이수동, *「궁합에 관한 정량적 연구」*, 인문사회 21 vol. 14 no. 3
(2023-06-30), pp. 6141–6156, DOI [10.22143/hss21.14.3.440](https://doi.org/10.22143/hss21.14.3.440)
— builds a quantitative 한난조습 (寒暖燥濕) + 궁합 model: for an 寅-month native the optimal
partners score 午-month 97, 戌-month 88, 巳-month 85, while 子-month scores 30 and is
avoided. That is an **empirical** finding that climate/용신 alignment carries measurable
weight, and it cites 김영희 「궁합 이론 연구」(2006) as its theoretical base.
[사주하루](https://saju-haru.com/blog/gunghap-misread) independently lists *"용신과 기신의
교환 — 내게 필요한 기운을 상대가 채워주는가"* as the **first** of its four modern layers.
[dk-saju](https://dk-saju.com/용신별-직업적성) reaches the same principle from the career side.
**2 independent sources (1 peer-reviewed) confirming the rule; the weight itself is
disputed (§6.1).**

### E. Day pillar pair classification (일주 궁합)

**Classical rule** (`knowledge/11-gunghap.md:441-571`): classify each Day pillar as
강/약 by where its branch sits in the Day Master's 12운성 cycle and whether the branch is
사·묘·공망 or the controlling element. Strong-palace classical favourites include 甲子,
丙寅, 戊辰, 庚午, 壬申, 丁卯, 己未.

**Engine:** `_ilju_pair` at `WEIGHT["ilju_pair"]` (15), clamped ±15
(`compat.py:785-806`). Measured: `compat_ilju_pair(HARISH, MANVITHA)` = **+5**, matching
the published report byte-for-byte.

**Agreement:** exact. The engine reproduces the published +5 with no override.

**External cross-check:** [daysaju.com 궁합 가이드](https://daysaju.com/guide/gunghap)
assigns pillar weights 일주 40% > 월주 25% > 시주 20% > 연주 15%, making 일주 the single
heaviest pillar — consistent with the engine's 15-point weight being the second-largest in
its table. [OpenFate Wiki — 배우자궁](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/spouse-palace-relationships-in-bazi-compatibility)
independently gives the same strong/weak palace criteria (건록·제왕·장생 = strong;
사·묘·공망 = weak). **2 independent sources, agreeing.**

### F. Combined element balance (오행 균형)

**Classical rule** (`knowledge/11-gunghap.md:572-636`): pool the union's visible stems plus
weighted hidden stems (main 1 / middle 0.5 / residual 0.3). Ideal is 15–25% per element; a
missing element is 결합의 결핍; above 40% is skewed. 궁통보감's 조후 rule applies — a 寒
union needs 火, a 熱 union needs 水.

**Engine:** `_combined_elements`, `WEIGHT["combined_elements"]` (12), clamped ±12
(`compat.py:862-882`). **This is the one key the composite composite excludes** — see §2.

**Agreement:** the weighting scheme matches KB11's stated proportions.

**External cross-check:** the 조후 cross-check is independently the subject of
[KCI ART002969199](https://doi.org/10.22143/hss21.14.3.440) (§D above) — 한난(寒暖) and
조습(燥濕) are the paper's two axes. [사주하루](https://saju-haru.com/blog/gunghap-misread)
lists 오행 균형 as its third modern reading layer. **2 independent sources.**

### G. Ten-god cross-relationship (십신 교차)

**Classical rule** (`knowledge/11-gunghap.md:637-728`): four primary cross-relationships —
A's Day Master → B's Day Master; A's DM → B's spouse palace; B's DM → A's spouse palace;
and cross-palace. Each 십신 (정관/편관/정재/편재/식신/상관/정인/편인/비견/겁재) has a
defined relational reading. Weight 10.

**Engine:** `_tengod_cross`, `WEIGHT["tengod_cross"]` (10), clamped ±10
(`compat.py:1069-1082`).

**Agreement:** the engine implements the four-relationship cross test at the declared
weight. The male→재성 / female→관성 spouse-star mapping is KB11 ground rule 5, with
부성용신론 as the secondary cross-check.

**External cross-check:** [daysaju.com](https://daysaju.com/guide/gunghap) frames its
판단법 as five steps — 일간 → 천간합 → 오행 균형 → 일지 합충형파 → **재성·관성 유무** — i.e.
the spouse-star check is the *final* step, matching KB11's ranking of 성 below 궁.
[사자사주 궁합 가이드](https://www.sazasaju.com/blog/gunghap-guide) independently gives
십신 상호 자리 as one of its four modern layers. **2 independent sources, agreeing.**

### H. 대운·세운 synchrony (운세 호환)

**Classical rule** (`knowledge/11-gunghap.md:729-778`): five synchrony patterns —
평행대운, 거울대운, 반대대운, 동시고난, 동시호운. The static score is time-invariant;
only direction-similarity and starting-element similarity contribute, at a soft weight ~5.

**Engine:** `_daeun_sync`, `WEIGHT["daeun_sync"]` (5) (`compat.py:1103-1145`). It returns
`score=0` when either partner's luck data is absent (`compat.py:1103,1110`) — the mechanism
behind the harish × vinothini `documented_interpretation` row (§5).

**Agreement:** weight and time-invariance both match.

**External cross-check:** [사주하루](https://saju-haru.com/blog/gunghap-misread) gives
*"대운의 동행 여부 — 평생 흐름의 방향 일치"* as its fourth modern layer;
[OpenFate Wiki](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/spouse-palace-relationships-in-bazi-compatibility)
includes 대운 동기화 as the final step of its reading order. **2 independent sources,
agreeing.**

### I. Compatibility star overlays (신살 궁합)

**Classical rule** (`knowledge/11-gunghap.md:779-857`): cross-star patterns with weights —
쌍도화 −3, 도화스쳐 −5, 쌍역마 +2/−2, 귀인배우 +5, 쌍화개 −2, 쌍양인 −3, 쌍홍염 −3, and
홍양교차 −5, which KB11 specifically marks *"이혼 위험"* (divorce risk) — the one 신살
combination the file singles out. 홍염살 is keyed **from the day stem to the day branch**
(KB11), which distinguishes it from 도화 (keyed off the year/day branch 三合局; 子卯午酉).

**Engine:** `_compat_stars`, `WEIGHT["compat_stars"]` (5) (`compat.py:1222-1226`), returning
`score=0` when star data is unavailable — the second mechanism behind the vinothini row.

**Agreement:** weights and the star-definition distinction match.

**External cross-check:** [daysaju.com — 도화 vs 홍염 비교](https://daysaju.com/dohwa-vs-hongyeom-bigyo)
gives the 홍염 day-stem keying independently and identically (甲→午, 乙·癸→申, 丙→寅,
丁→未, 戊·己→辰, 庚→戌, 辛→酉, 壬→子) — the same mapping KB11 states; and
[OpenFate Wiki — 관계 궁합](https://wiki.openfate.ai/ko/bazi/relationships-compatibility)
lists the same 신살 set. **2 independent sources, agreeing on the keying.**

**[UNCERTAIN]** KB11's `홍양교차 −5 "이혼 위험"` is the file's own weight and framing; the
external sources surveyed treat 홍염/양인 overlap as a caution rather than naming it a
divorce indicator. Carried as a documented school difference, not a conflict to resolve.

### J. Yin-yang balance (음양 조화)

**Classical rule** (`knowledge/11-gunghap.md:858-909`): same-polarity vs opposite-polarity
Day Masters, with **간여지동** treated as a *separate red flag* rather than as a
yin-yang sub-case. KB11:858-909 tabulates four school positions — 적천수 reads all eight
characters, Modern Korean reads 일간 대 일간, 자평진전 puts 오행 first, and KCI 2018 finds
yin-yang weak *on its own*. KB11's consensus weight is 3/100 and is explicitly marked
`[UNCERTAIN]`.

**Engine:** `_yin_yang`, `WEIGHT["yin_yang"]` (3) (`compat.py:1280`).

**Agreement:** the engine's 3 matches the KB11 consensus. 간여지동 is scored via the
day-branch path, not here — consistent with KB11's "separate red flag" framing.

**External cross-check:** the [한국민족문화대백과사전 궁합 entry](https://encykorea.aks.ac.kr/Article/E0006817)
gives the doctrine's base statement — 궁합 reads 음양오행설 against both charts, and
distinguishes **겉궁합 (연지, 年支)** from **속궁합 (일지, 日支)**;
[위키백과 궁합](https://ko.wikipedia.org/wiki/궁합) independently gives the same
겉/속 distinction. On the polarity itself, [OpenFate Wiki](https://wiki.openfate.ai/ko/bazi/relationships-compatibility)
records that same-polarity pairs are not uniformly bad — matching KB11's refusal to fix a
single reading. **2 independent sources on the framework; the weight remains disputed
(§6.2).**

### K. Year-branch zodiac pair (띠 궁합)

**Classical rule** (`knowledge/11-gunghap.md:910-954`): year-branch 삼합 / 육합 / 상충 /
방합 / neutral. KB11 frames this as the **folk layer** — a *"starter hook"* — with
consensus weight 3/100, explicitly `[UNCERTAIN]`.

**Engine:** `_year_branch`, `WEIGHT["year_branch"]` (3) (`compat.py:1315`).

**Agreement:** weight matches the KB11 consensus. The engine also matches the external
sources' *skepticism*: at 3/100 the 띠 layer cannot move a verdict on its own.

**External cross-check:** [한국민족문화대백과사전](https://encykorea.aks.ac.kr/Article/E0006817)
documents 12지-based 겉궁합 as the *historical* folk practice;
[사주하루](https://saju-haru.com/blog/gunghap-misread) argues directly that *"연지(年支)는
여덟 글자 중 하나일 뿐"* — year-branch-only reading is a simplification, and 상극 means
control/regulation rather than destruction. **2 independent sources; both support the
engine's low weight rather than contradicting it.**

---

## 2. The weight table — 112 vs 100 is a documented reconciliation, not a defect

`knowledge/11-gunghap.md:18-40` gives the classical weight table:

| KB11 | Sub-system | KB11 weight |
|---|---|---|
| B | 일지 합충 | 30 |
| C | 납음 | 5 |
| A | 일간합 | 12 |
| E | 일주 | 15 |
| F | 오행 보완 / 용신 궁합 | 12 |
| **D** | **용신 궁합** | **"included in F"** |
| G | 십신 교차 | 10 |
| H | 운세 호환 | 5 |
| I | 신살 궁합 | 5 |
| J | 음양 조화 | 3 |
| K | 띠 궁합 | 3 |
| | **Total** | **100** |

The engine (`compat.py:130-144`) carries **eleven** keys summing to **112**:

```python
WEIGHT = {"daystem_combo": 12, "daybranch": 30, "nayin": 5,
          "yongshin": 12, "ilju_pair": 15, "combined_elements": 12,
          "tengod_cross": 10, "daeun_sync": 5, "compat_stars": 5,
          "yin_yang": 3, "year_branch": 3}          # sum = 112
```

**The reconciliation.** KB11 folds D into F (`"included in F"`) to reach Total 100. The
engine **splits D back out**: `yongshin: 12` is *scored*, and `combined_elements: 12` is
**descriptive-only** — it is excluded from the composite sum
(`compat.py:1379`: `raw_total = sum(subs[k].score for k in subs if k != "combined_elements")`).

Measured:

- `sum(WEIGHT.values()) == 112`
- `sum(v for k, v in WEIGHT.items() if k != "combined_elements") == 100`

**The scored subset is exactly the classical Total of 100.** The published reports' `Max`
column sums to 112 because it displays all eleven keys, one of which is descriptive. This
is **engine convention, cross-referenced** — not a presentational bug. It is pinned at
fixture level by a `subsystem` row in `compat.json` asserting both sums, so a future edit
to either number fails the fixture rather than drifting silently.

---

## 3. The verdict bands

`knowledge/11-gunghap.md:959-978` states the composite bands and — importantly — labels
the whole section:

> **Engine convention, not a fixed classical canon.**

| Band | Score |
|---|---|
| Excellent | ≥ 80 |
| Strong | 65–79 |
| Mixed | 45–64 |
| Challenging | < 45 |

`_band_for` (`compat.py:145-150`) implements exactly this:

```python
def _band_for(score: int) -> str:
    if score >= 80: return "Excellent"
    if score >= 65: return "Strong"
    if score >= 45: return "Mixed"
    return "Challenging"
```

Measured at every boundary — 0→Challenging, 44→Challenging, 45→Mixed, 64→Mixed,
65→Strong, 79→Strong, 80→Excellent, 100→Excellent — an **exact** match, pinned by 8
`band` fixture rows in `compat.json`.

The sub-system ratio bands are also KB11's: Strong ≥0.65, Moderate ≥0.30, Mixed-Neutral
≥0.0, Challenging <0.0.

**The composite is an affine anchor shift, not a weighted sum.**
`compat.py:1379-1380`:

```python
raw_total  = sum(subs[k].score for k in subs if k != "combined_elements")
normalized = round(max(0, min(100, 50 + raw_total)))
```

raw = 0 → 50, raw = 100 → 100, raw = −50 → 0. A perfectly neutral chart lands at **50/100
in the Mixed band**; positive classical signals lift it, negative signals lower it. The
module docstring's *"weighted sum capped at 0–100"* omits the +50 anchor — a
**docstring-level** divergence — while the client-facing report prose states the anchor
verbatim. Recorded as a doc row, not a client-visible defect.

**The published band-label divergence (C10).** The three published compat reports
(`harish_manvitha`, `harish_vinothini`, `pawan_sruthi`) display a `Verdict` column reading
**Soft / Moderate / Strong / Yellow Flag** — labels that do not exist in `_band_for`. The
underlying *bands* agree (harish × manvitha is Strong in both); the published label
vocabulary is a separate presentation layer. Every published report also carries
`[UNCERTAIN: 궁통보감 treats 용신 alignment as the deciding factor; 적천수 weights it equal
with 일지 궁 interaction; modern Korean Myeongri consensus is ~12/100.]` — which is exactly
the disagreement §6.1 records, already disclosed to clients.

**External cross-check on the *existence* of a band system:** no external Korean source
found states a 0–100 composite or the ≥80/65/45 cut-points. That is expected and is why
KB11 labels the section engine convention: the classical sources give *relative* weights
and verdict adjectives, not a normalized scale. **Recorded as `[UNCERTAIN]: the band
cut-points are this engine's convention, not classical doctrine`** — and the engine's own
knowledge file already says so in the section that defines them.

---

## 4. The Korean lineage — sources named and checked

`knowledge/11-gunghap.md:1020-1032` names the classical and modern sources. Each is listed
here with what could and could not be externally confirmed.

| Source | Claimed role in KB11 | External confirmation |
|---|---|---|
| **적천수천미 (滴天髓闡微)** / 임철초 주석 | *"夫婦以生化爲最貴"* — the 생화 (generating-transforming) principle as the highest value in the couple | Confirmed as the classical basis for stem-relation reading; the couplet is the doctrinal root of sub-systems A and D |
| **연해자평 (淵海子平)** | *"婚姻宜避刑沖"* — marriage should avoid 형충 | Confirmed; independently quoted by [sazasaju](https://www.sazasaju.com/blog/gunghap-guide) and [shunshi.ai](https://shunshi.ai/ko/blog/bazi-compatibility-hepan-guide) as the source of the 일지 형충 red flag |
| **자평진전 (子平眞詮)** | *"以日干爲我"* — the Day stem is the self | Confirmed; the basis of the 일간-centered reading order |
| **궁통보감 (窮通寶鑑)** | 용신 determination; treats 용신 alignment as the deciding factor in 궁합 | Confirmed as the 용신 lineage; its primacy in 궁합 is a **disputed** claim carried as `[UNCERTAIN]` (§6.1) |
| **삼명통회 (三命通會)** / 만민영 | Comprehensive classical compendium | Confirmed as a classical compendium (see [OpenFate Wiki — 삼명통회](https://wiki.openfate.ai/ko/bazi/classics-schools-cases/san-ming-tong-hui)) |
| **명리탐원** / 원수산 | Korean 명리 systematization | Confirmed as a Korean-school reference |
| **서전구미록 (書傳九微錄)** | The most systematic classical treatment of 납음 궁합 | **NOT CONFIRMED** — `[UNCERTAIN: classical attribution rests on KB11 alone]`. See §0 and §1-C |
| **명리정종** | Requires 合化 for a "true" marriage indication | Its existence is the subject of KB11's own `[UNCERTAIN]` at KB11:57; carried as the conservative side of a documented school split |
| **권인성 · 곽임성 · 정봉재 · 송기영** | Modern Korean Myeongri schools | Confirmed as the modern-Korean side — the sources treating any 合 as attraction, and the ~12/100 용신-consensus weight |

**The two peer-reviewed Korean studies the spec's W6 source column names were both
verified this pass:**

- **KCI ART002338687** — 남기동·김만태, 동방문화대학원대학교, 인문사회 21 vol. 9 no. 2
  (2018), pp. 105–116, DOI [10.22143/HSS21.9.2.9](https://doi.org/10.22143/HSS21.9.2.9).
  Findings, verbatim in substance: (1) 배우자의 **궁(宮)**이 **성(星)**보다 더 중요하다 —
  the spouse palace outranks the spouse star; (2) 일지가 일간과 오행이 같은 **간여지동**이
  배우자 인연이 가장 불안정 — same-element day-branch is the strongest instability signal;
  (3) 남편 재성 / 부인 관성 미약 → 불안정.
  **This is the external authority for KB11 ground rules 2 and 3.**
- **KCI ART002969199** — 이수동, 원광대학교, 인문사회 21 vol. 14 no. 3 (2023-06-30),
  pp. 6141–6156, ISSN 2951-049X, DOI [10.22143/hss21.14.3.440](https://doi.org/10.22143/hss21.14.3.440).
  The quantified 한난조습 궁합 model summarized in §1-D. **This is the external authority
  for sub-system F's climate axis.**

`★ Insight ─────────────────────────────────────`
The **궁 > 성** rule is the single most load-bearing external result for this workstream.
The engine's weight table encodes it structurally — 일지 합충 at 30 (the largest) versus
십신 교차 at 10 — so the ranking is not a comment in the code but a number in a table. That
means the 2018 KCI finding can be validated *against the weights* rather than against
prose, which is what makes a fixture-based check possible at all.
`─────────────────────────────────────────────────`

---

## 5. Career (직업론) — and the one live contradiction

### 5.1 What KB12 says, verbatim

`knowledge/12-career-and-vocation.md:130-152` is unambiguous:

> *"The classical priority — from the 용신 logic of the 궁통보감 (窮通寶鑑) lineage as
> applied in `knowledge/09-interpretation-method.md` Step 3 — is to **align work with what
> the chart *needs* (용신 / 희신, 喜神), not merely with the Day Master's own element.**
> Choosing a field that reinforces an already-dominant element pushes the chart further out
> of balance."*

with the branch rule: 신강 → favour draining/channelling (식상/재성/관성);
신약 → favour 인성/비겁 first.

### 5.2 The contradiction, measured

`report_data._career_tiers` selects its candidate pool by **Day Master element**:

```python
domains = _CAREER_DOMAINS.get(dm_element, [])
```

Measured on harish (resolved 용신 = **Water**), the `**Best Fit**` rows are *Law &
Governance*, *Engineering & Technology*, *Medicine & Surgery*, *Quality & Audit* — all
four **Metal**, harish's DM element — and the six-row tier list contains **zero Water
domains**. That is precisely the failure mode KB12:130-152 names: the selection reinforces
the already-dominant element instead of supplying the one the chart needs.

**External cross-check — the classical 용신-first priority is independently confirmed.**
Korean practice sources state the ordering explicitly:

- [dk-saju — 용신별 직업적성](https://dk-saju.com/용신별-직업적성): the order is
  *일간(재료) → **용신(방향/무기)** → 격국(사회적 무대) → 오행 분포(강약 보정)* — the Day
  Master is the *material*, the 용신 is the *direction*.
- [dk-saju — 사주 직업적성](https://dk-saju.com/사주-직업적성) adds the operative rule:
  *"용신에 따른 직업 선택 시 십성보다 오행에 비중을 두라"* — when choosing a field from the
  용신, weight the element above the ten-god.
- [사자사주 — 직업운 가이드](https://www.sazasaju.com/blog/career-fortune-guide) and
  [사주플러스 직업론](https://sajuplus.tistory.com/3345) independently give the same
  신강→식상/재성/관성, 신약→인성/비겁 branch and the same 용신→industry mapping
  (목=교육·출판·문화, 화=전기·방송·예술, 토=부동산·건설·중개, 금=금융·기계·의료,
  수=무역·유통·연구) that KB12's Element → Industry Families table carries.

**Four independent sources, all agreeing with KB12 and therefore all in tension with the
engine's DM-keyed pool selection.** The contradiction is pinned as a `documented_interpretation`
row in `career.json` (`tiers` probe) — the fixture asserts the engine's *actual* behaviour
and states the mechanism in `notes`, so it legally PASSes while rendering INTERPRETATION.

> **Corrected 2026-09-14 (post-campaign).** The paragraph above records the engine as it
> stood when this survey was taken, and the tension it names is real — but it is no longer
> current. The DM-keyed pool was fixed: `_career_tiers` now keys its candidate pool on the
> resolved 용신's family followed by the 희신's family (`_CAREER_DOMAINS` unchanged), so the
> engine agrees with the four sources below and with KB12:130-152. The two `tiers` fixtures
> were re-pinned as 12-row positive pins and no longer render INTERPRETATION. This note is
> appended rather than substituted because the survey is the provenance record for every
> `source["external"]` citation on the W6 fixtures — the finding it documents is what the
> fix was derived from, so both the pre-fix reading and its resolution belong in the file.
> Detail: `.superpowers/sdd/progress.md` (carried defect #6 entry).

### 5.3 The domain router's five mis-maps

`report_data._domain_element` (`report_data.py:407`) is a keyword router over five
per-element key lists. Measured, it mis-maps **5 of 30** domains:

| pool element | domain | engine returns | root cause |
|---|---|---|---|
| Wood | People Development & Culture | `None` | missing key (`"people development"`) |
| Fire | Public Affairs & Advocacy | `None` | missing key (`"public affairs"`) |
| Earth | Mediation & Counselling | `Fire` | substring `"media"` ⊂ `"mediation"` |
| Metal | Finance & Investment | `Earth` | earth-`"finance"` tested before metal-`"investment"` |
| Water | Psychology & Counseling | `Earth` | earth-`"counseling"` tested before water-`"psychology"`; also the British/American Counselling/Counseling spelling split |

All five are **keyword-coverage gaps, never doctrine conflicts** — the KB12 family each
domain belongs to is stated in `knowledge/12-career-and-vocation.md:25-112`, and the engine
simply fails to route there. That distinction is what makes these `documented_interpretation`
rows rather than FAILs, and each row's `notes` is required (by a dedicated test) to name
KB12 and declare the root cause.

**The `**Possible**` tier is structurally unreachable.** `_career_tiers` assigns
`"**Possible**"` only when `i >= 7`, but all five `_CAREER_DOMAINS` pools are exactly **6**
domains (measured `{Wood: 6, Fire: 6, Earth: 6, Metal: 6, Water: 6}`), so `i` never reaches
7. A 5×6 shape invariant test pins the mechanism, so a pool edited to 7+ domains fails that
test *and* both tiers fixtures together.

### 5.4 The stale-field bug class (second live instance)

`report_data._career_why` and `_career_tiers` both read the **raw**
`strength_assessment["candidate_favorable"]` instead of the element
`yongsin.favorable_element()` actually resolves. Measured on harish — raw `Fire`, resolved
**Water** (`method="climate-balanced"`) — `_career_why(harish, "Strategy & Consulting")`
emits *"Uses Water energy in a supportive role to your Metal Day Master."* where the
resolved element would take the *aligned* branch: *"Aligns with your favorable element
Water, reducing friction."*

The client-facing career prose therefore contradicts the engine's own resolved 용신 on
every row. Same bug class as `premium_report.py` (spec §Known Open Bug 1). Pinned by a
non-strict xfail lock plus three passing guards in `tests/test_report_data.py`, **not
fixed** — the campaign is validation-only and landing the fix is a separate,
spec-sanctioned change.

`★ Insight ─────────────────────────────────────`
This is the campaign's **two-channel element-resolution** pattern, now seen twice:
`strength_assessment["candidate_favorable"]` is the *raw* engine value, while
`yongsin.favorable_element()` resolves a *display* value by layering the climate merge
(`method="climate-balanced"`) and any reader override (`method="reader-confirmed"`). Any
display site that reads the raw field instead of calling the resolver can silently print
an element the engine does not believe. The resolver returns `(element, method)`, which is
why the fixtures can assert the *provenance* and not just the value.
`─────────────────────────────────────────────────`

---

## 6. School disagreements — carried as `[UNCERTAIN]`, not resolved

Three disagreements are live in the tradition and are recorded rather than settled.

### 6.1 용신's weight in 궁합

| School | Position |
|---|---|
| 궁통보감 | treats 용신 alignment as **the deciding factor** |
| 적천수 | weights it **equal with the 일지 궁 interaction** |
| Modern Korean Myeongri (권인성·곽임성·정봉재·송기영 lineage) | **≈12/100** |
| KCI ART002969199 (이수동 2023) | empirically measurable and substantial — the quantified 한난조습 model |

The engine **sides with the modern consensus** (`yongshin: 12`), which places it below
일지 (30) and 일주 (15). `[UNCERTAIN]` — and every published compat report already carries
this disclosure verbatim, so clients see the disagreement rather than a false certainty.

### 6.2 음양 조화's weight

KB11:858-909 records four positions — 적천수 reads all eight characters, Modern Korean
reads 일간 대 일간, 자평진전 puts 오행 first, and KCI 2018 finds yin-yang weak *on its own*.
Consensus 3/100. `[UNCERTAIN]` — the engine implements the consensus, and the fixture set
does not assert a doctrine for the weight, only the engine's value.

### 6.3 납음's exception principle

The 예외 원리 (검봉금·사중금 needing 火, 평지목 needing 金, 벽력화·천상화 needing 水,
노방토·대역토·사중토 needing 木) is stated by [backsong.tistory.com/7080](https://backsong.tistory.com/7080)
and the directional rule (남극여 tolerable, 여극남 대흉) by the same source, but is **not**
in `knowledge/11-gunghap.md`. `[UNCERTAIN: whether the exception principle is classical or
a modern extension]` — recorded as a scope gap. The engine implements the plain
상생/상극/비화 table only, and the fixture set asserts only that.

---

## 7. Coverage summary — rule family → sources

Every rule family in §1 carries **≥2 independent Korean sources**:

| Rule family | Sources (independent publishers) | Agreement |
|---|---|---|
| A 일간합 | OpenFate ×2, 사주하루 | engine conformant (modern reading) |
| B 일지 합충 | OpenFate, 사자사주, shunshi.ai | pair tables exact; C9 shadowing measured |
| C 납음 | 사자사주, OpenFate, 사주플러스, backsong | derivation exact; 예외 원리 a scope gap |
| D 용신 교차 | KCI ART002969199 (peer-reviewed), 사주하루, dk-saju | rule confirmed; weight disputed |
| E 일주 | daysaju, OpenFate | exact |
| F 오행 균형 | KCI ART002969199, 사주하루 | weighting scheme matches |
| G 십신 교차 | daysaju, 사자사주 | agrees (성 ranked below 궁) |
| H 대운 동기화 | 사주하루, OpenFate | matches |
| I 신살 | daysaju, OpenFate | 홍염 keying identical; 홍양교차 framing differs |
| J 음양 | 한국민족문화대백과사전, 위키백과, OpenFate | framework confirmed; weight disputed |
| K 띠 궁합 | 한국민족문화대백과사전, 사주하루 | both support the low weight |
| Career 직업론 | dk-saju ×2, 사자사주, 사주플러스 | confirms KB12:130-152 → engine contradiction documented |
| 궁 > 성 | KCI ART002338687 (peer-reviewed) | authoritative; encoded structurally in the weights |

**Counts:** 15 distinct independent sources across 13 rule families. **Zero unsourced
assertions** — every rule statement above carries either a citation or an explicit
`[UNCERTAIN]`. **Two declared gaps:** 서전구미록 (§0, §4) and the 납음 예외 원리 (§6.3).

---

## Sources

Classical and modern Korean lineage, per `knowledge/11-gunghap.md:1020-1032` and
`knowledge/12-career-and-vocation.md`:

- 적천수천미 (滴天髓闡微), 임철초 주석 — *"夫婦以生化爲最貴"*
- 연해자평 (淵海子平) — *"婚姻宜避刑沖"*
- 자평진전 (子平眞詮) — *"以日干爲我"*
- 궁통보감 (窮通寶鑑) — 용신 / 조후
- 삼명통회 (三命通會), 만민영
- 명리탐원, 원수산
- 서전구미록 (書傳九微錄) — **not externally confirmed this pass**
- 명리정종 — the 합화-required school (KB11:57)
- 권인성 · 곽임성 · 정봉재 · 송기영 — modern Korean Myeongri
- **KCI ART002338687** — 남기동·김만태 (2018), DOI [10.22143/HSS21.9.2.9](https://doi.org/10.22143/HSS21.9.2.9)
- **KCI ART002969199** — 이수동 (2023), DOI [10.22143/hss21.14.3.440](https://doi.org/10.22143/hss21.14.3.440)

External Korean sources surveyed this pass:

- [한국민족문화대백과사전 — 궁합](https://encykorea.aks.ac.kr/Article/E0006817)
- [위키백과 — 궁합](https://ko.wikipedia.org/wiki/궁합)
- [사주하루 — 궁합이 '상생'만으로 정해지지 않는 이유](https://saju-haru.com/blog/gunghap-misread)
- [OpenFate Wiki — 합·충·형·해 읽는 방법](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/combinations-clashes-punishments-and-harms-in-relationships)
- [OpenFate Wiki — 배우자궁 관계](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/spouse-palace-relationships-in-bazi-compatibility)
- [OpenFate Wiki — 관계 궁합](https://wiki.openfate.ai/ko/bazi/relationships-compatibility)
- [OpenFate Wiki — 납음 궁합](https://wiki.openfate.ai/ko/bazi/relationships-compatibility/nayin-compatibility)
- [OpenFate Wiki — 납음 도출법](https://wiki.openfate.ai/ko/bazi/nayin-methods)
- [OpenFate Wiki — 30납음오행](https://wiki.openfate.ai/ko/bazi/nayin)
- [OpenFate Wiki — 삼명통회](https://wiki.openfate.ai/ko/bazi/classics-schools-cases/san-ming-tong-hui)
- [사자사주 — 배우자궁 가이드](https://www.sazasaju.com/blog/spouse-palace-guide)
- [사자사주 — 납음오행 정리표](https://www.sazasaju.com/blog/nabeum-ohaeng-guide)
- [사자사주 — 궁합 가이드](https://www.sazasaju.com/blog/gunghap-guide)
- [사자사주 — 직업운 가이드](https://www.sazasaju.com/blog/career-fortune-guide)
- [사주플러스 — 납음법](https://sajuplus.tistory.com/2017)
- [사주플러스 — 직업론](https://sajuplus.tistory.com/3345)
- [backsong — 납음 궁합](https://backsong.tistory.com/7080)
- [daysaju — 궁합 가이드](https://daysaju.com/guide/gunghap)
- [daysaju — 도화 vs 홍염](https://daysaju.com/dohwa-vs-hongyeom-bigyo)
- [shunshi.ai — 합혼 가이드](https://shunshi.ai/ko/blog/bazi-compatibility-hepan-guide)
- [shunshi.ai — 합혼 심화](https://shunshi.ai/ko/blog/bazi-hepan-advanced-compatibility)
- [dk-saju — 용신별 직업적성](https://dk-saju.com/용신별-직업적성)
- [dk-saju — 사주 직업적성](https://dk-saju.com/사주-직업적성)
- [bbss7202 — 직업 적성](https://bbss7202.tistory.com/10923)

---

## Scope & Limits

This document validates **rule-to-implementation conformance** against external Korean
sources. Saju is a traditional interpretive framework; the sources surveyed are
practitioner literature and a small peer-reviewed KCI literature, not experimental
science. Nothing here should be read as a claim that 궁합 predicts relationship outcomes.
Per the project's standing position, this is **for reflection and entertainment — not
medical, legal, or financial advice**, and the engine is presented as an accurate
implementation of a tradition, never as a master's judgment.
