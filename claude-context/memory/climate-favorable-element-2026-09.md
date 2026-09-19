---
name: climate-favorable-element-2026-09
description: 2026-09-13 — added 조후 (climate-balance) cross-check to the natal 용신 engine; fixed a related compat.py scoring/override bug it exposed; regenerated affected candidate reports
metadata: 
  node_type: memory
  type: project
  originSessionId: 8b67e2bb-e0e4-430b-946b-a0734905bd1c
  modified: 2026-09-13T11:01:58.913Z
---

The user noticed Harish's Saju report's favorable element (용신, Fire) disagreed with an
independent reading (Water) and asked to validate the engine. Investigation confirmed the
four-pillar computation was already correct — cross-checked against `tests/test_textbook_cases.py`'s
9 independently-published historical Korean charts. The real gap: the engine's 용신 method only
implemented 抑扶 (strength-balance) and a "least-represented element" fallback for balanced charts,
missing 조후 (climate-balance, from 궁통보감/적천수) — both classical texts already named in
CLAUDE.md's persona but never wired into the actual determination logic.

**Why this matters for future sessions:** if another candidate's report ever gets flagged as
disagreeing with "another source" on 용신/희신, check first whether their Day Master is in a
balanced-verdict, hot (巳午未) or cold (亥子丑) month — climate now decides the headline element
there (`src/saju_engine/climate.py` + `src/saju_engine/yongsin.py::favorable_element()`). See
[[gtm-pivot-2026-09]] for the broader product context this engine sits inside, and
`docs/MEMORY.md`'s "Decisions to Remember" #9 for the exact resolution order.

**How to apply / key facts:**
- Full history: `docs/superpowers/specs/2026-09-13-climate-favorable-element-design.md` (design),
  `docs/superpowers/plans/2026-09-13-climate-favorable-element.md` (plan + all 6 tasks), executed
  via subagent-driven-development (this repo has no git — adapted mode, no commits/worktrees).
- A real, unplanned bug was found mid-implementation: `compat.py` had 4 scoring functions and its
  reader-override mechanism reading `strength_assessment["candidate_favorable"]` directly, bypassing
  the new climate merge — would have silently broken compat scoring/overrides for any
  balanced+hot/cold chart (Mahesh, the project's own canonical demo compat partner, is one). User
  chose "fix fully now" over deferring — see [[user-feedback-scope-decisions]].
- Confirmed only 2 of 6 "affected" natal candidates actually needed regeneration (Harish, Vishnu
  Priya) — Sruthi/Pawan/Gurumoorthy use a documented reader-argued `--favorable-override`
  (bypasses climate by design) and Mahesh's report is a fully hand-crafted Weak-DM analysis
  overriding the engine's own balanced auto-verdict. **Lesson: always check the actual delivered
  report file for a documented override before assuming the raw engine table applies to it** — an
  earlier draft of the regeneration task nearly over-corrected all 6 based on bare (no-override)
  engine computation alone.
- 3 items were explicitly found and flagged but NOT fixed this session (tracked in `docs/MEMORY.md`
  Open Items): `premium_report.py`'s "What This Year Means for You" line reads the wrong raw field
  (live-wrong in Sruthi's/Pawan's published reports); Harish's `career.md`/
  `land-workshop-business.md`/`luck-timeline.md` still argue stale Fire/Wood; `md_to_saju_compat_pdf.py`'s
  default `--output` path resolves to a wrong location (workaround: always pass `--output`
  explicitly).
- Same session, follow-on: created `candidates_horoscope/marriage_compatibility/harish_manvitha/`
  (both tiers) — a fresh, no-override validation of the new engine (Manvitha: 甲 Day Master,
  strong, 亥월 → Fire/Earth). Composite 70/100, Strong.
