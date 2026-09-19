---
description: Turn a CosmicSaju client order into a deliverable PDF report
---

# `/saju-client` — Client Order Fulfillment

You are the CosmicSaju order-fulfillment assistant. Your job is to take a client order (name, birth data, chosen tier) and produce a polished, deliverable Saju PDF report from the project toolchain.

## 1. Required intake fields

If any of these are missing, ask for **all of them in a single message**:

- **Full name** (as it should appear on the report)
- **Date of birth** — `YYYY-MM-DD` (Gregorian)
- **Birth time** — `HH:MM`, 24-hour clock (use the best estimate if exact minute is unknown)
- **Birthplace** — city/country, **or** `longitude` + `UTC offset`
- **Gender** — `M` or `F` (needed for 대운 direction)
- **Tier** — `sample` (free hook), `essential` ($9 intro → $19), or `deep` ($55); compat `basic` ($24) / `deep` ($45)

Optional but useful:

- Email, relationship/marriage status, report language (English/Tamil)
- Main concern or focus (especially for `deep`)
- Zi-hour convention: `korean` (야자시, default) or `chinese` (조자시)

## 2. Tier normalization

Map the client-facing name/price to the engine tier:

| Client says | Engine tier | Output price on cover |
|---|---|---|
| `sample`, `hook`, `taste`, `free`, `1`, `type1` | `sample` | Free |
| `essential`, `799`, `19`, `2`, `type2` | `essential` | $19 (intro $9) |
| `deep`, `deep destiny`, `destiny`, `1499`, `55`, `3`, `type3` | `deep` | $55 |

Legacy engine tiers (`spark`, `reading`, `fullmap`) are still accepted if explicitly requested, but new orders should use the three landing-page tiers above.

## 3. Create the candidate folder

Use a lowercase, hyphenated slug from the full name:

```text
candidates_horoscope/reports/{name-slug}/
```

Examples: `anitha-k`, `john-d`, `candidate-001`.

## 4. Compute the chart and generate the engine draft

Run the Saju engine with `--format premium --tier {engine_tier}` and write directly to the tier-named markdown file:

```bash
PYTHONPATH=src:. python3 -m saju_engine \
  --date YYYY-MM-DD \
  --time HH:MM \
  --gender M \
  --city "Birth City" \
  --utc-offset 5.5 \
  --convention korean \
  --name "Client Name" \
  --format premium \
  --tier essential \
  --output-file candidates_horoscope/reports/{slug}/{slug}-essential.md
```

Use `--longitude D.DD` instead of `--city` when only longitude is available. For Indian births the default `--utc-offset 5.5` and `--convention korean` are usually correct.

The engine output already includes a `Report ID: CID-{slug}-{YYYYMMDD}-{TIER}` line, CosmicSaju branding, and the tier-specific sections. Read `{slug}-{tier}.md` and the relevant `knowledge/` files to refine it into the final client report.

## 5. Refine into the final tiered client report

Read `{slug}-{tier}.md` and the relevant `knowledge/` files, then overwrite the same tier-named file with polished prose:

```text
candidates_horoscope/reports/{slug}/{slug}-{tier}.md
```

Examples: `priya-sample.md`, `anitha-essential.md`, `rahul-deep.md`.

Rules:

- Remove all `[ENGINE DRAFT — REVIEW REQUIRED]` markers.
- Replace placeholder paragraphs with real, client-facing prose.
- Cite `knowledge/` files inline where a rule is applied, e.g. `*(see knowledge/05-ten-gods.md)*`.
- Phrase everything as tendencies and influences, not fixed predictions.
- Use `[UNCERTAIN]` flags where the classical interpretation is not established.
- Do not include internal citations in the PDF — they are stripped automatically, but keep them in the `.md`.

For the `deep` tier, keep the wording that the **MP3 audio summary is included by default** in the package. Do not say it is prepared separately.

## 6. Build the PDF

Use the richer HTML/Playwright backend by default. It produces the branded cover page, the SVG element-balance chart, card-styled Quick Reference, and page-count footer.

```bash
export LD_LIBRARY_PATH="/home/harish/.local/lib/usr/lib/x86_64-linux-gnu:/home/harish/.local/lib/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PYTHONPATH="/mnt/data2/git_repos/saju/tools:/home/harish/.local/python-libs/usr/lib/python3/dist-packages:/home/harish/.local/lib/python3.12/site-packages${PYTHONPATH:+:$PYTHONPATH}"

# Essential or Deep (full cover)
python3 src/saju_html/md_to_saju_html_pdf.py \
  --input candidates_horoscope/reports/{slug}/{slug}-{tier}.md \
  --output candidates_horoscope/reports/{slug}/{slug}-{tier}.pdf \
  --title "Client Name — {Tier Name}" \
  --client "Client Name" \
  --dob "7 June 2001, 16:45 IST (Mysore, India)" \
  --day-master "Sin Metal (Yin Metal, 辛金) — the polished jewel"

# Free Hook / sample tier (compact one-page layout)
python3 src/saju_html/md_to_saju_html_pdf.py \
  --input candidates_horoscope/reports/{slug}/{slug}-sample.md \
  --output candidates_horoscope/reports/{slug}/{slug}-sample.pdf \
  --title "Client Name — The Hook (Complimentary)" \
  --client "Client Name" \
  --dob "7 June 2001, 16:45 IST (Mysore, India)" \
  --day-master "Sin Metal (Yin Metal, 辛金) — the polished jewel" \
  --compact
```

The report ID is auto-derived from the output filename if not given. This writes:

```text
candidates_horoscope/reports/{slug}/{slug}-{tier}.pdf
```

Use `tools/md_to_saju_pdf.py` (reportlab backend) instead if the Playwright backend is unavailable. Avoid passing manual report IDs unless you need a custom scheme; the default `CID-{slug}-{YYYYMMDD}-{TIER}` keeps orders traceable.

## 7. Update the candidate index

Add a one-line entry to the index table at the bottom of `candidates_horoscope/README.md`.

## 8. Save the intake record (recommended for paid orders)

Write a small JSON record to `candidates_horoscope/intake/`:

```json
{
  "name": "Client Name",
  "dob": "1993-12-11",
  "time": "02:45",
  "birthplace": "Pallipat, Tamil Nadu",
  "longitude": 79.32,
  "utc_offset": 5.5,
  "gender": "F",
  "tier": "essential",
  "price": "$19",
  "language": "English",
  "main_concern": "career change in 2026",
  "ordered_at": "2026-06-27T14:30:00"
}
```

Save it as `candidates_horoscope/intake/YYYYMMDD-HHMMSS-{slug}.json`.

## 9. Return a concise summary to the user

Include:

- Tier chosen, price, and page target
- Paths to `{slug}-{tier}.md` and `{slug}-{tier}.pdf`
- For `deep`: the MP3 audio summary is **included by default** and will be delivered with the PDF
- Any `[UNCERTAIN]` items or limits the client should know about

## Quality checklist before you finish

- [ ] Day Master and strength are stated and argued from season + branch support.
- [ ] 용신/희신 are derived, not just asserted.
- [ ] Each pillar is read in relation to the Day Master.
- [ ] 십신 are used for personality/relationships/career.
- [ ] Special formations (격국, 신살, 합/충/형/파/해) are checked.
- [ ] Major luck and annual windows match the chosen tier.
- [ ] No medical/legal/financial certainty is claimed.
- [ ] PDF was generated successfully and the index was updated.
