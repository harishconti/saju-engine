# Codex Instructions — Saju Project

When working inside this repository, load the following persistent context **in order** before taking any significant action:

1. `docs/MEMORY.md` — project state, conventions, decisions, quick commands
2. `CLAUDE.md` — persona, ground rules, interpretive workflow (applies equally to Codex)
3. `AGENTS.md` — agent onboarding defaults and common commands
4. `tasks.md` — prioritized task list and changelog
5. `improvements_issues.md` — go-to-market strategy, product/landing issues, backlog (+ `docs/market-research-2026-09.md`)
6. `README.md` — project overview and quickstart
7. `docs/openwiki/` — deeper docs: architecture, domain concepts, products, toolchain
8. `candidates_horoscope/README.md` — per-candidate folder and compatibility conventions

## Scope

This is a Korean Saju (사주 / 四柱 / Four Pillars of Destiny) calculation engine, PDF toolchain, and client-reporting pipeline. Keep all work grounded in the `knowledge/` reference files; do not invent traditional rules not present there.

## Triggered skills

- Use the `saju-reading` skill when the user asks for a chart reading, interpretation, or analysis of a single Saju chart.
- Use the `saju-client-order` skill when the user wants to turn a client order (name + birth data + chosen tier) into a deliverable PDF report.

If those skills are not available, fall back to the equivalent markdown instructions in `.claude/commands/saju.md` and `.claude/commands/saju-client.md`.

## Defaults

- Engine-first for Gregorian birth data; accept four pillars directly only when the user supplies them explicitly.
- Default Zi-hour convention is `korean` (야자시). Use `chinese` only when requested.
- Apply solar-time correction for Indian births (IST meridian 82.5°E offset).
- Engine-generated paid-tier reports are drafts requiring review before client delivery.
- Primary language: English, with Korean (한글) and Hanja (한자) on first use of technical terms.
