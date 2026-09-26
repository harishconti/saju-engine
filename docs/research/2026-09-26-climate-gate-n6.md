# N-6 research: when should 조후 (climate) override 억부?

**Status:** research done 2026-09-26; **needs a user decision** before any code change (Ground Rule 1).
**Finding:** `docs/audits/2026-09-26-deep-engine-audit.md` §N-6. **Tracker:** `docs/audits/2026-09-26-deep-engine-audit-verification.md`.

## The question

`climate.assess_climate()` looks only at the month branch. So 조후 sets the headline 용신 for every chart
born in 巳午未亥子丑辰戌, whatever the rest of the chart holds. The user asked for more research before
picking a whole-chart "extremeness" gate.

## What the sources say

| Source | What it says | Gives a threshold? |
|---|---|---|
| 적천수 「寒暖」 (原文) | 「天道有寒暖 發育萬物 人道得之 不可過也」: cold and warmth must not be **excessive**. | No |
| 임철초, 적천수징의 (commentary on the same line) | Do not treat the northwest (Metal/Water) as cold and the southeast (Wood/Fire) as warm just by position. Examine how the chart itself changes. | No, but it rules out a position-only (month-only) test |
| 두루미사주 「억부용신」 | 「사주가 너무 차거나 너무 더우면 조후를 우선하고, 그렇지 않으면 억부를 우선하는 견해가 많습니다」, and 「이 판단은 학파별로 차이가 있고」 | No, and it says schools differ |
| postype 「조후, 한난조습 파악하기」 | Excessive 寒/濕/熱/燥 is a disease of the whole chart. The month branch has large influence. | No |
| Daum 명학 cafe 「용신정법」 | 조후 is the most basic principle. No criterion given. | No |

**Conclusion:** the classical line and its main commentary both say the test is about the **chart**, not
the month alone. That supports the audit. **No source found gives a numeric threshold.** Any cut-off (for
example "Fire ≥ 30% of weighted qi") would be invented, which Ground Rule 1 forbids.

## Options

| | Rule | New numbers? | Effect (1,500 random Seoul charts, current engine) |
|---|---|---|---|
| **A (recommended)** | Keep the month-based band. If the prescribed remedy element is **already the chart's most abundant element**, the chart is not extreme in that direction. Fall back to 억부 and set `requires_reader=True`. | None. "Most abundant" is an ordinal test. | 982 charts climate-governed; **124** (8%) would fall back |
| B | Whole-chart temperature score (Fire vs Water weight across stems and hidden stems, 조토/습토 included), gated on a threshold | Yes, a threshold no source gives | Depends on the chosen number |
| C | Leave as is and document the limitation | None | None |

Option A is the smallest change the sources support. It removes the audit's worst cases, where the
prescribed 용신 is already the chart's dominant element (for example 1963-10-24 11:00: a 戌 month says
"dry → Water" while the chart is 36% Water). It invents no threshold. Every chart that falls back is sent
to the reader instead of being decided by the engine.

## Sources

- 적천수 原文 and 임철초 commentary: <https://m.cafe.daum.net/ilovechg/Hthh/114>, <https://m.cafe.daum.net/adaseju48/MBFW/3>
- 두루미사주: <https://www.durumisaju.com/dict/yongshin/eokbu>
- postype: <https://www.postype.com/en/@saju-halang/post/15859519>
- 명학 cafe: <https://m.cafe.daum.net/1poetry/7NdS/417>
