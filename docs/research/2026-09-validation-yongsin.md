# 용신 (Favorable-Element) Merge Validation — External Research (2026-09-13)

Plan 4 (W4 yongsin) Task 3. Purpose: verify that the engine's 용신 merge logic
(strength + climate + reader override) is consistent with independent Korean
명리 sources. All external quotes fetched 2026-09-13 via WebSearch/WebFetch
(no browser automation, per binding protocol). Sources quoted verbatim;
translations ours.

## 1. What the engine implements

`src/saju_engine/yongsin.py` — `favorable_element(chart, override=None) -> FavorableElement`
(yongsin.py:120), frozen dataclass fields `element, method, confidence, note,
supporting, climate_band, climate_element, climate_agrees` (yongsin.py:95-100).

Merge precedence (read-only engine, summarized from yongsin.py:120-206):

1. **Reader override wins unconditionally** — explicit `override=` argument or
   `chart.strength_assessment["reader_override_favorable"]` (compat.py:1344-1355
   wiring). `_reader_confirmed` (yongsin.py:105-114) capitalizes the element,
   sets method/confidence = `"reader-confirmed"`, and resets climate fields to
   the temperate defaults.
2. **Balanced Day Master + non-temperate 조후 band** → the climate element
   becomes the headline: `method = "climate-balanced"` (yongsin.py:159).
3. **Strong or weak Day Master (or temperate climate)** → 억부 verdict governs
   via `_METHOD_BY_VERDICT` (yongsin.py:35-39): strong/extreme →
   `strong-dm-drain`, weak/extreme_weak → `weak-dm-support`, balanced (in a
   temperate climate) → `balanced-heuristic` (least-present element).
   조후 is carried only as cross-check fields (`climate_band`,
   `climate_element`, `climate_agrees`), not as the verdict.

This mirrors the documented derivation in `knowledge/09-interpretation-method.md`
Step 3 (lines 65-104: 신강 → drain/control set, 신약 → support set, 조후 as a
climate cross-check at lines 80-92) and `knowledge/17-climate-method.md`
§"How This Combines With 억부" (lines 56-67: "Balanced Day Master: 조후 is the
classical tie-breaker … Strong or weak Day Master: 억부 stays authoritative for
the headline 용신. 조후 is reported only as a cross-check note").

**Conservative climate model — why.** Full 궁통보감 is a per-day-stem × per-month
~120-cell table (10 일간 × 12 월령) of preferred 조후 stems. The engine instead
classifies each chart into three climate bands (hot / cold / temperate) and, for
balanced Day Masters in a non-temperate band, picks the band's corrective
element (hot → Water, cold → Fire). This is deliberately coarser than
궁통보감: it preserves the classical principle (extreme season needs its
corrective) without embedding a stem-specific table whose cell values are a
school-dependent editorial choice. The three-band model is what
`knowledge/17-climate-method.md` specifies; the full 120-cell table is a known
coverage gap, not an engine bug (see §5).

## 2. What the classical sources say

### Source 1 — 사자사주 (sazasaju.com), "용신이란? 억부용신부터 조후용신까지 종류 5가지 완전 정리"
URL: https://www.sazasaju.com/blog/yongsin-guide · fetched 2026-09-13

> "억부용신은 사주의 신강·신약에 따라 강한 것은 억제(抑)하고 약한 것은 보강(扶)하는 방식으로 결정하는 용신이다."
> (Suppression-support yongsin is determined by suppressing what is strong and supporting what is weak, per the Day Master's strength or weakness.)

> "적천수(滴天髓)의 억부론이 이론적 토대이다." — 적천수 grounds 억부.
> "궁통보감(窮通寶鑑)이 이론적 근거이며, 계절과 월지의 영향을 중시한다." — 궁통보감 grounds 조후, valuing season and month branch.

> 궁통보감 "계절에 따른 조후를 가장 우선시하여, 억부만으로는 해결되지 않는 한열(寒熱)의 문제를 보완하는 데 초점을 맞추었다"
> (Gungtongbogam prioritizes seasonal climate adjustment first, focusing on supplementing hot/cold problems that suppression-support alone cannot resolve.)

The article also classifies 적용 빈도: 억부 ~70%, 조후 ~20% of charts —
consistent with the engine treating 억부 as the default path and 조후 as the
balanced/non-temperate special case.

### Source 2 — 두루미사주 (durumisaju.com), "억부용신(抑扶用神)이란? — 강약으로 잡는 용신"
URL: https://www.durumisaju.com/dict/yongshin/eokbu · fetched 2026-09-13

> "억부용신(抑扶用神)은 사주 일간의 강약을 기준으로 잡는 용신입니다. 강하면 눌러주고(억抑) 약하면 도와주는(부扶) 원리에서 이름이 붙었으며"
> (Eokbu-yongsin is determined by the Day Master's strength; its name comes from pressing down when strong and supporting when weak.)

> "신강 사주의 억부용신은 식상(빼주기)·재성(쓰게 하기)·관성(눌러주기) 중에서 잡고, 신약 사주의 억부용신은 인성(생해주기)·비겁(같은 편 만들기) 중에서 잡습니다."
> (For a strong chart the 억부용신 is chosen among 식상/재성/관성; for a weak chart among 인성/비겁.)

> "일반적으로 사주가 너무 차거나 너무 더우면 조후를 우선하고, 그렇지 않으면 억부를 우선하는 견해가 많습니다."
> (In general, when a chart is too cold or too hot, 조후 takes priority; otherwise the common view is that 억부 takes priority.)

This is the closest external statement of the engine's load-bearing rule:
**climate wins only in extreme (non-temperate) charts; 억부 wins otherwise.**
The engine's "balanced DM + non-temperate band → climate-balanced" branch is
exactly the first clause; its "strong/weak → 억부 authoritative" branch is the
second.

### Source 3 — OpenFate Wiki, "사주 용신·희신·조후: 취용 방법 안내" + "조후와 부억 중 무엇을 우선할까"
URLs: https://wiki.openfate.ai/ko/bazi/useful-gods-climate (hub) ·
https://wiki.openfate.ai/ko/bazi/useful-gods-climate/climate-vs-strength-priority (article) · fetched 2026-09-13

> "조후와 부억에는 명식을 떠난 고정 순서가 없습니다."
> (There is no fixed order between climate regulation and strength balancing that exists apart from the chart itself.)

> "극단적 기후가 다른 기능을 막으면 조후가 전제가 되고, 기후가 이미 운용 가능하면 부억이 먼저일 수 있습니다."
> (If extreme climate blocks other functions, 조후 becomes the prerequisite; if the climate is already workable, 부억 may come first.)

> 《滴天髓》 "寒暖燥濕、旺衰與氣勢同時論 … 依盤而定" — 적천수 treats climate,
> strength, and momentum together, decided per-chart; 《三命通會》 "季節基線、
> 根透及全局作用同參，沒有固定永遠先調候或先扶抑的單一規則" — likewise no single
> always-first rule.

**Classification vs the engine:** OpenFate takes position (ii)-ish — no fixed
order, decided per-chart — which is *compatible with* the engine's
three-band simplification (the engine fixes the order deterministically:
extreme climate → climate first; temperate → 억부 first). It is a stricter,
band-quantized version of "no fixed order." The hub page also confirms the
주 용신 + 보조 희신 role split ("제일 용신과 보조 희신"), matching the engine's
`supporting` (희신) field semantics per knowledge/09 lines 96-102.

### Source 4 — 현인사주 (hyuninsaju.com), "용신 찾는 법 — 내 사주를 살리는 단 하나의 오행"
URL: https://www.hyuninsaju.com/blog/basics/yongsin-finding · search-result
summary only (page not fetched); fetched 2026-09-13 via search

Corroborates the same 3-step practical order used by the engine's merge:
1. 왕쇠 (strength) 판단 — 득령/득지/득세,
2. 부억 direction — weak → 인성·비겁, strong → drain/control,
3. 조후 미세 조정 — "부억과 조후가 같은 오행을 가리키면 용신 확정",
with the explicit warning that a summer weak chart must not be "helped" with
Fire (climate overrides naive 억부) — the same failure mode the
climate-balanced branch exists to prevent.

### Supporting: DBpia academic citation (search result only)
진영아·최정준, "『궁통보감』에서 용신의 의미와 <희용제요> — 甲木과 庚金을 중심으로", 동방문화와 사상 12 (2022).
https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11275955 · seen in search 2026-09-13

Key point per the search summary: 궁통보감 is 조후용신-based but the functional
role of the element is always present (e.g. autumn 갑목 uses 丁火 to temper 庚金
which prunes 甲木 — 丁·庚·甲 act as one functional set). This supports the
engine's design choice of carrying 조후 as a *cross-check* on the 억부 pick
rather than as an unrelated replacement: in 궁통보감 itself, the climate stem
and the structural need are entangled, not opposed.

### Priority classification summary (required by plan)

| Source | 조후 vs 억부 position |
|---|---|
| 사자사주 | 조후 우선 (for extreme 한열), 억부 otherwise; 궁통보감 "가장 우선시" within its own scope |
| 두루미사주 | explicit conditional: 너무 차거나 더우면 조후 우선, 아니면 억부 우선 |
| OpenFate | no fixed order — per-chart; extreme climate ⇒ 조후 전제, workable climate ⇒ 부억 먼저 |
| 현인사주 | 조후 as final 미세 조정 / guard against climate-blind 억부 |

**No source contradicts the engine's precedence.** All four converge on the
conditional structure the engine implements; OpenFate is the only one that
formalizes it as "no fixed order" rather than a band rule, a school difference
in presentation, not outcome, for the band extremes the engine distinguishes.

## 3. Published client verdicts vs engine

Corpus = `tests/validation/fixtures/yongsin.json` (13 entries). Published
verdicts come from hand-crafted client reports (line cites = report files).

| Candidate | Published 용신/희신 (cite) | Engine reading | Agreement |
|---|---|---|---|
| rm (1994-09-12 13:28) | Water 용신, Wood supporting (rm-report.md) | Water, strong-dm-drain, Wood — temperate | MATCH (fixture `rm-published` PASS) |
| gurumoorthy (1964-07-19 08:30) | Water 용신 (climate note) (gurumoorthy-report.md) | Water, strong-dm-drain, Water supporting; hot band, climate Water, climate_agrees False | MATCH (fixture `gurumoorthy-published` PASS; the published reading noted the hot climate, which the engine pins in the climate fields) |
| harish (1992-06-04 03:10) | Water 용신, Metal supporting (harish-report.md:48-50) | Water, climate-balanced, Metal, hot band | MATCH (`harish-published` PASS) |
| vishnu-priya (2001-06-07 16:45) | Water 용신, Metal supporting (vishnu-priya-report.md) | Water, climate-balanced, Metal, hot, agrees True | MATCH (`vishnu-priya-published` PASS) |
| sruthi (1993-12-11 02:45) | **Earth** 용신 (sruthi-report.md:48-50) | Fire (climate-balanced, cold band) | DOCUMENTED DIVERGENCE (`sruthi-published` INTERPRETATION — reader-argued Earth vs engine climate-balanced Fire; reader override channel reproduces Earth exactly) |
| pawan (1991-10-03 23:45) | **Water** 용신 (pawan-report.md) | Wood (balanced-heuristic) | DOCUMENTED DIVERGENCE (`pawan-published` INTERPRETATION; note: published chart was STALE pre-ya-ja-si-fix — report queued for regen) |
| mahesh (1995-01-19 23:50) | **Earth** 용신 (mahesh-report.md:42-45) | Fire (climate-balanced, cold band) | DOCUMENTED DIVERGENCE (`mahesh-published` INTERPRETATION; same STALE CHART ya-ja-si note) |

The three divergences are all *reader-argued* verdicts vs the engine's
mechanical band/least-present pick on genuinely borderline balanced charts —
exactly the class of cases every source in §2 says professionals split on
(OpenFate: "no fixed order"; 사자사주 §6: "감정가마다 용신이 갈리는 이유"). They
are recorded as INTERPRETATION, not FAIL, per the harness contract; the
reader-override fixtures prove the engine can reproduce each published
verdict when the reader's argument is supplied as the override.

## 4. Coverage matrix (method label × fixture)

| Method label | Fixture(s) | Layer |
|---|---|---|
| `strong-dm-drain` | rm-published, gurumoorthy-published | A (published) |
| `weak-dm-support` | weak-cold-agree, weak-cold-priority, weak-temperate | A (synthetic) |
| `balanced-heuristic` | pawan-published | B (published) |
| `climate-balanced` | sruthi-published, mahesh-published, harish-published, vishnu-priya-published | A/B (published) |
| `reader-confirmed` | sruthi-reader-override, sruthi-chart-override, gurumoorthy-override | C (override channels) |

All five `FavorableElement.method` labels exercised (strict coverage test green
at the 13-entry census). Both override channels (explicit argument and
`strength_assessment["reader_override_favorable"]`) produce byte-identical
`FavorableElement`.

## 5. Gaps and school debates

- **[UNCERTAIN] 辰戌丑未 climate banding** — the three-band (hot/cold/temperate)
  model maps the 12 months onto bands without stem-specific nuance; 辰戌丑未
  (earth-storage months) straddle temperate/non-temperate classification and
  궁통보감 treats each individually. `knowledge/17-climate-method.md` documents
  the simplification; the full 120-cell 궁통보감 table remains unimplemented
  (coverage gap, logged — not fixed in this campaign, which is validation-only).
- **Priority formalism differs by school** — OpenFate states no fixed
  조후/억부 order (per-chart dependency); the engine hard-codes a band rule
  (extreme ⇒ climate, else 억부). For balanced charts in moderate seasons the
  two can rank differently in principle; none of the corpus fixtures hit that
  corner, and no source was found that contradicts the band rule for its
  extreme/temperate poles. Logged as a school debate, not a defect.
- **종격 (dominant-structure charts)** — sources list 종격/從格 as a separate
  용신 family (사자사주 §6, OpenFate). The engine's 억부 thresholds
  (strength.py: extreme/extreme_weak) drain/support rather than follow; out of
  W4 scope, noted for future corpus work.

## Sources

1. `knowledge/09-interpretation-method.md` — Step 3 용신 derivation (lines 65-104), 조후 cross-check (lines 80-92).
2. `knowledge/17-climate-method.md` — 조후 merge with 억부 (lines 56-67), 궁통보감 grounding (lines 74-80).
3. 사자사주 — https://www.sazasaju.com/blog/yongsin-guide (fetched 2026-09-13).
4. 두루미사주 — https://www.durumisaju.com/dict/yongshin/eokbu (fetched 2026-09-13).
5. OpenFate Wiki — https://wiki.openfate.ai/ko/bazi/useful-gods-climate (hub, fetched 2026-09-13) and
   https://wiki.openfate.ai/ko/bazi/useful-gods-climate/climate-vs-strength-priority (fetched 2026-09-13).
6. 현인사주 — https://www.hyuninsaju.com/blog/basics/yongsin-finding (search-result summary, 2026-09-13).
7. DBpia (진영아·최정준 2022) — https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11275955 (search-result summary, 2026-09-13).
8. Engine read-only references: `src/saju_engine/yongsin.py:35-39,95-114,120-206`; `src/saju_engine/compat.py:1344-1355`; `src/saju_engine/strength.py` verdict thresholds.
9. Published client reports: `candidates_horoscope/reports/{rm,gurumoorthy,harish,vishnu-priya,sruthi,pawan,mahesh}/…-report.md` (line cites in §3).