import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

/**
 * "Complete payment" on the dashboard orders list hits the same gated checkout route as the order
 * flow (AU-24, D7). With no active service consent the route refuses with `CONSENT_REQUIRED`, so
 * this surface must offer the link to the control that fixes it — not just the refusal sentence.
 */

import { ResumeCheckoutButton } from "../dashboard/resume-checkout";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ResumeCheckoutButton — checkout refusal", () => {
  it("turns CONSENT_REQUIRED into a link to the consent control", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        error: "Please accept the privacy policy in your account settings first.",
        code: "CONSENT_REQUIRED",
      }),
    });
    render(<ResumeCheckoutButton orderId="order_1" />);

    fireEvent.click(screen.getByRole("button", { name: "Complete payment" }));

    expect(await screen.findByText(/accept the privacy policy/i)).toBeTruthy();
    expect(screen.getByRole("link", { name: /Open your consent settings/i }).getAttribute("href")).toBe(
      "/dashboard/account",
    );
  });

  it("does not add a consent link to an ordinary checkout error", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({ error: "Couldn't reach the payment provider." }),
    });
    render(<ResumeCheckoutButton orderId="order_1" />);

    fireEvent.click(screen.getByRole("button", { name: "Complete payment" }));

    expect(await screen.findByText("Couldn't reach the payment provider.")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /Open your consent settings/i })).toBeNull();
  });
});
