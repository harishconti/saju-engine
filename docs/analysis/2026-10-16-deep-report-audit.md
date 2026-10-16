# Deep Destiny Report ($55) — Full Audit

> **Date:** 2026-10-16 · **Auditor:** Claude Code (review session)
> **Specimen:** the delivered `prakash` Deep Destiny PDF (28 pp, ReportLab, Report ID
> `CID-prakash-20261016-DEEP`): 1992-06-12 13:08 Chennai, M, 己 Day Master.
> **Reproduced at HEAD:** `8685fee` ("report PDF: draw CJK, make it navigable, cut the repetition").
> Same birth data → `python -m saju_engine --format premium --tier deep` → `md_to_saju_pdf.py`
> (26 pp). Every defect below was checked against **both** files; the "HEAD" column says whether it
> still ships today.
> **Scope:** (1) what the PDF gets wrong, page by page, and where in code it comes from; (2) the
> structure, measured against what buyers actually pay for; (3) competitors; (4) PDF vs HTML
> delivery; (5) a ranked fix plan.

---

## 0. Verdict in one paragraph

The calculation underneath this report is good. The solar-time correction, the hour-boundary
warning, the 조후-over-억부 favourable-element argument, the void years, and the 2034 甲己 combination
are all things a careful human reader would catch, and many $10 apps miss them. **The document
around that calculation is not yet a $55 product.** It is an unpolished engine draft. Page 27
says so in the client's own copy: *"Engine-generated premium report draft. Interpretive prose must
be reviewed and finalized by a qualified reader before client delivery."* The brand promise is
*"read in clear English by a human"*. A buyer who reads that sentence, or meets "the querent" 53
times, or reads "Gi (Yin Earth, Gi Earth)" on the cover page, will conclude that the report is
machine output. They will be right, and at $55 that means a refund request. **Fix the
ship-blockers (section 2) before any further client delivery. Then restructure (section 4) and
move delivery to a web-first link with a PDF download (section 6).**

| Dimension | Score /10 | One-line reason |
|---|---|---|
| Calculation correctness | 8 | Solar time, 조후 logic, void, combinations all sound; hour-pillar uncertainty under-propagated |
| Internal consistency | 4 | Wood and Earth are "avoid" on p.3 and "good/favourable" on pp.10, 12, 16, 22 |
| Personal specificity | 4 | One vivid line ("garden plot waiting for rain"), then templates; ~27 % of prose sentences are near-duplicates |
| Language polish | 3 | Translation mash-ups, internal jargon, file/step references, "a Earth" grammar |
| Structure for the reader | 4 | Technical-first, 7 of 8 decades given equal weight, 5 pp of date lists, glossary after the closing |
| Answers what buyers want | 4 | No answer to the client's own question, no month-by-month for the coming year, no animal or 일주 identity |
| Visual / brand | 5 | Clean tables; no Hanja pillars, no element chart, a decade "chart" that is a plain table |
| **Overall, as a $55 deliverable** | **4.5** | Strong engine, draft-grade document |

---

## 1. Method

1. Read all 28 pages of the delivered PDF as a buyer would, then again as a Saju reader would.
2. Regenerated the same chart at HEAD and diffed the extracted text (`pdftotext`) of both PDFs
   against a list of defect patterns (counts in section 2).
3. Measured repetition. I split the HEAD markdown prose (tables excluded) into sentences and
   paired sentences with a `difflib` similarity above 0.75: **2,251 of 8,303 words (27.1 %) sit
   in near-duplicate sentences**. Exact template sentences (identical once the stem and element
   names are masked) make up another 6.1 %.
4. Traced each defect to its source: `src/saju_engine/premium_report.py`,
   `src/saju_engine/prose_fillers.py`, and the post-hoc translator in `src/saju_html/__init__.py`.
5. Researched the competition and how adjacent industries deliver reports (sources in section 9).

---

## 2. Defect log

Page numbers refer to the delivered 28-page PDF. **P0** means the defect should block delivery.
**P1** means it damages credibility. **P2** means polish.

### 2.1 P0: ship-blockers

| # | Defect (page) | Why it matters | Source | HEAD |
|---|---|---|---|---|
| 1 | **"Engine-generated premium report draft… must be reviewed and finalized by a qualified reader before client delivery."** (p.27, after the Closing Note) | Tells the buyer, in writing, that nobody reviewed their report. This contradicts the positioning line in `CLAUDE.md`. | `premium_report.py:2397, 2469` | **still ships** |
| 2 | **The client's name is lowercase**: "prakash — Saju Reading", "For prakash" (cover, p.2) | The first word on the cover is wrong. No human would send this. | intake → `--name` not title-cased | still ships |
| 3 | **Broken double glosses** from word-by-word Korean→English substitution: "Gi (Yin Earth, **Gi Earth**)" ×6, "Im (Yang Water, Im Water)", "a whole **Major Luck Water** 8" (대운**수** read as "Water", p.17), "day-officers/**28Water** almanac" (28**수** = 28 lunar mansions, p.22), "Coming of Age (**crown belt**)" (冠帶), "Bathing (**bathe bath**)" (沐浴), "Nurturing (nurture)", "(binding without transforming, binding without transforming)" ×3, "Myeongri (Korean Saju tradition) (destiny principles)", "Jeong-Im Wood combination (Jeong Im combination Wood)", "per **'s** '3 days = 1 year' rule" (the source name was erased) | Reads as machine translation. This is the strongest single "AI-slop" signal in the document. | `src/saju_html/__init__.py` `KOR_REPL`/`HANJA_MAP` single-syllable and Hanja passes run on already-glossed text | **all still ship** |
| 4 | **Internal machinery leaks into client copy**: "per Step 2" (p.3), "the engine has weighed both" (p.3), "The engine flags a likely Companion Grid" (p.14), "none of which this engine computes" (p.22), "Dominant pattern candidate" (p.14), table keys `year_stem` / `year_branch_middle` (p.15), "the querent" ×53 (×30 at HEAD) mixed with "you" | Exposes the pipeline and breaks the second-person voice. "Querent" is tarot-trade jargon that clients never use. | `prose_fillers.py` (most `querent` strings), `premium_report.py` wealth table, `P3-reader-claim` wording | still ships |
| 5 | **A non-Saju rule**: "Conjunction of new-moon or full-moon **eclipses** falling on spouse-palace or wealth-stem branches — defer the launch by 30–45 days" (p.17) | Western-astrology content. It violates Ground Rule 1 ("traditional principles only") and is in no `knowledge/` file. | `prose_fillers.py:2322` | still ships |
| 6 | **A raw HTML comment** `<!-- decade-roadmap:start -->` / `:end -->` printed as text, and the text above it promises "Green segments… amber… red" for a chart that is not drawn (p.22) | Visible template debris. ReportLab is the **locked production backend** (`docs/MEMORY.md`, 2026-10-15), so the HTML path's fix (`sections.py:127`) never reaches clients. | `premium_report.py:1419` + the ReportLab path in `md_to_saju_pdf.py` | still ships |
| 7 | **The client's "main concern" is collected but never answered.** The intake form enables the textarea *only* for the Deep tier, and nothing in `premium_report.py` reads it. | The one field that proves a human read *this* order is thrown away. Every competitor at this price answers 1–8 questions (section 5). | `premium_report.py` (no `concern` input) | still ships |
| 8 | **Price inside the deliverable**: "Deep Destiny Report · $55" (p.2) | It reads like an invoice and makes the length feel like value-for-money accounting. | header template | **fixed at HEAD** |
| 9 | **Raw markdown `>` blockquote markers** printed 16 times (pp.2, 6, 9, 11, 12, 14, 19, 22, 26, 27) | Template debris. | ReportLab blockquote handling | **fixed at HEAD** |

### 2.2 P1: credibility and internal contradictions

A Saju-literate client, or a sceptical one, will catch these. Each one undercuts the report's
claim to rigour.

1. **Wood is both "avoid" and "good".** Quick Reference (p.3) lists Wood as *"Draining Element,
   drains Water"* under Avoid/Watch. Partner Compatibility (p.10) rates Wood partners **"Good"**
   because they *"drain your strong Day Master"*. Health (pp.12, 25) says Wood is **deficient and
   needs gentle support**. These are three answers from three different rule sets: 조후, 억부, and
   raw element counts. None of them is reconciled with the others. *(See knowledge/09 Step 0 and
   knowledge/17: once 조후 governs, the 억부 pick and the count-based health note must be
   presented as secondary readings and labelled as such.)*
2. **Earth is "restraining, watch", yet the Earth-stem decades are "favourable".** Avoid/Watch
   includes Earth, since it restrains the favourable Water. But 戊申 (18–27) and 己酉 (28–37) are
   labelled "favorable" (pp.20–22), the current decade is "a clearly favorable window for visible
   wins" and a "tailwind decade" (pp.18–19), and 2028 戊申 / 2029 己酉 are called
   *"supporting-element (Metal) years"* although their stems are Earth. The lean is probably being
   judged on the Metal branch. That can be defended (branch-weighted 대운 reading), but the report
   has to *say so*. Otherwise it reads as a contradiction. Source:
   `prose_fillers.period_favorable_status` and `annual_lean`. Favourability is computed in
   several places and patched individually (see the long bug-history docstring at
   `prose_fillers.py:78-107`).
3. **The hour-pillar uncertainty is flagged once and then ignored.** Page 2 correctly warns that
   the corrected time (12:59) is 41 seconds from the 午/未 boundary. The rest of the report then
   treats the 庚午 hour as fact, including the parts that depend entirely on it:
   - the **午午 self-punishment**, which p.14 calls *"the most prominent natal branch signal"*;
   - the **second** 午未 six-combination row (p.13);
   - the Hurting Officer hour stem (which would be an Eating God under 辛未);
   - the children/later-life palace.

   A human reader would turn this into a strength. The report should spell out what changes if
   the time is a few minutes late, ask whether 13:08 comes from a hospital record, and mark the
   dependent sections. Nothing builds trust faster than visible honesty about uncertainty.
4. **"Top 5 Strengths" invents dominance.** It lists *Companion-dominant*, *Indirect
   Resource-dominant* and *Direct Wealth-dominant*, but the report itself says the dominant
   classes are Companion (5) and Resource (4). Direct Wealth appears twice.
5. **The six-combination row appears twice** (p.13), once for each 午. The note is word-for-word
   identical, including the triple parenthetical.
6. **Past decades get the same weight as future ones.** The client is 34. The report still gives
   full career strategy for ages 8–17, "conservation windows: ages 8–17" (p.26), and relocation
   windows of 18–27 (p.16). Past decades should be used as **validation** instead ("Looking back
   at roughly 2010–2019 (戊申), did peers or rivals shape your path more than mentors?"). Good
   human readers open this way, and it is the most persuasive move available.
7. **The "current year" is 2026 with 3½ months left.** The report was generated on 16 October,
   so the 丙午 solar year ends at 입춘 (~4 Feb 2027). The forward-looking value of the report is
   **2027 丁未 month by month**, which does not appear anywhere.
8. **The biggest future signal is buried.** 2034 甲寅 brings **甲己合 with the Day Master
   itself**, plus 寅申 clash and 寅巳申-family punishment. It sits mid-sentence inside a 90-word
   run-on (p.19). A human reader would make it a headline.
9. **The strength verdict is borderline but stated flatly.** "Strong" sits beside "support and
   drain sit close to even" (p.3). Say "moderately strong, close to balanced". The 조후 argument
   carries the 용신 anyway.
10. **The health section reads advice off percentages.** "Wood (2.8 %)" is presented with false
    precision. The 0.6/0.3/0.1 weighting is a house convention, not a classical figure. Keep the
    bars and drop the decimals in the client copy, or round to "very little Wood".

### 2.3 P2: template prose ("AI-slop" signals)

What readers notice is not exact repetition but the **same sentence skeleton with the nouns
swapped**. Measured on HEAD markdown: **27 % of prose words sit in near-duplicate sentences.**

| Where | What repeats | Fix |
|---|---|---|
| Four Pillars, One by One (pp.5–6) | The same three paragraphs ×4: "*The X branch is the container… Because the stem belongs to the X element, it tends to bring x-flavoured themes… qualities of motion, structure, or feeling…*" | Cut to one tight paragraph per pillar that says **what is specific**: year 壬申 = Direct Wealth on the ancestral pillar; month 丙午 = Direct Resource sitting on 건록; and so on. |
| Decade-by-decade career (pp.8–9) **and** Life Themes (pp.20–22) | The same decade paragraph template, rendered **twice** across two sections (the delivered PDF repeats "build and rise decade. Plant several seeds…" six times) | Merge into one "Life Map" section. Write the current decade and the next two in full, the past ones as one-line validations, and the far future in one line each. |
| Career Archetypes table (p.7) | "Aligns with your favorable element Water, reducing friction." ×5; "Uses Metal energy in a supportive role…" ×5 | Give each row its own reason, or collapse to three rows with one shared reason. |
| 10-Year Forecast (pp.18–19) | Rows come in identical pairs (2026 = 2027, 2028 = 2029, …), because the ten-god class drives the text | Write year text from the **branch interactions**, which differ every year, not from the ten-god class. |
| Year-by-Year Notes (pp.19–20) | Run-on lists of every 합/충/형/파/해 hit | Pick the single most consequential interaction per year and translate it into a life sentence. Move the full list to the appendix. |
| 90-day dates + Monthly Lucky Dates (pp.22–26) | ~5 pages. Both lists use the same filter and duplicate each other. About **25 % of all days** qualify as "lucky", which makes the label meaningless. | Keep **one** list: the top 2–3 days per month for the next 6 months, ranked, with one reason each. Put the rest in a downloadable calendar (`.ics`). |
| "In plain words" boxes | 7–9 boxes, twice back-to-back (p.6) | Use at most one per major section, written last. |
| 5 Practical Recommendations (p.26) | "Replace one caffeinated drink with a warm herbal tea", "Read fiction 30 min before bed" | Generic wellness tips with no chart link: the classic slop tell. Each tip must name the chart reason, or be cut. |
| Glossary | Placed after the Closing Note | Move it to an appendix, or to hover/tap definitions on web. |
| Grammar | "a Earth", "a Indirect", "a Hurting Officer ten-god", "nervous system system" | Article helper (`a`/`an`) in `prose_fillers`. |

**Before → after (style guide, using only facts already in this chart):**

> **Before (p.4):** *"With Gi (Gi (Yin Earth, Gi Earth)) as your Day Master … your core self
> carries the image of the rich garden soil nurturing many seeds. … Born in a Earth chart with the
> engine reading as strong, the way you meet the world is shaped by how much Earth energy is
> available."*
>
> **After:** *"You were born on a 己未 day: Gi (己, soft field soil) on Mi (未, the Goat, summer
> earth). Then look at the rest of the chart: a 午 Horse in the month **and** a 午 Horse in the
> hour. That is mid-June at noon, the hottest month at the hottest hour. A field in that heat
> does not need more sun or more soil. It needs rain. That one image explains most of this
> report: why Water is your favourable element even though your Earth is already well supported
> (knowledge/17), why winter is your best launch season, and why the two Water decades from age
> 48 matter so much."*

The rewrite uses no fact the engine did not already compute. It is concrete (two Horses, noon,
June) and it ties three later sections to one idea. That kind of connective reasoning is what
"a human read this" means.

---

## 3. What buyers actually pay for

Evidence, strongest first:

- **Korean market leaders sell the year, by topic, by month.** 포스텔러 (8.6M members) leads its
  App Store pitch with *"2026 병오년 신년운세 — 재물운, 연애운 등 주제별 상세 풀이부터 월운 흐름까지"*
  (money and love by topic, then the month-by-month flow). 점신 (17M downloads) adds niche
  topics such as real estate and investing. Interest peaks at New Year.
- **English competitors converge on the same five headings:** personality, love, money/career,
  health, 10-year timing, plus **answered questions** (Saju Atelier 3, Sajumuse 1 + 10
  follow-ups, Master Sean Chan up to 8, Fiverr readers 1–3).
- **The audience is entertainment-first.** Pew 2025: 20 % engage "just for fun", 10 % for
  insight, 1 % rely on it "a lot". They want to feel *seen* and to have something to share, more
  than doctrine.

**Ranked buyer interest, and how this report scores:**

| Rank | What they want | In this report? |
|---|---|---|
| 1 | "Is this *me*?": a personality portrait that feels specific | Partly. One good image, then generic Earth traits. **No 일주 (day-pillar) identity** (己未 "Earth Goat"), which is the most popular content type in Korean apps. **No zodiac animal** (1992 壬申 = Water Monkey), the easiest hook for Western buyers. |
| 2 | Love: what kind of partner, and *when* | Partner type is present (contradictory, see §2.2.1). Marriage windows are present but buried in one paragraph (p.11). |
| 3 | Money and career: what to do, and when | Present, but templated. |
| 4 | **This year and next year, month by month** | **Missing.** There are year rows and date lists, but no 월운 narrative for the next 12–15 months. |
| 5 | **My question answered** | **Missing** (P0 #7). |
| 6 | Shareable bits: lucky colour, number, animal, a "chart card" | The lucky card exists. No animal, no shareable visual. |
| 7 | Health tendencies (light touch) | Present, over-long, contradictory on Wood. |
| 8 | Technical depth (ten-gods, 신살, patterns) | Over-served and placed up front. Most buyers skip it; the few who want it want it *correct and cited*. |

---

## 4. Recommended structure (same engine, re-ordered, ~20–24 pages)

Lead with the reader's questions; put the technical material in the appendix.

| § | Section | Pages | Notes |
|---|---|---|---|
| — | **Cover** | 1 | Proper-case name, the four pillars **in Hanja** with Korean and English beneath, the year animal and day-pillar animal, the chart signature line. No price. |
| 1 | **A letter from your reader** | 1 | 150–250 words, *hand-written per client*: the 2–3 chart features that drive everything, and any caveat about birth-time accuracy. This page is the proof that a human read it. |
| 2 | **Your question, answered** | 1–2 | From the intake "main concern". If none was given, use "the question your chart raises most". |
| 3 | **Your chart at a glance** | 2 | Pillar grid with Hanja, the element wheel (SVG), quick reference, one clear 용신 explanation (조후 vs 억부, said once, in plain English). |
| 4 | **Who you are: 己未, the Earth Goat at noon** | 2–3 | Day-pillar portrait, the strengths you actually show, the shadow side. Ten-god relationships used as narrative, not as a table. |
| 5 | **Love & partnership** | 2–3 | Spouse palace, partner type (consistent with 용신), marriage/commitment windows as a dated list, the 궁합 upsell as one line. |
| 6 | **Work & money** | 2–3 | 3–5 career directions with *distinct* reasons, employment vs own business, the income pattern, investment temperament. |
| 7 | **The next 15 months** | 3 | Month by month from now to Jan 2028: one or two sentences per 월운 plus the best 2–3 dates. This is the section people reopen. |
| 8 | **The next 3 years & your current decade** | 2 | 2027–2029 in depth, plus 己酉 to 2028, then the 庚戌 decade shift. |
| 9 | **Your life map** | 2 | An SVG timeline of all decades. Past ones as one-line "look back" validations; the future in brief; flagged headline years (2032 void, 2034 甲己合). |
| 10 | **Health & energy** | 1 | Tendencies only, consistent with 용신. |
| 11 | **Your favourable-element card** | 1 | Designed as a shareable card or image. |
| 12 | **Closing note** | 1 | Hand-finished. Ends the report. |
| A | Appendix: the technical chart | 3–4 | Ten-god table, hidden stems, patterns/신살 table, classical sources (*named texts, not repo paths*), methodology, birth-time note. |
| B | Appendix: glossary + full date lists | 2 | Or replace with `.ics` plus web tooltips. |

The tier table in `CLAUDE.md` says 25–30 pages, but `premium_report.py:18` says "10–12 pages".
Pick one. **Do not compete on page count.** Sajumuse advertises 100+ pages for $39 and Saju Atelier
50+ for $69. Length is commoditised; specificity and a visible human touch are not.

**Citations: resolve a positioning conflict.** The positioning line promises *"with the classical
texts cited"*, but the pipeline strips every citation from the PDF. Keep repo paths out, as now,
but add client-facing source notes such as *"Why Water? 궁통보감's climate method: in peak
summer, an Earth chart's first need is moisture."* Put a few of these in the 용신 box and the
appendix. That delivers the brand promise without exposing the machinery.

---

## 5. Competitor comparison

| Provider | Price | Format & delivery | Size | Human? | Questions | Notable |
|---|---|---|---|---|---|---|
| **Cheok Cheok / SajuPlus** | $9.99 (Complete) | **In browser**, 60-day access via email verification | "15 guided sections" | AI | — | 2026-year report $7.99; free tools funnel |
| **SajuAI** | $7.99 | Illustrated report | 10 pp | AI | — | Free basic reading |
| **Saju Atelier** | $39 / **$69** (Eclipse) | Emailed **secure link, 30 days**, plus PDF download; live progress page | 20+ / 50+ pp | "Proprietary system" | 1 / **3** | "Under an hour"; glossary; 7-day satisfaction policy |
| **Sajumuse** | **$39** | **100+ pp PDF**, plus follow-ups answered **on the report page** | 100+ pp | Claims a "certified master" | 1 + 10 follow-ups | Couple bundle $72; child report |
| **Master Sean Chan** (BaZi) | unlisted, premium | Report + email Q&A, ~15 working days | long | Human | up to 8 | Natal → luck → **your questions**; specific, hedged, traceable |
| **Fiverr Korean readers** | $15–50 | PDF | 10–60 pp | Human | 1–3 | Cite K-culture demand |
| **CosmicSaju Deep** (this) | **$55** | PDF by email (+ MP3) | 28 pp | **Engine draft, unreviewed** | **0** | Best calculation in the set; the 궁합 product is unique |

**Reading the table:**

- At $55 this report sits between Sajumuse ($39, 100 pp, a question answered) and Saju Atelier
  Eclipse ($69, 50 pp, 3 questions). It currently **offers less than both on the axes buyers can
  see**: page count, questions, and the feel of a human touch. Its advantages (calculation
  honesty, the uncertainty notes, the cited method) are invisible unless the prose shows them.
- Nobody else surfaces **birth-time uncertainty** or the **조후 vs 억부 reasoning** to the client.
  This report already has both. They are the differentiators, so put them on page 1.
- Two of four direct competitors deliver **in the browser**, and one adds follow-ups **on the
  report page**. Web delivery is already normal in this niche (section 6).

---

## 6. PDF or HTML? How similar industries handle it

### 6.1 Evidence

- **One-off astrology/BaZi readings (Etsy, Fiverr, Gumroad):** the PDF is the default, and its
  stated benefit is "save and revisit, offline".
- **App-native Saju competitors:** **SajuPlus** delivers in the browser only, with access for 60
  days. **Saju Atelier** sends a secure link (30 days) plus a downloadable PDF. **Sajumuse**
  sends a PDF plus a web report page for follow-up Q&A.
- **Adjacent personal-report industries:** DNA (23andMe) uses an interactive dashboard as the
  primary experience with an optional PDF download for offline keeping. Lab results and banking
  use a portal plus PDF statements. The pattern is consistent: **web for using, PDF for keeping**.
- **No public study** compares customer preference between PDF and web for astrology reports. I
  searched and found only vendor marketing. Treat the recommendation below as a reasoned default
  and measure it.

### 6.2 Will clients accept HTML?

Yes, **provided three anxieties are handled**:

1. **"Will I lose it?"** Saju Atelier's 30-day expiry and SajuPlus's 60-day window are friction,
   not features. The token links in this repo already **do not expire** (`/report/{token}`),
   which is an advantage. State it ("Your reading stays at this link"), and always include
   **Download PDF**.
2. **"Is it private?"** Use an unguessable link, `noindex`, and no third-party trackers on the
   report page. Most of this is already in place: tokens are redacted from access logs.
3. **"Does it feel premium?"** It must look designed on a phone. A4 PDFs are poor on mobile (tiny
   tables, pinch-zoom). Assume most buyers open the email on a phone, and verify that with link
   analytics.

### 6.3 What web delivery unlocks

- **The MP3 on the same page.** The report already promises this ("it appears on the same page
  as your reading", p.27). A PDF cannot keep that promise; a web page can.
- **Tap-to-define glossary terms**, which removes the end glossary.
- **A live "This month" block** that is true whenever the client opens the page: the retention
  hook the Companion subscription needs.
- **A follow-up question box** under the report (Sajumuse's model), which is natural upsell
  inventory.
- **Collapsible appendix** for the technical chart: depth for those who want it, hidden from
  those who don't.
- **A shareable chart card** (an OG image of pillars, animal and element), which is free
  acquisition through the short-form social channel in `docs/market-research-2026-09.md` §4.1.

### 6.4 It also solves an infrastructure problem

`docs/MEMORY.md` (2026-10-15) locked **ReportLab** for production because Chromium does not fit a
Vercel function, and ReportLab is the renderer that prints the HTML comments and draws no SVG
charts. **A web report needs no browser on the server.** The HTML renderer (`src/saju_html/
renderer.py` + `theme.css` + `svg_charts.py`) can serve the page directly. The PDF can be
ReportLab (good enough as a keepsake) or a print stylesheet the client prints themselves.

### 6.5 Recommendation

**Make web the primary deliverable and the PDF the keepsake.** The delivery email carries the
private link as the main button, a "Download PDF" link, and the MP3. Run it for the next 20–30
orders and track link opens, PDF downloads, return visits, follow-up questions and refund
requests. If fewer than 30 % of buyers ever download the PDF, the PDF can stay a background
convenience.

---

## 7. Ranked fix plan

### Week 1: stop the bleeding (all P0, small, testable)

1. Remove the "Engine-generated … draft" line from client renders. Keep it **only** in the
   review console (`intake_admin.py show`). `premium_report.py:2397, 2469`.
2. Title-case the client name at intake, and let the reviewer override it.
3. Fix the translator so it never re-glosses text that is already glossed: protect spans inside
   parentheses, and translate compound terms (대운수, 28수, 冠帶, 沐浴, 合而不化) **before**
   single syllables. Add the exact strings from §2.1 #3 as regression tests in
   `tests/test_translation_quality.py`.
4. Replace "the querent" with "you" throughout `prose_fillers.py`. Remove "engine", "Step N",
   "candidate", and raw keys (`year_stem`) from client copy.
5. Delete the eclipse rule (`prose_fillers.py:2322`).
6. ReportLab: strip `<!-- … -->` and draw the decade roadmap. Either port the SVG to a ReportLab
   drawing, or render it as coloured table cells.
7. Add `main_concern` to `generate_premium_report(...)`, render a **"Your Question"** section
   stub that the reviewer must fill, and block `approve` while it is empty.
8. **Add a client-ready gate** (`tools/qa_client_ready.py`, run by `intake_admin approve`). It
   fails on: `querent|engine|draft|Step \d|<!--|^> |\$\d+` in the body; the regex
   `\b(\w+) \(([^()]*), \1 ` (double gloss); a lowercase name; repeated words (`system system`);
   `a [AEIOU]`; and any sentence that appears more than twice. This turns the audit into a
   permanent check.

### Weeks 2–3: credibility and structure

9. **One favourability verdict object.** Compute it once per report: 용신, 희신, 기신, 구신, and
   *which method governs and why*. Make every section (partner table, health, decades, years,
   dates) read from it. Where the branch is used for a decade lean, say so in the text.
10. **Propagate hour-pillar uncertainty.** When `hour_boundary_warning` is set, compute the
    alternative hour pillar and list which findings change. Tag dependent sections with a small
    "depends on birth minute" marker, and ask about the source of the birth time at intake.
11. Restructure to section 4. Merge the duplicated decade sections, cut the date lists to a
    top-3-per-month table plus `.ics`, and add **the next 15 months** (월운) and **the 일주 / animal
    identity**.
12. Re-weight time: past decades as one-line look-back validations, the current decade and the
    next two in depth.
13. Year text driven by the most consequential branch interaction, not the ten-god class.
14. Client-facing classical source notes (section 4, "Citations").

### Week 4+: delivery

15. Web report page at `/report/{token}`: mobile-first, embedded MP3, tap glossary, collapsible
    appendix, Download PDF.
16. Shareable chart card (OG image).
17. Follow-up question box (paid, or one free) feeding the review queue.
18. Instrument opens, downloads and return visits, then decide the PDF's role from that data.

### Review workflow (this is the product, not an add-on)

The positioning is "an accurate engine and an honest interpreter". The engine half is done. The
interpreter half needs a **fixed 30–45-minute review routine per order**, which matches the
market-research target in §7:

1. Read the intake and the main concern. Check the birth-time source.
2. Confirm or override the 용신 (`--favorable-override`).
3. Write the letter (§1) and the answer (§2).
4. Rewrite the portrait opening and the closing note by hand.
5. Read the 15-month section aloud, which catches template rhythm fast.
6. Run `qa_client_ready.py`, then `approve`.

---

## 8. Where the report is already good (keep these)

- The **true-solar-time** line with the arithmetic shown (p.2): rare, credible, keep it.
- The **hour-boundary warning** (p.2). It just needs propagating.
- The **조후-over-억부 explanation** for the 용신 (p.3). It needs one plain-English sentence, not
  three.
- **Void years flagged** (2032, 2033) with a sensible "document gains" reading.
- The **"Chart signature: a garden plot waiting for rain"** line. This is the best sentence in
  the report; build the narrative around it.
- The **major-luck start age** with both the precise and the manseryeok-rounded convention
  explained (p.17). Honest, and pre-empts the "my app says 8, you say 8.2" email.
- **Disclaimers** in health and dates that are sober rather than fatalistic, in line with the
  ground rules.

---

## 9. Sources

Competitor and industry research (fetched 2026-10-16 unless noted):

- SajuPlus Complete reading ($9.99, 15 sections, browser, 60-day access): https://sajuplus.com/en/premium-ai-saju-fortune · https://sajuplus.com/en/home
- Saju Atelier (Moonrise $39 / Eclipse $69, 20+/50+ pp, 30-day secure link + PDF, 3 questions): https://sajuatelier.com/
- Sajumuse (Premium $39, 100+ pp PDF, 10 follow-ups on report page): https://www.sajumuse.com/
- Master Sean Chan BaZi sample report (natal → luck → questions; ~15 working days): https://www.masterseanchan.com/bazi-sample-report/
- SajuAI ($7.99, 10-page illustrated): https://webmail.hunted.space/product/sajuai
- Fiverr Korean saju reader (PDF format, career/love/wealth/health, annual & monthly): https://www.fiverr.com/tom1004
- Fiverr BaZi 28-page PDF example: https://www.fiverr.com/s/LdayEqQ
- PDF vs interactive positioning among astrology report vendors: https://my-zodiac-ai.com/blog/natal-path-vs-astro-nectar-vs-my-zodiac-ai
- 포스텔러 App Store listing (신년운세: 재물운·연애운·월운): https://apps.apple.com/KR/app/id1262949138
- 점신 / 포스텔러 user numbers: https://gogumafarm.kr/?p=30378 · https://www.unicornfactory.co.kr/article/2025012414570018707
- 포스텔러 vs 점신 UX analysis: https://brunch.co.kr/@uibowl/403
- Astrology-app complaints (paywalls, repetitive daily themes): https://unstar.app/vi/blog/co-star-sanctuary-pattern-nebula-stellium-astrology-apps-ranked-2026 · https://kimola.com/reports/co-star-app-review-analysis-unveiling-user-insights-app-store-us-155484
- 23andMe dashboard + downloadable reports: https://www.lifeintech.com/2017/08/23/23andMe-Part-Two/ · https://www.techradar.com/uk/reviews/23andme-dna-test
- Pew Research 2025 (astrology engagement depth): cited in `docs/market-research-2026-09.md` §1.1

Repo evidence: `src/saju_engine/premium_report.py`, `src/saju_engine/prose_fillers.py`,
`src/saju_html/__init__.py`, `src/saju_html/sections.py`, `docs/MEMORY.md` (2026-10-15 decisions),
`docs/market-research-2026-09.md`, `knowledge/09-interpretation-method.md`,
`knowledge/17-climate-method.md`.
