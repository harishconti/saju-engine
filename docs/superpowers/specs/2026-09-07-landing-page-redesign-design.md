# Cosmic Saju Landing Page — Redesign Design Spec

**Date:** 2026-09-07
**Status:** IMPLEMENTED (2026-09-07) — plan `docs/superpowers/plans/2026-09-07-landing-page-redesign.md`; build/lint/133 vitest green; screenshot pass desktop+mobile / light+dark; 0 hydration errors; no horizontal body scroll; reduced-motion safe.

### Known polish follow-ups (not blockers)
- `WhatsInside` right column is short → empty space beside the tall TOC on desktop.
- Dead vertical space where an inline form step is short (forms sit between Pricing and HowItsBuilt).
- `ElementBalance` wheel: the `--c-surface-2` base ring reads as an empty grey segment at the top.
- `PersonalReports` "Essential" popular-card `ElementalRule` sits just under the "Intro $9" badge — tighten z/position.
- `AboutReader` "I ran my own chart" links to `#demo` as a placeholder until the founder's own report exists.
**App:** `apps/landing-page/` (Next.js 16, Tailwind v4, shadcn/ui, next-themes)
**Related:** `improvements_issues.md` §5 (LP items), the 2026-09-07 USD/global pivot

## User-approved direction (2026-09-07)

| Question | Decision |
|---|---|
| Depth | **Full restructure + visual system** — merge ~15 sections → ~9, reorder for a proof-first narrative, build a reusable Saju visual language |
| Aesthetic | **Premium editorial** — keep dark cosmic palette + gold + serif, but treat it as a serious analysis product: real diagrams, data-viz, restrained motion, credibility cues. Mysticism as accent, not theme |
| Custom visuals | **Yes, build the set** — theme-aware, responsive SVG React components used across hero, "why Saju", demo, and "what's inside" |
| Hero visual | **Option A** — a live four-pillars chart (SVG, elemental colors, draws itself in) |
| Demo report | **Keep it** (RM / masked couple) — restyle and move up, don't replace |

---

## 1. Problem

The current landing page (`src/app/page.tsx` → 15 section components) has:

- **Monotony** — nearly every section is: centered gold-gradient serif `<h2>` + muted `<p>` + a grid of bordered cards on `bg-cosmic-surface/50`. No layout variation, no imagery, no diagrams. Screenshots show large empty dark gaps and repetitive card rows.
- **Redundancy** — `WhatIsSaju`, `WhatYouReceive`, `TrustClarity` are ~60% the same content (4 icon-cards each). "Accurate birth details" is repeated verbatim in `ImportantDetails`, `FAQ`, and `Footer`. `FinalCTA` re-lists all pricing as 5 buttons.
- **Proof buried** — `DemoReports` (the strongest asset — a real chart) is section #10, below 9 sections of generic claims. `PersonalReports` (pricing) is section #4, before the reader understands or trusts the product.
- **The product is inherently visual** (four pillars, five elements, ten-god distribution, 대운 timeline) and **none** of that visual language appears on the page — even though `src/saju_html/svg_charts.py` already generates element-balance and decade-roadmap SVGs server-side.
- **Theme under-used** — `star-bg` only on the hero; the elemental palette, Korean typographic accents, and a "pillar" motif are absent.
- **CTA sprawl** — "Get My Report" / "Get Free Sample" / "Get Essential Report" / "Buy Essential — $19" / "Explore Reports" — five+ label variants; `FinalCTA` offers 5 competing buttons.
- **Fake-feeling scarcity** — "Only 15 reports processed per week" reads as manufactured urgency.

## 2. Goals / Non-goals

### Goals

- G1. Reduce ~15 sections to ~9 with a proof-first narrative arc (§4).
- G2. Ship a reusable, theme-aware, responsive Saju **visual system** (`src/components/viz/`, §5).
- G3. Every section: a distinct layout shape, a `<SectionHeading>` with an eyebrow label, and content a first-time visitor understands in one scroll.
- G4. Move the demo/proof above pricing.
- G5. One canonical primary CTA label and exactly two button styles + one text link.
- G6. Keep it **premium-editorial**: diagrams and data over ornament; motion subtle and `prefers-reduced-motion`-safe.
- G7. Preserve everything that works: theme system, light/dark, security headers/proxy, the intake forms and their handlers, the gated `Testimonials`, the RM/couple demo content.
- G8. `npm run build` + `npm run lint` + `npm test` stay green. Lighthouse ≥ current.

### Non-goals

- N1. No backend / API / checkout / payment changes (still `improvements_issues.md` P1).
- N2. No new engine work; the viz components consume static demo data, not a live engine call.
- N3. No real testimonials created; the section stays gated (`TESTIMONIALS_APPROVED = false`).
- N4. No deployment.
- N5. No change to the intake form field set or submission contract (visual restyle only).
- N6. No design-token color renames that would ripple through shadcn primitives; **add** tokens, don't rename.
- N7. Not building a live "calculate my chart" widget on the marketing page (that's LP10, separate).

---

## 3. Visual language (premium editorial)

**Keep:** `#08080f` near-black ground, gold `#C9A84C` (+ light/dark variants), purple `#7B5EA7` accent, Cormorant Garamond display serif, Inter body, `star-bg`, `gold-text` gradient, `card-hover`, scroll-reveal, light theme.

**Add:**

### 3.1 Elemental palette (new CSS tokens in `globals.css`)

Mirror the engine's `ELEMENT_COLORS` (`src/saju_engine/report_data.py`), adjusted for contrast on the dark ground:

| Element | Token | Dark | Light |
|---|---|---|---|
| Wood | `--el-wood` | `#3ECf8E` | `#1F9D6B` |
| Fire | `--el-fire` | `#F0654E` | `#D1442E` |
| Earth | `--el-earth` | `#E0A94C` | `#B5832F` |
| Metal | `--el-metal` | `#AEB4BE` | `#6B7280` |
| Water | `--el-water` | `#5B9CF6` | `#3B7DD8` |

Plus `--lean-favorable` `#3ECf8E`, `--lean-mixed` `#E0A94C`, `--lean-challenging` `#F0654E`.

### 3.2 Recurring motifs

- **Elemental rule** — a 1px horizontal gradient `wood→fire→earth→metal→water` used as: section dividers, the top edge of the "popular" pricing card, the footer top border, the hero underline. `.el-rule` utility.
- **Korean watermark** — `四柱` (or `사주`) set in the display serif at ~14rem, `opacity: 0.03–0.05`, absolutely positioned behind the hero and "the reader" sections. Never interactive; `aria-hidden`.
- **Eyebrow labels** — small (0.72rem), letter-spaced, uppercase, gold, above each section title.

### 3.3 Section rhythm

Alternate the 9 sections across four "shapes" so no two adjacent sections look alike:

1. **Split** — copy one side, a large visual the other (hero, "higher resolution", "how it's built").
2. **Centered feature** — heading + a single focused artifact, not a card grid (demo, pricing).
3. **Full-bleed dark** — `star-bg`, minimal (final CTA, section transitions).
4. **Editorial block** — asymmetric, text-forward, one inset visual (the reader, FAQ).

### 3.4 Motion

- Reveal: reduce travel to `translateY(12px)`, `0.5s`, and **stagger** direct children by 60ms
  (opt-in via `data-reveal-stagger` so existing sections are untouched).
- **Signature moment** — the hero four-pillars chart "stamps in" one **column** at a time, 90ms
  apart, ≤ 800ms total (fade + 6px rise per column). Like setting type / stamping an almanac. Once.
- Element-balance bars: width transition on first reveal.
- All gated behind `@media (prefers-reduced-motion: no-preference)`; a `reduce` block resets to visible.

### 3.5 Design tokens — refined (grounds the "premium editorial" direction in the subject)

The subject's real artifact is the **만세력** (perpetual almanac) a Korean reader consults — vertical
columns of 한자, computed tables, and a red seal (낙관 / 인장) stamped on the finished reading. The
page is "the almanac, set in type."

**Typography — 3 roles:**
| Role | Face | Use |
|---|---|---|
| Display | **Cormorant Garamond** (already loaded) | headlines only, used with restraint |
| Body | **Inter** (already loaded) | prose |
| **Utility / data (NEW)** | **IBM Plex Mono** — add via `next/font/google` as `--font-mono` | eyebrow labels, romanizations, ages, %, pillar position labels, chart data. Makes it read as *computed*, not mystical. |

**Elemental palette = 오방색** (Korea's five traditional directional colors), adjusted for the dark
ground. This replaces the generic web-element colors in §3.1:

| Element (direction / 오방색) | `--el-*` (dark) | `.light` |
|---|---|---|
| Wood — 동 / 청 (blue-green) | `#3FB68A` | `#1F9068` |
| Fire — 남 / 적 (cinnabar) | `#E24C36` | `#C13B27` |
| Earth — 중앙 / 황 | `#E0A94C` | `#B5832F` |
| Metal — 서 / 백 | `#C7CBD1` | `#6B7280` |
| Water — 북 / 흑 (deep blue on dark) | `#4B79C4` | `#3B63A8` |

`--lean-favorable: var(--el-wood)` · `--lean-mixed: var(--el-earth)` · `--lean-challenging: var(--el-fire)`.
`--seal: var(--el-fire)` — the cinnabar is reused, deliberately, for the seal mark.

**Signature element:** the **four pillars as vertical almanac columns** — each pillar a column read
top-down (stem 한자 → branch 한자 → hidden-stem chips), the four columns Year→Hour left-to-right,
cell tint per 오방색 element. Plus a small **cinnabar seal mark** — a `1px` cinnabar square containing
`人` ("a person"), captioned "hand-checked" — recurring at: the hero trust row, the foot of the demo
card, the footer. Component: `<SealMark label?="hand-checked" />` (added to the viz set).

**Structural devices:** numbered markers are used **only** where order is real information — the four
pillars (년/월/일/시) and "How it's built" (data → compute → interpret). Not elsewhere.

---

## 4. Section arc (new)

`src/app/page.tsx` `<main>` renders, in order:

| # | Section | id | Shape | Built from | Key content |
|---|---|---|---|---|---|
| 1 | **Header** | — | fixed bar | `Header` | Logo · nav (Why Saju / See a reading / Pricing / How it works / FAQ) · theme toggle · **one** primary CTA "Get your free chart snapshot" |
| 2 | **Hero** | — | Split + watermark | `Hero` | Left: eyebrow "Korean Saju · 四柱" → serif headline → 1-sentence subhead → primary CTA + text link "See a real reading ↓" → a 3-item trust row (7-day guarantee · 24-hour delivery · classical texts cited). Right: `<FourPillarsChart>` of the RM demo chart + a small `<ElementBalance variant="wheel">`. Replaces the "15 slots" badge with "Every reading is hand-checked before it's sent." |
| 3 | **Higher resolution than a sun sign** | `why` | Split | *new* (absorbs the "higher resolution" card blurbs) | Left: the pitch — 1 sun sign vs 8 characters; deterministic calculation, the value is in a careful reading; not a horoscope. Right: a simple comparison visual — a lone "♌" vs the 8-glyph pillar grid, or `<ElementBalance>` showing "your mix, not one label". |
| 4 | **See a real reading** | `demo` | Centered feature | `DemoReports` (moved up, rebuilt) | Rebuilt RM card: `<FourPillarsChart>` + `<ElementBalance variant="bars">` + `<DayMasterBadge>` + 용신 chip + `<LuckTimeline>` strip, then the masked-couple card (composite 55/100, both Day Masters), then the PDF links (sample / essential / deep · basic / deep compat). Keep the "public data, name masked, not affiliated" disclaimers. |
| — | *(Testimonials)* | — | — | `Testimonials` | Stays gated (`TESTIMONIALS_APPROVED === false` → renders null). Slot reserved here. |
| 5 | **What's inside your report** | `inside` | Split / toggle | `WhatIsSaju` + `WhatYouReceive` + ½ `TrustClarity` | An **Essential ⇄ Deep** toggle. Each state shows: a visual table-of-contents (the real report's section list) with the rows that tier unlocks highlighted, plus 3–4 "what you can do with it" points. Delivery note (digital, MP3 for Deep) folded in. |
| 6 | **Pricing** | `pricing` | Centered feature | `PersonalReports` + `CompatibilityReports` + `ComparisonTable` | (a) Personal: 3 cards (Free / Essential $9→$19 / Deep $55) + guarantee line + Companion strip. (b) Compatibility: a visually distinct 2-card group (purple accent) — Snapshot $24 / Deep $45. (c) "Compare every tier" — an expandable styled feature grid (not a raw `<table>`; a responsive definition-list / 2-col-on-mobile grid). |
| 7 | **How it's built** | `how` | Split | `HowItWorks` + `ImportantDetails` + engine/human story | 3 numbered steps with small diagrams: **1** you send birth date/time/place → **2** the engine computes the chart (solar-time correction to your true meridian, classical 60-cycle + hidden-stem + ten-god tables) → **3** a human reads it against 적천수 · 연해자평 · 궁통보감 and writes it in clear English. The "why accurate birth time matters" note lives here, **once**, as a inset caption on step 1. |
| 8 | **The reader** | `reader` | Editorial + watermark | `AboutReader` | Keep the honest bio ("I built the Saju engine Korean apps are built on… not a Korean master"). Add: "I ran my own chart — here's what it got right and what it didn't" (link placeholder → founder's own report when ready). Chips: 적천수·연해자평·궁통보감 / engine-computed, human-interpreted / 7-day guarantee. |
| 9 | **FAQ** | `faq` | Editorial | `FAQ` | Same accordion, grouped under 3 sub-headers: *The reading* · *Ordering & delivery* · *Accuracy & birth data*. |
| 10 | **Final CTA** | — | Full-bleed dark | `FinalCTA` | **One** primary button ("Get your free chart snapshot") + one text link ("or see pricing →"). `star-bg`, elemental rule, big serif line. No tier buttons. |
| — | Forms | `personal-form`, `compat-form` | — | `PersonalReportForm`, `CompatibilityForm` | Unchanged behavior. Visual restyle: match card system, elemental accent on the stepper, tighten spacing. |
| — | Footer / MobileStickyCta / BackToTop / ContactDialog | — | — | same | Footer gets the elemental top rule + a 사주 mark; MobileStickyCta label → canonical primary; otherwise minor. |

**Deleted as standalone sections:** `WhatIsSaju`, `WhatYouReceive`, `TrustClarity`, `ImportantDetails`, `ComparisonTable`. Their component files are removed; their data (`WHAT_IS_SAju_CARDS`, `WHAT_YOU_RECEIVE_CARDS`, `TRUST_CARDS`, `COMPARISON_ROWS`) is either folded into the new sections' local content or kept where still referenced.

---

## 5. Visual system — `src/components/viz/`

All components: server-renderable (no client hooks unless animating; animation via CSS + `IntersectionObserver` already in `page.tsx`), theme-aware (CSS vars, no hard-coded hex), responsive (viewBox + `width:100%`), `role="img"` + `<title>`/`aria-label`, degrade gracefully with `prefers-reduced-motion`.

### 5.1 `src/data/demo-chart.ts` — the RM demo data (real numbers)

```ts
export const DEMO_CHART = {
  name: "Mr. R.M.",           // masked
  born: "12 September 1994 · 13:28 KST · Seoul",
  dayMaster: { stem: "辛", en: "Sin", element: "Metal", polarity: "Yin" },
  strength: "Strong",
  favorable: "Water",
  supporting: "Wood",
  pattern: "비견격 · Companion Grid",
  pillars: [
    { position: "Year",  stem: "甲", branch: "戌", hidden: ["戊","辛","丁"] },
    { position: "Month", stem: "癸", branch: "酉", hidden: ["辛"] },
    { position: "Day",   stem: "辛", branch: "丑", hidden: ["己","癸","辛"] },
    { position: "Hour",  stem: "甲", branch: "午", hidden: ["丁","己"] },
  ],
  elements: { Fire: 9.3, Earth: 20.0, Metal: 26.7, Water: 17.3, Wood: 26.7 },
  luck: [
    { ages: "8–17",  pillar: "甲戌", tenGod: "正財", lean: "mixed" },
    { ages: "18–27", pillar: "乙亥", tenGod: "偏財", lean: "favorable" },
    { ages: "28–37", pillar: "丙子", tenGod: "正官", lean: "favorable", current: true },
    { ages: "38–47", pillar: "丁丑", tenGod: "偏官", lean: "mixed" },
    { ages: "48–57", pillar: "戊寅", tenGod: "正印", lean: "mixed" },
    { ages: "58–67", pillar: "己卯", tenGod: "偏印", lean: "mixed" },
    { ages: "68–77", pillar: "庚辰", tenGod: "劫財", lean: "favorable" },
    { ages: "78–87", pillar: "辛巳", tenGod: "比肩", lean: "favorable" },
  ],
};
// stem/branch → element map (from knowledge/01-stems.md, 02-branches.md) also lives here.
```

Plus `DEMO_COMPAT` (composite 55/100 Mixed, both Day Masters 丙 Yang Fire, day pillars 丙午 / 丙寅) for the couple card.

### 5.2 Components

| Component | Props | Renders | Used in |
|---|---|---|---|
| `<FourPillarsChart pillars variant?>` | `pillars: Pillar[]`, `variant?: "full" \| "compact"` | 4 columns; each: position label, big stem 한자 + small romanization, big branch 한자, hidden-stem chips; each cell background = `color-mix(in srgb, var(--el-X) 14%, transparent)`, border `var(--el-X) 40%`. `full` shows hidden stems + labels; `compact` is just the 8 glyphs. Draw-in animation on first reveal. | Hero (full), Demo (full), Why (compact) |
| `<ElementBalance data variant total?>` | `data: Record<Element,number>`, `variant: "bars" \| "wheel"` | `bars`: 5 horizontal rows, label + 한자 + bar (width %, fill `var(--el-X)`) + %. `wheel`: a 5-segment radial/donut, segment angle ∝ %, segment fill `var(--el-X)`, center shows the dominant element. | Hero (wheel), Demo (bars), Why (bars), Inside (bars) |
| `<LuckTimeline periods currentIndex?>` | `periods: LuckPeriod[]` | Horizontal ribbon of 8 segments; width equal; fill by `lean` (`--lean-*`); each segment labelled with age range; the `current` segment gets a gold "you are here" caret + ring. Scrolls horizontally on mobile inside `overflow-x:auto`. | Demo |
| `<DayMasterBadge stem en element polarity>` | | A pill: large 한자 in `var(--el-X)`, "Sin · Yin Metal" beside it, subtle `var(--el-X)` ring. | Demo, Hero (small) |
| `<TenGodDot>` / small helpers | | tiny labelled chips for 용신 / 희신 / pattern | Demo, Hero |
| `<SectionHeading eyebrow title intro? align?>` | | eyebrow (gold caps) + serif `<h2>` + optional intro `<p>`; `align: "center" \| "start"` | every section |
| `<ElementalRule />` | | the 1px `wood→water` gradient `<div>` | dividers, card tops, footer |
| `<KoreanWatermark char? />` | | absolutely-positioned low-opacity `四柱` | hero, reader |

### 5.3 Element token helper

`src/lib/elements.ts` — `elementColorVar(e: Element): string` → `"var(--el-wood)"` etc.; `stemElement(han: string)` / `branchElement(han: string)` maps (source: `knowledge/01-stems.md`, `02-branches.md`); `ELEMENT_ORDER = ["Wood","Fire","Earth","Metal","Water"]`.

---

## 6. Component/file plan

### New

```
src/components/viz/FourPillarsChart.tsx
src/components/viz/ElementBalance.tsx
src/components/viz/LuckTimeline.tsx
src/components/viz/DayMasterBadge.tsx
src/components/viz/SectionHeading.tsx
src/components/viz/ElementalRule.tsx
src/components/viz/KoreanWatermark.tsx
src/components/viz/index.ts
src/lib/elements.ts
src/data/demo-chart.ts
src/sections/WhySaju.tsx           (new #3)
src/sections/WhatsInside.tsx       (new #5 — replaces WhatYouReceive + WhatIsSaju)
src/sections/Pricing.tsx           (new #6 — wraps PersonalReports + CompatibilityReports + a CompareTiers subcomponent)
src/sections/HowItsBuilt.tsx       (new #7 — replaces HowItWorks + ImportantDetails)
src/sections/CompareTiers.tsx      (the styled feature grid; replaces ComparisonTable)
```

### Modified

```
src/app/globals.css                 elemental tokens, .el-rule, watermark utility, motion tweaks, staggered reveal
src/app/page.tsx                     new import set + <main> order; remove deleted sections
src/sections/Header.tsx              nav labels, single CTA, canonical label
src/sections/Hero.tsx                split layout, viz, watermark, trust row, badge copy
src/sections/DemoReports.tsx         rebuilt around viz components (keep content + disclaimers)
src/sections/AboutReader.tsx         editorial layout, watermark, "my own chart" hook, chip copy
src/sections/FAQ.tsx                 grouped sub-headers
src/sections/FinalCTA.tsx            one primary + one link
src/sections/Footer.tsx             elemental rule, 사주 mark
src/sections/MobileStickyCta.tsx    canonical primary label
src/sections/PersonalReports.tsx    becomes a child of <Pricing>; keep card logic, restyle
src/sections/CompatibilityReports.tsx  becomes a child of <Pricing>; restyle
src/sections/PersonalReportForm.tsx / CompatibilityForm.tsx  visual restyle only (elemental stepper, spacing)
src/data/landing-data.ts            keep PERSONAL_REPORTS / COMPAT_REPORTS / FAQS (regrouped) / SUBSCRIPTION-ish; the *_CARDS arrays for deleted sections either removed or repurposed into the new sections
```

### Deleted

```
src/sections/WhatIsSaju.tsx
src/sections/WhatYouReceive.tsx
src/sections/TrustClarity.tsx
src/sections/ImportantDetails.tsx
src/sections/ComparisonTable.tsx
```

Any tests referencing deleted component names / `COMPARISON_ROWS` / stale copy → update or remove.

---

## 7. Copy changes (canonical strings)

- **Primary CTA (everywhere):** "Get your free chart snapshot"
- **Secondary:** "See what's inside" / "Compare tiers" / "See a real reading"
- **Hero headline:** replace "Discover Your Cosmic Blueprint Through Korean Saju" with something concrete, e.g. *"Your Korean Saju chart, read the way a person would — not a horoscope."* (final wording in the plan)
- **Hero badge:** "Every reading is hand-checked before it's sent" (replaces the 15-slots scarcity)
- **Eyebrows:** Hero "Korean Saju · 四柱" · Why "Why it's different" · Demo "See a real reading" · Inside "What you get" · Pricing "Choose your reading" · How "How it's built" · Reader "Who reads your chart" · FAQ "Questions"
- Keep all honest-positioning language from the 2026-09-07 pivot (not a Korean master, classical texts cited, for reflection/entertainment).

---

## 8. Testing & acceptance

- `cd apps/landing-page && npm run build` — zero errors.
- `npm run lint` — zero warnings (`--max-warnings=0`).
- `npm test` — the 107 vitest pass (update the handful asserting deleted copy / `COMPARISON_ROWS`; don't weaken assertions).
- Manual: headless-Chrome screenshot pass — **desktop + mobile, light + dark** — for every section. No horizontal body scroll. Wide viz (LuckTimeline, CompareTiers) scroll inside their own container.
- Hydration: 0 warnings in a clean browser (the `suppressHydrationWarning` fixes from the prior task stay).
- `prefers-reduced-motion: reduce` — no transforms/animation; content fully visible.
- Lighthouse (mobile) ≥ the pre-redesign score; no CLS regression from the hero viz (reserve its aspect-ratio box).
- All existing anchors still resolve (`#reports`→`#pricing` etc. — add redirECTS or update nav + `scrollToForm` targets).

## 9. Build order (for the plan)

1. Tokens + `src/lib/elements.ts` + `src/data/demo-chart.ts` + `globals.css` motifs.
2. Viz primitives: `SectionHeading`, `ElementalRule`, `KoreanWatermark`, `DayMasterBadge`.
3. Viz charts: `FourPillarsChart`, `ElementBalance`, `LuckTimeline` — each with a tiny render test.
4. `Hero` rebuild (proves the viz + split shape + watermark + motion).
5. `DemoReports` rebuild (proves the viz in a data card + LuckTimeline mobile scroll).
6. `WhySaju` (new).
7. `WhatsInside` (new; delete `WhatIsSaju` + `WhatYouReceive`).
8. `Pricing` + `CompareTiers` (wrap `PersonalReports`/`CompatibilityReports`; delete `ComparisonTable`).
9. `HowItsBuilt` (new; delete `HowItWorks` + `ImportantDetails`; absorb `TrustClarity` residue into Hero trust row / Reader chips, then delete).
10. `AboutReader`, `FAQ`, `FinalCTA`, `Footer`, `MobileStickyCta` restyle.
11. Form restyle.
12. `page.tsx` reorder + import cleanup + anchor/`scrollToForm` fixes; delete dead files; fix tests.
13. Full screenshot + Lighthouse + build/lint/test pass.

## 10. Risks / open questions

- **R1.** `FourPillarsChart` needs a stem/branch→element map. Source it from `knowledge/01-stems.md` / `02-branches.md` and hard-code in `src/lib/elements.ts` (10 stems + 12 branches — small, stable).
- **R2.** The hero viz must not cause CLS — wrap in a fixed `aspect-ratio` box; SSR the SVG (no post-mount layout shift).
- **R3.** `CompareTiers` on mobile — a matrix is hard. Use a per-tier stacked list on `< sm`, a grid on `≥ sm`; never a horizontally-scrolling `<table>` as the only form.
- **R4.** Anchor churn — `#reports` is used by nav, `MobileStickyCta`, and `scrollToForm`. Renaming to `#pricing` means updating every reference; the plan must enumerate them.
- **Q1.** Hero headline final wording — propose 2–3 in the plan, pick one.
- **Q2.** Keep the "15 slots" idea anywhere (e.g. a true "limited weekly capacity" line on pricing) or drop entirely? *Proposed: drop; if real capacity limits exist later, add then.*
- **Q3.** `ContactDialog` + the "Meet the Reader" — leave contact in the footer only, or add a soft "questions? contact" near FAQ? *Proposed: footer only for now.*
