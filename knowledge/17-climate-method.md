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

## Scope Note

**No 궁통보감 source text was available to transcribe** into this project. 궁통보감
proper tabulates a specific 용신 for each of the 10 Day Master stems across each
of the 12 months (a stem-by-month organization; see `docs/research/
2026-09-validation-climate.md` §2 for why "120 cells" is a derived description,
not a sourced count), often naming exact stems rather than just elements (e.g.
"丙火 in 巳월 wants 壬水 and 庚金"). **This file does not attempt to reproduce
that table from memory** — doing so without a citable source would violate the
project's Ground Rule against inventing undocumented classical rules. The
Day-Master stem is therefore still not an input to `climate.py`: only the month
branch is. If a full 궁통보감 source text becomes available, expanding to the
per-stem table is future work.

What this file **does** implement, as of 2026-09-19, is the full **two-axis,
four-band** model below — the 寒暖 (hot/cold) axis plus the 燥濕 (dry/damp)
axis, producing four climate remedy-bands (plus Temperate, which needs no
climate override) — which is sourced (see `## Sources`), not invented.
*(Corrected 2026-09-20 — external report review, 4th pass: this and the other
"four-axis" mentions below previously described a model with two axes as
"four-axis," which does not match either the axis count (two: 寒暖 + 燥濕) or
the band count (five, including Temperate) — see the table's own heading.)*

## The Four Climate Bands — The Engine's Implemented Model

The classical 조후 treatment is four-way, not two-way. Its doctrinal basis is the
적천수 (滴天髓) couplet: *"天道有寒暖，发育万物 … 地道有燥湿"* — heaven's way has cold
and warmth; earth's way has dryness and dampness. **燥濕 (dryness/dampness) is a
second axis**, distinct from 寒暖 (cold/hot), and it is what gives 辰 and 戌 —
two of the four earth-storage months — a remedy of their own, separate from the
seasonal quartet they sit next to:

| Band | Month Branches | State | Classical Remedy (climate 용신) | 희신 (generates it) |
|---|---|---|---|---|
| Hot | 巳 午 未 | 暖/熱 (hot) | **Water** — cools and moistens | Metal |
| Cold | 亥 子 丑 | 寒 (cold) | **Fire** — warms | Wood |
| Damp | 辰 | 濕 (damp) | **Fire** — dries and warms | Wood |
| Dry | 戌 | 燥 (dry) | **Water** — moistens | Metal |
| Temperate | 寅 卯 申 酉 | Spring / Autumn | No climate override | — |

*(Sources: cantian.ai, directly reviewed 2026-09-13 — see
`docs/research/2026-09-validation-climate.md` §3; corroborated in framing by an
OpenFate editorial review of 2026-07-22, which pairs 辰·丑 as 寒濕 against 未·戌 as
溫燥 but prescribes no elements. A SajuGallery 庚金 line cited in the research doc —
"丑辰 습토에 왕생, 戌未 조토에는 부스러짐" — was **not** directly reviewed, so treat it
as unverified.)*

**Why 丑 and 未 are not listed separately.** The source's 燥濕 pairing groups 丑
with 辰 (both 濕/damp → Fire) and 未 with 戌 (both 燥/dry → Water). But 丑 and 未
are *also* covered by the 寒暖 axis above (丑 in the Cold quartet, 未 in the Hot
quartet), and both axes prescribe the **same element** for them — Fire for 丑,
Water for 未 — by convergent validity (two independent groupings landing on the
same answer). So 丑 and 未 need no separate row; only 辰 and 戌, which the 寒暖
axis alone would band temperate, need the 燥濕 axis to get a remedy at all.

**Historical note (resolved 2026-09-19):** until this date, `climate.py`
implemented the 寒暖 axis only, banding 辰 and 戌 temperate — a deliberate,
tested scope limit (see `docs/audits/2026-09-engine-validation-report.md` and
`docs/research/2026-09-validation-climate.md` §3 for the validation campaign
that surfaced and fully sourced this gap). Expanding to the full two-axis model
was a **user-approved product decision** (2026-09-19), not a bug fix — it moves
the client-facing `band` value for any chart born in a 辰 or 戌 month. No current
candidate report (`candidates_horoscope/reports/`) has a 辰 or 戌 month branch,
so the expansion does not move any previously-delivered natal report.

`[UNCERTAIN]` — not on the two-axis principle, which is classical and sourced,
but on the per-branch element assignments in the table above, which rest on a
modern practitioner source (cantian.ai) rather than a transcribed classical
text.

## How This Combines With 억부 (Strength-Balance)

Per `knowledge/09-interpretation-method.md` Step 3, **as of 2026-09-19**:

- **조후 governs the headline 용신 whenever the chart sits in a non-temperate
  climate band** (hot, cold, damp, or dry) — **regardless of the 억부 strength
  verdict.** This is the sourced doctrine: *"조후와 부억에는 명식을 떠난 고정
  순서가 없습니다... 극단적 기후가 다른 기능을 막으면 조후가 전제가 됩니다"*
  (OpenFate); *"사주가 너무 차거나 너무 더우면 조후를 우선하고, 그렇지 않으면
  억부를 우선하는 견해가 많습니다"* (두루미사주) — priority is gated on
  **climate extremeness**, not on the Day Master's strength. See
  `docs/research/2026-09-validation-climate.md` §5.
- **Temperate month:** 억부 stays authoritative for the headline 용신, since
  조후 has no opinion to offer in a mild season.
- **Reader override:** always wins outright over both methods, unchanged.

**Historical note (resolved 2026-09-19):** until this date, the rule gated
조후's priority on the 억부 verdict (climate governed only for a `balanced`
chart; strong/weak charts kept 억부 as authoritative and treated climate as a
cross-check note only). The 2026-09-13 validation campaign found this
verdict-based gate had no direct source support — the sourced doctrine
conditions priority on climate extremeness instead (`docs/research/
2026-09-validation-climate.md` §5, "그 전제는 뒷받침되지 않습니다" on the old
premise). Broadening the gate to match was a **user-approved product decision**
(2026-09-19), not a bug fix. **Impact check performed 2026-09-19:** every
current candidate is either reader-overridden (unaffected — an override always
wins outright) or already had a `balanced` verdict (unaffected — climate
already governed there under both the old and new rule) — **except Manvitha**
(in the `harish_manvitha` compatibility pair), whose strong-DM chart sits in a
cold month: her headline 용신 (Fire) was already climate-agreeing and is
unchanged, but her 희신 changed from the strong-DM convention (Earth) to the
climate-resolved one (Wood), moving the `harish_manvitha` compat score from
70/100 to 68/100 (still Strong band). That report needs regeneration to match.

## Sources

- 궁통보감 (窮通寶鑑) — the climate-balance (조후) concept and its role as the
  classical organizing principle for 용신 in each month; cited generally, not
  as a transcribed per-stem table (see Scope Note above).
- 적천수 (滴天髓) — per-stem stanzas that are frequently read with a seasonal
  lens (e.g. 辛金's love of abundant Water), supporting the general hot→Water /
  cold→Fire principle.
- `knowledge/11-gunghap.md` §"궁통보감 조후 perspective" — the existing use of
  this concept in this project, for compatibility (궁합) readings.
- `docs/research/2026-09-validation-climate.md` — the 2026-09-13/19 validation
  research backing the two-axis table (§3, citing cantian.ai and OpenFate) and
  the 조후-vs-억부 priority rule (§5, citing OpenFate's "조후와 부억 중 무엇을
  우선할까" and 두루미사주's "억부용신").
