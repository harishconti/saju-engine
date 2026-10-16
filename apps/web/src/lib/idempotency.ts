import { createHash } from "node:crypto";
import type { Prisma } from "@prisma/client";
import { prisma } from "./prisma";
import { ApiError } from "./api";

/**
 * Request-level idempotency for creates the client may retry (order creation, sample save).
 *
 * Uses a Postgres advisory transaction lock keyed on the user + key so two concurrent retries
 * cannot both run the mutation, then replays the stored response.
 *
 * The client supplies the key via the `Idempotency-Key` header (or an `idempotencyKey` body field).
 */

export interface IdempotencyOptions {
  userId: string;
  key?: string | null;
  body?: unknown;
}

export async function withIdempotency<T>(
  opts: IdempotencyOptions,
  run: (tx: Prisma.TransactionClient) => Promise<T>,
): Promise<{ data: T; replayed: boolean }> {
  const key = opts.key?.trim();
  if (!key) {
    return { data: await prisma.$transaction((tx) => run(tx)), replayed: false };
  }

  const requestHash = createHash("sha256")
    .update(JSON.stringify(opts.body ?? null))
    .digest("hex");
  const lockKey = `idem:${opts.userId}:${key}`;

  return prisma.$transaction(async (tx) => {
    await tx.$executeRaw`SELECT pg_advisory_xact_lock(hashtext(${lockKey}))`;

    const existing = await tx.idempotencyKey.findUnique({
      where: { userId_key: { userId: opts.userId, key } },
    });

    if (existing) {
      if (existing.requestHash !== requestHash) {
        throw ApiError.conflict(
          "This Idempotency-Key was already used with a different request body",
          "IDEMPOTENCY_MISMATCH",
        );
      }
      return { data: existing.response as T, replayed: true };
    }

    const data = await run(tx);

    await tx.idempotencyKey.create({
      data: {
        userId: opts.userId,
        key,
        requestHash,
        response: JSON.parse(JSON.stringify(data)) as Prisma.InputJsonValue,
      },
    });

    return { data, replayed: false };
  });
}

/** Purge keys older than 7 days (daily cleanup cron). */
export async function purgeOldIdempotencyKeys(): Promise<number> {
  const cutoff = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  const res = await prisma.idempotencyKey.deleteMany({ where: { createdAt: { lt: cutoff } } });
  return res.count;
}
