import { handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { kickOwnerJobs } from "@/lib/fulfilment";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

/**
 * Nudge the caller's own queued jobs.
 *
 * Why this exists: Vercel Hobby rejects a per-minute cron at deploy time, so the webhook is the primary
 * generation trigger (via `after()`) and this is the recovery path a client can trigger themselves.
 * Scoped to the caller's orders and rate limited — it can never touch another user's work.
 */
export const POST = handle(async () => {
  const user = await requireUser();
  await rateLimit(`kick:${user.id}`, 20, WINDOW.hour);

  const result = await kickOwnerJobs(user.id, 2);
  return json({
    ok: true,
    processed: result.processed,
    generated: result.generated,
    message:
      result.processed === 0
        ? "Nothing was waiting."
        : `Checked ${result.processed} report${result.processed === 1 ? "" : "s"}.`,
  });
});
