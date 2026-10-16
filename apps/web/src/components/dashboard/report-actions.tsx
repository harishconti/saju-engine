"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button } from "@/components/ui";

/** Client-side destructive action. No window.confirm — an inline confirm keeps focus and a11y sane. */
export function DeleteReportButton({ reportId }: { reportId: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/reports/${reportId}`, { method: "DELETE" });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Couldn't delete that. Try again.");
        return;
      }
      router.push("/dashboard/reports");
      router.refresh();
    } catch {
      setError("Couldn't delete that. Try again.");
    } finally {
      setBusy(false);
    }
  }

  if (!confirming) {
    return (
      <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
        Delete this reading
      </Button>
    );
  }

  return (
    <div className="space-y-3 rounded-md border border-destructive/40 bg-destructive/5 p-3">
      <p className="text-sm">
        Delete this reading and its PDF? This can&apos;t be undone. If you paid for it, the record of your
        purchase stays on file.
      </p>
      {error ? <Alert tone="danger">{error}</Alert> : null}
      <div className="flex gap-2">
        <Button variant="danger" size="sm" loading={busy} onClick={onDelete}>
          Yes, delete it
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setConfirming(false)} disabled={busy}>
          Keep it
        </Button>
      </div>
    </div>
  );
}
