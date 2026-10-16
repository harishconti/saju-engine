/** Presentation helpers. No business logic, no I/O. */

export function formatUSD(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
  }).format(cents / 100);
}

export function formatDate(value: Date | string | null | undefined): string {
  if (!value) return "—";
  const d = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric" }).format(d);
}

export function formatDateTime(value: Date | string | null | undefined): string {
  if (!value) return "—";
  const d = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(d.getTime())) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(d);
}

/** Coarse age, for operational urgency ("oldest item in the review queue"). */
export function timeAgo(value: Date | string | null | undefined): string {
  if (!value) return "—";
  const d = typeof value === "string" ? new Date(value) : value;
  const seconds = Math.floor((Date.now() - d.getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const REPORT_STATUS_LABEL: Record<string, string> = {
  DRAFT_READY: "In review",
  IN_REVIEW: "In review",
  APPROVED: "Approved",
  DELIVERED: "Delivered",
  SUPERSEDED: "Superseded",
  FAILED: "Failed",
};

export const ORDER_STATUS_LABEL: Record<string, string> = {
  AWAITING_PAYMENT: "Awaiting payment",
  PAID: "Paid",
  CANCELLED: "Cancelled",
  REFUNDED: "Refunded",
};

export const AUDIO_STATUS_LABEL: Record<string, string> = {
  NONE: "Not included",
  PENDING: "Being prepared",
  PROCESSING: "Being prepared",
  READY: "Ready",
  FAILED: "Unavailable",
};

/**
 * The audio is produced *after* approval, so this state is normal rather than a fault —
 * the wording has to make waiting feel like progress, not breakage.
 */
export const AUDIO_STATUS_HELP: Record<string, string> = {
  NONE: "This reading does not include an audio summary.",
  PENDING:
    "Your reading is already delivered and readable below. The audio summary is being recorded from it — you'll get an email when it's ready, and you don't need to wait here.",
  PROCESSING: "Recording your audio summary now. You'll get an email when it's ready.",
  READY: "Read aloud from the same reading below, so it says nothing the written version does not.",
  FAILED:
    "We couldn't record the audio summary. You have the full written reading, and we've been notified — reply to your order email if you'd like us to try again.",
};

/** The client-facing explanation for a report that exists but is not delivered yet. */
export const REPORT_STATUS_HELP: Record<string, string> = {
  DRAFT_READY:
    "We're checking your reading before sending it. Every paid report is reviewed by a human first — usually within a day.",
  IN_REVIEW: "A reviewer is with your reading now. Usually within a day.",
  APPROVED: "Approved — sending it to you now.",
  DELIVERED: "Delivered. Download it any time.",
  SUPERSEDED: "A newer version of this reading exists.",
  FAILED: "Something went wrong producing this reading. We're on it, and you haven't been double-charged.",
};

/** Display the four pillars as a compact string. */
export function formatPillars(pillars: string[] | null | undefined): string {
  if (!pillars || pillars.length === 0) return "—";
  return pillars.join(" · ");
}
