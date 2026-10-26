import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * D9 (owner decision, 2026-10-26): retention needs a durable "this account is still used" signal.
 *
 * `Profile.updatedAt` is written once, when the profile is created; `mirrorUser` returns early for an
 * unchanged account and no read route writes the profile. So a customer who signs in every month to
 * re-read their chart looked identical to one who left two years ago, and the 24-month sweep could
 * retire them. `User.lastSeenAt` is that signal: written on authenticated requests, at most once a
 * day per account, and never allowed to break authentication.
 */

type UserRow = {
  id: string;
  name: string;
  email: string;
  role: string;
  deletedAt: Date | null;
  lastSeenAt: Date | null;
};

const DAY_MS = 24 * 60 * 60 * 1000;

const { prismaMock, getSession } = vi.hoisted(() => {
  const prismaMock = {
    user: {
      findUnique: vi.fn(async (_args: Record<string, unknown>) => null as UserRow | null),
      update: vi.fn(async (_args: Record<string, unknown>) => ({
        id: "u1",
        name: "A",
        email: "a@b.c",
        role: "USER",
      })),
      create: vi.fn(async (_args: Record<string, unknown>) => ({
        id: "u1",
        name: "A",
        email: "a@b.c",
        role: "USER",
      })),
      updateMany: vi.fn(async (_args: Record<string, unknown>) => ({ count: 1 })),
    },
  };
  return { prismaMock, getSession: vi.fn() };
});

// `cache()` needs a React request scope that a unit test does not have; identity is what matters.
vi.mock("react", () => ({ cache: (fn: unknown) => fn }));
vi.mock("@/lib/prisma", () => ({ prisma: prismaMock }));
vi.mock("@/lib/auth/server", () => ({ auth: { getSession } }));

const { getCurrentUser } = await import("../auth");

const SESSION = {
  data: { user: { id: "u1", email: "a@b.c", name: "A", emailVerified: true } },
};

function existingRow(lastSeenAt: Date | null): UserRow {
  return { id: "u1", name: "A", email: "a@b.c", role: "USER", deletedAt: null, lastSeenAt };
}

beforeEach(() => {
  vi.clearAllMocks();
  getSession.mockResolvedValue(SESSION);
  prismaMock.user.findUnique.mockResolvedValue(existingRow(null));
  prismaMock.user.updateMany.mockResolvedValue({ count: 1 });
});

describe("getCurrentUser — lastSeenAt (D9)", () => {
  it("records a sign-in when the previous one is older than a day", async () => {
    const stale = new Date(Date.now() - 3 * DAY_MS);
    prismaMock.user.findUnique.mockResolvedValue(existingRow(stale));

    await expect(getCurrentUser()).resolves.toMatchObject({ id: "u1" });

    expect(prismaMock.user.updateMany).toHaveBeenCalledTimes(1);
    const args = prismaMock.user.updateMany.mock.calls[0]![0] as {
      where: { id: string; OR: Array<Record<string, unknown>> };
      data: { lastSeenAt: Date };
    };
    expect(args.where.id).toBe("u1");
    // Conditioned on the stored value as well as the id: two overlapping requests both pass the
    // in-memory check, and only one of them should move the timestamp.
    expect(args.where.OR).toEqual([
      { lastSeenAt: null },
      { lastSeenAt: { lt: expect.any(Date) } },
    ]);
    const threshold = (args.where.OR[1]!.lastSeenAt as { lt: Date }).lt;
    expect(Math.abs(threshold.getTime() - (Date.now() - DAY_MS))).toBeLessThan(5_000);
    expect(args.data.lastSeenAt).toBeInstanceOf(Date);
  });

  it("does not write again inside the 24-hour throttle", async () => {
    prismaMock.user.findUnique.mockResolvedValue(existingRow(new Date(Date.now() - 60_000)));

    await getCurrentUser();

    expect(prismaMock.user.updateMany).not.toHaveBeenCalled();
  });

  it("records the first authenticated request of an account that has never been seen", async () => {
    prismaMock.user.findUnique.mockResolvedValue(existingRow(null));

    await getCurrentUser();

    expect(prismaMock.user.updateMany).toHaveBeenCalledTimes(1);
    expect((prismaMock.user.updateMany.mock.calls[0]![0] as { data: { lastSeenAt: Date } }).data.lastSeenAt).toBeInstanceOf(Date);
  });

  it("stamps a newly mirrored account at creation", async () => {
    prismaMock.user.findUnique.mockResolvedValue(null);

    await expect(getCurrentUser()).resolves.toMatchObject({ id: "u1" });

    const args = prismaMock.user.create.mock.calls[0]![0] as {
      data: { lastSeenAt?: Date };
    };
    expect(args.data.lastSeenAt).toBeInstanceOf(Date);
  });

  it("still authenticates when the sign-in write fails", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    prismaMock.user.findUnique.mockResolvedValue(existingRow(new Date(Date.now() - 5 * DAY_MS)));
    prismaMock.user.updateMany.mockRejectedValue(new Error("database hiccup"));

    await expect(getCurrentUser()).resolves.toMatchObject({ id: "u1", email: "a@b.c" });

    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });

  it("writes nothing for a signed-out request", async () => {
    getSession.mockResolvedValue({ data: null });

    await expect(getCurrentUser()).resolves.toBeNull();

    expect(prismaMock.user.updateMany).not.toHaveBeenCalled();
    expect(prismaMock.user.create).not.toHaveBeenCalled();
  });
});
