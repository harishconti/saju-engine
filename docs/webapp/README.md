# Cosmic Saju Webapp — Documentation

Design and build reference for turning this repository into a **paid, account-based web product**:
a public marketing site, authenticated user accounts, report ordering, a human review console, and
private PDF delivery.

This set describes the **webapp layer**. The Saju engine itself is documented separately in
[`docs/openwiki/`](../openwiki/README.md).

## Pages

| # | Page | What it covers |
|---|---|---|
| 00 | [Overview](00-overview.md) | Product scope, target user flow, what exists today vs what is new, locked decisions. |
| 01 | [Architecture](01-architecture.md) | The two deployables, request paths, sequencing, and why the split is where it is. |
| 02 | [Data model](02-data-model.md) | Prisma schema, every model and field, invariants, indexing, retention. |
| 03 | [API spec](03-api-spec.md) | Every route: method, auth, request, response, error codes. |
| 04 | [Auth and roles](04-auth-and-roles.md) | Neon Auth wiring, user mirroring, gates, admin access. |
| 05 | [Report pipeline](05-report-pipeline.md) | Engine contract, job queue, dispatcher, review console, R2 storage. |
| 06 | [Frontend and UX](06-frontend-ux.md) | Route map, screens, landing-page sections, states, empty/error cases. |
| 07 | [Services and integrations](07-services-and-integrations.md) | Every external service, DNS, credentials, cost, critical path. |
| 08 | [Deployment](08-deployment.md) | Vercel projects, env scopes, CI/CD, release and rollback. |
| 09 | [Operations](09-operations.md) | Crons, health checks, runbooks, backups, incident response. |
| 10 | [Privacy and compliance](10-privacy-and-compliance.md) | PII handling, consent, retention, deletion, disclaimers. |
| 11 | [Build plan](11-build-plan.md) | Phases, tasks, acceptance criteria, sequencing. |
| 12 | [Testing](12-testing.md) | Test strategy across JS, Python, and end-to-end. |
| 13 | [Launch audit](13-launch-audit.md) | Point-in-time live-service audit and remediation. |
| 14 | [Security and hardening](14-security.md) | Threat boundaries, every control and where it lives, residual risks, deploy steps. |

## Reading order

- **Deciding whether to build it:** 00 → 11.
- **Building the backend:** 02 → 03 → 04 → 05.
- **Building the frontend:** 03 → 06.
- **Deploying it:** 07 → 08 → 09 → 10.
- **Just here for "what do I sign up for":** [07 — Services and integrations](07-services-and-integrations.md).

## Relationship to existing docs

| Document | Relationship |
|---|---|
| [`docs/openwiki/`](../openwiki/README.md) | The engine, knowledge base, PDF toolchain. **Unchanged by this work** except where noted in [11 — Build plan](11-build-plan.md). |
| [`docs/openwiki/products/reports.md`](../openwiki/products/reports.md) | Canonical tier names and prices. The webapp must not restate them with different values. |
| [`docs/openwiki/operations/toolchain-and-testing.md`](../openwiki/operations/toolchain-and-testing.md) | PDF backends, the existing FastAPI intake app, validation gates. |
| [`docs/MEMORY.md`](../MEMORY.md) | Persistent state and open items. |
| [`docs/market-research-2026-09.md`](../market-research-2026-09.md) | Positioning, pricing ranges, Merchant-of-Record choice, economics. |

## Ground rules that apply here too

These come from [`CLAUDE.md`](../../CLAUDE.md) and are **not** relaxed for the web layer:

1. **No auto-calculating four pillars without user confirmation.** The user enters birth data; the
   engine derives; the user sees and can correct it before ordering.
2. **No invented doctrine.** Any interpretive claim traces to `knowledge/`.
3. **No medical, legal, or financial certainty.** Report prose and site copy both.
4. **Citations stay in `.md`; client PDFs strip them.** Never let a citation or an internal
   reviewer note reach a client deliverable.
5. **Human review before client delivery** for every paid report (see [05](05-report-pipeline.md)).

## Maintenance

When any of these change, update the page in the same change:

- A new API route → [03](03-api-spec.md) **and** the Playwright auth-gate spec (see [12](12-testing.md)).
- A schema or enum change → [02](02-data-model.md) + a migration + the zod enum.
- A new external service or env var → [07](07-services-and-integrations.md) + [08](08-deployment.md).
- A new control, or a change to one → [14](14-security.md) (the bar) **and** a test that fails when
  the control is removed.
- A tier or price change → [07](07-services-and-integrations.md) (Dodo Payments map) **and**
  [`openwiki/products/reports.md`](../openwiki/products/reports.md).
