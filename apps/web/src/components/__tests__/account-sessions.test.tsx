import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

/**
 * AU-40 (D6): the account page's session list and "Sign out of other devices" control.
 *
 * The panel is a client component so the action can show an honest error; the list itself is
 * rendered on the server (the page test covers that) and passed in already redacted.
 */

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh, push: vi.fn(), replace: vi.fn() }),
}));

import { SessionsPanel } from "../dashboard/account-sessions";
import type { AccountSession } from "@/lib/auth";

const CURRENT: AccountSession = {
  id: "sess-current",
  userAgent:
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
  createdAt: "2026-10-01T10:00:00.000Z",
  lastUsedAt: "2026-10-20T11:30:00.000Z",
  current: true,
};
const OTHER: AccountSession = {
  id: "sess-other",
  userAgent:
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
  createdAt: "2026-09-01T10:00:00.000Z",
  lastUsedAt: "2026-10-18T09:05:00.000Z",
  current: false,
};

const fetchMock = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SessionsPanel", () => {
  it("names each device and marks only the current one", () => {
    render(<SessionsPanel sessions={[CURRENT, OTHER]} />);

    expect(screen.getByText("Chrome on macOS")).toBeTruthy();
    expect(screen.getByText("Chrome on Windows")).toBeTruthy();
    expect(screen.getAllByText("This device")).toHaveLength(1);
    // The exact clock time depends on the test machine's zone; the date and the label do not.
    expect(screen.getByText(/Last used 18 Oct 2026/)).toBeTruthy();
  });

  it("signs out other devices through the route and confirms the current one stayed", async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
    render(<SessionsPanel sessions={[CURRENT, OTHER]} />);

    fireEvent.click(screen.getByRole("button", { name: "Sign out of other devices" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0]! as [string, RequestInit];
    expect(url).toBe("/api/account/sessions");
    expect(init.method).toBe("POST");
    expect(await screen.findByText(/still signed in on this device/i)).toBeTruthy();
    expect(refresh).toHaveBeenCalled();
  });

  it("shows the server's error and keeps the list when the revoke fails", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ error: "We couldn't sign out your other devices. Please try again." }),
    });
    render(<SessionsPanel sessions={[CURRENT, OTHER]} />);

    fireEvent.click(screen.getByRole("button", { name: "Sign out of other devices" }));

    expect(await screen.findByText(/couldn't sign out your other devices/i)).toBeTruthy();
    expect(screen.getByText("Chrome on Windows")).toBeTruthy();
    expect(refresh).not.toHaveBeenCalled();
  });

  it("shows an error when the request never reaches the server", async () => {
    fetchMock.mockRejectedValue(new Error("offline"));
    render(<SessionsPanel sessions={[CURRENT, OTHER]} />);

    fireEvent.click(screen.getByRole("button", { name: "Sign out of other devices" }));

    expect(await screen.findByText(/couldn't sign out your other devices/i)).toBeTruthy();
  });

  it("says there is nothing to sign out when this is the only session", () => {
    render(<SessionsPanel sessions={[CURRENT]} />);

    const button = screen.getByRole("button", { name: "Sign out of other devices" }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    expect(screen.getByText(/only signed in on this device/i)).toBeTruthy();
  });

  describe("when the provider could not list the sessions", () => {
    it("keeps the revoke control and shows an error distinct from 'no other devices'", () => {
      render(<SessionsPanel sessions={null} />);

      expect(screen.getByText(/couldn't load your active sessions/i)).toBeTruthy();
      // Null is "we don't know", not "there are none" — the empty-list sentence would be a claim.
      expect(screen.queryByText(/only signed in on this device/i)).toBeNull();

      const button = screen.getByRole("button", { name: "Sign out of other devices" }) as HTMLButtonElement;
      expect(button.disabled).toBe(false);
      // Signing out and back in revokes nothing on the other devices, so it is not offered as a fix.
      expect(screen.queryByText(/sign out and back in/i)).toBeNull();
    });

    it("still calls the revoke route and confirms success without the list", async () => {
      fetchMock.mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
      render(<SessionsPanel sessions={null} />);

      fireEvent.click(screen.getByRole("button", { name: "Sign out of other devices" }));

      await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
      const [url, init] = fetchMock.mock.calls[0]! as [string, RequestInit];
      expect(url).toBe("/api/account/sessions");
      expect(init.method).toBe("POST");
      expect(await screen.findByText(/still signed in on this device/i)).toBeTruthy();
      expect(refresh).toHaveBeenCalled();
    });

    it("still reports a provider failure honestly", async () => {
      fetchMock.mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ error: "We couldn't sign out your other devices. Please try again." }),
      });
      render(<SessionsPanel sessions={null} />);

      fireEvent.click(screen.getByRole("button", { name: "Sign out of other devices" }));

      expect(await screen.findByText(/couldn't sign out your other devices/i)).toBeTruthy();
      expect(refresh).not.toHaveBeenCalled();
    });
  });
});
