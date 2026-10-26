# 10 — Privacy and compliance

This product handles **birth date, birth time, and birthplace** — the exact triple that constitutes
special-category-adjacent personal data under GDPR and sensitive personal data under India's DPDP Act.
It also handles email, name, and payment metadata. This page is the reasoning and the controls.

Two audiences matter here: **data-protection law** (GDPR/UK GDPR for EU/UK visitors, DPDP for India,
state privacy laws for the US) and **the product's own ground rules** about what may be claimed.

---

## 1. What data we hold, and why

| Data | Where | Classification | Lawful basis / purpose |
|---|---|---|---|
| Email, name | Neon (`User`) + Neon Auth | Personal data | Contract (account, delivery) |
| **Birth date, time, place, coordinates** | Neon (`Profile`) | **Sensitive / special-category-adjacent** | Explicit consent at sign-up and at profile creation |
| The **place index** behind the birthplace picker | `public/city-index.json`, served from our own origin | **Not personal data** — a static gazetteer | CC BY 4.0 (GeoNames); attribution in the footer. **No birthplace guess is ever sent to a geocoder**, so typing a place does not disclose it to a third party, and the coordinates stored at profile creation come from this file rather than from Nominatim |
| Report PDF + source markdown | Cloudflare R2 (private) | Personal data (derived) | Contract (the product itself) |
| Payment records | Dodo Payments (MoR) holds card data; we hold an order id, amount, status | Personal + financial | Contract, legal obligation (tax) |
| Audit log (actor, action, ip, ua) | Neon (`AuditLog`) | Personal data | Legitimate interest (security, dispute resolution) |
| Consent records | Neon (`ConsentRecord`) | Personal data | Legal obligation (proving consent) |
| Delivery log (email address, provider message id) | Neon (`Delivery`) | Personal data | Contract |
| **Correspondence** — support mail, refund requests, DSARs | **Hostinger email** (`hello@`, with the `privacy@` alias) | Personal data | Legitimate interest / legal obligation (answering the request). Lives in the mail provider's mailbox, **not** in our database |
| Anonymous sample objects | R2 `reports/anonymous/…` | Personal data until unlinked | Consent; **swept after 3 days** |
| Emailed sample address | Neon (`SampleLead`) | Personal data | **Consent** for the course; legitimate interest for the snapshot the person asked for. Deliberately holds **no birth data** — the visitor is anonymous |
| Webhook payloads | Neon (`WebhookEvent`) | May contain name/email from the MoR | Legitimate interest; purged at 90 days |

**We never hold:** card numbers, CVVs, passwords, OAuth tokens, or session tokens. Those are
Dodo Payments's and Neon Auth's respectively.

---

## 2. Consent

One checkbox at sign-up, recorded as a `ConsentRecord` with `policyVersion`, `grantedAt`, `ip`, and
`ua`. Purposes are stored as a JSON map so a future purpose can be added without a migration:

```json
{ "service": true, "service_messages": false }
```

| Purpose | Required? | Meaning |
|---|---|---|
| `service` | **Yes** | Process birth data to produce a report, email it, store it |
| `service_messages` | No | Non-essential service email (reminders, product news). Default off, and nothing sends without it |

Rules:

- Consent is recorded **before** any birth data is submitted, not after. **This is enforced, not merely
  promised:** `POST /api/profiles` and `PATCH /api/profiles/{id}` refuse with `403 CONSENT_REQUIRED` unless
  the most recent `ConsentRecord` is un-withdrawn and grants the `service` purpose
  (`src/lib/consent.ts`). Withdrawal needs no second code path — it is the same check reversed.
  It had to be made explicit because it was not true: recording consent was a best-effort *browser* call
  and nothing on the server ever looked, so the first real signup produced an account with **no**
  `ConsentRecord`, and the account page displayed the required consent as already granted on top of that.
- Withdrawing consent is a first-class action in `/dashboard/account`, not an email request.
  Withdrawing `service` stops processing and starts the deletion path.
- `ConsentRecord` is **append-only**. Never update a consent row; insert a new one and set
  `withdrawnAt` on the old. The history is the evidence.
- The exact policy version is stored, so "they consented to *that* text" is provable.

⚠️ **The birth-data consent wording matters more than the rest of the policy combined.** It must say,
plainly, what is collected, what it is used for, and that it is stored to produce and re-deliver the
report. A generic "we value your privacy" paragraph does not meet the bar for this category of data.

### Email

Two different things are being captured on the free-snapshot screen, and they must not be conflated:

- **The snapshot itself** is sent because the person asked for it — a requested message, not marketing.
  It needs no opt-in, and the form does not gate it: the result is on screen before the address is ever
  asked for (`06-frontend-ux.md`).
- **The five-part course, and anything else** is marketing. It is a **separate, unticked** checkbox, and
  `SampleLead.marketingOptIn` defaults to `false` **at the database level** as well as in the form, so an
  omitted field cannot be read as consent — which is the failure mode that matters, because for an
  anonymous visitor this row is the only record of their wishes.

Why `SampleLead` and not `ConsentRecord`: `ConsentRecord` is keyed to `userId` and its job is to prove
the lawful basis for holding **birth data**. An anonymous visitor has no `User` row and we hold no birth
data for them; they gave us an address. Recording an address as if it were birth-data consent would
overstate what was agreed to, in the direction that looks thorough and is actually wrong.

The address is stored with the `policyVersion` in force at the time, the IP it came from, and a `source`
of `sample`. Erasure requests are honoured against this table like any other, and the row is what makes
"we never emailed anyone who did not ask" checkable rather than asserted.

**Opt-out.** The transactional `Reply-To` points at a monitored mailbox, and the form's copy says
replying unsubscribes — so the promise has a working mechanism today rather than a hoped-for one. That is
adequate while nothing but the *requested* snapshot is sent. ⚠️ **Before the first marketing send**, add a
one-click unsubscribe (a tokenised route, not "reply and we'll do it") and a `unsubscribedAt` column:
reply-to is a courtesy, and a course is a marketing list, where consent withdrawal has to be as easy as
consent was given. Recorded as an open item rather than left implicit.

---

## 3. Retention

| Data | Retention | Mechanism |
|---|---|---|
| Anonymous samples (R2 + any row) | **3 days** | Cleanup cron — the *only* thing that deletes them: there is no R2 lifecycle rule on `reports/anonymous/` |
| Profiles / birth data | Until the user deletes it, or 24 months of inactivity | Daily sweep retires a profile only when its row, **every order and report that references it** (including a recent delivery of one), **and its owner's `COALESCE(lastSeenAt, createdAt)`** are older than 24 calendar months. There is **no warning at 23 months**: nothing in the app sends scheduled mail, so the warning was never implemented — the sweep is the whole mechanism |
| Reports + PDFs | Until deletion is requested, or with the retirement of their profile | Erasure deletes the `Report` rows and queues the R2 objects; the inactivity sweep does the same for a retired profile's reports |
| Account after a deletion request | Deleted, with `Order`/`Report` rows anonymised | 30-day grace, then cleanup cron |
| `Job`, `WebhookEvent` | 90 days | Cleanup cron |
| `RateLimit` windows | 1 hour | Cleanup cron |
| `IdempotencyKey` | 7 days | Cleanup cron |
| `Delivery` | 24 months | Kept for support; contains an email address |
| Mail in the mailbox | Kept while useful for support — **not a system of record** | Manual. The `Reply-To` routes client replies to `hello@`, so this is where a reply lands; nothing in the app depends on it |
| `AuditLog` | 24 months | Kept for dispute resolution |
| `ConsentRecord` | As long as the account, plus 24 months after deletion | Proof of consent |
| `SampleLead` (an emailed address from the free snapshot) | Until erasure is requested | **Kept on purpose — a lead that expires is not a lead.** No sweep. `marketingOptIn: false` rows are kept too: they are the record that someone *declined*, which is what makes the opt-in rows meaningful |
| Payment/financial records | As long as tax law requires (typically 7–8 years) | **Held by Dodo Payments (MoR), not by us** |

The financial-records retention is a genuine reason the MoR is the right choice: tax-retention
obligations are theirs to meet, and we simply do not hold the data that has to be kept.

---

## 4. Deletion

Self-service, cancellable, with a grace period.

```
POST /api/account/deletion
  → DeletionRequest{ status: 'pending', scheduledFor: now + 30 days }
  → immediate effect: account deactivated, sign-in blocked

DELETE /api/account/deletion
  → status: 'cancelled'  (allowed any time before scheduledFor)

cleanup cron, on scheduledFor:
  → anonymise the User: name = 'Deleted user',
                        email = 'deleted+<id>@deleted.invalid',
                        deletedAt = now
  → delete all Profiles (birth data gone)
  → delete all Report rows; queue every pdfKey/mdKey to ObjectDeletion
  → delete Consents? NO — mark withdrawn, retain for the audit trail
  → RETAIN Order rows (anonymised): amount, currency, paidAt, providerOrderId
    Reason: financial records and dispute defence. No birth data, no name, no email.
  → AuditLog entry with action 'delete'
```

Why the 30-day grace: it is the industry norm, it protects a user who deletes in anger, and it gives
support a window to intervene on an active order. Why it is cancellable: a deletion you cannot undo is
a support ticket.

**What survives a deletion, and why being explicit about it matters:**

| Survives | Reason |
|---|---|
| `Order` rows, anonymised (amount, date, provider id) | Financial record-keeping and dispute defence |
| `AuditLog` entries | Security and dispute resolution; contains no birth data |
| `ConsentRecord` | Proof that consent was obtained and withdrawn |
| `Delivery` rows, anonymised | Support |
| Mail already received in the mailbox | A mail thread you sent is a record of your request. It sits with the mail provider, not in our database |
| Anything Dodo Payments holds | They are the MoR and the tax record-keeper |

The privacy policy must **state these survivors explicitly**. "We delete everything" is false and is
the kind of false statement that turns a complaint into a penalty.

### Data-subject access

There is no automated export endpoint in v1. The process is: **the request arrives at `privacy@cosmicsaju.com`** (the address reserved for exactly this, so it is recognisable on sight), the owner assembles the user's
`Profile`, `Order`, `Report` (PDFs included), `Consent`, and `AuditLog` rows, and emails them from
`hello@cosmicsaju.com`. Document this in the policy with a stated response window (GDPR: 1 month).

**Add an export endpoint before volume makes this tedious** — it is a read-only route over data that
already exists, and manual fulfilment is the kind of thing that quietly becomes a legal miss.

---

## 5. Security controls

| Control | Implementation |
|---|---|
| Transport | TLS everywhere (Vercel-managed certs) |
| At rest | Neon encryption at rest; R2 encryption at rest. **No column-level encryption** — see the decision record below |
| Access to birth data | Only through routes that check ownership; never logged; never in an error message |
| File access | Private R2 bucket, presigned URLs (≤1 h), ownership-checked, no public URL exists |
| Downloads | Forced-download variant sends `octet-stream` + `Content-Disposition: attachment` + `nosniff` |
| Admin | `role = ADMIN` **and** email in `ADMIN_EMAILS` — two independent conditions |
| Rate limiting | Postgres fixed-window per IP/user on every write and the sample endpoint |
| Abuse | Cloudflare Turnstile on the sample flow |
| Webhooks | HMAC verification + event-id dedupe |
| Injection/XSS | zod on every input; React escaping; no `dangerouslySetInnerHTML` on user data |
| Secrets | Vercel env vars per scope; password manager as source of truth; no secret ever committed |
| Least privilege | The engine service holds no database credentials and no R2 credentials (it receives one presigned URL) |
| Logging | ids and error classes only. `jobs.py` already documents that exception *messages* can embed birth data |
| Headers | CSP (self + R2 only), HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, restrictive `Permissions-Policy` |

### Decision record: no column-level encryption

The retired SQLite store encrypted name/email/concern with Fernet (`SAJU_INTAKE_KEY`). The webapp does
**not** do this, deliberately:

| For | Against |
|---|---|
| Defence if the database is read | Breaks every `WHERE` on name/email, so search, support lookup, and reconciliation all need decrypt-and-filter |
| Preserves the previous posture | Key management becomes a launch blocker; a lost key is unrecoverable data |
| | Neon already encrypts at rest; the threat model it addresses (a raw dump) is largely covered |
| | It would encrypt data that is *already* in the report PDF in cleartext — the PDF is the product. Encrypting the columns while serving the PDF makes the encryption theatre |

If the threat model changes — for example, a regulator or a customer explicitly requires it — the
right move is not to encrypt individual columns but to add a second, encrypted-at-rest data store for
the birth data, or to move to a provider with client-side encryption. That is a redesign, and it
should be a decision, not a patch.

---

## 6. Disclaimers and the product's own ground rules

These come from [`CLAUDE.md`](../../CLAUDE.md) and apply to the site copy as much as to the reports.

| Rule | Where it must appear |
|---|---|
| **No medical certainty** | Report prose; site FAQ; never "this will cure/treat" |
| **No legal certainty** | Same |
| **No financial certainty** | Same. The Deep tier discusses career and wealth *timing and tendencies*, never instructions or guarantees |
| **No master/guarantee claims** | Site copy and reports. Positioning is explicitly "not a Korean master" |
| **No fabricated social proof** | The current illustrative testimonials are a documented FTC risk (worklog LP3). Replace with real, permissioned reviews or remove the section |
| **No false delivery promise** | Because every paid report is reviewed (D5), the copy must state the review window. "Instant" would be a misrepresentation |
| **No auto-calculated pillars presented as fact** | The user sees the derived pillars and confirms them before paying |
| **Citations stay internal** | A citation or reviewer note must never reach a client deliverable. Enforced by a `pdftotext` leak test, not by care |

### Minors

Paid readings cover relationship and health guidance, so they are sold to adults only.

- **Enforced server-side, not only in the form.** `orderSchema`
  (`apps/web/src/lib/validation/schemas.ts`) requires `adultConfirmed: true` — an absent or falsy
  field is a refusal, not a default — so a direct `POST /api/orders` cannot skip it. The order flow
  shows the checkbox and disables the pay button until it is ticked.
- **Why it exists.** The Hallyu / K-pop-adjacent audience this product can reach skews young. A paid
  report carrying health and relationship content sold to a 15-year-old is a reputational and
  payment-dispute risk, and merchant-of-record expectations assume an adult buyer.
- **The evidence is the order's audit row.** `POST /api/orders` records
  `adultConfirmed: true` on the `order.create` audit entry alongside the actor and timestamp. It is
  deliberately *not* a `ConsentRecord`: it is a per-purchase affirmation, not reusable consent, so it
  belongs with the order rather than in the consent history.
- **Not yet covered: the free snapshot.** `/sample` is deliberately account-free and un-gated (see
  [06](06-frontend-ux.md)), takes no payment and stores no row for an anonymous caller, so it asks
  for no age affirmation today. Revisit if that path ever collects contactable details.

**A chart has a minimum age too — one year.** This is a different rule from the 18+ affirmation
above (that one is about *who buys*; this one is about *whose chart can be read*).

- **Enforced server-side.** `validateBirth` (`apps/web/src/lib/birth.ts`) refuses a birth date
  inside the last year with `BIRTH_TOO_RECENT`, so profile creation, profile editing, the free
  snapshot and the share card all refuse it — a direct API call cannot skip it. The legacy
  self-service intake app applies the same rule (`tools/client_intake_app.py`).
- **Why one year.** The year pillar, the twelve-stage (12운성) cycle and the first major-luck
  chapter are **annual** structures. A chart for a baby is not a chart with fewer conclusions — the
  vocabulary is empty, and the engine would print a confident day master, a career arc and a
  relationship outlook for someone a few weeks old. The reading starts at one year old.
- **The form is a convenience, not the rule.** The date field carries the same cutoff, but the
  server is the rule of record, and the message the visitor sees comes from the same module
  (`lib/birth-date.ts`).

A short, honest footer disclaimer is required on the site: entertainment/self-reflection framing,
not prediction of outcomes, no professional advice. It is not a legal shield — it is the same honesty
the product claims as its differentiator.

---

## 7. Breach response

1. **Contain.** Rotate the affected credential; revoke sessions by rotating
   `NEON_AUTH_COOKIE_SECRET` if sessions may be compromised.
2. **Assess.** Which tables were reachable? Birth data is the trigger for notification; a leaked
   `Order` amount is not.
3. **Notify.** GDPR: supervisory authority within 72 hours if the risk to data subjects is not
   negligible, and the affected users without undue delay. DPDP: the Data Protection Board and the
   affected Data Principals. Write the notification in plain language: what data, when, what we did,
   what they should do.
4. **Record.** An `AuditLog` entry, plus a written incident note in the repo (not in this file, and
   not with any user data).
5. **Fix.** Whatever let it happen, plus a test that would have caught it.

The notification decision hinges on birth data. If a breach only exposed order amounts and timestamps,
document the reasoning for *not* notifying — the reasoning is what an auditor asks for.

---

## 8. Compliance checklist before launch

- [ ] Privacy policy published: what we collect, why, lawful basis, retention periods, **what survives
      account deletion**, sub-processors listed by name
- [x] Sub-processors named: Neon (database + auth), Cloudflare (storage + DNS + **Turnstile bot
      protection**), Vercel (hosting + **Web Analytics** — cookieless, same-origin, so no cookie
      banner is required), Resend (transactional email), **Hostinger (mailbox — holds
      customer correspondence)**, Dodo Payments (payments, MoR), Google (OAuth)
      — listed on the published privacy page, and kept honest by `vendor-naming.test.ts`. The page had
      been naming **Lemon Squeezy** as the merchant of record long after Dodo Payments replaced it
- [ ] **Third-party browser requests are accounted for.** Loading a font or a script from someone
      else's CDN hands them the visitor's IP and User-Agent, which is a transfer of personal data that
      the policy has to cover. Today there are exactly two. **Google Fonts** — `layout.tsx` pulls
      Cormorant Garamond, IBM Plex Mono and Inter from `fonts.googleapis.com` — is avoidable: self-host
      the three faces under `public/fonts/` and the request disappears. **Cloudflare Turnstile** is the
      other, and it is load-bearing for abuse control, so it stays and is named above.
- [ ] Terms of Service published
- [ ] **Refund policy published** — required by Dodo Payments, and a consumer-law expectation
- [x] **Real, monitored addresses**: `hello@cosmicsaju.com` (general + where replies land) and
      `privacy@cosmicsaju.com` (data-protection requests only). Records published in Cloudflare and
      **receiving verified** (`delivered`); ⚠️ the three **DKIM CNAMEs** are still to add — see
      [07](07-services-and-integrations.md) §Mailbox records
- [x] Consent checkbox records a `ConsentRecord` before any birth data is collected — **enforced
      server-side** at the profile write, not merely displayed (`403 CONSENT_REQUIRED`)
- [ ] Birth-data consent wording reviewed specifically for the sensitive category
- [ ] Deletion path works end to end and is cancellable
- [ ] Retention sweep and the 3-day anonymous-sample purge are running
- [ ] Disclaimer on the site and in the report footer
- [ ] Testimonials are real and permissioned, or the section is removed
- [ ] Delivery-time promise in the copy matches the review workflow
- [ ] Data-subject-access procedure documented (manual is acceptable at first, with a stated window)
- [ ] Breach-response steps known by the person who will have to run them
- [ ] Backups rehearsed once

## 9. Notes for a lawyer, not for me

This page is an engineering plan, not legal advice, and it is written by the team that built the
system. Before public launch, the privacy policy, terms, refund policy, and the birth-data consent
wording should be reviewed by someone qualified in (a) GDPR/UK GDPR for EU/UK visitors and (b) the
DPDP Act for Indian residents. The two areas most likely to need professional input are the
sensitive-data consent wording and the retention schedule for financial records that sit with the
Merchant of Record.
