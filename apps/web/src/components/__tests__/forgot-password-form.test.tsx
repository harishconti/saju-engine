import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";

/**
 * AU-41 (D6): "Forgot password?" — the request step.
 *
 * The visitor must not be able to tell a registered address from an unregistered one. The server
 * route is where that is guaranteed (its test compares both cases byte-for-byte); this test pins
 * the UI half: one confirmation sentence, reached by the same path for either address.
 */

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

import { ForgotPasswordForm } from "../forgot-password-form";

const NEUTRAL_CONFIRMATION =
  "If an account exists for that address, we've sent a reset link. Check your inbox — the link expires in an hour.";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function submit(email: string) {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: email } });
  fireEvent.click(screen.getByRole("button", { name: "Send reset link" }));
}

describe("ForgotPasswordForm", () => {
  it("shows the same neutral confirmation for any address", async () => {
    fetchMock.mockResolvedValue({ ok: true, status: 202, json: async () => ({ ok: true }) });
    render(<ForgotPasswordForm />);

    submit("member@example.com");
    expect(await screen.findByText(NEUTRAL_CONFIRMATION)).toBeTruthy();

    // A second visit from a fresh render, with an address that is certainly not registered.
    cleanup();
    fetchMock.mockClear();
    render(<ForgotPasswordForm />);
    submit("nobody@example.com");
    expect(await screen.findByText(NEUTRAL_CONFIRMATION)).toBeTruthy();
  });

  it("posts the trimmed address to the server route", async () => {
    fetchMock.mockResolvedValue({ ok: true, status: 202, json: async () => ({ ok: true }) });
    render(<ForgotPasswordForm />);

    submit("  Member@Example.com ");

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0]! as [string, RequestInit];
    expect(url).toBe("/api/account/password-reset");
    expect(init.method).toBe("POST");
    expect(JSON.parse(String(init.body))).toEqual({ email: "Member@Example.com" });
  });

  it("offers a way back to sign in", () => {
    render(<ForgotPasswordForm />);

    const link = screen.getByRole("link", { name: /back to sign in/i });
    expect(link.getAttribute("href")).toBe("/login");
  });

  it("explains a rate limit instead of pretending the mail was sent", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ error: "Too many requests, please slow down", code: "RATE_LIMITED" }),
    });
    render(<ForgotPasswordForm />);

    submit("member@example.com");

    expect(await screen.findByText(/too many reset requests/i)).toBeTruthy();
    expect(screen.queryByText(NEUTRAL_CONFIRMATION)).toBeNull();
  });

  it("shows an honest error when the request never reaches the server", async () => {
    fetchMock.mockRejectedValue(new Error("offline"));
    render(<ForgotPasswordForm />);

    submit("member@example.com");

    expect(await screen.findByText(/couldn't send that just now/i)).toBeTruthy();
  });
});
