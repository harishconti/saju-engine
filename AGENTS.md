# Agent Context — CosmicSaju

This file gives Claude Code agents quick orientation before they act on the Korean Saju project.

## First reads

1. `CLAUDE.md` — persona, ground rules, language conventions, quality checklist.
2. `docs/MEMORY.md` — current project state, test count, active wishes.
3. `docs/openwiki/` — deeper docs: architecture, domain concepts, products, toolchain.
4. `docs/market-research-2026-09.md` — sourced go-to-market research.

## Agent defaults

- **Tests first.** Run `pytest` before and after code changes. If you add a feature, add a regression test.
- **Cite `knowledge/`.** Any Saju interpretive claim must reference a file in `knowledge/`; do not invent doctrine.
- **Keep client deliverables auditable.** Citations belong in `.md` source files; PDF renderers strip them automatically.
- **Respect folder conventions.**
  - Single-chart reports: `candidates_horoscope/reports/{slug}/`.
  - Compatibility reports: `candidates_horoscope/marriage_compatibility/{name_a}_{name_b}/`.
  - Update `candidates_horoscope/README.md` indexes when adding either.
- **One subfolder per candidate / pair.** No duplicate topic files; append to existing topic files with dated headings.

## Common commands

```bash
# Test suite
pytest

# Premium report from chart
PYTHONPATH=src python3 -m saju_engine --date YYYY-MM-DD --time HH:MM --city "City" --gender M --format premium --tier deep --output-file report.md

# PDF rendering
./tools/build-pdf.sh --from-chart report.md "Title" "Client" "DOB" "Day Master"
./tools/build-pdf.sh --html --from-chart report.md "Title" "Client" "DOB" "Day Master"

# Combine base report + follow-ups
PYTHONPATH=src python3 src/saju_html/combine_candidate_report.py {name}
./tools/build-pdf.sh --combined {name} "Title" "Client" "DOB" "Day Master"

# Optional compliance QA gate on a report (needs TYPESAFE_API_KEY)
python3 tools/qa_compliance.py report.md
```

## Documentation maintenance

When the architecture, products, or toolchain change meaningfully, update the corresponding page in `docs/openwiki/`:

- `docs/openwiki/quickstart.md` — overview and directory map.
- `docs/openwiki/architecture/engine.md` — engine module layout and chart computation.
- `docs/openwiki/domain/knowledge-and-skill.md` — Saju concepts and interpretation procedure.
- `docs/openwiki/products/reports.md` — tiers, report pipeline, folder conventions.
- `docs/openwiki/operations/toolchain-and-testing.md` — CLI, PDF backends, tests.

The webapp layer (landing page, accounts, ordering, review, delivery, infrastructure) has its own
numbered set under `docs/webapp/`. Update it when the webapp, hosting, database, or pipeline change:

- `docs/webapp/00-overview.md` — scope, target flow, locked decisions.
- `docs/webapp/01-architecture.md` — the two deployables and why.
- `docs/webapp/02-data-model.md` — Prisma schema, invariants, retention.
- `docs/webapp/03-api-spec.md` — every route. **Update when adding a route.**
- `docs/webapp/04-auth-and-roles.md` — Neon Auth wiring and gates.
- `docs/webapp/05-report-pipeline.md` — engine contract, queue, review console, R2.
- `docs/webapp/06-frontend-ux.md` — routes, screens, landing-page sections, copy rules.
- `docs/webapp/07-services-and-integrations.md` — external services, DNS, credentials, cost.
- `docs/webapp/08-deployment.md` — Vercel projects, env scopes, CI, rollback.
- `docs/webapp/09-operations.md` — crons, health, runbooks.
- `docs/webapp/10-privacy-and-compliance.md` — PII, consent, retention, deletion, disclaimers.
- `docs/webapp/11-build-plan.md` — phases and acceptance criteria.
- `docs/webapp/12-testing.md` — test strategy and the two specialised gates.

Cross-cutting rules:

- A new API route → update `docs/webapp/03-api-spec.md` **and** the Playwright auth-gate spec.
- A schema or enum change → update `docs/webapp/02-data-model.md` + add a migration.
- A new external service or env var → update `docs/webapp/07-services-and-integrations.md` **and**
  `docs/webapp/08-deployment.md`.
- A tier or price change → update `docs/webapp/02-data-model.md` (tier map),
  `docs/webapp/07-services-and-integrations.md` (store config), **and**
  `docs/openwiki/products/reports.md`.
- **A new top-level route with UI → give it a layout.** Only `src/app/layout.tsx` (root) plus
  `dashboard/`, `admin/` and `reports/` render the shared `DashboardShell`. A page outside them renders
  into the bare `<body>`: no nav, no sign-out, no padding — which is what made `/admin` and
  `/reports/new` look broken, and was reported as *three* separate cosmetic bugs each time. The audit
  reports such a page as `NO SHELL`, but the fix is the layout, not the page.
- **Before claiming a frontend bar is met, run `python3 tools/audit-ui.py --strict`.** `06-frontend-ux.md`
  states a measurable bar; four of this project's bugs were documentation asserting a control the code did
  not have (`requiresReview`, `turnstileToken`, the admin role, the light theme). If you add to that bar,
  add it to the checker and say what the checker still does not cover.

## Out of scope

- Tarot, Zi Wei Dou Shu, QMDJ, Western astrology, standalone numerology.
- Auto-calculating four pillars without user confirmation.
- Medical/legal/financial certainty.
