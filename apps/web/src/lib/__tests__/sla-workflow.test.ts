import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { describe, expect, it } from "vitest";

/**
 * The scheduled workflow is the only thing that dispatches queued jobs on the normal path.
 *
 * AU-13 (2026-10-26 audit): Vercel's Hobby plan runs a cron once a day, but the code claimed a
 * per-minute dispatcher. A queued job — a `VOICE` job among them — waited up to 24 hours while the
 * pricing page promised a ten-hour delivery. Decision D4 is to dispatch every 15 minutes from the
 * workflow that already runs on that cadence.
 *
 * The dispatch must be its OWN job, not a step after the sweep: the sweep exits non-zero exactly
 * when jobs are stuck, so a later step in the same job would be skipped when dispatch matters most.
 *
 * `js-yaml` is parsed here, not asserted on with regular expressions, so a malformed workflow fails
 * this test rather than the next scheduled run. It is already in the dev tree via eslint.
 */

interface WorkflowStep {
  name?: string;
  env?: Record<string, string>;
  run?: string;
}
interface WorkflowJob {
  if?: string;
  "runs-on"?: string;
  steps?: WorkflowStep[];
}
interface WorkflowDoc {
  on?: { schedule?: Array<{ cron: string }> };
  jobs?: Record<string, WorkflowJob>;
}

const yaml = createRequire(import.meta.url)("js-yaml") as { load: (text: string) => unknown };

function workflow(): WorkflowDoc {
  const file = path.resolve(process.cwd(), "../../.github/workflows/sla-sweep.yml");
  return yaml.load(readFileSync(file, "utf8")) as WorkflowDoc;
}

describe("the 15-minute dispatch cadence", () => {
  it("parses, and every cron gate names a schedule entry that exists", () => {
    const doc = workflow();
    const schedules = (doc.on?.schedule ?? []).map((s) => s.cron);
    expect(schedules.length).toBeGreaterThan(0);

    for (const [name, job] of Object.entries(doc.jobs ?? {})) {
      const gate = job.if ?? "";
      const literal = /\*\/\d+ \* \* \* \*/.exec(gate);
      if (!literal) continue;
      // A gate comparing a string that is no longer scheduled means the job never runs.
      expect(schedules, `${name} is gated on ${literal[0]}`).toContain(literal[0]);
    }
  });

  it("dispatches queued jobs from an independent job, with the cron secret", () => {
    const doc = workflow();
    const dispatch = doc.jobs?.dispatch;
    expect(dispatch, "the workflow has no dispatch job").toBeTruthy();
    // Every 15 minutes, like the sweep — and independently, so a failing sweep cannot skip it.
    expect(dispatch!.if).toContain("*/15 * * * *");

    const step = dispatch!.steps?.find((s) => (s.run ?? "").includes("/api/cron/dispatch"));
    expect(step, "the dispatch job never calls /api/cron/dispatch").toBeTruthy();
    expect(step!.env?.CRON_SECRET).toBe("${{ secrets.CRON_SECRET }}");
    expect(step!.run).toContain("Authorization: Bearer $CRON_SECRET");
    expect(step!.run).toContain("POST");
  });

  it("does not hide the dispatch behind the sweep's failure exit", () => {
    const doc = workflow();
    const sweep = doc.jobs?.sweep;
    // The sweep deliberately exits non-zero on stuck or recently failed jobs. A dispatch step
    // placed after it in the same job would never run in exactly that state.
    const inSweep = (sweep?.steps ?? []).some((s) => (s.run ?? "").includes("/api/cron/dispatch"));
    expect(inSweep).toBe(false);
  });
});
