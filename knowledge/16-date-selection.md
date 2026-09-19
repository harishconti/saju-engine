# 16 · Date Selection (택일, 擇日)

Saju date selection is a **chart-relative** discipline: given a window already
narrowed by the luck layers, rank the candidate days by how a day's stem and
branch sit against the natal chart — favouring the querent's favourable element
(용신, 用神) and harmony with the natal day branch, avoiding a clash (충, 沖)
with the self-and-home axis. Everything here is a **tendency and an input to a
decision**, never a rule to obey or a guarantee that a well-chosen day makes an
event succeed.

> This file covers the **chart-relative layer only**. Traditional 택일 also runs
> a separate **almanac** discipline (황도길일, 손없는날, and the day-officer /
> mansion layers) that is **not** derived from the querent's chart — see
> `## Scope Boundary — The Almanac Layer`, the most important section here.

Work `knowledge/09-interpretation-method.md` Steps 2–5 first: Day Master
(일간, 日干) and its strength, then the 용신 (用神) / 희신 (喜神, supporting
element) / 기신 (忌神, unfavorable element), before applying anything below.

## Chart-Relative Principles

Read a candidate date's **day pillar** (its 일주, 日柱 — stem + branch) against
the natal chart. The day and hour branches govern the self and the
private / home sphere, so they are the branches a chosen date must not disturb
*(see `knowledge/09-interpretation-method.md` on the palaces)*.

**Avoid:**

- a day **branch that clashes (충, 沖)** the **natal day branch or hour branch**
  *(see `knowledge/02-branches.md` for the 충 pairs)* — the least settled timing
  for anything touching the self or the home;
- a day whose stem or branch **runs the 기신 (忌神)** — the element the chart is
  already over-supplied with or most strained by *(see
  `knowledge/03-five-elements.md`)*;
- a day that repeats a natal **형 (刑, penalty) / 파 (破, break) / 해 (害, harm)**
  against the day or hour branch, when a cleaner day exists in the window.

**Favour:**

- a day whose **stem or branch element is the 용신 (用神)** or **희신 (喜神)** —
  the day then supplies the element the chart wants *(see
  `knowledge/03-five-elements.md`)*;
- a day branch that **harmonises with the natal day branch** — a **육합 (六合,
  six-harmony)** or a **삼합 (三合, three-harmony)** partner *(see
  `knowledge/02-branches.md`)* — which reads as a cooperative, well-supported day;
- within the chosen day, an **hour (시, 時)** whose branch is also non-clashing
  and, ideally, favourable-element — the same day-pillar logic applied one layer
  down.

The luck layers say **when the window is**; this file says **which day inside the
window**. Narrow first with 대운 (大運) / 세운 (歲運) / 월운 (月運) *(see
`knowledge/08-luck-pillars.md`)*, then rank days with the daily layer (일운,
日運) *(see `knowledge/08-luck-pillars.md`, 일운 section)* using the principles
above.

## By Event Type

Each event type leans on the ten-god (십신, 十神) energy that matches its purpose
*(see `knowledge/05-ten-gods.md`)*, **on top of** the non-clash and
favourable-element baseline from the section above.

- **Moving house (이사, 移徙)** — key the day to the mover's **용신 direction**
  *(see `knowledge/14-directions-and-relocation.md`)* and choose a day that does
  **not** clash the natal day or hour branch. A 세운 or 월운 already running the
  용신 / 희신 element makes the whole window easier *(see
  `knowledge/08-luck-pillars.md`)*; a **역마 (驛馬, Post-Horse)** activation in
  the window reads as movement supported *(see
  `knowledge/07-special-formations.md`)*.
- **Business opening (개업, 開業)** — favour a day carrying **식상 (食傷, Output)**
  or **재성 (財星, Wealth)** energy, ideally in a favourable-element month, so the
  launch sits on the produce-and-earn axis *(see `knowledge/13-wealth-and-business.md`,
  식상생재)*. Avoid a day that runs the 기신 or clashes the day branch.
- **Signing / contracts** — favour **관성 (官星, Officer)** or **인성 (印星,
  Resource)** day energy — structure and documentation — with **no clash** to the
  natal day branch *(see `knowledge/05-ten-gods.md`)*.
- **Wedding (혼례 택일, 婚禮擇日)** — the day must be non-clashing for **both**
  charts and favourable or at least neutral in element to both. See
  `## Two-Person Events`.
- **Surgery / medical procedure** — avoid a day that clashes the natal day
  branch **and** avoid a day running the element that governs the organ system
  involved *(see `knowledge/15-health-and-body.md`, 오행 → organ systems)*. This
  is a scheduling preference only; medical timing is set by clinicians, not by a
  chart — see `## Scope & Limits`.

## Two-Person Events

For an event that binds two people — a wedding, a joint business opening, a
shared signing — the day should not heavily **clash (충)** or **drain** *either*
chart:

- prefer a day branch that is **favourable or neutral to both 용신 (用神)**;
- reject a day that clashes **either** partner's natal day or hour branch;
- a day branch that **harmonises (육합 / 삼합)** with one partner's day branch and
  is neutral to the other's is a good compromise when no day flatters both.

Cross-check the pair's compatibility layer for the branches already under strain
between the two charts *(see `knowledge/11-gunghap.md`)* and keep the chosen day
clear of those.

## Scope Boundary — The Almanac Layer

**A full traditional 택일 (擇日) is two layers.** This file and the engine cover
the **chart-relative** layer only. The other layer is the **almanac (책력, 冊曆)**
discipline, which is **not derived from the querent's chart** and is **not**
provided here:

- **황도길일 (黃道吉日)** — the "yellow-way" auspicious days (and their 흑도, 黑道
  inauspicious counterparts);
- **손없는날** — the "no-ghost" days traditionally chosen for moving house, keyed
  to the lunar date, not the chart;
- **건제십이신 (建除十二神)** — the twelve day-officers (건·제·만·평·정·집·파·위·
  성·수·개·폐) cycling through the days;
- the **28-mansion (이십팔수, 二十八宿)** day layer.

These form a **separate almanac practice** with its own inputs (the calendar
date and cyclical day-counts, not the birth chart). A complete 택일 needs this
almanac cross-check done by a practitioner. **The engine and readers must not
present the chart-relative shortlist as a finished 택일, and must not invent or
approximate the almanac layers.**

## Scope & Limits

- The engine's "Auspicious Dates" output is a **chart-relative shortlist** — days
  in a given window ranked by favourable element and non-clash — **not** a
  substitute for a traditional 택일 consultation, which adds the almanac layer
  above.
- A well-chosen date is a **supporting condition, not a cause**. Saju describes
  tendencies; it does not guarantee that an event on a favourable day succeeds or
  that one on an unfavourable day fails. Phrase every date suggestion as an
  influence, not a prediction *(see `CLAUDE.md` ground rules 4–5)*.
- **Medical, legal, and financial timing** is set by professionals and real
  constraints. A chart-relative preference never overrides a surgeon's schedule,
  a filing deadline, or a market condition; if a querent asks for certainty here,
  decline it.
- 전통 해석이 확립되지 않은 경우 — where the classical sources do not settle a
  rule (e.g. ranking two equally non-clashing favourable days), say so rather
  than inventing a tie-breaker.

## How to Use This File

1. **Argue the chart first.** Complete `knowledge/09-interpretation-method.md`
   Steps 2–5 — Day Master, strength, and the 용신 (用神) / 희신 (喜神) / 기신
   (忌神).
2. **Narrow to a window** with the luck layers — 대운 / 세운 / 월운 *(see
   `knowledge/08-luck-pillars.md`)*. Date selection operates *inside* a window
   the luck layers already favour; it does not rescue a bad year.
3. **Rank the days in that window** with `## Chart-Relative Principles` and the
   event-type lean in `## By Event Type` — non-clash to the natal day / hour
   branch is the hard filter; favourable element and harmony are the ranking.
4. **For a two-person event**, apply `## Two-Person Events` and check
   `knowledge/11-gunghap.md`.
5. **Then, outside this system**, cross-check the almanac layer
   (황도길일 · 손없는날 · 건제십이신 · 28수) with a practitioner — see
   `## Scope Boundary — The Almanac Layer`.
6. Deliver the result as a **shortlist with reasons**, each day phrased as a
   tendency, with the `## Scope & Limits` caveats attached.
