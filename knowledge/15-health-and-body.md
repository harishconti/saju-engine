# 15 · Health & Body (건강론, 健康論)

> **This file is a classical *tendency* reading only.** It is **not a diagnosis**,
> it is not screening or testing advice, and it is **not a substitute for a
> licensed medical professional**. Saju (사주, 四柱) describes where the Five
> Elements (오행, 五行) of a chart run heavy or thin and which body systems the
> classical tradition *associates* with those elements — nothing more. Every
> symptom tendency below is a **classical association, not a medical fact**. If a
> querent (질의자, 質疑者) has a health concern, the only correct response is to point
> them to a licensed clinician. (Mirrors `CLAUDE.md` Ground Rule 5.)

Saju health logic is a disciplined extension of the Five Elements (오행, 五行):
each element has a classical correspondence to a set of organs and functions
(장부, 臟腑 — the "viscera and bowels" of classical medicine), and the **balance**
of elements in a chart — read from `knowledge/03-five-elements.md` — points to
the systems that tend to be *over-stressed* (an element in excess) or
*under-supported* (an element depleted). The favourable element (용신, 用神) and
the luck layers (대운, 大運 / 세운, 歲運) then say *which* system to support and
*when*.

Work `knowledge/09-interpretation-method.md` Steps 2–5 first — Day Master
(일간, 日干) and its strength, then the element balance and the 용신 (用神) —
before applying anything here.

## 오행 → Organ Systems

The element → 장부 (臟腑) correspondence is **classical** (오행-장부 correspondence)
and is already stated in `knowledge/03-five-elements.md`; this table restates it
in the functional wording used for the health-tendency portion of a reading.

| Element (오행) | Organs & system (장부, 臟腑) |
|---|---|
| Wood (목, 木) | **liver / gallbladder** + nervous system |
| Fire (화, 火) | **heart / small intestine** + circulation |
| Earth (토, 土) | **spleen / stomach** + digestion |
| Metal (금, 金) | **lung / large intestine** + respiratory-immune boundary |
| Water (수, 水) | **kidney / bladder** + endocrine / reserve |

These functional wordings are the canonical values the engine's
`_ELEMENT_ORGANS` table must match. Read them as **domains of classical
association**, not as an organ-by-organ health report.

## Excess vs. Deficiency Tendencies

For each element, a chart can show it **over-dominant** (heavy: many stems and
branches of that element, seasonal support, combinations feeding it) or
**depleted** (thin: few or no supporting stems/branches, controlled by a strong
opposing element). The classical tradition associates each state with a
different set of body-tendencies. **These are classical associations only — not
symptoms to act on, and not a diagnosis.**

| Element (오행) | Over-dominant showing tends to stress… | Depleted showing tends to leave under-supported… |
|---|---|---|
| Wood (목, 木) | tension headaches, jaw/neck tightness, irritability, eye strain, a "wound-up" nervous system, liver-qi stagnation imagery | tendons and flexibility, steady mood, decisiveness; a sense of being easily depleted by stress |
| Fire (화, 火) | sleeplessness, palpitation, agitation, inflammation, flushing, "burning out" | circulation, warmth in the extremities, a flat or low mood, low daytime energy |
| Earth (토, 土) | heaviness, sluggish digestion, over-thinking / rumination, water-and-damp imagery, weight that settles centrally | appetite regularity, muscle tone, blood-sugar steadiness, grounded stamina; a tendency to worry without a settled base |
| Metal (금, 金) | dryness, tightness in the chest, a rigid breathing pattern, skin sensitivity, difficulty "letting go" | respiratory resilience, immune-boundary robustness at seasonal changes, skin and large-intestine regularity |
| Water (수, 水) | fluid retention, kidney / urinary load, hormonal swings, a restless "deep fear" imagery, cold in the lower body | low-back and knees, hearing (tinnitus imagery), memory and concentration, bone density, deep reserve / recovery capacity |

The two states are read against the Day Master (일간) and the 용신 (用神): an
excess element is a place to **avoid further loading**; a depleted element is a
place for **gentle preventive support**, not alarm.

## Controlling-Cycle Cascade

An element in excess does not only stress *its own* system — by the overcoming
cycle (상극, 相剋) it also strains the system of the element it **controls**. The
overcoming order — Wood → Earth → Water → Fire → Metal → Wood — is stated in
`knowledge/03-five-elements.md` (상극 overcoming cycle); this section simply reads
that cascade onto the 장부 (臟腑) map above.

| Over-strong element (오행) | Controls (상극) | System classically read as strained downstream |
|---|---|---|
| excess Wood (목, 木) | Earth (토, 土) | spleen / stomach + digestion |
| excess Fire (화, 火) | Metal (금, 金) | lung / large intestine + respiratory-immune boundary |
| excess Earth (토, 土) | Water (수, 水) | kidney / bladder + endocrine / reserve |
| excess Metal (금, 金) | Wood (목, 木) | liver / gallbladder + nervous system |
| excess Water (수, 水) | Fire (화, 火) | heart / small intestine + circulation |

So a chart heavy in Wood (목) is read as putting classical pressure on **both**
the liver/nervous-system domain (its own) **and** the spleen/stomach digestion
domain (what it controls). The reverse-overcoming note in
`knowledge/03-five-elements.md` (역극, 反剋) applies too: when the controlled
element is itself very strong, the strain can rebound onto the controller.
Again — **classical association, framed as a tendency, never a medical claim.**

## Foods, Lifestyle & Rhythm by Favourable Element

Once the 용신 (用神) is argued, its element points to the supportive daily
practices below. The food, direction, and seasonal correspondences are classical
(오행 방위, 五行方位 — element/direction; 오행-미, 五行-味 — element/flavour); the
specific lifestyle practices are a modern practical gloss on the classical
element imagery, safe as **suggestions for general wellbeing**, not
prescriptions. These are the canonical practice anchors the engine's
`_GROUNDING_PRACTICES` table must match.

### Wood (목, 木)

- **Anchor practice: time in forests** and tree-lined green space.
- Wake near dawn (the Wood hour); gentle stretching or tai-chi-style movement to
  keep Wood qi from stagnating.
- Leafy greens and sprouts; sour flavour **in moderation**.
- Morning planning or creative sessions rather than late-night ones.

### Fire (화, 火)

- **Anchor practice: brief midday sun** — short walks while the sun is high.
- Short, warm social breaks to rekindle enthusiasm; avoid isolating overwork.
- Bitter greens and red-coloured vegetables; warm rather than iced food and drink.
- Bright, south-facing rooms for work and gathering.

### Earth (토, 土)

- **Anchor practice: whole grains** as the dietary centre; mild natural sweetness.
- Hands-in-the-earth activity — gardening, pottery, kneading — to settle a
  ruminating mind.
- A **steady, regular meal and sleep schedule**; a grounded daily routine over an
  erratic one.

### Metal (금, 金)

- **Anchor practice: breathwork** — slow, deliberate breathing in cool, dry air.
- Decluttering and finishing / releasing what is done; Metal supports "letting go".
- White foods (radish, pear, root vegetables) and a little pungent spice.
- Quiet, contained rest in autumn especially.

### Water (수, 水)

- **Anchor practice: swimming and warm baths**; time in and near water.
- Evening stillness — winding down early, protecting deep rest and recovery.
- Black beans, seaweed, and other dark foods; salt **in moderation only**.
- North-facing, quiet rooms for sleep; guard the low back and keep the lower body warm.

The 용신 (用神) row is the personal "favourable" set; an element the chart already
holds in **excess** is the one to lean *away* from in sustained daily habits.

## Health-Watch Timing

Direction of support comes from the 용신 (用神); *timing* comes from the luck
layers. Read timing from `knowledge/08-luck-pillars.md` (대운, 大運 / 세운, 歲運 /
월운, 月運) — do not duplicate that method here.

- **More-preventive windows.** A 대운 (大運) or 세운 (歲運) that forms a strong
  **충 (沖, clash)** or **형 (刑, penalty)** against the natal chart — especially the
  day or hour branch — or that **spikes an already-excess element**, is the
  window to be more deliberate about rest, load management, and routine *(see
  `knowledge/02-branches.md` for the 충/형 pairs; `knowledge/08-luck-pillars.md`
  Part 5 for interactions)*.
- **Natural support windows.** The **season of the chart's depleted element** is
  the classical time to support that system gently — Wood in spring, Fire in
  summer, Metal in autumn, Water in winter, Earth in the late-summer and
  seasonal-transition periods.
- **Layering.** The decade (대운) sets the background weather; the year (세운)
  says whether *this* year carries the clash or the elemental spike; the month
  (월운, 月運) refines the window.

None of this predicts an illness or an event. It only says *when* the classical
reading would lean more toward prevention and *when* a thin element has seasonal
help.

## Scope & Limits

- **Not a diagnosis, not screening advice, not a substitute for a licensed
  medical professional.** This file supports reflection and general wellbeing
  habits only. Any actual symptom, concern, or decision belongs with a licensed
  clinician — always say so plainly.
- The chart's **lightest element is "where to begin gentle preventive support",
  not "what is wrong"**. A thin element is an invitation to a supportive habit,
  not a finding.
- Symptom tendencies here are **classical 오행-장부 association**, framed as
  potentials and influences — never as predictions of inevitable events
  (`CLAUDE.md` Ground Rule 4).
- Decline all medical certainty (`CLAUDE.md` Ground Rule 5). Use `[UNCERTAIN]`
  and *"전통 해석이 확립되지 않았습니다"* where the tradition is silent or divided,
  rather than inventing a rule (`CLAUDE.md` Ground Rules 1–2).
- This is 명리 (命理) health-tendency logic only. It is not classical Korean
  medicine (한의학, 韓醫學) practice, not herbal prescription, and not pulse or
  tongue diagnosis — those require a licensed 한의사 (韓醫師).

## How to Use This File

1. Read the **element balance first** in `knowledge/03-five-elements.md` — which
   elements are heavy, which are thin, and the 용신 (用神) once argued via
   `knowledge/09-interpretation-method.md`.
2. Come **here for the body mapping** — `## 오행 → Organ Systems` for the domains,
   `## Excess vs. Deficiency Tendencies` and `## Controlling-Cycle Cascade` for
   what a heavy or thin element is classically associated with.
3. Take the **supportive daily practices** from `## Foods, Lifestyle & Rhythm by
   Favourable Element`, keyed to the 용신 (用神).
4. Go to **`knowledge/08-luck-pillars.md` for timing** — then read
   `## Health-Watch Timing` here for how the clash and seasonal windows apply.
5. Close every health section of a reading with the scope statement from
   `## Scope & Limits`: a tendency reading, not a diagnosis, and no substitute
   for a licensed medical professional.
