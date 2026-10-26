import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

/**
 * AU-02's operator surface: the failed-orders table on the review-queue page, with a Retry button
 * per row and a plain success/failure message. The whole point is that recovery no longer needs
 * SQL, so the message has to say what happened.
 */

const refresh = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

import { FailedOrdersTable } from "../dashboard/failed-orders";

const ROW = {
  orderId: "cmvngcbv60007n1wpm8d74f5n",
  kind: "COMPAT" as const,
  tier: "basic",
  tierName: "Compatibility Snapshot",
  paidAt: "2026-10-25T10:00:00.000Z",
  profileLabel: "Me × Partner",
  jobId: "job-1",
  jobState: "FAILED",
  attempts: 3,
  maxAttempts: 3,
  lastError: "ENGINE_FAILED",
};

const fetchMock = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function reply(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  };
}

describe("FailedOrdersTable", () => {
  it("lists the failed order and its last error", () => {
    render(<FailedOrdersTable rows={[ROW]} />);

    expect(screen.getByText(/Compatibility Snapshot/)).toBeTruthy();
    expect(screen.getByText(/Me × Partner/)).toBeTruthy();
    expect(screen.getByText(/ENGINE_FAILED/)).toBeTruthy();
    expect(screen.getByRole("button", { name: /retry/i })).toBeTruthy();
  });

  it("retries the job for its order and reports success", async () => {
    fetchMock.mockResolvedValue(reply(200, { ok: true, jobId: "job-1", message: "Job requeued." }));

    render(<FailedOrdersTable rows={[ROW]} />);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/admin/jobs/retry",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ orderId: ROW.orderId }),
        }),
      );
    });
    expect(await screen.findByText("Job requeued.")).toBeTruthy();
    expect(refresh).toHaveBeenCalled();
  });

  it("shows the server's refusal instead of pretending the retry worked", async () => {
    fetchMock.mockResolvedValue(
      reply(409, { error: "This order already has a live job.", code: "JOB_ALREADY_LIVE" }),
    );

    render(<FailedOrdersTable rows={[ROW]} />);
    fireEvent.click(screen.getByRole("button", { name: /retry/i }));

    expect(await screen.findByText("This order already has a live job.")).toBeTruthy();
    expect(refresh).not.toHaveBeenCalled();
  });
});
