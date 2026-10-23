# Products and Reports

> **Positioning (2026-09-07 pivot):** target market is English-speaking global (K-culture fans,
> diaspora), priced in USD. India is a Phase-2 experiment only. Canonical line: *"an accurate engine
> and an honest interpreter — not a Korean master."* See `docs/market-research-2026-09.md`.

## Single-chart products

Legacy internal names are still accepted by the engine but should not be advertised to new clients.
Prices are USD launch prices — see `docs/market-research-2026-09.md` for ranges and the pricing risk.

Legacy aliases: `spark` → `essential`, `reading` → `deep`, `fullmap` → `deep`.

## Compatibility (궁합) products

`generate_compat_report` accepts `favorable_element_a` / `favorable_element_b` — pass the
reader-argued 용신 from the hand-crafted natal reading so the natal and compat products agree
(`src/saju_engine/yongsin.py`).

> **Year-end offer (2026-10-22 → 2026-12-31): 20% off every paid report.** The *list* prices in the
> table below are unchanged; the offer price is derived from them and charged through separate store
> products — $19 → **$15.20**, $55 → **$44**, $24 → **$19.20**, $45 → **$36**. The offer is a
> webapp concern only (the store and the landing page); **a report never prints a price**, and the
> engine's tier metadata is untouched. See `docs/webapp/02-data-model.md` §"The launch promotion".

| Client-facing name | Engine call | Price | Pages | Contents |
|---|---:|---:|---:|---|
| **Compatibility Snapshot (두 분 궁합)** | `generate_compat_report(..., tier="basic")` | $24 | ~4 | Composite 0–100 score + 4-band verdict, four-pillar glance, four decisive sub-systems, condensed practical guidance, closing note. |
| **Deep Compatibility (두 분 궁합)** — hero | `generate_compat_report(..., tier="deep")` | $45 | 9–10 | Basic + all 11 sub-system cards, per-partner element balance / Day Master snapshots, major-luck timelines, year-by-year couple timing overlay, full practical guidance, closing note. |

**Delivery (P4):** via the self-service app the free sample reading is instant (the free tier has no PDF — see `docs/webapp/03-api-spec.md` §`POST /api/sample`); every paid tier (single-chart and compat) is queued as an engine draft and delivered only after the owner reviews it and runs `tools/intake_admin.py approve <id> --base-url https://<host>`, which prints a private download link (no email sending yet). PII is encrypted with `SAJU_INTAKE_KEY`; retention default 180 days.

The 11 sub-systems are defined in `knowledge/11-gunghap.md` and implemented in `src/saju_engine/compat.py`.

## Report generation paths

### Direct engine report
```bash
PYTHONPATH=src python3 -m saju_engine \
  --date YYYY-MM-DD --time HH:MM --city "City" --gender M \
  --format premium --tier deep \
  --output-file /tmp/report.md
```

### From an existing markdown report
```bash
./tools/build-pdf.sh sruthi
```

### Combined base report + follow-ups
```bash
PYTHONPATH=src python3 src/saju_html/combine_candidate_report.py sruthi
./tools/build-pdf.sh --combined sruthi "Title" "Client" "DOB" "Day Master"
```

### Compatibility report
```bash
python3 src/saju_html/md_to_saju_compat_pdf.py <compat.md> --name-a ... --name-b ... --tier deep
```

### The web document (the reading; the PDF is the keepsake)

`markdown_to_html(..., web=True)` produces the artefact the client is meant to *read*:
one **self-contained** HTML file — inline CSS, inline SVG charts, no scripts, no
webfonts, no external requests — so the same bytes can be served at the report link *and*
downloaded and kept. Nothing in it depends on our origin, our build, or the reader's
installed fonts.

```bash
python3 src/saju_html/md_to_saju_html_pdf.py --from-chart --web \
  --name "…" --birth-year … --tier deep --output report.html [--audio-url https://…]
python3 tools/qa_client_ready.py report.md --html report.html   # gate the artefact
```

**It is styled from the webapp's own design system** — the same tokens, type scale and card
idioms as `apps/web/src/app/globals.css`, so a client moving from the product to their reading does
not notice the surface change. Dark cosmic base and gold accent by default, the OS light palette via
`prefers-color-scheme`, the five-element (오방색) colours driving every chart, `--radius` on cards.
Two mechanics make that work and are worth knowing before editing it:

- **The print sheet's tokens are re-pointed, not rewritten.** Every block in `theme.css` — tables,
  the quick-reference card, callouts, rules — was written against `--color-*`, so the web layer
  remaps those names to the app's palette. That brings the whole sheet into the design at once
  instead of patching blocks and missing the ones added later. `tests/test_web_report.py` asserts the
  mirror still matches `globals.css` token-for-token, so a rebrand cannot leave reports behind.
- **The charts are re-skinned by attribute.** They are drawn with the print palette inline
  (`fill="#e74c3c"`, Helvetica), which is right for the PDF and wrong on a dark card. The web layer
  overrides those fills and fonts from the app's palette, so the SVG emission — and therefore the PDF
  and its snapshots — is untouched. The element table's "Presence" bars are block glyphs, coloured
  per row with `:has()`.

Sections are laid out as **panels** — the app's card idiom — each with a monospace ordinal eyebrow,
and the markdown's own title block is dropped when it only repeats the cover. The readable column is a
**wrapper** (`.page`), not a rule on `body > *`: a `margin: auto` there was silently undone by the next
`p { margin: … }` in the same sheet, which left the front matter hard left while the panels below it
were centred. `test_the_readable_column_is_a_wrapper` pins that, on screen only.

**The app's own typefaces are embedded.** The app loads Inter, Cormorant Garamond and IBM Plex Mono
from a Google Fonts `<link>`; a delivered reading cannot make that request — it has to be one
self-contained file, and a third-party font request would tell someone when a client opened their
report. So `tools/build-web-fonts.py` subsets those three faces (variable Inter and Cormorant, static
Plex Mono; Inter's italic is left out because the app does not load one either) and the renderer
inlines them as `woff2` data URIs:

```bash
python3 tools/build-web-fonts.py           # regenerate into src/saju_html/fonts/
python3 tools/build-web-fonts.py --check    # coverage; informational about glyphs the face lacks
```

Cost and effect, measured: **+235 KB** per reading (Inter 93 KB, Cormorant 62 KB, Plex Mono 16 KB,
base64-inflated) — a Deep reading is ~370 KB, the one-page teal ~273 KB, and it is fetched once and
kept. The rendered page makes **zero network requests**, against four or more that the app's font link
issues. `test_the_embedded_faces_are_the_apps_own` compares the embedded families to the app's
`--font-*` tokens, so changing the app's stack cannot silently leave the reading in the old face, and
`test_the_reading_stays_a_reasonable_download` keeps the size a deliberate decision. The faces are
OFL; their notices travel in `src/saju_html/fonts/LICENSE-WebFonts.txt` and as the colophon line at
the foot of the reading.

What the web layer adds on top of the print stylesheet (`theme.css` is built for A4):

- **Navigation that works.** Every `h2`/`h3` gets a readable id (`#career-wealth`) and a
  tappable anchor, and the contents list is rewritten into real links — resolved with the
  same matcher the PDF outline uses, and left as plain text when a label has no heading.
  The HTML previously had **no ids at all**.
- **Wide tables scroll inside their own box** (`tabindex="0"`, `role="region"`), so a
  six-column ten-god table never pushes the page sideways. Verified: no horizontal
  overflow at 390 / 768 / 1440 px.
- **The audio summary where the copy promises it** — an inline player in the MP3 section,
  which a PDF cannot honour.
- **`noindex, nofollow`** and a viewport tag. The link is unguessable and the route is
  private; a reader's report must still never be indexable.
- **The cover carries the brand line, not the 命 watermark.** The watermark is a CJK glyph
  and the print sheet embeds its fonts; a web document that must render identically
  everywhere cannot depend on the reader having a Korean font (without one it is a tofu
  box at 110pt on the front page).
- A `report-toolbar` slot the webapp fills with download links when it serves the report.
  The downloadable file is rendered without it.

### The PDF artefact (ReportLab backend)

`src/saju_html/md_to_saju_pdf.py` renders the client PDF, and builds the document **twice**:
the first pass measures the page count for the "Page N / M" footer *and* the page each
heading landed on, and the second prints. What the client receives:

- **A linked contents page.** Each entry links to its heading and prints the page that
  heading is on. Contents labels are not always literal headings (the engine writes
  composite ones, e.g. "Life Themes by Major Luck Period — incl. Lifetime Decade Roadmap"
  for the heading "Life Themes by Major Luck Period", and the MP3 heading is *longer* than
  its label), so links resolve exact-first, then by closest prefix in either direction, and
  otherwise fall back to plain text — a contents page never ships a link to nowhere. The
  two passes lay out identically because the page number sits in a fixed-width column, which
  is why the printed numbers match the pages they name.
- **An outline** (`/Outlines`) so readers get a section panel, plus **Title / Author /
  Subject / Creator** document metadata.
- **CJK: English with the Hanja beside it** (owner decision, 2026-10-16). The report is
  written in English and every Korean/Hanja term is translated, but the term itself is kept
  — `Direct Officer (正官)`, `Gye Mi (癸未)`, `the ten-god (십신)` picture. That is exactly the
  notation the engine already writes in its markdown; the renderer used to *erase* it by
  translating the Hanja gloss back into the English that preceded it and collapsing the
  duplicate. Drawing needs an embedded face, so the PDFs carry a bundled glyph subset of
  **Noto Sans KR** (`src/saju_html/fonts/SajuCJK-*.ttf`, OFL) — unlike the Korean CID faces it
  replaced, which rely on the reader's CMaps and render blank in browsers. A character no
  Korean face can draw (simplified-Chinese forms) is dropped with a warning rather than
  printed as a tofu box, and a `()` emptied by that drop is removed. Two exceptions are
  deliberate: the **audio script stays English-only** (`gloss=False`), because a narrator
  would read the parentheses out loud. After adding Hanja to `knowledge/`, regenerate with
  `python3 tools/build-cjk-font-subset.py`;
  `tests/test_pdf_navigation.py::test_cjk_font_covers_repo_cjk` fails until you do.
- Markdown **blockquote** notes read as notes (no literal `>` surviving into the page), and
  the body heading carries the tier name only — never the price.
- **`approve` runs a client-ready gate.** `tools/qa_client_ready.py` fails a draft that still contains the audit's defect classes (internal jargon, template debris, double glosses, a lowercase name, `a Earth`, a repeated word, a sentence repeated more than twice, a price). `intake_admin.py approve` runs it over the draft's markdown and PDF and refuses to issue the link unless you pass `--force`. If the PDF's text cannot be extracted at all — it needs `pdftotext` (poppler) — the gate reports `ARTEFACT_NOT_CHECKED` and blocks rather than passing silently: a draft's only readable text *is* the PDF, so silence would mean approving a report nothing had read.
- **The reader's letter is drafted at review time, not by a template.** The audit's §1 wants a
  one-page letter naming the two or three features that drive the whole reading, plus the caveat
  about birth-time accuracy — the page that proves a human read *this* order. `tools/suggest_letter.py`
  grounds a draft in the computed chart and short `knowledge/` excerpts, and a deterministic validator
  rejects anything ungrounded before a reviewer sees it (unknown citations, numbers absent from the
  facts, a missing birth-time caveat, the client-ready gate's own rules). It is **suggest-only and never
  in the delivery path**; the reviewer edits and the name is added downstream, so no identifying data
  is ever sent to a provider.
- **The engine's reviewer note never reaches the client.** The markdown the engine writes
  ends with *"Engine-generated premium report draft. Interpretive prose must be reviewed and
  finalized by a qualified reader…"* — a note to the reviewer. It was printing on the last
  page of the client's copy, telling a paying buyer (and falsely, since the owner reviews
  every paid report) that nobody had read their reading. `strip_engine_drafts` removes it in
  both backends; the review console reads the engine markdown, so the reviewer still sees it.

## Candidate folder conventions

Each person receiving a reading gets a dedicated subfolder:

```
candidates_horoscope/reports/{name-slug}/
├── {name-slug}-report.md          # base natal reading
├── {name-slug}-report.pdf         # the keepsake (PDF)
├── {name-slug}-report.html        # the reading (web document)
├── {name-slug}-combined.md        # base + follow-ups (optional)
├── {name-slug}-combined.pdf
├── {name-slug}-combined.html
├── career.md                      # follow-up topic files
├── relationships.md
├── health.md
└── 2027-outlook.md
```

Rules:
- Slug style: lowercase, hyphenated.
- Every canonical deliverable (base, combined, `career`, luck-cycle, tiers, compat pair) ships **three** siblings: the `.md` source, the `.pdf` keepsake and the `.html` reading. `tools/regen/pdfs.sh` writes the PDFs and `tools/regen/html.sh` writes the readings; both are run by `tools/regen_client_reports.sh`.
- Base report follows the 9-section premium scaffold from `knowledge/10-output-template.md`.
- Overlapping follow-ups append to the existing topic file with a dated heading (`## YYYY-MM-DD — summary`) rather than creating duplicates.
- Update the index table at the bottom of `candidates_horoscope/README.md` for every new candidate.

## Compatibility folder conventions

Each pair gets its own subfolder:

```
candidates_horoscope/marriage_compatibility/{name_a}_{name_b}/
├── {name_a}_{name_b}_compatibility.md        # basic tier
├── {name_a}_{name_b}_compatibility.pdf
├── {name_a}_{name_b}_compatibility.html      # the reading (web document)
├── {name_a}_{name_b}_compatibility_deep.md   # deep tier
├── {name_a}_{name_b}_compatibility_deep.pdf
└── {name_a}_{name_b}_compatibility_deep.html
```

Partner A is listed first; for heterosexual pairs Partner A is the male. Update the **Compatibility (궁합) readings** table at the bottom of `candidates_horoscope/README.md`.

## Premium 9-section scaffold

The Deep Destiny tier follows this structure (shorter tiers omit sections):

1. **Cover** — title, candidate info, Day Master, generation date.
2. **Chart at a Glance** — four-pillar table, element balance, quick reference, "What This Year Means for You" callout.
3. **Day Master Portrait** — strength, personality, tendencies.
4. **Career & Wealth** — best fields, wealth pattern, career archetypes.
5. **Relationships** — spouse palace, compatibility pattern, timing.
6. **Health & Vitality** — depleted-element watch, lifestyle cues.
7. **Timing: Major Luck & Annual Windows** — 대운 narrative + 2025–2030 windows.
8. **Practical Guidance Summary** — strengths, growth areas, recommendations, lucky attributes reference card.
9. **Closing Note** — synthesis of 2–3 specific chart features.

## Quality checklist before delivery

- Day Master identified and strength argued from seasonal + branch support.
- 용신/희신 derived, not asserted.
- Each pillar read in relation to the Day Master.
- Ten-god relationships used for personality/relationship/career.
- Special formations checked.
- Major-luck and annual luck integrated if the question is time-bound.
- Output follows `knowledge/10-output-template.md`.
- No claim beyond what the cited knowledge file supports.
- Citations stay in `.md` but are stripped from client PDFs automatically.

## Source anchors

- `knowledge/10-output-template.md`
- `knowledge/11-gunghap.md`
- `src/saju_engine/premium_report.py`
- `src/saju_engine/compat_report.py`
- `src/saju_html/combine_candidate_report.py`
- `tools/build-pdf.sh`
- `candidates_horoscope/README.md`
