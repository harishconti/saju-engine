import { handle, json } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";
import { listRecoverableOrders } from "@/lib/admin-recovery";

export const dynamic = "force-dynamic";

/**
 * Read-only recovery list for AU-02 (2026-10-26 audit): PAID orders with no Report and no live
 * job — the set the October outage left unrecoverable from the console. The filtering (including
 * the exclusion for reports the customer deleted) lives in `lib/admin-recovery.ts` so the review
 * queue renders the same answer this endpoint returns.
 */
export const GET = handle(async () => {
  await requireAdmin();
  return json({ orders: await listRecoverableOrders() });
});
