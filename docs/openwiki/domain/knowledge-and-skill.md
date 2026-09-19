# Knowledge and Skill Map

## What the knowledge base is

The `knowledge/` directory holds the canonical reference for Korean Saju (사주, 四柱) interpretation. Unlike the engine, which derives deterministic chart data, the knowledge files contain the classical rules the reader uses to interpret that data.

The agent persona and ground rules live in [`CLAUDE.md`](../../../CLAUDE.md). When a reading is requested, the `/saju` skill loads these files in order.

## File guide

| File | Topic | First-use terms |
|---|---|---|
| `00-glossary.md` | Korean/Hanja glossary and romanization conventions. | Read first. |
| `01-stems.md` | 10 Heavenly Stems (천간, 天干) — yin/yang, elements, seasons, combinations. | Day Master identification. |
| `02-branches.md` | 12 Earthly Branches (지지, 地支) — zodiac, seasons, hidden stems. | Branch relationships, spouse palace. |
| `03-five-elements.md` | 오행 (五行) theory — generation, control, seasonal strength. | 용신 reasoning. |
| `04-yin-yang.md` | 음양 (陰陽) polarity — balance, contrast, Day Master gender. | Personality, polarity. |
| `05-ten-gods.md` | 십신 (十神) — ten gods relative to the Day Master. | Career, wealth, relationships. |
| `06-twelve-stages.md` | 12운성 (十二運星) — life-stage strength of the Day Master in each branch. | Timing, vitality. |
| `07-special-formations.md` | 격국 (格局), 신살 (神殺), 합/충/형/파/해. | Special patterns, red flags. |
| `08-luck-pillars.md` | 대운 (大運), 세운 (歲運), 월운, 일운. | Timing questions. |
| `09-interpretation-method.md` | Step-by-step reading procedure (9 steps). | How to structure any reading. |
| `10-output-template.md` | Report output structure and tables. | Final rendering. |
| `11-gunghap.md` | Compatibility (궁합, 宮合) — 11 sub-systems, weights, verdict bands. | Compatibility readings. |
| `12-career-and-vocation.md` | Career (직업론, 職業論) — element → industry families, ten-god → career mode, 용신 vs. Day Master, employment vs. entrepreneurship. | Career questions. |
| `13-wealth-and-business.md` | Wealth (재물론, 財物論) — 정재/편재 income styles, 식상생재 / 재생관 / 재고 chains, carrying capacity (재다신약), 겁재奪財 partnership risk, wealth timing. | Wealth & business questions. |
| `14-directions-and-relocation.md` | Directions (방위·이사, 方位·移徙) — element → direction, 용신 → favourable personal direction, move timing, colours/numbers; **not** 풍수. | Direction / relocation questions. |
| `15-health-and-body.md` | Health tendencies (건강론, 健康論) — 오행 → organ systems, excess/deficiency, controlling-cycle cascade, supportive practices by 용신, health-watch timing. Classical association only, not diagnosis. | Health-tendency questions. |
| `16-date-selection.md` | Date selection (택일, 擇日) — chart-relative day ranking vs. the natal chart, by event type, two-person events; the almanac layer is out of scope. | Auspicious-date questions. |

## How a reading is produced

1. **Confirm the chart** (`09-interpretation-method.md` Step 0). The user may provide four pillars directly or a birth date/time/place. When birth data is provided, the agent runs the engine first to produce a scaffold, then confirms the pillars with the querent.
2. **Identify the Day Master** (Step 1) using `01-stems.md`.
3. **Assess Day Master strength** (Step 2) using season, branch support, and ten-god balance.
4. **Determine 용신/희신/기신** (Step 3) using `03-five-elements.md` and `05-ten-gods.md`.
5. **Map the ten-god distribution** (Step 4) and read personality/career/relationships/health from `05-ten-gods.md`.
6. **Check special formations and stars** (Step 5) with `07-special-formations.md`.
7. **Integrate timing** (Steps 6–8) with `08-luck-pillars.md` for time-bound questions.
8. **Render** using `10-output-template.md`.

## Key interpretive principles

- **Day Master first.** Every stem and branch is read in relation to the Day Master (일간, 日干).
- **Strength before 용신.** Favorable elements are derived from whether the Day Master is strong, weak, or in a special grid — never asserted without reasoning.
- **Pillars are relational.** A pillar's meaning depends on its position (year = ancestry/early environment, month = parents/career frame, day = self/spouse palace, hour = children/late life).
- **No fatalism.** Readings describe tendencies and influences, not fixed destinies.
- **Cite the file.** Every analytical claim should reference the relevant `knowledge/` file inline, e.g. `*(see knowledge/05-ten-gods.md)`.

## Engine-first policy

When a user provides a Gregorian birth date, time, and place, the agent should:

1. Run `src/saju_engine` to derive the chart and a skeleton.
2. Present the four pillars and ask the user to confirm them (especially the month pillar, which can differ between solar-term and lunar reckoning).
3. Only after confirmation proceed with interpretive steps.

This policy reduces transcription errors and keeps the interpretation grounded in a reproducible chart.

## Special topics

### Spouse palace (배우자궁)
The day branch (일지, 日支) is the spouse palace. Its element, hidden stems, and 12운성 stage are read first for marriage/relationship questions *(see knowledge/07-special-formations.md)*.

### Special grids (격국)
- **정격 (regular grid):** Day Master strength aligns with the dominant element of the month branch's hidden stems.
- **화격 (transformation grid):** A stem combination is reinforced by the matching element in the month branch.
- **종격 (follower grid):** The chart is extremely weak and dominated by one element.

All special-form candidates are flagged `[UNCERTAIN]` unless multiple classical indicators agree.

### Compatibility (궁합)
Two-chart readings use `knowledge/11-gunghap.md`. The highest-weighted sub-system is the day-branch interaction (spouse-palace 합/충/형/파/해), followed by day-pillar classification, combined element balance, and ten-god cross-relationship. No single factor decides the verdict.

## Source anchors

- `CLAUDE.md`
- `knowledge/00-glossary.md`
- `knowledge/09-interpretation-method.md`
- `knowledge/10-output-template.md`
- `knowledge/11-gunghap.md`
