"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert, Button, Field, Select, Textarea } from "@/components/ui";

const ELEMENTS = ["Wood", "Fire", "Earth", "Metal", "Water"] as const;

/**
 * The review console's decision panel.
 *
 * The 용신 override is the point of the whole console: the engine derives the favourable element
 * heuristically and records its provenance; a reader who has argued a different element can impose it,
 * and the entire report re-derives consistently. That turns a 30–90 minute review into a 5–10 minute one.
 */
export function ReviewConsole({
  reportId,
  kind,
  initialOverrideA,
  initialOverrideB,
  chartHash,
  audioStatus,
  audioError,
  audioPromised,
  reportDelivered,
}: {
  reportId: string;
  kind: "SINGLE" | "COMPAT";
  initialOverrideA: string | null;
  initialOverrideB: string | null;
  chartHash: string | null;
  audioStatus: string;
  audioError: string | null;
  audioPromised: boolean;
  reportDelivered: boolean;
}) {
  const router = useRouter();

  const [overrideA, setOverrideA] = useState(initialOverrideA ?? "");
  const [overrideB, setOverrideB] = useState(initialOverrideB ?? "");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [downloading, setDownloading] = useState(false);

  const changed =
    (overrideA || null) !== (initialOverrideA ?? null) || (overrideB || null) !== (initialOverrideB ?? null);

  async function post(path: string, body?: unknown, label = "action") {
    setBusy(label);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json", ...(body ? {} : {}) },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = (await res.json().catch(() => ({}))) as { error?: string; message?: string };
      if (!res.ok) {
        setError(data.error ?? "That didn't work.");
        return false;
      }
      setNotice(data.message ?? "Done.");
      router.refresh();
      return true;
    } catch {
      setError("Network problem. Try again.");
      return false;
    } finally {
      setBusy(null);
    }
  }

  async function saveOverride() {
    const ok = await post(
      `/api/admin/reports/${reportId}/override`,
      {
        favorableOverrideA: overrideA || null,
        favorableOverrideB: kind === "COMPAT" ? overrideB || null : null,
      },
      "override",
    );
    if (ok) setNotice("Override saved. Regenerate to apply it to the report.");
  }

  async function regenerate() {
    await post(`/api/admin/reports/${reportId}/regenerate`, undefined, "regenerate");
  }

  async function openPreview() {
    setDownloading(true);
    try {
      const res = await fetch(`/api/admin/reports/${reportId}/preview`);
      const data = (await res.json().catch(() => ({}))) as { url?: string; error?: string };
      if (!res.ok || !data.url) {
        setError(data.error ?? "No preview available yet.");
        return;
      }
      window.open(data.url, "_blank", "noopener");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-5">
      {error ? <Alert tone="danger">{error}</Alert> : null}
      {notice ? <Alert tone="success">{notice}</Alert> : null}

      <div className="space-y-3">
        <h3 className="font-display text-lg">Favourable element (용신)</h3>
        <p className="text-xs text-muted-foreground">
          Leave as-is to keep the engine&apos;s derived value. Set one to impose the reader&apos;s argued
          element — the report body and the year callout re-derive together.
        </p>

        <Field label="Person A" htmlFor="overrideA">
          <Select id="overrideA" value={overrideA} onChange={(e) => setOverrideA(e.target.value)}>
            <option value="">Use engine value</option>
            {ELEMENTS.map((el) => (
              <option key={el} value={el}>
                {el}
              </option>
            ))}
          </Select>
        </Field>

        {kind === "COMPAT" ? (
          <Field label="Person B" htmlFor="overrideB">
            <Select id="overrideB" value={overrideB} onChange={(e) => setOverrideB(e.target.value)}>
              <option value="">Use engine value</option>
              {ELEMENTS.map((el) => (
                <option key={el} value={el}>
                  {el}
                </option>
              ))}
            </Select>
          </Field>
        ) : null}

        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" loading={busy === "override"} onClick={saveOverride} disabled={!changed}>
            Save override
          </Button>
          <Button
            size="sm"
            loading={busy === "regenerate"}
            onClick={regenerate}
            title={chartHash ? `chart hash ${chartHash.slice(0, 12)}…` : undefined}
          >
            Regenerate
          </Button>
        </div>
      </div>

      <div className="space-y-2 border-t border-border pt-4">
        <h3 className="font-display text-lg">Artifact</h3>
        <Button size="sm" variant="outline" loading={downloading} onClick={openPreview}>
          Open PDF preview
        </Button>
        <p className="text-xs text-muted-foreground">
          Compliance QA (predictive language, master claims, sensitive advice, missing hedging) is run by
          hand for now: <code className="font-mono">python3 tools/qa_compliance.py &lt;report.md&gt;</code>
        </p>
      </div>

      {audioPromised ? (
        <div className="space-y-2 border-t border-border pt-4">
          <h3 className="font-display text-lg">Audio summary</h3>
          <p className="text-xs text-muted-foreground">
            Recorded from the approved text, so it says nothing the PDF does not. Queued
            automatically on approval; delivery never waits for it.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs">{audioStatus}</span>
            {audioError ? <span className="text-xs text-destructive">{audioError}</span> : null}
            <Button
              size="sm"
              variant="outline"
              loading={busy === "audio"}
              disabled={audioStatus === "READY" || audioStatus === "PROCESSING" || !reportDelivered}
              onClick={() => post(`/api/admin/reports/${reportId}/audio`, undefined, "audio")}
            >
              {audioStatus === "FAILED" ? "Retry audio" : "Prepare audio"}
            </Button>
          </div>
          {!reportDelivered ? (
            <p className="text-xs text-muted-foreground">Available once the reading is delivered.</p>
          ) : null}
        </div>
      ) : null}

      <div className="space-y-3 border-t border-border pt-4">
        <h3 className="font-display text-lg">Decision</h3>
        <Button
          size="md"
          loading={busy === "approve"}
          onClick={() => post(`/api/admin/reports/${reportId}/approve`, undefined, "approve")}
        >
          Approve and deliver
        </Button>
        <p className="text-xs text-muted-foreground">
          Approving emails the client and files the reading in their profile. A delivered report is
          immutable — any change creates a new version.
        </p>

        {rejecting ? (
          <div className="space-y-2 rounded-md border border-destructive/40 bg-destructive/5 p-3">
            <Field label="Why?" htmlFor="reason" hint="The client sees this.">
              <Textarea
                id="reason"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                maxLength={500}
                minLength={3}
                required
              />
            </Field>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="danger"
                loading={busy === "reject"}
                disabled={rejectReason.trim().length < 3}
                onClick={async () => {
                  const ok = await post(
                    `/api/admin/reports/${reportId}/reject`,
                    { reason: rejectReason.trim() },
                    "reject",
                  );
                  if (ok) setRejecting(false);
                }}
              >
                Reject and notify
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setRejecting(false)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button size="sm" variant="ghost" onClick={() => setRejecting(true)}>
            Reject this reading
          </Button>
        )}
      </div>
    </div>
  );
}
