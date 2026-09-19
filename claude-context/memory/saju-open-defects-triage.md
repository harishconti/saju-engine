---
name: saju-open-defects-triage
description: "Triage of the 13 engine/report defects the 2026-09 validation campaign pinned but never fixed — which are client-visible, the fix-order dependency, and the operational consequence of fixing a pinned defect. As of 2026-09-14 NINE are fixed (#5, #6, #8, #9, #11, #12, #13, plus #4+item3 landed as (A)+C-none, which also resolved client-visible item 3); items 4–13 are down to #7 (client-report regen) + two product decisions. #4's measurement proved the 삼형 chain position is a no-op on all 27 fixtures, that C-high contradicts KB11 §B4, and that branch 삼형 is documented nowhere in knowledge/ — so the chain was left untouched and C9 re-pinned as a documented scope limit"
metadata: 
  node_type: memory
  type: project
  originSessionId: c0d81811-6bf6-4476-9d75-47fd790445e6
  modified: 2026-09-14T14:32:31.784Z
---

The 2026-09 validation campaign is COMPLETE but was **validation-only by design**: the defects it
found were pinned by tests asserting the *current wrong behaviour*, and none were fixed in-campaign.
See [[engine-validation-campaign-2026-09]] for the campaign record; the 13-item list also lives in
`.superpowers/sdd/progress.md` (search it for "Loose ends carried" and for the post-campaign entries).

On **2026-09-14** the user directed work to begin on **items 4–13** (the non-client-visible ten).
Items 1–3 were flagged as the higher-priority client-visible ones and remain unfixed.

## Progress on items 4–13 (2026-09-14)

Done and independently re-verified by the controller: **#6** (the KB12:130-152 Day-Master-keyed
tier-pool contradiction + `report_data` raw-favorable read — this one *also* closed client-visible
item 2, see below), **#8** (`md_to_saju_compat_pdf.py --output` path bug), **#9** (Harish's
longitude: 3 data sites moved to `79.42`, pillar-neutral, gates green), **#5** (C8 order-dependence
— `compat_score` was not symmetric; fixed in `compat.py::_canonical_nayin_pair()`, see below),
**#11** (辰/戌
Temperate-vs-Cold/Hot band divergence — resolved as a *documentation + scope* fix, **not** a model
change; see the decision note below), **#12** (`knowledge/17-climate-method.md` unsourced
dry/damp parenthetical), **#13** (dead `_CHECKERS` registry pruned).

**#5 decision (2026-09-14) — the reusable precedent for a *direction-bearing* subsystem.** The nayin
sub-system reads six relation labels that each name *which* tone generates or overcomes which
(상합/상구/상충/상해 …), so the answer depends on which partner is the SUBJECT — and the engine was
taking that from the **caller's argument order**, giving one couple two verdicts. The fix,
`compat.py::_canonical_nayin_pair(a, b, nayin_a, nayin_b)`, resolves the subject order BEFORE the
relation is computed *and displayed*: **male-first when both genders are known and differ**, else the
tone appearing earlier in `NAYIN_ORDER`. The index tiebreak is **declared a stability convention, not
a recovered classical rule** — `knowledge/11-gunghap.md` §C specifies an ordered 30×30 table but no
consulted source defines an order rule at all (the table is still the documented 5-element grammar
fallback, pending the published 서전구미록 table), so the engine declares its own order rather than
inventing a classical one. Both branches are a **NO-OP for every already-canonical (male-first)
pair**, which is the load-bearing safety property: no published verdict moves, no documented weight
changes (the `_score_map` normalization and the sub-system max are untouched). Four lockstep surfaces
moved (`compat.py`; `knowledge/11-gunghap.md` §C new "Canonical subject order" subsection;
`tests/test_compat.py`, lock retired + 3 positive order-independence guards; two `compat.json`
fixtures re-pinned), plus the harness `_GATE_HISTORY`/render prose. Measured: symmetry sweep over 12
charts × 3 gender configurations (M/F 144 pairs, None/None 12, M/M 12) → **0 composite- and 0
subsystem-differing in every configuration**; 27 compat fixtures re-measured with exactly the 2
pre-existing `documented_interpretation` divergences and no regression; a no-regression proof by
monkeypatching `_canonical_nayin_pair` to identity, which restored exact pre-fix semantics and
reproduced the old fixture text verbatim. Suite 880/15/0, CLI 194 (189/5/0), stdout md5 unchanged.

**#11 decision (2026-09-14) — the reusable precedent.** Two candidate fixes were weighed:
**(A)** extend `climate.py` to fire the 燥濕 override (辰→Fire, 戌→Water), vs **(B)** document the
model as a deliberate scope limit. **(B) was chosen** because the engine already agrees with the
fuller classical 寒暖燥濕 reading on *all ten branches where it prescribes an element at all* (no
element is ever computed wrongly), because the per-branch assignments rest on a modern practitioner
source rather than a transcribed classical text (Ground Rules 1–2), and because widening the model
moves the **client-facing `band` value** for every 辰/戌-month chart — a product decision, not a
patch. The lesson generalises: when a divergence is *which* rule fires rather than *what value* is
computed, and the rule's source is modern, the honest move is to name the scope and pin it, not to
silently widen. Four surfaces moved (knowledge file; `climate.py` docstring; four fixture `source`
strings; `validation.py` render prose) plus two test docstrings — **zero behaviour change**, suite
unchanged at 879/16/0, CLI 194 (189/5/0), stdout md5 identical. **The expansion itself is not
decided** — it is surfaced to the user alongside #10.

Still open, in the order they should land: **#7** (regenerate the Pawan/Mahesh client reports for
the 야자시 fix and refresh Harish's stale follow-ups; #9 and item 3 are both landed, so it is now
unblocked). **Two open PRODUCT decisions, not defects — surface both to the user rather than
deciding:** **#10** (조후 vs 억부 gate width) and **#11's model expansion** (whether `climate.py`
should implement the full 寒暖燥濕 four-way reading).

The #6 fix is the template for the rest, and it confirms the operational crux below: the engine
change was one helper plus two call sites, but it took **four lockstep surfaces** (fixture, two test
files, harness prose + `_GATE_HISTORY`) and the retired lock's XPASS was the only signal that the
marker should go.

## #4 + item 3 — LANDED as (A) + C-none (2026-09-14)

**The user's one-word approval was "(A) + C-none, go ahead"**, in response to the recommendation
*"I'd land (A) + C-none and keep the #4 chain untouched."* Both halves are now shipped and
re-verified. **(A)** = the 육합 arity fix only, in `compat._branch_pair_lookup`: the table parameter
re-typed `List[Tuple[str, str]]` → `Sequence[Tuple[str, ...]]` and the body
`(b1, b2) in table or (b2, b1) in table` → `any(tuple(row[:2]) in ((b1, b2), (b2, b1)) for row in
table)`, so the helper matches each relation row on its **branch columns** and stops depending on
table shape (충/해/파 are 2-tuples, 육합 is a 3-tuple). **C-none** = document 삼형's unsourced status
and re-pin C9 as a `documented_interpretation` scope limit — the same shape as the accepted #11
precedent — with the **relation-chain ORDER deliberately untouched**.

**The (A) fix moved exactly one fixture and the prediction held exactly.** `compat-mahesh-vp` went
**64/Mixed/daybranch 2 → 68/Strong/daybranch 6** — measured three independent ways (the fixture's own
`expected` = 68/Strong/6; the harness verdict PASS/`expect_match`; and a direct `compat_score()` call
giving composite 68, band Strong, daybranch 6, **zero subsystem mismatches**). The +4 is precisely
the 육합 intended `+4` at `compat.py:310`, so the arithmetic is self-consistent. **The two published
anchors (70/Strong, 74/Strong) did not move**, as predicted; `compat-harish-vinothini-pillars`
(45/Mixed) and `compat-pawan-sruthi-stale` (60/Mixed) stay their pre-existing
`documented_interpretation` rows. Note the band ladder boundary at 65: crossing it is why one fixture
flipped **Mixed → Strong** rather than merely nudging a number.

**Final gate state after (A) + C-none — re-measured, not carried:** suite **883 passed / 12 xfailed /
0 failed** (three runs agree); CLI **exit 0**, stdout md5 `9626959a…` **identical across two runs
(idempotent)**, reading **194 (PASS 189 / INTERPRETATION 5 / FAIL 0)**; the rendered report
regenerated with its md5 legitimately moving `855f24e4… → c697db8f…`. The suite arithmetic is
exactly conserved: retiring/adding nothing but prose left passed+xfailed at 895 either way, and the
post-fix 883/12 is the predicted shape.

**Why stdout did NOT change even though `render_report()` prose was rewritten** (an apparent
contradiction worth remembering): the CLI's stdout is a **two-line summary** — `report written:
<path>` plus `checks: 194 (PASS 189, INTERPRETATION 5, FAIL 0)`. The verbose prose goes to the
**markdown file only**. So stdout md5 is an invariant over *counts*, not over prose; the report
file's md5 is the thing that tracks prose edits. Corollary: **a stable stdout md5 is not evidence
that prose didn't change**, and a changed report md5 is not evidence of a behaviour change.

**Lockstep surfaces moved for the C-none half (five files, all prose/scope — zero behaviour):**
`knowledge/11-gunghap.md` (3 edits: §B4-C9 note re-pinned as a documented scope limit, §B9 carried as
the same, and the per-pair table); `tests/test_compat.py` (the C9 marker's reason string, plus the
comment block recording the grep-backed finding and "the 巳申 row is therefore unsatisfiable *given
the current chain* and that is the intended state… Do not 'fix' the row"); and **four** edits to
`src/saju_engine/validation.py` — the `_GATE_HISTORY` W6 `note`, the `render_report()` tally head,
the 육합 bullet (now a "FIXED 2026-09-14" record), and the C9 bullet.

**The harness edit corrected a claim the report used to make.** `validation.py`'s C9 bullet asserted
*"measured, a C9 fix alone flips 5/5, C9 + 육합 together flips only 4/5."* The variant measurements
**refute** it: the arity fix alone flips **0 of C9's 5** rows (it moves 巳申 from 육파 to 육합, which
is still not 삼형); the 4/5 figure came from **hoisting 삼형 above 육충**, a different and unsanctioned
change. The rewritten bullet also records that that full-chain reorder is a **NO-OP on all 27 compat
fixtures** — only relation *labels* and the lock's bookkeeping would change. The corrected text
**quotes** the old figure in order to refute it, so a naive `grep "flips 5/5"` still hits the report
and `validation.py`; that hit is a false positive, and position-in-sentence is what distinguishes a
refutation from an assertion.

### The measurement phase that produced the decision (2026-09-14)

Four variants of `compat.py` were built and measured end-to-end
(`/tmp/variant.py {pristine|A|A-mid|A-high}`; restore from `/tmp/compat.py.orig`):

| Variant | chain | suite | CLI | xfail→XPASS | C9 rows flipped | mahesh-vp |
|---|---|---|---|---|---|---|
| pristine (`ff719d82…`) | 육합→육충→육해→육파→삼형→반합 | 880 pass / 15 xf / 0 fail | 194 (189/5/0) | — | 0/5 | 64 / Mixed / daybranch 2 |
| **A** (`446e7a91…`) | arity fix only | 5 fail / 875 pass / 13 xf / 2 xpass | 194 (188/5/**1**) | 2 | 0/5 | 68 / Strong / daybranch 6 |
| **A-mid** (`07534b13…`) | 육합→육충→**삼형**→육해→육파→반합 | 5 fail / 875 / 11 xf / 4 xpass | 194 (188/5/**1**) | 4 | 寅巳, 未戌 | 68 / Strong / 6 |
| **A-high** (`f2ba2d2e…`) | 육합→**삼형**→육충→육해→육파→반합 | 5 fail / 875 / 9 xf / 6 xpass | 194 (188/5/**1**) | 6 | 丑未, 寅巳, 寅申, 未戌 | 68 / Strong / 6 |

**The decisive result — the 삼형 chain position is a NO-OP on everything the engine computes.**
Dumping all **27** compat fixtures under each variant (`/tmp/dump_all.py` → composite / band /
daybranch) gives: **A vs A-mid vs A-high differ on ZERO rows** (only the label line), and
pristine→A moves exactly **one** row, `compat-mahesh-vp` (64/Mixed/daybranch 2 → 68/Strong/6). So the
삼형 reorder changes no published anchor, no client-visible value and no fixture expectation — it
moves only pytest xfail-marker bookkeeping (2 → 4 → 6 XPASS). **The arity fix alone is the entire
behavioural payload of client-visible item 3.**

**⚠️ The variant switcher trap (hit 2026-09-14; check this first before any measurement).** The
experiment leaves the tree contaminated unless explicitly restored, and because this is a **no-git
repo** nothing catches it. On resume, `src/saju_engine/compat.py` was found at md5 `f2ba2d2e…` =
**variant A-high**, written 18:49 — six minutes *after* a `.remember/now.md` entry claimed pristine
had been restored. **Both** the engine *and* the CLI-rendered report were stale: the report read
`188/194 PASS` (the variant line) instead of `189/194`. Restoring from `/tmp/compat.py.orig`
(`ff719d82…`, 59556 bytes) and re-running both gates cleared both.

**Rule, corrected 2026-09-14 after (A) landed: the `ff719d82…` hash invariant has EXPIRED.** A bare
"md5 == `ff719d82…`" now **false-alarms**, because the sanctioned arity fix legitimately changed the
file (current md5 `9de82a55…`). **The durable check is to diff against the backup and verify every
hunk belongs to a known, sanctioned change** — currently that diff must be exactly **41 lines: the
`Sequence` import, the signature, the docstring, and the `row[:2]` body**, and nothing else (no
ladder reordering, no table edits). Hashes answer *"did anything change"*; diffs answer *"did
anything change that shouldn't have."* The rendered report is *not* evidence of the shipped engine —
it only ever reflects the last CLI run, whatever tree that ran against.

**Anchors — identical across A / A-mid / A-high:** `compat-harish-manvitha` 70/Strong/−6 PASS;
`compat-harish-vinothini-pillars` 45/Mixed/−4 INTERPRETATION; `compat-pawan-sruthi-stale`
60/Mixed/2 INTERPRETATION; `compat-mahesh-vp` 68/Strong/**6** **FAIL**; `…-override-b-earth`
74/Strong/−6 PASS. **The two published anchors (70/Strong, 74/Strong) cannot move.** (That
`mahesh-vp` FAIL is the *variant-run* state — the fixture still expected 64 at the time. After (A)
landed the fixture was re-pinned to 68/Strong/6 and the row is **PASS**.)

**The five failing tests are the same five under A, A-mid and A-high:** three are re-pins
(`test_compat_daybranch_returns_exact_demo_score` — `_MA_VP_SCORES["daybranch"]` 2→6;
`test_compat_order_independence_band_flipping_instance` — Mixed→Strong;
`test_compat_fixture[compat-mahesh-vp]` — 64/Mixed→68/Strong), one is the defect pin
(`test_punishment_pairs_reach_their_step`, which carries the 巳申 question), and one is Guard 3
(`test_guard_lookup_is_exhaustively_false_for_six_combinations`) whose own docstring declares its
failure the intended delete-the-marker signal. **All four non-C9 items were re-pinned as part of
landing (A); only the C9 defect pin remains, by design.**

### The 삼형 chain position has NO defensible source — and C-high contradicts documentation

- **C-high is classically indefensible on documented grounds**, not merely unsourced: hoisting 삼형
  above 육충 makes 丑未 and 寅申 lose their `knowledge/11-gunghap.md` §B4 label ("육충 — strongest
  RED FLAG") and drop −5 → −2, directly contradicting B4 and B8's consensus (일지 육충 = strongest
  unfavorable).
- **C-mid** preserves 육충's documented primacy and displaces only 해/파 — but KB11 ranks 형 against
  nothing; the only textual hint is `11-gunghap.md:1052` (연해자평 婚姻宜避刑沖), which names 형 and
  충 together and does **not** rank them.
- So **every** candidate position for 삼형 encodes a priority with no `knowledge/` source.
- **Option taken: (C-none) — APPROVED AND LANDED 2026-09-14.** It documents 삼형's unsourced status
  and re-pins C9 as a `documented_interpretation` scope limit, mirroring the accepted **#11
  precedent**. The two decisions that were put to the user, and their answers: **(1) 육합/B1** →
  **(A) arity fix only** (the (B) inventory-scan reading of the `11-gunghap.md:137` caveat was *not*
  approved; the narrow 巳申-only reading is **unsupported by the text**); **(2) #4 삼형** →
  **C-none** (not C-mid, not C-high). The chain order is untouched, so **four of C9's five rows still
  report their named shadowing relation and the fifth (巳申) now reports 육합 instead of 육파** —
  still not 삼형, so the row remains xfailed. Measured: **the arity fix alone flips 0 of C9's 5
  rows.**

### Knowledge-base integrity gap — branch 삼형 (三刑) is documented NOWHERE

Zero grep hits for `삼형|三刑|寅巳申|丑戌未` anywhere in `knowledge/`. 자형 (自刑) *is* documented
(`02-branches.md:96`, `07-special-formations.md:320`, `00-glossary.md:79,189`).
`07-special-formations.md`'s Part 3 relation table lists 합 · 충 · 자형 · 해 · 파 and **omits 삼형**.
`11-gunghap.md:323`'s 상형 −4 is the **Nayin** table (§C, 서전구미록), not branch 삼형. The W6
research doc `docs/research/2026-09-validation-compat-career.md` §B enumerates B1 육합 / B2 삼합·반합
/ B3 방합 / B4 육충 / B5 자형 / B6 해·파 and **never lists 삼형**. This is a *knowledge-file* gap,
not an engine bug — the engine's 삼형 table is correct, but nothing in `knowledge/` sanctions its
use, its weight, or its priority. Surface to the user alongside #10.

### Carried details from landing #4

- **L3 — REPAIRED as part of landing (A).** It was a mis-constructed, permanently-unsatisfiable lock:
  `tests/validation/test_val_compat.py` `_pillars_chart` hardcoded `("year","甲","子")` for **both**
  charts, so the 띠 lock compared 子 with 子 and could not distinguish the partners. That is exactly
  why it **never XPASSed under any variant** — it was unsatisfiable under *any* candidate fix, not
  merely under the ones tried. It now takes a `year_branch` parameter and stands as a positive
  behaviour pin asserting `result.score == 3`. **Lesson: a lock that never XPASSes is a signal to
  inspect the lock, not evidence that the defect is unfixable.**
- The two 육합 guards that remain: `test_guard_other_relation_tables_are_two_tuples` and
  `test_guard_two_tuple_tables_do_fire`, plus one **INVERTED** guard —
  `test_guard_lookup_is_shape_tolerant_for_six_combinations` had asserted the buggy premise
  ("六合 lookup is False for all six pairs") and now asserts shape-tolerance positively.
- The `compat.py:428` 반합 suppression guard stays **latent** after the arity fix (vacuous either
  way), and the secondary cross-chart loop skips any branch equal to the day branch
  (`if branch_b == day_b: continue`), so only 5 of 6 nominal cross pairs are evaluated when a chart
  repeats its day branch.
- Also carried: the **B1 caveat reading** — `knowledge/11-gunghap.md:137` says *"if 해 or 형 also
  exists in the cross, weight is halved."* Its own worked examples (자축합 disturbed by 자미해;
  인신형) are **cross-level co-occurrences**, so it is **not** a same-pair rule and **not** 巳申-only.
  Implementing it requires turning the first-match chain into an **inventory scan** — a real
  behaviour change, unlike the arity fix. **Not implemented** (option B was not approved; only (A)
  was).

## Client-visible — a wrong claim reaches a paying client

1. **`premium_report.py` reads the raw favorable element** — `(chart.strength_assessment or
   {}).get("candidate_favorable", "")` at `premium_report.py:181` and `:1395`, instead of
   `yongsin.favorable_element()`. Live-wrong in the Pawan/Sruthi client reports. **STILL OPEN — and
   now the last surface in this class.** Pinned by the two `xfail(strict=False)` markers at
   `tests/validation/test_val_climate.py:228` and `:249` (the "2 client-visible climate locks" in the
   harness tally). Not started: out of the user's directed scope (they directed items 4–13), so do not
   begin without direction.
2. **Same bug class in `report_data.py`** — `report_data.py:440` (`_career_why`) and `:458`
   (`_career_tiers`). Contradicts the engine's own resolved 용신 (用神) on every career row.
   **RESOLVED 2026-09-14** as a consequence of carried item #6 — the tier ranking and the per-row
   prose had to move to the display channel together, so fixing the pool keying fixed both halves.
   `_career_why`/`_career_tiers` now read a `_resolved_favorable(chart)` helper. The `unfavorable`
   channel deliberately stays raw, because `FavorableElement` publishes no display-channel
   unfavorable element at all (`yongsin.py:75-102`) — inventing one would assert a rule the
   knowledge files do not state.
3. **육합 (六合) dead code — RESOLVED 2026-09-14 by (A).** `lookup.py:305` declares
   `SIX_COMBINATIONS` as 3-tuples `(a, b, element)` while `_branch_pair_lookup` was annotated
   `List[Tuple[str, str]]` and tested 2-tuple membership → **never matched**. Unreachable at
   `compat.py:310` (+4), `:407` (spouse-palace +20), `:1295` (띠 +3), `:428` (vacuous 반합
   suppression). The engine's own narrative called 六合 the strongest favorable indicator in
   classical 궁합 (宮合) and then told the client the pair had "no direct 합/충". The helper now
   matches on `row[:2]`; see the (A) record above for the measured single-fixture movement.
   **Note: this defect was recorded ONLY in `tests/validation/test_val_compat.py`** — it is in
   neither the campaign spec's `Known Open Bugs Tracked`, nor plan 6, nor the 2026-08 audit addendum,
   and **KB11 has no arity note at all** (it is an engine bug, not a knowledge rule). Do not cite a
   KB11 anchor for it.

The two-channel bug class behind 1–2: `strength_assessment["candidate_favorable"]` is the **raw**
engine value; `yongsin.favorable_element()` resolves a **display** value (climate merge
`method="climate-balanced"`, reader override `method="reader-confirmed"`). Every consumer must pick
the right channel.

## Operational crux — what fixing a pinned defect costs

Fixing any of these is **not a local edit**. It ripples into four surfaces that must move together:

- the **defect pins** assert the wrong values, so a fix makes them **FAIL** (that is the
  paired-update signal — they must be re-pinned to the new correct values);
- the **fix-immune guards** use inputs a sanctioned fix cannot touch, so they must stay passing;
- the `xfail(strict=False)` markers turn **XPASS** — that is the delete-the-marker signal;
- the **anchors** (`compat-harish-manvitha` 70/Strong; override 74/Strong) and the fixture
  expectations shift, and `_GATE_HISTORY`'s certified W6 facts with them.

**Fix-order dependency — CORRECTED 2026-09-14 by the variant measurements.** The pre-measurement
hypothesis was that 巳申 (simultaneously 六合 and 六破, with 六合 tested first in the strict
first-match chain) coupled the two fixes: "fixing 육합 alone flips 4 of C9's 5 locks." **The
measurement refutes this.** The arity fix *alone* (variant A) flips **0 of C9's 5** rows and turns
only 2 locks XPASS. The 4-of-5 flip is the effect of **hoisting 삼형 above 육충** (variant A-high),
not of fixing 육합. So **item 3's arity fix and the C9 삼형 doctrine question are DECOUPLED** — the
arity fix can land on its own authority as a plain dead-code correctness fix, independent of the
unsourced-priority question. Only the `11-gunghap.md:137` caveat (option B, the inventory scan)
still interacts with the chain.

The validation report `docs/audits/2026-09-engine-validation-report.md` is **rendered by
`tools/run_validation.py`** — never hand-edit it. After any engine fix re-run both gates: the suite
and the CLI, and re-verify the counts independently (the controller re-measures; executor output is
never taken at face value).

## Business backlog (separate from engine work)

Tracked in `improvements_issues.md` §12 — master doc. Nothing shipped since the 2026-09-07 GTM pivot:
P0 testimonials + `TESTIMONIALS_APPROVED`; P1 Merchant-of-Record checkout (**nothing is charged
today**), self-service app PII encryption/queue/auth, deploy + harden, real WhatsApp number; P2 quiz
funnel, embedded calculator, Year-Ahead product, G4/G5 prose. See [[gtm-pivot-2026-09]] and
[[climate-favorable-element-2026-09]]. User prefers fixing correctness bugs fully/forward over
deferring once they reach paid deliverables — see [[user-feedback-scope-decisions]].
