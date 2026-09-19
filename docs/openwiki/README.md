# CosmicSaju OpenWiki

Structured documentation for the Korean Saju (사주, 四柱) project.

## Pages

| Page | What it covers |
|---|---|
| [Quickstart](quickstart.md) | Project overview, directory map, skill vs engine paths, where to go next. |
| [Architecture — Engine](architecture/engine.md) | `src/saju_engine/` module layout, chart computation flow, solar-time and 子時 conventions, CLI usage. |
| [Domain — Knowledge and Skill](domain/knowledge-and-skill.md) | Saju concepts, `knowledge/` file index, 9-step interpretation procedure, ground rules. |
| [Products — Reports](products/reports.md) | Client-facing tiers, report generation paths, candidate and compatibility folder conventions. |
| [Operations — Toolchain and Testing](operations/toolchain-and-testing.md) | PDF backends, intake servers, test suite, common commands, validation priorities. |

## Entry points

- **For readings and interpretations:** start with `CLAUDE.md`, then `knowledge/00-glossary.md` and `knowledge/09-interpretation-method.md`.
- **For engine and tooling:** start with [Architecture — Engine](architecture/engine.md) and [Operations — Toolchain and Testing](operations/toolchain-and-testing.md).
- **For product and delivery questions:** start with [Products — Reports](products/reports.md).
- **For project state and current priorities:** see `docs/MEMORY.md` and `tasks.md`.

## Maintenance

When the codebase changes in a way that affects any of these topics, update the relevant OpenWiki page before closing the task.
