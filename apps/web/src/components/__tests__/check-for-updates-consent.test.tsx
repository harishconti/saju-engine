import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

/**
 * "Check for updates" is the other way a customer can start report generation (AU-24, D7). With no
 * active service consent the route refuses with `CONSENT_REQUIRED`, and — as in the order flow —
 * the visitor needs the link to the control that fixes it, not just an error string.
 */

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

import { CheckForUpdatesButton } from "../dashboard/check-for-updates";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("CheckForUpdatesButton — withdrawn consent (AU-24)", () => {
  it("turns CONSENT_REQUIRED into a link to the consent control", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({
        error: "Please accept the privacy policy in your account settings first.",
        code: "CONSENT_REQUIRED",
      }),
    });
    render(<CheckForUpdatesButton />);

    fireEvent.click(screen.getByRole("button", { name: "Check for updates" }));

    expect(await screen.findByText(/accept the privacy policy/i)).toBeTruthy();
    expect(screen.getByRole("link", { name: /Open your consent settings/i }).getAttribute("href")).toBe(
      "/dashboard/account",
    );
  });
});
