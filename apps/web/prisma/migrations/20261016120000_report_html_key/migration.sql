-- The web document: the reading the client opens, one self-contained HTML file rendered from
-- the same markdown as the PDF. Nullable, so existing rows (and compatibility readings, which
-- have no web mode yet) keep working: the PDF is the fallback.
ALTER TABLE "Report" ADD COLUMN     "htmlKey" TEXT,
ADD COLUMN     "htmlBytes" INTEGER;
