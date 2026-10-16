#!/usr/bin/env python3
"""Prune old Vercel deployments, because Functions Storage counts every retained bundle.

Why this exists: Vercel charges the account's **Functions Storage** (Hobby: 10 GB) for every
retained deployment's function bundle. A bundle is not small here — the engine function carries
the whole Python dependency closure (~125 MB, mostly pandas and numpy pulled in by `sajupy`) plus
the repository, and the webapp carries Next's server output — so a few dozen deployments of each
project fill the cap. It is retention, not any single artefact, and every push to `develop`
deploys **both** projects.

    python3 tools/prune_deployments.py                    # dry run: show what would go
    python3 tools/prune_deployments.py --apply            # actually remove
    python3 tools/prune_deployments.py --keep 10 --apply   # keep more rollback history

Safety, in layers:

* **Dry run is the default.** Nothing is removed without `--apply`.
* **`--safe` is always passed to the CLI**, which refuses to remove any deployment holding an
  active alias. The live deployment can therefore not be removed by this script.
* **The newest `--keep` per project are never candidates**, so recent rollback targets survive.
* Vercel keeps a floor of its own regardless (Hobby: the last 3 created and the last 3 Ready
  production deployments, plus anything aliased or the latest preview of an active branch), so a
  project cannot be pruned below roughly `--keep 3` even if asked to.

Deleting a deployment is irreversible once its 30-day recovery window passes: an older deployment
cannot be promoted again afterwards. That is the trade this script makes, and why the default keep
is small but not zero.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

DEFAULT_PROJECTS = ("saju-engine", "saju-report-engine")
BATCH = 10


def vercel(*args: str, timeout: int = 180, allow_safe_skip: bool = False) -> str:
    """Run the Vercel CLI. `npx vercel` because the CLI is not installed globally here.

    With ``allow_safe_skip``, the one refusal that is *not* a failure is tolerated: `--safe`
    refuses a batch in which nothing is removable because every candidate is aliased
    ("Could not find unaliased deployments …"). That is the guard working, and a run with nothing
    left to do should say so rather than look like it crashed.
    """
    result = subprocess.run(
        ["npx", "--yes", "vercel", *args],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        combined = f"{result.stdout}\n{result.stderr}"
        if allow_safe_skip and "unaliased deployments" in combined:
            return combined
        # The CLI writes some errors to stdout, so report both rather than guess.
        raise SystemExit(
            f"vercel {' '.join(args)} failed (rc={result.returncode}):\n"
            f"{result.stdout.strip()}\n{result.stderr.strip()}"
        )
    return result.stdout


def list_deployments(project: str, *, max_pages: int = 20) -> list:
    """Every deployment of ``project``, newest first: [(createdAt, url, target, state)]."""
    deployments: list = []
    cursor = ""
    for _page in range(max_pages):
        args = ["ls", project, "--json"] + (["--next", cursor] if cursor else [])
        try:
            payload = json.loads(vercel(*args) or "{}")
        except json.JSONDecodeError:
            break
        items = payload.get("deployments") or []
        if not items:
            break
        for item in items:
            deployments.append((item.get("createdAt", 0), item.get("url", ""),
                                item.get("target", ""), item.get("state", "")))
        # The CLI returns the cursor as a *number*, which cannot go straight into an argv list.
        cursor = str((payload.get("pagination") or {}).get("next") or "")
        if not cursor:
            break
    deployments.sort(key=lambda row: row[0], reverse=True)
    return deployments


def prune(deployments: list, *, keep: int, apply: bool) -> tuple:
    """Plan (or perform) the removals. Returns (kept, candidates, removed, skipped)."""
    kept = deployments[:keep]
    candidates = [row for row in deployments[keep:] if row[1]]
    if not apply or not candidates:
        return kept, candidates, [], []

    removed: list = []
    skipped: list = []
    for index in range(0, len(candidates), BATCH):
        batch = [row[1] for row in candidates[index:index + BATCH]]
        # `--safe`: never remove a deployment with an active alias — the live site is not ours to
        # touch here. `--yes`: no interactive prompt, because this is meant to be repeatable.
        output = vercel("remove", *batch, "--safe", "--yes", allow_safe_skip=True)
        if "unaliased deployments" in output:
            skipped.extend(batch)
            state = "all aliased — left alone"
        else:
            removed.extend(batch)
            state = "removed"
        print(f"    batch {index // BATCH + 1}: {len(batch)} requested — {state}")
    return kept, candidates, removed, skipped


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", action="append", default=None,
                        help=f"project to prune (repeatable); default {list(DEFAULT_PROJECTS)}")
    parser.add_argument("--keep", type=int, default=3,
                        help="newest deployments to keep per project (default 3)")
    parser.add_argument("--apply", action="store_true",
                        help="actually remove; without it this is a dry run")
    parser.add_argument("--max-pages", type=int, default=20,
                        help="how many 20-deployment pages to read (default 20 = 400)")
    args = parser.parse_args(argv)

    projects = args.project or list(DEFAULT_PROJECTS)
    if args.keep < 1:
        parser.error("--keep must be at least 1: removing every deployment would take the site down")

    print(f"  {'APPLYING' if args.apply else 'DRY RUN'} — keeping the newest {args.keep} per project")
    total_candidates = 0
    for project in projects:
        try:
            deployments = list_deployments(project, max_pages=args.max_pages)
        except SystemExit as exc:
            print(f"  {project}: {exc}", file=sys.stderr)
            continue
        if not deployments:
            print(f"  {project}: no deployments found")
            continue
        kept, candidates, removed, skipped = prune(deployments, keep=args.keep, apply=args.apply)
        total_candidates += len(candidates)
        print(f"  {project}: {len(deployments)} found · keeping {len(kept)} · "
              f"{len(candidates)} outside the keep window")
        print(f"    newest kept: {kept[0][1] if kept else '—'}")

    if not args.apply:
        print(f"\n  {total_candidates} deployment(s) are candidates. Re-run with --apply.")
        return 0

    print("\n  done — `--safe` never removes a deployment with an active alias.")
    # Say what is left and why, rather than letting the next dry run look like a failure: Vercel
    # keeps a floor of its own (the last 3 created and the last 3 Ready production deployments on
    # Hobby, plus anything aliased or the latest preview of an active branch).
    for project in projects:
        try:
            remaining = list_deployments(project, max_pages=args.max_pages)
        except SystemExit:
            continue
        extra = max(0, len(remaining) - args.keep)
        note = (f" ({extra} retained by Vercel — aliased, or the platform's own floor)"
                if extra else "")
        print(f"  {project}: {len(remaining)} remain{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
