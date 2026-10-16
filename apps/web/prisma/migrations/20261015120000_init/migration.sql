-- CreateEnum
CREATE TYPE "Role" AS ENUM ('USER', 'ADMIN');

-- CreateEnum
CREATE TYPE "Gender" AS ENUM ('M', 'F');

-- CreateEnum
CREATE TYPE "OrderKind" AS ENUM ('SINGLE', 'COMPAT');

-- CreateEnum
CREATE TYPE "OrderStatus" AS ENUM ('AWAITING_PAYMENT', 'PAID', 'CANCELLED', 'REFUNDED');

-- CreateEnum
CREATE TYPE "JobKind" AS ENUM ('GENERATE', 'REGENERATE');

-- CreateEnum
CREATE TYPE "JobState" AS ENUM ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED');

-- CreateEnum
CREATE TYPE "ReportStatus" AS ENUM ('DRAFT_READY', 'IN_REVIEW', 'APPROVED', 'DELIVERED', 'SUPERSEDED', 'FAILED');

-- CreateEnum
CREATE TYPE "Channel" AS ENUM ('EMAIL', 'PROFILE');

-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "role" "Role" NOT NULL DEFAULT 'USER',
    "locale" TEXT NOT NULL DEFAULT 'en',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Profile" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "fullName" TEXT NOT NULL,
    "gender" "Gender" NOT NULL,
    "birthDate" DATE NOT NULL,
    "birthTime" TEXT NOT NULL,
    "timezone" TEXT,
    "utcOffset" DECIMAL(4,2),
    "city" TEXT NOT NULL,
    "country" TEXT NOT NULL,
    "latitude" DECIMAL(9,6),
    "longitude" DECIMAL(9,6),
    "timeKnown" BOOLEAN NOT NULL DEFAULT true,
    "isDefault" BOOLEAN NOT NULL DEFAULT false,
    "chartJson" JSONB,
    "chartComputedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Profile_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Order" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "kind" "OrderKind" NOT NULL,
    "tier" TEXT NOT NULL,
    "status" "OrderStatus" NOT NULL DEFAULT 'AWAITING_PAYMENT',
    "priceCents" INTEGER NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'USD',
    "provider" TEXT,
    "providerOrderId" TEXT,
    "providerCheckoutId" TEXT,
    "paidAt" TIMESTAMP(3),
    "profileAId" TEXT NOT NULL,
    "profileBId" TEXT,
    "favorableOverrideA" TEXT,
    "favorableOverrideB" TEXT,
    "idempotencyKey" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Order_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Job" (
    "id" TEXT NOT NULL,
    "orderId" TEXT NOT NULL,
    "kind" "JobKind" NOT NULL DEFAULT 'GENERATE',
    "state" "JobState" NOT NULL DEFAULT 'QUEUED',
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "maxAttempts" INTEGER NOT NULL DEFAULT 3,
    "leaseUntil" TIMESTAMP(3),
    "worker" TEXT,
    "payload" JSONB,
    "lastError" TEXT,
    "startedAt" TIMESTAMP(3),
    "finishedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Job_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Report" (
    "id" TEXT NOT NULL,
    "orderId" TEXT,
    "userId" TEXT NOT NULL,
    "kind" "OrderKind" NOT NULL,
    "tier" TEXT NOT NULL,
    "version" INTEGER NOT NULL DEFAULT 1,
    "status" "ReportStatus" NOT NULL DEFAULT 'DRAFT_READY',
    "profileAId" TEXT NOT NULL,
    "profileBId" TEXT,
    "pdfKey" TEXT,
    "mdKey" TEXT,
    "sha256" TEXT,
    "bytes" INTEGER,
    "pageCount" INTEGER,
    "chartHash" TEXT,
    "engineVersion" TEXT,
    "reviewedBy" TEXT,
    "reviewedAt" TIMESTAMP(3),
    "deliveredAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Report_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Delivery" (
    "id" TEXT NOT NULL,
    "reportId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "channel" "Channel" NOT NULL,
    "to" TEXT,
    "provider" TEXT,
    "providerMessageId" TEXT,
    "status" TEXT NOT NULL,
    "error" TEXT,
    "sentAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Delivery_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "WebhookEvent" (
    "id" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "eventId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "payload" JSONB NOT NULL,
    "receivedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "processedAt" TIMESTAMP(3),
    "error" TEXT,

    CONSTRAINT "WebhookEvent_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "AuditLog" (
    "id" TEXT NOT NULL,
    "entity" TEXT NOT NULL,
    "entityId" TEXT NOT NULL,
    "action" TEXT NOT NULL,
    "actorId" TEXT,
    "before" JSONB,
    "after" JSONB,
    "ip" TEXT,
    "ua" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditLog_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RateLimit" (
    "bucket" TEXT NOT NULL,
    "windowStart" TIMESTAMP(3) NOT NULL,
    "count" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "RateLimit_pkey" PRIMARY KEY ("bucket","windowStart")
);

-- CreateTable
CREATE TABLE "IdempotencyKey" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "key" TEXT NOT NULL,
    "requestHash" TEXT NOT NULL,
    "response" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "IdempotencyKey_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ObjectDeletion" (
    "id" TEXT NOT NULL,
    "fileKey" TEXT NOT NULL,
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "lastError" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ObjectDeletion_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ConsentRecord" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "policyVersion" TEXT NOT NULL,
    "purposes" JSONB NOT NULL,
    "grantedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "withdrawnAt" TIMESTAMP(3),
    "ip" TEXT,
    "ua" TEXT,

    CONSTRAINT "ConsentRecord_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeletionRequest" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'pending',
    "reason" TEXT,
    "requestedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "scheduledFor" TIMESTAMP(3) NOT NULL,
    "completedAt" TIMESTAMP(3),

    CONSTRAINT "DeletionRequest_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE INDEX "User_deletedAt_idx" ON "User"("deletedAt");

-- CreateIndex
CREATE INDEX "Profile_userId_deletedAt_idx" ON "Profile"("userId", "deletedAt");

-- CreateIndex
CREATE UNIQUE INDEX "Order_providerOrderId_key" ON "Order"("providerOrderId");

-- CreateIndex
CREATE INDEX "Order_userId_createdAt_idx" ON "Order"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "Order_status_createdAt_idx" ON "Order"("status", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "Order_userId_idempotencyKey_key" ON "Order"("userId", "idempotencyKey");

-- CreateIndex
CREATE INDEX "Job_state_createdAt_idx" ON "Job"("state", "createdAt");

-- CreateIndex
CREATE INDEX "Job_leaseUntil_idx" ON "Job"("leaseUntil");

-- CreateIndex
CREATE INDEX "Report_userId_createdAt_idx" ON "Report"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "Report_status_createdAt_idx" ON "Report"("status", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "Report_orderId_version_key" ON "Report"("orderId", "version");

-- CreateIndex
CREATE INDEX "Delivery_reportId_idx" ON "Delivery"("reportId");

-- CreateIndex
CREATE INDEX "Delivery_userId_createdAt_idx" ON "Delivery"("userId", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "WebhookEvent_provider_eventId_key" ON "WebhookEvent"("provider", "eventId");

-- CreateIndex
CREATE INDEX "AuditLog_entity_entityId_idx" ON "AuditLog"("entity", "entityId");

-- CreateIndex
CREATE INDEX "AuditLog_actorId_createdAt_idx" ON "AuditLog"("actorId", "createdAt");

-- CreateIndex
CREATE INDEX "AuditLog_createdAt_idx" ON "AuditLog"("createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "IdempotencyKey_userId_key_key" ON "IdempotencyKey"("userId", "key");

-- CreateIndex
CREATE INDEX "ObjectDeletion_createdAt_idx" ON "ObjectDeletion"("createdAt");

-- CreateIndex
CREATE INDEX "ConsentRecord_userId_grantedAt_idx" ON "ConsentRecord"("userId", "grantedAt");

-- CreateIndex
CREATE INDEX "DeletionRequest_status_scheduledFor_idx" ON "DeletionRequest"("status", "scheduledFor");

-- AddForeignKey
ALTER TABLE "Profile" ADD CONSTRAINT "Profile_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Order" ADD CONSTRAINT "Order_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Order" ADD CONSTRAINT "Order_profileAId_fkey" FOREIGN KEY ("profileAId") REFERENCES "Profile"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Order" ADD CONSTRAINT "Order_profileBId_fkey" FOREIGN KEY ("profileBId") REFERENCES "Profile"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Job" ADD CONSTRAINT "Job_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "Order"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Report" ADD CONSTRAINT "Report_orderId_fkey" FOREIGN KEY ("orderId") REFERENCES "Order"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Report" ADD CONSTRAINT "Report_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Report" ADD CONSTRAINT "Report_reviewedBy_fkey" FOREIGN KEY ("reviewedBy") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Report" ADD CONSTRAINT "Report_profileAId_fkey" FOREIGN KEY ("profileAId") REFERENCES "Profile"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Report" ADD CONSTRAINT "Report_profileBId_fkey" FOREIGN KEY ("profileBId") REFERENCES "Profile"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Delivery" ADD CONSTRAINT "Delivery_reportId_fkey" FOREIGN KEY ("reportId") REFERENCES "Report"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Delivery" ADD CONSTRAINT "Delivery_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "AuditLog" ADD CONSTRAINT "AuditLog_actorId_fkey" FOREIGN KEY ("actorId") REFERENCES "User"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IdempotencyKey" ADD CONSTRAINT "IdempotencyKey_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ConsentRecord" ADD CONSTRAINT "ConsentRecord_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeletionRequest" ADD CONSTRAINT "DeletionRequest_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────────────────────────────────────────
-- Hand-written constraints (Prisma does not emit these from the schema).
-- Normative: docs/webapp/02-data-model.md §"Invariants"
-- ─────────────────────────────────────────────────────────────────────────────

-- Invariant 1: kind = COMPAT  <=>  profileBId IS NOT NULL
ALTER TABLE "Order"
  ADD CONSTRAINT "order_compat_has_two_profiles"
  CHECK ((("kind" = 'COMPAT') = ("profileBId" IS NOT NULL)));

-- Invariant 2: a compatibility reading needs two DIFFERENT people
ALTER TABLE "Order"
  ADD CONSTRAINT "order_profiles_distinct"
  CHECK ("profileBId" IS NULL OR "profileBId" <> "profileAId");

-- Invariant 3: tier must be valid for the kind
ALTER TABLE "Order"
  ADD CONSTRAINT "order_tier_matches_kind"
  CHECK (
    ("kind" = 'SINGLE' AND "tier" IN ('sample', 'essential', 'deep'))
    OR
    ("kind" = 'COMPAT' AND "tier" IN ('basic', 'deep'))
  );

-- Money is never negative
ALTER TABLE "Order"
  ADD CONSTRAINT "order_price_non_negative"
  CHECK ("priceCents" >= 0);

-- Reports: same kind/profileB rule as the order they came from
ALTER TABLE "Report"
  ADD CONSTRAINT "report_compat_has_two_profiles"
  CHECK ((("kind" = 'COMPAT') = ("profileBId" IS NOT NULL)));

ALTER TABLE "Report"
  ADD CONSTRAINT "report_profiles_distinct"
  CHECK ("profileBId" IS NULL OR "profileBId" <> "profileAId");

ALTER TABLE "Report"
  ADD CONSTRAINT "report_version_positive"
  CHECK ("version" >= 1);

-- A delivered report must carry the artefact metadata
ALTER TABLE "Report"
  ADD CONSTRAINT "report_delivered_has_pdf"
  CHECK ("status" <> 'DELIVERED' OR "pdfKey" IS NOT NULL);

-- Invariant 8: RUNNING implies a lease
ALTER TABLE "Job"
  ADD CONSTRAINT "job_running_has_lease"
  CHECK ("state" <> 'RUNNING' OR "leaseUntil" IS NOT NULL);

ALTER TABLE "Job"
  ADD CONSTRAINT "job_attempts_non_negative"
  CHECK ("attempts" >= 0 AND "maxAttempts" >= 1);

-- Delivery status vocabulary
ALTER TABLE "Delivery"
  ADD CONSTRAINT "delivery_status_check"
  CHECK ("status" IN ('queued', 'sent', 'bounced', 'complained', 'failed'));

ALTER TABLE "Delivery"
  ADD CONSTRAINT "delivery_channel_check"
  CHECK ("channel" IN ('EMAIL', 'PROFILE'));

-- Only one default profile per user
CREATE UNIQUE INDEX "profile_one_default_per_user"
  ON "Profile" ("userId")
  WHERE "isDefault" = true AND "deletedAt" IS NULL;

-- Rate limit windows must not go backwards in meaning
ALTER TABLE "RateLimit"
  ADD CONSTRAINT "rate_limit_count_non_negative"
  CHECK ("count" >= 0);
