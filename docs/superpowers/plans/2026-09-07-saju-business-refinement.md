# Saju Business Refinement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the Saju repo's product, pricing, positioning, documentation, and three client-facing engine defects with a USD / English-speaking-global go-to-market, and record the analysis with honest, sourced numbers.

**Architecture:** Two new markdown deliverables (research writeup + master execution doc) lock the facts; three narrow engine fixes (G1 review-note leak, G2 per-pillar template, G3 용신 single-source-of-truth) land with regression tests; the Next.js landing page's data + copy move ₹→USD and India→global; then the other seven `.md` files' strategy sections are rewritten to point at the finished state.

**Tech Stack:** Python 3.10+ / pytest (engine), Next.js 15 / TypeScript / Vitest (landing page), Markdown (docs).

**Design spec:** `docs/superpowers/specs/2026-09-07-saju-business-refinement-design.md` — read it first; this plan implements it.

## Global Constraints

- **Currency:** USD everywhere in client-facing and strategy content. ₹ appears only when explicitly describing the *old* India pricing as history.
- **Canonical positioning line (verbatim):** "The Saju engine Korean apps are built on — read in clear English by a human, with the classical texts cited. Not a Korean master; an accurate engine and an honest interpreter."
- **Primary market:** English-speaking global. India = Phase-2 PPP experiment only; no India content/funnel work.
- **Every market number** in D1/D2 carries a confidence flag `[H]`/`[M]`/`[L]` and a source.
- **No claim** exceeds what a cited source or the repo supports. Author-estimated probabilities are labelled as such.
- **USD pricing ladder (launch prices):** Hook $0 · Essential Natal $9 intro→$19 · Compatibility Snapshot $24 · Deep Destiny Natal $55 · Deep Compatibility $45 · Topic Add-on $19 · Premium Bundle $89 · Cosmic Companion $9/mo or $79/yr (off primary grid).
- **Tests:** `python3 -m pytest` from repo root must stay green (baseline 568) and grow. `cd apps/landing-page && npm run build && npm test` must stay green (baseline 74).
- **Git:** repo root is NOT a git repo — no root-level commits. `apps/landing-page/` has its own git; commit there. Engine/docs changes are not version-controlled; rely on tests.
- **Testimonials:** do NOT edit the testimonial data; add a warning comment only (spec §6.7).

---

### Task 1: Market research writeup (D2)

**Files:**
- Create: `docs/market-research-2026-09.md`

**Interfaces:**
- Produces: the sourced fact base that Task 2 (`improvements_issues.md`) and Tasks 9's `.md` rewrites cite.

- [ ] **Step 1:** Write `docs/market-research-2026-09.md` with sections mirroring spec §3.1–3.7:
  demand (Pew 30% / shallow-engagement breakdown; 225M Hallyu; K-occult wave + caveat),
  market-size (₩1.4T InnoForest vs stale 2018 $3.7B; astrology-app $1.3–16B unusable),
  competition (Cheok Cheok direct-verified prices; saju.com English launch + PR-syndication caveat;
  mid/premium bands; Fiverr), channel (Starcrossed full caveats; organic-short-form pattern;
  conversion 4.0%/2.35% cross-industry, plan 1–2%; Etsy <$100/mo), API/MCP (commoditized APIs;
  <5% of 12k servers monetize), operations (30–90 min/report; $1–3K/mo ceiling; Lemon Squeezy/Paddle
  MoR from India; <$50/mo fixed cost). Each claim: query used + source URL + `[H]/[M]/[L]` + caveat.
- [ ] **Step 2:** Add a "How this compares to the research report" subsection reproducing the report's
  §6 verification verdicts and marking agree / extend / downgrade.
- [ ] **Step 3:** Add a grouped "Sources" list with all URLs.
- [ ] **Step 4:** Self-check: no number without a flag; no flag without a source.

Source URLs to cite (collected 2026-09-07):
- Pew: https://www.pewresearch.org/religion/2025/05/21/3-in-10-americans-consult-astrology-tarot-cards-or-fortune-tellers/
- Korea Foundation 225M: https://www.korea.net/NewsFocus/Society/view?articleId=248349
- InnoForest / market-size dispute: https://marketsize.net/fortune-telling-south-korea/ , https://www.taipeitimes.com/News/biz/archives/2026/08/16/2003862555
- Cheok Cheok: https://sajuplus.com/en/home (direct fetch: $9.99 / $8.99 / $7.99 / $2.99)
- saju.com English: https://www.wingerdaily.com/2026/03/30/saju-com-korea-top-ranked-fortune-service-with-5-million-users-launches-in-english/
- Astrology-app market range: https://www.researchandmarkets.com/reports/6090017/astrology-app-market-report , https://www.thebusinessresearchcompany.com/report/astrology-app-global-market-report
- Starcrossed: https://www.socialgrowthengineers.com/this-random-girl-built-a-70k-mrr-astrology-app-in-90-days , https://medium.com/@thesaucedepot/this-random-girl-built-an-astrology-app-to-70-000-mrr-in-90-days-cafb41661bbe
- Conversion benchmarks: https://landerlab.io/blog/landing-page-conversion-rate
- Astrology API pricing: https://vedika.io/blog/astrology-api-pricing-real-costs-2026 , https://roxyapi.com/blogs/best-astrology-apis-2026-developer-comparison
- MCP monetization: https://mcp-marketplace.io/blog/state-of-mcp-monetization-2026 , https://mcpize.com/blog/make-money-with-mcp
- AstroTalk FY25: https://entrackr.com/news/astrotalks-e-commerce-vertical-posts-rs-140-cr-revenue-in-2025-hits-rs-200-cr-arr-11004745 , https://www.outlookbusiness.com/news/astrotalk-reports-85-revenue-growth-in-fy25-as-tier-i-cities-boost-platform-activity
- K-occult wave: https://www.koreajoongangdaily.com/entertainment/k-shamanism-reads-its-own-fate-finding-overseas-success/12557063 , https://www.koreatimes.co.kr/entertainment/shows-dramas/20260304/spirits-survival-shows-and-saju-koreas-unlikely-shamanism-entertainment-boom
- MoR from India: https://www.playto.so/blogs/paddle-vs-lemon-squeezy-vs-playto-pay-india , https://www.lemonsqueezy.com/blog/2026-update
- Fiverr: https://www.fiverr.com/tom1004/read-your-destiny-with-authentic-korean-saju-fortune-telling

---

### Task 2: Master execution doc (D1)

**Files:**
- Create: `improvements_issues.md` (repo root)

**Interfaces:**
- Consumes: `docs/market-research-2026-09.md` (Task 1).
- Produces: the issue IDs (LP1–LPn, G1–G6, A1–A5) and prioritized backlog that Task 9's `tasks.md` edit references.

- [ ] **Step 1:** Write `improvements_issues.md` following spec §6.1 structure exactly (sections 0–12).
- [ ] **Step 2:** §0 reality check: side-income framing, the spec §3.7 outcome-distribution table
  (label probabilities "author estimate, not sourced"), the one defensible wedge.
- [ ] **Step 3:** §1 condensed verified-facts table (link to D2 for detail). §2 corrections to the
  research report (5 items from spec §3).
- [ ] **Step 4:** §3 strategic position (persona + canonical positioning line + authenticity
  guardrails). §4 the USD ladder (spec §4.2) + the pricing-increase risk note.
- [ ] **Step 5:** §5 landing-page issues table (LP1–LP10 from spec §6.1, with file + severity + fix).
  §6 product/report issues (G1–G6). §7 engine/architecture (A1–A5).
- [ ] **Step 6:** §8 marketing plan (spec §4.4 expanded). §9 execution plan (spec §4.5 expanded with
  gates). §10 API/MCP parked + revisit trigger (spec §4.3). §11 open risks (spec §9 R1–R5).
- [ ] **Step 7:** §12 single consolidated prioritized backlog P0→P3 with rough effort per item.
- [ ] **Step 8:** Self-check against spec §5 deliverable table — every D-item and issue-ID present.

---

### Task 3: G1 — review-note blockquotes must never reach client output

**Files:**
- Modify: `src/saju_engine/premium_report.py` (call sites ~line 294, ~341, ~454)
- Modify: `src/saju_html/__init__.py` (add belt-and-braces stripper near `_SOURCE_PATH_RE` ~line 291)
- Test: `tests/test_premium_report.py`, `tests/test_html_pdf.py`

**Interfaces:**
- Produces: `premium_report._reviewer_note(ctx, text: str) -> list[str]` — returns `[]` for client
  tiers (`sample`, `essential`, `deep`, `spark`, `reading`, `fullmap`), else `[f">*{text}*", ""]`.

- [ ] **Step 1: Write the failing test** in `tests/test_premium_report.py`:

```python
import pytest
from saju_engine.engine import compute_chart
from saju_engine.premium_report import generate_premium_report

_BANNED = ("Chart-derived", "verify against", "verify archetype", "Engine note:", "refine each entry")

@pytest.fixture(scope="module")
def _chart():
    return compute_chart(date="1993-12-11", time="02:45", city="Pallipat", gender="F")

@pytest.mark.parametrize("tier", ["sample", "essential", "deep"])
def test_no_reviewer_notes_in_client_markdown(_chart, tier):
    md = generate_premium_report(_chart, tier=tier)
    for bad in _BANNED:
        assert bad not in md, f"reviewer note {bad!r} leaked into {tier} report"
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python3 -m pytest tests/test_premium_report.py::test_no_reviewer_notes_in_client_markdown -v`
Expected: FAIL (at least `essential`/`deep` contain "Chart-derived").

- [ ] **Step 3: Implement.** In `premium_report.py` add near the top of the module:

```python
_CLIENT_TIERS = {"sample", "essential", "deep", "spark", "reading", "fullmap"}

def _reviewer_note(ctx, text):
    """Blockquote review note — emitted only for internal drafts, never client tiers."""
    if getattr(ctx, "tier", None) in _CLIENT_TIERS:
        return []
    return [f">*{text}*", ""]
```

Replace each hard-coded review-note blockquote (the three `">*Chart-derived …*"` / `">*… verify …*"`
list-appends near lines 294, 341, 454) with `lines += _reviewer_note(ctx, "<the text without >* *>")`.
Confirm `_ReportContext` carries `tier` (it is passed to `generate_premium_report`); if the per-pillar
helper `_four_pillars_one_by_one` lacks `ctx`, it already receives `ctx` — use it.

- [ ] **Step 4:** In `src/saju_html/__init__.py`, after `_SOURCE_PATH_RE` add:

```python
# Any stray reviewer-note blockquote left in a hand-written .md (belt-and-braces;
# the engine no longer emits these for client tiers — see premium_report._reviewer_note).
_REVIEW_NOTE_RE = re.compile(
    r"^\s*>\s*\*(?:Chart-derived|Engine note|Heuristic only)[^\n]*\*\s*$", re.MULTILINE
)
```

Apply `_REVIEW_NOTE_RE.sub("", text)` in the same function where `_SOURCE_CITATION_RE` /
`_SOURCE_PATH_RE` are applied (search for `_SOURCE_PATH_RE.sub`).

- [ ] **Step 5:** Add an HTML-render test in `tests/test_html_pdf.py` (follow that file's existing
  pattern — it already renders markdown to HTML):

```python
def test_review_note_stripped_from_rendered_html(tmp_path):
    from saju_html import _strip_source_citations  # use whatever the module's public strip fn is
    src = "Intro line.\n\n>*Chart-derived first draft — verify against the relevant knowledge files.*\n\nBody."
    out = _strip_source_citations(src)
    assert "Chart-derived" not in out
```

(If the strip function has a different name, grep `def _strip` in `src/saju_html/__init__.py` and use it.)

- [ ] **Step 6: Run tests**

Run: `python3 -m pytest tests/test_premium_report.py tests/test_html_pdf.py -v`
Expected: PASS (new + existing).

---

### Task 4: G2 — per-pillar template grammar + repeated filler

**Files:**
- Modify: `src/saju_engine/premium_report.py::_four_pillars_one_by_one` (~lines 329–378)
- Test: `tests/test_premium_report.py`

**Interfaces:**
- Consumes: nothing new. Produces: no new symbols (internal helper behavior change only).

- [ ] **Step 1: Write the failing test:**

```python
def test_per_pillar_walk_is_grammatical_and_distinct(_chart):
    md = generate_premium_report(_chart, tier="essential")
    assert "**. sits as **" not in md
    assert ". sits as " not in md
    # extract the four "#### <label> — ..." paragraphs and their following prose line
    import re
    blocks = re.findall(r"^#### .+?\n\n(.+)$", md, re.MULTILINE)
    walk = [b for b in blocks]
    assert len(walk) >= 4
    # strip pillar-specific tokens, then the remaining templates must not be all identical
    norm = {re.sub(r"\*\*[^*]+\*\*", "X", b) for b in walk[:4]}
    assert len(norm) > 1, "all four per-pillar paragraphs are the same template"
```

- [ ] **Step 2: Run — expect FAIL** (`". sits as "` present).

Run: `python3 -m pytest tests/test_premium_report.py::test_per_pillar_walk_is_grammatical_and_distinct -v`

- [ ] **Step 3: Implement.** Rewrite the `sentences >= 2` block of `_four_pillars_one_by_one`:

```python
if sentences >= 2:
    first = (
        f"The {p.combined} pillar pairs the **{p.stem}** stem ({stem_en}) with the "
        f"**{p.branch}** branch, together shaping **{area}**."
    )
    if tengod:
        first += (
            f" Its stem reads as **{tengod}** relative to your Day Master, so {area} "
            f"tends to carry that dynamic."
        )
    lines.append(first)
    lines.append("")
    lines.append(
        f"The **{branch_elem}** branch acts as the container for this area while the "
        f"stem supplies its drive; read the two together when weighing how {p.position}-pillar "
        f"matters unfold."
    )
    lines.append("")
```

Remove the old `tengod_phrase` variable and the old third sentence. Keep the `sentences >= 4`
(Deep) block but change its opening line so it does not restate `first`; apply the same
"no bare-space clause" rule if it uses `tengod`.

- [ ] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_premium_report.py -v`
Expected: PASS.

---

### Task 5: G3 — 용신 single source of truth + provenance

**Files:**
- Create: `src/saju_engine/yongsin.py`
- Modify: `src/saju_engine/premium_report.py` (Quick Reference block ~line 264; Sources & Limits)
- Modify: `src/saju_engine/compat_report.py` (~line 75; `generate_compat_report` favorable-element display)
- Test: `tests/test_yongsin_consistency.py` (new)

**Interfaces:**
- Produces:
  ```python
  # src/saju_engine/yongsin.py
  from dataclasses import dataclass
  @dataclass(frozen=True)
  class FavorableElement:
      element: str          # "Wood"|"Fire"|"Earth"|"Metal"|"Water"
      method: str           # "strong-dm-drain"|"weak-dm-support"|"balanced-heuristic"|"reader-confirmed"
      confidence: str       # "heuristic"|"reader-confirmed"
      note: str             # client-safe provenance sentence
  def favorable_element(chart, override: str | None = None) -> FavorableElement: ...
  ```

- [ ] **Step 1: Write the failing test** `tests/test_yongsin_consistency.py`:

```python
import pytest
from saju_engine.engine import compute_chart
from saju_engine.yongsin import favorable_element, FavorableElement
from saju_engine.premium_report import generate_premium_report
from saju_engine.compat_report import generate_compat_report

CANDIDATES = [
    dict(date="1993-12-11", time="02:45", city="Pallipat", gender="F"),
    dict(date="1988-02-01", time="09:20", city="Chennai", gender="M"),
    dict(date="1975-06-15", time="18:05", city="Seoul", gender="M"),
]

@pytest.mark.parametrize("kw", CANDIDATES)
def test_resolver_shape(kw):
    fe = favorable_element(compute_chart(**kw))
    assert isinstance(fe, FavorableElement)
    assert fe.element in {"Wood", "Fire", "Earth", "Metal", "Water"}
    assert fe.method in {"strong-dm-drain", "weak-dm-support", "balanced-heuristic", "reader-confirmed"}
    assert fe.note

@pytest.mark.parametrize("kw", CANDIDATES)
def test_natal_and_compat_agree(kw):
    chart = compute_chart(**kw)
    other = compute_chart(**CANDIDATES[0]) if kw is not CANDIDATES[0] else compute_chart(**CANDIDATES[1])
    fe = favorable_element(chart).element
    natal_md = generate_premium_report(chart, tier="deep")
    assert f"Favorable Element:** {fe}" in natal_md or f"Favorable element (용신):** {fe}" in natal_md
    compat_md = generate_compat_report(chart, other, "A", "B", tier="deep")
    # the partner-A snapshot 용신 must equal the resolver value
    assert fe in compat_md

def test_override_flips_confidence():
    chart = compute_chart(**CANDIDATES[0])
    fe = favorable_element(chart, override="Fire")
    assert fe.element == "Fire"
    assert fe.confidence == "reader-confirmed"
```

- [ ] **Step 2: Run — expect FAIL** (`saju_engine.yongsin` does not exist).

Run: `python3 -m pytest tests/test_yongsin_consistency.py -v`

- [ ] **Step 3: Implement `src/saju_engine/yongsin.py`.** Move the natal favorable-element logic
  currently in `premium_report.py` / `report_data.py` (strength verdict → drain vs support element,
  balanced-chart fallback) into `favorable_element()`. Read the strength assessment via the existing
  `strength.assess(chart)` (or `chart.strength_assessment`). Return `FavorableElement` with:
  - `method="strong-dm-drain"` when verdict is strong (용신 = 식상/재성/관성 drain element),
  - `method="weak-dm-support"` when weak (용신 = 인성/비겁),
  - `method="balanced-heuristic"` when balanced (current under-represented-element guess),
  - `confidence="heuristic"` for all three; `note` a one-sentence client-safe provenance string
    (e.g. `"Engine heuristic from a balanced chart — final 용신 requires classical review."`).
  - `override` non-None → `element=override, method="reader-confirmed", confidence="reader-confirmed"`.

- [ ] **Step 4:** In `premium_report.py`, replace the ad-hoc `ctx.favorable` derivation feeding the
  Quick Reference "Favorable Element" line with `favorable_element(ctx.chart)`; render `fe.note` in
  the "Sources & Limits" / balanced-chart caveat instead of the current inline string. Keep
  `ctx.supporting` (희신) logic as-is.

- [ ] **Step 5:** In `compat_report.py` line ~75, change the per-partner
  `Favorable element (용신): {sa.get('candidate_favorable')}` to use
  `favorable_element(chart_x).element` and append `favorable_element(chart_x).note` as the provenance.
  Keep the `favorable_element_a`/`favorable_element_b` parameters of `generate_compat_report`; when
  provided, pass them as `override=` to the resolver.

- [ ] **Step 6: Run**

Run: `python3 -m pytest tests/test_yongsin_consistency.py -v`
Expected: PASS. Adjust the test's exact assertion strings to the real rendered labels if needed
(read one generated report to confirm the "Favorable Element" label text).

---

### Task 6: Regenerate RM artifacts + full suite

**Files:**
- Modify: `candidates_horoscope/reports/rm/*` (regenerated)

- [ ] **Step 1:** Regenerate RM's Essential + Deep engine markdown and PDFs via the documented path
  (`PYTHONPATH=src python3 -m saju_engine --format premium --tier essential --name "RM" ...` then
  `./tools/build-pdf.sh` — use the exact RM birth args from the existing `candidates_horoscope/reports/rm/`
  files or `docs/MEMORY.md`).
- [ ] **Step 2:** grep the regenerated RM Essential md + `pdftotext` of the PDF for
  `Chart-derived|verify against|Engine note|. sits as` → expect zero hits.
- [ ] **Step 3: Run the full suite**

Run: `python3 -m pytest`
Expected: PASS, count ≥ 571 (568 baseline + new tests). Record exact before/after in the final report.

---

### Task 7: Landing page — pricing data + copy (D13)

**Files:**
- Modify: `apps/landing-page/src/data/landing-data.ts`
- Modify: section components found by grep (`apps/landing-page/src/sections/*.tsx`, `src/app/page.tsx`)

- [ ] **Step 1:** `cd apps/landing-page && git checkout -b strategy/usd-global-pivot`
- [ ] **Step 2:** Enumerate every ₹ / India reference:
  `grep -rn '₹\|Rs\.\|NRI\|Bangalore\|Chennai\|Dubai\|Vedic\|WhatsApp\|Marriage Compat' src/`
- [ ] **Step 3:** `landing-data.ts` edits (spec §6.7):
  - `PERSONAL_REPORTS`: `essential.price` `"₹799"`→`"$19"` (+ `priceNote:"Intro $9"`);
    `deep.price` `"₹1,499"`→`"$55"`; remove `companion` object from `PERSONAL_REPORTS`, move it to a
    new `export const SUBSCRIPTION_UPSELL` with `price:"$9"`, `priceNote:"per month · $79/yr"`.
  - `COMPAT_REPORTS`: `"₹799"`→`"$24"`, `"₹1,499"`→`"$45"`; titles "Marriage Compatibility Basic/
    Detailed" → "Compatibility Snapshot" / "Deep Compatibility" (keep "궁합" as a subtitle string).
  - `FAQS`: rewrite Companion answer (USD, off-grid); add "Do you offer a guarantee?" (7-day) and
    "Are you a Korean master?" (honest positioning answer using the canonical line).
  - `TESTIMONIALS`: prepend the exact warning comment from spec §6.7. Do not change the array.
  - `WHATSAPP_NUMBER`: keep value, add `// LP4: placeholder — de-emphasize WhatsApp; email-first for global buyers`.
  - `ABOUT_READER.bio`: rewrite to the canonical positioning line + English-craft framing; keep name.
  - `WHAT_IS_SAju_CARDS` / `WHAT_YOU_RECEIVE_CARDS` / `TRUST_CARDS`: swap generic "Eastern
    metaphysical" framing for K-culture / higher-resolution-than-a-sun-sign / honest-craft; add one
    "7-day guarantee" trust card.
- [ ] **Step 4:** Update any component that renders `companion` from `PERSONAL_REPORTS` (likely
  `src/sections/PersonalReports.tsx`) to render `SUBSCRIPTION_UPSELL` in a small block below the grid.
- [ ] **Step 5:** Fix ₹ / India strings in section components found in Step 2 (Hero, AboutReader,
  ImportantDetails, ComparisonTable labels, FAQ). Replace India personas/city copy with
  global-audience copy; do not invent testimonials.

---

### Task 8: Landing page — build + test

- [ ] **Step 1:** `cd apps/landing-page && npm run build`
  Expected: zero TypeScript / build errors.
- [ ] **Step 2:** `npm test`
  Expected: existing 74 tests pass (update any snapshot/string test that asserted a ₹ price — change
  the expectation to the USD value; do not weaken the assertion).
- [ ] **Step 3:** `grep -rn '₹\|NRI\|Vedic' src/` → only deliberate diaspora-language options remain
  (e.g. `LANGUAGE_OPTIONS` Hindi/Telugu/Tamil).
- [ ] **Step 4:** `git add -A && git commit -m "Pivot landing page to USD / English-global positioning"`
  (in `apps/landing-page` only).

---

### Task 9: Strategy rewrites of remaining .md files (D3–D9)

**Files:**
- Modify: `CLAUDE.md`, `README.md`, `docs/MEMORY.md`, `tasks.md`,
  `candidates_horoscope/README.md`, `docs/openwiki/products/reports.md`,
  `apps/landing-page/worklog.md`, `docs/issues_bugs.md`

- [ ] **Step 1:** `CLAUDE.md` — add "## Market & Positioning" (canonical line + primary-market
  statement) above "## Tiered Client Products"; replace that table with the USD ladder; fix ₹ in the
  legacy-tier paragraph and the Premium/Compat sections.
- [ ] **Step 2:** `README.md` — replace "## Client products" table with USD ladder; update the
  audience framing sentence; fix the `client_intake_form.html` "₹1,499" bullet.
- [ ] **Step 3:** `docs/MEMORY.md` — rewrite "## Current State" product bullets + "### Client
  products" table to USD; add "## Strategy (2026-09-07)" (one paragraph + pointers to
  `improvements_issues.md` and `docs/market-research-2026-09.md`); update "Active Wishes / Open
  Items" to list the P0 blockers; add a "Recent Changes" line.
- [ ] **Step 4:** `tasks.md` — update the top status line (no longer "Zero open issues"; note the
  pivot + 3 open P0 blockers); add "## Priority B — Business / Go-to-Market (opened 2026-09-07)"
  pointing at `improvements_issues.md`.
- [ ] **Step 5:** `candidates_horoscope/README.md` — all ₹ → USD ladder; keep folder conventions.
- [ ] **Step 6:** `docs/openwiki/products/reports.md` — tier table → USD + positioning line.
- [ ] **Step 7:** `apps/landing-page/worklog.md` — append dated "Strategy shift" entry.
- [ ] **Step 8:** `docs/issues_bugs.md` — add G1/G2/G3 as three rows under a new
  "## Reopened / New (2026-09-07)" heading, status per Task 3–5 outcome (FIXED once landed), each
  pointing at `improvements_issues.md`.
- [ ] **Step 9:** `grep -rn '₹799\|₹1,499\|₹1499' *.md docs/ candidates_horoscope/README.md` →
  only historical-context mentions remain.

---

### Task 10: Final verification

- [ ] **Step 1:** `python3 -m pytest` — green, record count.
- [ ] **Step 2:** `cd apps/landing-page && npm run build && npm test` — green.
- [ ] **Step 3:** Re-read `improvements_issues.md` and `docs/market-research-2026-09.md` for
  placeholder scan, confidence-flag coverage, internal consistency with the USD ladder.
- [ ] **Step 4:** Update `docs/superpowers/specs/2026-09-07-saju-business-refinement-design.md`
  status → IMPLEMENTED; note Q1/Q2 resolutions taken.
- [ ] **Step 5:** Write the persistent memory file (project memory) recording the pivot + the
  location of the two new docs.
- [ ] **Step 6:** Summarize to the user: before/after test counts, files changed, the P0 items that
  remain (checkout, real testimonials, deployment).

## Self-Review

**Spec coverage:** D1→T2, D2→T1, D3–D9→T9, D10→T3+T4, D11→T5, D12→T3, D13→T7/T8. Verification §7→T6/T8/T10.
Non-goals respected (no checkout, no API/MCP, no PPP infra, no testimonials, no deploy). ✅

**Placeholder scan:** test code is concrete; string assertions in T5 flagged as "confirm against real
rendered label" (acceptable — the label text is in the repo, implementer reads one file). Birth args
for RM in T6 point at existing repo files. ✅

**Type consistency:** `FavorableElement(element, method, confidence, note)` used identically in T5
steps 1/3/4/5. `_reviewer_note(ctx, text)` signature consistent T3 steps 1/3. ✅
