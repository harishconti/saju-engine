# The "Very Weak" (`extreme_weak`) Verdict Can Never Fire — Analysis and Options

*Date: 2026-10-03 · Tracker item: P2-W · Status: analysis only — no engine change made.*

## Summary

The engine sorts every Day Master (일간, 日干) into one of five strength bands. The
bottom band, `extreme_weak` (shown to clients as **"Very Weak"**), needs a strength
score of **−5.0 or lower**. The lowest score the formula can produce is **−3.78**.
So the band is **unreachable**: no chart, ever, gets it. A 120,000-chart scan agrees.
Nothing scored below −3.78.

The top band, `extreme` ("Very Strong"), fires for about **2.3 % of charts**. The bands
are meant to be symmetric (the code comment says "D3 fix: symmetric extreme bands"),
but they are not in practice.

This matters for one reason beyond the label. The 종격 (從格, Following Grid) check
only allows its highest confidence, **"likely"**, for `extreme_weak` charts. Because
that band never fires, the engine can never call a 종격 more than **"possible"**.

Bigger finding: a chart that meets knowledge/07's conditions for 종격 exactly (no
인성, no 비겁, no seasonal support) **always scores exactly −3.78**. The −5.0 cut-off
therefore leaves out exactly the charts the knowledge file describes as "too weak to
stand".

**Recommendation: Option C.** Stop using a score cut-off to decide whether a chart
can be "likely" 종격. Decide it from the structural conditions in knowledge/07, and
remove the unreachable label. Details and caveats are below.

## Measurements

Scan: 120,000 births, chosen by seeded random sampling from 1930-01-01 to 2030-12-31.
All 12 two-hour (時) slots are equally represented. Times are KST (UTC+9), longitude
127.0°E, true-solar-time on (the engine default), and the engine is on this branch
(`compute_chart`). Throwaway script: `/tmp/ewscan/scan.py` (not committed).

### Lower tail (weak side)

| Measure | Value |
|---|---|
| Minimum `total_score` | **−3.78** (267 charts, 0.22 %, sit exactly on this floor) |
| 0.1st percentile | −3.78 |
| 1st percentile | −3.41 |
| 5th percentile | −2.60 |
| Charts ≤ −3.0 | 3,144 (2.62 %) |
| Charts ≤ −3.5 | 763 (0.64 %) |
| Charts ≤ −4.0 | 0 |
| Charts ≤ −4.5 | 0 |
| Charts ≤ −5.0 (the `extreme_weak` cut-off) | **0** |

### Upper tail (strong side), for comparison

| Measure | Value |
|---|---|
| Maximum `total_score` | 8.11 |
| 95th / 97th / 99th / 99.9th percentile | 4.28 / 4.77 / 5.61 / 6.86 |
| Charts ≥ 4.0 | 7,656 (6.38 %) |
| Charts ≥ 4.5 | 4,879 (4.07 %) |
| Charts ≥ 5.0 (the `extreme` cut-off) | 2,721 (2.27 %) |
| Charts ≥ 6.0 | 667 (0.56 %) |

### Verdicts and 종격 confidence as the engine stands

| Verdict | Charts | Share |
|---|---|---|
| balanced | 61,317 | 51.1 % |
| strong | 36,695 | 30.6 % |
| weak | 19,281 | 16.1 % |
| extreme ("Very Strong") | 2,707 | 2.26 % |
| extreme_weak ("Very Weak") | **0** | 0 % |

The 2,707 vs 2,721 gap is rounding: the verdict uses the unrounded score, while the
table above uses the 2-decimal score the engine publishes.

| 종격 confidence | Charts |
|---|---|
| "likely" | **0** (needs `extreme_weak`) |
| "possible" (from `weak` charts) | 2,574 candidate flags |
| no 종격 candidate | 118,058 |

The share that mirrors how often `extreme` fires (2.27 %) falls at a score of
**−3.08** on the weak side.

## What knowledge/ actually says

- **There is no separate "very weak" class in knowledge/.** The strength step names
  two states, 신강 (身強, strong) and 신약 (身弱, weak). It adds that "some schools use a
  numeric count; others use seasonal dominance. Always state your reasoning"
  *(knowledge/09-interpretation-method.md:82)*. The output template's verdict line is
  `[신강 / 신약 / special grid — e.g., 종재격]`
  *(knowledge/10-output-template.md:37)*. A "very weak" bucket is not one of the
  options. The words 극신약 (極身弱) and 태약 (太弱) do not appear anywhere in knowledge/.
- **"Extreme" strength appears only as the gateway to special grids.** "A special
  grid (종격, 화격, 양인격) may apply if the strength is **extreme** in either
  direction" *(knowledge/09-interpretation-method.md:84)*. Special grids "apply when
  the Day Master is either very weak or very strong in unusual ways. They are read
  only when their specific conditions are met"
  *(knowledge/07-special-formations.md:55)*.
- **종격 is defined by structural conditions, not by a score.** "Day Master is too
  weak to stand… Conditions: Day Master has **no support** (no 인성, no 비겁, and
  **no** seasonal support). The month stem is **powerful** in the dominant element…
  the Day Master is 'in' the chart but has no ally"
  *(knowledge/07-special-formations.md:57-65)*. The glossary agrees: "The Day Master
  is so weak it cannot stand alone, and follows the dominant element"
  *(knowledge/00-glossary.md:177)*.
- **What changes when 종격 applies:** "the favorable element (용신) is the dominant
  element itself" *(knowledge/07-special-formations.md:73;
  knowledge/09-interpretation-method.md:125)*. For an ordinary weak chart, the 용신 is
  인성 then 비겁 *(knowledge/09-interpretation-method.md:122-124;
  knowledge/03-five-elements.md:91)*. So 종격 reverses the 용신 direction. "Weak" and
  "very weak" do not.
- **Where knowledge/ is silent:** no file gives a numeric threshold for "too weak to
  stand". No file defines a "very weak but not 종격" category with its own
  interpretation. 전통 해석이 확립되지 않았습니다 (the traditional interpretation is
  not established) for such a middle band. The engine's −5.0 (and the earlier −4.0)
  is an engine calibration, not doctrine.

## Why the threshold is unreachable (the arithmetic)

The score is computed in `src/saju_engine/strength.py:204-209`:

> score = 1.0 × self + 0.8 × resource + 1.5 × season − 0.7 × drain

- **self, resource and season can never go below zero.** They are counts and table
  weights.
- **drain has a ceiling.** A chart has 3 visible stems besides the Day Master, worth
  1.0 each. It also has 4 branches, and since the N-12 fix (commit `5bd3bbe`,
  2026-09-30) each branch's hidden stems total exactly 0.6. So the most that can
  press on the Day Master is 3 × 1.0 + 4 × 0.6 = **5.4**.
- **Floor = −0.7 × 5.4 = −3.78.** The scan's minimum hits this exactly. One example:
  1969-06-28 11:54 KST, with self 0, resource 0, season 0, drain 5.4.

The ceiling on the strong side is much higher: self up to ≈5.4, plus season up to
1.5 × 2.0 = 3.0, giving about 8.4 (observed max 8.11). The formula is lopsided by
design. Support has three positive terms. Pressure has one term with a 0.7 discount.
Mirroring the cut-offs (+5.0 / −5.0) therefore does not mirror their frequency.

**How −5.0 came about.** The original thresholds were ±4.0. Commit `62ccfcc`
(2026-09-29, the N-5 fix) widened both to ±5.0. The commit message and the comment
at `strength.py:211-220` explain the reason: the new season term raised the
*positive* ceiling, and the cut was moved "so 'extreme' stays genuinely rare (≈3 % of
charts)". The negative side was moved to match the old symmetric "D3" convention,
and its tail was never measured. Even under the hidden-stem weights in use that day
(a branch could total up to 1.0), the same arithmetic gives a floor of about
−0.7 × 7.0 = −4.9. That was already above −5.0. N-12, one day later, raised the floor
to −3.78. Neither audit comment cites a knowledge/ file for the −5.0 value.

**A key consequence.** knowledge/07's 종격 conditions say no 인성 and no 비겁 anywhere,
and no seasonal support. Those conditions force self = resource = 0, and every
non-Day-Master qi then counts as drain (5.4). So **every chart that meets the
knowledge/07 description, read strictly, scores exactly −3.78.** (Strict reading:
07:62 "no 인성, no 비겁" is taken to exclude support in any stem, branch or hidden
stem. The floor is necessary, not sufficient: 267 charts sit at −3.78, and only 47
of them also have a dominant share ≥ 50 % and are in season, i.e. reach "likely".) The −5.0 cut-off sits below every
chart the doctrine has in mind. (Seasonal support without a hidden root is also
impossible in the engine. Every non-zero entry in `_MONTH_BRANCH_SEASON` corresponds
to a hidden stem of the DM or resource element in that branch.)

## What `extreme_weak` actually controls today

In every 용신 path, the engine treats `extreme_weak` exactly like `weak`. It never
treats it differently:

- 용신 method `weak-dm-support` for both *(src/saju_engine/yongsin.py:60-66, 100-105)*.
  The candidate 용신 is 인성 and the 희신 is 비겁 for both *(strength.py:259-263)*.
- 화격 isolation accepts both *(patterns.py:236)*. Every career and prose branch tests
  `in ("weak", "extreme_weak")`.

It has only **two** effects of its own:

1. **Labels:** "Very Weak" in reports *(report_primitives.py:52)* and "quite weak" in
   the plain-words callouts *(prose_scaffold.py:292)*.
2. **종격 ceiling:** `detect_special_forms` allows "likely" only for `extreme_weak`
   (patterns.py:332-337). `weak` charts are capped at "possible".

Because the band never fires, neither effect has ever appeared in any output.

## Options

### Option A — Leave as-is and document it as unreachable

- **What changes:** nothing in code. This document and the existing notes are the
  record (golden `tests/golden/cases.py` note, P3 patterns fixtures listing
  `special_forms_likely` as UNREACHABLE).
- **Labels / 용신 / reports:** unchanged. "Very Weak" never prints. 종격 never goes
  above "possible".
- **종격:** the 47 charts in the scan (0.04 %) that meet every knowledge/07 condition
  stay at "possible", alongside about 2,500 charts that fail some condition.
  Readers cannot tell the textbook cases apart from the borderline ones.
- **Golden impact:** none.
- **Cost:** dead code stays. The engine appears to support a "Very Weak" class it can
  never output.

### Option B — Recalibrate the `extreme_weak` cut-off to the observed distribution

For example, use −3.1, the score that mirrors `extreme`'s 2.27 % share. Or use −3.5
(0.64 %) for a rarer band.

- **Labels:** about 2.6 % (at −3.0/−3.1) or 0.6 % (at −3.5) of charts change from
  "Weak" to "Very Weak" / "quite weak" in every report tier.
- **용신 paths:** **none change.** The 용신 method, 희신, 기신 and 화격 are identical
  for weak and extreme_weak.
- **종격:** charts in the new band become eligible for "likely". The scan shows that
  at −3.0 **and** at −3.5, exactly the same 47 charts (0.04 %) reach "likely". All of
  them are at −3.78. The rest stay "possible", because the engine's existing
  rooting and in-season checks downgrade them. So the threshold value hardly matters
  for 종격. The structural checks do the real work.
- **Report sections:** the special-formation prose *(premium_report.py:270,
  prose_fillers.py:1904)* would start printing "likely" wording for those 47-in-120k
  charts.
- **Golden impact:** **none at −3.0 or lower.** The golden charts' scores are park
  1.11, ny −1.08, seoul 0.88, lux 5.22, kiran 5.74, wren −2.26 (weak, 종관 possible),
  and clive 3.35. Wren would change only if the cut were set above −2.26. The 7
  canonical client charts (all balanced or strong per commit `62ccfcc`) are unaffected.
- **Weakness:** this is still a number with no knowledge/ source. It would add a
  client-facing "Very Weak" label for a class that knowledge/ does not define
  (knowledge/10-output-template.md:37). Any later change to the weights moves the
  distribution again, which is exactly how −5.0 became unreachable.

### Option C — Send very-weak charts to the 종격 check only, and remove the label

Let the knowledge/07 structural conditions, not a score band, decide whether a
`weak` chart's 종격 candidate can reach "likely". Drop `extreme_weak` as a verdict
(and so the "Very Weak" label).

- **Labels:** "Very Weak" / "quite weak" removed. Since they never print today, **no
  client-visible label changes.** The verdict set becomes strong / balanced / weak
  (plus the strong-side `extreme`, which is a separate question). That matches the
  template's 신강 / 신약 / special-grid line (knowledge/10-output-template.md:37).
- **용신 paths:** none change for ordinary weak charts. For a "likely" 종격, the
  existing reader-review flow is unchanged. The engine still only *flags*. It does
  not switch the 용신 to the dominant element (knowledge/07-special-formations.md:73), because that would
  be a separate decision.
- **종격:** **an important caveat came out of the scan.** The engine's rooting check
  (`_has_rooting`, patterns.py:278-299) looks only at branches and hidden stems. It
  does not look at the **visible** stems. If Option C were done naively (let every
  `weak` chart reach "likely"), 84 charts would reach "likely" instead of 47. The
  extra 37 score −2.08 or −2.28 because they have a visible 비겁 or 인성 stem.
  knowledge/07-special-formations.md:62 excludes those explicitly ("no 인성, no 비겁"). So Option C needs a
  visible-stem 비겁/인성 test alongside the rooting test. With that test, Option C
  produces exactly the same 47 "likely" charts as Option B, chosen for the doctrinal
  reason rather than by a number.
- **Report sections:** the same special-formation prose as Option B, for the same 47
  charts. The career and prose code that tests `in ("weak", "extreme_weak")` keeps
  working once `extreme_weak` is removed from those sets.
- **Golden impact:** none expected. No golden chart is `extreme_weak`. Wren (weak) has
  a 종관 "possible" candidate. If wren is rooted or out of season, it stays
  "possible". This must be confirmed when the change is made, but wren is not at the
  −3.78 floor, so by the scan's finding it cannot be one of the "likely" charts.
- **Cost:** a small engine change, plus updates to the tests and P3 fixtures that list
  `special_forms_likely` as UNREACHABLE. It also leaves the strong-side `extreme`
  label without a weak-side twin, which is fine, since knowledge/ defines neither.

## Recommendation

**Option C**, for three reasons:

1. **It follows what knowledge/ says.** 종격 is defined by the absence of 인성, 비겁 and
   seasonal support *(knowledge/07-special-formations.md:57-65)*, and special grids
   are "read only when their specific conditions are met"
   *(knowledge/07-special-formations.md:55)*. A score band is at best a stand-in for
   those conditions. The scan shows the conditions pin the score to −3.78 anyway, so
   the stand-in adds nothing and was set in the wrong place.
2. **It removes a label knowledge/ does not define.** The template offers only 신강 /
   신약 / special grid *(knowledge/10-output-template.md:37)*. A "Very Weak" class with
   no special-grid meaning has no source. 전통 해석이 확립되지 않았습니다 (no
   established traditional interpretation) for a "very weak but not 종격" band, so the
   engine should not invent one (CLAUDE.md Ground Rule 1).
3. **It cannot drift.** A structural test does not depend on the score weights, so
   the next calibration change cannot make it unreachable again.

**On knowledge/09-interpretation-method.md:84** ("a special grid may apply if the
strength is extreme in either direction"): under Option C "extreme" on the weak side
is not a score band. It is the 07:62 condition set itself (no 인성/비겁 anywhere, not
in season), which is what the engine now tests. The strong-side `extreme` verdict
remains as a separate gateway for the strong-side special grids.

**Honest limits:**

- knowledge/07 lists a second condition: "the month stem is powerful in the dominant
  element" (knowledge/07-special-formations.md:63). The engine's in-season test checks the month **branch**, not
  the month stem. Whether Option C should also enforce the month-stem condition is
  a doctrinal question for the owner.
- knowledge/ does not say whether a visible-only 비겁/인성 stem, with no root,
  disqualifies 종격, or only weakens it. Line 62 reads as disqualifying ("no 인성, no
  비겁"), and that reading is used above. Some schools may treat an unrooted visible
  stem more leniently. That is not in knowledge/, so it is not assumed here.
- Until the owner decides, **Option A is the status quo.** It is safe because no
  client output depends on the unreachable band. Option B is not recommended: it
  produces the same 종격 result as Option C, but by a number with no source, and it
  adds an undefined client label.

## Side observation (out of scope, not changed)

`prose_scaffold.py:288-294` keys its plain-words label on `"extreme_strong"`. The
engine's actual verdict is `"extreme"`, so "Very Strong" charts (≈2.3 %) get an empty
`strength_label` in the plain-words callouts. This should be filed separately.

## Decision (2026-10-03)

The owner chose **Option C**. The `extreme_weak` verdict is removed. 종격 is read only
from `weak` charts and reaches "likely" when the dominant element is >= 50 %, no
비겁/인성 appears in any branch, hidden stem or non-Day-Master visible stem, and the
dominant element is in season. The in-season test **keeps the month branch (월령)**,
a documented difference from the "month stem" wording of knowledge/07-special-formations.md:63.
The same change fixed the `_VERDICT_PLAIN_LABEL` key (`extreme_strong` -> `extreme`).

Follow-up decision (2026-10-03): a "likely" 종격 also switches the 용신 to the dominant element (`method="jonggyeok-follow"`, knowledge/07-special-formations.md:73); "possible" candidates keep the 억부/조후 resolution; a reader override still wins.
