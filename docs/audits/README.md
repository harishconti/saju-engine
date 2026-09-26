# Engine Audits — Historical Record

These are **point-in-time audit reports**. They are kept for the reasoning and
context they captured, but they are **superseded** by the current state of the
code and by the live trackers:

- **Current open work / go-to-market:** `../../improvements_issues.md`
- **Engine issue tracker (with fix history):** `../issues_bugs.md`
- **Project state & decisions:** `../MEMORY.md`
- **Task changelog:** `../../tasks.md`

Do not treat file paths, test counts, or "open bug" lists in these documents as
current — verify against the code.

| File | Date | Scope | Outcome |
|---|---|---|---|
| `2026-07-05-engine-audit.md` | 2026-07-05 | Full engine (then `tools/saju_engine/`, ~9,500 LOC) + tests + knowledge doctrine, via 7 parallel agents | Findings triaged into `issues_bugs.md`; all resolved. Baseline was 441 pytest. |
| `2026-08-10-architecture-audit.md` | 2026-08-10 | Full codebase architecture review (A1–A17 debt items) | Fixes A1–A17 landed; debt rows reconciled. Some claims later found stale — see the addendum. |
| `2026-08-22-engine-audit-addendum.md` | 2026-08-22 | Re-validation of the 2026-08-10 report against live code + 4 agent deep-dives | Confirmed A1–A17; corrected ~8 stale debt rows; found the compat-scoring / daeun-floor / report-leak cluster. Those Phase-0 fixes and the 2026-09-07 client-launch fixes (G1–G3) are done — see `issues_bugs.md`. |
| `2026-09-26-deep-engine-audit.md` | 2026-09-26 | Fresh deep audit after E-1…E-13 closed: calculation, 절기 data (ephemeris cross-check, `scripts/check_solar_terms.py`), strength/용신 doctrine, stars/grids, compat, web tools, CI | **Open** — 21 findings (N-1 P0, N-2…N-8 P1). See its §4 for fix order. |

The code has since moved to `src/saju_engine/` and `src/saju_html/`, the suite is
at 590 pytest, and the three client-launch blockers (G1–G3) plus the ₹→USD pivot
were completed 2026-09-07.
