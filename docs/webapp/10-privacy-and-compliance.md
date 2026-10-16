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
| Report PDF + source markdown | Cloudflare R2 (private) | Personal data (derived) | Contract (the product itself) |
| Payment records | Dodo Payments (MoR) holds card data; we hold an order id, amount, status | Personal + financial | Contract, legal obligation (tax) |
| Audit log (actor, action, ip, ua) | Neon (`AuditLog`) | Personal data | Legitimate interest (security, dispute resolution) |
| Consent records | Neon (`ConsentRecord`) | Personal data | Legal obligation (proving consent) |
| Delivery log (email address, provider message id) | Neon (`Delivery`) | Personal data | Contract |
| **Correspondence** — support mail, refund requests, DSARs | **Hostinger email** (`hello@`, with the `privacy@` alias) | Personal data | Legitimate interest / legal obligation (answering the request). Lives in the mail provider's mailbox, **not** in our database |
| Anonymous sample objects | R2 `reports/anonymous/…` | Personal data until unlinked | Consent; **swept after 7 days** |
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

- Consent is recorded **before** any birth data is submitted, not after.
- Withdrawing consent is a first-class action in `/dashboard/account`, not an email request.
  Withdrawing `service` stops processing and starts the deletion path.
- `ConsentRecord` is **append-only**. Never update a consent row; insert a new one and set
  `withdrawnAt` on the old. The history is the evidence.
- The exact policy version is stored, so "they consented to *that* text" is provable.

⚠️ **The birth-data consent wording matters more than the rest of the policy combined.** It must say,
plainly, what is collected, what it is used for, and that it is stored to produce and re-deliver the
report. A generic "we value your privacy" paragraph does not meet the bar for this category of data.

---

## 3. Retention

| Data | Retention | Mechanism |
|---|---|---|
| Anonymous samples (R2 + any row) | 7 days | Cleanup cron |
| Profiles / birth data | Until the user deletes it, or 24 months of inactivity | Warning at 23 months, sweep at 24 |
| Reports + PDFs | Until deletion is requested | Deleted together with the `Report` row |
| Account after a deletion request | Deleted, with `Order`/`Report` rows anonymised | 30-day grace, then cleanup cron |
| `Job`, `WebhookEvent` | 90 days | Cleanup cron |
| `RateLimit` windows | 1 hour | Cleanup cron |
| `IdempotencyKey` | 7 days | Cleanup cron |
| `Delivery` | 24 months | Kept for support; contains an email address |
| Mail in the mailbox | Kept while useful for support — **not a system of record** | Manual. The `Reply-To` routes client replies to `hello@`, so this is where a reply lands; nothing in the app depends on it |
| `AuditLog` | 24 months | Kept for dispute resolution |
| `ConsentRecord` | As long as the account, plus 24 months after deletion | Proof of consent |
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
- [ ] Sub-processors named: Neon (database + auth), Cloudflare (storage + DNS), Vercel (hosting), Resend
      (transactional email), **Hostinger (mailbox — holds customer correspondence)**, Dodo Payments
      (payments, MoR), Google (OAuth)
- [ ] Terms of Service published
- [ ] **Refund policy published** — required by Dodo Payments, and a consumer-law expectation
- [x] **Real, monitored addresses**: `hello@cosmicsaju.com` (general + where replies land) and
      `privacy@cosmicsaju.com` (data-protection requests only). Records published in Cloudflare and
      **receiving verified** (`delivered`); ⚠️ the three **DKIM CNAMEs** are still to add — see
      [07](07-services-and-integrations.md) §Mailbox records
- [ ] Consent checkbox records a `ConsentRecord` before any birth data is collected
- [ ] Birth-data consent wording reviewed specifically for the sensitive category
- [ ] Deletion path works end to end and is cancellable
- [ ] Retention sweep and 7-day anonymous-sample purge are running
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
