import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient | undefined };

/**
 * Prisma singleton.
 *
 * Prisma's defaults (2s to acquire a connection, 5s per interactive transaction) are too tight
 * for serverless Postgres: a Neon cold start plus a multi-statement write can exceed them and
 * abort with P2028. Widen both.
 *
 * Uses the POOLED connection string (DATABASE_URL). Migrations use DIRECT_URL — see
 * prisma/schema.prisma and docs/webapp/02-data-model.md.
 */
export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["warn", "error"] : ["error"],
    transactionOptions: { maxWait: 10_000, timeout: 15_000 },
  });

if (process.env.NODE_ENV !== "production") {
  globalForPrisma.prisma = prisma;
}
