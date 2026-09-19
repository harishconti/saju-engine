# Saju Reading Skeleton (사주 감정 골격)

> ⚠️ This file is an **engine-generated skeleton**. Interpretive prose must be
> added by a qualified reader following `knowledge/09-interpretation-method.md`.

## Birth Information

- **Name**: Vishnu Priya
- **Gender**: F
- **Birth date/time**: 2001-06-07 16:45
- **Location**: Mysore (lon=76.6554)
- **Zi-hour convention**: korean

## Four Pillars

| Pillar | Stem | Branch | Hidden Stems | 12운성 |
|--------|------|--------|--------------|--------|
| Year (년주) | 辛 | 巳 | main 丙, middle 庚, residual 戊 | 사 |
| Month (월주) | 甲 | 午 | main 丁, middle 己 | 병 |
| Day (일주) | 辛 | 丑 | main 己, middle 癸, residual 辛 | 양 |
| Hour (시주) | 丙 | 申 | main 庚, middle 壬, residual 戊 | 제왕 |

## Day Master (일간): 辛

Element: Metal (Yin)

### Strength heuristic

- **Verdict**: balanced
- **Candidate 용신**: Water
- **Candidate 희신**: Metal
- **Candidate 기신**: —
- **Total score**: 0.52
- **Element counts**: {'Metal': 3.0, 'Wood': 1.0, 'Fire': 2.2, 'Earth': 1.1, 'Water': 0.6}
- **Note**: Heuristic only; final 용신 must be argued from the full chart context.

### Ten-God Distribution

| Class | Positions |
|-------|-----------|
| 비견 | year_stem, day_stem, day_branch_residual |
| 겁재 | year_branch_middle, hour_branch_main |
| 식신 | day_branch_middle |
| 상관 | hour_branch_middle |
| 정재 | month_stem |
| 편관 | month_branch_main |
| 정관 | year_branch_main, hour_stem |
| 편인 | month_branch_middle, day_branch_main |
| 정인 | year_branch_residual, hour_branch_residual |

## Branch Relationships

**六合 / 三合**: 巳申(Water)

**六害**: 丑午

**六破**: 申巳

**三刑**: 巳申

## Grid / Pattern Candidates (격국 후보)

**Regular grids (정격)**:

- 편관격 / Seven Killings Grid — month branch 午 본기 hidden stem 丁 (no hidden stem 투출; 본기 fallback per classical rule); 丁 is 편관 of Day Master 辛 (likely)

**천간합 (Ten-Stem Combinations)**:

- 辛丙 → 병신합수 (Water, not in season, no breaker, possible)

- 辛丙 → 병신합수 (Water, not in season, no breaker, possible)

## Stars

- **공망 (空亡)**: 巳
- **도화 (桃花)**: 午
- **화개 (華蓋)**: 丑
- **천을귀인 (天乙貴人)**: 午
- **지살 (地煞)**: 巳
- **연살 (年煞)**: 午
- **망신 (亡神)**: 申
- **원진 (怨嗔)**: 丑-午
- **귀문관 (鬼門關)**: 丑-午
- **월덕귀인 (月德貴人)**: 丙

## Major Luck Periods (대운)

| Age | Pillar | Ten-God | Activations | Favorability |
|-----|--------|---------|-------------|--------------|
| 9-18 | 乙未 | 편재 | 未午 (combine), 未丑 (clash) | neutral |
| 19-28 | 丙申 | 정관 | 申巳 (combine); 천간합: 丙辛→Water ×2 | neutral |
| 29-38 | 丁酉 | 편관 | — | neutral |
| 39-48 | 戊戌 | 정인 | — | neutral |
| 49-58 | 己亥 | 편인 | 亥巳 (clash), 亥申 (harm); 천간합: 己甲→Earth | favorable |
| 59-68 | 庚子 | 겁재 | 子午 (clash), 子丑 (combine) | favorable |
| 69-78 | 辛丑 | 비견 | 丑午 (harm); 천간합: 辛丙→Water | neutral |
| 79-88 | 壬寅 | 상관 | 寅巳 (harm), 寅申 (clash) | favorable |

## Annual-Luck Window (2024–2028)

| Year | Pillar | Annual Ten-God | Activations |
|------|--------|----------------|-------------|
| 2024 | 甲辰 | 정재 | 辰丑 (break) |
| 2025 | 乙巳 | 편재 | 巳申 (combine) |
| 2026 | 丙午 | 정관 | 午午 (self_punish), 午丑 (harm) |
| 2027 | 丁未 | 편관 | 未午 (combine), 未丑 (clash) |
| 2028 | 戊申 | 정인 | 申巳 (combine) |

### Focus year: 2026

_(interpret the annual pillar and its natal activations here)_
<!-- Use `sewoon.derive_sewoon()` or the `--year` CLI flag to populate. -->

## Monthly-Luck Window (2026-07 ± 2 months)

| Month | Pillar | Monthly Ten-God | Activations |
|-------|--------|-----------------|-------------|
| 2026-05 | 癸巳 | 식신 | 巳申 (combine) |
| 2026-06 | 甲午 | 정재 | 午午 (self_punish), 午丑 (harm) |
| 2026-07 | 甲午 | 정재 | 午午 (self_punish), 午丑 (harm) |
| 2026-08 | 乙未 | 편재 | 未午 (combine), 未丑 (clash) |
| 2026-09 | 丙申 | 정관 | 申巳 (combine) |

## Daily-Luck Window (2026-07-06 ± 2 days)

| Date | Pillar | Daily Ten-God | Activations |
|------|--------|---------------|-------------|
| 2026-07-04 | 己卯 | 편인 | 卯午 (break) |
| 2026-07-05 | 庚辰 | 겁재 | 辰丑 (break) |
| 2026-07-06 | 辛巳 | 비견 | 巳申 (combine) |
| 2026-07-07 | 壬午 | 상관 | 午午 (self_punish), 午丑 (harm) |
| 2026-07-08 | 癸未 | 식신 | 未午 (combine), 未丑 (clash) |

## Interpretive Sections

> ⚠️ The paragraphs below are **engine-drafted scaffolds**. They pull facts from the computed chart but are **not a finished reading**. The reader must verify, refine, and add the classical reasoning and citations from `knowledge/`.

### 1. Day Master Strength Reasoning (draft)

Day Master **辛** is Yin Metal. Born in the **午** month (peak Fire), the Day Master's 12운성 stage there is **병 (病)**. The month branch is outside the Day Master's season of peak (Autumn), so seasonal support is muted. The engine's heuristic places the chart toward **balanced**, with a candidate 용신 (用神) of **Water**. The final ruling must still consider hidden-stem support, 합 (合)/충 (沖), and any special-grid candidate.

### 2. Favorable Element (용신) & Reasoning (draft)

The heuristic reads the chart as balanced. The engine suggests cultivating **Water** (용신) because it is the most under-represented element, with **Metal** as 희신 (喜神); this should be argued from the full chart context rather than accepted blindly.

### 3. Personality (draft)

With **辛** (Metal, Yin) as the Day Master, the self carries the image of the **polished jewel or fine instrument**: precision, refinement, and a gift for detail and quality are natural strengths, while perfectionism, detachment, or being easily bruised by criticism may need attention. The chart's dominant ten-god classes are **Companion (5)** and **Resource (4)**, shaping how this self expresses in relationships, work, and stress.

### 4. Career / Wealth (draft)

The ten-god mix shows 3 Authority (관성), 1 Wealth (재성), and 2 Output (식상) occurrences. A noticeable 관성 presence points toward structure, status, and conventional accomplishment. Strong Output favors creative, expressive, or teaching paths where the self produces something visible. Fields aligned with the favorable element **Water** and the Day Master's Metal nature are generally supportive. The reader should weigh whether the Day Master is strong enough to hold wealth and authority, or whether it needs resource/peer support first.

### 5. Relationships (draft)

The spouse palace is the day branch **丑**, whose main hidden stem relates to the Day Master as **편인**. **도화 (Peach Blossom)** is present at **午**, adding charm and relational magnetism. Natal branch combinations suggest an attraction to harmony and partnership. 

### 6. Health Tendencies (draft)

This is a classical tendency reading, not a medical diagnosis. The chart's weighted element counts show **Metal** as the most present element and **Water** as the least present. Excess **Metal** may stress the lungs/large intestine (폐/대장) system; deficiency of **Water** may leave the kidneys/bladder (신/방광) system under-supported. For any health concern, consult a licensed medical professional.

### 7. Current Time-Based Themes (draft)

As of 2026, the annual pillar is **丙午** (정관 ten-god). It activates the natal chart through: harm, self_punish. The current monthly pillar is **甲午** (정재), with activations: harm, self_punish. The current major-luck period (ages 19-28) is **丙申** (정관), favorability **neutral**.

## Sources & Limits

- Engine output from `tools/saju_engine/`.
- Interpretive framework from `knowledge/09-interpretation-method.md`.
- This reading describes tendencies, not fixed outcomes.