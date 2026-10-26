import { beforeEach, describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";

/**
 * Owner decision D12 (2026-10-26): the account page promised that withdrawing the `service` consent
 * "starts the deletion path". Nothing starts a deletion path — deletion is the separate "Delete
 * account" control with its own grace period. The corrected copy must say what actually happens
 * (owner decision D11): new orders and new readings stop; readings already paid for are still
 * produced and delivered.
 */

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

const { requireUser, listAccountSessions, prisma } = vi.hoisted(() => ({
  requireUser: vi.fn(),
  listAccountSessions: vi.fn(),
  prisma: {
    consentRecord: { findFirst: vi.fn() },
    deletionRequest: { findFirst: vi.fn() },
    user: { findUnique: vi.fn() },
  },
}));

vi.mock("@/lib/auth", () => ({ requireUser, listAccountSessions }));
vi.mock("@/lib/prisma", () => ({ prisma }));

import AccountPage from "@/app/dashboard/account/page";

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", name: "Visitor", email: "visitor@example.com", role: "CLIENT" });
  // AU-40: the page also lists active sessions; an empty list keeps this test about copy.
  listAccountSessions.mockResolvedValue([]);
  prisma.consentRecord.findFirst.mockResolvedValue(null);
  prisma.deletionRequest.findFirst.mockResolvedValue(null);
  prisma.user.findUnique.mockResolvedValue({
    createdAt: new Date("2026-01-01T00:00:00.000Z"),
    _count: { profiles: 0, reports: 0, orders: 0 },
  });
});

describe("account page — withdrawal copy (D11, D12)", () => {
  it("says withdrawal stops new work, not that it starts a deletion path", async () => {
    const { container } = render(await AccountPage());
    const text = container.textContent ?? "";

    expect(text).not.toMatch(/starts the deletion path/i);
    expect(text).not.toMatch(/begins the deletion path/i);
    // What is actually true, in the product's own voice.
    expect(text).toMatch(/stopping? new orders and new readings|stops new orders and new readings/i);
    expect(text).toMatch(/already paid for/i);
    // The append-only-history promise survives the rewrite.
    expect(text).toMatch(/append-only/i);
  });
});
