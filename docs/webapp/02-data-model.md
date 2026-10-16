# 02 — Data model

Neon Postgres, accessed through Prisma. This page is the contract: if something here changes, a
migration and [03 — API spec](03-api-spec.md) change with it.

## Principles

1. **Birth data lives on `Profile`, once.** Orders reference profiles; they never duplicate birth
   data. This is what makes "the sample becomes your first profile" and "buy a compat reading
   against the partner you already saved" work.
2. **Reports are immutable once delivered.** A change creates a new `version`. History is never
   edited, so a client can always be shown exactly what they received.
3. **All operational state is a table.** Rate limits, idempotency keys, job leases, the R2 deletion
   queue, webhook events. No Redis, no broker.
4. **Nothing cascade-deletes a user's money trail.** `Order` and `Report` rows survive account
   deletion in anonymised form (see [10](10-privacy-and-compliance.md)).
5. **Enum-like columns get a database `CHECK` constraint** as well as a Prisma enum and a zod enum.
   Three places, deliberately.

## Schema

```prisma
// ─────────────────────────── Identity ───────────────────────────

model User {
  id            String    @id                       // = Neon Auth user id. No default.
  email         String    @unique
  name          String
  role          Role      @default(USER)
  locale        String    @default("en")
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  deletedAt     DateTime?                            // set on erasure: account anonymised, kept for records

  profiles       Profile[]
  orders         Order[]
  reports        Report[]
  deliveries     Delivery[]
  consents       ConsentRecord[]
  deletions      DeletionRequest[]
  auditLogs      AuditLog[]
  idempotency    IdempotencyKey[]
  reviewedReports Report[]  @relation("ReportReviewer")

  @@index([deletedAt])
}

enum Role {
  USER
  ADMIN
}

// ─────────────────────────── Birth data ───────────────────────────

model Profile {
  id         String    @id @default(cuid())
  userId     String
  label      String                                  // "Me", "Partner — Jisoo", "Mum"
  fullName   String
  gender     Gender                                  // required: 대운 direction depends on it
  birthDate  DateTime  @db.Date
  birthTime  String                                   // "HH:MM", 24h, local wall clock at the birthplace
  timezone   String?                                  // IANA, e.g. "Asia/Seoul". Preferred.
  utcOffset  Decimal?  @db.Decimal(4, 2)              // fallback when the zone is unknown; [-12, 14]
  city       String
  country    String
  latitude   Decimal?  @db.Decimal(9, 6)
  longitude  Decimal?  @db.Decimal(9, 6)              // drives solar-time correction
  timeKnown  Boolean   @default(true)                 // false => birthTime is a guess; surface a caveat
  isDefault  Boolean   @default(false)
  // Derived chart summary, computed ONCE when the profile is created (never at read time).
  // Lets the dashboard and the order flow show the four pillars for confirmation before payment —
  // a project ground rule (CLAUDE.md: no silent auto-calculated pillars).
  chartJson       Json?
  chartComputedAt DateTime?
  createdAt  DateTime  @default(now())
  updatedAt  DateTime  @updatedAt
  deletedAt  DateTime?

  user       User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  ordersAsA  Order[]   @relation("OrderProfileA")
  ordersAsB  Order[]   @relation("OrderProfileB")
  reportsAsA Report[]  @relation("ReportProfileA")
  reportsAsB Report[]  @relation("ReportProfileB")

  @@index([userId, deletedAt])
}

enum Gender {
  M
  F
}
```

> **Why `latitude`/`longitude` are stored rather than looked up.** The engine's `pillars.py` resolves
> a city name through Nominatim (geopy) at *runtime*. That is a network call with a usage policy and
> a latency budget, and it silently degrades to "standard time" on failure. Profiles resolve the
> coordinates **once**, at creation, from a bundled city table; the engine always receives explicit
> `longitude`, `timezone`, or `utcOffset`. This removes a vendor, a failure mode, and per-report
> latency in one move.

> **`gender` is required.** `render_single` raises `"PDF generation requires gender Female or Male so
> major-luck timing can be computed"` without it. The intake form must not allow it to be skipped.

> **`timeKnown`** exists because "I don't know my birth time" is common and the hour pillar is
> genuinely uncertain in that case. The engine already flags hour-boundary and solar-term-boundary
> knife-edges; this widens the caveat. Never silently default to 12:00 and present it as fact.

> **`chartJson` / `chartComputedAt`** exist so the dashboard and the order flow can show the derived
> four pillars without calling the engine on every page load, and so the order flow can satisfy the
> ground rule that the user sees the chart **before** paying. It is populated once, when the profile is
> created or when anything chart-affecting changes, by `POST {ENGINE_URL}/chart` (see
> [05 — Report pipeline](05-report-pipeline.md) §2). A profile is fully usable with `chartJson = null`
> — the UI says the chart has not been derived yet rather than failing.

```prisma
// ─────────────────────────── Commerce ───────────────────────────

model Order {
  id               String      @id @default(cuid())
  userId           String
  kind             OrderKind                        // SINGLE | COMPAT
  tier             String                            // engine tier: sample|essential|deep|basic|deep-compat — see the tier map
  status           OrderStatus @default(AWAITING_PAYMENT)

  priceCents       Int                               // resolved server-side. Never from the client.
  currency         String      @default("USD")

  provider         String?                           // "dodo" | "manual"
  providerOrderId  String?     @unique
  providerCheckoutId String?
  paidAt           DateTime?

  profileAId       String
  profileBId       String?                           // required when kind = COMPAT
  favorableOverrideA String?                         // reader-argued 용신; set by a reviewer, not the client
  favorableOverrideB String?

  idempotencyKey   String?
  createdAt        DateTime    @default(now())
  updatedAt        DateTime    @updatedAt

  user      User      @relation(fields: [userId], references: [id], onDelete: Cascade)
  profileA  Profile   @relation("OrderProfileA", fields: [profileAId], references: [id])
  profileB  Profile?  @relation("OrderProfileB", fields: [profileBId], references: [id])
  jobs      Job[]
  reports   Report[]

  @@index([userId, createdAt])
  @@index([status, createdAt])
  @@unique([userId, idempotencyKey])
}

enum OrderKind {
  SINGLE
  COMPAT
}

enum OrderStatus {
  AWAITING_PAYMENT
  PAID
  CANCELLED        // abandoned or refunded
  REFUNDED
}
```

```prisma
// ─────────────────────────── Work ───────────────────────────

model Job {
  id          String    @id @default(cuid())
  orderId     String
  kind        JobKind   @default(GENERATE)           // GENERATE | REGENERATE
  state       JobState  @default(QUEUED)

  attempts    Int       @default(0)
  maxAttempts Int       @default(3)
  leaseUntil  DateTime?                              // claimed until this instant
  worker      String?                                // dispatcher invocation id, for forensics

  payload     Json?                                  // the exact engine request (includes overrides)
  lastError   String?                                // exception class / code only. Never PII.
  startedAt   DateTime?
  finishedAt  DateTime?
  createdAt   DateTime  @default(now())

  order   Order    @relation(fields: [orderId], references: [id], onDelete: Cascade)
  reports Report[]

  @@index([state, createdAt])
  @@index([leaseUntil])
}

enum JobKind  { GENERATE REGENERATE }
enum JobState { QUEUED RUNNING SUCCEEDED FAILED }
```

```prisma
model Report {
  id        String       @id @default(cuid())
  orderId   String?                                   // null for a saved free sample
  userId    String
  kind      OrderKind
  tier      String
  version   Int          @default(1)                  // increments on regenerate

  status    ReportStatus @default(DRAFT_READY)

  profileAId String
  profileBId String?

  pdfKey    String?                                   // R2 object key
  mdKey     String?                                   // source markdown, kept for audit
  sha256    String?                                   // integrity check on download
  bytes     Int?
  pageCount Int?

  chartHash String?                                   // hash of (chart inputs + overrides). Skips no-op regens.
  engineVersion String?                               // contract version of the engine service

  reviewedBy  String?
  reviewedAt  DateTime?
  deliveredAt DateTime?
  createdAt   DateTime    @default(now())

  order     Order?   @relation(fields: [orderId], references: [id], onDelete: SetNull)
  user      User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  reviewer  User?    @relation("ReportReviewer", fields: [reviewedBy], references: [id])
  profileA  Profile  @relation("ReportProfileA", fields: [profileAId], references: [id])
  profileB  Profile? @relation("ReportProfileB", fields: [profileBId], references: [id])
  deliveries Delivery[]

  @@unique([orderId, version])
  @@index([userId, createdAt])
  @@index([status, createdAt])
}

enum ReportStatus {
  DRAFT_READY
  IN_REVIEW
  APPROVED
  DELIVERED
  SUPERSEDED
  FAILED
}
```

```prisma
model Delivery {
  id                String   @id @default(cuid())
  reportId          String
  userId            String
  channel           Channel                            // EMAIL | PROFILE
  to                String?
  provider          String?                            // "resend"
  providerMessageId String?
  status            String                             // queued|sent|bounced|complained|failed
  error             String?
  sentAt            DateTime?
  createdAt         DateTime @default(now())

  report Report @relation(fields: [reportId], references: [id], onDelete: Cascade)
  user   User   @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([reportId])
  @@index([userId, createdAt])
}

enum Channel { EMAIL PROFILE }
```

```prisma
// ─────────────────────────── Operations ───────────────────────────

model WebhookEvent {
  id          String    @id @default(cuid())
  provider    String                                   // "dodo" | "resend"
  eventId     String
  type        String
  payload     Json
  receivedAt  DateTime  @default(now())
  processedAt DateTime?
  error       String?

  @@unique([provider, eventId])                        // the idempotency guarantee that matters most
}

model AuditLog {
  id        String   @id @default(cuid())
  entity    String                                     // "order" | "report" | "profile" | "user" | "consent" | "deletion" | "webhook"
  entityId  String
  action    String                                     // "create" | "update" | "approve" | "regenerate" | "deliver" | "delete" | "role_change" | "override"
  actorId   String?                                    // null = system (cron, webhook)
  before    Json?
  after     Json?
  ip        String?
  ua        String?
  createdAt DateTime @default(now())

  actor User? @relation(fields: [actorId], references: [id])

  @@index([entity, entityId])
  @@index([actorId, createdAt])
  @@index([createdAt])
}

model RateLimit {
  bucket      String
  windowStart DateTime
  count       Int      @default(0)

  @@unique([bucket, windowStart])
}

model IdempotencyKey {
  id          String   @id @default(cuid())
  userId      String
  key         String
  requestHash String
  response    Json?
  createdAt   DateTime @default(now())

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@unique([userId, key])
}

model ObjectDeletion {
  id        String   @id @default(cuid())
  fileKey   String
  attempts  Int      @default(0)
  lastError String?
  createdAt DateTime @default(now())

  @@index([createdAt])
}
```

```prisma
// ─────────────────────────── Privacy ───────────────────────────

model ConsentRecord {
  id            String    @id @default(cuid())
  userId        String
  policyVersion String
  purposes      Json                                   // { "service": true, "service_messages": false }
  grantedAt     DateTime  @default(now())
  withdrawnAt   DateTime?
  ip            String?
  ua            String?

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([userId, grantedAt])
}

model DeletionRequest {
  id           String    @id @default(cuid())
  userId       String
  status       String    @default("pending")           // pending | cancelled | completed
  reason       String?
  requestedAt  DateTime  @default(now())
  scheduledFor DateTime                                 // now + grace period (30 days)
  completedAt  DateTime?

  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@index([status, scheduledFor])
}
```

## Tier map

One table, referenced from the API layer, the store config, and the engine contract. Keep it in one
module (`src/lib/tiers.ts`) so a price change is a one-file change.

| UI name | `kind` | `tier` (engine) | Price | Dodo Payments variant env |
|---|---|---|---|---|
| The Hook (sample) | `SINGLE` | `sample` | $0 | — (not a product) |
| Essential Report | `SINGLE` | `essential` | $19 | `DODO_PRODUCT_ESSENTIAL` |
| Deep Destiny Report | `SINGLE` | `deep` | $55 | `DODO_PRODUCT_DEEP` |
| Compatibility Snapshot | `COMPAT` | `basic` | $24 | `DODO_PRODUCT_COMPAT_BASIC` |
| Deep Compatibility | `COMPAT` | `deep` (compat) | $45 | `DODO_PRODUCT_COMPAT_DEEP` |

Engine legacy aliases accepted but never surfaced: `spark` → `essential`, `reading` → `deep`,
`fullmap` → `deep`. `companion` exists in the engine and is **not offered**.

## Invariants worth asserting in code

| # | Invariant | Where enforced |
|---|---|---|
| 1 | `kind = COMPAT` ⟺ `profileBId IS NOT NULL` | CHECK constraint + zod refine |
| 2 | `profileAId <> profileBId` for compat | CHECK constraint + zod refine |
| 3 | A profile can only be referenced by an order owned by its own user | Application check, inside the transaction |
| 4 | `priceCents` matches the tier map at order creation | Server-side resolution; the client's price is discarded |
| 5 | `tier` is one of the allowed values for `kind` | CHECK constraint |
| 6 | `Report.version` is unique per order | `@@unique([orderId, version])` |
| 7 | A `DELIVERED` report is never mutated | Application rule; the only legal transition out is to `SUPERSEDED` via a new version |
| 8 | `Job.state = RUNNING` implies `leaseUntil IS NOT NULL` | Application rule |
| 9 | `Delivery` exists only for an `APPROVED`+ report | Application rule; nothing emails a draft |
| 10 | `gender` is present on every profile used by an order | zod at intake + engine guard |

## Indexing notes

The indexes above are chosen for the three queries that will run constantly:

1. `Report WHERE userId = ? ORDER BY createdAt DESC` → `@@index([userId, createdAt])`
2. `Job WHERE state = 'QUEUED' ORDER BY createdAt LIMIT n` → `@@index([state, createdAt])`
3. `SELECT … WHERE state IN ('QUEUED','RUNNING') AND leaseUntil < now() FOR UPDATE SKIP LOCKED`
   → `@@index([leaseUntil])` in addition to the state index

Deliberately **not** indexed: `AuditLog.before/after` (JSON, never queried), `Report.mdKey` (fetched
by primary key).

## Migration discipline

```bash
# local, against the dev branch, using DIRECT_URL
npx prisma migrate dev --name <snake_case_description>

# production, after a backup
npx prisma migrate status
npx prisma migrate deploy
```

- Migrations always run through `DIRECT_URL`. A pooled connection cannot run DDL reliably.
- Hand-edit the generated SQL when you need a `CHECK` constraint or a partial index — Prisma does not
  emit those from the schema.
- Prisma's default transaction timings (2 s to acquire a connection, 5 s per interactive
  transaction) are too tight for serverless against Neon. Set
  `transactionOptions: { maxWait: 10_000, timeout: 15_000 }` on the client.
- **Never** touch the `neon_auth` schema. Neon Auth owns it.

## Retention

| Data | Retention | Mechanism |
|---|---|---|
| Anonymous sample PDFs | 7 days | Daily cleanup cron sweeps `reports/anonymous/…` |
| Anonymous sample rows | none (never persisted) | The sample flow is stateless until "save to profile" |
| Profile birth data | until the user deletes it, or 24 months after last activity | `Profile.deletedAt` + a periodic sweep |
| Reports + PDFs | until deletion is requested | `Report` rows + R2 objects, deleted together via `ObjectDeletion` |
| `Job`, `WebhookEvent` | 90 days | Daily cleanup cron |
| `RateLimit` windows | 1 hour | Daily cleanup cron |
| `IdempotencyKey` | 7 days | Daily cleanup cron |
| `AuditLog` | 24 months | Kept for support and dispute resolution |
| Deleted accounts | `Order`/`Report` rows anonymised, PII stripped | `DeletionRequest` → cleanup cron |

See [10 — Privacy and compliance](10-privacy-and-compliance.md) for the legal reasoning.
