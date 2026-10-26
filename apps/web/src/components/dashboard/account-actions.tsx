"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Field, Input } from "@/components/ui";

export function AccountNameForm({ initialName }: { initialName: string }) {
  const router = useRouter();
  const [name, setName] = useState(initialName);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch("/api/account", {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: name.trim() }),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Couldn't save that.");
        return;
      }
      setSaved(true);
      router.refresh();
    } catch {
      setError("Couldn't save that.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <Field label="Display name" htmlFor="name" hint="Used in your emails and on the dashboard.">
        <Input id="name" value={name} onChange={(e) => setName(e.target.value)} maxLength={80} required />
      </Field>
      {error ? <Alert tone="danger">{error}</Alert> : null}
      {saved ? <Alert tone="success">Saved.</Alert> : null}
      <Button type="submit" size="sm" loading={busy}>
        Save name
      </Button>
    </form>
  );
}

export function ConsentForm({
  initial,
  policyVersion,
}: {
  initial: { service: boolean; service_messages: boolean };
  policyVersion: string;
}) {
  const router = useRouter();
  const [purposes, setPurposes] = useState(initial);
  // What the server is known to hold. A failed save snaps back to this rather than to `initial`,
  // which is only the value at mount and would undo an earlier successful save (AU-19).
  const [confirmed, setConfirmed] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(next: typeof purposes) {
    setPurposes(next);
    setBusy(true);
    setSaved(false);
    setError(null);
    try {
      const res = await fetch("/api/account/consent", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ policyVersion, purposes: next }),
      });
      if (!res.ok) {
        // Never claim it saved. Consent is the lawful basis for birth data, so a failed write here
        // must be visible rather than silently absent.
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "We couldn't save that. Please try again.");
        setPurposes(confirmed); // snap the checkbox back to what is actually recorded
        return;
      }
      setConfirmed(next);
      setSaved(true);
      router.refresh();
    } catch {
      // AU-19: a dropped connection has no response to inspect. It must not leave the checkbox
      // toggled as though the consent were recorded.
      setError("We couldn't save that. Please try again.");
      setPurposes(confirmed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      <label className="flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          className="mt-0.5 h-4 w-4 accent-[var(--primary)]"
          checked={purposes.service}
          onChange={(e) => save({ ...purposes, service: e.target.checked })}
        />
        <span>
          <span className="font-medium text-foreground">Produce and deliver my readings</span>
          <span className="ml-1 text-muted-foreground">
            Required. Turning this off stops processing and starts the deletion path.
          </span>
        </span>
      </label>
      <label className="flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          className="mt-0.5 h-4 w-4 accent-[var(--primary)]"
          checked={purposes.service_messages}
          onChange={(e) => save({ ...purposes, service_messages: e.target.checked })}
        />
        <span>
          <span className="font-medium text-foreground">Occasional service emails</span>
          <span className="ml-1 text-muted-foreground">
            Product news and reminders. Off by default; nothing is sent without it.
          </span>
        </span>
      </label>
      {busy ? <p className="text-xs text-muted-foreground">Saving…</p> : null}
      {saved && !busy ? <p className="text-xs text-success">Preferences saved.</p> : null}
      {error && !busy ? <p className="text-xs text-destructive">{error}</p> : null}
    </div>
  );
}

export function DeletionPanel({
  scheduledFor,
  status,
}: {
  scheduledFor: string | null;
  status: string | null;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const active = status === "pending" && scheduledFor;

  async function request() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/account/deletion", { method: "POST" });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Couldn't schedule deletion.");
        return;
      }
      setConfirming(false);
      router.refresh();
    } catch {
      // AU-19: without this the panel looked as though the click had done something.
      setError("Couldn't schedule deletion.");
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/account/deletion", { method: "DELETE" });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? "Couldn't cancel deletion.");
        return;
      }
      router.refresh();
    } catch {
      setError("Couldn't cancel deletion.");
    } finally {
      setBusy(false);
    }
  }

  if (active) {
    return (
      <div className="space-y-3">
        <Alert tone="warning" title={`Deletion scheduled for ${scheduledFor}`}>
          Your account is deactivated and sign-in is disabled. Until that date you can cancel this and
          everything returns unchanged.
        </Alert>
        {error ? <Alert tone="danger">{error}</Alert> : null}
        <Button variant="outline" size="sm" loading={busy} onClick={cancel}>
          Cancel deletion
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        Deleting your account removes your birth details and reports, and gives you a 30-day window to
        change your mind. Purchase records are kept in anonymised form — we have to be able to account for
        the money.
      </p>
      {error ? <Alert tone="danger">{error}</Alert> : null}
      {confirming ? (
        <div className="space-y-2">
          <Button variant="danger" size="sm" loading={busy} onClick={request}>
            Yes, schedule deletion
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setConfirming(false)} disabled={busy}>
            Cancel
          </Button>
        </div>
      ) : (
        <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
          Delete my account
        </Button>
      )}
    </div>
  );
}
