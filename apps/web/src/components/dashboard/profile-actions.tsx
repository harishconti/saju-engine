"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button } from "@/components/ui";

export function ProfileActions({ profileId, isDefault }: { profileId: string; isDefault: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);

  async function makePrimary() {
    setBusy("primary");
    setError(null);
    try {
      const res = await fetch(`/api/profiles/${profileId}`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ isDefault: true }),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Couldn't update that.");
        return;
      }
      router.refresh();
    } finally {
      setBusy(null);
    }
  }

  async function remove() {
    setBusy("delete");
    setError(null);
    try {
      const res = await fetch(`/api/profiles/${profileId}`, { method: "DELETE" });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Couldn't remove that profile.");
        return;
      }
      router.refresh();
    } finally {
      setBusy(null);
      setConfirming(false);
    }
  }

  return (
    <div className="space-y-2">
      {error ? <Alert tone="danger">{error}</Alert> : null}

      {confirming ? (
        <div className="space-y-2 rounded-md border border-destructive/40 bg-destructive/5 p-3">
          <p className="text-sm">
            Remove this person? Their birth details are deleted. Readings already delivered are kept.
          </p>
          <div className="flex gap-2">
            <Button variant="danger" size="sm" loading={busy === "delete"} onClick={remove}>
              Remove
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
              Keep
            </Button>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {!isDefault ? (
            <Button variant="ghost" size="sm" loading={busy === "primary"} onClick={makePrimary}>
              Make primary
            </Button>
          ) : (
            <span className="inline-flex items-center px-3 text-xs text-muted-foreground">Primary profile</span>
          )}
          <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
            Remove
          </Button>
        </div>
      )}
    </div>
  );
}
