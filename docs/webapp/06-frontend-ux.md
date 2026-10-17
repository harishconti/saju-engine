# 06 — Frontend and UX

Two audiences in one Next.js app: an anonymous visitor deciding whether this is real, and a
signed-in client (plus the owner) managing reports. The design system is inherited from the existing
landing page — dark cosmic base, gold accent, Cormorant Garamond for display, IBM Plex Mono for
numerals and pillar tables, and the 오방색 five-element tokens.

## The reading uses the app's design system

The delivered report is a client-facing surface of this product, so it is held to the same design
standard as the app it belongs to: the report's web layer (`src/saju_html/theme-web.css`) is written
against the tokens in `apps/web/src/app/globals.css` — same palette, same type scale, same card and
callout idioms, same 44 px control bar, dark by default with the OS light palette.

- `tests/test_web_report.py::test_report_tokens_match_the_webapp` compares the mirror to
  `globals.css` in both schemes, so the two cannot drift.
- It is a **self-contained** file: inline CSS, inline SVG, no scripts, and the app's three faces
  **embedded as subsetted `woff2`** rather than linked. The app's own `layout.tsx` pulls them from a
  Google Fonts `<link>`; a delivered reading cannot, both because it must be one file and because a
  third-party font request would tell someone when a client opened their report. The rendered reading
  makes **zero network requests**. `tests/test_web_report.py` compares the embedded families to the
  `--font-*` tokens here, so the two cannot drift.
- Print is deliberately separate: `theme.css` remains the A4 sheet, and `@media print` in the web
  layer hands the page back to it, so the PDF and its golden snapshots are unaffected.

## Route map

```
PUBLIC                                 AUTHENTICATED                        ADMIN
────────────────────────────────       ──────────────────────────────       ──────────────────────
/                  landing + sections  /dashboard          overview          /admin
/sample            free sample flow    /dashboard/reports  library           /admin/reports/{id}
/privacy           legal               /dashboard/reports/{id}  one report
/terms             legal               /dashboard/profiles people
/refund-policy     legal (required by  /dashboard/orders   purchases
                    Dodo Payments)     /dashboard/account  settings + consent + deletion
/login             sign in / sign up   /reports/new        order flow
/auth/complete     OAuth / magic-link landing
```

This map is the build output, not an intention — it was corrected on 2026-10-16 because it listed
`/admin/queue`, `/admin/orders`, `/consent` and `/reports/{id}`, **none of which exist**. `/pricing`,
`/about` and `/faq` are anchors on `/`, not routes; the review queue *is* `/admin`; consent is managed on
`/dashboard/account`; and a single report is `/dashboard/reports/{id}`.

**Every authenticated and admin route sits inside a layout that renders `DashboardShell`**
(`dashboard/`, `admin/`, `reports/`). A top-level route with UI that is not inside one renders straight
into the bare `<body>` — no nav, no padding — which is what made `/admin` and `/reports/new` look broken.
The audit tool reports such a page as `NO SHELL`.

The landing page is **one route with anchored sections**, not eight routes. That matches the existing
9-section narrative arc, keeps internal links cheap, and means the marketing content is one Server
Component tree rather than eight route boundaries.

## Landing page sections

Rebuilt from the archived static prototype at `misc/landing-page/archive/cosmicsaju_landing.html`. (The
legacy `apps/landing-page/` scaffold — whose `src/` was never in this repo — was deleted 2026-10-17;
its section inventory in `worklog.md` remains in git history at `fa2eab0`.)

| # | Section | Job | Notes |
|---|---|---|---|
| 1 | **Hero** | Answer "what is this?" in five seconds | Live four-pillars chart that draws itself, element wheel, seal mark, 四柱 watermark. The single animated flourish |
| 2 | **Why Saju** | Frame the category and the honest positioning | Merged from the former WhatIsSaju + WhySaju |
| 3 | **Demo reports** | Show the actual artefact | Real RM demo **readings** and PDFs, plus the two compatibility demos — each tier offers the web document first ("Read it"), then Save and PDF, mirroring the product's download order. Also the `FourPillarsChart` / `ElementBalance` / `LuckTimeline` visuals built from RM's real chart data |
| 4 | **Pricing** | Price, after trust is established | All five tiers: the three single-chart cards, then a labelled **For two people** block with both compatibility readings. Prices come from `lib/tiers.ts`, never prose. The free sample is the entry CTA |
| 5 | **Compare tiers** | Remove choice paralysis | The table is **scoped to the single-chart tiers** and says so in its caption/`aria-label` — its rows (Day Master, 대운 table, relationships, year-by-year timing) are single-chart concepts, so two-chart columns would misrepresent them. One canonical primary CTA: *"Get your free chart snapshot"* |
| 6 | **How it's built** | Justify the price against a $9.99 competitor | The engine-and-honest-interpreter story: cited classical principles, the human review step, what we will not claim |
| 7 | **About the reader** | Put a human behind it | The honest "engine + human, not a Korean master" line |
| 8 | **FAQ** | Handle the real objections | Grouped. Must include "Are you a Korean master?" and "Do you offer a guarantee?" |
| 9 | **Final CTA + footer** | Convert and close | One CTA, elemental rule motif, 사주 mark |

Plus, persistently: **header** (nav + canonical CTA) and a **mobile sticky CTA**.

**The header reflects who is looking at it.** Signed out: `Sign in` (ghost) + `Free chart snapshot`
(primary). Signed in: `Dashboard` (primary), with the snapshot CTA demoted to secondary. `SiteHeader`
takes the session as a prop and each caller reads it. It was previously hardcoded to `Sign in`, and `/`
was statically prerendered, so a signed-in visitor was still invited to sign in — the page had no way to
know. Reported by the owner right after signing up.

- **Consequence to keep in mind: `/`, `/privacy`, `/terms` and `/refund-policy` are now dynamic**
  (`export const dynamic = "force-dynamic"`). Rendering the shell from the session opts a route out of
  static prerendering, so those pages are server-rendered per request and are not CDN-cacheable. That is
  the deliberate trade while the CTA matters more than static caching. If it ever needs reverting, the
  honest alternative is a client-side upgrade that **degrades to the signed-out header on failure** — a
  client patch that fails open would show the wrong state silently, which is the same class of bug this
  page keeps producing.

**Every authenticated page shares one shell.** The sidebar/mobile-nav/footer/padding markup lives in
`components/dashboard/shell-frame.tsx`, used by **three** layouts: `dashboard/`, `admin/` and `reports/`.
Two of those existed only because the missing one was reported as a cosmetic complaint:

- `/admin` had **no layout at all**, so the review console rendered straight into `<body>` — no
  navigation, no sign-out, no route back to the dashboard, no padding. Reported as three separate
  problems ("no back button", "no dashboard button", "padding is not good"); it was one missing file.
- `/reports/new` (the ordering flow) had the same gap for the same reason, and looked broken for it —
  the wizard inside it was perfectly well structured, which is the tell: **when a page looks wrong
  "however you arrange the contents", suspect the shell.**

⚠️ **Rule: a top-level route with UI needs a layout.** Only `src/app/layout.tsx` (root) plus these three
provide one. Anything else renders into the bare `<body>` with no padding. The audit that catches this is
one pass over `src/app/**/page.tsx` checking each page for a shell, its own container, or a delegated one
(`LegalLayout`, `SiteHeader`).

**The ordering page itself.** `ProfileForm`-style tidiness: the inline `← Dashboard` link was removed
once the shell supplied the nav (it was duplicated navigation rendered directly under the header), and
the sample-report link moved from a trailing orphan paragraph into the page header's action slot.

**Consent is asked for where it bites.** `ProfileForm` takes `hasConsent`; when the account holds no
active `service` consent the form shows the privacy-policy checkbox **inline**, above the save button,
and records consent immediately before writing the profile. The server refuses the write either way
(`403 CONSENT_REQUIRED`) — the point of the inline prompt is that the refusal is actionable there and
then, rather than reading as a save that silently did nothing.

### Copy rules

- **Delivery expectation must be stated.** Decision D5 means paid reports are reviewed first. The
  site says reviewed-and-delivered within a stated window; it must not imply instant delivery. Vague
  promises here are the most likely source of a refund dispute.
- **No fabricated testimonials.** The current array is flagged in the worklog as illustrative and a
  documented FTC risk (LP3). Replace with real, permissioned reviews or **remove the section**. Do not
  ship placeholders.
- **No price/claim drift.** Prices come from the tier map, not from prose. See
  [`openwiki/products/reports.md`](../openwiki/products/reports.md) as the canonical source.
- **No medical, legal, or financial certainty** anywhere on the site — the same ground rule as the
  report prose.
- **Scarcity is not invented.** The previous "15 slots/week" line was removed for being fake. Do not
  reintroduce manufactured scarcity.
- **Which address appears where.** The footer's Contact block and any *"reply to us"* prompt use
  **`hello@cosmicsaju.com`** (`NEXT_PUBLIC_CONTACT_EMAIL`). **`privacy@cosmicsaju.com`**
  (`NEXT_PUBLIC_LEGAL_CONTACT_EMAIL`) appears **only** where someone is exercising a data right — the
  privacy policy's DSAR paragraph and the account page — so those requests are recognisable on arrival.
  Both resolve from `apps/web/src/lib/contact.ts`; never inline an address in a component.

## Key screens

### Free sample (`/sample`)

The funnel, and the only place a visitor does real work before signing up.

```
Step 1  Birth data        name · gender · date · time · "I don't know my time" · city
Step 2  Confirm the chart the derived four pillars are shown for confirmation
                          ← this is a product requirement, not a nicety
Step 3  Result            Reading preview + PDF preview + download, then:
                          "Keep this — create an account and I'll save these details"
```

- **Gender is required** and the form must say why (major-luck direction is undefined without it).
- **"I don't know my birth time"** is a first-class path: it sets `timeKnown: false` and the UI
  explains that the hour pillar becomes uncertain and the report will say so.
- **City** is a typeahead against the bundled city table; it resolves coordinates without any
  network geocoding.
- Solar-term and hour-boundary knife-edges surface as a confirmation, not a silent guess.
- Turnstile is invisible; it only appears if it challenges.
- The whole flow is usable without an account, and the "keep this" step is where the account is
  created. **Do not gate the sample behind sign-up** — it is the only proof the product works.

### `/dashboard`

Overview: the default profile's four pillars, the most recent report, and the two next actions
("Get a deep reading", "Add a partner for compatibility").

Empty states matter more than usual here:

| State | Message |
|---|---|
| No profiles | "Add your birth details to see your chart" |
| No reports | "Your free sample is waiting — generate it now" (with the sample CTA) |
| Report `DRAFT_READY` / `IN_REVIEW` | "In review — we're checking your reading before sending it. Usually within a day." |
| Report `FAILED` | "Something went wrong with this report — we're on it. You haven't been charged twice." |

That third state is load-bearing: because every paid report is reviewed, `DRAFT_READY` is the
*normal* state for a while. The UI must make waiting feel like care, not like a broken product.

### `/reports/new` (order flow)

```
1  Choose a reading     tier cards with price, page count, and contents
2  Choose profiles      A (required) · B (compat only, required for compat tiers)
3  Confirm              chart shown again for both profiles (for compat: the pair)
4  Pay                  → Dodo Payments hosted checkout (off-site)
5  Return               /dashboard/reports with the order in "awaiting review"
```

Price is displayed from the server tier map and re-resolved server-side on submission. If the client
and server disagree, the server wins and the UI shows the server's number.

### `/reports/{id}`

Chart summary, tier, status timeline (ordered → generated → reviewed → delivered), page count,
download, and — if superseded — an explicit "a newer version exists" notice. Never silently swap the
file under a client.

**This is where the reading lives**, so it is the only screen with per-format actions: **Read your
reading** (primary) → **Save** → **PDF**. It reads them from `report.htmlKey`, so a report rendered
before the web document existed offers the PDF alone rather than a dead "read" link.

### `/dashboard/reports`

The library: one row per report, **one action per row — `Details`**. No download button, and
deliberately no per-format buttons: the row used to carry a `Download PDF` that called the download
route with no `kind`, which resolves to the **web document** by default — so the button labelled "PDF"
handed back the reading. A row is a pointer, not a download manager. The reading, the Save and the PDF
all live one click away on `/dashboard/reports/{id}` (above), which is also the only place that can
explain *why* an older report has no reading ("regenerate to add it").

### `/admin/reports/{id}`

The review console described in [05](05-report-pipeline.md) §5. Layout: PDF viewer on the left,
decision panel on the right (override select, regenerate, compliance QA result, approve/reject with
reason). Keyboard-friendly, because the reviewer may do this repeatedly.

**The audio panel has two routes to an MP3.** `Prepare audio` queues the text-to-speech narration, and is
offered only where the tier promises one. **`Upload MP3`** is offered wherever the report has an order, so
a hand-recorded narration — or the audio a compatibility customer asks for under the report's cross-sell —
can be attached. The upload is **presigned PUT → R2 → confirm**, never a form post: a ten-minute MP3 is
~10 MB and a Vercel function body is capped near 4.5 MB, which is exactly why the bucket needed the CORS
rule in [07](07-services-and-integrations.md) §CORS.

## Component conventions

| Concern | Rule |
|---|---|
| Primitives | `src/components/ui/` only — Button, Field/TextInput/DateInput/Textarea/Select, Alert, Toast, ConfirmDialog, Sheet, Skeleton, EmptyState, Badge, Lightbox |
| Styling | Semantic tokens only (`--background`, `--foreground`, `--primary`, `--el-wood`…) — never a raw hex in a component |
| Charts | In-house SVG under `src/components/viz/` — `FourPillarsChart`, `ElementBalance`, `LuckTimeline`, `DayMasterBadge`, `SealMark`, `KoreanWatermark`, `SectionHeading`, `ElementalRule` |
| Theming | Dark is the brand surface (`:root`); **`@media (prefers-color-scheme: light)`** swaps the token set for visitors whose OS asks for light. Both must render every screen. ⚠️ This row used to name `next-themes` and a `.theme-light` class — **neither existed**: the class was on nothing, so a complete light palette sat dead in `globals.css` while this table claimed a theme system. Corrected 2026-10-16 by wiring the tokens to the media query. There is deliberately **no user-facing toggle**; add one only if asked, and move the block behind a class if so |
| Motion | Subtle, `prefers-reduced-motion`-safe. Content must be fully visible with motion disabled |
| Targets | **≥44 px on controls** (buttons, tabs, selects) — `buttonClasses("sm")` is `h-11` for exactly this reason, not the usual 36 px. Text links follow WCAG 2.5.8's **spacing exception** instead (small is allowed when targets are far enough apart); the footer link lists carry `py-1` so they clear the 24 px minimum outright. No `window.confirm` |
| Roles | Hide write affordances from non-owners rather than letting them fail |
| Data fetching | Server Components read Prisma directly with `force-dynamic`; **no client fetching of own APIs** for reads |
| Forms | zod schema shared between client and server where practical |

## Accessibility and quality bar

The acceptance bar carried over from the previous redesign, and still the bar:

- Lighthouse ≥ the pre-redesign baseline.
- No horizontal body scroll at **360** / 390 / 768 / 1440, and **no element whose right edge passes the
  viewport** at those widths — checked element by element, not only at page level, and exempting anything
  inside an ancestor with `overflow-x: auto|scroll`, which is *supposed* to overflow. 360 is the default
  logical width of most Android phones — the smallest width this bar claims — and it is checked because a
  390-only audit missed a real defect: the landing header's CTA ran 27px past a 360dp viewport and was
  **clipped**, so nothing scrolled to reveal it and a page-level scroll check saw nothing. Only an
  element-level check at the real width could see it (2026-10-17). The audit reads these widths **out of
  this page** and refuses to run if they disagree with its own viewport list — because they did disagree
  once, and this page and the docstring both promised 360 while the code measured only 390 / 768 / 1440.
- **What the checker still does not cover**, so it is not read as more than it is: 320dp (the smallest
  devices); overflow off the **left** edge (the element check tests `right > viewport`, and reports at most
  the first four offenders); text clipped *inside* an element that is itself within the viewport (a
  squeezed button or an ellipsised label); and whether a horizontally scrollable table is *discoverable*
  as swipeable on a phone. The wide tier-comparison table is exempt on purpose — it sits in an
  `overflow-x-auto` box.
- Zero hydration warnings.
- `prefers-reduced-motion` leaves all content visible.
- Light and dark both render on every screen.
- axe clean (light and dark) on every screen, **asserted** — see below.
- Keyboard reachable: every control, including the admin override select and the PDF viewer's page
  controls.

**What actually asserts this bar: `tools/audit-ui.py`**, run in CI by the `ui` job. It measures, per page
and per viewport, in **both colour schemes**: horizontal overflow (ignoring anything inside an
`overflow-x: auto` ancestor, which is *meant* to overflow), axe-core violations with the offending node,
hydration warnings, one `<h1>`, whether a shell is present, and sub-44 px controls (text links are
reported separately, per the spacing exception). `--strict` makes any of those a build failure.

⚠️ **What it does *not* cover**, so nobody assumes otherwise: **Lighthouse** (no budget is asserted here
— the line above is aspirational until it is), `prefers-reduced-motion` content visibility, keyboard *tab
order*, screen-reader reading order, contrast beyond what axe checks, or any page behind the login (the
tool can do authenticated runs with `AUDIT_EMAIL`/`AUDIT_PASSWORD`, but CI does not, so the dashboard,
`/admin` and the ordering flow are audited only when someone runs it deliberately).

Two findings this bar was silently failing until 2026-10-16: `.theme-light` was dead CSS (above), and the
footer overflowed 27 px at exactly 768 px on five pages because it switched to a row at `md` where the
brand block plus three columns cannot fit.

## Anti-patterns to avoid

| Anti-pattern | Why it is wrong here |
|---|---|
| Gating the free sample behind sign-up | The sample is the only proof the product works |
| Hiding the derived pillars until after payment | Violates the project's own ground rule about auto-calculated charts |
| Implying instant delivery | D5 means review first; the copy must match |
| A spinner that never resolves | `DRAFT_READY` is normal — show a status timeline, not a spinner |
| Fabricated reviews | Documented FTC risk |
| A second design system for the app shell | The dashboard inherits the landing page's tokens, or the product looks bolted together |
| Client-side price display without a server re-check | Trivially tampered |
