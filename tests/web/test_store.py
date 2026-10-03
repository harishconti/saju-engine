"""Tests for saju_web.store (encrypted SQLite intake store)."""
from datetime import datetime, timedelta, timezone

import pytest

pytest.importorskip("cryptography")

from saju_web.store import IntakeStore, generate_key  # noqa: E402

PII = {"name": "Alice Kim", "email": "alice@example.com", "concern": "secret worry about career"}
BIRTH = {"dob": "1990-05-01", "birth_time": "10:30", "location": "Seoul", "utc_offset": "+09:00"}


@pytest.fixture
def store(tmp_path):
    return IntakeStore(tmp_path / "intake.sqlite", generate_key().encode())


def _add(store):
    return store.add_intake(kind="single", tier="essential", pii=PII, birth=BIRTH)


def test_roundtrip_decrypts(store):
    i = _add(store)
    row = store.get_intake(i)
    assert row["pii"] == PII
    assert row["birth"] == BIRTH
    assert row["status"] == "received" and row["kind"] == "single" and row["tier"] == "essential"
    assert row["pdf_path"] is None and row["error"] is None
    assert row["created_at"].endswith("+00:00")


def test_raw_db_has_no_plaintext_pii(tmp_path):
    p = tmp_path / "i.sqlite"
    s = IntakeStore(p, generate_key().encode())
    _add(s)
    data = b"".join(f.read_bytes() for f in tmp_path.glob("i.sqlite*"))
    for needle in (b"alice@example.com", b"Alice Kim", b"secret worry"):
        assert needle not in data
    assert b"1990-05-01" in data  # birth stays plain


def test_wrong_key_raises(tmp_path):
    p = tmp_path / "i.sqlite"
    i = _add(IntakeStore(p, generate_key().encode()))
    with pytest.raises(Exception):
        IntakeStore(p, generate_key().encode()).get_intake(i)


def test_from_env(tmp_path, monkeypatch):
    monkeypatch.delenv("SAJU_INTAKE_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SAJU_INTAKE_KEY"):
        IntakeStore.from_env(tmp_path / "a.sqlite")
    monkeypatch.setenv("SAJU_INTAKE_KEY", "not-a-key")
    with pytest.raises(RuntimeError, match="SAJU_INTAKE_KEY"):
        IntakeStore.from_env(tmp_path / "a.sqlite")
    monkeypatch.setenv("SAJU_INTAKE_KEY", generate_key())
    assert IntakeStore.from_env(tmp_path / "a.sqlite")


def test_status_transitions(store):
    i = _add(store)
    store.set_status(i, "draft_ready", pdf_path="/x.pdf")
    r = store.get_intake(i)
    assert r["status"] == "draft_ready" and r["pdf_path"] == "/x.pdf"
    store.set_status(i, "failed", error="boom")
    assert store.get_intake(i)["error"] == "boom"
    with pytest.raises(ValueError):
        store.set_status(i, "bogus")
    with pytest.raises(ValueError):
        store.add_intake(kind="weird", tier="t", pii={}, birth={})


def test_token_flow(tmp_path):
    p = tmp_path / "i.sqlite"
    s = IntakeStore(p, generate_key().encode())
    i = _add(s)
    with pytest.raises(ValueError):
        s.issue_token(i)  # still "received"
    s.set_status(i, "draft_ready")
    tok = s.issue_token(i)
    assert s.get_intake(i)["status"] == "approved"
    assert s.resolve_token(tok)["id"] == i
    assert s.resolve_token("nope") is None
    data = b"".join(f.read_bytes() for f in tmp_path.glob("i.sqlite*"))
    assert tok.encode() not in data
    with pytest.raises(ValueError):
        s.issue_token(i)  # already approved


def test_list_intakes_minimal_pii(store):
    i = _add(store)
    store.set_status(i, "draft_ready")
    _add(store)
    rows = store.list_intakes()
    assert len(rows) == 2
    assert [r["id"] for r in store.list_intakes("draft_ready")] == [i]
    for r in rows:
        assert r["name"] == "Alice Kim"
        assert "email" not in str(r) and "concern" not in str(r) and "pii" not in r


def test_purge(tmp_path):
    s = IntakeStore(tmp_path / "i.sqlite", generate_key().encode())
    old_pdf = tmp_path / "old.pdf"
    old_md = tmp_path / "old.md"
    new_pdf = tmp_path / "new.pdf"
    for f in (old_pdf, old_md, new_pdf):
        f.write_text("x")
    old, new = _add(s), _add(s)
    s.set_status(old, "draft_ready", pdf_path=str(old_pdf))
    s.set_status(new, "draft_ready", pdf_path=str(new_pdf))
    now = datetime.now(timezone.utc) + timedelta(days=200)
    # make "new" recent relative to now
    import sqlite3
    with sqlite3.connect(tmp_path / "i.sqlite") as c:
        c.execute("UPDATE intake SET created_at=? WHERE id=?", ((now - timedelta(days=5)).isoformat(), new))
    assert s.purge_older_than(180, now=now) == 1
    assert not old_pdf.exists() and not old_md.exists()
    assert new_pdf.exists()
    assert [r["id"] for r in s.list_intakes()] == [new]
    with pytest.raises(KeyError):
        s.get_intake(old)
