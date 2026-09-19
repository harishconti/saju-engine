# Products and Reports

> **Positioning (2026-09-07 pivot):** target market is English-speaking global (K-culture fans,
> diaspora), priced in USD. India is a Phase-2 experiment only. Canonical line: *"an accurate engine
> and an honest interpreter — not a Korean master."* See `improvements_issues.md` and
> `docs/market-research-2026-09.md`.

## Single-chart products

Legacy internal names are still accepted by the engine but should not be advertised to new clients.
Prices are USD launch prices — see `improvements_issues.md` §4 for ranges and the pricing risk.

| Client-facing name | Engine tier | Price | Pages | Contents |
|---|---:|---:|---:|---|
| **The Hook** | `sample` | Free | ~1 | Compact cover, four pillars, element balance, Day Master, lucky colors/directions/numbers, upgrade CTA. |
| **The Essential Report** | `essential` | $9 intro → $19 | 6–7 | Cover, four pillars, element balance, quick reference, short Day Master portrait, career & wealth overview, major-luck table, abbreviated lucky attributes, short closing note. |
| **The Deep Destiny Report** | `deep` | $55 | 10–12 | Everything in Essential + full Day Master portrait, relationships, health & vitality, business & launch timing, year-by-year windows, full practical guidance, full closing note. |
| **Cosmic Companion** | `companion` | $9/mo or $79/yr | 3–4 | Focused timing read for the current month/quarter; manual-billing subscription (off the primary pricing grid). |

Legacy aliases: `spark` → `essential`, `reading` → `deep`, `fullmap` → `deep`.

## Compatibility (궁합) products

`generate_compat_report` accepts `favorable_element_a` / `favorable_element_b` — pass the
reader-argued 용신 from the hand-crafted natal reading so the natal and compat products agree
(`src/saju_engine/yongsin.py`).

| Client-facing name | Engine call | Price | Pages | Contents |
|---|---:|---:|---:|---|
| **Compatibility Snapshot (두 분 궁합)** | `generate_compat_report(..., tier="basic")` | $24 | ~4 | Composite 0–100 score + 4-band verdict, four-pillar glance, four decisive sub-systems, condensed practical guidance, closing note. |
| **Deep Compatibility (두 분 궁합)** — hero | `generate_compat_report(..., tier="deep")` | $45 | 9–10 | Basic + all 11 sub-system cards, per-partner element balance / Day Master snapshots, major-luck timelines, year-by-year couple timing overlay, full practical guidance, closing note. |

The 11 sub-systems are defined in `knowledge/11-gunghap.md` and implemented in `src/saju_engine/compat.py`.

## Report generation paths

### Direct engine report
```bash
PYTHONPATH=src python3 -m saju_engine \
  --date YYYY-MM-DD --time HH:MM --city "City" --gender M \
  --format premium --tier deep \
  --output-file /tmp/report.md
```

### From an existing markdown report
```bash
./tools/build-pdf.sh sruthi
```

### Combined base report + follow-ups
```bash
PYTHONPATH=src python3 src/saju_html/combine_candidate_report.py sruthi
./tools/build-pdf.sh --combined --html sruthi "Title" "Client" "DOB" "Day Master"
```

### Compatibility report
```bash
python3 src/saju_html/md_to_saju_compat_pdf.py <compat.md> --name-a ... --name-b ... --tier deep
```

## Candidate folder conventions

Each person receiving a reading gets a dedicated subfolder:

```
candidates_horoscope/reports/{name-slug}/
├── {name-slug}-report.md          # base natal reading
├── {name-slug}-combined.md        # base + follow-ups (optional)
├── {name-slug}-combined.pdf
├── career.md                      # follow-up topic files
├── relationships.md
├── health.md
└── 2027-outlook.md
```

Rules:
- Slug style: lowercase, hyphenated.
- Base report follows the 9-section premium scaffold from `knowledge/10-output-template.md`.
- Overlapping follow-ups append to the existing topic file with a dated heading (`## YYYY-MM-DD — summary`) rather than creating duplicates.
- Update the index table at the bottom of `candidates_horoscope/README.md` for every new candidate.

## Compatibility folder conventions

Each pair gets its own subfolder:

```
candidates_horoscope/marriage_compatibility/{name_a}_{name_b}/
├── {name_a}_{name_b}_compatibility.md        # basic tier
├── {name_a}_{name_b}_compatibility.pdf
├── {name_a}_{name_b}_compatibility_deep.md   # deep tier
└── {name_a}_{name_b}_compatibility_deep.pdf
```

Partner A is listed first; for heterosexual pairs Partner A is the male. Update the **Compatibility (궁합) readings** table at the bottom of `candidates_horoscope/README.md`.

## Premium 9-section scaffold

The Deep Destiny tier follows this structure (shorter tiers omit sections):

1. **Cover** — title, candidate info, Day Master, generation date.
2. **Chart at a Glance** — four-pillar table, element balance, quick reference, "What This Year Means for You" callout.
3. **Day Master Portrait** — strength, personality, tendencies.
4. **Career & Wealth** — best fields, wealth pattern, career archetypes.
5. **Relationships** — spouse palace, compatibility pattern, timing.
6. **Health & Vitality** — depleted-element watch, lifestyle cues.
7. **Timing: Major Luck & Annual Windows** — 대운 narrative + 2025–2030 windows.
8. **Practical Guidance Summary** — strengths, growth areas, recommendations, lucky attributes reference card.
9. **Closing Note** — synthesis of 2–3 specific chart features.

## Quality checklist before delivery

- Day Master identified and strength argued from seasonal + branch support.
- 용신/희신 derived, not asserted.
- Each pillar read in relation to the Day Master.
- Ten-god relationships used for personality/relationship/career.
- Special formations checked.
- Major-luck and annual luck integrated if the question is time-bound.
- Output follows `knowledge/10-output-template.md`.
- No claim beyond what the cited knowledge file supports.
- Citations stay in `.md` but are stripped from client PDFs automatically.

## Source anchors

- `knowledge/10-output-template.md`
- `knowledge/11-gunghap.md`
- `src/saju_engine/premium_report.py`
- `src/saju_engine/compat_report.py`
- `src/saju_html/combine_candidate_report.py`
- `tools/build-pdf.sh`
- `candidates_horoscope/README.md`
