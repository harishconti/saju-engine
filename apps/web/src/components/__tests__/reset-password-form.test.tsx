import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

/**
 * AU-41 (D6): the reset page.
 *
 * The token arrives in the query string. It is read from `window.location.search` on mount — never
 * from the page's `searchParams`, which Next serialises into the server-rendered payload — then read
 * once into a ref, never rendered, never logged, and never kept after the submit. The address bar is
 * scrubbed on mount so it is not copied into a screenshot or a chat message. The server is the
 * authority on whether the token is valid — the page only reports its answer, with one message for
 * invalid and expired.
 */

let replaceState: ReturnType<typeof vi.spyOn>;

import { ResetPasswordForm } from "../reset-password-form";

const TOKEN = "tok_4f9a2c7b1e8d6f3a5c0b9e7d2a1f8c6b";
const INVALID = "This reset link is invalid or has expired. Request a new one.";

const fetchMock = vi.fn();

function setUrl(search: string) {
  // A test may call this after the spy exists; drop it so the address bar really changes.
  replaceState?.mockRestore();
  window.history.replaceState(null, "", `/reset-password${search}`);
}

beforeEach(() => {
  vi.clearAllMocks();
  setUrl(`?token=${TOKEN}`);
  vi.stubGlobal("fetch", fetchMock);
  replaceState = vi.spyOn(window.history, "replaceState").mockImplementation(() => {});
});

afterEach(() => {
  vi.unstubAllGlobals();
  replaceState.mockRestore();
});

function fill(newPassword = "correct-horse-battery", confirm = newPassword) {
  fireEvent.change(screen.getByLabelText("New password"), { target: { value: newPassword } });
  fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: confirm } });
}

function submit() {
  fireEvent.click(screen.getByRole("button", { name: "Set new password" }));
}

describe("ResetPasswordForm", () => {
  it("accepts a valid token and sets the password", async () => {
    fetchMock.mockResolvedValue({ ok: true, status: 200, json: async () => ({ ok: true }) });
    render(<ResetPasswordForm />);

    fill();
    submit();

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const [url, init] = fetchMock.mock.calls[0]! as [string, RequestInit];
    expect(url).toBe("/api/account/password-reset/confirm");
    expect(JSON.parse(String(init.body))).toEqual({
      token: TOKEN,
      newPassword: "correct-horse-battery",
    });
    expect(await screen.findByText(/your password has been changed/i)).toBeTruthy();
  });

  it("shows one message for an invalid or expired token", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ error: INVALID, code: "INVALID_RESET_TOKEN" }),
    });
    render(<ResetPasswordForm />);

    fill();
    submit();

    expect(await screen.findByText(INVALID)).toBeTruthy();
    expect(screen.queryByText(/your password has been changed/i)).toBeNull();
  });

  it("handles an expired link that arrives with ?error= instead of a token", () => {
    setUrl("?error=INVALID_TOKEN");
    render(<ResetPasswordForm />);

    expect(screen.getByText(INVALID)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Set new password" })).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("refuses a mismatch before spending the one-time token", async () => {
    render(<ResetPasswordForm />);

    fill("correct-horse-battery", "different-password");
    submit();

    expect(await screen.findByText(/passwords don't match/i)).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("refuses a short password before spending the one-time token", async () => {
    render(<ResetPasswordForm />);

    fill("short", "short");
    submit();

    expect(await screen.findByText(/at least 8 characters/i)).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("refuses an over-long password before spending the one-time token", async () => {
    render(<ResetPasswordForm />);

    // The server schema caps the password at 128; checking it here gives the length message instead
    // of a generic failure from the route's validation.
    const tooLong = "a".repeat(129);
    fill(tooLong, tooLong);
    submit();

    expect(await screen.findByText(/at most 128 characters/i)).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("explains a rate limit instead of claiming the token was bad", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => ({ error: "Too many requests, please slow down", code: "RATE_LIMITED" }),
    });
    render(<ResetPasswordForm />);

    fill();
    submit();

    expect(await screen.findByText(/too many attempts/i)).toBeTruthy();
    expect(screen.queryByText(INVALID)).toBeNull();
  });

  it("never renders the token", () => {
    const { container } = render(<ResetPasswordForm />);

    expect(container.textContent).not.toContain(TOKEN);
    expect(container.innerHTML).not.toContain(TOKEN);
  });

  it("scrubs the token out of the address bar on mount", () => {
    render(<ResetPasswordForm />);

    expect(replaceState).toHaveBeenCalledWith(null, "", "/reset-password");
  });

  it("never writes the token to a log line", async () => {
    const errors = vi.spyOn(console, "error").mockImplementation(() => {});
    const warns = vi.spyOn(console, "warn").mockImplementation(() => {});
    const logs = vi.spyOn(console, "log").mockImplementation(() => {});
    fetchMock.mockRejectedValue(new Error(`network down for ${TOKEN}`));
    render(<ResetPasswordForm />);

    fill();
    submit();
    await screen.findByText(/couldn't reset your password just now/i);

    const all = [...errors.mock.calls, ...warns.mock.calls, ...logs.mock.calls]
      .flat()
      .map((arg) => (typeof arg === "string" ? arg : JSON.stringify(arg)))
      .join(" ");
    expect(all).not.toContain(TOKEN);

    errors.mockRestore();
    warns.mockRestore();
    logs.mockRestore();
  });
});
