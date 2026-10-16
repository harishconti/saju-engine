#!/usr/bin/env python3
"""Owner CLI for the self-service intake queue.

    python3 tools/intake_admin.py genkey
    python3 tools/intake_admin.py list [--status S]
    python3 tools/intake_admin.py show <id>            # decrypted PII, owner only
    python3 tools/intake_admin.py approve <id> [--base-url URL]   # default: $SAJU_PUBLIC_URL
    python3 tools/intake_admin.py attach <id> <pdf>    # hand-polished PDF (draft_ready only)
    python3 tools/intake_admin.py revoke <id>          # approved -> draft_ready, link stops working
    python3 tools/intake_admin.py reissue <id> [--base-url URL]   # new link, old one stops working
    python3 tools/intake_admin.py regenerate <id> [--force]
    python3 tools/intake_admin.py rotate               # re-encrypt PII with the first SAJU_INTAKE_KEY
    python3 tools/intake_admin.py purge [--days N]

Needs SAJU_INTAKE_KEY (except genkey; a comma-separated list = key rotation, first key
encrypts); SAJU_PUBLIC_URL is the base for printed links (no localhost default); SAJU_INTAKE_DIR overrides the storage dir.
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

from saju_web import notify  # noqa: E402
from saju_web.jobs import is_stale  # noqa: E402
from saju_web.store import IntakeStore, generate_key  # noqa: E402

INTAKE_DIR = Path(os.environ.get("SAJU_INTAKE_DIR") or PROJECT_ROOT / "candidates_horoscope" / "intake")


def _store() -> IntakeStore:
    return IntakeStore.from_env(INTAKE_DIR / "intake.sqlite", INTAKE_DIR / "files")


def _base_url(cli_value: str | None) -> str | None:
    base = (cli_value or os.environ.get("SAJU_PUBLIC_URL", "")).strip()
    if not base:
        print("error: no base URL - pass --base-url or set SAJU_PUBLIC_URL "
              "(there is no localhost default)", file=sys.stderr)
        return None
    return base.rstrip("/")


def _deliver_link(link: str, row: dict) -> None:
    """Print the private link and, when SMTP is configured, email it (D2).

    Always prints the link so the owner can deliver it by hand if email is
    unavailable or fails. Never prints or logs the recipient address.
    """
    print(link)
    email = (row.get("pii") or {}).get("email", "")
    if not notify.is_configured():
        return
    if not email:
        print("note: intake has no email on file; link printed only", file=sys.stderr)
        return
    if notify.send_report_link(link, email):
        print(f"intake {row['id']}: emailed the private link")
    else:
        print(f"intake {row['id']}: email delivery failed; link printed above", file=sys.stderr)


def _client_ready_findings(store: IntakeStore, intake_id: int) -> list:
    """Run the client-ready gate over an intake's draft (markdown + PDF).

    Returns findings (empty when clean, or when there is nothing to check, e.g. a
    hand-attached PDF whose source markdown is not on disk).
    """
    import glob
    import sys as _sys

    # Works whether this file is run as a script (`python3 tools/intake_admin.py`,
    # where `tools/` is sys.path[0]) or imported as a module by the tests.
    _tools = str(Path(__file__).resolve().parent)
    if _tools not in _sys.path:
        _sys.path.insert(0, _tools)
    from qa_client_ready import scan

    root = store.files_root / str(intake_id)
    findings: list = []
    for md in sorted(glob.glob(str(root / "*.md"))):
        if md.endswith("-engine.md"):
            continue  # a sidecar, not the deliverable
        findings.extend(scan(Path(md).read_text(encoding="utf-8"), source="markdown"))
    for pdf in sorted(glob.glob(str(root / "*.pdf"))):
        text = _pdf_text(Path(pdf))
        if text:
            findings.extend(scan(text, source="pdf", rendered=True))
    return findings


def _pdf_text(pdf: Path) -> str | None:
    """Extract a PDF's text, or None when poppler is unavailable."""
    import shutil
    import subprocess

    if shutil.which("pdftotext") is None:
        return None
    result = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
                            capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def _attach(store: IntakeStore, row: dict, src: Path) -> int:
    import shutil
    if row["status"] != "draft_ready":
        print(f"error: intake {row['id']} is '{row['status']}'; attach needs 'draft_ready'",
              file=sys.stderr)
        return 1
    try:
        with src.open("rb") as fh:
            head = fh.read(5)
    except OSError as exc:
        print(f"error: cannot read {src}: {exc.strerror}", file=sys.stderr)
        return 1
    if head[:4] != b"%PDF":
        print(f"error: {src} is not a PDF", file=sys.stderr)
        return 1
    root = store.files_root.resolve()
    dest = (root / str(row["id"]) / "report.pdf")
    if not dest.resolve().is_relative_to(root):
        print("error: destination escapes the files root", file=sys.stderr)
        return 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() != dest.resolve():
        shutil.copyfile(src, dest)
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass
    store.mark_polished(row["id"], str(dest))
    print(f"intake {row['id']}: attached polished PDF ({dest})")
    return 0


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
    sp.add_argument("--force", action="store_true",
                    help="approve even if the client-ready gate flags the report")
    sp.add_argument("--base-url", default=None)
    sp = sub.add_parser("attach")
    sp.add_argument("id", type=int)
    sp.add_argument("pdf", type=Path)
    sp = sub.add_parser("revoke")
    sp.add_argument("id", type=int)
    sp = sub.add_parser("reissue")
    sp.add_argument("id", type=int)
    sp.add_argument("--base-url", default=None)
    sub.add_parser("rotate")
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
    if args.cmd == "rotate":
        print(f"re-encrypted {store.rotate_key()} intake(s) with the first key")
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
        # Client-ready gate. Every check in it came from a defect that reached a
        # delivered report (docs/analysis/2026-10-16-deep-report-audit.md); the
        # point of running it here is that a report cannot be approved with one of
        # them in it. `--force` is the deliberate override.
        findings = _client_ready_findings(store, args.id)
        if findings and not args.force:
            print(f"error: client-ready gate flagged intake {args.id} "
                  f"({len(findings)} finding(s)); fix them or pass --force", file=sys.stderr)
            for f in findings[:20]:
                where = f"{f.source}:{f.line}" if f.line else f.source
                print(f"  [{f.code}] {where}: {f.note}", file=sys.stderr)
            if len(findings) > 20:
                print(f"  ... and {len(findings) - 20} more", file=sys.stderr)
            return 1
        if findings:
            print(f"warning: client-ready gate flagged {len(findings)} finding(s); "
                  "--force given, approving anyway", file=sys.stderr)
        base = _base_url(args.base_url)
        if base is None:
            return 2
        token = store.issue_token(args.id)
        _deliver_link(f"{base}/report/{token}", row)
        return 0
    if args.cmd == "attach":
        return _attach(store, row, args.pdf)
    if args.cmd == "revoke":
        try:
            store.revoke_token(args.id)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"intake {args.id}: revoked (draft_ready); the old link no longer works")
        return 0
    if args.cmd == "reissue":
        base = _base_url(args.base_url)
        if base is None:
            return 2
        try:
            token = store.reissue_token(args.id)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        _deliver_link(f"{base}/report/{token}", row)
        return 0
    if args.cmd == "regenerate":
        if row["status"] == "approved":
            print(f"error: intake {args.id} is already approved", file=sys.stderr)
            return 1
        if row.get("polished") and not args.force:
            print(f"error: intake {args.id} has a hand-attached PDF; regenerate would "
                  "replace it - pass --force to overwrite", file=sys.stderr)
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
