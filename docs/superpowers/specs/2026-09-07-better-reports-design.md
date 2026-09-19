# Better Reports — Design

**Status:** APPROVED (design) — not yet planned or implemented
**Date:** 2026-09-07
**Supersedes:** nothing. Complements `improvements_issues.md` G4 ("richer engine-drafted prose").

---

## 1. Goal

Engine-generated Saju reports currently do two things poorly:

1. **Jargon without translation.** Reports render classical terms — ten-god names
   ("Direct Wealth (正財)", "Seven Killings (偏官)"), bare Korean (재성, 대운, 용신,
   도화, 격국), 12운성 stage names, pattern names ("비견격 / Companion Grid") — but
   almost never say what they *mean* for the reader. Sentences like *"Its stem reads
   as Direct Wealth (正財) relative to your Day Master, so this area of life tends to
   carry that dynamic"* give a label and no meaning.

2. **Ungrounded interpretive data.** The engine's career, direction, colour, gemstone,
   organ, and grounding-practice tables (`report_data.py`) are hand-authored lists
   with **no `knowledge/` file behind them**. This violates `CLAUDE.md` Ground Rule 1
   ("every analytical claim must be derivable from the knowledge files"). When writing
   Harish's career and land readings, the reader had to explicitly flag *"the knowledge
   base has no business-type-by-element table"* and *"fengshui / 양택 house-siting is
   out of scope"* — gaps that recur for every candidate.

This spec fixes both, as **one spec with two tracks**:

- **Track B — Knowledge-base expansion.** Five new `knowledge/` files covering the
  highest-demand question areas, plus re-grounding the engine's hardcoded tables
  against them. Ships first — it is the raw material Track A presents.
- **Track A — Plain-language report layer.** A new engine module that adds inline
  term glosses, per-section "In plain words" callouts, and a tier-scaled glossary
  appendix to every generated report.

### Demand evidence (web research, 2026-09-07)

Common questions people bring to a Saju / BaZi reading, and current `knowledge/`
coverage:

| Topic | Representative questions | Coverage today |
|---|---|---|
| Career / vocation | "What job fits me?" · "employment vs. business?" · "skills to develop?" | none; `_CAREER_DOMAINS` is ungrounded |
| Wealth / business | "Which business suits me?" · "정재 vs 편재?" · "when does money come?" · "when to buy a house?" · "how to keep wealth?" | thin (`05-ten-gods.md` names 재성 only) |
| Directions / relocation | "Which way to sleep / desk / move?" · "favourable direction from 용신?" | none; `_ELEMENT_ASSOCIATIONS` ungrounded; saju-vs-풍수 boundary undefined |
| Health / constitution | "my 체질?" · "which organ?" · "foods / exercise?" · "risk years?" | minimal; organ map ungrounded |
| Auspicious dates (택일) | moving / opening / wedding / contract / surgery dates | none, though the engine emits an "Auspicious Dates" section |
| Personality / 일주 | "what is my 일주 and its traits?" | partial (`stem_profiles.py`, Day-Master stem only) — **deferred** |
| 신살 meaning | "what 살 do I have, what does it mean?" | `07-special-formations.md` is solid — Track A handles the plain layer |

Sources: Mindbridge 45-question list (KR); DeepOracle "BaZi reading — what to ask";
Bazi Fortune "career by element"; MyFengShui "BaZi & business"; BornChart "BaZi
favourable direction"; DeepOracle "BaZi health / organs"; Daebak "Korean saju guide
(incl. 택일)". Full URLs in the session transcript / `docs/market-research-2026-09.md`
if promoted.

---

## 2. Non-goals

- No change to chart computation (`engine.py`, `pillars.py`, `strength.py`, `yongsin.py`).
- No change to tier structure, pricing, or `apps/landing-page`.
- **No new report sections** and **no new skeleton `--focus` modes.** Track B enriches
  the content of sections the engine already emits (including the fullmap-tier
  `## Relocation, Travel & Direction Guidance` and `## Wealth & Investment Timing`).
- `knowledge/17-day-pillar-personality.md` (60 일주 profiles) is **deferred** to a
  separate later effort — it is a large standalone table.
- No change to the compat 11-sub-system engine logic (`compat.py`); Track A's plain
  layer applies to `compat_report.py` output only.

---

## 3. Track B — Knowledge-base expansion

### 3.1 New knowledge files

All follow the house style of the existing `knowledge/NN-*.md` files: English primary,
Korean + Hanja on first use, a "How to Use This File" footer, tables where the content
is tabular, and **explicit scope limits** where the topic borders a non-saju discipline.

Each file's interpretive claims must be traceable to the Korean classical lineage named
in `CLAUDE.md` (연해자평 for ten-gods, 궁통보감 for 용신, 적천수 for stem relations, the
명리 school) or to `03-five-elements.md` / `05-ten-gods.md` cycle logic. Where a
correspondence is a widely-published modern convention rather than a classical rule
(e.g. element→gemstone), the file says so in a "Classical vs. modern" note.

#### `knowledge/12-career-and-vocation.md`

- **Element → industry families.** Wood / Fire / Earth / Metal / Water, each with a
  short rationale from the element's nature (`03-five-elements.md`) and a list of
  fields. Reconciled with the enriched `_CAREER_DOMAINS`.
- **Ten-god → career mode.** 재성 → business/sales/ownership of resources; 관성 →
  institutions, management, licensed authority; 식상 → creation, expression, teaching,
  making; 인성 → research, advisory, knowledge work, credentialed practice; 비겁 →
  peer/team/competitive/independent-operator settings. From `05-ten-gods.md`.
- **용신 vs. Day-Master element for career choice.** The classical priority: align work
  with what the chart *needs* (용신 / 희신), not merely with the Day Master's own
  element; a chart that is too strong wants Output/Wealth/Officer fields to drain it,
  a chart that is too weak wants Resource/Companion fields to support it. Cross-ref
  `09-interpretation-method.md` Step 3.
- **Employment vs. entrepreneurship signals.** Strong DM + visible 식상/재성 → can
  carry independent variability; weak DM or 관성-led → institutional employment fits
  better first; 겁재 prominent → partnership caution. Tendency language only.
- **Skill-levers by dominant ten-god class.**
- **Scope limit:** this is vocational *tendency*, not a prediction of a specific job
  or a guarantee of success.

#### `knowledge/13-wealth-and-business.md`

- **정재 (Direct Wealth) vs. 편재 (Indirect Wealth) income styles.** Salary / steady
  cash flow / disciplined revenue vs. deal-making / commissions / trading / windfalls /
  higher variance. From `05-ten-gods.md`.
- **Wealth-producing chains.** 식상생재 (produce → earn; favourable for entrepreneurs),
  재생관 (wealth funds status / institutional position), 재고 (Wealth stored in an
  Earth branch — delayed / accumulated wealth). From `05-ten-gods.md` conflict-pattern
  section + `02-branches.md` storehouse logic.
- **Can the Day Master hold wealth?** Strong DM carries 재성 and 관성 directly; weak DM
  needs 인성 / 비겁 support before wealth is stable — otherwise 재성 becomes a burden
  (재다신약). From `09-interpretation-method.md`.
- **겁재奪財 (Robber robs Wealth).** Partnership / shared-money / family-business risk
  and the standard mitigations (written roles, separate accounts, structure).
- **Wealth timing.** Read from 대운 / 세운 touching 재성 stems/branches or running the
  favourable element; house-purchase and large-commitment timing keyed to 인성
  (property, seals) + favourable-element years. From `08-luck-pillars.md`.
- **Wealth preservation.** Diversification for strong DM; favourable-element-aligned
  custodianship; caution in 겁재 / 기신 decades.
- **Scope limit:** not financial advice; describes tendencies in how money is earned,
  held, and timed — not amounts or outcomes.

#### `knowledge/14-directions-and-relocation.md`

- **Element → cardinal direction.** Wood = East, Fire = South, Earth = Centre,
  Metal = West, Water = North. From `03-five-elements.md` (already stated there;
  this file makes it a usable table with the derived guidance).
- **용신 → favourable personal direction.** For the home's facing, the bed's head
  direction, the desk's facing, the direction of a move or a posting, and travel.
  희신 as the supporting direction; 기신 as the direction to minimise.
- **Relocation timing.** Move in favourable-element years / months; avoid months that
  clash (충) the natal day or hour branch; 역마 activation as a "movement is favoured"
  signal. From `07-special-formations.md` (역마) + `08-luck-pillars.md`.
- **Colours / numbers / seasons / materials by element.** The "Lucky Attributes"
  correspondences, with a "Classical vs. modern" note (직관적 오행 correspondence for
  colour/season/material is classical; specific gemstone lists are modern convention).
  Reconciled with `_ELEMENT_ASSOCIATIONS`.
- **Scope boundary (required, prominent):** this file covers the 명리 direction logic
  derived from 오행 and 용신 only. It is **not** 풍수 / 양택 (fengshui / dwelling
  siting) — no room-by-room placement, door/gate positions, stove/bed 방위 systems,
  eight mansions (팔택), flying stars (현공), or Kua numbers. A layout reading needs a
  풍수 practitioner. The engine and readers must not present 풍수 method as saju.

#### `knowledge/15-health-and-body.md`

- **오행 → 장부 (organ systems).** Wood = liver / gallbladder + nervous system;
  Fire = heart / small intestine + circulation; Earth = spleen / stomach + digestion;
  Metal = lung / large intestine + respiratory-immune boundary; Water = kidney /
  bladder + endocrine / reserve. Classical 오행-장부 mapping.
- **Excess vs. deficiency tendencies.** For each element, what an over-dominant vs. a
  depleted showing tends to stress (e.g. excess Water → fluid / kidney / hormonal
  load; deficient Fire → circulation / heart-warmth under-support). Tendency, not
  diagnosis.
- **Controlling-cycle cascade.** An over-strong element strains the organ system of
  the element it controls (excess Wood → Earth / digestion; excess Fire → Metal /
  lungs). From `03-five-elements.md` overcoming cycle.
- **Foods / lifestyle / rhythm by favourable element.** Reconciled with
  `_GROUNDING_PRACTICES`.
- **Health-watch timing.** 대운 / 세운 that heavily clash the chart or spike the
  already-excess element are the windows to be more preventive.
- **Scope limit (required, prominent):** classical tendency reading only. Not a
  diagnosis, not a screening recommendation, not a substitute for a licensed medical
  professional. Mirror `CLAUDE.md` Ground Rule 5.

#### `knowledge/16-date-selection.md`

- **택일 (date selection) principles, saju-scope only.** A candidate date's day pillar
  vs. the natal chart: avoid a day branch that clashes (충) the natal day or hour
  branch; avoid days running the 기신; favour days whose stem/branch element is the
  용신 or 희신; for a two-person event (wedding, joint venture) neither chart should be
  heavily clashed or drained. From `08-luck-pillars.md` (일운) + `03-five-elements.md`.
- **By event type.** Moving (이사), business opening (개업), signing / contracts,
  wedding date (혼례 택일), surgery / medical — what each keys to.
- **Scope boundary (required):** traditional 택일 also draws on the almanac's
  황도길일 / 손없는날 / 건제십이신 layers, which are a **separate almanac discipline**
  not derived from the querent's chart. This file and the engine cover the
  chart-relative layer only and say so; a full 택일 needs the almanac cross-check.
- **Limit:** the engine's "Auspicious Dates" output is a chart-relative shortlist, not
  a substitute for a traditional 택일 consultation.

### 3.2 Engine re-grounding + enrichment

**Principle:** every interpretive data table in `report_data.py` gets a
`# source: knowledge/NN-*.md` comment, and its content is reconciled to match that
file. Where the file is richer than the current table, the table is enriched to match
(more industries per element, direction / colour / number data, health excess-vs-
deficiency lines). No new report sections are added.

Tables to re-ground:

| Table (`report_data.py`) | Source file | Change |
|---|---|---|
| `_CAREER_DOMAINS` | `knowledge/12` | `# source:` tag; reconcile + enrich the per-element lists |
| `_ELEMENT_ASSOCIATIONS` (colors, direction, gemstones, season, foods, best times, avoid) | `knowledge/14` (+ `15` for foods) | `# source:` tag; reconcile; add a "modern convention" note in the docstring for gemstones |
| `_ELEMENT_ORGANS` | `knowledge/15` | `# source:` tag; reconcile wording |
| `_GROUNDING_PRACTICES` | `knowledge/15` | `# source:` tag; reconcile |
| `_SIGNATURES` (chart-signature one-liners) | `knowledge/03` + `01` stem imagery | `# source:` tag; confirm each line is defensible |

Prose fillers that consume these tables and speak to career / wealth / direction /
health must be checked so their claims still match the (possibly reworded) source:
`prose_fillers.py` — `wealth_pattern`, `employment_vs_entrepreneurship`, `income_rhythm`,
`skill_levers`, `company_type_fit`, `decade_career_strategy`, `depleted_element_health`,
`seasonal_daily_rhythms`, `element_story`, `long_term_vitality_strategy`,
`business_launch_format`, `business_seasonal_note`, `travel_timing`;
`prose_scaffold.py` career / health / 용신 scaffolds.

**Consistency test (new):** a `tests/test_knowledge_grounding.py` that, for each
re-grounded table, asserts the table's keys/domains appear in the cited file (a cheap
substring / heading check — not a semantic check, but it catches a table drifting away
from its source or a `# source:` pointing at the wrong file).

### 3.3 Wiring the new files into the method

- `knowledge/09-interpretation-method.md` — add references to `12`–`16` at the relevant
  steps (Step 4 ten-gods → career; Step 5 pillars → wealth/relationships; Step 8
  synthesis → direction, health, dates).
- `knowledge/00-glossary.md` — add any new terms introduced (재고, 재다신약, 택일,
  개업, 양택 as an *excluded* term with a "see 14 scope note").
- `CLAUDE.md` — "How to Answer" step 2 and the topic-file list: add `12`–`16`.
- `.claude/skills/` `saju` skill body — step 4 "load the topic knowledge files": add
  the career/wealth/direction/health/date-selection files to the relevant question types.
- `docs/openwiki/domain/knowledge-and-skill.md` — refresh the `knowledge/` file index.

---

## 4. Track A — Plain-language report layer

### 4.1 New module: `src/saju_engine/plain_glossary.py`

Mirrors `hanja_glossary.py` structurally.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class PlainDef:
    plain: str      # the lay gloss, <= ~14 words, curated from `knowledge/`
    display: str    # canonical rendering, e.g. "Direct Wealth (正財)"
    source: str     # e.g. "knowledge/05-ten-gods.md"

PLAIN_GLOSSARY: dict[str, PlainDef]
# keyed by every trigger form a generator might emit:
#   English tech name ("Direct Wealth"), the "English (漢字)" form it usually
#   appears in, and the bare Korean ("정재", "재성", "대운", "용신", ...).
# Multiple keys may map to the same PlainDef.
```

**Coverage of `PLAIN_GLOSSARY`:**

- 10 ten-gods (비견 겁재 식신 상관 편재 정재 편관 정관 편인 정인) + the 5 class terms
  (비겁 식상 재성 관성 인성) — glosses from `knowledge/05-ten-gods.md`
- 용신 희신 기신 한신 구신 — from `knowledge/03-five-elements.md` / `00-glossary.md`
- 대운 세운 월운 일운 — from `knowledge/08-luck-pillars.md`
- 격국 + the grid display names (비견격 / "Companion Grid" …) — from `00-glossary.md`
  / `knowledge/07-special-formations.md`
- 12운성 stages (장생 목욕 관대 건록 제왕 쇠 병 사 묘 절 태 양) and their English
  labels (Peak, Death, Bath …) — from `knowledge/06-twelve-stages.md`
- 신살: 도화 역마 화개 천을귀인 문창귀인 양인 공망 백호 괴강 원진 귀문관 겁살 재살
  천살 지살 월살 망신 장성 반안 천덕귀인 월덕귀인 — from `knowledge/07-special-formations.md`
- structural phrases: Day Master (일간), Day Pillar (일주), spouse palace, hidden
  stems (지장간), 본기 / 중기 / 여기, Heavenly Stem / Earthly Branch

**Functions:**

```python
def gloss_first_use(text: str, already_used: set[str]) -> str:
    """Append ' — {plain}' after the first occurrence of each glossary term.

    - longest trigger first (so "천을귀인" beats "천간")
    - skips a term already in `already_used` (mutated in place)
    - skips an occurrence already followed by ' — ' or '(' + gloss-like text
    - runs AFTER inject_hanja so it can match the "정재 (正財)" form
    - the ' — {plain}' carries an inline '*(see {source})*' citation which the
      PDF layer strips like every other citation; the gloss text itself stays
    """

def collect_used_terms(text: str) -> list[str]:
    """Return the display names of glossary terms that appear in `text`,
    in first-appearance order, deduped by PlainDef."""

def render_terms_section(used: list[str], tier: str) -> str:
    """Return the '## What the Terms Mean' markdown, or '' for the sample tier.

    - sample                          -> ''
    - essential / companion / spark   -> used terms, `plain` only (short)
    - deep / reading / fullmap / skeleton -> used terms, `plain` + one clarifying
                                             sentence (the fuller `PlainDef` note)
    Definition-list format: '- **{display}:** {gloss}'
    """
```

### 4.2 Section callouts — trailing `> **In plain words:** …`

Deterministic, chart-derived, ≤ 2 sentences, **not** marked `[ENGINE DRAFT]`.
New filler functions, one per target section:

- `prose_fillers.py` (premium): `plain_words_day_master(ctx)`,
  `plain_words_career(ctx)`, `plain_words_relationships(ctx)`,
  `plain_words_health(ctx)`, `plain_words_timing(ctx)`,
  `plain_words_pattern(ctx)`, `plain_words_ten_gods(ctx)`
- `prose_scaffold.py` (skeleton): equivalents keyed off the scaffold's context
- `compat_report.py`: `_plain_words_verdict`, `_plain_words_daymaster_cross`,
  `_plain_words_timing` (compat has its own section set)

Each returns a single blockquote line: `> **In plain words:** <text>` (or `""`
if the section is absent for that tier). The generator appends it as the last
content of the section, before the `---` / next `##`.

**Voice:** "bottom line" — what the section means for the reader's life, in the
same register as the existing prose. Example (Career & Wealth, strong DM +
식상생재): *"> **In plain words:** Your chart earns best by building niche
expertise other people pay a premium for and turning it into a product or
service — not by chasing big one-off wins. Keep income steady while that
compounds."*

**Insertion points** (premium, by `premium_report.py` line region as of 2026-09-07 —
the plan will re-locate by heading, not line number):

| Section heading | Callout after |
|---|---|
| `## Day Master Portrait` | end of the portrait prose (before `### Four Pillars, One by One` or the section's `---`) |
| `### Ten-God Distribution Table` | after the table's trailing note |
| `## Career & Wealth` | after the last `###` subsection present for the tier |
| `## Relationships` | after the last `###` subsection present for the tier |
| `## Health & Vitality` (and `— Deep-Dive`) | after the last `###` subsection |
| `## Timing: Major Luck …` | after the last `###` subsection |
| `## Natal Pattern Analysis` | note: this section **already** emits `### What This Means in Plain Language` — reuse / align, do not double up |

### 4.3 Glossary appendix — `## What the Terms Mean`

- Emitted **after** the Closing Note by all generators.
- Tier-scaled per `render_terms_section`.
- `src/saju_html/combine_candidate_report.py`: `_extract_closing_note` /
  `_strip_closing_note` currently take "from `## Closing Note` to EOF". Update so a
  trailing `## What the Terms Mean` section is preserved and re-appended *after* the
  moved Closing Note in the combined document (Closing Note stays the emotional
  ending; the glossary is a reference appendix behind it).

### 4.4 Assembly order (all three generators)

```
build sections  ->  append section callouts  ->  inject_hanja(...)
  ->  gloss_first_use(...)  ->  append render_terms_section(collect_used_terms(doc), tier)
```

`gloss_first_use` runs over the fully-assembled document (one `already_used` set for
the whole doc) so a term is glossed once, at its first appearance, wherever that is.

### 4.5 PDF safety (`src/saju_html/`)

- `strip_source_citations` (`_SOURCE_CITATION_RE`, `_SOURCE_SEE_RE`, `_SOURCE_PATH_RE`):
  must strip the `*(see knowledge/…)*` inside a gloss / callout / glossary entry but
  **leave the surrounding sentence**. Add tests with a `> **In plain words:** … *(see
  knowledge/05-ten-gods.md)*` line and a glossary entry.
- `strip_engine_drafts`: must **not** touch `> **In plain words:**` blockquotes (they
  are not draft markers). Verify the regexes (`_ENGINE_DRAFT_LINE_RE` is marker-only,
  so it should already be safe — add a regression test).
- `_strip_sources_section`: must not eat `## What the Terms Mean` (it targets
  `## Sources` / `## Sources & Limits` only — verify).
- `md_to_saju_pdf.py`: any new Korean / Hanja term that reaches the PDF via a gloss or
  the glossary and is not already in `STEM_MAP` / `BRANCH_MAP` / `TENGOD_MAP` /
  `KOR_REPL` / `HANJA_MAP` gets added.

---

## 5. Testing strategy

### Track B

- `tests/test_knowledge_grounding.py` (new): each re-grounded `report_data.py` table's
  domain keys / list items appear in the cited `knowledge/` file; every `# source:`
  path exists.
- Existing `tests/test_prose_fillers.py` / `tests/test_prose_scaffold.py`: update any
  assertions whose expected wording changed with the reconciliation.
- Manual: regenerate one candidate report end-to-end and read the career / health /
  direction sections against the new files.

### Track A

- `tests/test_plain_glossary.py` (new):
  - `gloss_first_use` glosses the first occurrence only; second occurrence untouched
  - longest-match: `천을귀인` not partially matched as `천간`
  - a term already followed by `(漢字)` + gloss is not re-glossed
  - `already_used` is honoured across calls
  - `render_terms_section`: `sample` → `""`; `essential` → short defs, only used
    terms; `deep` → fuller defs; unused terms absent
  - every `PlainDef.source` file exists
- `tests/test_premium_report.py`: for `essential` and `deep` —
  - each target section ends with exactly one `> **In plain words:**` line
  - `## What the Terms Mean` present, after `## Closing Note`, tier-appropriate length
  - `sample` has inline glosses but no callouts and no glossary
  - no `[ENGINE DRAFT — REVIEW REQUIRED]` anywhere
- `tests/test_skeleton.py`: skeleton gets glosses + full glossary
- compat tests: callouts + glossary present in `basic` and `deep`
- `src/saju_html` tests: gloss/callout/glossary survive `strip_source_citations` +
  `strip_engine_drafts`; only the `*(see …)*` is removed
- `tests/test_combine_candidate_report.py`: combined doc ends with
  `## What the Terms Mean` *after* the moved `## Closing Note`

### Regeneration

Regenerate and re-leak-check the checked-in demo / candidate outputs:
`candidates_horoscope/reports/rm/*`, and spot-check `vishnu-priya`, `mahesh`. The
`rm` demo PDFs under `apps/landing-page/public/demo-rm-*.pdf` are regenerated from the
same source and must stay leak-free.

---

## 6. Sequencing

1. **Track B first.** Knowledge files → glossary/method wiring → re-ground tables →
   grounding test → fix prose-filler wording → regenerate.
2. **Track A second.** `plain_glossary.py` (dict + functions + tests) → section
   callout fillers → wire into `premium_report` / `skeleton` / `compat_report` →
   PDF-safety tests → `combine_candidate_report` tweak → regenerate demos.

Each track is independently shippable and independently testable. The writing-plans
step may produce one plan with two parts or two plans; two parts of one plan is
acceptable here because Track A depends on Track B's plain definitions existing.

---

## 7. Files touched (summary)

**New:**
`knowledge/12-career-and-vocation.md`, `knowledge/13-wealth-and-business.md`,
`knowledge/14-directions-and-relocation.md`, `knowledge/15-health-and-body.md`,
`knowledge/16-date-selection.md`, `src/saju_engine/plain_glossary.py`,
`tests/test_plain_glossary.py`, `tests/test_knowledge_grounding.py`

**Modified:**
`src/saju_engine/report_data.py`, `src/saju_engine/prose_fillers.py`,
`src/saju_engine/prose_scaffold.py`, `src/saju_engine/premium_report.py`,
`src/saju_engine/skeleton.py`, `src/saju_engine/compat_report.py`,
`src/saju_html/__init__.py`, `src/saju_html/combine_candidate_report.py`,
`src/saju_html/md_to_saju_pdf.py`,
`knowledge/00-glossary.md`, `knowledge/09-interpretation-method.md`,
`CLAUDE.md`, the `saju` skill body, `docs/openwiki/domain/knowledge-and-skill.md`,
`tests/test_premium_report.py`, `tests/test_prose_fillers.py`,
`tests/test_prose_scaffold.py`, `tests/test_skeleton.py`,
`tests/test_combine_candidate_report.py`, compat tests

**Regenerated:**
`candidates_horoscope/reports/rm/*`, `apps/landing-page/public/demo-rm-*.pdf`,
`candidates_horoscope/README.md` (if any index line changes)

---

## 8. Open questions

None blocking. Two to confirm during planning:

- **Callout for `## Chart at a Glance`, `## Practical Guidance Summary`,
  `## Closing Note`:** design says no (they are already plain). Confirm when the first
  regenerated report is reviewed.
- **`knowledge/17-day-pillar-personality.md`:** deferred. If the plain-language layer
  makes the Day-Master-stem-only portrait feel thin, revisit as a fast follow.
