"""SQLite intake store with Fernet-encrypted PII and retention purge.

Name, email and concern live encrypted in ``pii_enc``; birth data stays plain so
charts can be recomputed. Download tokens are stored only as SHA-256 hashes.
Never log decrypted PII; log intake ids only.

The ``error`` column is PLAINTEXT: callers must store sanitized messages only
(e.g. the exception class name), never PII or raw exception text.

Deploy with ``umask 077`` so the SQLite -wal/-shm sidecar files are not
group/world readable; the db file itself and ``files_root`` are chmod'ed here.

Approval is only reachable via ``issue_token`` (tokened) or, for the free
sample tier, ``mark_approved_without_token``; ``set_status`` refuses it.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, List, Optional

from cryptography.fernet import Fernet

STATUSES = ("received", "generating", "draft_ready", "approved", "failed")
KINDS = ("single", "compat")

_log = logging.getLogger(__name__)
_UNSET: Any = object()  # sentinel: "leave column unchanged" (None means clear)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS intake(
    id INTEGER PRIMARY KEY,
    created_at TEXT, kind TEXT, tier TEXT, status TEXT,
    pii_enc BLOB, birth_json TEXT, pdf_path TEXT, error TEXT,
    token_sha256 TEXT UNIQUE, approved_at TEXT, updated_at TEXT
)
"""


def generate_key() -> str:
    return Fernet.generate_key().decode()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class IntakeStore:
    def __init__(self, db_path: Path, key: bytes, files_root: Optional[Path] = None):
        self.db_path = Path(db_path)
        self._fernet = Fernet(key)
        self.files_root = Path(files_root) if files_root is not None else self.db_path.parent / "files"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.files_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.files_root, 0o700)
        except OSError:
            pass
        conn = self._conn()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(_SCHEMA)
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(intake)")}
            if "updated_at" not in cols:  # migrate pre-existing stores
                conn.execute("ALTER TABLE intake ADD COLUMN updated_at TEXT")
            conn.commit()
        finally:
            conn.close()
        try:
            os.chmod(self.db_path, 0o600)
        except (OSError, NotImplementedError):
            pass

    @classmethod
    def from_env(cls, db_path: Path, files_root: Optional[Path] = None) -> "IntakeStore":
        raw = os.environ.get("SAJU_INTAKE_KEY", "").strip()
        howto = (
            "SAJU_INTAKE_KEY is not set or invalid. Generate one with: "
            "python -c 'from saju_web.store import generate_key; print(generate_key())' "
            "and export it as SAJU_INTAKE_KEY."
        )
        if not raw:
            raise RuntimeError(howto)
        try:
            return cls(db_path, raw.encode(), files_root)
        except (ValueError, TypeError) as exc:
            raise RuntimeError(howto) from exc

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _enc(self, pii: dict) -> bytes:
        return self._fernet.encrypt(json.dumps(pii).encode())

    def _dec(self, blob: bytes) -> dict:
        return json.loads(self._fernet.decrypt(bytes(blob)))

    def _row(self, r: sqlite3.Row) -> dict:
        return {
            "id": r["id"], "kind": r["kind"], "tier": r["tier"], "status": r["status"],
            "created_at": r["created_at"], "pii": self._dec(r["pii_enc"]),
            "birth": json.loads(r["birth_json"]), "pdf_path": r["pdf_path"], "error": r["error"],
        }

    def add_intake(self, *, kind: str, tier: str, pii: dict, birth: dict) -> int:
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        conn = self._conn()
        try:
            cur = conn.execute(
                "INSERT INTO intake(created_at, updated_at, kind, tier, status, pii_enc, birth_json) "
                "VALUES (?,?,?,?,?,?,?)",
                (_now().isoformat(), _now().isoformat(), kind, tier, "received",
                 self._enc(pii), json.dumps(birth)),
            )
            conn.commit()
            return int(cur.lastrowid)
        finally:
            conn.close()

    def get_intake(self, intake_id: int) -> dict:
        conn = self._conn()
        try:
            r = conn.execute("SELECT * FROM intake WHERE id=?", (intake_id,)).fetchone()
        finally:
            conn.close()
        if r is None:
            raise KeyError(intake_id)
        return self._row(r)

    def set_status(self, intake_id: int, status: str, *, pdf_path: Any = _UNSET,
                   error: Any = _UNSET) -> None:
        """Update status. ``pdf_path``/``error``: omitted keeps, ``None`` clears.

        Moving to "generating" or "draft_ready" clears ``error`` unless one is
        passed. Raises KeyError for an unknown id; "approved" is not allowed here.
        """
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        if status == "approved":
            raise ValueError("approval only via issue_token (or mark_approved_without_token)")
        if error is _UNSET and status in ("generating", "draft_ready"):
            error = None
        sets, params = ["status=?", "updated_at=?"], [status, _now().isoformat()]
        if pdf_path is not _UNSET:
            sets.append("pdf_path=?")
            params.append(pdf_path)
        if error is not _UNSET:
            sets.append("error=?")
            params.append(error)
        params.append(intake_id)
        conn = self._conn()
        try:
            cur = conn.execute(f"UPDATE intake SET {', '.join(sets)} WHERE id=?", params)
            conn.commit()
            if cur.rowcount == 0:
                raise KeyError(intake_id)
        finally:
            conn.close()

    def mark_approved_without_token(self, intake_id: int) -> None:
        """Approve with no download token. FREE SAMPLE TIER ONLY; paid tiers use issue_token."""
        conn = self._conn()
        try:
            cur = conn.execute(
                "UPDATE intake SET status='approved', token_sha256=NULL, approved_at=? WHERE id=?",
                (_now().isoformat(), intake_id),
            )
            conn.commit()
            if cur.rowcount == 0:
                raise KeyError(intake_id)
        finally:
            conn.close()

    def list_intakes(self, status: Optional[str] = None) -> List[dict]:
        conn = self._conn()
        try:
            if status is None:
                rows = conn.execute("SELECT * FROM intake ORDER BY id").fetchall()
            else:
                rows = conn.execute("SELECT * FROM intake WHERE status=? ORDER BY id",
                                    (status,)).fetchall()
        finally:
            conn.close()
        out = []
        for r in rows:
            try:
                name = self._dec(r["pii_enc"]).get("name")
            except Exception:  # bad/corrupt row must not break the admin list
                _log.warning("intake %s: PII decryption failed", r["id"])
                name = None
            out.append({"id": r["id"], "kind": r["kind"], "tier": r["tier"],
                        "status": r["status"], "created_at": r["created_at"],
                        "updated_at": r["updated_at"] or r["created_at"], "name": name})
        return out

    def issue_token(self, intake_id: int) -> str:
        token = secrets.token_urlsafe(32)
        conn = self._conn()
        try:
            cur = conn.execute(
                "UPDATE intake SET status='approved', token_sha256=?, approved_at=? "
                "WHERE id=? AND status='draft_ready'",
                (_hash(token), _now().isoformat(), intake_id),
            )
            conn.commit()
            if cur.rowcount != 1:
                raise ValueError(f"intake {intake_id} must be in status 'draft_ready' to approve")
        finally:
            conn.close()
        return token

    def resolve_token(self, token: str) -> Optional[dict]:
        conn = self._conn()
        try:
            r = conn.execute("SELECT * FROM intake WHERE token_sha256=? AND status='approved'",
                             (_hash(token),)).fetchone()
        finally:
            conn.close()
        return self._row(r) if r else None

    def purge_older_than(self, days: int, *, now: Optional[datetime] = None) -> int:
        if now is not None:
            if now.tzinfo is None:
                raise ValueError("now must be timezone-aware")
            now = now.astimezone(timezone.utc)
        cutoff = ((now or _now()) - timedelta(days=days)).isoformat()
        conn = self._conn()
        try:
            rows = conn.execute("SELECT id, pdf_path FROM intake WHERE created_at < ?",
                                (cutoff,)).fetchall()
            conn.executemany("DELETE FROM intake WHERE id=?", [(r["id"],) for r in rows])
            conn.commit()
        finally:
            conn.close()
        root = self.files_root.resolve()
        for r in rows:
            if not r["pdf_path"]:
                continue
            pdf = Path(r["pdf_path"])
            for f in (pdf, pdf.with_suffix(".md")):
                try:
                    if f.resolve().is_relative_to(root):
                        f.unlink(missing_ok=True)
                except OSError:
                    _log.warning("intake %s: could not remove a stored file", r["id"])
        return len(rows)
