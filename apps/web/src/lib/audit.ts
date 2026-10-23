import type { Prisma } from "@prisma/client";
import { prisma } from "./prisma";

/**
 * Audit trail. Must be written with the SAME transaction client as the mutation it describes,
 * or the log and the change can diverge.
 *
 * Never store birth data, names, emails, tokens, or signed URLs in `before`/`after`.
 */

export type AuditEntity =
  | "order"
  | "report"
  | "profile"
  | "user"
  | "consent"
  | "deletion"
  | "webhook"
  | "job";

export type AuditAction =
  | "create"
  | "update"
  | "delete"
  | "approve"
  | "reject"
  | "regenerate"
  | "deliver"
  /** The 10-hour queue deadline released a reading without a human reading it. */
  | "sla_deliver"
  | "override"
  | "role_change"
  | "paid"
  | "refund";

export interface AuditEntry {
  entity: AuditEntity;
  entityId: string;
  action: AuditAction;
  /** null = system (cron, webhook) */
  actorId?: string | null;
  before?: unknown;
  after?: unknown;
  ip?: string | null;
  ua?: string | null;
}

function toJson(value: unknown): Prisma.InputJsonValue | undefined {
  if (value === undefined) return undefined;
  if (value === null) return undefined;
  return JSON.parse(JSON.stringify(value)) as Prisma.InputJsonValue;
}

export async function writeAudit(tx: Prisma.TransactionClient, entry: AuditEntry): Promise<void> {
  await tx.auditLog.create({
    data: {
      entity: entry.entity,
      entityId: entry.entityId,
      action: entry.action,
      actorId: entry.actorId ?? null,
      before: toJson(entry.before),
      after: toJson(entry.after),
      ip: entry.ip ?? null,
      ua: entry.ua ?? null,
    },
  });
}

/** Convenience for the common "one mutation, one audit row" case outside an explicit txn. */
export async function audit(entry: AuditEntry): Promise<void> {
  await prisma.$transaction((tx) => writeAudit(tx, entry));
}

/** Recent activity for a single record — used by the admin console. */
export async function auditTrail(entity: AuditEntity, entityId: string, take = 20) {
  return prisma.auditLog.findMany({
    where: { entity, entityId },
    orderBy: { createdAt: "desc" },
    take,
    select: { id: true, action: true, actorId: true, createdAt: true, after: true },
  });
}
