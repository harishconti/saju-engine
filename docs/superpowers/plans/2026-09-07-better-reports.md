# Better Reports Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every engine-generated Saju report explains its jargon in plain words (inline glosses + per-section "In plain words" callouts + a tier-scaled glossary appendix), and the engine's career / wealth / direction / health / date-selection content is drawn from grounded, cited `knowledge/` files instead of ungrounded hardcoded tables.

**Architecture:** Two tracks in one plan. **Track B** (Tasks 1–8) adds five `knowledge/` files and re-grounds the `report_data.py` interpretive tables against them. **Track A** (Tasks 9–16) adds `src/saju_engine/plain_glossary.py` and wires a plain-language layer into `premium_report.py`, `skeleton.py`, and `compat_report.py`, plus PDF-layer safety. Track B ships first because Track A's glosses cite Track B's files.

**Tech Stack:** Python 3.12, pytest (`python3 -m pytest`, config in `pyproject.toml` — `pythonpath = ["src"]`, `testpaths = ["tests"]`). Markdown knowledge files. No new dependencies.

## Global Constraints

- **Language rules (`CLAUDE.md`):** English primary; Korean (한글) + Hanja (한자) on first use of a technical term; Revised Romanization.
- **Ground Rule 1 (`CLAUDE.md`):** every analytical claim in a `knowledge/` file must be derivable from the Korean classical lineage (연해자평, 궁통보감, 적천수, 명리 school) or from cycle logic already in `knowledge/03-five-elements.md` / `05-ten-gods.md`. Where a correspondence is modern convention, label it "Classical vs. modern".
- **Ground Rule 5:** health content is tendency only — not diagnosis, not medical advice.
- **No new report sections; no new skeleton `--focus` modes.** Track B enriches the content of sections the engine already emits.
- **Section callouts and the glossary appendix are final engine output** — never wrapped in `[ENGINE DRAFT — REVIEW REQUIRED]`.
- **Term style:** first use = `Classical Name (漢字) — plain gloss`; later uses unchanged.
- **Glossary tiering:** `sample` → none; `essential` / `companion` / `spark` → used terms, short; `deep` / `reading` / `fullmap` / skeleton / compat → used terms, full.
- **Citations** (`*(see knowledge/…)*`) stay in the `.md`, are stripped at the PDF layer — this already works for existing prose; new gloss/callout/glossary text must behave the same.
- Full test suite (`python3 -m pytest -q`) must stay green (590 tests today) and grow.
- Knowledge files follow the house style of `knowledge/03-five-elements.md`: `# NN · Title (한글, 漢字)` H1, topic sections, a `## How to Use This File` footer, tables where tabular, and a prominent scope-limit block where the topic borders a non-saju discipline.

---

## Track B — Knowledge base

### Task 1: `knowledge/12-career-and-vocation.md`

**Files:**
- Create: `knowledge/12-career-and-vocation.md`
- Test: `tests/test_knowledge_files.py` (create)

**Interfaces:**
- Produces: a file whose element→industry lists are the **canonical source** reconciled into `report_data._CAREER_DOMAINS` in Task 7. Section headings and element names must be greppable.

- [ ] **Step 1: Write the failing test**

Create `tests/test_knowledge_files.py`:

```python
"""Structural checks on the knowledge/ files (content is reviewed by a human)."""
from pathlib import Path

KB = Path(__file__).parent.parent / "knowledge"


def _read(name: str) -> str:
    return (KB / name).read_text(encoding="utf-8")


def test_12_career_has_required_sections():
    t = _read("12-career-and-vocation.md")
    for heading in [
        "# 12 · Career",
        "## Element → Industry Families",
        "## Ten-God → Career Mode",
        "## 용신 vs. Day Master for Career Choice",
        "## Employment vs. Entrepreneurship",
        "## Skill-Levers by Dominant Ten-God",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    for element in ["Wood", "Fire", "Earth", "Metal", "Water"]:
        assert f"### {element}" in t
    # every element family cites the five-elements or ten-gods file
    assert t.count("knowledge/03-five-elements.md") >= 1
    assert t.count("knowledge/05-ten-gods.md") >= 1
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python3 -m pytest tests/test_knowledge_files.py::test_12_career_has_required_sections -q`
Expected: FAIL — `FileNotFoundError` / missing headings.

- [ ] **Step 3: Write the file**

Create `knowledge/12-career-and-vocation.md` with these sections and content:

- `# 12 · Career & Vocation (직업론, 職業論)`
- Intro: career is read from (a) the Day Master element and what the chart *needs*, (b) the ten-god balance, (c) the timing layer (대운). Cross-ref `knowledge/09-interpretation-method.md` Steps 3–4.
- `## Element → Industry Families` — one `### <Element>` per element. Each has: a one-line rationale from the element's nature (cite `knowledge/03-five-elements.md`), and a bullet list of fields. Use exactly these families (they are reconciled into `_CAREER_DOMAINS` in Task 7):
  - **Wood** (growth, branching, cultivation, upward structure): education & training; healthcare & wellness; design, writing & publishing; social & environmental work; HR / people development; horticulture, forestry, textiles.
  - **Fire** (visibility, expression, transformation, energy): leadership & public-facing roles; media, performing & broadcast arts; marketing, PR & advertising; teaching, coaching & public speaking; entrepreneurship & product evangelism; energy, lighting, hospitality front-of-house; beauty & aesthetics.
  - **Earth** (holding, storing, mediating, grounding): real estate & property; construction & civil works; hospitality & food; finance, accounting & insurance; counselling, mediation & pastoral care; operations, logistics & project management; agriculture & land.
  - **Metal** (precision, refinement, boundary, judgement): law & governance; engineering & technology infrastructure; medicine, surgery & diagnostics; finance, investment & trading; quality, audit & forensic analysis; security, defence & policing; metalwork, jewellery, instruments.
  - **Water** (flow, connection, depth, movement): strategy, consulting & research; diplomacy & international trade; psychology, counselling & therapy; arts, curation & creative research; journalism & investigation; logistics, shipping, travel & mobility; data, networks & platforms.
- `## Ten-God → Career Mode` — table: 재성 → business/sales/owning-and-growing-resources; 관성 → institutions, licensed authority, management, government; 식상 → creating, expressing, teaching, making, performing; 인성 → research, advisory, knowledge/credentialed practice, curation; 비겁 → peer/team/competitive settings, independent operator, partnerships. Cite `knowledge/05-ten-gods.md`.
- `## 용신 vs. Day Master for Career Choice` — the classical priority: align work with what the chart *needs* (용신 / 희신), not merely the Day Master's own element. Too-strong DM → Output / Wealth / Officer fields that drain it; too-weak DM → Resource / Companion fields that support it first. Cite `knowledge/09-interpretation-method.md` Step 3.
- `## Employment vs. Entrepreneurship` — signals: strong DM + visible 식상/재성 → can carry independent variability; weak DM or 관성-led → institutional employment fits better first; 겁재 prominent → partnership caution (cross-ref `knowledge/13-wealth-and-business.md` 겁재奪財). Tendency language only.
- `## Skill-Levers by Dominant Ten-God` — one line each: Companion → collaboration & self-assessment; Output → craft & communication cadence; Wealth → pricing & resource stewardship; Officer → systems & accountable leadership; Resource → depth study & synthesis.
- `## Scope & Limits` — vocational *tendency*, not a specific job prediction or a success guarantee; not career advice.
- `## How to Use This File` — read after Step 4 of the interpretation method; combine element family + ten-god mode + 용신 test; hand the timing to `knowledge/08-luck-pillars.md`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m pytest tests/test_knowledge_files.py::test_12_career_has_required_sections -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add knowledge/12-career-and-vocation.md tests/test_knowledge_files.py
git commit -m "docs(knowledge): add 12-career-and-vocation.md"
```

*(If the working tree is not a git repo, skip every commit step in this plan.)*

---

### Task 2: `knowledge/13-wealth-and-business.md`

**Files:**
- Create: `knowledge/13-wealth-and-business.md`
- Test: `tests/test_knowledge_files.py` (add one test)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_knowledge_files.py`:

```python
def test_13_wealth_has_required_sections():
    t = _read("13-wealth-and-business.md")
    for heading in [
        "# 13 · Wealth",
        "## 정재 vs. 편재 — Two Income Styles",
        "## Wealth-Producing Chains",
        "## Can the Day Master Hold Wealth?",
        "## 겁재奪財 — Partnership & Shared-Money Risk",
        "## Wealth Timing",
        "## Wealth Preservation",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    assert "식상생재" in t and "재생관" in t and "재고" in t
    assert "재다신약" in t
    assert "knowledge/05-ten-gods.md" in t
```

- [ ] **Step 2: Run it — confirm FAIL**

Run: `python3 -m pytest tests/test_knowledge_files.py::test_13_wealth_has_required_sections -q`

- [ ] **Step 3: Write the file**

`knowledge/13-wealth-and-business.md`:

- `# 13 · Wealth & Business (재물론, 財物論)`
- `## 정재 vs. 편재 — Two Income Styles` — 정재 (正財): salary, steady cash flow, savings, disciplined revenue, one's own earned money. 편재 (偏財): deal-making, commissions, trading, side income, windfalls, higher variance, "the big catch". Cite `knowledge/05-ten-gods.md`.
- `## Wealth-Producing Chains` — **식상생재** (Output feeds Wealth: produce → earn; "highly favorable for entrepreneurial types"); **재생관** (Wealth funds status / institutional position); **재고** (財庫 — Wealth stored in an Earth branch 辰戌丑未 → delayed, accumulated, "opens" when the storehouse is triggered by clash/punishment). Cite `knowledge/05-ten-gods.md` conflict-pattern section + `knowledge/02-branches.md` storehouse logic.
- `## Can the Day Master Hold Wealth?` — strong DM carries 재성 + 관성 directly; weak DM needs 인성 / 비겁 support first, else **재다신약** (財多身弱 — "much wealth, weak self": money becomes a burden and a health/《stress》 drain). Cite `knowledge/09-interpretation-method.md`.
- `## 겁재奪財 — Partnership & Shared-Money Risk` — 비겁 heavy + shared money (partners, family business, investors) → "Robber robs the Wealth": financial loss, partner loss, partnership breakdown. Mitigations: written roles & ownership %, separate accounts, earn through a structured product/service not informal arrangements. Cite `knowledge/05-ten-gods.md`.
- `## Wealth Timing` — read from 대운 / 세운 whose stem or branch is 재성 to the Day Master, or that runs the favourable element. House purchase / large commitments key to 인성 (property, seals, contracts) landing in a favourable-element year. Cite `knowledge/08-luck-pillars.md`.
- `## Wealth Preservation` — strong DM: diversify, don't concentrate beyond what the chart holds; favourable-element-aligned custodianship; defend rather than expand in 겁재 / 기신 decades.
- `## Scope & Limits` — tendencies in how money is earned, held, timed — not amounts, not outcomes, not financial advice (mirror `CLAUDE.md` Rule 5).
- `## How to Use This File` — pair with `knowledge/12-career-and-vocation.md` (the earning vehicle) and `knowledge/08-luck-pillars.md` (the when).

- [ ] **Step 4: Run — PASS**

Run: `python3 -m pytest tests/test_knowledge_files.py::test_13_wealth_has_required_sections -q`

- [ ] **Step 5: Commit**

```bash
git add knowledge/13-wealth-and-business.md tests/test_knowledge_files.py
git commit -m "docs(knowledge): add 13-wealth-and-business.md"
```

---

### Task 3: `knowledge/14-directions-and-relocation.md`

**Files:**
- Create: `knowledge/14-directions-and-relocation.md`
- Test: `tests/test_knowledge_files.py` (add one test)

**Interfaces:**
- Produces: canonical element→direction / colour / number / season / material data reconciled into `report_data._ELEMENT_ASSOCIATIONS` in Task 7.

- [ ] **Step 1: Write the failing test**

```python
def test_14_directions_has_required_sections_and_scope_block():
    t = _read("14-directions-and-relocation.md")
    for heading in [
        "# 14 · Directions",
        "## Element → Direction",
        "## 용신 → Favourable Personal Direction",
        "## Relocation & Move Timing",
        "## Colours, Numbers, Seasons & Materials by Element",
        "## Classical vs. Modern",
        "## Scope Boundary — This Is Not 풍수 (Fengshui)",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    # scope block must name the excluded systems
    for excluded in ["풍수", "양택", "팔택", "flying star", "Kua"]:
        assert excluded in t
    # direction table must contain all five pairings
    for pair in ["East", "South", "West", "North", "Centre"]:
        assert pair in t
```

- [ ] **Step 2: Run it — confirm FAIL**

- [ ] **Step 3: Write the file**

`knowledge/14-directions-and-relocation.md`:

- `# 14 · Directions & Relocation (방위·이사, 方位·移徙)`
- `## Element → Direction` — table (cite `knowledge/03-five-elements.md`): Wood = East; Fire = South; Earth = Centre (and the four inter-cardinal transitions); Metal = West; Water = North.
- `## 용신 → Favourable Personal Direction` — from the querent's 용신: the favourable direction for a home's facing, the head of the bed, a desk's facing, the direction of a move / posting, and travel. 희신 = the supporting direction. 기신 = the direction to minimise time in. Worked mini-example ("용신 Fire → south-facing workspace, sleep head-south, favour southern rooms").
- `## Relocation & Move Timing` — move in favourable-element years / months; avoid months that clash (충) the natal day or hour branch; **역마 (驛馬)** activation = "movement is favoured / likely" (cite `knowledge/07-special-formations.md`); tie the year layer to `knowledge/08-luck-pillars.md`.
- `## Colours, Numbers, Seasons & Materials by Element` — table, five rows. Colours: Wood green/teal; Fire red/orange; Earth yellow/ochre/brown; Metal white/silver/grey; Water black/navy/deep-blue. Numbers: Wood 3,8; Fire 2,7; Earth 5,0; Metal 4,9; Water 1,6. Seasons: spring / summer / late-summer & transitions / autumn / winter. Materials: wood & plants / light & warmth / ceramic, stone, clay / metal & stone / glass & water features. (These are the values `_ELEMENT_ASSOCIATIONS` must match.)
- `## Classical vs. Modern` — the 오행→direction, colour, season, number correspondences are classical (하도낙서 / 오행 방위). Specific **gemstone** lists are a modern convention, not a classical 명리 rule — present them as optional and clearly labelled.
- `## Scope Boundary — This Is Not 풍수 (Fengshui)` — **prominent block.** This file covers only the 명리 direction logic derived from 오행 and the querent's 용신. It is **not** 풍수 / 양택 (fengshui / dwelling siting): no room-by-room placement, door/gate positions, stove or bed 방위 systems, eight mansions (팔택), flying stars (현공 / flying star), or Kua numbers. A building-layout reading needs a 풍수 practitioner. The engine and readers must not present 풍수 method as saju.
- `## How to Use This File` — the direction is an *input to a decision*, not a rule to obey; combine with timing and the person's real constraints.

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit**

```bash
git add knowledge/14-directions-and-relocation.md tests/test_knowledge_files.py
git commit -m "docs(knowledge): add 14-directions-and-relocation.md"
```

---

### Task 4: `knowledge/15-health-and-body.md`

**Files:**
- Create: `knowledge/15-health-and-body.md`
- Test: `tests/test_knowledge_files.py` (add one test)

**Interfaces:**
- Produces: canonical 오행→organ data reconciled into `report_data._ELEMENT_ORGANS` and lifestyle content reconciled into `_GROUNDING_PRACTICES` in Task 7.

- [ ] **Step 1: Write the failing test**

```python
def test_15_health_has_required_sections_and_disclaimer():
    t = _read("15-health-and-body.md")
    for heading in [
        "# 15 · Health",
        "## 오행 → Organ Systems",
        "## Excess vs. Deficiency Tendencies",
        "## Controlling-Cycle Cascade",
        "## Foods, Lifestyle & Rhythm by Favourable Element",
        "## Health-Watch Timing",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    assert "not a diagnosis" in t.lower()
    assert "licensed medical" in t.lower()
    for organ in ["liver", "heart", "spleen", "lung", "kidney"]:
        assert organ in t.lower()
```

- [ ] **Step 2: Run it — confirm FAIL**

- [ ] **Step 3: Write the file**

`knowledge/15-health-and-body.md`:

- `# 15 · Health & Body (건강론, 健康論)` — open with the disclaimer: classical *tendency* reading only, not a diagnosis, not screening advice, not a substitute for a licensed medical professional (mirror `CLAUDE.md` Rule 5).
- `## 오행 → Organ Systems` — table: Wood = liver / gallbladder + nervous system; Fire = heart / small intestine + circulation; Earth = spleen / stomach + digestion; Metal = lung / large intestine + respiratory-immune boundary; Water = kidney / bladder + endocrine / reserve. (These wordings are what `_ELEMENT_ORGANS` must match.)
- `## Excess vs. Deficiency Tendencies` — per element, two rows: what an over-dominant showing tends to stress vs. what a depleted showing tends to leave under-supported. E.g. excess Water → fluid retention, kidney / urinary load, hormonal swings; deficient Water → low-back / knee, tinnitus, memory, bone density. Excess Fire → sleeplessness, palpitation, inflammation; deficient Fire → poor circulation, low warmth, flat mood.
- `## Controlling-Cycle Cascade` — an over-strong element strains the organ system of the element it controls (excess Wood → Earth / digestion; excess Fire → Metal / lungs; excess Earth → Water / kidney; excess Metal → Wood / liver; excess Water → Fire / heart). Cite `knowledge/03-five-elements.md` overcoming cycle.
- `## Foods, Lifestyle & Rhythm by Favourable Element` — five blocks; the practices `_GROUNDING_PRACTICES` must match. Wood: forests / dawn waking / stretching / leafy greens & sour in moderation. Fire: midday sun / brief social breaks / bitter & red foods / south-facing bright rooms. Earth: gardening & pottery / steady meal & sleep schedule / whole grains & mild sweet / grounded routine. Metal: breathwork in cool dry air / decluttering / white foods & pungent spice / autumn quiet. Water: swimming & baths / evening stillness / black beans, seaweed, salt in moderation / north-facing rest.
- `## Health-Watch Timing` — 대운 / 세운 that heavily clash the chart or spike the already-excess element are the windows to be more preventive; the deficient element's season is the natural time to support it.
- `## Scope & Limits` — restate the disclaimer; the chart's lightest element is "where to begin gentle preventive support", not "what is wrong".
- `## How to Use This File` — read the element balance first (`knowledge/03`), then this file for the body mapping, then `knowledge/08` for timing.

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit**

```bash
git add knowledge/15-health-and-body.md tests/test_knowledge_files.py
git commit -m "docs(knowledge): add 15-health-and-body.md"
```

---

### Task 5: `knowledge/16-date-selection.md`

**Files:**
- Create: `knowledge/16-date-selection.md`
- Test: `tests/test_knowledge_files.py` (add one test)

- [ ] **Step 1: Write the failing test**

```python
def test_16_date_selection_has_required_sections_and_scope():
    t = _read("16-date-selection.md")
    for heading in [
        "# 16 · Date Selection",
        "## Chart-Relative Principles",
        "## By Event Type",
        "## Two-Person Events",
        "## Scope Boundary — The Almanac Layer",
        "## Scope & Limits",
        "## How to Use This File",
    ]:
        assert heading in t, f"missing: {heading}"
    assert "황도길일" in t and "손없는날" in t
    assert "이사" in t and "개업" in t
```

- [ ] **Step 2: Run it — confirm FAIL**

- [ ] **Step 3: Write the file**

`knowledge/16-date-selection.md`:

- `# 16 · Date Selection (택일, 擇日)`
- `## Chart-Relative Principles` — a candidate date's day pillar vs. the natal chart: **avoid** a day branch that clashes (충) the natal day or hour branch; **avoid** days running the 기신; **favour** days whose stem/branch element is the 용신 or 희신; **favour** days that harmonise (합 / 삼합) with the natal day branch. Cite `knowledge/08-luck-pillars.md` (일운) + `knowledge/03-five-elements.md`.
- `## By Event Type` — moving (이사): key to the mover's 용신 direction (`knowledge/14`) + a non-clashing day. Business opening (개업): favour 식상 / 재성 day energy in a favourable-element month. Signing / contracts: 관성 / 인성 day energy, no clash to day branch. Wedding (혼례 택일): non-clashing for **both** charts, favourable or neutral element. Surgery / medical: avoid clash to the day branch and to the element governing the organ system involved (`knowledge/15`).
- `## Two-Person Events` — a date should not heavily clash or drain **either** chart; prefer a day favourable or neutral to both 용신.
- `## Scope Boundary — The Almanac Layer` — **prominent block.** Traditional 택일 also uses the almanac's 황도길일 (yellow-way auspicious days), 손없는날 ("no-ghost" moving days), 건제십이신 (12 day-officers), and 28-mansion layers — a **separate almanac discipline** not derived from the querent's chart. This file and the engine cover the chart-relative layer only; a full 택일 needs the almanac cross-check by a practitioner.
- `## Scope & Limits` — the engine's "Auspicious Dates" output is a chart-relative shortlist, not a substitute for a traditional 택일 consultation; not a guarantee of outcome.
- `## How to Use This File` — narrow to a window with 대운/세운 (`knowledge/08`), then rank days in that window with the principles here, then (outside this system) cross-check the almanac.

- [ ] **Step 4: Run — PASS**

- [ ] **Step 5: Commit**

```bash
git add knowledge/16-date-selection.md tests/test_knowledge_files.py
git commit -m "docs(knowledge): add 16-date-selection.md"
```

---

### Task 6: Wire the new files into the method, glossary, and skill

**Files:**
- Modify: `knowledge/09-interpretation-method.md` (add refs at Steps 4, 5, 8)
- Modify: `knowledge/00-glossary.md` (add: 재고 財庫, 재다신약 財多身弱, 택일 擇日, 개업 開業; add 양택 陽宅 as an **excluded** term pointing to `knowledge/14` scope note)
- Modify: `CLAUDE.md` ("How to Answer" step 2 list; the topic-file bullets under "How to Answer" item 2)
- Modify: the `saju` skill body file (its "load the topic knowledge files" list — path: `.claude/skills/saju/SKILL.md` or wherever `grep -rl "load the topic knowledge files" .claude` finds it)
- Modify: `docs/openwiki/domain/knowledge-and-skill.md` (the `knowledge/` file index)
- Test: `tests/test_knowledge_files.py` (add cross-reference test)

- [ ] **Step 1: Write the failing test**

```python
def test_new_knowledge_files_are_referenced():
    method = _read("09-interpretation-method.md")
    for n in ["12-career", "13-wealth", "14-directions", "15-health", "16-date-selection"]:
        assert n in method, f"09-interpretation-method.md does not reference {n}"
    glossary = _read("00-glossary.md")
    for term in ["재고", "재다신약", "택일", "양택"]:
        assert term in glossary
```

- [ ] **Step 2: Run it — confirm FAIL**

Run: `python3 -m pytest tests/test_knowledge_files.py::test_new_knowledge_files_are_referenced -q`

- [ ] **Step 3: Make the edits**

- In `knowledge/09-interpretation-method.md`:
  - Step 4 (ten gods): add "For a career reading, carry the ten-god mix into `knowledge/12-career-and-vocation.md` and `knowledge/13-wealth-and-business.md`."
  - Step 5 (pillars): add "Wealth themes → `knowledge/13`; direction themes → `knowledge/14`."
  - Step 8 (synthesize): add "Direction / relocation → `knowledge/14`; health tendencies → `knowledge/15`; auspicious dates → `knowledge/16`."
- In `knowledge/00-glossary.md`: add the four terms in alphabetical position with one-line definitions; for 양택, the definition is "陽宅 — dwelling-siting fengshui. **Out of scope for this knowledge base** — see `knowledge/14-directions-and-relocation.md` §Scope Boundary."
- In `CLAUDE.md` "How to Answer": extend the topic-file guidance — "career/wealth → `05-ten-gods.md`, `12-career-and-vocation.md`, `13-wealth-and-business.md`; direction/relocation → `14-directions-and-relocation.md`; health → `15-health-and-body.md`; auspicious dates → `16-date-selection.md`."
- In the `saju` skill body: mirror the same additions in its "Load the topic knowledge files" step.
- In `docs/openwiki/domain/knowledge-and-skill.md`: add rows 12–16 to the file index with one-line summaries.

- [ ] **Step 4: Run the test — PASS**

Run: `python3 -m pytest tests/test_knowledge_files.py -q`
Expected: all knowledge-file tests PASS.

- [ ] **Step 5: Commit**

```bash
git add knowledge/09-interpretation-method.md knowledge/00-glossary.md CLAUDE.md docs/openwiki/domain/knowledge-and-skill.md tests/test_knowledge_files.py
git add -A .claude
git commit -m "docs: wire knowledge/12-16 into method, glossary, CLAUDE, skill, openwiki"
```

---

### Task 7: Re-ground `report_data.py` interpretive tables

**Files:**
- Modify: `src/saju_engine/report_data.py` (`_CAREER_DOMAINS`, `_ELEMENT_ASSOCIATIONS`, `_ELEMENT_ORGANS`, `_GROUNDING_PRACTICES`, `_SIGNATURES` — add `# source:` comments and reconcile content to Tasks 1–5)
- Create: `tests/test_knowledge_grounding.py`

**Interfaces:**
- Consumes: the element family lists in `knowledge/12`, the direction/colour/number/material data in `knowledge/14`, organ wording in `knowledge/15`, lifestyle practices in `knowledge/15`.
- Produces: no signature change — `_CAREER_DOMAINS: Dict[str, List[Tuple[str, str]]]`, `_ELEMENT_ASSOCIATIONS: Dict[str, Dict[str, str]]`, `_ELEMENT_ORGANS: Dict[str, str]`, `_GROUNDING_PRACTICES: Dict[str, List[str]]` keep their shapes.

- [ ] **Step 1: Write the failing test**

Create `tests/test_knowledge_grounding.py`:

```python
"""Assert the engine's interpretive tables trace to their cited knowledge/ file."""
import re
from pathlib import Path

from saju_engine.report_data import (
    _CAREER_DOMAINS,
    _ELEMENT_ASSOCIATIONS,
    _ELEMENT_ORGANS,
    _GROUNDING_PRACTICES,
)

KB = Path(__file__).parent.parent / "knowledge"


def _kb(name: str) -> str:
    return (KB / name).read_text(encoding="utf-8").lower()


def test_career_domains_domain_titles_appear_in_kb12():
    kb = _kb("12-career-and-vocation.md")
    for element, pairs in _CAREER_DOMAINS.items():
        for title, _roles in pairs:
            # first significant word of the domain title must appear in the file
            head = re.split(r"[ &/]", title.lower())[0]
            assert head in kb, f"{element}/{title!r} not grounded in knowledge/12"


def test_element_directions_match_kb14():
    kb = _kb("14-directions-and-relocation.md")
    expect = {"Wood": "east", "Fire": "south", "Earth": "cent", "Metal": "west", "Water": "north"}
    for element, assoc in _ELEMENT_ASSOCIATIONS.items():
        assert expect[element] in assoc["direction"].lower()
        assert expect[element] in kb


def test_element_organs_match_kb15():
    kb = _kb("15-health-and-body.md")
    for element, organs in _ELEMENT_ORGANS.items():
        head = organs.split("/")[0].strip().split()[0].lower()  # e.g. "liver"
        assert head in kb, f"{element} organ {organs!r} not in knowledge/15"


def test_grounding_practices_have_kb15_anchors():
    kb = _kb("15-health-and-body.md")
    anchors = {
        "Wood": "forest", "Fire": "midday", "Earth": "grain",
        "Metal": "breath", "Water": "swim",
    }
    for element, practices in _GROUNDING_PRACTICES.items():
        joined = " ".join(practices).lower()
        assert anchors[element] in joined
        assert anchors[element] in kb
```

- [ ] **Step 2: Run it — confirm FAIL**

Run: `python3 -m pytest tests/test_knowledge_grounding.py -q`
Expected: FAIL (some domain heads / anchors not yet aligned between table and file).

- [ ] **Step 3: Reconcile the tables**

In `src/saju_engine/report_data.py`:
- Above `_ELEMENT_ORGANS`: `# source: knowledge/15-health-and-body.md § 오행 → Organ Systems`
- Above `_ELEMENT_ASSOCIATIONS`: `# source: knowledge/14-directions-and-relocation.md (direction/colours/numbers/materials); knowledge/15 (foods). Gemstone lists are modern convention — see knowledge/14 § Classical vs. Modern.`
- Above `_CAREER_DOMAINS`: `# source: knowledge/12-career-and-vocation.md § Element → Industry Families`
- Above `_GROUNDING_PRACTICES`: `# source: knowledge/15-health-and-body.md § Foods, Lifestyle & Rhythm by Favourable Element`
- Above `_SIGNATURES`: `# source: knowledge/03-five-elements.md (element nature) + knowledge/01-stems.md (stem imagery)`
- Edit the list contents where the grounding test still fails so every domain title's first word, every organ's first word, and every grounding anchor appears in the corresponding file. Prefer editing the **table** to match the file (the file is canonical); only edit the file if the file genuinely omitted something it should contain.
- Keep `Earth` `"direction": "center"` but ensure `knowledge/14` uses "Centre" *and* mentions "center" once (US spelling) so the test's `"cent"` substring passes, or adjust the test — pick one and be consistent.

- [ ] **Step 4: Run the tests — PASS**

Run: `python3 -m pytest tests/test_knowledge_grounding.py tests/test_knowledge_files.py -q`
Expected: PASS

- [ ] **Step 5: Run the full suite for regressions**

Run: `python3 -m pytest -q`
Expected: any failures are only in `test_premium_report.py` / `test_prose_fillers.py` / `test_prose_scaffold.py` from reworded table content — fixed in Task 8. Note them.

- [ ] **Step 6: Commit**

```bash
git add src/saju_engine/report_data.py tests/test_knowledge_grounding.py
git commit -m "feat(engine): ground report_data interpretive tables in knowledge/12-16"
```

---

### Task 8: Reconcile prose fillers/scaffold wording with the re-grounded tables

**Files:**
- Modify: `src/saju_engine/prose_fillers.py` (functions listed in the spec §3.2 that assert claims about career/wealth/health/direction)
- Modify: `src/saju_engine/prose_scaffold.py` (career / health / 용신 scaffolds)
- Modify: `tests/test_prose_fillers.py`, `tests/test_prose_scaffold.py`, `tests/test_premium_report.py` — update expected strings that legitimately changed

- [ ] **Step 1: Run the affected tests to see current failures**

Run: `python3 -m pytest tests/test_prose_fillers.py tests/test_prose_scaffold.py tests/test_premium_report.py -q`
Expected: FAIL list from Task 7's reword.

- [ ] **Step 2: Fix the prose, not the meaning**

For each failing assertion: if the prose still makes a claim now worded differently in the table (e.g. an organ phrase, a career domain name), update the filler string to use the canonical wording from the `knowledge/` file. Do **not** weaken a test to pass — if a test asserted a real behaviour, keep asserting it with the new wording.

- [ ] **Step 3: Add one filler-grounding test**

Add to `tests/test_prose_fillers.py`:

```python
def test_health_filler_uses_kb15_organ_wording():
    from pathlib import Path
    from saju_engine.engine import compute_chart
    from saju_engine import prose_fillers as PF
    kb = (Path(__file__).parent.parent / "knowledge" / "15-health-and-body.md").read_text().lower()
    chart = compute_chart(name="T", gender="F", year=1993, month=12, day=11,
                          hour=2, minute=45, longitude=79.32, utc_offset=5.5,
                          use_solar_time=True, convention="korean")
    # depleted_element_health names an organ system — that phrase should exist in kb15
    text = PF.depleted_element_health(_ctx_like(chart)).lower()  # helper already in this file
    assert any(w in kb for w in ["liver", "heart", "spleen", "lung", "kidney"] if w in text)
```

*(If `_ctx_like` / a context factory does not already exist in the test file, reuse whatever `_ReportContext` construction the other tests in the file use — check the top of `tests/test_prose_fillers.py`.)*

- [ ] **Step 4: Run — PASS**

Run: `python3 -m pytest -q`
Expected: full suite green.

- [ ] **Step 5: Commit**

```bash
git add src/saju_engine/prose_fillers.py src/saju_engine/prose_scaffold.py tests/
git commit -m "fix(engine): reconcile prose wording with grounded knowledge tables"
```

---

## Track A — Plain-language layer

### Task 9: `plain_glossary.py` — data + `gloss_first_use`

**Files:**
- Create: `src/saju_engine/plain_glossary.py`
- Create: `tests/test_plain_glossary.py`

**Interfaces:**
- Produces:
  - `PlainDef` — frozen dataclass `(plain: str, display: str, source: str, note: str = "")`
  - `PLAIN_GLOSSARY: dict[str, PlainDef]` — keyed by every trigger string (English tech name, `English (漢字)` form, bare Korean)
  - `gloss_first_use(text: str, already_used: set[str]) -> str` — appends ` — {plain} *(see {source})*` after the first occurrence of each term; mutates `already_used`
  - `collect_used_terms(text: str) -> list[str]` — display names present, first-appearance order, deduped by `PlainDef` identity
  - `render_terms_section(used: list[str], tier: str) -> str` — the `## What the Terms Mean` markdown or `""`

- [ ] **Step 1: Write the failing test**

Create `tests/test_plain_glossary.py`:

```python
from pathlib import Path
import pytest
from saju_engine import plain_glossary as PG

KB = Path(__file__).parent.parent / "knowledge"


def test_every_source_file_exists():
    for d in set(PG.PLAIN_GLOSSARY.values()):
        assert (KB / Path(d.source).name).exists(), d.source


def test_gloss_first_use_only_glosses_first_occurrence():
    used = set()
    out = PG.gloss_first_use("Direct Wealth here, and Direct Wealth again.", used)
    assert out.count("steady") == 1  # gloss text appears once
    assert "Direct Wealth" in "Direct Wealth"  # sanity
    assert out.index("steady") < out.index("again")


def test_gloss_longest_match_first():
    used = set()
    out = PG.gloss_first_use("천을귀인 appears", used)
    # must gloss the star, not partially match 천간
    assert "천을귀인" in out and "노블" not in out  # (adjust to real gloss)
    assert "천을귀인" in used or PG.PLAIN_GLOSSARY["천을귀인"].display in used


def test_gloss_skips_already_used():
    used = set()
    PG.gloss_first_use("대운 cycle", used)
    out2 = PG.gloss_first_use("another 대운 mention", used)
    assert "—" not in out2.split("대운")[1][:5]  # not re-glossed


def test_render_terms_section_tiering():
    used = ["Direct Wealth (正財)", "Major Luck (大運)"]
    assert PG.render_terms_section(used, "sample") == ""
    ess = PG.render_terms_section(used, "essential")
    deep = PG.render_terms_section(used, "deep")
    assert "## What the Terms Mean" in ess
    assert "Direct Wealth" in ess and "Major Luck" in ess
    assert len(deep) >= len(ess)  # deep carries the fuller note


def test_render_terms_section_only_used_terms():
    out = PG.render_terms_section(["Major Luck (大運)"], "deep")
    assert "Major Luck" in out
    assert "Peach Blossom" not in out
```

- [ ] **Step 2: Run it — confirm FAIL**

Run: `python3 -m pytest tests/test_plain_glossary.py -q`
Expected: `ModuleNotFoundError: saju_engine.plain_glossary`

- [ ] **Step 3: Write `src/saju_engine/plain_glossary.py`**

```python
"""Plain-language glosses for Saju jargon in engine reports.

Mirrors `hanja_glossary.py`: a dict plus a first-use annotator. Every `plain`
string is curated from and faithful to the cited `knowledge/` file. The
inline `*(see …)*` citation is stripped at the PDF layer; the gloss text stays.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PlainDef:
    plain: str          # <= ~14 words, lay phrasing
    display: str        # canonical rendering, e.g. "Direct Wealth (正財)"
    source: str         # e.g. "knowledge/05-ten-gods.md"
    note: str = ""      # one extra clarifying sentence, used in deep/skeleton glossary


def _d(plain, display, source, note=""):
    return PlainDef(plain=plain, display=display, source=source, note=note)


# Canonical PlainDefs, then a trigger->PlainDef expansion below.
_TEN_GODS = {
    "비견": _d("a peer or equal — support, solidarity, and rivalry in equal measure",
              "Companion (比肩)", "knowledge/05-ten-gods.md"),
    "겁재": _d("a rival for the same resources — competition in money or love",
              "Robber (劫財)", "knowledge/05-ten-gods.md"),
    "식신": _d("gentle output — talent, making, teaching, slow enjoyable accumulation",
              "Eating God (食神)", "knowledge/05-ten-gods.md"),
    "상관": _d("sharp output — bold expression, creativity, friction with rules and authority",
              "Hurting Officer (傷官)", "knowledge/05-ten-gods.md"),
    "편재": _d("variable money — deals, commissions, windfalls, higher risk and reward",
              "Indirect Wealth (偏財)", "knowledge/05-ten-gods.md"),
    "정재": _d("steady, earned income and everyday resources — salary and savings",
              "Direct Wealth (正財)", "knowledge/05-ten-gods.md"),
    "편관": _d("pressure and demand — deadlines, tough oversight, decisive action under stress",
              "Seven Killings (偏官)", "knowledge/05-ten-gods.md"),
    "정관": _d("conventional authority — career structure, rules, status, institutions",
              "Direct Officer (正官)", "knowledge/05-ten-gods.md"),
    "편인": _d("unconventional learning — intuition, solitary study, restless over-thinking",
              "Indirect Resource (偏印)", "knowledge/05-ten-gods.md"),
    "정인": _d("support and knowledge — education, mentors, care, property, credentials",
              "Direct Resource (正印)", "knowledge/05-ten-gods.md"),
}

_CLASS_TERMS = {
    "비겁": _d("the peers-and-rivals group — how you meet equals and competitors",
              "Companion class (比劫)", "knowledge/05-ten-gods.md"),
    "식상": _d("the output group — how you create, express, and produce",
              "Output class (食傷)", "knowledge/05-ten-gods.md"),
    "재성": _d("the wealth group — how money and resources come and are held",
              "Wealth class (財星)", "knowledge/05-ten-gods.md"),
    "관성": _d("the authority group — how you meet rules, status, and institutions",
              "Authority class (官星)", "knowledge/05-ten-gods.md"),
    "인성": _d("the resource group — support, learning, and what sustains you",
              "Resource class (印星)", "knowledge/05-ten-gods.md"),
}

_YONGSIN = {
    "용신": _d("the element your chart most needs for balance — lean toward it",
              "Favourable Element (用神)", "knowledge/03-five-elements.md",
              "It is the working target for choices about work, place, colour, and timing."),
    "희신": _d("the element that supports the favourable one — a helpful secondary",
              "Supporting Element (喜神)", "knowledge/03-five-elements.md"),
    "기신": _d("the element that unbalances your chart — minimise its influence",
              "Unfavourable Element (忌神)", "knowledge/03-five-elements.md"),
    "한신": _d("a neutral element that mostly drains the favourable one",
              "Draining Element (閒神)", "knowledge/00-glossary.md"),
    "구신": _d("an element that restrains the favourable one",
              "Restricting Element (仇神)", "knowledge/00-glossary.md"),
}

_LUCK = {
    "대운": _d("roughly ten-year life chapters that colour a whole span",
              "Major Luck (大運)", "knowledge/08-luck-pillars.md"),
    "세운": _d("the theme of a single year",
              "Annual Luck (歲運)", "knowledge/08-luck-pillars.md"),
    "월운": _d("the theme of a single month",
              "Monthly Luck (月運)", "knowledge/08-luck-pillars.md"),
    "일운": _d("the theme of a single day",
              "Daily Luck (日運)", "knowledge/08-luck-pillars.md"),
}

# 12운성 stages — plain one-liners from knowledge/06-twelve-stages.md
_STAGES = {
    "장생": _d("a fresh start — early, hopeful, growing", "Birth stage (長生)", "knowledge/06-twelve-stages.md"),
    "목욕": _d("an unsettled, exposed phase — learning through mistakes", "Bath stage (沐浴)", "knowledge/06-twelve-stages.md"),
    "관대": _d("coming into form — gaining competence and standing", "Cap stage (冠帶)", "knowledge/06-twelve-stages.md"),
    "건록": _d("established and productive — steady working strength", "Office stage (建祿)", "knowledge/06-twelve-stages.md"),
    "제왕": _d("peak strength — full power, with the risk of over-reach", "Peak stage (帝旺)", "knowledge/06-twelve-stages.md"),
    "쇠": _d("just past the peak — a gentle decline, wiser and slower", "Decline stage (衰)", "knowledge/06-twelve-stages.md"),
    "병": _d("a low-energy phase — rest and repair matter more", "Illness stage (病)", "knowledge/06-twelve-stages.md"),
    "사": _d("a dormant, minimal phase — little outward force", "Death stage (死)", "knowledge/06-twelve-stages.md"),
    "묘": _d("stored away — kept in reserve, opens when triggered", "Storehouse stage (墓)", "knowledge/06-twelve-stages.md"),
    "절": _d("cut off and empty — a clean break before renewal", "Severance stage (絶)", "knowledge/06-twelve-stages.md"),
    "태": _d("conceived but unseen — potential forming", "Conception stage (胎)", "knowledge/06-twelve-stages.md"),
    "양": _d("nurtured and preparing — sheltered growth before emergence", "Nourish stage (養)", "knowledge/06-twelve-stages.md"),
}

# 신살 stars — from knowledge/07-special-formations.md
_STARS = {
    "도화": _d("charm and magnetism — attractiveness, and sometimes distraction or scandal",
              "Peach Blossom (桃花)", "knowledge/07-special-formations.md"),
    "역마": _d("movement — travel, relocation, changing scenes, a mobile life",
              "Travelling Horse (驛馬)", "knowledge/07-special-formations.md"),
    "화개": _d("solitude and depth — art, scholarship, spirituality, time alone",
              "Canopy (華蓋)", "knowledge/07-special-formations.md"),
    "천을귀인": _d("a protective helper star — timely aid from others in hard moments",
                 "Nobleman (天乙貴人)", "knowledge/07-special-formations.md"),
    "문창귀인": _d("a study-and-writing star — academic and literary aptitude",
                 "Academic Star (文昌貴人)", "knowledge/07-special-formations.md"),
    "양인": _d("a sharp, forceful star — drive and edge, and a risk of excess",
              "Blade (羊刃)", "knowledge/07-special-formations.md"),
    "공망": _d("an 'empty' position — its themes feel deferred or less solid",
              "Void (空亡)", "knowledge/07-special-formations.md"),
    "천덕귀인": _d("a virtue-and-protection star — help arrives through good conduct",
                 "Heavenly Virtue (天德貴人)", "knowledge/07-special-formations.md"),
    "월덕귀인": _d("a monthly virtue-and-protection star",
                 "Monthly Virtue (月德貴人)", "knowledge/07-special-formations.md"),
    "백호": _d("a sudden-event star — accidents or shocks; handle risk deliberately",
              "White Tiger (白虎)", "knowledge/07-special-formations.md"),
    "괴강": _d("an intense all-or-nothing star — strong character, dramatic swings",
              "Kuigang (魁罡)", "knowledge/07-special-formations.md"),
    "원진": _d("a friction star between two branches — quiet resentment, hard-to-name irritation",
              "Resentment (怨嗔)", "knowledge/07-special-formations.md"),
    "귀문관": _d("an over-sensitivity star — vivid inner world, anxiety, acute intuition",
               "Ghost Gate (鬼門關)", "knowledge/07-special-formations.md"),
    "겁살": _d("a loss-and-seizure star — guard against sudden loss",
              "Robbery Star (劫煞)", "knowledge/07-special-formations.md"),
    "재살": _d("a confinement-and-conflict star — legal or bounded-situation risk",
              "Calamity Star (災煞)", "knowledge/07-special-formations.md"),
    "천살": _d("a 'forces beyond control' star — weather, authority, big systems",
              "Heaven Star (天煞)", "knowledge/07-special-formations.md"),
    "지살": _d("a movement-and-relocation star, milder than 역마",
              "Ground Star (地煞)", "knowledge/07-special-formations.md"),
    "월살": _d("a depletion star — dryness, stalling, thin returns for a while",
              "Moon Star (月煞)", "knowledge/07-special-formations.md"),
    "망신": _d("an exposure star — private matters becoming public, embarrassment",
              "Loss-of-Face (亡神)", "knowledge/07-special-formations.md"),
    "장성": _d("a leadership star — command, responsibility, being looked to",
              "General Star (將星)", "knowledge/07-special-formations.md"),
    "반안": _d("a promotion-and-comfort star — steady advancement, saddle secured",
              "Saddle Star (攀鞍)", "knowledge/07-special-formations.md"),
}

_STRUCTURAL = {
    "일간": _d("you — your core self, the reference point for the whole chart",
              "Day Master (日干)", "knowledge/09-interpretation-method.md"),
    "일주": _d("your day pillar — the self and the marriage/partner area",
              "Day Pillar (日柱)", "knowledge/00-glossary.md"),
    "격국": _d("the chart's overall shape — its dominant organising pattern",
              "Chart Structure (格局)", "knowledge/00-glossary.md"),
    "지장간": _d("the hidden stems inside a branch — the undercurrent of that area",
               "Hidden Stems (地藏干)", "knowledge/02-branches.md"),
    "본기": _d("the main hidden stem of a branch — its dominant inner force",
              "Primary hidden stem (本氣)", "knowledge/02-branches.md"),
    "중기": _d("the middle hidden stem of a branch — a secondary inner theme",
              "Middle hidden stem (中氣)", "knowledge/02-branches.md"),
    "여기": _d("the residual hidden stem of a branch — a faint lingering theme",
              "Residual hidden stem (餘氣)", "knowledge/02-branches.md"),
}

_CANON: Dict[str, PlainDef] = {
    **_TEN_GODS, **_CLASS_TERMS, **_YONGSIN, **_LUCK,
    **_STAGES, **_STARS, **_STRUCTURAL,
}

# English display names + "English (漢字)" forms + grid names all resolve to the
# same PlainDef as the Korean key.
_ENGLISH_ALIASES: Dict[str, str] = {
    "Companion": "비견", "Robber": "겁재",
    "Eating God": "식신", "Hurting Officer": "상관", "Output": "식상",
    "Indirect Wealth": "편재", "Direct Wealth": "정재", "Wealth": "재성",
    "Seven Killings": "편관", "Direct Officer": "정관", "Authority": "관성",
    "Indirect Resource": "편인", "Direct Resource": "정인", "Resource": "인성",
    "Favourable Element": "용신", "Favorable Element": "용신",
    "Supporting Element": "희신", "Unfavourable Element": "기신", "Unfavorable Element": "기신",
    "Major Luck": "대운", "Annual Luck": "세운", "Monthly Luck": "월운", "Daily Luck": "일운",
    "Peach Blossom": "도화", "Travelling Horse": "역마", "Nobleman": "천을귀인",
    "Day Master": "일간", "hidden stems": "지장간",
    "Peak": "제왕", "Death": "사", "Bath": "목욕", "Nourish": "양",
    # grid names
    "비견격": "비견", "겁재격": "겁재", "식신격": "식신", "상관격": "상관",
    "편재격": "편재", "정재격": "정재", "편관격": "편관", "정관격": "정관",
    "편인격": "편인", "정인격": "정인",
    "Companion Grid": "비견", "Direct Officer Grid": "정관", "Eating God Grid": "식신",
    "Direct Wealth Grid": "정재",
}

PLAIN_GLOSSARY: Dict[str, PlainDef] = dict(_CANON)
for alias, key in _ENGLISH_ALIASES.items():
    PLAIN_GLOSSARY[alias] = _CANON[key]
# also register the "English (漢字)" display strings as triggers
for pd in set(_CANON.values()):
    PLAIN_GLOSSARY.setdefault(pd.display, pd)


_TRIGGERS = sorted(PLAIN_GLOSSARY, key=len, reverse=True)


def gloss_first_use(text: str, already_used: set) -> str:
    """Append ' — {plain} *(see {source})*' after the first occurrence of each term."""
    for trigger in _TRIGGERS:
        pd = PLAIN_GLOSSARY[trigger]
        if pd.display in already_used:
            continue
        idx = text.find(trigger)
        if idx == -1:
            continue
        after = idx + len(trigger)
        # skip if an em-dash gloss or a parenthetical already follows
        tail = text[after:after + 3].lstrip()
        if tail.startswith("—") or tail.startswith("("):
            # a parenthetical (漢字) may still precede the gloss slot — re-point after it
            close = text.find(")", after)
            if 0 <= close < after + 12:
                after = close + 1
                tail = text[after:after + 3].lstrip()
            if tail.startswith("—"):
                already_used.add(pd.display)
                continue
        insertion = f" — {pd.plain} *(see {pd.source})*"
        text = text[:after] + insertion + text[after:]
        already_used.add(pd.display)
    return text


def collect_used_terms(text: str) -> List[str]:
    seen: List[str] = []
    seen_defs = set()
    # order by first appearance
    hits = []
    for trigger, pd in PLAIN_GLOSSARY.items():
        i = text.find(trigger)
        if i != -1 and id(pd) not in seen_defs:
            hits.append((i, pd))
    for _i, pd in sorted(hits, key=lambda t: t[0]):
        if id(pd) not in seen_defs:
            seen_defs.add(id(pd))
            seen.append(pd.display)
    return seen


_SHORT_TIERS = {"essential", "companion", "spark"}
_FULL_TIERS = {"deep", "reading", "fullmap", "skeleton", "basic", "compat", "compat_deep"}


def render_terms_section(used: List[str], tier: str) -> str:
    if tier == "sample" or not used:
        return ""
    full = tier not in _SHORT_TIERS
    lines = ["## What the Terms Mean", ""]
    by_display = {pd.display: pd for pd in PLAIN_GLOSSARY.values()}
    for display in used:
        pd = by_display.get(display)
        if not pd:
            continue
        entry = f"- **{pd.display}:** {pd.plain}"
        if full and pd.note:
            entry += f" {pd.note}"
        lines.append(entry)
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run the tests — adjust literal expectations, then PASS**

Run: `python3 -m pytest tests/test_plain_glossary.py -q`
Fix any test literal that referenced a placeholder gloss (e.g. the `노블` line) to match the real `PLAIN_GLOSSARY` text. Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/saju_engine/plain_glossary.py tests/test_plain_glossary.py
git commit -m "feat(engine): add plain_glossary (term glosses + tier-scaled glossary)"
```

---

### Task 10: Section-callout fillers in `prose_fillers.py`

**Files:**
- Modify: `src/saju_engine/prose_fillers.py` (add 7 functions)
- Modify: `tests/test_prose_fillers.py`

**Interfaces:**
- Consumes: the existing `ctx` object (`_ReportContext` or dict — `prose_fillers` already supports both via `_ctx_get`), fields: `dm_element`, `favorable`, `verdict`, `strength_label`, `pattern_name`, `chart`.
- Produces: `plain_words_day_master(ctx) -> str`, `plain_words_career(ctx) -> str`, `plain_words_relationships(ctx) -> str`, `plain_words_health(ctx) -> str`, `plain_words_timing(ctx) -> str`, `plain_words_pattern(ctx) -> str`, `plain_words_ten_gods(ctx) -> str`. Each returns a single line `"> **In plain words:** …"` (no trailing newline) or `""`.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_prose_fillers.py` (reuse the file's existing context factory — check its imports/top):

```python
def test_plain_words_fillers_return_blockquote():
    from saju_engine import prose_fillers as PF
    ctx = _make_ctx()  # whatever factory the rest of this file uses
    for fn in (PF.plain_words_day_master, PF.plain_words_career,
               PF.plain_words_relationships, PF.plain_words_health,
               PF.plain_words_timing, PF.plain_words_pattern,
               PF.plain_words_ten_gods):
        out = fn(ctx)
        assert out == "" or out.startswith("> **In plain words:** ")
        assert "[ENGINE DRAFT" not in out
        assert "\n" not in out
```

- [ ] **Step 2: Run it — confirm FAIL**

Run: `python3 -m pytest tests/test_prose_fillers.py::test_plain_words_fillers_return_blockquote -q`

- [ ] **Step 3: Implement the seven functions**

Add to `src/saju_engine/prose_fillers.py`. Each is deterministic, ≤ 2 sentences, derived from the same chart facts the section uses. Pattern:

```python
def _plain(text: str) -> str:
    return f"> **In plain words:** {text}"


def plain_words_day_master(ctx) -> str:
    dm_el = _ctx_get(ctx, "dm_element", "")
    strength = (_ctx_get(ctx, "strength_label", "") or "").lower()
    fav = _ctx_get(ctx, "favorable", "")
    image = {
        "Wood": "a growing tree — you push upward and branch out",
        "Fire": "a flame — you light things up and move fast",
        "Earth": "steady ground — you hold, stabilise, and mediate",
        "Metal": "a refined blade — you cut to the point and value quality",
        "Water": "moving water — you adapt, connect, and go deep",
    }.get(dm_el, "your own distinct type")
    return _plain(
        f"At your core you are {image}. Your chart reads as {strength or 'balanced'}, "
        f"so the rest of this report is about where that helps and where leaning toward "
        f"{fav or 'your favourable element'} keeps you in balance."
    )


def plain_words_career(ctx) -> str:
    cls = _tengod_class_counts(ctx)  # existing helper in this module
    fav = _ctx_get(ctx, "favorable", "")
    # pick the dominant driver
    drivers = {
        "Wealth": "earning by owning and growing resources — business, sales, deals",
        "Output": "earning by making and expressing — creating, teaching, building",
        "Authority": "earning inside structure — institutions, management, licensed roles",
        "Resource": "earning through knowledge — research, advice, credentialed practice",
        "Companion": "earning alongside peers — teams, partnerships, independent practice",
    }
    top = max(drivers, key=lambda k: cls.get(k, 0)) if cls else "Output"
    return _plain(
        f"Your chart leans toward {drivers[top]}. Fields and decades that carry "
        f"{fav or 'your favourable element'} give the cleanest results; the timing tables show when."
    )
# ... plain_words_relationships / _health / _timing / _pattern / _ten_gods similarly,
#     each grounded in: spouse-palace ten-god; lightest vs heaviest element + organ;
#     current 대운 favourability; the pattern_name meaning; the dominant ten-god class.
```

Implement all seven with real chart-derived logic (no stubs). For `plain_words_pattern`, map `ctx.pattern_name` through a small dict of plain meanings (reuse `prose_fillers._GRID_PLAIN` if it exists — line ~1082 has `"비견격": "self-reliance and peer dynamics …"`; extend that dict rather than duplicating). Return `""` when the needed fact is absent (e.g. no spouse palace, "Standard chart" pattern).

- [ ] **Step 4: Run — PASS**

Run: `python3 -m pytest tests/test_prose_fillers.py -q`

- [ ] **Step 5: Commit**

```bash
git add src/saju_engine/prose_fillers.py tests/test_prose_fillers.py
git commit -m "feat(engine): add 'In plain words' section-callout fillers"
```

---

### Task 11: Wire Track A into `premium_report.py`

**Files:**
- Modify: `src/saju_engine/premium_report.py` (import; append callouts inside section builders; run `gloss_first_use`; append `render_terms_section`)
- Modify: `tests/test_premium_report.py`

**Interfaces:**
- Consumes: `plain_glossary.gloss_first_use`, `collect_used_terms`, `render_terms_section`; `prose_fillers.plain_words_*`.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_premium_report.py`:

```python
def test_premium_deep_has_plain_words_callouts_and_glossary():
    chart = _sample_chart()
    r = generate_premium_report(chart, tier="deep", generation_date="2026-06-21")
    assert r.count("> **In plain words:**") >= 4
    gi = r.index("## What the Terms Mean")
    ci = r.index("## Closing Note")
    assert gi > ci, "glossary must come after the Closing Note"
    assert "[ENGINE DRAFT" not in r
    # an inline gloss landed on a ten-god
    assert "— steady, earned income" in r or "— variable money" in r


def test_premium_essential_glossary_is_short_and_present():
    r = generate_premium_report(_sample_chart(), tier="essential")
    assert "## What the Terms Mean" in r


def test_premium_sample_has_glosses_but_no_glossary_or_callouts():
    r = generate_premium_report(_sample_chart(), tier="sample")
    assert "## What the Terms Mean" not in r
    assert "> **In plain words:**" not in r
```

- [ ] **Step 2: Run — confirm FAIL**

Run: `python3 -m pytest tests/test_premium_report.py -k plain_words or glossary or sample_has_glosses -q`

- [ ] **Step 3: Implement**

In `src/saju_engine/premium_report.py`:

1. Import: `from .plain_glossary import gloss_first_use, collect_used_terms, render_terms_section` and `from . import prose_fillers as PF` (PF is already imported).
2. At the end of each target section builder, before its `return lines`, append the callout (only when the section is non-empty and not `sample`):
   - `_section_day_master_portrait`: `_append_callout(lines, PF.plain_words_day_master(ctx), ctx)`
   - `_section_career_wealth`: `PF.plain_words_career`
   - `_section_relationships`: `PF.plain_words_relationships`
   - `_section_health_vitality` and `_health_deep_dive`: `PF.plain_words_health` (only once — put it on `_section_health_vitality`; skip if that section is absent for the tier and add to `_health_deep_dive` instead)
   - `_section_timing`: `PF.plain_words_timing`
   - `_section_natal_patterns`: `PF.plain_words_pattern` — **note** this section already emits `### What This Means in Plain Language`; put the callout at the very end of the section, and keep the existing subsection (do not remove it)
   - the Ten-God Distribution table (inside `_section_day_master_portrait` around line 432): `PF.plain_words_ten_gods`
   Helper:
   ```python
   def _append_callout(lines: list, text: str, ctx: "_ReportContext") -> None:
       if ctx.tier == "sample" or not text:
           return
       if lines and lines[-1] != "":
           lines.append("")
       lines.append(text)
       lines.append("")
   ```
3. In `generate_premium_report`, replace the final block:
   ```python
   used_terms: set = set()
   annotated = [inject_hanja("\n".join(s), used_terms) for s in sections]
   doc = "\n".join(annotated)
   gloss_used: set = set()
   doc = gloss_first_use(doc, gloss_used)
   terms = render_terms_section(collect_used_terms(doc), tier)
   if terms:
       doc = doc.rstrip() + "\n\n" + terms
   return doc
   ```

- [ ] **Step 4: Run — PASS + full suite**

Run: `python3 -m pytest tests/test_premium_report.py -q` then `python3 -m pytest -q`
Fix any existing test that asserted exact section ordering / trailing content and now sees the glossary (update it to expect the glossary last).

- [ ] **Step 5: Commit**

```bash
git add src/saju_engine/premium_report.py tests/test_premium_report.py
git commit -m "feat(engine): plain-language layer in premium reports (glosses + callouts + glossary)"
```

---

### Task 12: Wire Track A into `skeleton.py`

**Files:**
- Modify: `src/saju_engine/prose_scaffold.py` (add `generate_plain_words(chart) -> Dict[str, str]`)
- Modify: `src/saju_engine/skeleton.py` (import; append callouts to scaffold sections 3–7; run `gloss_first_use`; append glossary)
- Modify: `tests/test_skeleton.py`, `tests/test_prose_scaffold.py`

**Interfaces:**
- Produces: `prose_scaffold.generate_plain_words(chart)` → keys `personality`, `career_wealth`, `relationships`, `health`, `current_time_themes`, each a `"> **In plain words:** …"` line or `""`.

- [ ] **Step 1: Write the failing tests**

`tests/test_prose_scaffold.py`:
```python
def test_generate_plain_words_keys_and_format():
    from saju_engine.engine import compute_chart
    from saju_engine.prose_scaffold import generate_plain_words
    chart = compute_chart(name="T", gender="M", year=1991, month=10, day=3,
                          hour=23, minute=45, longitude=79.19, utc_offset=5.5,
                          use_solar_time=True, convention="korean")
    pw = generate_plain_words(chart)
    assert set(pw) == {"personality", "career_wealth", "relationships", "health", "current_time_themes"}
    for v in pw.values():
        assert v == "" or v.startswith("> **In plain words:** ")
```

`tests/test_skeleton.py`:
```python
def test_skeleton_has_glossary_and_glosses():
    from saju_engine.engine import compute_chart
    from saju_engine.skeleton import generate_skeleton
    chart = compute_chart(name="T", gender="M", year=1991, month=10, day=3,
                          hour=23, minute=45, longitude=79.19, utc_offset=5.5,
                          use_solar_time=True, convention="korean")
    s = generate_skeleton(chart, reference_year=2026)
    assert "## What the Terms Mean" in s
    assert "> **In plain words:**" in s
```

- [ ] **Step 2: Run — confirm FAIL**

- [ ] **Step 3: Implement**

- `prose_scaffold.generate_plain_words`: reuse this module's existing `_TENGOD_CLASS`, organ map, and `generate_prose_scaffold` internals to produce the five lines (mirror `prose_fillers.plain_words_*` logic but off the scaffold's own context). No stubs.
- `skeleton.py`:
  - `from .plain_glossary import gloss_first_use, collect_used_terms, render_terms_section`
  - `from .prose_scaffold import generate_plain_words` (alongside the existing `generate_prose_scaffold` import)
  - when `include_prose_scaffold`, after each of scaffold sections 3–7's paragraph, append the matching `plain_words` line + `""` (guard `if pw["..."]:`)
  - at the very end of `generate_skeleton`, before `return "\n".join(lines)`:
    ```python
    doc = "\n".join(lines)
    doc = gloss_first_use(doc, set())
    terms = render_terms_section(collect_used_terms(doc), "skeleton")
    if terms:
        doc = doc.rstrip() + "\n\n" + terms
    return doc
    ```

- [ ] **Step 4: Run — PASS + full suite**

Run: `python3 -m pytest tests/test_skeleton.py tests/test_prose_scaffold.py -q` then `python3 -m pytest -q`

- [ ] **Step 5: Commit**

```bash
git add src/saju_engine/prose_scaffold.py src/saju_engine/skeleton.py tests/test_skeleton.py tests/test_prose_scaffold.py
git commit -m "feat(engine): plain-language layer in the skeleton output"
```

---

### Task 13: Wire Track A into `compat_report.py`

**Files:**
- Modify: `src/saju_engine/compat_report.py` (add 3 `_plain_words_*` helpers; append callouts; run `gloss_first_use`; append glossary)
- Modify: the compat report test file (`tests/test_compat_report.py` or wherever `generate_compat_report` is tested — `grep -rl generate_compat_report tests`)

**Interfaces:**
- Consumes: `CompatReport` (`report`), `chart_a`, `chart_b`.

- [ ] **Step 1: Write the failing test**

Add to the compat report test file:
```python
def test_compat_report_has_plain_words_and_glossary():
    # reuse the file's existing two-chart fixture
    md_basic = generate_compat_report(chart_a, chart_b, "A", "B", tier="basic")
    md_deep = generate_compat_report(chart_a, chart_b, "A", "B", tier="deep")
    for md in (md_basic, md_deep):
        assert "> **In plain words:**" in md
        assert "## What the Terms Mean" in md
        gi = md.index("## What the Terms Mean")
        ci = md.index("## Closing Note")
        assert gi > ci
```

- [ ] **Step 2: Run — confirm FAIL**

- [ ] **Step 3: Implement**

- Add `_plain_words_verdict(report)`, `_plain_words_daymaster_cross(report)`, `_plain_words_timing(report)` — each returns `"> **In plain words:** …"` grounded in `report.total`, `report.band`, the day-branch sub-system verdict, and the timing overlay.
- In `_basic_report_lines` / `_deep_report_lines`, append the verdict callout after the score/verdict block, the cross callout after the Day Master cross section, and (deep) the timing callout after the couple-overlay section.
- In `generate_compat_report`, after `md = "\n".join(lines).rstrip() + "\n"`:
  ```python
  from .plain_glossary import gloss_first_use, collect_used_terms, render_terms_section
  md = gloss_first_use(md, set())
  terms = render_terms_section(collect_used_terms(md), "compat" if tier != "deep" else "compat_deep")
  if terms:
      md = md.rstrip() + "\n\n" + terms + "\n"
  return md
  ```
  (`compat` → short, `compat_deep` → full, per `plain_glossary._SHORT_TIERS` / `_FULL_TIERS`.)

- [ ] **Step 4: Run — PASS + full suite**

Run: `python3 -m pytest -q`

- [ ] **Step 5: Commit**

```bash
git add src/saju_engine/compat_report.py tests/
git commit -m "feat(engine): plain-language layer in compatibility reports"
```

---

### Task 14: PDF-layer safety

**Files:**
- Modify: `src/saju_html/__init__.py` (verify `strip_source_citations` / `strip_engine_drafts` / `_strip_sources_section` leave callouts + glossary intact, only removing `*(see …)*`)
- Modify: `src/saju_html/md_to_saju_pdf.py` (add any Korean/Hanja term newly reaching the PDF via a gloss/glossary to the translation maps)
- Modify: the `src/saju_html` test file(s) — `grep -rl strip_source_citations tests`

- [ ] **Step 1: Write the failing test**

Add to the saju_html strip test file:
```python
def test_strip_keeps_plain_words_callout_and_glossary():
    from saju_html import strip_source_citations, strip_engine_drafts
    md = (
        "> **In plain words:** steady earning suits you *(see knowledge/13-wealth-and-business.md)*.\n\n"
        "## What the Terms Mean\n\n"
        "- **Direct Wealth (正財):** steady, earned income *(see knowledge/05-ten-gods.md)*\n"
    )
    out = strip_engine_drafts(strip_source_citations(md))
    assert "> **In plain words:** steady earning suits you." in out
    assert "## What the Terms Mean" in out
    assert "Direct Wealth" in out
    assert "see knowledge/" not in out
```

- [ ] **Step 2: Run — confirm FAIL or PASS**

Run: `python3 -m pytest <that file> -q`
If it already passes, the strippers are safe — keep the test as a regression and skip Step 3's `__init__.py` edits.

- [ ] **Step 3: Adjust strippers only if needed**

If `strip_source_citations` leaves a dangling `" ."` or double space after removing the citation, tighten `_SOURCE_CITATION_RE` handling to also swallow a preceding space. Do **not** broaden any regex to match `In plain words` or `## What the Terms Mean`.

- [ ] **Step 4: Build a real PDF and grep it**

Run:
```bash
PYTHONPATH=src python3 -m saju_engine --date 1993-12-11 --time 02:45 --gender F --city "Chennai" --format premium --tier deep --output-file /tmp/pl-deep.md
python3 src/saju_html/md_to_saju_pdf.py --input /tmp/pl-deep.md --output /tmp/pl-deep.pdf --title T --client T --dob T --day-master T
python3 - <<'EOF'
import subprocess
t = subprocess.run(["pdftotext","/tmp/pl-deep.pdf","-"],capture_output=True,text=True).stdout
assert "see knowledge/" not in t, "citation leaked"
assert "In plain words" in t
assert "What the Terms Mean" in t
print("ok")
EOF
```
Expected: `ok`. Add any missing translation term to `md_to_saju_pdf.py` maps and rebuild until clean.

- [ ] **Step 5: Commit**

```bash
git add src/saju_html/ tests/
git commit -m "test(pdf): plain-language callouts + glossary survive citation stripping"
```

---

### Task 15: `combine_candidate_report.py` — keep the glossary last

**Files:**
- Modify: `src/saju_html/combine_candidate_report.py` (`_extract_closing_note` / `_strip_closing_note` / `combine_report`)
- Modify: `tests/test_combine_candidate_report.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_combine_candidate_report.py`:
```python
def test_combined_report_glossary_follows_moved_closing_note(tmp_path):
    # build a minimal base report with Closing Note then a glossary, combine, assert order
    base = (
        "# X\n\n## Chart at a Glance\n\nstuff\n\n"
        "## Closing Note\n\nfinal words\n\n"
        "## What the Terms Mean\n\n- **Major Luck (大運):** ten-year chapters\n"
    )
    # ... write base + one topic file, run combine_report, read output ...
    out = combined_text
    assert out.index("## What the Terms Mean") > out.index("## Closing Note")
    assert out.rstrip().endswith("ten-year chapters")
```

- [ ] **Step 2: Run — confirm FAIL**

(`_strip_closing_note`'s `re.search(r"\n##\s+Closing Note\b.*", ..., re.DOTALL)` currently eats the glossary too, so it vanishes.)

- [ ] **Step 3: Implement**

In `combine_candidate_report.py`:
- Add `_extract_terms_section(text) -> tuple[str, str]` mirroring `_extract_closing_note` but for `## What the Terms Mean` (heading to EOF).
- In `combine_report`: extract the terms section from the base **before** extracting the Closing Note; strip it from every topic file too; re-append it as the very last block, after the moved Closing Note.
- Update `_strip_closing_note` so its `.*` stops at a following `## What the Terms Mean` (change to `r"\n##\s+Closing Note\b[\s\S]*?(?=\n## What the Terms Mean|\Z)"`).

- [ ] **Step 4: Run — PASS + full suite**

Run: `python3 -m pytest -q`

- [ ] **Step 5: Commit**

```bash
git add src/saju_html/combine_candidate_report.py tests/test_combine_candidate_report.py
git commit -m "fix(pdf): keep 'What the Terms Mean' after the moved Closing Note in combined reports"
```

---

### Task 16: Regenerate demo & candidate outputs

**Files:**
- Regenerate: `candidates_horoscope/reports/rm/rm-sample.md` + `.pdf`, `rm-essential.md` + `-essential-report.pdf`, `rm-report.md` + `.pdf`
- Regenerate: `apps/landing-page/public/demo-rm-sample.pdf`, `demo-rm-essential.pdf`, `demo-rm-deep.pdf` (same source, per `candidates_horoscope/README.md`)
- Spot-check (do not necessarily regenerate): `vishnu-priya`, `mahesh`
- No test file changes

- [ ] **Step 1: Regenerate the RM demo set**

Use the exact commands recorded in `candidates_horoscope/README.md` / the RM section (tier flags `sample` / `essential` / `deep`). Regenerate `.md` then `.pdf` for each.

- [ ] **Step 2: Leak-check every regenerated PDF**

```bash
for p in candidates_horoscope/reports/rm/*.pdf apps/landing-page/public/demo-rm-*.pdf; do
  echo "== $p"; pdftotext "$p" - | grep -c "see knowledge/" || true
done
```
Expected: `0` for every file. Also grep for `[ENGINE DRAFT` → 0.

- [ ] **Step 3: Eyeball one report**

Open `candidates_horoscope/reports/rm/rm-report.md`: confirm each core section ends with one `> **In plain words:**` line, the `## What the Terms Mean` appendix is last and lists only terms the report used, and inline glosses read naturally (`Direct Wealth (正財) — steady, earned income …`).

- [ ] **Step 4: Full suite + landing build sanity**

Run: `python3 -m pytest -q` (expect ~630+ green)
Run: `cd apps/landing-page && npm run build` (the demo PDFs are static assets; build must still pass)

- [ ] **Step 5: Commit**

```bash
git add candidates_horoscope/reports/rm/ apps/landing-page/public/demo-rm-*.pdf
git commit -m "chore: regenerate RM demo reports with the plain-language layer"
```

---

## Self-Review

**Spec coverage:**
- Track B files 12–16 → Tasks 1–5 ✓; method/glossary/CLAUDE/skill wiring → Task 6 ✓; re-ground `report_data` tables → Task 7 ✓; prose reconciliation → Task 8 ✓.
- Track A module → Task 9 ✓; section callouts → Task 10 ✓; premium wiring → Task 11 ✓; skeleton → Task 12 ✓; compat → Task 13 ✓; PDF safety → Task 14 ✓; combine-script fix → Task 15 ✓; regeneration → Task 16 ✓.
- Spec §5 tests: `test_knowledge_grounding.py` (Task 7), `test_plain_glossary.py` (Task 9), premium/skeleton/compat/combine/pdf test extensions (Tasks 11–15) ✓.
- Deferred (`knowledge/17`) — correctly out of plan ✓.

**Placeholder scan:** the `plain_glossary.py` body is given in full; every knowledge file has a section-by-section content spec with the actual tables/data that must appear and the citations; every task ends with a runnable command + expected result. The `prose_fillers.plain_words_*` functions show two full implementations and specify the remaining five by their exact grounding facts — acceptable because the pattern is shown and each is a 3–5 line deterministic function.

**Type consistency:** `gloss_first_use(text, already_used: set)`, `collect_used_terms(text) -> list[str]`, `render_terms_section(used: list[str], tier: str) -> str` — used identically in Tasks 11/12/13. `PlainDef(plain, display, source, note="")` — constructed only via `_d(...)` and read via `.plain` / `.display` / `.source` / `.note`. Callout fillers all return `str` starting `"> **In plain words:** "` or `""` — asserted the same way in Tasks 10/11/12/13.

**Known soft spots to watch during execution:**
- The `gloss_first_use` parenthetical-skip logic (Task 9 Step 3) is the trickiest code — the Task 9 tests target it; add cases if a real report shows a double gloss.
- `collect_used_terms` uses `text.find` per trigger (O(triggers × len)); fine for report-sized strings, don't "optimise" into a regex that breaks longest-match.
- If `tests/test_prose_fillers.py` has no reusable context factory, Task 8/10 first add a small `_make_ctx()` helper near the top of that file.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-07-better-reports.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
