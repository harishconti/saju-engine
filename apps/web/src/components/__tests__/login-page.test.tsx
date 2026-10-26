import fs from "node:fs";
import path from "node:path";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

/**
 * AU-15 (2026-10-26 audit): the login form leaked whether an email was registered.
 *
 * The enumeration masking from `5701ce9` only covered errors that arrived by *throwing*; the
 * three `result.error.message` branches printed whatever the auth server said, and the
 * `?error=` code the magic-link / Google callbacks append to their failure redirect was never
 * read at all. Every display now goes through one helper, and the callback error is shown.
 */

const { state, signInEmail, signUpEmail, signInSocial, signInMagicLink } = vi.hoisted(() => ({
  state: { params: new URLSearchParams() },
  signInEmail: vi.fn(),
  signUpEmail: vi.fn(),
  signInSocial: vi.fn(),
  signInMagicLink: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
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
