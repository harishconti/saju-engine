#!/usr/bin/env python3
"""Owner CLI for the self-service intake queue.

    python3 tools/intake_admin.py genkey
    python3 tools/intake_admin.py list [--status S]
    python3 tools/intake_admin.py show <id>            # decrypted PII, owner only
    python3 tools/intake_admin.py approve <id> [--base-url URL]
    python3 tools/intake_admin.py regenerate <id>
    python3 tools/intake_admin.py purge [--days N]

Needs SAJU_INTAKE_KEY (except genkey); SAJU_INTAKE_DIR overrides the storage dir.
No email is sent: `approve` prints the private link for you to send.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
for p in (str(PROJECT_ROOT / "src"), os.environ.get("SAJU_SITE")):
    if p and p not in sys.path:
        sys.path.insert(0, p)

from saju_web.jobs import is_stale  # noqa: E402
from saju_web.store import IntakeStore, generate_key  # noqa: E402

INTAKE_DIR = Path(os.environ.get("SAJU_INTAKE_DIR") or PROJECT_ROOT / "candidates_horoscope" / "intake")


def _store() -> IntakeStore:
    return IntakeStore.from_env(INTAKE_DIR / "intake.sqlite", INTAKE_DIR / "files")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="intake_admin")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("genkey")
    sp = sub.add_parser("list")
    sp.add_argument("--status")
    sp = sub.add_parser("show")
    sp.add_argument("id", type=int)
    sp = sub.add_parser("approve")
    sp.add_argument("id", type=int)
    sp.add_argument("--base-url", default="http://localhost:8080")
    sp = sub.add_parser("regenerate")
    sp.add_argument("id", type=int)
    sp.add_argument("--force", action="store_true",
                    help="regenerate even if the row is still 'generating' (not stale)")
    sp = sub.add_parser("purge")
    sp.add_argument("--days", type=int, default=180)
    args = ap.parse_args(argv)

    if args.cmd == "genkey":
        print(generate_key())
        return 0
    try:
        store = _store()
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.cmd == "list":
        now = datetime.now(timezone.utc)
        for r in store.list_intakes(args.status):
            line = f"{r['id']}\t{r['status']}\t{r['kind']}/{r['tier']}\t{r['created_at']}\t{r['name']}"
            if r["status"] in ("received", "generating") and is_stale(r["updated_at"], now):
                line += "\tSTALE - run regenerate"
            print(line)
        return 0
    if args.cmd == "purge":
        n = store.purge_older_than(args.days)
        print(f"purged {n} intake(s) older than {args.days} days")
        return 0

    try:
        row = store.get_intake(args.id)
    except KeyError:
        print(f"error: no intake with id {args.id}", file=sys.stderr)
        return 1
    if args.cmd == "show":
        print(json.dumps(row, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "approve":
        if row["status"] != "draft_ready":
            print(f"error: intake {args.id} is '{row['status']}', must be 'draft_ready' to approve "
                  "(review the draft PDF first; use `regenerate` if it failed)", file=sys.stderr)
            return 1
        token = store.issue_token(args.id)
        print(f"{args.base_url.rstrip('/')}/report/{token}")
        return 0
    if args.cmd == "regenerate":
        if row["status"] == "approved":
            print(f"error: intake {args.id} is already approved", file=sys.stderr)
            return 1
        if (row["status"] == "generating"
                and not is_stale(store.list_intake_updated_at(args.id)) and not args.force):
            print(f"error: intake {args.id} is still 'generating' (not stale); "
                  "wait for it or pass --force", file=sys.stderr)
            return 1
        from saju_web.jobs import generate_draft
        generate_draft(store, args.id, store.files_root)
        print(f"intake {args.id}: {store.get_intake(args.id)['status']}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
