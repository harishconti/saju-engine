# Cosmic Saju Landing Page Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (or subagent-driven-development). Steps use `- [ ]` checkboxes. Consult `frontend-design` skill guidance while building sections.

**Goal:** Restructure `apps/landing-page` from ~15 monotonous card-grid sections into ~9 with a proof-first narrative, and add a reusable, theme-aware Saju visual system — premium-editorial aesthetic.

**Architecture:** New `src/components/viz/` SVG components (theme-var-driven, responsive, motion-safe) fed by a static `src/data/demo-chart.ts` (RM's real chart numbers). New/merged sections consume them. Old redundant sections are deleted. `page.tsx` reorders `<main>`. No backend/form-contract/security changes.

**Tech Stack:** Next.js 16, React 19, Tailwind v4 (CSS-var tokens in `globals.css`), shadcn/ui, next-themes, lucide-react. Tests: vitest (`node` project for `src/lib/**/*.test.ts`, `browser` project = happy-dom + `@testing-library/react` + `vitest-axe` for `src/**/*.test.tsx`).

**Spec:** `docs/superpowers/specs/2026-09-07-landing-page-redesign-design.md` — read it; this plan implements it.

## Global Constraints

- **Aesthetic:** premium-editorial. Diagrams/data over ornament. Dark cosmic ground `#08080f`, gold `#C9A84C`, purple `#7B5EA7` accent, Cormorant Garamond display / Inter body — all already in `globals.css`.
- **Theme:** every new color goes through a CSS var (`var(--el-fire)` etc.). Never hard-code hex in a component. Must work in `:root` (dark) and `.light`.
- **Motion:** all animation behind `@media (prefers-reduced-motion: no-preference)`. Content fully visible/usable with motion off.
- **Responsive:** relative units; wide content (`LuckTimeline`, `CompareTiers`) scrolls inside its own `overflow-x:auto`; **body never scrolls horizontally**.
- **A11y:** every viz component `role="img"` + `<title>` / `aria-label`; `KoreanWatermark` `aria-hidden`; new `.test.tsx` files assert `await axe(container)` → `toHaveNoViolations()`.
- **Canonical primary CTA label everywhere:** `Get your free chart snapshot`. Two button styles only (gold solid / gold outline) + one text link. Purple outline reserved for compatibility CTAs.
- **Do not touch:** `src/app/api/*`, `src/lib/submit-handlers.ts`, `src/lib/validate.ts`, `src/lib/rate-limit.ts`, `src/proxy.ts`, the intake form field set / submission contract, `TESTIMONIALS_APPROVED` gate.
- **Green gates each task:** `npm run build` (0 errors), `npm run lint` (`--max-warnings=0`), `npm test`. Section tasks also: headless screenshot desktop+mobile, dark+light.
- **Git:** `apps/landing-page` has its own repo with a large pre-existing uncommitted staged set. Work on top; commit only if the user asks. Don't `git add -A`.
- **Elemental tokens = 오방색** (see spec §3.5; add to `globals.css`, do not rename existing):
  dark `--el-wood:#3FB68A` `--el-fire:#E24C36` `--el-earth:#E0A94C` `--el-metal:#C7CBD1` `--el-water:#4B79C4`;
  `.light` `#1F9068 #C13B27 #B5832F #6B7280 #3B63A8`;
  `--lean-favorable:var(--el-wood)` `--lean-mixed:var(--el-earth)` `--lean-challenging:var(--el-fire)`;
  `--seal:var(--el-fire)`.
- **Element order:** `["Wood","Fire","Earth","Metal","Water"]`.
- **Third font (NEW):** add `IBM_Plex_Mono` via `next/font/google` in `src/app/layout.tsx` as
  `--font-mono` (weights 400,500). Use for eyebrow labels, romanizations, ages, %, pillar labels.
- **Signature:** four pillars as vertical almanac columns + a recurring `<SealMark>` (cinnabar square
  with `人`, "hand-checked"). Pillars "stamp in" one column at a time on first reveal.

---

### Task 1: Elemental tokens, motifs, and `src/lib/elements.ts`

**Files:**
- Modify: `src/app/globals.css`
- Create: `src/lib/elements.ts`
- Test: `src/lib/elements.test.ts`

**Interfaces — Produces:**
```ts
// src/lib/elements.ts
export type Element = "Wood" | "Fire" | "Earth" | "Metal" | "Water";
export const ELEMENT_ORDER: Element[];
export const ELEMENT_HANJA: Record<Element, string>;      // 木 火 土 金 水
export function elementVar(e: Element): string;            // "var(--el-wood)"
export function stemElement(han: string): Element | null;  // 甲→Wood ... 癸→Water (10 stems)
export function branchElement(han: string): Element | null;// 子→Water ... 亥→Water (12 branches)
export type Lean = "favorable" | "mixed" | "challenging";
export function leanVar(l: Lean): string;                  // "var(--lean-favorable)"
```
Stem map (knowledge/01-stems.md): 甲乙→Wood 丙丁→Fire 戊己→Earth 庚辛→Metal 壬癸→Water.
Branch map (knowledge/02-branches.md): 寅卯→Wood 巳午→Fire 辰戌丑未→Earth 申酉→Metal 亥子→Water.

- [ ] **Step 1: Write `src/lib/elements.test.ts`** (node project):

```ts
import { describe, it, expect } from "vitest";
import { ELEMENT_ORDER, ELEMENT_HANJA, elementVar, stemElement, branchElement, leanVar } from "./elements";

describe("elements", () => {
  it("has 5 elements in canonical order", () => {
    expect(ELEMENT_ORDER).toEqual(["Wood","Fire","Earth","Metal","Water"]);
  });
  it("maps hanja", () => {
    expect(ELEMENT_HANJA.Water).toBe("水");
  });
  it("elementVar → css var", () => {
    expect(elementVar("Fire")).toBe("var(--el-fire)");
  });
  it("stemElement covers all 10 stems", () => {
    for (const [s, e] of [["甲","Wood"],["丁","Fire"],["己","Earth"],["庚","Metal"],["癸","Water"]] as const)
      expect(stemElement(s)).toBe(e);
    expect(stemElement("x")).toBeNull();
  });
  it("branchElement covers key branches", () => {
    for (const [b, e] of [["寅","Wood"],["午","Fire"],["丑","Earth"],["酉","Metal"],["子","Water"]] as const)
      expect(branchElement(b)).toBe(e);
  });
  it("leanVar", () => {
    expect(leanVar("challenging")).toBe("var(--lean-challenging)");
  });
});
```

- [ ] **Step 2: Run — expect FAIL** `npx vitest run src/lib/elements.test.ts` → module not found.
- [ ] **Step 3: Implement `src/lib/elements.ts`** per the interface + maps above.
- [ ] **Step 4:** Add to `src/app/globals.css`:
  - the `--el-*` and `--lean-*` vars under `:root` and `.light` (values in Global Constraints).
  - `.el-rule { height:1px; background:linear-gradient(90deg,var(--el-wood),var(--el-fire),var(--el-earth),var(--el-metal),var(--el-water)); opacity:.6; }`
  - `.kr-watermark { position:absolute; font-family:var(--font-display),Georgia,serif; opacity:.04; pointer-events:none; user-select:none; line-height:1; }` (`.light` → `opacity:.05`)
  - `.eyebrow { font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:var(--color-gold); font-weight:600; }`
  - staggered reveal: `[data-reveal] > * { opacity:0; transform:translateY(12px); }` + `.reveal-visible > * { opacity:1; transform:none; transition:opacity .5s ease-out, transform .5s ease-out; }` with `:nth-child(n)` delays 0/60/120/180ms; wrap the whole reveal block in `@media (prefers-reduced-motion:no-preference)` and add a `@media (prefers-reduced-motion:reduce){ [data-reveal],[data-reveal]>*{opacity:1!important;transform:none!important} }` reset. **Keep the existing `[data-reveal]` opacity rule working** — adjust, don't break `page.tsx`'s observer that adds `.reveal-visible`.
- [ ] **Step 5: Run** `npx vitest run src/lib/elements.test.ts` → PASS. Then `npm run build` → 0 errors.

---

### Task 2: `src/data/demo-chart.ts`

**Files:**
- Create: `src/data/demo-chart.ts`
- Test: `src/data/demo-chart.test.ts`

**Interfaces — Produces:** `DEMO_CHART`, `DEMO_COMPAT` (shapes in spec §5.1). All values are RM's real numbers (verified from `candidates_horoscope/reports/rm/rm-report.md`):
pillars 甲戌 / 癸酉 / 辛丑 / 甲午; hidden stems Year[戊,辛,丁] Month[辛] Day[己,癸,辛] Hour[丁,己];
Day Master 辛 Sin Yin Metal, Strong, favorable Water, supporting Wood, pattern 비견격;
elements Fire 9.3 / Earth 20.0 / Metal 26.7 / Water 17.3 / Wood 26.7;
luck (8 periods) 8–17 甲戌 正財 mixed · 18–27 乙亥 偏財 favorable · 28–37 丙子 正官 favorable *(current)* · 38–47 丁丑 偏官 mixed · 48–57 戊寅 正印 mixed · 58–67 己卯 偏印 mixed · 68–77 庚辰 劫財 favorable · 78–87 辛巳 比肩 favorable.
`DEMO_COMPAT`: composite 55, band "Mixed", partners A/B both Day Master 丙 Yang Fire, day pillars 丙午 / 丙寅.

- [ ] **Step 1: Write `src/data/demo-chart.test.ts`:** assert `DEMO_CHART.pillars.length === 4`, `Object.values(DEMO_CHART.elements).reduce((a,b)=>a+b) ` ≈ 100 (±0.5), `DEMO_CHART.luck.length === 8`, exactly one `luck[i].current === true`, `DEMO_COMPAT.composite === 55`.
- [ ] **Step 2: Run — FAIL.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run — PASS** + `npm run build`.

---

### Task 3: Primitive viz — `SectionHeading`, `ElementalRule`, `KoreanWatermark`, `DayMasterBadge`, `SealMark`

**Files:**
- Create: `src/components/viz/SectionHeading.tsx`, `ElementalRule.tsx`, `KoreanWatermark.tsx`, `DayMasterBadge.tsx`, `SealMark.tsx`, `index.ts`
- Modify: `src/app/layout.tsx` (add `IBM_Plex_Mono` → `--font-mono`)
- Test: `src/components/viz/primitives.test.tsx`

**Interfaces — Produces:**
```tsx
<SectionHeading eyebrow="Why it's different" title="…" intro?="…" align?="center"|"start" as?="h2" />
<ElementalRule className?="" />                       // <div className="el-rule" aria-hidden />
<KoreanWatermark char?="四柱" className="…position…" />  // aria-hidden absolutely-positioned span
<DayMasterBadge stem="辛" en="Sin" element="Metal" polarity="Yin" size?="sm"|"md" />
<SealMark label?="hand-checked" className?="" />      // cinnabar 1px square w/ 人 + mono caption
```
Eyebrow text uses `font-mono`. `SealMark` square border `var(--seal)`, glyph `人` in `var(--seal)`, caption in `font-mono` `text-cosmic-muted`.

- [ ] **Step 1: Write `primitives.test.tsx`** (browser project). For each: render, assert key text present, `expect(await axe(container)).toHaveNoViolations()`. E.g.:
```tsx
import { render } from "@testing-library/react";
import { axe } from "@/../src/test-setup";
import { SectionHeading, DayMasterBadge, KoreanWatermark } from "./index";

it("SectionHeading shows eyebrow + title", async () => {
  const { getByText, container } = render(<SectionHeading eyebrow="Why" title="Higher resolution" />);
  getByText("Why"); getByText("Higher resolution");
  expect(await axe(container)).toHaveNoViolations();
});
it("DayMasterBadge shows the stem + element", async () => {
  const { getByText, container } = render(<DayMasterBadge stem="辛" en="Sin" element="Metal" polarity="Yin" />);
  getByText("辛"); getByText(/Yin Metal/);
  expect(await axe(container)).toHaveNoViolations();
});
it("KoreanWatermark is aria-hidden", () => {
  const { container } = render(<KoreanWatermark />);
  expect(container.firstChild).toHaveAttribute("aria-hidden", "true");
});
```
- [ ] **Step 2: Run — FAIL.**
- [ ] **Step 3: Implement.**
  - `SectionHeading`: `<div>` → optional `<p className="eyebrow">`, `<h2 style={{fontFamily:"var(--font-display),Georgia,serif"}} className="gold-text text-3xl sm:text-4xl font-bold">`, optional intro `<p className="text-cosmic-muted …">`. `align` controls `text-center` vs `text-left` + `mx-auto`.
  - `DayMasterBadge`: pill — big 한자 in `style={{color:elementVar(element)}}`, "{en} · {polarity} {element}" beside, ring `style={{boxShadow:\`0 0 0 1px color-mix(in srgb, ${elementVar(element)} 45%, transparent)\`}}`.
  - `ElementalRule`: `<div role="presentation" aria-hidden className={cn("el-rule", className)} />`.
  - `KoreanWatermark`: `<span aria-hidden className={cn("kr-watermark", className)} style={{fontSize:"14rem"}}>{char}</span>`.
- [ ] **Step 4: Run — PASS** + `npm run build` + `npm run lint`.

---

### Task 4: `FourPillarsChart`

**Files:**
- Create: `src/components/viz/FourPillarsChart.tsx`
- Test: `src/components/viz/FourPillarsChart.test.tsx`

**Interfaces — Produces:**
```tsx
type Pillar = { position: "Year"|"Month"|"Day"|"Hour"; stem: string; branch: string; hidden: string[] };
<FourPillarsChart pillars={Pillar[]} variant?="full"|"compact" className?="" />
```
`full`: 4 columns; each column = position label (top), stem cell (한자 + small `stemElement` name), branch cell (한자), hidden-stem chips row. Cell bg `color-mix(in srgb, {elementVar} 14%, transparent)`, border `color-mix(… 40% …)`. `compact`: just the 8 glyphs in a 4×2 grid, no labels/hidden.
SVG-or-div: **use a CSS grid of divs** (simpler for 한자 text + responsive) wrapped in a `role="img"` container with `aria-label` summarising the four pillars. Draw-in animation: `@media (prefers-reduced-motion:no-preference)` fade+rise per column staggered — reuse the `[data-reveal]` stagger by giving the container `data-reveal` OR a scoped keyframe.

- [ ] **Step 1: Write test:** render `variant="full"` with `DEMO_CHART.pillars`; assert all 8 glyphs present (`甲 戌 癸 酉 辛 丑 甲 午`), the 4 position labels present, container has `role="img"` + non-empty `aria-label`; `toHaveNoViolations`. Render `variant="compact"`; assert labels absent, glyphs present.
- [ ] **Step 2: Run — FAIL.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run — PASS** + build + lint.

---

### Task 5: `ElementBalance` (bars + wheel)

**Files:**
- Create: `src/components/viz/ElementBalance.tsx`
- Test: `src/components/viz/ElementBalance.test.tsx`

**Interfaces — Produces:**
```tsx
<ElementBalance data={Record<Element, number>} variant="bars"|"wheel" className?="" />
```
`bars`: 5 rows in `ELEMENT_ORDER`; each = `{Element} {hanja}` label, track + fill `<div style={{width:`${pct}%`, background:elementVar(e)}}>` with a width transition on reveal, `{pct.toFixed(1)}%`.
`wheel`: an SVG donut — 5 arcs, sweep ∝ pct, `fill/stroke = elementVar(e)`; center text = dominant element name + %. `viewBox="0 0 120 120"`, `width:100%`, `role="img"` + aria-label.

- [ ] **Step 1: Write test:** `bars` with `DEMO_CHART.elements` → all 5 element names + "26.7%" (×2) present, 5 fill elements; `wheel` → `role="img"`, aria-label mentions "Metal" or "Wood" (dominant), `toHaveNoViolations` for both.
- [ ] **Step 2: FAIL → Step 3: implement → Step 4: PASS** + build + lint.

---

### Task 6: `LuckTimeline`

**Files:**
- Create: `src/components/viz/LuckTimeline.tsx`
- Test: `src/components/viz/LuckTimeline.test.tsx`

**Interfaces — Produces:**
```tsx
type LuckPeriod = { ages: string; pillar: string; tenGod: string; lean: "favorable"|"mixed"|"challenging"; current?: boolean };
<LuckTimeline periods={LuckPeriod[]} className?="" />
```
Horizontal flex of equal-width segments; each: age range label, thin bar `background:leanVar(lean)`, pillar 한자 small; `current` segment → gold ring + a "you are here" caret above. Outer wrapper `overflow-x-auto` with `min-width` so it scrolls on mobile. `role="img"` + aria-label ("8 ten-year periods; currently ages 28–37, favorable").

- [ ] **Step 1: Write test:** render `DEMO_CHART.luck` → 8 age-range labels present, exactly one element with the "you are here" marker (query by text/aria), wrapper has `overflow-x-auto` class, `toHaveNoViolations`.
- [ ] **Step 2: FAIL → 3: implement → 4: PASS** + build + lint.

---

### Task 7: Hero rebuild

**Files:**
- Modify: `src/sections/Hero.tsx`
- (No new test file; covered by build + screenshot. Optional: `Hero.test.tsx` asserting the canonical CTA label + headline render.)

- [ ] **Step 1:** Rebuild `Hero` as a **2-col split** (`lg:grid-cols-2`, stacks on mobile), inside the existing `star-bg` section, with a `<KoreanWatermark char="四柱" className="top-0 right-0 -z-0" />`:
  - **Left:** `<p className="eyebrow">Korean Saju · 四柱</p>` → serif `<h1>` (headline — pick from Task 12 Q1; default *"Your Korean Saju chart, read the way a person would — not a horoscope."*) → 1-sentence subhead → button row: primary `Get your free chart snapshot` (`scrollToForm("free")`) + text link `See a real reading ↓` (`href="#demo"`) → a 3-item trust row (7-day guarantee · 24-hour delivery · classical texts cited) with small lucide icons.
  - **Right:** an `aspect-[4/5]` (or fixed-height) box containing `<FourPillarsChart pillars={DEMO_CHART.pillars} variant="full" />` and, below/overlaid small, `<ElementBalance data={DEMO_CHART.elements} variant="wheel" />` + a caption "A real reading — Mr. R.M. (details masked)".
  - Replace the `Only 15 reports processed per week` badge with `Every reading is hand-checked before it's sent`.
  - Add `<ElementalRule className="max-w-4xl mx-auto mt-16" />` at the section's foot.
- [ ] **Step 2:** `npm run build` + `npm run lint` + `npm test`.
- [ ] **Step 3:** Screenshot desktop+mobile / dark+light (script in Task 13). Verify: no CLS (the right box reserves its size), no horizontal scroll, headline + CTA legible, chart renders with element colors.

---

### Task 8: `DemoReports` rebuild → section `#demo`

**Files:**
- Modify: `src/sections/DemoReports.tsx`

- [ ] **Step 1:** Add `id="demo"` to the section. Replace the two plain "Chart snapshot / Match snapshot" `<div>` blocks with viz:
  - **Personal card:** `<SectionHeading eyebrow="See a real reading" title="…" align="start" />` (or keep the h3), then `<DayMasterBadge …>` + a 용신 chip ("Favorable element · Water") + pattern chip, `<FourPillarsChart variant="full" pillars={DEMO_CHART.pillars} />`, `<ElementBalance variant="bars" data={DEMO_CHART.elements} />`, `<LuckTimeline periods={DEMO_CHART.luck} />`, then the existing PDF-link buttons (sample / essential / deep). Keep the "public data, name masked, not affiliated" disclaimer.
  - **Couple card:** `DEMO_COMPAT` — composite `55 / 100 — Mixed` as a prominent number, both `<DayMasterBadge>` (丙 Yang Fire ×2), day pillars, then the compat PDF buttons + consent disclaimer.
- [ ] **Step 2:** build + lint + test.
- [ ] **Step 3:** Screenshot. Verify `LuckTimeline` scrolls horizontally on mobile inside its own container (body does not).

---

### Task 9: New section `WhySaju` (`#why`)

**Files:**
- Create: `src/sections/WhySaju.tsx`
- Modify: `src/data/landing-data.ts` (repurpose/remove `WHAT_IS_SAju_CARDS`)

- [ ] **Step 1:** `<section id="why">` — **split**: left = `<SectionHeading eyebrow="Why it's different" title="Higher resolution than a sun sign" align="start" />` + 3 short points (8 characters vs 1 sign · a deterministic calculation — the value is in a careful reading · not a horoscope: timing and direction you can act on). Right = a comparison visual: a large lone "♌" glyph (muted) beside `<FourPillarsChart variant="compact" pillars={DEMO_CHART.pillars} />`, or `<ElementBalance variant="bars">` captioned "your mix — not one label". Foot: `<ElementalRule />`.
- [ ] **Step 2:** build + lint + test. **Step 3:** screenshot.

---

### Task 10: New section `WhatsInside` (`#inside`) — deletes `WhatIsSaju` + `WhatYouReceive`

**Files:**
- Create: `src/sections/WhatsInside.tsx`
- Delete: `src/sections/WhatIsSaju.tsx`, `src/sections/WhatYouReceive.tsx`
- Modify: `src/data/landing-data.ts` (`WHAT_YOU_RECEIVE_CARDS` → fold copy into the new section or a `REPORT_CONTENTS` const), `src/app/page.tsx` (imports)

- [ ] **Step 1:** `<section id="inside">` with an **Essential ⇄ Deep toggle** (`useState`, 2 pills). For the active tier, render a visual table-of-contents: the real report section list (from spec — Chart at a Glance / Day Master Portrait / Career & Wealth / Relationships / Health / Timing / Practical Guidance / Closing Note (+ Deep-only: Natal Pattern Analysis, year-by-year windows, Business & Launch, MP3)), with the rows the active tier unlocks in gold/opaque and the locked rows muted with a small lock icon. Beside it: 3 "what you can do with it" lines + the delivery note (digital; MP3 for Deep).
- [ ] **Step 2:** build + lint + test (**update/remove** any vitest asserting `WHAT_IS_SAju_CARDS` / `WHAT_YOU_RECEIVE_CARDS` / deleted-section copy). **Step 3:** screenshot both toggle states.

---

### Task 11: `Pricing` (`#pricing`) + `CompareTiers` — deletes `ComparisonTable`, wraps `PersonalReports`/`CompatibilityReports`

**Files:**
- Create: `src/sections/Pricing.tsx`, `src/sections/CompareTiers.tsx`
- Delete: `src/sections/ComparisonTable.tsx`
- Modify: `src/sections/PersonalReports.tsx`, `src/sections/CompatibilityReports.tsx` (strip their outer `<section>` + heading; export the inner grid as used by `<Pricing>`), `src/data/landing-data.ts` (`COMPARISON_ROWS` stays, consumed by `CompareTiers`), `src/app/page.tsx`

- [ ] **Step 1:** `<Pricing>` = `<section id="pricing">` → `<SectionHeading eyebrow="Choose your reading" title="Pricing" />` → `<PersonalReportsGrid>` (3 cards + guarantee line + Companion strip, unchanged logic) → a visually distinct **Compatibility** block (purple accent, own sub-heading) `<CompatibilityGrid>` → `<CompareTiers>` (collapsible: a `<details>` or a toggle "Compare every tier").
- [ ] **Step 2:** `<CompareTiers>` renders `COMPARISON_ROWS` as: on `< sm` a per-tier stacked list; on `≥ sm` a CSS-grid matrix (header row = tier names, cells = ✓ / value / —), the whole thing inside `overflow-x-auto`. **Not** a bare `<table>` as the only layout. Gold check icons, elemental-rule top border on the popular column.
- [ ] **Step 3:** Update `#reports` → `#pricing` everywhere: `Header.tsx` nav, `Hero.tsx` link, `MobileStickyCta.tsx`, `FinalCTA.tsx`, any `href="#reports"`. Grep `grep -rn '#reports' src/`.
- [ ] **Step 4:** build + lint + test (update `COMPARISON_ROWS` label assertions if any). **Step 5:** screenshot; verify the compare matrix scrolls in its own container on mobile.

---

### Task 12: `HowItsBuilt` (`#how`) + restyle `AboutReader` / `FAQ` / `FinalCTA` / `Footer` / `MobileStickyCta` — deletes `HowItWorks` + `ImportantDetails` + `TrustClarity`

**Files:**
- Create: `src/sections/HowItsBuilt.tsx`
- Delete: `src/sections/HowItWorks.tsx`, `src/sections/ImportantDetails.tsx`, `src/sections/TrustClarity.tsx`
- Modify: `AboutReader.tsx`, `FAQ.tsx`, `FinalCTA.tsx`, `Footer.tsx`, `MobileStickyCta.tsx`, `src/data/landing-data.ts` (`TRUST_CARDS` removed; `STEPS` → repurposed; `FAQS` regrouped), `src/app/page.tsx`

- [ ] **Step 1: `HowItsBuilt`** — `<section id="how">` split: `<SectionHeading eyebrow="How it's built" title="An engine, then a person" />` + 3 numbered steps with small inline diagrams (birth data icon → a mini chart-grid → a book/quill). Step 1 caption = the "accurate birth time matters" note (once). Step 3 names 적천수 · 연해자평 · 궁통보감.
- [ ] **Step 2: `AboutReader`** — editorial layout (text-forward, one inset), `<KoreanWatermark char="사주" />`, keep the honest bio, add the "I ran my own chart — what it got right and wrong" line (link `#` placeholder), chips: 적천수·연해자평·궁통보감 / engine-computed, human-interpreted / 7-day guarantee.
- [ ] **Step 3: `FAQ`** — wrap the accordion items in 3 groups with small `<h3>` sub-headers: *The reading* / *Ordering & delivery* / *Accuracy & birth data*. Regroup `FAQS` in `landing-data.ts` (add a `group` field or split into 3 arrays).
- [ ] **Step 4: `FinalCTA`** — one primary button `Get your free chart snapshot` + one text link `or see pricing →` (`#pricing`). Full-bleed `star-bg`, `<ElementalRule>`, big serif line. Delete the 5-button grid.
- [ ] **Step 5: `Footer`** — add `<ElementalRule>` as the top border, a low-opacity `사주` mark. **`MobileStickyCta`** — primary label → canonical.
- [ ] **Step 6:** Fold the residual `TrustClarity` value props into the Hero trust row + AboutReader chips, then delete the file + `TRUST_CARDS`.
- [ ] **Step 7:** build + lint + test (update tests referencing deleted components/data). **Step 8:** screenshot each.

---

### Task 13: `page.tsx` reorder, cleanup, and full verification

**Files:**
- Modify: `src/app/page.tsx`
- Create: (scratch) screenshot script

- [ ] **Step 1:** Rewrite the `<main>` block to the spec §4 order:
  `<Hero/> <WhySaju/> <DemoReports/> <Testimonials/> <WhatsInside/> <Pricing/> <PersonalReportForm/> <CompatibilityForm/> <HowItsBuilt/> <AboutReader/> <FAQ/> <FinalCTA/>`
  (forms stay near pricing as scroll targets). Remove imports for deleted sections. Update `Header` nav items to `#why #demo #pricing #how #faq`.
- [ ] **Step 2:** `grep -rn '#reports\|WhatIsSaju\|WhatYouReceive\|TrustClarity\|ImportantDetails\|ComparisonTable\|HowItWorks' src/` → only intentional hits (none in code).
- [ ] **Step 3:** `npm run build` (0 errors) · `npm run lint` (0 warnings) · `npm test` (all pass — fix/remove the handful of tests asserting deleted copy).
- [ ] **Step 4:** Screenshot script (`/tmp/ss-redesign.py`, python playwright + `channel="chrome"`): for `[desktop 1440, mobile 390] × [dark, light]`, load `http://localhost:4400`, force `[data-reveal]` visible, screenshot each section by `id`, plus one full-page each. Save to scratchpad. **Read every screenshot.** Check per spec §8: distinct section shapes, no horizontal body scroll, wide viz scroll in-container, legible in both themes, chart colors correct.
- [ ] **Step 5:** `prefers-reduced-motion` check — launch chrome with `--force-prefers-reduced-motion`, confirm content fully visible, no transforms.
- [ ] **Step 6:** Hydration check — headless load + console listener → 0 errors (reuse the Task from the prior session).
- [ ] **Step 7:** Lighthouse (mobile) via `npx lighthouse http://localhost:4400 --only-categories=performance,accessibility --preset=perf` or the chrome-devtools MCP — record score, compare to the pre-redesign `apps/landing-page/lighthouse-reports/report.json`. No CLS regression.
- [ ] **Step 8:** Update `improvements_issues.md` §5a status → done; `tasks.md`; `apps/landing-page/worklog.md` stage summary; project memory.

## Self-Review

**Spec coverage:** §3 tokens/motifs → T1; §5.1 data → T2; §5.2 components → T3–T6; §4 sections → T7–T12; §6 file plan → T1–T13 (creates/modifies/deletes enumerated per task); §7 copy → T7/T11/T12; §8 acceptance → T13; §9 build order → task order matches. ✅

**Placeholder scan:** Hero headline is Q1 — flagged in T7 with a concrete default and "pick in T12/Q1"; resolve at T7 (use the default unless the user weighs in). `AboutReader` "my own chart" link is `#` until the founder's report exists — intentional, noted. No "TODO/TBD" left as work. ✅

**Type consistency:** `Element` / `Lean` / `Pillar` / `LuckPeriod` defined once (T1, T2) and reused verbatim in T4–T6/T8. `elementVar`/`leanVar` return `var(--el-*)` strings used in `style={{}}` throughout. Canonical CTA label identical in T7/T11/T12. ✅

**Open decisions to make at execution (don't block):** Q1 hero headline (default given); Q2 drop the "15 slots" idea (spec §10 → drop); Q3 contact stays footer-only.
