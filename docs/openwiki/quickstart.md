# OpenWiki Quickstart

## What this repository is

This repository is a Korean Saju (사주, 四柱 / Four Pillars of Destiny) project that combines:

- a Claude Code skill and instruction set for readings,
- a Python chart engine that derives pillars and overlays,
- a PDF/report toolchain,
- client intake flows, and
- a stored library of candidate readings.

The authoritative human-facing summary is in [`README.md`](../../README.md). The agent rules live in [`CLAUDE.md`](../../CLAUDE.md), and the persistent project memory is in [`MEMORY.md`](../MEMORY.md).

## What to read first

1. [Knowledge and skill map](domain/knowledge-and-skill.md) — the interpretive vocabulary, knowledge files, and reading procedure.
2. [Engine and architecture](architecture/engine.md) — how the chart is computed and how the engine data model is structured.
3. [Products and reports](products/reports.md) — single-chart tiers, compatibility reports, and candidate folder conventions.
4. [Operations and toolchain](operations/toolchain-and-testing.md) — CLI entry points, PDF generation, intake apps, and tests.

## Main execution paths

### 1) Human reading workflow

The `/saju` skill path is driven by `.claude/commands/saju.md` and `CLAUDE.md`.
It is meant for interpretation using the knowledge base under `knowledge/`, and it now has an engine-first policy when users provide birth date, time, and place.

### 2) Engine / product workflow

The `saju-engine` Python package lives under `src/saju_engine/` and computes charts, compatibility scores, premium report scaffolds, and related overlays. That engine feeds the PDF builders in `tools/` and the intake apps.

## Repository shape

- `knowledge/` — the canonical Saju knowledge base and output template.
- `src/saju_engine/` — chart derivation, compatibility, luck overlays, report generation.
- `tools/` — PDF renderers, intake forms/servers, report combiner, validation helpers.
- `candidates_horoscope/` — stored reports, compatibility readings, and intake output.
- `tests/` — pytest coverage for engine, CLI, PDF, compat, and report layers.

## Notable constraints

- The project distinguishes Korean `야자시` and Chinese `조자시` conventions; the engine defaults to Korean semantics.
- Solar-time correction is enabled by default for non-standard longitudes.
- Premium outputs are draft-generated and explicitly require human review before client delivery.
- The docs below intentionally avoid reading secrets or `.env` files.

## Best starting points for changes

- Change chart derivation or timing rules: [Engine and architecture](architecture/engine.md)
- Change reading rules or wording: [Knowledge and skill map](domain/knowledge-and-skill.md)
- Change products, report structure, or compat logic: [Products and reports](products/reports.md)
- Change CLI/PDF/intake/testing behavior: [Operations and toolchain](operations/toolchain-and-testing.md)

## Source anchors

- `README.md`
- `CLAUDE.md`
- `docs/MEMORY.md`
- `pyproject.toml`
- `src/saju_engine/engine.py`
- `src/saju_engine/chart.py`
- `src/saju_engine/pillars.py`
- `src/saju_engine/compat.py`
- `src/saju_engine/compat_report.py`
- `knowledge/09-interpretation-method.md`
- `knowledge/10-output-template.md`
