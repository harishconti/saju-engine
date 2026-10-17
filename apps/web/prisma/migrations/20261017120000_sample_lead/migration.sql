-- An address left by an anonymous visitor asking for their free snapshot by email.
--
-- Additive and nullable-only, so it cannot break anything already running: a new table, no column on
-- an existing one. `marketingOptIn` defaults to FALSE at the database level as well as in the form, so
-- an omitted field can never be read as consent.
--
-- Deliberately NOT a `ConsentRecord`: that table is keyed to `userId` and records the lawful basis for
-- holding birth data. An anonymous sample visitor has no `User` row and we keep no birth data for them
-- — they gave us an address. See docs/webapp/02-data-model.md and 10-privacy-and-compliance.md.
CREATE TABLE "SampleLead" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "marketingOptIn" BOOLEAN NOT NULL DEFAULT false,
    "policyVersion" TEXT NOT NULL,
    "source" TEXT NOT NULL DEFAULT 'sample',
    "ip" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "SampleLead_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "SampleLead_email_key" ON "SampleLead"("email");

CREATE INDEX "SampleLead_createdAt_idx" ON "SampleLead"("createdAt");
