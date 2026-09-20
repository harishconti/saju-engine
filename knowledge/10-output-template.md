# 10 · Output Template (출력 템플릿)

Use this template as the **structure** for every Saju reading. The wording can vary, but the **sections** should appear in the order below.

---

# Saju Reading (사주 감정)

## Birth Information (출생 정보)

| | |
|---|---|
| **Date of birth** | YYYY-MM-DD |
| **Time of birth** | HH:MM (or "unknown") |
| **Place of birth** | (for time-zone reference) |
| **Gender** | (for 대운 direction) |
| **Chart source** | (e.g., 사주넷, myungri app, hand-calculated) |

## The Four Pillars (사주 원국)

| | Year (년주) | Month (월주) | Day (일주) | Hour (시주) |
|---|---|---|---|---|
| **Stem (천간)** | | | | |
| **Branch (지지)** | | | | |
| **Hidden stems (본/중/여)** | | | | |
| **Ten-god of Day Master** | | | | |
| **12운성 of Day Master** | | | | |

## Day Master (일간)

> **Day Master: [한자] [한글] ([Yin/Yang] [Element])**
>
> *(see knowledge/01-stems.md)*

### Day Master Strength (신강신약)

**Verdict:** [신강 / 신약 / special grid — e.g., 종재격]

**Reasoning:**
- Month branch (season):
- Branch hidden stems:
- Stem support:
- 결론 (conclusion):

### Favorable Element (용신)

> **용신:** [element]
> **희신:** [element]
> **기신:** [element]

**Reasoning:**
- (state the logic in 1–3 sentences)

## Ten-God Distribution (십신 분포)

| Class | Stems | Branches (via hidden stems) | Total |
|---|---|---|---|
| 비겁 (Companion) | | | |
| 식상 (Output) | | | |
| 재성 (Wealth) | | | |
| 관성 (Authority) | | | |
| 인성 (Resource) | | | |

## Personality (성격)

> A 2–4 sentence summary. Reference the Day Master profile from `01-stems.md` and the dominant ten-god classes. Avoid blanket statements; integrate the chart's specific mix.

## Career & Wealth (직업과 재물)

- **Tendencies** — based on 관성/식상/재성 balance.
- **Best fields** — based on Day Master element and 용신.
- **Wealth pattern** — based on 재성 distribution (편재 dominant → variable / speculative; 정재 dominant → steady).

## Relationships (대인관계)

- **General tendency** — based on Day Master yin/yang + dominant ten-god.
- **Spouse palace (배우자궁, day branch)** — element, 12운성 stage, hidden stems. 도화살 if present.
- **Compatibility pattern** — what kinds of people naturally fit.

## Health Tendencies (건강 경향)

> ⚠️ **Disclaimer:** This is a classical tendency reading, not a medical diagnosis. Consult a licensed medical professional for health concerns.

- **Element-deficient organs** may be at risk of imbalance (see `03-five-elements.md` for organ-element mapping).
- **Element-excess organs** may also be at risk of imbalance (e.g., excess Fire may stress the Heart in classical reading).

## Time-Based Commentary (시운)

> Include this section only if the question is time-bound.

### Current Major Luck Period (현재 대운)

| | |
|---|---|
| **Period** | YYYY – YYYY (age ## – ##) |
| **Stem / Branch** | [stem / branch] |
| **Element** | |
| **Theme** | (1–2 sentences on what this decade emphasizes) |

### Current Annual Luck (올해 세운)

| | |
|---|---|
| **Year** | YYYY |
| **Stem / Branch** | [stem / branch] |
| **Element** | |
| **Theme** | (1–2 sentences) |

### Natal Activations (활성화)

- (List any 합/충/형/파/해 that the current major / annual pillars trigger.)

## Summary (종합)

> A 2–3 sentence summary that brings together the key insight of the chart in a non-fatalistic, non-medical tone. End with **what the querent can lean into** — i.e., the favorable element's themes — and what to be mindful of.

## Sources & Limits (출처 및 한계)

- **Cited knowledge files:** 00-glossary, 01-stems, 02-branches, 03-five-elements, 04-yin-yang, 05-ten-gods, 06-twelve-stages, 07-special-formations, 08-luck-pillars, 09-interpretation-method, and (as the specific question requires) 10–17 — 12-career-and-vocation, 13-wealth-and-business, 14-directions-and-relocation, 15-health-and-body, 16-date-selection, 17-climate-method, and 11-gunghap for compatibility readings. *(Added 2026-09-20 — external report review, 4th pass: this list previously stopped at 09, so a generated report's own "Sources" section under-credited the topic files it actually cited.)*
- **Limits:**
  - The four pillars are taken as supplied by the querent; this skill does not auto-derive them. *(Scope note: this governs an interactive reading conducted directly in this Claude-driven skill — it does not describe `src/saju_engine`'s packaged report-generation engine, `compute_chart()`, which does auto-derive the four pillars by design; see `09-interpretation-method.md`'s own scope note.)*
  - The hour pillar may be missing; this limits the analysis of children / late life.
  - This reading is a classical 명리 interpretation, not a prediction of fixed events.
  - The querent is encouraged to use this as one of many lenses, not a deterministic one.

---

## How to Use This Template

1. Fill in **Birth Information** and **Four Pillars** first — these are the data; the rest is interpretation.
2. The **Day Master** and **Favorable Element** sections are the **two key judgments** — they should each be supported by a short reasoning block.
3. The **Ten-God Distribution** table gives the reader a quick visual on what the chart emphasizes.
4. The **thematic sections** (Personality, Career, Relationships, Health) should each be 1 short paragraph (~3–5 sentences) referencing the chart's specific findings — avoid generic copy-paste.
5. **Time-Based Commentary** is optional; include it when the question is time-bound.
6. **Summary** is the closing — keep it warm, grounded, and non-fatalistic.
7. **Sources & Limits** is mandatory — it anchors the reading in the knowledge base and protects against over-claiming.

For worked examples, see `candidates_horoscope/reports/sruthi/sruthi-report.md` and other candidate folders.
