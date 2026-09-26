# 08 · Luck Pillars (대운 · 세운 · 월운)

A Saju reading is incomplete without considering **time-based** influences. The natal chart is the **constitution**; the luck pillars are the **weather** that passes over it.

This file covers:

- **대운 (大運, Major Luck Periods)** — roughly decade-long cycles
- **세운 (歲運, Annual Luck)** — year-by-year
- **월운 (月運, Monthly Luck)** — month-by-month
- **일운 (日運, Daily Luck)** — sometimes used for short-horizon questions

## Part 1: 대운 (Major Luck Periods)

대운 is determined by:

1. The **direction of progression** (forward / backward) of the major luck sequence.
2. The **starting age** of the first major luck period.
3. The **content of each major luck period** (10-year stems and branches in sequence).

### Direction of Progression

The classical rule (Korean 명리 convention):

| Year stem yin/yang | Gender | Direction |
|---|---|---|
| Yang (양) | Male (남) | **Forward** (순행) — from month pillar to next |
| Yang (양) | Female (여) | **Backward** (역행) — from month pillar to previous |
| Yin (음) | Male (남) | **Backward** (역행) — from month pillar to previous |
| Yin (음) | Female (여) | **Forward** (순행) — from month pillar to next |

> **Yin / yang of the year stem** decides the direction. **Gender of the querent** decides whether the direction is "forward" or "backward" relative to the cycle.

In simpler terms: **same-yang-year-and-gender** or **same-yin-year-and-gender** is **forward**; otherwise **backward**. (Yang-year-male and yin-year-female go forward; yang-year-female and yin-year-male go backward.)

### Starting Age

The starting age is the number of days from the **birth date** to the **previous 節氣 (節, month-opener)** (역행) or **next 節氣 (節, month-opener)** (순행), divided by 3. *(Corrected 2026-09-20 — external report review, 4th pass: this line previously said "years," inverting the "3 days = 1 year" rule the very next paragraph correctly states.)*

In other words:
- For **forward (순행)**: Count the number of days from the birth date to the **next 節氣** (one of the 12 month-opener solar terms: 立春, 驚蟄, 淸明, 立夏, 芒種, 小暑, 立秋, 白露, 寒露, 立冬, 大雪, 小寒). Divide by 3. The result is the starting age.
- For **backward (역행)**: Count the number of days from the birth date to the **previous 節氣** (same 12 month-openers). Divide by 3.

> 1 day = 4 months of life. 3 days = 1 year. So 10 days = ~3.3 years.
>
> **Display convention (added 2026-09-26, E-13).** Korean 만세력 apps round days ÷ 3 to a whole
> **대운수** (a remainder of 1.5 days or more rounds up) and list the decades as N, N+10, N+20…, often
> in Korean age (세는나이). This engine's tables use 10-year age-range labels (0–9, 10–19…) and state the
> precise fractional start separately, so the two presentations describe the same periods with labels
> that can differ by about a year. *(Sources: Korean Wikipedia 「대운 (사주팔자)」; KNS뉴스통신
> 「제31강 대운수 산출법」.)*

> **Note on terminology:** the Korean 명리 tradition uses the 12 **節氣 (節, month-openers)** for the starting-age calculation, not the 24 jieqi as a whole. The 24-jieqi version (counting to the next 節 OR 中) gives systematically shorter starting ages and is **not** the standard Korean convention.
>
> **Provenance note (revised 2026-09-20):** this rule was previously footnoted as "verified against Sruthi, Pawan, and Harish readings" — that is circular (the product's own generated reports cannot validate the classical convention the product itself implements) and has been removed. The 12-節氣 vs. 24-jieqi distinction stated above still stands as the documented engine behavior; it has not been independently cross-checked against an external classical or academic source in this file. Treat it as the implemented convention, not as externally verified doctrine, until such a source is added.

The first major luck period begins at this age. Each major luck period lasts **10 years**.

### Content of Each Major Luck Period

The major luck sequence follows the **sixty-甲子 (육십갑자)** cycle:

- **Forward (순행):** The first major luck = month pillar + 1 step in the 60 cycle. The second = +2 steps. Etc.
- **Backward (역행):** The first major luck = month pillar - 1 step. The second = -2 steps. Etc.

For example, if the month pillar is 辛丑 (신축):
- Forward next = 壬寅 (임인)
- Then = 癸卯 (계묘)
- Then = 甲辰 (갑진)
- Etc.

If backward:
- Backward previous = 庚子 (경자)
- Then = 己亥 (기해)
- Then = 戊戌 (무술)
- Etc.

### How to Interpret a Major Luck Period

When a new major luck period arrives, the **stem and branch of the major luck** enter the chart as a "guest." Their element is added to the chart's overall balance. The major luck:

1. **Activates** any natal relationships involving the same element (e.g., major luck brings 申 → if natal chart has 寅, the 寅申 충 is "lit up").
2. **Strengthens or weakens** the Day Master if the major luck's element supports or drains it.
3. **May bring** a major life theme for those 10 years (career, family, relocation) depending on the relationship.

## Part 2: 세운 (Annual Luck)

The 세운 is the **pillar of the current calendar year**. For example, 2026 is the year of 丙午 (병오) — Yang Fire over Yang Fire. Each year of life has a new 세운.

### How to Use the Annual Pillar

1. **Identify the annual stem and branch.**
2. **Determine the annual element** and its relationship to the Day Master.
3. **Check for natal activation:**
   - Annual branch vs. natal branches → 충, 합, 형, 파, 해?
   - Annual stem vs. natal stems → 합 (천간합)? 천간충 (甲庚, 乙辛, 丙壬, 丁癸)? *(see `01-stems.md`
     §Stem Combinations and §Stem Clashes — check against **every** natal stem, not only the Day
     Master. Updated 2026-09-26, E-7.)*
4. **Read the year's theme** as the "weather" of the year.

### Common Patterns (Cheat Sheet)

| Pattern | Reading |
|---|---|
| Annual branch clashes natal Day branch (배우자궁) | Year of relational change — marriage, breakup, partner's change, home change |
| Annual branch combines with natal month branch (월지) | Year of career / life-stage change |
| Annual stem is the Day Master's 정관 | Year of recognition, formal position, exam, marriage (in some schools) |
| Annual stem is the Day Master's 편관 | Year of pressure, discipline, possible legal/official issues |
| Annual stem is the Day Master's 정재 or 편재 | Year of money — earning, spending, financial moves |
| Annual stem is the Day Master's 식상 | Year of expression, creativity, output, children |
| Annual stem is the Day Master's 인성 | Year of support, learning, rest, recovery |
| Annual stem is the Day Master's 비겁 | Year of competition, partnership, self-reliance |

## Part 3: 월운 (Monthly Luck)

The 월운 is the pillar of the current month, used for short-horizon timing. Same logic as 세운, narrower window. Often used to refine within an annual reading.

## Part 4: 일운 (Daily Luck) and 시운 (Hourly Luck)

Used in some schools for very short-horizon questions (electional astrology, daily-fortune readings). The user can ask for these if they want; the analysis follows the same logic but with much narrower time scope.

## Part 5: Interactions — 대운 + 세운 + Natal

When reading a period, classical 명리 considers three layers:

1. **Natal chart (사주, 사주 원국)** — the constitution.
2. **Major luck (대운)** — the decade's weather pattern.
3. **Annual luck (세운)** — the year's weather event.

A rule of thumb: **a "trigger" is most powerful when all three layers point in the same direction.** E.g., if the natal chart has 寅申 충, the major luck brings 申, and the annual brings 寅 — the 충 is "doubly activated" and the year may bring a sharp event.

Conversely, if a natal pattern is only weakly present and the time-based luck is "out of phase" with it, the pattern may stay dormant or be neutralized.

## Part 5b: Relationship & Marriage Timing (결혼 시기)

*(Added 2026-09-26, E-8 of the 2026-09-25 engine audit.)* Commitment timing is read from the
**spouse star** and the **spouse palace**, not from the 용신 alone:

1. **Spouse star (배우자성).** Male querent → 재성 (정재/편재); female querent → 관성 (정관/편관)
   *(same gender mapping as `11-gunghap.md` §G)*. A 대운 whose stem carries the spouse star **opens a
   window**; a 세운 whose stem carries it **selects the year** within that window.
2. **Spouse palace (배우자궁, the day branch).** A 세운/대운 branch that forms **육합 or 삼합** with the
   day branch is read as the palace being "bound" — meetings and formal commitments cluster here.
3. **Obstructions.** A year that **충/형/파** the day branch is read as unfavorable for formalising
   (better for deepening privately), as is a year dominated by the spouse star's classical obstruction —
   **상관** (which strikes 관성) for a female querent, **겁재** (which contests 재성) for a male.
4. The more of (1)–(3) converge, the stronger the window. 용신/희신 years remain a supporting
   (not primary) signal. Phrase every result as a tendency, never a prediction (Ground Rule 4).

*Sources:* 사자사주 「결혼 시기 사주: 배우자 만나는 시기 보는법」 ("배우자를 상징하는 십성(여성: 관성, 남성:
재성)이 대운이나 세운에 들어오는 타이밍으로 판단", "배우자궁인 일지의 상태가 그 바탕"; checklist: spouse star in
대운, 세운 strengthening it, 일지 합 with the annual branch, absence of 충/파, weakened 상관/겁재) —
<https://www.sazasaju.com/blog/marriage-timing-guide>; 정사주 「결혼운사주 보는 법」 —
<https://jeongsaju.com/blog/marriage-fortune-saju-interpretation>.

## Part 6: Useful Tables for Speed

### 2026 Annual Pillar

| Year | Annual Pillar (세운) | Element | Note |
|---|---|---|---|
| 2026 | 丙午 (병오) | Yang Fire | Year of the Horse |
| 2027 | 丁未 (정미) | Yin Fire | Year of the Goat |
| 2028 | 戊申 (무신) | Yang Earth | Year of the Monkey |
| 2029 | 己酉 (기유) | Yin Earth | Year of the Rooster |
| 2030 | 庚戌 (경술) | Yang Metal | Year of the Dog |
| 2031 | 辛亥 (신해) | Yin Metal | Year of the Pig |
| 2032 | 壬子 (임자) | Yang Water | Year of the Rat |
| 2033 | 癸丑 (계축) | Yin Water | Year of the Ox |

> The annual pillar **does not change at Lunar New Year**; it changes at **입춘 (Lichun)**, around Feb 4. The exact moment of 입춘 marks the start of the new year in Saju.

## How to Use This File

- To determine the major luck direction → use the Direction of Progression table.
- To determine the starting age → use the Starting Age rule (3 days = 1 year).
- To interpret a major luck period → use the relationship rules + natal activation.
- To interpret an annual or monthly period → use the Cheat Sheet and the Interaction rules.
- For specific year lookup (e.g., 2026) → use the table in Part 6.
