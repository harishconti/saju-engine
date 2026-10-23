import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// The form uses the app router for `refresh()`; outside a Next tree that context does not exist.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

import { ProfileForm } from "../dashboard/profile-form";

/**
 * The reported bug: "I added a person and pressed save but I don't see any saved person."
 *
 * Nothing had gone wrong in the form — the server correctly refused to store birth data without an
 * active `service` consent, and said so. But the refusal pointed at another page and read as a save
 * that silently did nothing, which is a dead end. Consent is now asked for **in place**, beside the
 * data it covers, so the refusal is actionable where it happens.
 */
describe("ProfileForm and consent", () => {
  it("asks for consent in place when the account has none", () => {
    render(<ProfileForm hasConsent={false} />);
    expect(screen.getByText("I accept the privacy policy")).toBeTruthy();
  });

  it("does not ask when consent is already recorded", () => {
    render(<ProfileForm hasConsent />);
    expect(screen.queryByText("I accept the privacy policy")).toBeNull();
  });

  it("still renders the save button when consent is missing — the prompt must not look like a dead end", () => {
    render(<ProfileForm hasConsent={false} />);
    expect(screen.getByText("Save this person")).toBeTruthy();
  });

  it("keeps the consent tick uncontrolled-by-default, i.e. unasserted until the visitor acts", () => {
    render(<ProfileForm hasConsent={false} />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    const consentBox = boxes.find((b) => b.closest("label")?.textContent?.includes("privacy policy"));
    expect(consentBox).toBeTruthy();
    expect(consentBox!.checked).toBe(false);
  });

  it("does not pre-fill a birth time — a guessed noon is a guessed hour pillar", () => {
    // The site's FAQ promises an unknown birth time is "marked as lower-confidence rather than
    // quietly assuming a time". A pre-filled 12:00 would break that silently.
    render(<ProfileForm hasConsent />);
    const time = screen.getByLabelText("Time of birth") as HTMLInputElement;
    expect(time.value).toBe("");
  });

  it("does not pre-fill a date of birth", () => {
    render(<ProfileForm hasConsent />);
    const date = screen.getByLabelText("Date of birth") as HTMLInputElement;
    expect(date.value).toBe("");
  });
});
