-- The review-queue SLA (2026-10-23).
--
-- A reading that nobody has looked at used to wait in the queue forever. It now has a 10-hour
-- deadline: after that it is delivered anyway, and this table records THAT it was delivered
-- without a human reading it, rather than leaving the difference invisible.
--
--   reviewOutcome     HUMAN     — a person reviewed it (the normal path)
--                    SLA_AUTO  — the deadline passed and it was delivered unreviewed
--   slaApprovedAt     when the deadline released it (null for a human approval)
--   ownerAlertedAt    when the owner was told a reading is waiting (the alert dedup)
--   emailHeldForAudio true while the delivery EMAIL waits for the MP3, so an auto-delivered
--                    deep reading reaches the client as one message. The reading itself is
--                    already in their profile; only the mail waits.
--
-- Additive only — a new enum with a default and three new columns — so it can be applied
-- BEFORE the code that writes them. Nothing here can break a running deployment.
--
-- See docs/webapp/05-report-pipeline.md §"The 10-hour delivery rule" and
-- docs/webapp/09-operations.md.
CREATE TYPE "ReviewOutcome" AS ENUM ('HUMAN', 'SLA_AUTO');

-- AlterTable
ALTER TABLE "Report" ADD COLUMN     "emailHeldForAudio" BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN     "ownerAlertedAt" TIMESTAMP(3),
ADD COLUMN     "reviewOutcome" "ReviewOutcome" NOT NULL DEFAULT 'HUMAN',
ADD COLUMN     "slaApprovedAt" TIMESTAMP(3);
