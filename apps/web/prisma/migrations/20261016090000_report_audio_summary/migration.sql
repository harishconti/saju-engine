-- CreateEnum
CREATE TYPE "AudioStatus" AS ENUM ('NONE', 'PENDING', 'PROCESSING', 'READY', 'FAILED');

-- AlterEnum
ALTER TYPE "JobKind" ADD VALUE 'VOICE';

-- AlterTable
ALTER TABLE "Report" ADD COLUMN     "audioBytes" INTEGER,
ADD COLUMN     "audioError" TEXT,
ADD COLUMN     "audioKey" TEXT,
ADD COLUMN     "audioReadyAt" TIMESTAMP(3),
ADD COLUMN     "audioStatus" "AudioStatus" NOT NULL DEFAULT 'NONE',
ADD COLUMN     "enginePayload" JSONB,
ADD COLUMN     "script" TEXT;


-- Hand-written invariant: a READY audio must point at an object, mirroring
-- "report_delivered_has_pdf". Prevents a "ready" status with nothing to play.
ALTER TABLE "Report"
  ADD CONSTRAINT "report_audio_ready_has_key"
  CHECK ("audioStatus" <> 'READY' OR "audioKey" IS NOT NULL);
