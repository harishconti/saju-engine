-- AlterTable
ALTER TABLE "Job" ADD COLUMN     "reportId" TEXT;

-- CreateIndex
CREATE INDEX "Job_reportId_idx" ON "Job"("reportId");

-- AddForeignKey
ALTER TABLE "Job" ADD CONSTRAINT "Job_reportId_fkey" FOREIGN KEY ("reportId") REFERENCES "Report"("id") ON DELETE CASCADE ON UPDATE CASCADE;

