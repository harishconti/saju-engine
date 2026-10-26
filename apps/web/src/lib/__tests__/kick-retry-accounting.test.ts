import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "@/lib/api";

/**
 * "Check for updates" must not spend the job's retries.
 *
 * AU-12 (2026-10-26 audit): the dashboard button runs the same claim the dispatcher runs, and that
 * claim incremented `attempts`. During an outage every click hit a fast 5xx, so two clicks could push
 * a paid job to `maxAttempts` and fail it for good — the customer's own attempt to recover the order
 * killed it.
 *
 * The behaviour locked here, on the real `kickOwnerJobs` path with the real queue helpers over a fake
 * database:
 *  - a transient refusal leaves `attempts` exactly where it was, and the job queued;
 *  - a successful check still renders and succeeds;
 *  - a permanent refusal (bad birth data) still records the attempt — it really did run.
 */

const mocks = vi.hoisted(() => ({
  prisma: {
    job: { findMany: vi.fn(), updateMany: vi.fn(), update: vi.fn(), findUnique: vi.fn(), count: vi.fn() },
    order: { findUnique: vi.fn() },
    report: { findFirst: vi.fn() },
    $transaction: vi.fn(),
  },
  callEngine: vi.fn(),
  headObject: vi.fn(),
  presignPutUrl: vi.fn(async (key: string) => `https://r2.test/${key}`),
}));

vi.mock("@/lib/prisma", () => ({ prisma: mocks.prisma }));
vi.mock("@/lib/r2", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../r2")>()),
  isR2Configured: () => true,
  presignPutUrl: mocks.presignPutUrl,
  headObject: mocks.headObject,
}));
vi.mock("@/lib/engine", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../engine")>()),
  callEngine: mocks.callEngine,
}));
vi.mock("@/lib/email", () => ({ deliverReport: vi.fn(), deliverAudioReadyEmail: vi.fn() }));
vi.mock("@/lib/owner-alert", () => ({
  notifyOwnerNewReview: vi.fn().mockResolvedValue(true),
  notifyOwnerEngineFailure: vi.fn().mockResolvedValue(true),
}));
vi.mock("@/lib/audit", () => ({ writeAudit: vi.fn() }));

const { kickOwnerJobs } = await import("../fulfilment");

const PROFILE = {
  id: "prof_1",
  fullName: "Priya",
  gender: "F" as const,
  birthDate: new Date("1992-03-20T00:00:00.000Z"),
  birthTime: "14:00",
  timeKnown: true,
  timezone: "Asia/Seoul",
  utcOffset: 9,
  city: "Seoul",
  latitude: 37.5665,
  longitude: 126.978,
};

const ORDER = {
  id: "order_1",
  userId: "user_1",
  kind: "SINGLE" as const,
  tier: "deep",
  profileAId: "prof_1",
  profileBId: null,
  profileA: PROFILE,
  profileB: null,
  user: { deletedAt: null },
  favorableOverrideA: null,
  favorableOverrideB: null,
};

interface FakeJob {
  id: string;
  orderId: string;
  reportId: string | null;
  kind: "GENERATE";
  state: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";
  attempts: number;
  maxAttempts: number;
  leaseUntil: Date | null;
  worker: string | null;
  lastError: string | null;
  startedAt: Date | null;
  finishedAt: Date | null;
  createdAt: Date;
  payload: null;
}

let job: FakeJob;

function freshJob(): FakeJob {
  return {
    id: "job_1",
    orderId: "order_1",
    reportId: null,
    kind: "GENERATE",
    state: "QUEUED",
    attempts: 0,
    maxAttempts: 3,
    leaseUntil: null,
    worker: null,
    lastError: null,
    startedAt: null,
    finishedAt: null,
    createdAt: new Date("2026-10-26T06:36:00.000Z"),
    payload: null,
  };
}

/** Apply a Prisma-shaped update to the fake row, including the counter operations. */
function applyJobData(data: Record<string, unknown>): void {
  if (typeof data.state === "string") job.state = data.state as FakeJob["state"];
  const attempts = data.attempts as { increment?: number; decrement?: number } | number | undefined;
  if (typeof attempts === "number") job.attempts = attempts;
  else if (attempts && typeof attempts === "object") {
    if (typeof attempts.increment === "number") job.attempts += attempts.increment;
    if (typeof attempts.decrement === "number") job.attempts -= attempts.decrement;
  }
  if ("lastError" in data) job.lastError = (data.lastError as string | null) ?? null;
  if ("finishedAt" in data) job.finishedAt = (data.finishedAt as Date | null) ?? null;
  if ("leaseUntil" in data) job.leaseUntil = (data.leaseUntil as Date | null) ?? null;
  if ("worker" in data) job.worker = (data.worker as string | null) ?? null;
}

/** The transaction body touches the account state, report/delivery, and the job update (the real fake). */
const tx = {
  // Must-fix 2b: the report write re-reads `deletedAt`; this account is live.
  user: { findUnique: vi.fn(async () => ({ deletedAt: null })) },
  report: { create: vi.fn(), updateMany: vi.fn() },
  delivery: { create: vi.fn() },
  job: { update: vi.fn() },
};

beforeEach(() => {
  vi.clearAllMocks();
  job = freshJob();

  mocks.prisma.job.findMany.mockImplementation(async () =>
    job.state === "QUEUED" ? [{ id: job.id }] : [],
  );
  mocks.prisma.job.updateMany.mockImplementation(
    async ({ where, data }: { where: { id: string; state?: string }; data: Record<string, unknown> }) => {
      if (where.id !== job.id || (where.state !== undefined && job.state !== where.state)) {
        return { count: 0 };
      }
      applyJobData(data);
      return { count: 1 };
    },
  );
  mocks.prisma.job.update.mockImplementation(
    async ({ data }: { data: Record<string, unknown> }) => {
      applyJobData(data);
      return { ...job };
    },
  );
  mocks.prisma.job.findUnique.mockImplementation(async () => ({ ...job }));
  mocks.prisma.job.count.mockResolvedValue(0);
  mocks.prisma.order.findUnique.mockResolvedValue(ORDER);
  mocks.prisma.report.findFirst.mockResolvedValue(null);
  tx.job.update.mockImplementation(async ({ data }: { data: Record<string, unknown> }) => {
    applyJobData(data);
    return { ...job };
  });
  mocks.prisma.$transaction.mockImplementation(async (fn: (t: typeof tx) => Promise<unknown>) => fn(tx));

  mocks.headObject.mockResolvedValue(null);
});

describe("a customer's check does not spend the job's retries", () => {
  it("leaves attempts at zero across two checks that hit a fast 5xx", async () => {
    mocks.callEngine.mockRejectedValue(
      new ApiError(503, "UPLOAD_HOSTS_UNCONFIGURED", "no allowlist", { engineStatus: 503 }),
    );

    const first = await kickOwnerJobs("user_1", 2);
    const second = await kickOwnerJobs("user_1", 2);

    expect(job.attempts).toBe(0);
    expect(job.state).toBe("QUEUED");
    // …and the customer is told the check failed rather than shown a silent success.
    expect(first).toMatchObject({ processed: 1, generated: 0, failed: 1 });
    expect(second).toMatchObject({ processed: 1, generated: 0, failed: 1 });
  });

  it("still processes the job when the check succeeds", async () => {
    mocks.callEngine.mockResolvedValue({
      sha256: "a".repeat(64),
      bytes: 4096,
      engineVersion: "0.2.0",
      htmlBytes: null,
    });
    mocks.headObject.mockResolvedValue({ size: 4096 });

    const result = await kickOwnerJobs("user_1", 2);

    expect(result).toMatchObject({ processed: 1, generated: 1, failed: 0 });
    expect(job.state).toBe("SUCCEEDED");
  });

  it("records the attempt when the refusal is permanent", async () => {
    // Bad birth data will not improve on the next click, so this one really did run.
    mocks.callEngine.mockRejectedValue(
      new ApiError(422, "INVALID_BIRTH_DATE", "bad birth date", { engineStatus: 422 }),
    );

    const result = await kickOwnerJobs("user_1", 2);

    expect(result).toMatchObject({ generated: 0, failed: 1 });
    expect(job.state).toBe("FAILED");
    expect(job.attempts).toBe(1);
  });

  it("does not count a job another dispatcher claimed first", async () => {
    // The job is picked up between our query and our claim: nothing ran here, so nothing failed.
    mocks.prisma.job.updateMany.mockResolvedValue({ count: 0 });

    const result = await kickOwnerJobs("user_1", 2);

    expect(result).toMatchObject({ processed: 1, generated: 0, failed: 0 });
  });
});
