# 14 · Directions & Relocation (방위·이사, 方位·移徙)

Saju direction logic is a small, disciplined extension of the Five Elements
(오행, 五行): each element has a classical compass direction, and the querent's
favourable element (용신, 用神) points to the directions that tend to *support*
them — for a home's facing, a desk, a bed, a move, or travel. Everything in this
file is a **tendency and an input to a decision**, never a rule to obey or a
prediction of an outcome.

> This file gives **direction and correspondence logic only**. It is **not** a
> building-siting system — 풍수 (風水, Fengshui) is a separate discipline. See
> `## Scope Boundary — This Is Not 풍수 (Fengshui)`, the most important section
> here.

Work `knowledge/09-interpretation-method.md` Steps 2–5 first: Day Master
(일간, 日干) and its strength, then the 용신 (用神) / 희신 (喜神, supporting
element) / 기신 (忌神, unfavorable element), before applying anything below.

## Element → Direction

The element → direction correspondence is **classical** and is already stated in
`knowledge/03-five-elements.md` (오행 방위); this table repeats it with the four
inter-cardinal transitions made explicit.

| Element (오행) | Direction | Compass sector |
|---|---|---|
| Wood (목, 木) | **East** | due East; ENE–ESE band |
| Fire (화, 火) | **South** | due South; SSE–SSW band |
| Earth (토, 土) | **Centre** | the centre / axis; also read into the four inter-cardinal corners (NE, SE, SW, NW) as the transitions between the other four elements |
| Metal (금, 金) | **West** | due West; WNW–WSW band |
| Water (수, 水) | **North** | due North; NNW–NNE band |

The four **inter-cardinal transitions** carry the element of the season-change
they sit on: **NE** = Wood-emerging-from-Water (late winter → spring), **SE** =
Fire-emerging-from-Wood (late spring → summer), **SW** = Metal-emerging-from-Fire
(late summer → autumn), **NW** = Water-emerging-from-Metal (late autumn →
winter). Earth governs the centre (US spelling: center) and, by extension,
mediates all four corners.

## 용신 → Favourable Personal Direction

Once the 용신 (用神) is argued from the chart, read direction from it:

- **용신 direction = the favourable personal direction.** Favour it for:
  - the **facing of a home or main room** (the direction it opens toward / gets
    its light and entrance from),
  - the **head of the bed** (sleep with the crown of the head toward this
    direction),
  - the **facing of a desk or workstation** (the direction you look toward when
    working),
  - the **direction of a move, posting, or relocation** relative to the current
    home,
  - **travel** — trips and stays in this direction tend to feel restorative.
- **희신 (喜神) direction = the supporting direction** — the second-best choice,
  used when the 용신 direction is not available.
- **기신 (忌神) direction = the direction to minimise time in** — not "forbidden",
  but the one to spend less sustained time facing or living toward, and to avoid
  for a long-term move when a better option exists.

### Worked mini-example

Day Master weak Wood, **용신 = Fire** (Output drains and warms the cold Wood),
**희신 = Wood** (비겁 support), **기신 = Water** (excess Resource, already
over-supplied).

- Choose a **south-facing** workspace; orient the **desk to face south**.
- **Sleep with the head toward south**; prefer **southern rooms** of the home.
- For a job move, a posting **south** of the current city is the supportive
  read; **east** (희신, Wood) is the fallback.
- Minimise a long-term move due **north** (기신, Water) and don't site the main
  workspace on the cold north side.

All of this is weighed against real constraints (cost, commute, family, the
actual building stock available) — the direction is one factor among many.

## Relocation & Move Timing

Direction says *where*; the luck layers say *when*. Read timing from
`knowledge/08-luck-pillars.md` (대운, 大運 / 세운, 歲運 / 월운, 月運) — do not
duplicate that method here.

- **Move in favourable years and months.** Prefer a 세운 (歲運) — and within it a
  월운 — whose stem or branch runs the chart's **용신 (用神) / 희신 (喜神)**
  element. A move made in a favourable-element window tends to settle more
  easily.
- **Avoid months that clash the natal chart.** Skip a 월운 (or 세운) branch that
  forms a **충 (沖, clash)** with the **natal day branch or hour branch** *(see
  `knowledge/02-branches.md` for the 충 pairs)* — the day and hour branches
  govern the self and the private/home sphere, so a clash there during a move is
  the least settled timing.
- **역마 (驛馬) activation = movement is favoured / likely.** When a 대운 or 세운
  branch triggers the natal **역마 (驛馬, Post-Horse star)** — or supplies the
  역마 branch for the natal day/year triplet — relocation, travel, and a change
  of environment are read as *supported and more probable* in that window *(see
  `knowledge/07-special-formations.md`, 역마살 section)*. Excess 역마 ("always
  moving, never arriving") is the caution, not a reason to force a move.
- **Tie the year layer to the luck-pillar method.** The decade (대운) sets the
  weather; the year (세운) sets whether *this* year is a move year; the month
  (월운) refines the window *(see `knowledge/08-luck-pillars.md`, Part 5 —
  Interactions)*.

## Colours, Numbers, Seasons & Materials by Element

The element → colour, number, and season correspondences are **classical**
(하도낙서 / 河圖洛書; 오행 방위). Use the 용신 (用神) / 희신 (喜神) row as a
personal "favourable palette"; the 기신 (忌神) row is the one to lean away from
in sustained daily surroundings.

| Element (오행) | Colours | Numbers | Season | Materials |
|---|---|---|---|---|
| Wood (목, 木) | green, teal | 3, 8 | spring | wood & plants |
| Fire (화, 火) | red, orange | 2, 7 | summer | light & warmth |
| Earth (토, 土) | yellow, ochre, brown | 5, 0 | late-summer & the seasonal transitions | ceramic, stone, clay |
| Metal (금, 金) | white, silver, grey | 4, 9 | autumn | metal & stone |
| Water (수, 水) | black, navy, deep-blue | 1, 6 | winter | glass & water features |

These are the canonical values the engine's `_ELEMENT_ASSOCIATIONS` table must
match (colours, the 하도 number pairs, seasons, and material families).

## Classical vs. Modern

- **Classical (use freely, cite the source):** element → **direction**, element →
  **colour**, element → **season**, and element → **number** (the 하도낙서
  1·6-Water / 2·7-Fire / 3·8-Wood / 4·9-Metal / 5·0(10)-Earth pairs). These are
  standard 오행 방위 doctrine and are anchored in
  `knowledge/03-five-elements.md`.
- **Modern convention (label it, keep it optional):** specific **gemstone /
  crystal** lists tied to each element are a **modern** popular-astrology
  convention, **not** a classical 명리 (命理) rule. If a reading includes
  gemstones, present them as an optional, clearly-labelled extra — never as
  derived doctrine — and do not let them carry analytical weight.
- The **material families** in the table above are a modern practical gloss on
  the classical element imagery; they are safe as suggestions but are not
  themselves classical text.

## Scope Boundary — This Is Not 풍수 (Fengshui)

**This file covers only the 명리 (命理) direction logic derived from the Five
Elements (오행) and the querent's 용신 (用神).** It stops there.

It is **not 풍수 (風水)** and **not 양택 (陽宅, dwelling / building siting)**. In
particular, this file does **not** provide, and a Saju reading must **not**
present as saju:

- room-by-room placement, or a floor-plan analysis;
- door, gate, or entrance 방위 systems;
- stove, kitchen, or bed placement rules of the 풍수 schools;
- **팔택 (八宅, eight mansions / eight houses)** — the East/West-group system;
- **flying star (현공, 玄空 / flying star)** and its time-period charts;
- **Kua numbers** (personal trigram / gua numbers) and the good/bad direction
  sets derived from them.

Those belong to **풍수 / 양택** practice and require a 풍수 practitioner and a
site survey. They use a different theoretical base (팔괘, the Luoshu grid, and
building-plus-time inputs) and are **not interchangeable** with the 오행/용신
direction read here. **The engine and readers must not label 풍수 method as
saju, blend the two systems in one reading, or imply that a 명리 direction read
substitutes for a building-layout consultation.** Blending the two systems in a
single reading — or letting a 명리 direction read stand in for a 풍수 site
survey — is a known failure mode to avoid.

If a querent asks for a home-layout or building 풍수 reading, say plainly that it
is out of scope for a Saju reading and point them to a 풍수 practitioner.

## How to Use This File

- Use it **after** Step 5 of `knowledge/09-interpretation-method.md` — the
  용신 (用神) / 희신 (喜神) / 기신 (忌神) must already be argued from the chart,
  not assumed.
- Read direction from the **용신** (favourable), fall back to the **희신**
  (supporting), and treat the **기신** direction as the one to *minimise*, not
  forbid.
- The direction is an **input to a decision, not a rule to obey.** Combine it
  with move timing (`knowledge/08-luck-pillars.md`), 역마 signals
  (`knowledge/07-special-formations.md`), and — decisively — the person's real
  constraints: budget, work, family, health, and what housing actually exists.
- For colours and numbers, give the **용신 / 희신** row as a "favourable
  palette" suggestion; keep gemstones optional and labelled modern.
- For anything about a building's internal layout, stop and refer to 풍수 — see
  the Scope Boundary above.
