import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

/**
 * AU-22 (2026-10-26 audit): when the sample route refuses a signed-in visitor for missing consent
 * it answers 409 with `{ code: "CONSENT_REQUIRED" }`. The visitor must be sent to the control that
 * fixes it — not told to "try again", which would resubmit the same refused request forever.
 */

vi.mock("@/lib/use-city-index", () => ({ useCityIndex: () => true }));
vi.mock("@vercel/analytics", () => ({ track: vi.fn() }));

import { SampleFlow } from "@/components/sample-flow";

const fetchMock = vi.fn();

function fillTheForm() {
  fireEvent.change(screen.getByLabelText("Your name"), { target: { value: "Visitor" } });

  const date = screen.getByLabelText("Date of birth");
  fireEvent.change(date, { target: { value: "1993-03-19" } });
  fireEvent.blur(date);

  const time = screen.getByLabelText("Time of birth");
  fireEvent.change(time, { target: { value: "14:30" } });
  fireEvent.blur(time);

  fireEvent.change(screen.getByLabelText("Place of birth"), { target: { value: "Seoul" } });
}

beforeEach(() => {
  vi.clearAllMocks();
  fetchMock.mockResolvedValue(
    new Response(JSON.stringify({ error: "Consent required", code: "CONSENT_REQUIRED" }), {
      status: 409,
      headers: { "content-type": "application/json" },
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
});

describe("SampleFlow — consent refusal (AU-22)", () => {
  it("renders a link to the consent control instead of a retry", async () => {
    render(<SampleFlow signedIn engineReady />);
    fillTheForm();

    fireEvent.click(screen.getByRole("button", { name: "Get my free snapshot" }));

    const link = await screen.findByRole("link", { name: /consent/i });
    expect(link.getAttribute("href")).toBe("/dashboard/account");
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
  });
});
