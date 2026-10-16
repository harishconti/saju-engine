# 06 — Frontend and UX

Two audiences in one Next.js app: an anonymous visitor deciding whether this is real, and a
signed-in client (plus the owner) managing reports. The design system is inherited from the existing
landing page — dark cosmic base, gold accent, Cormorant Garamond for display, IBM Plex Mono for
numerals and pillar tables, and the 오방색 five-element tokens.

## Route map

```
PUBLIC                                 AUTHENTICATED                    ADMIN
────────────────────────────────       ────────────────────────────     ──────────────────────
/                  landing             /dashboard        overview       /admin               
/sample            free sample flow    /dashboard/reports  library       /admin/queue
/pricing           (anchor on /)       /dashboard/profiles profiles      /admin/reports/{id}
/about             (anchor on /)       /dashboard/orders   purchases     /admin/orders
/faq               (anchor on /)       /dashboard/account  settings
/privacy           legal               /reports/new        order flow
/terms             legal               /reports/{id}       report detail
/refund-policy     legal (required by
                    Dodo Payments)
/login             sign in / sign up
/auth/complete     OAuth / magic-link landing
/consent           consent management
```

The landing page is **one route with anchored sections**, not eight routes. That matches the existing
9-section narrative arc, keeps internal links cheap, and means the marketing content is one Server
Component tree rather than eight route boundaries.

## Landing page sections

Rebuilt from the section inventory preserved in `apps/landing-page/worklog.md` and the archived
static prototype at `misc/landing-page/archive/cosmicsaju_landing.html`.

| # | Section | Job | Notes |
|---|---|---|---|
| 1 | **Hero** | Answer "what is this?" in five seconds | Live four-pillars chart that draws itself, element wheel, seal mark, 四柱 watermark. The single animated flourish |
| 2 | **Why Saju** | Frame the category and the honest positioning | Merged from the former WhatIsSaju + WhySaju |
| 3 | **Demo reports** | Show the actual artefact | Real RM demo PDFs (regenerated with ReportLab — see [05](05-report-pipeline.md) §1), plus the `FourPillarsChart` / `ElementBalance` / `LuckTimeline` visuals built from RM's real chart data |
| 4 | **Pricing** | Price, after trust is established | Four tiers + the free sample as the entry CTA. `CompareTiers` follows |
| 5 | **Compare tiers** | Remove choice paralysis | Table across tiers, one canonical primary CTA: *"Get your free chart snapshot"* |
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
Step 3  Result            PDF preview + download, then:
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

### `/admin/reports/{id}`

The review console described in [05](05-report-pipeline.md) §5. Layout: PDF viewer on the left,
decision panel on the right (override select, regenerate, compliance QA result, approve/reject with
reason). Keyboard-friendly, because the reviewer may do this repeatedly.

## Component conventions

| Concern | Rule |
|---|---|
| Primitives | `src/components/ui/` only — Button, Field/TextInput/DateInput/Textarea/Select, Alert, Toast, ConfirmDialog, Sheet, Skeleton, EmptyState, Badge, Lightbox |
| Styling | Semantic tokens only (`--background`, `--foreground`, `--primary`, `--el-wood`…) — never a raw hex in a component |
| Charts | In-house SVG under `src/components/viz/` — `FourPillarsChart`, `ElementBalance`, `LuckTimeline`, `DayMasterBadge`, `SealMark`, `KoreanWatermark`, `SectionHeading`, `ElementalRule` |
| Theming | `darkMode: 'class'` via `next-themes`; both themes must render every screen |
| Motion | Subtle, `prefers-reduced-motion`-safe. Content must be fully visible with motion disabled |
| Targets | ≥44 px touch targets; no `window.confirm` |
| Roles | Hide write affordances from non-owners rather than letting them fail |
| Data fetching | Server Components read Prisma directly with `force-dynamic`; **no client fetching of own APIs** for reads |
| Forms | zod schema shared between client and server where practical |

## Accessibility and quality bar

The acceptance bar carried over from the previous redesign, and still the bar:

- Lighthouse ≥ the pre-redesign baseline.
- No horizontal body scroll at 390 / 768 / 1440.
- Zero hydration warnings.
- `prefers-reduced-motion` leaves all content visible.
- Light and dark both render on every screen.
- axe clean (light and dark) on every screen, asserted in e2e.
- Keyboard reachable: every control, including the admin override select and the PDF viewer's page
  controls.

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
