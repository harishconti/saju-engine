import { handle, json } from "@/lib/api";
import { requireUser } from "@/lib/auth";
import { rateLimit, WINDOW } from "@/lib/ratelimit";
import { kickOwnerJobs } from "@/lib/fulfilment";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

/**
 * Nudge the caller's own queued jobs.
 *
 * Why this exists: the scheduled dispatcher runs every 15 minutes (`.github/workflows/sla-sweep.yml`;
 * Vercel Hobby cannot run a per-minute cron, and the daily Vercel cron is only a fallback), so a job
 * queued behind a failed webhook dispatch can wait a quarter of an hour. This is the recovery path a
 * client can trigger themselves. Scoped to the caller's orders and rate limited — it can never touch
 * another user's work.
 *
 * AU-12 (2026-10-26 audit): a check that renders nothing is NOT a success. The old answer was
 * `200 { ok: true, message: "Checked N reports." }` even when the job had just failed and gone back
 * on the queue, so the customer saw "Checked" and waited. The failure now travels as a non-2xx with
 * an `error` the dashboard already renders as an alert.
 */
export const POST = handle(async () => {
  const user = await requireUser();
  await rateLimit(`kick:${user.id}`, 20, WINDOW.hour);

  const result = await kickOwnerJobs(user.id, 2);

  if (result.failed > 0) {
    return json(
      {
        ok: false,
        code: "CHECK_FAILED",
        processed: result.processed,
        generated: result.generated,
        failed: result.failed,
        error:
          "We couldn't rebuild the report just now. Your order is safe and still queued — please try again in a few minutes.",
      },
      503,
    );
  }

  return json({
    ok: true,
    processed: result.processed,
    generated: result.generated,
    failed: 0,
    message:
      result.processed === 0
        ? "Nothing was waiting."
        : `Checked ${result.processed} report${result.processed === 1 ? "" : "s"}.`,
  });
});
