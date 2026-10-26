import { beforeEach, describe, expect, it, vi } from "vitest";

/**
 * AU-22 (2026-10-26 audit): Google and magic-link sign-ups never recorded consent. The three
 * sign-in paths converge on `/auth/complete`, and it is the only server-side point every one of
 * them passes through — so recording the initial grant there is what makes the promise true for
 * all three instead of only the email form's best-effort browser call.
 */

const { getCurrentUser, recordInitialServiceConsent, redirect } = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  recordInitialServiceConsent: vi.fn(),
  redirect: vi.fn((url: string) => {
    throw new Error(`NEXT_REDIRECT:${url}`);
  }),
}));

vi.mock("@/lib/auth", () => ({ getCurrentUser }));
vi.mock("@/lib/consent", () => ({ recordInitialServiceConsent }));
vi.mock("next/navigation", () => ({ redirect }));

const { default: AuthCompletePage } = await import("@/app/auth/complete/page");

beforeEach(() => {
  vi.clearAllMocks();
  getCurrentUser.mockResolvedValue({ id: "u1", name: "Test", email: "t@test", role: "CLIENT" });
  recordInitialServiceConsent.mockResolvedValue(undefined);
});

describe("/auth/complete — initial consent (AU-22)", () => {
  it("records the first consent for the just-mirrored user, then redirects onward", async () => {
    await expect(
      AuthCompletePage({ searchParams: Promise.resolve({ next: "/dashboard" }) }),
    ).rejects.toThrow("NEXT_REDIRECT:/dashboard");

    expect(recordInitialServiceConsent).toHaveBeenCalledTimes(1);
    expect(recordInitialServiceConsent).toHaveBeenCalledWith("u1");
  });

  it("redirects without recording for an arrival with no session", async () => {
    getCurrentUser.mockResolvedValue(null);

    await expect(
      AuthCompletePage({ searchParams: Promise.resolve({ next: "/sample" }) }),
    ).rejects.toThrow("NEXT_REDIRECT:/sample");

    expect(recordInitialServiceConsent).not.toHaveBeenCalled();
  });

  it("never blocks sign-in when the consent write fails — the app gate still protects birth data", async () => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    recordInitialServiceConsent.mockRejectedValue(new Error("database down"));

    await expect(
      AuthCompletePage({ searchParams: Promise.resolve({ next: "/dashboard" }) }),
    ).rejects.toThrow("NEXT_REDIRECT:/dashboard");

    expect(error).toHaveBeenCalled();
    error.mockRestore();
  });
});
