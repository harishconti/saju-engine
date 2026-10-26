import { Prisma } from "@prisma/client";
import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-04 (2026-10-26 audit): erasure failed for anyone who had ever ordered.
 *
 * `processDueDeletions` deleted the R2 artefacts first and then tried to delete every profile. But
 * `Order_profileAId_fkey` is ON DELETE RESTRICT, so the transaction raised P2003 and rolled back —
 * after the artefacts were already gone. The request stayed `pending`, and every later cron run
 * threw on the same rows, blocking deletions queued behind them.
 *
 * Owner decision D2: keep order rows for accounting and scrub the profiles they reference. The
 * birth data still goes, and the R2 objects are removed only once the database has committed.
 */

const {
  prismaMock,
  txMock,
  r2Mock,
  ownerAlertMock,
  processDodoEvent,
  events,
  jobRows,
  ORIGINAL_JOB_PAYLOAD,
} = vi.hoisted(() => {
  const events: string[] = [];

  /**
   * A retained job row as `fulfilment.ts` really leaves it: `Job.payload` holds the whole engine
   * request — the profiles' names and full birth details included — and the row outlives the account
   * for up to 90 days (`queue.ts` purge window). The transaction mock below mutates this fixture, so
   * the assertion is about what a retained row actually contains, not about a call being made.
   *
   * `ownerId` is test-only: the real row has no user column, and the erasure reaches it through its
   * required `order` relation.
   */
  const ORIGINAL_JOB_PAYLOAD = {
    contractVersion: "1.0",
    kind: "single",
    tier: "deep",
    uploadUrl: "https://r2.test/reports/u1/o1/r1.pdf",
    mdUploadUrl: "https://r2.test/reports/u1/o1/r1.md",
    htmlUploadUrl: "https://r2.test/reports/u1/o1/r1.html",
    profileA: {
      fullName: "Priya Sharma",
      birthDate: "1992-03-20",
      birthTime: "14:00",
      timezone: "Asia/Seoul",
      utcOffset: 9,
      city: "Seoul",
      latitude: 37.5665,
      longitude: 126.978,
    },
  };
  const jobRows: Array<{ id: string; orderId: string; ownerId: string; payload: unknown }> = [
    { id: "job_1", orderId: "o1", ownerId: "u1", payload: structuredClone(ORIGINAL_JOB_PAYLOAD) },
    // Another account's retained job. The erasure must reach only the erased user's rows.
    { id: "job_2", orderId: "o2", ownerId: "u2", payload: structuredClone(ORIGINAL_JOB_PAYLOAD) },
  ];

  const txMock = {
    // AU-25: the Neon identity is deleted with raw statements on the transaction client. The
    // default probe answers "the relation exists"; tests override the once-queue to simulate a
    // missing relation or a failing delete.
    $queryRaw: vi.fn(
      async (_strings: TemplateStringsArray, relation: string): Promise<Array<{ name: string | null }>> => [
        { name: relation },
      ],
    ),
    $executeRaw: vi.fn(async (strings: TemplateStringsArray, ...values: unknown[]) => {
      const sql = strings.join("?");
      if (sql.includes('neon_auth."session"')) events.push("neon:session");
      else if (sql.includes('neon_auth."account"')) events.push("neon:account");
      else if (sql.includes('neon_auth."user"')) events.push("neon:user");
      events.push(`neon:id:${String(values[0])}`);
      return 1;
    }),
    report: {
      // Must-fix 2(a): the key capture moved inside the transaction, so this is the read whose
      // result the deletion and the queued keys both come from.
      findMany: vi.fn(),
      deleteMany: vi.fn(async () => {
        events.push("tx:report.deleteMany");
        return { count: 1 };
      }),
    },
    // Must-fix 1: `Job.payload` is nullable Json, so erasure writes `Prisma.DbNull` — a literal
    // `null` would store JSON null and `{}` an object, neither of which is a SQL NULL.
    job: {
      updateMany: vi.fn(async (args: { where: { order?: { userId?: string } }; data: { payload?: unknown } }) => {
        events.push("tx:job.updateMany");
        let count = 0;
        for (const row of jobRows) {
          if (row.ownerId !== args.where.order?.userId) continue;
          row.payload = args.data.payload === Prisma.DbNull ? null : args.data.payload;
          count++;
        }
        return { count };
      }),
    },
    profile: {
      updateMany: vi.fn(async () => {
        events.push("tx:profile.updateMany");
        return { count: 1 };
      }),
      deleteMany: vi.fn(async () => {
        events.push("tx:profile.deleteMany");
        return { count: 1 };
      }),
    },
    delivery: {
      deleteMany: vi.fn(async () => {
        events.push("tx:delivery.deleteMany");
        return { count: 0 };
      }),
    },
    // The captured keys are also queued here, inside the transaction, so a crash between the
    // commit and the post-commit R2 loop cannot lose them.
    objectDeletion: {
      createMany: vi.fn(async (args: { data: Array<{ fileKey: string }> }) => {
        events.push("tx:objectDeletion.createMany");
        return { count: args.data.length };
      }),
    },
    user: {
      update: vi.fn(async () => {
        events.push("tx:user.update");
        return {};
      }),
    },
    consentRecord: {
      updateMany: vi.fn(async () => {
        events.push("tx:consentRecord.updateMany");
        return { count: 0 };
      }),
    },
    auditLog: {
      create: vi.fn(async () => {
        events.push("tx:auditLog.create");
        return {};
      }),
    },
  };

  const prismaMock = {
    deletionRequest: {
      findMany: vi.fn(),
      update: vi.fn(async (_args: { where: { id: string }; data: Record<string, unknown> }) => {
        events.push("deletion:completed");
        return {};
      }),
      // AU-25: the terminal transition is guarded on `status: "pending"` so two overlapping cleanup
      // runs cannot both alert. A count of 0 means the other run already settled this request.
      updateMany: vi.fn(async (_args: { where: Record<string, unknown>; data: Record<string, unknown> }) => {
        events.push("deletion:terminal");
        return { count: 1 };
      }),
    },
    report: { findMany: vi.fn(), deleteMany: vi.fn() },
    profile: { findMany: vi.fn(), updateMany: vi.fn(), deleteMany: vi.fn() },
    order: { findMany: vi.fn() },
    user: { update: vi.fn() },
    consentRecord: { updateMany: vi.fn() },
    auditLog: {
      create: vi.fn(async (_args: { data: Record<string, unknown> }) => {
        events.push("audit:identity");
        return {};
      }),
      // AU-25 retry cap: the sweep counts how many times this request already failed to delete
      // its identity, so a permanent fault cannot retry forever.
      count: vi.fn(async (_args: Record<string, unknown>) => 0),
    },
    webhookEvent: { findMany: vi.fn(), update: vi.fn() },
    $transaction: vi.fn(),
  };

  const r2Mock = {
    isR2Configured: vi.fn(() => true),
    drainObjectDeletions: vi.fn(),
    listObjectsByPrefix: vi.fn(),
    deleteObjects: vi.fn(),
    deleteObjectOrQueue: vi.fn(async (key: string) => {
      events.push(`r2:${key}`);
    }),
  };

  const processDodoEvent = vi.fn();

  // AU-25: a terminal identity failure must reach a human. The alert is a seam, so the test asserts
  // it was called rather than what the mail said.
  const ownerAlertMock = { notifyOwnerIdentityDeletionFailed: vi.fn(async () => true) };

  return {
    prismaMock,
    txMock,
    r2Mock,
    ownerAlertMock,
    processDodoEvent,
    events,
    jobRows,
    ORIGINAL_JOB_PAYLOAD,
  };
});

vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/r2", () => r2Mock);
vi.mock("@/lib/owner-alert", () => ownerAlertMock);
vi.mock("@/lib/dodo-webhook", () => ({ processDodoEvent }));

const { processDueDeletions } = await import("../cleanup");

const NOW = new Date("2026-10-26T12:00:00.000Z");

const KEYS = {
  pdfKey: "reports/u1/o1/r1.pdf",
  mdKey: "reports/u1/o1/r1.md",
  audioKey: "reports/u1/o1/r1.mp3",
  htmlKey: "reports/u1/o1/r1.html",
};

function deletionRequest(id: string, userId: string) {
  return { id, userId };
}

beforeEach(() => {
  vi.clearAllMocks();
  events.length = 0;

  // The retained job fixture is mutated by the transaction mock, so each test starts from the
  // pre-erasure state — the state a real database is in before any erasure runs.
  for (const row of jobRows) row.payload = structuredClone(ORIGINAL_JOB_PAYLOAD);

  // A commit is what makes the post-commit R2 deletion safe, so record when it happens.
  prismaMock.$transaction.mockImplementation(async (fn: (tx: typeof txMock) => Promise<unknown>) => {
    const result = await fn(txMock);
    events.push("commit");
    return result;
  });

  prismaMock.deletionRequest.findMany.mockResolvedValue([deletionRequest("dr1", "u1")]);
  prismaMock.deletionRequest.updateMany.mockResolvedValue({ count: 1 });
  prismaMock.auditLog.count.mockResolvedValue(0);
  // The report read inside the erasure transaction, and the post-commit re-sweep. Both default to
  // "nothing there", like a real user with no reports.
  txMock.report.findMany.mockResolvedValue([]);
  prismaMock.report.findMany.mockResolvedValue([]);
  prismaMock.profile.findMany.mockResolvedValue([]);
  prismaMock.order.findMany.mockResolvedValue([]);
});

describe("processDueDeletions — erasure with an order (AU-04, D2)", () => {
  beforeEach(() => {
    txMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.order.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);
  });

  it("completes instead of hitting the Order RESTRICT constraint", async () => {
    await expect(processDueDeletions(NOW)).resolves.toBe(1);
    expect(prismaMock.deletionRequest.update).toHaveBeenCalledWith({
      where: { id: "dr1" },
      data: { status: "completed", completedAt: NOW },
    });
  });

  it("keeps the order and scrubs the profile it references", async () => {
    await processDueDeletions(NOW);

    expect(txMock.profile.deleteMany).toHaveBeenCalledWith({
      where: { userId: "u1", id: { notIn: ["p1"] } },
    });
    expect(txMock.profile.updateMany).toHaveBeenCalledWith({
      where: { userId: "u1", id: { in: ["p1"] } },
      data: expect.objectContaining({
        label: "Deleted profile",
        fullName: "Deleted profile",
        birthDate: new Date(0),
        birthTime: "00:00",
        timezone: null,
        utcOffset: null,
        city: "Deleted",
        country: "Deleted",
        latitude: null,
        longitude: null,
        timeKnown: false,
        chartJson: Prisma.DbNull,
        chartComputedAt: null,
        deletedAt: NOW,
      }),
    });
    // The order itself is never touched.
    expect(prismaMock.order.findMany).toHaveBeenCalledWith({
      where: { OR: [{ profileAId: { in: ["p1"] } }, { profileBId: { in: ["p1"] } }] },
      select: { profileAId: true, profileBId: true },
    });
  });

  it("deletes report artefacts only after the transaction commits", async () => {
    await processDueDeletions(NOW);

    const commitAt = events.indexOf("commit");
    expect(commitAt).toBeGreaterThan(-1);
    for (const key of Object.values(KEYS)) {
      const deletedAt = events.indexOf(`r2:${key}`);
      expect(deletedAt, `${key} was never deleted`).toBeGreaterThan(-1);
      expect(deletedAt, `${key} was deleted before the commit`).toBeGreaterThan(commitAt);
    }
    expect(r2Mock.deleteObjectOrQueue).toHaveBeenCalledTimes(4);
  });

  it("deletes deliveries and anonymises the account", async () => {
    await processDueDeletions(NOW);

    // The reports are deleted by the ids just read, never by `userId`: at READ COMMITTED a
    // `where: { userId }` delete would take a fresh snapshot and could remove a report whose keys
    // were never captured. A row that commits after the read survives to the re-sweep instead.
    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["r1"] } } });
    expect(txMock.delivery.deleteMany).toHaveBeenCalledWith({ where: { userId: "u1" } });
    expect(txMock.user.update).toHaveBeenCalledWith({
      where: { id: "u1" },
      data: {
        name: "Deleted user",
        email: "deleted+u1@deleted.invalid",
        deletedAt: NOW,
      },
    });
    expect(txMock.consentRecord.updateMany).toHaveBeenCalledWith({
      where: { userId: "u1", withdrawnAt: null },
      data: { withdrawnAt: NOW },
    });
  });
});

describe("processDueDeletions — erasure with no order", () => {
  it("deletes the profile as before", async () => {
    txMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    expect(txMock.profile.updateMany).not.toHaveBeenCalled();
    expect(txMock.profile.deleteMany).toHaveBeenCalledWith({
      where: { userId: "u1", id: { notIn: [] } },
    });
    const commitAt = events.indexOf("commit");
    expect(events.indexOf(`r2:${KEYS.pdfKey}`)).toBeGreaterThan(commitAt);
  });
});

describe("processDueDeletions — Neon identity deletion (AU-25)", () => {
  beforeEach(() => {
    txMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.order.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);
  });

  it("deletes sessions, accounts then the user in one transaction, before marking the request completed", async () => {
    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    const session = events.indexOf("neon:session");
    const account = events.indexOf("neon:account");
    const user = events.indexOf("neon:user");
    const completed = events.indexOf("deletion:completed");

    expect(session).toBeGreaterThanOrEqual(0);
    expect(account).toBeGreaterThan(session);
    expect(user).toBeGreaterThan(account);
    expect(completed).toBeGreaterThan(user);
    // Every statement went through the transaction client, and the three probes ran first.
    expect(txMock.$executeRaw).toHaveBeenCalledTimes(3);
    expect(txMock.$queryRaw).toHaveBeenCalledTimes(3);
  });

  it("uses the pre-anonymisation User.id, never the rewritten email", async () => {
    await processDueDeletions(NOW);

    for (const call of txMock.$executeRaw.mock.calls) {
      expect(call).toContain("u1");
      expect(call.join(" ")).not.toContain("deleted+u1@deleted.invalid");
    }
  });

  it("leaves the request pending when the raw delete throws, after the local erasure committed", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    txMock.$executeRaw.mockRejectedValueOnce(new Error("permission denied"));

    await expect(processDueDeletions(NOW)).resolves.toBe(0);

    // The local half committed: the account is anonymised and the request can be retried safely.
    expect(txMock.user.update).toHaveBeenCalled();
    expect(events.indexOf("commit")).toBeGreaterThanOrEqual(0);
    // The identity half did not: no completion, and the failure is recorded for an operator.
    expect(prismaMock.deletionRequest.update).not.toHaveBeenCalled();
    expect(prismaMock.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          entity: "deletion",
          action: "update",
          after: expect.objectContaining({ neonIdentity: "failed" }),
        }),
      }),
    );
    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });

  it("marks a missing relation terminal instead of retrying it forever, and alerts the owner", async () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    txMock.$queryRaw
      .mockResolvedValueOnce([{ name: 'neon_auth."session"' }])
      .mockResolvedValueOnce([{ name: null }])
      .mockResolvedValueOnce([{ name: 'neon_auth."user"' }]);

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    expect(txMock.$executeRaw).not.toHaveBeenCalled();
    // Terminal, not retryable: a schema that no longer matches cannot be fixed by trying again, and
    // leaving it `pending` would take one of the ten slots on every run for ever.
    expect(prismaMock.deletionRequest.updateMany).toHaveBeenCalledWith({
      where: { id: "dr1", status: "pending" },
      data: { status: "completed_with_identity_error", completedAt: NOW },
    });
    expect(prismaMock.deletionRequest.update).not.toHaveBeenCalled();
    expect(prismaMock.auditLog.create).toHaveBeenCalledWith(
      expect.objectContaining({
        data: expect.objectContaining({
          entity: "deletion",
          entityId: "dr1",
          after: expect.objectContaining({ neonIdentity: "missing-relation" }),
        }),
      }),
    );
    expect(ownerAlertMock.notifyOwnerIdentityDeletionFailed).toHaveBeenCalledWith(
      expect.objectContaining({ requestId: "dr1", outcome: "missing-relation" }),
    );
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it("caps transient identity failures, then marks the request terminal and alerts the owner", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    txMock.$executeRaw.mockRejectedValueOnce(new Error("permission denied"));
    // Two earlier attempts are already on record; this run is the third and last.
    prismaMock.auditLog.count.mockResolvedValue(2);

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    // The counter is scoped to this request and to this failure, so one request's history cannot
    // exhaust another's retries.
    expect(prismaMock.auditLog.count).toHaveBeenCalledWith({
      where: {
        entity: "deletion",
        entityId: "dr1",
        action: "update",
        after: { path: ["neonIdentity"], equals: "failed" },
      },
    });
    expect(prismaMock.deletionRequest.updateMany).toHaveBeenCalledWith({
      where: { id: "dr1", status: "pending" },
      data: { status: "completed_with_identity_error", completedAt: NOW },
    });
    expect(ownerAlertMock.notifyOwnerIdentityDeletionFailed).toHaveBeenCalledWith(
      expect.objectContaining({ requestId: "dr1", outcome: "failed", attempts: 3 }),
    );
    error.mockRestore();
  });

  it("keeps retrying a transient identity failure below the cap", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    txMock.$executeRaw.mockRejectedValueOnce(new Error("connection reset"));
    prismaMock.auditLog.count.mockResolvedValue(1);

    await expect(processDueDeletions(NOW)).resolves.toBe(0);

    expect(prismaMock.deletionRequest.update).not.toHaveBeenCalled();
    expect(prismaMock.deletionRequest.updateMany).not.toHaveBeenCalled();
    expect(ownerAlertMock.notifyOwnerIdentityDeletionFailed).not.toHaveBeenCalled();
    error.mockRestore();
  });

  it("does not alert twice when two cleanup runs settle the same request", async () => {
    // The terminal transition is conditional on the row still being `pending`. The second run's
    // guarded update changes nothing, so only the run that actually settled the request alerts.
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    txMock.$queryRaw
      .mockResolvedValueOnce([{ name: null }])
      .mockResolvedValueOnce([{ name: null }])
      .mockResolvedValueOnce([{ name: null }]);
    prismaMock.deletionRequest.updateMany.mockResolvedValue({ count: 0 });

    await processDueDeletions(NOW);

    expect(ownerAlertMock.notifyOwnerIdentityDeletionFailed).not.toHaveBeenCalled();
    warn.mockRestore();
  });

  it("takes pending requests oldest-first so one stuck request cannot starve the queue", async () => {
    await processDueDeletions(NOW);

    expect(prismaMock.deletionRequest.findMany).toHaveBeenCalledWith({
      where: { status: "pending", scheduledFor: { lte: NOW } },
      orderBy: { scheduledFor: "asc" },
      take: 10,
      select: { id: true, userId: true },
    });
  });
});

describe("processDueDeletions — the engine payload (must-fix 1)", () => {
  beforeEach(() => {
    txMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.order.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);
  });

  it("nulls Job.payload for every job the erased user still owns", async () => {
    await processDueDeletions(NOW);

    // Reached through the job's required order relation, and `Prisma.DbNull` — not `null`, which
    // would store a JSON null in a nullable Json column, and not `{}`, which would keep a row shape.
    expect(txMock.job.updateMany).toHaveBeenCalledWith({
      where: { order: { userId: "u1" } },
      data: { payload: Prisma.DbNull },
    });
  });

  it("leaves no retained row of the erased user carrying a birth field", async () => {
    await processDueDeletions(NOW);

    // Everything the erased user still has: order rows are retained for accounting, and this job
    // hangs off one. Serialising the retained rows is the privacy page's promise made testable.
    const erasedUserRows = jobRows.filter((row) => row.ownerId === "u1");
    expect(erasedUserRows.length).toBeGreaterThan(0);
    const retained = JSON.stringify(erasedUserRows);
    for (const field of [
      "fullName",
      "birthDate",
      "birthTime",
      "timezone",
      "utcOffset",
      "city",
      "latitude",
      "longitude",
    ]) {
      expect(retained, `a retained job row still carries ${field}`).not.toContain(field);
    }
    expect(erasedUserRows[0]!.payload).toBeNull();
  });

  it("does not touch another account's job payload", async () => {
    await processDueDeletions(NOW);

    // The `order: { userId }` filter is the scope. Another user's retained row is not this
    // request's to change.
    const other = jobRows.find((row) => row.ownerId === "u2");
    expect(other?.payload).toEqual(ORIGINAL_JOB_PAYLOAD);
  });

  it("is safe to run twice: the second pass writes the same NULL again", async () => {
    await processDueDeletions(NOW);
    await processDueDeletions(NOW);

    expect(txMock.job.updateMany).toHaveBeenCalledTimes(2);
    expect(jobRows[0]!.payload).toBeNull();
  });
});

describe("processDueDeletions — a report that commits during erasure (must-fix 2a)", () => {
  const LATE_KEYS = {
    pdfKey: "reports/u1/o1/r2.pdf",
    mdKey: "reports/u1/o1/r2.md",
    audioKey: null,
    htmlKey: "reports/u1/o1/r2.html",
  };

  beforeEach(() => {
    txMock.report.findMany.mockResolvedValue([{ id: "r1", ...KEYS }]);
    prismaMock.profile.findMany.mockResolvedValue([{ id: "p1" }]);
    prismaMock.order.findMany.mockResolvedValue([{ profileAId: "p1", profileBId: null }]);
  });

  it("reads the keys and deletes exactly the rows it read, by id", async () => {
    await processDueDeletions(NOW);

    expect(txMock.report.findMany).toHaveBeenCalledWith({
      where: { userId: "u1" },
      select: { id: true, pdfKey: true, mdKey: true, audioKey: true, htmlKey: true },
    });
    // Not `where: { userId }`. The transaction is READ COMMITTED (`prisma.ts` sets no
    // `isolationLevel`), so each statement takes a fresh snapshot: a `userId` delete could remove a
    // report that committed after the read, with keys that were never captured.
    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["r1"] } } });
  });

  it("survives a row that commits between the reads and is swept by id next pass", async () => {
    // The row the transaction read, and one that committed after that read — the delete by captured
    // ids cannot touch the second, which is the point: it survives this pass and the re-sweep reads
    // its keys before deleting it by its own id.
    prismaMock.report.findMany
      .mockResolvedValueOnce([{ id: "r2", ...LATE_KEYS }])
      .mockResolvedValue([]);
    prismaMock.report.deleteMany.mockResolvedValue({ count: 1 });

    await processDueDeletions(NOW);

    expect(txMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["r1"] } } });
    expect(prismaMock.report.deleteMany).toHaveBeenCalledWith({ where: { id: { in: ["r2"] } } });
    const queued = (r2Mock.deleteObjectOrQueue.mock.calls as unknown as Array<[string]>).map(
      (call) => call[0],
    );
    expect(queued).toEqual(
      expect.arrayContaining([
        KEYS.pdfKey,
        KEYS.mdKey,
        KEYS.audioKey,
        KEYS.htmlKey,
        LATE_KEYS.pdfKey,
        LATE_KEYS.mdKey,
        LATE_KEYS.htmlKey,
      ]),
    );
    // Two passes only: the late report, then the empty confirmation. The bound is not reached.
    expect(prismaMock.report.findMany).toHaveBeenCalledTimes(2);
  });

  it("writes the captured keys to the deletion queue inside the transaction", async () => {
    await processDueDeletions(NOW);

    // Between the commit and the post-commit R2 loop only memory holds the keys. A process death
    // there would leave the rows deleted, the objects present, and the retry finding no rows — so
    // the queue row must exist before the commit.
    expect(txMock.objectDeletion.createMany).toHaveBeenCalledWith({
      data: Object.values(KEYS).map((fileKey) => ({ fileKey })),
    });
    const queuedAt = events.indexOf("tx:objectDeletion.createMany");
    expect(queuedAt).toBeGreaterThan(-1);
    expect(queuedAt).toBeLessThan(events.indexOf("commit"));
  });

  it("keeps the queued keys even when the post-commit loop fails", async () => {
    // The loop is best-effort; the queue row is what actually guarantees the objects are deleted.
    for (let i = 0; i < Object.keys(KEYS).length; i += 1) {
      r2Mock.deleteObjectOrQueue.mockRejectedValueOnce(new Error("r2 down"));
    }
    const error = vi.spyOn(console, "error").mockImplementation(() => {});

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    expect(txMock.objectDeletion.createMany).toHaveBeenCalledWith({
      data: Object.values(KEYS).map((fileKey) => ({ fileKey })),
    });
    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });

  it("stops the re-sweep at its fixed bound and logs once", async () => {
    // A writer that keeps committing: every read returns a row, so the loop must terminate on the
    // bound rather than chase it for ever.
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    prismaMock.report.findMany.mockResolvedValue([{ id: "r2", ...LATE_KEYS }]);
    prismaMock.report.deleteMany.mockResolvedValue({ count: 1 });

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    expect(prismaMock.report.findMany).toHaveBeenCalledTimes(3);
    const boundLogs = error.mock.calls.filter((call) =>
      String(call[0]).includes("re-sweep hit its bound"),
    );
    expect(boundLogs).toHaveLength(1);
    error.mockRestore();
  });

  it("does not log the bound when the first re-sweep pass finds nothing", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});

    await processDueDeletions(NOW);

    expect(prismaMock.report.findMany).toHaveBeenCalledTimes(1);
    expect(error).not.toHaveBeenCalled();
    error.mockRestore();
  });
});

describe("processDueDeletions — one failure cannot block the rest", () => {
  it("leaves the failed request pending and completes a later one", async () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    prismaMock.deletionRequest.findMany.mockResolvedValue([
      deletionRequest("dr1", "u1"),
      deletionRequest("dr2", "u2"),
    ]);
    // The failure the erasure must survive is a database error inside its own transaction: it
    // happens before anything commits, so request u1 stays pending and u2 is still processed.
    txMock.report.findMany
      .mockRejectedValueOnce(new Error("database hiccup"))
      .mockResolvedValue([]);
    prismaMock.profile.findMany.mockResolvedValue([]);

    await expect(processDueDeletions(NOW)).resolves.toBe(1);

    const completedIds = (
      prismaMock.deletionRequest.update.mock.calls as unknown as Array<[{ where: { id: string } }]>
    ).map((call) => call[0].where.id);
    expect(completedIds).toEqual(["dr2"]);
    expect(consoleError).toHaveBeenCalled();
    consoleError.mockRestore();
  });
});
