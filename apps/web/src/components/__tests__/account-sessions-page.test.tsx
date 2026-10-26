import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

/**
 * AU-40 (D6): the account page carries the session list and the revoke control. The list is read on
 * the server through the auth wrapper; nothing about the provider is called from the browser.
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

const CURRENT = {
  id: "sess-current",
  userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130.0 Safari/537.36",
  createdAt: "2026-10-01T10:00:00.000Z",
  lastUsedAt: "2026-10-20T11:30:00.000Z",
  current: true,
};
const OTHER = {
  id: "sess-other",
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Safari/604.1",
  createdAt: "2026-09-01T10:00:00.000Z",
  lastUsedAt: "2026-10-18T09:05:00.000Z",
  current: false,
};

beforeEach(() => {
  vi.clearAllMocks();
  requireUser.mockResolvedValue({ id: "u1", name: "Visitor", email: "visitor@example.com", role: "CLIENT" });
  listAccountSessions.mockResolvedValue([CURRENT, OTHER]);
  prisma.consentRecord.findFirst.mockResolvedValue(null);
  prisma.deletionRequest.findFirst.mockResolvedValue(null);
  prisma.user.findUnique.mockResolvedValue({
    createdAt: new Date("2026-01-01T00:00:00.000Z"),
    _count: { profiles: 0, reports: 0, orders: 0 },
  });
});

describe("account page — sessions (AU-40)", () => {
  it("renders the session list, the current-device marker, and the revoke control", async () => {
    const { container } = render(await AccountPage());

    expect(screen.getByRole("heading", { name: "Where you're signed in" })).toBeTruthy();
    expect(screen.getByText("Chrome on macOS")).toBeTruthy();
    expect(screen.getByText("Safari on iOS")).toBeTruthy();
    expect(screen.getByText("This device")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Sign out of other devices" })).toBeTruthy();
    expect(container.textContent).not.toMatch(/session token/i);
  });

  it("promises the current session survives", async () => {
    render(await AccountPage());

    expect(screen.getByText(/this device stays signed in/i)).toBeTruthy();
  });

  it("says so plainly when the provider could not list the sessions", async () => {
    listAccountSessions.mockResolvedValue(null);

    render(await AccountPage());

    expect(screen.getByText(/couldn't load your active sessions/i)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Sign out of other devices" })).toBeNull();
  });
});
