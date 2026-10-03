"""SQLite intake store with Fernet-encrypted PII and retention purge.

Name, email and concern live encrypted in ``pii_enc``; birth data stays plain so
charts can be recomputed. Download tokens are stored only as SHA-256 hashes.
Never log decrypted PII; log intake ids only.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from cryptography.fernet import Fernet

STATUSES = ("received", "generating", "draft_ready", "approved", "failed")
KINDS = ("single", "compat")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS intake(
    id INTEGER PRIMARY KEY,
    created_at TEXT, kind TEXT, tier TEXT, status TEXT,
    pii_enc BLOB, birth_json TEXT, pdf_path TEXT, error TEXT,
    token_sha256 TEXT UNIQUE, approved_at TEXT
)
"""


def generate_key() -> str:
    return Fernet.generate_key().decode()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class IntakeStore:
    def __init__(self, db_path: Path, key: bytes):
        self.db_path = Path(db_path)
        self._fernet = Fernet(key)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._conn()
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def from_env(cls, db_path: Path) -> "IntakeStore":
        raw = os.environ.get("SAJU_INTAKE_KEY", "").strip()
        howto = (
            "SAJU_INTAKE_KEY is not set or invalid. Generate one with: "
            "python -c 'from saju_web.store import generate_key; print(generate_key())' "
            "and export it as SAJU_INTAKE_KEY."
        )
        if not raw:
            raise RuntimeError(howto)
        try:
            return cls(db_path, raw.encode())
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
                "INSERT INTO intake(created_at, kind, tier, status, pii_enc, birth_json) "
                "VALUES (?,?,?,?,?,?)",
                (_now().isoformat(), kind, tier, "received", self._enc(pii), json.dumps(birth)),
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

    def set_status(self, intake_id: int, status: str, *, pdf_path: Optional[str] = None,
                   error: Optional[str] = None) -> None:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        conn = self._conn()
        try:
            conn.execute(
                "UPDATE intake SET status=?, pdf_path=COALESCE(?, pdf_path), "
                "error=COALESCE(?, error) WHERE id=?",
                (status, pdf_path, error, intake_id),
            )
            conn.commit()
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
        return [
            {"id": r["id"], "kind": r["kind"], "tier": r["tier"], "status": r["status"],
             "created_at": r["created_at"], "name": self._dec(r["pii_enc"]).get("name")}
            for r in rows
        ]

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
        cutoff = ((now or _now()) - timedelta(days=days)).isoformat()
        conn = self._conn()
        try:
            rows = conn.execute("SELECT id, pdf_path FROM intake WHERE created_at < ?",
                                (cutoff,)).fetchall()
            for r in rows:
                if r["pdf_path"]:
                    pdf = Path(r["pdf_path"])
                    for f in (pdf, pdf.with_suffix(".md")):
                        try:
                            f.unlink()
                        except FileNotFoundError:
                            pass
                conn.execute("DELETE FROM intake WHERE id=?", (r["id"],))
            conn.commit()
            return len(rows)
        finally:
            conn.close()
