---
Task ID: 1
Agent: main
Task: Security hardening, modern landing page essentials, and integration testing

Work Log:
- Audited full codebase for security gaps, missing landing page elements, and data breach vectors
- Created `src/middleware.ts` — security headers (CSP, X-Frame-Options, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy), blocked path scanning (/.env, /.git, /wp-admin, etc.)
- Created `src/lib/rate-limit.ts` — in-memory sliding window rate limiter per IP
- Created `src/lib/validate.ts` — comprehensive input validation (email RFC-compliant, phone intl format, date validation, XSS/injection pattern detection, field length limits, honeypot detection, deep sanitization)
- Rewrote `src/app/api/submit/route.ts` — strict origin check (exact hostname, not .includes()), rate limiting (5/min), honeypot, full person validation, same-email fraud detection for compat, SMTP env check, input sanitization, proper error messages (no leak)
- Rewrote `src/app/api/contact/route.ts` — same security hardening (3/min rate limit), contact form validation, honeypot, sanitization
- Created `src/app/not-found.tsx` — themed 404 page
- Created `src/app/error.tsx` — error boundary with retry
- Created `src/app/loading.tsx` — cosmic loading spinner
- Created `src/app/sitemap.ts` — dynamic sitemap
- Created `src/app/robots.ts` — dynamic robots.txt (blocks /api/, references sitemap)
- Created `src/app/manifest.ts` — web app manifest
- Updated `next.config.ts` — poweredByHeader: false, security headers array
- Updated `src/app/layout.tsx` — canonical URL, fixed apple icon reference
- Updated `src/app/page.tsx` — honeypot fields on all 3 forms, 429 rate-limit handling with Retry-After toast on all 3 fetch calls
- Created `.env.example` — documents required SMTP env vars
- Updated `.gitignore` — added .env.production
- Removed static `public/robots.txt` (replaced by dynamic `robots.ts`)
- Created `vitest.config.ts` + test suite `src/lib/__tests__/validate.test.ts` (74 tests, all passing)
- Created `src/lib/__tests__/api.test.ts` — API integration tests (skipped by default, run with `npm run test:api` when dev server is up)
- Added `test` and `test:api` scripts to package.json

Stage Summary:
- 15 files created/modified
- Build passes clean (zero TS errors, zero build errors)
- 74/74 unit tests passing
- Security: CSP, HSTS, X-Frame-Options, rate limiting, origin validation, XSS detection, honeypot, input sanitization, env validation, path blocking, server fingerprint reduction
- Data protection: no raw SMTP pass fallback, error messages don't leak internals, same-email compat fraud detection
- Modern landing page: 404, error boundary, loading state, sitemap, robots, manifest, canonical URL
---
Task ID: (2026-09-07)
Agent: main
Task: Strategy pivot — USD / English-speaking-global positioning

Work Log:
- Repositioned from India / ₹ / Vedic-adjacent NRI framing to English-speaking-global / USD.
  Rationale + research: ../../improvements_issues.md and ../../docs/market-research-2026-09.md.
- `src/data/landing-data.ts`: PERSONAL_REPORTS + COMPAT_REPORTS prices ₹→USD
  (Essential $9→$19, Deep $55, Companion $9/mo, Compat Snapshot $24, Deep Compat $45);
  renamed "Marriage Compatibility" → "Compatibility (궁합)"; rewrote ABOUT_READER bio to the
  honest "engine + human, not a Korean master" line; reworked What-Is / What-You-Receive /
  Trust cards to the K-culture + honest-craft angle; added a 7-day-guarantee trust card and
  two FAQ entries ("Are you a Korean master?", "Do you offer a guarantee?").
- Synced the two other tier-label maps: `src/lib/page-helpers.ts`, `src/app/api/submit/route.ts`.
- `src/sections/FinalCTA.tsx`, `CompatibilityForm.tsx`, `CompatibilityReports.tsx`,
  `DemoReports.tsx`, `src/app/layout.tsx`: ₹→USD; "the boy and the girl" → "both people";
  form step labels "Boy/Girl Details" → "Partner A/B"; page <title> updated.
- Regenerated the demo PDFs in `public/` (demo-rm-*, demo-compat-*) from the fixed engine —
  now free of the internal reviewer-note leak (G1).
- LP3 (do-not-ship): the TESTIMONIALS array is fabricated. Added a prominent warning comment;
  it MUST be replaced with real permissioned reviews or removed before launch (FTC risk).
- Not done here (tracked in improvements_issues.md §12): real checkout, quiz funnel, embedded
  calculator, real WhatsApp number, deployment.

Stage Summary:
- `npm run build` clean; `npm test` 107 passed / 39 skipped.
- Internal `boy`/`girl` payload keys and `compatBoy`/`compatGirl` identifiers left as-is
  (not user-visible); renaming the API contract is a follow-up.

---
Task ID: (2026-09-07)
Agent: main
Task: Full landing-page redesign — restructure + Saju visual system

Plan: ../../docs/superpowers/plans/2026-09-07-landing-page-redesign.md
Spec: ../../docs/superpowers/specs/2026-09-07-landing-page-redesign-design.md
Tracker: ../../improvements_issues.md §5a (LP13)

Direction (user-approved 2026-09-07):
- Full restructure: ~15 sections → ~9, proof-first narrative arc. Demo report moves to
  section #4 (was #10); pricing after the reader understands + trusts the product.
- Premium-editorial aesthetic: keep dark cosmic + gold + Cormorant serif, but lead with
  diagrams / data-viz / credibility cues. Mysticism as accent, not theme.
- New visual system src/components/viz/: FourPillarsChart, ElementBalance (bars + wheel),
  LuckTimeline, DayMasterBadge, SectionHeading (eyebrow labels), ElementalRule,
  KoreanWatermark. Theme-aware SVG, responsive, prefers-reduced-motion-safe.
  Data: src/data/demo-chart.ts (RM / Kim Nam-joon real numbers from the engine report).
- Elemental palette tokens in globals.css (--el-wood/fire/earth/metal/water, --lean-*);
  elemental gradient rule motif; 四柱 low-opacity watermark; staggered scroll-reveal; one
  "hero chart draws itself" animation.
- Deleted sections: WhatIsSaju, WhatYouReceive, TrustClarity, ImportantDetails,
  ComparisonTable (content merged into WhySaju / WhatsInside / Pricing / HowItsBuilt).
- CTA system: one canonical primary label ("Get your free chart snapshot"), 2 button
  styles + 1 text link. FinalCTA drops its 5 tier buttons.
- Not touched: intake form contract, API routes, checkout, Testimonials gate,
  security headers / proxy.

Acceptance: npm run build + lint + test green; screenshot pass desktop+mobile /
light+dark for every section; 0 hydration warnings; prefers-reduced-motion clean;
Lighthouse >= pre-redesign; no horizontal body scroll.

Stage Summary (2026-09-07):
- New: src/lib/elements.ts, src/data/demo-chart.ts, 8 src/components/viz/* components
  (SectionHeading, ElementalRule, KoreanWatermark, DayMasterBadge, SealMark,
  FourPillarsChart, ElementBalance, LuckTimeline) + 26 vitest cases.
- New sections: WhySaju, WhatsInside, Pricing, CompareTiers, HowItsBuilt.
- Deleted: WhatIsSaju, WhatYouReceive, TrustClarity, ImportantDetails, ComparisonTable
  (+ their landing-data exports and the fake "15 slots/week" scarcity line).
- Rebuilt: Hero (split + live four-pillars chart + wheel + seal + 四柱 watermark),
  DemoReports (viz data card, moved to section #4, id="demo"), AboutReader, FAQ (grouped),
  FinalCTA (one CTA), Footer (elemental rule + 사주), Header (new nav + canonical CTA),
  MobileStickyCta. page.tsx <main> reordered to the 9-section arc; #reports → #pricing.
- globals.css: 오방색 --el-* tokens (+ .light), --lean-*, --seal, .eyebrow, .el-rule,
  .kr-watermark, .seal-mark, staggered reveal, pillar "stamp-in", reduced-motion reset.
  layout.tsx: added IBM Plex Mono as --font-mono. vitest.config: node project include
  broadened to src/**/*.test.ts; test-setup: afterEach(cleanup).
- Verify: npm run build clean · npm run lint clean · 133 vitest pass (39 api skipped) ·
  no horizontal body scroll at 390/768/1440 · 0 hydration errors · prefers-reduced-motion
  keeps content visible · light + dark both render.
- Follow-ups (non-blocking): WhatsInside right-column emptiness; form-section dead space;
  wheel base-ring grey segment; Essential card elemental-rule vs badge overlap.
