# Agent Context — CosmicSaju

This file gives Claude Code agents quick orientation before they act on the Korean Saju project.

## First reads

1. `CLAUDE.md` — persona, ground rules, language conventions, quality checklist.
2. `docs/MEMORY.md` — current project state, test count, active wishes.
3. `tasks.md` — prioritized task list and completion status.
4. `improvements_issues.md` — go-to-market strategy, product/landing issues, prioritised P0–P3 backlog
   (sourced research: `docs/market-research-2026-09.md`).
5. `docs/openwiki/` — deeper docs: architecture, domain concepts, products, toolchain.

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
```

## Documentation maintenance

When the architecture, products, or toolchain change meaningfully, update the corresponding page in `docs/openwiki/`:

- `docs/openwiki/quickstart.md` — overview and directory map.
- `docs/openwiki/architecture/engine.md` — engine module layout and chart computation.
- `docs/openwiki/domain/knowledge-and-skill.md` — Saju concepts and interpretation procedure.
- `docs/openwiki/products/reports.md` — tiers, report pipeline, folder conventions.
- `docs/openwiki/operations/toolchain-and-testing.md` — CLI, PDF backends, tests.

## Out of scope

- Tarot, Zi Wei Dou Shu, QMDJ, Western astrology, standalone numerology.
- Auto-calculating four pillars without user confirmation.
- Medical/legal/financial certainty.
