import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

/**
 * AU-24 (owner decision D7, 2026-10-26): a pending deletion is supposed to disable sign-in, and the
 * account page promised it in exactly those words. The block happens server-side (`getCurrentUser`
 * answers null), but credentials still verify at the identity provider, so without this the visitor
 * would be bounced between pages with no explanation.
 *
 * Two things are owed once the credentials verify: a specific reason, and the cancel control the
 * privacy page promises is available "any time before it completes" — which is unreachable from the
 * account page when sign-in is off.
 */

const { state, signInEmail, signUpEmail, signInSocial, signInMagicLink, push, refresh } = vi.hoisted(() => ({
  state: { params: new URLSearchParams() },
  signInEmail: vi.fn(),
  signUpEmail: vi.fn(),
  signInSocial: vi.fn(),
  signInMagicLink: vi.fn(),
  push: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, refresh }),
  useSearchParams: () => state.params,
}));

vi.mock("@/lib/auth/client", () => ({
  authClient: {
    signIn: { email: signInEmail, social: signInSocial, magicLink: signInMagicLink },
    signUp: { email: signUpEmail },
  },
}));

vi.mock("@neondatabase/auth/next", () => ({
  isAuthError: (err: unknown) => typeof err === "object" && err !== null && "__isAuthError" in err,
}));

import LoginPage from "@/app/login/page";

const fetchMock = vi.fn();

function fillSignIn() {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "visitor@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "correct-horse" } });
}

function jsonResponse(body: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => body };
}

beforeEach(() => {
  vi.clearAllMocks();
  state.params = new URLSearchParams();
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockResolvedValue(jsonResponse({ deletion: null }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("login — pending deletion (AU-24)", () => {
  it("shows a specific message and does not enter the app when credentials verify", async () => {
    signInEmail.mockResolvedValue({});
    // This is the answer `/api/account/deletion` gives a blocked session: the session exists, but
    // the account is not a live user.
    fetchMock.mockResolvedValue(
      jsonResponse({ deletion: { id: "d1", status: "pending" }, pendingDeletion: true }),
    );
    render(<LoginPage />);
    fillSignIn();

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText(/This account is pending deletion/i)).toBeTruthy();
    expect(push).not.toHaveBeenCalled();
  });

  it("offers the cancel control, and cancelling resumes the sign-in", async () => {
    signInEmail.mockResolvedValue({});
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ deletion: { id: "d1" }, pendingDeletion: true }))
      .mockResolvedValueOnce(jsonResponse({ deletion: { id: "d1", status: "cancelled" } }));
    render(<LoginPage />);
    fillSignIn();

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    const cancel = await screen.findByRole("button", { name: /Cancel scheduled deletion/i });

    fireEvent.click(cancel);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(fetchMock.mock.calls[1]![1]).toMatchObject({ method: "DELETE" });
    await waitFor(() => expect(push).toHaveBeenCalledWith("/dashboard"));
  });

  it("signs a normal account straight in without mentioning deletion", async () => {
    signInEmail.mockResolvedValue({});
    render(<LoginPage />);
    fillSignIn();

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(push).toHaveBeenCalledWith("/dashboard"));
    expect(screen.queryByText(/pending deletion/i)).toBeNull();
  });

  it("shows the same reason when an OAuth sign-in bounces back with the code", () => {
    state.params = new URLSearchParams("error=ACCOUNT_PENDING_DELETION");

    render(<LoginPage />);

    expect(screen.getByText(/This account is pending deletion/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Cancel scheduled deletion/i })).toBeTruthy();
  });

  it("keeps the generic message for other callback codes", () => {
    state.params = new URLSearchParams("error=state_mismatch");

    render(<LoginPage />);

    expect(screen.getByText(/state_mismatch/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Cancel scheduled deletion/i })).toBeNull();
  });
});
