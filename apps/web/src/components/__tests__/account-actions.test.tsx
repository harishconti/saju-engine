import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

/**
 * AU-19 (2026-10-26 audit): the account panels could claim a save that never happened.
 *
 * `ConsentForm` optimistically ticked the box and had no `catch`, so a dropped connection left the
 * checkbox looking saved while nothing was recorded; the deletion panel had no `catch` at all.
 * Consent is the lawful basis for storing birth data, so a failed write must be visible and the
 * control must snap back to the last state the server actually recorded.
 */

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn(), push: vi.fn(), replace: vi.fn() }),
}));

import { AccountNameForm, ConsentForm, DeletionPanel } from "../dashboard/account-actions";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

describe("ConsentForm", () => {
  it("reverts the checkbox and shows the error when the server refuses the save", async () => {
    const pending = deferred<{ ok: boolean; json: () => Promise<{ error: string }> }>();
    fetchMock.mockReturnValue(pending.promise);
    render(<ConsentForm initial={{ service: true, service_messages: false }} policyVersion="v1" />);
    const box = screen.getByRole("checkbox", { name: /Occasional service emails/ }) as HTMLInputElement;

    fireEvent.click(box);
    expect(box.checked).toBe(true); // optimistic, while the request is in flight

    pending.resolve({ ok: false, json: async () => ({ error: "Consent store unavailable" }) });

    expect(await screen.findByText("Consent store unavailable")).toBeTruthy();
    await waitFor(() => expect(box.checked).toBe(false));
  });

  it("reverts the checkbox and shows an error when the request never reaches the server", async () => {
    fetchMock.mockRejectedValue(new Error("offline"));
    render(<ConsentForm initial={{ service: true, service_messages: false }} policyVersion="v1" />);
    const box = screen.getByRole("checkbox", { name: /Occasional service emails/ }) as HTMLInputElement;

    fireEvent.click(box);

    expect(await screen.findByText("We couldn't save that. Please try again.")).toBeTruthy();
    await waitFor(() => expect(box.checked).toBe(false));
  });

  it("reverts to the last confirmed state, not the value at mount", async () => {
    // First save succeeds, so `service_messages: true` is now what the server holds.
    fetchMock.mockResolvedValueOnce({ ok: true, json: async () => ({}) });
    fetchMock.mockRejectedValueOnce(new Error("offline"));
    render(<ConsentForm initial={{ service: true, service_messages: false }} policyVersion="v1" />);
    const box = screen.getByRole("checkbox", { name: /Occasional service emails/ }) as HTMLInputElement;

    fireEvent.click(box);
    await waitFor(() => expect(box.checked).toBe(true));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    fireEvent.click(box); // turn it off again: this save fails
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    await screen.findByText("We couldn't save that. Please try again.");

    // The recorded state after the successful save was "on", so a failed "off" snaps back on.
    expect(box.checked).toBe(true);
  });
});

describe("DeletionPanel", () => {
  it("shows an error instead of silently doing nothing when the request fails", async () => {
    fetchMock.mockRejectedValue(new Error("offline"));
    render(<DeletionPanel scheduledFor={null} status={null} />);

    fireEvent.click(screen.getByRole("button", { name: "Delete my account" }));
    fireEvent.click(screen.getByRole("button", { name: "Yes, schedule deletion" }));

    expect(await screen.findByText("Couldn't schedule deletion.")).toBeTruthy();
  });

  it("shows an error when cancelling a scheduled deletion fails", async () => {
    fetchMock.mockRejectedValue(new Error("offline"));
    render(<DeletionPanel scheduledFor="12 November 2026" status="pending" />);

    fireEvent.click(screen.getByRole("button", { name: "Cancel deletion" }));

    expect(await screen.findByText("Couldn't cancel deletion.")).toBeTruthy();
  });
});

describe("AccountNameForm", () => {
  it("shows an error when the save request fails", async () => {
    fetchMock.mockRejectedValue(new Error("offline"));
    render(<AccountNameForm initialName="Visitor" />);

    fireEvent.click(screen.getByRole("button", { name: "Save name" }));

    expect(await screen.findByText("Couldn't save that.")).toBeTruthy();
  });
});
