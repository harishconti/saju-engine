# 09 · Interpretation Method (해석 절차)

A step-by-step procedure for reading a Saju chart. Follow these steps in order; do not skip ahead.

## Step 0 · Confirm the Chart

Before interpreting, **confirm the four pillars** with the querent. A Saju reading is only as good as the chart it's based on. The user must provide:

- **년주 (Year Pillar)**
- **월주 (Month Pillar)**
- **일주 (Day Pillar)** — the Day Pillar contains the Day Master
- **시주 (Hour Pillar)** — only needed if the querent knows the exact birth time

If the querent gives a Gregorian date but no pillars, ask them to compute the pillars from a trusted source (e.g., a Korean 명리 app like "사주넷" or "신점명리" or a mainland BaZi tool) and **double-check the month pillar is the solar-term month, not the lunar month**. Do not auto-derive the pillars in this skill.

If the querent does not know the birth time, **proceed without the hour pillar** and note that the hour pillar would add detail. Do not invent a default time.

> **Scope note (added 2026-09-20, external report review, 3rd pass).** "Do not auto-derive the pillars in this skill" governs an interactive reading conducted directly in this Claude-driven skill, where pillar math has not been independently checked in that conversation. It does not describe `src/saju_engine`'s packaged report-generation engine (`compute_chart()`), which *does* auto-derive the four pillars from a birth date/time/location — that is a separate, independently validated code path (see `docs/openwiki/architecture/engine.md` and the engine's own test suite) and is the intended way client-facing reports (`candidates_horoscope/`) are produced. A reader of this knowledge base alone, without that context, could otherwise read this file as contradicting the product it documents.

## Step 1 · Identify the Day Master (일간, 日干)

The Day Master is the **stem of the day pillar**. Write it at the top of the analysis with its full identification:

> "Day Master: **甲 갑** (Yang Wood)"

> *(See `knowledge/01-stems.md` for the master stem table.)*

This is the **self** in the chart — the querent.

## Step 2 · Assess Day Master Strength (신강신약, 身強身弱)

Determine whether the Day Master is **신강 (身強, strong)** or **신약 (身弱, weak)**. This is the foundation of all further analysis.

### Factors that STRENGTHEN the Day Master

1. **Seasonal support (월지, 月支):** Is the Day Master in **season**? See `01-stems.md` for Season of Peak.
   - If the month branch is the Day Master's peak season → strongest support.
   - If the month branch is the Day Master's own element (e.g., 甲 day master + 寅 or 卯 month) → strong support.
2. **지 (Branch) support (지지):** Do the year, day, and hour branches contain the Day Master's element in their 본기 or middle hidden stems?
3. **인성 (Resource) presence:** Does the chart have stems that generate the Day Master (인성)?
4. **비겁 (Companion) presence:** Does the chart have stems/branches of the same element as the Day Master?

### Factors that WEAKEN the Day Master

1. **Off-season birth:** The month branch is in a season that does not support the Day Master (e.g., Wood day master in autumn Metal season).
2. **관성 (Authority) presence:** Stems that control the Day Master.
3. **재성 (Wealth) presence:** Stems that the Day Master controls (drain).
4. **식상 (Output) presence:** Stems that the Day Master generates (drain).
5. **Natal branches sitting in the day pillar's 공망 (void).** *(Reworded 2026-09-20 — external report review, 4th pass: 공망 is computed relative to the day pillar's 순 (旬) in the 60-cycle and applies to branches, not to "the Day Master" — a stem — directly.)*

### Quick Reference

| Indicator | Strong | Weak |
|---|---|---|
| Day Master in season | ✓ | |
| Day Master off season | | ✓ |
| 인성 in stems | ✓ | |
| 비겁 in stems | ✓ | |
| 과도한 관/재/식 in stems | | ✓ |
| Branch hidden stems support DM | ✓ | |
| Branch hidden stems drain DM | | ✓ |

> The classical definition: Day Master is **신강** if the month branch's hidden stems + 1 supporting ally in stems keep it strong. **신약** otherwise. Some schools use a numeric count; others use seasonal dominance. Always state your reasoning.

> A **special grid (종격, 화격, 양인격)** may apply if the strength is **extreme** in either direction — see `07-special-formations.md`.

## Step 3 · Determine the Favorable Element (용신, 用神)

The 용신 is **the single most important key** to a chart's reading. It is the element that, if added, would balance the chart most.

### Logic

**0. First, check whether 조후 (climate-balance) governs at all** — see
`knowledge/17-climate-method.md`, revised 2026-09-19. Priority between 조후
and 억부 (strength-balance) is gated on **climate extremeness, not on the
strength verdict**: a chart born in the hot summer months (巳午未), the cold
winter months (亥子丑), or the two 燥/濕 storage months 辰 (damp) / 戌 (dry) has
a non-temperate climate band, and 조후 governs the headline 용신 there
**regardless of whether the Day Master reads as 신강, 신약, or balanced.**
This is the sourced classical doctrine (조후와 부억에는 명식을 떠난 고정 순서가
없습니다 — priority follows climate extremeness, not verdict), not a
tie-breaker reserved for balanced charts only. Only for a **temperate-month
birth** (寅卯申酉, i.e. none of the eight non-temperate branches above — 巳午未
+ 亥子丑 + 辰/戌 = 8, matching 12 − 8 = 4 temperate branches) does 조후
have no opinion, and the 억부 logic below (Steps 1–3) becomes the primary
signal.

1. **If 신강 (Day Master is strong) — and the month is temperate:** The chart has too much of the Day Master. The 용신 is one of the elements that **drains or controls** the Day Master:
   - **식상 (Output)** is the most common first choice for 신강 — it channels the Day Master's energy out.
   - **재성 (Wealth)** is the second choice.
   - **관성 (Authority)** is the third choice (sometimes first if the chart is heavily insubordinate).
2. **If 신약 (Day Master is weak) — and the month is temperate:** The chart needs to support the Day Master. The 용신 is one of the elements that **strengthens** it:
   - **인성 (Resource)** is the most common first choice — it feeds the Day Master.
   - **비겁 (Companion)** is the second choice.
3. **If special grid (종격, 화격):** The 용신 may be the **dominant element** of the chart (the element of the chart's overall character), not the Day Master's element.
4. **If the Day Master is balanced and the month is temperate:** the 억부
   logic above has no clear strong/weak signal either, so fall back to the
   chart's numeric least-represented element as a weaker, provisional
   candidate — see `knowledge/17-climate-method.md` for the exact merge.

> **Historical note (resolved 2026-09-19):** an earlier version of this file
> gated 조후 on the verdict (balanced-only) and told the reader that "a clear
> strength imbalance stays the primary signal" for strong/weak charts even in
> a non-temperate month. That premise was found to have no direct classical
> source support (see `docs/research/2026-09-validation-climate.md` §5) and
> is superseded by Step 0 above. If you see report prose or older notes
> repeating the verdict-gated framing, treat it as stale and defer to this
> file's current Step 0.

### 희신 (Supporting Element)

The element that **generates** the 용신. E.g., if 용신 is Water, 희신 is Metal (Metal generates Water).

### 기신 / 한신 / 구신 (Other Classifications)

- **기신 (Unfavorable Element):** The element that **opposes** the chart's balance. Often the element the chart already has in excess.
- **한신 (Draining Element):** The element that the 용신 generates (drains it).
- **구신 (Restraining Element):** The element that controls the 용신.

> Always state the 용신 AND its reasoning. A reading without a stated 용신 is incomplete.

## Step 4 · Decode the Ten Gods (십신)

For each stem and each branch's hidden stems, identify the ten-god relationship to the Day Master. Use the master reference table in `05-ten-gods.md`.

Lay them out in a table for clarity.

| Pillar | Stem | Branch | Branch hidden stems (본/중/여) | Ten-god of Day Master |
|---|---|---|---|---|
| 년주 (Year) | ... | ... | .../.../... | ... |
| 월주 (Month) | ... | ... | .../.../... | ... |
| 일주 (Day) | ... (Day Master) | ... (Spouse palace) | .../.../... | ... (Day Master is the self) |
| 시주 (Hour) | ... | ... | .../.../... | ... |

> For a **career or wealth** reading, carry the ten-god mix into
> `knowledge/12-career-and-vocation.md` and `knowledge/13-wealth-and-business.md`.

## Step 5 · Read Each Pillar in Relation to the Day Master

For each pillar, interpret:

- **Stem:** What ten-god is it? What does that ten-god mean in this position? (Year = ancestors / outer persona, Month = career / parents, Day = self / spouse palace, Hour = children / late life)
- **Branch:** What element, what is the 12운성 stage of the Day Master in this branch? Does the branch form any 합/충 with other branches?
- **Branch's hidden stems:** What ten-gods are stored here?

### Quick Pillar Meanings

| Pillar | Self | Spouse / Family | Career | Children |
|---|---|---|---|---|
| Year (년주) | Ancestors, outer persona | Grandparents | Childhood environment | — |
| Month (월주) | Parents (esp. mother) | Siblings | Social standing, career path, age 15–30 | — |
| Day (일주) | The self (stem) | **Spouse palace (branch)** | — | — |
| Hour (시주) | Children, late life | Children | Old-age, children, age 50+ | Children |

> Thematic hand-offs: **wealth** themes → `knowledge/13-wealth-and-business.md`;
> **direction / relocation** themes → `knowledge/14-directions-and-relocation.md`.

## Step 6 · Check Special Formations (격국, 신살, 합, 충, 형, 파, 해)

Use `07-special-formations.md` to:

1. **Identify the 격국** (chart structure) based on the month stem.
2. **Check 신살** (stars) based on the day branch (or year branch / day stem depending on school).
3. **Check branch relationships** (합, 충, 형, 파, 해) between all four branches.

## Step 7 · Integrate Time-Based Luck (대운 / 세운)

If the question is **time-bound** (e.g., "When will I get married?" or "How is 2026 looking?"):

1. Compute the **major luck periods** (see `08-luck-pillars.md`).
2. Identify the **current major luck period** and the **next** if relevant.
3. Identify the **current annual pillar** and check for natal activation.
4. Read the **integration** of natal + major luck + annual.

## Step 8 · Synthesize the Reading

Now — and only now — write the reading. Organize by theme:

1. **Pillar table** (년/월/일/시 with stem, branch, ten-god)
2. **Day Master strength** (신강 / 신약 / 격국) and reasoning
3. **Favorable element** (용신) and reasoning
4. **Ten-god distribution** (which classes are present, in what density)
5. **Personality** — based on Day Master + ten-god mix
6. **Career / wealth** — based on 재성, 관성, 식상
7. **Relationships** — based on Day Branch (spouse palace), 도화살, 정재/편재
8. **Health** — based on element balance, organ correspondences
9. **Time-based commentary** (if asked) — based on current major luck + annual luck
10. **Closing note** — what the querent can lean into (in line with their 용신) and what to be mindful of

> Topic deep-dives for this step: career/wealth →
> `knowledge/12-career-and-vocation.md`, `knowledge/13-wealth-and-business.md`;
> direction / relocation → `knowledge/14-directions-and-relocation.md`; health
> tendencies → `knowledge/15-health-and-body.md`; auspicious dates (택일) →
> `knowledge/16-date-selection.md`.

## Step 9 · Cite Sources and Note Limits

At the end of the reading:

- Cite which knowledge files were used.
- Note any **uncertainty** (e.g., "the 시주 is missing; this section would be clearer with it").
- Note the **scope** (e.g., "I do not auto-derive the four pillars in this skill; please verify them with a trusted source").

## Quick Workflow Reference (1-Page)

```
1. Confirm the chart with the querent (년/월/일/시).
2. Identify the Day Master (일간).
3. Assess Day Master strength (신강/신약).
4. Determine the Favorable Element (용신).
5. Decode the Ten Gods (십신) for each stem and branch's hidden stems.
6. Read each pillar in relation to the Day Master.
7. Check special formations (격국, 신살, 합/충/형/파/해).
8. If time-bound, integrate 대운/세운.
9. Synthesize the reading.
10. Cite sources and note limits.
```

## How to Use This File

- Follow the steps **in order** for every reading.
- Do not skip Step 0 — a chart from a wrong source invalidates everything.
- Do not skip the **reasoning** at Step 2 and Step 3 — the analysis without reasoning is just label-slapping.
- For the **output structure**, use `knowledge/10-output-template.md`.
- For the **worked examples**, see `candidates_horoscope/reports/` (e.g. `sruthi/`, `pawan/`).
