"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Card, CardContent, EmptyState } from "@/components/ui";
import { formatDateTime } from "@/lib/format";

/**
 * AU-02 (2026-10-26 audit): paid orders the outage left with no reading and no job in flight.
 *
 * Before this table, recovering one meant manual SQL. The Retry button requeues the order's
 * existing generation job; the message says what the server did, success or refusal, because a
 * silently unchanged table is indistinguishable from a button that does nothing.
 */

export interface FailedOrderRow {
  orderId: string;
  kind: string;
  tier: string;
  tierName: string;
  paidAt: string | null;
  profileLabel: string;
  jobId: string | null;
  jobState: string | null;
  attempts: number | null;
  maxAttempts: number | null;
  lastError: string | null;
}

export function FailedOrdersTable({ rows }: { rows: FailedOrderRow[] }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function retry(orderId: string) {
    setBusy(orderId);
    setMessage(null);
    setError(null);
    try {
      const res = await fetch("/api/admin/jobs/retry", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ orderId }),
      });
      const body = (await res.json().catch(() => ({}))) as { message?: string; error?: string };
      if (!res.ok) {
        setError(body.error ?? "Couldn't retry that job.");
        return;
      }
      setMessage(body.message ?? "Job requeued.");
      router.refresh();
    } catch {
      setError("Couldn't retry that job. Check your connection and try again.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card>
      <CardContent className="py-4">
        <h2 className="pb-2 font-display text-xl">Failed orders</h2>
        <p className="pb-3 text-sm text-muted-foreground">
          Paid orders with no reading and no job queued or running. Retrying resets the attempt
          counter and puts the existing generation job back on the queue. An order the customer
          deleted themselves is not listed.
        </p>

        {message ? <Alert tone="success">{message}</Alert> : null}
        {error ? <Alert tone="danger">{error}</Alert> : null}

        {rows.length === 0 ? (
          <EmptyState
            title="No failed orders"
            description="Every paid order has a reading or a job in progress."
          />
        ) : (
          <div
            className="overflow-x-auto"
            tabIndex={0}
            role="region"
            aria-label="Paid orders with no reading"
          >
            <table className="w-full min-w-[760px] border-collapse text-sm">
              <caption className="sr-only">
                Paid orders with no reading and no queued or running job
              </caption>
              <thead>
                <tr className="border-b border-border text-left">
                  <th scope="col" className="py-2 pr-4 font-medium">Order</th>
                  <th scope="col" className="px-3 py-2 font-medium">Paid</th>
                  <th scope="col" className="px-3 py-2 font-medium">Last attempt</th>
                  <th scope="col" className="px-3 py-2 font-medium">
                    <span className="sr-only">Action</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.orderId} className="border-b border-border/60 align-top">
                    <td className="py-3 pr-4">
                      <p className="font-display">{row.tierName}</p>
                      <p className="text-xs text-muted-foreground">
                        {row.profileLabel} · {row.kind} · {row.tier}
                      </p>
                      <p className="font-mono text-[11px] text-muted-foreground">{row.orderId}</p>
                    </td>
                    <td className="px-3 py-3 text-muted-foreground">{formatDateTime(row.paidAt)}</td>
                    <td className="px-3 py-3">
                      <p className="text-destructive">{row.lastError ?? "No job"}</p>
                      {row.attempts != null ? (
                        <p className="text-xs text-muted-foreground">
                          attempts {row.attempts}/{row.maxAttempts ?? "?"}
                          {row.jobState ? ` · ${row.jobState}` : ""}
                        </p>
                      ) : null}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        loading={busy === row.orderId}
                        disabled={!row.jobId || busy !== null}
                        title={row.jobId ? undefined : "This order has no job to retry"}
                        onClick={() => retry(row.orderId)}
                      >
                        Retry
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
