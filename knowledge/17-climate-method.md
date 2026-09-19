# 조후 (Climate / Temperature Balance)

## What This File Covers

조후 (調候), literally "adjusting the climate," is the classical principle
that a chart's month of birth sets a temperature — hot, cold, or mild — that
the favorable element (용신, 用神) should help balance, independent of
whether the Day Master itself reads as strong or weak. It is the organizing
principle of **궁통보감 (窮通寶鑑)**, and it is closely tied to **적천수
(滴天髓)**'s per-stem stanzas, several of which are explicitly seasonal
(e.g. 辛金's "乐水之盈" — a love of abundant Water — is most often read against
a summer birth month).

Both texts are already named in this project's persona (CLAUDE.md) and are
already used for the compatibility (궁합) reading in `knowledge/11-gunghap.md`
§"궁통보감 조후 perspective." This file brings the same concept into the
**natal** 용신 determination in `knowledge/09-interpretation-method.md` Step 3,
which previously covered only the 抑扶 (strength-balance) method.

## Scope Note — This Is a Conservative Model

**No 궁통보감 source text was available to transcribe** into this project at
the time this file was written. 궁통보감 proper tabulates a specific 용신 for
each of the 10 Day Master stems across each of the 12 months (120 cells),
often naming exact stems rather than just elements (e.g. "丙火 in 巳월 wants
壬水 and 庚金"). **This file does not attempt to reproduce that table from
memory** — doing so without a citable source would violate the project's
Ground Rule against inventing undocumented classical rules.

Instead, this file documents only the general, uncontroversial classical
principle both texts share: **a chart peaking in summer heat wants Water to
cool it; a chart peaking in winter cold wants Fire to warm it.** This is
derived from the standard four seasonal quartets already used elsewhere in
this project (see `knowledge/03-five-elements.md` and the month-branch season
groupings in the engine), not invented here.

If a full 궁통보감 source text becomes available, this file and the
`climate.py` module it documents should be expanded to the full per-stem
table, and this scope note removed.

## The Three Climate Bands — The Engine's Implemented Model

| Band | Month Branches | Season | Classical Remedy (climate 용신) | 희신 (generates it) |
|---|---|---|---|---|
| Hot | 巳 午 未 | Summer | **Water** — cools and moistens | Metal |
| Cold | 亥 子 丑 | Winter | **Fire** — warms | Wood |
| Temperate | 寅 卯 辰 申 酉 戌 | Spring / Autumn | No climate override | — |

This table is the **寒暖 (hot/cold) axis only**, and it is what `climate.py`
implements. It is a deliberate subset of the fuller classical treatment — not a
claim that the fuller treatment does not exist. See the next section.

## The Fuller 寒暖燥濕 Reading — Sourced, Not Implemented

The classical 조후 treatment is four-way, not two-way. Its doctrinal basis is the
적천수 (滴天髓) couplet: *"天道有寒暖，发育万物 … 地道有燥湿"* — heaven's way has cold
and warmth; earth's way has dryness and dampness. **燥濕 (dryness/dampness) is a
second axis**, and it is what gives 辰戌丑未 — the four storage months — a remedy
of their own:

| Branch | Axis | State | Climate Remedy | 희신 |
|---|---|---|---|---|
| 亥 子 | 寒 | cold | Fire | Wood |
| 巳 午 | 暖 / 熱 | hot | Water | Metal |
| 戌 未 | 燥 | dry | Water | Metal |
| 辰 丑 | 濕 | damp | Fire | Wood |

*(Sources: cantian.ai, directly reviewed 2026-09-13 — see
`docs/research/2026-09-validation-climate.md` §3; corroborated in framing by an
OpenFate editorial review of 2026-07-22, which pairs 辰·丑 as 寒濕 against 未·戌 as
溫燥 but prescribes no elements. A SajuGallery 庚金 line cited in the research doc —
"丑辰 습토에 왕생, 戌未 조토에는 부스러짐" — was **not** directly reviewed, so treat it
as unverified.)*

**How the engine's model compares.** `climate.py` implements only the 寒暖 axis,
grouping each storage month with its adjacent seasonal quartet:

- **The engine agrees on all ten branches where it prescribes an element at
  all.** There is no element-level disagreement anywhere in this subsystem.
- **The divergence is exactly two branches — 辰 and 戌** — and it is confined to
  *whether an override fires at all*: the engine bands both temperate (no
  override), while the fuller reading gives each a remedy (辰 濕 → Fire,
  戌 燥 → Water). Neither branch is assigned a *different* element by anybody;
  the models differ on whether they are assigned one.
- **丑 and 未 agree by convergent validity, not by identical grouping.** The
  engine groups by seasonal *quartet* (丑 with 亥子, 未 with 巳午); the fuller
  reading pairs by damp/dry *state* (辰丑 damp, 戌未 dry). The two schemes cut the
  branches differently and still land on the same element — Fire for 丑, Water
  for 未.

**Why the fuller reading is not implemented.** Two reasons, and both are
Ground-Rule reasons rather than engineering ones. First, the per-branch element
assignments above rest on a modern practitioner source — directly reviewed, but
not a classical text transcribed into this project; the 적천수 couplet establishes
the 燥濕 *principle*, not these four assignments. Second, widening the model
changes the **band** value itself, which is a client-facing field: it appears in
the 조후 note attached to the 용신 for every chart born in a 辰 or 戌 month.
Until a citable classical source for the per-branch assignments is available, the
expansion is a **product decision to be taken deliberately**, not a defect to be
patched. The divergence is pinned so that any expansion is a *signalled* change:
`tests/test_climate.py::test_temperate_branches_have_no_override` asserts the
temperate band for all six non-quartet branches, and the `band-chen` / `band-xu`
validation fixtures pin the engine's temperate output at branch level.

`[UNCERTAIN]` — not on the principle, which is classical and sourced, but on the
per-branch element assignments, which are not.

## How This Combines With 억부 (Strength-Balance)

Per `knowledge/09-interpretation-method.md` Step 3:

- **Balanced Day Master:** 조후 is the classical tie-breaker. When the month
  falls in the hot or cold band, the climate element becomes the headline
  용신, overriding the numeric least-represented-element fallback. When the
  month is temperate, the least-represented-element fallback still applies —
  조후 has no strong opinion in mild seasons.
- **Strong or weak Day Master:** 억부 stays authoritative for the headline
  용신. 조후 is reported only as a cross-check note — agreement reinforces
  confidence in the 억부 pick; disagreement is noted but does not change the
  headline, because a clear strength imbalance is a stronger signal than
  climate for these charts.
- **Reader override:** always wins outright over both methods, unchanged.

## Sources

- 궁통보감 (窮通寶鑑) — the climate-balance (조후) concept and its role as the
  classical organizing principle for 용신 in each month; cited generally, not
  as a transcribed per-stem table (see Scope Note above).
- 적천수 (滴天髓) — per-stem stanzas that are frequently read with a seasonal
  lens (e.g. 辛金's love of abundant Water), supporting the general hot→Water /
  cold→Fire principle.
- `knowledge/11-gunghap.md` §"궁통보감 조후 perspective" — the existing use of
  this concept in this project, for compatibility (궁합) readings.
