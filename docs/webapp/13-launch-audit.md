# 13 — Launch audit (2026-10-15)

A point-in-time audit of the **live** service and the landing page: what is genuinely working, what is
broken, and what is promised but not kept.

Everything here was verified against the running system, not inferred from the other docs. Where a
claim is evidence-backed, the command or response is quoted.

> **Status: live, engine working — held back by a short checklist.** `https://www.cosmicsaju.com` serves
> the real site; the database, storage, auth, payments, the report engine, and (since 2026-10-16) the
> audio summary all work, and the contact mailbox now receives mail. What remains is the mailbox's
> **DKIM** records, webapp CI and end-to-end tests, the Dodo test→live migration, and rotating two leaked
> credentials. See §4.
>
> *Revised 2026-10-16: §B4, §D2, and the service table reflect the mailbox/contact work; `13` is a
> point-in-time document, so dates in the evidence are kept.*

---

## 1. Service state

| Service | Status | Evidence |
|---|---|---|
| **Hostinger** | ✅ registrar only | DNS lives at Cloudflare |
| **Cloudflare DNS** | ✅ nameservers; **proxy off** | `NS randy/veronica.ns.cloudflare.com` (authoritative); apex A → Vercel's `216.198.79.1` with the proxy **off** (`server: Vercel`, no `cf-ray`). Registration is at Hostinger, DNS at Cloudflare |
| **Cloudflare R2** | ✅ one bucket, `saju-engine-dev` | presigned PUT → `HeadObject` → presigned GET → delete all pass; an **unsigned** list is refused (bucket is private) |
| **Neon Postgres** | ✅ project `saju`, `aws-ap-southeast-1` | 14 tables; **13 hand-written `CHECK` constraints rejected bad rows by name** when probed; partial unique index `profile_one_default_per_user` present with the right predicate; all 8 enums correct |
| **Neon Auth** | ✅ enabled on `production` | JWKS reachable, Ed25519 key; trusted domains set; localhost allowed. ⏸️ Google still on Neon's **shared dev key** (deferred, >10 users) |
| **Vercel** | ✅ live | project `saju-engine`; root `apps/web`; region `sin1`; Node 24.x; **32 env vars**; Hobby plan |
| **Resend** | ✅ verified | Resend's **own API** reports `cosmicsaju.com` verified, region `ap-northeast-1`, DKIM + both SPF records verified |
| **Dodo Payments** | ✅ configured (**test mode**) | 4 products, all `one_time_price`; the exact `createCheckout()` payload returns HTTP 200 + a real `checkout_url`; the webhook passed **5/5** end-to-end checks against production |
| **GitHub** | ✅ linked | production branch `develop` |
| ✅ **report engine** | **written and deployed** | Second Vercel project `saju-report-engine` (root = repo root, region `sin1`). Verified locally *and* deployed: `/chart` reproduces the reference chart exactly, and `/generate` rendered a deep report (139,898 bytes, 1.6 s), PUT it to R2, and the downloaded bytes' sha256 matched. **1,909 pytest cases pass** (up from 1,846 — the engine service, the audio-script extractor, and 20 contract tests). See [05](05-report-pipeline.md) §1. |
| ✅ **Mailbox** | **live and receiving** | `hello@cosmicsaju.com` plus `privacy@` / `reports@` / `dmarc@` / `postmaster@` aliases. Records published **in Cloudflare** — a mail host cannot write to a zone it does not host, so until that was done the mailbox existed and received nothing. Now: `MX → mx1/mx2.hostinger.com` (5/10), exactly one apex SPF, `_dmarc` present; a real send to `hello@` reported **`delivered`** from Resend's API. ⚠️ The three DKIM CNAMEs are still missing |
| ❌ Uptime monitor, analytics, Turnstile | none | — |

---

## 2. Blockers

### ✅ B1 — RESOLVED and verified live

The hero CTA *"Get your free chart snapshot"* and both pricing CTAs used to land on a `503
ENGINE_UNREACHABLE`, publicly visible on a live, indexed site.

**Fixed, end to end, against production:**

```json
POST https://www.cosmicsaju.com/api/sample
→ 200 {"ok":true,"bytes":70899,"engineVersion":"0.2.0",
       "downloadUrl":"https://…r2.cloudflarestorage.com/reports/anonymous/…/sample.pdf?X-Amz-…",
       "expiresIn":900}
```

The downloaded artefact was checked: a valid PDF, a correct cover (`Born 15 August 1988, 14:20, Seoul`,
`Day Master Im (Water Yang)`), Korean terms properly romanised, and **zero** citation / draft /
reviewer leaks. The health probe is green across the board for the first time:

```json
{"status":"ok","db":true,"storage":true,"engine":true,"payments":true,"paymentsMode":"test_mode"}
```

### ✅ B2 — RESOLVED: engine prerequisites (E1/E2/E3) — all done, see [05](05-report-pipeline.md) §"Required engine changes — status"

| # | Change | File | Why it blocks |
|---|---|---|---|
| E1 | `SAJU_FONT_DIR` override + bundled DejaVu | `src/saju_html/md_to_saju_pdf.py` | The font directory is hardcoded to `/usr/share/fonts/truetype/dejavu`, which does not exist in a Vercel function; the renderer then silently degrades |
| E2 | **No silent geocoding on the request path** | callers of `src/saju_engine/pillars.py` | `sajupy` geocodes via Nominatim **only when `longitude is None`** (`sajupy/core.py:406`); when longitude is supplied it is used directly. The webapp always supplies one, so this is already satisfied on our path — the residual risk is a profile with `longitude = NULL`, which would trigger a live Nominatim call, a usage-policy breach, and a silent fallback that **changes the chart**. Remediation is therefore narrow: the service must *require* longitude and fail loudly without it |
| E3 | Thread `favorable_override` through the single-chart render path | `src/saju_html/chart_input.py` (`prepare_chart_render` → `chart_markdown`) | The CLI and the compat path already accept an override; **the single-chart web path does not** — and that is the review console's headline feature |

### ✅ B3 — RESOLVED: payments can now be fulfilled

This was never a payment problem — the engine simply did not exist, so a successful payment had nothing
to produce. With the engine live, `payment.succeeded` → `Job` → `runDispatchTick` can now render and
file a report.

What remains is **the test→live migration**, which is not a toggle: Dodo runs `test.` and `live.` as
separate servers, so live mode needs **4 new products**, a **new webhook endpoint** with a **new
signing secret**, and re-pointed `DODO_PRODUCT_*` values. Do that *after* a test-mode purchase has been
clicked through end to end.

### 🟢 B4 — Contact mail: receiving verified, DKIM still to add

`privacy@cosmicsaju.com` had **no MX record**, yet appeared on the privacy policy, the terms, the refund
policy, and the site footer. Investigating it surfaced a problem larger than the legal address:

| Where | What it told the client | Reality before the fix |
|---|---|---|
| `api/admin/reports/[id]/reject/route.ts` | *"we'll either fix this or refund you — **just reply to this email**"* | bounced |
| report page, `FAILED` state | *"…**reply to your order email**"* | bounced |
| report page, audio failed | *"…**reply to your order email** if you'd like us to try again"* | bounced |
| privacy / terms / refund policy / footer | `privacy@cosmicsaju.com` | bounced |

**Fixed in the app (2026-10-16):** one mailbox (`hello@cosmicsaju.com`) with receive-only aliases now
exists; the published contact is **split** — `hello@` for general contact and the footer, `privacy@`
reserved for data-protection requests so those are recognisable on arrival; and `sendEmail()` applies a
default **`Reply-To: hello@cosmicsaju.com`** (`EMAIL_REPLY_TO`), so every *"just reply"* invitation now
has somewhere real to land. Verified live: `/privacy` publishes `privacy@`, the site footer publishes
`hello@`, and a real Resend delivery stores `reply_to: ["hello@cosmicsaju.com"]`.

**✅ Now published, and receiving is verified.** The MX/SPF/DMARC records live in the **Cloudflare** zone.
A mail host cannot publish them for you — it does not host the zone, which is why its panel says *"log in
to Cloudflare … and add the records below"*. While that was pending, `MX` was `NONE` even though the
mailbox was configured. Today: `MX → mx1/mx2.hostinger.com` (priority 5/10), exactly one apex SPF
(`v=spf1 include:_spf.mail.hostinger.com ~all`), and `_dmarc` = `v=DMARC1; p=none`. A real message sent
from the app's own `EMAIL_FROM` to `hello@cosmicsaju.com` was reported **`delivered`** by Resend's API,
with `reply_to: ["hello@cosmicsaju.com"]`.

**⚠️ Remaining: DKIM — our side is done, one Hostinger-side gap.** Measured by DNS-over-HTTPS
(2026-10-16, after the records were fixed):

| Name | Resolves (CNAME) | Key served | Verdict |
|---|---|---|---|
| `hostingermail-a._domainkey` | ✅ | `v=DKIM1;k=rsa;p=MIIBIj…` | ✅ valid |
| `hostingermail-b._domainkey` | ✅ | `v=DKIM1;p=` — empty | ❌ Hostinger-side |
| `hostingermail-c._domainkey` | ✅ | `v=DKIM1;p=` — empty | ❌ Hostinger-side |

All three CNAMEs now resolve and the earlier mistyped `c` record (the *value* pasted into **Name**) has been
replaced — **so nothing further is possible in Cloudflare.** Selectors `b` and `c` serve **empty** keys at
Hostinger, so they can never validate; only `a` carries a real key.

**Decisive test:** send from `hello@` in Hostinger webmail to a Gmail address → *Show original* → read
`dkim=` and `header.s=`. `dkim=pass … header.s=hostingermail-a` means the empty selectors are simply unused
and the panel warning is cosmetic. `dkim=fail … header.s=hostingermail-b|-c` means Hostinger must issue the
keys. **Neither case risks delivery:** `_dmarc` is `p=none`, and DMARC passes on SPF alignment alone (the
envelope sender is `…@cosmicsaju.com`; the apex SPF authorises Hostinger), so this is reputation hygiene,
not deliverability.

⚠️ **Scope:** only mail sent **by hand from Hostinger webmail** is affected. The app's mail goes through
**Resend** (`resend._domainkey`, verified), so reports, audio and reject emails are fine. *"Pointing to
external provider"* is expected — the zone is Cloudflare's. `_dmarc` should still gain
`rua=mailto:dmarc@cosmicsaju.com` (it is currently bare `p=none`).

### 🟠 B5 — Partly resolved: CI now gates the webapp; end-to-end tests still missing

- ✅ **Fixed 2026-10-16.** `.github/workflows/ci.yml` now triggers on **`develop`** (the production
  branch) and `main`, and adds a **webapp** job: `npm ci` → `prisma generate` → lint → typecheck →
  `vitest run` → `next build`. Before this it triggered on **`main` only**, so it never ran for real
  work at all, and it covered the Python engine alone. All five webapp steps were run locally with
  placeholder secrets before committing, so the first push is green rather than a discovery exercise.
- **No end-to-end tests exist**, although [12 — Testing](12-testing.md) describes Playwright specs
  (`auth-gate.spec.ts`, `landing.spec.ts`, `order.spec.ts`, …) as though they did.

**This is not theoretical.** The project sat with Vercel's **Root Directory set to
`apps/landing-page`** — a directory whose `src/` is not in this repo — so nothing built and the domain
returned `DEPLOYMENT_NOT_FOUND`. Nothing flagged it; it was found by inspecting the project settings.

### 🟡 B6 — Lesser items

| # | Item | Note |
|---|---|---|
| 1 | **Rotate two leaked credentials** | A Neon password and a Resend API key appear in the working session transcript (tooling masking slips, not a code leak). Nothing is in git |
| 2 | `ADMIN_EMAILS` is an **assumed** address (`ngharish.conti@gmail.com`) | If it does not match the sign-in email, `/admin` is unreachable by anyone |
| 3 | No uptime monitor | An outage would go unnoticed |
| 4 | No `_dmarc` TXT record | Deliverability only; Resend does not require it for verification. It is now part of the mailbox record set — add it when publishing those ([07](07-services-and-integrations.md) §Mailbox records) |
| 5 | The only R2 bucket is named `saju-engine-dev` but holds production reports | A deliberate single-bucket decision; the name will mislead later |
| 6 | No analytics | Sample → signup → purchase conversion is unmeasurable |

---

## 3. Landing page discrepancies

### ✅ D1 — RESOLVED: the MP3 is now real

The public demo PDFs promised an "included MP3 audio summary", the free sample repeated it, and
`README.md` said the MP3 was produced separately. A customer could read the promise before paying.

**Resolved by delivering it** rather than by deleting the claim. The audio is a **deterministic
derivation of the approved report text** — no model writes it — so it can be produced *after* the human
review without a second review pass, and it says nothing the PDF does not. Delivery does not wait for
it: the PDF lands at approval and the audio follows, with the client's page showing *"being prepared"*.
See [05](05-report-pipeline.md) §6.1.

Cost is ~$0.32–0.40 per Deep report on ElevenLabs Flash v2.5 — about 0.6% of a $55 sale.

Still outstanding, and smaller: the **window mismatch** in the copy. The audio note promises timing
windows for `current_year … +2` while the sample upsell promises `current_year … +5`; the narration now
covers the report's full window, so the note under-promises. Harmless, but it should be reconciled —
and it moves the golden snapshots, so it is its own change.

### 🟡 D2 — Documentation drifts from reality

| Doc says | Reality |
|---|---|
| `POST /api/contact` exists | **Resolved:** it never did. Removed from [03](03-api-spec.md) — contact is a `mailto:` to a monitored address, which is honest and needs no spam-filtering surface |
| Turnstile protects the free-sample form | Only a `turnstileToken` field in the zod schema. **No widget, no server-side verification**; the Postgres rate limit (5/min/IP) is the only protection |
| Playwright specs exist | None do |
| CI covers the webapp | ✅ **Fixed 2026-10-16** — it now triggers on `develop` (production) and runs a webapp job. Only the Playwright tier is still outstanding (§B5) |
| The repo tracks the webapp | ❌ **It did not.** `apps/web` had **0 tracked files**, and the root `.gitignore`'s unanchored `lib/` was silently swallowing `apps/web/src/lib/` — 34 files including `fulfilment.ts`, `queue.ts` and the entire Vitest suite. Committed 2026-10-16 after anchoring those patterns; verified against a fresh clone |
| The demo PDFs are "old HTML/Chromium renders" (D5 below) | ❌ **Wrong, corrected by inspection:** all five are **ReportLab** renders (`Producer: ReportLab PDF Library`, dated 2026-10-01), i.e. the same toolchain customers get. They are simply **stale** — pre-audio and pre-`$19` |

### 🟢 D3 — What is already right

- **No fabricated testimonials.** The section was never built, so the documented FTC risk (worklog LP3)
  is resolved by omission rather than papered over.
- **Pricing renders correctly**: `$19 / $55 / $24 / $45`, matching the four Dodo products exactly.
- The three legal pages exist, and the copy avoids medical/legal/financial certainty.

### ⚠️ D4 — A claim never yet exercised

The page states *"Reviewed by a human"* and *"usually takes under a day"*. The review console exists, but
**not one report has ever been reviewed**, because none can be generated. The claim is not dishonest —
it simply has no evidence behind it yet.

### 🟡 D5 — Polish

No `og:image` (social shares are text-only; `twitter:card` is `summary`, not `summary_large_image`).

The demos are **stale ReportLab renders** — inspection (2026-10-16) shows all five carry
`Producer: ReportLab PDF Library` and a creation date of **2026-10-01**, so they use the *same* renderer
customers receive. An earlier note here claimed they were "old HTML/Chromium renders"; that was wrong.
The real drift is age, not toolchain: they predate the audio summary, and `demo-rm-essential.pdf` still
advertises **"$9 intro → $19"** while the product sells at **$19** flat. Regenerate them, and drop the
retired intro price from the Essential cover.

---

## 3a. The free tier: four findings, all fixed (2026-10-16)

The free snapshot is the one report that needs **no** review — deliberately, and for three reasons: it is
the only artefact that has to be instant (it is the proof the product works), it carries almost no
interpretive surface (pillars, balance, Day Master and lucky cues are engine-derived *facts*; the
judgement lives in the paid prose), and reviewing a free snapshot would devalue what paid tiers are
paying for.

The implementation only *accidentally* agreed with that, in four ways:

| # | Finding | Fix |
|---|---|---|
| 1 | **`requiresReview` was dead data** — declared on the tier map and asserted in tests, but read by **no application code**. `processClaimedJob` always set `DRAFT_READY`, so any free tier added later would silently join the review queue | The rule is now consulted via `autoDelivers()`; a non-review tier is created `DELIVERED` with a `Delivery(PROFILE)` row and emailed after commit. Unit-tested, including that an **unknown** tier fails safe |
| 2 | **`POST /api/orders` accepted `tier: "sample"`** (price 0 → `PAID` + a job) → the free report landed in the review queue. Unreachable from the UI, reachable from the API | Rejected with `422 TIER_NOT_ORDERABLE`; the snapshot has its own synchronous path |
| 3 | **"Saved to your profile" was half true.** The sample saved a `Profile` but **never a `Report`**, so the PDF never appeared in the dashboard library and the download link expired after 15 minutes | A signed-in sample is now filed as a delivered `Report` under `reports/{userId}/samples/…` — outside the swept prefix — and reuses a profile for identical birth details instead of accumulating one per run |
| 4 | 🐛 **Anonymous samples were never deleted.** The sweep found stale objects by querying `Report` rows with `orderId: null` — but anonymous samples create **no row**, so it matched nothing and they accumulated in R2 forever (~70 KB per visitor) while `05` claimed a 7-day sweep | The sweep now lists `reports/anonymous/` **by prefix and deletes by object age**, plus a row-backed pass scoped to never-delivered drafts so it cannot touch a sample a user kept |

Nothing had leaked yet — `users (real): 0` at the time.

## 4. Remediation, ordered

**Blocking a real sale:**

1. ~~Build `services/report-engine` and land E1/E2/E3~~ — **done** (engine at `api/index.py`, root = repo root); fixes the broken CTA **and** unblocks fulfilment
2. ~~Make the contact address real~~ — **done**: mailbox + aliases in Cloudflare, receiving verified
   (`delivered`), default `Reply-To` wired. ⚠️ Add the three **DKIM CNAMEs** — §B4
3. Regenerate the demo PDFs with ReportLab; remove the MP3 promise; drop the `$9 intro` from the
   Essential cover
4. Rotate both leaked credentials; confirm `ADMIN_EMAILS`
5. **Then** go live: 4 live products, a live webhook endpoint, `live_mode`

**Trust and safety net:**

6. A webapp CI job (lint / typecheck / vitest / build)
7. Playwright public tier: every protected route 401s, both themes render, the sample flow completes
8. Uptime monitor on `/api/health` (10 s timeout); wire Turnstile properly or drop the claim

**Nice to have:**

9. `og:image`; 10. analytics; 11. the `_dmarc` record (folded into the mailbox set); 12. reconcile the docs

---

## 5. Open decisions

| # | Decision | Status |
|---|---|---|
| 1 | ~~The MP3 promise~~ | ✅ **Decided: produce the audio.** Delivered as a deterministic derivation of the approved text ([05](05-report-pipeline.md) §6.1). Remaining nit: the note says `current_year … +2` while the upsell says `+5` |
| 2 | ~~Priority (engine vs trust gaps)~~ | ✅ **Resolved by events** — the engine landed, so the broken CTA and fulfilment are both unblocked |
| 3 | Contact addresses: one address or two? | ✅ **Decided (2026-10-16): two.** `hello@` for general contact, `privacy@` reserved for data-protection requests — so a DSAR is recognisable on arrival, and the published privacy address is the one a regulator expects |
| 4 | The `-dev` R2 bucket holding production reports | Rename later, or accept |

---

## Source anchors

- `apps/web/src/app/page.tsx` — the live landing page copy
- `apps/web/public/demo/*.pdf` — the public demo artefacts (and the MP3/$9 discrepancies)
- `apps/web/src/app/api/sample/route.ts` — the endpoint returning `ENGINE_UNREACHABLE`
- `apps/web/src/lib/dodo.ts`, `apps/web/src/app/api/webhooks/dodo/route.ts` — payments
- `apps/web/src/lib/contact.ts`, `apps/web/src/lib/email.ts` — the published addresses and the default
  `Reply-To` (the fix for §B4)
- `apps/web/scripts/dodo-webhook-smoke.mjs` — the end-to-end payment verification
- `docs/webapp/05-report-pipeline.md` — the engine contract and the E1/E2/E3 remediation
- `docs/openwiki/products/reports.md`, `README.md` — the MP3 and pricing statements the demos contradict
