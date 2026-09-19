---
name: user-feedback-scope-decisions
description: "User prefers fixing correctness bugs fully in-scope over deferring, even when they expand beyond the original plan, once the bug reaches paid client deliverables"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8b67e2bb-e0e4-430b-946b-a0734905bd1c
  modified: 2026-09-13T11:02:12.244Z
---

When a subagent-driven implementation (see [[climate-favorable-element-2026-09]]) surfaced a real,
unplanned bug — `compat.py` bypassing the new favorable-element resolver, which would silently
defeat compat scoring/overrides for an entire class of charts — I presented three options: full
fix now (touching an explicitly out-of-scope file), a narrower partial fix, or defer entirely. The
user chose the full fix. Later in the same session, when a review found the fix itself introduced
a new cross-deliverable contradiction (two candidates' compat report disagreeing with their own
individual natal reports on one field), I again presented options (fix the natal reports, revert
the compat change, or leave both as-is) — the user again chose to fix forward (update the natal
reports to the classically-correct value) rather than revert or defer. When later asked to also
fix 3 more flagged-but-deferred items, they said "fix all 3" rather than picking a subset.

**Why:** these are real, paid client deliverables (CosmicSaju reports/PDFs); the user treats
internal consistency and correctness in delivered content as worth fixing immediately even at the
cost of expanding a plan's scope, rather than shipping a narrower fix and leaving known
inconsistencies for later.

**How to apply:** when a fix surfaces a related correctness bug in already-delivered client
content, default to recommending the full/forward fix as the primary option (not just "defer" or
"narrow scope") when presenting the choice — this matches the user's demonstrated preference. Still
present the options and let them confirm for anything that expands scope beyond what was explicitly
approved, per the project's plan-conflict-resolution norms — don't skip the check, just weight the
recommendation accordingly.
