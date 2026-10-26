import fs from "node:fs";
import path from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

/**
 * AU-15 (2026-10-26 audit): the login form leaked whether an email was registered.
 *
 * The enumeration masking from `5701ce9` only covered errors that arrived by *throwing*; the
 * three `result.error.message` branches printed whatever the auth server said, and the
 * `?error=` code the magic-link / Google callbacks append to their failure redirect was never
 * read at all. Every display now goes through one helper, and the callback error is shown.
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

// Same shape the real guard uses: an object carrying the private `__isAuthError` marker.
vi.mock("@neondatabase/auth/next", () => ({
  isAuthError: (err: unknown) => typeof err === "object" && err !== null && "__isAuthError" in err,
}));

import LoginPage from "@/app/login/page";

const NEUTRAL =
  "We couldn't do that with this email. If you already have an account, sign in or use a magic link.";

function authError(message: string, code?: string): Error {
  return Object.assign(new Error(message), {
    __isAuthError: true,
    name: "AuthApiError",
    status: 400,
    code,
  });
}

function fillSignIn() {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "visitor@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong-password" } });
}

function fillSignUp() {
  fireEvent.click(screen.getByRole("tab", { name: "Sign up" }));
  fireEvent.change(screen.getByLabelText("What should we call you?"), { target: { value: "Visitor" } });
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "visitor@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "correct-horse" } });
  fireEvent.click(screen.getAllByRole("checkbox")[0]!);
}

beforeEach(() => {
  vi.clearAllMocks();
  state.params = new URLSearchParams();
});

describe("login error display", () => {
  it("shows the actionable message for a wrong password", async () => {
    signInEmail.mockRejectedValue(authError("Invalid email or password", "invalid_credentials"));
    render(<LoginPage />);
    fillSignIn();

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByText("Invalid email or password")).toBeTruthy();
  });

  it("shows the neutral sentence when sign-up reports an existing account", async () => {
    signUpEmail.mockRejectedValue(
      authError("User already exists", "USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL"),
    );
    render(<LoginPage />);
    fillSignUp();

    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText(NEUTRAL)).toBeTruthy();
    expect(screen.queryByText("User already exists")).toBeNull();
  });

  it("masks an existing account even when the error is returned rather than thrown", async () => {
    // The client's contract has both shapes; the returned object is a plain `{ code, message }`.
    signUpEmail.mockResolvedValue({ error: { message: "User already exists", code: "user_already_exists" } });
    render(<LoginPage />);
    fillSignUp();

    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    expect(await screen.findByText(NEUTRAL)).toBeTruthy();
    expect(screen.queryByText("User already exists")).toBeNull();
  });

  it("shows the error code a magic-link or Google callback put in the URL", () => {
    state.params = new URLSearchParams("error=access_denied");
    render(<LoginPage />);

    expect(screen.getByText(/access_denied/)).toBeTruthy();
  });

  it("reads the callback error from the same query string that carries next", () => {
    state.params = new URLSearchParams("next=%2Fdashboard&error=state_mismatch");
    render(<LoginPage />);

    expect(screen.getByText(/state_mismatch/)).toBeTruthy();
  });
});

describe("password reset entry point (AU-41, D6)", () => {
  it("offers a 'Forgot password?' link that leads to the request step", () => {
    render(<LoginPage />);

    const link = screen.getByRole("link", { name: /forgot password\?/i });
    expect(link.getAttribute("href")).toBe("/forgot-password");
  });
});

describe("all three sign-in paths record consent through /auth/complete (AU-22)", () => {
  it("sends a completed email sign-up through /auth/complete, not straight to the dashboard", async () => {
    signUpEmail.mockResolvedValue({});
    render(<LoginPage />);
    fillSignUp();

    fireEvent.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => expect(push).toHaveBeenCalledTimes(1));
    expect(push.mock.calls[0]![0]).toBe(`/auth/complete?next=${encodeURIComponent("/dashboard")}`);
  });

  it("points Google and magic-link new users at the same place", async () => {
    signInSocial.mockResolvedValue({});
    signInMagicLink.mockResolvedValue({});
    render(<LoginPage />);

    fireEvent.click(screen.getByRole("button", { name: /Continue with Google/ }));
    await waitFor(() => expect(signInSocial).toHaveBeenCalledTimes(1));
    const google = signInSocial.mock.calls[0]![0] as Record<string, string>;
    expect(google.callbackURL).toMatch(/\/auth\/complete\?next=%2Fdashboard$/);
    expect(google.newUserCallbackURL).toMatch(/\/auth\/complete\?next=%2Fdashboard$/);

    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "visitor@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: /magic link/i }));
    await waitFor(() => expect(signInMagicLink).toHaveBeenCalledTimes(1));
    const magic = signInMagicLink.mock.calls[0]![0] as Record<string, string>;
    expect(magic.callbackURL).toMatch(/\/auth\/complete\?next=%2Fdashboard$/);
    expect(magic.newUserCallbackURL).toMatch(/\/auth\/complete\?next=%2Fdashboard$/);
  });
});

describe("no login path can print the server's raw error message", () => {
  const source = fs.readFileSync(
    path.resolve(import.meta.dirname, "../../app/login/page.tsx"),
    "utf8",
  );

  it("never renders result.error.message directly", () => {
    expect(source).not.toMatch(/result\?\.error\.message/);
  });

  it("routes all three returned-error branches through authErrorMessage", () => {
    expect(source.match(/authErrorMessage\(result\?\.error/g) ?? []).toHaveLength(3);
  });
});
