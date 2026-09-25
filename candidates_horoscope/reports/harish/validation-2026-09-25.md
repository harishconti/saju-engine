# Harish: Independent Parallel Reading & Validation of the Combined Report

> Topic file. It validates `harish-combined.md` (base report + `career.md`) generated 2026-09-25.
> Read the base report [`harish-report.md`](harish-report.md) first. Engine root causes for every
> defect found here are in [`docs/audits/2026-09-25-engine-audit.md`](../../../docs/audits/2026-09-25-engine-audit.md)
> (referenced below as E-n).

## 2026-09-25 — Parallel reading built from first principles and checked claim by claim

### 0. How this was checked

- **Calculation** was recomputed without sajupy or the engine. Solar terms come from the `ephem`
  ephemeris, the day pillar from the Julian Day Number, and true solar time from the Sun's actual hour
  angle.
- **Interpretation** follows `knowledge/09-interpretation-method.md` step by step, with each rule cited
  to its knowledge file. Where the knowledge files do not settle a question, it is flagged
  **[UNCERTAIN]** (Ground Rule 2).
- Birth data as given in the report: **1992-06-04, 03:10 IST (UTC+5:30), Pallipattu (79.44°E), male.**

---

### 1. Calculation layer

| Item | Report | Independent value | Verdict |
|---|---|---|---|
| Year pillar | 壬申 | 壬申 (立春 1992-02-04 13:47 UTC, well before birth) | ✅ |
| Month pillar | 乙巳 | 乙巳 (芒種 = 1992-06-05 **10:21 UTC**; birth = 06-03 21:40 UTC, 1.53 d before) | ✅ |
| Day pillar | 辛亥 | 辛亥 (JDN method, anchor 2000-01-01 = 戊午) | ✅ |
| True solar time | 02:59 (−10.5 min) | **02:59:32** (LMT −12.24 min, EoT +1.77 min) | ✅ |
| Hour pillar | 己丑 (alt 庚寅) | 己丑. **28 seconds** from the 丑/寅 boundary | ✅ but see note ↓ |
| 대운 direction | forward | forward (yang year 壬 + male, `08-luck-pillars.md`) | ✅ |
| 대운 sequence | 丙午 丁未 戊申 己酉 庚戌 辛亥 壬子 癸丑 | same | ✅ |
| 대운수 | ~0.6 (1.7 days) | **~0.51 (1.53 days)**. The engine compares a KST term time with IST (E-1) | ⚠ small error |
| Current 대운 | 己酉 (30-39) | 己酉. Runs from **~Dec 2022 to ~Dec 2032** (start age 0.51) | ✅ label slightly off |
| 세운 2026–2035 | 丙午 … 乙卯 | same | ✅ |
| Hidden stems 丑 | 己(본) 癸(중) 辛(여) | 己(정기) **辛(중기) 癸(여기)**. The order is swapped (E-2) | ❌ |
| Hidden stems 亥 | 壬, 甲 | 壬, 甲 (+ 戊 여기 in the full 3-stem table) | ⚠ convention |
| Element balance | Water 27.8 / Metal 25.3 / Earth 22.8 / Wood 16.5 / Fire 7.6 | With 丑 corrected: **Metal 27.8 / Water 25.3** / Earth 22.8 / Wood 16.5 / Fire 7.6 | ❌ Water and Metal are swapped |
| All ten-gods (stems + hidden) | as tabled | same | ✅ |
| 12운성 of 辛 | 巳 = 사, 亥 = 목욕, 대운 午 병 … 丑 양 | same (`06-twelve-stages.md` 辛 row) | ✅ |
| Auspicious-date day pillars | e.g. 2026-09-26 癸卯, 10-03 庚戌 | same (sampled 6/20) | ✅ pillars; ⚠ filter (E-11) |

> **Hour pillar: the biggest calculation risk in the whole reading.** The corrected time sits
> **28 seconds** before 寅. A recorded time of 03:11 instead of 03:10 moves the hour pillar to
> **庚寅**. Different calculators will disagree:
> - Tools with no solar correction (most Indian and many Chinese apps) show **庚寅**.
> - Longitude-only tools (most Korean 만세력) show 02:58, which is **己丑**.
> - This engine (longitude + EoT) shows **己丑**.
>
> Treat everything drawn from the hour pillar as low confidence: children and later-life themes, the
> 丑 root, the 午丑/丑未/丑戌 annual hits, 月살 at 丑, and the Resource=4 tie. This is the most likely
> explanation for any calculation "disagreement" seen when comparing apps.

**Verdict on calculation:** the four pillars are **correct**. The errors are in the hidden-stem table,
which flips the Water/Metal ranking, and a small 대운수 offset.

---

### 2. Parallel reading (independent)

#### 2.1 Pillars and hidden stems (corrected)

| | Year | Month | Day | Hour |
|---|---|---|---|---|
| Stem | 壬 상관 | 乙 편재 | **辛 (Day Master)** | 己 편인 |
| Branch | 申 | 巳 | 亥 | 丑 |
| Hidden (정/중/여) | 庚 겁재 / 壬 상관 / 戊 정인 | 丙 정관 / 庚 겁재 / 戊 정인 | 壬 상관 / 甲 정재 (/ 戊 정인) | 己 편인 / **辛 비견 / 癸 식신** |
| 12운성 (辛) | 제왕 | 사 | 목욕 | 양 |

#### 2.2 Day Master strength (일간 강약): **moderately weak (신약), borderline**

The report says "Balanced". Arguing it step by step (`09-interpretation-method.md` Step 2):

- **득령 (month command): no.** 辛 is at **사** in 巳 (`06-twelve-stages.md`). 巳 is the peak-Fire
  month and Fire controls Metal (`03-five-elements.md`). The seasonal baseline is weak.
- **득지 (day branch): no.** 亥 is Water, which drains Metal (상관), and 辛 is at 목욕 there.
- **Roots: two real ones, both off the day branch.** 申 (year) has 庚 as main qi (겁재) and is 辛's
  제왕 position, so it is a strong root, but it sits far from the Day Master and is bound by 巳申합
  (see 2.4). 丑 (hour) is wet earth holding 辛 as 중기, a genuine root plus resource, and it sits
  next to the Day Master. 巳 also carries 庚 as middle qi.
- **득세 (stems):** support comes from 己 편인 (adjacent). Drain and pressure come from 壬 상관 and
  乙 편재.
- **Balance:** support (己, 申, 丑) is outweighed by drain and pressure (壬, 乙, 巳 Fire, 亥 Water).
  The engine's own numbers agree: support 2.8 against drain 4.1 (E-4).

**Conclusion: 신약 (weak), not extreme.** **[UNCERTAIN]:** a reader who weights the 申 root heavily
could argue near-중화. The report's own Quick Reference sentence ("the drain outweighs the support")
already argues for weak while printing "Balanced".

#### 2.3 Favorable element (용신)

Two methods apply (`09-interpretation-method.md` Step 3, `17-climate-method.md`):

| Element | 억부 (weak DM → needs Resource/Peer) | 조후 (巳 = Hot band → Water; 희신 Metal) | Net |
|---|---|---|---|
| **Metal** | ✅ peer support | ✅ generates Water (희신) | **Favorable under both methods** |
| **Water** | ❌ drains a weak DM (상관) | ✅ cools the summer chart (용신) | Favorable for climate; drains the DM |
| **Earth** | ✅ resource | wet 己/丑/辰 help; dry 戊/戌/未 add heat | **Mixed.** Wet earth good, dry earth poor |
| **Wood** | ❌ wealth drains the DM | ❌ feeds Fire | **Mildly unfavorable** |
| **Fire** | ❌ controls the DM | ❌ adds heat | **Unfavorable under both methods (기신)** |

**My reading:** 용신/희신 sit on the **Metal–Water axis**, and **Fire is clearly 기신**.

- The report's *Water 용신 / Metal 희신* is **defensible** as a 조후-first reading.
- **[UNCERTAIN] ordering.** Water is already well represented (壬 visible, 亥 day branch, 申 and 丑
  hidden: ~25%), so the climate need is partly met, and the Day Master is weak. Several readers would
  therefore rank **Metal first** (it satisfies both methods), with Water second. The knowledge files do
  not decide this priority when 조후 is partly satisfied. Present both to the client; neither is wrong.
- **Where the report goes wrong:**
  - It treats Earth as flatly 구신. Wet 己丑 is actually one of the chart's supports.
  - It treats Wood as neutral 한신. Wood feeds the 기신 and drains a weak DM.
  - It never lets "Fire = 기신" reach the timing tables (E-3).

#### 2.4 Natal interactions (`02-branches.md`, `07-special-formations.md`)

| Interaction | Report | Independent | Note |
|---|---|---|---|
| 巳申 육합 (→ Water) | ✅ "transforms toward Water" | **합而不化**: Water is not in season in 巳, and the pair is disturbed by 巳亥沖 (`02-branches.md` 합화 note) | ❌ overstated. It *binds* 申, which weakens the DM's best root |
| 巳亥 沖 (month ↔ day) | ✅ | ✅ Month (career) ↔ spouse palace | ✅ |
| 申巳 형 (partial 寅巳申) | ✅ | ✅ | ✅ |
| 申亥 해 | ✅ | ✅ | ✅ |
| 申巳 파 | ✅ | ✅ | ✅ |
| 巳丑 반합 (巳酉丑, missing 酉) | — | Present but latent (no central 酉) | ⚠ omitted. It matters because 酉 arrives in the current 대운 |
| 亥丑 (亥子丑, missing 子) | — | Latent | ⚠ omitted. Completes in 2032 |
| 乙辛 (DM controls month-stem 편재) | — | Present (standard 천간충 pair) | ❌ omitted. For a male this touches the wife star |
| 상관견관 (壬 vs hidden 丙) | ✅ | ✅. 정관 is only hidden, so it is milder | ✅ |
| 격국 정관격 | ✅ named | 정관격 by 본기 fallback (`07` Part 1 step 4), but **damaged**: 상관견관 + 월지충 + weak DM | ⚠ report omits the 파격 caveat (E-9) |

#### 2.5 Stars (신살)

| Star | Report | Independent |
|---|---|---|
| 천덕귀인 on 辛 (巳 month) | ✅ | ✅ correct |
| 역마 at 巳 | ✅ (day-branch basis) | ✅. The year-branch basis gives 寅 instead (not natal) |
| 도화 not natal | ✅ | ✅. **But** 酉 = 도화 by year branch 申 arrives with the current 대운 己酉 |
| 겁살 申, 지살 亥, 월살 丑 | positions ✅ | ✅ positions on the day-branch basis. **Meanings wrong**: 지살 = movement/departure, not "bureaucratic friction". 월살 = stagnation/drying up, not "romantic turbulence" (E-7) |
| 공망 | — | 辛亥 lies in the 甲辰旬, so 공망 = **寅卯**. Not natal, but **2034 甲寅 / 2035 乙卯** are 공망 years |

#### 2.6 Relationships (male chart)

Per `11-gunghap.md` §5 (male: 재성 = wife) and §2 (palace outweighs star):

- **Spouse palace 亥:** 상관 main qi (candid, expressive). This matches the report. It is **clashed by
  the month branch 巳** (a home/career tug-of-war) and harmed by 申.
- **Spouse star:** **정재 甲 sits inside the spouse palace 亥**. That is a supportive classical signal
  (the wife star in the wife palace) and the report never mentions it. **편재 乙** on the month stem is
  directly controlled by the Day Master (乙辛), a pattern to handle gently.
- **Timing:** classical activation years are spouse-palace combinations and wealth-star years, not
  generic "Water years". Candidates in the window: **2034 甲寅** (정재 year, 寅亥合 into the spouse
  palace; but also 寅巳申 삼형 + 寅申沖 and 공망, so formal/legal care is needed). **2031 辛亥**
  activates the spouse palace heavily (亥亥 자형, 巳亥沖, 申亥해; 辛 vs 乙): a year of change at home.
  **[UNCERTAIN]:** these are tendencies, not event predictions (Ground Rule 4).

The report's partner table rates **Fire as "Compatible"** even though it lists Fire as 기신 itself. ❌ (E-3)

#### 2.7 Current 대운 己酉 (~Dec 2022 → ~Dec 2032): **favorable, for a reason the report misses**

- 己 편인 (wet earth resource) supports a weak DM. ✅
- 酉 is 辛's **건록**, a strong root. ✅
- **酉 completes 巳酉丑 金局 with the natal 巳 and 丑.** For the whole decade Metal is greatly
  reinforced, and the Fire of 巳 is pulled into the Metal frame, which eases the 巳亥 clash and the
  pressure from 관성.

This is the structural reason the decade is supportive. The report calls it favorable only because the
branch element is "Metal", and never mentions the 삼합. **[UNCERTAIN]:** whether 己 earth "muddies"
壬 water is a 궁통보감-specific idea that `17-climate-method.md` says is not transcribed in the KB, so it
is not asserted here.

Next 대운 **庚戌 (~Dec 2032 → ~Dec 2042)** is mixed. 庚 겁재 supports the DM, but **乙庚合** ties up
the month-stem wealth star (a 겁재奪財 flavour: shared money and partnerships need clear terms).
戌 is dry, hot earth and 형s the natal 丑. The report's "build and rise, plant several seeds" is too
upbeat.

Earlier decades 丙午 / 丁未 (childhood and teens) were **Fire = 기신 decades**. The report calls them
"neutral".

#### 2.8 Annual forecast 2026–2035: report vs independent

| Year | Report lean | Independent lean | Why (knowledge-file rules) |
|---|---|---|---|
| **2026 丙午** | "mixed / neutral"; listed as a *favorable business window* | **Caution (기신 year)** | 丙 정관 + 午: Fire on a weak summer Metal. 丙辛合 with the DM (합而不化 outside Water season). 丙 vs natal 壬 (Water–Fire opposition) hits the 조후 element. 午丑 해 on the hour. Career and authority matters surface as **pressure**; accept formal duties, avoid confrontations with superiors (상관견관 theme). |
| **2027 丁未** | "mixed / neutral"; *favorable business window* | **Most cautionary year in the window** | 丁 편관 attacks 辛 directly. 未 is hot, dry earth. **丑未沖** hits the hour branch, the DM's wet-earth root. **丁壬合** ties up the natal 壬 (the 조후 water). |
| 2028 戊申 | mixed | **Moderately favorable** | 戊 정인 supports (dry earth, a caveat). 申 root returns, but also 巳申 합+형+파 and 申亥해: support with contractual friction. |
| **2029 己酉** | mixed | **Favorable** | 己 편인 + 酉 건록. **巳酉丑 삼합 completes** (natal + annual + 대운). The strongest support year of the decade. |
| 2030 庚戌 | "favorable-element year" | **Mixed** | 庚 겁재 supports, but **乙庚合** (wealth star tied up; watch money and partnerships) and **丑戌 형**. |
| 2031 辛亥 | "favorable-element year" | **Mixed; relationship/home change** | 비견 support, but 巳亥沖, **亥亥 자형**, 申亥해 and 辛 vs 乙 all land on the spouse palace and the wealth star. |
| 2032 壬子 | favorable | **Mixed-positive** | **亥子丑 방합 (Water)** + 子丑합 + 申子 반합. A big 상관 Water year: good for 조후 and creative output, but it drains a weak DM and sharpens 상관견관. Watch speech and authority friction. The 대운 changes around Dec 2032. |
| 2033 癸丑 | favorable | **Favorable** | 식신 (gentle output), 丑 root, 巳丑 반합 Metal. |
| 2034 甲寅 | mixed | **Volatile** | 정재 year with 寅亥合 into the spouse palace (relationship/income activation), **but 寅巳申 삼형 completes**, 寅申沖 (the year-branch root) hits, 甲己合, and it is a 공망 year. Keep contracts written and conservative. |
| 2035 乙卯 | mixed | **Mildly unfavorable** | 편재 Wood feeds Fire. 亥卯 반합 Wood. 공망 year. 卯戌합 (Fire) with the 대운 戌. |

**Net difference:** the report ranks the near term as "2030–2033 best, 2026–2029 neutral". The chart
instead reads **2029 as the best single year**, **2026–2027 as the caution years**, and **2030–2031 as
mixed**. `career.md`'s recommendation to make a structured move in 2030–2033 should be revised toward
**2028–2029 (prepare) → 2029 (move)**, avoiding a leap in 2026–27.

#### 2.9 Health (`15-health-and-body.md`; tendencies only, Ground Rule 5)

- The report's "Water excess (kidney) / Fire deficient (heart)" comes from raw percentages that are
  (a) built on the swapped 丑 table (E-2), and (b) blind to the season. A **peak-Fire-month chart with
  a 조후 need for Water** has Fire as the *overheating* element, not a deficient one.
- Independent reading: **Metal (lungs, large intestine, skin)** is the Day Master organ system under
  Fire pressure (Fire controls Metal), and **Water (kidneys)** is the cooling reserve the chart needs
  to protect.
- Practical tendency advice: cooling and hydration, respiratory care in hot and dry seasons, and
  avoiding overheating and overwork in 2026–27. Not a diagnosis; consult a licensed professional.

---

### 3. Claim-by-claim errors in `harish-combined.md` (client-facing)

| # | Report text | Problem | Severity |
|---|---|---|---|
| 1 | "Strength: **Balanced** — … the drain … outweighs the peer and resource support" | Self-contradiction. The argument supports weak (E-4). | High |
| 2 | Element Balance: Water 27.8% highest, Metal 25.3% | 丑 hidden-stem order swapped. Metal is highest (E-2). | High |
| 3 | Hidden stems 丑: 癸 (중), 辛 (여) | Should be 辛 (중), 癸 (여). | High |
| 4 | "Avoid: Fire (기신)", yet 2026–27 appear in **"Favorable Windows"** and are called "neutral"; 丙午/丁未 decades "neutral"; Fire partner "Compatible" | 기신 never propagated (E-3). | High |
| 5 | Earth = 구신, yet the boss profile recommends an "Earth anchor" and the Earth-stem decades 戊申/己酉 are "favorable" | Internal contradiction. | Medium |
| 6 | "overrides the numeric least-represented-element pick (**Fire**)" | Exposes a folk heuristic that named the 기신 as a 용신 candidate (E-5). Remove from client text. | Medium |
| 7 | 巳申 "transforms toward Water energy" | Not in season, and disturbed by 沖, so 합而不化 (`02-branches.md`). | Medium |
| 8 | Year notes: nothing for 2029; 2030/2034/2035 incomplete | Misses 巳酉丑 삼합, 乙庚合, 丑戌형, 寅巳申 삼형, 甲己합 (E-6). | High |
| 9 | Current-decade text never mentions the 巳酉丑 삼합 | This is the real driver of the decade (E-6). | Medium |
| 10 | 지살 "bureaucratic friction", 월살 "romantic turbulence" | Wrong meanings (E-7). | Medium |
| 11 | Relationship section: no spouse-star analysis for a male chart | 甲 정재 in the spouse palace is unmentioned (E-8). | Medium |
| 12 | 정관격 "conventional respectability, large institutions" | 파격 conditions ignored (E-9). | Medium |
| 13 | 대운수 "~0.6 (~1.7 days)" | True 0.51 (1.53 days) (E-1). | Low |
| 14 | "Direct Officer **stem** values hierarchy" | There is no 정관 stem; it is hidden only. | Low |
| 15 | 辛亥 decade: "peer/rival type (**겁재**奪財)" | 辛 is 비견. | Low |
| 16 | 庚戌 and 辛亥 decades: "themes of **support and study**" | Copy-paste template (E-12). | Low |
| 17 | "a 묘/관/**충** stage" | 충 is not one of the 12 stages. | Low |
| 18 | Travel: "favorable **Water** … ages 20-29 (戊申), 30-39 (己酉), 40-49 (庚戌)" | None of those decades carries Water. | Low |
| 19 | Launch season: autumn (Business) vs winter (Health) | Contradictory. | Low |
| 20 | Friendship / Closing: "Output (4), Companion (4)" | Resource is also 4. `career.md` itself says three-way tie. | Low |
| 21 | Auspicious days 10-03 庚戌, 10-15 壬戌, 10-04 辛亥, 10-16 癸亥 | 丑戌 형 on the hour branch; 亥亥 자형 on the day branch (E-11). | Low |
| 22 | 2026 note: "best focused on visibility, speaking, visible output" | Fire here is 관성 (authority/pressure), not output. The text is keyed to the element, not the ten-god. | Medium |
| 23 | `career.md`: "Fire … the element Water … regulates; … what it already has in surplus" / "2030–2033 cleanest window" | Treats summer Fire as scarce, and relies on the wrong annual leans (see 2.8). | Medium |

### 4. What the report gets right

The pillars, all ten-gods, the 12 stages, the 대운 sequence and direction, the 세운 pillars, the
hour-boundary warning, 천덕귀인, no natal 도화, the natal 충/형/해/파 list, 상관견관, the 河圖 numbers,
and the general Metal–Water favorable axis are all correct. The Water 용신 is a defensible 조후 reading.

### 5. Recommendation

**Do not re-deliver the current PDF.** Fix E-1/E-2/E-3/E-6 in the engine (or hand-patch items 1–12 in
the markdown), regenerate, and then apply the §2.8 timing table and the §2.6 spouse-star paragraph by
hand. Confirm the birth time to the minute with the client (hospital record if possible). A one-minute
difference changes the hour pillar.

*For reflection and entertainment — not medical, legal, or financial advice.*
