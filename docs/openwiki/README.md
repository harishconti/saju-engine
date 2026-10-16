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

## Webapp documentation (separate set)

The paid, account-based web product — landing page, accounts, ordering, human review, private PDF
delivery — is documented in its own numbered set:

| Page | What it covers |
|---|---|
| [Webapp — Overview](../webapp/README.md) | Index for the whole set: architecture, data model, API, auth, report pipeline, frontend, services, deployment, operations, privacy, build plan, testing. |
| [Webapp — Services and integrations](../webapp/07-services-and-integrations.md) | The external-service and DNS checklist (start here if you are setting up infrastructure). |
| [Webapp — Build plan](../webapp/11-build-plan.md) | Phases, tasks, acceptance criteria, risk order. |

## Entry points

- **For readings and interpretations:** start with `CLAUDE.md`, then `knowledge/00-glossary.md` and `knowledge/09-interpretation-method.md`.
- **For engine and tooling:** start with [Architecture — Engine](architecture/engine.md) and [Operations — Toolchain and Testing](operations/toolchain-and-testing.md).
- **For product and delivery questions:** start with [Products — Reports](products/reports.md).
- **For the webapp, deployment, or infrastructure:** start with [Webapp — Overview](../webapp/README.md).
- **For project state and current priorities:** see `docs/MEMORY.md` and `README.md`.

## Maintenance

When the codebase changes in a way that affects any of these topics, update the relevant OpenWiki page before closing the task.
