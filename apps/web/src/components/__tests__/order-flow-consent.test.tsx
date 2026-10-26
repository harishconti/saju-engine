import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

/**
 * AU-24 (owner decision D7, 2026-10-26): withdrawing the `service` purpose stops processing. The
 * server now refuses to create an order with a 409 `CONSENT_REQUIRED`, and the visitor's only route
 * back is the account page — so the alert has to carry that link. A bare "couldn't create that
 * order" would be a dead end.
 */

const { push, refresh } = vi.hoisted(() => ({ push: vi.fn(), refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
}));

vi.mock("@vercel/analytics", () => ({ track: vi.fn() }));

import { OrderFlow } from "../dashboard/order-flow";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

const PROFILES = [
  { id: "p1", label: "Me", fullName: "Visitor", gender: "F" as const, hasChart: true },
];

async function submitPaidOrder() {
  render(<OrderFlow profiles={PROFILES} initialTier="essential" />);
  fireEvent.click(screen.getByRole("checkbox", { name: /18 or over/i }));
  fireEvent.click(screen.getByRole("button", { name: /^Pay / }));
}

describe("OrderFlow — withdrawn consent (AU-24)", () => {
  it("turns CONSENT_REQUIRED into a link to the consent control", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        error: "Please accept the privacy policy in your account settings first.",
        code: "CONSENT_REQUIRED",
      }),
    });

    await submitPaidOrder();

    expect(await screen.findByText(/accept the privacy policy/i)).toBeTruthy();
    const link = screen.getByRole("link", { name: /Open your consent settings/i });
    expect(link.getAttribute("href")).toBe("/dashboard/account");
  });

  it("does not offer the consent link for an unrelated failure", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ error: "Something went wrong", code: "INTERNAL_ERROR" }),
    });

    await submitPaidOrder();

    expect(await screen.findByText("Something went wrong")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /Open your consent settings/i })).toBeNull();
  });
});
